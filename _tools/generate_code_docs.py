"""Genera 'EXPLICACION DE CODIGO/data.js' a partir del codigo fuente real.

Recorre los archivos del proyecto (backend Python, frontend JS/CSS, plantillas,
tests, migraciones y scripts), extrae simbolos (clases/funciones/metodos con
firma y docstring) y relaciones (imports -> importado por), y vuelca todo en un
unico data.js que consume el visor 'EXPLICACION DE CODIGO/index.html'.

Ademas fusiona la capa de ANALISIS (carpeta '_tools/analysis/'): explicaciones
redactadas tras analizar el cuerpo real de cada archivo y cada funcion, en
lenguaje sencillo. El analisis tiene prioridad sobre el docstring original, que
se conserva en 'purpose_doc' / 'doc_orig' para poder mostrarlo junto al
analisis.

Uso:
    .\\venv\\Scripts\\python.exe _tools\\generate_code_docs.py
"""

from __future__ import annotations

import ast
import importlib.util
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from resumenes_archivos import obtener_resumen_escueto

OUT_DIR = ROOT / "EXPLICACION DE CODIGO"
OUT_FILE = OUT_DIR / "data.js"
ANALYSIS_DIR = ROOT / "_tools" / "analysis"

SKIP_PARTS = {"venv", "scripts.bak", "alpr_debug", "__pycache__", ".git", ".pytest_cache", "captured_images", "node_modules", "EXPLICACION DE CODIGO", "Diseno_Proyecto", "Info proyecto", "backlogAUTOPASS", "data"}

