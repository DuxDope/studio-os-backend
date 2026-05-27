from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from uuid import UUID

# --- ESQUEMAS DE CLIENTE ---

# Base: Lo que comparten la creación y la respuesta
class ClienteBase(BaseModel):
    nombre_completo: str
    telefono: str
    email: EmailStr
    notas_medicas: Optional[str] = None

# Create: Lo que pedimos cuando se registra un cliente nuevo
class ClienteCreate(ClienteBase):
    pass

# Response: Lo que devolvems al frontend (incluye el ID y fecha generados por la DB)
class ClienteResponse(ClienteBase):
    id: UUID
    fecha_registro: datetime

    class Config:
        from_attributes = True # Esto le dice a Pydantic que lea desde modelos SQLAlchemy

# --- ESQUEMAS DE COTIZACIÓN ---

class CotizacionBase(BaseModel):
    descripcion_idea: str
    zona_cuerpo: str
    tamano_cm: str
    es_cover_up: bool = False

class CotizacionCreate(CotizacionBase):
    cliente_id: UUID

class CotizacionResponse(CotizacionBase):
    id: UUID
    cliente_id: UUID
    estado: str
    precio_estimado: Optional[float] = None
    tiempo_estimado_hrs: Optional[int] = None
    fecha_solicitud: datetime

    class Config:
        from_attributes = True

class CitaBase(BaseModel):
    cotizacion_id: str
    fecha_inicio: datetime
    fecha_fin: datetime

class CitaCreate(BaseModel):
    cotizacion_id: str
    fecha_inicio: datetime
    fecha_fin: datetime
    tatuador_id: Optional[int] = None  # <-- AGREGADO
    abono: Optional[int] = None        # <-- AGREGADO

class Cita(CitaBase): # <--- ESTA ES LA QUE FALTA O ESTÁ MAL ESCRITA
    id: str
    tatuador_id: str
    estado: str

    class Config:
        from_attributes = True