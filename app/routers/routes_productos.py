# app/routers/routes_productos.py

from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.permisos import PermisoEnum
from app.models.producto import ProductoModel, ProductoPresentacion
from app.models.usuario import UsuarioModel
from app.routers.deps import require_permission
from app.schemas import (
    PrecioActualizar,
    ProductoActualizar,
    ProductoCrear,
    ProductoPresentacionCreate,
    ProductoPresentacionRead,
    ProductoPresentacionUpdate,
    ProductoRespuesta,
)
from app.services.audit_service import registrar_auditoria

router = APIRouter(prefix="/productos", tags=["Productos"])


# ---- Listado y detalle (catálogo) ----

@router.get("", response_model=list[ProductoRespuesta])
def listar_productos(
    search: str | None = Query(default=None, min_length=1),
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.CATALOGO_VER)),
):
    query = select(ProductoModel)
    if search:
        query = query.where(ProductoModel.producto.ilike(f"%{search}%"))
    query = query.order_by(ProductoModel.producto)
    return session.exec(query).all()


@router.get("/{producto_id}", response_model=ProductoRespuesta)
def obtener_producto(
    producto_id: int,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.CATALOGO_VER)),
):
    producto = session.get(ProductoModel, producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return producto


# ---- Crear / editar ----

@router.post("", response_model=ProductoRespuesta, status_code=201)
def crear_producto(
    producto: ProductoCrear,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.PRODUCTO_CREAR)
    ),
):
    try:
        nuevo_producto = ProductoModel(
            producto=producto.producto,
            codigo_barras=producto.codigo_barras,
            categoria=producto.categoria,
            laboratorio=producto.laboratorio,
            stock_minimo=producto.stock_minimo,
        )
        session.add(nuevo_producto)
        session.flush()

        # La presentación "unidad" predeterminada lleva el precio base
        session.add(
            ProductoPresentacion(
                producto_id=nuevo_producto.id,
                precio_venta=producto.precio_venta,
                predeterminada=True,
            )
        )

        registrar_auditoria(
            session,
            current_user.id,
            "crear_producto",
            entidad="producto",
            entidad_id=nuevo_producto.id,
        )

        session.commit()
        session.refresh(nuevo_producto)
        return nuevo_producto
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El producto ya existe o hay un conflicto de datos",
        )


@router.put("/{producto_id}", response_model=ProductoRespuesta)
def actualizar_producto(
    producto_id: int,
    producto: ProductoActualizar,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.PRODUCTO_EDITAR)),
):
    existente = session.get(ProductoModel, producto_id)
    if existente is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    for key, value in producto.model_dump(exclude_unset=True).items():
        setattr(existente, key, value)

    session.commit()
    session.refresh(existente)
    return existente


@router.delete("/{producto_id}", status_code=204)
def eliminar_producto(
    producto_id: int,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.PRODUCTO_EDITAR)),
):
    producto = session.get(ProductoModel, producto_id)
    if producto is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    # Borrado lógico para preservar historial de ventas/lotes
    producto.activo = False
    session.commit()
    return None


# ---- Precios (solo Superadmin, o quien tenga el permiso temporal) ----

@router.patch("/{producto_id}/precio", response_model=ProductoPresentacionRead)
def cambiar_precio(
    producto_id: int,
    datos: PrecioActualizar,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.PRECIO_EDITAR)
    ),
):
    presentacion = _presentacion_predeterminada(session, producto_id)
    if presentacion is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    anterior = presentacion.precio_venta
    presentacion.precio_venta = datos.precio_venta

    registrar_auditoria(
        session,
        current_user.id,
        "cambiar_precio",
        entidad="producto",
        entidad_id=producto_id,
        detalle=f"{anterior} -> {datos.precio_venta}",
    )

    session.commit()
    session.refresh(presentacion)
    return presentacion


# ---- Presentaciones ----

@router.get(
    "/{producto_id}/presentaciones",
    response_model=list[ProductoPresentacionRead],
)
def listar_presentaciones(
    producto_id: int,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.CATALOGO_VER)),
):
    return session.exec(
        select(ProductoPresentacion)
        .where(ProductoPresentacion.producto_id == producto_id)
        .order_by(ProductoPresentacion.id)
    ).all()


@router.post(
    "/{producto_id}/presentaciones",
    response_model=ProductoPresentacionRead,
    status_code=201,
)
def crear_presentacion(
    producto_id: int,
    datos: ProductoPresentacionCreate,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.PRODUCTO_EDITAR)),
):
    if session.get(ProductoModel, producto_id) is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")

    if datos.predeterminada:
        _limpiar_predeterminadas(session, producto_id)

    nueva = ProductoPresentacion(producto_id=producto_id, **datos.model_dump())
    session.add(nueva)
    session.commit()
    session.refresh(nueva)
    return nueva


@router.patch(
    "/{producto_id}/presentaciones/{presentacion_id}",
    response_model=ProductoPresentacionRead,
)
def actualizar_presentacion(
    producto_id: int,
    presentacion_id: int,
    datos: ProductoPresentacionUpdate,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.PRODUCTO_EDITAR)),
):
    presentacion = session.get(ProductoPresentacion, presentacion_id)
    if presentacion is None or presentacion.producto_id != producto_id:
        raise HTTPException(status_code=404, detail="Presentación no encontrada")

    cambios = datos.model_dump(exclude_unset=True)
    if cambios.get("predeterminada"):
        _limpiar_predeterminadas(session, producto_id)

    for key, value in cambios.items():
        setattr(presentacion, key, value)

    session.commit()
    session.refresh(presentacion)
    return presentacion


# ---- Helpers ----

def _presentacion_predeterminada(
    session: Session, producto_id: int
) -> ProductoPresentacion | None:
    return session.exec(
        select(ProductoPresentacion).where(
            ProductoPresentacion.producto_id == producto_id,
            ProductoPresentacion.predeterminada == True,  # noqa: E712
        )
    ).first()


def _limpiar_predeterminadas(session: Session, producto_id: int) -> None:
    for p in session.exec(
        select(ProductoPresentacion).where(
            ProductoPresentacion.producto_id == producto_id,
            ProductoPresentacion.predeterminada == True,  # noqa: E712
        )
    ).all():
        p.predeterminada = False
        session.add(p)
