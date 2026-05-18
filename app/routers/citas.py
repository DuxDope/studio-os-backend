from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid
from .. import models, schemas, auth, database
from .cotizaciones import obtener_usuario_actual
from ..database import get_db
from pydantic import BaseModel
from datetime import timedelta, datetime

router = APIRouter(prefix="/citas", tags=["Agenda"])

# ¡Ojo aquí! Le quitamos el response_model=schemas.Cita de la línea de @router
@router.post("/")
def crear_cita(cita: schemas.CitaCreate, db: Session = Depends(get_db)):
    print(f"📅 Intentando agendar cita para cotización: {cita.cotizacion_id}")
    
    # Verificamos que la cotización exista
    cotizacion = db.query(models.Cotizacion).filter(models.Cotizacion.id == cita.cotizacion_id).first()
    if not cotizacion:
        print("❌ Error: La cotización no existe en la DB")
        raise HTTPException(status_code=404, detail="Cotización no encontrada")

    # Creamos la cita (Sin tatuador_id para evitar problemas)
    nueva_cita = models.Cita(
        cotizacion_id=cita.cotizacion_id,
        fecha_inicio=cita.fecha_inicio,
        fecha_fin=cita.fecha_fin, 
        estado="programada"
    )
    
    try:
        db.add(nueva_cita)
        # Cambiamos el estado de la cotización para que desaparezca de las pendientes
        cotizacion.estado = "agendada" 
        db.commit()
        
        print("✅ Cita agendada con éxito en Neon")
        
        # ¡ESTA ES LA MAGIA! 
        # En vez de devolver el objeto, devolvemos un simple mensaje.
        # Así evitamos el error de validación de FastAPI.
        return {"mensaje": "Cita agendada exitosamente"}
        
    except Exception as e:
        db.rollback()
        print(f"❌ Error de base de datos: {str(e)}")
        raise HTTPException(status_code=400, detail="Error al guardar la cita")
    
@router.get("/mis-citas")
def obtener_mis_citas(
    db: Session = Depends(database.get_db),
    email_tatuador: str = Depends(obtener_usuario_actual)
):
    tatuador = db.query(models.Usuario).filter(models.Usuario.email == email_tatuador).first()
    
    # Traemos todas las citas
    citas = db.query(models.Cita).all()
    
    resultado = []
    for c in citas:
        # PARCHE DE ZONA HORARIA: 
        # Si la base de datos te devuelve la hora en UTC, le restamos 4 horas 
        # para que en el calendario de Chile se vea en el día y hora correcto.
        hora_local = c.fecha_inicio - timedelta(hours=4)
        
        url_imagen = c.cotizacion.imagenes[0].url_imagen if c.cotizacion.imagenes else None
        
        resultado.append({
            "id": str(c.id),
            "fecha_inicio": hora_local.isoformat(), # Enviamos la hora ya ajustada
            "estado": c.estado,
            "cotizacion": {
                "cliente": c.cotizacion.cliente.nombre_completo,
                "idea": c.cotizacion.descripcion_idea,
                "zona_cuerpo": c.cotizacion.zona_cuerpo,
                "tamano_cm": c.cotizacion.tamano_cm,
                "imagen_url": url_imagen
            }
        })
    
    return resultado


# -------------------------------------------------------------------
# MOTOR DE RESERVAS: PORTAL DEL CLIENTE (MAGIC LINKS)
# -------------------------------------------------------------------

@router.get("/disponibilidad/{fecha}")
def obtener_disponibilidad(fecha: str, db: Session = Depends(database.get_db)):
    """
    Algoritmo de colisión: Busca espacios de 3 horas libres entre las 11:00 y las 21:00
    """
    # 1. Convertimos la fecha que manda React a objeto Date
    fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
    
    # 2. Traemos todas las citas y extraemos solo las del día solicitado
    citas_db = db.query(models.Cita).all()
    citas_del_dia = []
    
    for c in citas_db:
        # Usamos tu parche de zona horaria para leer la hora correcta de Chile
        hora_local_inicio = c.fecha_inicio - timedelta(hours=4) 
        hora_local_fin = c.fecha_fin - timedelta(hours=4)
        
        if hora_local_inicio.date() == fecha_obj:
            citas_del_dia.append({
                "inicio": hora_local_inicio,
                "fin": hora_local_fin
            })

    # 3. Rango de trabajo: 11 a 18 (para que el último de 3hrs termine a las 21)
    horas_posibles = [11, 12, 13, 14, 15, 16, 17, 18]
    horas_libres = []

    for hora in horas_posibles:
        # Calculamos el inicio y el fin del bloque propuesto (Ej: 14:00 a 17:00)
        inicio_propuesto = datetime.combine(fecha_obj, datetime.min.time()) + timedelta(hours=hora)
        fin_propuesto = inicio_propuesto + timedelta(hours=3)
        
        choque = False
        for cita in citas_del_dia:
            # ALGORITMO DE COLISIÓN MATEMÁTICA:
            # Hay choque si el inicio propuesto es ANTES del fin de otra cita,
            # Y el fin propuesto es DESPUÉS del inicio de esa misma cita.
            if inicio_propuesto < cita["fin"] and fin_propuesto > cita["inicio"]:
                choque = True
                break
        
        # Si pasó el filtro sin chocar, habilitamos la hora para el cliente
        if not choque:
            horas_libres.append(f"{hora:02d}:00")

    return {"fecha": fecha, "horas_disponibles": horas_libres}


