from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Optional
from schemas.validators import validate_password_strength, validate_dni_digits, validate_phone_digits, validate_email_format

class UserBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    nombre: str
    apellido: str
    dni: str
    telefono: str
    email: str
    rol: Optional[str] = "user"
    sucursal: Optional[str] = None
    direccion: Optional[str] = None
    puntos_acumulados: Optional[int] = 0
    saldo: Optional[float] = 0.0
    is_blocked: Optional[bool] = False

    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v):
        return validate_phone_digits(v)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_format(v)

class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None

    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v):
        return validate_phone_digits(v)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_format(v)

class UserAdminUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    sucursal: Optional[str] = None
    rol: Optional[str] = None

    @field_validator('dni')
    @classmethod
    def validate_dni(cls, v):
        return validate_dni_digits(v)

    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v):
        return validate_phone_digits(v)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_format(v)

class UserCreate(UserBase):
    password: str

    @field_validator('dni')
    @classmethod
    def validate_dni(cls, v):
        return validate_dni_digits(v)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        return validate_password_strength(cls, v)

class ChangePassword(BaseModel):
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        return validate_password_strength(cls, v)

class UserLogin(BaseModel):
    email: str
    password: str
    device_id: Optional[str] = None

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_format(v)

class RechargeBalance(BaseModel):
    monto: float

class UserPasswordChange(BaseModel):
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        return validate_password_strength(cls, v)

class PromotionCreate(BaseModel):
    titulo: str
    descripcion: str
    costo_puntos: int = Field(..., gt=0)
    icono: Optional[str] = "fas fa-gift"
    categoria: Optional[str] = "Beneficio"
    sucursal: Optional[str] = None
    tipo_canje: Optional[str] = "voucher"          # 'descuento_reserva' o 'voucher'
    valor_descuento: Optional[int] = Field(default=None, ge=1, le=100)  # porcentaje si tipo_canje == 'descuento_reserva'
    direccion: Optional[str] = None                # dirección donde se canjea (visible en la card)
    latitude: Optional[float] = None               # marcador del mapa
    longitude: Optional[float] = None

class PromotionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descripcion: str
    costo_puntos: int
    icono: str
    categoria: str
    activa: bool
    sucursal: Optional[str] = None
    tipo_canje: Optional[str] = "voucher"
    valor_descuento: Optional[int] = None
    direccion: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class RedemptionTicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    promotion_id: Optional[int] = None
    codigo: str
    titulo: str
    descripcion: Optional[str] = None
    tipo_canje: Optional[str] = "voucher"
    valor_descuento: Optional[int] = None
    icono: Optional[str] = "fas fa-gift"
    sucursal: Optional[str] = None
    estado: Optional[str] = "VIGENTE"
    qr_data: Optional[str] = None
    observacion: Optional[str] = None
    created_at: Optional[str] = None
    fecha_vencimiento: Optional[str] = None
    fecha_uso: Optional[str] = None
    reserva_id: Optional[int] = None
    direccion: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
