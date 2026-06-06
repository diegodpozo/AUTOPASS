# Estado del Proyecto: AUTOPASS (Actualizado 2026-06-05)

### 🚀 Hitos Recientes (Junio 2026) - Versión 8.0.0 (Smart Finance & Flexible Cancellations)
- [x] **Motor Financiero Pro 2.0**:
    *   **Paginación SQL Nativa**: Refactorización de reportes usando `UNION ALL` y paginación en base de datos para escalabilidad masiva.
    *   **Recaudación Neta**: Implementación de lógica contable que resta reembolsos y cancelaciones del total bruto.
    *   **Trazabilidad Granular**: Adición de la columna `monto_reembolsado` y `fecha_pago` en la base de datos para auditoría exacta de devoluciones y transacciones.
    *   **FIX: Reportes Financieros**: Corrección de la lógica de fechas para usar el momento de la transacción (`fecha_pago`) en lugar del inicio de reserva, garantizando precisión diaria.
    *   **KPIs de Eficiencia**: Nuevas métricas de "Tasa de Cancelación" e "Incumplimiento de Reservas" para análisis de abandono.
    *   **Ingresos Proyectados**: Cálculo en tiempo real de la deuda acumulada de vehículos actualmente en el predio.
- [x] **Gestión de Accesos & Ocupación**:
    *   **Cancelación de Estadía**: Nueva funcionalidad "Cancelar Estadía" con regla de **15 minutos de cortesía** (sin cargo) y validación de deuda excedida.
    *   **Multi-Ingreso de Reservas**: Soporte para que reservas de largo plazo (Día, Semana, Mes) puedan entrar y salir múltiples veces durante su vigencia.
    *   **Optimización de Ocupación**: Lista de vehículos estacionados ahora con unicidad de patente y orden cronológico (ingresos recientes primero).
- [x] **Política de Cancelación Inteligente**:
    *   **Reembolsos Proporcionales**: Sistema automático que devuelve el dinero exacto del tiempo no utilizado (para todos los tipos de estadía).
    *   **Bloqueo de Seguridad**: Restricción técnica que impide cancelar reservas si el vehículo se encuentra físicamente dentro del estacionamiento.
    *   **Ajuste de Fidelización**: Deducción prorrateada de puntos AutoPass en caso de reembolso.
- [x] **UI de Transparencia Financiera**:
    *   **Previsualización de Reembolso**: Modal de confirmación que muestra al usuario el monto exacto a recuperar antes de cancelar.
    *   **Dashboard Expandido**: Nueva cuadrícula de 5 columnas con trazabilidad visual de reembolsos (filas en rojo con montos negativos).

### 🚀 Hitos Previos (Junio 2026) - Versión 7.9.0 (UI Refinement & Asset Optimization)

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
