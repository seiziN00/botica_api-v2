# app/routers/routes_facturas.py

"""Flujo de facturas con revisión humana:

POST /procesar-ocr → PROCESANDO → (OCR ok) → PENDIENTE → revisión humana
→ POST /{id}/confirmar → PROCESADA (transaccional, aquí se modifica stock)
Si OCR falla: PROCESANDO → ERROR → POST /{id}/reprocesar → PROCESANDO

El OCR solo genera un borrador revisable; nunca toca el stock.
"""

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlmodel import Session, select

from app.core.config import PERU_TZ
from app.core.security import ahora
from app.db.session import get_session
from app.models.factura import Factura, FacturaEstado, FacturaLinea
from app.models.permisos import PermisoEnum
from app.models.usuario import UsuarioModel
from app.routers.deps import require_permission
from app.schemas import (
    FacturaConLineas,
    FacturaLineaActualizar,
    FacturaLineaCrear,
    FacturaLineaRespuesta,
    FacturaRespuesta,
)
from app.services.audit_service import registrar_auditoria
from app.services.cloudinary_service import (
    build_url,
    calculate_sha256,
    upload_factura,
)
from app.services.inventario_service import ingresar_stock
from app.services.ocr_service import extract_invoice_with_ocr

router = APIRouter(prefix="/facturas", tags=["Facturas"])

FORMATOS_PERMITIDOS = {"image/jpeg", "image/png", "image/webp"}
TAMANO_MAXIMO = 12 * 1024 * 1024  # 12 MB


# ---- Procesamiento OCR ----

@router.post(
    "/procesar-ocr",
    status_code=status.HTTP_202_ACCEPTED,
)
def procesar_factura_ocr(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.FACTURA_PROCESAR)
    ),
    session: Session = Depends(get_session),
):
    if file.content_type not in FORMATOS_PERMITIDOS:
        raise HTTPException(status_code=400, detail="Formato no permitido")

    file.file.seek(0, 2)
    if file.file.tell() > TAMANO_MAXIMO:
        raise HTTPException(
            status_code=413, detail="La imagen supera 12 MB"
        )
    file.file.seek(0)

    sha256 = calculate_sha256(file.file)

    ahora_peru = ahora()
    upload_result = upload_factura(
        file.file,
        year=ahora_peru.year,
        month=ahora_peru.month,
    )

    factura = Factura(
        estado=FacturaEstado.PROCESANDO,
        nombre_archivo=file.filename or "factura",
        cloudinary_public_id=upload_result["public_id"],
        cloudinary_asset_id=upload_result.get("asset_id"),
        cloudinary_format=upload_result.get("format"),
        sha256=sha256,
        mime_type=file.content_type,
        creada_por_id=current_user.id,
    )

    session.add(factura)
    session.commit()
    session.refresh(factura)

    background_tasks.add_task(_procesar_ocr_background, factura.id)

    return {
        "id": factura.id,
        "estado": factura.estado,
        "mensaje": "Factura recibida y enviada a procesamiento",
    }


def _procesar_ocr_background(factura_id: int) -> None:
    """Ejecuta el OCR y genera las líneas borrador. Nunca toca stock."""
    from app.db.session import SessionLocal

    with SessionLocal() as session:
        factura = session.get(Factura, factura_id)
        if not factura:
            return

        try:
            image_url = build_url(
                factura.cloudinary_public_id, factura.cloudinary_format
            )
            resultado = extract_invoice_with_ocr([image_url])
            factura.ocr_resultado = resultado

            # Limpiar líneas previas (por si es un reprocesamiento)
            for linea in session.exec(
                select(FacturaLinea).where(
                    FacturaLinea.factura_id == factura.id
                )
            ).all():
                session.delete(linea)

            for item in resultado.get("items", []):
                session.add(
                    FacturaLinea(
                        factura_id=factura.id,
                        producto_id=None,  # el humano asigna el producto
                        descripcion_ocr=item["producto"],
                        cantidad=item["cantidad"],
                        precio_unitario=Decimal(str(item["precio_unitario"])),
                        importe=Decimal(str(item["precio_total"])),
                        lote_codigo=item.get("lote") or None,
                        fecha_vencimiento=_parsear_vencimiento(
                            item.get("vencimiento")
                        ),
                    )
                )

            factura.estado = FacturaEstado.PENDIENTE
        except Exception as e:
            factura.estado = FacturaEstado.ERROR
            factura.ocr_error = str(e)[:500]

        factura.processed_at = ahora()
        session.add(factura)
        session.commit()


