from fastapi import FastAPI
from sqlmodel import SQLModel

import app.models  # registra todas las tablas en SQLModel.metadata
from app.database import engine
from app.routers import (
    routes_productos,
    routes_auth,
    routes_usuarios,
    routes_lotes,
)


app = FastAPI(
    title="API Farmacia",
    description="API para gestionar el catálogo de productos",
    version="1.0.0",
    # docs_url=None,
    # redoc_url=None,
)

@app.on_event("startup")
def crear_tablas():
    # Crea las tablas si no existen (no borra ni modifica datos existentes)
    SQLModel.metadata.create_all(engine)


app.include_router(routes_productos.router)
app.include_router(routes_auth.router)
app.include_router(routes_usuarios.router)
app.include_router(routes_lotes.router)

@app.get("/")
def root():
    return {
        "mensaje": "API Farmacia funcionando"
    }