# app/schemas/movimiento.py

from datetime import date, datetime

from pydantic import BaseModel

from app.models.movimiento import TipoMovimiento


class KardexItem(BaseModel):
    fecha: datetime
    tipo: TipoMovimiento
    cantidad: int
    stock_anterior: int
    stock_posterior: int
    lote: int
    lote_codigo: str | None
    vencimiento: date | None
    usuario: str
    referencia: str | None
    motivo: str | None
    observacion: str | None


class KardexRespuesta(BaseModel):
    total: int
    items: list[KardexItem]
