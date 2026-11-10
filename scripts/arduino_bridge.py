"""
Script Puente (Bridge) para Arduino Uno (AUTOPASS).
Soporta dos modos de comunicación con el servidor central:
1. WebSocket (Recomendado): Conexión directa y segura vía Cloudflare Tunnel o Tailscale.
2. MQTT: Conexión mediante broker MQTT (ej: broker.hivemq.com).

Escucha los comandos de barrera emitidos por el servidor y los reenvía por puerto Serie USB al Arduino.
"""

import sys
import json
import time
import os
import argparse
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Variables de entorno o defaults
DEFAULT_BACKEND_URL = os.getenv("BACKEND_URL", os.getenv("BASE_URL", ""))
DEFAULT_SECRET = os.getenv("HARDWARE_SECRET", os.getenv("ALPR_NODE_SECRET", os.getenv("SECRET_KEY", "")))
MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
TOPIC_ENTRADA = os.getenv("MQTT_TOPIC_ENTRADA", "parking/barrera/entrada/control")
TOPIC_SALIDA = os.getenv("MQTT_TOPIC_SALIDA", "parking/barrera/salida/control")
SERIAL_PORT_CONFIG = os.getenv("SERIAL_PORT", "AUTO")
SERIAL_BAUDRATE = int(os.getenv("SERIAL_BAUDRATE", 9600))

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

try:
    import websockets
    HAS_WEBSOCKETS = True
except ImportError:
    HAS_WEBSOCKETS = False

try:
    import paho.mqtt.client as mqtt
    from paho.mqtt.enums import CallbackAPIVersion
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False


class ArduinoController:
    """Gestiona la conexión y re-conexión automática al puerto Serie del Arduino Uno."""

    def __init__(self, target_port: str = "AUTO", baudrate: int = 9600):
        self.target_port = target_port
        self.baudrate = baudrate
        self.ser = None
        self.active_port_name = None

    def find_port(self) -> str:
        if self.target_port and self.target_port.upper() != "AUTO":
            return self.target_port
        if not HAS_SERIAL:
            return None
        try:
            ports = list(serial.tools.list_ports.comports())
            for p in ports:
                desc = p.description or ""
                if any(k in desc for k in ["Arduino", "CH340", "FT232", "USB Serial", "VID:PID"]) or "ttyACM" in p.device or "COM" in p.device:
                    return p.device
        except Exception:
            pass
        return None

    def connect(self) -> bool:
        if not HAS_SERIAL:
            print("❌ Error: PySerial no está instalado. Ejecuta: pip install pyserial")
            return False

        if self.ser and getattr(self.ser, "is_open", False):
            return True

        port = self.find_port()
        if not port:
            return False

        try:
            self.ser = serial.Serial(port, self.baudrate, timeout=1)
            time.sleep(2)  # Reset inicial del bootloader de Arduino
            self.active_port_name = port
            print(f"🔌 Conectado exitosamente a Arduino Uno en {port} ({self.baudrate} baudios)")
            return True
        except Exception as e:
            self.ser = None
            self.active_port_name = None
            print(f"⚠️  No se pudo abrir puerto {port}: {e}")
            return False

    def send_command(self, cmd_str: str) -> bool:
        cmd_clean = cmd_str.strip() + "\n"
        if not self.connect():
            port = self.find_port()
            if port:
                print(f"⚠️  Arduino detectado en {port} pero no conectado. Reintentando...")
                self.connect()
            else:
                print("❌ No se encontró puerto de Arduino conectado.")
            return False

        try:
            self.ser.write(cmd_clean.encode("utf-8"))
            self.ser.flush()
            print(f"⚡ [ARDUINO] -> {cmd_clean.strip()} (puerto {self.active_port_name})")
            return True
        except Exception as e:
            print(f"❌ Error enviando comando a Arduino: {e}")
            try:
                self.ser.close()
            except Exception:
                pass
            self.ser = None
            self.active_port_name = None
            return False


def build_ws_url(raw_url: str, secret: str = "") -> str:
    """Construye la URL WebSocket ws:// o wss:// apuntando al endpoint de hardware."""
    url = raw_url.strip()
    if url.startswith("https://"):
        url = "wss://" + url[8:]
    elif url.startswith("http://"):
        url = "ws://" + url[7:]
    elif not url.startswith("ws://") and not url.startswith("wss://"):
        url = "wss://" + url if "trycloudflare" in url else "ws://" + url

    url = url.rstrip("/")
    if not url.endswith("/ws/hardware"):
        if "/v1/system" not in url:
            url = f"{url}/v1/system/ws/hardware"
        else:
            url = f"{url}/ws/hardware"

    if secret:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}node_secret={secret}"
    return url


def process_barrier_payload(payload_data: dict, arduino: ArduinoController):
    """Interpreta el JSON de comando y lo despacha al Arduino."""
    command = str(payload_data.get("command", "OPEN")).upper()
    gate = str(payload_data.get("gate", "ENTRADA")).upper()
    method = payload_data.get("method", "AUTO")

    cmd_str = f"{command}_{gate}"
    print(f"📢 Evento de barrera recibido: {cmd_str} (método={method})")
    arduino.send_command(cmd_str)


