# app/services/inventario_service.py

"""Capa responsable de TODA modificación de stock.

Invariante: ningún cambio a LoteModel.stock ocurre fuera de este módulo,
y todo cambio genera su Movimiento (kardex) con snapshots correctos.

Ninguna función hace commit: el caller controla la transacción.
"""

from datetime import date
from decimal import Decimal

from sqlmodel import Session, select

from app.core.security import ahora
from app.models.lote import LoteModel
from app.models.movimiento import Movimiento, TipoMovimiento


class StockInsuficienteError(Exception):
    def __init__(self, producto_id: int, disponible: int, requerido: int):
        self.producto_id = producto_id
        self.disponible = disponible
        self.requerido = requerido
        super().__init__(
            f"Stock insuficiente para producto {producto_id}: "
            f"disponible {disponible}, requerido {requerido}"
        )


def stock_disponible(session: Session, producto_id: int) -> int:
    lotes = session.exec(
        select(LoteModel.stock).where(
            LoteModel.producto_id == producto_id,
            LoteModel.activo == True,  # noqa: E712
        )
    ).all()
    return sum(lotes)


def _registrar_movimiento(
    session: Session,
    *,
    tipo: TipoMovimiento,
    lote: LoteModel,
    cantidad: int,
    stock_anterior: int,
    usuario_id: int,
    referencia_tipo: str | None = None,
    referencia_id: int | None = None,
    motivo: str | None = None,
    observacion: str | None = None,
) -> Movimiento:
    movimiento = Movimiento(
        tipo=tipo,
        producto_id=lote.producto_id,
        lote_id=lote.id,
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_posterior=lote.stock,
        usuario_id=usuario_id,
        referencia_tipo=referencia_tipo,
        referencia_id=referencia_id,
        motivo=motivo,
        observacion=observacion,
    )
    session.add(movimiento)
    return movimiento


def descontar_fefo(
    session: Session,
    *,
    producto_id: int,
    unidades: int,
    usuario_id: int,
    referencia_tipo: str | None = None,
    referencia_id: int | None = None,
) -> list[tuple[LoteModel, int]]:
    """Descuenta unidades de los lotes más próximos a vencer (FEFO).

    Devuelve las asignaciones [(lote, unidades_tomadas), ...].
    Lanza StockInsuficienteError si no alcanza (no modifica nada en ese caso,
    siempre que se valide antes con stock_disponible).
    """
    lotes = session.exec(
        select(LoteModel)
        .where(
            LoteModel.producto_id == producto_id,
            LoteModel.activo == True,  # noqa: E712
            LoteModel.stock > 0,
        )
        .order_by(LoteModel.vencimiento.is_(None), LoteModel.vencimiento)
    ).all()

    asignaciones: list[tuple[LoteModel, int]] = []
    restante = unidades
    for lote in lotes:
        if restante <= 0:
            break
        tomado = min(lote.stock, restante)
        stock_anterior = lote.stock
        lote.stock -= tomado
        lote.updated_at = ahora()
        session.add(lote)
        _registrar_movimiento(
            session,
            tipo=TipoMovimiento.SALIDA_VENTA,
            lote=lote,
            cantidad=tomado,
            stock_anterior=stock_anterior,
            usuario_id=usuario_id,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
        )
        asignaciones.append((lote, tomado))
        restante -= tomado

    if restante > 0:
        raise StockInsuficienteError(
            producto_id,
            disponible=unidades - restante,
            requerido=unidades,
        )

    return asignaciones


def ingresar_stock(
    session: Session,
    *,
    producto_id: int,
    cantidad: int,
    usuario_id: int,
    lote_codigo: str | None = None,
    vencimiento: date | None = None,
    costo_unitario: Decimal | None = None,
    tipo: TipoMovimiento = TipoMovimiento.ENTRADA_COMPRA,
    referencia_tipo: str | None = None,
    referencia_id: int | None = None,
    motivo: str | None = None,
    observacion: str | None = None,
) -> LoteModel:
    """Ingresa stock: reutiliza el lote si coincide (código + vencimiento)
    o crea uno nuevo. Registra el movimiento de entrada."""
    lote = None
    if lote_codigo:
        lote = session.exec(
            select(LoteModel).where(
                LoteModel.producto_id == producto_id,
                LoteModel.codigo == lote_codigo,
                LoteModel.vencimiento == vencimiento,
                LoteModel.activo == True,  # noqa: E712
            )
        ).first()

    if lote is None:
        lote = LoteModel(
            producto_id=producto_id,
            codigo=lote_codigo or "LOTE-INICIAL",
            vencimiento=vencimiento,
            stock=0,
            costo_unitario=costo_unitario,
        )
        session.add(lote)
        session.flush()

    if cantidad > 0:
        stock_anterior = lote.stock
        lote.stock += cantidad
        if costo_unitario is not None:
            lote.costo_unitario = costo_unitario
        lote.updated_at = ahora()
        session.add(lote)

        _registrar_movimiento(
            session,
            tipo=tipo,
            lote=lote,
            cantidad=cantidad,
            stock_anterior=stock_anterior,
            usuario_id=usuario_id,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            motivo=motivo,
            observacion=observacion,
        )
    return lote


def ajustar_stock(
    session: Session,
    *,
    lote_id: int,
    nuevo_stock: int,
    motivo: str,
    usuario_id: int,
    observacion: str | None = None,
) -> LoteModel:
    """Ajuste manual de stock de un lote. Registra ENTRADA/SALIDA_AJUSTE
    según el signo del delta. No hace nada si no hay diferencia."""
    lote = session.get(LoteModel, lote_id)
    if not lote:
        raise ValueError(f"Lote {lote_id} no encontrado")
    if nuevo_stock < 0:
        raise ValueError("El stock no puede quedar negativo")

    delta = nuevo_stock - lote.stock
    if delta == 0:
        return lote

    stock_anterior = lote.stock
    lote.stock = nuevo_stock
    lote.updated_at = ahora()
    session.add(lote)

    _registrar_movimiento(
        session,
        tipo=(
            TipoMovimiento.ENTRADA_AJUSTE
            if delta > 0
            else TipoMovimiento.SALIDA_AJUSTE
        ),
        lote=lote,
        cantidad=abs(delta),
        stock_anterior=stock_anterior,
        usuario_id=usuario_id,
        referencia_tipo="ajuste",
        motivo=motivo,
        observacion=observacion,
    )
    return lote
