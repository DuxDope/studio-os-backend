import uuid
from sqlalchemy import Column, String, Integer, Boolean, Numeric, ForeignKey, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class Cliente(Base):
    __tablename__ = "clientes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nombre_completo = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    notas_medicas = Column(String, nullable=True)
    fecha_registro = Column(DateTime, default=datetime.utcnow)
    saldo_abono = Column(Integer, default=0, nullable=False)
    abono_movimientos = relationship("AbonoMovimiento", back_populates="cliente")

    # Relación 1 a N: Un cliente puede tener muchas cotizaciones
    cotizaciones = relationship("Cotizacion", back_populates="cliente")
    abono_movimientos = relationship("AbonoMovimiento", back_populates="cliente")

class Cotizacion(Base):
    __tablename__ = "cotizaciones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"))
    descripcion_idea = Column(String, nullable=False)
    zona_cuerpo = Column(String, nullable=False)
    tamano_cm = Column(String, nullable=False)
    es_cover_up = Column(Boolean, default=False)
    estado = Column(String, default="pendiente") # pendiente, revisada, agendada
    precio_estimado = Column(Numeric(10, 2), nullable=True)
    tiempo_estimado_hrs = Column(Integer, nullable=True)
    fecha_solicitud = Column(DateTime, default=datetime.utcnow)

    # Relaciones
    cliente = relationship("Cliente", back_populates="cotizaciones")
    imagenes = relationship("ImagenReferencia", back_populates="cotizacion")
    cita = relationship("Cita", back_populates="cotizacion", uselist=False)

class ImagenReferencia(Base):
    __tablename__ = "imagenes_referencia"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cotizacion_id = Column(UUID(as_uuid=True), ForeignKey("cotizaciones.id"))
    url_imagen = Column(String, nullable=False)

    # Relaciones
    cotizacion = relationship("Cotizacion", back_populates="imagenes")

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(String, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    nombre = Column(String)
    password_hashed = Column(String)
    activo = Column(Boolean, default=True)

class Cita(Base):
    __tablename__ = "citas"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    cotizacion_id = Column(UUID(as_uuid=True), ForeignKey("cotizaciones.id"))
    tatuador_id = Column(String, ForeignKey("usuarios.id"), nullable=True)
    fecha_inicio = Column(DateTime, nullable=False)
    fecha_fin = Column(DateTime, nullable=False)
    estado = Column(String, default="programada")

    # Relaciones
    cotizacion = relationship("Cotizacion", back_populates="cita")


# --- TABLAS DE CONTENIDO (LANDING PAGE) ---

class Promocion(Base):
    __tablename__ = "promociones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    titulo = Column(String, index=True)
    descripcion = Column(String)
    precio = Column(Numeric(10, 2))
    url_imagen = Column(String, nullable=True)
    activa = Column(Boolean, default=True)

class Galeria(Base):
    __tablename__ = "galeria"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    url_imagen = Column(String)
    titulo = Column(String, nullable=True)

class AbonoMovimiento(Base):
    __tablename__ = "abono_movimientos"

    id = Column(Integer, primary_key=True, index=True)
    # ¡Aquí está el cambio clave!
    cliente_id = Column(UUID(as_uuid=True), ForeignKey("clientes.id"), nullable=False)
    monto = Column(Integer, nullable=False)
    tipo = Column(String(20), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha = Column(DateTime, default=datetime.utcnow)

    cliente = relationship("Cliente", back_populates="abono_movimientos")