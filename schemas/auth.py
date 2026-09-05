from pydantic import BaseModel, field_validator
from schemas.validators import validate_password_strength

class Token(BaseModel):
    access_token: str
    token_type: str
    rol: str
    nombre: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v):
        return validate_password_strength(cls, v)
