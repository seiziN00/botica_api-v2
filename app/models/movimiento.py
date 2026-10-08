# app/models/movimiento.py

from datetime import datetime
from enum import Enum

from sqlmodel import Field, SQLModel

from app.core.security import ahora


class TipoMovimiento(str, Enum):
    # Entradas
    ENTRADA_COMPRA = "entrada_compra"
    ENTRADA_AJUSTE = "entrada_ajuste"

    # Salidas por operación normal
    SALIDA_VENTA = "salida_venta"

    # Salidas por ajuste / pérdida
    SALIDA_AJUSTE = "salida_ajuste"
    SALIDA_VENCIMIENTO = "salida_vencimiento"
    SALIDA_DETERIORO = "salida_deterioro"

    # Salidas para uso de la propia botica
    SALIDA_AUTOCONSUMO = "salida_autoconsumo"

    # Salidas no comerciales
    SALIDA_DONACION = "salida_donacion"
    SALIDA_MUESTRA_MEDICA = "salida_muestra_medica"


class Movimiento(SQLModel, table=True):
    """Historial de movimientos de stock (kardex). No es fuente de stock:
    el stock real vive en LoteModel.stock; aquí solo se registra la bitácora."""

    __tablename__ = "movimientos"

    id: int | None = Field(default=None, primary_key=True)

    fecha: datetime = Field(
        default_factory=ahora,
        nullable=False,
        index=True,
    )

    tipo: TipoMovimiento = Field(
        nullable=False,
        index=True,
    )

    producto_id: int = Field(
        foreign_key="productos.id",
        nullable=False,
        index=True,
    )

    lote_id: int = Field(
        foreign_key="lotes.id",
        nullable=False,
        index=True,
    )

    # Siempre positivo; el signo lo define el tipo
    cantidad: int = Field(nullable=False, ge=1)

    # Snapshot del stock DEL LOTE en el momento del movimiento
    stock_anterior: int = Field(nullable=False)
    stock_posterior: int = Field(nullable=False)

    usuario_id: int = Field(
        foreign_key="usuarios.id",
        nullable=False,
    )

    # Referencia genérica al origen: "venta", "factura", "ajuste", None
    referencia_tipo: str | None = Field(default=None, index=True)
    referencia_id: int | None = Field(default=None)

    motivo: str | None = None
    observacion: str | None = None
