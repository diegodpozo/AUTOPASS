'''Bucle maestro de ALPR. Coordina la lectura de cuadros, el descarte por inactividad y el encolado hacia el hilo trabajador de OCR.'''


import time								# Importa `time` para medir intervalos (cooldown de
									# OCR, pausas del bucle y logs periodicos)
import asyncio								# Importa `asyncio` porque el worker de WebSocket
									# de monitoreo se ejecuta como corutina dentro de
									# un hilo aparte
import threading							# Importa `threading` para lanzar la captura de
									# video, el OCR y el monitoreo como hilos
									# concurrentes sin bloquear el bucle principal
from alpr.config import VIDEO_SOURCE, GATE_TYPE, GATE_ID, FORCE_OCR, OCR_INTERVAL, AUTO_DETECT_USB
									# Trae de la configuracion los parametros que
									# gobiernan el arranque: fuente de video, tipo y id
									# del porton, OCR forzado e intervalo de OCR
from alpr.camera_detector import resolve_video_source, is_dummy_green_frame
									# Importa el resolvedor inteligente de fuentes
									# y detector de standby verde (DroidCam/OBS)
from alpr.video_streamer import VideoStreamer				# Importa `VideoStreamer`, el componente que abre
									# la camara/stream y entrega frames
from alpr.ocr_engine import ALPREngine, ReadingStatusNotifier		# Importa `ALPREngine` (deteccion+OCR) y
									# `ReadingStatusNotifier` (aviso de lectura) desde
									# el motor de reconocimiento
from alpr.ws_client import ws_monitoring_worker				# Importa `ws_monitoring_worker`, el worker que
									# transmite video y estados al backend por
									# WebSocket

_reading_notifier = ReadingStatusNotifier()				# Crea la instancia global `_reading_notifier`, que
									# avisa cuando hay una lectura en curso para que el
									# canal de monitoreo lo refleje

