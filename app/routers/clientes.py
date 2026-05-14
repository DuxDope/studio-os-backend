from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

# Creamos el router
router = APIRouter(
    prefix="/clientes",
    tags=["Clientes"]
)

# Endpoint para CREAR un cliente (Versión Corregida)
@router.post("/", response_model=schemas.ClienteResponse)
def crear_cliente(cliente: schemas.ClienteCreate, db: Session = Depends(get_db)):
    
    # 1. Buscamos si el correo ya existe
    db_cliente = db.query(models.Cliente).filter(models.Cliente.email == cliente.email).first()
    
    if db_cliente:
        # 2. Si existe, no lanzamos error. Solo actualizamos sus notas/redes y lo devolvemos
        db_cliente.notas_medicas = cliente.notas_medicas
        db.commit()
        db.refresh(db_cliente)
        return db_cliente 
    
    # 3. Si no existe, lo creamos como un cliente nuevo
    nuevo_cliente = models.Cliente(**cliente.model_dump())
    db.add(nuevo_cliente)
    db.commit()
    db.refresh(nuevo_cliente)
    return nuevo_cliente

# (Aquí puedes agregar tu Endpoint para OBTENER todos los clientes más adelante si lo necesitas)