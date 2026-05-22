import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from core.config import settings

def get_mqtt_client():
    """Configura e inicializa el cliente MQTT."""
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    
    # Podrías agregar callbacks globales aquí
    # client.on_connect = on_connect
    
    return client

mqtt_client = get_mqtt_client()
