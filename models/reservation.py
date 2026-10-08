from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, CheckConstraint
from sqlalchemy.orm import relationship
from core.database import Base
from models.types import DateTimeAsStr

class Reservation(Base):
    """REGISTRO DE ESTADIAS PROGRAMADAS O RECURRENTES."""
    __tablename__ = "reservations"
    __table_args__ = (
        CheckConstraint("COALESCE(monto_total, 0) >= 0", name="ck_reservations_monto_total_nonneg"),
        CheckConstraint("COALESCE(monto_reembolsado, 0) >= 0", name="ck_reservations_monto_reembolsado_nonneg"),
        CheckConstraint("fecha_inicio IS NULL OR fecha_fin IS NULL OR fecha_fin >= fecha_inicio",
                        name="ck_reservations_orden_fechas"),
    )
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    patente = Column(String, index=True)
    fecha_inicio = Column(DateTimeAsStr)
    fecha_fin = Column(DateTimeAsStr)
    dias_semana = Column(String, nullable=True) # ALMACENAMIENTO SERIALIZADO: "0,1,2" (0=LUNES...)
    monto_total = Column(Float)
    monto_reembolsado = Column(Float, default=0.0)
    fecha_pago = Column(DateTimeAsStr, nullable=True) # FECHA DE LA TRANSACCION (PAGO O REEMBOLSO)
    mp_preference_id = Column(String, nullable=True) # ID DE INTEGRACION CON MERCADO PAGO
    estado_pago = Column(String, default="Pendiente")
    estado_reserva = Column(String, default="Pendiente")
    sucursal_nombre = Column(String, nullable=True, index=True)
    sucursal_info = Column(String, nullable=True)
    tipo_estadia = Column(String, default="hora")
    cliente_nombre = Column(String, nullable=True)
    recordatorio_confirmado = Column(Boolean, default=False)
    metodo_pago = Column(String, nullable=True)  # METODO DE PAGO UTILIZADO (EFECTIVO, TRANSFERENCIA, TARJETA, MP, ETC)
    tipo_vehiculo = Column(String, default="Auto")  # AUTO / MOTO / CAMIONETA
    origen = Column(String, default="cliente")  # 'cliente' (creada por el usuario) o 'manual' (creada por admin/empleado)

    user = relationship("User", back_populates="reservations")
    access_logs = relationship("AccessLog", back_populates="reservation")
