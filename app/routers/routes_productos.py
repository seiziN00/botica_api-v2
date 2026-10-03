from fastapi import APIRouter, HTTPException, Query, Depends
from sqlmodel import Session, select
from sqlalchemy.exc import IntegrityError

from app.database import get_db
from app.models import ProductoModel, LoteModel
from app.schemas import (
    ProductoCrear,
    ProductoActualizar,
    ProductoRespuesta,
)

router = APIRouter(
    prefix="/productos",
    tags=["Productos"],
)

# @@@@@@@@@@@@@
# @@ LISTADO @@
# @@@@@@@@@@@@@
@router.get("", response_model=list[ProductoRespuesta])
def listar_productos(
    search: str | None = Query(default=None, min_length=1),
    session: Session = Depends(get_db)
):
    query = select(ProductoModel)
    if search:
        query = query.where(ProductoModel.producto.ilike(f"%{search}%"))

    query = query.order_by(ProductoModel.producto)
    productos = session.exec(query).all()

    return productos


# @@@@@@@@@@@@@@@@@@@@@@@@@
# @@ OBTENER UN PRODUCTO @@
# @@@@@@@@@@@@@@@@@@@@@@@@@
@router.get("/{producto_id}", response_model=ProductoRespuesta)
def obtener_producto(producto_id: int, session: Session = Depends(get_db)):
    producto = session.get(ProductoModel, producto_id)

    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    return producto


# @@@@@@@@@@@
# @@ CREAR @@
# @@@@@@@@@@@
@router.post("", response_model=ProductoRespuesta, status_code=201)
def crear_producto(producto: ProductoCrear, session: Session = Depends(get_db)):
    try:
        nuevo_producto = ProductoModel(
            producto=producto.producto,
            precio_venta=producto.precio_venta,
            codigo_barras=getattr(producto, "codigo_barras", None),
            categoria=getattr(producto, "categoria", None),
            laboratorio=getattr(producto, "laboratorio", None),
            presentacion=getattr(producto, "presentacion", None),
            principio_activo=getattr(producto, "principio_activo", None)
        )
        session.add(nuevo_producto)
        session.commit()
        session.refresh(nuevo_producto)

    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="El producto ya existe o hay un conflicto de datos")


# @@@@@@@@@@@@
# @@ EDITAR @@
# @@@@@@@@@@@@
@router.put("/{producto_id}", response_model=ProductoRespuesta)
def actualizar_producto(
    producto_id: int,
    producto: ProductoActualizar,
    session: Session = Depends(get_db)
):
    existente = session.get(ProductoModel, producto_id)

    if existente is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    datos_actualizados = producto.model_dump(exclude_unset=True)
    for key, value in datos_actualizados.items():
        setattr(existente, key, value)

    session.commit()
    session.refresh(existente)
    return existente


# @@@@@@@@@@@@@@
# @@ ELIMINAR @@
# @@@@@@@@@@@@@@
@router.delete("/{producto_id}", status_code=204)
def eliminar_producto(producto_id: int, session: Session = Depends(get_db)):
    producto = session.get(ProductoModel, producto_id)

    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    session.delete(producto)
    session.commit()
    return None