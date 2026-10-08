# app/schemas/venta.py

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class VentaItem(BaseModel):
    producto_id: int
    presentacion_id: int | None = None
    cantidad: int = Field(ge=1)


class VentaCrear(BaseModel):
    items: list[VentaItem] = Field(min_length=1)


class VentaDetalleLoteRespuesta(BaseModel):
    lote_id: int
    lote_codigo: str | None = None
    cantidad: int


class VentaDetalleRespuesta(BaseModel):
    id: int
    producto_id: int
    presentacion_id: int | None
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    unidades_base: int
    lotes: list[VentaDetalleLoteRespuesta] = []

    class Config:
        from_attributes = True


class VentaRespuesta(BaseModel):
    id: int
    fecha: datetime
    vendedor_id: int
    total: Decimal

    class Config:
        from_attributes = True


class VentaConDetalle(VentaRespuesta):
    detalles: list[VentaDetalleRespuesta] = []
