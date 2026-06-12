# AUTOPASS

Solución empresarial para la gestión de estacionamientos que combina **Visión Artificial (ALPR)**, **Arquitectura Limpia (Clean Architecture)** y un **Frontend Premium** de alto impacto.

## Últimas Actualizaciones (v8.2.0)
- **Gestión Vertical (Multi-Piso)**: Soporte para múltiples niveles por sucursal con control de aforo independiente.
- **Soporte Bimodal (Autos/Motos)**: Identificación y facturación diferenciada para motocicletas con tarifas reducidas.
- **RBAC Operativo Refinado**: Separación estricta de roles; Super Admin (Gestión de Red) y Local Admin (Control total de sucursal/pisos/tarifas).
- **UI de Gestión Unificada**: Nueva tabla de niveles que integra la Planta Baja (PB) con pisos superiores para una administración centralizada.

## Arquitectura del Sistema

El proyecto sigue una estructura modular diseñada para el escalamiento y la alta mantenibilidad:

- **`core/`**: Infraestructura crítica (Configuración, Seguridad JWT/RBAC, DB, MQTT).
- **`models/` & `schemas/`**: Capa de datos organizada por dominios (Usuarios, Parking, Reservas). Se incluye la nueva entidad **`ParkingFloor`**.
- **`routes/`**: Controladores de API y entrega de Vistas HTML.
- **`services/`**: Inteligencia de negocio y procesos de fondo (Facturación bimodal).
- **`templates/`**: Frontend modular basado en Jinja2 con componentes reutilizables.

## Características Principales

- **Multi-Piso Nativo**: Capacidad para definir N niveles por sucursal con cupos de autos/motos configurables.
- **Facturación Diferenciada**: Motor de precios que aplica descuentos automáticos para motocicletas.
- **Multi-Sucursal Pro**: Gestión independiente de tarifas, aforo y personal por sucursal.
- **Visión Artificial Híbrida**: Reconocimiento de patentes y códigos QR en tiempo real.
- **RBAC (Role Based Access Control)**: Jerarquía de permisos (Admin, Local Admin, Staff, User).

## Inicio Rápido

1. **Instalar dependencias:** `pip install -r requirements.txt`
2. **Inicializar DB:** `python init_db.py` (Maneja migraciones automáticas).
3. **Arrancar Servidor:** `run_server.bat`
4. **Arrancar Cámaras:** `run_camera_entry.bat` y `run_camera_exit.bat`.

## Tecnologías

- **Backend:** FastAPI (Python 3.9+)
- **Base de Datos:** SQLAlchemy (SQLite/PostgreSQL)
- **Frontend:** Vanilla JS, CSS Moderno, Jinja2, Chart.js.
- **IoT:** Paho-MQTT.
- **IA:** OpenCV + EasyOCR (Deep Learning).
