from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UsuarioModel
from app.schemas import UsuarioCrear, UsuarioRespuesta
from app.security import get_password_hash

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

@router.post("/", response_model=UsuarioRespuesta, status_code=201)
def crear_usuario(usuario: UsuarioCrear, db: Session = Depends(get_db)):
    # 1. Verificar si el email ya existe
    db_user = db.query(UsuarioModel).filter(UsuarioModel.email == usuario.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    # 2. Hashear la contraseña antes de guardarla
    hashed_password = get_password_hash(usuario.password)

    # 3. Crear el nuevo usuario
    nuevo_usuario = UsuarioModel(
        nombre=usuario.nombre,
        email=usuario.email,
        password_hash=hashed_password,
        is_active=True
    )
    
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    
    return nuevo_usuario