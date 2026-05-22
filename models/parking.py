from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.database import Base

class ParkingAforo(Base):
    """Control de capacidad y ocupación en tiempo real."""
    __tablename__ = "parking_aforo"
    id = Column(Integer, primary_key=True, index=True)
    capacidad_total = Column(Integer, default=20)
    ocupacion_actual = Column(Integer, default=0)
    ultima_actualizacion = Column(String)
    sucursal = Column(String, unique=True, nullable=True)

class Settings(Base):
    """Configuraciones globales del sistema (precios, parámetros)."""
    __tablename__ = "settings"
    id = Column(Integer, primary_key=True, index=True)
    clave = Column(String) # Removido unique=True para permitir variantes por sede
    valor = Column(Float)
    sucursal = Column(String, nullable=True) # None = Configuración Global

class AccessLog(Base):
    """Auditoría visual y cronológica de accesos (ALPR)."""
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    patente_detectada = Column(String)
    tipo_evento = Column(String) # 'ENTRADA' o 'SALIDA'
    reserva_id = Column(Integer, ForeignKey("reservations.id"), nullable=True)
    fecha_hora = Column(String)
    fecha_pago = Column(String, nullable=True) # Nueva columna para reportes financieros
    imagen_path = Column(String, nullable=True)
    pago_confirmado = Column(Boolean, default=False)
    costo_estadia = Column(Float, default=0.0)
    sucursal = Column(String, nullable=True)

    reservation = relationship("Reservation", back_populates="access_logs")
