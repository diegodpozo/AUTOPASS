from pydantic import BaseModel, ConfigDict
from typing import Optional

class PriceQuoteInput(BaseModel):
    """Tarifas y cálculo tal como los cotizó el front al crear/editar la reserva.
    El backend revalida horas/total contra su propio cálculo (ver ReservationService)
    y los persiste como foto histórica del precio. Opcionales por compatibilidad."""
    tarifa_hora: Optional[float] = None
    tarifa_fraccion: Optional[float] = None
    tarifa_aplicada: Optional[float] = None
    horas_calculadas: Optional[float] = None
    monto_calculado: Optional[float] = None

class UserReservationCreate(PriceQuoteInput):
    patente: str
    fecha_inicio: str
    fecha_fin: str
    sucursal_nombre: Optional[str] = "AUTOPASS Central"
    tipo_estadia: Optional[str] = "hora"
    dias_semana: Optional[str] = None

class AdminReservationCreate(PriceQuoteInput):
    user_id: Optional[int] = None
    cliente_nombre: Optional[str] = ""
    patente: str
    fecha_inicio: str
    fecha_fin: str
    sucursal_nombre: Optional[str] = "AUTOPASS Ituzaingó"
    tipo_estadia: Optional[str] = "hora"
    metodo_pago: Optional[str] = None
    pagar: Optional[bool] = False
    tipo_vehiculo: Optional[str] = "Auto"
    redemption_ticket_id: Optional[int] = None
    cobrar_diferencia_metodo: Optional[str] = None
    reembolsar_diferencia_metodo: Optional[str] = None

class ReservationUpdate(PriceQuoteInput):
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    patente: Optional[str] = None
    tipo_estadia: Optional[str] = None
    sucursal_nombre: Optional[str] = None
    estado_pago: Optional[str] = None
    estado_reserva: Optional[str] = None
    metodo_pago: Optional[str] = None
    tipo_vehiculo: Optional[str] = None

class ConfirmPaymentRequest(BaseModel):
    metodo_pago: Optional[str] = "Caja"
    redemption_ticket_id: Optional[int] = None

class UserReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    patente: str
    fecha_inicio: str
    fecha_fin: str
    tipo_estadia: Optional[str] = "hora"
    dias_semana: Optional[str] = None
    estado_pago: str
    estado_reserva: str
    monto_total: float
    monto_reembolsado: Optional[float] = 0.0
    sucursal_nombre: Optional[str] = None
    sucursal_info: Optional[str] = None
    metodo_pago: Optional[str] = None
    tipo_vehiculo: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    usuario_nombre: Optional[str] = None
    usuario_apellido: Optional[str] = None
    en_predio: bool = False
    origen: Optional[str] = "cliente"
    # FOTO HISTÓRICA DE TARIFAS (trazabilidad del precio cotizado)
    tarifa_hora: Optional[float] = None
    tarifa_fraccion: Optional[float] = None
    tarifa_aplicada: Optional[float] = None
    horas_calculadas: Optional[float] = None
    monto_calculado: Optional[float] = None
    descuento_pct: Optional[float] = None
    tarifa_fijada_en: Optional[str] = None
