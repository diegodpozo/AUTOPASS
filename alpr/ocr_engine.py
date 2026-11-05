'''Ejecuta el OCR, valida contra formatos de patentes latinoamericanas y corrige confusiones tipográficas.'''


import cv2								# Importa `cv2` (OpenCV) para manipular frames,
									# detectar QR y dibujar el overlay
import requests								# Importa `requests` para enviar por HTTP los
									# eventos de patente/QR al backend
import time								# Importa `time` para medir tiempos de OCR,
									# cooldowns y ventanas de consenso
import os								# Importa `os` para crear la carpeta de debug donde
									# se guardan imagenes de patentes aceptadas
import re								# Importa `re` para los multiples regex de limpieza
									# y validacion de patentes
import base64								# Importa `base64` para codificar el frame JPEG y
									# enviarlo en el JSON al backend
import queue								# Importa `queue` para la cola thread-safe entre el
									# runner (productor) y el OCR (consumidor)
import threading							# Importa `threading` para lanzar el aviso de
									# lectura en un hilo aparte sin bloquear el bucle
import numpy as np							# Importa `numpy` como `np` para manipular los
									# arreglos de puntos del overlay
OCR_ENGINE_NAME = None							# Inicializa `OCR_ENGINE_NAME` en None; guardara el
									# nombre del motor OCR que se logre importar
OCR_ENGINE_ERROR = None							# Inicializa `OCR_ENGINE_ERROR` en None; acumulara
									# mensajes si falla la importacion de los motores
try:									# Abre un `try` para intentar importar el motor OCR
									# preferido (RapidOCR)
    from rapidocr_onnxruntime import RapidOCR				# Importa `RapidOCR` de `rapidocr_onnxruntime`, el
									# motor OCR rapido basado en ONNX
    OCR_ENGINE_NAME = "RapidOCR"					# Guarda 'RapidOCR' como motor disponible cuando la
									# importacion tuvo exito
except Exception as _e_rapid:						# Captura el fallo de importacion de RapidOCR para
									# intentar el siguiente motor
    OCR_ENGINE_ERROR = f"rapidocr-onnxruntime: {type(_e_rapid).__name__}: {_e_rapid}"
									# Registra el motivo del fallo de RapidOCR en
									# `OCR_ENGINE_ERROR`
    try:								# Abre un `try` dentro del `except` para intentar
									# el motor alternativo (PaddleOCR)
        from paddleocr import PaddleOCR					# Importa `PaddleOCR` como segundo motor OCR
									# disponible
        OCR_ENGINE_NAME = "PaddleOCR"					# Guarda 'PaddleOCR' como motor disponible si la
									# importacion tuvo exito
    except Exception as _e_paddle:					# Captura el fallo de PaddleOCR y acumula el
									# detalle en `OCR_ENGINE_ERROR`
        OCR_ENGINE_ERROR = f"{OCR_ENGINE_ERROR} ; paddleocr: {type(_e_paddle).__name__}: {_e_paddle}"
									# Concatena al error previo el motivo del fallo de
									# PaddleOCR

if not OCR_ENGINE_NAME:							# Comprueba si ningun motor OCR pudo importarse
    print(f"[ALPR] WARNING: Ni rapidocr-onnxruntime ni paddleocr están disponibles. ({OCR_ENGINE_ERROR})")
									# Imprime la advertencia de que no hay motor OCR
									# instalado, indicando como instalarlo

class ReadingStatusNotifier:						# Define la clase `ReadingStatusNotifier`, que
									# avisa al backend que la camara esta leyendo
    """NOTIFICA AL BACKEND QUE LA CAMARA ESTA LEYENDO ACTIVAMENTE UNA PATENTE.
    Con debounce para no spamear (max 1 cada INTERVALO s) y en hilo aparte
    para no bloquear el bucle de captura de frames del runner."""

    def __init__(self, interval: float = 1.5):				# Define el constructor `__init__` con un intervalo
									# de debounce por defecto de 1.5 segundos
        self.interval = interval					# Guarda el intervalo de debounce en
									# `self.interval`
        self._last_notify = 0.0						# Inicializa `_last_notify` en 0.0 para registrar
									# el ultimo envio de aviso

    def notify_reading(self):						# Define `notify_reading()`, el metodo que avisa
									# que hay una lectura en curso
        now = time.time()						# Toma la hora actual para el control de debounce
        if now - self._last_notify < self.interval:			# Si no paso suficiente tiempo desde el ultimo
									# aviso, no envia nada (debounce)
            return							# Retorna sin enviar cuando el aviso esta dentro
									# del intervalo
        self._last_notify = now						# Actualiza `_last_notify` con la hora del aviso
									# efectivo
        threading.Thread(target=self._fire, daemon=True).start()	# Lanza un hilo daemon que ejecuta `_fire` para no
									# bloquear el bucle de captura

    def _fire(self):							# Define `_fire()`, que realiza el POST real al
									# backend
        try:								# Abre un `try` para que un fallo de red no
									# propague error
            requests.post(f"{BACKEND_URL}/v1/system/camera-reading/{GATE_ID}", timeout=0.8,
									# Envia un POST al endpoint de lectura de camara
									# del porton `GATE_ID`, con timeout corto de 0.8 s
                          headers={"X-Node-Secret": ALPR_NODE_SECRET} if ALPR_NODE_SECRET else None)
									# Agrega la cabecera `X-Node-Secret` si hay secreto
									# configurado, autenticando el nodo
        except Exception:						# Captura cualquier excepcion del envio del aviso
									# de lectura
            pass							# Ignora el error silenciosamente, ya que el aviso
									# es solo informativo

from concurrent.futures import ThreadPoolExecutor			# Importa `ThreadPoolExecutor` para despachar los
									# envios HTTP en un pool de hilos
from alpr.config import (						# Empieza el import multiple de la configuracion
									# ALPR
    GATE_ID, GATE_TYPE, BACKEND_URL, ALPR_NODE_SECRET, COOLDOWN_SECONDS,
									# Trae `GATE_ID`, `GATE_TYPE`, `BACKEND_URL` y
									# `ALPR_NODE_SECRET` para el envio de eventos
    CONFIDENCE_THRESHOLD, FRAME_QUEUE_MAXSIZE, CONSENSUS_REQUIRED,	# Trae los parametros de consenso:
									# `COOLDOWN_SECONDS`, `CONFIDENCE_THRESHOLD` y el
									# tamaño de la cola
    CONSENSUS_WINDOW, LATAM_PLATE_PATTERN, MOTO_PATTERN, MOTO_MIN_CONFIDENCE,
									# Trae los patrones y umbrales de motos:
									# `LATAM_PLATE_PATTERN`, `MOTO_PATTERN`,
									# `MOTO_MIN_CONFIDENCE`
    ENABLE_MOTO_RECOGNITION						# Trae `ENABLE_MOTO_RECOGNITION` para saber si las
									# motos estan habilitadas
)									# Cierra el import multiple
from alpr.preprocessor import ImagePreprocessor				# Importa `ImagePreprocessor` con las utilidades de
									# ROI y franja MERCOSUR

MAPA_LETRAS = {'0': 'O', '1': 'I', '2': 'Z', '4': 'A', '5': 'S', '6': 'G', '8': 'B'}
									# Define `MAPA_LETRAS`: digitos frecuentemente
									# confundidos por OCR mapeados a su letra
									# equivalente
MAPA_DIGITOS = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'A': '4', 'S': '5', 'G': '6', 'B': '8'}
									# Define `MAPA_DIGITOS`: letras confundidas por OCR
									# mapeadas a su digito equivalente

def CorregirLetra(caracter: str) -> str:				# Define `CorregirLetra(caracter)`: convierte un
									# digito confundido en su letra equivalente
    """REEMPLAZA DIGITOS COMUNES POR SUS LETRAS EQUIVALENTES EN POSICIONES ALFABETICAS."""
    return MAPA_LETRAS.get(caracter, caracter)				# Devuelve el caracter corregido por `MAPA_LETRAS`
									# o el mismo si no esta en el mapa

def CorregirDigito(caracter: str) -> str:				# Define `CorregirDigito(caracter)`: convierte una
									# letra confundida en su digito equivalente
    """REEMPLAZA LETRAS COMUNES POR SUS DIGITOS EQUIVALENTES EN POSICIONES NUMERICAS."""
    return MAPA_DIGITOS.get(caracter, caracter)				# Devuelve el caracter corregido por `MAPA_DIGITOS`
									# o el mismo si no esta en el mapa

