import json
import logging
import threading
import time
import datetime
from typing import Optional
from fastapi import Request
from core.config import settings

try:
    import serial
    import serial.tools.list_ports
    HAS_SERIAL = True
except ImportError:
    HAS_SERIAL = False

logger = logging.getLogger("HardwareService")

class HardwareService:
    """
    Servicio unificado de hardware para orquestación de barreras físicas
    vía MQTT y/o conexión Serie USB directa con Arduino Uno.
    """
    _serial_port: Optional[object] = None
    _lock = threading.Lock()
    _connected_port_name: Optional[str] = None

    @classmethod
    def get_serial_connection(cls):
        """Mantiene y auto-reconecta una sesión Serie USB thread-safe con Arduino Uno."""
        if not HAS_SERIAL or not settings.SERIAL_ENABLED:
            return None
        
        with cls._lock:
            if cls._serial_port and getattr(cls._serial_port, 'is_open', False):
                return cls._serial_port
            
            target_port = settings.SERIAL_PORT
            if not target_port or target_port.upper() == "AUTO":
                try:
                    ports = list(serial.tools.list_ports.comports())
                    arduino_ports = [
                        p.device for p in ports 
                        if any(k in (p.description or "") for k in ["Arduino", "CH340", "FT232", "USB Serial", "VID:PID"]) 
                        or "ttyACM" in p.device or "COM" in p.device
                    ]
                    target_port = arduino_ports[0] if arduino_ports else None
                except Exception as e:
                    logger.warning(f"[HARDWARE] Error buscando puertos serie: {e}")
                    target_port = None
            
            if not target_port:
                return None
            
            try:
                cls._serial_port = serial.Serial(target_port, baudrate=settings.SERIAL_BAUDRATE, timeout=1)
                time.sleep(2)  # Reset del bootloader de Arduino
                cls._connected_port_name = target_port
                print(f"[HARDWARE] Conectado exitosamente a Arduino Uno en puerto {target_port} ({settings.SERIAL_BAUDRATE} baudios)")
                return cls._serial_port
            except Exception as e:
                cls._serial_port = None
                cls._connected_port_name = None
                return None

    @classmethod
    def send_serial_command(cls, raw_cmd: str) -> bool:
        """Envía una cadena de comando terminada en salto de línea al Arduino Uno."""
        conn = cls.get_serial_connection()
        if not conn:
            return False
        try:
            with cls._lock:
                line = f"{raw_cmd.strip()}\n"
                conn.write(line.encode('utf-8'))
                conn.flush()
                print(f"[HARDWARE SERIAL] -> Arduino ({cls._connected_port_name}): {line.strip()}")
                return True
        except Exception as e:
            print(f"[HARDWARE SERIAL ERROR] Error enviando a Arduino: {e}")
            cls._serial_port = None
            cls._connected_port_name = None
            return False

    @classmethod
    def publish_mqtt(cls, request: Optional[Request], topic: str, payload: dict):
        """Publica el evento en el broker MQTT."""
        try:
            if request and hasattr(request, 'app') and hasattr(request.app, 'mqtt_client'):
                request.app.mqtt_client.publish(topic, json.dumps(payload))
                print(f"[HARDWARE MQTT] Publicado en {topic}: {payload.get('command')} gate={payload.get('gate')} method={payload.get('method')}")
            else:
                from core.mqtt import mqtt_client
                mqtt_client.publish(topic, json.dumps(payload))
                print(f"[HARDWARE MQTT] Publicado directo en {topic}: {payload.get('command')} gate={payload.get('gate')}")
        except Exception as e:
            print(f"[HARDWARE MQTT ERROR] No se pudo publicar MQTT: {e}")

    @classmethod
    def trigger_barrier(
        cls, 
        gate_id: str, 
        command: str = "OPEN", 
        method: str = "AUTO", 
        details: Optional[dict] = None, 
        request: Optional[Request] = None
    ) -> dict:
        """
        Orquesta la apertura o cierre de la barrera especificada (ENTRADA o SALIDA).
        Dispara simultáneamente el mensaje MQTT y el comando Serie a Arduino Uno.
        """
        gate = "ENTRADA" if "ENTRADA" in gate_id.upper() else "SALIDA"
        cmd = "OPEN" if command.upper().startswith("OPEN") else "CLOSE"
        now_iso = datetime.datetime.now().isoformat()
        
        topic = settings.MQTT_TOPIC_ENTRADA if gate == "ENTRADA" else settings.MQTT_TOPIC_SALIDA
        
        payload = {
            "command": cmd,
            "gate": gate,
            "method": method,
            "timestamp": now_iso
        }
        if details:
            payload.update(details)
            
        # 1. Broker MQTT
        cls.publish_mqtt(request, topic, payload)
        
        # 2. USB Serial Directo Arduino Uno (OPEN_ENTRADA, CLOSE_ENTRADA, OPEN_SALIDA, CLOSE_SALIDA)
        serial_cmd = f"{cmd}_{gate}"
        cls.send_serial_command(serial_cmd)
        
        return {
            "status": "ok", 
            "gate": gate, 
            "command": cmd, 
            "method": method,
            "timestamp": now_iso
        }
