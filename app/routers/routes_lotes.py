# app/routers/routes_lotes.py

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.core.security import ahora
from app.db.session import get_session
from app.models.lote import LoteModel
from app.models.permisos import PermisoEnum
from app.models.producto import ProductoModel
from app.models.usuario import UsuarioModel
from app.routers.deps import require_permission
from app.schemas import LoteActualizar, LoteCrear, LoteRespuesta
from app.services.audit_service import registrar_auditoria
from app.services.inventario_service import ajustar_stock, ingresar_stock

router = APIRouter(prefix="/lotes", tags=["Lotes"])


@router.get("/producto/{producto_id}", response_model=list[LoteRespuesta])
def listar_lotes_por_producto(
    producto_id: int,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.INVENTARIO_VER)),
):
    if not session.get(ProductoModel, producto_id):
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return session.exec(
        select(LoteModel)
        .where(LoteModel.producto_id == producto_id)
        .order_by(LoteModel.vencimiento)
    ).all()


@router.post("", response_model=LoteRespuesta, status_code=201)
def crear_lote(
    lote: LoteCrear,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.LOTE_CREAR)
    ),
):
    if not session.get(ProductoModel, lote.producto_id):
        raise HTTPException(
            status_code=404, detail="El producto asociado no existe"
        )

    # ingresar_stock crea el lote (o reutiliza uno con mismo código +
    # vencimiento) y registra el movimiento de entrada en el kardex
    nuevo_lote = ingresar_stock(
        session,
        producto_id=lote.producto_id,
        cantidad=lote.stock,
        usuario_id=current_user.id,
        lote_codigo=lote.codigo,
        vencimiento=lote.vencimiento,
        costo_unitario=lote.costo_unitario,
        motivo="creación de lote",
    )

    registrar_auditoria(
        session,
        current_user.id,
        "crear_lote",
        entidad="lote",
        entidad_id=nuevo_lote.id,
        detalle=f"producto_id={lote.producto_id}, stock={lote.stock}",
    )

    session.commit()
    session.refresh(nuevo_lote)
    return nuevo_lote


@router.put("/{lote_id}", response_model=LoteRespuesta)
def actualizar_lote(
    lote_id: int,
    lote_data: LoteActualizar,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.LOTE_EDITAR)
    ),
):
    lote = session.get(LoteModel, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    datos = lote_data.model_dump(exclude_unset=True)
    nuevo_stock = datos.pop("stock", None)
    motivo = datos.pop("motivo", None)

    # El stock solo cambia por ajuste, nunca por edición directa,
    # para que el kardex registre el movimiento
    if nuevo_stock is not None and nuevo_stock != lote.stock:
        if not motivo:
            raise HTTPException(
                status_code=400,
                detail="Se requiere 'motivo' para ajustar el stock",
            )
        try:
            ajustar_stock(
                session,
                lote_id=lote.id,
                nuevo_stock=nuevo_stock,
                motivo=motivo,
                usuario_id=current_user.id,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    for key, value in datos.items():
        setattr(lote, key, value)
    lote.updated_at = ahora()

    session.commit()
    session.refresh(lote)
    return lote


@router.delete("/{lote_id}", status_code=204)
def eliminar_lote(
    lote_id: int,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.LOTE_EDITAR)
    ),
):
    lote = session.get(LoteModel, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    # Borrado lógico: el lote puede tener movimientos y ventas históricas
    lote.activo = False
    lote.updated_at = ahora()
    session.add(lote)

    registrar_auditoria(
        session,
        current_user.id,
        "eliminar_lote",
        entidad="lote",
        entidad_id=lote.id,
        detalle=f"producto_id={lote.producto_id} (borrado lógico)",
    )

    session.commit()
    return None


@router.get("/venciendo", response_model=list[LoteRespuesta])
def lotes_venciendo(
    dias: int | None = Query(default=None, ge=0),
    meses: int | None = Query(default=None, ge=0),
    desde: date | None = None,
    hasta: date | None = None,
    producto_id: int | None = None,
    vencidos: bool | None = Query(default=None, description="True para ver ya vencidos, False para vigentes"),
    solo_con_stock: bool = Query(default=True),
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.INVENTARIO_VER)),
):
    """Lotes que vencen en el futuro inmediato.

    Filtros (combinables):
      - dias  : vencen en los próximos N días
      - meses : vencen en los próximos N meses
      - desde/hasta : rango absoluto de fechas de vencimiento
      - producto_id : limitar a un producto
      - vencidos: ver los ya vencidos
      - solo_con_stock : solo lotes con stock > 0
    """
    hoy = ahora().date()
    corte = hoy
    if dias:
        corte = corte + timedelta(days=dias)
    if meses:
        corte = corte + relativedelta(months=meses)

    filtros = [
        LoteModel.activo == True, # noqa: E712
        LoteModel.vencimiento.is_not(None),
    ]

    if solo_con_stock:
        filtros.append(LoteModel.stock > 0)
    if producto_id is not None:
        filtros.append(LoteModel.producto_id == producto_id)

    # Rango de vencimiento: [hoy, corte] si se dio un parámetro relativo
    if vencidos is not None:
        if vencidos:
            filtros.append(LoteModel.vencimiento < hoy)
        else:
            filtros.append(LoteModel.vencimiento >= hoy)
    else:
        if dias or meses:
            filtros.append(LoteModel.vencimiento.is_not(None))
            filtros.append(LoteModel.vencimiento >= hoy)
            filtros.append(LoteModel.vencimiento <= corte)
        else:
            if desde is not None:
                filtros.append(LoteModel.vencimiento >= desde)
            if hasta is not None:
                filtros.append(LoteModel.vencimiento <= hasta)

    return session.exec(
        select(LoteModel)
        .where(*filtros)
        .order_by(LoteModel.vencimiento)
    ).all()