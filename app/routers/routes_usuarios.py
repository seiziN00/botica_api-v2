# app/routers/routes_usuarios.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.security import ahora, hash_password
from app.db.session import get_session
from app.models.permisos import PermisoEnum, RolEnum
from app.models.usuario import UsuarioModel
from app.routers.deps import require_permission
from app.schemas import UsuarioCrear, UsuarioRespuesta
from app.services.audit_service import registrar_auditoria

router = APIRouter(prefix="/usuarios", tags=["Usuarios"])

# Jerarquía estricta:
#   SUPERADMIN -> crea/elimina ADMIN (y cualquier usuario)
#   ADMIN      -> gestiona STAFF
#   STAFF      -> no gestiona usuarios


def _crear_usuario(
    datos: UsuarioCrear,
    rol: RolEnum,
    session: Session,
    creador_id: int,
) -> UsuarioModel:
    existe = session.exec(
        select(UsuarioModel).where(UsuarioModel.email == datos.email)
    ).first()

    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado",
        )

    nuevo = UsuarioModel(
        nombre=datos.nombre,
        email=datos.email,
        password_hash=hash_password(datos.password),
        rol=rol,
        activo=True,
    )
    session.add(nuevo)
    session.flush()

    registrar_auditoria(
        session,
        creador_id,
        "crear_usuario",
        entidad="usuario",
        entidad_id=nuevo.id,
        detalle=f"rol={rol.value}",
    )

    session.commit()
    session.refresh(nuevo)
    return nuevo


@router.post("/staff", response_model=UsuarioRespuesta, status_code=201)
def crear_staff(
    datos: UsuarioCrear,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.STAFF_GESTIONAR)
    ),
):
    """Admin (o superior) crea cuentas de Staff."""
    return _crear_usuario(datos, RolEnum.STAFF, session, current_user.id)


@router.post("/admins", response_model=UsuarioRespuesta, status_code=201)
def crear_admin(
    datos: UsuarioCrear,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.ADMIN_CREAR)
    ),
):
    """Solo Superadmin crea cuentas de Admin."""
    return _crear_usuario(datos, RolEnum.ADMIN, session, current_user.id)


@router.get("", response_model=list[UsuarioRespuesta])
def listar_usuarios(
    rol: RolEnum | None = None,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.STAFF_GESTIONAR)
    ),
):
    statement = select(UsuarioModel).order_by(UsuarioModel.nombre)
    if rol:
        statement = statement.where(UsuarioModel.rol == rol)
    return session.exec(statement).all()


@router.patch("/{usuario_id}/desactivar", response_model=UsuarioRespuesta)
def desactivar_usuario(
    usuario_id: int,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.STAFF_GESTIONAR)
    ),
):
    usuario = session.get(UsuarioModel, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    _validar_jerarquia(current_user, usuario)

    usuario.activo = False
    usuario.token_version += 1  # invalida sus tokens
    usuario.updated_at = ahora()
    session.add(usuario)

    registrar_auditoria(
        session,
        current_user.id,
        "desactivar_usuario",
        entidad="usuario",
        entidad_id=usuario.id,
    )

    session.commit()
    session.refresh(usuario)
    return usuario


@router.patch("/{usuario_id}/activar", response_model=UsuarioRespuesta)
def activar_usuario(
    usuario_id: int,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.STAFF_GESTIONAR)
    ),
):
    usuario = session.get(UsuarioModel, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    _validar_jerarquia(current_user, usuario)

    usuario.activo = True
    usuario.updated_at = ahora()
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=204)
def eliminar_usuario(
    usuario_id: int,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.ADMIN_ELIMINAR)
    ),
):
    """Solo Superadmin elimina usuarios (no puede eliminarse a sí mismo)."""
    usuario = session.get(UsuarioModel, usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if usuario.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta",
        )

    registrar_auditoria(
        session,
        current_user.id,
        "eliminar_usuario",
        entidad="usuario",
        entidad_id=usuario.id,
        detalle=f"email={usuario.email}, rol={usuario.rol.value}",
    )

    session.delete(usuario)
    session.commit()
    return None


def _validar_jerarquia(actor: UsuarioModel, objetivo: UsuarioModel) -> None:
    """Un Admin solo gestiona Staff; Superadmin gestiona a todos."""
    if actor.rol == RolEnum.SUPERADMIN:
        return
    if actor.rol == RolEnum.ADMIN and objetivo.rol == RolEnum.STAFF:
        return
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="No puedes gestionar usuarios de tu mismo nivel o superior",
    )
