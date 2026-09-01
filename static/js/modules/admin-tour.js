/**
 * AUTOPASS - TOUR DE ADMINISTRACION Y GUIA OPERATIVA (v9.9.9)
 * Modulo ES6 especializado en recorridos guiados e instruccion operativa
 * para Personal Staff, Administradores Locales y Administradores Generales.
 */

// --- 1. CONFIGURACION DE TOURS OPERATIVOS ESPECIFICOS ---

// Tour 1: Monitoreo CCTV & Control de Operaciones ALPR
const adminLiveTourSteps = [
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
const adminReservationsTourSteps = [
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
const adminUsersTourSteps = [
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
const adminFinanceTourSteps = [
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
const adminTicketsTourSteps = [
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
const adminBranchesSettingsTourSteps = [
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
const adminFullDashboardTourSteps = [
    ...adminLiveTourSteps,
    ...adminReservationsTourSteps.slice(1),
    ...adminUsersTourSteps.slice(1),
    ...adminFinanceTourSteps.slice(1),
    ...adminTicketsTourSteps.slice(1),
    ...adminBranchesSettingsTourSteps.slice(1)
];

// --- 2. VARIABLES DE ESTADO DEL TOUR ---

let activeTourSteps = [];
let currentAdminStepIndex = 0;
let adminTourOverlay = null;
let adminTourTooltip = null;
let adminTourArrow = null;
let positioningToken = 0;
let isPositioningActive = false;
let isAdminTourActive = false;
let activeResizeObserver = null;

// --- 3. CREACION DE ELEMENTOS DEL DOM ---

function createAdminTourElements() {
    const existing = document.getElementById('autopass-admin-tour-overlay');
    if (existing) existing.remove();

    adminTourOverlay = document.createElement('div');
    adminTourOverlay.id = 'autopass-admin-tour-overlay';

    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, 'svg');
    svg.id = 'autopass-admin-tour-svg';
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';

    const path = document.createElementNS(svgNS, 'path');
    path.setAttribute('fill', 'rgba(3, 7, 18, 0.75)');
    path.setAttribute('fill-rule', 'evenodd');

    const highlightRect = document.createElementNS(svgNS, 'rect');
    highlightRect.id = 'autopass-admin-tour-highlight-rect';
    highlightRect.setAttribute('fill', 'none');
    highlightRect.setAttribute('stroke', '#dfba6b');
    highlightRect.setAttribute('stroke-width', '2');
    highlightRect.setAttribute('rx', '10');
    highlightRect.setAttribute('ry', '10');
    highlightRect.style.display = 'none';

    svg.appendChild(path);
    svg.appendChild(highlightRect);
    adminTourOverlay.appendChild(svg);
    document.body.appendChild(adminTourOverlay);

    // Tooltip
    adminTourTooltip = document.createElement('div');
    adminTourTooltip.id = 'autopass-admin-tour-tooltip';
    adminTourTooltip.className = 'admin-tour-tooltip';
    adminTourOverlay.appendChild(adminTourTooltip);

    // Arrow
    adminTourArrow = document.createElement('div');
    adminTourArrow.id = 'autopass-admin-tour-arrow';
    adminTourArrow.className = 'admin-tour-arrow';
    adminTourOverlay.appendChild(adminTourArrow);

    adminTourTooltip.innerHTML = `
        <div class="admin-tour-header">
            <span id="admin-tour-badge" class="admin-tour-badge"><i class="fas fa-gauge-high"></i> PASO 1 DE 5</span>
            <button id="admin-tour-end" class="btn-admin-tour-end" title="Cerrar tour"><i class="fas fa-xmark"></i> Omitir</button>
        </div>
        <div id="admin-tour-title" class="admin-tour-title"></div>
        <div id="admin-tour-text" class="admin-tour-text"></div>
        <div class="admin-tour-footer">
            <button id="admin-tour-prev" class="btn-admin-tour-prev"><i class="fas fa-arrow-left"></i> Anterior</button>
            <div class="admin-tour-buttons-group">
                <button id="admin-tour-next" class="btn-admin-tour-next">Siguiente <i class="fas fa-arrow-right"></i></button>
            </div>
        </div>
    `;

    document.getElementById('admin-tour-prev').addEventListener('click', prevAdminTourStep);
    document.getElementById('admin-tour-next').addEventListener('click', nextAdminTourStep);
    document.getElementById('admin-tour-end').addEventListener('click', endAdminTour);

    window.addEventListener('resize', handleAdminWindowReposition, { passive: true });
    window.addEventListener('scroll', handleAdminWindowReposition, { passive: true });
    window.addEventListener('keydown', handleAdminTourKeydown);
}

function handleAdminTourKeydown(e) {
    if (!isAdminTourActive || !adminTourOverlay || adminTourOverlay.style.display === 'none') return;
    if (e.key === 'Escape') endAdminTour();
    else if (e.key === 'ArrowRight') nextAdminTourStep();
    else if (e.key === 'ArrowLeft') prevAdminTourStep();
}

function updateAdminSvgCutout(rect) {
    const svg = document.getElementById('autopass-admin-tour-svg');
    if (!svg) return;
    const path = svg.querySelector('path');
    const highlightRect = document.getElementById('autopass-admin-tour-highlight-rect');
    if (!path) return;

    const w = window.innerWidth;
    const h = window.innerHeight;

    if (!rect || rect.width === 0 || rect.height === 0) {
        path.setAttribute('d', `M 0,0 L ${w},0 L ${w},${h} L 0,${h} Z`);
        if (highlightRect) highlightRect.style.display = 'none';
        return;
    }

    const padding = 8;
    const x = rect.left - padding;
    const y = rect.top - padding;
    const width = rect.width + (padding * 2);
    const height = rect.height + (padding * 2);
    const r = 10;

    const innerW = Math.max(0, width - (r * 2));
    const innerH = Math.max(0, height - (r * 2));

    const outerPath = `M 0,0 h ${w} v ${h} h ${-w} z`;
    const cutoutPath = `
        M ${x + r},${y}
        h ${innerW}
        a ${r},${r} 0 0 1 ${r},${r}
        v ${innerH}
        a ${r},${r} 0 0 1 ${-r},${r}
        h ${-innerW}
        a ${r},${r} 0 0 1 ${-r},${-r}
        v ${-innerH}
        a ${r},${r} 0 0 1 ${r},${-r}
        z
    `.trim().replace(/\s+/g, ' ');

    path.setAttribute('d', `${outerPath} ${cutoutPath}`);

    if (highlightRect) {
        highlightRect.setAttribute('x', x);
        highlightRect.setAttribute('y', y);
        highlightRect.setAttribute('width', width);
        highlightRect.setAttribute('height', height);
        highlightRect.style.display = 'block';
    }
}

function handleAdminWindowReposition() {
    if (!adminTourOverlay || adminTourOverlay.style.display === 'none' || currentAdminStepIndex === -1) return;
    if (isPositioningActive) return;
    isPositioningActive = true;
    requestAnimationFrame(() => {
        repositionActiveAdminStep();
        isPositioningActive = false;
    });
}

function getVisibleTarget(selector) {
    if (!selector) return null;
    const parts = selector.split(',').map(s => s.trim());
    for (const sel of parts) {
        const elements = document.querySelectorAll(sel);
        for (const el of elements) {
            if (el && el.getBoundingClientRect) {
                const rect = el.getBoundingClientRect();
                const isVisible = (el.offsetWidth > 0 || el.offsetHeight > 0) && rect.width > 0 && rect.height > 0;
                if (isVisible) return el;
            }
        }
    }
    return document.querySelector(parts[0]);
}

function repositionActiveAdminStep() {
    if (currentAdminStepIndex < 0 || currentAdminStepIndex >= activeTourSteps.length) return;
    const step = activeTourSteps[currentAdminStepIndex];
    if (!step) return;
    const target = getVisibleTarget(step.selector);
    if (!target) return;

    const rect = target.getBoundingClientRect();

    if (step.center || (rect.width === 0 && rect.height === 0)) {
        updateAdminSvgCutout(null);
        adminTourTooltip.style.position = 'fixed';
        adminTourTooltip.style.left = '50%';
        adminTourTooltip.style.top = '50%';
        adminTourTooltip.style.transform = 'translate(-50%, -50%)';
        if (adminTourArrow) {
            adminTourArrow.classList.remove('active');
            adminTourArrow.style.display = 'none';
        }
        return;
    }

    updateAdminSvgCutout(rect);

    adminTourTooltip.style.position = 'fixed';
    adminTourTooltip.style.transform = '';

    const padding = 8;
    const targetLeft = rect.left - padding;
    const targetTop = rect.top - padding;
    const targetWidth = rect.width + (padding * 2);
    const targetHeight = rect.height + (padding * 2);

    const tooltipWidth = adminTourTooltip.offsetWidth || 380;
    const tooltipHeight = adminTourTooltip.offsetHeight || 180;

    const vw = window.innerWidth;
    const vh = window.innerHeight;

    let effectiveAlign = step.align || 'bottom';
    if (vw < 680 && (effectiveAlign === 'left' || effectiveAlign === 'right')) {
        effectiveAlign = (targetTop + targetHeight / 2 > vh / 2) ? 'top' : 'bottom';
    }

    let ttLeft = targetLeft + (targetWidth / 2) - (tooltipWidth / 2);
    let ttTop = targetTop + targetHeight + 14;

    if (effectiveAlign === 'top') {
        ttTop = targetTop - tooltipHeight - 14;
    } else if (effectiveAlign === 'left') {
        ttLeft = targetLeft - tooltipWidth - 14;
        ttTop = targetTop + (targetHeight / 2) - (tooltipHeight / 2);
    } else if (effectiveAlign === 'right') {
        ttLeft = targetLeft + targetWidth + 14;
        ttTop = targetTop + (targetHeight / 2) - (tooltipHeight / 2);
    }

    if (effectiveAlign === 'top' && ttTop < 12) {
        ttTop = targetTop + targetHeight + 14;
        effectiveAlign = 'bottom';
    } else if (effectiveAlign === 'bottom' && ttTop + tooltipHeight > vh - 12) {
        if (targetTop - tooltipHeight - 14 > 12) {
            ttTop = targetTop - tooltipHeight - 14;
            effectiveAlign = 'top';
        }
    }

    const margin = 12;
    const finalLeft = Math.max(margin, Math.min(ttLeft, vw - tooltipWidth - margin));
    const finalTop = Math.max(margin, Math.min(ttTop, vh - tooltipHeight - margin));

    adminTourTooltip.style.left = finalLeft + 'px';
    adminTourTooltip.style.top = finalTop + 'px';

    if (adminTourArrow) {
        adminTourArrow.style.display = 'block';
        adminTourArrow.style.position = 'fixed';
        adminTourArrow.className = 'admin-tour-arrow active';
        adminTourArrow.style.borderLeft = '';
        adminTourArrow.style.borderRight = '';
        adminTourArrow.style.borderTop = '';
        adminTourArrow.style.borderBottom = '';

        const arrowSize = 10;
        const targetCenterX = targetLeft + (targetWidth / 2);
        const targetCenterY = targetTop + (targetHeight / 2);

        if (effectiveAlign === 'top') {
            adminTourArrow.style.borderLeft = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderRight = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderTop = `${arrowSize}px solid rgba(10, 16, 26, 0.96)`;

            let arrowLeft = targetCenterX - arrowSize;
            arrowLeft = Math.max(finalLeft + 16, Math.min(arrowLeft, finalLeft + tooltipWidth - 16 - (arrowSize * 2)));

            adminTourArrow.style.left = arrowLeft + 'px';
            adminTourArrow.style.top = (finalTop + tooltipHeight) + 'px';
        } else if (effectiveAlign === 'left') {
            adminTourArrow.style.borderTop = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderBottom = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderLeft = `${arrowSize}px solid rgba(10, 16, 26, 0.96)`;

            let arrowTop = targetCenterY - arrowSize;
            arrowTop = Math.max(finalTop + 16, Math.min(arrowTop, finalTop + tooltipHeight - 16 - (arrowSize * 2)));

            adminTourArrow.style.left = (finalLeft + tooltipWidth) + 'px';
            adminTourArrow.style.top = arrowTop + 'px';
        } else if (effectiveAlign === 'right') {
            adminTourArrow.style.borderTop = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderBottom = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderRight = `${arrowSize}px solid rgba(10, 16, 26, 0.96)`;

            let arrowTop = targetCenterY - arrowSize;
            arrowTop = Math.max(finalTop + 16, Math.min(arrowTop, finalTop + tooltipHeight - 16 - (arrowSize * 2)));

            adminTourArrow.style.left = (finalLeft - (arrowSize * 2)) + 'px';
            adminTourArrow.style.top = arrowTop + 'px';
        } else {
            adminTourArrow.style.borderLeft = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderRight = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderBottom = `${arrowSize}px solid rgba(10, 16, 26, 0.96)`;

            let arrowLeft = targetCenterX - arrowSize;
            arrowLeft = Math.max(finalLeft + 16, Math.min(arrowLeft, finalLeft + tooltipWidth - 16 - (arrowSize * 2)));

            adminTourArrow.style.left = arrowLeft + 'px';
            adminTourArrow.style.top = (finalTop - (arrowSize * 2)) + 'px';
        }
    }
}

async function showAdminTourStep(index) {
    currentAdminStepIndex = index;

    if (index < 0) index = 0;
    if (index >= activeTourSteps.length) return endAdminTour();

    const step = activeTourSteps[index];
    if (!step) return;

    if (activeResizeObserver) {
        try { activeResizeObserver.disconnect(); } catch(e){}
        activeResizeObserver = null;
    }

    if (typeof step.beforeShow === 'function') {
        try {
            const res = step.beforeShow();
            if (res && typeof res.then === 'function') await res;
        } catch (e) { console.warn('[ADMIN TOUR] Error en beforeShow:', e); }
    }

    const badgeEl = document.getElementById('admin-tour-badge');
    const titleEl = document.getElementById('admin-tour-title');
    const textEl = document.getElementById('admin-tour-text');

    if (badgeEl) badgeEl.innerHTML = `<i class="fas fa-gauge-high"></i> PASO ${index + 1} DE ${activeTourSteps.length}`;
    if (titleEl) titleEl.innerHTML = `<i class="fas fa-compass"></i> ${step.title || ''}`;
    if (textEl) textEl.innerText = step.text || '';

    if (adminTourTooltip) adminTourTooltip.classList.remove('active');
    if (adminTourArrow) adminTourArrow.classList.remove('active');

    if (step.interactive) {
        adminTourOverlay.classList.add('interactive');
    } else {
        adminTourOverlay.classList.remove('interactive');
    }

    const waitForVisible = (sel, attempts = 0) => {
        const target = getVisibleTarget(sel);
        if (target) {
            const rect = target.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) return target;
        }
        if (attempts >= 12) return null;
        return new Promise(resolve => setTimeout(() => resolve(waitForVisible(sel, attempts + 1)), 150));
    };

    positioningToken = (typeof positioningToken === 'number' ? positioningToken + 1 : 1);
    const myToken = positioningToken;

    Promise.resolve(waitForVisible(step.selector)).then(async (resolvedTarget) => {
        if (myToken !== positioningToken) return;

        if (!resolvedTarget) {
            console.warn('[ADMIN TOUR] Target no encontrado:', step.selector);
            if (index < activeTourSteps.length - 1) return showAdminTourStep(index + 1);
            return endAdminTour();
        }

        if (window.ResizeObserver && resolvedTarget) {
            try {
                activeResizeObserver = new ResizeObserver(() => {
                    if (myToken === positioningToken) repositionActiveAdminStep();
                });
                activeResizeObserver.observe(resolvedTarget);
                if (resolvedTarget.parentElement) activeResizeObserver.observe(resolvedTarget.parentElement);
            } catch(e){}
        }

        if (!step.center) {
            try {
                const rect = resolvedTarget.getBoundingClientRect();
                const isVisible = (rect.top >= 0) && (rect.bottom <= window.innerHeight);
                if (!isVisible) {
                    resolvedTarget.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            } catch (e) {}
        }

        let frameCount = 0;
        const trackScroll = () => {
            if (myToken !== positioningToken) return;
            repositionActiveAdminStep();
            frameCount++;
            if (frameCount < 40) requestAnimationFrame(trackScroll);
        };
        requestAnimationFrame(trackScroll);

        setTimeout(() => { if (myToken === positioningToken) repositionActiveAdminStep(); }, 300);

        setTimeout(() => {
            if (myToken !== positioningToken) return;
            repositionActiveAdminStep();
            adminTourTooltip.classList.add('active');
            if (adminTourArrow && !step.center) adminTourArrow.classList.add('active');
        }, 120);
    });

    const prevBtn = document.getElementById('admin-tour-prev');
    const nextBtn = document.getElementById('admin-tour-next');

    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) nextBtn.innerHTML = index === activeTourSteps.length - 1 ? 'Finalizar <i class="fas fa-check"></i>' : 'Siguiente <i class="fas fa-arrow-right"></i>';
}

function nextAdminTourStep() {
    if (currentAdminStepIndex < activeTourSteps.length - 1) showAdminTourStep(currentAdminStepIndex + 1);
    else endAdminTour();
}

function prevAdminTourStep() {
    if (currentAdminStepIndex > 0) showAdminTourStep(currentAdminStepIndex - 1);
}

function endAdminTour() {
    isAdminTourActive = false;
    if (activeResizeObserver) {
        try { activeResizeObserver.disconnect(); } catch(e){}
        activeResizeObserver = null;
    }
    if (adminTourOverlay) {
        adminTourOverlay.classList.remove('active');
        if (adminTourTooltip) adminTourTooltip.classList.remove('active');
        if (adminTourArrow) adminTourArrow.classList.remove('active');
        setTimeout(() => {
            adminTourOverlay.style.display = 'none';
        }, 300);
    }
}

// --- 4. FUNCIONES EXPORTADAS PARA INICIAR CADA TOUR ---

function launchAdminTour(steps) {
    isAdminTourActive = true;
    activeTourSteps = steps.slice();
    if (!adminTourOverlay) createAdminTourElements();
    adminTourOverlay.style.display = 'block';
    setTimeout(() => {
        adminTourOverlay.classList.add('active');
        showAdminTourStep(0);
    }, 15);
}

export function startAdminLiveTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminLiveTourSteps);
}
window.startAdminLiveTour = startAdminLiveTour;

export function startAdminReservationsTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminReservationsTourSteps);
}
window.startAdminReservationsTour = startAdminReservationsTour;

