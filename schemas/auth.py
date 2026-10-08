import re
from pydantic import BaseModel, field_validator
from schemas.validators import validate_password_strength

class OAuthComplete(BaseModel):
    code: str
    dni: str
    telefono: str

    @field_validator('dni')
    @classmethod
    def validate_dni(cls, v):
        clean = re.sub(r'[^0-9]', '', v or '')
        if not re.fullmatch(r'\d{7,8}', clean):
            raise ValueError('El DNI debe tener 7 u 8 números (se toleran puntos)')
        return clean

    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v):
        clean = re.sub(r'[^0-9]', '', v or '')
        if len(clean) < 10:
            raise ValueError('El teléfono debe contener al menos 10 dígitos (característica + número)')
        return v.strip()

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        return validate_password_strength(cls, v)
