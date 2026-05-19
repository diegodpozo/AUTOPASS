# Estado del Proyecto: ParkingTech (Actualizado 2026-05-17)

### 🚀 Hitos Recientes (Mayo 2026) - Versión 6.4.0
- [x] **Soporte Multi-Sede Avanzado**:
    *   Implementación de **RBAC Descentralizado**: Roles específicos para Administradores de Sede (`local_admin`) y Empleados de Sede (`staff`).
    *   **Aislamiento Total de Datos**: Los administradores locales solo gestionan usuarios, reservas y finanzas de su propia sucursal.
    *   **Tarifario Independiente**: Cada Punto AutoPass puede configurar sus propios precios por hora, día, semana, etc.
- [x] **Reglas de Negocio Estrictas**:
    *   Implementación de **Anticipación Mínima de 2 Horas** para todas las reservas (Frontend & Backend).
    *   Ajuste de **Margen de Gracia de 2 Horas** para limpieza de reservas pendientes, evitando cancelaciones preventivas accidentales.
- [x] **Seguridad y Roles (RBAC)**:
    *   Ampliación de permisos para el rol **Empleado (Staff)**: ahora pueden visualizar logs de acceso y auditoría visual.
    *   Blindaje del Dashboard: manejo de errores silencioso para evitar fallos de carga ante falta de permisos financieros.
- [x] **Command Center 2.5 (UX Refactor)**:
    *   Arquitectura colapsable integral.
    *   Nuevo modal de **EVENTO** con placeholder "IMAGEN NO DISPONIBLE" y UI minimalista.
    *   Reestructuración de sidebar operativa.
- [x] **Servicio Híbrido ALPR + QR**: El motor de visión ahora detecta códigos QR y patentes simultáneamente con optimización de CPU (10 FPS).
- [x] **Seguridad de Reservas**: Restricción de cancelación para reservas en curso (solo administradores pueden cancelar estadías activas).
- [x] **Corrección de Tarifas**: Sincronización exacta de cálculos de fechas y montos para estadías largas (semana/mes).

### 🏗️ Arquitectura Professional (v6.2)
- [x] **Validación QR Robusta**: El sistema ahora prioriza la base de datos sobre el contenido del QR para evitar discrepancias de patente.
- [x] **Limpieza de Reservas**: Ajuste en la lógica de "auto-cleanup" para permitir reservas inmediatas sin cancelación por falta de pago previo.
- [x] **Optimización ALPR**: Reducción de carga en el backend mediante streaming controlado y supresión de logs de FFmpeg.

### 🌟 Funcionalidades Core
- **ALPR Digital Audit**: Auditoría física con fotos reales vinculadas a cada evento de entrada/salida.
- **Centro de Comando Operativo**: Monitoreo en vivo, control de barreras y servicios del sistema.
- **Pase Digital Híbrido**: Acceso mediante reconocimiento de patente o escaneo de código QR (Pase Digital).
