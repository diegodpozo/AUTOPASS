# AUTOPASS

Solución empresarial para la gestión de estacionamientos que combina **Visión Artificial (ALPR)**, **Arquitectura Limpia (Clean Architecture)** y un **Frontend Premium** de alto impacto.

## Últimas Actualizaciones (v9.2.0)
- **Aforo Inteligente con Reservas**: Las reservas de Día/Semana/Quincena/Mes descuentan la plaza del aforo al pagar y la liberan solo al vencer o cancelar. El cliente puede entrar y salir libremente sin perder su lugar.
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

1. **Instalar dependencias:** `pip install -r requirements.txt`
2. **Parche EasyOCR:** `python scripts/patch_bidi.py` (Corrige error de importación de `bidi`).
3. **Inicializar DB:** `python init_db.py` (Maneja migraciones automáticas).
3. **Arrancar Servidor:** `run_server.bat`
4. **Arrancar Cámaras:** Configurar IPs desde Dashboard (Ajustes > Monitoreo) y presionar Play (▶). El backend inicia el servicio automáticamente.

## Tecnologías

- **Backend:** FastAPI (Python 3.9+)
- **Base de Datos:** SQLAlchemy (SQLite/PostgreSQL)
- **Frontend:** Vanilla JS, CSS Moderno, Jinja2, Chart.js.
- **IoT:** Paho-MQTT.
- **IA:** OpenCV + EasyOCR (Deep Learning).
