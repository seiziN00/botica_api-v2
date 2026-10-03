from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field


class LoteBase(BaseModel):
    codigo: str | None = Field(default=None)
    vencimiento: date | None = None
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
    codigo: str | None = Field(
        default=None,
        max_length=100,
    )
    vencimiento: date | None = None
    costo_unitario: Decimal | None = Field(
        default=None,
        ge=0,
    )


class LoteRespuesta(LoteBase):
    id: int
    producto_id: int