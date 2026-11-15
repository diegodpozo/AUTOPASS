'''Centraliza constantes operativas: URLs, umbral de confianza, intervalo de cooldown anti-duplicados y formatos de patente aceptados.'''


import os								# Importa `os` para leer variables de entorno y,
									# unas lineas abajo, fijar variables de logging de
									# OpenCV y FFmpeg - os importa funciones del sistema operativo
import re								# Importa `re` para compilar mas abajo las
									# expresiones regulares que validan formatos de
									# patente
import warnings								# Importa `warnings` para silenciar los avisos de
									# la libreria torch que ensuciarian la consola del
									# nodo ALPR
from dotenv import load_dotenv						# Importa `load_dotenv` de python-dotenv para
									# cargar las variables del archivo `.env` en el
									# entorno del proceso

# Configuración de seguridad y logs
os.environ["OPENCV_LOG_LEVEL"] = "ERROR"				# Sube el nivel de log de OpenCV a ERROR para que
									# no imprima avisos de bajo nivel durante la
									# captura de video
os.environ["FFMPEG_LOG_LEVEL"] = "quiet"				# Pone a 'quiet' el log de FFmpeg para que no
									# muestre mensajes ruidosos al abrir streams
									# RTSP/HTTP
warnings.filterwarnings("ignore", category=UserWarning, module="torch")
									# Filtra los `UserWarning` originados en torch, que
									# de otro modo aparecerian al cargar modelos de
									# OCR
load_dotenv()								# Ejecuta `load_dotenv()` para inyectar en
									# `os.environ` las variables definidas en el `.env`
									# (camaras, backend, secretos)

# Variables de entorno principales
VIDEO_SOURCE = os.getenv("VIDEO_SOURCE", "0")				# Lee `VIDEO_SOURCE` del entorno (por defecto '0');
									# puede ser el indice de una camara local o una URL
									# RTSP/HTTP
if isinstance(VIDEO_SOURCE, str) and VIDEO_SOURCE.isdigit():		# Verifica si `VIDEO_SOURCE` es un texto compuesto
									# solo por digitos para tratarlo como indice
									# numerico de camara
    VIDEO_SOURCE = int(VIDEO_SOURCE)					# Convierte `VIDEO_SOURCE` a entero, de modo que
									# '0' pase a ser el indice 0 y las URLs queden como
									# strings

GATE_TYPE = os.getenv("GATE_TYPE", "entrada").lower()			# Lee `GATE_TYPE` del entorno ('entrada' o
									# 'salida') y lo normaliza a minusculas para
									# comparaciones posteriores
RAW_GATE_ID = os.getenv("GATE_ID", "ENTRADA_PRINCIPAL" if GATE_TYPE == "entrada" else "SALIDA_PRINCIPAL")
									# Lee `GATE_ID` del entorno; si no esta definido
									# elige 'ENTRADA_PRINCIPAL' o 'SALIDA_PRINCIPAL'
									# segun el tipo de porton
FORCE_OCR = os.getenv("ALPR_FORCE_OCR", "true").lower() in ("1", "true", "yes")
									# Convierte `ALPR_FORCE_OCR` a booleano: acepta
									# '1', 'true' o 'yes' (por defecto true) para
									# forzar OCR en cada frame
AUTO_DETECT_USB = os.getenv("ALPR_AUTO_DETECT_USB", "true").lower() in ("1", "true", "yes")
									# Habilita auto-detección y conmutación USB/IP
									# para portones de entrada/salida (por defecto true)

from core.normalize import normalize_name as normalize_id		# Importa `normalize_name` como `normalize_id`
									# desde `core/normalize`, el helper compartido que
									# sanea identificadores


GATE_ID = normalize_id(RAW_GATE_ID)					# Normaliza `RAW_GATE_ID` con `normalize_id` para
									# obtener un identificador de porton consistente
									# (sin espacios ni mayusculas raras)
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
									# Lee `BACKEND_URL` del entorno (por defecto
									# `http://localhost:8000`) y le quita la barra
									# final sobrante
ALPR_NODE_SECRET = os.getenv("ALPR_NODE_SECRET", "")			# Lee `ALPR_NODE_SECRET` del entorno: el secreto
									# con el que el nodo ALPR se autentica ante el
									# backend (puede quedar vacio)
WS_BACKEND_URL = BACKEND_URL.replace("http", "ws") + f"/v1/system/ws/video/{GATE_ID}"
									# Deriva `WS_BACKEND_URL` cambiando http por ws,
									# apuntando al endpoint WebSocket de video del
									# porton `GATE_ID`
