'''Maneja el hilo de captura independiente, reconexión automática ante caídas de red'''


import cv2								# Importa `cv2` (OpenCV), que abre la camara o el
									# stream y entrega los frames de video
import time								# Importa `time` para las pausas de reintento
									# cuando no llega frame del stream
import threading							# Importa `threading` para capturar el video en un
									# hilo propio y proteger el frame con un candado

class VideoStreamer:							# Define la clase `VideoStreamer`, responsable de
									# capturar video en segundo plano y exponer el
									# ultimo frame
    """Captura video en un hilo separado y provee acceso thread-safe al ultimo frame."""

    def __init__(self, source, target_width=1280):			# Define el constructor `__init__` con la `source`
									# (indice o URL) y un ancho objetivo por defecto de
									# 1280 px
        if isinstance(source, str) and source.startswith("http"):	# Detecta si la fuente es una URL que empieza con
									# 'http' para tratarla como stream de red en vez de
									# camara local
            self.cap = cv2.VideoCapture(source, cv2.CAP_FFMPEG)		# Abre el stream HTTP/RTSP con el backend FFmpeg de
									# OpenCV, adecuado para camaras IP
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)			# Limita el buffer del stream a 1 frame para que
									# siempre se lea la imagen mas reciente y no queden
									# atrasadas
            self.cap.set(cv2.CAP_PROP_OPEN_TIMEOUT_MSEC, 5000)		# Fija un timeout de apertura de 5000 ms para no
									# colgarse si la camara de red no responde
            self.cap.set(cv2.CAP_PROP_READ_TIMEOUT_MSEC, 5000)		# Fija un timeout de lectura de 5000 ms, evitando
									# bloqueos indefinidos si el stream se corta
        else:								# Rama `else`: la fuente es un dispositivo local
									# (indice numerico), no una URL
            self.cap = cv2.VideoCapture(source)				# Abre la camara local con `cv2.VideoCapture`
									# usando el indice configurado
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)			# Solicita al dispositivo un ancho de frame de 1280
									# px como resolucion de trabajo
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)			# Solicita una altura de frame de 720 px,
									# completando la resolucion 1280x720 objetivo
        self.target_width = target_width				# Guarda `target_width` para usarlo luego al
									# redimensionar frames que lleguen mas anchos
        self.current_frame = None					# Inicializa `current_frame` en None; guardara el
									# ultimo frame valido recibido
        self.is_running = True						# Activa `is_running` para que el hilo de captura
									# sepa que debe seguir leyendo frames
        self.lock = threading.Lock()					# Crea un `threading.Lock` para sincronizar el
									# acceso al frame entre el hilo de captura y los
									# lectores

    def start(self):							# Define `start()`, que arranca el hilo de captura
									# y devuelve el propio streamer
        threading.Thread(target=self._update, daemon=True).start()	# Lanza el hilo daemon que ejecuta `_update` (el
									# bucle que lee frames) y devuelve inmediatamente
        return self							# Devuelve `self` para poder encadenar la llamada
									# `VideoStreamer(...).start()`

    def _update(self):							# Define `_update()`, el bucle que corre en el hilo
									# y lee frames en forma continua
        retries = 0							# Inicializa `retries` en 0 para contar lecturas
									# fallidas consecutivas sin frame
        while self.is_running:						# Bucle principal: sigue capturando mientras
									# `is_running` siga en True
            try:							# Abre un `try` para que un error de lectura no
									# mate el hilo de captura
                ret, frame = self.cap.read()				# Lee un frame del stream; `ret` indica si la
									# lectura tuvo exito y `frame` es la imagen
                if not ret:						# Comprueba si la lectura fallo (`ret` False) para
									# contarla como reintento
                    retries += 1					# Incrementa el contador de reintentos
									# consecutivos
                    if retries <= 3:					# Solo imprime el aviso los primeros 3 reintentos
									# para no inundar la consola
                        print(f"[VideoStreamer] Frame no recibido (intento {retries}/3). Verificá la URL y que la app IP Webcam esté activa.")
									# Imprime el mensaje pidiendo verificar la URL y
									# que la app IP Webcam este activa
                    time.sleep(1)					# Espera 1 segundo antes de reintentar la lectura
									# del stream
                    continue						# Salta a la proxima vuelta del bucle sin intentar
									# usar un frame invalido
                retries = 0						# Reinicia `retries` a 0 porque la lectura se
									# recupero con exito
                h, w = frame.shape[:2]					# Lee alto y ancho del frame con `frame.shape[:2]`
									# para decidir si hay que redimensionar
                if w > self.target_width:				# Comprueba si el ancho del frame supera el ancho
									# objetivo configurado
                    scale = self.target_width / w			# Calcula el factor de escala para llevar el ancho
									# al valor objetivo
                    new_w = self.target_width				# Fija `new_w` en el ancho objetivo para conservar
									# la proporcion al redimensionar
                    new_h = int(h * scale)				# Calcula `new_h` proporcionalmente para no
									# deformar la imagen
                    frame = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
									# Redimensiona el frame con interpolacion lineal al
									# tamaño calculado, reduciendo el costo de
									# procesamiento
                with self.lock:						# Toma el lock antes de escribir el frame para
									# evitar que un lector lo consulte a medio
									# actualizar
                    self.current_frame = frame				# Guarda el frame procesado como `current_frame`,
									# quedando disponible para los demas hilos
            except Exception as e:					# Captura cualquier excepcion durante la lectura o
									# el redimensionado para mantener el hilo vivo
                print(f"[VideoStreamer] Excepción: {type(e).__name__} - {e}")
									# Imprime el tipo y mensaje de la excepcion del
									# streamer para diagnostico
                time.sleep(1)						# Espera 1 segundo antes de reintentar tras una
									# excepcion

    def get_frame(self):						# Define `get_frame()`, la API thread-safe para
									# obtener el ultimo frame
        with self.lock:							# Toma el lock para leer el frame de forma segura
									# frente al hilo de captura
            return self.current_frame.copy() if self.current_frame is not None else None
									# Devuelve una copia del frame actual (o None si
									# aun no hay imagen), evitando que el lector mute
									# el original

    def stop(self):							# Define `stop()`, que detiene el hilo de captura y
									# libera la camara
        self.is_running = False						# Pone `is_running` en False para que el bucle
									# `_update` termine en su proxima vuelta
        if self.cap and self.cap.isOpened():				# Comprueba que el objeto de captura exista y este
									# abierto antes de liberarlo
            self.cap.release()						# Libera el recurso de la camara/stream con
									# `cap.release()`
