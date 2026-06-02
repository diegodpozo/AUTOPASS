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

class BranchBase(BaseModel):
    nombre: str
    direccion: str
    telefono: str
    horario: str
    is_24h: bool = False
    logo_url: Optional[str] = None
    activa: bool = True
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class BranchCreate(BranchBase):
    pass

class BranchResponse(BranchBase):
    id: int
    admin_name: Optional[str] = None

    class Config:
        from_attributes = True
