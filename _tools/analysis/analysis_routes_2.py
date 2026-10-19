"""Explicaciones analizadas de rutas (parte 2: auth + parking + reports + system)."""

ANALISIS: dict[str, dict] = {
    "routes/auth.py": {
        "proposito": 'Router FastAPI con prefijo /v1/auth que concentra todo el ciclo de identidad del usuario: registro, recuperación/restablecimiento de contraseña, login con detección de dispositivos nuevos y logout, más el flujo completo de inicio de sesión social (OAuth). Delega la lógica real en UserService, EmailService, oauth_service y los repositorios de usuario/sesión.',
        "simbolos": {
            "_oauth_redirect": (
                '💡 LA IDEA: Es el puente invisible que envía al usuario de regreso a la aplicación después de identificarse con Google o GitHub, escondiendo las claves en el enlace para que nadie las espíe.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que datos confidenciales o tokens de acceso queden grabados en el historial de navegación o en los registros de acceso del servidor web.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper privado que arma una RedirectResponse 303 hacia la raíz del frontend colocando los parámetros en el fragmento de la URL (#clave=valor), de modo que credenciales como el token OAuth viajen fuera del servidor y no queden registradas en logs. Codifica cada valor con urllib.parse.quote y omite los que son None.'
            ),
            "_login_payload": (
                '💡 LA IDEA: Es el pase de acceso digital que se le entrega al usuario apenas demuestra su identidad, conteniendo su credencial JWT y los datos básicos de su perfil.\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica el formato de respuesta de sesión para que el login tradicional con contraseña y el login social reciban exactamente la misma estructura.\n\n'
                "⚙️ FUNCIONAMIENTO: Helper privado que genera un token JWT de acceso (create_access_token con 'sub'=email y 'rol', expiración según ACCESS_TOKEN_EXPIRE_MINUTES) y devuelve el diccionario estándar de sesión: access_token, token_type, rol, nombre, apellido, sucursal y nuevo_dispositivo. Lo reutilizan el login normal y el callback OAuth."
            ),
            "register": (
                '💡 LA IDEA: Es el mostrador de bienvenida para crear una cuenta nueva ingresando nombre, correo, documento y contraseña.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que nuevos conductores se registren en la plataforma, impidiendo que existan dos cuentas con el mismo correo o DNI.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/auth/register (límite 10/minuto). Recibe el cuerpo schemas.UserCreate con los datos del nuevo usuario y crea la cuenta llamando a UserService.create_user con rol USER. Devuelve {status:ok} o lanza 400 si el correo o DNI ya existen (IntegrityError) y 500 ante error interno.'
            ),
            "forgot_password": (
                '💡 LA IDEA: Es el botón de auxilio para quien olvidó su clave, enviándole un enlace seguro a su casilla de correo para restablecerla.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita bloquear a usuarios distraídos y responde siempre el mismo mensaje neutral para no revelar si un correo electrónico está registrado o no en el sistema.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint POST /v1/auth/forgot-password (límite 5/minuto). Recibe schemas.auth.ForgotPasswordRequest; busca el usuario activo por email normalizado y, si existe, genera un JWT con propósito 'recovery', arma la URL de reset y envía el correo con EmailService.send_recovery_email. Por seguridad responde siempre el mismo mensaje, exista o no la cuenta."
            ),
            "reset_password": (
                '💡 LA IDEA: Es el formulario final donde el usuario ingresa su nueva contraseña tras hacer clic en el enlace recibido por correo.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida que el enlace no haya vencido ni sido adulterado, cifrando la nueva clave en la base de datos de forma irreversible.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint POST /v1/auth/reset-password (límite 10/minuto). Decodifica el JWT recibido con jose, valida que el propósito sea 'recovery' o 'activation' y busca el usuario; si todo es válido actualiza password_hash con get_password_hash y hace commit. En invitaciones (purpose='activation') además envía el correo de confirmación de registro. Lanza 400 si el token es inválido/expirado y 404 si no encuentra al usuario."
            ),
            "login": (
                '💡 LA IDEA: Es la puerta de entrada principal donde el usuario ingresa su usuario y contraseña para comenzar a operar.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la identidad del usuario, genera su credencial de sesión segura y detecta si se está conectando desde un teléfono o computadora nunca antes vistos para alertarlo.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/auth/login (límite 15/minuto). Normaliza el email, autentica con authenticate_user y, si las credenciales son inválidas, lanza 401. Si el cliente envía device_id, registra/actualiza la UserSession del dispositivo (absorbiendo la sesión reciente del mismo user-agent para no contar el mismo navegador) y, cuando es un dispositivo nuevo y hay otros activos, crea una notificación NEW_DEVICE_LOGIN y marca nuevo_dispositivo=True. Devuelve el token JWT y los datos de sesión.'
            ),
            "logout": (
                '💡 LA IDEA: Es la despedida formal que destruye el pase de acceso y desconecta el dispositivo para que nadie más pueda usarlo.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza la seguridad en computadoras públicas o compartidas, invalidando el token JWT para que no pueda reutilizarse.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/auth/logout (límite 30/minuto). Requiere token Bearer y usuario autenticado; revoca el token (revoke_token sobre su jti) y, si el cuerpo trae device_id, elimina esa UserSession del usuario. Devuelve {status:ok} y nunca falla aunque el borrado de sesión falle.'
            ),
            "oauth_providers": (
                '💡 LA IDEA: Es el escaparate que muestra qué redes sociales están activadas para iniciar sesión (por ejemplo, Google o GitHub).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a la interfaz dibujar únicamente los botones de inicio social que están realmente configurados y listos para funcionar.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/auth/oauth/providers (límite 30/minuto). Devuelve la lista de proveedores de login social que tienen credenciales configuradas (oauth_service.enabled_providers) para que el frontend muestre solo los botones disponibles.'
            ),
            "oauth_authorize": (
                '💡 LA IDEA: Es el desvío hacia la pantalla oficial de Google o GitHub con un sello de seguridad antiengaño bajo el brazo.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la autenticación contra ataques de falsificación de petición (CSRF) asegurando que quien regresa sea quien inició el proceso.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/auth/oauth/{provider}/authorize (límite 10/minuto). Valida que el proveedor esté configurado (503 si no), firma un state anti-CSRF con oauth_service.sign_state y responde con un redirect 302 a la URL de autorización del proveedor.'
            ),
            "oauth_callback": (
                '💡 LA IDEA: Es la recepción del usuario cuando regresa de identificarse en Google o GitHub con su comprobante de identidad.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida el código entregado por la red social, loguea automáticamente a usuarios existentes o solicita los datos faltantes a usuarios nuevos.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/auth/oauth/{provider}/callback (límite 10/minuto). Recibe code/state/error del proveedor; si hay error, state inválido o falta code redirige al frontend con oauth_error. Intercambia el código por un token, obtiene los datos del usuario: si la cuenta existe la loguea (409 si está bloqueada) y si no, emite un código de alta social (oauth_signup) para completar el registro.'
            ),
            "oauth_complete": (
                '💡 LA IDEA: Es el paso final del registro social donde un usuario nuevo que vino de Google completa su DNI y teléfono.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite vincular cuentas de redes sociales con los requisitos legales y operativos necesarios para registrar vehículos y facturar.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/auth/oauth/complete (límite 10/minuto). Recibe schemas.auth.OAuthComplete (código de alta, DNI y teléfono), completa el registro social con oauth_service.complete_oauth_signup y devuelve directamente el payload de login (_login_payload) ya autenticado.'
            ),
        },
    },
    "routes/parking/__init__.py": {
        "proposito": (
            "💡 LA IDEA: Es la 'cabina de peaje y acceso' de la API. Conecta todas las entradas de autos, salidas, consultas de cocheras libres y validaciones de pases QR bajo una misma ventanilla de atención.\n\n"
            "🎯 POR QUE FUE GENERADA: Agrupa ordenadamente todas las operaciones vehiculares bajo el prefijo `/v1/` y la etiqueta 'Parking & Access', evitando tener endpoints dispersos y facilitando la documentación OpenAPI.\n\n"
            "⚙️ FUNCIONAMIENTO: Crea el router principal de estacionamiento, fusiona los subrouters de estado (`status`) y accesos (`access`), y reexporta funciones de normalización para que otros archivos puedan importarlas cómodamente."
        ),
        "simbolos": {
        },
    },
    "routes/parking/access.py": {
        "proposito": 'Subrouter FastAPI (sin prefijo propio; cuelga de /v1) que expone las operaciones de acceso al estacionamiento: validación de patente de entrada y salida, validación de pases QR y cobro de estadías. Los tres endpoints que ingieren lecturas de cámara exigen la dependencia require_alpr_node (solo nodos ALPR autorizados por secreto o red local) y delegan en AccessService/BillingService.',
        "simbolos": {
            "validate_plate": (
                '💡 LA IDEA: Es el ojo de la entrada: procesa la patente captada por la cámara en la barrera de ingreso y decide si el auto puede entrar.\n\n'
                '🎯 POR QUE FUE GENERADA: Automatiza el ingreso vehicular en segundos, validando aforo disponible o reservas previas y emitiendo la orden de levantar la barrera.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/access/validate-plate (límite 120/minuto, response_model AccessResponse). Recibe schemas.PlateValidation, exige require_alpr_node para descartar llamadas que no provengan de un nodo ALPR de confianza y delega en AccessService.validate_plate pasándole la request (para IP/contexto). Registra el ingreso de un vehículo por patente.'
            ),
            "exit_plate": (
                '💡 LA IDEA: Es el ojo de la salida: procesa la patente en la barrera de egreso para comprobar si pagó su estadía antes de dejarlo ir.\n\n'
                '🎯 POR QUE FUE GENERADA: Controla que ningún vehículo abandone el estacionamiento sin abonar el tiempo utilizado, agilizando el egreso de los que ya pagaron.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/access/exit-plate (límite 120/minuto, response_model AccessResponse). Recibe schemas.PlateValidation, valida el nodo ALPR con require_alpr_node y llama a AccessService.exit_plate. Procesa la salida de un vehículo detectado por patente.'
            ),
            "validate_qr": (
                '💡 LA IDEA: Es el lector de pases digitales para conductores que ingresan o salen mostrando un código QR desde la pantalla de su celular.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite acceder cómodamente a usuarios con autos alquilados, patentes deterioradas o pases especiales de cortesía.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/access/validate-qr (límite 60/minuto, response_model AccessResponse). Recibe schemas.QRValidation, exige require_alpr_node y delega en AccessService.validate_qr para validar un pase digital (QR) leído por la cámara.'
            ),
            "pay_stay": (
                '💡 LA IDEA: Es la ventanilla de cobro en garita donde el empleado cobra manualmente la estadía de un cliente antes de su salida.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita cobrar en efectivo o con tarjeta física a clientes que no abonan mediante la billetera virtual ni Mercado Pago.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/access/pay-stay (límite 10/minuto). Requiere personal operativo (get_operational_user) y recibe la patente por query y el método de pago (por defecto DIGITAL). Normaliza la patente y cobra con BillingService.process_payment; si el resultado no es ok lanza 400 con el mensaje, en caso contrario retorna el resultado.'
            ),
        },
    },
    "routes/parking/status.py": {
        "proposito": 'Subrouter de estado de ocupación de estacionamientos (sin prefijo propio; cuelga de /v1). Define OccupancyManager, el gestor en memoria de conexiones WebSocket agrupadas por sucursal que difunde cambios de aforo y eventos puntuales en tiempo real, e implementa el WebSocket de monitoreo más los endpoints REST públicos y operativos de disponibilidad de plazas.',
        "simbolos": {
            "OccupancyManager": (
                '💡 LA IDEA: Es la central de transmisiones en vivo que mantiene conectados los paneles del personal para avisarles al instante cada vez que entra o sale un auto.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite actualizar las pantallas del estacionamiento en tiempo real sin obligar al navegador a recargar la página todo el tiempo.\n\n'
                "⚙️ FUNCIONAMIENTO: Clase que administra los WebSockets activos del tablero de ocupación, agrupados por nombre de sucursal normalizado (el Admin Global usa la clave 'GLOBAL'). Mantiene el diccionario active_connections y ofrece conexión, desconexión, difusión del estado de aforo y difusión de eventos puntuales."
            ),
            "__init__": (
                '💡 LA IDEA: Es la libreta en blanco donde la central anota las conexiones activas divididas por cada sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Prepara la memoria del servidor para clasificar a qué pantalla enviarle la información correspondiente a cada sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Constructor de OccupancyManager: inicializa active_connections como diccionario vacío sucursal->lista de WebSockets.'
            ),
            "connect": (
                '💡 LA IDEA: Es el enganche de un nuevo navegador al canal de televisión en vivo del estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Registra la pantalla del operador bajo su sucursal correspondiente para empezar a mandarle actualizaciones al instante.\n\n'
                "⚙️ FUNCIONAMIENTO: Método asíncrono que acepta el WebSocket, determina la clave de agrupación (nombre de sucursal normalizado, o 'GLOBAL' si el usuario es ADMIN), registra la conexión en active_connections y devuelve la clave de sucursal usada."
            ),
            "disconnect": (
                '💡 LA IDEA: Es la baja de la lista de conexiones cuando un usuario cierra la pestaña o pierde la señal de internet.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita saturar la memoria del servidor intentando enviar datos a pantallas que ya no están abiertas.\n\n'
                '⚙️ FUNCIONAMIENTO: Método que quita el WebSocket de la lista de conexiones de la sucursal indicada, ignorando silenciosamente si ya no estaba presente.'
            ),
            "broadcast_update": (
                '💡 LA IDEA: Es el mensaje por altavoz a todas las pantallas informando el nuevo recuento de autos y lugares libres.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene a todo el equipo sincronizado con los datos de aforo actualizados en milisegundos tras cada movimiento.\n\n'
                "⚙️ FUNCIONAMIENTO: Método asíncrono que envía el estado actual de aforo a todos los interesados. Si recibe una sucursal concreta difunde a esa y a GLOBAL; si no, solo a GLOBAL. Con force_refresh invalida la caché 'occupancy_' para recalcular; si no, reutiliza los payloads cacheados hasta 3s. Crea su propia sesión de DB si no se le pasa una y limpia del registro las conexiones que fallen al enviar."
            ),
            "broadcast_event": (
                "💡 LA IDEA: Es una alerta rápida por pantalla (como 'auto esperando en la barrera') que no modifica los números de capacidad.\n\n"
                '🎯 POR QUE FUE GENERADA: Notifica incidentes o estados momentáneos sin obligar a recalcular toda la matemática de plazas del predio.\n\n'
                '⚙️ FUNCIONAMIENTO: Método asíncrono que envía un evento puntual (por ejemplo PENDING_EXIT) a los sockets de la sucursal y al Admin Global sin recalcular aforo: manda el payload tal cual y da de baja las conexiones que fallen.'
            ),
            "_get_global_status": (
                '💡 LA IDEA: Es la foto panorámica de todas las sucursales al mismo tiempo pensada para el director general de la empresa.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a la gerencia monitorear la ocupación completa de la red aprovechando una memoria caché para no colapsar la base de datos.\n\n'
                "⚙️ FUNCIONAMIENTO: Método privado que arma el payload {type:GLOBAL_UPDATE, branches:[...]} con ocupación y capacidad (incluidas reservas por tipo de vehículo) de todas las sucursales activas, consultando OccupancyService. Cachea el resultado en ttl_cache 3 segundos bajo la clave 'occupancy_ws_global'."
            ),
            "_get_branch_status": (
                '💡 LA IDEA: Es la foto detallada de un estacionamiento puntual con sus plazas por tipo de vehículo y el último suceso registrado.\n\n'
                '🎯 POR QUE FUE GENERADA: Genera el paquete exacto de datos que necesita el operador de garita para controlar su piso de trabajo en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Método privado que arma el payload {type:BRANCH_UPDATE, data:{...}} para una sucursal normalizada. Busca la sucursal por nombre normalizado; si existe usa calculate_branch_capacities, si no cae al aforo legacy (aforo_by_normalized_name) y, en última instancia, a default_capacities. Agrega siempre last_event de NotificationService y cachea 3 segundos por sucursal.'
            ),
            "occupancy_websocket_endpoint": (
                '💡 LA IDEA: Es la tubería digital abierta que conecta al panel de control con el servidor para recibir novedades instantáneas.\n\n'
                '🎯 POR QUE FUE GENERADA: Habilita la comunicación bidireccional inmediata, verificando antes los permisos de seguridad del empleado conectado.\n\n'
                '⚙️ FUNCIONAMIENTO: WebSocket /v1/parking/ws. Exige token por query, decodifica el JWT, carga el usuario y rechaza (código 4008) si no existe o está bloqueado o (4003) si no es rol operativo. Conecta al OccupancyManager, registra el event loop para permitir notificaciones desde hilos y envía el primer estado de inmediato; mantiene el socket vivo hasta que el cliente se desconecta.'
            ),
            "list_public_branches": (
                '💡 LA IDEA: Es el mapa interactivo abierto al público donde cualquier conductor puede ver qué sucursales están abiertas y con lugares libres.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a los conductores a elegir a qué estacionamiento dirigirse sin requerir que inicien sesión previamente.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint GET /v1/parking/branches (response_model List[BranchPublicResponse]). Devuelve las sucursales activas con ubicación y su ocupación real (por tipo de vehículo y reservas) más los pisos, para el mapa público, sin requerir autenticación. Cachea el resultado en ttl_cache 3 segundos bajo 'occupancy_public_branches'."
            ),
            "get_parking_status": (
                '💡 LA IDEA: Es la consulta tradicional de capacidades y lugares disponibles que hace el panel de control al cargar la página.\n\n'
                '🎯 POR QUE FUE GENERADA: Entrega la situación inicial del predio a la interfaz antes de que se encienda la transmisión continua por WebSocket.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/parking/status (response_model ParkingStatus). Requiere personal operativo. Aísla por sede: un usuario no-global usa su sucursal; un Admin Global consulta por organización (organization_id). Busca la sucursal, y si la encuentra devuelve sus capacidades; si no, cae a default_capacities o al aforo legacy de la sucursal.'
            ),
            "current_occupancy": (
                '💡 LA IDEA: Es la lista de autos actualmente estacionados dentro del predio con el reloj corriendo y la cuenta a pagar acumulada.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga al cajero y operador visibilidad total sobre qué patentes están adentro y cuánto debe abonar cada una en ese instante.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/parking/current-occupancy. Requiere personal operativo y lista los vehículos estacionados en la sede del usuario con la deuda calculada, delegando en OccupancyService.current_occupancy (Admin Global consulta por organización).'
            ),
        },
    },
    "routes/parking/utils.py": {
        "proposito": (
            "💡 LA IDEA: Es el 'puente de compatibilidad de limpieza de datos'. Si alguna parte del sistema busca las herramientas para limpiar patentes y DNI en la carpeta vieja de estacionamiento, este archivo la redirige inmediatamente a la fábrica oficial en `core.normalize`.\n\n"
            "🎯 POR QUE FUE GENERADA: Garantiza retrocompatibilidad total: cuando se refactorizó el código y se movieron las funciones de normalización al núcleo del sistema, este archivo se dejó como puente para que ningún archivo viejo se rompa al importar.\n\n"
            "⚙️ FUNCIONAMIENTO: Reexporta sin alterar desde `core.normalize` las funciones: `normalize_plate`, `format_plate`, `normalize_dni`, `normalize_name`, `normalize_user_name` y `normalize_branch_name`."
        ),
        "simbolos": {
        },
    },
    "routes/reports.py": {
        "proposito": "Router FastAPI con prefijo /v1/reports y tag 'Reports & Analytics'. Expone de forma delgada los reportes de recaudación, historial de pagos, logs ALPR y métricas (actividad, mapa de calor, ocupación y tiempos OCR), limitándose a validar dependencias (rol operativo o de gestión) y delegar todo el cálculo en ReportService.",
        "simbolos": {
            "get_financial_summary": (
                '💡 LA IDEA: Es el resumen contable del día, mes o año que muestra el total recaudado discriminado por tipo de pago y tipo de vehículo.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona a los administradores métricas claras de facturación para balances contables y toma de decisiones comerciales.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/reports/financial-summary. Requiere personal operativo y acepta filtros period, start, end, vehicle_type, payment_method y sucursal. Delega en ReportService.get_financial_summary para calcular el resumen de recaudación unificado.'
            ),
            "get_payment_history": (
                '💡 LA IDEA: Es el libro diario de cobros donde figura cada ticket abonado con su fecha, patente, importe y sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite auditar cobros individuales, conciliar cuentas bancarias y rastrear pagos ante reclamos de clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/reports/payment-history. Requiere rol de gestión (get_local_manager) y acepta los mismos filtros más paginación (page, limit). Delega en ReportService.get_payment_history para listar las transacciones.'
            ),
            "get_reports_access": (
                '💡 LA IDEA: Es la bitácora de entradas y salidas que guarda qué auto pasó por qué barrera y a qué hora exacta.\n\n'
                '🎯 POR QUE FUE GENERADA: Esencial para resolver disputas por horarios de estadía, extravío de vehículos o controles de seguridad en las instalaciones.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/reports/access. Requiere personal operativo; acepta filtro opcional patente y limit validado entre 1 y 1000 (por defecto 300). Delega en ReportService.get_access_logs para consultar el historial de eventos ALPR.'
            ),
            "get_ocr_stats": (
                '💡 LA IDEA: Es el velocímetro del sistema de cámaras que mide qué tan rápido lee las patentes y con qué tasa de éxito.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite evaluar el rendimiento técnico de la inteligencia artificial e identificar cámaras que anden lentas o descalibradas.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/reports/ocr-stats. Requiere personal operativo y recibe limit (por defecto 100). Delega en ReportService.get_ocr_stats para obtener estadísticas de tiempos de procesamiento OCR.'
            ),
            "get_metrics_access_activity": (
                '💡 LA IDEA: Es el gráfico de flujo vehicular hora por hora que muestra las horas pico de ingresos y salidas en el estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a planificar turnos de personal y prever horarios de máxima afluencia de clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/reports/metrics/access-activity. Requiere rol de gestión y acepta rango opcional desde/hasta. Delega en ReportService.get_access_activity para construir la serie temporal horaria de accesos (entradas/salidas).'
            ),
            "get_metrics_traffic_heatmap": (
                '💡 LA IDEA: Es el mapa de calor mensual que pinta con colores qué días y horas de la semana se llena el estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite detectar patrones de conducta de los clientes a lo largo del mes para lanzar promociones en horarios de baja demanda.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/reports/metrics/traffic-heatmap. Requiere rol de gestión y acepta sucursal y rango desde/hasta. Delega en ReportService.get_traffic_heatmap para el mapa de calor diario (día del mes x hora) con totales por día y hora.'
            ),
            "get_metrics_occupancy_summary": (
                '💡 LA IDEA: Es la comparativa entre la cantidad de reservas tomadas y las plazas reales disponibles, incluyendo la tasa de clientes que no asistieron.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita el sobrecupo y mide la efectividad del sistema de reservas para optimizar la rentabilidad del predio.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/reports/metrics/occupancy-summary. Requiere rol de gestión y acepta sucursal y rango desde/hasta. Delega en ReportService.get_occupancy_summary para comparar ocupación de reservas vs capacidad por hora e incluir KPIs (con no-show).'
            ),
            "get_ocr_activity": (
                '💡 LA IDEA: Es el electroencefalograma en vivo del reconocimiento de patentes que muestra la evolución cronológica de cada lectura.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta los gráficos móviles del panel técnico para supervisar en directo la estabilidad de los nodos de video.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/reports/ocr-activity. Requiere personal operativo y delega en ReportService.get_ocr_activity para devolver la serie cronológica completa de tiempos OCR del gráfico móvil.'
            ),
        },
    },
    "routes/system/__init__.py": {
        "proposito": (
            "💡 LA IDEA: Es el 'panel de monitoreo y sala de máquinas' del backend. Agrupa las rutas que vigilan la salud del servidor, el estado de las cámaras y la transmisión de video en vivo.\n\n"
            "🎯 POR QUE FUE GENERADA: Separa las operaciones técnicas de infraestructura (cámaras, streaming, salud del sistema) de la lógica comercial de reservas y pagos.\n\n"
            "⚙️ FUNCIONAMIENTO: Crea el router montado bajo `/v1/system`, agrupa los subrouters de salud (`health`), cámaras (`cameras`) y video (`video`), y expone la función `stop_all_cameras()` para apagar de forma segura todas las cámaras al detener el servidor."
        ),
        "simbolos": {
        },
    },
    "routes/system/cameras.py": {
        "proposito": 'Router de gestión de cámaras ALPR del sistema. Permite consultar y guardar la configuración de una cámara, arrancar/detener los subprocesos alpr_service.py, administrar el CRUD de cámaras y su orden, y notificar lecturas en curso. Todos los endpoints exigen personal operativo y aplican aislamiento multiempresa (organización) y por sucursal.',
        "simbolos": {
            "_schedule_async": (
                '💡 LA IDEA: Es el cartero que lleva un encargo urgente desde un proceso secundario hacia el motor principal del servidor para que se envíe sin demora.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que tareas que corren en hilos aislados puedan emitir avisos en tiempo real por WebSockets sin provocar fallas de concurrencia.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper privado que programa una coroutine sobre el event loop principal de uvicorn (guardado en NotificationService._loop) usando asyncio.run_coroutine_threadsafe, para poder difundir desde hilos secundarios. Devuelve True si lo logró y False si no hay loop disponible.'
            ),
            "_stream_console_output": (
                '💡 LA IDEA: Es el micrófono espía que escucha todo lo que escribe el programa de la cámara en su terminal y lo manda a la pantalla del administrador.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite diagnosticar fallas de video o ver el proceso de reconocimiento de patentes en vivo directamente desde el navegador web.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper privado que corre en un hilo: lee línea por línea el stdout del subproceso ALPR, las decodifica y reenvía al frontend por el WebSocket de video de la cámara mediante video_manager.broadcast_console. Es una ruta paralela aditiva que no toca los frames ni los eventos; al terminar cierra y libera stdout.'
            ),
            "_enforce_camera_org": (
                '💡 LA IDEA: Es el control de pertenencia que asegura que un empleado solo pueda ver o tocar cámaras de los estacionamientos de su empresa.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que operadores de una empresa espíen el streaming o desactiven cámaras pertenecientes a otra compañía.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper privado que aplica el aislamiento multiempresa sobre una cámara: llama a enforce_organization_scope comparando la organización del staff con la de la sucursal de la cámara, lanzando 403 si pertenecen a organizaciones distintas.'
            ),
            "get_camera_config": (
                '💡 LA IDEA: Es la ficha técnica de una barrera que indica qué cámara web o enlace de video tiene asignado y si está encendida.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al operador consultar la configuración actual de un punto de acceso antes de cambiarla o reiniciar el servicio.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint GET /v1/system/camera-config/{gate_id}. Requiere personal operativo; valida que un usuario no-admin solo consulte su propia sede (por prefijo de la sucursal en el gate_id, 403 si no). Lee el ajuste CAMERA_SOURCE_<gate_id> (por defecto '0') e informa si el proceso está en ejecución."
            ),
            "set_camera_config": (
                '💡 LA IDEA: Es el selector de canal donde se define la dirección de video (cámara 0, RTSP o video de prueba) para una barrera determinada.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita configurar qué cámara apunta a cada entrada o salida sin tener que modificar archivos de configuración en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/system/camera-config. Requiere personal operativo y recibe CameraConfig (gate_id y source); verifica que un no-admin solo configure su sede. Crea o actualiza el ajuste CAMERA_SOURCE_<gate_id> con la fuente de video y confirma la operación.'
            ),
            "control_camera_service": (
                '💡 LA IDEA: Es el interruptor de encendido y apagado del motor de reconocimiento automático de patentes para una barrera concreta.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite arrancar el proceso de visión artificial cuando abre el estacionamiento o detenerlo ante mantenimientos de hardware.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/system/camera-service/{gate_id}/{action}. Requiere personal operativo y valida el acceso por sede. Con action=start lee la fuente del ajuste, arma el entorno (GATE_ID, VIDEO_SOURCE, GATE_TYPE entrada/salida/qr, BACKEND_URL local, PYTHONUNBUFFERED) y lanza alpr_service.py como subproceso registrándolo en CAMERA_PROCESSES con un hilo que reenvía su consola. Con action=stop mata el proceso (taskkill en Windows) y lo elimina del registro. Acción distinta devuelve error.'
            ),
            "get_cameras": (
                '💡 LA IDEA: Es la lista completa de todas las cámaras instaladas en las sucursales con su estado de funcionamiento en tiempo real.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda una vista unificada de todo el parque de cámaras para detectar al instante cualquier equipo fuera de línea.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/system/cameras (response_model List[CameraResponse]). Requiere personal operativo y lista las cámaras aplicando alcance: el Admin Global ve solo las de sedes de su organización y el resto solo las de su propia sucursal. Calcula para cada cámara su identificador de proceso y si está corriendo.'
            ),
            "create_camera": (
                '💡 LA IDEA: Es el formulario de instalación digital para registrar una nueva cámara indicando su tipo (entrada, salida o QR) y sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite sumar puntos de control vehicular a la red de estacionamientos de forma ordenada y asignándoles su identificador.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/system/cameras (response_model CameraResponse). Requiere personal operativo; la sucursal se toma del staff salvo para Admin Global, que la indica en el body. Resuelve el branch_id por nombre/organización (403 si el admin no tiene acceso a esa sede), crea el ParkingCamera y lo guarda. Devuelve la cámara creada con is_running=False.'
            ),
            "reorder_cameras": (
                '💡 LA IDEA: Es la cuadrícula para ordenar visualmente cómo aparecen las cámaras en la pantalla de monitoreo.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita a los guardias colocar primero las cámaras de las entradas principales para vigilarlas con mayor comodidad.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint PUT /v1/system/cameras/order. Requiere personal operativo, recibe CameraOrderUpdate con la lista de ids y asigna el campo orden secuencial (1..N). Por cada cámara valida pertenencia a la organización y, para no-admin, a su sucursal; lanza 404 si alguna no existe y 403 si no tiene permiso.'
            ),
            "update_camera": (
                '💡 LA IDEA: Es la herramienta de edición para cambiarle el nombre, la fuente de video o la función a una cámara ya instalada.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite actualizar configuraciones cuando se reemplaza una cámara dañada o se cambia su posición física sin perder su historial.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint PUT /v1/system/cameras/{camera_id} (response_model CameraResponse). Requiere personal operativo, busca la cámara (404 si no existe), valida organización y sucursal, y actualiza nombre, tipo, source y activa (el campo sucursal solo lo puede cambiar un Admin). Devuelve la cámara actualizada con su estado de ejecución.'
            ),
            "delete_camera": (
                '💡 LA IDEA: Es la orden de desinstalación que apaga el proceso de reconocimiento y borra la cámara del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Limpia cámaras dadas de baja, asegurándose de matar sus procesos en ejecución para no dejar recursos consumiendo memoria en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint DELETE /v1/system/cameras/{camera_id}. Requiere personal operativo, busca la cámara (404), valida permisos y, si su proceso ALPR está activo, lo mata y lo quita de CAMERA_PROCESSES. Luego elimina la cámara de la base de datos y confirma.'
            ),
            "control_dynamic_camera_service": (
                '💡 LA IDEA: Es el botón de marcha/parada para cámaras gestionadas dinámicamente desde el panel web según su identificador en base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Simplifica el control operativo diario de cámaras creadas por los usuarios desde la interfaz visual sin depender de claves fijas.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/system/cameras/{camera_id}/control/{action}. Requiere personal operativo, busca y autoriza la cámara y calcula su proc_id. Con action=start arranca alpr_service.py con entorno derivado del tipo de cámara (qr/salida/entrada) y registra el hilo de consola; con action=stop detiene y desregistra el proceso. Acción inválida u otros errores se informan en el resultado.'
            ),
            "notify_camera_reading": (
                "💡 LA IDEA: Es el cartel titilante de 'ANALIZANDO VEHICULO...' que se enciende en pantalla apenas una cámara detecta un auto acercándose.\n\n"
                '🎯 POR QUE FUE GENERADA: Informa de inmediato al operador de garita que el sistema está trabajando en la lectura de la patente, brindando retroalimentación visual en vivo.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint POST /v1/system/camera-reading/{gate_id} protegido con require_alpr_node. Deducido el gate_id, intenta resolver a qué sucursal pertenece buscando por nombre normalizado y registra en NotificationService.set_last_event el estado 'READING' (LEYENDO PATENTE...). Solo nodos ALPR autorizados pueden invocarlo, evitando spoofing del estado operativo."
            ),
        },
    },
    "routes/system/common.py": {
        "proposito": 'Módulo compartido del paquete system: define el estado global de procesos ALPR (CAMERA_PROCESSES y ALPR_HEARTBEATS), el modelo CameraConfig, helpers de sucursal y el ConnectionManager de WebSockets de video por sucursal, para que cameras.py, health.py y video.py reutilicen estos elementos sin duplicarlos.',
        "simbolos": {
            "CameraConfig": (
                '💡 LA IDEA: Es la plantilla formal que empaqueta el identificador de la barrera y la dirección de origen de su cámara para transmitirlos de forma segura.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida que los datos recibidos para configurar una cámara cumplan con los formatos esperados antes de guardarlos.\n\n'
                '⚙️ FUNCIONAMIENTO: Modelo Pydantic con los campos gate_id y source, usado como cuerpo de los endpoints que guardan la configuración de una cámara ALPR.'
            ),
            "stop_all_cameras": (
                '💡 LA IDEA: Es el disyuntor general de emergencia que apaga todos los subprocesos de lectura de cámaras de un solo golpe al apagar el servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que queden programas huérfanos consumiendo CPU y memoria en Windows cuando se reinicia el sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper que detiene todos los servicios ALPR registrados en CAMERA_PROCESSES al apagar el servidor: mata cada proceso vivo (taskkill en Windows), registra la parada y finalmente vacía el diccionario.'
            ),
            "misma_sucursal": (
                '💡 LA IDEA: Es la verificación de compatibilidad geográfica que confirma si un operador y una cámara pertenecen al mismo predio.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el personal solo pueda controlar o visualizar las cámaras del establecimiento en el que está trabajando.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper que compara si una cámara y un operador son de la misma sede. Si ambos tienen sucursal_id lo compara directamente; si no, cae al fallback legacy comparando el nombre de sucursal normalizado.'
            ),
            "ConnectionManager": (
                '💡 LA IDEA: Es el distribuidor de video que reparte la imagen de cada cámara entre todos los operadores que la están mirando en ese instante.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la transmisión de streaming, optimiza el consumo de red y guarda la última foto para el próximo que se conecte.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase que gestiona los WebSockets de espectadores del streaming de video, agrupados por camera_id, y guarda el último frame recibido de cada cámara para reenviarlo a quien se conecte después.'
            ),
            "__init__": (
                '💡 LA IDEA: Es el archivador vacío donde el distribuidor organiza los espectadores de cada cámara y las últimas capturas recibidas.\n\n'
                '🎯 POR QUE FUE GENERADA: Prepara las estructuras de memoria necesarias para que el sistema de video funcione sin confusiones entre cámaras distintas.\n\n'
                '⚙️ FUNCIONAMIENTO: Constructor de ConnectionManager: inicializa active_connections (camera_id -> lista de WebSockets) y last_frames (camera_id -> último frame en base64).'
            ),
            "connect": (
                '💡 LA IDEA: Es el portero que autoriza la entrada de un espectador a la sala de video de una cámara y le entrega la última foto disponible.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el usuario tenga permiso para ver esa sede y le muestra la imagen de inmediato sin esperar al siguiente cuadro.\n\n'
                '⚙️ FUNCIONAMIENTO: Método asíncrono que valida permisos antes de aceptar al espectador: un usuario no-admin solo puede ver cámaras cuyo prefijo de sucursal coincida con la suya (si no, cierra con 4003 y devuelve False). Acepta el WebSocket, lo registra y, si hay un último frame guardado, se lo envía de inmediato.'
            ),
            "disconnect": (
                '💡 LA IDEA: Es el aviso de salida de un usuario que apagó el visor de video de una cámara.\n\n'
                '🎯 POR QUE FUE GENERADA: Da de baja al espectador para no desperdiciar ancho de banda enviando imágenes a una pantalla inactiva.\n\n'
                '⚙️ FUNCIONAMIENTO: Método que desregistra un WebSocket de la cámara indicada, ignorando silenciosamente si ya no estaba.'
            ),
            "broadcast_frame": (
                '💡 LA IDEA: Es el proyector de cine que reparte la foto actual a todos los espectadores conectados a esa cámara simultáneamente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que múltiples operadores vean el video en vivo al mismo tiempo sin saturar la cámara original.\n\n'
                '⚙️ FUNCIONAMIENTO: Método asíncrono que actualiza last_frames con el nuevo frame base64 y lo envía a todos los espectadores de esa cámara, dando de baja las conexiones que fallen.'
            ),
            "broadcast_console": (
                '💡 LA IDEA: Es el teletipo que transmite los mensajes técnicos de la cámara a las pantallas autorizadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita a los técnicos ver lo que la cámara está pensando o detectando en texto plano mientras observan la imagen.\n\n'
                '⚙️ FUNCIONAMIENTO: Método asíncrono que reenvía una línea de consola del subproceso ALPR a los espectadores de la cámara como JSON con la marca __console__ (para distinguirla del frame base64), dando de baja las conexiones que fallen.'
            ),
        },
    },
    "routes/system/health.py": {
        "proposito": 'Router de salud y mantenimiento del sistema (montado bajo /v1/system). Expone el diagnóstico de base de datos/API y estado de nodos ALPR, el latido que envían esos nodos, el reseteo global de datos y la hora virtual pública usada por el frontend.',
        "simbolos": {
            "get_health": (
                '💡 LA IDEA: Es el chequeo médico completo del sistema que verifica que la base de datos responda y que todas las cámaras estén vivas y conectadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los técnicos y administradores comprobar en un segundo si toda la plataforma está operativa o si algún componente falló.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/system/health. Requiere personal operativo; verifica la base de datos con SELECT 1 y calcula el estado de cada nodo ALPR comparando ALPR_HEARTBEATS (ONLINE si el latido es de hace menos de 90s). Para Admin Global muestra todos los gates; para el resto, solo las cámaras de su sucursal (o los gates <sede>_ENTRADA/SALIDA como fallback).'
            ),
            "alpr_heartbeat": (
                "💡 LA IDEA: Es el pulso cardíaco periódico que cada cámara envía cada pocos segundos al servidor para avisar 'estoy encendida y trabajando'.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite detectar cámaras desconectadas o colgadas si dejan de enviar su pulso durante más de un minuto y medio.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/system/heartbeat protegido con require_alpr_node. Normaliza el gate_id y registra en ALPR_HEARTBEATS la marca de tiempo actual, permitiendo que /health sepa qué nodos ALPR están vivos. La protección evita que clientes arbitrarios falseen nodos ONLINE.'
            ),
            "reset_system": (
                '💡 LA IDEA: Es el botón de reseteo a valores de fábrica exclusivo para pruebas escolares que borra todos los vehículos, cobros y fotos del servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite limpiar la base de datos y reiniciar el estacionamiento desde cero para comenzar una nueva demostración práctica.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/system/reset (límite 5/minuto). Requiere super admin (get_super_admin); borra todos los datos con SystemRepository.reset_all_data y elimina los archivos del directorio de imágenes (settings.IMAGE_DIR), devolviendo {status:ok}.'
            ),
            "get_virtual_time_public": (
                '💡 LA IDEA: Es el reloj público que anuncia a la interfaz qué hora virtual está corriendo en el simulador sin requerir contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que las pantallas de demostración sincronicen sus relojes y muestren la hora de simulación adecuada a los usuarios.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/system/virtual-time. Sin autenticación, devuelve TimeService.get_info() con la información de la hora virtual del entorno de prueba para que el frontend la sincronice.'
            ),
        },
    },
    "routes/system/video.py": {
        "proposito": 'Router de video del sistema (bajo /v1/system). Implementa el canal WebSocket por el que los nodos ALPR suben frames y los espectadores los ven en vivo, un endpoint HTTP equivalente, el fallback MJPEG y la entrega de imágenes capturadas de un log. Aplica autenticación por token de usuario o por confianza de nodo ALPR y aislamiento por sucursal.',
        "simbolos": {
            "websocket_video_endpoint": (
                '💡 LA IDEA: Es el túnel de alta velocidad por donde la cámara sube sus cuadros de video y los operadores los reciben en vivo en su navegador.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona transmisión de video fluida con bajísima latencia, validando credenciales de cámaras o permisos de los empleados.\n\n'
                '⚙️ FUNCIONAMIENTO: WebSocket /v1/system/ws/video/{camera_id}. Si llega token, resuelve el usuario; si es usuario, exige rol ADMIN/LOCAL_ADMIN/STAFF y lo conecta como espectador vía manager.connect (con validación de sucursal). Si no hay usuario, actúa como nodo ALPR: valida por node_secret o red trusted y, de ser válido, reenvía cada frame recibido a los espectadores con manager.broadcast_frame. Rechaza con 4403 si no pasa ninguna validación.'
            ),
            "update_frame_http": (
                '💡 LA IDEA: Es la puerta alternativa para que cámaras o nodos de video envíen imágenes individuales mediante peticiones web tradicionales.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite integrar cámaras sencillas o scripts que no soportan WebSockets pero necesitan mandar fotos para el monitoreo.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /v1/system/update-frame/{camera_id}. Solo acepta nodos ALPR autorizados (valida el peer y node_secret, 403 si no); si el cuerpo JSON trae el campo image, difunde el frame con manager.broadcast_frame y devuelve {status:ok}.'
            ),
            "video_feed_legacy": (
                '💡 LA IDEA: Es la transmisión de video clásica compatible con navegadores antiguos o pantallas simples que no soportan tecnologías modernas.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura compatibilidad hacia atrás emitiendo un flujo continuo de imágenes (MJPEG) que cualquier navegador puede reproducir.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/system/video-feed/{camera_id}. Requiere personal operativo; un no-admin solo accede a cámaras de su sucursal (403 si el prefijo no coincide). Devuelve un StreamingResponse MJPEG que en cada iteración decodifica el último frame base64 de la cámara y lo emite, con pausa de 0.1s.'
            ),
            "_user_from_token": (
                '💡 LA IDEA: Es el inspector de credenciales que lee el pase digital de un usuario antes de permitirle abrir un canal de video.\n\n'
                '🎯 POR QUE FUE GENERADA: Bloquea intentos de acceso no autorizados al streaming de las cámaras, verificando que el usuario tenga un rol habilitado.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper privado que resuelve el usuario autenticado a partir de un JWT: decodifica el token (401 si es inválido/expirado), busca el usuario activo (401 si no existe) y valida que tenga rol ADMIN/LOCAL_ADMIN/STAFF (403 si no).'
            ),
            "get_capture": (
                '💡 LA IDEA: Es el visor de fotos que entrega la captura fotográfica del auto guardada en el momento exacto en que ingresó o salió del predio.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite mostrar la foto probatoria de la patente en los reportes de acceso y auditorías ante cualquier reclamo o duda.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /v1/system/capture/{log_id}. Autentica aceptando el token por query (para etiquetas <img>) o por cabecera Bearer (401 si no hay ninguno). Busca el log de acceso (404 si no existe) y valida que un no-admin solo acceda a logs de su sucursal (403). Devuelve la imagen capturada si el archivo existe o el logo por defecto como fallback.'
            ),
        },
    },
}
