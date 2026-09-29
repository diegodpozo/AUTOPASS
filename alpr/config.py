import os
import re
import warnings
from dotenv import load_dotenv

# Configuración de seguridad y logs
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"
os.environ["FFMPEG_LOG_LEVEL"] = "quiet"
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
load_dotenv()

# Variables de entorno principales
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")
if isinstance(VIDEO_SOURCE, str) and VIDEO_SOURCE.isdigit():
    VIDEO_SOURCE = int(VIDEO_SOURCE)

GATE_TYPE = os.getenv("GATE_TYPE", "entrada").lower()
RAW_GATE_ID = os.getenv("GATE_ID", "ENTRADA_PRINCIPAL" if GATE_TYPE == "entrada" else "SALIDA_PRINCIPAL")
FORCE_OCR = os.getenv("ALPR_FORCE_OCR", "true").lower() in ("1", "true", "yes")

from core.normalize import normalize_name as normalize_id


GATE_ID = normalize_id(RAW_GATE_ID)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
ALPR_NODE_SECRET = os.getenv("ALPR_NODE_SECRET", "")
WS_BACKEND_URL = BACKEND_URL.replace("http", "ws") + f"/v1/system/ws/video/{GATE_ID}"
if ALPR_NODE_SECRET:
    WS_BACKEND_URL += f"?node_secret={ALPR_NODE_SECRET}"

# Parámetros sensibles de visión y consenso
COOLDOWN_SECONDS = int(os.getenv("ALPR_COOLDOWN", 10))
MIN_CONFIDENCE_VOTES = int(os.getenv("ALPR_MIN_CONFIDENCE", 1))
OCR_INTERVAL = float(os.getenv("ALPR_OCR_INTERVAL", 0.35))
CONFIDENCE_THRESHOLD = float(os.getenv("ALPR_CONFIDENCE_THRESHOLD", 0.45))
MOTION_THRESHOLD = int(os.getenv("ALPR_MOTION_THRESHOLD", 3000))
FRAME_QUEUE_MAXSIZE = int(os.getenv("ALPR_FRAMEQ_MAXSIZE", 12))
CONSENSUS_REQUIRED = int(os.getenv("ALPR_CONSENSUS_REQUIRED", 2))
CONSENSUS_WINDOW = float(os.getenv("ALPR_CONSENSUS_WINDOW", 4.0))

PLATE_ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

# MODO DE DETECCION DE MOTOS (HABILITAR O DESHABILITAR FACILMENTE)
# PARA HABILITAR MOTOS, CAMBIAR A True O SETEAR ALPR_ENABLE_MOTOS=true EN .ENV
ENABLE_MOTO_RECOGNITION = os.getenv("ALPR_ENABLE_MOTOS", "false").lower() in ("1", "true", "yes")

# --- PATRONES OFICIALES DE AUTOS ---
AUTO_PLATE_PATTERN = (
    r'\b(' +
    r'[A-Z]{2}\d{3}[A-Z]{2}' + r'|' +    # ARGENTINA AUTOS MERCOSUR (AB123CD) - 7 CARACTERES
    r'[A-Z]{3}\d{3}' + r'|' +            # ARGENTINA AUTOS FORMATO CLASICO (ABC123) - 6 CARACTERES
    r'[A-Z]{3}\d[A-Z]\d{2}' + r'|' +     # BRASIL MERCOSUR (ABC1D23) - 7 CARACTERES
    r'[A-Z]{3}\d{4}' + r'|' +            # URUGUAY (ABC1234) - 7 CARACTERES
    r'[A-Z]{4}\d{3}' +                   # PARAGUAY AUTOS MERCOSUR (ABCD123) - 7 CARACTERES
    r')\b'
)

# --- PATRONES OFICIALES DE MOTOS (PRESERVADOS PARA FACIL ACTIVACION) ---
MOTO_PLATE_PATTERN = (
    r'\b(' +
    r'[A-Z]\d{3}[A-Z]{3}' + r'|' +       # ARGENTINA MOTOS MERCOSUR (A123BCD) - 7 CARACTERES
    r'[A-Z]{2}\d{3}' + r'|' +            # ARGENTINA MOTOS ANTIGUA (AB123) - 5 CARACTERES
    r'[A-Z]{2}\d{3}[A-Z]' + r'|' +       # ARGENTINA MOTOS MERCOSUR (AB123A) - 6 CARACTERES
    r'\d{3}[A-Z]{3}' + r'|' +            # ARGENTINA MOTOS FORMATO CLASICO (123ABC) - 6 CARACTERES
    r'\d{3}[A-Z]{4}' +                   # PARAGUAY MOTOS (123ABCD) - 7 CARACTERES
    r')\b'
)

if ENABLE_MOTO_RECOGNITION:
    LATAM_PLATE_PATTERN = (
        r'\b(' +
        r'[A-Z]{2}\d{3}[A-Z]{2}' + r'|' +
        r'[A-Z]{3}\d{3}' + r'|' +
        r'[A-Z]{3}\d[A-Z]\d{2}' + r'|' +
        r'[A-Z]{3}\d{4}' + r'|' +
        r'[A-Z]{4}\d{3}' + r'|' +
        r'[A-Z]\d{3}[A-Z]{3}' + r'|' +
        r'[A-Z]{2}\d{3}' + r'|' +
        r'[A-Z]{2}\d{3}[A-Z]' + r'|' +
        r'\d{3}[A-Z]{3}' + r'|' +
        r'\d{3}[A-Z]{4}' +
        r')\b'
    )
else:
    LATAM_PLATE_PATTERN = AUTO_PLATE_PATTERN

MOTO_PATTERN = re.compile(r'^[A-Z]{2}\d{3}$|^[A-Z]{2}\d{3}[A-Z]$|^[A-Z]\d{3}[A-Z]{3}$|^\d{3}[A-Z]{3}$|^\d{3}[A-Z]{4}$')
MOTO_MIN_CONFIDENCE = float(os.getenv("ALPR_MOTO_CONFIDENCE", 0.75))
