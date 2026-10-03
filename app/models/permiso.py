# app/models/permiso.py

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.models.usuario import RolEnum, UsuarioModel


class PermisoTemporal(SQLModel, table=True):
    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    usuario_id: int = Field(
        foreign_key="usuarios.id",
        nullable=False,
        index=True,
    )

    permiso: str = Field(
        nullable=False,
        index=True,
    )

    otorgado_por_id: int = Field(
        foreign_key="usuarios.id",
        nullable=False,
    )

    inicio: datetime = Field(nullable=False)

    expiracion: datetime = Field(nullable=False)

    activo: bool = Field(
        default=True,
        nullable=False,
    )