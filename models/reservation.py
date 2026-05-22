from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.database import Base

class Reservation(Base):
    """Registro de estadías programadas o recurrentes."""
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patente = Column(String)
    fecha_inicio = Column(String)
    fecha_fin = Column(String)
    dias_semana = Column(String, nullable=True) # Almacenamiento serializado: "0,1,2" (0=Lunes...)
    monto_total = Column(Float)
    mp_preference_id = Column(String, nullable=True) # ID de integración con Mercado Pago
    estado_pago = Column(String, default="Pendiente")
    estado_reserva = Column(String, default="Pendiente")
    sucursal_nombre = Column(String, nullable=True)
    sucursal_info = Column(String, nullable=True)
    tipo_estadia = Column(String, default="hora")
    cliente_nombre = Column(String, nullable=True)

    user = relationship("User", back_populates="reservations")
    access_logs = relationship("AccessLog", back_populates="reservation")

class Coupon(Base):
    """Gestión de cupones de descuento para reservas."""
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    descuento_porcentaje = Column(Integer)
    fecha_expiracion = Column(String)
    activo = Column(Boolean, default=True)
