# app/services/cloudinary_service.py

from datetime import datetime
from zoneinfo import ZoneInfo

import cloudinary
import cloudinary.uploader


def upload_factura(file_bytes, filename: str):
    """
	Sube a Cloudinary organizando por año/mes
	"""

    peru_tz = ZoneInfo("America/Lima")
	now = datetime.now(peru_tz)
	
	year = now.strftime("%Y")
	mont = now.strftime("%m")
	folder_path = f"facturas/{year}/{month}"

    response = cloudinary.uploader.upload(
        file_bytes,
        folder=folder_path,
        resource_type="image",
        type="authenticated",
        use_filename=True,
        unique_filename=True,
    )

    return {
        "secure_url": response.get("secure_url"),
		"public_id": response.get("public_id"),
		"folder": folder_path,
		"original_filename": filename,
		"upload_date": now.isoformat()
    }