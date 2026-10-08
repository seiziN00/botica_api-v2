# app/routers/routes_auditoria.py

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.auditoria import Auditoria
from app.models.permisos import PermisoEnum
from app.models.usuario import UsuarioModel
from app.routers.deps import require_permission
from app.schemas import AuditoriaRespuesta

router = APIRouter(prefix="/auditoria", tags=["Auditoría"])


@router.get("", response_model=list[AuditoriaRespuesta])
def listar_auditoria(
    entidad: str | None = Query(default=None),
    limite: int = Query(default=100, ge=1, le=500),
    session: Session = Depends(get_session),
    _: UsuarioModel = Depends(require_permission(PermisoEnum.AUDITORIA_VER)),
):
    statement = select(Auditoria).order_by(Auditoria.fecha.desc()).limit(limite)
    if entidad:
        statement = statement.where(Auditoria.entidad == entidad)
    return session.exec(statement).all()
