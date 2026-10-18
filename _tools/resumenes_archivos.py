# RESUMENES ESCUETOS EN MAYUSCULAS Y SIN ACENTOS PARA CADA ARCHIVO DE AUTOPASS
from __future__ import annotations
import re
import unicodedata

def _limpiar(texto: str) -> str:
    s = ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')
    return s.upper().replace('Ñ', 'N').strip()

MAPA_RESUMENES: dict[str, str] = {
    # ---- ARRANQUE Y ENTORNO ----
    "main.py": "ARRANQUE PRINCIPAL DE LA API Y RUTAS",
    "init_db.py": "CREACION DE TABLAS Y SEMILLAS DE BD",
    "alpr_service.py": "SERVICIO INDEPENDIENTE DE VISION Y CAMARAS",
    "locustfile.py": "PRUEBAS DE CARGA Y RENDIMIENTO",
    "alembic/env.py": "CONFIGURACION DE MIGRACIONES ONLINE Y OFFLINE",
    "run_server.bat": "LANZADOR DEL SERVIDOR EN WINDOWS",
    "static/offline.html": "PANTALLA OFFLINE DE CONTINGENCIA PWA",
    "static/test_plates.html": "PATENTES DE PRUEBA IMPRIMIBLES",

    # ---- CORE ----
    "core/__init__.py": "PAQUETE DE UTILIDADES DEL NUCLEO",
    "core/alpr_security.py": "SEGURIDAD DE CAMARA Y PATENTES",
    "core/cache.py": "CACHE TEMPORAL EN MEMORIA RAM",
    "core/config.py": "CONFIGURACION CENTRAL Y VARIABLES DE ENTORNO",
    "core/database.py": "CONEXION Y MOTOR DE BASE DE DATOS",
    "core/limiter.py": "CONTROL DE LIMITE DE PETICIONES",
    "core/logger.py": "REGISTRO DE EVENTOS Y LOGS EN DISCO",
    "core/mqtt.py": "CONTROL DE BARRERAS POR PROTOCOLO MQTT",
    "core/normalize.py": "NORMALIZACION DE TEXTOS Y PATENTES",
    "core/security.py": "ENCRIPTACION Y VALIDACION DE TOKENS JWT",
    "core/seed.py": "CARGA DE DATOS INICIALES DE PRUEBA",
    "core/time.py": "HORA DEL SISTEMA Y RELOJ VIRTUAL",

    # ---- ALPR ----
    "alpr/__init__.py": "PAQUETE DEL SERVICIO DE VISION",
    "alpr/config.py": "CONFIGURACION DE VISION Y PATENTES",
    "alpr/ocr_engine.py": "MOTOR DE LECTURA OCR Y DETECCION DE PATENTES",
    "alpr/preprocessor.py": "PREPROCESAMIENTO Y FILTRADO DE IMAGEN",
    "alpr/runner.py": "ORQUESTADOR DEL BUCLE DE CAMARAS",
    "alpr/video_streamer.py": "CAPTURA DE CUADROS DE VIDEO EN VIVO",
    "alpr/ws_client.py": "ENVIO DE VIDEO POR WEBSOCKET",

    # ---- MODELS ----
    "models/__init__.py": "PAQUETE DE MODELOS DE BASE DE DATOS",
    "models/branch_ref.py": "REFERENCIA RELACIONAL DE SUCURSALES",
    "models/enums.py": "ENUMERACIONES Y ESTADOS DEL SISTEMA",
    "models/mercadopago.py": "MODELO DE PAGOS MERCADO PAGO",
    "models/notification.py": "MODELO DE NOTIFICACIONES Y ALERTAS",
    "models/organization.py": "MODELO DE ORGANIZACIONES Y PLAYAS",
    "models/parking.py": "MODELO DE COCHERAS PISOS Y TARIFAS",
    "models/reservation.py": "MODELO DE RESERVAS Y CUPOS",
    "models/support.py": "MODELO DE TICKETS DE CONSULTA Y SOPORTE",
    "models/types.py": "TIPOS DE DATOS Y CONVERTIDORES SQL",
    "models/user.py": "MODELO DE USUARIOS Y ROLES DEL SISTEMA",
    "models/user_session.py": "MODELO DE SESIONES ACTIVAS DE USUARIO",

    # ---- SCHEMAS ----
    "schemas/__init__.py": "PAQUETE DE ESQUEMAS DE VALIDACION",
    "schemas/auth.py": "VALIDACION DE LOGIN Y REGISTRO",
    "schemas/mercadopago.py": "VALIDACION DE PAGOS MERCADO PAGO",
    "schemas/notification.py": "VALIDACION DE NOTIFICACIONES",
    "schemas/parking.py": "VALIDACION DE ESTADIAS Y ACCESOS",
    "schemas/reservation.py": "VALIDACION DE RESERVAS Y FECHAS",
    "schemas/support.py": "VALIDACION DE TICKETS DE SOPORTE",
    "schemas/user.py": "VALIDACION DE DATOS DE USUARIOS",
    "schemas/validators.py": "REGLAS COMUNES DE VALIDACION",

    # ---- REPOSITORIES ----
    "repositories/__init__.py": "PAQUETE DE ACCESO A BASE DE DATOS",
    "repositories/access_log_repository.py": "CONSULTAS DE HISTORIAL DE ACCESOS",
    "repositories/branch_repository.py": "CONSULTAS DE SUCURSALES Y PISOS",
    "repositories/camera_repository.py": "CONSULTAS DE CAMARAS IP DE AUDITORIA",
    "repositories/mercadopago_repository.py": "CONSULTAS DE REGISTROS MERCADO PAGO",
    "repositories/notification_repository.py": "CONSULTAS DE BANDEJA DE NOTIFICACIONES",
    "repositories/points_repository.py": "CONSULTAS DE PUNTOS Y MOVIMIENTOS",
    "repositories/promotion_repository.py": "CONSULTAS DE PROMOCIONES Y DESCUENTOS",
    "repositories/redemption_repository.py": "CONSULTAS DE TICKETS DE CANJE DE PUNTOS",
    "repositories/report_repository.py": "CONSULTAS DE METRICAS Y REPORTES",
    "repositories/reservation_repository.py": "CONSULTAS DE RESERVAS Y DISPONIBILIDAD",
    "repositories/scoping.py": "FILTRADO DE DATOS POR SUCURSAL Y ROL",
    "repositories/session_repository.py": "CONSULTAS DE SESIONES Y TOKENS ACTIVOS",
    "repositories/settings_repository.py": "CONSULTAS DE AJUSTES Y CONFIGURACION",
    "repositories/support_repository.py": "CONSULTAS DE TICKETS Y MENSAJES DE SOPORTE",
    "repositories/system_repository.py": "CONSULTAS DE PARAMETROS Y DIAGNOSTICO",
    "repositories/user_repository.py": "CONSULTAS DE USUARIOS Y ROLES EN BD",
    "repositories/vehicle_repository.py": "CONSULTAS DE VEHICULOS Y FLOTA",

    # ---- SERVICES ----
    "services/__init__.py": "PAQUETE DE REGLAS DE NEGOCIO",
    "services/access_occupancy.py": "CALCULO DE OCUPACION Y AFORO EN VIVO",
    "services/access_service.py": "PROCESAMIENTO DE INGRESOS Y EGRESOS",
    "services/availability.py": "CALCULO DE COCHERAS DISPONIBLES",
    "services/billing_service.py": "FACTURACION Y CALCULO DE DEUDA",
    "services/branch_service.py": "GESTION DE SUCURSALES Y PISOS",
    "services/email_service.py": "DESPACHO DE CORREOS ELECTRONICOS",
    "services/hardware_service.py": "INTEGRACION CON BARRERAS Y SENSORES",
    "services/mercadopago_service.py": "PASARELA DE PAGO CON MERCADO PAGO",
    "services/notification_service.py": "CENTRAL DE ENVIO DE ALERTAS Y PUSH",
    "services/oauth_service.py": "AUTENTICACION CON GOOGLE Y MICROSOFT",
    "services/occupancy_service.py": "METRICAS DE OCUPACION EN TIEMPO REAL",
    "services/organization_service.py": "ADMINISTRACION DE ORGANIZACIONES",
    "services/payments.py": "PROCESAMIENTO DE PAGOS Y BILLETERA",
    "services/report_service.py": "GENERACION DE INFORMES Y ESTADISTICAS",
    "services/reservation_service.py": "GESTION Y CONFIRMACION DE RESERVAS",
    "services/support_service.py": "ATENCION DE TICKETS DE SOPORTE",
    "services/time_service.py": "SINCRONIZACION DEL RELOJ VIRTUAL",
    "services/user_notification_service.py": "DESPACHO DE AVISOS AL USUARIO",
    "services/user_service.py": "GESTION DE CUENTAS DE USUARIO Y ROLES",
    "services/worker_service.py": "TAREAS PROGRAMADAS EN SEGUNDO PLANO",

    # ---- ROUTES ----
    "routes/__init__.py": "PAQUETE PRINCIPAL DE RUTAS HTTP",
    "routes/auth.py": "ENDPOINTS DE REGISTRO LOGIN Y OAUTH",
    "routes/views.py": "ENDPOINTS DE VISTAS HTML DEL SISTEMA",
    "routes/reports.py": "ENDPOINTS DE REPORTES Y METRICAS",
    "routes/admin/__init__.py": "PAQUETE DE RUTAS DE ADMINISTRACION",
    "routes/admin/branches.py": "ENDPOINTS DE ADMINISTRACION DE SUCURSALES",
    "routes/admin/operations.py": "ENDPOINTS DE OPERACIONES MANUALES Y CAJA",
    "routes/admin/promotions.py": "ENDPOINTS DE ADMINISTRACION DE DESCUENTOS",
    "routes/admin/reservations.py": "ENDPOINTS DE GESTION ADMIN DE RESERVAS",
    "routes/admin/settings.py": "ENDPOINTS DE AJUSTES DEL SISTEMA Y TARIFAS",
    "routes/admin/support.py": "ENDPOINTS DE GESTION DE TICKETS DE SOPORTE",
    "routes/admin/users.py": "ENDPOINTS DE GESTION DE USUARIOS ADMIN",
    "routes/admin/virtual_time.py": "ENDPOINTS DE CONTROL DEL RELOJ VIRTUAL",
    "routes/parking/__init__.py": "PAQUETE DE RUTAS DE OPERACION DE PLAYA",
    "routes/parking/access.py": "ENDPOINTS DE INGRESO Y EGRESO VEHICULAR",
    "routes/parking/status.py": "ENDPOINTS DE ESTADO DE OCUPACION EN VIVO",
    "routes/parking/utils.py": "UTILIDADES INTERNAS DE RUTAS DE PARKING",
    "routes/system/__init__.py": "PAQUETE DE RUTAS DE INFRAESTRUCTURA",
    "routes/system/cameras.py": "ENDPOINTS DE MONITOREO Y GESTION DE CAMARAS",
    "routes/system/common.py": "WEBSOCKET Y MANEJO DE PROCESOS DE CAMARAS",
    "routes/system/health.py": "ENDPOINTS DE DIAGNOSTICO DE SALUD TECNICA",
    "routes/system/video.py": "ENDPOINTS DE TRANSMISION DE VIDEO EN VIVO",
    "routes/user/__init__.py": "PAQUETE DE RUTAS DEL CLIENTE FINAL",
    "routes/user/balance.py": "ENDPOINTS DE SALDO Y RECARGAS",
    "routes/user/fidelization.py": "ENDPOINTS DE PUNTOS Y RECOMPENSAS",
    "routes/user/mercadopago.py": "ENDPOINTS DE CHECKOUT MERCADO PAGO",
    "routes/user/notifications.py": "ENDPOINTS DE BANDEJA DE NOTIFICACIONES",
    "routes/user/profile.py": "ENDPOINTS DE PERFIL Y DATOS PERSONALES",
    "routes/user/reservations.py": "ENDPOINTS DE RESERVAS DEL CLIENTE",
    "routes/user/support.py": "ENDPOINTS DE ENVIO DE TICKETS DE AYUDA",
    "routes/user/vehicles.py": "ENDPOINTS DE GESTION DE FLOTA DEL CLIENTE",

    # ---- FRONTEND JS ----
    "static/js/api_client.js": "PUENTE DE COMPATIBILIDAD API GLOBAL",
    "static/js/auth.js": "ORQUESTADOR DE FORMULARIOS DE ACCESO",
    "static/js/contacto.js": "ENVIO DEL FORMULARIO DE CONTACTO",
    "static/js/dashboard.js": "COMANDANTE GENERAL DEL PANEL ADMIN",
    "static/js/landing.js": "ORQUESTADOR DE PORTADA MAPA Y CARRUSEL",
    "static/js/main.js": "UTILIDADES GLOBALES Y GESTION DE SESION",
    "static/js/perfil.js": "DIRECTOR DE ORQUESTA DEL PORTAL CLIENTE",
    "static/js/reservas.js": "PUENTE DE RESERVAS Y REFRESCO EN SEGUNDO PLANO",
    "static/js/vehicles.js": "COCHERA PERSONAL Y ALTA DE VEHICULOS",
    "static/js/modules/action-menu.js": "MENU CONTEXTUAL DESPLEGABLE",
    "static/js/modules/admin-help.js": "CENTRO DE ASISTENCIA Y FAQ ADMIN",
    "static/js/modules/admin-tour-engine.js": "MOTOR DE TOURS GUIADOS DEL PANEL",
    "static/js/modules/admin-tour-steps.js": "PASOS DE LOS TOURS ADMINISTRATIVOS",
    "static/js/modules/admin-tour.js": "ORQUESTADOR DE TOURS DE ADMINISTRACION",
    "static/js/modules/api.js": "CLIENTE HTTP CENTRAL Y TOKENS JWT",
    "static/js/modules/auth.js": "LOGICA DE INGRESO REGISTRO Y OAUTH",
    "static/js/modules/chart-window.js": "ZOOM Y VENTANA DESLIZANTE DE GRAFICOS",
    "static/js/modules/dashboard-admin-branches-crud.js": "ALTA EDICION Y BAJA DE SUCURSALES",
    "static/js/modules/dashboard-admin-branches-floors.js": "GESTION DE PISOS Y AFORO POR NIVEL",
    "static/js/modules/dashboard-admin-branches.js": "FACHADA DE SUCURSALES Y NIVELES",
    "static/js/modules/dashboard-admin-settings.js": "AJUSTES DE BARRERAS MQTT Y TARIFAS",
    "static/js/modules/dashboard-admin-users.js": "GESTION Y BLOQUEO DE USUARIOS ADMIN",
    "static/js/modules/dashboard-admin.js": "FACHADA CENTRAL DE ADMINISTRACION",
    "static/js/modules/dashboard-cameras.js": "ADMINISTRACION DE CAMARAS IP",
    "static/js/modules/dashboard-finance.js": "MOVIMIENTOS FINANCIEROS Y CIERRE DE CAJA",
    "static/js/modules/dashboard-informes.js": "MAPA DE CALOR Y REPORTES AVANZADOS",
    "static/js/modules/dashboard-metrics.js": "METRICAS VISUALES CON GRAFICOS",
    "static/js/modules/dashboard-operations.js": "INGRESOS Y EGRESOS MANUALES EN GARITA",
    "static/js/modules/dashboard-promotions.js": "CREACION Y GESTION DE PROMOCIONES",
    "static/js/modules/dashboard-reservations.js": "FACHADA DE RESERVAS ADMINISTRATIVAS",
    "static/js/modules/dashboard-stats.js": "TABLA DE OCUPACION Y WEBSOCKET EN VIVO",
    "static/js/modules/dashboard-tickets.js": "RESOLUCION DE TICKETS DE SOPORTE",
    "static/js/modules/dashboard-ui.js": "NAVEGACION DE SOLAPAS DEL DASHBOARD",
    "static/js/modules/drag-sort.js": "REORDENAMIENTO DE ELEMENTOS POR ARRASTRE",
    "static/js/modules/estadisticas-ocr.js": "GRAFICOS Y AUDITORIA DE LECTURAS OCR",
    "static/js/modules/landing-carousel.js": "ANIMACION DEL CARRUSEL DE IMAGENES",
    "static/js/modules/landing-data.js": "DATOS ESTATICOS DE LA PORTADA",
    "static/js/modules/landing-map-state.js": "ESTADO COMPARTIDO DEL MAPA PUBLICO",
    "static/js/modules/landing-map.js": "MAPA LEAFLET INTERACTIVO DE SEDES",
    "static/js/modules/landing-reviews.js": "TESTIMONIOS Y OPINIONES DE CLIENTES",
    "static/js/modules/landing.js": "COMPORTAMIENTO DINAMICO DE PORTADA",
    "static/js/modules/list-pagination.js": "CONTROL DE PAGINADO DE TABLAS",
    "static/js/modules/notifications-actions.js": "ACCIONES DE NOTIFICACIONES LEIDAS Y BORRADO",
    "static/js/modules/notifications-badge.js": "CONTEO Y BURBUJA ROJA DE NO LEIDAS",
    "static/js/modules/notifications-dropdown.js": "MENU DESPLEGABLE DE ALERTAS EN HEADER",
    "static/js/modules/notifications-format.js": "ICONOS CATEGORIAS Y FECHAS DE AVISOS",
    "static/js/modules/notifications-nav.js": "ACCIONES RAPIDAS DESDE NOTIFICACIONES",
    "static/js/modules/notifications-polling.js": "CONSULTA PERIODICA DE NUEVAS ALERTAS",
    "static/js/modules/notifications-render.js": "DIBUJADO Y FILTROS DE NOTIFICACIONES",
    "static/js/modules/notifications-state.js": "ESTADO COMPARTIDO DE NOTIFICACIONES",
    "static/js/modules/notifications.js": "CENTRAL DE ALERTAS Y NOTIFICACIONES",
    "static/js/modules/onboarding-helpers.js": "ASISTENTE DE PRIMER INGRESO Y MODALES",
    "static/js/modules/operator-alerts.js": "ALERTAS AUDIBLES Y VISUALES DE GARITA",
    "static/js/modules/profile-help.js": "CENTRO DE AYUDA Y TICKETS DE CLIENTE",
    "static/js/modules/profile.js": "GESTION DE DATOS PUNTOS Y BILLETERA",
    "static/js/modules/reservas-actions.js": "PAGOS Y CANCELACIONES DE RESERVAS",
    "static/js/modules/reservas-form.js": "FORMULARIO Y CALCULADORA DE RESERVAS",
    "static/js/modules/reservas-list.js": "HISTORIAL Y TARJETAS DE RESERVA",
    "static/js/modules/reservas-pass.js": "PASE DIGITAL CON CODIGO QR",
    "static/js/modules/reservas.js": "FACHADA INTEGRAL DE RESERVAS CLIENTE",
    "static/js/modules/reset-password.js": "RESTABLECIMIENTO DE CONTRASENA",
    "static/js/modules/theme.js": "PALETA DE COLORES Y TEMA VISUAL",
    "static/js/modules/tour-steps.js": "PASOS DE LOS TOURS DE BIENVENIDA",
    "static/js/modules/tour.js": "MOTOR DE TOURS INTERACTIVOS",
    "static/js/modules/ui.js": "CONTROL DE VENTANAS MODALES Y VISTAS",
    "static/js/modules/utils.js": "FORMATEO DE DATOS Y CARTELES TOAST",
    "static/js/modules/vehicles.js": "VALIDACION Y CRUD DE VEHICULOS",
    "static/js/modules/virtual-time.js": "RELOJ VIRTUAL DE SIMULACION",

    # ---- SCRIPTS ----
    "scripts/arduino_bridge.py": "PUENTE SERIE ENTRE ARDUINO Y MQTT",
    "scripts/cleanup_invalid_plates.py": "LIMPIEZA DE PATENTES INVALIDAS EN BD",
    "scripts/crear_usuarios_demo.py": "CREACION DE USUARIOS DE PRUEBA Y ROLES",
    "scripts/generate_demo_traffic.py": "SIMULACION DE TRAFICO DE VEHICULOS",
    "scripts/generate_reservation_test.py": "GENERACION DE RESERVAS DE PRUEBA",
    "scripts/generate_test_plates.py": "GENERADOR DE PATENTES A4 IMPRIMIBLES",
    "scripts/test_video.py": "PRUEBA AISLADA DE CAPTURA DE CAMARA",

    # ---- TEMPLATES ----
    "templates/base.html": "ESTRUCTURA PRINCIPAL DE TODA LA WEB",
    "templates/index.html": "PORTADA PUBLICA Y HERO PRINCIPAL",
    "templates/dashboard.html": "ESTRUCTURA DEL PANEL DE ADMINISTRACION",
    "templates/perfil.html": "ESTRUCTURA DEL PORTAL DEL CLIENTE",
    "templates/contacto.html": "PAGINA DE CONTACTO Y SOPORTE",
    "templates/instalar.html": "PAGINA DE INSTALACION DE LA PWA",
    "templates/estadisticas_ocr.html": "ESTADISTICAS Y METRICAS OCR",
    "templates/monitoreo_live.html": "MONITOREO DE CAMARAS EN VIVO",
    "templates/nuestra_red.html": "MAPA DE SUCURSALES Y RED DE PLAYAS",
    "templates/privacidad.html": "POLITICAS DE PRIVACIDAD Y DATOS",
    "templates/terminos.html": "TERMINOS Y CONDICIONES DE SERVICIO",
    "templates/reset_password.html": "PANTALLA DE RESTABLECIMIENTO DE CLAVE",
}

