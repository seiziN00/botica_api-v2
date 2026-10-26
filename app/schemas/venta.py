# app/schemas/venta.py

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.venta import MetodoPago


class VentaItem(BaseModel):
    producto_id: int
    presentacion_id: int | None = None
    cantidad: int = Field(ge=1)


class VentaPagoItem(BaseModel):
    metodo: MetodoPago
    monto: Decimal = Field(gt=Decimal("0.00"))


class VentaPagoRespuesta(BaseModel):
    id: int
    metodo: MetodoPago
    monto: Decimal

    class Config:
        from_attributes = True


class VentaCrear(BaseModel):
    items: list[VentaItem] = Field(min_length=1)
    descuento: Decimal = Field(default=Decimal("0.00"), ge=0)
    pagos: list[VentaPagoItem] = Field(min_length=1)


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
    producto_snapshot: str | None = None
    presentacion_snapshot: str | None = None
    laboratorio_snapshot: str | None = None
    vendedor_snapshot: str | None = None
    lotes: list[VentaDetalleLoteRespuesta] = []

    class Config:
        from_attributes = True


class VentaRespuesta(BaseModel):
    id: int
    fecha: datetime
    vendedor_id: int
    total: Decimal
    descuento: Decimal
    pagos: list[VentaPagoRespuesta] = []

    class Config:
        from_attributes = True


class VentaConDetalle(VentaRespuesta):
    detalles: list[VentaDetalleRespuesta] = []
