from fastapi import FastAPI
from sqlmodel import SQLModel

import app.models  # registra todas las tablas en SQLModel.metadata
from app.db.session import engine
from app.routers import (
    routes_auditoria,
    routes_auth,
    routes_facturas,
    routes_kardex,
    routes_lotes,
    routes_permisos,
    routes_productos,
    routes_reportes,
    routes_usuarios,
    routes_ventas,
)

app = FastAPI(
    title="API Botica",
    description="API para gestionar una botica: catálogo, lotes, ventas, usuarios y auditoría",
    version="2.0.0",
)


@app.on_event("startup")
def crear_tablas():
    # Crea las tablas si no existen (no borra ni modifica datos existentes)
    SQLModel.metadata.create_all(engine)


app.include_router(routes_auth.router)
app.include_router(routes_usuarios.router)
app.include_router(routes_productos.router)
app.include_router(routes_lotes.router)
app.include_router(routes_ventas.router)
app.include_router(routes_reportes.router)
app.include_router(routes_auditoria.router)
app.include_router(routes_permisos.router)
app.include_router(routes_facturas.router)
app.include_router(routes_kardex.router)


@app.get("/")
def root():
    return {"mensaje": "API Botica funcionando"}
