# app/models/auditoria.py

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.core.security import ahora


class Auditoria(SQLModel, table=True):
    __tablename__ = "auditoria"

    id: int | None = Field(
        default=None,
        primary_key=True,
    )

    usuario_id: int | None = Field(
        default=None,
        foreign_key="usuarios.id",
        index=True,
    )

    accion: str = Field(
        nullable=False,
        index=True,
        max_length=100,
    )

    entidad: str | None = Field(
        default=None,
        index=True,
        max_length=50,
    )

    entidad_id: int | None = Field(
        default=None,
    )

    detalle: str | None = Field(
        default=None,
    )

    fecha: datetime = Field(
        default_factory=ahora,
        nullable=False,
        index=True,
    )
