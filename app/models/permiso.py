# app/models/permiso.py

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.core.security import ahora
from app.models.permisos import PermisoEnum


class PermisoTemporal(SQLModel, table=True):
    __tablename__ = "permisos_temporales"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    usuario_id: int = Field(
        foreign_key="usuarios.id",
        nullable=False,
        index=True,
    )

    permiso: PermisoEnum = Field(
        nullable=False,
        index=True,
    )

    otorgado_por_id: int = Field(
        foreign_key="usuarios.id",
        nullable=False,
    )

    inicio: datetime = Field(
        default_factory=ahora,
        nullable=False,
    )

    expiracion: datetime = Field(
        nullable=False,
    )

    activo: bool = Field(
        default=True,
        nullable=False,
    )
