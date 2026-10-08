# app/schemas/usuario.py

from pydantic import BaseModel, Field, EmailStr

from app.models.permisos import RolEnum


class UsuarioLogin(BaseModel):
    email: str
    password: str


class UsuarioCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)
    rol: RolEnum = RolEnum.STAFF


class UsuarioRespuesta(BaseModel):
    id: int
    nombre: str
    email: str
    rol: RolEnum
    activo: bool

    class Config:
        from_attributes = True


class UsuarioActualizarPerfil(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)


class CambiarPassword(BaseModel):
    password_actual: str
    password_nuevo: str = Field(min_length=8, max_length=100)
