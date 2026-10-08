# app/schemas/reporte.py

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.venta import VentaRespuesta


class VentasDelDia(BaseModel):
    fecha: date
    total_ventas: int
    monto_total: Decimal
    ventas: list[VentaRespuesta]


class ReporteFinanciero(BaseModel):
    desde: date
    hasta: date
    total_ventas: int
    ingresos: Decimal
    costo_estimado: Decimal
    utilidad_estimada: Decimal
