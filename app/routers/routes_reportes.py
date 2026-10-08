# app/routers/routes_reportes.py

from datetime import date, datetime, time, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.core.config import PERU_TZ
from app.db.session import get_session
from app.models.lote import LoteModel
from app.models.permisos import PermisoEnum
from app.models.usuario import UsuarioModel
from app.models.venta import Venta, VentaDetalle
from app.routers.deps import require_permission
from app.schemas import ReporteFinanciero

router = APIRouter(prefix="/reportes", tags=["Reportes"])


@router.get("/financiero", response_model=ReporteFinanciero)
def reporte_financiero(
    desde: date = Query(...),
    hasta: date = Query(...),
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(
        require_permission(PermisoEnum.REPORTE_FINANCIERO_VER)
    ),
):
    inicio = datetime.combine(desde, time.min, tzinfo=PERU_TZ)
    fin = datetime.combine(hasta, time.min, tzinfo=PERU_TZ) + timedelta(days=1)

    ventas = session.exec(
        select(Venta).where(Venta.fecha >= inicio, Venta.fecha < fin)
    ).all()

    ingresos = sum((v.total for v in ventas), Decimal("0"))

    # Costo estimado: costo del lote vigente * unidades vendidas
    venta_ids = [v.id for v in ventas]
    costo_estimado = Decimal("0")
    if venta_ids:
        detalles = session.exec(
            select(VentaDetalle).where(VentaDetalle.venta_id.in_(venta_ids))
        ).all()
        for detalle in detalles:
            lote = session.exec(
                select(LoteModel)
                .where(
                    LoteModel.producto_id == detalle.producto_id,
                    LoteModel.costo_unitario.is_not(None),
                )
                .order_by(LoteModel.id.desc())
                .limit(1)
            ).first()
            if lote and lote.costo_unitario:
                costo_estimado += lote.costo_unitario * detalle.cantidad

    return ReporteFinanciero(
        desde=desde,
        hasta=hasta,
        total_ventas=len(ventas),
        ingresos=ingresos,
        costo_estimado=costo_estimado,
        utilidad_estimada=ingresos - costo_estimado,
    )
