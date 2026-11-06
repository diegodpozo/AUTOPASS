from sqlalchemy import Column, Integer, String, Float, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from core.database import Base
from models.types import DateTimeValue, MoneyValue

class MercadoPagoPayment(Base):
    """REGISTRO DE INTENCIONES Y CONFIRMACIONES DE PAGO MERCADO PAGO (CHECKOUT PRO)."""
    __tablename__ = "mercadopago_payments"
    __table_args__ = (
        CheckConstraint("COALESCE(monto, 0) >= 0", name="ck_mercadopago_payments_monto_nonneg"),
    )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    tipo = Column(String, nullable=False)          # 'reserva' | 'estadia'
    reserva_id = Column(Integer, ForeignKey("reservations.id"), nullable=True)
    access_log_id = Column(Integer, ForeignKey("access_logs.id"), nullable=True)
    redemption_ticket_id = Column(Integer, nullable=True)   # Descuento % por canje (solo reservas)
    patente = Column(String, nullable=True)
    monto = Column(MoneyValue, nullable=False)
    moneda = Column(String, default="ARS")

    external_reference = Column(String, unique=True, index=True, nullable=True)
    preference_id = Column(String, nullable=True)
    # CLAVE DE IDEMPOTENCIA (FASE 5): Mercado Pago reintenta los webhooks, por lo que
    # el mismo pago puede llegar varias veces. `payment_id` es el id del pago en MP y
    # UNICO a nivel de base: un segundo intento de aplicar el mismo pago choca con el
    # indice en vez de acreditar dos veces. "Sin id de MP todavia" se guarda como NULL
    # (no ''): varios NULL NO colisionan en un indice unico, asi que los pagos
    # pendientes conviven sin romper.
    payment_id = Column(String, nullable=True, unique=True, index=True)

    estado = Column(String, default="PENDIENTE")   # PENDIENTE | APROBADO | FALLIDO | CANCELADO
    mp_status = Column(String, nullable=True)      # status crudo reportado por Mercado Pago

    fecha_creacion = Column(DateTimeValue, nullable=True)
    fecha_confirmacion = Column(DateTimeValue, nullable=True)

    user = relationship("User")
    reservation = relationship("Reservation")
    access_log = relationship("AccessLog")

    @property
    def aplicado(self) -> bool:
        return self.estado == "APROBADO"