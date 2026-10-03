from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from jose import JWTError, jwt
from passlib.context import CryptContext


SECRET_KEY = "8$]ga~sSx6W;X`s$9fW0ahI7@)M=uY5H"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # Token válido por 24 horas

PERU_TIMEZONE = ZoneInfo("America/Lima")

# Contexto para bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_peru_now() -> datetime:
    """Devuelve la fecha y hora actual de Perú."""
    return datetime.now(PERU_TIMEZONE)


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: timedelta | None = None
):
    to_encode = data.copy()

    now_peru = get_peru_now()

    if expires_delta:
        expire_peru = now_peru + expires_delta
    else:
        expire_peru = now_peru + timedelta(minutes=15)

    # JWT trabaja con timestamps UTC.
    # Así que se convierte la fecha de expiración de Perú a UTC.
    expire_utc = expire_peru.astimezone(timezone.utc)

    to_encode.update({"exp": expire_utc})

    encoded_jwt = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return encoded_jwt