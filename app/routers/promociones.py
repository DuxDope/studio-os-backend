from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import shutil
import uuid
from .. import models
from ..database import get_db

router = APIRouter(
    prefix="/promociones",
    tags=["Promociones / Flashes"]
)

UPLOAD_DIR = "uploads"

# 1. Endpoint para SUBIR un nuevo Flash/Promo (Uso exclusivo del Tatuador)
@router.post("/")
def crear_promocion(
    titulo: str = Form(...),
    descripcion: str = Form(...),
    precio: float = Form(...),
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    # Guardamos la imagen física
    extension = imagen.filename.split(".")[-1]
    nombre_archivo = f"flash_{uuid.uuid4()}.{extension}"
    ruta_archivo = f"{UPLOAD_DIR}/{nombre_archivo}"

    with open(ruta_archivo, "wb") as buffer:
        shutil.copyfileobj(imagen.file, buffer)

    # Creamos el registro en la base de datos
    nueva_promo = models.Promocion(
        titulo=titulo,
        descripcion=descripcion,
        precio=precio,
        url_imagen=ruta_archivo
    )
    db.add(nueva_promo)
    db.commit()
    db.refresh(nueva_promo)

    return {"mensaje": "Promoción creada con éxito", "promo_id": nueva_promo.id}

# 2. Endpoint para MOSTRAR todos los Flashes (Esto lo verá el Cliente en su celular)
@router.get("/")
def listar_promociones_activas(db: Session = Depends(get_db)):
    # Solo mostramos las que están activas
    promos = db.query(models.Promocion).filter(models.Promocion.activa == True).all()
    
    # Le damos formato bonito para el frontend
    resultado = []
    for p in promos:
        resultado.append({
            "id": p.id,
            "titulo": p.titulo,
            "descripcion": p.descripcion,
            "precio": p.precio,
            "imagen_url": f"http://127.0.0.1:8000/{p.url_imagen}"
        })
    return resultado