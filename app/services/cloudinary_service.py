# app/services/cloudinary_service.py

import hashlib

import cloudinary
import cloudinary.uploader
import cloudinary.utils

from app.core.config import settings


def _configurar() -> None:
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )


def build_url(public_id: str, formato: str | None = None) -> str | None:
    """Reconstruye la URL segura de un asset ya subido.
    Devuelve None si Cloudinary no está configurado."""
    if not settings.CLOUDINARY_CLOUD_NAME:
        return None
    _configurar()
    url, _ = cloudinary.utils.cloudinary_url(
        public_id,
        format=formato,
        resource_type="image",
        secure=True,
    )
    return url


def calculate_sha256(file_obj) -> str:
    """Calcula el SHA-256 de un archivo y deja el cursor al inicio."""
    file_obj.seek(0)
    digest = hashlib.sha256(file_obj.read()).hexdigest()
    file_obj.seek(0)
    return digest


def upload_factura(file_obj, year: int, month: int) -> dict:
    """Sube una imagen de factura a Cloudinary, organizada por año/mes."""
    _configurar()
    folder = f"facturas/{year}/{month:02d}"

    response = cloudinary.uploader.upload(
        file_obj,
        folder=folder,
        resource_type="image",
        use_filename=True,
        unique_filename=True,
    )

    return {
        "public_id": response.get("public_id"),
        "asset_id": response.get("asset_id"),
        "format": response.get("format"),
        "secure_url": response.get("secure_url"),
    }
