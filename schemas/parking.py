from pydantic import BaseModel
from typing import Optional

class PlateValidation(BaseModel):
    plate: str
    gate_id: str
    image_base64: Optional[str] = None

class QRValidation(BaseModel):
    qr_data: str
    gate_id: str

class AccessResponse(BaseModel):
    status: str
    action: Optional[str] = None
    message: str

class ParkingStatus(BaseModel):
    capacidad_total: int
    ocupacion_actual: int
    disponibilidad: int
