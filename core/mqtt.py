"""
CLIENTE CENTRAL MQTT PARA COMUNICACION IOT CON BARRERAS FISICAS.

ACLARACION IMPORTANTE DE ARQUITECTURA:
1. ESTE MODULO NO SE CONECTA NI INTERACTUA CON LAS CAMARAS DE SEGURIDAD.
   LAS CAMARAS TRANSMITEN FLUJOS DE VIDEO MEDIANTE RTSP / HTTP CAPTURADOS
   POR OPENCV (ALPR/VIDEO_STREAMER.PY), Y ENVIAN LAS PATENTES DETECTADAS
   AL SERVIDOR A TRAVES DE WEBSOCKETS (ALPR/WS_CLIENT.PY).

2. EL PROTOCOLO MQTT SE EMPLEA EXCLUSIVAMENTE PARA EL ACCIONAMIENTO DE
   LAS BARRERAS FISICAS DEL ESTACIONAMIENTO MEDIANTE HARDWARE IOT
   (MICROCONTROLADORES ESP32 CONECTADOS POR WI-FI O PUENTES ARDUINO).

3. QUIEN GENERA Y ORQUESTA LOS COMANDOS DE APERTURA Y CIERRE ES EL SERVICIO:
   SERVICES/HARDWARE_SERVICE.PY (CLASE HARDWARESERVICE).
   CUANDO SERVICES/ACCESS_SERVICE.PY O EL PANEL DE CONTROL VALIDAN UN INGRESO
   O SALIDA, INVOCAN A HARDWARESERVICE.TRIGGER_BARRIER(GATE_ID, COMMAND='OPEN'),
   EL CUAL DISPARA DOS ACCIONES EN PARALELO:
   A) PUBLICA UN MENSAJE JSON VIA MQTT EN EL TOPICO CORRESPONDIENTE
      (MQTT_TOPIC_ENTRADA O MQTT_TOPIC_SALIDA) USANDO ESTE CLIENTE MQTT.
   B) ENVIA UN COMANDO SERIE USB DIRECTO AL ARDUINO UNO ('OPEN_ENTRADA\n').

4. ESTE ARCHIVO (CORE/MQTT.PY) UNICAMENTE CONFIGURA, INICIALIZA Y EXPORTA
   LA INSTANCIA DEL CLIENTE PAHO MQTT (MQTT_CLIENT) PARA QUE MAIN.PY
   Y HARDWARESERVICE.PY PUEDAN PUBLICAR MENSAJES HACIA EL BROKER.
"""

import paho.mqtt.client as mqtt						# Importa la libreria `paho.mqtt.client` (alias
									# `mqtt`), el cliente Python que habla el protocolo
									# MQTT con el broker
from paho.mqtt.enums import CallbackAPIVersion				# Importa `CallbackAPIVersion` para elegir la
									# version de la API de callbacks de Paho; la v2 es
									# la firma moderna de los callbacks


def get_mqtt_client():							# Define `get_mqtt_client()`, la funcion de fabrica
									# que crea y devuelve un cliente MQTT de Paho ya
									# configurado
    """CONFIGURA E INICIALIZA LA INSTANCIA DEL CLIENTE MQTT DE PAHO."""
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
									# Crea el cliente Paho con `callback_api_version=Ca
									# llbackAPIVersion.VERSION2`, fijando la firma
									# moderna de los callbacks de conexion y mensajes
    return client							# Devuelve el cliente recien creado para que quien
									# llama pueda publicar en el broker o guardarlo
									# como instancia global


# INSTANCIA GLOBAL DEL CLIENTE MQTT UTILIZADA EN TODA LA APLICACION
mqtt_client = get_mqtt_client()						# Crea al importar el modulo la instancia global
									# `mqtt_client` llamando a `get_mqtt_client()`,
									# para reutilizarla en `main.py` y
									# `hardware_service.py`
