import cv2
import base64
import asyncio
import websockets
from alpr.config import WS_BACKEND_URL, GATE_ID

async def ws_monitoring_worker(streamer):
    """Streaming de frames por WebSocket al backend con reconexión automática."""
    print(f"[*] Intentando conectar streaming a: {WS_BACKEND_URL}")
    while streamer.is_running:
        try:
            async with websockets.connect(WS_BACKEND_URL, ping_interval=20, ping_timeout=20) as websocket:
                print(f"[*] WS Conectado exitosamente para streaming en {GATE_ID}")
                while streamer.is_running:
                    frame = streamer.get_frame()
                    if frame is not None:
                        try:
                            view_frame = cv2.resize(frame, (640, 360))
                            _, buffer = cv2.imencode('.jpg', view_frame, [cv2.IMWRITE_JPEG_QUALITY, 50])
                            await websocket.send(base64.b64encode(buffer).decode('utf-8'))
                        except Exception as fe:
                            print(f"[!] Error al procesar/enviar frame ({GATE_ID}): {fe}")
                            break
                    await asyncio.sleep(0.05)
        except Exception as e:
            print(f"[!] WS Streaming Error ({GATE_ID}): {type(e).__name__} - {e}")
            await asyncio.sleep(5)
