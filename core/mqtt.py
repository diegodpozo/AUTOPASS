import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion

def get_mqtt_client():
    """CONFIGURA E INICIALIZA EL CLIENTE MQTT."""
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    
    # PODRIAS AGREGAR CALLBACKS GLOBALES AQUI
    #CLIENT.ON_CONNECT = ON_CONNECT
    
    return client

mqtt_client = get_mqtt_client()
