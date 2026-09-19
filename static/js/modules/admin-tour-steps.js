/**
 * AUTOPASS - PASOS DE LOS TOURS DE ADMINISTRACION (v9.9.9)
 * Submodulo de admin-tour.js: definicion pura de los recorridos guiados
 * operativos para Personal Staff, Administradores Locales y Generales.
 */

// Tour 1: Monitoreo CCTV & Control de Operaciones ALPR
export const adminLiveTourSteps = [
    {
        selector: '#tab-live .stats-row, #tab-live',
        title: 'Indicadores de Disponibilidad en Vivo',
        text: 'Muestra la disponibilidad actual de plazas para Autos, Motos y Camionetas en la sucursal en tiempo real.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => { if (window.switchTab) window.switchTab('live'); }
    },
    {
        selector: 'a[href="/monitoreo"], #tab-live',
        title: 'Monitor Externo Multi-Cámara',
        text: 'Acceso directo para abrir la consola de video CCTV dedicada en una pantalla o monitor secundario.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('live'); }
    },
    {
        selector: '#monitor-tab-occ, #tab-live .table-container, #tab-live',
        title: 'Vehículos Estacionados & Permanencia',
        text: 'Tabla de vehículos físicamente presentes en la sucursal, con hora de ingreso, tiempo de permanencia y cobro acumulado.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            if (window.switchTab) window.switchTab('live');
            if (window.switchMonitorTab) {
                const btn = document.querySelector('button[onclick*="switchMonitorTab(\'occ\'"]');
                if (btn) window.switchMonitorTab('occ', btn);
            }
        }
    },
    {
        selector: '#monitor-tab-logs, #tab-live',
        title: 'Últimos Movimientos & Lectura ALPR',
        text: 'Consola con el historial en vivo de entradas y salidas procesadas por el motor de visión artificial EasyOCR.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            if (window.switchTab) window.switchTab('live');
            if (window.switchMonitorTab) {
                const btn = document.querySelector('button[onclick*="switchMonitorTab(\'logs\'"]');
                if (btn) window.switchMonitorTab('logs', btn);
            }
        }
    },
    {
        selector: '#manual-ops-content, #tab-live .monitoring-side, #tab-live',
        title: 'Panel de Ingreso Manual',
        text: 'Permite registrar un ingreso o egreso manual si una patente no es legible por la cámara ALPR, cobrar la estadía en caja o anular un registro.',
        align: 'left',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('live'); }
    },
    {
        selector: 'button[onclick*="openBarrier"]',
        title: 'Apertura Manual de Barreras (MQTT)',
        text: 'Botón de pulso directo MQTT para enviar la orden de apertura a las barreras físicas de Entrada o Salida en emergencias.',
        align: 'left',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('live'); }
    }
];

// Tour 2: Gestión de Reservas & Cobros Administrativos
export const adminReservationsTourSteps = [
    {
        selector: '#tab-admin-reservations .kpi-grid, #tab-admin-reservations',
        title: 'Métricas de Reservas del Sistema',
        text: 'Resumen general de reservas en la sucursal: total acumulado y reservas pendientes de inicio en el día.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => { if (window.switchTab) window.switchTab('admin-reservations'); }
    },
    {
        selector: '#tab-admin-reservations .header-actions, #tab-admin-reservations',
        title: 'Filtros y Búsqueda de Reservas',
        text: 'Filtrá el listado por estado (Pendientes, Activas, Completadas, Canceladas) o buscá por patente o cliente.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('admin-reservations'); }
    },
    {
        selector: '#tab-admin-reservations table, #tab-admin-reservations',
        title: 'Consola de Comprobantes & Fechas',
        text: 'Consultá el desglose de estadías (Hora, Día, Semana, Quincena, Mes), fechas de inicio/fin, importe total y estado del pago.',
        align: 'top',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('admin-reservations'); }
    },
    {
        selector: '#tab-admin-reservations .btn-confirm-payment, #tab-admin-reservations table',
        title: 'Confirmación Manual de Pago',
        text: 'Si el cliente abona su reserva en la caja física o por transferencia, usá este botón para validar el cobro y activar la reserva al instante.',
        align: 'left',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('admin-reservations'); }
    },
    {
        selector: '#tab-admin-reservations .btn-cancel-reservation, #tab-admin-reservations table',
        title: 'Cancelación Administrativa',
        text: 'Permite anular una reserva. El sistema calculará automáticamente si corresponde reembolso según el tiempo restante y devolverá el saldo a la billetera virtual.',
        align: 'left',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('admin-reservations'); }
    }
];

