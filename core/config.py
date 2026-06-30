import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AUTOPASS Professional"
    VERSION: str = "9.2.0"
    
    # CONTACTO
    CONTACT_SUPPORT: str = "soporte@autopass.com.ar"
    CONTACT_EXPANSION: str = "expansion@autopass.com.ar"
    CONTACT_PRIVACY: str = "privacidad@autopass.com.ar"
    CONTACT_INFO: str = "info@autopass.com.ar"
    
    # SEGURIDAD
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu_super_secreto_para_produccion")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
    ALLOWED_ORIGINS: list = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    
    # BASE DE DATOS
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./parking.db")
    
    # SMTP (MAILTRAP POR DEFECTO PARA DESARROLLO)
    SMTP_SERVER: str = os.getenv("SMTP_SERVER", "sandbox.smtp.mailtrap.io")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", 2525))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM: str = os.getenv("SMTP_FROM", "no-reply@autopass.com.ar")
    
    # RECUPERACION
    RECOVERY_TOKEN_EXPIRE_MINUTES: int = 30
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")
    
    # MQTT
    MQTT_BROKER: str = os.getenv("MQTT_BROKER", "broker.hivemq.com")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", 1883))
    MQTT_TOPIC_ENTRADA: str = os.getenv("MQTT_TOPIC_ENTRADA", "parking/barrera/entrada/control")
    MQTT_TOPIC_SALIDA: str = os.getenv("MQTT_TOPIC_SALIDA", "parking/barrera/salida/control")
    
    # TARIFAS FALLBACK
    DEFAULT_HOURLY_RATE: float = 1500.0
    DEFAULT_BASE_RATE: float = 1000.0
    
    # RUTAS DE ASSETS
    BASE_DIR: str = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOGO_PATH: str = os.path.join(BASE_DIR, "static", "images", "logo.png")
    IMAGE_DIR: str = os.getenv("IMAGE_DIR", "captured_images")

    # RESERVAS
    RESERVA_HORA_MIN_SEGUNDOS: int = int(os.getenv("RESERVA_HORA_MIN_SEGUNDOS", 1800))

    # MANTENIMIENTO Y SALUD
    MAINTENANCE_INTERVAL_SECONDS: int = int(os.getenv("MAINTENANCE_INTERVAL_SECONDS", 300))
    HEARTBEAT_TIMEOUT_SECONDS: int = int(os.getenv("HEARTBEAT_TIMEOUT_SECONDS", 90))

settings = Settings()
