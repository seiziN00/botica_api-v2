from datetime import date, datetime
from zoneinfo import ZoneInfo
from decimal import Decimal

from sqlmodel import Field, SQLModel


class LoteModel(SQLModel, table=True):
    __tablename__ = "lotes"

    id: int | None = Field(default=None, primary_key=True)

    producto_id: int = Field(
        foreign_key="productos.id",
        nullable=False,
        index=True,
    )

    codigo: str | None = Field(
        default="LOTE-INICIAL",
        index=True,
    )

    vencimiento: date | None = Field(
        default=None,
        index=True,
    )

    stock: int = Field(
        default=0,
        ge=0,
        nullable=False,
    )

    costo_unitario: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=2,
    )

    activo: bool = Field(
        default=True,
        index=True,
    )

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("America/Lima")),
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(ZoneInfo("America/Lima")),
    )