# ---------------------------------------------------------------------------
# Propositos y notas por archivo (overlay). Se usa cuando el archivo no tiene
# docstring de modulo (Python) o cabecera JSDoc (JS). Clave = ruta con '/'.
# ---------------------------------------------------------------------------
FILE_NOTES: dict[str, dict[str, str]] = {
    # ---- arranque ----
    "main.py": {
        "purpose": "Punto de entrada de la API FastAPI: monta routers, middlewares, lifespan de arranque/apagado, workers de fondo, servicio de manifest PWA y cabeceras de seguridad.",
    },
    "init_db.py": {"purpose": "Script CLI para crear todas las tablas y sembrar los datos iniciales (sucursal demo, admin, parametros) en la base configurada."},
    "alpr_service.py": {"purpose": "Entry point que arranca el proceso del servicio ALPR (lectura de patentes/QR) delegando en alpr.runner."},
    "locustfile.py": {"purpose": "Escenario de prueba de carga (Locust) que autentica usuarios y ejerce endpoints para medir rendimiento."},
    "alembic/env.py": {"purpose": "Configuracion del entorno Alembic: carga la URL de BD, los metadatos de los modelos y ejecuta las migraciones online/offline."},
    # ---- core ----
    "core/__init__.py": {"purpose": "Marca el paquete core (utilidades transversales: config, seguridad, BD, cache, logging)."},
    "core/config.py": {"purpose": "Define la clase Settings con toda la configuracion del sistema (leida desde variables de entorno / .env): BD, JWT, MercadoPago, MQTT, SMTP, ALPR, etc."},
    "core/time.py": {"purpose": "Helpers de tiempo del sistema: utcnow (UTC real) y localnow (hora de negocio, afectada por el reloj virtual de testing)."},
    "core/mqtt.py": {"purpose": "Cliente central MQTT para control de barreras fisicas. No gestiona camaras; los comandos de apertura nacen en services/hardware_service.py."},
    "core/limiter.py": {"purpose": "Limitador de tasa (rate limiting) reutilizable, aplicado sobre todo a endpoints administrativos."},
    "core/cache.py": {"purpose": "Cache TTL en memoria (SimpleTTLCache) para evitar recalculos costosos dentro de una misma peticion."},
    "core/seed.py": {"purpose": "Siembra los datos iniciales de la plataforma (organizacion principal, sucursal demo, usuario admin, settings base)."},
    # ---- routes ----
    "routes/__init__.py": {"purpose": "Marca el paquete de routers HTTP."},
    "routes/views.py": {"purpose": "Rutas que devuelven las vistas HTML (Jinja2): landing, instalacion PWA, dashboard, perfil, legal, monitoreo, etc."},
    "routes/auth.py": {"purpose": "Autenticacion: registro, login/logout, recuperacion de contrasena y flujo OAuth (Google/Microsoft)."},
    "routes/reports.py": {"purpose": "Endpoints de informes y metricas: resumen financiero, historial de pagos, accesos, estadisticas OCR, heatmap de trafico y ocupacion."},
    "routes/parking/__init__.py": {"purpose": "Marca el subpaquete de rutas de operacion de estacionamiento (accesos y estado)."},
    "routes/parking/utils.py": {"purpose": "Utilidades compartidas por las rutas de parking."},
    "routes/admin/__init__.py": {"purpose": "Marca el subpaquete de rutas administrativas."},
    "routes/system/__init__.py": {"purpose": "Marca el subpaquete de rutas de sistema (camaras, salud, video)."},
    "routes/system/common.py": {"purpose": "Infraestructura compartida de camaras: esquema de configuracion, manejo de procesos y ConnectionManager de WebSockets."},
    "routes/user/__init__.py": {"purpose": "Marca el subpaquete de rutas del cliente final."},
    # ---- models ----
    "models/__init__.py": {"purpose": "Marca el paquete de modelos ORM SQLAlchemy."},
    # ---- schemas ----
    "schemas/__init__.py": {"purpose": "Marca el paquete de esquemas Pydantic (validacion de entrada/salida)."},
    # ---- frontend JS nucleo ----
    "static/js/api_client.js": {"purpose": "Cliente HTTP legado expuesto en el objeto global para las paginas que no cargan modulos ES."},
    "static/js/auth.js": {"purpose": "Orquestador de la pagina de autenticacion: conecta el modulo auth.js con el DOM (login, registro, recuperacion)."},
    "static/js/contacto.js": {"purpose": "Bootstrap de la pagina de contacto (envio del formulario / interacciones del DOM)."},
    "static/js/dashboard.js": {"purpose": "Orquestador del dashboard operativo: inicializa modulos de estadisticas, ocupacion, camaras y metricas segun la pagina."},
    "static/js/landing.js": {"purpose": "Orquestador de la landing publica: scroll del header, estado de sesion y arranque del mapa/carrusel."},
    "static/js/main.js": {"purpose": "Bootstrap global: registra el Service Worker, inicializa helpers de UI comunes y el tour de bienvenida."},
    "static/js/perfil.js": {"purpose": "Orquestador de la pagina de perfil del cliente: carga inicial de la seccion activa y wiring de modulos."},
    "static/js/reservas.js": {"purpose": "Orquestador de la pagina de reservas: inicializa el listado, el formulario y el pase digital."},
    "static/js/vehicles.js": {"purpose": "Orquestador de la pagina de vehiculos (pagina suelta); el CRUD real vive en modules/vehicles.js."},
    "static/js/modules/api.js": {"purpose": "Cliente HTTP central del frontend: arma la URL base /v1, adjunta el token JWT, maneja refresh y normaliza errores."},
    "static/js/modules/theme.js": {"purpose": "Paleta y tokens de color del tema (objeto THEME) usados por graficos y estilos dinamicos."},
    "static/js/modules/reservas.js": {"purpose": "Re-exportador del formulario de reservas (fachada) para las paginas que lo importan."},
    "static/js/modules/notifications.js": {"purpose": "Re-exportador de utilidades de notificaciones (fachada)."},
    "static/js/modules/dashboard-admin.js": {"purpose": "Fachada del panel admin: reune las funciones usadas por el HTML (usuarios, sucursales, settings, camaras)."},
    "static/js/modules/dashboard-admin-branches.js": {"purpose": "Fachada del modulo de sucursales del admin (reune CRUD + pisos)."},
    "static/js/modules/dashboard-reservations.js": {"purpose": "Fachada del modulo de reservas del admin (form + listado)."},
    "static/js/modules/chart-window.js": {"purpose": "Componente de ventana/zoom deslizante reutilizado por los graficos de metricas."},
    "static/js/modules/landing-map-state.js": {"purpose": "Estado mutable compartido del mapa de la landing (objeto lmState)."},
    "static/js/modules/notifications-state.js": {"purpose": "Estado mutable compartido de notificaciones (objeto notifState)."},
    # ---- alpr ----
    "alpr/config.py": {"purpose": "Carga la configuracion del servicio ALPR desde variables de entorno (fuente de video, tipo de gate, modelos OCR, backend y secreto de nodo)."},
    "alpr/ocr_engine.py": {"purpose": "Motor OCR principal: deteccion de movimiento, OCR de patente, sistema de consenso por votos, overlay y envio de eventos al backend."},
    "alpr/preprocessor.py": {"purpose": "Preprocesado de imagen para ALPR: deteccion de patente (Haar), filtros de forma, recorte de banda Mercosur y realce."},
    "alpr/runner.py": {"purpose": "Orquesta el servicio ALPR completo: streamer de video + motor OCR + cliente WebSocket de monitoreo."},
    "alpr/video_streamer.py": {"purpose": "Lector de video en hilo aparte (webcam/RTSP/archivo) que entrega el ultimo frame disponible (politica drop-oldest)."},
    "alpr/ws_client.py": {"purpose": "Cliente WebSocket que envia frames y consola del ALPR al backend para el monitoreo en vivo."},
    # ---- core ----
    "core/alpr_security.py": {"purpose": "Protege los endpoints de nodos ALPR: valida origen local/privado y el secreto compartido del nodo."},
    "core/database.py": {"purpose": "Configura el engine SQLAlchemy, la sesion por peticion (get_db), la creacion/sincronizacion de esquema y la inicializacion."},
    "core/logger.py": {"purpose": "Configuracion de logging central y helpers (get_logger, mask_email para no exponer datos personales)."},
    "core/normalize.py": {"purpose": "Normalizacion canonica de textos (nombres, sucursales, patentes, DNI) para comparaciones y unicidad consistentes."},
    "core/security.py": {"purpose": "Nucleo de seguridad: hash/verificacion de contrasenas, JWT (crear/decodificar/revocar), dependencias de roles y aislamiento multiempresa."},
    # ---- models ----
    "models/enums.py": {"purpose": "Enumeraciones del dominio (roles, tipos de vehiculo, estados de reserva/pago, tipos de evento y de notificacion)."},
    "models/mercadopago.py": {"purpose": "Modelo MercadoPagoPayment: registro de pagos de MercadoPago y su aplicacion a la cuenta/estadia."},
    "models/notification.py": {"purpose": "Modelo UserNotification: notificaciones in-app del usuario."},
    "models/organization.py": {"purpose": "Modelo Organization: empresa/tenant que agrupa sucursales y usuarios (soporte multiempresa)."},
    "models/parking.py": {"purpose": "Modelos fisicos del estacionamiento: aforo, configuracion, camaras, logs de acceso, sucursales y pisos."},
    "models/reservation.py": {"purpose": "Modelo Reservation: reservas con estado, tipo de estadia, vehiculo, pago y snapshot de tarifas."},
    "models/support.py": {"purpose": "Modelos de soporte: tickets de ayuda y sus mensajes."},
    "models/types.py": {"purpose": "Tipos personalizados SQLAlchemy: fechas serializadas como texto ISO (DateTimeAsStr)."},
    "models/user.py": {"purpose": "Modelos de usuario y fidelizacion: User, Vehicle, PointsLog, Promotion y RedemptionTicket."},
    "models/user_session.py": {"purpose": "Modelo UserSession: dispositivos/sesiones activas para deteccion de nuevos dispositivos."},
    # ---- repositories ----
    "repositories/access_log_repository.py": {"purpose": "Consultas de logs de acceso: ultimo ingreso/salida, salidas pendientes y busquedas por patente/sucursal."},
    "repositories/branch_repository.py": {"purpose": "Consultas de sucursales: listado, busqueda por nombre, pisos, aforo y sedes activas."},
    "repositories/camera_repository.py": {"purpose": "Consultas de camaras."},
    "repositories/mercadopago_repository.py": {"purpose": "Consultas de pagos de MercadoPago."},
    "repositories/notification_repository.py": {"purpose": "Persistencia de notificaciones in-app (listar, contar, marcar leidas, limpiar)."},
    "repositories/points_repository.py": {"purpose": "Historial de puntos de fidelizacion."},
    "repositories/promotion_repository.py": {"purpose": "Consultas de promociones (por sucursal/global, activas)."},
    "repositories/redemption_repository.py": {"purpose": "Consultas de tickets de canje/descuento (validos, usados, por usuario)."},
    "repositories/report_repository.py": {"purpose": "Consultas agregadas para informes: recaudacion, reembolsos, metodos de pago, heatmap y accesos."},
    "repositories/reservation_repository.py": {"purpose": "Consultas de reservas: por usuario, solapamientos, vencimientos, filtros admin y recordatorios."},
    "repositories/session_repository.py": {"purpose": "Consultas de sesiones/dispositivos por usuario."},
    "repositories/settings_repository.py": {"purpose": "Lectura/escritura de settings: tarifas y parametros por sucursal y organizacion."},
    "repositories/support_repository.py": {"purpose": "Persistencia de tickets de soporte y sus mensajes."},
    "repositories/system_repository.py": {"purpose": "Operaciones de sistema (reset de todos los datos)."},
    "repositories/user_repository.py": {"purpose": "Consultas de usuarios: por email/DNI/rol, staff, admin local, saldo y puntos."},
    "repositories/vehicle_repository.py": {"purpose": "Consultas de vehiculos: por patente/usuario, tipo y favoritos."},
    # ---- routes ----
    "routes/admin/branches.py": {"purpose": "Endpoints admin de sucursales y pisos: CRUD, logo, habilitar/deshabilitar y capacidad por nivel."},
    "routes/admin/operations.py": {"purpose": "Operaciones manuales de staff: abrir barrera, entrada/salida manual y cancelar estadia."},
    "routes/admin/promotions.py": {"purpose": "CRUD de promociones para administradores."},
    "routes/admin/reservations.py": {"purpose": "Gestion admin de reservas: listar, crear, editar, confirmar pago, cancelar y descuentos."},
    "routes/admin/settings.py": {"purpose": "Configuracion admin: lectura de settings/parametros y actualizacion de tarifas."},
    "routes/admin/support.py": {"purpose": "Gestion admin de tickets de soporte (listar, detallar, responder y marcar notificaciones)."},
    "routes/admin/users.py": {"purpose": "Gestion admin de usuarios: listar, crear/invitar, editar, cambiar rol, bloquear, saldo, contrasena y borrar."},
    "routes/admin/virtual_time.py": {"purpose": "Control del reloj virtual (avanzar/retroceder/fijar/reset) para testing."},
    "routes/parking/access.py": {"purpose": "Endpoints de acceso fisico: validar patente/QR, salida y pago de estadia."},
    "routes/parking/status.py": {"purpose": "Estado de ocupacion y WebSocket en tiempo real; listado publico de sucursales."},
    "routes/system/cameras.py": {"purpose": "Gestion de camaras: configuracion, control del servicio (start/stop), orden, alta/edicion/borrado y notificacion de lectura."},
    "routes/system/health.py": {"purpose": "Salud del sistema, heartbeat de nodos ALPR, reset y hora virtual publica."},
    "routes/system/video.py": {"purpose": "Streaming de video por WebSocket/HTTP y captura de imagenes de los logs de acceso."},
    "routes/user/balance.py": {"purpose": "Saldo y estadias del usuario; tarifas vigentes (get_current_rates) y recarga de saldo."},
    "routes/user/fidelization.py": {"purpose": "Fidelizacion del cliente: promociones, canje de puntos, tickets y descuentos."},
    "routes/user/mercadopago.py": {"purpose": "Checkout de MercadoPago y sus retornos/webhook de pago."},
    "routes/user/notifications.py": {"purpose": "Notificaciones in-app del usuario (listar, leer, borrar)."},
    "routes/user/profile.py": {"purpose": "Perfil del usuario: obtener, actualizar y cambiar contrasena."},
    "routes/user/reservations.py": {"purpose": "Reservas del cliente: disponibilidad, crear/editar, pagar, recordatorio y cancelar."},
    "routes/user/support.py": {"purpose": "Tickets de soporte del cliente: crear, listar, detallar y responder."},
    "routes/user/vehicles.py": {"purpose": "Vehiculos del cliente: listar, agregar, marcar favorito y borrar."},
    # ---- schemas ----
    "schemas/auth.py": {"purpose": "Esquemas de autenticacion (completar OAuth, recuperar/restablecer contrasena) con sus validaciones."},
    "schemas/mercadopago.py": {"purpose": "Esquemas del checkout de MercadoPago y su respuesta."},
    "schemas/notification.py": {"purpose": "Esquemas de respuesta de notificaciones y contadores."},
    "schemas/parking.py": {"purpose": "Esquemas de estacionamiento: vehiculos, validacion de patente/QR, sucursales, pisos, camaras y estados."},
    "schemas/reservation.py": {"purpose": "Esquemas de reservas: creacion (cliente/admin), edicion, cotizacion de precio (PriceQuoteInput) y respuesta."},
    "schemas/support.py": {"purpose": "Esquemas de creacion/actualizacion de tickets de soporte."},
    "schemas/user.py": {"purpose": "Esquemas de usuario: alta, edicion, invitacion, login, cambio de contrasena, promociones y tickets."},
    "schemas/validators.py": {"purpose": "Validadores Pydantic reutilizables: contrasena, DNI, telefono y email."},
    # ---- services ----
    "services/access_service.py": {"purpose": "Servicio de accesos fisicos: entrada/salida ALPR, QR de reservas, operaciones manuales, control de aforo y apertura de barrera."},
    "services/billing_service.py": {"purpose": "Calculo de tarifas y deuda de estadias segun modalidad/sede/tipo de vehiculo, snapshot de tarifas de reserva y puntos ganados."},
    "services/branch_service.py": {"purpose": "Logica de sucursales: informacion, tarifas, capacidad, renombrado y resumen con ocupacion."},
    "services/email_service.py": {"purpose": "Envio de emails (confirmacion, recordatorio, auto-cancelacion, recuperacion, invitacion) usando plantillas Jinja."},
    "services/hardware_service.py": {"purpose": "Control de hardware: resolucion de barreras, comandos por puerto serie y publicacion MQTT."},
    "services/mercadopago_service.py": {"purpose": "Integracion con MercadoPago: crear pago, confirmar y aplicar el pago a la reserva."},
    "services/notification_service.py": {"purpose": "Gestion de eventos de ocupacion y salida pendiente para los dashboards, con despacho asincrono."},
    "services/oauth_service.py": {"purpose": "OAuth (Google/Microsoft): armado de URL, validacion de state, intercambio de codigo y alta del usuario."},
    "services/occupancy_service.py": {"purpose": "Calculo de ocupacion y capacidades por sucursal/piso."},
    "services/report_service.py": {"purpose": "Logica de informes y metricas: resumen financiero, historial de pagos, accesos, OCR, heatmap y ocupacion."},
    "services/reservation_service.py": {"purpose": "Nucleo de reservas: crear/editar/pagar/cancelar, disponibilidad, validacion de cotizacion y snapshot de tarifa, y vencimientos."},
    "services/support_service.py": {"purpose": "Logica de soporte: alta de tickets, consultas por cliente/admin, respuestas y notificaciones."},
    "services/time_service.py": {"purpose": "Reloj virtual para testing: offset, avanzar/retroceder/fijar y reset."},
    "services/user_notification_service.py": {"purpose": "CRUD de notificaciones in-app del usuario."},
    "services/user_service.py": {"purpose": "Logica de usuarios: alta, invitacion, edicion, borrado y gestion de vehiculos."},
    "services/worker_service.py": {"purpose": "Workers de fondo: limpieza de reservas vencidas, purga de imagenes ALPR, recordatorios y auto-cancelaciones."},
    # ---- frontend JS ----
    "static/js/modules/action-menu.js": {"purpose": "Menu de acciones contextual (tres puntos) para filas de tablas, con posicionamiento flotante."},
    "static/js/modules/dashboard-admin-branches-crud.js": {"purpose": "CRUD de sucursales en el panel admin (crear/editar/borrar, mapa, logo y horario)."},
    "static/js/modules/dashboard-admin-branches-floors.js": {"purpose": "Gestion de pisos y capacidades por sucursal."},
    "static/js/modules/dashboard-admin-settings.js": {"purpose": "Configuracion del admin: tarifas, parametros, capacidades, diagnostico, reset y exportacion."},
    "static/js/modules/dashboard-admin-users.js": {"purpose": "Gestion de usuarios en el panel admin (listar, crear/invitar, editar, bloquear, contrasena y paginacion)."},
    "static/js/modules/dashboard-cameras.js": {"purpose": "Configuracion de camaras: orden, alta/edicion, servicio dinamico y tabla."},
    "static/js/modules/dashboard-finance.js": {"purpose": "Panel financiero: carga de datos, filtros y grafico de recaudacion."},
    "static/js/modules/dashboard-informes.js": {"purpose": "Informes: heatmap, ocupacion, recaudacion, OCR y filtros."},
    "static/js/modules/dashboard-metrics.js": {"purpose": "Metricas del dashboard: series, KPIs, ventana deslizante y graficos."},
    "static/js/modules/dashboard-operations.js": {"purpose": "Operaciones del dashboard: entrada/salida manual, pago de ocupacion, detalle de log y salida pendiente."},
    "static/js/modules/dashboard-promotions.js": {"purpose": "CRUD de promociones en el panel admin (mapa, tipo de canje, iconos y tabla)."},
    "static/js/modules/dashboard-stats.js": {"purpose": "Estadisticas en vivo del dashboard: logs recientes, ocupacion, WebSocket y paginacion."},
    "static/js/modules/dashboard-tickets.js": {"purpose": "Gestion de tickets de soporte en el panel admin (listar, responder, filtrar y badge)."},
    "static/js/modules/dashboard-ui.js": {"purpose": "UI del dashboard: salud del sistema, streams de video, reloj, tabs y sidebar."},
    "static/js/modules/drag-sort.js": {"purpose": "Reordenamiento por arrastrar y soltar (drag & drop) para listas."},
    "static/js/modules/landing-carousel.js": {"purpose": "Carrusel de la landing publica."},
    "static/js/modules/landing-data.js": {"purpose": "Datos estaticos y cache de la landing (POIs, estadios) y contenido del carrusel."},
    "static/js/modules/landing.js": {"purpose": "Comportamiento de la landing: scroll del header y estado de sesion."},
    "static/js/modules/monitoreo-live.js": {"purpose": "Centro de monitoreo DVR: grilla de camaras, WebSockets, eventos y consola."},
    "static/js/modules/onboarding-helpers.js": {"purpose": "Asistente de primer ingreso: modales legales y onboarding de reservas."},
    "static/js/modules/profile-help.js": {"purpose": "Centro de ayuda del perfil: tickets, FAQ y adjuntos."},
    "static/js/modules/profile.js": {"purpose": "Perfil del cliente: datos, puntos, vouchers, recargas, estadias y promociones."},
    "static/js/modules/reservas-actions.js": {"purpose": "Acciones sobre reservas: cancelar y pagar (saldo o MercadoPago)."},
    "static/js/modules/reservas-list.js": {"purpose": "Listado e historial de reservas del cliente."},
    "static/js/modules/reservas-pass.js": {"purpose": "Pase digital de reserva (QR) y pago desde el pase."},
    "static/js/modules/reservations-admin-form.js": {"purpose": "Formulario admin de alta/edicion de reservas (lookup de patente, tarifas y slots)."},
    "static/js/modules/reservations-admin-list.js": {"purpose": "Listado de reservas del panel admin."},
    "static/js/modules/tour-steps.js": {"purpose": "Definicion de los pasos de los tours guiados del cliente."},
    "static/js/modules/tour.js": {"purpose": "Motor de inicio de los tours guiados del cliente."},
    "static/js/modules/vehicles.js": {"purpose": "CRUD de vehiculos del cliente."},
    "static/js/modules/list-pagination.js": {"purpose": "Componente reutilizable de listado paginado / limitado."},
    "static/js/modules/auth.js": {"purpose": "Logica de autenticacion en el cliente: login, registro, recuperacion, OAuth, validacion de contrasena y device id."},
    # ---- templates clave ----
    "templates/base.html": {"purpose": "Plantilla base del layout: define el <head>, fuentes/iconos, CSS modular y los bloques (title, extra_head, body_class, content) que heredan las demas vistas."},
    "templates/dashboard.html": {"purpose": "Vista del dashboard operativo: contenedores de estadisticas, ocupacion, camaras, metricas y modales de operacion."},
    "templates/perfil.html": {"purpose": "Vista del perfil del cliente: secciones de cuenta, saldo, reservas, vehiculos, puntos, notificaciones y ayuda."},
    "templates/reservas.html": {"purpose": "Vista de reservas del cliente: formulario de nueva reserva, listado/historial y pase digital."},
    "templates/profile/tabs/reservas.html": {"purpose": "Tab de reservas del perfil: formulario, listado e historial de reservas del cliente."},
    "templates/index.html": {"purpose": "Vista publica (landing): hero, features, mapa de sucursales, carrusel y modales de acceso."},
    "templates/monitoreo_live.html": {"purpose": "Vista del centro de monitoreo en vivo: grilla de camaras por sede, WebSockets y consola."},
    "templates/instalar.html": {"purpose": "Vista de instalacion de la PWA (guia para agregar la app al dispositivo)."},
    "templates/contacto.html": {"purpose": "Vista publica de contacto/consulta."},
    "templates/terminos.html": {"purpose": "Vista publica de terminos y condiciones."},
    "templates/privacidad.html": {"purpose": "Vista publica de politica de privacidad."},
    "templates/reset_password.html": {"purpose": "Vista de restablecimiento de contrasena (llega con token por email)."},
    "templates/estadisticas_ocr.html": {"purpose": "Vista de estadisticas de rendimiento del OCR de patentes."},
    "static/offline.html": {"purpose": "Pagina offline de la PWA que se muestra cuando no hay conexion."},
    "static/test_plates.html": {"purpose": "Pagina de desarrollo para probar la lectura de patentes / ALPR."},
    # ---- tabs dashboard ----
    "templates/dashboard/tabs/live.html": {"purpose": "Tab del dashboard: estadisticas en vivo, movimientos recientes y ocupacion por sede."},
    "templates/dashboard/tabs/finance.html": {"purpose": "Tab del dashboard: panel financiero con KPIs, filtros y grafico de recaudacion."},
    "templates/dashboard/tabs/metricas.html": {"purpose": "Tab del dashboard: metricas y graficos de trafico, ocupacion y accesos."},
    "templates/dashboard/tabs/users.html": {"purpose": "Tab del dashboard: gestion de usuarios (alta, edicion, roles y saldo)."},
    "templates/dashboard/tabs/branches.html": {"purpose": "Tab del dashboard: gestion de sucursales y pisos."},
    "templates/dashboard/tabs/promotions.html": {"purpose": "Tab del dashboard: gestion de promociones."},
    "templates/dashboard/tabs/tickets.html": {"purpose": "Tab del dashboard: gestion de tickets de soporte."},
    "templates/dashboard/tabs/admin_reservations.html": {"purpose": "Tab del dashboard: gestion administrativa de reservas."},
    "templates/dashboard/tabs/settings.html": {"purpose": "Tab del dashboard: configuracion (tarifas, parametros, plazas y monitoreo)."},
    "templates/dashboard/tabs/settings/settings_rates.html": {"purpose": "Sub-tab de configuracion: edicion del tarifario por tipo de vehiculo y modalidad."},
    "templates/dashboard/tabs/settings/settings_floors.html": {"purpose": "Sub-tab de configuracion: plazas/capacidad por piso."},
    "templates/dashboard/tabs/settings/settings_monitoring.html": {"purpose": "Sub-tab de configuracion: camaras y control de barreras."},
    "templates/dashboard/tabs/settings/settings_system.html": {"purpose": "Sub-tab de configuracion: parametros del sistema, diagnostico y reset."},
    # ---- tabs perfil ----
    "templates/profile/tabs/inicio.html": {"purpose": "Tab de inicio del perfil: resumen de cuenta, accesos rapidos y FAB de nueva reserva."},
    "templates/profile/tabs/cuenta.html": {"purpose": "Tab de cuenta del perfil: datos personales, cambio de contrasena y saldo."},
    "templates/profile/tabs/vehiculos.html": {"purpose": "Tab de vehiculos del perfil: alta/edicion, favorito y borrado."},
    "templates/profile/tabs/puntos.html": {"purpose": "Tab de puntos: saldo de fidelizacion, promociones, canjes e historial."},
    "templates/profile/tabs/notificaciones.html": {"purpose": "Tab de notificaciones del perfil: listado, filtros y acciones."},
    "templates/profile/tabs/ayuda.html": {"purpose": "Tab de ayuda del perfil: FAQ y tickets de soporte."},
}