def _parsear_vencimiento(valor: str | None) -> date | None:
    """El OCR devuelve DD-MM-YYYY; tolera formatos inválidos."""
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%d-%m-%Y").date()
    except ValueError:
        return None


# ---- Consulta ----

@router.get("", response_model=list[FacturaRespuesta])
def listar_facturas(
    estado: FacturaEstado | None = None,
    mes: str | None = Query(
        default=None,
        pattern=r"^\d{4}-\d{2}$",
        description="Formato YYYY-MM",
    ),
    desde: date | None = None,
    hasta: date | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.FACTURA_PROCESAR)),
):
    filtros = []
    if estado is not None:
        filtros.append(Factura.estado == estado)
    if mes is not None:
        anio, mes_num = map(int, mes.split("-"))
        inicio_mes = datetime(anio, mes_num, 1, tzinfo=PERU_TZ)
        if mes_num == 12:
            fin_mes = datetime(anio + 1, 1, 1, tzinfo=PERU_TZ)
        else:
            fin_mes = datetime(anio, mes_num + 1, 1, tzinfo=PERU_TZ)
        filtros.append(Factura.created_at >= inicio_mes)
        filtros.append(Factura.created_at < fin_mes)
    if desde is not None:
        filtros.append(
            Factura.created_at
            >= datetime.combine(desde, time.min, tzinfo=PERU_TZ)
        )
    if hasta is not None:
        fin = datetime.combine(hasta, time.min, tzinfo=PERU_TZ) + timedelta(days=1)
        filtros.append(Factura.created_at < fin)

    return session.exec(
        select(Factura)
        .where(*filtros)
        .order_by(Factura.created_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()


@router.get("/{factura_id}", response_model=FacturaConLineas)
def obtener_factura(
    factura_id: int,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.FACTURA_PROCESAR)),
):
    factura = _obtener_factura(session, factura_id)
    return _factura_con_lineas(session, factura)


# ---- Edición de líneas (solo en PENDIENTE) ----

@router.post(
    "/{factura_id}/lineas",
    response_model=FacturaLineaRespuesta,
    status_code=201,
)
def agregar_linea(
    factura_id: int,
    datos: FacturaLineaCrear,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.FACTURA_PROCESAR)),
):
    factura = _obtener_factura(session, factura_id)
    _requerir_pendiente(factura)

    linea = FacturaLinea(
        factura_id=factura.id,
        importe=datos.precio_unitario * datos.cantidad,
        **datos.model_dump(),
    )
    session.add(linea)
    session.commit()
    session.refresh(linea)
    return linea


@router.patch(
    "/{factura_id}/lineas/{linea_id}",
    response_model=FacturaLineaRespuesta,
)
def editar_linea(
    factura_id: int,
    linea_id: int,
    datos: FacturaLineaActualizar,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.FACTURA_PROCESAR)),
):
    factura = _obtener_factura(session, factura_id)
    _requerir_pendiente(factura)
    linea = _obtener_linea(session, factura.id, linea_id)

    for key, value in datos.model_dump(exclude_unset=True).items():
        setattr(linea, key, value)
    linea.importe = linea.precio_unitario * linea.cantidad

    session.add(linea)
    session.commit()
    session.refresh(linea)
    return linea


@router.delete("/{factura_id}/lineas/{linea_id}", status_code=204)
def eliminar_linea(
    factura_id: int,
    linea_id: int,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.FACTURA_PROCESAR)),
):
    factura = _obtener_factura(session, factura_id)
    _requerir_pendiente(factura)
    linea = _obtener_linea(session, factura.id, linea_id)

    session.delete(linea)
    session.commit()
    return None


