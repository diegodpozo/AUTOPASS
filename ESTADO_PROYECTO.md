# Estado del Proyecto: AUTOPASS (Actualizado 2026-06-02)

### 🚀 Hitos Recientes (Junio 2026) - Versión 7.7.0 (Sucursal UI & Notification Hardening)
- [x] **Unificación Terminológica**:
    *   Migración total de "Sede" a **"Sucursal"** en toda la interfaz (Admin y Cliente) y documentación.
- [x] **Rediseño de Notificaciones (Toasts)**:
    *   Sistema **Glassmorphism** en la esquina superior derecha con iconos dinámicos y auto-cierre.
- [x] **Gestión de Sucursales (Puntos AutoPass)**:
    *   [x] CRUD completo con logos circulares y sin marcos.
    *   [x] **Geolocalización Nativa**: Soporte para coordenadas (Lat/Lng) por sucursal.
    *   [x] **Selector de Mapa Interactivo**: Picker Leaflet integrado en el alta de sucursales.
    *   [x] **Buscador de Direcciones**: Integración con API Nominatim para autocompletado de coordenadas.
    *   [x] Configuración de horario simplificada con selector de 24hs integrado.
    *   [x] Carga dinámica de sucursales en formularios de reserva y promociones.
- [x] **Mapa de Red Dinámico**:
    *   [x] API pública para consumo de puntos geolocalizados.
    *   [x] Renderizado automático de sucursales en la landing page con popups informativos.
- [x] **Hardening de UX en Dashboard**:
    *   [x] Eliminación de parpadeo (flicker) de contenido no autorizado mediante inyección de clase de rol inmediata.
    *   [x] Simplificación de lista de usuarios (eliminación de colapsables innecesarios).
    *   [x] Restricción visual total de Reservas y Monitoreo para el Admin Global.
- [x] **RBAC Reforzado**:
    *   Bloqueo automático de sucursal para Administradores Locales en la creación de promociones.

### 🚀 Hitos Previos (Junio 2026) - Versión 7.6.5 (Branch Management & UI Unification)
- [x] **Gestión de Sucursales (Puntos AutoPass)**:
    - [x] CRUD completo de sucursales con aislamiento de datos.
    - [x] Soporte para carga de logos locales (sistema de archivos).
    - [x] Configuración de horarios flexible (24hs o rangos específicos).
- [x] **Refactorización de UI Administrativa**:
    - [x] Unificación visual de módulos (Promociones y Sucursales).
    - [x] Implementación de `switch-premium` animado para estados.
    - [x] Sistema de acciones contextuales (reveal on hover) para tablas premium.
    - [x] Previsualización dinámica de imágenes antes de la carga.
- [x] **Motor ALPR Avanzado**:
    - [x] Procesamiento asíncrono con EasyOCR y colas de prioridad.
    - [x] Pre-procesamiento de imagen con OpenCV (Filtros, CLAHE, Adaptive Threshold).
    - [x] Algoritmo de consenso por votación (elimina falsos positivos).
- [x] **Hardening de Interfaz y Sesión**:
    - [x] Etiquetas dinámicas de cargo y sucursal (ej: "Administrador Morón") en tiempo real.
    - [x] Inicialización resiliente del Dashboard con modo debug integrado.
    - [x] Sincronización de sucursal en el proceso de Login y localStorage.

### 🛠️ Arquitectura Actual
- **Capas**: Clean Architecture con aislamiento por sucursal.
- **Frontend**: Dashboard Premium (Gold & Black) con módulos ES6 y CSS por capas.
- **Seguridad**: JWT + RBAC con persistencia de rol en el ciclo de vida del DOM.
- **ALPR Engine**: Procesamiento asíncrono con colas y validación por votación.

### 📊 Cobertura de Funcionalidades
- **Seguridad**: RBAC con 4 niveles (Admin, Local Admin, Staff, User).
- **Multi-Sucursal**: Aislamiento total de datos, tarifas y aforo por sucursal.
- **Fidelización**: Sistema de puntos AutoPass con historial y canje de beneficios.
- **Accesos**: ALPR híbrido (Patente + QR) con auditoría visual.

### 📅 Próximos Pasos (Roadmap v7.x)
- [ ] Integración real con Mercado Pago (Webhooks).
- [ ] Dashboard de Super-Admin con mapas de calor de ocupación multi-sucursal.
- [ ] App Móvil nativa consumiendo los nuevos esquemas modulares.
- [ ] Implementación de WebSockets para notificaciones de entrada/salida en tiempo real.