# ---------------------------------------------------------------------------
# Descripcion de secciones (orden de aparicion en el visor).
# ---------------------------------------------------------------------------
SECTIONS = [
    ("arranque", "Arranque y entry points", "Scripts que ponen en marcha el sistema: API, servicio ALPR, inicializacion de base y utilidades de desarrollo."),
    ("core", "core/ - utilidades transversales", "Configuracion, seguridad (JWT/roles/multiempresa), base de datos, cache, logging, MQTT y normalizacion de textos."),
    ("models", "models/ - modelos ORM", "Tablas SQLAlchemy: usuarios, vehiculos, reservas, accesos, sucursales, promociones, tickets, etc."),
    ("schemas", "schemas/ - validacion Pydantic", "Contratos de entrada/salida de la API y validadores reutilizables (DNI, telefono, email, contrasena)."),
    ("repositories", "repositories/ - acceso a datos", "Consultas a la base de datos encapsuladas por dominio; unica capa que habla con SQLAlchemy en lectura."),
    ("services", "services/ - logica de negocio", "Reglas del negocio: accesos, disponibilidad, facturacion, pagos, reservas, reportes, notificaciones, workers."),
    ("routes", "routes/ - endpoints HTTP", "Capa delgada de FastAPI que valida la peticion, delega en services y devuelve la respuesta."),
    ("alpr", "alpr/ - reconocimiento de patentes", "Servicio independiente de vision: captura de video, preprocesado, OCR de patentes/QR y envio al backend."),
    ("frontend-nucleo", "Frontend - nucleo compartido", "Cliente HTTP, utilidades, UI, tema y modulos base reutilizados por todas las paginas."),
    ("frontend-cliente", "Frontend - area cliente", "Perfil, reservas, vehiculos, notificaciones, puntos, ayuda y tours del usuario final."),
    ("frontend-admin", "Frontend - area admin/staff", "Dashboard, sucursales, usuarios, finanzas, metricas, camaras, tickets y operaciones del panel."),
    ("frontend-landing", "Frontend - landing y monitoreo", "Pagina publica (mapa, carrusel), contacto, centro de monitoreo DVR y estadisticas OCR."),
    ("css", "Estilos (CSS)", "Hojas de estilo organizadas por capas: base, layout, components y pages."),
    ("templates", "Plantillas (Jinja2)", "Vistas HTML renderizadas por el servidor y plantillas de email."),
    ("tests", "Tests", "Suite de pruebas automatizadas (pytest) que cubre backend, ALPR, rutas y reglas de negocio."),
    ("migraciones", "Migraciones (Alembic)", "Versionado incremental del esquema de base de datos."),
    ("scripts", "Scripts y herramientas", "Utilidades CLI: datos demo, limpieza, generacion de manuales y guards de calidad de codigo."),
]


