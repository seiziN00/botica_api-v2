# app/api/deps.py

import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select

from app.core.config import settings
from app.db.session import get_session
from app.models.usuario import Usuario


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: Session = Depends(get_session),
) -> Usuario:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        user_id = payload.get("sub")

        if not user_id:
            raise credentials_exception

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError):
        raise credentials_exception

    user = session.get(Usuario, user_id)

    if not user:
        raise credentials_exception

    if not user.activo:
        raise HTTPException(
            status_code=403,
            detail="Usuario desactivado",
        )

    if not user.email_verificado:
        raise HTTPException(
            status_code=403,
            detail="Email no verificado",
        )

    return user


ROL_LEVEL = {
    RolEnum.STAFF: 1,
    RolEnum.ADMIN: 2,
    RolEnum.SUPERADMIN: 3,
}

def require_min_role(required_role: RolEnum):
    def dependency(
        current_user: Usuario = Depends(get_current_user),
    ) -> Usuario:
        current_level = ROLE_LEVEL[current_user.rol]
        required_level = ROLE_LEVEL[current_role]

        if current_level < required_level:
            raise HTTPException(
                status_code=403,
                detail="No tienes permisos suficientes",
            )

        return current_user

    return dependency