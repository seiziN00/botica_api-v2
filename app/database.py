import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session as SQLModelSession


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./botica.db")

# Corrección de compatibilidad para Railway y SQLAlchemy
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Crear engine
if DATABASE_URL.startswith("sqlite"):
    # SQLite necesita este argumento adicional para hilos múltiples
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # PostgreSQL se conecta de forma estándar
    engine = create_engine(DATABASE_URL)

# Fábrica de sesiones para las peticiones HTTP
# Usa la Session de SQLModel para soportar tanto .exec() (SQLModel)
# como .query() (SQLAlchemy clásico) en los endpoints
SessionLocal = sessionmaker(
    class_=SQLModelSession,
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Base para declarar los modelos de las tablas
Base = declarative_base()

# Dependencia para inyectar la sesión de base de datos en los endpoints de FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# No entiendo mucho esta cosa, pero me gusta.