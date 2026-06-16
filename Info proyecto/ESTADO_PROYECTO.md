# Estado del Proyecto: AUTOPASS (Actualizado 2026-06-16)

### 🚀 Hitos Recientes (Junio 2026) - Versión 8.8.5 (UI/UX Refinement)
- [x] **Form Normalization**: Estandarización de inputs de reserva y vehículos (48px height, 0.9rem font, centrado total).
- [x] **Minimalist Alerts**: Rediseño de alertas de confirmación sin marcos internos y con jerarquía financiera mejorada.
- [x] **Direct Swap Vehicles**: Nueva interacción para el registro de flota eliminando colapsables por intercambio de componentes.
- [x] **Unified Visual Style**: Sincronización estética total entre el formulario de inicio ("Quick Add") y la gestión de flota.
- [x] **Clean Empty States**: Estados vacíos simplificados con iconos neutros (#444) y sin ruido visual.

### 🚀 Hitos Previos (Junio 2026) - Versión 8.7.5 (UX/UI Map Enhancement)
- [x] **Smart Map Overlay**: Cuadro informativo dinámico que muestra nombre y dirección de sucursal solo al seleccionarla.
- [x] **Ubicación Predictiva**: Nueva leyenda flotante "estacioná en tu zona" con manito animada (FontAwesome 6) para guiar al usuario hacia la geolocalización.
- [x] **Normalización de Direcciones**: Algoritmo de formateo automático para asegurar comas entre número y localidad, y visualización en Title Case.
- [x] **Sincronización UX**: Experiencia de mapa idéntica entre Landing Page y Dashboard de Usuario (incluyendo corrección de overflow en cards).
- [x] **Gestión Tarifaria Segura**: Interfaz simplificada con botón unificado "EDITAR/APLICAR" y validación previa mediante modal con resumen detallado.

### 🚀 Hitos Previos (Junio 2026) - Versión 8.7.0 (Finanzas y Configuración Avanzada)
- [x] **Filtros Financieros Avanzados**: Nuevos selectores por \"Método de Pago\" (Digital vs Caja) y \"Tipo de Vehículo\" (Auto/Moto) para KPIs y gráficos.
- [x] **Historial de Pagos Inteligente**: Distinción clara entre \"PAGO DIGITAL\" (App/QR) y \"PAGO EN CAJA\" (Manual).
- [x] **Formato de Fechas**: Estandarización a formato legible (DD/MM/YYYY HH:MM) en tablas de auditoría.
- [ ] Mapas de calor de ocupación por piso en el dashboard.
- [ ] Implementación de WebSockets para actualizaciones de aforo instantáneas sin recarga.
- [ ] Exportación de reportes detallados por nivel/piso.

### 🛠️ Arquitectura Actual (v8.7.5)
- **Capas**: Clean Architecture.
- **Seguridad**: JWT + RBAC.
- **Frontend**: Dashboard Premium, Vanilla JS, CSS Glassmorphism, Chart.js.

### 📊 Cobertura de Funcionalidades
- **Gestión**: Multi-sucursal y Multi-piso.
- **Facturación**: Bimodal (Auto/Moto) con filtros avanzados de canal de pago.
- **Monitoreo**: ALPR en vivo con auditoría detallada.
