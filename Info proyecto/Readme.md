# AUTOPASS

Solución empresarial para la gestión de estacionamientos que combina **Visión Artificial (ALPR)**, **Arquitectura Limpia (Clean Architecture)** y un **Frontend Premium** de alto impacto.

## Últimas Actualizaciones (v9.9.0+ - Agosto 2026)
- **Setup Modernizado**: Instalador etapeado (`setup_backend.bat`) con dependencias divididas en `requirements-core.txt` (obligatorio) y `requirements-ai.txt` (opcional). Output limpio sin spameo de pip.
- **Migración a Neon/Postgres (sa-east-1)**: La base online pasó de Turso/Oregón (~1200 ms/query) a **Neon en São Paulo** con latencia medida de ~100 ms (12× más rápida). Configurable vía `DATABASE_URL=postgresql://...` en `.env` (fallback a SQLite local).
- **OCR Dual (v9.10.0)**: Motor OCR **RapidOCR ONNX** como primario (compatible con Python 3.14+) con fallback a **PaddleOCR** para Python < 3.14. Reemplaza por completo a EasyOCR.

## Versiones Previas
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

- **Multi-Piso Nativo**: Capacidad para definir N niveles por sucursal con cupos de autos/motos configurables.
- **Facturación Diferenciada**: Motor de precios que aplica descuentos automáticos para motocicletas.
- **Multi-Sucursal Pro**: Gestión independiente de tarifas, aforo y personal por sucursal.
- **Visión Artificial Híbrida**: Reconocimiento de patentes y códigos QR en tiempo real.
- **RBAC (Role Based Access Control)**: Jerarquía de permisos (Admin, Local Admin, Staff, User).

## Inicio Rápido

1. **Instalar dependencias:** `setup_backend.bat` (configura también la base online y el `.env`).
2. **Arrancar Servidor:** `run_server.bat`
3. **Arrancar Cámaras:** Configurar IPs desde Dashboard (Ajustes > Monitoreo) y presionar Play (▶). El backend inicia el servicio automáticamente.

## Tecnologías

- **Backend:** FastAPI (Python 3.13)
- **Base de Datos:** SQLAlchemy — SQLite local o **Neon/Postgres en la nube** (compartida entre varias PC, región `sa-east-1`)
- **Frontend:** Vanilla JS (ES6 Modules), CSS Moderno, Jinja2, Chart.js.
- **IoT:** Paho-MQTT.
- **IA:** OpenCV + RapidOCR ONNX / PaddleOCR (lectura de patentes) + detección QR y consenso de votos.