def run_alpr_service():							# Define `run_alpr_service()`, la funcion que
									# orquesta todo el ciclo de vida del nodo ALPR
    """Ejecuta el ciclo principal del servicio ALPR."""
    active_source, source_log = resolve_video_source(
        configured_source=VIDEO_SOURCE,
        gate_type=GATE_TYPE,
        auto_detect_usb=AUTO_DETECT_USB
    )
    print(f"[ALPR] {source_log}")

    try:								# Abre un `try` para capturar fallos al
									# inicializar la fuente de video
        streamer = VideoStreamer(active_source, target_width=1280).start()
    except Exception as e:						# Captura cualquier excepcion al abrir el stream o la camara
        print(f"[!] Error al iniciar VideoStreamer con fuente {active_source}: {e}")
        if active_source != VIDEO_SOURCE:
            print(f"[INFO] Reintentando con fuente IP configurada: {VIDEO_SOURCE}...")
            active_source = VIDEO_SOURCE
            try:
                streamer = VideoStreamer(active_source, target_width=1280).start()
            except Exception as e2:
                print(f"[!] Error FATAL al iniciar VideoStreamer con IP: {e2}")
                return
        else:
            return
    
    time.sleep(2)							# Espera 2 segundos para dar tiempo a que la camara entregue frames
    initial_frame = streamer.get_frame()				# Obtiene el frame inicial de comprobacion
    if initial_frame is None:						# Comprueba si el streamer entrega frame
        if active_source != VIDEO_SOURCE:
            print(f"[!] Dispositivo USB {active_source} no entregó imagen. Conmutando a fuente IP: {VIDEO_SOURCE}...")
            try:
                streamer.stop()
            except Exception:
                pass
            active_source = VIDEO_SOURCE
            try:
                streamer = VideoStreamer(active_source, target_width=1280).start()
                time.sleep(1)
            except Exception as e:
                print(f"[!] Error al conmutar a IP {active_source}: {e}")
        else:
            print(f"[!] ADVERTENCIA: No se recibe imagen de la fuente {active_source}. Verificá la URL o el dispositivo.")
    elif is_dummy_green_frame(initial_frame):
        print(f"[AVISO] La cámara USB {active_source} está en standby (pantalla verde). Hacé clic en 'Start' en la app DroidCam de tu PC.")

    try:								# Abre el `try` principal que envuelve toda la
									# logica de hilos y el bucle de captura
        if GATE_TYPE == "predio":					# Evalua si el porton es de tipo 'predio': en ese
									# caso la camara solo transmite video, sin ALPR
            threading.Thread(target=asyncio.run, args=(ws_monitoring_worker(streamer),), daemon=True).start()
									# Arranca un hilo daemon que corre
									# `ws_monitoring_worker(streamer)` con asyncio,
									# habilitando solo el streaming de video del
									# predio
            print(f"[OK] Servicio de cámara activo: {GATE_ID} | Modo: PREDIO (Solo Streaming)")
									# Informa por consola que el servicio quedo activo
									# en modo PREDIO (solo streaming) para el porton
									# `GATE_ID`
            while True:							# Entra en un bucle infinito que mantiene vivo el
									# proceso del modo predio sin hacer trabajo
									# adicional
                time.sleep(1)						# Duerme 1 segundo por vuelta para no consumir CPU
									# mientras solo se transmite video

        engine = ALPREngine()						# Instancia `ALPREngine()`, que carga el motor
									# OCR/deteccion de patentes y expone la cola de
									# frames y los detectores
        
        if GATE_TYPE in ("entrada", "salida", "patente"):		# Evalua si el tipo de porton requiere
									# reconocimiento de patente (entrada, salida o
									# patente)
            threading.Thread(target=engine.ocr_worker, daemon=True).start()
									# Lanza un hilo daemon que ejecuta
									# `engine.ocr_worker`, el consumidor que procesa la
									# cola de frames y reconoce patentes
            
        threading.Thread(target=asyncio.run, args=(ws_monitoring_worker(streamer, engine),), daemon=True).start()
									# Arranca el hilo daemon del worker de WebSocket
									# pasandole tambien el engine, para transmitir
									# video y estados de lectura
        motor_txt = engine.engine_type or f"NO DISPONIBLE ({engine.ocr_error})"
									# Calcula `motor_txt`: el tipo de motor OCR activo
									# o un texto de NO DISPONIBLE con el motivo del
									# error
        print(f"[OK] Servicio de cámara activo: {GATE_ID} | Modo: {GATE_TYPE.upper()} | Motor: {motor_txt}")
									# Imprime el estado de arranque con el porton, el
									# modo (GATE_TYPE en mayusculas) y el motor OCR en
									# uso
        
        last_ocr_time = 0						# Inicializa `last_ocr_time` en 0 para controlar
									# cuando corresponde el proximo intento de OCR
        motion_skip_count = 0						# Inicializa `motion_skip_count` en 0, contador de
									# frames descartados por falta de movimiento
        last_motion_log = time.time()					# Inicializa `last_motion_log` con la hora actual
									# para emitir el resumen de frames descartados cada
									# 5 segundos
        while True:							# Inicia el bucle principal infinito que lee frames
									# y decide si correr QR u OCR
            frame = streamer.get_frame()				# Pide el frame mas reciente al `VideoStreamer`
									# para analizarlo en esta vuelta
            if frame is None:						# Comprueba si el frame es None, es decir si aun no
									# hay imagen disponible
                time.sleep(0.1)						# Duerme 0.1 segundos para esperar imagen sin
									# quemar CPU en un bucle apretado
                continue						# Salta a la proxima iteracion cuando no hay frame
									# para procesar
            now = time.time()						# Toma la marca de tiempo actual (`now`) que se
									# usara para cooldowns y comparaciones

            if GATE_TYPE in ("entrada", "salida", "qr"):		# Evalua si el porton maneja QR (entrada, salida o
									# qr) antes de intentar decodificar uno
                try:							# Abre un `try` para que un fallo del detector QR
									# no corte el bucle principal
                    qr_data, _, _ = engine.qr_detector.detectAndDecode(frame)
									# Ejecuta `detectAndDecode` de OpenCV sobre el
									# frame y descompone su resultado en datos, puntos
									# y rectangulo del QR
                    if qr_data:						# Comprueba si el detector devolvio contenido de QR
									# (`qr_data`)
                        qr_text = qr_data[0] if isinstance(qr_data, (list, tuple)) and len(qr_data) > 0 else str(qr_data)
									# Normaliza el contenido: toma el primer elemento
									# si es lista/tupla o convierte el resultado a
									# texto
                        engine.send_event("qr", qr_text, frame)		# Envia el evento de tipo 'qr' al backend con el
									# texto leido y el frame de evidencia
                        last_ocr_time = now				# Actualiza `last_ocr_time` para no repetir
									# analisis inmediatamente despues de un QR valido
                        time.sleep(0.05)				# Duerme 0.05 segundos y libera CPU entre frames
									# cuando ya se proceso un QR
                        continue					# Salta la logica de patente de esta vuelta porque
									# ya hubo un evento QR
                except Exception:					# Captura y descarta excepciones del detector QR
									# para mantener el bucle vivo
                    pass						# Cierra el bloque de manejo QR; `pass` deja la
									# iteracion continuar normalmente

            if GATE_TYPE in ("entrada", "salida", "patente"):		# Evalua si el porton reconoce patentes (entrada,
									# salida o patente)
                if now - last_ocr_time > OCR_INTERVAL:			# Comprueba que haya pasado suficiente tiempo desde
									# el ultimo OCR segun `OCR_INTERVAL`
                    has_motion = FORCE_OCR or engine.detect_motion(frame)
									# Determina `has_motion`: si `FORCE_OCR` esta
									# activo siempre es true, si no consulta
									# `engine.detect_motion(frame)`
                    if has_motion:					# Solo encola el frame para OCR si hay movimiento o
									# si el OCR esta forzado
                        _reading_notifier.notify_reading()		# Avisa al notificador que hay una lectura en
									# curso, para que el canal de monitoreo muestre ese
									# estado
                        try:						# Abre un `try` interno para tolerar errores de la
									# cola sin romper el bucle
                            if not engine.frame_queue.full():		# Comprueba si la cola de frames NO esta llena
									# antes de encolar
                                engine.frame_queue.put(frame)		# Encola el frame para que `ocr_worker` lo procese
                                last_ocr_time = now			# Actualiza `last_ocr_time` marcando que ya se
									# envió un frame a OCR en este instante
                            else:					# Rama `else`: la cola estaba llena y hay que hacer
									# lugar descartando el frame mas antiguo
                                try:					# Abre un `try` para el descarte del frame viejo,
									# que puede fallar si la cola cambio entre medio
                                    engine.frame_queue.get_nowait()	# Saca sin bloquear el frame mas antiguo de la cola
									# para liberar espacio
                                    engine.frame_queue.put(frame)	# Encola el frame actual reemplazando al
									# descartado, priorizando la imagen mas reciente
                                    last_ocr_time = now			# Actualiza `last_ocr_time` tras reemplazar el
									# frame en la cola
                                except Exception:			# Captura y descarta errores al vaciar/encolar si
									# la cola se comporto de forma inesperada
                                    pass				# Cierra el `try` interno de la cola; `pass` evita
									# propagar el error
                        except Exception:				# Captura cualquier error del bloque de encolado
									# para que el bucle no se detenga
                            pass					# Cierra el `try` externo del encolado con `pass`
                    else:						# Rama `else`: no hubo movimiento, asi que no se
									# analiza este frame
                        motion_skip_count += 1				# Incrementa `motion_skip_count` para contabilizar
									# el frame descartado por falta de movimiento
                        if time.time() - last_motion_log >= 5:		# Comprueba si pasaron 5 segundos desde el ultimo
									# resumen para no loguear en cada vuelta
                            print(f"[ALPR] Sin movimiento: {motion_skip_count} frames descartados en los últimos {int(time.time() - last_motion_log)}s")
									# Imprime el resumen de frames descartados por
									# falta de movimiento y el periodo transcurrido
                            motion_skip_count = 0			# Reinicia el contador `motion_skip_count` a 0 tras
									# loguear el resumen
                            last_motion_log = time.time()		# Actualiza `last_motion_log` para medir los
									# proximos 5 segundos desde ahora
            time.sleep(0.01)						# Duerme 0.01 segundos por vuelta para ceder CPU al
									# resto de los hilos
    except Exception as e:						# Captura una excepcion fatal del bucle principal
									# para informarla sin que el proceso muera en
									# silencio
        print(f"[!] Error FATAL en el bucle principal: {e}")		# Imprime el error FATAL del bucle principal
									# indicando que el servicio ALPR fallo en tiempo de
									# ejecucion
