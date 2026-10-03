from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import UsuarioModel
from app.auth import get_current_user
from app.schemas import UsuarioRespuesta, UsuarioActualizarPerfil
from app.security import verify_password, create_access_token


router = APIRouter(tags=["Autenticación"])

@router.post("/auth/login")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(UsuarioModel).filter(UsuarioModel.email == form_data.username).first()

    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Cuenta desactivada")

    if not user.email_verificado:
        raise HTTPException(
            status_code=403,
            detail="Debes verificar tu cuenta antes de iniciar sesión"
        )
    
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": UsuarioRespuesta.model_validate(user)
    }


@router.patch("/perfil", response_model=UsuarioRespuesta)
def actualizar_mi_perfil(
    datos: UsuarioActualizarPerfil,
    current_user: UsuarioModel = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # current_user ya viene identificado por el Token
    current_user.nombre = datos.nombre
    db.commit()
    db.refresh(current_user)
    return current_user