"""Explicaciones analizadas de alpr (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "alpr/__init__.py": {
        "proposito": (
            "💡 LA IDEA: Es la 'puerta de entrada principal y recepción' del módulo de cámaras. En vez de que otras partes del sistema tengan que golpear puertas internas en distintas habitaciones para buscar el motor de OCR o el streamer de video, este archivo recibe todo en la mesa de entrada y lo entrega listo para usar.\n\n"
            "🎯 POR QUE FUE GENERADA: Simplifica los accesos y evita dependencias enredadas. Al importar `from alpr import ALPREngine, VideoStreamer`, el resto del proyecto no necesita saber en qué archivo específico está guardada cada pieza, facilitando el mantenimiento y evitando errores de importación.\n\n"
            "⚙️ FUNCIONAMIENTO: Declara formalmente a la carpeta `alpr` como un paquete Python válido y reexporta en su espacio de nombres las clases y funciones esenciales: la configuración general (`GATE_ID`, `GATE_TYPE`), el motor de lectura OCR (`ALPREngine`), el capturador de video (`VideoStreamer`) y el cliente de comunicación en vivo (`ws_monitoring_worker`)."
        ),
        "simbolos": {
        },
    },
    "alpr/config.py": {
        "proposito": (
            "💡 LA IDEA: Es el 'tablero de fusibles y perillas de calibración' de todo el sistema de cámaras. En lugar de tocar los motores matemáticos de inteligencia artificial cada vez que se cambia una cámara de lugar o se reemplaza una lente, todos los cables, contraseñas, tolerancias y direcciones de red se calibran desde este único panel centralizado.\n\n"
            "🎯 POR QUE FUE GENERADA: En un estacionamiento real las condiciones cambian constantemente: se agrega un carril nuevo, se cambia una webcam USB por una cámara IP profesional de alta velocidad, o se necesita regular qué tan estricta debe ser la lectura para no dejar afuera a autos con patentes despintadas. Si estos valores estuvieran dispersos adentro del código de visión artificial, cambiar una IP obligaría a reescribir todo el sistema con riesgo de romperlo. Este archivo separa la configuración del motor de IA.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Silencia advertencias técnicas: desactiva avisos ruidosos de OpenCV, FFmpeg y PyTorch para mantener limpia la consola. 2. Lee el archivo `.env`: toma la fuente de video (`VIDEO_SOURCE`: índice de webcam, flujo RTSP o video grabado). 3. Configura el carril: define si es entrada, salida o predio (`GATE_TYPE`) y normaliza el identificador de la puerta (`GATE_ID`). 4. Conecta con el servidor: arma las URLs HTTP y WebSocket (`BACKEND_URL` y `WS_BACKEND_URL`) con la clave de seguridad del hardware (`ALPR_NODE_SECRET`). 5. Calibra los sensores: fija el tiempo de espera anti-rebote (`COOLDOWN_SECONDS=10s`), el intervalo entre lecturas (`OCR_INTERVAL=0.35s`), la certeza mínima exigida (`CONFIDENCE_THRESHOLD=0.45`), el detector de movimiento (`MOTION_THRESHOLD=3000`) y el consenso por votos temporales. 6. Define los patrones de patentes: mediante expresiones regulares (`LATAM_PLATE_PATTERN`), reconoce matrículas oficiales de Argentina (Mercosur y clásica), motos (si está habilitado con `ENABLE_MOTO_RECOGNITION`), Brasil, Uruguay y Paraguay."
        ),
        "simbolos": {
        },
    },
    "alpr/ocr_engine.py": {
        "proposito": 'Corazón del servicio ALPR: importa el motor OCR disponible (RapidOCR con fallback a PaddleOCR), corrige errores clásicos de lectura de patentes, consume la cola de frames, aplica consenso por votos y confianza mínima, y despacha los eventos de patente/QR al backend por HTTP. También dibuja el overlay de detecciones para el streaming.',
        "simbolos": {
            "ReadingStatusNotifier": (
                "💡 LA IDEA: Es como la luz titilante de 'Procesando...' en un cajero automático: le avisa al tablero de control que la cámara está enfocando un auto y leyendo una chapa, pero sin mandar mil mensajes por segundo.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita saturar el servidor con avisos continuos mientras el auto avanza despacio frente a la lente.\n\n'
                "⚙️ FUNCIONAMIENTO: Avisa al backend, con debounce, que la cámara está leyendo activamente una patente, para que la interfaz muestre el estado 'leyendo' sin saturar el servidor."
            ),
            "ReadingStatusNotifier.__init__": (
                '💡 LA IDEA: Pone el reloj en cero y fija que no se puede mandar más de un aviso de lectura cada 1,5 segundos.\n\n'
                '🎯 POR QUE FUE GENERADA: Establece el límite de frecuencia para no sobrecargar la red ni el backend.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el intervalo mínimo entre avisos (1,5 s por defecto) y el timestamp del último aviso emitido, inicializado en cero.'
            ),
            "notify_reading": (
                '💡 LA IDEA: Comprueba si ya pasó el tiempo reglamentario desde el último aviso; si pasó, despacha el mensaje en un hilo secundario sin frenar a la cámara.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita congelar el video en vivo de la cámara mientras se envía un aviso por internet.\n\n'
                '⚙️ FUNCIONAMIENTO: Si pasó menos que el intervalo desde el último aviso, sale sin hacer nada; si no, actualiza el timestamp y lanza un hilo daemon que dispara la notificación para no bloquear el bucle de captura de frames.'
            ),
            "_fire": (
                '💡 LA IDEA: Es el disparo rápido del mensaje HTTP hacia el servidor central, con un tiempo límite de espera ultra corto (0,8 segundos).\n\n'
                '🎯 POR QUE FUE GENERADA: Si el servidor tarda en contestar o la red titila, se aborta de inmediato para no trabar la fluidez del reconocimiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Hace un `POST` sin respuesta a `/v1/system/camera-reading/{GATE_ID}` con timeout de 0,8 s y el header `X-Node-Secret` si hay secreto configurado; cualquier excepción se traga en silencio para no tumbar la captura.'
            ),
            "CorregirLetra": (
                "💡 LA IDEA: Es el corrector ortográfico de patentes: si en una posición donde debería haber una letra el OCR leyó un número (por ejemplo un cero '0' o un ocho '8'), lo transforma en la letra correspondiente ('O' o 'B').\n\n"
                '🎯 POR QUE FUE GENERADA: Resuelve las confusiones visuales más comunes de las cámaras causadas por sombras o reflejos en la chapa metálica.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplaza dígitos confundibles por su letra equivalente usando `MAPA_LETRAS` (0→O, 1→I, 2→Z, 4→A, 5→S, 6→G, 8→B); si el carácter no está en el mapa lo devuelve tal cual. Sirve para corregir posiciones alfabéticas de la patente.'
            ),
            "CorregirDigito": (
                "💡 LA IDEA: Es el inverso de la corrección alfabética: si en una posición numérica la cámara confunde un número con una letra (como una 'S' en vez de un '5' o una 'B' por un '8'), lo convierte en su número correcto.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita que el sistema rechace patentes válidas solo porque el OCR leyó una letra en lugar de un número.\n\n'
                '⚙️ FUNCIONAMIENTO: Operación inversa a `CorregirLetra`: con `MAPA_DIGITOS` cambia letras parecidas a números (O/Q/D→0, I/L→1, Z→2, A→4, S→5, G→6, B→8) para corregir posiciones numéricas; devuelve el carácter sin cambios si no figura en el mapa.'
            ),
            "CorregirPatente": (
                "💡 LA IDEA: Es el cirujano experto en patentes: quita leyendas molestas como 'ARGENTINA' o 'MERCOSUR' y analiza la estructura completa (auto Mercosur, moto, formato clásico o Mercosur Brasil) para reconstruir la patente perfecta.\n\n"
                '🎯 POR QUE FUE GENERADA: Salva cientos de lecturas dudosas que de otro modo obligarían al conductor a detenerse y pedir auxilio manual.\n\n'
                "⚙️ FUNCIONAMIENTO: Normaliza y desambigua una lectura cruda: limpia todo lo que no sea A-Z/0-9, quita marcas de agua ('ARGENTINA', 'MERCOSUR', etc.), y si el texto no ya cumple un formato estricto de 6 o 7 caracteres intenta corregirlo posicionalmente (moto Mercosur A+3+3, auto Mercosur 2+3+2, Brasil ABC1D23, autos clásicos ABC123 y motos clásicas 123ABC). Devuelve la patente corregida o el texto limpio si ningún patrón calza."
            ),
            "ALPREngine": (
                '💡 LA IDEA: Es el cerebro de visión artificial: coordina al lector de caracteres (OCR), al detector de códigos QR, a los hilos de procesamiento y a la urna de votación de patentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza todo el procesamiento pesado de imágenes en un único motor eficiente que no se cuelga.\n\n'
                '⚙️ FUNCIONAMIENTO: Motor principal de visión: instancia el OCR, el detector de QR, la cola de frames, el buffer de votos y el pool de hilos que usan `ocr_worker`, `send_event` y el overlay.'
            ),
            "ALPREngine.__init__": (
                '💡 LA IDEA: Inicializa los motores neuronales de lectura (RapidOCR / PaddleOCR), prepara la cola de imágenes y alista el equipo de hilos de trabajo.\n\n'
                '🎯 POR QUE FUE GENERADA: Deja todo listo para empezar a procesar frames apenas arranca la cámara sin demoras en la primera lectura.\n\n'
                '⚙️ FUNCIONAMIENTO: Intenta crear RapidOCR y, si falla, PaddleOCR (dejando el error en `ocr_error` si ninguno está disponible); además prepara el detector de QR de OpenCV, la cola acotada de frames, el buffer de votos, el ThreadPoolExecutor de 3 hilos y el estado de detecciones/overlay.'
            ),
            "flush_queue": (
                '💡 LA IDEA: Es el vaciador del tacho de basura: cuando un auto ya fue reconocido con éxito y se levantó la barrera, tira todas las fotos viejas que quedaron encoladas.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita procesar fotos del baúl o del paragolpes del auto que ya pasó, liberando el procesador para el próximo vehículo.\n\n'
                '⚙️ FUNCIONAMIENTO: Vacía la cola de frames descartando todo lo acumulado con `get_nowait` en un bucle, envuelto en try/except para no explotar si otro hilo la está consumiendo; se usa para borrar frames viejos tras una lectura aceptada.'
            ),
            "detect_motion": (
                '💡 LA IDEA: Es el sensor de presencia: compara la foto actual con la anterior y si no hay movimiento en el centro de la escena, apaga el OCR para que la computadora descanse.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra hasta un 80% de consumo de procesador (CPU) impidiendo que la máquina gaste energía leyendo el piso vacío cuando no hay autos.\n\n'
                '⚙️ FUNCIONAMIENTO: Compara la zona de patente (ROI central del frame) en escala de grises con el frame anterior: aplica blur Gaussiano, `absdiff` y umbral, y devuelve True si hay más de 800 píxeles distintos; en el primer frame o ante un error devuelve True (es decir, no frenar la lectura).'
            ),
            "_ocr_single_roi": (
                '💡 LA IDEA: Es la lupa que lee un recorte específico de la imagen: si el recorte es muy chiquito lo agranda y se lo entrega al modelo neuronal para que extraiga el texto y el porcentaje de seguridad.\n\n'
                '🎯 POR QUE FUE GENERADA: Estandariza la lectura para que funcione de manera idéntica tanto si se usa RapidOCR como PaddleOCR.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta el motor OCR sobre un recorte: si es muy chico lo escala a 80 px de alto, luego adapta la lectura al formato de RapidOCR (`reader(img)`) o PaddleOCR (`reader.ocr`) y devuelve tres listas (textos, confianzas, polígonos); sin motor o ante excepción devuelve listas vacías.'
            ),
            "ocr_worker": (
                '💡 LA IDEA: Es el operario incansable: revisa cada foto que llega, descarta imágenes negras, prueba leer códigos QR, detecta patentes, busca consensos de votos entre varias fotos consecutivas y manda la orden de apertura.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el corazón que hace funcionar todo el estacionamiento automatizado; sin este hilo continuo, las barreras no se levantarían solas.\n\n'
                '⚙️ FUNCIONAMIENTO: Bucle infinito que toma frames de la cola y hace todo el pipeline de lectura: descarta frames negros, intenta QR, recorta la ROI principal (y debajo de la franja azul si es Mercosur), corre OCR, limpia ruido de encabezados, arma la patente por prioridades (detección individual → combinación de fragmentos por X → fallback por Y → caza de contornos con confianza mínima 0,65), valida formato/país/motos, exige consenso de votos dentro de `CONSENSUS_WINDOW` y confianza mínima, guarda imagen de debug si es Argentina, y al aceptar limpia buffers, vacía la cola durante el cooldown de 5 s y envía el evento.'
            ),
            "get_frame_with_overlay": (
                '💡 LA IDEA: Es el director de efectos especiales: decide si hay que pegarle el recuadro verde neón con la patente leída al video en vivo o si se muestra el video limpio.\n\n'
                '🎯 POR QUE FUE GENERADA: Ofrece una confirmación visual clara en el monitor del guardia de seguridad indicando qué patente fue detectada.\n\n'
                '⚙️ FUNCIONAMIENTO: Decide qué overlay corresponde al frame actual: muestra las detecciones activas solo durante 1,5 s desde la última lectura y el banner de confirmación solo durante 3 s; si no hay nada vigente devuelve el frame sin tocar.'
            ),
            "draw_overlay": (
                '💡 LA IDEA: Es el dibujante que pinta los recuadros verdes estilo visor militar (HUD CCTV), los textos de confianza y el cartel de bienvenida sobre la imagen de la cámara.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el operador humano vea en tiempo real exactamente qué parte del auto está mirando el algoritmo de inteligencia artificial.\n\n'
                '⚙️ FUNCIONAMIENTO: Estático: pinta sobre una copia del frame los recuadros verde neón de cada detección (desplazados al offset de la ROI), esquinas estilo HUD CCTV en amarillo, etiqueta con texto y confianza sobre fondo translúcido, y durante 3 s un banner verde superior con la patente aceptada, país y confianza.'
            ),
            "_plate_close": (
                '💡 LA IDEA: Es el comparador de similitud: determina si dos lecturas son casi la misma patente (por ejemplo si coinciden en 6 de 7 letras), para saber si es el mismo auto pasando despacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita cobrarle dos veces o levantarle la barrera dos veces al mismo vehículo por una mínima oscilación de lectura.\n\n'
                "⚙️ FUNCIONAMIENTO: Compara dos patentes normalizadas: son 'cercanas' si son iguales, si comparten el mismo bloque de 3 o más dígitos (variantes de la misma escena) o si tienen igual longitud con hasta `max_dist` (1) caracteres de diferencia; sirve para que el cooldown no deje pasar la misma placa leída con ruido."
            ),
            "send_event": (
                '💡 LA IDEA: Es el filtro de enfriamiento (cooldown): si la misma patente vuelve a aparecer antes de 5 segundos, la ignora para no inundar el sistema con eventos duplicados.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve el problema clásico de las cámaras donde un auto detenido frente a la barrera dispara 20 ingresos en 3 segundos.\n\n'
                "⚙️ FUNCIONAMIENTO: Aplica debounce de duplicados: normaliza el dato y el último patrón validado, y si dentro de `COOLDOWN_SECONDS` la lectura es 'cercana' según `_plate_close` la descarta; si pasa, actualiza estado y delega el envío HTTP real a `_dispatch_request` en el ThreadPoolExecutor para no bloquear el hilo OCR."
            ),
            "_dispatch_request": (
                '💡 LA IDEA: Es el cartero que empaqueta la foto del auto en formato comprimido (JPEG) y la envía junto con la patente y la hora al servidor backend para que autorice el ingreso o salida.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que la evidencia fotográfica viaje rápido al servidor central para auditoría y archivo legal del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Codifica el frame a JPEG calidad 70 en base64, elige el endpoint según el tipo de portón (`validate-plate`, `exit-plate` o `validate-qr`), arma el payload con `gate_id`, imagen y dato (más `ocr_time` si llega), y hace el `POST` al backend con timeout de 5 s y header de secreto; imprime el resultado (ingreso/salida/error) con los tiempos.'
            ),
        },
    },
    "alpr/preprocessor.py": {
        "proposito": 'Utilidades de imagen compartidas por el motor: identifica el país de la patente por su formato, detecta movimiento entre frames, preprocesa capturas de pantallas (antimoiré), y busca regiones candidatas a patente (franjas fijas + contornos) filtrando por tamaño, aspecto y solapamiento. Es la capa de visión que alimenta al OCR.',
        "simbolos": {
            "ImagePreprocessor": (
                '💡 LA IDEA: Es el laboratorio fotográfico: agrupa todas las recetas matemáticas para mejorar la nitidez, recortar bordes y detectar franjas de patentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita mezclar la matemática de imagen con la lógica del negocio, manteniendo el código limpio y modular.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrupa en métodos estáticos todas las operaciones de preprocesamiento y detección de ROI que usa `ALPREngine`, sin estado propio.'
            ),
            "identify_country": (
                '💡 LA IDEA: Es el experto en banderas y formatos: analiza la secuencia de letras y números para saber si la patente es de Argentina, Brasil, Uruguay o Paraguay.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite aplicar reglas tarifarias y de auditoría específicas según el país de origen del vehículo.\n\n'
                "⚙️ FUNCIONAMIENTO: Recibe la patente ya corregida y el flag Mercosur, y devuelve el país probable según el formato regex (auto Mercosur, moto Mercosur, auto/moto antiguos argentinos, Brasil, Uruguay, Paraguay); si ningún formato calza pero había franja azul devuelve 'MERCOSUR (Otro)' o si no 'DESCONOCIDO'."
            ),
            "detect_motion": (
                '💡 LA IDEA: Es la versión liviana y ultrarrápida del detector de movimiento, optimizada para procesar fotos a baja resolución (320x240).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber si hay algo moviéndose en menos de 2 milisegundos sin consumir casi nada de procesador.\n\n'
                "⚙️ FUNCIONAMIENTO: Versión estática y liviana (320x240) del detector de movimiento: si `FORCE_OCR` está activo siempre devuelve True; si no, compara el frame actual en grises con el anterior devolviendo el nuevo estado y un bool de si el score de píxeles cambios supera `MOTION_THRESHOLD`. Devuelve también la imagen 'gris' para usarla como anterior en la próxima llamada."
            ),
            "preprocess_for_screen": (
                '💡 LA IDEA: Es el filtro antirreflejo para pantallas: cuando un usuario muestra una patente o QR desde su celular, limpia el brillo del vidrio y el granulado de la pantalla para que el OCR no se encandile.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite validar patentes de prueba o vouchers mostrados directamente desde la pantalla de un smartphone.\n\n'
                '⚙️ FUNCIONAMIENTO: Prepara una captura de pantalla para el OCR: escala 2,5x con Lanczos, mediana para ruido, CLAHE de contraste, sharpening, umbralización adaptativa Gaussiana y su inversión; devuelve los tres resultados (afinada, binaria e invertida) como lista para que el llamador pruebe cuál lee mejor.'
            ),
            "_iou": (
                '💡 LA IDEA: Es la regla que mide cuánto se superponen dos recuadros candidatos sobre la foto.\n\n'
                '🎯 POR QUE FUE GENERADA: Si dos detectores encontraron la misma patente en lugares casi idénticos, descarta el duplicado y se queda con el mejor.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula la intersección sobre unión de dos cajas `(x0, y0, x1, y1)`, devolviendo 0 si no hay unión; se usa para descartar candidatos solapados.'
            ),
            "_is_valid_plate_roi": (
                '💡 LA IDEA: Es el filtro de proporciones: descarta recuadros que sean demasiado chicos, cuadrados o gigantescos para ser una patente real.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el OCR gaste tiempo intentando leer una parrilla, una rueda o una calcomanía del parabrisas.\n\n'
                '⚙️ FUNCIONAMIENTO: Filtra un recorte candidato: descarta si mide menos de 70x18 px, si ocupa más del 85% del ancho del frame o si su relación de aspecto queda fuera del rango 1,5–6,0 (tamaños plausibles de una patente).'
            ),
            "find_plate_roi": (
                '💡 LA IDEA: Es el rastreador de emergencia: si la búsqueda principal falla, divide la imagen en franjas horizontales y busca contornos geométricos rectangulares para encontrar la chapa.\n\n'
                '🎯 POR QUE FUE GENERADA: Rescata lecturas de autos que entran cruzados o fuera del centro de la calzada.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve una lista de recortes candidatos a patente cuando el OCR principal falló: arma franjas horizontales (centro y abajo) divididas en segmentos, más cajas de contornos detectados con Canny/morfología, las ordena por prioridad y tamaño, valida con `_is_valid_plate_roi`, elimina solapamientos con `_iou` (máx. 10) y, si no queda ninguna, devuelve la ROI principal completa.'
            ),
            "is_mercosur_candidate": (
                '💡 LA IDEA: Es el detector de la franja azul oficial de las patentes Mercosur en la parte superior de la chapa.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber de inmediato si la chapa es del nuevo estándar Mercosur para aplicar los filtros correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte la ROI a HSV, mascara el rango de azul y mide qué proporción de los píxeles del 35% superior es azul; devuelve True si supera 0,06, es decir si se ve la franja azul Mercosur (tolerando impresiones en papel). Ante cualquier error devuelve False.'
            ),
            "crop_below_blue": (
                '💡 LA IDEA: Es la guillotina que corta la franja azul superior para quedarse solo con los caracteres blancos y negros.\n\n'
                "🎯 POR QUE FUE GENERADA: Evita que el OCR se confunda intentando leer la palabra 'ARGENTINA' o el escudo en vez de la patente del auto.\n\n"
                '⚙️ FUNCIONAMIENTO: Si hay franja azul en la mitad superior de la ROI, recorta todo lo que está por debajo del último píxel azul (más 5 px de margen) para quedarse solo con la zona de caracteres; devuelve la ROI original si no hay franja, si esta ocupa demasiado (>45% de la altura) o si el recorte resultante queda muy chico.'
            ),
        },
    },
    "alpr/runner.py": {
        "proposito": 'Punto de entrada del servicio de cámara: levanta el streamer, decide el modo según `GATE_TYPE` (solo streaming para predio; OCR y QR para entrada/salida/patente) y ejecuta el bucle principal que muestrea frames, aplica rate-limit de OCR y descarta frames sin movimiento.',
        "simbolos": {
            "run_alpr_service": (
                '💡 LA IDEA: Es el interruptor general que enciende la cámara: levanta el video, inicia la transmisión en vivo y pone a correr el motor de reconocimiento en un bucle continuo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ejecutar el sistema de cámaras como un programa independiente del servidor web, ideal para ponerlo en una microcomputadora al lado de la barrera.\n\n'
                "⚙️ FUNCIONAMIENTO: Ciclo principal: crea e inicia `VideoStreamer` (aborta con mensaje si falla), verifica que llegue imagen, y según `GATE_TYPE` queda en modo solo-streaming (hilo de WebSocket eterno) o arma `ALPREngine` con su hilo `ocr_worker` y el worker WebSocket. En el bucle infinito toma frames, intenta leer QR (si calza envía el evento y salta), y cada `OCR_INTERVAL` solo encola el frame si hay movimiento (o `FORCE_OCR`), avisando 'leyendo' y descartando frames viejos si la cola está llena; cuenta y loguea cada 5 s los frames descartados por falta de movimiento."
            ),
        },
    },
    "alpr/video_streamer.py": {
        "proposito": 'Captura el flujo de video (cámara IP o índice local) en un hilo propio y expone siempre el último frame al resto de los hilos de forma segura, redimensionado al ancho objetivo para no saturar CPU.',
        "simbolos": {
            "VideoStreamer": (
                '💡 LA IDEA: Es el proyector de cine: captura continuamente los fotogramas del lente de la cámara y mantiene siempre la foto más reciente lista para que cualquiera la consulte.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que la cámara se trabe si el reconocedor de patentes se toma unos milisegundos de más en pensar.\n\n'
                '⚙️ FUNCIONAMIENTO: Envuelve un `cv2.VideoCapture` con un lock y un hilo de lectura continuo para que OCR y WebSocket puedan pedir el frame actual sin bloquearse entre sí.'
            ),
            "VideoStreamer.__init__": (
                '💡 LA IDEA: Enchufa la cámara (por USB o por red IP RTSP), fija la resolución en alta definición (1280x720) y prepara los candados de memoria.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza una captura fluida y sin retardos en cualquier tipo de cámara de seguridad.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre la fuente: si es una URL HTTP usa FFmpeg con buffer de 1 frame y timeouts de 5 s de apertura/lectura; si no, abre el dispositivo directo. Fija resolución 1280x720, guarda el ancho objetivo y prepara `current_frame`, la bandera `is_running` y el lock.'
            ),
            "start": (
                '💡 LA IDEA: Dispara el motor de captura en segundo plano para que empiece a recibir video inmediatamente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el programa principal siga haciendo otras cosas mientras la cámara rueda sola.\n\n'
                '⚙️ FUNCIONAMIENTO: Lanza el hilo daemon que actualiza los frames y devuelve `self` para poder encadenar la creación (`VideoStreamer(...).start()`).'
            ),
            "_update": (
                '💡 LA IDEA: Es el bucle que lee foto tras foto sin parar, reintenta si se corta la señal y redimensiona la imagen para no sobrecalentar el equipo.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda tolerancia a fallos; si un cable de red de la cámara se afloja unos segundos, no se cuelga el programa sino que reintenta automáticamente.\n\n'
                '⚙️ FUNCIONAMIENTO: Bucle de captura: lee frames, reintenta hasta 3 veces con aviso si no llegan, redimensiona a `target_width` si el frame es más ancho y publica el resultado bajo el lock; cualquier excepción se loguea y espera 1 s antes de reintentar mientras `is_running` sea True.'
            ),
            "get_frame": (
                '💡 LA IDEA: Le entrega una copia fresca de la última foto del video a quien la pida, protegiendo la imagen con un candado para que nadie la modifique por error.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita errores de memoria o imágenes corruptas entre hilos concurrentes.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve una copia del último frame bajo el lock (o None si todavía no llegó ninguno), para que el consumidor no pueda alterar el buffer compartido.'
            ),
            "stop": (
                '💡 LA IDEA: Apaga la cámara y desconecta el lente ordenadamente cuando se cierra el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Libera el hardware de la cámara para que no quede bloqueada en Windows.\n\n'
                '⚙️ FUNCIONAMIENTO: Detiene el bucle `_update` y libera el `VideoCapture` si sigue abierto.'
            ),
        },
    },
    "alpr/ws_client.py": {
        "proposito": 'Mantiene una conexión WebSocket permanente con el backend para transmitir el video de la cámara (con overlay si hay motor OCR), con reconexión automática ante caídas.',
        "simbolos": {
            "ws_monitoring_worker": (
                '💡 LA IDEA: Es el cable coaxil virtual: transmite el video de la cámara en vivo por internet hacia el panel del guardia, y si la conexión a internet titila, reintenta conectarse solo cada 5 segundos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el administrador mire las cámaras de todas las sucursales desde cualquier navegador web en tiempo real sin necesidad de software especial.\n\n'
                '⚙️ FUNCIONAMIENTO: Coroutine que mientras el streamer esté vivo conecta a `WS_BACKEND_URL` (con ping cada 20 s), y en cada ciclo toma el frame, le aplica el overlay si hay `engine`, lo reduce a 640x360, lo comprime a JPEG calidad 50 y lo envía en base64; duerme 0,05 s entre frames, cierra el ciclo si falla el envío, y ante cualquier error de conexión espera 5 s y reconecta.'
            ),
        },
    },
}
