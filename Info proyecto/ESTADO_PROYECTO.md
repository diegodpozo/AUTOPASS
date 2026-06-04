# Estado del Proyecto: AUTOPASS (Actualizado 2026-06-04)

### 🚀 Hitos Recientes (Junio 2026) - Versión 7.9.0 (UI Refinement & Asset Optimization)
- [x] **Optimización de Assets y Estructura**:
    *   Renombramiento de carpetas de recursos a minúsculas (`static/images/inicio`) para estandarización.
    *   Consolidación de imágenes de fallback: el sistema ahora usa assets de `static` para registros sin captura real, eliminando duplicidad en `captured_images`.
- [x] **Experiencia de Mapa Premium (v2.0)**:
    *   **Popups Rediseñados**: Nueva estética Dark & Gold con bordes suavizados y botones de reserva integrados.
    *   **Lógica de Ocupación Refinada**: Mensajes cualitativos dinámicos ("Alta disponibilidad", "Lugares limitados", "Sucursal Completa") sin exponer contadores técnicos.
    *   **Limpieza de UI**: Eliminación del marcador default "AUTOPASS HQ" para un inicio de mapa más limpio enfocado en sucursales.
    *   **Guía Visual**: Implementación de *hints* flotantes permanentes en el mapa de Perfil e Inicio para asistir al usuario.
- [x] **Refactorización de Panel de Inicio**:
    *   Restructuración completa de la pestaña "Inicio" del cliente para máxima simplicidad.
    *   Eliminación de widgets secundarios (Mi Progreso, Contadores redundantes).
    *   Nueva tarjeta de acción principal **"RESERVAR AHORA"** con icono descriptivo y acceso directo a utilidades financieras.

### 🚀 Hitos Previos (Junio 2026) - Versión 7.8.5 (Deep Modularization & Clean Logic)
- [x] **Arquitectura de Rutas Micro-Modular**:
    *   Refactorización total de `routes/admin.py`, `routes/user.py` y `routes/parking.py` en paquetes de sub-módulos especializados.
- [x] **Desacoplamiento de Comunicaciones**:
    *   Migración de emails hardcodeados a plantillas Jinja2 en `templates/emails/`.
- [x] **Configuración Centralizada Pro**:
    *   Parámetros de IA (ALPR) movidos al entorno (.env).

### 🛠️ Arquitectura Actual
- **Capas**: Clean Architecture con aislamiento por sucursal.
- **Frontend**: Dashboard Premium (Gold & Black) con módulos ES6 y CSS por capas.
- **Assets**: Organización optimizada en `static/` con fallback inteligente en Backend.
- **Seguridad**: JWT + RBAC con persistencia de rol en el ciclo de vida del DOM.

### 📊 Cobertura de Funcionalidades
- **Seguridad**: RBAC con 4 niveles (Admin, Local Admin, Staff, User).
- **Multi-Sucursal**: Aislamiento total de datos, tarifas y aforo por sucursal.
- **Fidelización**: Sistema de puntos AutoPass con historial y canje de beneficios.
- **Accesos**: ALPR híbrido (Patente + QR) con auditoría visual y fallback de imágenes.

### 📅 Próximos Pasos (Roadmap v7.x)
- [ ] Integración real con Mercado Pago (Webhooks).
- [ ] Dashboard de Super-Admin con mapas de calor de ocupación multi-sucursal.
- [ ] App Móvil nativa consumiendo los nuevos esquemas modulares.
- [ ] Implementación de WebSockets para notificaciones de entrada/salida en tiempo real.