export function startAdminUsersTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminUsersTourSteps);
}
window.startAdminUsersTour = startAdminUsersTour;

export function startAdminFinanceTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminFinanceTourSteps);
}
window.startAdminFinanceTour = startAdminFinanceTour;

export function startAdminTicketsTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminTicketsTourSteps);
}
window.startAdminTicketsTour = startAdminTicketsTour;

export function startAdminBranchesSettingsTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminBranchesSettingsTourSteps);
}
window.startAdminBranchesSettingsTour = startAdminBranchesSettingsTour;

export function startAdminFullDashboardTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    const rol = localStorage.getItem('rol');
    if (rol === 'staff') {
        const staffFullSteps = [
            ...adminLiveTourSteps,
            ...adminReservationsTourSteps.slice(1)
        ];
        launchAdminTour(staffFullSteps);
    } else {
        launchAdminTour(adminFullDashboardTourSteps);
    }
}
window.startAdminFullDashboardTour = startAdminFullDashboardTour;

export function openAdminHelpModal() {
    if (window.openModal) {
        window.openModal('modal-admin-help');
    } else {
        const modal = document.getElementById('modal-admin-help');
        if (modal) modal.style.display = 'flex';
    }
}
window.openAdminHelpModal = openAdminHelpModal;

export function toggleAdminFaq(el) {
    const item = el.closest('.admin-faq-item');
    if (item) {
        item.classList.toggle('open');
    }
}
window.toggleAdminFaq = toggleAdminFaq;

