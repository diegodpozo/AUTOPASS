import re

def normalize_plate(p: str): 
    """Elimina caracteres especiales y convierte a mayúsculas."""
    if not p: return ""
    return re.sub(r'[^A-Z0-9]', '', p.upper())

def format_plate(p: str):
    """Aplica formato visual estándar a la patente Mercosur."""
    clean = normalize_plate(p)
    # Formato AAA 111 (Arg Antigua)
    if len(clean) == 6: return f"{clean[:3]} {clean[3:]}"
    # Formato AB 123 CD (Arg Mercosur)
    if len(clean) == 7 and clean[2:5].isdigit(): return f"{clean[:2]} {clean[2:5]} {clean[5:]}"
    # Formato ABC 1D23 (Brasil Mercosur)
    if len(clean) == 7 and clean[3].isdigit() and clean[4].isalpha(): return f"{clean[:3]} {clean[3:]}"
    # Formato ABC 1234 (Uruguay)
    if len(clean) == 7 and clean[3:].isdigit(): return f"{clean[:3]} {clean[3:]}"
    # Formato ABCD 123 (Paraguay Autos)
    if len(clean) == 7 and clean[:4].isalpha() and clean[4:].isdigit(): return f"{clean[:4]} {clean[4:]}"
    # Formato 123 ABCD (Paraguay Motos)
    if len(clean) == 7 and clean[:3].isdigit() and clean[3:].isalpha(): return f"{clean[:3]} {clean[3:]}"
    
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
