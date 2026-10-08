# app/schemas/producto.py

from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.producto import TipoPresentacion


class ProductoBase(BaseModel):
    producto: str = Field(min_length=1)
    codigo_barras: str | None = Field(default=None)
    categoria: str | None = Field(default=None)
    laboratorio: str | None = Field(default=None)
    stock_minimo: int = Field(default=5, ge=0)


class ProductoCrear(ProductoBase):
    precio_venta: Decimal = Field(ge=0)


class ProductoActualizar(BaseModel):
    producto: str | None = Field(default=None, min_length=1)
    codigo_barras: str | None = None
    categoria: str | None = None
    laboratorio: str | None = None
    stock_minimo: int | None = Field(default=None, ge=0)
    activo: bool | None = None


class PrecioActualizar(BaseModel):
    precio_venta: Decimal = Field(ge=0)


class ProductoRespuesta(ProductoBase):
    id: int
    activo: bool

    class Config:
        from_attributes = True


# ---- Presentaciones ----

class ProductoPresentacionCreate(BaseModel):
    tipo: TipoPresentacion
    unidades_base: int = Field(ge=1)
    precio_venta: Decimal = Field(ge=0)
    predeterminada: bool = False


class ProductoPresentacionUpdate(BaseModel):
    precio_venta: Decimal | None = Field(default=None, ge=0)
    predeterminada: bool | None = None
    activo: bool | None = None


class ProductoPresentacionRead(BaseModel):
    id: int
    tipo: TipoPresentacion
    unidades_base: int
    precio_venta: Decimal
    predeterminada: bool
    activo: bool

    class Config:
        from_attributes = True