export function filterAdminHelpCategory(category, buttonEl) {
    const pills = document.querySelectorAll('.admin-help-pill');
    pills.forEach(p => p.classList.remove('active'));
    if (buttonEl) buttonEl.classList.add('active');

    const cards = document.querySelectorAll('.admin-help-quick-card');
    cards.forEach(card => {
        const cardCat = card.getAttribute('data-category');
        if (category === 'all' || cardCat === category || cardCat === 'all') {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });

    const faqGroups = document.querySelectorAll('.admin-faq-category-group');
    faqGroups.forEach(group => {
        const groupCat = group.getAttribute('data-category');
        if (category === 'all' || groupCat === category) {
            group.style.display = '';
        } else {
            group.style.display = 'none';
        }
    });
}
window.filterAdminHelpCategory = filterAdminHelpCategory;

export function filterAdminHelpSearch(query) {
    const term = (query || '').toLowerCase().trim();
    const cards = document.querySelectorAll('.admin-help-quick-card');
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        if (!term || text.includes(term)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });

    const faqItems = document.querySelectorAll('.admin-faq-item');
    faqItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (!term || text.includes(term)) {
            item.style.display = '';
            const group = item.closest('.admin-faq-category-group');
            if (group) group.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}
window.filterAdminHelpSearch = filterAdminHelpSearch;

