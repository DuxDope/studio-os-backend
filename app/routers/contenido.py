import cloudinary.uploader
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db

# Importamos tu función de seguridad desde el archivo de cotizaciones (o de donde la tengas en auth)
from .cotizaciones import obtener_usuario_actual 

router = APIRouter(prefix="/contenido", tags=["contenido"])

# --- RUTAS DE CONTENIDO ---

# 1. PÚBLICO: Cualquier persona puede ver esto para la Landing Page
@router.get("/publico")
def obtener_contenido_publico(db: Session = Depends(get_db)):
    promos = db.query(models.Promocion).filter(models.Promocion.activa == True).all()
    galeria = db.query(models.Galeria).all()
    return {"promociones": promos, "galeria": galeria}

# 2. PRIVADO: Solo el tatuador logueado puede subir fotos a su portafolio
@router.post("/galeria")
def subir_a_galeria(
    imagen: UploadFile = File(...), 
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_usuario_actual)  # <--- CANDADO DE SEGURIDAD
):
    res = cloudinary.uploader.upload(imagen.file)
    nuevo_trabajo = models.Galeria(url_imagen=res.get("secure_url"))
    db.add(nuevo_trabajo)
    db.commit()
    return {"mensaje": "Foto agregada a la galería"}

# 3. PRIVADO: Solo el tatuador puede prender/apagar sus promos
@router.patch("/promociones/{promo_id}/toggle")
def toggle_promocion(
    promo_id: str, 
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_usuario_actual)  # <--- CANDADO DE SEGURIDAD
):
    promo = db.query(models.Promocion).filter(models.Promocion.id == promo_id).first()
    if not promo:
        raise HTTPException(status_code=404, detail="Promoción no encontrada")
        
    promo.activa = not promo.activa
    db.commit()
    return {"estado": promo.activa}

# 4. PRIVADO: Para que el tatuador pueda crear promos nuevas desde su panel
@router.post("/promociones")
def crear_promocion(
    titulo: str = Form(...),
    descripcion: str = Form(...),
    precio: str = Form(...),
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_usuario_actual)  # <--- CANDADO DE SEGURIDAD
):
    nueva_promo = models.Promocion(titulo=titulo, descripcion=descripcion, precio=precio)
    db.add(nueva_promo)
    db.commit()
    return {"mensaje": "Promoción creada exitosamente"}