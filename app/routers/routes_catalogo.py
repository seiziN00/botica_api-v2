# app/routers/routes_catalogo.py

"""Catálogo completo en una sola llamada: productos + presentaciones +
stock disponible. Pensado para que el POS lo cachee en local y solo
vuelva a consultar tras ventas o actualizaciones."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, func, select

from app.db.session import get_session
from app.models.lote import LoteModel
from app.models.permisos import PermisoEnum
from app.models.producto import ProductoModel, ProductoPresentacion
from app.models.usuario import UsuarioModel
from app.routers.deps import require_permission
from app.schemas import (
    ProductoCatalogo,
    ProductoPresentacionRead,
    ProductoRespuesta,
)

router = APIRouter(prefix="/catalogo", tags=["Catálogo"])


@router.get("", response_model=list[ProductoCatalogo])
def obtener_catalogo(
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.CATALOGO_VER)),
):
    # 3 consultas en total (evita N+1)
    productos = session.exec(
        select(ProductoModel).order_by(ProductoModel.producto)
    ).all()

    presentaciones = session.exec(
        select(ProductoPresentacion).order_by(ProductoPresentacion.id)
    ).all()

    stock_por_producto = dict(
        session.exec(
            select(
                LoteModel.producto_id,
                func.coalesce(func.sum(LoteModel.stock), 0),
            )
            .where(
                LoteModel.activo == True, # noqa: E712
                LoteModel.stock > 0,
            )
            .group_by(LoteModel.producto_id)
        ).all()
    )

    presentaciones_por_producto: dict[int, list[ProductoPresentacion]] = {}
    for p in presentaciones:
        presentaciones_por_producto.setdefault(p.producto_id, []).append(p)

    return [
        ProductoCatalogo(
            **ProductoRespuesta.model_validate(prod).model_dump(),
            stock_disponible=stock_por_producto.get(prod.id, 0),
            presentaciones=[
                ProductoPresentacionRead.model_validate(p)
                for p in presentaciones_por_producto.get(prod.id, [])
            ],
        )
        for prod in productos
    ]
