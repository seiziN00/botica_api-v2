# app/models/usuario.py

from datetime import datetime

from sqlmodel import Field, SQLModel

from app.core.security import ahora
from app.models.permisos import RolEnum


class UsuarioModel(SQLModel, table=True):
    __tablename__ = "usuarios"

    id: int | None = Field(default=None, primary_key=True)

    email: str = Field(
        nullable=False,
        unique=True,
        index=True,
        max_length=320,
    )

    nombre: str = Field(
        nullable=False,
        index=True,
        max_length=150,
    )

    password_hash: str = Field(
        nullable=False,
        max_length=255,
    )

    activo: bool = Field(
        default=True,
        nullable=False,
        index=True,
    )

    rol: RolEnum = Field(
        default=RolEnum.STAFF,
        nullable=False,
        index=True,
    )

    token_version: int = Field(
        default=0,
        nullable=False,
    )

    created_at: datetime = Field(
        default_factory=ahora,
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=ahora,
        nullable=False,
    )
