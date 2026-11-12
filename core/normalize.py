import re
import unicodedata


def normalize_name(text: str):
    """NORMALIZA UN NOMBRE PARA COMPARARLO: MAYUSCULAS, SIN ACENTOS Y SIN PREFIJO 'AUTOPASS '.

    Es la forma canonica que usa el proyecto para nombres de sede/organizacion
    ("AUTOPASS Ituzaingó" y "ituzaingo" quedan como la misma clave).
    """
    if not text: return ""
    text = text.upper().replace("AUTOPASS ", "").strip()
    return "".join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')


def normalize_branch_name(text: str) -> str:
    """ALIAS SEMANTICO DE `normalize_name` PARA NOMBRES DE SUCURSAL."""
    return normalize_name(text)


def same_branch(a: str, b: str) -> bool:
    """TRUE SI DOS NOMBRES DE SUCURSAL REFIEREN A LA MISMA SEDE.
    Comparacion canonica del proyecto: ignora prefijo 'AUTOPASS ', mayusculas y acentos.
    Devuelve False si alguna sede es vacia (denegar ante dato faltante)."""
    na = normalize_branch_name(a or "")
    return bool(na) and na == normalize_branch_name(b or "")


def normalize_user_name(s: str):
    """NORMALIZA UN NOMBRE DE PERSONA A FORMATO TITULO (sin espacios sobrantes).

    Ej.: "  juan  perez " -> "Juan  Perez". Solo recorta extremos y capitaliza
    cada palabra; no colapsa espacios internos.
    """
    if not s: return ""
    return s.strip().title()


def normalize_plate(p: str): 
    """ELIMINA CARACTERES ESPECIALES Y CONVIERTE A MAYUSCULAS."""
    if not p: return ""
    return re.sub(r'[^A-Z0-9]', '', p.upper())


# FORMATOS DE PATENTE RECONOCIDOS (LATAM): AR, BR, UY Y PY.
PLATE_PATTERNS = (
    r'^[A-Z]{3}\d{3}$',         # ARGENTINA AUTO CLASICO (ABC123)
    r'^[A-Z]{2}\d{3}[A-Z]{2}$', # ARGENTINA AUTO MERCOSUR (AB123CD)
    r'^\d{3}[A-Z]{3}$',         # ARGENTINA MOTO CLASICO (123ABC)
    r'^[A-Z]\d{3}[A-Z]{3}$',    # ARGENTINA MOTO MERCOSUR (A123BCD)
    r'^[A-Z]{3}\d{4}$',         # BRASIL / URUGUAY (ABC1234)
    r'^[A-Z]{3}\d[A-Z]\d{2}$',  # BRASIL MERCOSUR (ABC1D23)
    r'^[A-Z]{4}\d{3}$',         # PARAGUAY AUTO (ABCD123)
    r'^\d{4}[A-Z]{3}$',         # PARAGUAY (1234ABC)
)
_PLATE_RE = re.compile("|".join(f"(?:{p})" for p in PLATE_PATTERNS))


def is_valid_plate(p: str) -> bool:
    """TRUE SI LA PATENTE (ya normalizada) COINCIDE CON UN FORMATO LATAM RECONOCIDO."""
    clean = normalize_plate(p)
    return bool(clean) and _PLATE_RE.match(clean) is not None


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

