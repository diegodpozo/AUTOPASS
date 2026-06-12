from pydantic import BaseModel
from typing import Optional, List

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
    capacidad_motos: int
    ocupacion_motos: int
    disponibilidad: int
    disponibilidad_motos: int

class FloorBase(BaseModel):
    nombre: str
    capacidad_total: int = 20
    capacidad_motos: int = 10

class FloorCreate(FloorBase):
    pass

class FloorResponse(FloorBase):
    id: int
    branch_id: int
    ocupacion_actual: int = 0
    ocupacion_motos: int = 0

    class Config:
        from_attributes = True

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
    floors: List[FloorResponse] = []
    # Campos calculados para resumen
    capacidad_autos_total: int = 0
    capacidad_motos_total: int = 0
    ocupacion_autos_total: int = 0
    ocupacion_motos_total: int = 0

    class Config:
        from_attributes = True

class BranchPublicResponse(BranchBase):
    id: int
    ocupacion_actual: int = 0
    capacidad_total: int = 20
    ocupacion_motos: int = 0
    capacidad_motos: int = 10
    floors: List[FloorResponse] = []

    class Config:
        from_attributes = True
