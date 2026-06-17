# Estado del Proyecto: AUTOPASS (Actualizado 2026-06-17)

### 🚀 Hitos Recientes (Junio 2026) - Versión 9.1.5 (UX/UI Refinement & RBAC)
- [x] **Monitoring UI Redesign**: Rediseño total de la pestaña de Monitoreo en Ajustes usando un layout de grilla bimodal, iconografía técnica mejorada y tipografía monospace para fuentes de video.
- [x] **Financial Filter Expansion**: Integración de "Camionetas" en los filtros de reportes financieros para auditoría trimodal completa.
- [x] **RBAC UI Hardening**: Restricción física de opciones de "Administrador General" para usuarios con rol de Admin Local en filtros y edición de roles.
- [x] **Trimodal Pricing Model**: Expansión del motor de tarifas para soportar una tercera categoría: **Camionetas**, con configuración independiente de hora, día, semana y mes.
- [x] **Enhanced Vehicle Registration**: Actualización de los formularios de registro (Mis Vehículos y Quick Add) para permitir la selección manual de Camionetas, incluyendo nueva iconografía (`fa-truck-pickup`).
- [x] **Real-time Occupancy WebSocket**: Implementación de un sistema de notificaciones push para el aforo, eliminando el polling y permitiendo actualizaciones instantáneas en el dashboard.

### 🚀 Hitos Previos (Junio 2026) - Versión 9.0.0 (Real-time & Settings Overhaul)
- [x] **Settings Monitoring Tab**: Migración de la configuración de cámaras IP y control de servicios ALPR a una nueva pestaña dedicada en Ajustes.
- [x] **WebSocket Notification Service**: Nueva arquitectura desacoplada para gestionar eventos asíncronos en el backend.
- [x] **UI Tab Fix**: Corrección de la estructura HTML en ajustes para evitar solapamiento de secciones.
- [x] **Video Stream Visibility Fix**: Corregida la lógica de opacidad y carga de frames en el Dashboard para asegurar la visualización inmediata.
- [x] **Dynamic WS Token Validation**: Implementada validación de token en el cliente WS para diferenciar visualizadores de nodos ALPR.

### 🚀 Hitos Previos (Junio 2026) - Versión 8.9.5 (Video Stream Optimization)
- [x] **Placeholder Refinement**: Implementación de placeholders transparentes para evitar errores de carga (404) antes de la conexión del stream.
- [x] **Camera Remote Control**: Implementación de gestión de servicios ALPR desde el UI (Start/Stop/Config).
- [x] **Dynamic Video Source**: Soporte para cambio de IPs de cámaras en tiempo real sin reiniciar el servidor.
- [x] **Settings Expansion**: Extensión del modelo de base de datos para soportar configuraciones de texto (IPs, URLs).
- [x] **Form Normalization**: Estandarización de inputs de reserva y vehículos (48px height, 0.9rem font).
- [x] **Minimalist Alerts**: Rediseño de alertas de confirmación sin marcos internos y con jerarquía financiera mejorada.
- [x] **Direct Swap Vehicles**: Nueva interacción para el registro de flota eliminando colapsables por intercambio de componentes.
- [x] **Unified Visual Style**: Sincronización estética total entre el formulario de inicio ("Quick Add") y la gestión de flota.
- [x] **Clean Empty States**: Estados vacíos simplificados con iconos neutros (#444) y sin ruido visual.

### 🛠️ Arquitectura Actual (v9.1.5)
- **Capas**: Clean Architecture con Servicios de Notificación Asíncronos.
- **Seguridad**: JWT + RBAC (Endurecido en UI).
- **Frontend**: Dashboard Premium, Vanilla JS, CSS Glassmorphism, WebSockets (Video/Aforo).
- **Modelo Vehicular**: Trimodal (Auto, Moto, Camioneta).

### 📊 Cobertura de Funcionalidades
- **Gestión**: Multi-sucursal y Multi-piso con restricciones de seguridad por sede.
- **Facturación**: Trimodal (Auto/Moto/Camioneta) con filtros avanzados de canal de pago.
- **Monitoreo**: ALPR en vivo con gestión centralizada y aforo real-time.
