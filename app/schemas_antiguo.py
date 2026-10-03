from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, EmailStr


# ------------ PRODUCTOS --------------
class ProductoBase(BaseModel):
    producto: str = Field(min_length=1)
    precio_venta: float = Field(ge=0)
    codigo_barras: str | None = Field(default=None)
    laboratorio: str | None = Field(default=None)


class ProductoCrear(ProductoBase):
    pass


class ProductoActualizar(ProductoBase):
    pass


class ProductoRespuesta(ProductoBase):
    id: int



# Para el Login
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


# LOTES
class LoteBase(BaseModel):
    codigo_lote: str | None = Field(default=None)
    fecha_vencimiento: date | None = None
    stock: int = Field(
        default=0,
        ge=0,
    )
    costo_unitario: Decimal | None = Field(
        default=None,
        ge=0,
    )


class LoteCrear(LoteBase):
    producto_id: int


class LoteActualizar(BaseModel):
    codigo_lote: str | None = Field(
        default=None,
        max_length=100,
    )
    fecha_vencimiento: date | None = None
    costo_unitario: Decimal | None = Field(
        default=None,
        ge=0,
    )


class LoteRespuesta(LoteBase):
    id: int
    producto_id: int