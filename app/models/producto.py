from decimal import Decimal
from enum import Enum

from sqlmodel import Field, SQLModel
from sqlalchemy import UniqueConstraint


class ProductoModel(SQLModel, table=True):
    __tablename__ = "productos"

    id: int | None = Field(default=None, primary_key=True)
    producto: str = Field(nullable=False, index=True)

    codigo_barras: str | None = Field(
        default=None,
        index=True,
        unique=True,
    )

    categoria: str | None = Field(
        default=None,
        index=True,
    )

    laboratorio: str | None = Field(
        default=None,
        index=True,
    )
    
    stock_minimo: int = Field(
        default=5,
        ge=0,
        nullable=False,
    )

    activo: bool = Field(
        default=True,
        nullable=False,
        index=True,
    )


class TipoPresentacion(str, Enum):
    UNIDAD = "unidad"
    BLISTER = "blister"
    CAJA = "caja"


class ProductoPresentacion(SQLModel, table=True):
    __tablename__ = "producto_presentaciones"
    
    id: int | None = Field(
        default=None,
        primary_key=True
    )
    
    producto_id: int = Field(
        foreign_key="productos.id",
        nullable=False,
        index=True,
    )
    
    tipo: TipoPresentacion = Field(
        default=TipoPresentacion.UNIDAD,
        nullable=False,
        index=True,
    )
    
    unidades_base: int = Field(
        default=1,
        ge=1,
        nullable=False,
    )
    
    precio_venta: Decimal = Field(
        max_digits=10,
        decimal_places=2,
        ge=0,
        nullable=False,
    )

    predeterminada: bool = Field(
        default=False,
        nullable=False,
    )
    
    activo: bool = Field(
        default=True,
        nullable=False,
        index=True,
    )


class ProductoAlias(SQLModel, table=True):
    __tablename__ = "producto_aliases"

    id: int | None = Field(default=None, primary_key=True)
    producto_id: int = Field(
        foreign_key="productos.id",
        index=True,
        nullable=False,
    )
    nombre: str = Field(
        nullable=False,
        index=True,
    )
    origen: str | None = None


class PrincipioActivoModel(SQLModel, table=True):
    __tablename__ = "principios_activos"

    id: int | None = Field(default=None, primary_key=True)

    nombre: str = Field(
        nullable=False,
        index=True,
        unique=True,
    )

    activo: bool = Field(
        default=True,
        index=True,
    )


# Tabla intermedia entre productos y principios activos
class ProductoPrincipioActivoModel(SQLModel, table=True):
    __tablename__ = "producto_principio_activo"

    producto_id: int = Field(
        foreign_key="productos.id",
        primary_key=True,
    )

    principio_activo_id: int = Field(
        foreign_key="principios_activos.id",
        primary_key=True,
    )

    cantidad: Decimal | None = Field(
        default=None,
        max_digits=10,
        decimal_places=3,
    )

    unidad: str | None = None