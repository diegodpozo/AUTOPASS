# AUTOPASS

Solución empresarial para la gestión de estacionamientos que combina **Visión Artificial (ALPR)**, **Arquitectura Limpia (Clean Architecture)** y un **Frontend Premium** de alto impacto.

## Últimas Actualizaciones (v9.34.87 - Octubre 2026)
- **Soporte usuario↔admin (A1–A6)**: listado "Mis consultas" para el cliente, XSS cerrado en el chat, estado "En Revisión", tickets terminales bloqueados y rediseño de la pantalla de Ayuda (`profile-help.js`, `support_service.py`).
- **Auditorías cerradas**: validaciones (`AUDITORIA_VALIDACIONES` V1–V12: DNI duplicado, logos, rangos, patentes Mercosur BR/UY/PY, adjuntos por chunks, solapamiento de patente en reservas) y autorización (`AUDITORIA_RBAC` R1–R10: scoping por sucursal, PII minimizada, rol operativo en WS).
- **Escalabilidad de listados**: helper DRY `static/js/modules/list-pagination.js` (`renderCappedList`/`renderPaginatedList`) aplicado a consultas, vouchers, notificaciones, promociones, tickets y reservas admin (paginador de 10 con card de altura estable).
- **Mejoras BD (Neon)**: fechas varchar→timestamp, 11 CheckConstraints, UNIQUE de settings y 4 FKs de sucursal (`b2f4e8c1a9d7`), con backups previos.
- **Gestión Integral de Reservas para Admins**: Módulo completo en Dashboard (`routes/admin/reservations.py`, `dashboard-reservations.js`) con búsqueda multi-criterio (cliente, email, DNI, patente, ID, sucursal), filtros por estado (`PENDIENTE_PAGO`, `PAGADA`, `EN_USO`, `FINALIZADA`, `CANCELADA`), tipo de vehículo, rango de fechas y sucursal. Permite crear reservas a nombre de usuarios, editar fechas/patente/tipo con **ajuste financiero automático** (cobra/reembolsa la diferencia), confirmar pagos con método configurable (`DIGITAL`, `CAJA`, `MERCADOPAGO`, `SALDO`) y cancelar con reembolso simular/aplicar.
- **Soporte de `tipo_vehiculo` y `metodo_pago` en Reservas**: Nuevos campos en `Reservation` y migraciones Alembic (`a4c8d2e3f5b6` y `d3b7e1a9c2f0`). Validación de disponibilidad respetando cupos por tipo de vehículo (`capacidad_reservas_autos/motos/camionetas`).
- **Suite de 813 Tests Automáticos**: **813 pruebas passing en 57 archivos de test** (`pytest`), cubriendo OAuth, Checkout Mercado Pago, Admin Reservations, ALPR, Notificaciones, Rate Limiting, Tiempo Virtual, Soporte y Lógica de Aforo.
- **Login social (OAuth 2.0 - Google + Facebook)**: Botones "Continuar con..." en login y registro. Usuarios nuevos completan DNI y teléfono en una modal (nombre/email precargados) y quedan logueados sin contraseña; usuarios existentes entran directo por su correo. Config vía `GOOGLE_OAUTH_CLIENT_ID/SECRET` y `FACEBOOK_OAUTH_CLIENT_ID/SECRET` (`services/oauth_service.py`).
- **Pagos manuales en efectivo (`CAJA`)**: El operador puede registrar el pago de una estadía en efectivo desde el monitoreo (`metodo=CAJA` en `POST /v1/access/pay-stay`); los reportes financieros desglosan la recaudación por método (`recaudado_efectivo` / `recaudado_digital`) con KPIs dedicados en el dashboard.
- **Re-impresión de vouchers**: Los tickets de canje de puntos pueden reimprimirse desde el portal de usuario.
- **PWA instalable & Standalone Layout**: Manifest + Service Worker en scope raíz (`autopass-v3`) con página `/instalar` y forzado de layout desktop en PWA instalada (`standalone.css`).
- **Pagos con Mercado Pago (v9.14.0)**: Checkout Pro por redirección para abonar **reservas** y **estadías en curso** sin tocar el saldo de la billetera; confirmación por retorno (`/success|pending|failure`) y webhook (`services/mercadopago_service.py`, tabla `mercadopago_payments`).
- **Soporte con adjuntos**: Los tickets de soporte aceptan archivos jpg/jpeg/png/gif/webp/pdf (máx. 1 MB) en mensajes del hilo, con modal responsive y scrolleable.
- **Performance & Caché**: Índices de base de datos (migración `49a240f0fc25`) y caché TTL en memoria (`core/cache.py`) para tarifas.
- **Setup Modernizado & Neon/Postgres**: Instalador (`setup_backend.bat`) con `requirements.txt` modularizado. Base online en Neon São Paulo (`sa-east-1`, ~100 ms).
- **OCR Dual (v9.10.0)**: Motor OCR **RapidOCR ONNX** como primario (compatible con Python 3.14+) con fallback a **PaddleOCR**. Saludo personalizado en monitor ALPR ("¡BIENVENIDO!" / "¡HASTA LUEGO!").

