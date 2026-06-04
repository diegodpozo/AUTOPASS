import re

def normalize_plate(p: str): 
    """Elimina caracteres especiales y convierte a mayúsculas."""
    if not p: return ""
    return re.sub(r'[^A-Z0-9]', '', p.upper())

def format_plate(p: str):
    """Aplica formato visual estándar a la patente (Ej: ABC 123)."""
    clean = normalize_plate(p)
    if len(clean) == 6: return f"{clean[:3]} {clean[3:]}"
    if len(clean) == 7: return f"{clean[:2]} {clean[2:5]} {clean[5:]}"
    return clean

def normalize_name(s: str):
    """Formatea nombres y apellidos."""
    if not s: return ""
    return s.strip().title()

def normalize_dni(s: str):
    """Aplica formato de puntos al DNI para visualización."""
    if not s: return ""
    clean = re.sub(r'[^0-9]', '', s)
    if len(clean) == 7: return f"{clean[0]}.{clean[1:4]}.{clean[4:]}"
    if len(clean) == 8: return f"{clean[:2]}.{clean[2:5]}.{clean[5:]}"
    return clean
