# app/models/venta.py

from datetime import datetime
from decimal import Decimal

from sqlmodel import Field, SQLModel

from app.core.security import ahora


class Venta(SQLModel, table=True):
    __tablename__ = "ventas"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    fecha: datetime = Field(
        default_factory=ahora,
        nullable=False,
        index=True,
    )

    vendedor_id: int = Field(
        foreign_key="usuarios.id",
        nullable=False,
        index=True,
    )

    total: Decimal = Field(
        default=Decimal("0"),
        max_digits=12,
        decimal_places=2,
        nullable=False,
    )


class VentaDetalle(SQLModel, table=True):
    __tablename__ = "venta_detalles"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    venta_id: int = Field(
        foreign_key="ventas.id",
        nullable=False,
        index=True,
    )

    producto_id: int = Field(
        foreign_key="productos.id",
        nullable=False,
        index=True,
    )

    presentacion_id: int | None = Field(
        default=None,
        foreign_key="producto_presentaciones.id",
    )

    cantidad: int = Field(
        nullable=False,
        ge=1,
    )

    precio_unitario: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        nullable=False,
    )

    subtotal: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        nullable=False,
    )

    # Snapshot histórico: unidades base descontadas (cantidad * multiplicador).
    # Protege el historial si luego se edita la presentación.
    unidades_base: int = Field(nullable=False, ge=1)


class VentaDetalleLote(SQLModel, table=True):
    """Trazabilidad FEFO: de qué lote(s) salió cada detalle de venta."""

    __tablename__ = "venta_detalle_lotes"

    id: int | None = Field(default=None, primary_key=True)

    venta_detalle_id: int = Field(
        foreign_key="venta_detalles.id",
        nullable=False,
        index=True,
    )

    lote_id: int = Field(
        foreign_key="lotes.id",
        nullable=False,
        index=True,
    )

    # Unidades base tomadas de ese lote
    cantidad: int = Field(nullable=False, ge=1)