# ==========================================
# MODO 1: WEBSOCKET (CLOUDFLARE / TAILSCALE)
# ==========================================
async def run_websocket_mode(base_url: str, secret: str, arduino: ArduinoController):
    if not HAS_WEBSOCKETS:
        print("❌ Error: La librería 'websockets' no está instalada.")
        print("   Instálala en tu laptop con: pip install websockets")
        return

    ws_url = build_ws_url(base_url, secret)
    print("=" * 60)
    print("🚀 INICIANDO AUTOPASS HARDWARE BRIDGE (MODO WEBSOCKET)")
    print(f"🌐 Servidor destino: {ws_url.split('?')[0]}")
    print(f"🔐 Secreto de nodo  : {'***' + secret[-4:] if len(secret) > 4 else ('Configurado' if secret else 'No especificado (solo red local/Tailscale)')}")
    print("=" * 60)

    # Intento inicial de conexión a Arduino
    arduino.connect()

    while True:
        try:
            print(f"🔄 Conectando a {ws_url.split('?')[0]} ...")
            async with websockets.connect(ws_url, ping_interval=20, ping_timeout=20) as ws:
                print("✅ Conectado exitosamente al servidor AUTOPASS vía WebSocket.")
                print("🟢 Esperando órdenes de apertura de barrera (ALPR, QR o Dashboard)...")

                async for message in ws:
                    try:
                        data = json.loads(message)
                        if data.get("type") == "info":
                            print(f"ℹ️  [SERVIDOR]: {data.get('message')}")
                            continue
                        process_barrier_payload(data, arduino)
                    except json.JSONDecodeError:
                        print(f"📩 Mensaje recibido (texto): {message}")
                    except Exception as e:
                        print(f"⚠️  Error procesando mensaje: {e}")

        except websockets.exceptions.InvalidStatusCode as e:
            if e.status_code == 4403 or e.status_code == 403:
                print("❌ ERROR 403: Secreto no autorizado.")
                print("   Asegúrate de pasar el secreto con --secret o definir ALPR_NODE_SECRET en tu .env.")
            else:
                print(f"⚠️  Error HTTP de WebSocket ({e.status_code}).")
            print("⏳ Reintentando en 5 segundos...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"⚠️  Conexión interrumpida ({e}). Reintentando en 3 segundos...")
            await asyncio.sleep(3)


# ==========================================
# MODO 2: MQTT BROKER (HIVEMQ / PRIVADO)
# ==========================================
def run_mqtt_mode(broker: str, port: int, arduino: ArduinoController):
    if not HAS_MQTT:
        print("❌ Error: Paho MQTT no está instalado. Instálalo con: pip install paho-mqtt")
        return

    print("=" * 60)
    print("🚀 INICIANDO AUTOPASS HARDWARE BRIDGE (MODO MQTT)")
    print(f"📡 Broker MQTT: {broker}:{port}")
    print(f"📌 Tópicos    : {TOPIC_ENTRADA} y {TOPIC_SALIDA}")
    print("=" * 60)

    arduino.connect()

    def on_connect(client, userdata, flags, rc, properties=None):
        print(f"✅ Conectado al Broker MQTT ({broker}:{port})")
        client.subscribe(TOPIC_ENTRADA)
        client.subscribe(TOPIC_SALIDA)
        print("🟢 Esperando órdenes de apertura vía MQTT...")

    def on_message(client, userdata, msg):
        try:
            payload_raw = msg.payload.decode("utf-8")
            print(f"📩 Mensaje MQTT en [{msg.topic}]: {payload_raw}")
            try:
                data = json.loads(payload_raw)
            except Exception:
                data = {"command": "OPEN" if "OPEN" in payload_raw.upper() else "CLOSE"}
                data["gate"] = "ENTRADA" if "entrada" in msg.topic.lower() else "SALIDA"
            process_barrier_payload(data, arduino)
        except Exception as e:
            print(f"❌ Error procesando mensaje MQTT: {e}")

    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    while True:
        try:
            print(f"🔄 Conectando a MQTT Broker: {broker}:{port}...")
            client.connect(broker, port, 60)
            client.loop_forever()
        except Exception as e:
            print(f"⚠️  Desconectado de MQTT ({e}). Reintentando en 5 segundos...")
            time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="AUTOPASS Arduino Hardware Bridge")
    parser.add_argument("--mode", choices=["ws", "mqtt"], default=None, help="Modo de conexión: 'ws' (WebSocket) o 'mqtt'")
    parser.add_argument("--url", default=DEFAULT_BACKEND_URL, help="URL del servidor (Cloudflare Tunnel o IP Tailscale, ej: https://xxx.trycloudflare.com o http://100.x.y.z:8000)")
    parser.add_argument("--secret", default=DEFAULT_SECRET, help="Secreto del nodo (ALPR_NODE_SECRET o SECRET_KEY)")
    parser.add_argument("--port", default=SERIAL_PORT_CONFIG, help="Puerto Serie de Arduino (ej: COM3 o AUTO)")
    parser.add_argument("--baud", type=int, default=SERIAL_BAUDRATE, help="Velocidad en baudios (default 9600)")
    parser.add_argument("--broker", default=MQTT_BROKER, help="Broker MQTT (si se usa modo mqtt)")
    parser.add_argument("--mqtt-port", type=int, default=MQTT_PORT, help="Puerto del broker MQTT")

    args = parser.parse_args()

    # Si no se especificó modo pero hay URL configurada, usar WebSocket; de lo contrario MQTT
    mode = args.mode
    if not mode:
        if args.url:
            mode = "ws"
        else:
            mode = "mqtt"

    arduino = ArduinoController(target_port=args.port, baudrate=args.baud)

    if mode == "ws":
        if not args.url:
            print("❌ Error: Para usar modo WebSocket debes indicar la URL del servidor.")
            print("   Ejemplo: python scripts/arduino_bridge.py --url https://tu-tunel.trycloudflare.com --secret tu_secreto")
            sys.exit(1)
        asyncio.run(run_websocket_mode(args.url, args.secret, arduino))
    else:
        run_mqtt_mode(args.broker, args.mqtt_port, arduino)


if __name__ == "__main__":
    main()
