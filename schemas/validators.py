import re

DNI_MIN_DIGITS = 7
DNI_MAX_DIGITS = 8
PHONE_MIN_DIGITS = 10
PHONE_MAX_DIGITS = 13


def validate_password_strength(cls, v):
    if len(v) < 8:
        raise ValueError('La contraseña debe tener al menos 8 caracteres')
    if not re.search(r"[A-Z]", v):
        raise ValueError('La contraseña debe tener al menos una mayúscula')
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
        raise ValueError('La contraseña debe tener al menos un carácter especial')
    return v


def validate_dni_digits(v):
    """DEJA SOLO DIGITOS Y EXIGE 7 U 8 (DNI ARGENTINO)."""
    if v is None:
        return v
    clean = re.sub(r'\D', '', v or '')
    if not re.fullmatch(r'\d{7,8}', clean):
        raise ValueError(f'El DNI debe contener solo números ({DNI_MIN_DIGITS} u {DNI_MAX_DIGITS} dígitos)')
    return clean


def validate_phone_digits(v):
    """DEJA SOLO DIGITOS Y VALIDA EL RANGO DE 10 A 13."""
    if v is None:
        return v
    clean = re.sub(r'\D', '', v or '')
    if len(clean) < PHONE_MIN_DIGITS:
        raise ValueError(f'El teléfono debe contener solo números y al menos {PHONE_MIN_DIGITS} dígitos')
    if len(clean) > PHONE_MAX_DIGITS:
        raise ValueError(f'El teléfono debe contener como máximo {PHONE_MAX_DIGITS} dígitos')
    return clean


def validate_email_format(v):
    """EXIGE UN EMAIL BIEN FORMADO: UNA SOLA @, USUARIO, DOMINIO Y TLD."""
    if v is None:
        return v
    clean = (v or '').strip()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', clean):
        raise ValueError('El correo electrónico debe tener un formato válido (ej: nombre@dominio.com)')
    return clean
