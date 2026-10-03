from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select

from app.database import get_db
from app.models import LoteModel, ProductoModel
from app.schemas import LoteCrear, LoteActualizar, LoteRespuesta

router = APIRouter(
    prefix="/lotes",
    tags=["Lotes"],
)

# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
# @@ LISTAR LOTES DE UN PRODUCTO @@
# @@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@router.get("/producto/{producto_id}", response_model=list[LoteRespuesta])
def listar_lotes_por_producto(producto_id: int, session: Session = Depends(get_db)):
    producto = session.get(ProductoModel, producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    lotes = session.exec(
        select(LoteModel).where(LoteModel.producto_id == producto_id)
    ).all()
    
    return lotes


# @@@@@@@@@@@
# @@ CREAR @@
# @@@@@@@@@@@
@router.post("", response_model=LoteRespuesta, status_code=201)
def crear_lote(lote: LoteCrear, session: Session = Depends(get_db)):
    producto = session.get(ProductoModel, lote.producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="El producto asociado no existe")
    
    nuevo_lote = LoteModel(**lote.model_dump())
    session.add(nuevo_lote)
    session.commit()
    session.refresh(nuevo_lote)
    
    return nuevo_lote


# @@@@@@@@@@@@
# @@ EDITAR @@
# @@@@@@@@@@@@
@router.put("/{lote_id}", response_model=LoteRespuesta)
def actualizar_lote(
    lote_id: int,
    lote_data: LoteActualizar,
    session: Session = Depends(get_db)
):
    lote = session.get(LoteModel, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    # Actualizar solo los campos enviados en el schema
    datos_actualizacion = lote_data.model_dump(exclude_unset=True)
    for key, value in datos_actualizacion.items():
        setattr(lote, key, value)

    session.commit()
    session.refresh(lote)
    
    return lote


# @@@@@@@@@@@@@@
# @@ ELIMINAR @@
# @@@@@@@@@@@@@@
@router.delete("/{lote_id}", status_code=204)
def eliminar_lote(lote_id: int, session: Session = Depends(get_db)):
    lote = session.get(LoteModel, lote_id)
    if not lote:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    
    session.delete(lote)
    session.commit()
    
    return None