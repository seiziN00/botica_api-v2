# app/routers/routes_kardex.py

from datetime import date, datetime, time, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, func, select

from app.core.config import PERU_TZ
from app.db.session import get_session
from app.models.lote import LoteModel
from app.models.movimiento import Movimiento, TipoMovimiento
from app.models.permisos import PermisoEnum
from app.models.producto import ProductoModel
from app.models.usuario import UsuarioModel
from app.routers.deps import require_permission
from app.schemas import KardexItem, KardexRespuesta

router = APIRouter(prefix="/kardex", tags=["Kardex"])


def _query_kardex(
    session: Session,
    *,
    producto_id: int | None = None,
    lote_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    tipo: TipoMovimiento | None = None,
    limit: int,
    offset: int,
) -> KardexRespuesta:
    filtros = []
    if producto_id is not None:
        filtros.append(Movimiento.producto_id == producto_id)
    if lote_id is not None:
        filtros.append(Movimiento.lote_id == lote_id)
    if desde is not None:
        filtros.append(
            Movimiento.fecha >= datetime.combine(desde, time.min, tzinfo=PERU_TZ)
        )
    if hasta is not None:
        fin = datetime.combine(hasta, time.min, tzinfo=PERU_TZ) + timedelta(days=1)
        filtros.append(Movimiento.fecha < fin)
    if tipo is not None:
        filtros.append(Movimiento.tipo == tipo)

    total = session.exec(
        select(func.count()).select_from(Movimiento).where(*filtros)
    ).one()

    filas = session.exec(
        select(Movimiento, LoteModel, UsuarioModel)
        .join(LoteModel, Movimiento.lote_id == LoteModel.id)
        .join(UsuarioModel, Movimiento.usuario_id == UsuarioModel.id)
        .where(*filtros)
        .order_by(Movimiento.fecha.desc(), Movimiento.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    items = [
        KardexItem(
            fecha=mov.fecha,
            tipo=mov.tipo,
            cantidad=mov.cantidad,
            stock_anterior=mov.stock_anterior,
            stock_posterior=mov.stock_posterior,
            lote=lote.id,
            lote_codigo=lote.codigo,
            vencimiento=lote.vencimiento,
            usuario=usuario.nombre,
            referencia=(
                f"{mov.referencia_tipo}:{mov.referencia_id}"
                if mov.referencia_tipo
                else None
            ),
            motivo=mov.motivo,
            observacion=mov.observacion,
        )
        for mov, lote, usuario in filas
    ]

    return KardexRespuesta(total=total, items=items)


@router.get("/productos/{producto_id}", response_model=KardexRespuesta)
def kardex_por_producto(
    producto_id: int,
    desde: date | None = None,
    hasta: date | None = None,
    tipo: TipoMovimiento | None = None,
    lote_id: int | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.KARDEX_VER)),
):
    if not session.get(ProductoModel, producto_id):
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return _query_kardex(
        session,
        producto_id=producto_id,
        lote_id=lote_id,
        desde=desde,
        hasta=hasta,
        tipo=tipo,
        limit=limit,
        offset=offset,
    )


@router.get("/lotes/{lote_id}", response_model=KardexRespuesta)
def kardex_por_lote(
    lote_id: int,
    desde: date | None = None,
    hasta: date | None = None,
    tipo: TipoMovimiento | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.KARDEX_VER)),
):
    if not session.get(LoteModel, lote_id):
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    return _query_kardex(
        session,
        lote_id=lote_id,
        desde=desde,
        hasta=hasta,
        tipo=tipo,
        limit=limit,
        offset=offset,
    )
