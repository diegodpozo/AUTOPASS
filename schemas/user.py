from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
import re
from schemas.validators import validate_password_strength

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
        clean = re.sub(r'[^0-9]', '', v)
        if len(clean) < 10:
            raise ValueError('El teléfono debe contener al menos 10 dígitos (característica + número)')
        return v

class UserUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    telefono: Optional[str] = None
    email: Optional[str] = None
    direccion: Optional[str] = None

class UserAdminUpdate(BaseModel):
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    dni: Optional[str] = None
    telefono: Optional[str] = None
    sucursal: Optional[str] = None
    rol: Optional[str] = None

class UserCreate(UserBase):
    password: str

    @field_validator('dni')
    @classmethod
    def validate_dni(cls, v):
        if not v.isdigit():
            raise ValueError('El DNI debe contener únicamente números (sin puntos ni espacios)')
        return v

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
    costo_puntos: int
    icono: Optional[str] = "fas fa-gift"
    categoria: Optional[str] = "Beneficio"
    sucursal: Optional[str] = None

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
