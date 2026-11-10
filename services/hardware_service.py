'''Orquestador del hardware de barreras: publica los comandos en los topics MQTT de entrada/salida y/o envía la orden por serie USB al Arduino Uno, con resolucion de barrera'''

import json								# Importa `json` para serializar el payload que se
									# publica por MQTT
import logging								# Importa `logging` para registrar la actividad del
									# servicio de hardware
import re								# Importa `re` para dividir y limpiar el `gate_id`
									# recibido
import threading							# Importa `threading` para el lock que hace
									# thread-safe la conexion serie
import time								# Importa `time` para la pausa que espera el reset
									# del bootloader del Arduino
import datetime								# Importa `datetime` para sellar con timestamp los
									# comandos de barrera
from typing import Optional, List						# Importa `Optional` y `List` para tipar parametros
from fastapi import Request, HTTPException, WebSocket				# Importa `Request`, `HTTPException` y `WebSocket` de FastAPI
									# para fallar con 400 si el porton es invalido
from core.config import settings					# Importa `settings` con los parametros de MQTT y
									# de la conexion serie

try:									# Abre un `try` para importar el soporte de puerto
									# serie, que puede no estar instalado
    import serial							# Importa `serial`, la libreria pyserial para
									# hablar con el Arduino
    import serial.tools.list_ports					# Importa `serial.tools.list_ports` para enumerar
									# los puertos disponibles y autodetectar el
									# Arduino
    HAS_SERIAL = True							# Marca `HAS_SERIAL` en True indicando que pyserial
									# esta disponible
except ImportError:							# Captura el `ImportError` cuando pyserial no esta
									# instalado
    HAS_SERIAL = False							# Marca `HAS_SERIAL` en False y sigue funcionando
									# solo con MQTT

logger = logging.getLogger("HardwareService")				# Crea el logger `HardwareService` para los
									# mensajes de este servicio

