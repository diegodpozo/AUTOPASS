# Estado del Proyecto: AUTOPASS (Actualizado 2026-06-03)

### 🚀 Hitos Recientes (Junio 2026) - Versión 7.8.0 (Interactive Maps & Admin Power)
- [x] **Gestión Administrativa Pro**:
    *   Edición completa de información de usuarios y personal desde el dashboard.
    *   Validación de seguridad RBAC para cambios de jerarquía y sucursal.
    *   Normalización automática de identidad (DNI sin puntos/espacios).
- [x] **Mapa de Disponibilidad Inteligente**:
    *   **Heat Map en Vivo**: Indicadores de ocupación real (Dorado/Naranja/Rojo) basados en aforo.
    *   **Geolocalización Asistida**: Botón de ubicación para encontrar la sucursal más cercana (Haversine).
    *   **Reserva One-Click**: Redirección inteligente desde el mapa al perfil con precarga de datos.
- [x] **Hardening de Sesión y Login**:
    *   Normalización de emails (lowercase/strip) en el proceso de autenticación.
    *   Corrección de bug de DNIs duplicados en la inicialización de base de datos.
- [x] **Unificación Terminológica**:
    *   Migración total de "Sede" a **"Sucursal"** en toda la interfaz (Admin y Cliente) y documentación.

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
