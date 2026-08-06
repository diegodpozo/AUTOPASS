# AUTOPASS

Solución empresarial para la gestión de estacionamientos que combina **Visión Artificial (ALPR)**, **Arquitectura Limpia (Clean Architecture)** y un **Frontend Premium** de alto impacto.

## Últimas Actualizaciones (v9.9.0 - Agosto 2026)
- **Mosaicos de Google Maps gratuitos sin API Key**: Capas `Google Calles`, `Google Satélite`, `Google Híbrido` y `CartoDB Oscuro` con selector multicapa en la landing y el CRUD de sucursales.
- **Indicadores Circulares de Disponibilidad (Status Dots)**: Estado luminoso discriminado para Auto, Moto y Camioneta en los mapas.
- **Centro de Notificaciones Rediseñado**: Chips de filtro, borrado individual/masivo y conteo exacto (`DELETE /v1/user/profile/notifications/{id}` y `clear-read`).
- **Sistema de Tickets de Soporte (`SupportTicket`)**: Endpoints `/v1/user/support-tickets` y `/v1/admin/support-tickets` con aislamiento por sucursal y real-time.

## Últimas Actualizaciones Previas (v9.8.x - Agosto 2026)
- **Migraciones con Alembic**: Control de versiones de esquema (`alembic/`, migración inicial `c833a3129266_initial_schema`) y pipeline CI/CD en `.github/workflows/ci.yml`.
- **Suite de Tests expandida**: 15+ pruebas automatizadas en `tests/` (auth con TestClient, ALPR, cortesía 10 min, notificaciones, soporte).

## Últimas Actualizaciones Previas (v9.6.0 - Julio 2026)
- **Modularización ALPR (`alpr/`)**: Refactorización del servicio de visión artificial monolítico en el paquete `alpr/` (`config`, `preprocessor`, `video_streamer`, `ws_client`, `ocr_engine`, `runner`) manteniendo compatibilidad total.
- **Servicio de Reportes (`ReportService`)**: Abstracción de analítica financiera y transacciones en `services/report_service.py`, aligerando `routes/reports.py` (Clean Architecture).
- **Rutas de Sistema (`routes/system/`)**: División del módulo `system.py` en submódulos especializados (`common.py`, `health.py`, `cameras.py`, `video.py`).

## Últimas Actualizaciones Previas (v9.5.0 - Julio 2026)
- **Monitoreo DVR CCTV Dinámico**: Nuevo visor de cámaras en grilla auto-ajustable de tamaño uniforme.
- **Identificadores HUD**: Indicador técnico explícito de la función de cada cámara en el visor.
- **Panel Flotante de DVR**: Reemplazo de la botonera superior por un panel flotante semi-transparente.

## Últimas Actualizaciones Previas (v9.3.0)
- **FAB "Nueva Reserva" en Perfil**: Botón flotante con animación expansiva, oculto en la tab "inicio". Reemplaza botones redundantes en cada tab del perfil.
- **Monitoreo Limpio**: Cards de aforo sin texto repetido ("Tot. Disp." eliminado). Barras de progreso con colores dinámicos (verde/amarillo/naranja/rojo).
- **Worker Robusto**: DB sessions con `try/finally` para evitar `QueuePool limit` errors. Pool size aumentado a 10 con overflow 20.
- **Ocupación Solo Física (v9.5+)**: El aforo refleja únicamente vehículos físicamente presentes; el ALPR (entrada/salida) maneja el conteo para todos los vehículos. Las reservas no horarias no pre-ocupan plaza.
- **Restricción de Anticipación Selectiva**: Solo las reservas por hora requieren anticipación (1 hora configurable vía `RESERVA_HORA_MIN_SEGUNDOS`). Las de período largo no tienen restricción.
- **Gestión Vertical (Multi-Piso)**: Soporte para múltiples niveles por sucursal con control de aforo independiente.
- **Soporte Trimodal (Autos/Motos/Camionetas)**: Identificación y facturación diferenciada para motocicletas y camionetas con tarifas reducidas.
- **RBAC Operativo Refinado**: Separación estricta de roles; Super Admin (Gestión de Red) y Local Admin (Control total de sucursal/pisos/tarifas).

## Arquitectura del Sistema

El proyecto sigue una estructura modular diseñada para el escalamiento y la alta mantenibilidad:

- **`core/`**: Infraestructura crítica (Configuración, Seguridad JWT/RBAC, DB, MQTT).
- **`models/` & `schemas/`**: Capa de datos organizada por dominios (Usuarios, Parking, Reservas). Se incluye la nueva entidad **`ParkingFloor`**.
- **`routes/`**: Controladores de API y entrega de Vistas HTML.
- **`services/`**: Inteligencia de negocio y procesos de fondo (Facturación trimodal, aforo por reservas, WebSockets).
- **`templates/`**: Frontend modular basado en Jinja2 con componentes reutilizables.

## Características Principales

- **Multi-Piso Nativo**: Capacidad para definir N niveles por sucursal con cupos de autos/motos configurables.
- **Facturación Diferenciada**: Motor de precios que aplica descuentos automáticos para motocicletas.
- **Multi-Sucursal Pro**: Gestión independiente de tarifas, aforo y personal por sucursal.
- **Visión Artificial Híbrida**: Reconocimiento de patentes y códigos QR en tiempo real.
- **RBAC (Role Based Access Control)**: Jerarquía de permisos (Admin, Local Admin, Staff, User).

## Inicio Rápido

1. **Instalar dependencias:** `setup_backend.bat`
2. **Arrancar Servidor:** `run_server.bat`
3. **Arrancar Cámaras:** Configurar IPs desde Dashboard (Ajustes > Monitoreo) y presionar Play (▶). El backend inicia el servicio automáticamente.

## Tecnologías

- **Backend:** FastAPI (Python 3.14)
- **Base de Datos:** SQLAlchemy (SQLite)
- **Frontend:** Vanilla JS (ES6 Modules), CSS Moderno, Jinja2, Chart.js.
- **IoT:** Paho-MQTT.
- **IA:** OpenCV + EasyOCR + PyTorch (Deep Learning).
