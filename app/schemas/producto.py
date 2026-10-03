# app/schemas/productos.py

from pydantic import BaseModel, Field


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