if ALPR_NODE_SECRET:							# Comprueba si hay un secreto de nodo configurado
									# antes de anexarlo a la URL de WebSocket
    WS_BACKEND_URL += f"?node_secret={ALPR_NODE_SECRET}"		# Agrega `?node_secret=...` a la URL de WebSocket
									# para que el backend autentique el canal de video
									# del nodo

# Parámetros sensibles de visión y consenso
COOLDOWN_SECONDS = int(os.getenv("ALPR_COOLDOWN", 10))			# Define el cooldown en segundos (por defecto 10)
									# para no reevaluar la misma patente dos veces
									# seguidas
MIN_CONFIDENCE_VOTES = int(os.getenv("ALPR_MIN_CONFIDENCE", 1))		# Define el minimo de votos de confianza
									# (`ALPR_MIN_CONFIDENCE`, por defecto 1) que se
									# exige para considerar valida una lectura
OCR_INTERVAL = float(os.getenv("ALPR_OCR_INTERVAL", 0.35))		# Fija el intervalo entre intentos de OCR en
									# segundos (`ALPR_OCR_INTERVAL`, por defecto 0.35)
									# para no saturar el CPU
CONFIDENCE_THRESHOLD = float(os.getenv("ALPR_CONFIDENCE_THRESHOLD", 0.45))
									# Establece el umbral de confianza del OCR
									# (`ALPR_CONFIDENCE_THRESHOLD`, 0.45): lecturas por
									# debajo se descartan
MOTION_THRESHOLD = int(os.getenv("ALPR_MOTION_THRESHOLD", 3000))	# Fija el umbral de movimiento
									# (`ALPR_MOTION_THRESHOLD`, 3000 pixeles) que
									# decide cuando hay un vehiculo frente a la camara
FRAME_QUEUE_MAXSIZE = int(os.getenv("ALPR_FRAMEQ_MAXSIZE", 12))		# Tamaño maximo de la cola de frames (por defecto
									# 12); si se llena se descarta el frame mas viejo
									# para priorizar el reciente
CONSENSUS_REQUIRED = int(os.getenv("ALPR_CONSENSUS_REQUIRED", 2))	# Indica cuantas coincidencias
									# (`ALPR_CONSENSUS_REQUIRED`, 2) se necesitan para
									# confirmar una patente por consenso temporal
CONSENSUS_WINDOW = float(os.getenv("ALPR_CONSENSUS_WINDOW", 4.0))	# Define la ventana de tiempo en segundos
									# (`ALPR_CONSENSUS_WINDOW`, 4.0) dentro de la cual
									# deben coincidir esas lecturas

PLATE_ALLOWLIST = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"		# Define el alfabeto permitido para patentes
									# (letras A-Z y digitos 0-9) usado al limpiar los
									# textos que devuelve el OCR

# MODO DE DETECCION DE MOTOS (HABILITAR O DESHABILITAR FACILMENTE)
# PARA HABILITAR MOTOS, CAMBIAR A True O SETEAR ALPR_ENABLE_MOTOS=true EN .ENV
ENABLE_MOTO_RECOGNITION = os.getenv("ALPR_ENABLE_MOTOS", "false").lower() in ("1", "true", "yes")
									# Lee `ALPR_ENABLE_MOTOS` y lo convierte a
									# booleano; por defecto queda en false, o sea motos
									# deshabilitadas

# --- PATRONES OFICIALES DE AUTOS ---
AUTO_PLATE_PATTERN = (							# Comienza la construccion de `AUTO_PLATE_PATTERN`
    r'\b(' +								# Abre el grupo `\b(` que ancla la patente a
									# limites de palabra
    r'[A-Z]{2}\d{3}[A-Z]{2}' + r'|' +    # ARGENTINA AUTOS MERCOSUR (AB123CD) - 7 CARACTERES
    r'[A-Z]{3}\d{3}' + r'|' +            # ARGENTINA AUTOS FORMATO CLASICO (ABC123) - 6 CARACTERES
    r'[A-Z]{3}\d[A-Z]\d{2}' + r'|' +     # BRASIL MERCOSUR (ABC1D23) - 7 CARACTERES
    r'[A-Z]{3}\d{4}' + r'|' +            # URUGUAY (ABC1234) - 7 CARACTERES
    r'[A-Z]{4}\d{3}' +                   # PARAGUAY AUTOS MERCOSUR (ABCD123) - 7 CARACTERES
    r')\b'								# Cierra el grupo `)` del patron y lo ancla con
									# `\b` al final
)									# Cierra la tupla que concatena todas las
									# alternativas del patron de autos

