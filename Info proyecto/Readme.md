# AUTOPASS

Solución empresarial para la gestión de estacionamientos que combina **Visión Artificial (ALPR)**, **Arquitectura Limpia (Clean Architecture)** y un **Frontend Premium** de alto impacto.

## Últimas Actualizaciones (v9.14.1+ - Septiembre 2026)
- **Pagos manuales en efectivo (`CAJA`)**: El operador puede registrar el pago de una estadía en efectivo desde el monitoreo (`metodo=CAJA` en `POST /v1/access/pay-stay`); los reportes financieros desglosan la recaudación por método (`recaudado_efectivo` / `recaudado_digital`) con KPIs dedicados en el dashboard.
- **Re-impresión de vouchers**: Los tickets de canje de puntos pueden reimprimirse desde el portal de usuario.
- **PWA instalable**: Manifest + Service Worker en scope raíz (`autopass-v2`) con página `/instalar`; el botón de instalación está oculto en el monitor multicámara (fuera del alcance de la PWA).
- **Pagos con Mercado Pago (v9.14.0)**: Checkout Pro por redirección para abonar **reservas** y **estadías en curso** sin tocar el saldo de la billetera; confirmación por retorno (`/success|pending|failure`) y webhook, con aplicación idempotente (`services/mercadopago_service.py`, tabla `mercadopago_payments`).
- **Canje de puntos por descuentos**: `RedemptionTicket` con voucher (código de 16 caracteres + QR, válido 30 días) o `descuento_reserva` aplicado automáticamente al pagar la próxima reserva.
- **Soporte con adjuntos**: Los tickets de soporte aceptan archivos jpg/jpeg/png/gif/webp/pdf (máx. 1 MB) en mensajes del hilo, con notificaciones de lectura para el admin.
- **Performance & Caché**: Índices de base de datos (migración `49a240f0fc25`) y caché TTL en memoria (`core/cache.py`) para tarifas.
- **Setup Modernizado**: Instalador (`setup_backend.bat`) con dependencias organizadas por secciones (Core / DB / Seguridad / CV / IA-OCR) dentro de un único `requirements.txt`, con markers por versión de Python para numpy y para `paddleocr`/`paddlepaddle` (solo Python < 3.14). Output limpio sin spameo de pip y aborta mostrando el error real si algo falla.
- **Migración a Neon/Postgres (sa-east-1)**: La base online pasó de Turso/Oregón (~1200 ms/query) a **Neon en São Paulo** con latencia medida de ~100 ms (12× más rápida). Configurable vía `DATABASE_URL=postgresql://...` en `.env` (fallback a SQLite local).
- **OCR Dual (v9.10.0)**: Motor OCR **RapidOCR ONNX** como primario (compatible con Python 3.14+) con fallback a **PaddleOCR** para Python < 3.14. Reemplaza por completo a EasyOCR.

## Versiones Previas
- **v9.13.0**: Motor OCR lazy/opcional (RapidOCR/PaddleOCR) y estadísticas OCR (`/estadisticas-ocr`).
- **v9.12.0**: Notificaciones de usuario, permisos de sucursal para `local_admin`, soporte visual del admin.
- **v9.8.x**: Migraciones con Alembic, suite de tests expandida (24 pruebas).
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
- **Base de Datos:** SQLAlchemy — SQLite local o **Neon/Postgres en la nube** (compartida entre varias PC, región `sa-east-1`)
- **Frontend:** Vanilla JS (ES6 Modules), CSS Moderno, Jinja2, Chart.js.
- **IoT:** Paho-MQTT (ESP32) + Serie USB / pyserial (Arduino Uno).
- **IA:** OpenCV + RapidOCR ONNX / PaddleOCR (lectura de patentes) + detección QR y consenso de votos.