def CorregirPatente(texto: str) -> str:					# Define `CorregirPatente(texto)`: aplica
									# desambiguacion posicional segun el formato
									# esperado
    """APLICA DESAMBIGUACION POSICIONAL DE CARACTERES PARA FORMATOS MERCOSUR Y CLASICOS."""
    if not texto:							# Si el texto viene vacio, corta temprano
        return ""							# Devuelve cadena vacia para entrada vacia
    t = re.sub(r'[^A-Z0-9]', '', texto.upper())				# Pasa a mayusculas y elimina todo lo que no sea
									# A-Z o 0-9, dejando solo el nucleo de la patente

    # REMOVER MARCAS DE AGUA Y TEXTOS DE ENCABEZADO NACIONALES
    t = re.sub(r'^(ARGENTINA|REPUBLICA|MERCOSUR|BRASIL|URUGUAY|PARAGUAY|TINA|IINA)+', '', t)
									# Elimina prefijos como ARGENTINA, REPUBLICA,
									# MERCOSUR, etc., que el OCR a veces antepone a la
									# patente
    t = re.sub(r'(ARGENTINA|MERCOSUR|AR)$', '', t)			# Elimina sufijos como ARGENTINA, MERCOSUR o AR que
									# quedan pegados al final de la lectura

    # 1. SI YA CUMPLE CON UN FORMATO ESTRICTO DE 6 O 7 CARACTERES, SE RETORNA DIRECTAMENTE
    patron_estricto = (							# Comienza a construir `patron_estricto`, el regex
									# de formatos validos segun configuracion de motos
        r'^[A-Z]{2}\d{3}[A-Z]{2}$|'					# Incluye el formato auto Mercosur argentino
									# `AB123CD`
        r'^[A-Z]{3}\d{3}$|'						# Incluye el formato auto clasico `ABC123`
        r'^[A-Z]{3}\d[A-Z]\d{2}$' if not ENABLE_MOTO_RECOGNITION else	# Tercera opcion con `if not
									# ENABLE_MOTO_RECOGNITION else`, que bifurca el
									# patron segun motos habilitadas
        r'^[A-Z]{2}\d{3}[A-Z]{2}$|'					# Si motos estan habilitadas, repite el patron auto
									# Mercosur argentino
        r'^[A-Z]{3}\d{3}$|'						# Repite el formato auto clasico `ABC123`
        r'^[A-Z]\d{3}[A-Z]{3}$|'					# Agrega el formato de moto Mercosur `A123BCD`
        r'^\d{3}[A-Z]{3}$|'						# Agrega el formato de moto clasica `123ABC`
        r'^[A-Z]{3}\d[A-Z]\d{2}$'					# Agrega el formato Brasil `ABC1D23`, cerrando el
									# patron del modo con motos
    )									# Cierra la construccion del patron estricto
    if re.match(patron_estricto, t):					# Si el texto ya cumple un formato estricto, lo
									# devuelve tal cual sin corregir nada
        return t							# Devuelve el texto valido de forma directa

    if len(t) == 7:							# Evalua el caso de patente de 7 caracteres, donde
									# se prueban los formatos largos
        # 1. MOTO MERCOSUR ARGENTINA: A NNN LLL (EJ: A012BCD, AO12BCD)
        if t[0] == 'A' and (t[4:].isalpha() or (t[5].isalpha() and t[6].isalpha())) and (t[1].isdigit() or t[1] in ('O', 'Q', 'D', 'I', 'L', 'Z', 'S')):
									# Comprueba el patron de moto Mercosur argentina:
									# primer caracter A, letras al final y digito (o
									# simil) en la segunda posicion
            cand_moto = (						# Comienza a construir la candidata `cand_moto`
									# para moto Mercosur argentina
                'A' +							# Fija la primera letra como 'A', que identifica a
									# la moto Mercosur argentina
                CorregirDigito(t[1]) + CorregirDigito(t[2]) + CorregirDigito(t[3]) +
									# Corrige los tres digitos centrales con
									# `CorregirDigito`
                CorregirLetra(t[4]) + CorregirLetra(t[5]) + CorregirLetra(t[6])
									# Corrige las tres letras finales con
									# `CorregirLetra`
            )								# Cierra la construccion de `cand_moto`
            if re.match(r'^[A-Z]\d{3}[A-Z]{3}$', cand_moto):		# Valida que la candidata coincida con el formato
									# de moto `A123BCD`
                return cand_moto					# Devuelve la patente de moto corregida cuando el
									# formato es valido

        # 2. AUTO MERCOSUR ARGENTINA: LL NNN LL (EJ: AA123BB, AAI23BB, AA12OBB)
        cand_auto = (							# Comienza a construir `cand_auto` para auto
									# Mercosur argentino
            CorregirLetra(t[0]) + CorregirLetra(t[1]) +			# Corrige las dos primeras letras con
									# `CorregirLetra`
            CorregirDigito(t[2]) + CorregirDigito(t[3]) + CorregirDigito(t[4]) +
									# Corrige los tres digitos centrales con
									# `CorregirDigito`
            CorregirLetra(t[5]) + CorregirLetra(t[6])			# Corrige las dos letras finales con
									# `CorregirLetra`
        )								# Cierra la construccion de `cand_auto`
        if re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$', cand_auto):		# Valida que la candidata coincida con el formato
									# auto `AB123CD`
            return cand_auto						# Devuelve la patente de auto corregida cuando el
									# formato es valido

        # 3. MOTO MERCOSUR ARGENTINA GENERAL
        cand_moto = (							# Construye la candidata general de moto
									# corrigiendo posicion por posicion
            CorregirLetra(t[0]) +					# Corrige la primera letra con `CorregirLetra`
            CorregirDigito(t[1]) + CorregirDigito(t[2]) + CorregirDigito(t[3]) +
									# Corrige los tres digitos centrales con
									# `CorregirDigito`
            CorregirLetra(t[4]) + CorregirLetra(t[5]) + CorregirLetra(t[6])
									# Corrige las letras finales con `CorregirLetra`
        )								# Cierra la construccion de la candidata de moto
									# general
        if re.match(r'^[A-Z]\d{3}[A-Z]{3}$', cand_moto):		# Valida que la candidata coincida con el formato
									# de moto `A123BCD`
            return cand_moto						# Devuelve la patente de moto general corregida
									# cuando el formato es valido

        # 4. AUTO BRASIL MERCOSUR: LLL N L NN (EJ: ABC1D23)
        cand_br = (							# Comienza a construir `cand_br` para el formato
									# Brasil
            CorregirLetra(t[0]) + CorregirLetra(t[1]) + CorregirLetra(t[2]) +
									# Corrige las tres primeras letras con
									# `CorregirLetra`
            CorregirDigito(t[3]) +					# Corrige el digito central con `CorregirDigito`
            CorregirLetra(t[4]) +					# Corrige la letra intermedia con `CorregirLetra`
            CorregirDigito(t[5]) + CorregirDigito(t[6])			# Corrige los dos digitos finales con
									# `CorregirDigito`
        )								# Cierra la construccion de `cand_br`
        if re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', cand_br):		# Valida que la candidata coincida con el formato
									# Brasil `ABC1D23`
            return cand_br						# Devuelve la patente Brasil corregida cuando el
									# formato es valido

    elif len(t) == 6:							# Rama `elif` para patentes de 6 caracteres, que
									# cubre los formatos clasicos
        # 1. AUTO CLASICO ARGENTINO: LLL NNN (ULTIMOS 3 SON DIGITOS / LETRAS AL INICIO)
        if t[4].isdigit() or t[5].isdigit() or (t[1].isalpha() and t[2].isalpha()):
									# Comprueba indicios del formato auto clasico
									# (digitos al final o letras al inicio)
            cand_auto_old = (						# Comienza a construir `cand_auto_old` para el auto
									# clasico
                CorregirLetra(t[0]) + CorregirLetra(t[1]) + CorregirLetra(t[2]) +
									# Corrige las tres primeras letras con
									# `CorregirLetra`
                CorregirDigito(t[3]) + CorregirDigito(t[4]) + CorregirDigito(t[5])
									# Corrige los tres digitos finales con
									# `CorregirDigito`
            )								# Cierra la construccion de `cand_auto_old`
            if re.match(r'^[A-Z]{3}\d{3}$', cand_auto_old):		# Valida que la candidata coincida con el formato
									# auto clasico `ABC123`
                return cand_auto_old					# Devuelve el auto clasico corregido cuando el
									# formato es valido

        # 2. MOTO CLASICA ARGENTINA: NNN LLL (ULTIMOS 3 SON LETRAS / DIGITOS AL INICIO)
        if t[4].isalpha() or t[5].isalpha() or (t[1].isdigit() and t[2].isdigit()):
									# Comprueba indicios del formato moto clasica
									# (letras al final o digitos al inicio)
            cand_moto_old = (						# Comienza a construir `cand_moto_old` para la moto
									# clasica
                CorregirDigito(t[0]) + CorregirDigito(t[1]) + CorregirDigito(t[2]) +
									# Corrige los tres primeros digitos con
									# `CorregirDigito`
                CorregirLetra(t[3]) + CorregirLetra(t[4]) + CorregirLetra(t[5])
									# Corrige las tres letras finales con
									# `CorregirLetra`
            )								# Cierra la construccion de `cand_moto_old`
            if re.match(r'^\d{3}[A-Z]{3}$', cand_moto_old):		# Valida que la candidata coincida con el formato
									# moto clasica `123ABC`
                return cand_moto_old					# Devuelve la moto clasica corregida cuando el
									# formato es valido

    return t								# Devuelve el texto (corregido o no) como ultimo
									# recurso cuando ninguna regla aplico

