# app/routers/routes_auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select

from app.core.security import (
    ahora,
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.session import get_session
from app.models.usuario import UsuarioModel
from app.routers.deps import get_current_user
from app.schemas import (
    CambiarPassword,
    Token,
    UsuarioActualizarPerfil,
    UsuarioRespuesta,
)
from app.services.audit_service import registrar_auditoria

router = APIRouter(tags=["Autenticación"])


@router.post("/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):
    user = session.exec(
        select(UsuarioModel).where(UsuarioModel.email == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
        )

    if not user.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cuenta desactivada",
        )

    access_token = create_access_token(user.id, user.token_version)

    return Token(
        access_token=access_token,
        user=UsuarioRespuesta.model_validate(user),
    )


@router.get("/perfil", response_model=UsuarioRespuesta)
def ver_mi_perfil(current_user: UsuarioModel = Depends(get_current_user)):
    return current_user


@router.patch("/perfil", response_model=UsuarioRespuesta)
def actualizar_mi_perfil(
    datos: UsuarioActualizarPerfil,
    current_user: UsuarioModel = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    current_user.nombre = datos.nombre
    current_user.updated_at = ahora()
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    return current_user


@router.post("/perfil/cambiar-password", status_code=204)
def cambiar_password(
    datos: CambiarPassword,
    current_user: UsuarioModel = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    if not verify_password(datos.password_actual, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La contraseña actual es incorrecta",
        )

    current_user.password_hash = hash_password(datos.password_nuevo)
    # Invalida todos los tokens emitidos anteriormente
    current_user.token_version += 1
    current_user.updated_at = ahora()

    session.add(current_user)
    registrar_auditoria(
        session,
        current_user.id,
        "cambiar_password",
        entidad="usuario",
        entidad_id=current_user.id,
    )
    session.commit()
    return None
