from pydantic import BaseModel, field_validator
from schemas.validators import validate_password_strength, validate_dni_digits, validate_phone_digits, validate_email_format

class OAuthComplete(BaseModel):
    code: str
    dni: str
    telefono: str

    @field_validator('dni')
    @classmethod
    def validate_dni(cls, v):
        return validate_dni_digits(v)

    @field_validator('telefono')
    @classmethod
    def validate_telefono(cls, v):
        return validate_phone_digits(v)

class ForgotPasswordRequest(BaseModel):
    email: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        return validate_email_format(v)

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        return validate_password_strength(cls, v)