class ALPREngine:							# Define la clase `ALPREngine`, el motor principal
									# de vision artificial
    """Motor principal de vision artificial: RapidOCR / PaddleOCR, QR, consenso y despacho de eventos."""

    def __init__(self):							# Define el constructor `__init__` del motor ALPR
        self.reader = None						# Inicializa `self.reader` en None; guardara el
									# objeto OCR cargado
        self.engine_type = None						# Inicializa `self.engine_type` en None; guardara
									# el nombre del motor activo
        self.ocr_error = OCR_ENGINE_ERROR or "No hay un motor OCR instalado. Ejecuta: pip install rapidocr-onnxruntime"
									# Prepara `self.ocr_error` con el error de
									# importacion previo o un mensaje con instrucciones
									# de instalacion
        if OCR_ENGINE_NAME == "RapidOCR":				# Si el motor importado era RapidOCR, intenta
									# cargarlo
            try:							# Abre un `try` para capturar fallos de
									# inicializacion de RapidOCR
                self.reader = RapidOCR()				# Instancia `RapidOCR()`, cargando el modelo OCR en
									# memoria
                self.engine_type = "RapidOCR"				# Marca `engine_type` como 'RapidOCR'
                self.ocr_error = None					# Limpia `ocr_error` porque el motor quedo
									# operativo
            except Exception as e:					# Captura el fallo al inicializar RapidOCR
                self.ocr_error = f"RapidOCR: {type(e).__name__}: {e}"	# Registra en `ocr_error` el detalle del fallo de
									# RapidOCR
        elif OCR_ENGINE_NAME == "PaddleOCR":				# Rama `elif`: si el motor importado era PaddleOCR,
									# se inicializa ese
            try:							# Abre un `try` para capturar fallos de PaddleOCR
                self.reader = PaddleOCR(				# Instancia `PaddleOCR` desactivando clasificacion
									# de orientacion y unwarping para cargar mas
									# rapido
                    use_doc_orientation_classify=False,			# Desactiva la clasificacion de orientacion de
									# documento
                    use_doc_unwarping=False,				# Desactiva el enderezado de documento (unwarping)
                    use_textline_orientation=False			# Desactiva la deteccion de orientacion de linea de
									# texto
                )							# Cierra la configuracion del constructor de
									# PaddleOCR
                self.engine_type = "PaddleOCR"				# Marca `engine_type` como 'PaddleOCR'
                self.ocr_error = None					# Limpia `ocr_error` porque el motor quedo
									# operativo
            except Exception as e:					# Captura el fallo al inicializar PaddleOCR
                self.ocr_error = f"PaddleOCR: {type(e).__name__}: {e}"	# Registra en `ocr_error` el detalle del fallo de
									# PaddleOCR

        self.qr_detector = cv2.QRCodeDetector()				# Crea `self.qr_detector` con el detector de QR de
									# OpenCV
        self.frame_queue = queue.Queue(maxsize=FRAME_QUEUE_MAXSIZE)	# Crea la `frame_queue` con tamaño maximo
									# `FRAME_QUEUE_MAXSIZE` para los frames a analizar
        self.vote_buffer = []						# Inicializa `vote_buffer` vacio para acumular
									# votos de consenso
        self.last_validated_plate = ""					# Inicializa `last_validated_plate` vacio para el
									# control de duplicados
        self.last_validation_time = 0					# Inicializa `last_validation_time` en 0 para medir
									# el cooldown
        self.is_running = True						# Activa `is_running` para que el worker OCR siga
									# procesando
        self.executor = ThreadPoolExecutor(max_workers=3)		# Crea un `ThreadPoolExecutor` con 3 workers para
									# despachar los POST al backend en paralelo
        self.prev_gray = None						# Inicializa `prev_gray` en None para el frame
									# previo de la deteccion de movimiento
        self.active_detections = []					# Inicializa `active_detections` vacio, con las
									# detecciones para dibujar el overlay
        self.last_detection_time = 0					# Inicializa `last_detection_time` en 0 para saber
									# si las detecciones estan frescas
        self.accepted_event = None					# Inicializa `accepted_event` en None, con la
									# ultima patente aceptada para el banner

    def flush_queue(self):						# Define `flush_queue()`: descarta los frames
									# obsoletos acumulados en la cola
        """Descarta todos los frames obsoletos acumulados en la cola de escaneo."""
        try:								# Abre un `try` para que la cola no cause errores
									# al vaciarla
            while not self.frame_queue.empty():				# Repite mientras la cola no este vacia
                try:							# Abre un `try` interno para extraer sin bloquear
                    self.frame_queue.get_nowait()			# Extrae un frame con `get_nowait` para
									# descartarlo
                except Exception:					# Captura la excepcion si la cola se vacia entre la
									# comprobacion y el get
                    break						# Rompe el bucle interno cuando la cola ya no tiene
									# elementos
        except Exception:						# Captura cualquier error externo del vaciado
            pass							# Ignora el error con `pass`; el vaciado es
									# best-effort

    def detect_motion(self, frame) -> bool:				# Define `detect_motion(frame)`: detecta variacion
									# significativa entre frames consecutivos
        """Detecta variacion significativa entre frames consecutivos en la zona de patente."""
        try:								# Abre un `try` para tolerar frames invalidos
            h, w = frame.shape[:2]					# Lee alto y ancho del frame
            roi = frame[int(h*0.25):int(h*0.85), int(w*0.10):int(w*0.90)]
									# Recorta la zona de la patente (25%-85% alto,
									# 10%-90% ancho) como ROI de deteccion
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)		# Convierte la ROI a escala de grises
            gray = cv2.GaussianBlur(gray, (21, 21), 0)			# Aplica un desenfoque gaussiano 21x21 para reducir
									# ruido antes de comparar
            if self.prev_gray is None:					# Si no hay frame previo, inicializa la referencia
                self.prev_gray = gray					# Guarda el gris actual como `prev_gray`
                return True						# Devuelve True en el primer frame, asumiendo
									# movimiento para inicializar
            diff = cv2.absdiff(self.prev_gray, gray)			# Calcula la diferencia absoluta entre el gris
									# previo y el actual
            self.prev_gray = gray					# Actualiza `prev_gray` con el gris actual para el
									# proximo analisis
            non_zero = cv2.countNonZero(cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)[1])
									# Cuenta los pixeles que cambiaron por encima del
									# umbral 25
            return non_zero > 800					# Devuelve True si mas de 800 pixeles cambiaron,
									# indicando movimiento en la zona
        except Exception:						# Captura cualquier error del analisis de
									# movimiento
            return True							# Devuelve True ante error, priorizando intentar
									# OCR por seguridad

    def _ocr_single_roi(self, roi_img):					# Define `_ocr_single_roi(roi_img)`: corre el OCR
									# sobre un recorte
        """Ejecuta OCR sobre una ROI recortada."""
        if roi_img is None or roi_img.size == 0:			# Si la ROI es None o esta vacia, devuelve listas
									# vacias
            return [], [], []						# Devuelve tres listas vacias (textos, scores,
									# poligonos)
        if self.reader is None or self.engine_type is None:		# Si no hay motor OCR o engine_type, no puede
									# procesar
            return [], [], []						# Devuelve listas vacias cuando el motor no esta
									# disponible
        try:								# Abre un `try` para tolerar fallos del OCR
            h, w = roi_img.shape[:2]					# Lee alto y ancho de la ROI
            if h < 80 and h > 0:					# Si la ROI es muy baja (menos de 80 px), la escala
									# para que el OCR tenga mejor resolucion vertical
                scale = 80.0 / h					# Calcula el factor para llevar la altura a 80 px
                roi_img = cv2.resize(roi_img, (int(w * scale), 80), interpolation=cv2.INTER_CUBIC)
									# Redimensiona la ROI a altura 80 con interpolacion
									# cubica
            if self.engine_type == "RapidOCR":				# Rama para el motor RapidOCR
                result, _ = self.reader(roi_img)			# Ejecuta el OCR de RapidOCR sobre la ROI
                if not result:						# Si no hay resultados, devuelve listas vacias
                    return [], [], []					# Devuelve vacio cuando RapidOCR no detecto texto
                texts = [res[1] for res in result]			# Extrae los textos de cada resultado
                scores = [float(res[2]) for res in result]		# Extrae las confianzas como floats
                polys = [res[0] for res in result]			# Extrae los poligonos (cajas) de cada texto
                return texts, scores, polys				# Devuelve textos, scores y poligonos de RapidOCR
            elif self.engine_type == "PaddleOCR":			# Rama `elif` para el motor PaddleOCR
                result = self.reader.ocr(roi_img, cls=False)		# Ejecuta `reader.ocr` de PaddleOCR sin
									# clasificador de orientacion
                if not result or not result[0]:				# Si PaddleOCR no devolvio resultados, corta
                    return [], [], []					# Devuelve vacio cuando no hay texto detectado
                texts = [line[1][0] for line in result[0]]		# Extrae los textos del formato anidado de
									# PaddleOCR
                scores = [float(line[1][1]) for line in result[0]]	# Extrae las confianzas como floats
                polys = [line[0] for line in result[0]]			# Extrae los poligonos de cada linea
                return texts, scores, polys				# Devuelve textos, scores y poligonos de PaddleOCR
        except Exception as e:						# Captura cualquier error durante el OCR
            print(f"[ALPR OCR] Error {self.engine_type}: {type(e).__name__} - {e}")
									# Imprime el error del motor OCR con su tipo y
									# mensaje
            return [], [], []						# Devuelve listas vacias ante error, para no cortar
									# el worker

    def ocr_worker(self):						# Define `ocr_worker()`: el consumidor que procesa
									# la cola de frames y reconoce patentes
        if self.reader is None:						# Si no hay motor OCR cargado, no tiene sentido
									# arrancar el worker
            print(f"[ALPR OCR] MOTOR NO DISPONIBLE: {self.ocr_error or 'ningún motor OCR importable'}")
									# Imprime que el motor no esta disponible junto con
									# el motivo
            return							# Termina el worker cuando no hay OCR
        full_7_pattern = re.compile(					# Compila `full_7_pattern`, el regex que busca
									# patentes completas de 7 caracteres (incluye
									# varios formatos)
            r'[A-Z]{2}\d{3}[A-Z]{2}|[A-Z]{3}\d[A-Z]\d{2}|[A-Z]{3}\d{4}|[A-Z]{4}\d{3}|\d{3}[A-Z]{4}|[A-Z]\d{3}[A-Z]{3}'
									# Define las alternativas del patron de patente
									# completa (Mercosur, clasico, Uruguay, Paraguay y
									# moto)
        )								# Cierra la compilacion de `full_7_pattern`
        HEADER_NOISE_WORDS = re.compile(				# Compila `HEADER_NOISE_WORDS`, el regex de
									# palabras de encabezado/marca de agua a limpiar
            r'\b(REPUBLICA|ARGENTINA|MERCOSUR|BRASIL|URUGUAY|PARAGUAY|GENTINA|TINA|REPU|MERCO|SUR)\b',
									# Lista las palabras ruido (REPUBLICA, ARGENTINA,
									# MERCOSUR, etc.) a remover de las lecturas
            re.IGNORECASE						# Activa la busqueda sin distinguir mayusculas
        )								# Cierra la compilacion de `HEADER_NOISE_WORDS`

        while self.is_running:						# Bucle principal del worker: procesa mientras el
									# engine siga activo
            try:							# Abre un `try` para tolerar cualquier error de un
									# frame individual
                frame = self.frame_queue.get(timeout=1)			# Toma un frame de la cola esperando hasta 1
									# segundo
                t_start = time.time()					# Marca `t_start` para medir el tiempo de OCR de
									# este frame

                # Descarte de frames en negro / tapados
                gray_check = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)	# Convierte el frame a gris para medir su
									# luminosidad media
                if cv2.mean(gray_check)[0] < 12:			# Si el brillo medio es menor a 12 (frame casi
									# negro/tapado), descarta el frame
                    self.vote_buffer = []				# Vacia el `vote_buffer` porque una imagen negra no
									# aporta votos validos
                    continue						# Salta a la proxima vuelta del bucle

                qr_data, _, _ = self.qr_detector.detectAndDecode(frame)
									# Intenta detectar y decodificar un codigo QR en el
									# frame
                if qr_data:						# Si se detecto contenido de QR, procesarlo
                    qr_text = qr_data[0] if isinstance(qr_data, (list, tuple)) and len(qr_data) > 0 else str(qr_data)
									# Normaliza el contenido del QR a texto
                    elapsed = time.time() - t_start			# Calcula el tiempo transcurrido desde `t_start`
									# hasta ahora
                    print(f"[ALPR] Código QR leído: {qr_text[:80]}")	# Imprime el QR leido (recortado a 80 caracteres)
									# para diagnostico
                    self.send_event("qr", qr_text, frame, ocr_time=elapsed)
									# Envia el evento de tipo 'qr' al backend con el
									# texto y el frame de evidencia
                    time.sleep(1)					# Espera 1 segundo para no repetir la lectura
									# inmediata del mismo QR
                    continue						# Salta a la proxima vuelta porque ya se proceso el
									# QR

                h, w = frame.shape[:2]					# Lee alto y ancho del frame para recortar la ROI
									# principal
                main_roi = frame[int(h*0.15):int(h*0.92), int(w*0.05):int(w*0.95)]
									# Recorta el ROI principal con margenes (15%-92%
									# alto, 5%-95% ancho)

                is_mercosur = ImagePreprocessor.is_mercosur_candidate(main_roi)
									# Analiza si el ROI tiene franja azul MERCOSUR con
									# `is_mercosur_candidate`
                if is_mercosur:						# Si es MERCOSUR, conviene recortar la franja azul
									# antes del OCR
                    main_roi = ImagePreprocessor.crop_below_blue(main_roi)
									# Recorta el ROI por debajo de la franja azul,
									# mejorando la lectura del texto

                texts, scores, polys = self._ocr_single_roi(main_roi)	# Ejecuta el OCR sobre el ROI principal y obtiene
									# textos, scores y poligonos
                t_ocr = time.time() - t_start				# Mide el tiempo de OCR transcurrido desde
									# `t_start`

                if not texts:						# Si el OCR no devolvio textos, descarta el frame
                    continue						# Salta a la proxima vuelta

                detections = []						# Inicializa `detections` con las lecturas limpias
									# de este frame
                for i, text in enumerate(texts):			# Recorre cada texto detectado con su indice
                    t = text.strip()					# Quita espacios alrededor del texto OCR
                    if not t or len(t) < 2:				# Descarta textos vacios o de menos de 2
									# caracteres, que no pueden ser patente
                        continue					# Salta los textos demasiado cortos
                    # Limpiar texto del borde/cabecera (ej: ARGENTINA, REPUBLICA, TINA)
                    clean_header_text = HEADER_NOISE_WORDS.sub('', t.upper()).strip()
									# Remueve esas palabras de encabezado del texto en
									# mayusculas
                    if not clean_header_text or len(clean_header_text) < 2:
									# Si el texto limpio queda vacio o muy corto, lo
									# descarta
                        continue					# Salta el texto que era solo encabezado
                    conf = float(scores[i]) if i < len(scores) else 0.0
									# Obtiene la confianza de la deteccion (0.0 si no
									# hay score)
                    if i < len(polys):					# Si hay poligono para esa deteccion, lo convierte
									# a lista de puntos enteros
                        bbox = [[int(p[0]), int(p[1])] for p in polys[i]]
									# Convierte cada punto del poligono a coordenadas
									# enteras
                    else:						# Rama `else`: si no hay poligono, usa una caja por
									# defecto
                        bbox = [[0,0],[10,0],[10,10],[0,10]]		# Asigna una caja por defecto 10x10 para no romper
									# el overlay
                    detections.append({"text": clean_header_text, "confidence": conf, "bbox": bbox})
									# Agrega la deteccion limpia (texto, confianza y
									# bbox) a la lista

                if not detections:					# Si no quedo ninguna deteccion valida, descarta el
									# frame
                    continue						# Salta a la proxima vuelta

                self.active_detections = detections			# Guarda las detecciones como `active_detections`
									# para el overlay
                self.last_detection_time = time.time()			# Actualiza `last_detection_time` para saber que
									# las detecciones estan frescas

                plate = None						# Inicializa `plate` en None; guardara la patente
									# encontrada
                avg_conf = 0.0						# Inicializa `avg_conf` en 0.0; guardara la
									# confianza promedio asociada

                # 1. PRIORIDAD 1: BUSCAR SI ALGUNA DETECCION INDIVIDUAL CONTIENE UNA PATENTE COMPLETA
                # (EVITA CONCATENAR INDEBIDAMENTE CON TEXTOS DE FONDO O MARCAS DE AGUA)
                for det in detections:					# Recorre cadadeteccion buscando una patente
									# completa en una sola
                    t = re.sub(r'[^A-Z0-9]', '', det["text"].upper())	# Limpia el texto de la deteccion dejando solo A-Z
									# y 0-9
                    t_corr = CorregirPatente(t)				# Corrige posicionalmente la patente con
									# `CorregirPatente`
                    if full_7_pattern.search(t_corr):			# Si el texto corregido contiene una patente
									# completa, la toma
                        plate = full_7_pattern.search(t_corr).group(0)	# Extrae la patente completa encontrada
                        avg_conf = det["confidence"]			# Asocia la confianza de esa deteccion
                        break						# Corta el bucle apenas encuentra una patente
									# completa
                    match_6 = re.search(r'^[A-Z]{3}\d{3}$|^\d{3}[A-Z]{3}$', t_corr)
									# Sino, intenta un formato corto de 6 caracteres
									# clasico
                    if match_6:						# Rama que evalua el formato de 6 caracteres dentro
									# del bucle
                        plate = match_6.group(0)			# Toma la patente de 6 caracteres encontrada
                        avg_conf = det["confidence"]			# Asocia la confianza de la deteccion de 6
									# caracteres
                        break						# Corta el bucle al encontrar una patente valida

                # 2. PRIORIDAD 2: SI NINGUNA DETECCION INDIVIDUAL FUE COMPLETA, PROBAR COMBINAR FRAGMENTOS
                if not plate and len(detections) >= 2:			# Si no hubo patente y hay al menos dos
									# detecciones, intenta combinar fragmentos
                    try:						# Abre un `try` para tolerar errores de
									# combinacion
                        by_x = sorted(detections, key=lambda d: d["bbox"][0][0])
									# Ordena las detecciones por coordenada X
									# (izquierda a derecha)
                        combined_x = "".join(re.sub(r'[^A-Z0-9]', '', d["text"]) for d in by_x)
									# Une los textos en orden horizontal, limpiandolos
                        corrected_x = CorregirPatente(combined_x)	# Corrige la patente combinada posicionalmente
                        match_7 = full_7_pattern.search(corrected_x) or re.search(LATAM_PLATE_PATTERN, corrected_x)
									# Busca una patente completa o un patron
									# latinoamericano en la combinacion
                        if match_7:					# Si la combinacion horizontal produjo una patente,
									# la toma
                            plate = match_7.group(0)			# Extrae la patente de la combinacion
                            avg_conf = sum(d["confidence"] for d in by_x) / max(1, len(by_x))
									# Calcula la confianza promedio de las detecciones
									# combinadas
                    except Exception:					# Captura errores de la combinacion horizontal
                        pass						# Ignora el error y sigue con la siguiente
									# estrategia

                # 3. PRIORIDAD 3: FALLBACK PATRON GENERAL EN DETECCION UNICA
                if not plate:						# Si todavia no hay patente, prueba el patron
									# general sobre cada deteccion
                    for det in detections:				# Recorre cada deteccion
                        t = re.sub(r'[^A-Z0-9]', '', det["text"])	# Limpia el texto dejando solo A-Z y 0-9 (sin pasar
									# a mayusculas explicitamente)
                        t_corr = CorregirPatente(t)			# Corrige la patente posicionalmente
                        match_gen = re.search(LATAM_PLATE_PATTERN, t_corr)
									# Busca el patron latinoamericano general en el
									# texto corregido
                        if match_gen:					# Si el patron general encaja, toma esa patente
                            plate = match_gen.group(0)			# Extrae la patente encontrada
                            avg_conf = det["confidence"]		# Asocia la confianza de la deteccion
                            break					# Corta el bucle al encontrar patente

                if not plate and len(detections) >= 2:			# Si sigue sin patente y hay 2+ detecciones,
									# intenta combinar por Y (lineas apiladas)
                    try:						# Abre un `try` para la combinacion vertical
                        by_y = sorted(detections, key=lambda d: sum(p[1] for p in d["bbox"]) / max(1, len(d["bbox"])))
									# Ordena las detecciones por coordenada Y promedio
									# (arriba a abajo)
                        combined = "".join(re.sub(r'[^A-Z0-9]', '', d["text"]) for d in by_y)
									# Une los textos en orden vertical, limpiandolos
                        corrected_y = CorregirPatente(combined)		# Corrige la patente combinada
                        match = re.search(LATAM_PLATE_PATTERN, corrected_y)
									# Busca el patron latinoamericano en la combinacion
									# vertical
                        if match:					# Si la combinacion vertical produce patente, la
									# toma
                            plate = re.sub(r'[^A-Z0-9]', '', match.group(0))
									# Limpia y extrae la patente de la combinacion
									# vertical
                            avg_conf = sum(d["confidence"] for d in by_y) / max(1, len(by_y))
									# Calcula la confianza promedio de las detecciones
									# combinadas verticalmente
                    except Exception:					# Captura errores de la combinacion vertical
                        pass						# Ignora el error y sigue

                if not plate and len(detections) >= 2:			# Si sigue sin patente y hay 2+ detecciones,
									# reintenta combinacion horizontal (variante 2)
                    try:						# Abre un `try` para la segunda combinacion
									# horizontal
                        by_x = sorted(detections, key=lambda d: d["bbox"][0][0])
									# Ordena las detecciones por X de nuevo
                        combined = "".join(re.sub(r'[^A-Z0-9]', '', d["text"]) for d in by_x)
									# Une los textos de izquierda a derecha
                        corrected_x2 = CorregirPatente(combined)	# Corrige la patente combinada
                        match = re.search(LATAM_PLATE_PATTERN, corrected_x2)
									# Busca el patron latinoamericano
                        if match:					# Si aparece patente, la toma
                            plate = re.sub(r'[^A-Z0-9]', '', match.group(0))
									# Limpia y extrae la patente
                            avg_conf = sum(d["confidence"] for d in by_x) / max(1, len(by_x))
									# Calcula la confianza promedio de esas
									# detecciones
                    except Exception:					# Captura errores de esta combinacion
                        pass						# Ignora el error y sigue

                if not plate:						# Si aun no hay patente, intenta el fallback para
									# placas impresas o descentradas
                    # FALLBACK PARA PATENTES IMPRESAS EN PAPEL / POSICIONES FUERA DE CENTRO
                    # Se exige confianza más alta (0.65) ya que estas son detecciones
                    # de menor calidad obtenidas por caza de contornos
                    FALLBACK_MIN_CONFIDENCE = 0.65			# Define `FALLBACK_MIN_CONFIDENCE` en 0.65, mas
									# estricto que el umbral normal
                    try:						# Abre un `try` para el fallback de ROI por
									# contornos
                        candidates = ImagePreprocessor.find_plate_roi(frame)
									# Obtiene candidatos de ROI con `find_plate_roi`
                        for cand in candidates:				# Recorre cada recorte candidato
                            c_texts, c_scores, _ = self._ocr_single_roi(cand)
									# Ejecuta OCR sobre el candidato
                            if not c_texts:				# Si no hay textos, pasa al siguiente candidato
                                continue				# Salta al siguiente candidato
                            for i, text in enumerate(c_texts):		# Recorre cada texto del candidato
                                t = re.sub(r'[^A-Z0-9]', '', text.strip().upper())
									# Limpia el texto dejando solo A-Z y 0-9 en
									# mayusculas
                                t_corr = CorregirPatente(t)		# Corrige la patente posicionalmente
                                match = re.search(LATAM_PLATE_PATTERN, t_corr)
									# Busca el patron latinoamericano en el texto
                                c_conf = float(c_scores[i]) if i < len(c_scores) else 0.0
									# Obtiene la confianza del texto del candidato
                                if match and c_conf >= FALLBACK_MIN_CONFIDENCE:
									# Si hay patente y la confianza supera 0.65, la
									# acepta
                                    plate = re.sub(r'[^A-Z0-9]', '', match.group(0))
									# Limpia y extrae la patente aceptada del fallback
                                    avg_conf = c_conf			# Asocia la confianza del candidato
                                    break				# Corta el bucle de textos del candidato
                            if plate:					# Si ya hay patente, corta el bucle de candidatos
                                break					# Rompe el bucle de candidatos al encontrar
									# patente
                    except Exception:					# Captura errores del fallback
                        pass						# Ignora el error del fallback

                if not plate:						# Si despues de todo no hay patente, descarta el
									# frame
                    continue						# Salta a la proxima vuelta del worker

                country = ImagePreprocessor.identify_country(plate, is_mercosur)
									# Identifica el pais probable de la patente con
									# `identify_country`

                # EXIGIR ESTRICTAMENTE 6 O 7 CARACTERES Y COMBINACION LETRA-NUMERO
                if len(plate) < 6 or len(plate) > 7 or not re.search(r'[A-Z]', plate) or not re.search(r'\d', plate):
									# Descarta la patente si no tiene 6-7 caracteres o
									# si no contiene al menos una letra y un digito
                    continue						# Salta a la proxima vuelta si el formato es
									# invalido

                now = time.time()					# Toma la hora actual para el voto y la ventana de
									# consenso
                self.vote_buffer.append((plate, avg_conf, now))		# Agrega el voto (patente, confianza, tiempo) al
									# `vote_buffer`
                self.vote_buffer = [(p,c,t) for (p,c,t) in self.vote_buffer if now - t <= CONSENSUS_WINDOW]
									# Elimina del buffer los votos mas viejos que
									# `CONSENSUS_WINDOW`
                same_votes = [v for v in self.vote_buffer if v[0] == plate]
									# Filtra los votos que coinciden con la patente
									# actual

                is_moto = bool(MOTO_PATTERN.match(plate))		# Determina si la patente es de moto con
									# `MOTO_PATTERN`

                # SI LA REGLA DE MOTOS ESTA DESHABILITADA, DESCARTAR DETECCIONES DE MOTOS
                if not ENABLE_MOTO_RECOGNITION and is_moto:		# Si las motos estan deshabilitadas y la patente es
									# de moto, la ignora
                    continue						# Salta a la proxima vuelta para no aceptar motos

                # Filtro de aspecto: un recorte incompleto de auto que coincida con patrón de moto
                # (ej: AC404 de AC404SD) con caja horizontal (> 2.2) es un recorte incompleto
                if is_moto and detections:				# Si parece moto y hay detecciones, calcula el
									# aspecto de la caja para descartar recortes
									# incompletos
                    det = detections[0]					# Toma la primera deteccion para medir su bbox
                    xs = [p[0] for p in det["bbox"]]			# Extrae las coordenadas X del bbox
                    ys = [p[1] for p in det["bbox"]]			# Extrae las coordenadas Y del bbox
                    bbox_w = max(xs) - min(xs)				# Calcula el ancho del bbox
                    bbox_h = max(ys) - min(ys)				# Calcula el alto del bbox
                    if bbox_h > 0 and (bbox_w / bbox_h) > 2.2:		# Si el bbox es muy ancho respecto de su alto
									# (>2.2), descarta la lectura como recorte
									# incompleto
                        continue					# Salta a la proxima vuelta descartando ese falso
									# positivo

                is_valid_format = bool(re.match(			# Comienza a validar el formato final de la patente
									# con un regex estricto
                    r'^[A-Z]{2}\d{3}[A-Z]{2}$|'				# Incluye el formato auto Mercosur argentino
									# `AB123CD`
                    r'^[A-Z]{3}\d{3}$|'					# Incluye el formato auto clasico `ABC123`
                    r'^[A-Z]{3}\d[A-Z]\d{2}$|'				# Incluye el formato Brasil `ABC1D23`
                    r'^[A-Z]{3}\d{4}$|'					# Incluye el formato Uruguay `ABC1234`
                    r'^[A-Z]{4}\d{3}$' if not ENABLE_MOTO_RECOGNITION else
									# Incluye el formato Paraguay `ABCD123` con la
									# bifurcacion de motos
                    r'^[A-Z]{2}\d{3}[A-Z]{2}$|'				# Si las motos estan habilitadas, repite el patron
									# auto Mercosur argentino
                    r'^[A-Z]{3}\d{3}$|'					# Repite el formato auto clasico
                    r'^[A-Z]{3}\d[A-Z]\d{2}$|'				# Repite el formato Brasil
                    r'^[A-Z]{3}\d{4}$|'					# Repite el formato Uruguay
                    r'^[A-Z]{4}\d{3}$|'					# Repite el formato Paraguay
                    r'^[A-Z]{2}\d{3}$|'					# Agrega el formato moto antigua `AB123`
                    r'^[A-Z]{2}\d{3}[A-Z]$|'				# Agrega el formato moto `AB123A`
                    r'^[A-Z]\d{3}[A-Z]{3}$|'				# Agrega el formato moto Mercosur `A123BCD`
                    r'^\d{3}[A-Z]{3}$|'					# Agrega el formato moto clasica `123ABC`
                    r'^\d{3}[A-Z]{4}$',					# Agrega el formato moto Paraguay `123ABCD`,
									# cerrando el patron del modo con motos
                    plate						# Pasa la patente al `re.match` para validar el
									# formato; el resultado se guarda en
									# `is_valid_format`
                ))							# Cierra la llamada al match de validacion

                if not is_valid_format:					# Si el formato no es valido, descarta la lectura
                    continue						# Salta a la proxima vuelta

                # EXIGIR CONSENSO MINIMO PARA EVITAR QUE UN SOLO FOTOGRAMA CON RUIDO DE OCR GENERE INGRESOS
                req_votes = CONSENSUS_REQUIRED				# Fija `req_votes` con el minimo de votos
									# requeridos (`CONSENSUS_REQUIRED`)
                if is_moto:						# Si la patente es de moto, aplica la regla de
									# motos
                    if avg_conf < MOTO_MIN_CONFIDENCE or len(same_votes) < req_votes:
									# Para motos, exige confianza >=
									# `MOTO_MIN_CONFIDENCE` y votos suficientes; si no,
									# descarta
                        continue					# Salta a la proxima vuelta si la moto no alcanza
									# confianza/votos
                else:							# Rama `else` para patentes de autos
                    if avg_conf < CONFIDENCE_THRESHOLD or len(same_votes) < req_votes:
									# Para autos, exige confianza >=
									# `CONFIDENCE_THRESHOLD` y votos suficientes; si
									# no, descarta
                        continue					# Salta a la proxima vuelta si el auto no alcanza
									# confianza/votos

                try:							# Abre un `try` para guardar la imagen de debug sin
									# afectar el flujo
                    if 'ARGENTINA' in country.upper():			# Si el pais incluye 'ARGENTINA', guarda evidencia
									# de la lectura aceptada
                        os.makedirs('alpr_debug', exist_ok=True)	# Crea la carpeta `alpr_debug` si no existe
                        debug_path = os.path.join('alpr_debug', f'accepted_plate_{GATE_ID}_{plate}_{int(time.time()*1000)}.jpg')
									# Arma la ruta del archivo de debug con porton,
									# patente y timestamp
                        cv2.imwrite(debug_path, main_roi)		# Escribe el ROI como imagen JPG de evidencia
                except Exception:					# Captura cualquier error al guardar el debug (por
									# ejemplo permisos)
                    pass						# Ignora el error del guardado de debug

                print(f"[ALPR] Patente aceptada: {plate} [{country}] (Conf: {avg_conf:.2f})")
									# Imprime la patente aceptada con su pais y
									# confianza
                self.accepted_event = {					# Guarda el ultimo evento aceptado (patente, pais,
									# conf, tiempo) para el banner de overlay
                    "plate": plate,					# Fija la patente en `accepted_event`
                    "country": country,					# Fija el pais en `accepted_event`
                    "conf": avg_conf,					# Fija la confianza en `accepted_event`
                    "time": time.time()					# Fija la hora del evento para que el banner se
									# muestre solo 3 segundos
                }							# Cierra la construccion de `accepted_event`
                self.send_event("plate", plate, frame, ocr_time=t_ocr)	# Envia el evento de tipo 'plate' al backend con la
									# patente, el frame y el tiempo de OCR
                self.vote_buffer = []					# Vacia el `vote_buffer` porque ya se confirmo una
									# patente
                self.active_detections = []				# Limpia `active_detections` para reiniciar el
									# overlay
                self.flush_queue()					# Vacia la cola de frames obsoletos tras aceptar un
									# evento

                # Vaciado activo de la cola durante el cooldown de 5 segundos
                for _ in range(10):					# Repite 10 veces para cubrir unos 5 segundos de
									# cooldown
                    time.sleep(0.5)					# Espera 0.5 segundos entre iteraciones
                    self.flush_queue()					# Vacia la cola durante el cooldown para descartar
									# frames del mismo auto
                continue						# Salta a la proxima vuelta del worker

            except queue.Empty:						# Captura el caso de cola vacia (`queue.Empty`)
									# para no cortar el worker
                continue						# Continua el bucle cuando no habia frame en el
									# timeout
            except Exception as e:					# Captura cualquier otra excepcion del
									# procesamiento del frame
                print(f"[ALPR OCR] Exception en ocr_worker: {type(e).__name__} - {e}")
									# Imprime el error del worker OCR con su tipo y
									# mensaje

    def get_frame_with_overlay(self, frame):				# Define `get_frame_with_overlay(frame)`: superpone
									# cajas, HUD y banner al frame para el streaming
        """Superpone bounding boxes, HUD de OCR y banner de confirmacion sobre el frame para el streaming."""
        if frame is None:						# Si el frame es None, lo devuelve sin cambios
            return frame						# Devuelve el frame sin procesar cuando no hay
									# imagen
        
        now = time.time()						# Toma la hora actual para decidir que
									# superposiciones estan vigentes
        active_dets = self.active_detections if (now - self.last_detection_time <= 1.5) else []
									# Usa las detecciones activas solo si son recientes
									# (<= 1.5 s), si no muestra ninguna
        accepted_ev = self.accepted_event if (self.accepted_event and (now - self.accepted_event.get("time", 0) <= 3.0)) else None
									# Usa el evento aceptado solo si ocurrio hace 3.0 s
									# o menos

        if not active_dets and not accepted_ev:				# Si no hay detecciones recientes ni evento
									# aceptado, no hay nada que dibujar
            return frame						# Devuelve el frame original sin overlay

        return self.draw_overlay(frame, active_detections=active_dets, accepted_event=accepted_ev)
									# Delega el dibujo a `draw_overlay` con las
									# detecciones activas y el evento aceptado

    @staticmethod							# Decorador `@staticmethod` que marca
									# `draw_overlay` como metodo estatico
    def draw_overlay(frame, active_detections=None, accepted_event=None):
									# Define `draw_overlay(frame, active_detections,
									# accepted_event)`: dibuja recuadros y etiquetas
        """Dibuja recuadros verde neon, esquinas HUD CCTV y etiqueta de texto sobre el frame."""
        if frame is None:						# Si el frame es None, lo devuelve sin cambios
            return frame						# Devuelve el frame sin procesar cuando no hay
									# imagen

        out_frame = frame.copy()					# Copia el frame para no modificar el original
									# mientras se dibuja
        h, w = out_frame.shape[:2]					# Lee alto y ancho del frame de salida
        roi_offset_x = int(w * 0.05)					# Calcula el offset X del ROI (5%) para alinear las
									# cajas con las coordenadas originales
        roi_offset_y = int(h * 0.15)					# Calcula el offset Y del ROI (15%) para el mismo
									# alineamiento

        if active_detections:						# Si hay detecciones activas, dibuja cada una
            for det in active_detections:				# Recorre cada deteccion activa
                raw_bbox = det.get("bbox", [])				# Obtiene el bbox de la deteccion
                text = det.get("text", "")				# Obtiene el texto detectado
                conf = det.get("confidence", 0.0)			# Obtiene la confianza de la deteccion

                if not raw_bbox or len(raw_bbox) < 4:			# Salta detecciones sin un bbox de al menos 4
									# puntos
                    continue						# Continua con la siguiente deteccion

                pts = []						# Inicializa la lista de puntos del poligono
									# ajustados al frame
                for p in raw_bbox:					# Recorre cada punto del bbox
                    px = int(p[0] + roi_offset_x)			# Ajusta la X sumando el offset del ROI
                    py = int(p[1] + roi_offset_y)			# Ajusta la Y sumando el offset del ROI
                    pts.append([px, py])				# Agrega el punto ajustado

                pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))	# Convierte los puntos a un arreglo numpy con forma
									# de poligono para OpenCV

                # Caja principal (Verde Neón)
                cv2.polylines(out_frame, [pts_arr], isClosed=True, color=(0, 255, 127), thickness=2)
									# Dibuja el contorno del poligono en verde neon con
									# grosor 2

                min_x = max(0, min(p[0] for p in pts))			# Calcula la X minima del poligono, acotada a 0
                max_x = min(w - 1, max(p[0] for p in pts))		# Calcula la X maxima del poligono, acotada al
									# ancho del frame
                min_y = max(0, min(p[1] for p in pts))			# Calcula la Y minima del poligono, acotada a 0
                max_y = min(h - 1, max(p[1] for p in pts))		# Calcula la Y maxima del poligono, acotada al alto
									# del frame
                corner_len = max(6, int((max_x - min_x) * 0.2))		# Calcula la longitud de las esquinas HUD como el
									# 20% del ancho de la caja (minimo 6 px)

                # Esquinas estilo HUD CCTV (Amarillo Dorado)
                hud_color = (0, 215, 255)				# Define el color amarillo dorado `hud_color` para
									# las esquinas
                # Top-Left
                cv2.line(out_frame, (min_x, min_y), (min_x + corner_len, min_y), hud_color, 2)
									# Dibuja la linea horizontal de la esquina superior
									# izquierda
                cv2.line(out_frame, (min_x, min_y), (min_x, min_y + corner_len), hud_color, 2)
									# Dibuja la linea vertical de la esquina superior
									# izquierda
                # Top-Right
                cv2.line(out_frame, (max_x, min_y), (max_x - corner_len, min_y), hud_color, 2)
									# Dibuja la linea horizontal de la esquina superior
									# derecha
                cv2.line(out_frame, (max_x, min_y), (max_x, min_y + corner_len), hud_color, 2)
									# Dibuja la linea vertical de la esquina superior
									# derecha
                # Bottom-Left
                cv2.line(out_frame, (min_x, max_y), (min_x + corner_len, max_y), hud_color, 2)
									# Dibuja la linea horizontal de la esquina inferior
									# izquierda
                cv2.line(out_frame, (min_x, max_y), (min_x, max_y + corner_len), hud_color, 2)
									# Dibuja la linea vertical de la esquina inferior
									# izquierda
                # Bottom-Right
                cv2.line(out_frame, (max_x, max_y), (max_x - corner_len, max_y), hud_color, 2)
									# Dibuja la linea horizontal de la esquina inferior
									# derecha
                cv2.line(out_frame, (max_x, max_y), (max_x, max_y - corner_len), hud_color, 2)
									# Dibuja la linea vertical de la esquina inferior
									# derecha

                # Banner de información de la patente arriba de la caja
                clean_text = re.sub(r'[^A-Z0-9]', '', text)		# Limpia el texto dejando solo A-Z y 0-9 para la
									# etiqueta
                if len(clean_text) >= 3:				# Solo dibuja la etiqueta si el texto tiene al
									# menos 3 caracteres
                    label = f"{clean_text} ({int(conf * 100)}%)"	# Arma la etiqueta con el texto y el porcentaje de
									# confianza
                    (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
									# Mide el ancho y alto del texto con la fuente
									# elegida para dimensionar el fondo
                    label_y = max(min_y - 6, text_h + 6)		# Calcula la Y de la etiqueta, evitando que se
									# salga por arriba

                    # Fondo translúcido oscuro
                    cv2.rectangle(out_frame, (min_x, label_y - text_h - 4), (min_x + text_w + 6, label_y + 4), (15, 23, 42), -1)
									# Dibuja el rectangulo de fondo oscuro relleno
									# detras de la etiqueta
                    cv2.rectangle(out_frame, (min_x, label_y - text_h - 4), (min_x + text_w + 6, label_y + 4), (0, 255, 127), 1)
									# Dibuja el borde verde neon del rectangulo de la
									# etiqueta
                    cv2.putText(out_frame, label, (min_x + 3, label_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
									# Escribe el texto de la etiqueta en blanco sobre
									# el fondo

        if accepted_event and (time.time() - accepted_event.get("time", 0) <= 3.0):
									# Si hay evento aceptado y ocurrio hace 3.0 s o
									# menos, dibuja el banner de confirmacion
            plate = accepted_event.get("plate", "")			# Obtiene la patente del evento aceptado
            country = accepted_event.get("country", "")			# Obtiene el pais del evento aceptado
            conf = accepted_event.get("conf", 0.0)			# Obtiene la confianza del evento aceptado

            banner_h = 38						# Define la altura del banner de confirmacion (38
									# px)
            overlay_sub = out_frame.copy()				# Copia el frame para componer el banner
									# translucido
            cv2.rectangle(overlay_sub, (0, 0), (w, banner_h), (16, 185, 129), -1)
									# Dibuja la franja verde superior rellena donde ira
									# el mensaje
            cv2.addWeighted(overlay_sub, 0.85, out_frame, 0.15, 0, out_frame)
									# Mezcla la franja con el frame (85%/15%) para un
									# efecto translucido

            msg = f"[OK] LECTURA CONFIRMADA: {plate} [{country}] ({int(conf * 100)}%)"
									# Arma el mensaje de lectura confirmada con
									# patente, pais y confianza
            cv2.putText(out_frame, msg, (12, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
									# Escribe el mensaje de confirmacion en blanco
									# sobre la franja

        return out_frame						# Devuelve el frame con el overlay dibujado

    @staticmethod							# Decorador `@staticmethod` que marca
									# `_plate_close` como metodo estatico
    def _plate_close(a: str, b: str, max_dist: int = 1) -> bool:	# Define `_plate_close(a, b, max_dist)`: compara
									# dos patentes permitiendo pocas diferencias
        """Compara dos patentes normalizadas, permitiendo hasta max_dist caracteres de diferencia o coincidencia de bloque numérico."""
        if a == b:							# Si las patentes son identicas, son la misma
									# lectura
            return True							# Devuelve True cuando son exactamente iguales
        # Si comparten los mismos 3+ dígitos (ej: NVZ087 vs VZ087AR vs TINA087), es una variante/alucinación en la misma escena
        digits_a = re.sub(r'\D', '', a)					# Extrae solo los digitos de la primera patente
        digits_b = re.sub(r'\D', '', b)					# Extrae solo los digitos de la segunda patente
        if len(digits_a) >= 3 and digits_a == digits_b:			# Si ambas tienen 3+ digitos y coinciden, se tratan
									# como la misma patente (variante/alucinacion)
            return True							# Devuelve True cuando el bloque numerico coincide
        if len(a) != len(b) or abs(len(a) - len(b)) > max_dist:		# Si cambia la longitud mas alla de `max_dist`, no
									# son cercanas
            return False						# Devuelve False cuando la diferencia de longitud
									# es excesiva
        diff = sum(1 for x, y in zip(a, b) if x != y)			# Cuenta las diferencias caracter por caracter
									# entre ambas patentes
        return diff <= max_dist						# Devuelve True si las diferencias no superan
									# `max_dist`

    def send_event(self, type, data, frame, ocr_time=None):		# Define `send_event(type, data, frame, ocr_time)`:
									# evita duplicados y despacha el envio HTTP
        """Evita duplicados con debounce y delega el envio HTTP al pool de hilos."""
        try:								# Abre un `try` para el control de duplicados
            key = re.sub(r'[^A-Z0-9]', '', str(data)).upper()		# Normaliza el dato (patente o QR) a clave de
									# comparacion en mayusculas
            now = time.time()						# Toma la hora actual para medir el cooldown
            last_key = re.sub(r'[^A-Z0-9]', '', self.last_validated_plate).upper()
									# Normaliza la ultima patente validada como clave
									# de comparacion
            elapsed = now - getattr(self, 'last_validation_time', 0)	# Calcula el tiempo transcurrido desde la ultima
									# validacion
            if elapsed < COOLDOWN_SECONDS and self._plate_close(key, last_key):
									# Si esta dentro del cooldown y la patente es
									# cercana a la anterior, evita el evento duplicado
                return							# Retorna sin enviar cuando el evento es duplicado
            self.last_validated_plate = key				# Guarda la clave como nueva ultima patente
									# validada
            self.last_validation_time = now				# Actualiza el tiempo de la ultima validacion
        except Exception:						# Captura cualquier error del control de
									# duplicados
            pass							# Ignora el error y deja que el evento se envie
									# igual
        self.executor.submit(self._dispatch_request, type, data, frame, ocr_time)
									# Envia el evento al pool de hilos, que ejecuta la
									# peticion HTTP sin bloquear el worker

    def _dispatch_request(self, type, data, frame, ocr_time=None):	# Define `_dispatch_request(type, data, frame,
									# ocr_time)`: codifica el frame y envia el HTTP al
									# backend
        """Codifica el frame y envia la peticion HTTP al backend."""
        t_dispatch = time.time()					# Marca `t_dispatch` para medir el tiempo del
									# envio
        try:								# Abre un `try` para capturar errores de
									# serializacion/envio
            _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 70])
									# Codifica el frame como JPEG con calidad 70
            img_b64 = base64.b64encode(buffer).decode('utf-8')		# Codifica el buffer JPEG en base64 como texto
            is_entry_gate = "salida" not in GATE_TYPE and "egreso" not in GATE_TYPE
									# Determina si el porton es de entrada (no contiene
									# 'salida' ni 'egreso')
            endpoint = "/v1/access/validate-plate" if is_entry_gate else "/v1/access/exit-plate"
									# Elige el endpoint segun entrada/salida:
									# `validate-plate` o `exit-plate`
            if type == "qr":						# Si el tipo es 'qr', redirige al endpoint
									# `validate-qr`
                endpoint = "/v1/access/validate-qr"			# Asigna el endpoint `validate-qr` cuando el tipo
									# es QR
            payload_key = "plate" if type != "qr" else "qr_data"	# Elige la clave del payload: 'plate' o 'qr_data'
									# segun el tipo
            payload = {"gate_id": GATE_ID, "image_base64": img_b64, payload_key: data}
									# Agrega gate_id, imagen y el dato (plate o
									# qr_data) al payload
            if ocr_time is not None:					# Si se midio el tiempo de OCR, lo agrega al
									# payload para metricas
                payload["ocr_time"] = round(ocr_time, 3)		# Agrega el `ocr_time` redondeado a 3 decimales
            try:							# Abre un `try` para el envio HTTP propiamente
									# dicho
                resp = requests.post(f"{BACKEND_URL}{endpoint}", json=payload, timeout=5,
									# Hace el POST al backend con timeout de 5 s y el
									# payload JSON
                                     headers={"X-Node-Secret": ALPR_NODE_SECRET} if ALPR_NODE_SECRET else None)
									# Incluye la cabecera `X-Node-Secret` si hay
									# secreto configurado
                elapsed = time.time() - t_dispatch			# Calcula el tiempo transcurrido del envio al
									# backend
                if resp.ok:						# Si la respuesta es exitosa (2xx), procesa el
									# mensaje
                    msg = resp.json().get("message", "")		# Extrae el mensaje de la respuesta del backend
                    if "bienvenido" in msg.lower():			# Si el mensaje contiene 'bienvenido', es un
									# ingreso
                        print(f"[OK] Ingreso: Bienvenido {data}! (backend: {elapsed:.2f}s)")
									# Imprime el ingreso con la patente y el tiempo de
									# backend
                    elif "hasta luego" in msg.lower() or "salida" in msg.lower():
									# Si el mensaje indica salida, es un egreso
                        print(f"[OK] Salida: Hasta luego {data}! (backend: {elapsed:.2f}s)")
									# Imprime la salida con la patente y el tiempo de
									# backend
                    else:						# Rama `else`: cualquier otro mensaje de exito
                        print(f"[OK] {msg} (backend: {elapsed:.2f}s)")	# Imprime el mensaje generico del backend con su
									# tiempo
                else:							# Rama para respuestas no exitosas
                    print(f"[ERROR] {resp.status_code}: {resp.text[:200]} (backend: {elapsed:.2f}s)")
									# Imprime el codigo de error y los primeros 200
									# caracteres del cuerpo
            except Exception as re:					# Captura excepciones del envio HTTP (red caida,
									# timeout)
                elapsed = time.time() - t_dispatch			# Calcula el tiempo transcurrido hasta el error
                print(f"[ALPR ERROR] Error enviando peticion al backend: {type(re).__name__} - {re} (backend: {elapsed:.2f}s)")
									# Imprime el error de envio al backend con su tipo
									# y mensaje
        except Exception as e:						# Captura errores al preparar o serializar el
									# frame
            print(f"[ALPR ERROR] Error preparando/serializando frame: {type(e).__name__} - {e}")
									# Imprime el error de preparacion/serializacion del
									# frame
