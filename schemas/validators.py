import re


def validate_password_strength(cls, v):
    if len(v) < 8:
        raise ValueError('La contraseña debe tener al menos 8 caracteres')
    if not re.search(r"[A-Z]", v):
        raise ValueError('La contraseña debe tener al menos una mayúscula')
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
        raise ValueError('La contraseña debe tener al menos un carácter especial')
    return v