## Versiones Previas
- **v9.20.0-v9.34.87**: Reservas admin (edición con ajuste financiero automático, descuentos en caja, notificaciones tipificadas), auditorías de seguridad/validaciones/RBAC, escalabilidad de listados, rediseño de Ayuda y mejoras UX del portal.
- **v9.14.0-v9.14.1**: Mercado Pago Checkout Pro, Pagos en efectivo CAJA, KPIs financieros, PWA instalable.
- **v9.13.0**: Motor OCR lazy/opcional (RapidOCR/PaddleOCR) y estadísticas OCR (`/estadisticas-ocr`).
- **v9.12.0**: Notificaciones de usuario, permisos de sucursal para `local_admin`, soporte visual del admin.
- **v9.8.x**: Migraciones con Alembic, suite de tests expandida.
- **v9.6.0**: Modularización ALPR (`alpr/`), Servicio de Reportes (`ReportService`), Rutas de Sistema (`routes/system/`).
- **v9.5.0**: Ocupación solo física, cortesía 10 min, multi-piso, trimodal.
- **v9.0.0**: Real-time WebSocket, Settings Monitoring, Video Stream.

## Arquitectura del Sistema

El proyecto sigue una estructura modular diseñada para el escalamiento y la alta mantenibilidad:

- **`core/`**: Infraestructura crítica (Configuración, Seguridad JWT/RBAC, DB, MQTT).
- **`models/` & `schemas/`**: Capa de datos organizada por dominios (Usuarios, Parking, Reservas). Se incluye la nueva entidad **`ParkingFloor`**.
- **`routes/`**: Controladores de API y entrega de Vistas HTML.
- **`services/`**: Inteligencia de negocio y procesos de fondo (Facturación trimodal, aforo por reservas, WebSockets).
- **`templates/`**: Frontend modular basado en Jinja2 con componentes reutilizables.

## Características Principales

- **Multi-Piso Nativo**: Capacidad para definir N niveles por sucursal con cupos de autos/motos/camionetas configurables (trimodal).
- **Facturación Diferenciada**: Motor de precios que aplica descuentos automáticos para motocicletas.
- **Multi-Sucursal Pro**: Gestión independiente de tarifas, aforo y personal por sucursal.
- **Visión Artificial Híbrida**: Reconocimiento de patentes y códigos QR en tiempo real.
- **RBAC (Role Based Access Control)**: Jerarquía de permisos (Admin, Local Admin, Staff, User).

## Inicio Rápido

1. **Instalar dependencias:** `setup_backend.bat` (configura también la base online y el `.env`).
2. **Arrancar Servidor:** `run_server.bat`
3. **Arrancar Cámaras:** Configurar IPs desde Dashboard (Ajustes > Monitoreo) y presionar Play (▶). El backend inicia el servicio automáticamente.

## Tecnologías

- **Backend:** FastAPI (Python 3.14)
- **Base de Datos:** SQLAlchemy — **Neon/Postgres en la nube** (compartida entre varias PC, región `sa-east-1`, por defecto) o SQLite local (opcional, aislado)
- **Frontend:** Vanilla JS (ES6 Modules), CSS Moderno, Jinja2, Chart.js.
- **IoT:** Paho-MQTT (ESP32) + Serie USB / pyserial (Arduino Uno).
- **IA:** OpenCV + RapidOCR ONNX / PaddleOCR (lectura de patentes) + detección QR y consenso de votos.
