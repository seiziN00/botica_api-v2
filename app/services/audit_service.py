# app/services/audit_service.py

from sqlmodel import Session

from app.models.auditoria import Auditoria


def registrar_auditoria(
    session: Session,
    usuario_id: int | None,
    accion: str,
    entidad: str | None = None,
    entidad_id: int | None = None,
    detalle: str | None = None,
) -> None:
    """Registra una acción sensible. No hace commit: lo hace el caller."""
    session.add(
        Auditoria(
            usuario_id=usuario_id,
            accion=accion,
            entidad=entidad,
            entidad_id=entidad_id,
            detalle=detalle,
        )
    )
