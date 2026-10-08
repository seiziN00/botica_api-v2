# app/core/config.py

import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()

PERU_TZ = ZoneInfo("America/Lima")


def _database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///./botica.db")
    # Para producción
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


@dataclass(frozen=True)
class Settings:
    DATABASE_URL: str

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str


def load_settings() -> Settings:
    return Settings(
        DATABASE_URL=_database_url(),
        JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", ""),
        JWT_ALGORITHM=os.getenv("JWT_ALGORITHM", ""),
        ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "")),
        OPENROUTER_API_KEY=os.getenv("OPENROUTER_API_KEY", ""),
        OPENROUTER_MODEL=os.getenv("OPENROUTER_MODEL", ""),
        CLOUDINARY_CLOUD_NAME=os.getenv("CLOUDINARY_CLOUD_NAME", ""),
        CLOUDINARY_API_KEY=os.getenv("CLOUDINARY_API_KEY", ""),
        CLOUDINARY_API_SECRET=os.getenv("CLOUDINARY_API_SECRET", ""),
    )


settings = load_settings()
