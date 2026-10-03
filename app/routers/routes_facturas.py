from datetime import datetime
from zoneinfo import ZoneInfo


@router.post(
    "/facturas/procesar-ocr",
    status_code=status.HTTP_202_ACCEPTED,
)
def procesar_factura_ocr(
    background_tasks: BackgroundTasks,
    file: UploadFile,
    current_user: Usuario = Depends(
        require_min_role(RolEnum.STAFF)
    ),
    session: Session = Depends(get_session),
):

    if file.content_type not in {
        "image/jpeg",
        "image/png",
        "image/webp",
    }:
        raise HTTPException(
            status_code=400,
            detail="Formato no permitido",
        )

    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > 12 * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail="La imagen supera 12 MB",
        )

    sha256 = calculate_sha256(file.file)

    now = datetime.now(ZoneInfo("America/Lima"))

    upload_result = upload_factura(
        file.file,
        year=now.year,
        month=now.month,
    )

    factura = Factura(
        estado=FacturaEstado.PROCESANDO,
        nombre_archivo=file.filename or "factura",
        cloudinary_public_id=upload_result["public_id"],
        cloudinary_asset_id=upload_result["asset_id"],
        cloudinary_format=upload_result["format"],
        sha256=sha256,
        mime_type=file.content_type,
        creada_por_id=current_user.id,
        created_at=datetime.now(timezone.utc),
    )

    session.add(factura)
    session.commit()
    session.refresh(factura)

    background_tasks.add_task(
        procesar_factura_ocr_background,
        factura.id,
    )

    return {
        "id": factura.id,
        "estado": factura.estado,
        "mensaje": "Factura recibida y enviada a procesamiento",
    }