def is_skipped(path: Path) -> bool:
    if len(path.parts) >= 2 and path.parts[-2] == "analysis" and path.parts[-3] == "_tools":
        return True
    return any(part in SKIP_PARTS for part in path.parts)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


# ---------------------------------------------------------------------------
# Capa de analisis (_tools/analysis/analysis_*.py -> ANALISIS)
# ---------------------------------------------------------------------------
def load_analysis() -> dict[str, dict]:
    """Carga y fusiona todos los ANALISIS declarados en _tools/analysis/."""
    out: dict[str, dict] = {}
    if not ANALYSIS_DIR.is_dir():
        return out
    for p in sorted(ANALYSIS_DIR.glob("analysis_*.py")):
        spec = importlib.util.spec_from_file_location(p.stem, p)
        if spec is None or spec.loader is None:
            continue
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as err:  # noqa: BLE001 - informa y sigue con el resto
            print(f"[analisis] No se pudo cargar {p.name}: {err}")
            continue
        data = getattr(mod, "ANALISIS", None)
        if isinstance(data, dict):
            out.update(data)
    return out


def FormatearEmojisNuevaLinea(Texto: str) -> str:
    # ASEGURA QUE CADA EMOJI COMIENCE SIEMPRE EN UNA NUEVA LINEA
    if not Texto:
        return ""
    PatronEmoji = re.compile(r"([^\n\r])[ \t]*([\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50\u203c\u2049\u2139])")
    return PatronEmoji.sub(r"\1\n\n\2", str(Texto))


def apply_analysis(entry: dict, analisis: dict[str, dict]) -> None:
    """Sobrescribe proposito y docs de simbolos con el analisis redactado.

    Si el archivo/simbolo ya tenia texto propio (docstring o FILE_NOTES) y es
    distinto al analisis, se conserva en 'purpose_doc' / 'doc_orig' para que el
    visor pueda mostrarlo como referencia.
    """
    data = analisis.get(entry["path"])
    if not data:
        return
    entry["analizado"] = True
    prop_raw = data.get("proposito")
    if isinstance(prop_raw, str):
        prop = prop_raw.strip()
    elif isinstance(prop_raw, (list, tuple)):
        prop = " ".join(str(x) for x in prop_raw).strip()
    else:
        prop = ""
    if prop:
        prop = FormatearEmojisNuevaLinea(prop)
        actual = (entry.get("purpose") or "").strip()
        if actual and actual != prop:
            entry["purpose_doc"] = FormatearEmojisNuevaLinea(actual)
        entry["purpose"] = prop
    simbolos = data.get("simbolos") or {}
    for sym in entry.get("symbols", []):
        exp = simbolos.get(sym.get("qual") or sym["name"])
        if exp is None:
            exp = simbolos.get(sym["name"])
        if not exp or not isinstance(exp, str):
            continue
        exp = FormatearEmojisNuevaLinea(exp.strip())
        actual = (sym.get("doc") or "").strip()
        if actual and actual != exp:
            sym["doc_orig"] = FormatearEmojisNuevaLinea(actual)
        sym["doc"] = exp
        sym["analizado"] = True


# ---------------------------------------------------------------------------
# Python
# ---------------------------------------------------------------------------
def py_signature(node: ast.AST) -> str:
    args = node.args
    parts = [a.arg for a in args.posonlyargs]
    if args.posonlyargs:
        parts.append("/")
    parts += [a.arg for a in args.args]
    if args.vararg:
        parts.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        parts.append("*")
    parts += [a.arg for a in args.kwonlyargs]
    if args.kwarg:
        parts.append("**" + args.kwarg.arg)
    defaults = len(args.defaults)
    for i in range(len(parts) - defaults, len(parts)):
        if i >= 0:
            parts[i] += "=..."
    return f"({', '.join(parts)})"


def py_symbol(node: ast.AST, indent: int = 0) -> dict:
    kind = "class" if isinstance(node, ast.ClassDef) else "function"
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("_"):
        kind = "private"
    sig = ""
    if isinstance(node, ast.ClassDef):
        bases = [ast.unparse(b) for b in node.bases]
        sig = f"({', '.join(bases)})" if bases else ""
    else:
        sig = py_signature(node)
        if isinstance(node, ast.AsyncFunctionDef):
            sig = "async " + node.name + sig
        else:
            sig = node.name + sig
    return {
        "name": node.name,
        "qual": node.name,
        "kind": kind,
        "sig": sig,
        "doc": (ast.get_docstring(node) or "").strip(),
        "line": node.lineno,
        "indent": indent,
    }


def py_module_doc(tree: ast.Module) -> str:
    return (ast.get_docstring(tree) or "").strip()


def py_symbols(tree: ast.Module) -> list[dict]:
    out: list[dict] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            out.append(py_symbol(node, 0))
            for sub in node.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    sym = py_symbol(sub, 1)
                    sym["qual"] = f"{node.name}.{sub.name}"
                    out.append(sym)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(py_symbol(node, 0))
    return out


def py_imports(tree: ast.Module, mod_path: str) -> list[str]:
    pkg_parts = mod_path.split("/")[:-1]
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(".".join(alias.name.split(".")[:2]))
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                base = pkg_parts[: len(pkg_parts) - (node.level - 1)]
                mod = ".".join(base + ([node.module] if node.module else []))
            else:
                mod = node.module or ""
            if mod:
                found.add(".".join(mod.split(".")[:2]))
    return sorted(found)


# ---------------------------------------------------------------------------
# JavaScript
# ---------------------------------------------------------------------------
JS_RE = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?(?:function|class)\s+([A-Za-z_$][\w$]*)"
    r"|^\s*export\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)",
    re.MULTILINE,
)
JS_HEADER = re.compile(r"^\s*/\*\*(.*?)\*/", re.DOTALL)


def js_symbols(text: str) -> list[dict]:
    lines = text.splitlines()
    out: list[dict] = []
    for i, line in enumerate(lines):
        m = re.match(r"(\s*)(?:export\s+)?(?:async\s+)?(function|class)\s+([A-Za-z_$][\w$]*)", line)
        m2 = re.match(r"(\s*)export\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)", line)
        if m:
            name, kind = m.group(3), m.group(2)
            export = "export" in line
            d = _js_doc(lines, i)
            out.append({"name": name, "kind": kind, "sig": f"{'export ' if export else ''}{kind} {name}", "doc": d, "line": i + 1, "indent": 0})
        elif m2:
            name = m2.group(2)
            export = True
            rhs = line.split("=", 1)[1].strip() if "=" in line else ""
            kind = "value"
            if re.search(r"=>|\bfunction\b", rhs):
                kind = "function"
            d = _js_doc(lines, i)
            out.append({"name": name, "kind": kind, "sig": f"export const {name}", "doc": d, "line": i + 1, "indent": 0})
    return out


def _js_doc(lines: list[str], idx: int) -> str:
    j = idx - 1
    buf: list[str] = []
    while j >= 0:
        s = lines[j].strip()
        if s.startswith("//"):
            buf.insert(0, s.lstrip("/ "))
        elif s.endswith("*/"):
            block: list[str] = []
            k = j
            while k >= 0 and "/**" not in lines[k] and "/*" not in lines[k]:
                block.insert(0, lines[k].strip().strip("*").strip())
                k -= 1
            if k >= 0:
                block.insert(0, lines[k].strip().lstrip("/*").strip("*").strip())
            return " ".join(x for x in block if x).strip()
        else:
            break
        j -= 1
    return " ".join(buf).strip()


def js_header(text: str) -> str:
    m = JS_HEADER.match(text)
    if m:
        body = m.group(1)
        clean = []
        for ln in body.splitlines():
            s = ln.strip().lstrip("*").strip()
            if s:
                clean.append(s)
        return " ".join(clean).strip()
    return ""


def js_imports(text: str) -> list[str]:
    found: set[str] = set()
    for m in re.finditer(r"""from\s+['"](\.[^'"]+)['"]""", text):
        found.add(m.group(1))
    return sorted(found)


# ---------------------------------------------------------------------------
# Secciones por ruta
# ---------------------------------------------------------------------------
def section_for(path: str) -> str:
    if path.startswith("alembic/versions/"):
        return "migraciones"
    if path.startswith("alembic/"):
        return "arranque"
    if path.startswith("tests/"):
        return "tests"
    if path.startswith("core/"):
        return "core"
    if path.startswith("models/"):
        return "models"
    if path.startswith("schemas/"):
        return "schemas"
    if path.startswith("repositories/"):
        return "repositories"
    if path.startswith("services/"):
        return "services"
    if path.startswith("routes/"):
        return "routes"
    if path.startswith("alpr/"):
        return "alpr"
    if path.startswith("static/css/"):
        return "css"
    if path.startswith("templates/"):
        return "templates"
    if path.startswith("scripts/") or path.startswith("_tools/") or path.startswith("manual/tools/"):
        return "scripts"
    if path.startswith("static/js/"):
        name = path.split("/")[-1]
        if any(k in name for k in ("landing", "contacto", "monitoreo", "estadisticas-ocr")):
            return "frontend-landing"
        if any(k in name for k in ("dashboard", "admin", "reservation")):
            return "frontend-admin"
        if any(k in name for k in ("profile", "perfil", "reservas", "reserva", "vehicle", "vehiculo", "notif", "tour", "onboarding", "operator", "action-menu", "list-pagination", "drag-sort", "chart-window", "virtual-time")):
            return "frontend-cliente"
        return "frontend-nucleo"
    if path in ("main.py", "init_db.py", "alpr_service.py", "locustfile.py"):
        return "arranque"
    return "arranque"


def collect() -> list[dict]:
    files: list[dict] = []
    analisis = load_analysis()
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file() or is_skipped(p):
            continue
        sp = rel(p)
        if p.suffix == ".py":
            entry = _collect_py(p, sp)
        elif p.suffix == ".js" and sp.startswith("static/js/"):
            entry = _collect_js(p, sp)
        elif p.suffix == ".css" and sp.startswith("static/css/"):
            entry = _collect_css(p, sp)
        elif p.suffix == ".html" and (sp.startswith("templates/") or sp.startswith("static/")):
            entry = _collect_html(p, sp)
        else:
            continue
        if entry:
            apply_analysis(entry, analisis)
            if not entry["purpose"]:
                entry["purpose"] = fallback_purpose(sp, entry["lang"])
            entry["resumen"] = obtener_resumen_escueto(sp, entry.get("purpose", ""), entry.get("section", ""))
            files.append(entry)
    return files


def _base_entry(sp: str, lang: str) -> dict:
    note = FILE_NOTES.get(sp, {})
    sec = note.get("section") or section_for(sp)
    return {"path": sp, "lang": lang, "section": sec, "purpose": note.get("purpose", ""), "relations": note.get("relations", ""), "imports": [], "symbols": []}


