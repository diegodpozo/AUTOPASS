import cv2
import time
import asyncio
import threading
from alpr.config import VIDEO_SOURCE, GATE_TYPE, GATE_ID, OCR_INTERVAL
from alpr.video_streamer import VideoStreamer
from alpr.ocr_engine import ALPREngine
from alpr.ws_client import ws_monitoring_worker

def run_alpr_service():
    """Ejecuta el ciclo principal del servicio ALPR."""
    print(f"[*] Iniciando VideoStreamer con fuente: {VIDEO_SOURCE}")
    try:
        streamer = VideoStreamer(VIDEO_SOURCE, target_width=640).start()
    except Exception as e:
        print(f"[!] Error FATAL al iniciar VideoStreamer: {e}")
        return
    
    time.sleep(2)
    if streamer.get_frame() is None:
        print(f"[!] ADVERTENCIA: No se recibe imagen de la fuente {VIDEO_SOURCE}. Verificá la URL o el dispositivo.")

    try:
        if GATE_TYPE == "predio":
            threading.Thread(target=asyncio.run, args=(ws_monitoring_worker(streamer),), daemon=True).start()
            print(f"[*] Modo PREDIO: Streaming activo en {GATE_ID}. Escaneo desactivado.")
            while True:
                time.sleep(1)

        engine = ALPREngine()
        
        if GATE_TYPE in ("entrada", "salida", "patente"):
            threading.Thread(target=engine.ocr_worker, daemon=True).start()
            
        threading.Thread(target=asyncio.run, args=(ws_monitoring_worker(streamer),), daemon=True).start()
        print(f"[*] Bucle de escaneo activo en {GATE_ID} (Modo: {GATE_TYPE.upper()}). 'Ctrl+C' para salir.")
        
        last_ocr_time = 0
        while True:
            frame = streamer.get_frame()
            if frame is None:
                time.sleep(0.1)
                continue
            now = time.time()

            if GATE_TYPE in ("entrada", "salida", "qr"):
                try:
                    small = cv2.resize(frame, (320, 240))
                    qr_data, _, _ = engine.qr_detector.detectAndDecode(small)
                    if qr_data:
                        engine.send_event("qr", qr_data, frame)
                        last_ocr_time = now
                        time.sleep(0.05)
                        continue
                except Exception:
                    pass

            if GATE_TYPE in ("entrada", "salida", "patente"):
                if now - last_ocr_time > OCR_INTERVAL:
                    if engine.detect_motion(frame):
                        try:
                            if not engine.frame_queue.full():
                                engine.frame_queue.put(frame)
                                last_ocr_time = now
                            else:
                                try:
                                    engine.frame_queue.get_nowait()
                                    engine.frame_queue.put(frame)
                                    last_ocr_time = now
                                except Exception:
                                    pass
                        except Exception:
                            pass
            time.sleep(0.01)
    except Exception as e:
        print(f"[!] Error FATAL en el bucle principal: {e}")
