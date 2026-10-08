from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Column, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Field, SQLModel

from app.core.security import ahora

# JSONB en PostgreSQL, JSON genérico en SQLite y otros motores
JSONType = JSON().with_variant(JSONB(), "postgresql")


class FacturaEstado(str, Enum):
    PROCESANDO = "procesando"
    PENDIENTE = "pendiente"
    PROCESADA = "procesada"
    ERROR = "error"


class Factura(SQLModel, table=True):
    __tablename__ = "facturas"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    estado: FacturaEstado = Field(
        default=FacturaEstado.PROCESANDO,
        nullable=False,
        index=True,
    )

    nombre_archivo: str = Field(
        nullable=False,
    )

    cloudinary_public_id: str = Field(
        nullable=False,
    )

    cloudinary_asset_id: str | None = Field(
        default=None,
    )

    cloudinary_format: str | None = Field(
        default=None,
    )

    sha256: str = Field(
        nullable=False,
        index=True,
    )

    mime_type: str = Field(
        nullable=False,
    )

    ocr_resultado: dict | None = Field(
        default=None,
        sa_column=Column(JSONType, nullable=True),
    )

    ocr_modelo: str | None = None

    ocr_error: str | None = None

    creada_por_id: int = Field(
        foreign_key="usuarios.id",
        nullable=False,
    )

    confirmada_por_id: int | None = Field(
        default=None,
        foreign_key="usuarios.id",
    )

    created_at: datetime = Field(
        default_factory=ahora,
        nullable=False,
    )
    processed_at: datetime | None = None
    confirmed_at: datetime | None = None


class FacturaLinea(SQLModel, table=True):
    __tablename__ = "factura_lineas"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    factura_id: int = Field(
        foreign_key="facturas.id",
        nullable=False,
        index=True,
    )

    producto_id: int | None = Field(
        default=None,
        foreign_key="productos.id",
    )

    descripcion_ocr: str = Field(
        nullable=False,
    )

    cantidad: int = Field(
        nullable=False,
        ge=1,
    )

    precio_unitario: Decimal = Field(
        nullable=False,
        max_digits=10,
        decimal_places=2,
    )

    importe: Decimal = Field(
        nullable=False,
        max_digits=10,
        decimal_places=2,
    )

    lote_codigo: str | None = None

    fecha_vencimiento: date | None = None