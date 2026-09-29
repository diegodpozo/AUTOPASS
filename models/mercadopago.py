from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from core.database import Base

class MercadoPagoPayment(Base):
    """REGISTRO DE INTENCIONES Y CONFIRMACIONES DE PAGO MERCADO PAGO (CHECKOUT PRO)."""
    __tablename__ = "mercadopago_payments"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tipo = Column(String, nullable=False)          # 'reserva' | 'estadia'
    reserva_id = Column(Integer, ForeignKey("reservations.id"), nullable=True)
    access_log_id = Column(Integer, ForeignKey("access_logs.id"), nullable=True)
    redemption_ticket_id = Column(Integer, nullable=True)   # Descuento % por canje (solo reservas)
    patente = Column(String, nullable=True)
    monto = Column(Float, nullable=False)
    moneda = Column(String, default="ARS")

    external_reference = Column(String, unique=True, index=True, nullable=True)
    preference_id = Column(String, nullable=True)
    payment_id = Column(String, nullable=True)

    estado = Column(String, default="PENDIENTE")   # PENDIENTE | APROBADO | FALLIDO | CANCELADO
    mp_status = Column(String, nullable=True)      # status crudo reportado por Mercado Pago

    fecha_creacion = Column(String, nullable=True)
    fecha_confirmacion = Column(String, nullable=True)

    user = relationship("User")
    reservation = relationship("Reservation")
    access_log = relationship("AccessLog")

    @property
    def aplicado(self) -> bool:
        return self.estado == "APROBADO"