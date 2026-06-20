import re

def normalize_plate(p: str): 
    """ELIMINA CARACTERES ESPECIALES Y CONVIERTE A MAYUSCULAS."""
    if not p: return ""
    return re.sub(r'[^A-Z0-9]', '', p.upper())

def format_plate(p: str):
    """APLICA FORMATO VISUAL ESTANDAR A LA PATENTE MERCOSUR."""
    clean = normalize_plate(p)
    # FORMATO AAA 111 (ARG ANTIGUA)
    if len(clean) == 6: return f"{clean[:3]} {clean[3:]}"
    # FORMATO AB 123 CD (ARG MERCOSUR)
    if len(clean) == 7 and clean[2:5].isdigit(): return f"{clean[:2]} {clean[2:5]} {clean[5:]}"
    # FORMATO ABC 1D23 (BRASIL MERCOSUR)
    if len(clean) == 7 and clean[3].isdigit() and clean[4].isalpha(): return f"{clean[:3]} {clean[3:]}"
    # FORMATO ABC 1234 (URUGUAY)
    if len(clean) == 7 and clean[3:].isdigit(): return f"{clean[:3]} {clean[3:]}"
    # FORMATO ABCD 123 (PARAGUAY AUTOS)
    if len(clean) == 7 and clean[:4].isalpha() and clean[4:].isdigit(): return f"{clean[:4]} {clean[4:]}"
    # FORMATO 123 ABCD (PARAGUAY MOTOS)
    if len(clean) == 7 and clean[:3].isdigit() and clean[3:].isalpha(): return f"{clean[:3]} {clean[3:]}"
    
    return clean

def normalize_name(s: str):
    """FORMATEA NOMBRES Y APELLIDOS."""
    if not s: return ""
    return s.strip().title()

def normalize_dni(s: str):
    """APLICA FORMATO DE PUNTOS AL DNI PARA VISUALIZACION."""
    if not s: return ""
    clean = re.sub(r'[^0-9]', '', s)
    if len(clean) == 7: return f"{clean[0]}.{clean[1:4]}.{clean[4:]}"
    if len(clean) == 8: return f"{clean[:2]}.{clean[2:5]}.{clean[5:]}"
    return clean