# --- PATRONES OFICIALES DE MOTOS (PRESERVADOS PARA FACIL ACTIVACION) ---
MOTO_PLATE_PATTERN = (							# Comienza `MOTO_PLATE_PATTERN`
    r'\b(' +								# Abre el grupo `\b(` para reconocer patentes de
									# moto dentro del texto
    r'[A-Z]\d{3}[A-Z]{3}' + r'|' +       # ARGENTINA MOTOS MERCOSUR (A123BCD) - 7 CARACTERES
    r'[A-Z]{2}\d{3}' + r'|' +            # ARGENTINA MOTOS ANTIGUA (AB123) - 5 CARACTERES
    r'[A-Z]{2}\d{3}[A-Z]' + r'|' +       # ARGENTINA MOTOS MERCOSUR (AB123A) - 6 CARACTERES
    r'\d{3}[A-Z]{3}' + r'|' +            # ARGENTINA MOTOS FORMATO CLASICO (123ABC) - 6 CARACTERES
    r'\d{3}[A-Z]{4}' +                   # PARAGUAY MOTOS (123ABCD) - 7 CARACTERES
    r')\b'								# Cierra el grupo `)` del patron de motos y lo
									# ancla con `\b`
)									# Cierra la tupla que concatena las alternativas
									# del patron de motos

if ENABLE_MOTO_RECOGNITION:						# Evalua `ENABLE_MOTO_RECOGNITION` para decidir si
									# el patron general incluye o no los formatos de
									# moto
    LATAM_PLATE_PATTERN = (						# Inicio de `LATAM_PLATE_PATTERN` cuando las motos
									# estan habilitadas: abre el grupo con `\b(`
        r'\b(' +							# Alternativa 1 del patron latinoamericano: auto
									# Mercosur argentino `AB123CD`
        r'[A-Z]{2}\d{3}[A-Z]{2}' + r'|' +				# Alternativa 2: auto clasico argentino `ABC123`
        r'[A-Z]{3}\d{3}' + r'|' +					# Alternativa 3: auto Brasil `ABC1D23`
        r'[A-Z]{3}\d[A-Z]\d{2}' + r'|' +				# Alternativa 4: auto Uruguay `ABC1234`
        r'[A-Z]{3}\d{4}' + r'|' +					# Alternativa 5: auto Paraguay `ABCD123`
        r'[A-Z]{4}\d{3}' + r'|' +					# Alternativa 6: moto Mercosur argentina `A123BCD`
        r'[A-Z]\d{3}[A-Z]{3}' + r'|' +					# Alternativa 7: moto antigua argentina `AB123`
        r'[A-Z]{2}\d{3}' + r'|' +					# Alternativa 8: moto argentina `AB123A`
        r'[A-Z]{2}\d{3}[A-Z]' + r'|' +					# Alternativa 9: moto clasica `123ABC`
        r'\d{3}[A-Z]{3}' + r'|' +					# Alternativa 10: moto Paraguay `123ABCD`; ultima
									# opcion sin `|` final
        r'\d{3}[A-Z]{4}' +						# Cierra el grupo `)` y lo ancla con `\b`,
									# completando el patron unificado de autos y motos
        r')\b'								# Cierra la tupla del patron latinoamericano cuando
									# las motos estan habilitadas
    )									# Cierra el `if` del bloque de motos habilitadas
else:									# Rama `else`: cuando las motos estan
									# deshabilitadas, el patron general se reduce al de
									# autos
    LATAM_PLATE_PATTERN = AUTO_PLATE_PATTERN				# Asigna `AUTO_PLATE_PATTERN` como patron general,
									# de modo que las motos no se reconocen por
									# defecto

MOTO_PATTERN = re.compile(r'^[A-Z]{2}\d{3}$|^[A-Z]{2}\d{3}[A-Z]$|^[A-Z]\d{3}[A-Z]{3}$|^\d{3}[A-Z]{3}$|^\d{3}[A-Z]{4}$')
									# Compila con `re.compile` el regex `MOTO_PATTERN`
									# que valida si un texto ya normalizado corresponde
									# a una moto
MOTO_MIN_CONFIDENCE = float(os.getenv("ALPR_MOTO_CONFIDENCE", 0.75))	# Define `MOTO_MIN_CONFIDENCE`
									# (`ALPR_MOTO_CONFIDENCE`, 0.75): umbral de
									# confianza mas alto exigido a las lecturas de
									# moto
