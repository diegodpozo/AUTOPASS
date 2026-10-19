import os
import re
import subprocess
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from core.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

_FALLBACK_VERSION = "0.0.0"
_VERSION_SCAN_DEPTH = 50
_CANONICAL_VERSION = re.compile(r"^v(\d+\.\d+\.\d+)\b")
_LOOSE_VERSION = re.compile(r"v(\d+\.\d+\.\d+)\b")


@lru_cache(maxsize=1)
def _version() -> str:
    """Version del proyecto, derivada del historial de commits.

    Busca hacia atras en el subject de los ultimos commits y devuelve la
    version del mas reciente que la menciona. Se aceptan dos formas:

    - canonica: `vX.Y.Z: ...` o `vX.Y.Z ...` al inicio del subject;
    - incidental: `refactor(v9.34.17): ...`, `docs(v9.31.3): ...`.

    Prioriza siempre la forma canonica: si un commit viejo dice "volver a
    v9.30.0" y otro mas nuevo empieza con `v9.34.79:`, gana el canonico.
    Sin commits, sin git, o sin ninguna version en el historial devuelve
    `_FALLBACK_VERSION`.
    """
    repo = Path(__file__).resolve().parent.parent
    try:
        out = subprocess.run(
            ["git", "log", f"-{_VERSION_SCAN_DEPTH}", "--format=%s"],
            cwd=repo,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout
    except Exception:
        logger.debug("No se pudo leer el historial de git", exc_info=True)
        return _FALLBACK_VERSION

    subjects = [line for line in out.splitlines() if line.strip()]
    if not subjects:
        logger.debug("Historial de git vacio: version %s", _FALLBACK_VERSION)
        return _FALLBACK_VERSION

    for pattern in (_CANONICAL_VERSION, _LOOSE_VERSION):
        for subject in subjects:
            found = pattern.search(subject)
            if found:
                logger.debug("Version %s derivada del subject %r", found.group(1), subject)
                return found.group(1)

    logger.warning(
        "Ninguno de los ultimos %d commits menciona una version (sigue %s): "
        "conviene versionar con prefijo 'vX.Y.Z:'",
        len(subjects),
        _FALLBACK_VERSION,
    )
    return _FALLBACK_VERSION


class Settings:
    PROJECT_NAME: str = "AUTOPASS Professional"
    VERSION: str = _version()
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # CONTACTO
    CONTACT_SUPPORT: str = "soporte@autopass.com.ar"
    CONTACT_EXPANSION: str = "expansion@autopass.com.ar"
    CONTACT_PRIVACY: str = "privacidad@autopass.com.ar"
    CONTACT_INFO: str = "info@autopass.com.ar"
    
    # SEGURIDAD
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu_super_secreto_para_produccion")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
    ALLOWED_ORIGINS: list = [o.strip() for o in os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:8000,http://127.0.0.1:8000"
    ).split(",") if o.strip()]
    # Secreto compartido de los nodos ALPR para el WS de video y update-frame.
    # Vacio: solo se aceptan nodos desde red local/loopback (recomendado para ALPR en la misma maquina).
    ALPR_NODE_SECRET: str = os.getenv("ALPR_NODE_SECRET", "")
    # ORGANIZACION A LA QUE ESTA LIGADO ESTE NODO ALPR (0 = sin binding).
    # Atribucion gate -> sede -> empresa: con binding, un gate que no pertenece a
    # ninguna sede de esa organizacion se rechaza (fail-closed).
    ALPR_NODE_ORG_ID: int = int(os.getenv("ALPR_NODE_ORG_ID", "0") or 0)
    
    # BASE DE DATOS
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./parking.db")
    
    # SMTP (MAILTRAP POR DEFECTO PARA DESARROLLO)
    # SMTP_TLS: STARTTLS antes del login. Mailtrap (2525) no lo usa; Gmail/Outlook (587) si.
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "sandbox.smtp.mailtrap.io")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 2525))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "no-reply@autopass.com.ar")
    SMTP_TLS: bool = os.getenv("SMTP_TLS", "false").lower() == "true"
    
    # RECUPERACION / INVITACION
    RECOVERY_TOKEN_EXPIRE_MINUTES: int = 30
    # Vigencia del enlace de invitacion para que un nuevo Admin General fije su clave.
    ACTIVATION_TOKEN_EXPIRE_HOURS: int = int(os.getenv("ACTIVATION_TOKEN_EXPIRE_HOURS", 72))
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # MQTT
    MQTT_BROKER: str = os.getenv("MQTT_BROKER", "broker.hivemq.com")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", 1883))
    MQTT_TOPIC_ENTRADA: str = os.getenv("MQTT_TOPIC_ENTRADA", "parking/barrera/entrada/control")
    MQTT_TOPIC_SALIDA: str = os.getenv("MQTT_TOPIC_SALIDA", "parking/barrera/salida/control")
    
    # HARDWARE / SERIAL (ARDUINO UNO)
    SERIAL_ENABLED: bool = os.getenv("SERIAL_ENABLED", "true").lower() == "true"
    SERIAL_PORT: str = os.getenv("SERIAL_PORT", "AUTO")
    SERIAL_BAUDRATE: int = int(os.getenv("SERIAL_BAUDRATE", 9600))
    
    # TARIFAS FALLBACK
    DEFAULT_HOURLY_RATE: float = 1500.0
    DEFAULT_BASE_RATE: float = 1000.0
    
    # RUTAS DE ASSETS
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOGO_PATH: str = os.path.join(BASE_DIR, "static", "images", "logo.png")
    IMAGE_DIR: str = os.getenv("IMAGE_DIR", "captured_images")
    ALPR_IMAGE_RETENTION_DAYS: int = int(os.getenv("ALPR_IMAGE_RETENTION_DAYS", "30"))

    # RESERVAS
    RESERVA_HORA_MIN_SEGUNDOS: int = int(os.getenv("RESERVA_HORA_MIN_SEGUNDOS", 1800))

    # MANTENIMIENTO Y SALUD
    MAINTENANCE_INTERVAL_SECONDS: int = int(os.getenv("MAINTENANCE_INTERVAL_SECONDS", 300))
    HEARTBEAT_TIMEOUT_SECONDS: int = int(os.getenv("HEARTBEAT_TIMEOUT_SECONDS", 90))

    # CONCURRENCIA (FASE 2): timeout maximo para adquirir un lock transaccional
    # (pg_advisory_xact_lock). Al expirar, el endpoint responde HTTP 409.
    LOCK_TIMEOUT_SECONDS: int = int(os.getenv("LOCK_TIMEOUT_SECONDS", 10))

    # MERCADO PAGO (CHECKOUT PRO)
    # Credenciales de prueba (sandbox): https://www.mercadopago.com.ar/developers/panel/apps
    # MP_ACCESS_TOKEN: Access Token de la cuenta de prueba (test seller).
    # MP_PUBLIC_KEY:        Public Key de la cuenta de prueba (no necesaria para Checkout Pro backend).
    # MP_WEBHOOK_URL:       URL de notificaciones (opcional; para pruebas con localhost usar redirect-back).
    MP_ACCESS_TOKEN: str = os.getenv("MP_ACCESS_TOKEN", "")
    MP_PUBLIC_KEY: str = os.getenv("MP_PUBLIC_KEY", "")
    MP_WEBHOOK_URL: str = os.getenv("MP_WEBHOOK_URL", "")
    MP_PREFERENCE_EXPIRE_MINUTES: int = int(os.getenv("MP_PREFERENCE_EXPIRE_MINUTES", 45))

    # LOGIN SOCIAL (OAUTH 2.0 - GOOGLE + FACEBOOK)
    # Credenciales: Google Cloud Console (OAuth 2.0 Client ID) y Facebook Developers (App).
    # Redirect URI permitida en cada proveedor: {BASE_URL}/v1/auth/oauth/{google|facebook}/callback
    # Si un proveedor queda sin credenciales, sus botones se ocultan en el frontend.
    GOOGLE_OAUTH_CLIENT_ID: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    GOOGLE_OAUTH_CLIENT_SECRET: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    FACEBOOK_OAUTH_CLIENT_ID: str = os.getenv("FACEBOOK_OAUTH_CLIENT_ID", "")
    FACEBOOK_OAUTH_CLIENT_SECRET: str = os.getenv("FACEBOOK_OAUTH_CLIENT_SECRET", "")
    OAUTH_STATE_TTL_SECONDS: int = int(os.getenv("OAUTH_STATE_TTL_SECONDS", "600"))
    OAUTH_SIGNUP_EXPIRE_MINUTES: int = int(os.getenv("OAUTH_SIGNUP_EXPIRE_MINUTES", "15"))

    @property
    def MP_ENABLED(self) -> bool:
        return bool(self.MP_ACCESS_TOKEN.strip())

settings = Settings()
