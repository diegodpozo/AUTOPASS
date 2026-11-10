import json
import logging
import re
import threading
import time
import datetime
from typing import Optional, List
from fastapi import Request, HTTPException, WebSocket
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
    vía MQTT, WebSocket remoto (Cloudflare / Tailscale) y/o conexión Serie USB directa con Arduino Uno.
    """
    _serial_port: Optional[object] = None
    _lock = threading.Lock()
    _connected_port_name: Optional[str] = None
    _ws_clients: List[WebSocket] = []
    _loop: Optional[object] = None

    _GATE_ALIASES = {
        "ENTRADA": "ENTRADA", "INGRESO": "ENTRADA", "ENTRY": "ENTRADA", "IN": "ENTRADA",
        "SALIDA": "SALIDA", "EGRESO": "SALIDA", "EXIT": "SALIDA", "OUT": "SALIDA",
    }

    @classmethod
    def set_event_loop(cls, loop):
        """Registra el event loop principal de FastAPI para disparar broadcast WS desde hilos sincrónicos."""
        cls._loop = loop

    @classmethod
    async def register_ws(cls, websocket: WebSocket):
        """Registra un cliente WebSocket de hardware (ej: laptop con Arduino vía Cloudflare/Tailscale)."""
        import asyncio
        try:
            cls._loop = asyncio.get_running_loop()
        except Exception:
            pass
        with cls._lock:
            if websocket not in cls._ws_clients:
                cls._ws_clients.append(websocket)
        logger.info(f"[HARDWARE WS] Cliente conectado. Total activos: {len(cls._ws_clients)}")

    @classmethod
    async def unregister_ws(cls, websocket: WebSocket):
        """Elimina un cliente WebSocket desconectado."""
        with cls._lock:
            if websocket in cls._ws_clients:
                cls._ws_clients.remove(websocket)
        logger.info(f"[HARDWARE WS] Cliente desconectado. Total activos: {len(cls._ws_clients)}")

    @classmethod
    def broadcast_ws(cls, payload: dict):
        """Transmite el evento de barrera a todos los clientes WebSocket de hardware conectados."""
        with cls._lock:
            clients = list(cls._ws_clients)
        if not clients:
            return

        async def _send_all():
            text = json.dumps(payload)
            dead = []
            for ws in clients:
                try:
                    await ws.send_text(text)
                except Exception as e:
                    logger.debug(f"[HARDWARE WS] Error al enviar a cliente: {e}")
                    dead.append(ws)
            if dead:
                with cls._lock:
                    for d in dead:
                        if d in cls._ws_clients:
                            cls._ws_clients.remove(d)

        import asyncio
        loop = cls._loop
        if loop and getattr(loop, "is_running", lambda: False)():
            try:
                try:
                    curr = asyncio.get_running_loop()
                except RuntimeError:
                    curr = None
                if curr is loop:
                    loop.create_task(_send_all())
                else:
                    asyncio.run_coroutine_threadsafe(_send_all(), loop)
            except Exception as e:
                logger.error(f"[HARDWARE WS] Error programando broadcast WS: {e}")
        else:
            try:
                curr = asyncio.get_running_loop()
                if curr and curr.is_running():
                    curr.create_task(_send_all())
            except Exception:
                pass

    @classmethod
    def resolve_gate(cls, gate_id: str) -> str:
        """RESUELVE EL PORTON DESTINO. ES EXPLICITO: UN GATE_ID DESCONOCIDO NO SE ASUME SALIDA."""
        raw = (gate_id or "").strip().upper()
        candidates = [c for c in re.split(r"[^A-Z0-9]+", raw) if c]
        resueltos = {cls._GATE_ALIASES[c] for c in candidates if c in cls._GATE_ALIASES}
        if len(resueltos) == 1:
            return resueltos.pop()
        raise HTTPException(
            status_code=400,
            detail=(
                f"gate_id '{gate_id}' no identifica un porton valido. "
                "Debe indicar ENTRADA o SALIDA (tambien se aceptan INGRESO, EGRESO, ENTRY, EXIT)."
            ),
        )

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
                logger.info(f"Conectado exitosamente a Arduino Uno en puerto {target_port} ({settings.SERIAL_BAUDRATE} baudios)")
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
                logger.info(f"[HARDWARE SERIAL] -> Arduino ({cls._connected_port_name}): {line.strip()}")
                return True
        except Exception as e:
            logger.error(f"Error enviando a Arduino: {e}")
            cls._serial_port = None
            cls._connected_port_name = None
            return False

    @classmethod
    def publish_mqtt(cls, request: Optional[Request], topic: str, payload: dict):
        """Publica el evento en el broker MQTT."""
        try:
            if request and hasattr(request, 'app') and hasattr(request.app, 'mqtt_client'):
                request.app.mqtt_client.publish(topic, json.dumps(payload))
                logger.info(f"Publicado en {topic}: {payload.get('command')} gate={payload.get('gate')} method={payload.get('method')}")
            else:
                from core.mqtt import mqtt_client
                mqtt_client.publish(topic, json.dumps(payload))
                logger.info(f"Publicado directo en {topic}: {payload.get('command')} gate={payload.get('gate')}")
        except Exception as e:
            logger.error(f"No se pudo publicar MQTT: {e}")

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
        Dispara simultáneamente el mensaje MQTT, la transmisión por WebSocket y el comando Serie a Arduino Uno.
        """
        gate = cls.resolve_gate(gate_id)
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

        # 2. Clientes WebSocket remotos (ej: Laptop con Arduino vía Cloudflare/Tailscale)
        cls.broadcast_ws(payload)

        # 3. USB Serial Directo Arduino Uno (OPEN_ENTRADA, CLOSE_ENTRADA, OPEN_SALIDA, CLOSE_SALIDA)
        serial_cmd = f"{cmd}_{gate}"
        cls.send_serial_command(serial_cmd)

        return {
            "status": "ok",
            "gate": gate,
            "command": cmd,
            "method": method,
            "timestamp": now_iso
        }
