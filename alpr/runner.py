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
        streamer = VideoStreamer(VIDEO_SOURCE, target_width=1280).start()
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
                    qr_data, _, _ = engine.qr_detector.detectAndDecode(frame)
                    if qr_data:
                        qr_text = qr_data[0] if isinstance(qr_data, (list, tuple)) and len(qr_data) > 0 else str(qr_data)
                        engine.send_event("qr", qr_text, frame)
                        last_ocr_time = now
                        time.sleep(0.05)
                        continue
                except Exception:
                    pass

            if GATE_TYPE in ("entrada", "salida", "patente"):
                if now - last_ocr_time > OCR_INTERVAL:
                    has_motion = engine.detect_motion(frame)
                    if has_motion:
                        try:
                            if not engine.frame_queue.full():
                                engine.frame_queue.put(frame)
                                last_ocr_time = now
                                print(f"[ALPR RUNNER] Frame enviado a OCR (queue={engine.frame_queue.qsize()})")
                            else:
                                try:
                                    engine.frame_queue.get_nowait()
                                    engine.frame_queue.put(frame)
                                    last_ocr_time = now
                                except Exception:
                                    pass
                        except Exception:
                            pass
                    else:
                        if int(now) % 10 == 0:
                            print(f"[ALPR RUNNER] Sin movimiento (last_check={int(now)})")
            time.sleep(0.01)
    except Exception as e:
        print(f"[!] Error FATAL en el bucle principal: {e}")
