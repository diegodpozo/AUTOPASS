import re
import unicodedata


def normalize_name(text: str):
    if not text: return ""
    text = text.upper().replace("AUTOPASS ", "").strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def normalize_branch_name(text: str) -> str:
    return normalize_name(text)


def normalize_user_name(s: str):
    if not s: return ""
    return s.strip().title()


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


def normalize_dni(s: str):
    """DNI CANONICO: SOLO DIGITOS, SIN PUNTOS NI SEPARADORES (unifica '12.345.678' y '12345678')."""
    if not s: return ""
    return re.sub(r'[^0-9]', '', s)


def format_dni(s: str) -> str:
    """DNI SOLO DIGITOS PARA VISUALIZACION (sin puntos)."""
    return normalize_dni(s)

