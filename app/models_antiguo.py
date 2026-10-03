from decimal import Decimal
from datetime import date
from sqlmodel import Field, SQLModel


class ProductoModel(SQLModel, table=True):
    __tablename__ = "productos"

    id: int | None = Field(default=None, primary_key=True)
    producto: str = Field(nullable=False, index=True)
    precio_venta: Decimal = Field(
        default=Decimal("0.00"),
        max_digits=10,
        decimal_places=2,
        ge=0,
    )

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

    presentacion: str | None = None      # tableta, frasco, sobre, etc
    
    activo: bool = Field(
        default=True,
        index=True,
    )


class ProductoAlias(SQLModel, table=True):
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



class LoteModel(SQLModel, table=True):
    __tablename__ = "lotes"

    id: int | None = Field(default=None, primary_key=True)
    producto_id: int = Field(foreign_key="productos.id", index=True)

    codigo: str = Field(default="LOTE-INICIAL", index=True)
    stock: int = Field(default=0, ge=0)
    vencimiento: date | None = Field(default=None)
    
    activo: bool = Field(default=True, index=True)


class UsuarioModel(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: int | None = Field(default=None, primary_key=True)
    nombre: str
    email: str = Field(unique=True)
    password_hash: str
    is_active: bool = Field(default=True)