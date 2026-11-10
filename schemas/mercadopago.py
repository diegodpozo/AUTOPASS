from pydantic import BaseModel
from typing import Optional, Literal
from schemas.types import MoneyAmount

class MercadoPagoCheckout(BaseModel):
    """SOLICITUD DE CHECKOUT PARA MERCADO PAGO (CHECKOUT PRO)."""
    tipo: Literal["reserva", "estadia"] = "reserva"
    reserva_id: Optional[int] = None
    access_log_id: Optional[int] = None
    redemption_ticket_id: Optional[int] = None   # Descuento % por canje (solo reservas)

class MercadoPagoCheckoutResponse(BaseModel):
    init_point: str
    external_reference: str
    monto: MoneyAmount
    preference_id: str