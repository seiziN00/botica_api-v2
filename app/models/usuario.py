from datetime import datetime
from zoneinfo import ZoneInfo
from enum import Enum

from sqlmodel import Field, SQLModel


peru_tz = ZoneInfo("America/Lima")


class RolEnum(str, Enum):
    STAFF = "staff"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"


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

    email_verificado_at: datetime | None = Field(
        default=None,
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
        default_factory=lambda: datetime.now(peru_tz),
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(peru_tz),
        nullable=False,
    )


# Alias de compatibilidad para código que importa "Usuario"
Usuario = UsuarioModel