def pretty(name: str) -> str:
    base = Path(name).name
    for ext in (".py", ".js", ".css", ".html"):
        if base.endswith(ext):
            base = base[: -len(ext)]
            break
    return base.replace("_", " ").replace("-", " ").strip()


def fallback_purpose(sp: str, lang: str) -> str:
    disp = pretty(sp)
    if lang == "css":
        if "/base/" in sp:
            return f"Estilos base del design system: {disp}."
        if "/components/" in sp:
            return f"Estilos del componente reutilizable «{disp}»."
        if "/layout/" in sp:
            return f"Estilos de layout (estructura de pagina): {disp}."
        if "/pages/" in sp:
            return f"Estilos especificos de la pagina «{disp}»."
        return "Hoja de estilos agregada."
    if lang == "html":
        if sp.startswith("templates/emails/"):
            return f"Plantilla HTML de email: {disp}."
        if sp.startswith("templates/components/"):
            return f"Partial reutilizable de plantilla: {disp}."
        return f"Vista/plantilla: {disp}."
    if sp.startswith("tests/"):
        return f"Pruebas automatizadas (pytest): {disp}."
    if lang == "js":
        return f"Modulo de frontend: {disp}."
    if sp.startswith("scripts/") or sp.startswith("_tools/") or sp.startswith("manual/tools/"):
        return f"Utilidad de linea de comandos: {disp}."
    return ""


def _collect_py(p: Path, sp: str) -> dict | None:
    if sp.startswith("alembic/versions/") and p.name != "__init__.py":
        e = _base_entry(sp, "py")
        m = re.search(r'"""\s*(.*?)"""', p.read_text(encoding="utf-8"), re.DOTALL)
        e["purpose"] = (m.group(1).strip().split("\n")[0] if m else "") or "Migracion de esquema Alembic."
        e["symbols"] = [{"name": "upgrade / downgrade", "kind": "function", "sig": "revision=" + p.stem.split("_")[0], "doc": "", "line": 0, "indent": 0}]
        return e
    e = _base_entry(sp, "py")
    try:
        src = p.read_text(encoding="utf-8")
        tree = ast.parse(src)
    except Exception:
        return e
    if not e["purpose"]:
        e["purpose"] = py_module_doc(tree)
    e["imports"] = py_imports(tree, sp)
    e["symbols"] = py_symbols(tree)
    return e


def _collect_js(p: Path, sp: str) -> dict:
    e = _base_entry(sp, "js")
    text = p.read_text(encoding="utf-8")
    if not e["purpose"]:
        e["purpose"] = js_header(text)
    e["imports"] = js_imports(text)
    e["symbols"] = js_symbols(text)
    return e


def _collect_css(p: Path, sp: str) -> dict:
    e = _base_entry(sp, "css")
    text = p.read_text(encoding="utf-8")
    e["symbols"] = [{"name": sel.strip(), "kind": "selector", "sig": sel.strip(), "doc": "", "line": 0, "indent": 0} for sel in _css_selectors(text)][:60]
    return e


def _css_selectors(text: str) -> list[str]:
    sels = []
    for m in re.finditer(r"(^|\})\s*([^{}@/][^{}]*)\{", text):
        body = m.group(2).strip()
        if body and len(body) < 120:
            sels.append(body)
    return sels


def _collect_html(p: Path, sp: str) -> dict:
    e = _base_entry(sp, "html")
    text = p.read_text(encoding="utf-8")
    head = text.lstrip(" \t\r\n")
    mj = re.match(r"\{#\s*(.*?)\s*#\}", head, re.DOTALL)
    mh = re.match(r"<!--\s*(.*?)\s*-->", head, re.DOTALL)
    lead = mj or mh
    if not e["purpose"] and lead:
        e["purpose"] = " ".join(lead.group(1).split())
    rel: list[str] = []
    extends = None
    for m in re.finditer(r"""\{%\s*(extends|include|import)\s+["']([^"']+)["']""", text):
        tpl = m.group(2).lstrip("./")
        cand = "templates/" + tpl
        if (ROOT / cand).is_file():
            rel.append(cand)
            if m.group(1) == "extends" and not extends:
                extends = cand
    if not e["purpose"] and extends:
        e["purpose"] = f"Vista que extiende {Path(extends).name}."
    e["imports"] = sorted(set(rel))
    blocks = re.findall(r"{%\s*block\s+(\w+)", text)
    e["symbols"] = [{"name": b, "kind": "block", "sig": "{% block " + b + " %}", "doc": "", "line": 0, "indent": 0} for b in dict.fromkeys(blocks)]
    return e


def resolve_import(imp: str, from_path: str, allpaths: set[str], modindex: dict[str, str]) -> str | None:
    if imp in allpaths:
        return imp
    if from_path.endswith(".js") and imp.startswith("."):
        base = from_path.split("/")[:-1]
        for part in imp.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                base.pop()
            else:
                base.append(part)
        cand = "/".join(base)
        return cand if cand in allpaths else None
    return modindex.get(imp)


def main() -> None:
    files = collect()
    allpaths = {f["path"] for f in files}
    modindex = {f["path"][:-3].replace("/", "."): f["path"] for f in files if f["path"].endswith(".py")}
    rev: dict[str, list[str]] = {}
    for f in files:
        for imp in f["imports"]:
            target = resolve_import(imp, f["path"], allpaths, modindex)
            if target and target != f["path"]:
                rev.setdefault(target, [])
                if f["path"] not in rev[target]:
                    rev[target].append(f["path"])
    for f in files:
        f["importedBy"] = sorted(rev.get(f["path"], []))
        f["symbolNames"] = [s["name"] for s in f["symbols"]]
        if f.get("purpose"):
            f["purpose"] = FormatearEmojisNuevaLinea(f["purpose"])
        if f.get("purpose_doc"):
            f["purpose_doc"] = FormatearEmojisNuevaLinea(f["purpose_doc"])
        for s in f.get("symbols", []):
            if s.get("doc"):
                s["doc"] = FormatearEmojisNuevaLinea(s["doc"])
            if s.get("doc_orig"):
                s["doc_orig"] = FormatearEmojisNuevaLinea(s["doc_orig"])

    data = {
        "project": "AUTOPASS - Gestion de estacionamiento inteligente",
        "generated": date.today().isoformat(),
        "sections": [{"id": i, "title": t, "description": d} for i, t, d in SECTIONS],
        "files": files,
    }
    OUT_DIR.mkdir(exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2)
    OUT_FILE.write_text("window.CODE_DOCS = " + payload + ";\n", encoding="utf-8")
    missing = [f["path"] for f in files if not f["purpose"]]
    print(f"Archivos documentados: {len(files)}")
    print(f"Simbolos: {sum(len(f['symbols']) for f in files)}")
    analizados = [f for f in files if f.get("analizado")]
    sim_analizados = sum(1 for f in files for s in f["symbols"] if s.get("analizado"))
    sim_totales = sum(len(f["symbols"]) for f in files)
    print(f"Archivos con analisis: {len(analizados)}/{len(files)}")
    print(f"Simbolos con analisis: {sim_analizados}/{sim_totales}")
    pendientes = [f for f in files if not f.get("analizado")]
    print(f"Pendientes de analizar: {len(pendientes)}")
    print(f"Sin proposito: {len(missing)}")
    for m in missing:
        print("  -", m)

    # EXPORTAR CADA ARCHIVO A SU PROPIO DOCUMENTO HTML
    ExportarHtmlEstatico(data)


