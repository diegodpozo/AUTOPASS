"""Explicaciones analizadas de core (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "core/__init__.py": {
        "proposito": (
            "💡 LA IDEA: Es la 'piedra fundamental de los cimientos' de la aplicación. Convierte a la carpeta `core` en el corazón técnico compartido del sistema, donde viven todas las herramientas que cualquier parte del proyecto necesita (la base de datos, las contraseñas, la seguridad y los registros de actividad).\n\n"
            "🎯 POR QUE FUE GENERADA: En Python, para que los archivos de distintas carpetas (rutas, servicios, modelos) puedan importar herramientas comunes con la sintaxis limpia `from core.database import get_db` o `from core.config import settings`, el directorio debe ser reconocido formalmente como un paquete del sistema.\n\n"
            "⚙️ FUNCIONAMIENTO: Declara formalmente al directorio `core/` como un módulo importable en Python, centralizando las dependencias transversales de infraestructura para que toda la arquitectura de capas pueda comunicarse fluidamente sin rutas relativas complejas."
        ),
        "simbolos": {
        },
    },
    "core/alpr_security.py": {
        "proposito": 'Protege los endpoints de acceso por patente/QR que invocan los nodos ALPR (cámaras/lectores): decide si un llamador es un nodo autorizado, usando la IP de origen (red local/privada) o un secreto compartido configurado por variable de entorno.',
        "simbolos": {
            "is_local_or_private": (
                '💡 LA IDEA: Es el portero que mira si quien toca el timbre viene desde adentro de la casa o desde el jardín de entrada (dirección IP local 127.0.0.1 o red privada de la empresa), en lugar de venir desde la calle pública de internet.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que un intruso remoto desde cualquier parte del mundo intente mandar peticiones simulando ser una cámara física del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte el host recibido en un objeto ip_address y devuelve True si es loopback (127.0.0.1/::1) o una red privada. Si el texto no es una IP válida (ValueError) devuelve False: ante dato dudoso se deniega.'
            ),
            "is_trusted_alpr_node": (
                "💡 LA IDEA: Es el sistema de 'contraseña secreta por walkie-talkie' entre la cámara y el servidor. Compara la clave de la cámara con el secreto oficial en un tiempo matemáticamente idéntico (`compare_digest`), para que nadie pueda adivinar la clave midiendo millonésimas de segundo.\n\n"
                '🎯 POR QUE FUE GENERADA: Resuelve el riesgo de falsificación de patentes; si alguien conecta una cámara no autorizada a la red, no podrá abrir barreras sin conocer el secreto compartido.\n\n'
                '⚙️ FUNCIONAMIENTO: Si hay un ALPR_NODE_SECRET configurado, exige que el secreto enviado por el nodo coincida con él, comparándolo con secrets.compare_digest (comparación en tiempo constante para evitar ataques por timing) y descartando cadenas vacías. Si no hay secreto configurado, acepta cualquier nodo cuya IP sea local o privada (modo ALPR en la misma máquina).'
            ),
            "require_alpr_node": (
                "💡 LA IDEA: Es la traba de seguridad en la puerta del endpoint de patentes. Si la cámara no demuestra ser de confianza, le frena el paso inmediatamente con un cartel de 'Acceso Denegado' (error HTTP 403).\n\n"
                '🎯 POR QUE FUE GENERADA: Protege los endpoints críticos de apertura de barrera para que FastAPI rechace automáticamente cualquier mensaje que no provenga de un nodo ALPR legítimo.\n\n'
                "⚙️ FUNCIONAMIENTO: Dependencia de FastAPI: toma el secreto del header x-node-secret o del parámetro de query node_secret, y la IP del cliente de la conexión. Si is_trusted_alpr_node no valida, lanza HTTPException 403 con detalle 'Nodo ALPR no autorizado' y corta la petición."
            ),
        },
    },
    "core/cache.py": {
        "proposito": 'Caché en memoria con TTL (tiempo de vida limitado) para no repetir consultas caras en endpoints de alta concurrencia, con invalidación explícita por prefijo de clave. El módulo crea una instancia compartida `ttl_cache` con 5 segundos por defecto que reutilizan los demás componentes.',
        "simbolos": {
            "SimpleTTLCache": (
                "💡 LA IDEA: Es un anotador tipo 'pizarrón con temporizador' en el escritorio del recepcionista: en vez de llamar a archivo cada vez que preguntan lo mismo, anota la respuesta y le pone una hora de vencimiento de unos pocos segundos.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita colapsar la base de datos con cientos de consultas idénticas por segundo cuando muchos usuarios miran la ocupación o tarifas al mismo instante.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase de caché genérica: guarda en un diccionario interno tuplas (valor, instante de expiración) calculadas con time.time(), con un TTL por defecto configurable y soporte de invalidación selectiva. No es thread-safe ni persiste entre reinicios: vive solo en memoria del proceso.'
            ),
            "__init__": (
                '💡 LA IDEA: Compra el pizarrón nuevo, define que por defecto las notas duran 5 segundos y borra cualquier rastro previo para empezar de cero.\n\n'
                '🎯 POR QUE FUE GENERADA: Inicializa el almacenamiento en memoria con una vigencia prudente para que los datos nunca queden desactualizados por mucho tiempo.\n\n'
                '⚙️ FUNCIONAMIENTO: Recibe el TTL por defecto (5 segundos si no se pasa) y crea el diccionario vacío _store donde se guardan los pares clave -> (valor, expiración).'
            ),
            "get": (
                '💡 LA IDEA: Mira si la respuesta está anotada en el pizarrón; si todavía no se venció el tiempo la entrega al instante, y si ya expiró, le pasa el borrador y responde que no la tiene.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra tiempo de procesamiento entregando datos frescos de inmediato y descartando automáticamente la información vieja.\n\n'
                '⚙️ FUNCIONAMIENTO: Si la clave existe y todavía no venció, devuelve el valor guardado. Si venció, la elimina del diccionario y devuelve None; si no existe, también devuelve None.'
            ),
            "set": (
                '💡 LA IDEA: Escribe un dato nuevo en el pizarrón junto con la hora exacta en la que perderá validez.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite guardar el resultado de operaciones pesadas para que estén disponibles al instante durante los próximos segundos.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el valor asociado a la clave con fecha de expiración igual a ahora más el TTL indicado, o al TTL por defecto de la instancia si no se pasa ninguno.'
            ),
            "invalidate": (
                '💡 LA IDEA: Es el borrador selectivo: permite borrar todo el pizarrón o pasar el borrador solo sobre las notas que pertenecen a una sucursal específica.\n\n'
                '🎯 POR QUE FUE GENERADA: Si el administrador cambia el precio de una playa, esta función borra de inmediato el caché de esa sede para que los clientes vean la nueva tarifa sin tener que esperar a que expire el tiempo.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin prefijo limpia toda la caché (clear del diccionario); con prefijo, recorre las claves y borra solo las que empiezan con ese texto, permitiendo invalidar un grupo relacionado (por ejemplo todas las claves de una sucursal) sin vaciar el resto.'
            ),
        },
    },
    "core/config.py": {
        "proposito": 'Carga la configuración de todo el sistema desde el archivo .env y las variables de entorno, con valores por defecto seguros para desarrollo, y la expone como el singleton `settings` que importa el resto del proyecto. También deriva la versión del proyecto a partir del historial de git.',
        "simbolos": {
            "_version": (
                '💡 LA IDEA: Es un detective que revisa los últimos 50 mensajes del historial de Git para descubrir qué número de versión (`vX.Y.Z`) tiene el sistema actualmente.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita tener que actualizar a mano el número de versión en archivos de código cada vez que se publica una mejora; se deduce solo del historial de cambios.\n\n'
                "⚙️ FUNCIONAMIENTO: Función cacheada con lru_cache que ejecuta `git log -50 --format=%s` en el repositorio y busca una versión en los subjects de los commits: primero prueba el patrón canónico (vX.Y.Z al inicio del subject) y recién después el incidental (por ejemplo 'refactor(v9.34.17):'), de modo que un commit viejo con forma canónica gana sobre uno nuevo incidental. Sin git, sin commits o sin ninguna versión devuelve el fallback '0.0.0' y registra un warning pidiendo versionar con prefijo 'vX.Y.Z:'."
            ),
            "Settings": (
                "💡 LA IDEA: Es el 'manual de especificaciones y tablero de fusibles' central del edificio. Lee el archivo `.env` y reúne en un solo lugar todas las llaves maestras: contraseñas de base de datos, claves de Mercado Pago, servidores de correo y puertos de hardware.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita desparramar claves y URLs fijas por todo el código. Permite cambiar de SQLite a PostgreSQL o cambiar de credenciales con solo editar un archivo de texto, sin tocar una sola línea del programa.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase que agrupa toda la configuración de AUTOPASS como atributos de clase con su valor por defecto: identidad del proyecto y versión, correos de contacto, seguridad JWT (SECRET_KEY, algoritmo, expiración de tokens), CORS permitido, secreto de los nodos ALPR, URL de la base de datos (SQLite por defecto), SMTP de correo (Mailtrap en desarrollo), vigencia de tokens de recuperación e invitación, broker y tópicos MQTT, hardware serial del Arduino, tarifas por defecto, rutas de assets y retención de imágenes, mínimos de reserva, intervalos de mantenimiento y heartbeat, credenciales y tiempos de Mercado Pago, y credenciales OAuth de Google y Facebook. La mayoría lee os.getenv con fallback, así que se sobrescribe por variables de entorno sin tocar el código.'
            ),
            "MP_ENABLED": (
                '💡 LA IDEA: Es una palanquita de encendido/apagado para Mercado Pago: revisa si se configuró un token de cobro real o si está en blanco.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el sistema funcione fluidamente en modo desarrollo o demostración sin arrojar errores de cobro si no se tienen cuentas comerciales configuradas.\n\n'
                '⚙️ FUNCIONAMIENTO: Propiedad calculada de Settings: devuelve True si MP_ACCESS_TOKEN tiene contenido después de quitar espacios en blanco. Define si el checkout de Mercado Pago está habilitado: sin token (modo vacío) el frontend y el backend ocultan o desactivan todo lo relacionado con MP.'
            ),
        },
    },
    "core/database.py": {
        "proposito": 'Armazón de datos del proyecto: crea el motor de SQLAlchemy según la URL configurada, la fábrica de sesiones y la Base de modelos, y define el flujo de sincronización del esquema al arrancar (modelos + Alembic). Es la capa de la que cuelgan todos los repositories y endpoints vía la dependencia get_db.',
        "simbolos": {
            "normalize_database_url": (
                '💡 LA IDEA: Es un traductor de direcciones de base de datos: si recibe una URL de PostgreSQL genérica, le agrega el adaptador moderno (`postgresql+psycopg://`) para que Python entienda cómo hablarle.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita errores de compatibilidad de drivers entre SQLAlchemy y las versiones nuevas de PostgreSQL en servidores de prueba o nube.\n\n'
                "⚙️ FUNCIONAMIENTO: Si la URL está vacía devuelve la SQLite por defecto ('sqlite:///./parking.db'). Si es 'postgresql://...' sin driver explícito (no hay un '+' antes de '://'), la reescribe a 'postgresql+psycopg://...' para que SQLAlchemy use el driver psycopg 3; si ya trae un driver, la devuelve sin tocar."
            ),
            "get_db": (
                '💡 LA IDEA: Es la ventanilla que le entrega una ficha de conexión a la base de datos a cada cliente que llega, y pase lo que pase, se asegura de recuperarla y cerrarla cuando el cliente se va.\n\n'
                "🎯 POR QUE FUE GENERADA: Evita las 'fugas de conexiones' (connection leaks), un problema gravísimo que ocurre cuando una petición falla y deja conexiones abiertas en el servidor hasta que la base de datos se bloquea y deja de responder.\n\n"
                '⚙️ FUNCIONAMIENTO: Dependencia generadora de FastAPI: abre una sesión con SessionLocal, la cede al endpoint con yield y la cierra siempre en el bloque finally, incluso si el endpoint lanza error. Así cada petición trabaja con su propia sesión y no queda ninguna conexión abierta.'
            ),
            "init_db": (
                '💡 LA IDEA: Es el constructor que revisa si el terreno tiene cimientos: mira todos los modelos del sistema y crea las tablas que falten en el archivo o motor de base de datos.\n\n'
                "🎯 POR QUE FUE GENERADA: Garantiza que la primera vez que se prende el sistema no explote con errores de 'tabla no encontrada'.\n\n"
                '⚙️ FUNCIONAMIENTO: Importa el paquete models (necesario para que todas las clases se registren en Base.metadata) y ejecuta create_all sobre el motor, creando las tablas que aún no existen. No altera ni borra columnas existentes.'
            ),
            "sync_schema": (
                '💡 LA IDEA: Es el inspector de obras que sincroniza el plano con la construcción real: crea las tablas con SQLAlchemy y luego sella la versión de Alembic al día más reciente (`head`).\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve conflictos entre la creación directa de tablas y las migraciones de Alembic, garantizando que el servidor arranque sin importar si la base era virgen o ya existía.\n\n'
                "⚙️ FUNCIONAMIENTO: Flujo único de esquema al arrancar: primero llama a init_db (los modelos crean las tablas faltantes) y después intenta llevar Alembic a 'head'. Compara los heads del script con la revisión actual de la BD: si ya está al día devuelve True; si el upgrade falla porque la cadena de migraciones no es reproducible desde cero (create_all ya materializó el esquema), sella la versión con 'stamp head' y emite un warning, devolviendo igualmente True; si Alembic ni siquiera está disponible devuelve False; si falla también el stamp, relanza la excepción."
            ),
        },
    },
    "core/limiter.py": {
        "proposito": 'Configura el limitador de tasa centralizado de la app (slowapi) con una clave por dirección IP remota y un límite global de 300 peticiones por minuto, y expone la dependencia de límite para el panel administrativo.',
        "simbolos": {
            "admin_rate_limit": (
                '💡 LA IDEA: Es un molinete que solo deja pasar hasta 30 peticiones por minuto por cada computadora en los paneles de administración.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que un atacante intente adivinar contraseñas o bombardear el panel administrativo con miles de clics por segundo para saturarlo.\n\n'
                "⚙️ FUNCIONAMIENTO: Función decorada con @limiter.limit('30/minute') que no hace nada por sí misma (devuelve None): se inyecta como dependency de FastAPI en los endpoints de mutación del panel admin y slowapi aplica el límite de 30 peticiones por minuto por IP al recibir el request. Dejarla sin parámetros en la firma permite llamar las funciones de negocio directamente desde los tests sin pasar un request."
            ),
        },
    },
    "core/logger.py": {
        "proposito": 'Centraliza el sistema de logging de la aplicación: formato, nivel y salida estándar por una sola vía, baja el ruido de las librerías externas y ofrece una utilidad para enmascarar correos electrónicos antes de escribirlos en los logs.',
        "simbolos": {
            "setup_logging": (
                '💡 LA IDEA: Es el director de comunicaciones de la empresa: define un formato prolijo y ordenado para los mensajes en pantalla y le baja el volumen a librerías ruidosas (como SQLAlchemy o Uvicorn) para que no tapen los mensajes importantes del negocio.\n\n'
                '🎯 POR QUE FUE GENERADA: Sin esta función, la consola se llenaría de miles de líneas técnicas incomprensibles cada segundo, haciendo imposible encontrar errores reales del estacionamiento.\n\n'
                "⚙️ FUNCIONAMIENTO: Silencia los warnings de tipo DeprecationWarning y UserWarning, y configura logging.basicConfig con formato '[fecha] NIVEL nombre: mensaje', nivel INFO por defecto y salida a stdout (force=True para pisar configuraciones previas). Además baja a WARNING los loggers verbosos que ensucian cada arranque: sqlalchemy.engine, uvicorn (access y error), alembic y sus migraciones, y paho.mqtt."
            ),
            "get_logger": (
                '💡 LA IDEA: Le entrega un micrófono identificado con su nombre a cada archivo del sistema (por ejemplo `services.access_service`), para saber exactamente quién emitió cada mensaje.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite rastrear al instante en qué archivo y función ocurrió un problema al leer el archivo de registros.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el logger estándar de Python con el nombre que recibe (casi siempre __name__ del módulo que llama), para que los mensajes aparezcan firmados por el módulo correcto dentro del formato global.'
            ),
            "mask_email": (
                '💡 LA IDEA: Es una cinta adhesiva negra que censura parte del correo electrónico (convierte `juan.perez@mail.com` en `jua***@mail.com`).\n\n'
                '🎯 POR QUE FUE GENERADA: Cumple con normas de privacidad y protección de datos personales, evitando que los correos de los clientes queden expuestos en archivos de log de texto plano.\n\n'
                "⚙️ FUNCIONAMIENTO: Enmascara un correo para poder registrarlo sin exponerlo: si está vacío o no tiene '@', lo devuelve como texto tal cual; si el usuario tiene 3 caracteres o menos devuelve '***@dominio'; en el contrario conserva los primeros 3 caracteres y agrega '***@dominio' (por ejemplo 'juan.perez@mail.com' -> 'jua***@mail.com')."
            ),
        },
    },
    "core/mqtt.py": {
        "proposito": (
            "💡 LA IDEA: ES EL TRANSMISOR Y CANAL DE TELECOMUNICACION IOT EXCLUSIVO PARA EL ACCIONAMIENTO DE LAS BARRERAS FISICAS DEL ESTACIONAMIENTO.\n\n"
            "⚠️ ACLARACION FUNDAMENTAL DE ARQUITECTURA:\n"
            "1. NO SE CONECTA NI GESTIONA LAS CAMARAS: LAS CAMARAS NO UTILIZAN MQTT BAJO NINGUN CONCEPTO. TRANSMITEN FLUJOS PESADOS DE VIDEO EN VIVO MEDIANTE RTSP / HTTP CAPTURADOS POR OPENCV (EN ALPR/VIDEO_STREAMER.PY) Y ENVIAN LAS PATENTES RECONOCIDAS AL SERVIDOR A TRAVES DE WEBSOCKETS (ALPR/WS_CLIENT.PY).\n\n"
            "2. QUIEN GENERA LOS COMANDOS DE APERTURA Y CIERRE: ESTE ARCHIVO NO TOMA DECISIONES NI CREA ORDENES DE PASO. EL VERDADERO RESPONSABLE DE GENERAR LOS COMANDOS DE APERTURA Y CIERRE ('OPEN' / 'CLOSE') ES EL SERVICIO SERVICES/HARDWARE_SERVICE.PY A TRAVES DE SU METODO CENTRAL HARDWARESERVICE.TRIGGER_BARRIER().\n\n"
            "3. ROL EXACTO DE CORE/MQTT.PY: ESTE ARCHIVO UNICAMENTE CONFIGURA, INSTANCIA Y EXPORTA EL CLIENTE OFICIAL PAHO MQTT (MQTT_CLIENT). AL INICIAR LA APLICACION, MAIN.PY SE CONECTA AL BROKER (BROKER.HIVEMQ.COM:1883) Y LEVANTA EL HILO DE ESCUCHA (LOOP_START). CUANDO ACCESS_SERVICE O EL OPERADOR DE GARITA AUTORIZAN UN ACCESO, HARDWARE_SERVICE USA ESTE CLIENTE PARA PUBLICAR EL MENSAJE JSON EN LOS TOPICOS 'MQTT_TOPIC_ENTRADA' O 'MQTT_TOPIC_SALIDA', LOGRANDO QUE EL MICROCONTROLADOR ESP32 DE LA BARRERA LEVANTE EL BRAZO MECANICO.\n\n"
            "🎯 POR QUE FUE GENERADA: LAS BARRERAS FISICAS (ACCIONADAS POR PLACAS ESP32 CON WI-FI O ARDUINO) REQUIEREN UN CANAL INALAMBRICO ULTRALIVIANO, ASINCRONICO Y DE MUY BAJA LATENCIA QUE NO BLOQUEE AL SERVIDOR PRINCIPAL.\n\n"
            "⚙️ FUNCIONAMIENTO: CONFIGURA EL CLIENTE MQTT DE PAHO UTILIZANDO CALLBACKAPIVERSION.VERSION2 Y CREA EL SINGLETON GLOBAL MQTT_CLIENT DISPONIBLE PARA TODA LA APLICACION."
        ),
        "simbolos": {
            "get_mqtt_client": (
                "💡 LA IDEA: ES LA FABRICA QUE CONSTRUYE Y CALIBRA EL CLIENTE DE COMUNICACION MQTT CON LA VERSION MODERNA DE CALLBACKS DE PAHO.\n\n"
                "🎯 POR QUE FUE GENERADA: AISLA Y CENTRALIZA LA CONFIGURACION TECNICA DEL CLIENTE MQTT PARA EVITAR DISCREPANCIAS O CODIGO DUPLICADO EN EL RESTO DEL SISTEMA.\n\n"
                "⚙️ FUNCIONAMIENTO: RETORNA UN OBJETO MQTT.CLIENT CONFIGURADO CON CALLBACKAPIVERSION.VERSION2 LISTO PARA VINCULARSE AL BROKER Y ASIGNARSE A LA INSTANCIA GLOBAL."
            ),
        },
    },
    "core/normalize.py": {
        "proposito": "Conjunto de funciones de normalización canónicas del dominio: nombres de sucursal y usuario, patentes y DNI. Estándarizan cómo se guardan y se comparan esos datos en todo el proyecto para que 'Castelar', 'castelar ' o 'AUTOPASS Castelar' se traten como lo mismo, y para que las patentes y DNIs se validen con un único criterio.",
        "simbolos": {
            "normalize_name": (
                "💡 LA IDEA: Es la plancha que alisa los textos: pasa todo a mayúsculas, quita acentos y elimina palabras repetitivas como 'AUTOPASS ' para que dos nombres escritos de forma distinta se comparen de igual a igual.\n\n"
                "🎯 POR QUE FUE GENERADA: Evita que el sistema confunda o duplique sucursales por pequeñas diferencias de escritura (como 'Centro' vs 'CENTRO' o 'Autopass Centro').\n\n"
                "⚙️ FUNCIONAMIENTO: Si el texto está vacío devuelve cadena vacía. Lo pasa a mayúsculas, elimina el prefijo 'AUTOPASS ' y los espacios sobrantes, y quita las tildes con una normalización NFD que descarta los caracteres diacríticos (categoría Mn), dejando solo letras planas en mayúsculas."
            ),
            "normalize_branch_name": (
                '💡 LA IDEA: Es la regla de normalización aplicada exclusivamente a nombres de sucursales para que siempre sigan el estándar canónico del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que la búsqueda y asignación de cocheras no falle por diferencias de mayúsculas o espacios.\n\n'
                "⚙️ FUNCIONAMIENTO: Delega directamente en normalize_name: los nombres de sucursal se normalizan con la misma regla canónica que el resto de los nombres del proyecto (mayúsculas, sin prefijo 'AUTOPASS ', sin acentos)."
            ),
            "same_branch": (
                '💡 LA IDEA: Es el juez que compara dos nombres de sucursal y dictamina si se refieren exactamente al mismo lugar físico, ignorando diferencias menores de tipeo.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que un usuario o administrador quede bloqueado al buscar reservas porque una pantalla escribió la sede con tilde y la otra sin tilde.\n\n'
                '⚙️ FUNCIONAMIENTO: Normaliza ambos nombres de sucursal y compara. Devuelve False si el primero queda vacío después de normalizar (se deniega ante dato faltante) o si las formas canónicas no coinciden; solo devuelve True si las dos sedes refieren al mismo lugar según la normalización del proyecto.'
            ),
            "normalize_user_name": (
                '💡 LA IDEA: Es el estilista de nombres de personas: recorta espacios sobrantes y pone en mayúscula la primera letra de cada palabra (formato título) para que se vea elegante en la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Logra que la interfaz de bienvenida y los tickets muestren nombres limpios y profesionales aunque el usuario se haya registrado todo en minúsculas.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el texto está vacío devuelve cadena vacía; si no, recorta los espacios de los extremos y aplica title() para mostrar el nombre propio con la primera letra de cada palabra en mayúscula (formato de visualización, no de comparación).'
            ),
            "normalize_plate": (
                '💡 LA IDEA: Es el limpiador de patentes: pasa todo a mayúsculas y barre con guiones, espacios y puntos, dejando únicamente letras y números puros.\n\n'
                "🎯 POR QUE FUE GENERADA: Evita que la cámara ALPR no reconozca un auto porque en la base de datos la patente se guardó como 'AA-123-BB' y la cámara leyó 'AA123BB'.\n\n"
                '⚙️ FUNCIONAMIENTO: Si la patente está vacía devuelve cadena vacía; si no, la convierte a mayúsculas y elimina con re.sub todo lo que no sea letra A-Z o dígito 0-9, dejando la patente en su forma canónica sin espacios ni guiones.'
            ),
            "is_valid_plate": (
                '💡 LA IDEA: Es el inspector de aduana que revisa si la combinación de letras y números respeta los formatos legales de patentes de Argentina, Brasil, Uruguay o Paraguay.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que los usuarios ingresen patentes inventadas o textos basura que romperían el cobro y la apertura automática.\n\n'
                '⚙️ FUNCIONAMIENTO: Normaliza la patente con normalize_plate y la contrae contra una unión de regex de formatos LATAM reconocidos (Argentina clásico y Mercosur para auto y moto, Brasil, Uruguay y Paraguay). Devuelve False si tras normalizar queda vacía o si no coincide con ningún patrón.'
            ),
            "format_plate": (
                "💡 LA IDEA: Es el diseñador de chapa patente: toma las letras y números limpios y les coloca los espacios en el lugar exacto según el país (ej: 'AB 123 CD' para Mercosur Argentina o 'ABC 123' para el formato clásico).\n\n"
                '🎯 POR QUE FUE GENERADA: Hace que las patentes se lean con naturalidad y claridad humana en los listados, tarjetas y tickets del sistema.\n\n'
                "⚙️ FUNCIONAMIENTO: Normaliza la patente y le aplica el formato visual según su longitud y la distribución de letras y dígitos: 6 caracteres -> 'ABC 123' (Argentina antigua); 7 con dígitos en el medio -> 'AB 123 CD' (Mercosur argentina); si el cuarto es dígito y el quinto letra -> 'ABC 1D23' (Brasil Mercosur); si los últimos cuatro son dígitos -> 'ABC 1234' (Uruguay); si los primeros cuatro son letras -> 'ABCD 123' (Paraguay autos); si los primeros tres son dígitos -> '123 ABCD' (Paraguay motos). Si no reconoce el formato, devuelve la patente limpia sin espacios."
            ),
            "normalize_dni": (
                '💡 LA IDEA: Es el extractor numérico de documentos: quita puntos, comas y espacios dejando exclusivamente los dígitos del DNI.\n\n'
                "🎯 POR QUE FUE GENERADA: Evita que una persona figure como dos clientes distintos porque en un formulario escribió '35.123.456' y en otro '35123456'.\n\n"
                "⚙️ FUNCIONAMIENTO: Si el DNI está vacío devuelve cadena vacía; si no, elimina con re.sub todo lo que no sea dígito, dejando solo números. Unifica así '12.345.678', '12 345 678' y '12345678' en una única forma canónica para guardar y comparar."
            ),
            "format_dni": (
                '💡 LA IDEA: Asegura que el DNI se muestre de forma limpia y consistente en todas las vistas del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene unificada la presentación visual del documento en toda la plataforma.\n\n'
                '⚙️ FUNCIONAMIENTO: Delega en normalize_dni: para visualización devuelve el DNI solo con dígitos y sin puntos, con el mismo criterio que la forma canónica guardada en la base.'
            ),
        },
    },
    "core/security.py": {
        "proposito": 'Núcleo de autenticación y autorización de AUTOPASS: hash de contraseñas con bcrypt, emisión y validación de JWT (con lista de revocados para logout), dependencias FastAPI que controlan rol de usuario y las reglas de aislamiento por sucursal y por organización multiempresa.',
        "simbolos": {
            "revoke_token": (
                "💡 LA IDEA: Es el libro de pases anulados: cuando un usuario pulsa 'Cerrar Sesión', anota el número de serie de su pase digital (JTI) en una lista negra para que nadie pueda volver a usarlo.\n\n"
                '🎯 POR QUE FUE GENERADA: Resuelve la vulnerabilidad de que alguien copie el token JWT antes de cerrar sesión y pretenda seguir entrando después de que el usuario se fue.\n\n'
                "⚙️ FUNCIONAMIENTO: Para el logout: decodifica el token con la clave y algoritmo del proyecto; si el token es inválido (JWTError) sale sin hacer nada, y si es válido extrae el 'jti' y lo agrega al set _revoked_jtis. Ese set vive en memoria, por lo que la revocación se pierde al reiniciar el proceso."
            ),
            "verify_password": (
                '💡 LA IDEA: Es el cerrajero que prueba si la llave que ingresa el usuario encaja matemáticamente en el candado encriptado guardado en la base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite autenticar al usuario de manera ultra segura sin necesidad de saber ni almacenar su contraseña real en texto plano.\n\n'
                '⚙️ FUNCIONAMIENTO: Compara la contraseña en texto plano con su hash usando bcrypt.checkpw (ambas en bytes UTF-8) y devuelve True o False. No lanza excepciones: ante cualquier problema de formato bcrypt devuelve False.'
            ),
            "get_password_hash": (
                '💡 LA IDEA: Es la trituradora irreversible: toma una contraseña elegida por el usuario, le añade una pizca de sal aleatoria y la convierte en un código indescifrable (`bcrypt`).\n\n'
                '🎯 POR QUE FUE GENERADA: Protege a los usuarios en caso de robo o filtración de la base de datos; nadie podrá leer las contraseñas originales.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera un salt nuevo con bcrypt.gensalt() y devuelve el hash de la contraseña como string UTF-8. Se usa al crear usuarios y en el seed inicial.'
            ),
            "create_access_token": (
                '💡 LA IDEA: Es la máquina que imprime pases VIP plastificados con fecha de vencimiento y firma digital infalsificable del estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el usuario navegue por toda la aplicación demostrando quién es sin tener que reenviar su usuario y contraseña en cada clic.\n\n'
                "⚙️ FUNCIONAMIENTO: Copia los datos recibidos, calcula la expiración con utcnow() más el expires_delta indicado (o 15 minutos por defecto), y agrega al payload 'exp', 'iat', un 'jti' único (uuid4 en hex, que después permite revocar) y 'token_type' tomado de 'purpose' o 'access'. Firma el todo con SECRET_KEY y ALGORITHM (HS256 por defecto) y devuelve el JWT como string."
            ),
            "decode_access_token": (
                '💡 LA IDEA: Es el escáner del guardia que lee el pase digital, comprueba que la firma sea legítima, verifica que no esté vencido y confirma que no esté en la lista de pases anulados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que solo peticiones legítimas y no manipuladas puedan acceder a la información privada del sistema.\n\n'
                "⚙️ FUNCIONAMIENTO: Decodifica y verifica la firma del token; si falla (JWTError) devuelve None. Además rechaza los tokens cuyo token_type no sea 'access' (así un token de recuperación o de signup OAuth no sirve como sesión) y los que tengan el jti en la lista de revocados; solo en el caso completamente válido devuelve el payload."
            ),
            "get_current_user": (
                '💡 LA IDEA: Es el recepcionista que recibe el pase digital del navegador, busca al usuario en el padrón y se fija si su cuenta no fue suspendida o eliminada.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona el usuario autenticado a cualquier endpoint de FastAPI de forma automática y segura, cortando el acceso a cuentas dadas de baja.\n\n'
                "⚙️ FUNCIONAMIENTO: Dependencia que extrae el token con oauth2_scheme y arma un HTTPException 401 por defecto. Cualquiera de estas situaciones termina en 401: JWT inválido o expirado, token que no es de acceso, jti revocado, payload sin 'sub' (email), o usuario inexistente o borrado (is_deleted). Si el usuario existe pero está bloqueado (is_blocked) lanza 403 con mensaje de cuenta suspendida. Si todo está bien, consulta la tabla User por email y devuelve la instancia."
            ),
            "get_super_admin": (
                '💡 LA IDEA: Es la puerta con lector biométrico que solo se abre para el Administrador Global de la empresa.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que empleados de playa o clientes comunes accedan a configuraciones delicadas del negocio o balances contables.\n\n'
                "⚙️ FUNCIONAMIENTO: Dependencia de autorización: si el rol del usuario no es ADMIN (comparado como string contra UserRole.ADMIN) lanza 403 'Requiere permisos de Administrador Global'; si lo es, devuelve el usuario para que el endpoint lo use."
            ),
            "get_local_manager": (
                '💡 LA IDEA: Es la llave de acceso para los encargados de sucursal y administradores generales.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que los gerentes locales gestionen su propia playa y su personal sin permitir el paso al público general.\n\n'
                "⚙️ FUNCIONAMIENTO: Dependencia que acepta los roles ADMIN y LOCAL_ADMIN; cualquier otro rol recibe 403 'Requiere permisos de gestión administrativa'. Devuelve el usuario autenticado cuando pasa el control."
            ),
            "is_operational_role": (
                "💡 LA IDEA: Es el carnet de 'Personal de Servicio': verifica si alguien pertenece al equipo de trabajo (Admin, Gerente Local o Empleado de Barrera).\n\n"
                '🎯 POR QUE FUE GENERADA: Simplifica los controles de acceso en pantallas operativas compartidas por todo el equipo de trabajo.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve True si el rol (funciona tanto con enums de UserRole como con strings, gracias a getattr sobre 'value') pertenece al tuple OPERATIONAL_ROLES: ADMIN, LOCAL_ADMIN o STAFF. Sirve como filtro común de personal operativo."
            ),
            "get_operational_user": (
                '💡 LA IDEA: La barrera de seguridad que valida que quien realiza una maniobra de cochera sea un miembro acreditado del personal operativo.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que un cliente final pueda ejecutar operaciones manuales de barrera o cambios de estado de estadías.\n\n'
                "⚙️ FUNCIONAMIENTO: Dependencia que encadena get_current_user y después valida is_operational_role con el rol del usuario; si no es personal operativo lanza 403 'Acceso restringido a personal autorizado' y si pasa devuelve el usuario."
            ),
            "validate_local_admin_branch": (
                "💡 LA IDEA: Es el límite de jurisdicción: se asegura de que el encargado de la sede 'Morón' no pueda modificar las tarifas o cocheras de la sede 'Palermo'.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita interferencias y desconfiguraciones accidentales entre administradores de distintas sucursales.\n\n'
                "⚙️ FUNCIONAMIENTO: Control de sucursal para endpoints que reciben recursos por id (algo que una dependencia de rol no puede saber): si el usuario es ADMIN global pasa sin restricción; si es LOCAL_ADMIN, normaliza su sucursal y la del recurso con normalize_branch_name y, si no coinciden, lanza 403 'No tenés permisos sobre recursos de otra sucursal'. Así 'Castelar' y 'castelar' se tratan como la misma sede."
            ),
            "is_principal_org_admin": (
                '💡 LA IDEA: El pase maestro del dueño supremo de la franquicia de estacionamientos: distingue al administrador principal de la cadena de los administradores de inquilinos secundarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite gobernar la plataforma a nivel global en arquitecturas multiempresa.\n\n'
                '⚙️ FUNCIONAMIENTO: Indica si el usuario es ADMIN de la organización marcada como es_principal (super-admin de plataforma, que puede gestionar a todos los demás Admin Generales). Es tolerante: devuelve False si el user es None o su rol no es ADMIN, y también devuelve False si al mirar user.organization ocurre cualquier error (por ejemplo la instancia quedó desligada de la sesión), sin lanzar excepción.'
            ),
            "enforce_organization_scope": (
                "💡 LA IDEA: Es la pared divisoria entre empresas: impide tajantemente que la empresa 'A' pueda espiar o alterar los datos y autos de la empresa 'B'.\n\n"
                '🎯 POR QUE FUE GENERADA: Garantiza el aislamiento total de datos en entornos multiempresa (multi-tenant), protegiendo el secreto comercial.\n\n'
                '⚙️ FUNCIONAMIENTO: Aislamiento multiempresa: un administrador solo opera recursos de su organización. Si el actor o el recurso no tienen organization_id (datos legacy o de tests) no restringe, preservando el comportamiento single-tenant; si el actor es super-admin de la organización principal pasa siempre; y si los ids difieren lanza HTTPException con el status_code y el detail que reciba por parámetro (403 y un mensaje genérico por defecto).'
            ),
            "authenticate_user": (
                '💡 LA IDEA: Es la ventanilla de recepción de credenciales: recibe el correo y la contraseña, busca al cliente y valida que la clave sea correcta y que la cuenta no esté congelada.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el corazón del inicio de sesión seguro; unifica todas las validaciones de acceso en un único punto a prueba de fallos.\n\n'
                "⚙️ FUNCIONAMIENTO: Busca el usuario por email con is_deleted == False; si no existe devuelve None, y si la contraseña no verifica con bcrypt contra password_hash también devuelve None (sin distinguuir el motivo, para no filtrar cuentas). Si el usuario existe pero está bloqueado (is_blocked), lanza 403 'Tu cuenta ha sido suspendida'. Con credenciales válidas devuelve la instancia de User."
            ),
        },
    },
    "core/seed.py": {
        "proposito": 'Siembra los datos maestros iniciales de AUTOPASS al arrancar con la base vacía: organización principal, usuarios administradores de prueba, aforo global, tarifas, promociones y la red inicial de sucursales. Es idempotente: solo crea lo que falta y también repara datos existentes (DNI con puntos, organización sin asignar).',
        "simbolos": {
            "seed_initial_data": (
                '💡 LA IDEA: Es el kit de inauguración del estacionamiento: cuando la base de datos se crea vacía, planta automáticamente los usuarios administradores, las sucursales iniciales y las tarifas por hora básicas.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra horas de configuración inicial permitiendo que el sistema esté listo para usarse y probarse inmediatamente después de la instalación.\n\n'
                "⚙️ FUNCIONAMIENTO: Recibe una sesión de SQLAlchemy y carga en orden los datos base, asociando todo a la organización principal (la busca por es_principal y la crea con nombre 'AUTOPASS' si no existe): primero los usuarios de INITIAL_USERS (hasheando la contraseña con bcrypt, y si el usuario ya existía le quita los puntos al DNI y le asigna la organización si le faltaba), luego el aforo global (sucursal None) con 20 plazas, después las tarifas de DEFAULT_PRICES como filas de Settings globales, las promociones de INITIAL_PROMOS solo si la tabla está vacía, y la red inicial de 4 sucursales solo si no hay ninguna. Termina con un único db.commit() que persiste todo."
            ),
        },
    },
    "core/time.py": {
        "proposito": 'Define los dos puntos de tiempo del sistema: uno para lo criptográfico (UTC real) y otro para los datos de negocio (hora local virtual manipulable con el reloj de pruebas), para que cada uso elija el correcto.',
        "simbolos": {
            "utcnow": (
                '💡 LA IDEA: Es el reloj atómico internacional de Greenwich: da la hora estándar del planeta sin importar en qué país o huso horario esté la computadora.\n\n'
                '🎯 POR QUE FUE GENERADA: Se utiliza exclusivamente para la fecha de expiración de los pases JWT, ya que los estándares mundiales de criptografía exigen evaluar el tiempo en UTC neutro.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve la hora actual en UTC pero como datetime naive (sin zona horaria), obtenida con datetime.now(timezone.utc).replace(tzinfo=None). Su uso está reservado a la expiración de los tokens JWT, porque python-jose valida el campo 'exp' contra UTC."
            ),
            "localnow": (
                '💡 LA IDEA: Es el reloj de pared de la sucursal, pero con un botón mágico de prueba: permite adelantar o atrasar el tiempo virtualmente para comprobar cómo reacciona el sistema ante estadías de 3 días o reservas vencidas.\n\n'
                '🎯 POR QUE FUE GENERADA: Es fundamental para hacer pruebas de cobro y vencimiento de reservas sin tener que esperar horas de tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la hora local virtual de AUTOPASS llamando a TimeService.now() (importado en el momento para evitar ciclos), que combina la hora real con el offset del reloj virtual y por eso sigue siendo manipulable en pruebas. Es el que hay que usar para los timestamps de datos de negocio (tickets, mensajes, notificaciones, sesiones) para que coincidan con la hora local que muestra el frontend.'
            ),
        },
    },
}
