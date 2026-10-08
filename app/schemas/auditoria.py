# app/schemas/auditoria.py

from datetime import datetime

from pydantic import BaseModel


class AuditoriaRespuesta(BaseModel):
    id: int
    usuario_id: int | None
    accion: str
    entidad: str | None
    entidad_id: int | None
    detalle: str | None
    fecha: datetime

    class Config:
        from_attributes = True