def EscaparTextoHtml(Texto: str | None) -> str:
    # ESCAPAR CARACTERES ESPECIALES DE HTML
    if Texto is None:
        return ""
    return (
        str(Texto)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def SlugAncla(Nombre: str) -> str:
    # NORMALIZAR UN NOMBRE DE SIMBOLO A UN ID DE ANCLA VALIDO (MINUSCULAS, GUIONES)
    return re.sub(r"[^0-9a-zA-Z]+", "-", Nombre or "").strip("-").lower() or "x"


GlosarioTerminos = {
    # FRASES COMPUESTAS
    "middlewares de compresión": "Filtros intermedios que compactan y achican los datos antes de enviarlos por internet para que carguen rápido.",
    "middlewares de compresion": "Filtros intermedios que compactan y achican los datos antes de enviarlos por internet para que carguen rápido.",
    "middleware de compresión": "Filtro intermedio que compacta los datos antes de transmitirlos para ahorrar ancho de banda.",
    "middleware de compresion": "Filtro intermedio que compacta los datos antes de transmitirlos para ahorrar ancho de banda.",
    "middlewares de seguridad": "Filtros de control que revisan cada petición para proteger el sistema contra inyecciones y ataques cibernéticos.",
    "middleware de seguridad": "Filtro de control que protege el sistema contra accesos no autorizados o peticiones maliciosas.",
    "eventos de arranque/apagado": "Acciones que se ejecutan automáticamente cuando el servidor se enciende o se apaga (ciclo lifespan).",
    "eventos de arranque": "Rutinas que se inician automáticamente al prender el servidor web.",
    "evento de arranque": "Rutina automática que se ejecuta al iniciar el servidor.",
    "archivos estáticos": "Archivos que no cambian en el servidor (imágenes, hojas de estilo CSS, scripts JS) y se entregan directamente al navegador.",
    "archivos estaticos": "Archivos que no cambian en el servidor (imágenes, hojas de estilo CSS, scripts JS) y se entregan directamente al navegador.",
    "archivo estático": "Recurso directo como una imagen, CSS o JS que el navegador descarga sin procesar en la base de datos.",
    "archivo estatico": "Recurso directo como una imagen, CSS o JS que el navegador descarga sin procesar en la base de datos.",
    "esquema de base de datos": "La estructura organizada de tablas, columnas y tipos de datos que componen la base de datos.",
    "esquemas de base de datos": "Las definiciones formales de las tablas y relaciones que componen la base de datos.",
    "workers de fondo": "Pequeños programas ayudantes que corren en segundo plano realizando tareas automáticas de mantenimiento.",
    "worker de fondo": "Proceso en segundo plano que realiza tareas pesadas o recurrentes sin demorar la respuesta web.",
    "puntos de entrada": "Los archivos o módulos principales por donde se inicia la ejecución del sistema.",
    "punto de entrada": "El archivo o función inicial por donde el programa empieza a ejecutarse cuando se pone en marcha.",
    "código fuente": "El conjunto de instrucciones escritas por los programadores que le dicen a la computadora qué hacer.",
    "codigo fuente": "El conjunto de instrucciones escritas por los programadores que le dicen a la computadora qué hacer.",
    "reloj virtual": "Herramienta de simulación que permite adelantar el tiempo del sistema para probar estadías y cobros futuros.",
    "compresión GZip": "Técnica que compacta el texto enviado por internet para que las páginas carguen casi al instante.",
    "compresion GZip": "Técnica que compacta el texto enviado por internet para que las páginas carguen casi al instante.",
    "datos semilla": "Registros iniciales de prueba que se crean automáticamente si la base de datos está virgen.",
    "dato semilla": "Registro inicial de prueba cargado en la base de datos para facilitar el desarrollo.",
    "modelos ORM": "Clases de Python que representan cosas del mundo real como Usuario o Cochera en tablas de BD.",
    "modelo ORM": "Clase de Python vinculada directamente a una tabla de la base de datos mediante SQLAlchemy.",
    "Service Worker": "Script en segundo plano en el navegador que guarda archivos en caché para que la app cargue de inmediato.",
    "service worker": "Script en segundo plano en el navegador que guarda archivos en caché para que la app cargue de inmediato.",
    "Rate Limiting": "Escudo que frena cuántos clics o peticiones puede hacer una misma persona por segundo para evitar hackeos.",
    "rate limiting": "Freno de seguridad que limita la frecuencia de peticiones para proteger el servidor de saturación.",
    "rate limit": "Límite máximo de peticiones por minuto permitido a una misma dirección IP o usuario.",
    "hash bcrypt": "Algoritmo matemático que tritura la contraseña de forma irreversible para que nadie pueda ver la clave real.",
    "código QR": "Código de barras bidimensional que almacena datos para ser escaneado rápidamente por una cámara o celular.",
    "codigo QR": "Código de barras bidimensional que almacena datos para ser escaneado rápidamente por una cámara o celular.",
    "pase QR": "Credencial digital en pantalla con código QR para abrir la barrera del estacionamiento.",
    "API REST": "Menú de servicios estándar donde la pantalla (frontend) pide o guarda datos en el servidor en formato JSON.",

    # TERMINOS INDIVIDUALES
    "middlewares": "Filtros o puestos de peaje por donde pasa cada mensaje antes de llegar a la aplicación para revisar seguridad, comprimir datos o bloquear abusos.",
    "middleware": "Filtro o puesto de control intermedio que intercepta cada petición web para verificar permisos o transformar datos.",
    "FastAPI": "Librería moderna y de alto rendimiento de Python para crear servicios web y APIs a máxima velocidad.",
    "fastapi": "Librería moderna y de alto rendimiento de Python para crear servicios web y APIs a máxima velocidad.",
    "PWA": "Progressive Web App: sitio web que se puede instalar en el celular o PC como si fuera una aplicación nativa descargada de una tienda.",
    "pwa": "Progressive Web App: sitio web que se puede instalar en el celular o PC como si fuera una aplicación nativa descargada de una tienda.",
    "CORS": "Regla de seguridad del navegador que define qué sitios web externos tienen permiso de pedirle datos a nuestro servidor.",
    "cors": "Regla de seguridad del navegador que define qué sitios web externos tienen permiso de pedirle datos a nuestro servidor.",
    "MQTT": "Protocolo de mensajería ultraliviano para enviar órdenes a dispositivos físicos como barreras electrónicas.",
    "mqtt": "Protocolo de mensajería ultraliviano para enviar órdenes a dispositivos físicos como barreras electrónicas.",
    "seguridad": "Conjunto de protecciones y validaciones para evitar accesos no autorizados o ataques informáticos.",
    "compresión": "Técnica que reduce el peso de los datos para que viajen más rápido por internet.",
    "compresion": "Técnica que reduce el peso de los datos para que viajen más rápido por internet.",
    "GZip": "Algoritmo de compresión que reduce el tamaño de los archivos para acelerar la carga web.",
    "gzip": "Algoritmo de compresión que reduce el tamaño de los archivos para acelerar la carga web.",
    "base de datos": "El archivador digital ordenado donde quedan guardados permanentemente los usuarios, autos, reservas y cobros.",
    "bases de datos": "Archivadores digitales organizados donde se almacenan permanentemente todos los datos de la aplicación.",
    "esquemas": "Modelos que definen qué campos y reglas debe tener la información que entra o sale de la aplicación.",
    "esquema": "La estructura definida de datos o campos que debe tener un objeto en la base de datos o en la API.",
    "schemas": "Estructuras formales de validación de datos que definen los campos obligatorios y sus tipos.",
    "schema": "Estructura de validación que define la forma y tipos de datos aceptados por un endpoint.",
    "workers": "Subprogramas en segundo plano que realizan tareas automáticas sin hacer esperar al usuario.",
    "worker": "Proceso en segundo plano que ejecuta tareas programadas sin congelar la pantalla.",
    "routers": "Señalizadores de tránsito en el código: asocian cada dirección web a una función específica.",
    "router": "Módulo que agrupa y organiza un conjunto de rutas web relacionadas (ej: todas las de usuarios).",
    "vistas": "Páginas o pantallas preparadas para ser mostradas al usuario en su navegador.",
    "vista": "Pantalla o página visual entregada por el servidor para interactuar con el usuario.",
    "frontend": "La parte visual de la aplicación: lo que el usuario ve, toca e interactúa en el navegador.",
    "backend": "El cerebro del sistema que corre en el servidor procesando la lógica, seguridad y base de datos.",
    "endpoints": "Direcciones web del servidor preparadas para recibir peticiones y devolver respuestas.",
    "endpoint": "Dirección web específica (URL) del servidor encargada de realizar una acción concreta.",
    "API": "Interfaz de comunicación que permite a dos programas o pantallas hablarse e intercambiar información.",
    "APIs": "Conjuntos de interfaces que permiten conectar sistemas y aplicaciones entre sí.",
    "JWT": "Token digital con firma electrónica inviolable que identifica al usuario en cada clic sin pedir la clave.",
    "jwt": "Token digital con firma electrónica inviolable que identifica al usuario en cada clic sin pedir la clave.",
    "tokens": "Credenciales digitales temporales usadas para autenticar peticiones sin reenviar contraseñas.",
    "token": "Llave digital temporal que demuestra que el usuario ya inició sesión correctamente.",
    "SQLAlchemy": "El conector inteligente que traduce objetos de Python a tablas de base de datos sin escribir SQL a mano.",
    "sqlalchemy": "El conector inteligente que traduce objetos de Python a tablas de base de datos sin escribir SQL a mano.",
    "ORM": "Mapeo Objeto-Relacional: tecnología que permite manejar tablas de base de datos como si fueran objetos de Python.",
    "orm": "Mapeo Objeto-Relacional: tecnología que permite manejar tablas de base de datos como si fueran objetos de Python.",
    "lifespan": "Ciclo de vida del servidor: código que se ejecuta automáticamente al arrancar y al apagarse.",
    "Jinja2": "Motor que toma una plantilla HTML y le inserta los datos reales antes de enviarla a la pantalla.",
    "jinja2": "Motor que toma una plantilla HTML y le inserta los datos reales antes de enviarla a la pantalla.",
    "WebSockets": "Canal de comunicación en vivo y bidireccional para recibir novedades al instante sin recargar la pantalla.",
    "WebSocket": "Conexión continua en tiempo real entre el navegador y el servidor para intercambiar datos al instante.",
    "websockets": "Canal de comunicación en vivo y bidireccional para recibir novedades al instante sin recargar la pantalla.",
    "websocket": "Conexión continua en tiempo real entre el navegador y el servidor para intercambiar datos al instante.",
    "Pydantic": "Validador estricto de Python que comprueba que los datos recibidos tengan el formato y tipo esperado.",
    "pydantic": "Validador estricto de Python que comprueba que los datos recibidos tengan el formato y tipo esperado.",
    "bcrypt": "Algoritmo criptográfico de máxima seguridad para encriptar contraseñas de forma irreversible.",
    "hash": "Cadena de caracteres cifrada e irreversible generada a partir de un texto como una contraseña.",
    "localStorage": "Memoria privada del navegador del usuario donde se guarda su token de acceso.",
    "localstorage": "Memoria privada del navegador del usuario donde se guarda su token de acceso.",
    "ALPR": "Reconocimiento Automático de Patentes: cámaras con visión artificial que leen matrículas vehiculares.",
    "alpr": "Reconocimiento Automático de Patentes: cámaras con visión artificial que leen matrículas vehiculares.",
    "OCR": "Reconocimiento Óptico de Caracteres: tecnología que convierte los píxeles de una foto en letras y números editables.",
    "ocr": "Reconocimiento Óptico de Caracteres: tecnología que convierte los píxeles de una foto en letras y números editables.",
    "MercadoPago": "Pasarela de pagos en línea para cobrar reservas y recargar saldo con tarjeta o cuenta.",
    "mercadopago": "Pasarela de pagos en línea para cobrar reservas y recargar saldo con tarjeta o cuenta.",
    "seed": "Datos iniciales de prueba que se cargan automáticamente en la base de datos si está vacía.",
    "seeds": "Conjunto de datos iniciales que pueblan la base de datos para pruebas y demostraciones.",
    "cookies": "Pequeños archivos de texto que el navegador guarda para recordar preferencias o sesiones.",
    "cookie": "Dato pequeño que el servidor guarda en el navegador para recordar al usuario.",
    "ASGI": "Estándar moderno para que servidores web en Python puedan atender miles de conexiones al mismo tiempo.",
    "asgi": "Estándar moderno para que servidores web en Python puedan atender miles de conexiones al mismo tiempo.",
    "Uvicorn": "Servidor web rápido para Python que ejecuta aplicaciones ASGI como FastAPI.",
    "uvicorn": "El servidor web liviano y ultra veloz que ejecuta la aplicación en Python.",
    "CRUD": "Las cuatro operaciones básicas de cualquier sistema: Crear, Leer, Actualizar y Borrar registros.",
    "DOM": "Estructura interna de elementos HTML que el navegador arma para mostrar e interactuar con la página.",
    "CSS": "Lenguaje de diseño que define los colores, tamaños, fuentes y disposición visual de la página web.",
    "HTML": "Lenguaje de marcado que define los textos, botones, formularios e imágenes de una página web.",
    "JavaScript": "Lenguaje de programación que corre en el navegador y le da dinamismo e interactividad a la pantalla.",
    "Python": "Lenguaje de programación claro y versátil en el que está construido todo el backend de AUTOPASS.",
    "python": "Lenguaje de programación claro y versátil en el que está construido todo el backend de AUTOPASS.",
    "SQLite": "Motor de base de datos ultraliviano que guarda toda la información en un único archivo de disco.",
    "sqlite": "Motor de base de datos ultraliviano que guarda toda la información en un único archivo de disco.",
    "PostgreSQL": "Motor de base de datos potente y profesional ideal para almacenar grandes volúmenes de datos.",
    "postgresql": "Motor de base de datos potente y profesional ideal para almacenar grandes volúmenes de datos.",
    "Postgres": "Motor de base de datos relacional robusto y avanzado para entornos de alto tráfico.",
    "QR": "Código de barras bidimensional que almacena datos para ser escaneado rápidamente por una cámara o celular.",
    "qr": "Código de barras bidimensional que almacena datos para ser escaneado rápidamente por una cámara o celular.",
    "docstring": "Comentario especial dentro del código fuente donde el programador explica qué hace una función o clase.",
    "docstrings": "Comentarios explicativos integrados en el código de cada función o clase.",
    "repositorio": "Módulo de código especializado exclusivamente en comunicarse con la base de datos.",
    "repositorios": "Capa del sistema encargada de buscar, guardar y actualizar información en las tablas.",
    "servicio": "Módulo donde residen las reglas de negocio y la lógica de cálculos de la aplicación.",
    "servicios": "Capa del sistema que procesa las operaciones (cobros, asignación de lugares, validaciones).",
    "mock": "Objeto o función falsa creada durante las pruebas para simular un componente real sin afectar el sistema.",
    "mocks": "Simulaciones controladas de módulos reales utilizadas para probar el código de forma aislada.",
    "webhook": "Aviso automático enviado por un servicio externo (como MercadoPago) informando que se concretó una acción.",
    "webhooks": "Notificaciones automáticas entre servidores por HTTP para avisar eventos en tiempo real.",
    "OAuth": "Protocolo de autorización estándar que permite iniciar sesión usando cuentas externas como Google.",
    "payload": "El contenido o paquete de datos útiles que se envía dentro de una petición o respuesta de red.",
    "query": "Consulta o filtro de búsqueda enviado a la base de datos o en los parámetros de la URL.",
    "sesión": "Período activo durante el cual un usuario navega en el sistema habiéndose identificado previamente.",
    "sesion": "Período activo durante el cual un usuario navega en el sistema habiéndose identificado previamente.",
    "sesiones": "Conexiones activas de usuarios registradas en el sistema.",
    "caché": "Memoria de acceso ultrarrápido que guarda resultados recientes para no recalcularlos ni volver a pedirlos.",
    "cache": "Memoria de acceso ultrarrápido que guarda resultados recientes para no recalcularlos ni volver a pedirlos.",
    "JSON": "Formato de texto ligero y universal para transferir datos estructurados entre clientes y servidores.",
    "json": "Formato de texto ligero y universal para transferir datos estructurados entre clientes y servidores.",
    "HTTP": "Protocolo estándar de comunicación en la web para solicitar y enviar páginas y datos.",
    "HTTPS": "Versión cifrada y segura del protocolo HTTP protegida con certificados SSL/TLS.",
    "singleton": "Patrón de diseño que asegura que una clase tenga una única instancia viva en todo el sistema.",
    "framework": "Estructura de trabajo y herramientas prefabricadas sobre la cual se construye un software.",
    "asíncrono": "Código que puede esperar una respuesta de red o disco sin congelar el resto del programa.",
    "asincrono": "Código que puede esperar una respuesta de red o disco sin congelar el resto del programa.",
    "patente": "Matrícula identificatoria del vehículo leída por cámaras ALPR o ingresada manualmente.",
    "patentes": "Matrículas vehiculares registradas en el sistema para permitir el acceso automático.",
    "cochera": "Lugar individual y numerado dentro del estacionamiento asignado a un vehículo.",
    "cocheras": "Espacios de estacionamiento disponibles para autos, camionetas o motos.",
    "aforo": "Cantidad total o límite máximo de vehículos permitidos dentro del estacionamiento.",
    "tarifa": "Valor monetario configurado por hora o fracción de tiempo de estadía.",
    "tarifas": "Esquema de precios configurado según sucursal, horario y tipo de vehículo.",
    "barrera": "Dispositivo físico electromecánico en el ingreso o egreso que se abre al validar acceso.",
    "barreras": "Dispositivos electromecánicos de entrada y salida controlados por la aplicación.",
    "fidelización": "Programa de recompensas que otorga puntos a los clientes por cada estadía realizada.",
    "fidelizacion": "Programa de recompensas que otorga puntos a los clientes por cada estadía realizada.",
    "canje": "Uso de puntos de fidelización acumulados para conseguir estadías gratis o bonificaciones.",
    "canjes": "Operaciones donde el usuario utiliza sus puntos acumulados para obtener beneficios.",
    "autenticación": "Proceso mediante el cual el sistema confirma la identidad del usuario (ej: email y clave).",
    "autenticacion": "Proceso mediante el cual el sistema confirma la identidad del usuario (ej: email y clave).",
    "autorización": "Verificación de los permisos y rol del usuario para determinar si puede ejecutar una acción.",
    "autorizacion": "Verificación de los permisos y rol del usuario para determinar si puede ejecutar una acción.",
    "estadía": "Tiempo transcurrido desde que un vehículo entra al estacionamiento hasta que egresa.",
    "estadia": "Tiempo transcurrido desde que un vehículo entra al estacionamiento hasta que egresa.",
    "estadías": "Registros de permanencia y cobro de vehículos en el estacionamiento.",
    "estadias": "Registros de permanencia y cobro de vehículos en el estacionamiento.",
    "parámetros": "Valores de entrada que se le envían a una función para indicarle sobre qué datos trabajar.",
    "parametros": "Valores de entrada que se le envían a una función para indicarle sobre qué datos trabajar.",
    "parámetro": "Dato específico enviado a una función para configurar o completar su ejecución.",
    "parametro": "Dato específico enviado a una función para configurar o completar su ejecución."
}

MapaGlosario = {k.lower(): v for k, v in GlosarioTerminos.items()}
ClavesGlosarioOrdenadas = sorted(GlosarioTerminos.keys(), key=lambda k: len(k), reverse=True)
PatronGlosario = re.compile(
    r'(?<![a-zA-Z0-9_áéíóúÁÉÍÓÚñÑ])(' + '|'.join(re.escape(k) for k in ClavesGlosarioOrdenadas) + r')(?![a-zA-Z0-9_áéíóúÁÉÍÓÚñÑ])',
    re.IGNORECASE
)


def EnriquecerGlosarioHtml(Texto: str) -> str:
    # ESCAPAR PRIMERO Y LUEGO ENVOLVER CADA TERMINO TECNICO EN UN ABBR CON TOOLTIP
    if not Texto:
        return ""
    TextoConEmojisSeparados = FormatearEmojisNuevaLinea(Texto)
    TextoEscapado = EscaparTextoHtml(TextoConEmojisSeparados)
    def ReemplazarTermino(Coincidencia: re.Match) -> str:
        Termino = Coincidencia.group(1)
        Significado = MapaGlosario.get(Termino.lower(), "")
        if not Significado:
            return Termino
        return f'<abbr class="cd-term" data-tooltip="{EscaparTextoHtml(Significado)}">{Termino}</abbr>'
    return PatronGlosario.sub(ReemplazarTermino, TextoEscapado)


def ExportarHtmlEstatico(Datos: dict) -> None:
    # EXPORTAR CADA ARCHIVO ANALIZADO A UN DOCUMENTO HTML INDEPENDIENTE
    CarpetaArchivos = OUT_DIR / "archivos"
    CarpetaArchivos.mkdir(exist_ok=True)
    RutasValidas = {Archivo["path"] for Archivo in Datos["files"]}
    IndiceModulos = {
        Archivo["path"][:-3].replace("/", "."): Archivo["path"]
        for Archivo in Datos["files"]
        if Archivo["path"].endswith(".py")
    }

    EtiquetasTipos = {
        "class": "clase",
        "function": "funcion",
        "private": "privada",
        "value": "constante",
        "selector": "selector",
        "block": "bloque",
    }
    ClasesTipos = {
        "class": "b-class",
        "function": "b-function",
        "private": "b-private",
        "value": "b-value",
        "selector": "b-method",
        "block": "b-method",
    }
    EtiquetasLenguajes = {
        "py": "Python",
        "js": "JavaScript",
        "css": "CSS",
        "html": "HTML",
    }

    MapaSecciones = {Seccion["id"]: Seccion["title"] for Seccion in Datos["sections"]}

    for Archivo in Datos["files"]:
        ArchivoDestino = CarpetaArchivos / f"{Archivo['path']}.html"
        ArchivoDestino.parent.mkdir(parents=True, exist_ok=True)
        Profundidad = len(Archivo["path"].split("/"))
        PrefijoRaiz = "../" * Profundidad

        # RESOLVER DEPENDENCIAS LOCALES
        DependenciasLocales = []
        for Importacion in Archivo.get("imports", []):
            DestinoResuelto = resolve_import(Importacion, Archivo["path"], RutasValidas, IndiceModulos)
            if DestinoResuelto and DestinoResuelto != Archivo["path"] and DestinoResuelto not in DependenciasLocales:
                DependenciasLocales.append(DestinoResuelto)

        UsadoPor = Archivo.get("importedBy", [])
        TituloSeccion = MapaSecciones.get(Archivo.get("section"), Archivo.get("section", ""))
        TituloSeccionSimbolos = "CLASES Y FUNCIONES" if Archivo.get("symbols") else "EXPLICACION DEL CODIGO DEL ARCHIVO (FUNCIONAMIENTO GENERAL)"

        HtmlSimbolos = ""
        if not Archivo.get("symbols"):
            TextoProposito = Archivo.get("purpose", "")
            HtmlDocArchivo = f'<div class="cd-sym-doc">{EnriquecerGlosarioHtml(TextoProposito)}</div>' if TextoProposito else '<p class="cd-empty">SIN EXPLICACION REGISTRADA.</p>'
            HtmlSimbolos = f'''<div class="cd-symbols"><div id="sym-archivo" class="cd-sym analizado">
                    <div class="cd-sym-head">
                        <span class="cd-badge b-module">codigo general</span>
                        <span class="cd-sym-name">{EscaparTextoHtml(Archivo["path"])}</span>
                    </div>
                    <div>
                        <div class="cd-sym-sig"><code>Configuracion y logica a nivel de archivo</code></div>
                        {HtmlDocArchivo}
                    </div>
                </div></div>'''
        else:
            TarjetasSimbolos = []
            AnclasUsadas: dict[str, int] = {}
            for Simbolo in Archivo["symbols"]:
                EsMetodo = Simbolo.get("indent", 0) > 0
                Etiqueta = "metodo" if EsMetodo else EtiquetasTipos.get(Simbolo.get("kind"), Simbolo.get("kind", ""))
                ClaseInsignia = "b-method" if EsMetodo else ClasesTipos.get(Simbolo.get("kind"), "b-method")
                Calificador = Simbolo.get("qual") or ""
                PrefijoClase = f'<span class="cd-sym-cls">{EscaparTextoHtml(Calificador.split(".")[0])}.</span>' if "." in Calificador else ""
                MostrarFirma = Simbolo.get("sig") and Simbolo["sig"].strip() and Simbolo["sig"].strip() != Simbolo["name"].strip()
                HtmlFirma = f'<div class="cd-sym-sig"><code>{EscaparTextoHtml(Simbolo["sig"])}</code></div>' if MostrarFirma else ""
                HtmlDoc = f'<div class="cd-sym-doc">{EnriquecerGlosarioHtml(Simbolo.get("doc", ""))}</div>' if Simbolo.get("doc") else ""
                HtmlDocOrig = f'<div class="cd-sym-doc cd-sym-doc-orig">DOCSTRING ORIGINAL: {EnriquecerGlosarioHtml(Simbolo.get("doc_orig", ""))}</div>' if Simbolo.get("doc_orig") else ""

                BaseAncla = SlugAncla(Simbolo.get("name", ""))
                Repeticion = AnclasUsadas.get(BaseAncla, 0)
                AnclasUsadas[BaseAncla] = Repeticion + 1
                IdAncla = f"sym-{BaseAncla}" if Repeticion == 0 else f"sym-{BaseAncla}-{Repeticion + 1}"

                Tarjeta = f'''<div id="{IdAncla}" class="cd-sym {'method' if EsMetodo else 'kind-' + EscaparTextoHtml(Simbolo.get('kind', ''))}{' analizado' if Simbolo.get('analizado') else ''}">
                    <div class="cd-sym-head">
                        <span class="cd-badge {ClaseInsignia}">{EscaparTextoHtml(Etiqueta)}</span>
                        <span class="cd-sym-name">{PrefijoClase}{EscaparTextoHtml(Simbolo["name"])}</span>
                    </div>
                    <div>
                        {HtmlFirma}
                        {HtmlDoc}
                        {HtmlDocOrig}
                    </div>
                </div>'''
                TarjetasSimbolos.append(Tarjeta)
            HtmlSimbolos = f'<div class="cd-symbols">{"".join(TarjetasSimbolos)}</div>'

        EnlacesDependencias = "".join(f'<a href="{PrefijoRaiz}archivos/{p}.html" title="{EscaparTextoHtml(Archivo.get("resumen", p))}">{EscaparTextoHtml(p)}</a>' for p in DependenciasLocales) if DependenciasLocales else '<span class="cd-empty">SIN DEPENDENCIAS LOCALES.</span>'
        EnlacesUsadoPor = "".join(f'<a href="{PrefijoRaiz}archivos/{p}.html" title="{EscaparTextoHtml(Archivo.get("resumen", p))}">{EscaparTextoHtml(p)}</a>' for p in UsadoPor) if UsadoPor else '<span class="cd-empty">SIN REFERENCIAS DETECTADAS.</span>'

        HtmlPropositoOriginal = f'<div class="cd-purpose cd-purpose-orig">DOCSTRING ORIGINAL: {EnriquecerGlosarioHtml(Archivo.get("purpose_doc", ""))}</div>' if Archivo.get("purpose_doc") else ""
        HtmlInfoRelaciones = f'<div class="cd-purpose cd-purpose-info">{EnriquecerGlosarioHtml(Archivo.get("relations", ""))}</div>' if Archivo.get("relations") else ""

        ContenidoPagina = f'''<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AUTOPASS · {EscaparTextoHtml(Archivo["path"])}</title>
<link rel="stylesheet" href="{PrefijoRaiz}assets/code-docs.css">
</head>
<body>
<header class="cd-header">
  <div class="cd-brand">
    <a href="{PrefijoRaiz}index.html" class="cd-logo" style="text-decoration:none; color:inherit;">A</a>
    <div>
      <div class="cd-brand-title">AUTOPASS · EXPLICACION DE CODIGO</div>
      <div class="cd-brand-sub">ARCHIVO: {EscaparTextoHtml(Archivo["path"])}</div>
    </div>
  </div>
  <nav class="cd-topnav">
    <a href="{PrefijoRaiz}index.html">INICIO</a>
    <a href="{PrefijoRaiz}index.html#/{EscaparTextoHtml(Archivo["path"])}">VER EN ARBOL</a>
    <a href="{PrefijoRaiz}base-de-datos.html">BASE DE DATOS</a>
  </nav>
</header>

<div class="cd-layout" style="grid-template-columns: 1fr; max-width: 1100px; margin: 0 auto; padding: 24px 20px;">
  <main class="cd-main" style="padding: 0;">
    <div class="cd-crumb">
      <a href="{PrefijoRaiz}index.html">INICIO</a> / 
      <a href="{PrefijoRaiz}index.html#/section/{EscaparTextoHtml(Archivo.get('section', ''))}">{EscaparTextoHtml(TituloSeccion)}</a> / 
      {EscaparTextoHtml(Archivo["path"])}
    </div>

    <div class="cd-title">
      <span class="cd-path">{EscaparTextoHtml(Archivo["path"])}</span>
      <span class="cd-chip lang-{EscaparTextoHtml(Archivo.get('lang', ''))}">{EscaparTextoHtml(EtiquetasLenguajes.get(Archivo.get('lang', ''), Archivo.get('lang', '')))}</span>
      {'<span class="cd-chip chip-analizado">ANALIZADO</span>' if Archivo.get('analizado') else ''}
      <span class="cd-chip">{len(Archivo.get('symbols', []))} SIMBOLOS</span>
    </div>

    <div class="cd-checklist" data-file="{EscaparTextoHtml(Archivo['path'])}">
      <span class="cd-checklist-title">ESTADO DE LECTURA:</span>
      <label class="cd-check-label cd-check-leido">
        <input type="checkbox" data-status-key="leido">
        <span class="cd-check-box"></span>
        <span>LEIDO</span>
      </label>
      <label class="cd-check-label cd-check-entendido">
        <input type="checkbox" data-status-key="entendido">
        <span class="cd-check-box"></span>
        <span>ENTENDIDO</span>
      </label>
      <label class="cd-check-label cd-check-ok">
        <input type="checkbox" data-status-key="ok">
        <span class="cd-check-box"></span>
        <span>OK</span>
      </label>
    </div>

    <div class="cd-purpose">{EnriquecerGlosarioHtml(Archivo.get("purpose", "SIN DESCRIPCION REGISTRADA."))}</div>
    {HtmlPropositoOriginal}
    {HtmlInfoRelaciones}

    <div class="cd-sectionbox">
      <h2>RELACIONES DEL ARCHIVO</h2>
      <div class="cd-relations">
        <div class="cd-rel-card">
          <h3>DEPENDE DE (IMPORTA)</h3>
          <div class="cd-rel-list">
            {EnlacesDependencias}
          </div>
        </div>
        <div class="cd-rel-card">
          <h3>ES USADO POR</h3>
          <div class="cd-rel-list">
            {EnlacesUsadoPor}
          </div>
        </div>
      </div>
    </div>

    <div class="cd-sectionbox">
      <h2>{TituloSeccionSimbolos}</h2>
      {HtmlSimbolos}
    </div>

    <div class="cd-note">
      EXPLICACION GENERADA DESDE EL CODIGO FUENTE REAL DE AUTOPASS. VISOR INTERACTIVO EN <a href="{PrefijoRaiz}index.html#/{EscaparTextoHtml(Archivo["path"])}">index.html#/{EscaparTextoHtml(Archivo["path"])}</a>.
    </div>
  </main>
</div>
<script src="{PrefijoRaiz}assets/tooltip.js"></script>
</body>
</html>'''

        ArchivoDestino.write_text(ContenidoPagina, encoding="utf-8")

    print(f"PAGINAS HTML ESTATICAS GENERADAS: {len(Datos['files'])} EN EXPLICACION DE CODIGO/archivos/")



def inventario(seccion: str) -> None:
    """Lista los archivos y simbolos que un lote de analisis debe cubrir.

    Uso: _tools/generate_code_docs.py --inventario <seccion|<ruta de archivo>>
    """
    files = collect()
    if seccion in {"all", "*"}:
        elegidos = files
    elif any(f["path"] == seccion for f in files):
        elegidos = [f for f in files if f["path"] == seccion]
    else:
        elegidos = [f for f in files if f["section"] == seccion]
    if not elegidos:
        print(f"Sin archivos para '{seccion}'.")
        print("Secciones:", ", ".join(s[0] for s in SECTIONS))
        return
    print(f"LOTE: {seccion}  ->  {len(elegidos)} archivo(s), "
          f"{sum(len(f['symbols']) for f in elegidos)} simbolo(s)\n")
    for f in elegidos:
        print(f"## {f['path']}")
        for s in f["symbols"]:
            print(f"   - [{s['kind']}] {s['name']}")
        if not f["symbols"]:
            print("   (sin simbolos de nivel superior)")
        print()


def cobertura() -> None:
    """Informa qué simbolos del inventario todavia no tienen analisis.

    No escribe data.js: sirve para verificar lotes en paralelo.
    Uso: _tools/generate_code_docs.py --cobertura [seccion]
    """
    analisis = load_analysis()
    files = collect()
    filtro = sys.argv[2] if len(sys.argv) > 2 else None
    filtros = [x for x in filtro.split(",") if x] if filtro else []
    tot_falta = 0
    cubiertos = 0
    tot_sim = 0
    print(f"Analisis cargado: {len(analisis)} archivo(s)\n")

    def coincide(f: dict) -> bool:
        if not filtros:
            return True
        return f["section"] in filtros or any(f["path"].startswith(x) or f["path"] == x for x in filtros)

    for f in files:
        if not coincide(f):
            continue
        sims = analisis.get(f["path"], {}).get("simbolos") or {}
        if f["section"] == "css":
            falta = []
        else:
            falta = [s["name"] for s in f["symbols"] if s.get("qual") not in sims and s["name"] not in sims]
        tiene = f["path"] in analisis
        cubiertos += len(f["symbols"]) - len(falta)
        tot_falta += len(falta)
        tot_sim += len(f["symbols"])
        if falta or not tiene:
            print(f"  FALTA  {f['path']}  ({len(falta)}/{len(f['symbols'])} simbolos)")
    print()
    print(f"Simbolos con analisis: {cubiertos}/{tot_sim}")
    print(f"Simbolos pendientes: {tot_falta}")


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--inventario":
        inventario(sys.argv[2])
    elif sys.argv[1:2] == ["--cobertura"]:
        cobertura()
    else:
        main()