// Tour 3: Administración de Usuarios y Permisos
export const adminUsersTourSteps = [
    {
        selector: '#tab-users .user-stats-collapsible, #tab-users',
        title: 'Resumen de Usuarios & Roles',
        text: 'Gestión centralizada de cuentas de la plataforma: desglosado entre clientes, empleados staff, administradores de sucursal y administradores generales.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => { if (window.switchTab) window.switchTab('users'); }
    },
    {
        selector: '#tab-users .header-actions, #tab-users',
        title: 'Buscador y Filtro por Rol',
        text: 'Filtrá el personal o los clientes por nombre, correo electrónico, DNI o nivel de rol.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('users'); }
    },
    {
        selector: 'button[onclick*="showCreateUserModal"], .btn-new-user-mobile-fix',
        title: 'Alta de Nuevo Usuario / Personal',
        text: 'Pulsá este botón para dar de alta un nuevo cliente o crear cuentas para empleados y operadores de sucursal.',
        align: 'left',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('users'); }
    },
    {
        selector: '#tab-users table, #tab-users',
        title: 'Directorio & Billetera Virtual',
        text: 'Revisá la información detallada de cada cuenta, incluyendo el saldo acreditado en la billetera virtual y sus puntos acumulados.',
        align: 'top',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('users'); }
    },
    {
        selector: '#tab-users table button[onclick*="toggleUserBlock"], #tab-users table',
        title: 'Bloqueo / Activación de Cuentas',
        text: 'Hacé click sobre el icono de candado para suspender preventivamente o reactivar el acceso de un usuario a la red AutoPass.',
        align: 'left',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('users'); }
    },
    {
        selector: '#tab-users table button[onclick*="openBalanceModal"], #tab-users table button[onclick*="balance"], #tab-users table',
        title: 'Ajuste de Saldo en Billetera Virtual',
        text: 'Cargá o acreditá saldo a favor de cualquier cliente para permitirle estacionar mediante lectura de patente ALPR sin necesidad de efectivo.',
        align: 'left',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('users'); }
    },
    {
        selector: '#tab-users table button[onclick*="openEditUserModal"], #tab-users table button[onclick*="openPasswordModal"], #tab-users table',
        title: 'Edición de Perfil & Permisos',
        text: 'Restablecé la contraseña de un usuario o modificá su rol para asignarlo como operador de sucursal o administrador.',
        align: 'left',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('users'); }
    }
];

// Tour 4: Analítica Financiera & Exportación de Datos
export const adminFinanceTourSteps = [
    {
        selector: '#tab-finance .kpi-grid-4, #tab-finance',
        title: 'Métricas Financieras Ejecutivas',
        text: 'Tablero financiero con la recaudación neta, total reembolsado, cantidad de tickets emitidos y ticket promedio.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => { if (window.switchTab) window.switchTab('finance'); }
    },
    {
        selector: '#tab-finance .finance-breakdown-row, #tab-finance',
        title: 'Desglose por Canal de Cobro',
        text: 'Comparativa contable entre ingresos generados por estadías por hora/ALPR vs reservas abonadas por el sitio web.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => { if (window.switchTab) window.switchTab('finance'); }
    },
    {
        selector: '#tab-finance .header-actions, #tab-finance',
        title: 'Filtros por Período, Método de Pago & Vehículo',
        text: 'Filtrá el reporte por período (Hoy, Semana, Mes, Año), discriminá entre pagos Digitales o en Caja, y categorizá por Auto, Moto o Camioneta.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('finance'); }
    },
    {
        selector: '#tab-finance table, #tab-finance',
        title: 'Auditoría Contable de Transacciones',
        text: 'Historial unificado de todos los movimientos de caja, cobros de estadías, cancelaciones de reservas y recargas de saldo.',
        align: 'top',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('finance'); }
    },
    {
        selector: 'button[onclick*="exportFinanceData"], #tab-finance .btn-outline',
        title: 'Exportación de Reportes a CSV',
        text: 'Descargá la plantilla de datos auditados en formato CSV para conciliar con sistemas contables o exportar a Microsoft Excel.',
        align: 'left',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('finance'); }
    }
];

