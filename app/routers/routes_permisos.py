# app/routers/routes_permisos.py

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.security import ahora
from app.db.session import get_session
from app.models.permiso import PermisoTemporal
from app.models.permisos import PermisoEnum
from app.models.usuario import UsuarioModel
from app.routers.deps import require_permission
from app.schemas import PermisoTemporalCrear, PermisoTemporalRespuesta
from app.services.audit_service import registrar_auditoria

router = APIRouter(prefix="/permisos", tags=["Permisos temporales"])


@router.post("", response_model=PermisoTemporalRespuesta, status_code=201)
def otorgar_permiso(
    datos: PermisoTemporalCrear,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.PERMISO_OTORGAR)
    ),
):
    """Superadmin otorga un permiso extra a un usuario por tiempo limitado."""
    usuario = session.get(UsuarioModel, datos.usuario_id)
    if not usuario or not usuario.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    grant = PermisoTemporal(
        usuario_id=datos.usuario_id,
        permiso=datos.permiso,
        otorgado_por_id=current_user.id,
        expiracion=ahora() + timedelta(hours=datos.duracion_horas),
    )
    session.add(grant)
    session.flush()

    registrar_auditoria(
        session,
        current_user.id,
        "otorgar_permiso",
        entidad="usuario",
        entidad_id=datos.usuario_id,
        detalle=f"permiso={datos.permiso.value}, horas={datos.duracion_horas}",
    )

    session.commit()
    session.refresh(grant)
    return grant


@router.get("", response_model=list[PermisoTemporalRespuesta])
def listar_permisos(
    usuario_id: int | None = None,
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.PERMISO_OTORGAR)),
):
    statement = select(PermisoTemporal).order_by(PermisoTemporal.id.desc())
    if usuario_id:
        statement = statement.where(PermisoTemporal.usuario_id == usuario_id)
    return session.exec(statement).all()


@router.delete("/{permiso_id}", status_code=204)
def revocar_permiso(
    permiso_id: int,
    session: Session = Depends(get_session),
    current_user: UsuarioModel = Depends(
        require_permission(PermisoEnum.PERMISO_OTORGAR)
    ),
):
    grant = session.get(PermisoTemporal, permiso_id)
    if not grant:
        raise HTTPException(status_code=404, detail="Permiso no encontrado")

    grant.activo = False

    registrar_auditoria(
        session,
        current_user.id,
        "revocar_permiso",
        entidad="usuario",
        entidad_id=grant.usuario_id,
        detalle=f"permiso={grant.permiso.value}",
    )

    session.commit()
    return None