class HardwareService:							# Define la clase `HardwareService`, que orquesta
									# las barreras fisicas
    """
    Servicio unificado de hardware para orquestación de barreras físicas
    vía MQTT, WebSocket remoto (Cloudflare / Tailscale) y/o conexión Serie USB directa con Arduino Uno.
    """
    _serial_port: Optional[object] = None				# Declara el atributo de clase `_serial_port` (la
									# conexion serie, o None)
    _lock = threading.Lock()						# Declara el lock de clase `_lock`, que serializa
									# el acceso concurrente al puerto serie
    _connected_port_name: Optional[str] = None				# Declara `_connected_port_name`, el nombre del
									# puerto serie conectado actualmente
    _ws_clients: List[WebSocket] = []
    _loop: Optional[object] = None

    _GATE_ALIASES = {							# Define `_GATE_ALIASES`: mapa que traduce
									# sinonimos (ENTRADA/INGRESO/ENTRY/IN) a un porton
									# canonico
        "ENTRADA": "ENTRADA", "INGRESO": "ENTRADA", "ENTRY": "ENTRADA", "IN": "ENTRADA",
									# Define los alias de entrada: ENTRADA, INGRESO,
									# ENTRY e IN
        "SALIDA": "SALIDA", "EGRESO": "SALIDA", "EXIT": "SALIDA", "OUT": "SALIDA",
									# Define los alias de salida: SALIDA, EGRESO, EXIT
									# y OUT
    }									# Cierra el diccionario de alias de portones

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

    @classmethod							# Decorador `@classmethod` porque `resolve_gate`
									# usa el mapa de clase
    def resolve_gate(cls, gate_id: str) -> str:				# Define `resolve_gate(gate_id)`: resuelve el
									# porton destino a ENTRADA o SALIDA
        """RESUELVE EL PORTON DESTINO. ES EXPLICITO: UN GATE_ID DESCONOCIDO NO SE ASUME SALIDA."""
        raw = (gate_id or "").strip().upper()				# Normaliza la entrada: la convierte a texto, quita
									# espacios y pasa a mayusculas
        candidates = [c for c in re.split(r"[^A-Z0-9]+", raw) if c]	# Divide el gate_id en tokens alfanumericos (por
									# '_', '-', etc.), descartando vacios
        resueltos = {cls._GATE_ALIASES[c] for c in candidates if c in cls._GATE_ALIASES}
									# Convierte cada token en su porton canonico,
									# descartando los que no estan en el mapa
        if len(resueltos) == 1:						# Si exactamente un porton fue identificado, es una
									# resolucion valida
            return resueltos.pop()					# Devuelve el unico porton resuelto
        raise HTTPException(						# Inicio de la excepcion cuando el gate_id no
									# identifica un porton valido
            status_code=400,						# Fija el codigo de estado 400 (peticion invalida)
            detail=(							# Empieza el mensaje de detalle del error
                f"gate_id '{gate_id}' no identifica un porton valido. "
									# Indica cual fue el gate_id invalido recibido
                "Debe indicar ENTRADA o SALIDA (tambien se aceptan INGRESO, EGRESO, ENTRY, EXIT)."
									# Explica que debe indicar ENTRADA o SALIDA y los
									# sinonimos aceptados
            ),								# Cierra el mensaje de detalle
        )								# Cierra la construccion del `HTTPException`

    @classmethod							# Decorador `@classmethod` porque la conexion serie
									# se mantiene a nivel de clase
    def get_serial_connection(cls):					# Define `get_serial_connection()`: mantiene y
									# auto-reconecta la sesion serie con el Arduino
        """Mantiene y auto-reconecta una sesión Serie USB thread-safe con Arduino Uno."""
        if not HAS_SERIAL or not settings.SERIAL_ENABLED:		# Si no hay pyserial o el serie esta deshabilitado
									# por configuracion, no hay conexion
            return None							# Devuelve None cuando el puerto serie no esta
									# disponible
        
        with cls._lock:							# Toma el lock para evitar que dos hilos abran el
									# puerto a la vez
            if cls._serial_port and getattr(cls._serial_port, 'is_open', False):
									# Si ya hay un puerto serie abierto, lo reutiliza
                return cls._serial_port					# Devuelve la conexion serie existente y abierta
            
            target_port = settings.SERIAL_PORT				# Lee el puerto objetivo desde
									# `settings.SERIAL_PORT`
            if not target_port or target_port.upper() == "AUTO":	# Si el puerto esta vacio o en modo AUTO,
									# autodetecta el Arduino
                try:							# Abre un `try` para tolerar errores al enumerar
									# puertos
                    ports = list(serial.tools.list_ports.comports())	# Lista los puertos serie disponibles en el
									# sistema

                    def _prioridad(p):					# Define `_prioridad`, funcion local que puntua
									# cada puerto para elegir el mas adecuado
                        """Ordena los puertos: Arduino/USB reales antes que Bluetooth/genéricos."""
                        desc = (p.description or "").lower()		# Normaliza a minusculas la descripcion del puerto
									# para comparar palabras clave
                        dev = (p.device or "").lower()			# Normaliza a minusculas el nombre del dispositivo,
									# por ejemplo `com9` o `ttyusb0`
                        if "bluetooth" in desc:				# Si la descripcion contiene 'bluetooth', el puerto
									# es inalambrico y queda al final
                            return 3					# Devuelve prioridad 3 (ultimo recurso) para los
									# puertos Bluetooth
                        if any(k in desc for k in ("arduino", "ch340", "ft232", "usb serial", "vid:pid")):
									# Si la descripcion menciona Arduino, CH340, FT232,
									# USB Serial o VID:PID, es un USB real
                            return 0					# Devuelve prioridad 0, la maxima, para placas
									# Arduino/CH340 y adaptadores USB
                        if "ttyacm" in dev or "ttyusb" in dev:		# En Linux, `ttyACM` o `ttyUSB` tambien indican un
									# dispositivo USB por cable
                            return 1					# Devuelve prioridad 1 para esos puertos USB de
									# Linux
                        if "com" in dev or "tty" in dev:		# Cualquier otro puerto COM/tty generico queda con
									# prioridad intermedia
                            return 2					# Devuelve prioridad 2 para puertos genericos
                        return 4					# Devuelve prioridad 4 para puertos que no encajan
									# en ninguna categoria

                    candidatos = sorted(				# Ordena los puertos candidatos de menor a mayor
									# prioridad
                        (p for p in ports if "com" in (p.device or "").lower() or "tty" in (p.device or "").lower()),
									# Generador: toma solo puertos cuyo nombre contiene
									# 'com' o 'tty'
                        key=lambda p: (_prioridad(p), p.device),	# Clave de orden: primero la prioridad y, como
									# desempate, el nombre del dispositivo
                    )							# Cierra la llamada a `sorted`
                    target_port = candidatos[0].device if candidatos else None
									# Elige el primer puerto del ranking (el mejor) o
									# `None` si no hay candidatos
                    if target_port and _prioridad(candidatos[0]) >= 3:	# Si el mejor candidato es Bluetooth/generico
									# (prioridad 3 o 4), avisa que es ultimo recurso
                        logger.warning(					# Registra la advertencia de que solo se
									# encontraron puertos de ultimo recurso
                            "AUTO solo encontró puertos Bluetooth/genéricos; usando %s como último recurso.",
									# Texto de la advertencia; `%s` se reemplaza por el
									# puerto elegido
                            target_port,				# Pasa el puerto elegido como argumento del mensaje
									# de advertencia
                        )						# Cierra la llamada a `logger.warning`
                except Exception as e:					# Captura errores al buscar puertos serie
                    logger.warning(f"[HARDWARE] Error buscando puertos serie: {e}")
									# Registra una advertencia con el error de busqueda
									# de puertos
                    target_port = None					# Deja `target_port` en None tras el fallo de
									# busqueda
            
            if not target_port:						# Si no se encontro ningun puerto objetivo, no
									# puede conectar
                return None						# Devuelve None cuando no hay puerto disponible
            
            try:							# Abre un `try` para la apertura efectiva del
									# puerto serie
                cls._serial_port = serial.Serial(target_port, baudrate=settings.SERIAL_BAUDRATE, timeout=1)
									# Abre el puerto serie con el baudrate configurado
									# y timeout de 1 s, guardandolo en `_serial_port`
                time.sleep(2)  # Reset del bootloader de Arduino
                cls._connected_port_name = target_port			# Guarda el nombre del puerto conectado en
									# `_connected_port_name`
                logger.info(f"Conectado exitosamente a Arduino Uno en puerto {target_port} ({settings.SERIAL_BAUDRATE} baudios)")
									# Registra en log la conexion exitosa con puerto y
									# baudrate
                return cls._serial_port					# Devuelve la conexion serie lista para usar
            except Exception as e:					# Captura el fallo al abrir el puerto serie
                cls._serial_port = None					# Limpia `_serial_port` porque la conexion no se
									# pudo establecer
                cls._connected_port_name = None				# Limpia `_connected_port_name`
                return None						# Devuelve None si la apertura fallo

    @classmethod							# Decorador `@classmethod` para el envio de
									# comandos serie
    def send_serial_command(cls, raw_cmd: str) -> bool:			# Define `send_serial_command(raw_cmd)`: envia un
									# comando de texto terminado en salto de linea
        """Envía una cadena de comando terminada en salto de línea al Arduino Uno."""
        conn = cls.get_serial_connection()				# Obtiene (o reconecta) la conexion serie llamando
									# al helper anterior
        if not conn:							# Si no hay conexion, no se puede enviar
            return False						# Devuelve False cuando no hay puerto serie
									# disponible
        try:								# Abre un `try` para tolerar errores de escritura
            with cls._lock:						# Toma el lock para que solo un hilo escriba en el
									# puerto a la vez
                line = f"{raw_cmd.strip()}\n"				# Arma la linea agregando el terminador `\n`, que
									# el Arduino usa como fin de comando
                conn.write(line.encode('utf-8'))			# Escribe el comando codificado en UTF-8 en el
									# puerto serie
                conn.flush()						# Fuerza el vaciado del buffer de salida para
									# asegurar el envio
                logger.info(f"[HARDWARE SERIAL] -> Arduino ({cls._connected_port_name}): {line.strip()}")
									# Registra en log el comando enviado y el puerto
                return True						# Devuelve True indicando envio exitoso
        except Exception as e:						# Captura errores de escritura, por ejemplo puerto
									# desconectado
            logger.error(f"Error enviando a Arduino: {e}")		# Registra el error del envio a Arduino
            cls._serial_port = None					# Limpia `_serial_port` para forzar reconexion en
									# el proximo intento
            cls._connected_port_name = None				# Limpia `_connected_port_name`
            return False						# Devuelve False porque el comando no se pudo
									# enviar

    @classmethod							# Decorador `@classmethod` para la publicacion
									# MQTT
    def publish_mqtt(cls, request: Optional[Request], topic: str, payload: dict):
									# Define `publish_mqtt(request, topic, payload)`:
									# publica el evento en el broker MQTT
        """Publica el evento en el broker MQTT."""
        try:								# Abre un `try` para tolerar fallos del broker
            if request and hasattr(request, 'app') and hasattr(request.app, 'mqtt_client'):
									# Si el request trae la app con un cliente MQTT,
									# usa ese cliente inyectado
                request.app.mqtt_client.publish(topic, json.dumps(payload))
									# Publica el payload serializado como JSON en el
									# topic, usando el cliente de la app
                logger.info(f"Publicado en {topic}: {payload.get('command')} gate={payload.get('gate')} method={payload.get('method')}")
									# Registra en log la publicacion con comando, gate
									# y metodo
            else:							# Rama `else`: no hay cliente MQTT en la app, se
									# importa el cliente global
                from core.mqtt import mqtt_client			# Importa `mqtt_client` desde `core/mqtt` como
									# respaldo
                mqtt_client.publish(topic, json.dumps(payload))		# Publica el payload con el cliente global
                logger.info(f"Publicado directo en {topic}: {payload.get('command')} gate={payload.get('gate')}")
									# Registra la publicacion directa con comando y
									# gate
        except Exception as e:						# Captura cualquier fallo al publicar MQTT
            logger.error(f"No se pudo publicar MQTT: {e}")		# Registra el error de publicacion MQTT

    @classmethod							# Decorador `@classmethod` para el disparo de la
									# barrera
    def trigger_barrier(						# Define `trigger_barrier`: orquesta apertura o
									# cierre de la barrera
        cls,								# Comienza la firma con el gate_id como primer
									# parametro
        gate_id: str,							# Recibe el comando (por defecto OPEN)
        command: str = "OPEN",						# Recibe el metodo de disparo (por defecto AUTO)
        method: str = "AUTO",						# Recibe detalles opcionales para enriquecer el
									# payload
        details: Optional[dict] = None,					# Recibe un request opcional para reutilizar el
									# cliente MQTT de la app
        request: Optional[Request] = None				# Cierra la firma de `trigger_barrier`
    ) -> dict:								# Declara el tipo de retorno como `dict`
        """
        Orquesta la apertura o cierre de la barrera especificada (ENTRADA o SALIDA).
        Dispara simultáneamente el mensaje MQTT, la transmisión por WebSocket y el comando Serie a Arduino Uno.
        """
        gate = cls.resolve_gate(gate_id)				# Resuelve el porton canonico con `resolve_gate`
									# (falla si es ambiguo)
        cmd = "OPEN" if command.upper().startswith("OPEN") else "CLOSE"
									# Normaliza el comando a OPEN o CLOSE segun como
									# empiece el texto recibido
        now_iso = datetime.datetime.now().isoformat()			# Genera el timestamp ISO actual para el evento
        
        topic = settings.MQTT_TOPIC_ENTRADA if gate == "ENTRADA" else settings.MQTT_TOPIC_SALIDA
									# Elige el topic MQTT de entrada o salida segun el
									# porton resuelto
        
        payload = {							# Empieza a armar el payload del comando
            "command": cmd,						# Incluye el comando (OPEN/CLOSE)
            "gate": gate,						# Incluye el porton (ENTRADA/SALIDA)
            "method": method,						# Incluye el metodo de disparo
            "timestamp": now_iso					# Incluye el timestamp del comando
        }								# Cierra el diccionario base del payload
        if details:							# Si se pasaron detalles extra, los agrega al
									# payload
            payload.update(details)					# Fusiona los detalles adicionales en el mismo
									# payload
            
        # 1. Broker MQTT
        cls.publish_mqtt(request, topic, payload)			# Publica el payload en el topic MQTT elegido
        
        # 2. Clientes WebSocket remotos (ej: Laptop con Arduino vía Cloudflare/Tailscale)
        cls.broadcast_ws(payload)

        # 3. USB Serial Directo Arduino Uno (OPEN_ENTRADA, CLOSE_ENTRADA, OPEN_SALIDA, CLOSE_SALIDA)
        serial_cmd = f"{cmd}_{gate}"					# Construye el comando serie combinando comando y
									# porton, por ejemplo `OPEN_ENTRADA`
        cls.send_serial_command(serial_cmd)				# Envia el comando serie al Arduino por USB
        
        return {							# Empieza a armar la respuesta de resultado
            "status": "ok",						# Incluye el estado 'ok' en la respuesta
            "gate": gate,						# Incluye el porton resuelto
            "command": cmd,						# Incluye el comando normalizado
            "method": method,						# Incluye el metodo de disparo
            "timestamp": now_iso					# Incluye el timestamp del evento
        }								# Cierra el diccionario de respuesta que devuelve
									# el metodo