# ---- Confirmación y reprocesamiento ----

@router.post("/{factura_id}/confirmar", response_model=FacturaConLineas)
def confirmar_factura(
    factura_id: int,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.FACTURA_PROCESAR)
    ),
):
    factura = _obtener_factura(session, factura_id)
    if factura.estado != FacturaEstado.PENDIENTE:
        raise HTTPException(
            status_code=409,
            detail=f"Solo se puede confirmar una factura PENDIENTE (actual: {factura.estado})",
        )

    lineas = session.exec(
        select(FacturaLinea).where(FacturaLinea.factura_id == factura.id)
    ).all()
    if not lineas:
        raise HTTPException(
            status_code=409, detail="La factura no tiene líneas"
        )

    sin_producto = [l.id for l in lineas if l.producto_id is None]
    if sin_producto:
        raise HTTPException(
            status_code=409,
            detail=f"Líneas sin producto asignado: {sin_producto}",
        )

    # Transaccional: ingreso de stock + movimientos + cambio de estado
    for linea in lineas:
        ingresar_stock(
            session,
            producto_id=linea.producto_id,
            cantidad=linea.cantidad,
            usuario_id=current_user.id,
            lote_codigo=linea.lote_codigo,
            vencimiento=linea.fecha_vencimiento,
            costo_unitario=linea.precio_unitario,
            referencia_tipo="factura",
            referencia_id=factura.id,
        )

    factura.estado = FacturaEstado.PROCESADA
    factura.confirmada_por_id = current_user.id
    factura.confirmed_at = ahora()
    session.add(factura)

    registrar_auditoria(
        session,
        current_user.id,
        "confirmar_factura",
        entidad="factura",
        entidad_id=factura.id,
        detalle=f"lineas={len(lineas)}",
    )

    session.commit()

    return _factura_con_lineas(session, factura)


@router.post(
    "/{factura_id}/reprocesar",
    status_code=status.HTTP_202_ACCEPTED,
)
def reprocesar_factura(
    factura_id: int,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.FACTURA_PROCESAR)),
):
    factura = _obtener_factura(session, factura_id)
    if factura.estado != FacturaEstado.ERROR:
        raise HTTPException(
            status_code=409,
            detail=f"Solo se puede reprocesar una factura en ERROR (actual: {factura.estado})",
        )

    factura.estado = FacturaEstado.PROCESANDO
    factura.ocr_error = None
    session.add(factura)
    session.commit()

    background_tasks.add_task(_procesar_ocr_background, factura.id)

    return {
        "id": factura.id,
        "estado": factura.estado,
        "mensaje": "Factura reenviada a procesamiento",
    }


# ---- Helpers ----

def _obtener_factura(session: Session, factura_id: int) -> Factura:
    factura = session.get(Factura, factura_id)
    if not factura:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    return factura


def _obtener_linea(
    session: Session, factura_id: int, linea_id: int
) -> FacturaLinea:
    linea = session.get(FacturaLinea, linea_id)
    if not linea or linea.factura_id != factura_id:
        raise HTTPException(status_code=404, detail="Línea no encontrada")
    return linea


def _requerir_pendiente(factura: Factura) -> None:
    if factura.estado != FacturaEstado.PENDIENTE:
        raise HTTPException(
            status_code=409,
            detail=f"Solo se pueden editar líneas de una factura PENDIENTE (actual: {factura.estado})",
        )


def _factura_con_lineas(session: Session, factura: Factura) -> FacturaConLineas:
    lineas = session.exec(
        select(FacturaLinea).where(FacturaLinea.factura_id == factura.id)
    ).all()
    return FacturaConLineas(
        **FacturaRespuesta.model_validate(factura).model_dump(),
        url=build_url(factura.cloudinary_public_id, factura.cloudinary_format),
        lineas=lineas,
    )