def obtener_resumen_escueto(path: str, purpose: str = "", section: str = "") -> str:
    # 1. MAPEO EXPLICITO
    if path in MAPA_RESUMENES:
        return MAPA_RESUMENES[path]

    # 2. HERRAMIENTAS INTERNAS (_tools/)
    if path.startswith("_tools/"):
        nombre = path.split("/")[-1].replace(".py", "")
        if "check_" in nombre:
            sub = nombre.replace("check_", "").replace("_", " ")
            return _limpiar(f"AUDITORIA: {sub}")
        if "migrate_" in nombre:
            sub = nombre.replace("migrate_", "").replace("_", " ")
            return _limpiar(f"MIGRACION DE TOKENS: {sub}")
        if "generate_" in nombre:
            sub = nombre.replace("generate_", "").replace("_", " ")
            return _limpiar(f"GENERADOR: {sub}")
        return _limpiar(f"HERRAMIENTA: {nombre.replace('_', ' ')}")

    # 3. MIGRACIONES DE BASE DE DATOS (alembic/versions/)
    if path.startswith("alembic/versions/"):
        nombre = path.split("/")[-1].replace(".py", "")
        # QUITAR EL HASH INICIAL (EJ: 49a240f0fc25_add_performance_indexes -> add_performance_indexes)
        if "_" in nombre:
            _, resto = nombre.split("_", 1)
        else:
            resto = nombre
        palabras = resto.replace("_", " ")
        return _limpiar(f"MIGRACION BD: {palabras}")

    # 4. HOJAS DE ESTILO (static/css/)
    if path.startswith("static/css/"):
        sub = path.replace("static/css/", "").replace(".css", "")
        partes = sub.split("/")
        tipo = partes[0] if len(partes) > 1 else "general"
        nom = partes[-1].replace("_", " ").replace("-", " ")
        if tipo == "base":
            return _limpiar(f"ESTILOS BASE: {nom}")
        if tipo == "components":
            return _limpiar(f"COMPONENTE CSS: {nom}")
        if tipo == "layout":
            return _limpiar(f"ESTILOS LAYOUT: {nom}")
        if tipo == "pages":
            return _limpiar(f"ESTILOS DE PAGINA: {nom}")
        return _limpiar(f"ESTILOS CSS: {nom}")

    # 5. PLANTILLAS HTML (templates/)
    if path.startswith("templates/"):
        sub = path.replace("templates/", "").replace(".html", "")
        partes = sub.split("/")
        if partes[0] == "emails":
            nom = partes[-1].replace("_", " ")
            return _limpiar(f"EMAIL: {nom}")
        if partes[0] == "components":
            nom = partes[-1].replace("_", " ")
            return _limpiar(f"COMPONENTE: {nom}")
        if partes[0] == "dashboard":
            nom = partes[-1].replace("_", " ")
            return _limpiar(f"PANEL ADMIN: {nom}")
        if partes[0] == "profile":
            nom = partes[-1].replace("_", " ")
            return _limpiar(f"PORTAL CLIENTE: {nom}")
        nom = partes[-1].replace("_", " ")
        return _limpiar(f"PLANTILLA: {nom}")

    # 6. PRUEBAS AUTOMATIZADAS (tests/)
    if path.startswith("tests/"):
        nom = path.replace("tests/", "").replace(".py", "")
        if nom == "conftest":
            return "CONFIGURACION Y FIXTURES DE PYTEST"
        if nom.startswith("test_"):
            resto = nom.replace("test_", "").replace("_", " ")
            return _limpiar(f"PRUEBA: {resto}")
        return _limpiar(f"TEST: {nom.replace('_', ' ')}")

    # 7. EXTRACCION DESDE PURPOSE O NOMBRE
    if purpose:
        primera_frase = purpose.split(".")[0].split(":")[0].strip()
        palabras = primera_frase.split()[:5]
        if palabras:
            return _limpiar(" ".join(palabras))

    base = path.split("/")[-1].split(".")[0].replace("_", " ").replace("-", " ")
    return _limpiar(base)