// Tour 5: Centro de Soporte & Tickets de Clientes
export const adminTicketsTourSteps = [
    {
        selector: '#tab-tickets .kpi-grid, #tab-tickets',
        title: 'Métricas de Tickets de Soporte',
        text: 'Bandeja de entrada centralizada: total de tickets, consultas pendientes, en proceso y resueltas.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => { if (window.switchTab) window.switchTab('tickets'); }
    },
    {
        selector: '#tab-tickets .header-actions, #tab-tickets',
        title: 'Buscador en Tiempo Real y Filtros',
        text: 'Filtrá los tickets por estado (Pendiente, En Proceso, Resuelto) y buscá instantáneamente por cliente, correo o asunto.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('tickets'); }
    },
    {
        selector: '#tab-tickets table, #tab-tickets',
        title: 'Tabla de Atenciones a Clientes',
        text: 'Listado completo de mensajes e incidencias registradas por los usuarios desde la app o el sitio web.',
        align: 'top',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('tickets'); }
    },
    {
        selector: '#tickets-admin-table-body button[onclick*="openTicketAnswerModal"], #tab-tickets table',
        title: 'Respuesta Directa & Notificación Push',
        text: 'Hacé click en "RESPONDER" para enviar una respuesta al cliente. La notificación le llegará en tiempo real por WebSockets a su dispositivo.',
        align: 'left',
        interactive: true,
        beforeShow: () => { if (window.switchTab) window.switchTab('tickets'); }
    }
];

// Tour 6: Sucursales, Pisos, Tarifas & Cámaras IP
export const adminBranchesSettingsTourSteps = [
    {
        selector: '#tab-branches table, #tab-branches, #tab-settings',
        title: 'Red de Sucursales & Geolocalización',
        text: 'Administración de sedes físicas, datos operativos, mapa Leaflet interactivo y asignación de administradores locales.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            const rol = localStorage.getItem('rol');
            if (rol === 'admin' && window.switchTab) window.switchTab('branches');
            else if (window.switchTab) window.switchTab('settings');
        }
    },
    {
        selector: '#set-section-floors, .settings-floors, #tab-branches, #tab-settings',
        title: 'Gestión Multi-Piso (ParkingFloor)',
        text: 'Permite configurar múltiples niveles por sucursal definiendo capacidades independientes de plazas para Autos, Motos y Camionetas.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            const rol = localStorage.getItem('rol');
            if (rol === 'admin' && window.switchTab) window.switchTab('branches');
            else if (window.switchTab) {
                window.switchTab('settings');
                if (window.switchSettingsTab) {
                    const btn = document.querySelector('button[onclick*="switchSettingsTab(\'floors\'"]');
                    if (btn) window.switchSettingsTab('floors', btn);
                }
            }
        }
    },
    {
        selector: '#set-section-rates, .rates-form-grid, #tab-settings',
        title: 'Matriz de Tarifas Trimodales',
        text: 'Configuración del motor de precios. Podés ajustar las tarifas por Hora, Día, Semana, Quincena y Mes para Auto, Moto y Camioneta.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            if (window.switchTab) window.switchTab('settings');
            if (window.switchSettingsTab) {
                const btn = document.querySelector('button[onclick*="switchSettingsTab(\'rates\'"]');
                if (btn) window.switchSettingsTab('rates', btn);
            }
        }
    },
    {
        selector: '#set-section-monitoring, .cameras-config-table, #tab-settings',
        title: 'Control de Cámaras IP & ALPR',
        text: 'Vinculá las URLs de streaming RTSP/MJPEG de las cámaras IP por puerta (Entrada/Salida) y encendé o apagá el motor ALPR.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            if (window.switchTab) window.switchTab('settings');
            if (window.switchSettingsTab) {
                const btn = document.querySelector('button[onclick*="switchSettingsTab(\'monitoring\'"]');
                if (btn) window.switchSettingsTab('monitoring', btn);
            }
        }
    }
];

// Tour 7: Recorrido Completo e Integral del Dashboard
export const adminFullDashboardTourSteps = [
    ...adminLiveTourSteps,
    ...adminReservationsTourSteps.slice(1),
    ...adminUsersTourSteps.slice(1),
    ...adminFinanceTourSteps.slice(1),
    ...adminTicketsTourSteps.slice(1),
    ...adminBranchesSettingsTourSteps.slice(1)
];