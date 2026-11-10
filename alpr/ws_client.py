'''Canal WebSocket continuo que envía los fotogramas hacia el servidor para visualizarlos en la pantalla de monitoreo'''


import cv2								# Importa `cv2` para redimensionar el frame y
									# codificarlo como JPEG antes de enviarlo
import base64								# Importa `base64` para convertir el JPEG a texto y
									# poder transportarlo dentro del mensaje WebSocket
import asyncio								# Importa `asyncio` para las pausas asincronas del
									# worker sin bloquear el hilo del streamer
import websockets							# Importa `websockets`, el cliente que abre el
									# canal WebSocket contra el backend
from alpr.config import WS_BACKEND_URL, GATE_ID				# Trae de la configuracion la URL del WebSocket de
									# monitoreo y el identificador del porton
									# `GATE_ID`

async def ws_monitoring_worker(streamer, engine=None):			# Define la corutina
									# `ws_monitoring_worker(streamer, engine=None)`,
									# que transmite frames al backend con reconexion
									# automatica
    """Streaming de frames por WebSocket al backend con reconexión automática y overlay HUD/BoundingBox."""
    while streamer.is_running:						# Bucle externo de reconexion: sigue intentando
									# mientras el streamer este activo (`is_running`)
        try:								# Abre un `try` que captura caidas de conexion o
									# errores de envio
            async with websockets.connect(WS_BACKEND_URL, ping_interval=20, ping_timeout=20) as websocket:
									# Conecta al WebSocket del backend con ping cada 20
									# s y timeout de 20 s, como contexto que cierra la
									# conexion al salir
                while streamer.is_running:				# Bucle interno de envio: transmite frames mientras
									# el streamer siga activo y la conexion este
									# abierta
                    frame = streamer.get_frame()			# Pide el ultimo frame disponible al
									# `VideoStreamer`
                    if frame is not None:				# Comprueba que haya frame antes de intentar
									# procesarlo y enviarlo
                        if engine is not None:				# Comprueba si hay un `engine` ALPR para dibujar el
									# overlay (HUD y caja de la patente)
                            frame = engine.get_frame_with_overlay(frame)
									# Sustituye el frame por su version con overlay
									# generada por el engine, mostrando estado y
									# deteccion
                        try:						# Abre un `try` interno para que un fallo al
									# codificar o enviar no corte el bucle externo de
									# reconexion
                            view_frame = cv2.resize(frame, (640, 360))	# Redimensiona el frame a 640x360, version liviana
									# pensada para el video de monitoreo
                            _, buffer = cv2.imencode('.jpg', view_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
									# Codifica el frame reducido como JPEG con calidad
									# 50 para equilibrar peso de red y legibilidad
                            await websocket.send(base64.b64encode(buffer).decode('utf-8'))
									# Codifica el buffer JPEG en base64 y lo envia como
									# texto por el WebSocket al backend
                        except Exception as fe:				# Captura la excepcion si algo falla al procesar o
									# enviar el frame
                            print(f"[!] Error al procesar/enviar frame ({GATE_ID}): {fe}")
									# Imprime el error de envio incluyendo el `GATE_ID`
									# para identificar el nodo afectado
                            break					# Rompe el bucle interno para forzar una reconexion
									# limpia del WebSocket
                    await asyncio.sleep(0.05)				# Duerme 0.05 s entre frames, fijando el ritmo de
									# streaming (~20 fps) de video de monitoreo
        except Exception as e:						# Captura cualquier excepcion del bloque de
									# conexion para reconectar en vez de matar el
									# worker
            print(f"[!] WS Streaming Error ({GATE_ID}): {type(e).__name__} - {e}")
									# Imprime el error de streaming WebSocket con el
									# `GATE_ID` y el tipo de excepcion
            await asyncio.sleep(5)					# Espera 5 segundos antes de reintentar la
									# conexion, evitando martillar al backend si esta
									# caido
