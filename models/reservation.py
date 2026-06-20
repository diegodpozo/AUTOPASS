from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from core.database import Base

class Reservation(Base):
    """REGISTRO DE ESTADIAS PROGRAMADAS O RECURRENTES."""
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    patente = Column(String)
    fecha_inicio = Column(String)
    fecha_fin = Column(String)
    dias_semana = Column(String, nullable=True) # ALMACENAMIENTO SERIALIZADO: "0,1,2" (0=LUNES...)
    monto_total = Column(Float)
    monto_reembolsado = Column(Float, default=0.0)
    fecha_pago = Column(String, nullable=True) # FECHA DE LA TRANSACCION (PAGO O REEMBOLSO)
    mp_preference_id = Column(String, nullable=True) # ID DE INTEGRACION CON MERCADO PAGO
    estado_pago = Column(String, default="Pendiente")
    estado_reserva = Column(String, default="Pendiente")
    sucursal_nombre = Column(String, nullable=True)
    sucursal_info = Column(String, nullable=True)
    tipo_estadia = Column(String, default="hora")
    cliente_nombre = Column(String, nullable=True)

    user = relationship("User", back_populates="reservations")
    access_logs = relationship("AccessLog", back_populates="reservation")

class Coupon(Base):
    """GESTION DE CUPONES DE DESCUENTO PARA RESERVAS."""
    __tablename__ = "coupons"
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String, unique=True, index=True)
    descuento_porcentaje = Column(Integer)
    fecha_expiracion = Column(String)
    activo = Column(Boolean, default=True)
