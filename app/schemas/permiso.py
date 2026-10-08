# app/schemas/permiso.py

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.permisos import PermisoEnum


class PermisoTemporalCrear(BaseModel):
    usuario_id: int
    permiso: PermisoEnum
    duracion_horas: int = Field(default=24, ge=1, le=720)


class PermisoTemporalRespuesta(BaseModel):
    id: int
    usuario_id: int
    permiso: PermisoEnum
    otorgado_por_id: int
    inicio: datetime
    expiracion: datetime
    activo: bool

    class Config:
        from_attributes = True
