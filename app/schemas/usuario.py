from pydantic import BaseModel, Field, EmailStr


class UsuarioLogin(BaseModel):
    email: str
    password: str

# Para crear un usuario
class UsuarioCrear(BaseModel):
    nombre: str = Field(min_length=1, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=100)

# Respuesta segura (sin password)
class UsuarioRespuesta(BaseModel):
    id: int
    nombre: str
    email: str
    
    class Config:
        from_attributes = True

# Permite cambiar solo el nombre
class UsuarioActualizarPerfil(BaseModel):
    nombre: str