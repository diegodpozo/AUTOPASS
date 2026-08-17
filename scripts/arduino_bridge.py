"""
Script Puente (Bridge) MQTT <-> USB Serial para Arduino Uno (AUTOPASS).
Escucha los temas de control MQTT y reenvía comandos al Arduino por puerto Serie USB.
"""

import sys
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC_ENTRADA = os.getenv("MQTT_TOPIC_ENTRADA", "parking/barrera/entrada/control")
TOPIC_SALIDA = os.getenv("MQTT_TOPIC_SALIDA", "parking/barrera/salida/control")
SERIAL_PORT_CONFIG = os.getenv("SERIAL_PORT", "AUTO")
SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", 9600))

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    print("❌ Error: PySerial no está instalado. Instálalo con: pip install pyserial")
    sys.exit(1)

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.enums import CallbackAPIVersion
except ImportError:
    print("❌ Error: Paho MQTT no está instalado. Instálalo con: pip install paho-mqtt")
    sys.exit(1)

def find_arduino_port():
    if SERIAL_PORT_CONFIG and SERIAL_PORT_CONFIG.upper() != "AUTO":
        return SERIAL_PORT_CONFIG
    ports = list(serial.tools.list_ports.comports())
    for p in ports:
        desc = p.description or ""
        if any(k in desc for k in ["Arduino", "CH340", "FT232", "USB Serial"]) or "ttyACM" in p.device or "COM" in p.device:
            return p.device
    return None

def main():
    port_name = find_arduino_port()
    if not port_name:
        print("⚠️  No se encontró ningún puerto Serie de Arduino. Esperando conexión...")
    else:
        print(f"🔌 Intentando conectar a Arduino Uno en {port_name}...")

    ser = None
    if port_name:
        try:
            ser = serial.Serial(port_name, SERIAL_BAUDRATE, timeout=1)
            time.sleep(2)
            print(f"✅ Conectado a Arduino Uno en {port_name} ({SERIAL_BAUDRATE} baudios)")
        except Exception as e:
            print(f"❌ Error abriendo puerto {port_name}: {e}")

    def on_connect(client, userdata, flags, rc, properties=None):
        print("📡 Conectado al Broker MQTT")
        client.subscribe(TOPIC_ENTRADA)
        client.subscribe(TOPIC_SALIDA)
        print(f"📌 Subscrito a: {TOPIC_ENTRADA} y {TOPIC_SALIDA}")

    def on_message(client, userdata, msg):
        try:
            payload_raw = msg.payload.decode('utf-8')
            print(f"📩 Mensaje MQTT recibido en [{msg.topic}]: {payload_raw}")
            
            command = "OPEN"
            gate = "ENTRADA" if "entrada" in msg.topic.lower() else "SALIDA"
            
            try:
                data = json.loads(payload_raw)
                command = data.get("command", "OPEN").upper()
                if "gate" in data:
                    gate = data["gate"].upper()
            except Exception:
                if "CLOSE" in payload_raw.upper():
                    command = "CLOSE"

            cmd_str = f"{command}_{gate}\n"

            nonlocal ser
            if ser and ser.is_open:
                ser.write(cmd_str.encode('utf-8'))
                ser.flush()
                print(f"⚡ Reenviado a Arduino: {cmd_str.strip()}")
            else:
                p = find_arduino_port()
                if p:
                    try:
                        ser = serial.Serial(p, SERIAL_BAUDRATE, timeout=1)
                        time.sleep(2)
                        ser.write(cmd_str.encode('utf-8'))
                        ser.flush()
                        print(f"⚡ Reenviado a Arduino ({p}): {cmd_str.strip()}")
                    except Exception as ex:
                        print(f"❌ No se pudo conectar a Arduino: {ex}")
        except Exception as e:
            print(f"❌ Error procesando mensaje: {e}")

    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    print(f"🚀 Conectando a MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}...")
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()

if __name__ == "__main__":
    main()
