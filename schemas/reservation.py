from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_serializer

from models.types import formatear_fecha
from schemas.types import MoneyAmount

class PriceQuoteInput(BaseModel):
    """Tarifas y cálculo tal como los cotizó el front al crear/editar la reserva.
    El backend revalida horas/total contra su propio cálculo (ver ReservationService)
    y los persiste como foto histórica del precio. Opcionales por compatibilidad."""
    tarifa_hora: Optional[MoneyAmount] = None
    tarifa_fraccion: Optional[MoneyAmount] = None
    tarifa_aplicada: Optional[MoneyAmount] = None
    horas_calculadas: Optional[float] = None
    monto_calculado: Optional[MoneyAmount] = None

class UserReservationCreate(PriceQuoteInput):
    patente: str
    fecha_inicio: datetime
    fecha_fin: datetime
    sucursal_nombre: Optional[str] = "AUTOPASS Central"
    tipo_estadia: Optional[str] = "hora"
    dias_semana: Optional[str] = None

class AdminReservationCreate(PriceQuoteInput):
    user_id: Optional[int] = None
    cliente_nombre: Optional[str] = ""
    patente: str
    fecha_inicio: datetime
    fecha_fin: datetime
    sucursal_nombre: Optional[str] = "AUTOPASS Ituzaingó"
    tipo_estadia: Optional[str] = "hora"
    metodo_pago: Optional[str] = None
    pagar: Optional[bool] = False
    tipo_vehiculo: Optional[str] = "Auto"
    redemption_ticket_id: Optional[int] = None
    cobrar_diferencia_metodo: Optional[str] = None
    reembolsar_diferencia_metodo: Optional[str] = None

class ReservationUpdate(PriceQuoteInput):
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
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
    fecha_inicio: datetime
    fecha_fin: datetime
    tipo_estadia: Optional[str] = "hora"
    dias_semana: Optional[str] = None
    estado_pago: str
    estado_reserva: str
    monto_total: MoneyAmount
    monto_reembolsado: Optional[MoneyAmount] = 0
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
    tarifa_hora: Optional[MoneyAmount] = None
    tarifa_fraccion: Optional[MoneyAmount] = None
    tarifa_aplicada: Optional[MoneyAmount] = None
    horas_calculadas: Optional[float] = None
    monto_calculado: Optional[MoneyAmount] = None
    descuento_pct: Optional[float] = None
    tarifa_fijada_en: Optional[datetime] = None

    @field_serializer("fecha_inicio", "fecha_fin", "tarifa_fijada_en", when_used="json")
    def _serializar_fechas(self, valor):
        return formatear_fecha(valor)
