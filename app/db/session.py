# app/db/session.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session as SQLModelSession

from app.core.config import settings

if settings.DATABASE_URL.startswith("sqlite"):
    # SQLite necesita este argumento para hilos múltiples
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_engine(settings.DATABASE_URL)

# Fábrica de sesiones: usa la Session de SQLModel para soportar
# tanto .exec() (SQLModel) como .query() (SQLAlchemy clásico)
SessionLocal = sessionmaker(
    class_=SQLModelSession,
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_session():
    """Dependencia FastAPI: inyecta una sesión de base de datos."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
