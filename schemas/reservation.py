from pydantic import BaseModel
from typing import Optional

class ReservationCreate(BaseModel):
    user_id: int
    patente: str
    start_time: str
    duration_hours: int
    coupon_code: Optional[str] = None

class UserReservationCreate(BaseModel):
    patente: str
    fecha_inicio: str
    fecha_fin: str
    sucursal_nombre: Optional[str] = "AUTOPASS Central"
    tipo_estadia: Optional[str] = "hora"
    dias_semana: Optional[str] = None

class AdminReservationCreate(BaseModel):
    user_id: Optional[int] = None
    cliente_nombre: Optional[str] = ""
    patente: str
    fecha_inicio: str
    fecha_fin: str
    sucursal_nombre: Optional[str] = "AUTOPASS Ituzaingó"
    tipo_estadia: Optional[str] = "hora"

class ReservationUpdate(BaseModel):
    fecha_inicio: Optional[str] = None
    fecha_fin: Optional[str] = None
    patente: Optional[str] = None
    tipo_estadia: Optional[str] = None
    sucursal_nombre: Optional[str] = None

class UserReservationResponse(BaseModel):
    id: int
    patente: str
    fecha_inicio: str
    fecha_fin: str
    tipo_estadia: Optional[str] = "hora"
    dias_semana: Optional[str] = None
    estado_pago: str
    estado_reserva: str
    monto_total: float
    sucursal_nombre: Optional[str] = None
    sucursal_info: Optional[str] = None
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    usuario_nombre: Optional[str] = None
    usuario_apellido: Optional[str] = None

    class Config:
        from_attributes = True
