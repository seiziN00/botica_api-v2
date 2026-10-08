# app/services/ocr_service.py

import json
from decimal import Decimal
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from app.core.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


# --- Esquema Pydantic para JSON Schema estricto ---

class InvoiceItem(BaseModel):
    producto: str = Field(description="Nombre completo del producto tal como aparece en la factura")
    cantidad: int = Field(ge=1, description="Cantidad comprada, entero mayor o igual a 1")
    laboratorio: str = Field(default="", description="Laboratorio fabricante. Vacío si no aparece")
    lote: str = Field(default="", description="Número de lote. Vacío si no aparece")
    vencimiento: str = Field(
        default="",
        description="Fecha de vencimiento SIEMPRE en formato DD-MM-YYYY. "
                    "Si viene como YYYY-MM, convertir al último día del mes. "
                    "Vacío si no aparece."
    )
    unidad: str = Field(
        default="UND",
        description="Unidad de medida en mayúsculas (TABLETA, CÁPSULA, SOBRE, FRASCO, TUBO, CAJA, AMPOLLA, UND). "
                    "Default: UND si no aparece"
    )
    precio_unitario: Decimal = Field(default=Decimal("0"), ge=0, description="Precio por unidad. 0 si no aparece")
    precio_total: Decimal = Field(default=Decimal("0"), ge=0, description="Precio total del ítem. 0 si no aparece")


class InvoiceOCRResponse(BaseModel):
    items: list[InvoiceItem] = Field(description="Lista de todos los productos extraídos de la(s) factura(s)")


PROMPT = """Analiza la(s) imagen(es) adjunta(s): son fotografías de una factura o boleta de compra \
de una botica (farmacia) peruana. Las imágenes pueden ser páginas del mismo comprobante.

Extrae TODOS los ítems de productos de la(s) tabla(s). Omite filas de subtotal, IGV, total \
y columnas de CÓDIGO o PESO si aparecen.

Devuelve ÚNICAMENTE un JSON válido, sin markdown, sin comentarios, toma esta estructura de ejemplo:
{
    "items": [
        {
            "producto": "AZITROMICINA 200MG/5ML PPS x 30ML",
            "cantidad": 6,
            "laboratorio": "PORTUGAL",
            "lote": "2057806",
            "vencimiento": "2029-05",
            "unidad": "FRASCO",
            "precio_unitario": 6.16,
            "precio_total": 36.96
        }
    ]
}

Reglas críticas:
- "vencimiento": SIEMPRE devolver en formato DD-MM-YYYY. Si la fuente es YYYY-MM o MM-YYYY, usa el último día de ese mes.
- Si un dato de texto no aparece, usa "". Si un precio no aparece, usa 0.
- "cantidad" debe ser entero >= 1.
- "unidad" siempre en mayúsculas. Si no aparece, usa "UND".
- No inventes datos que no estén visibles en la imagen."""


def extract_invoice_with_ocr(image_urls: list[str]) -> dict:
    if not image_urls:
        raise ValueError("Se requiere al menos una URL de imagen")
    if len(image_urls) > 4:
        raise ValueError(f"Máximo 4 imágenes permitidas, recibidas: {len(image_urls)}")

    content_blocks: list[dict] = [{"type": "text", "text": PROMPT}]
    for url in image_urls:
        content_blocks.append({
            "type": "image_url",
            "image_url": {"url": url}
        })

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un sistema de OCR especializado en facturas de farmacias peruanas. "
                    "Extrae únicamente información visible. No inventes datos."
                ),
            },
            {
                "role": "user",
                "content": content_blocks,
            },
        ],
        "reasoning": {"enabled": False},
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "invoice_ocr",
                "strict": True,
                "schema": InvoiceOCRResponse.model_json_schema(),
            },
        },
        "temperature": 0,
    }

    with httpx.Client(timeout=120) as client:
        response = client.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

    data = response.json()
    raw_content = data["choices"][0]["message"]["content"]
    parsed = json.loads(raw_content)
    validated = InvoiceOCRResponse.model_validate(parsed)

    return validated.model_dump()