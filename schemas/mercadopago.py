from pydantic import BaseModel
from typing import Optional, Literal

class MercadoPagoCheckout(BaseModel):
    """SOLICITUD DE CHECKOUT PARA MERCADO PAGO (CHECKOUT PRO)."""
    tipo: Literal["reserva", "estadia"] = "reserva"
    reserva_id: Optional[int] = None
    access_log_id: Optional[int] = None
    redemption_ticket_id: Optional[int] = None   # Descuento % por canje (solo reservas)

class MercadoPagoCheckoutResponse(BaseModel):
    init_point: str
    external_reference: str
    monto: float
    preference_id: str