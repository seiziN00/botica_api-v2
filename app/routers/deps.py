# app/routers/deps.py

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.security import ahora, decode_access_token
from app.db.session import get_session
from app.models.permiso import PermisoTemporal
from app.models.permisos import PERMISOS_POR_ROL, PermisoEnum
from app.models.usuario import UsuarioModel

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

CREDENCIALES_INVALIDAS = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Credenciales inválidas",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> UsuarioModel:
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
        token_version = payload.get("tv", 0)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise CREDENCIALES_INVALIDAS

    user = session.get(UsuarioModel, user_id)

    if user is None:
        raise CREDENCIALES_INVALIDAS

    if token_version != user.token_version:
        # Token emitido antes de un cambio de contraseña / revocación
        raise CREDENCIALES_INVALIDAS

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario desactivado",
        )

    return user


def usuario_tiene_permiso(
    session: Session,
    usuario: UsuarioModel,
    permiso: PermisoEnum,
) -> bool:
    """True si el rol lo incluye o si tiene un permiso temporal vigente."""
    if permiso in PERMISOS_POR_ROL.get(usuario.rol, set()):
        return True

    ahora_peru = ahora()
    grant = session.exec(
        select(PermisoTemporal).where(
            PermisoTemporal.usuario_id == usuario.id,
            PermisoTemporal.permiso == permiso.value,
            PermisoTemporal.activo == True,  # noqa: E712
            PermisoTemporal.inicio <= ahora_peru,
            PermisoTemporal.expiracion > ahora_peru,
        )
    ).first()

    return grant is not None


def require_permission(permiso: PermisoEnum):
    """Dependencia FastAPI: exige un permiso (por rol o temporal)."""
    def dependency(
        current_user: UsuarioModel = Depends(get_current_user),
        session: Session = Depends(get_session),
    ) -> UsuarioModel:
        if not usuario_tiene_permiso(session, current_user, permiso):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permiso requerido: {permiso.value}",
            )
        return current_user

    return dependency
