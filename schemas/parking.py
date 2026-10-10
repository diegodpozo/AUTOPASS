from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Literal

class VehicleCreate(BaseModel):
    patente: str
    marca_modelo: str
    tipo: Literal["Auto", "Moto", "Camioneta"] = "Auto"

class PlateValidation(BaseModel):
    plate: str
    gate_id: str
    image_base64: Optional[str] = None
    ocr_time: Optional[float] = None

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
    capacidad_camionetas: int = 0
    ocupacion_camionetas: int = 0
    capacidad_reservas_autos: int = 5
    ocupacion_reservas_autos: int = 0
    capacidad_reservas_motos: int = 3
    ocupacion_reservas_motos: int = 0
    capacidad_reservas_camionetas: int = 2
    ocupacion_reservas_camionetas: int = 0
    capacidad_reservas: int = 10
    ocupacion_reservas: int = 0
    disponibilidad: int
    disponibilidad_motos: int
    disponibilidad_camionetas: int = 0
    disponibilidad_reservas_autos: int = 5
    disponibilidad_reservas_motos: int = 3
    disponibilidad_reservas_camionetas: int = 2
    disponibilidad_reservas: int = 10

class FloorBase(BaseModel):
    nombre: str
    capacidad_total: int = 20
    capacidad_motos: int = 10
    capacidad_camionetas: int = 5
    capacidad_reservas_autos: int = 5
    capacidad_reservas_motos: int = 3
    capacidad_reservas_camionetas: int = 2
    capacidad_reservas: int = 10

class FloorCreate(FloorBase):
    pass

class FloorResponse(FloorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int
    ocupacion_actual: int = 0
    ocupacion_motos: int = 0
    capacidad_camionetas: int = 5
    ocupacion_camionetas: int = 0
    capacidad_reservas_autos: int = 5
    ocupacion_reservas_autos: int = 0
    capacidad_reservas_motos: int = 3
    ocupacion_reservas_motos: int = 0
    capacidad_reservas_camionetas: int = 2
    ocupacion_reservas_camionetas: int = 0
    capacidad_reservas: int = 10
    ocupacion_reservas: int = 0

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

class BranchResponse(BranchBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    admin_name: Optional[str] = None
    floors: List[FloorResponse] = []
    # CAMPOS CALCULADOS PARA RESUMEN
    capacidad_autos_total: int = 0
    capacidad_motos_total: int = 0
    capacidad_camionetas_total: int = 0
    capacidad_reservas_autos_total: int = 0
    capacidad_reservas_motos_total: int = 0
    capacidad_reservas_camionetas_total: int = 0
    capacidad_reservas_total: int = 0
    ocupacion_autos_total: int = 0
    ocupacion_motos_total: int = 0
    ocupacion_camionetas_total: int = 0
    ocupacion_reservas_autos_total: int = 0
    ocupacion_reservas_motos_total: int = 0
    ocupacion_reservas_camionetas_total: int = 0
    ocupacion_reservas_total: int = 0
    # TARIFAS POR TIPO DE VEHICULO (None = sin tarifario configurado en la sucursal)
    tarifa_hora: Optional[float] = None
    tarifa_dia: Optional[float] = None
    tarifa_semana: Optional[float] = None
    tarifa_quincena: Optional[float] = None
    tarifa_mes: Optional[float] = None
    tarifa_hora_moto: Optional[float] = None
    tarifa_dia_moto: Optional[float] = None
    tarifa_semana_moto: Optional[float] = None
    tarifa_quincena_moto: Optional[float] = None
    tarifa_mes_moto: Optional[float] = None
    tarifa_hora_camioneta: Optional[float] = None
    tarifa_dia_camioneta: Optional[float] = None
    tarifa_semana_camioneta: Optional[float] = None
    tarifa_quincena_camioneta: Optional[float] = None
    tarifa_mes_camioneta: Optional[float] = None

class BranchPublicResponse(BranchBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ocupacion_actual: int = 0
    capacidad_total: int = 20
    ocupacion_motos: int = 0
    capacidad_motos: int = 10
    ocupacion_camionetas: int = 0
    capacidad_camionetas: int = 5
    ocupacion_reservas_autos: int = 0
    capacidad_reservas_autos: int = 5
    ocupacion_reservas_motos: int = 0
    capacidad_reservas_motos: int = 3
    ocupacion_reservas_camionetas: int = 0
    capacidad_reservas_camionetas: int = 2
    ocupacion_reservas: int = 0
    capacidad_reservas: int = 10
    floors: List[FloorResponse] = []

class CameraBase(BaseModel):
    nombre: str
    tipo: str # 'ENTRADA', 'SALIDA', 'PREDIO', 'PATENTE', 'QR'
    source: str
    activa: bool = True
    sucursal: Optional[str] = None

class CameraCreate(CameraBase):
    pass

class CameraResponse(CameraBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_running: bool = False

