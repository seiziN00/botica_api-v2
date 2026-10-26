# app/models/venta.py

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from sqlmodel import Field, SQLModel, Relationship

from app.core.security import ahora


class MetodoPago(str, Enum):
    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    TRANSFERENCIA = "transferencia"
    DEBITO = "debito"
    BIM = "bim"
    TUNKI = "tunki"
    LIGO = "ligo"
    AGORA_PAY = "agora pay"
    YAPE = "yape"
    PLIN = "plin"


class Venta(SQLModel, table=True):
    __tablename__ = "ventas"

    id: Optional[int] = Field(
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

    descuento: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=12,
        decimal_places=2,
        nullable=False,
        ge=Decimal("0.00"),
    )

    pagos: List["VentaPago"] = Relationship(
        back_populates="venta",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    detalles: List["VentaDetalle"] = Relationship(
        back_populates="venta",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class VentaDetalle(SQLModel, table=True):
    __tablename__ = "venta_detalles"

    id: Optional[int] = Field(
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
        ge=Decimal("0.00"),
    )

    subtotal: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        nullable=False,
        ge=Decimal("0.00"),
    )

    # Snapshots
    producto_snapshot: str = Field(
        max_length=200,
        nullable=False,
    )

    presentacion_snapshot: Optional[str] = Field(
        default=None,
        max_length=50,
    )

    laboratorio_snapshot: Optional[str] = Field(
        default=None,
        max_length=100,
    )

    vendedor_snapshot: Optional[str] = Field(
        default=None,
        max_length=200,
        nullable=True,
    )

    unidades_base: int = Field(
        nullable=False,
        ge=1,
    )

    # Relaciones ORM
    venta: Optional[Venta] = Relationship(back_populates="detalles")

    lotes: List["VentaDetalleLote"] = Relationship(
        back_populates="venta_detalle",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class VentaDetalleLote(SQLModel, table=True):
    """Trazabilidad FEFO: de qué lote(s) salió cada detalle de venta."""

    __tablename__ = "venta_detalle_lotes"

    id: Optional[int] = Field(
        default=None,
        primary_key=True,
    )

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
    cantidad: int = Field(
        nullable=False,
        ge=1,
    )

    # Relación ORM
    venta_detalle: Optional[VentaDetalle] = Relationship(back_populates="lotes")


class VentaPago(SQLModel, table=True):
    """Un método de pago de una venta. Una venta puede tener varios."""
    __tablename__ = "venta_pagos"

    id: int | None = Field(default=None, primary_key=True)

    venta_id: int = Field(
        foreign_key="ventas.id",
        nullable=False,
        index=True,
    )

    metodo: MetodoPago = Field(nullable=False)

    monto: Decimal = Field(
        max_digits=12,
        decimal_places=2,
        nullable=False,
        ge=Decimal("0.00"),
    )

    # Relación ORM
    venta: Optional[Venta] = Relationship(back_populates="pagos")