# app/schemas/factura.py

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.factura import FacturaEstado


class FacturaLineaCrear(BaseModel):
    producto_id: int | None = None
    descripcion_ocr: str = Field(min_length=1)
    cantidad: int = Field(ge=1)
    precio_unitario: Decimal = Field(ge=0)
    lote_codigo: str | None = None
    fecha_vencimiento: date | None = None


class FacturaLineaActualizar(BaseModel):
    producto_id: int | None = None
    descripcion_ocr: str | None = Field(default=None, min_length=1)
    cantidad: int | None = Field(default=None, ge=1)
    precio_unitario: Decimal | None = Field(default=None, ge=0)
    lote_codigo: str | None = None
    fecha_vencimiento: date | None = None


class FacturaLineaRespuesta(BaseModel):
    id: int
    factura_id: int
    producto_id: int | None
    descripcion_ocr: str
    cantidad: int
    precio_unitario: Decimal
    importe: Decimal
    lote_codigo: str | None
    fecha_vencimiento: date | None

    class Config:
        from_attributes = True


class FacturaRespuesta(BaseModel):
    id: int
    estado: FacturaEstado
    nombre_archivo: str
    created_at: datetime
    processed_at: datetime | None
    confirmed_at: datetime | None
    creada_por_id: int
    confirmada_por_id: int | None
    ocr_error: str | None

    class Config:
        from_attributes = True


class FacturaConLineas(FacturaRespuesta):
    url: str | None = None
    lineas: list[FacturaLineaRespuesta] = []
