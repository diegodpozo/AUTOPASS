import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AUTOPASS Professional"
    VERSION: str = "4.5.0"
    
    # Seguridad
    SECRET_KEY: str = os.getenv("SECRET_KEY", "tu_super_secreto_para_produccion")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))
    
    # Base de Datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./parking.db")
    
    # MQTT
    MQTT_BROKER: str = os.getenv("MQTT_BROKER", "broker.hivemq.com")
    MQTT_PORT: int = int(os.getenv("MQTT_PORT", 1883))
    MQTT_TOPIC_ENTRADA: str = os.getenv("MQTT_TOPIC_ENTRADA", "parking/barrera/entrada/control")
    MQTT_TOPIC_SALIDA: str = os.getenv("MQTT_TOPIC_SALIDA", "parking/barrera/salida/control")
    
    # ALPR
    IMAGE_DIR: str = "captured_images"

settings = Settings()
