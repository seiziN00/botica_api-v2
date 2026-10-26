# app/routers/routes_ventas.py

from datetime import datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.core.config import PERU_TZ
from app.core.security import ahora
from app.db.session import get_session
from app.models.lote import LoteModel
from app.models.permisos import PermisoEnum
from app.models.producto import ProductoModel, ProductoPresentacion
from app.models.usuario import UsuarioModel
from app.models.venta import Venta, VentaDetalle, VentaDetalleLote, VentaPago
from app.routers.deps import require_permission
from app.schemas import (
    VentaConDetalle,
    VentaCrear,
    VentaDetalleLoteRespuesta,
    VentaDetalleRespuesta,
    VentaRespuesta,
    VentasDelDia,
)
from app.services.audit_service import registrar_auditoria
from app.services.inventario_service import (
    StockInsuficienteError,
    descontar_fefo,
    stock_disponible,
)

router = APIRouter(prefix="/ventas", tags=["Ventas"])


@router.post("", response_model=VentaConDetalle, status_code=201)
def crear_venta(
    datos: VentaCrear,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.VENTA_CREAR)
    ),
):
    # 1. Validar que los pagos enviados sumen un monto válido
    total_pagado = sum((p.monto for p in datos.pagos), Decimal("0.00"))
    if total_pagado <= Decimal("0.00"):
        raise HTTPException(
            status_code=400,
            detail="El monto total de los pagos debe ser mayor a cero",
        )

    # 2. Validar productos, presentaciones, stock y calcular el total de los ítems
    total = Decimal("0.00")
    preparados = []

    for item in datos.items:
        producto = session.get(ProductoModel, item.producto_id)
        if not producto or not producto.activo:
            raise HTTPException(
                status_code=404,
                detail=f"Producto {item.producto_id} no encontrado",
            )

        multiplicador = 1
        if item.presentacion_id:
            presentacion = session.get(
                ProductoPresentacion, item.presentacion_id
            )
            if (
                not presentacion
                or presentacion.producto_id != item.producto_id
                or not presentacion.activo
            ):
                raise HTTPException(
                    status_code=404,
                    detail=f"Presentación {item.presentacion_id} inválida",
                )
            precio_unitario = presentacion.precio_venta
            multiplicador = presentacion.unidades_base
        else:
            presentacion = session.exec(
                select(ProductoPresentacion).where(
                    ProductoPresentacion.producto_id == item.producto_id,
                    ProductoPresentacion.predeterminada == True,  # noqa: E712
                    ProductoPresentacion.activo == True,  # noqa: E712
                )
            ).first()
            if not presentacion:
                raise HTTPException(
                    status_code=409,
                    detail=f"El producto {item.producto_id} no tiene presentación predeterminada",
                )
            precio_unitario = presentacion.precio_venta
            item.presentacion_id = presentacion.id

        unidades = item.cantidad * multiplicador
        disponible = stock_disponible(session, item.producto_id)
        if disponible < unidades:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Stock insuficiente para '{producto.producto}': "
                    f"disponible {disponible}, requerido {unidades}"
                ),
            )

        subtotal = precio_unitario * item.cantidad
        total += subtotal
        preparados.append((item, producto, presentacion, precio_unitario, unidades, subtotal))

    # Aplicar descuento global
    descuento_global = datos.descuento if datos.descuento else Decimal("0.00")
    total = total - descuento_global

    if total < Decimal("0.00"):
        raise HTTPException(
            status_code=400,
            detail="El descuento no puede ser mayor al total de la venta",
        )

    # 3. Validar que los pagos coincidan exactamente con el total final
    if total_pagado != total:
        raise HTTPException(
            status_code=400,
            detail=f"El total pagado ({total_pagado}) no coincide con el total de la venta ({total})",
        )

    # 4. Crear la cabecera de la venta
    venta = Venta(
        vendedor_id=current_user.id,
        total=total,
        descuento=descuento_global,
    )
    session.add(venta)
    session.flush()

    # 5. Registrar los métodos de pago múltiples
    for pago_item in datos.pagos:
        session.add(
            VentaPago(
                venta_id=venta.id,
                metodo=pago_item.metodo,
                monto=pago_item.monto,
            )
        )

    # 6. Descontar stock (FEFO) y registrar detalles y lotes
    detalles: list[VentaDetalle] = []
    asignaciones_por_detalle: list[list[tuple[LoteModel, int]]] = []

    try:
        for item, producto, presentacion, precio_unitario, unidades, subtotal in preparados:
            asignaciones = descontar_fefo(
                session,
                producto_id=item.producto_id,
                unidades=unidades,
                usuario_id=current_user.id,
                referencia_tipo="venta",
                referencia_id=venta.id,
            )
            
            detalles.append(
                VentaDetalle(
                    venta_id=venta.id,
                    producto_id=item.producto_id,
                    presentacion_id=item.presentacion_id,
                    cantidad=item.cantidad,
                    precio_unitario=precio_unitario,
                    subtotal=subtotal,
                    unidades_base=unidades,
                    descuento_snapshot=Decimal("0.00"),
                    producto_snapshot=producto.producto,
                    presentacion_snapshot=f"{presentacion.tipo.value} x {presentacion.unidades_base}" if presentacion else None,
                    laboratorio_snapshot=producto.laboratorio,
                    vendedor_snapshot=current_user.nombre,
                )
            )
            asignaciones_por_detalle.append(asignaciones)
    except StockInsuficienteError as e:
        raise HTTPException(status_code=409, detail=str(e))

    for detalle in detalles:
        session.add(detalle)
    session.flush()

    for detalle, asignaciones in zip(detalles, asignaciones_por_detalle):
        for lote, tomado in asignaciones:
            session.add(
                VentaDetalleLote(
                    venta_detalle_id=detalle.id,
                    lote_id=lote.id,
                    cantidad=tomado,
                )
            )

    registrar_auditoria(
        session,
        current_user.id,
        "crear_venta",
        entidad="venta",
        entidad_id=venta.id,
        detalle=f"total={total}",
    )

    session.commit()
    session.refresh(venta)

    return _venta_con_detalle(session, venta)


