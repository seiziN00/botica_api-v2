# app/schemas/auth.py

from pydantic import BaseModel

from app.schemas.usuario import UsuarioRespuesta


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UsuarioRespuesta
