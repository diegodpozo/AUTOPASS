'''Filtros de tratamiento de imagen con OpenCV para maximizar la tasa de acierto del OCR bajo lluvia, sombras o de noche.'''


import cv2								# Importa `cv2` para las operaciones de imagen:
									# resize, filtros, umbral, contornos y color
import re								# Importa `re` para los regex que identifican el
									# pais probable segun el formato de la patente
import numpy as np							# Importa `numpy` como `np` para las matrices de
									# kernel, mascaras y calculos numericos sobre
									# imagenes
from alpr.config import FORCE_OCR, MOTION_THRESHOLD			# Trae la configuracion `FORCE_OCR` y
									# `MOTION_THRESHOLD` que gobiernan la deteccion de
									# movimiento

class ImagePreprocessor:						# Define la clase `ImagePreprocessor`, con
									# utilidades de procesamiento de imagen, ROI y
									# movimiento para ALPR
    """Utilidades de procesamiento de imagen, detección de ROI y movimiento para ALPR."""

    @staticmethod							# Decorador `@staticmethod` que marca
									# `identify_country` como metodo estatico (no
									# necesita instancia)
    def identify_country(plate: str, is_mercosur: bool) -> str:		# Define `identify_country(plate, is_mercosur)`:
									# adivina el pais segun el formato y la franja
									# azul
        """Identifica el país probable basado en el formato y la franja azul (compatible con impresiones en papel B&N)."""
        if re.match(r'^[A-Z]{2}\d{3}[A-Z]{2}$', plate):			# Evalua si la patente tiene formato auto Mercosur
									# argentino `AB123CD`
            return "ARGENTINA (Mercosur)"				# Devuelve 'ARGENTINA (Mercosur)' cuando el formato
									# coincide con autos Mercosur argentinos
        if re.match(r'^[A-Z]{2}\d{3}[A-Z]$|^[A-Z]\d{3}[A-Z]{3}$|^[A-Z]\d{3}[A-Z]{2}$', plate):
									# Evalua formatos de moto Mercosur argentina
									# (varias longitudes) con una sola condicion
            return "ARGENTINA (Moto Mercosur)"				# Devuelve 'ARGENTINA (Moto Mercosur)' cuando la
									# patente corresponde a una moto Mercosur
        if re.match(r'^[A-Z]{3}\d{3}$', plate):				# Evalua el formato clasico argentino `ABC123` de
									# autos
            return "ARGENTINA (Antigua)"				# Devuelve 'ARGENTINA (Antigua)' para placas
									# clasicas argentinas
        if re.match(r'^[A-Z]{2}\d{3}$', plate):				# Evalua el formato de moto antigua `AB123`
            return "ARGENTINA (Moto Antigua)"				# Devuelve 'ARGENTINA (Moto Antigua)' para motos de
									# formato viejo
        if re.match(r'^[A-Z]{3}\d[A-Z]\d{2}$', plate):			# Evalua el formato de Brasil `ABC1D23`
            return "BRASIL"						# Devuelve 'BRASIL' cuando el formato corresponde a
									# placas brasileñas
        if re.match(r'^[A-Z]{3}\d{4}$', plate):				# Evalua el formato de Uruguay `ABC1234`
            return "URUGUAY"						# Devuelve 'URUGUAY' cuando el formato corresponde
									# a placas uruguayas
        if re.match(r'^[A-Z]{4}\d{3}$', plate):				# Evalua el formato de Paraguay Mercosur `ABCD123`
            return "PARAGUAY (Mercosur)"				# Devuelve 'PARAGUAY (Mercosur)' para placas
									# paraguayas
        
        if is_mercosur:							# Si ningun formato especifico coincidio, comprueba
									# el flag `is_mercosur` (franja azul detectada)
            return "MERCOSUR (Otro)"					# Devuelve 'MERCOSUR (Otro)' cuando hay franja azul
									# pero el formato no es de un pais conocido
        return "DESCONOCIDO"						# Devuelve 'DESCONOCIDO' como ultimo recurso cuando
									# no hay pistas de pais

    @staticmethod							# Decorador `@staticmethod` que marca
									# `detect_motion` como metodo estatico
    def detect_motion(frame, prev_gray) -> tuple[bool, np.ndarray]:	# Define `detect_motion(frame, prev_gray)`: decide
									# si hay movimiento entre el frame actual y el
									# anterior
        """Calcula si hay movimiento entre el frame actual y el anterior."""
        if FORCE_OCR:							# Si `FORCE_OCR` esta activo, salta la deteccion y
									# considera siempre que hay movimiento
            return True, prev_gray					# Devuelve True (hay movimiento) y el `prev_gray`
									# recibido, para no recalcular la escala de grises
        small = cv2.resize(frame, (320, 240))				# Reduce el frame a 320x240 para comparar
									# movimiento con mucho menos costo de CPU
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)			# Convierte el frame reducido a escala de grises,
									# que es lo que se compara entre frames
        if prev_gray is None:						# Si todavia no hay frame previo (`prev_gray`
									# None), asume el primer frame como movimiento
            return True, gray						# Devuelve True y el gris actual para inicializar
									# la referencia del siguiente frame
        frame_delta = cv2.absdiff(prev_gray, gray)			# Calcula `absdiff` (diferencia absoluta) entre el
									# gris previo y el actual, midiendo el cambio por
									# pixel
        motion_score = np.sum(cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]) / 255
									# Umbraliza la diferencia y suma los pixeles
									# cambiados (dividiendo por 255) para obtener un
									# score de movimiento
        return motion_score > MOTION_THRESHOLD, gray			# Devuelve True si el score supera
									# `MOTION_THRESHOLD`, junto con el gris actual como
									# nueva referencia

    @staticmethod							# Decorador `@staticmethod` que marca
									# `preprocess_for_screen` como metodo estatico
    def preprocess_for_screen(img) -> list:				# Define `preprocess_for_screen(img)`: prepara la
									# imagen para leer placas mostradas en pantallas
        """Optimizado para quitar el efecto moiré y ruido de píxeles de pantallas."""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)			# Convierte la imagen a escala de grises como
									# primer paso del preprocesado
        gray = cv2.resize(gray, None, fx=2.5, fy=2.5, interpolation=cv2.INTER_LANCZOS4)
									# Amplia la imagen 2.5x con interpolacion Lanczos
									# para que el OCR tenga mas detalle por caracter
        
        # 1. Filtro de mediana
        gray = cv2.medianBlur(gray, 3)					# Aplica un desenfoque de mediana de radio 3 para
									# eliminar ruido puntual conservando bordes
        
        # 2. Aumento de contraste
        clahe = cv2.createCLAHE(clipLimit=4.0, tileGridSize=(4,4))	# Crea un objeto CLAHE con limite de contraste 4.0
									# y grilla 4x4 para ecualizar iluminacion local
        contrast = clahe.apply(gray)					# Aplica CLAHE a la imagen gris, aumentando el
									# contraste local para resaltar los caracteres
        
        # 3. Sharpening
        kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])		# Define el kernel de realce: centro 9 y vecinos
									# -1, que acentua los bordes del texto
        sharpened = cv2.filter2D(contrast, -1, kernel)			# Aplica el kernel con `filter2D` para obtener la
									# version nitida de la imagen
        
        # 4. Umbralización adaptativa
        v2 = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 13, 5)
									# Binariza la imagen con umbral adaptativo
									# gaussiano (bloque 13, constante 5), creando
									# blanco/negro local
        
        # 5. Inversión
        v2_inv = cv2.bitwise_not(v2)					# Invierte los colores de la imagen binarizada para
									# generar una variante con texto claro sobre fondo
									# oscuro
        
        return [sharpened, v2, v2_inv]					# Devuelve las tres variantes (nitida, binaria y
									# binaria invertida) para que el OCR pruebe todas

    @staticmethod							# Decorador `@staticmethod` que marca `_iou` como
									# metodo estatico
    def _iou(b1, b2):							# Define `_iou(b1, b2)`: calcula la interseccion
									# sobre union de dos cajas, para deduplicar ROIs
        x0 = max(b1[0], b2[0]); y0 = max(b1[1], b2[1])			# Calcula las coordenadas de la esquina superior
									# izquierda de la interseccion (max de los
									# minimos)
        x1 = min(b1[2], b2[2]); y1 = min(b1[3], b2[3])			# Calcula las coordenadas de la esquina inferior
									# derecha de la interseccion (min de los maximos)
        inter = max(0, x1-x0) * max(0, y1-y0)				# Calcula el area de interseccion, recortando a 0
									# si las cajas no se solapan
        a1 = (b1[2]-b1[0]) * (b1[3]-b1[1])				# Calcula el area de la primera caja
        a2 = (b2[2]-b2[0]) * (b2[3]-b2[1])				# Calcula el area de la segunda caja
        union = a1 + a2 - inter						# Calcula la union como suma de areas menos la
									# interseccion
        return inter / union if union > 0 else 0			# Devuelve IoU (interseccion/union) o 0 si la union
									# es nula, evitando division por cero

    @staticmethod							# Decorador `@staticmethod` que marca
									# `_is_valid_plate_roi` como metodo estatico
    def _is_valid_plate_roi(crop, frame_w, frame_h):			# Define `_is_valid_plate_roi(crop, frame_w,
									# frame_h)`: filtra ROIs que no parecen una
									# patente
        ch, cw = crop.shape[:2]						# Lee alto y ancho del recorte candidato
        if cw < 70 or ch < 18:						# Descarta el ROI si es demasiado pequeño (menos de
									# 70x18 px) para contener caracteres legibles
            return False						# Devuelve False para recortes demasiado chicos
        if cw > frame_w * 0.85:						# Descarta el ROI si ocupa mas del 85% del ancho
									# del frame (probablemente no es una patente)
            return False						# Devuelve False para recortes
									# desproporcionadamente anchos
        aspect = cw / max(ch, 1)					# Calcula la relacion de aspecto (ancho/alto) del
									# recorte, evitando division por cero
        return 1.5 <= aspect <= 6.0					# Acepta el ROI solo si su aspecto esta entre 1.5 y
									# 6.0, el rango tipico de una chapa patente

    @staticmethod							# Decorador `@staticmethod` que marca
									# `find_plate_roi` como metodo estatico
    def find_plate_roi(frame, plate_cascade=None) -> list:		# Define `find_plate_roi(frame,
									# plate_cascade=None)`: busca regiones donde puede
									# estar la patente
        """Encuentra regiones de interés donde puede ubicarse una patente."""
        h, w = frame.shape[:2]						# Lee alto y ancho del frame completo
        main_roi = frame[int(h*0.15):int(h*0.92), int(w*0.05):int(w*0.95)]
									# Recorta un ROI principal dejando margenes
									# (15%-92% en alto, 5%-95% en ancho) para excluir
									# bordes
        rh, rw = main_roi.shape[:2]					# Lee alto y ancho del ROI principal para calcular
									# strip y segmentos
        gray = cv2.cvtColor(main_roi, cv2.COLOR_BGR2GRAY)		# Convierte el ROI principal a escala de grises
									# para los analisis de bordes y contornos

        raw_boxes = []							# Inicializa `raw_boxes` donde se iran acumulando
									# las cajas candidatas

        strip_configs = [						# Define `strip_configs`: bandas horizontales
									# configurables donde suele aparecer la patente
            (0.55, 0.75, "strip_bottom"),				# Banda inferior (55%-75% de la altura) etiquetada
									# como `strip_bottom`
            (0.30, 0.50, "strip_center"),				# Banda central (30%-50% de la altura) etiquetada
									# como `strip_center`
        ]								# Cierra la lista de configs de bandas
        SEGMENT_W = 320							# Define el ancho de segmento (320 px) usado para
									# partir las bandas en tramos manejables
        for y_pct0, y_pct1, tag in strip_configs:			# Recorre cada banda con su rango vertical
									# (porcentajes) y su etiqueta
            sy0, sy1 = int(rh*y_pct0), int(rh*y_pct1)			# Convierte los porcentajes de la banda a pixeles
									# (inicio y fin en alto del ROI)
            strip_h = sy1 - sy0						# Calcula la altura de la banda como diferencia
									# entre inicio y fin
            if strip_h < 20:						# Descarta bandas demasiado finas (menos de 20 px)
									# que no aportarian informacion
                continue						# Salta la banda si es demasiado delgada
            n_segs = max(1, (rw + SEGMENT_W - 1) // SEGMENT_W)		# Calcula cuantos segmentos de ancho `SEGMENT_W`
									# caben en el ancho del ROI
            seg_w = rw // n_segs					# Divide el ancho del ROI entre la cantidad de
									# segmentos para obtener el ancho de cada tramo
            for i in range(n_segs):					# Recorre cada segmento horizontal de la banda
                sx0 = i * seg_w						# Calcula la coordenada X inicial del segmento
                sx1 = min(rw, sx0 + seg_w)				# Calcula la coordenada X final del segmento,
									# limitada al ancho del ROI
                raw_boxes.append((sx0, sy0, sx1, sy1, tag))		# Agrega la caja del segmento (con su etiqueta de
									# banda) a las candidatas

        try:								# Abre un `try` porque el analisis de contornos
									# puede fallar con imagenes problematicas
            blur = cv2.bilateralFilter(gray, 9, 75, 75)			# Aplica un filtro bilateral para suavizar ruido
									# conservando bordes, mejorando la deteccion de
									# contornos
            edged = cv2.Canny(blur, 50, 200)				# Aplica el detector de bordes Canny (umbrales 50 y
									# 200) para resaltar los limites de objetos
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))	# Crea un kernel rectangular 5x3 para la operacion
									# morfologica de cierre
            closed = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel)	# Cierra los bordes con morfologia para unir lineas
									# rotas y formar contornos cerrados
            contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
									# Busca los contornos externos de la imagen de
									# bordes cerrada
            for cnt in contours:					# Recorre cada contorno detectado
                area = cv2.contourArea(cnt)				# Calcula el area del contorno
                if area < (rw * rh) * 0.001:				# Descarta contornos demasiado pequeños (menos del
									# 0.1% del area del ROI)
                    continue						# Salta el contorno si es ruido por tamaño
                x, y, cw, ch = cv2.boundingRect(cnt)			# Obtiene la caja envolvente (x, y, ancho, alto)
									# del contorno
                aspect = (cw / float(ch)) if ch > 0 else 0		# Calcula el aspecto del contorno, evitando
									# division por cero
                if not (1.5 <= aspect <= 8.0 and cw > rw * 0.08):	# Descarta contornos que no tengan aspecto 1.5-8.0
									# ni un ancho minimo del 8% del ROI
                    continue						# Salta el contorno si no parece una posible
									# patente
                pad_x, pad_y = int(cw * 0.10), int(ch * 0.25)		# Calcula el padding horizontal (10%) y vertical
									# (25%) para ampliar la caja alrededor del
									# contorno
                bx0 = max(0, x-pad_x); by0 = max(0, y-pad_y)		# Calcula la esquina superior izquierda de la caja
									# con padding, limitada a 0
                bx1 = min(rw, x+cw+pad_x); by1 = min(rh, y+ch+pad_y)	# Calcula la esquina inferior derecha con padding,
									# limitada al tamaño del ROI
                raw_boxes.append((bx0, by0, bx1, by1, "contour"))	# Agrega la caja del contorno (con padding) a las
									# candidatas con la etiqueta 'contour'
        except Exception:						# Captura cualquier error del analisis de contornos
									# para no romper la deteccion
            pass							# Ignora el error con `pass` y sigue con las cajas
									# ya recolectadas

        priority = {"contour": 0, "strip_center": 1, "strip_bottom": 2}
									# Define la prioridad de las etiquetas: 'contour'
									# primero (0), luego 'strip_center' (1) y
									# 'strip_bottom' (2)
        raw_boxes.sort(key=lambda b: (priority.get(b[4], 9), -(b[2]-b[0])*(b[3]-b[1])))
									# Ordena las cajas por prioridad y, dentro de la
									# misma, por area descendente para quedarse con las
									# mas grandes

        merged = []							# Inicializa `merged`, la lista de cajas ya
									# deduplicadas
        for box in raw_boxes[:20]:					# Recorre solo las 20 cajas mas prioritarias para
									# acotar el costo
            b = box[:4]							# Extrae las coordenadas de la caja (sin la
									# etiqueta)
            crop = main_roi[b[1]:b[3], b[0]:b[2]]			# Recorta del ROI principal la region de esa caja
            if not ImagePreprocessor._is_valid_plate_roi(crop, rw, rh):
									# Valida el recorte con `_is_valid_plate_roi`; si
									# no parece patente, lo descarta
                continue						# Salta el recorte invalido
            skip = False						# Inicializa `skip` en False para marcar si la caja
									# se solapa con una ya aceptada
            for existing in merged:					# Compara la caja con cada caja ya fusionada
                if ImagePreprocessor._iou(b, existing) > 0.4:		# Si el IoU con una caja existente supera 0.4, la
									# considera duplicada
                    skip = True						# Marca `skip` en True cuando detecta solapamiento
                    break						# Corta el bucle de comparacion apenas encuentra un
									# duplicado
            if not skip:						# Si la caja no es duplicada, la agrega a `merged`
                merged.append(b)					# Agrega la caja aceptada a la lista de regiones
									# unicas
                if len(merged) >= 10:					# Corta si ya reunio 10 candidatos, suficiente para
									# intentar OCR
                    break						# Rompe el bucle al alcanzar el limite de 10

        candidates = [main_roi[b[1]:b[3], b[0]:b[2]] for b in merged]	# Construye la lista `candidates` recortando el ROI
									# principal en cada caja fusionada
        if not candidates:						# Comprueba si no quedo ninguna candidata valida
            candidates.append(main_roi)					# Agrega el ROI principal completo como candidata
									# de respaldo

        return candidates						# Devuelve la lista de recortes candidatos para que
									# el motor OCR los analice

    @staticmethod							# Decorador `@staticmethod` que marca
									# `is_mercosur_candidate` como metodo estatico
    def is_mercosur_candidate(roi) -> bool:				# Define `is_mercosur_candidate(roi)`: detecta si
									# el ROI tiene la franja azul caracteristica de
									# MERCOSUR
        """Detecta si un ROI tiene la franja azul característica del MERCOSUR (adaptado para papel e impresiones)."""
        try:								# Abre un `try` porque la conversion de color puede
									# fallar con imagenes invalidas
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)			# Convierte el ROI al espacio HSV, que separa el
									# tono y facilita segmentar el azul
            lower_blue = np.array([90, 40, 40])				# Define el limite inferior del rango azul en HSV
									# (tono 90, saturacion 40, valor 40)
            upper_blue = np.array([135, 255, 255])			# Define el limite superior del rango azul en HSV
									# (tono 135, saturacion y valor al maximo)
            mask = cv2.inRange(hsv, lower_blue, upper_blue)		# Crea una mascara binaria con los pixeles que caen
									# en el rango azul
            
            h, _ = mask.shape[:2]					# Lee la altura de la mascara para analizar solo la
									# parte superior (donde va la franja azul)
            top_strip = mask[0:int(h*0.35), :]				# Toma la franja superior (35% de la altura) donde
									# suele estar la banda azul MERCOSUR
            blue_ratio = np.sum(top_strip > 0) / max(1, top_strip.size)
									# Calcula la proporcion de pixeles azules en esa
									# franja superior
            return blue_ratio > 0.06					# Devuelve True si la proporcion de azul supera el
									# 6%, indicando franja MERCOSUR probable
        except Exception:						# Captura cualquier excepcion durante el analisis
									# de color
            return False						# Devuelve False si el analisis falla, tratando el
									# ROI como no MERCOSUR

    @staticmethod							# Decorador `@staticmethod` que marca
									# `crop_below_blue` como metodo estatico
    def crop_below_blue(roi):						# Define `crop_below_blue(roi)`: recorta justo
									# debajo de la franja azul si esta presente
        """Recorta por debajo de la franja azul MERCOSUR si está presente."""
        try:								# Abre un `try` para tolerar errores de imagen
            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)			# Convierte el ROI a HSV para localizar el azul de
									# la franja
            lower_blue = np.array([90, 40, 40])				# Define el limite inferior del rango azul en HSV
									# (igual que en la deteccion previa)
            upper_blue = np.array([135, 255, 255])			# Define el limite superior del rango azul en HSV
            mask = cv2.inRange(hsv, lower_blue, upper_blue)		# Construye la mascara de pixeles azules
            h, _ = mask.shape[:2]					# Lee la altura de la mascara
            top_mask = mask[0:int(h*0.5), :]				# Toma la mitad superior de la mascara, donde se
									# busca la franja azul
            if np.sum(top_mask) == 0:					# Si no hay ningun pixel azul en la mitad superior,
									# devuelve el ROI sin recortar
                return roi						# Devuelve el ROI original cuando no hay franja
									# azul
            ys, _ = np.where(top_mask > 0)				# Obtiene las filas (Y) donde hay pixeles azules en
									# la mascara superior
            if len(ys) == 0:						# Si no se encontro ninguna fila con azul, devuelve
									# el ROI sin cambios
                return roi						# Devuelve el ROI original como salvaguarda
            y_max = int(np.max(ys))					# Toma la fila Y mas baja con azul: el borde
									# inferior de la franja
            new_y0 = min(h-1, int((y_max + 5)))				# Calcula el nuevo Y de inicio unos 5 px debajo de
									# la franja para no incluir borde azul
            if y_max > int(h*0.45):					# Si esa franja baja llega mas alla del 45% de la
									# altura, no conviene recortar
                return roi						# Devuelve el ROI completo cuando la franja azul es
									# demasiado baja
            cropped = roi[new_y0: , :]					# Recorta el ROI desde el nuevo Y hacia abajo,
									# descartando la franja azul superior
            if cropped.shape[0] < int(h*0.25):				# Si el recorte resultante queda demasiado bajo
									# (menos del 25% de altura), descarta el recorte
                return roi						# Devuelve el ROI original cuando el recorte
									# dejaria muy poco contenido
            return cropped						# Devuelve el recorte sin la franja azul, que suele
									# dejar mejor el texto para el OCR
        except Exception:						# Captura cualquier excepcion del proceso de
									# recorte
            return roi							# Devuelve el ROI original como respaldo si algo
									# falla durante el recorte
