# AUTOPASS

Solución empresarial para la gestión de estacionamientos que combina **Visión Artificial (ALPR)**, **Arquitectura Limpia (Clean Architecture)** y un **Frontend Premium** de alto impacto.

## Últimas Actualizaciones (v9.5.0 - Julio 2026)
- **Fix ALPR "ya está en la sede"**: Verificación corregida de duplicados de entrada.
- **Cortesía 10 min en ALPR y manual**: Salida sin costo dentro de los primeros 10 minutos.
- **Ocupación solo física**: Las reservas no horarias ya no pre-ocupan plaza. El aforo refleja solo autos físicamente presentes.
- **Virtual Time Service**: Sistema de tiempo offset para testing sin alterar el reloj real.

## Últimas Actualizaciones Previas (v9.4.0 - Julio 2026)
- **Monitoreo DVR CCTV Dinámico**: Nuevo visor de cámaras en grilla auto-ajustable de tamaño uniforme.
- **Identificadores HUD**: Indicador técnico explícito de la función de cada cámara en el visor.
- **Panel Flotante de DVR**: Reemplazo de la botonera superior por un panel flotante semi-transparente.

## Últimas Actualizaciones Previas (v9.3.0)
- **FAB "Nueva Reserva" en Perfil**: Botón flotante con animación expansiva, oculto en la tab "inicio". Reemplaza botones redundantes en cada tab del perfil.
- **Monitoreo Limpio**: Cards de aforo sin texto repetido ("Tot. Disp." eliminado). Barras de progreso con colores dinámicos (verde/amarillo/naranja/rojo).
- **Worker Robusto**: DB sessions con `try/finally` para evitar `QueuePool limit` errors. Pool size aumentado a 10 con overflow 20.
- **Aforo Inteligente con Reservas**: Las reservas de Día/Semana/Quincena/Mes descuentan la plaza del aforo al iniciar el período (vía worker), no al pagar. La plaza se libera solo al vencer o cancelar.
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

- **Backend:** FastAPI (Python 3.9+)
- **Base de Datos:** SQLAlchemy (SQLite/PostgreSQL)
- **Frontend:** Vanilla JS, CSS Moderno, Jinja2, Chart.js.
- **IoT:** Paho-MQTT.
- **IA:** OpenCV + EasyOCR (Deep Learning).