@router.get("", response_model=list[VentaRespuesta])
def listar_ventas(
    limite: int = Query(default=50, ge=1, le=200),
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.VENTA_VER)),
):
    return session.exec(
        select(Venta).order_by(Venta.fecha.desc()).limit(limite)
    ).all()


@router.get("/del-dia", response_model=VentasDelDia)
def ventas_del_dia(
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.VENTA_VER_DIA)),
):
    hoy = ahora().date()
    inicio = datetime.combine(hoy, time.min, tzinfo=PERU_TZ)
    fin = inicio + timedelta(days=1)

    ventas = session.exec(
        select(Venta).where(Venta.fecha >= inicio, Venta.fecha < fin)
    ).all()

    monto_total = sum((v.total for v in ventas), Decimal("0"))

    return VentasDelDia(
        fecha=hoy,
        total_ventas=len(ventas),
        monto_total=monto_total,
        ventas=ventas,
    )


@router.get("/{venta_id}", response_model=VentaConDetalle)
def obtener_venta(
    venta_id: int,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.VENTA_VER)),
):
    venta = session.get(Venta, venta_id)
    if not venta:
        raise HTTPException(status_code=404, detail="Venta no encontrada")
    return _venta_con_detalle(session, venta)


# ---- Helper de respuesta ----

def _venta_con_detalle(session: Session, venta: Venta) -> VentaConDetalle:
    detalles = session.exec(
        select(VentaDetalle).where(VentaDetalle.venta_id == venta.id)
    ).all()

    detalles_resp = []
    for detalle in detalles:
        asignaciones = session.exec(
            select(VentaDetalleLote, LoteModel)
            .join(LoteModel, VentaDetalleLote.lote_id == LoteModel.id)
            .where(VentaDetalleLote.venta_detalle_id == detalle.id)
        ).all()
        lotes_resp = [
            VentaDetalleLoteRespuesta(
                lote_id=lote.id,
                lote_codigo=lote.codigo,
                cantidad=asignacion.cantidad,
            )
            for asignacion, lote in asignaciones
        ]
        detalles_resp.append(
            VentaDetalleRespuesta(
                id=detalle.id,
                producto_id=detalle.producto_id,
                presentacion_id=detalle.presentacion_id,
                cantidad=detalle.cantidad,
                precio_unitario=detalle.precio_unitario,
                subtotal=detalle.subtotal,
                unidades_base=detalle.unidades_base,
                producto_snapshot=detalle.producto_snapshot,
                presentacion_snapshot=detalle.presentacion_snapshot,
                laboratorio_snapshot=detalle.laboratorio_snapshot,
                vendedor_snapshot=detalle.vendedor_snapshot,
                lotes=lotes_resp,
            )
        )

    return VentaConDetalle(
        **VentaRespuesta.model_validate(venta).model_dump(),
        detalles=detalles_resp,
    )