@router.get("/portal-cliente/{cotizacion_id}")
def ver_cotizacion_cliente(cotizacion_id: str, db: Session = Depends(database.get_db)):
    """
    Permite al cliente leer su propia cotización usando su Link Único sin iniciar sesión.
    """
    cotizacion = db.query(models.Cotizacion).filter(models.Cotizacion.id == cotizacion_id).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="El link es inválido o expiró.")
        
    url_imagen = cotizacion.imagenes[0].url_imagen if cotizacion.imagenes else None
    
    # Devolvemos solo la info segura para el cliente (sin revelar datos del estudio)
    return {
        "id": str(cotizacion.id),
        "cliente": cotizacion.cliente.nombre_completo,
        "idea": cotizacion.descripcion_idea,
        "zona_cuerpo": cotizacion.zona_cuerpo,
        "tamano_cm": cotizacion.tamano_cm,
        "precio_estimado": cotizacion.precio_estimado,
        "tiempo_estimado_hrs": cotizacion.tiempo_estimado_hrs or 3, # 3 por defecto
        "imagen_url": url_imagen,
        "estado": cotizacion.estado
    }

# Esquema para recibir los nuevos datos
class CitaReprogramar(BaseModel):
    fecha_inicio: str
    fecha_fin: str

@router.put("/{cita_id}")
def reprogramar_cita(cita_id: str, datos: CitaReprogramar, db: Session = Depends(database.get_db)):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    
    # Limpiamos la "Z" del formato de JavaScript para que Python lo lea sin errores
    inicio_str = datos.fecha_inicio.replace("Z", "")
    fin_str = datos.fecha_fin.replace("Z", "")
    
    cita.fecha_inicio = datetime.fromisoformat(inicio_str)
    cita.fecha_fin = datetime.fromisoformat(fin_str)
    
    db.commit()
    return {"mensaje": "Cita reprogramada con éxito"}

@router.delete("/{cita_id}")
def eliminar_cita(cita_id: str, db: Session = Depends(database.get_db)):
    cita = db.query(models.Cita).filter(models.Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Borramos la cita de la base de datos
    db.delete(cita)
    
    # Opcional: Devolvemos la cotización a estado 'revisada' por si quieres volver a agendarla luego
    if cita.cotizacion:
        cita.cotizacion.estado = "revisada"
        
    db.commit()
    return {"mensaje": "Cita eliminada correctamente"}

@router.patch("/{cita_id}/completar")
def completar_cita(cita_id: int, db: Session = Depends(get_db)):
    # Buscar la cita
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Cambiar el estado de la cotización asociada
    if cita.cotizacion:
        cita.cotizacion.estado = "completada"
    
    db.commit()
    
    # Preparar el mensaje de WhatsApp
    cliente_nombre = cita.cotizacion.cliente if cita.cotizacion else "Cliente"
    telefono = cita.cotizacion.telefono if cita.cotizacion else ""
    
    texto_cuidados = (
        f"¡Hola {cliente_nombre}! 🔥 Qué tremenda sesión la de hoy. "
        f"Para que tu tatuaje cure perfecto, recuerda seguir estos cuidados:\n\n"
        f"1. 🧼 Retira el parche en 2-3 horas y lava con jabón neutro y agua tibia.\n"
        f"2. 🧴 Aplica una capa delgada de crema cicatrizante 3 veces al día.\n"
        f"3. ☀️ NO lo expongas al sol directo, piscinas, playa o sauna por al menos 15 días.\n"
        f"4. 🚫 No rasques ni arranques las cáscaras.\n\n"
        f"Cualquier duda me avisas. ¡Gracias por la confianza!"
    )
    
    return {"status": "success", "telefono": telefono, "texto_cuidados": texto_cuidados} 