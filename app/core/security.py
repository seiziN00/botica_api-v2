# app/core/security.py

from datetime import datetime, timedelta
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import PERU_TZ, settings

password_hash = PasswordHash.recommended()


def ahora() -> datetime:
    """Fecha y hora actual en Perú (timezone-aware, requerido por SQLModel)."""
    return datetime.now(PERU_TZ)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(user_id: int, token_version: int = 0) -> str:
    now = ahora()

    payload = {
        "sub": str(user_id),
        "type": "access",
        "jti": str(uuid4()),
        "tv": token_version,
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """Decodifica y valida un token. Lanza jwt.InvalidTokenError si es inválido."""
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
