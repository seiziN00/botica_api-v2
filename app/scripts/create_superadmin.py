# app/scripts/create_superadmin.py
"""
Crea el usuario superadmin inicial.

Uso:
    SUPERADMIN_EMAIL=admin@botica.com SUPERADMIN_PASSWORD=secreto123 \
    SUPERADMIN_NOMBRE="Administrador" python -m app.scripts.create_superadmin

O interactivo (te pedirá los datos):
    python -m app.scripts.create_superadmin
"""

import getpass
import os

from sqlmodel import Session, select

from app.core.security import hash_password
from app.db.session import engine
from app.models.permisos import RolEnum
from app.models.usuario import UsuarioModel


def main() -> None:
    email = os.getenv("SUPERADMIN_EMAIL") or input("Email: ").strip()
    nombre = os.getenv("SUPERADMIN_NOMBRE") or input("Nombre: ").strip()
    password = os.getenv("SUPERADMIN_PASSWORD") or getpass.getpass(
        "Password (mín. 8 caracteres): "
    )

    if len(password) < 8:
        raise SystemExit("La contraseña debe tener al menos 8 caracteres")

    with Session(engine) as session:
        existe = session.exec(
            select(UsuarioModel).where(UsuarioModel.email == email)
        ).first()

        if existe:
            existe.rol = RolEnum.SUPERADMIN
            existe.activo = True
            existe.password_hash = hash_password(password)
            session.add(existe)
            session.commit()
            print(f"Usuario existente promovido a superadmin: {email}")
            return

        superadmin = UsuarioModel(
            nombre=nombre,
            email=email,
            password_hash=hash_password(password),
            rol=RolEnum.SUPERADMIN,
            activo=True,
        )
        session.add(superadmin)
        session.commit()
        print(f"Superadmin creado: {email}")


if __name__ == "__main__":
    main()
