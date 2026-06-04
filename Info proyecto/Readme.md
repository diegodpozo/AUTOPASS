# AUTOPASS

Solución empresarial para la gestión de estacionamientos que combina **Visión Artificial (ALPR)**, **Arquitectura Limpia (Clean Architecture)** y un **Frontend Premium** de alto impacto.

## Últimas Actualizaciones (v7.9.0)
- **UI/UX Refined**: Panel de inicio minimalista, popups de mapa premium y lógica de ocupación cualitativa.
- **Optimización de Assets**: Eliminación de imágenes duplicadas y estandarización de rutas en minúsculas.
- **Persistencia Visual**: Mensajes de guía permanentes en mapas para mejorar la navegación del usuario.
- **Estabilidad**: Resolución de conflictos de atributos en la carga de configuraciones (IMAGE_DIR).
## Arquitectura del Sistema

El proyecto sigue una estructura modular diseñada para el escalamiento y la alta mantenibilidad:

- **`core/`**: Infraestructura crítica (Configuración, Seguridad JWT/RBAC, DB, MQTT).
- **`models/` & `schemas/`**: Capa de datos organizada por dominios (Usuarios, Parking, Reservas).
- **`routes/`**: Controladores de API y entrega de Vistas HTML.
- **`services/`**: Inteligencia de negocio y procesos de fondo.
- **`templates/`**: Frontend modular basado en Jinja2 con componentes reutilizables.

## Características Principales

- **Multi-Sucursal Nativo**: Gestión independiente de tarifas, aforo y personal por sucursal.
- **Visión Artificial Híbrida**: Reconocimiento de patentes y códigos QR en tiempo real.
- **RBAC (Role Based Access Control)**: Jerarquía de permisos (Admin, Local Admin, Staff, User).
- **Fidelización**: Sistema de puntos AutoPass por consumo.
- **IoT Ready**: Comunicación MQTT integrada para el control de hardware (barreras).

## Inicio Rápido

1. **Instalar dependencias:** `pip install -r requirements.txt`
2. **Inicializar DB:** `python init_db.py`
3. **Arrancar Servidor:** `run_server.bat`
4. **Arrancar Cámaras:** `run_camera_entry.bat` y `run_camera_exit.bat` (en terminales separadas).

## Tecnologías

- **Backend:** FastAPI (Python 3.9+)
- **Base de Datos:** SQLAlchemy (SQLite/PostgreSQL)
- **Frontend:** Vanilla JS, CSS Moderno, Jinja2, Chart.js.
- **IoT:** Paho-MQTT.
- **IA:** OpenCV + EasyOCR (Deep Learning).
