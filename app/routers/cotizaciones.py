from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import List
import shutil
import os
import uuid
from jose import JWTError, jwt

from .. import models, schemas, auth
from ..database import get_db
from ..auth import SECRET_KEY, ALGORITHM

router = APIRouter(
    prefix="/cotizaciones",
    tags=["Cotizaciones"]
)

# Configuración para que FastAPI sepa de dónde extraer el token
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Carpeta de fotos
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- FUNCIÓN PARA PROTEGER RUTAS ---
def obtener_usuario_actual(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Token inválido"
            )
        return email
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Sesión expirada o inválida"
        )

# --- RUTAS ---

@router.post("/")
def crear_cotizacion(
    cliente_id: str = Form(...),
    descripcion_idea: str = Form(...),
    zona_cuerpo: str = Form(...),
    tamano_cm: str = Form(...),  # <--- ¡CORREGIDO AQUÍ! (str en vez de int)
    es_cover_up: bool = Form(False),
    imagen: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    cliente = db.query(models.Cliente).filter(models.Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")

    nueva_cotizacion = models.Cotizacion(
        cliente_id=cliente.id,
        descripcion_idea=descripcion_idea,
        zona_cuerpo=zona_cuerpo,
        tamano_cm=tamano_cm,
        es_cover_up=es_cover_up
    )
    db.add(nueva_cotizacion)
    db.commit()
    db.refresh(nueva_cotizacion)

    extension = imagen.filename.split(".")[-1]
    nombre_archivo = f"{uuid.uuid4()}.{extension}"
    ruta_archivo = f"{UPLOAD_DIR}/{nombre_archivo}"

    with open(ruta_archivo, "wb") as buffer:
        shutil.copyfileobj(imagen.file, buffer)

    nueva_imagen = models.ImagenReferencia(
        cotizacion_id=nueva_cotizacion.id,
        url_imagen=ruta_archivo
    )
    db.add(nueva_imagen)
    db.commit()

    return {
        "mensaje": "Cotización enviada con éxito",
        "cotizacion_id": nueva_cotizacion.id,
        "imagen_subida": ruta_archivo
    }

# Endpoint protegido: Solo el tatuador logueado puede responder
@router.patch("/{cotizacion_id}/responder")
def responder_cotizacion(
    cotizacion_id: str, 
    precio: float = Form(...), 
    horas: int = Form(...), 
    notas: str = Form(None),
    db: Session = Depends(get_db),
    usuario: str = Depends(obtener_usuario_actual) # SEGURIDAD
):
    cot = db.query(models.Cotizacion).filter(models.Cotizacion.id == cotizacion_id).first()
    if not cot:
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    cot.precio_estimado = precio
    cot.tiempo_estimado_hrs = horas
    cot.notas_tatuador = notas 
    cot.estado = "revisada" 

    db.commit()
    return {"mensaje": "Respuesta enviada y mesa limpia"}

# Endpoint protegido: Solo el tatuador logueado ve la mesa de trabajo
@router.get("/mesa-trabajo")
def obtener_mesa_trabajo(db: Session = Depends(get_db)):
    cotizaciones = db.query(models.Cotizacion).all()
    resultado = []
    
    for cot in cotizaciones:
        # Buscamos la primera imagen asociada a esta cotización en la tabla de imágenes
        imagen = db.query(models.ImagenReferencia).filter(models.ImagenReferencia.cotizacion_id == cot.id).first()
        
        # Extraemos solo el nombre del archivo de la ruta guardada (ej: de "uploads/foto.jpg" a "foto.jpg")
        nombre_archivo = imagen.url_imagen.split("/")[-1] if imagen else None

        resultado.append({
            "id": str(cot.id),
            "cliente": cot.cliente.nombre_completo,
            "telefono": cot.cliente.telefono,
            "idea": cot.descripcion_idea,
            "zona_cuerpo": cot.zona_cuerpo,
            "tamano_cm": cot.tamano_cm,
            "estado": cot.estado,
            # Construimos la URL apuntando a tu servidor local
            "imagen_url": f"http://127.0.0.1:8000/uploads/{nombre_archivo}" if nombre_archivo else None,
            "notas_medicas": cot.cliente.notas_medicas
        })
        
    return resultado