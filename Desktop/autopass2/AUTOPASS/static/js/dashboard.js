/**
 * AUTOPASS Professional Dashboard Logic
 * Handles tab switching, real-time updates, and administrative actions.
 */

let revenueChart = null;
let userPage = 1;
const userPageSize = 10;
let allUsersData = [];

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
    initClock();
    checkSystemHealth();
    
    // Aplicar clase de rol al body para CSS
    const rol = localStorage.getItem('rol');
    if (rol === 'staff') {
        document.body.classList.add('is-staff');
        // Cambiar badge de admin en el header
        const badge = document.querySelector('.admin-badge');
        if (badge) {
            badge.innerHTML = '<i class="fas fa-user-gear"></i> <span>Empleado</span>';
            badge.style.background = 'var(--secondary)';
        }
    }

    // Check for saved tab or default to live
    let lastTab = localStorage.getItem('activeAdminTab') || 'live';
    
    // Seguridad: Si es staff y la última pestaña era admin-only, resetear a live
    if (rol === 'staff' && ['users', 'finance', 'settings'].includes(lastTab)) {
        lastTab = 'live';
    }

    const activeItem = document.querySelector(`.nav-item[onclick*="'${lastTab}'"]`);
    if (activeItem) {
        switchTab(lastTab, activeItem);
    }

    // Live Refresh every 10 seconds for stats and logs
    setInterval(() => {
        const activeTab = localStorage.getItem('activeAdminTab');
        if (activeTab === 'live') {
            loadLiveStats();
            loadRecentLogs();
            loadOccupancy();
        }
    }, 10000);
});

/**
 * Updates the dashboard clock every second.
 */
function initClock() {
    const clockEl = document.getElementById('clock');
    if (!clockEl) return;
    
    const update = () => {
        const now = new Date();
        clockEl.innerText = now.toLocaleTimeString('es-AR', { hour12: false });
    };
    
    update();
    setInterval(update, 1000);
}

/**
 * Checks system status (DB, MQTT, API).
 */
async function checkSystemHealth() {
    const mainDot = document.getElementById('health-db');
    const res = await apiClient.get('/system/health');
    
    if (res.ok) {
        const data = res.data;
        // Punto principal del header
        if (mainDot) {
            const isOnline = data.database === 'ONLINE' && data.api === 'ONLINE';
            mainDot.style.background = isOnline ? '#10b981' : '#ef4444';
            if (isOnline) mainDot.classList.add('online');
            else mainDot.classList.remove('online');
        }

        // Listado de nodos en pestaña Live
        updateHealthNode('node-db', data.database === 'ONLINE');
        updateHealthNode('node-api', data.api === 'ONLINE');
        
        // El servicio ALPR es un objeto con múltiples cámaras
        const alprEntry = data.alpr?.ENTRADA_PRINCIPAL === 'ONLINE';
        const alprExit = data.alpr?.SALIDA_PRINCIPAL === 'ONLINE';
        updateHealthNode('node-ocr-entry', alprEntry);
        updateHealthNode('node-ocr-exit', alprExit);
    }
}

function updateHealthNode(id, isOnline) {
    const el = document.getElementById(id);
    if (!el) return;
    el.className = isOnline ? 'dot online' : 'dot';
}

async function openBarrier(gateId) {
    const confirm = await showConfirm('Apertura Forzada', `¿Estás seguro de abrir la barrera de <b>${gateId}</b> manualmente?`);
    if (!confirm) return;

    const iconId = gateId === 'ENTRADA' ? 'icon-barrier-entry' : 'icon-barrier-exit';
    const iconEl = document.getElementById(iconId);

    // Cambiar a barrera alta (visual)
    if (iconEl) iconEl.src = '/static/images/barrera alta.png';

    showToast(`Enviando señal de apertura a ${gateId}...`);
    const res = await apiClient.post(`/admin/open-barrier?gate_id=${gateId}`);

    if (res.ok) {
        showToast(`Barrera ${gateId} abierta correctamente.`, 'success');
        // Volver a barrera baja después de 3 segundos
        setTimeout(() => {
            if (iconEl) iconEl.src = '/static/images/barrera baja.png';
        }, 3000);
    } else {
        showToast(`Error al abrir barrera: ${res.error}`, 'danger');
        // Volver a barrera baja si falla
        if (iconEl) iconEl.src = '/static/images/barrera baja.png';
    }
}

/**
 * Toggle the visibility of manual operation controls.
 */
window.toggleManualOps = function() {
    const content = document.getElementById('manual-ops-content');
    const chevron = document.getElementById('manual-ops-chevron');
    if (!content || !chevron) return;

    if (content.style.maxHeight === '0px' || content.style.maxHeight === '') {
        content.style.maxHeight = '400px'; // Sufficient height for all content + shadows
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.maxHeight = '0px';
        chevron.style.transform = 'rotate(0deg)';
    }
}

/**
 * Toggle the visibility of the current occupancy list in the monitoring tab.
 */
window.toggleOccupancy = function() {
    const content = document.getElementById('occupancy-content');
    const chevron = document.getElementById('occupancy-chevron');
    if (!content || !chevron) return;

    if (content.style.maxHeight === '0px' || content.style.maxHeight === '') {
        content.style.maxHeight = '1000px'; // High enough to fit the table
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.maxHeight = '0px';
        chevron.style.transform = 'rotate(0deg)';
    }
}

/**
 * Toggle the visibility of the rates section in settings.
 */
window.toggleRates = function() {
    const content = document.getElementById('rates-content');
    const chevron = document.getElementById('rates-chevron');
    if (!content || !chevron) return;

    if (content.style.maxHeight === '0px' || content.style.maxHeight === '') {
        content.style.maxHeight = '600px'; // Sufficient for the rates form
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.maxHeight = '0px';
        chevron.style.transform = 'rotate(0deg)';
    }
}

/**
 * Toggle the visibility of the plazas section in settings.
 */
window.togglePlazas = function() {
    const content = document.getElementById('plazas-content');
    const chevron = document.getElementById('plazas-chevron');
    if (!content || !chevron) return;

    if (content.style.maxHeight === '0px' || content.style.maxHeight === '') {
        content.style.maxHeight = '300px'; // Sufficient for the plazas form
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.maxHeight = '0px';
        chevron.style.transform = 'rotate(0deg)';
    }
}

// --- NAVIGATION ---

function switchTab(tabId, element) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    element.classList.add('active');
    
    document.querySelectorAll('.tab-view').forEach(view => view.classList.remove('active'));
    const activeTab = document.getElementById(`tab-${tabId}`);
    if (activeTab) activeTab.classList.add('active');
    
    const titleEl = document.getElementById('view-title');
    if (titleEl) {
        const rol = localStorage.getItem('rol');
        const titles = {
            'live': 'Monitoreo',
            'admin-reservations': 'Reservas',
            'users': 'Gestión de Usuarios',
            'finance': 'Reporte Financiero',
            'settings': 'Configuración'
        };
        titleEl.innerText = titles[tabId] || 'Dashboard';
        
        // Actualizar subtítulo según rol
        const subtitleEl = document.querySelector('.header-subtitle');
        if (subtitleEl) {
            subtitleEl.innerText = rol === 'admin' ? 'Panel de Control Administrativo' : 'Panel de Operaciones';
        }
    }
    
    localStorage.setItem('activeAdminTab', tabId);
    loadTabData(tabId);
}

function loadTabData(tabId) {
    switch (tabId) {
        case 'live':
            loadLiveStats();
            loadRecentLogs();
            loadOccupancy();
            break;
        case 'admin-reservations':
            loadAdminReservations();
            break;
        case 'users':
            loadUsers();
            break;
        case 'finance':
            loadFinanceData();
            break;
        case 'settings':
            loadSettings();
            break;
    }
}

// --- TAB DATA LOADING ---

async function loadLiveStats() {
    // 1. Ocupación
    const resStatus = await apiClient.get('/parking/status');
    if (resStatus.ok) {
        const free = resStatus.data.disponibilidad;
        const occupied = resStatus.data.ocupacion_actual;
        const total = resStatus.data.capacidad_total;

        const freeEl = document.getElementById('stat-free');
        const occupiedEl = document.getElementById('stat-occupied');
        if (freeEl) freeEl.innerText = free;
        if (occupiedEl) occupiedEl.innerText = occupied;

        // Actualizar barras de progreso
        const barFree = document.getElementById('bar-free');
        const barOccupied = document.getElementById('bar-occupied');
        if (barFree) barFree.style.width = `${(free / total) * 100}%`;
        if (barOccupied) barOccupied.style.width = `${(occupied / total) * 100}%`;
    }

    // 2. Ingresos hoy (Solo si existen los elementos, usualmente solo para admin)
    const resFinance = await apiClient.get('/reports/financial-summary?period=day');
    if (resFinance.ok) {
        const entriesEl = document.getElementById('stat-entries');
        const moneyEl = document.getElementById('stat-money');
        if (entriesEl) entriesEl.innerText = resFinance.data.cantidad_pagos;
        if (moneyEl) moneyEl.innerText = `$${resFinance.data.total_recaudado.toLocaleString('es-AR')}`;
    }
}

async function loadRecentLogs() {
    const res = await apiClient.get('/reports/access');
    if (!res.ok) return;

    const tbody = document.getElementById('live-logs');
    if (!tbody) return;

    tbody.innerHTML = res.data.slice(0, 10).map(log => {
        const date = new Date(log.fecha_hora);
        const time = date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
        const badgeClass = log.tipo_evento === 'ENTRADA' ? 'text-secondary' : 'text-dorado';
        const statusBadge = log.pago_confirmado ? 
            `<span class="badge badge-success-light">PAGADO</span>` : 
            `<span class="badge badge-danger-light">PENDIENTE</span>`;

        return `
            <tr>
                <td>${time}</td>
                <td><span class="plate-style">${log.patente_detectada}</span></td>
                <td class="${badgeClass} text-bold">${log.tipo_evento}</td>
                <td>${statusBadge}</td>
                <td><button class="btn-edit" onclick="showLogDetail(${log.id})" title="Ver captura"><i class="fas fa-eye"></i></button></td>
            </tr>
        `;
    }).join('') || '<tr><td colspan="5" class="text-center py-20">No hay movimientos registrados hoy.</td></tr>';

    // Re-aplicar filtro si existe
    const filterInput = document.querySelector('#tab-live .search-box-premium input');
    if (filterInput && filterInput.value) {
        filterTable('live-logs', filterInput.value);
    }
}

async function loadOccupancy() {
    const res = await apiClient.get('/parking/current-occupancy');
    if (!res.ok) return;

    const data = res.data;
    const tbody = document.getElementById('occ-list');
    if (!tbody) return;

    // Calcular KPIs
    const totalCount = data.length;
    let totalDebt = 0;
    let totalMs = 0;

    tbody.innerHTML = data.map(occ => {
        const date = new Date(occ.ingreso);
        const time = date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
        
        const diffMs = new Date() - date;
        totalMs += diffMs;
        totalDebt += occ.deuda;

        const diffHrs = Math.floor(diffMs / 3600000);
        const diffMins = Math.floor((diffMs % 3600000) / 60000);
        const duration = `${diffHrs}h ${diffMins}m`;

        const statusBadge = occ.ya_pago ? 
            `<span class="badge badge-success-light">PAGO CONFIRMADO</span>` :
            `<span class="badge badge-warning-light">$${occ.deuda.toLocaleString('es-AR')} PENDIENTE</span>`;

        return `
            <tr>
                <td><span class="plate-style">${occ.patente}</span></td>
                <td>${time}</td>
                <td class="text-bold text-light text-center">${duration}</td>
                <td>${statusBadge}</td>
                <td>
                    <div class="flex-row gap-5">
                        ${!occ.ya_pago ? `<button class="btn-icon-premium sm" onclick="payOccupancy('${occ.patente}')" title="Procesar Pago"><i class="fas fa-cash-register"></i></button>` : ''}
                        <button class="btn-icon-premium sm warning" onclick="manualExit('${occ.patente}')" title="Registrar Salida"><i class="fas fa-door-open"></i></button>
                    </div>
                </td>
            </tr>
        `;
    }).join('') || '<tr><td colspan="5" class="text-center py-20">No hay vehículos en el predio.</td></tr>';

    // Actualizar KPIs en la UI (con validación de existencia)
    const countEl = document.getElementById('occ-stat-count');
    const debtEl = document.getElementById('occ-stat-debt');
    const avgEl = document.getElementById('occ-stat-avg-time');

    if (countEl) countEl.innerText = totalCount;
    if (debtEl) debtEl.innerText = `$${totalDebt.toLocaleString('es-AR')}`;
    
    if (avgEl) {
        if (totalCount > 0) {
            const avgMs = totalMs / totalCount;
            const avgHrs = Math.floor(avgMs / 3600000);
            const avgMins = Math.floor((avgMs % 3600000) / 60000);
            avgEl.innerText = `${avgHrs}h ${avgMins}m`;
        } else {
            avgEl.innerText = '--';
        }
    }
}

async function loadAdminReservations() {
    const sucursal = document.getElementById('admin-res-filter-sucursal')?.value || '';
    const statusFilter = document.getElementById('admin-res-filter-status')?.value || '';
    
    const res = await apiClient.get(`/admin/reservations${sucursal ? '?sucursal=' + encodeURIComponent(sucursal) : ''}`);
    if (!res.ok) return;

    let data = res.data;
    
    // Filtro por estado en el cliente
    if (statusFilter) {
        data = data.filter(r => r.estado_reserva === statusFilter);
    }

    const tbody = document.getElementById('admin-res-list');
    if (!tbody) return;

    // Calcular KPIs
    const totalCount = data.length;
    let pendingToday = 0;
    let totalProjectedRevenue = 0;
    const todayStr = new Date().toISOString().split('T')[0];

    tbody.innerHTML = data.map(r => {
        if (r.fecha_inicio.startsWith(todayStr) && r.estado_reserva === 'Pendiente') {
            pendingToday++;
        }
        
        // Sumar al total proyectado (solo lo que no está cancelado)
        if (r.estado_reserva !== 'Cancelada') {
            totalProjectedRevenue += r.monto_total;
        }

        const pagoBadge = r.estado_pago === 'Pagado' ? 
            '<span class="badge badge-success-light">PAGADO</span>' : 
            '<span class="badge badge-danger-light">PENDIENTE</span>';
        
        const statusClassMap = {
            'Pendiente': 'text-dorado',
            'Activa': 'text-secondary',
            'Completada': 'text-muted',
            'Cancelada': 'text-danger'
        };
        const statusClass = statusClassMap[r.estado_reserva] || '';

        return `
            <tr>
                <td><b>#${r.id}</b></td>
                <td>
                    <div class="flex-col gap-5">
                        <span class="text-bold">${r.user_name || 'Consumidor Final'}</span>
                        <span class="text-small text-muted">${r.user_email || 'Manual / Externo'}</span>
                    </div>
                </td>
                <td><span class="plate-style">${r.patente}</span></td>
                <td>
                    <div class="text-small">
                        <div class="text-light">${formatDate(r.fecha_inicio)}</div>
                        <div class="text-muted">${formatDate(r.fecha_fin)}</div>
                    </div>
                </td>
                <td>
                    <div class="flex-col">
                        <span class="text-bold text-small">${r.sucursal_nombre}</span>
                        <span class="badge badge-info-dark mt-5">${(r.tipo_estadia || '').charAt(0).toUpperCase() + (r.tipo_estadia || '').slice(1)}</span>
                    </div>
                </td>
                <td class="text-dorado text-bold">$${r.monto_total.toLocaleString('es-AR')}</td>
                <td>${pagoBadge}</td>
                <td><span class="${statusClass} text-bold text-xs uppercase">${r.estado_reserva}</span></td>
                <td>
                    <div class="flex-row gap-5">
                        ${(r.estado_pago !== 'Pagado' && r.estado_reserva !== 'Cancelada' && r.estado_reserva !== 'Completada') ? `<button class="btn-icon-premium sm" onclick="confirmPaymentAdmin(${r.id})" title="Confirmar Pago"><i class="fas fa-check-double"></i></button>` : ''}
                        ${(r.estado_reserva !== 'Cancelada' && r.estado_reserva !== 'Completada') ? `<button class="btn-icon-premium sm danger" onclick="cancelReservationAdmin(${r.id})" title="Cancelar Reserva"><i class="fas fa-xmark"></i></button>` : ''}
                    </div>
                </td>
            </tr>`;
    }).join('') || '<tr><td colspan="9" class="text-center py-20">No hay reservas registradas.</td></tr>';

    // Actualizar KPIs
    document.getElementById('admin-res-stat-total').innerText = totalCount;
    document.getElementById('admin-res-stat-pending').innerText = pendingToday;
    document.getElementById('admin-res-stat-revenue').innerText = `$${totalProjectedRevenue.toLocaleString('es-AR')}`;
}

async function confirmPaymentAdmin(id) {
    const confirm = await showConfirm('Confirmar Pago', `¿Confirmás el pago manual para la reserva <b>#${id}</b>?`);
    if (!confirm) return;

    const res = await apiClient.post(`/admin/reservations/${id}/confirm-payment`);
    if (res.ok) {
        showToast(`Reserva #${id} marcada como PAGADA.`);
        loadAdminReservations();
    } else {
        showToast(res.error);
    }
}

async function cancelReservationAdmin(id) {
    const confirm = await showConfirm('Cancelar Reserva', `¿Estás seguro de cancelar la reserva <b>#${id}</b>? Esta acción es irreversible.`);
    if (!confirm) return;

    const res = await apiClient.post(`/admin/reservations/${id}/cancel`);
    if (res.ok) {
        showToast(`Reserva #${id} cancelada.`);
        loadAdminReservations();
    } else {
        showToast(res.error);
    }
}

async function loadUsers() {
    const res = await apiClient.get('/admin/users');
    if (!res.ok) return;

    allUsersData = res.data;
    
    // Ordenar por jerarquía de roles: admin > staff > user
    const roleOrder = { 'admin': 1, 'staff': 2, 'user': 3 };
    allUsersData.sort((a, b) => (roleOrder[a.rol] || 99) - (roleOrder[b.rol] || 99));

    // Actualizar KPI de Totales
    const statTotalEl = document.getElementById('stat-total-users');
    if (statTotalEl) statTotalEl.innerText = allUsersData.length;

    // Contar usuarios por rol
    const counts = allUsersData.reduce((acc, u) => {
        acc[u.rol] = (acc[u.rol] || 0) + 1;
        return acc;
    }, {});

    const statAdminEl = document.getElementById('stat-admin-users');
    const statStaffEl = document.getElementById('stat-staff-users');
    const statCustomerEl = document.getElementById('stat-customer-users');

    if (statAdminEl) statAdminEl.innerText = counts['admin'] || 0;
    if (statStaffEl) statStaffEl.innerText = counts['staff'] || 0;
    if (statCustomerEl) statCustomerEl.innerText = counts['user'] || 0;

    userPage = 1;
    renderUserPage();
}

/**
 * Renderiza una página específica de la lista de usuarios.
 */
function renderUserPage(dataToRender = null) {
    const tbody = document.getElementById('user-list');
    if (!tbody) return;

    const data = dataToRender || allUsersData;
    const totalPages = Math.ceil(data.length / userPageSize) || 1;
    
    if (userPage > totalPages) userPage = totalPages;
    if (userPage < 1) userPage = 1;

    const start = (userPage - 1) * userPageSize;
    const end = start + userPageSize;
    const pageData = data.slice(start, end);

    tbody.innerHTML = pageData.map(u => {
        let rolBadge = '';
        if (u.rol === 'admin') {
            rolBadge = `<span class="badge" style="background: var(--dorado); color: #000; font-weight: 900; border: none;">ADMIN</span>`;
        } else if (u.rol === 'staff') {
            rolBadge = `<span class="badge" style="background: rgba(16, 185, 129, 0.1); color: var(--secondary); border: 1px solid rgba(16, 185, 129, 0.2); font-weight: 800;">EMPLEADO</span>`;
        } else {
            rolBadge = `<span class="badge" style="background: rgba(59, 130, 246, 0.1); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.2); font-weight: 800;">CLIENTE</span>`;
        }

        return `
            <tr>
                <td>
                    <div class="flex-col">
                        <span class="text-bold ${u.is_blocked ? 'text-danger' : ''}">${u.nombre} ${u.apellido}</span>
                        <span class="text-xs text-muted">DNI: ${u.dni} ${u.is_blocked ? '<span class="badge badge-danger-light ml-5">BLOQUEADO</span>' : ''}</span>
                    </div>
                </td>
                <td>
                    <div class="flex-col gap-5">
                        <div class="text-small text-light"><i class="fas fa-envelope text-dorado mr-10"></i> ${u.email}</div>
                        <div class="text-xs text-muted"><i class="fas fa-phone mr-10"></i> ${u.telefono || 'S/D'}</div>
                    </div>
                </td>
                <td>${rolBadge}</td>
                <td><b class="text-dorado">${u.puntos_acumulados || 0}</b> <small class="text-muted">pts</small></td>
                <td class="text-bold">$${u.saldo.toLocaleString('es-AR')}</td>
                <td>
                    <div class="flex-row gap-5">
                        ${u.rol !== 'admin' ? `
                            <button class="btn-icon-premium sm ${u.is_blocked ? 'success' : 'danger'}" onclick="toggleUserBlock(${u.id}, '${u.nombre}', ${u.is_blocked})" title="${u.is_blocked ? 'Desbloquear' : 'Bloquear'}">
                                <i class="fas ${u.is_blocked ? 'fa-user-check' : 'fa-user-slash'}"></i>
                            </button>
                        ` : ''}

                        ${u.rol === 'user' ? `
                        <button class="btn-icon-premium sm" onclick="adjustUserBalance(${u.id}, '${u.nombre}')" title="Ajustar Saldo">
                            <i class="fas fa-wallet"></i>
                        </button>` : ''}
                        
                        ${u.rol !== 'admin' ? `
                            <button class="btn-icon-premium sm" onclick="changeUserRole(${u.id}, '${u.rol}')" title="Cambiar Rol">
                                <i class="fas fa-user-shield"></i>
                            </button>
                            
                            <button class="btn-icon-premium sm danger" onclick="deleteUserAdmin(${u.id})" title="Eliminar">
                                <i class="fas fa-trash-can"></i>
                            </button>
                        ` : ''}
                    </div>
                </td>
            </tr>
        `;
    }).join('') || `<tr><td colspan="6" class="text-center py-20">${data.length === 0 ? 'No se encontraron usuarios.' : 'Fin de la lista.'}</td></tr>`;

    // Actualizar controles de paginación
    document.getElementById('user-page-info').innerText = `Página ${userPage} de ${totalPages}`;
    document.getElementById('prev-user-btn').disabled = userPage === 1;
    document.getElementById('next-user-btn').disabled = userPage === totalPages || totalPages === 0;
}

function prevUserPage() {
    if (userPage > 1) {
        userPage--;
        renderUserPage();
    }
}

function nextUserPage() {
    const totalPages = Math.ceil(allUsersData.length / userPageSize);
    if (userPage < totalPages) {
        userPage++;
        renderUserPage();
    }
}

function toggleUserList() {
    const content = document.getElementById('user-list-collapsible');
    const btn = document.getElementById('user-list-toggle-btn');
    if (!content || !btn) return;

    const isExpanded = content.classList.toggle('expanded');
    btn.querySelector('i').className = isExpanded ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
}

function filterUserList(query) {
    const q = query.toLowerCase();
    const filtered = allUsersData.filter(u => 
        u.nombre.toLowerCase().includes(q) || 
        u.apellido.toLowerCase().includes(q) || 
        u.dni.includes(q) || 
        u.email.toLowerCase().includes(q)
    );
    userPage = 1;
    renderUserPage(filtered);
}

async function loadFinanceData() {
    const period = document.getElementById('fin-period')?.value || 'total';
    const resSummary = await apiClient.get(`/reports/financial-summary?period=${period}`);
    
    if (resSummary.ok) {
        document.getElementById('fin-total').innerText = `$${resSummary.data.total_recaudado.toLocaleString('es-AR')}`;
        document.getElementById('fin-count').innerText = resSummary.data.cantidad_pagos;
        document.getElementById('fin-avg').innerText = `$${resSummary.data.ticket_promedio.toLocaleString('es-AR')}`;
        
        // Inicializar o actualizar gráfico
        updateRevenueChart(period);
    }

    const resHistory = await apiClient.get('/reports/payment-history');
    if (resHistory.ok) {
        const tbody = document.getElementById('payment-list');
        tbody.innerHTML = resHistory.data.slice(0, 15).map(pay => `
            <tr>
                <td>${new Date(pay.fecha_hora).toLocaleString('es-AR')}</td>
                <td><span class="plate-style">${pay.patente_detectada}</span></td>
                <td class="text-bold">$${pay.costo_estadia.toLocaleString('es-AR')}</td>
                <td><span class="badge badge-muted">SALDO VIRTUAL</span></td>
                <td class="text-secondary text-bold">CONFIRMADO</td>
            </tr>
        `).join('') || '<tr><td colspan="5" class="text-center py-20">No hay transacciones registradas.</td></tr>';
    }
}

/**
 * Genera o actualiza el gráfico de tendencia de ingresos con datos reales.
 */
async function updateRevenueChart(period) {
    const ctx = document.getElementById('revenueChart')?.getContext('2d');
    if (!ctx) return;

    // Obtener historial de pagos para el periodo
    const res = await apiClient.get(`/reports/payment-history?period=${period}`);
    if (!res.ok) return;

    const data = res.data;
    const grouped = {};
    const labels = [];
    const now = new Date();

    // 1. Pre-poblar etiquetas según el periodo para que el gráfico no esté vacío
    if (period === 'day') {
        for (let i = 0; i <= 23; i++) {
            const label = `${i.toString().padStart(2, '0')}:00`;
            labels.push(label);
            grouped[label] = 0;
        }
    } else if (period === 'week') {
        const days = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
        for (let i = 6; i >= 0; i--) {
            const d = new Date();
            d.setDate(now.getDate() - i);
            const label = days[d.getDay()];
            labels.push(label);
            grouped[label] = 0;
        }
    } else {
        const months = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
        for (let i = 5; i >= 0; i--) {
            const d = new Date();
            d.setMonth(now.getMonth() - i);
            const label = months[d.getMonth()];
            labels.push(label);
            grouped[label] = 0;
        }
    }

    // 2. Llenar con datos reales
    data.forEach(p => {
        const d = new Date(p.fecha_hora);
        let key;
        if (period === 'day') key = `${d.getHours().toString().padStart(2, '0')}:00`;
        else if (period === 'week') key = d.toLocaleDateString('es-AR', { weekday: 'short' }).replace('.', '');
        else key = d.toLocaleDateString('es-AR', { month: 'short' }).replace('.', '');
        
        // Capitalizar primera letra para matchear pre-poblado
        key = key.charAt(0).toUpperCase() + key.slice(1);
        if (grouped[key] !== undefined) grouped[key] += p.costo_estadia;
    });

    const dataValues = labels.map(l => grouped[l]);

    if (revenueChart) revenueChart.destroy();

    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Ingresos ($)',
                data: dataValues,
                borderColor: '#C5A059',
                backgroundColor: 'rgba(197, 160, 89, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#C5A059',
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: { 
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleFont: { family: 'Montserrat', weight: 'bold' },
                    bodyFont: { family: 'Montserrat' },
                    callbacks: {
                        label: (ctx) => ` Recaudado: $${ctx.raw.toLocaleString('es-AR')}`
                    }
                }
            },
            scales: {
                y: { 
                    beginAtZero: true, 
                    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false }, 
                    ticks: { color: '#666', font: { size: 10 }, callback: (val) => '$' + val.toLocaleString() } 
                },
                x: { 
                    grid: { display: false }, 
                    ticks: { color: '#666', font: { size: 10 } } 
                }
            }
        }
    });
}

async function loadSettings() {
    const res = await apiClient.get('/admin/settings');
    if (res.ok) {
        const keys = ['precio_hora', 'precio_dia', 'precio_semana', 'precio_quincena', 'precio_mes', 'capacidad_total'];
        keys.forEach(k => {
            const input = document.getElementById(`cfg-${k}`);
            if (input && res.data[k] !== undefined) input.value = res.data[k];
        });
    }

    // Si capacidad_total no está en settings, traerla de /parking/status
    const capInput = document.getElementById('cfg-capacidad_total');
    if (capInput && (!capInput.value || capInput.value == 0)) {
        const resStatus = await apiClient.get('/parking/status');
        if (resStatus.ok) {
            capInput.value = resStatus.data.capacidad_total;
        }
    }
}

// --- OPERATIONS ---

async function saveAllRates() {
    const rates = ['precio_hora', 'precio_dia', 'precio_semana', 'precio_quincena', 'precio_mes'];
    let successCount = 0;
    
    for (const r of rates) {
        const val = document.getElementById(`cfg-${r}`).value;
        const res = await apiClient.post(`/settings/prices?clave=${r}&valor=${val}`);
        if (res.ok) successCount++;
    }
    
    if (successCount === rates.length) showToast('Tarifario actualizado correctamente');
    else showToast('Algunas tarifas no se pudieron guardar');
}

async function saveSystemParam(key) {
    const val = document.getElementById(`cfg-${key}`).value;
    const res = await apiClient.post(`/settings/prices?clave=${key}&valor=${val}`);
    if (res.ok) showToast('Parámetro actualizado');
    else showToast(res.error);
}

async function manualEntry() {
    const plateInput = document.getElementById('manual-plate');
    const plate = plateInput.value.trim().toUpperCase();
    if (!plate) return showToast('Ingresá una patente');
    
    const confirm = await showConfirm('Registrar Ingreso', `¿Confirmás el ingreso manual del vehículo <b>${plate}</b>?`);
    if (!confirm) return;
    
    const res = await apiClient.post(`/admin/manual-entry?plate=${plate}`);
    if (res.ok) {
        showToast(`Vehículo ${plate} ingresado.`);
        plateInput.value = '';
        loadOccupancy();
    } else {
        showToast(res.error);
    }
}

async function manualExit(prefillPlate = null) {
    const plate = prefillPlate || document.getElementById('manual-plate').value.trim().toUpperCase();
    if (!plate) return showToast('Ingresá una patente');
    
    const confirm = await showConfirm('Registrar Salida', `¿Confirmás la salida manual del vehículo <b>${plate}</b>?`);
    if (!confirm) return;
    
    const res = await apiClient.post(`/admin/manual-exit?plate=${plate}`);
    if (res.ok) {
        showToast(`Vehículo ${plate} egresado correctamente.`);
        loadOccupancy();
    } else {
        showToast(res.error);
    }
}

async function payOccupancy(plate) {
    const res = await apiClient.post(`/access/pay-stay?plate=${plate}`);
    if (res.ok) {
        showToast(`Pago procesado con éxito para ${plate}.`);
        loadOccupancy();
    } else {
        showToast(res.error);
    }
}

async function resetSys() {
    const confirm = await showConfirm('🚨 REINICIO INTEGRAL', '¿Estás absolutamente seguro? Se borrarán todos los datos, fotos y registros del sistema.');
    if (!confirm) return;
    
    const res = await apiClient.post('/admin/system/reset');
    if (res.ok) {
        showToast('Sistema reiniciado con éxito.');
        window.location.reload();
    } else {
        showToast(res.error);
    }
}

async function handleAdminCreateUser(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const originalText = btn.innerText;

    const rol = document.getElementById('admin-user-rol').value;
    const sucursal = (rol === 'staff' || rol === 'local_admin') ? document.getElementById('admin-user-sucursal').value : null;

    const payload = {
        nombre: document.getElementById('admin-user-nombre').value,
        apellido: document.getElementById('admin-user-apellido').value,
        email: document.getElementById('admin-user-email').value,
        dni: document.getElementById('admin-user-dni').value,
        password: document.getElementById('admin-user-password').value,
        telefono: "1112345678", // Default válido para evitar error de validación schema
        sucursal: sucursal
    };

    btn.innerText = 'PROCESANDO...';
    btn.disabled = true;

    const res = await apiClient.post(`/admin/users?rol=${rol}`, payload);
    if (res.ok) {
        showToast(`Usuario ${payload.nombre} creado correctamente con rol ${rol} en ${sucursal || 'Global'}.`, 'success');
        closeModal('modal-create-user');
        event.target.reset();
        const branchRow = document.getElementById('branch-selection-row');
        if (branchRow) branchRow.style.display = 'none';
        loadUsers(); 
    } else {
        // Mejor extracción de errores de FastAPI (soporta string y array de validación)
        let errorMsg = 'Error desconocido';
        if (res.error) {
            if (typeof res.error.detail === 'string') {
                errorMsg = res.error.detail;
            } else if (Array.isArray(res.error.detail)) {
                errorMsg = res.error.detail.map(e => e.msg).join(', ');
            } else if (typeof res.error === 'string') {
                errorMsg = res.error;
            }
        }
        showToast(`Error: ${errorMsg}`, 'danger');
    }

    btn.innerText = originalText;
    btn.disabled = false;
}

function filterTable(tableId, query) {
    const rows = document.getElementById(tableId).getElementsByTagName('tr');
    const q = query.toLowerCase();
    for (let row of rows) {
        row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
    }
}

/**
 * Muestra/Oculta la selección de sucursal según el rol seleccionado.
 */
window.toggleBranchSelection = function() {
    const rol = document.getElementById('admin-user-rol').value;
    const row = document.getElementById('branch-selection-row');
    if (!row) return;

    if (rol === 'staff' || rol === 'local_admin') {
        row.style.display = 'flex';
    } else {
        row.style.display = 'none';
    }
}

/**
 * Muestra el detalle visual de un log de acceso (Auditoría ALPR).
 */
async function showLogDetail(logId) {
    const res = await apiClient.get(`/reports/access`);
    if (!res.ok) return;

    // Buscamos el log específico en la lista (o podríamos tener un endpoint de detalle)
    const log = res.data.find(l => l.id === logId);
    if (!log) return showToast('No se encontró información del registro', 'danger');

    // Poblar modal
    document.getElementById('audit-plate').innerText = log.patente_detectada;
    document.getElementById('audit-plate-overlay').innerText = log.patente_detectada;
    document.getElementById('audit-time').innerText = new Date(log.fecha_hora).toLocaleString('es-AR');
    document.getElementById('audit-type').innerText = log.tipo_evento;
    document.getElementById('audit-payment').innerText = log.pago_confirmado ? 'PAGADO' : 'PENDIENTE';
    document.getElementById('audit-res-id').innerText = log.reserva_id ? `#${log.reserva_id}` : 'SIN RESERVA';

    // Ajustar iconos y colores
    const typeIcon = document.getElementById('audit-type-icon');
    if (log.tipo_evento === 'ENTRADA') {
        typeIcon.className = 'fas fa-sign-in-alt text-secondary';
        document.getElementById('audit-type').className = 'text-secondary text-bold';
    } else {
        typeIcon.className = 'fas fa-sign-out-alt text-dorado';
        document.getElementById('audit-type').className = 'text-dorado text-bold';
    }

    // Cargar imagen desde el nuevo endpoint
    const imgEl = document.getElementById('audit-image');
    const placeholderEl = document.getElementById('audit-placeholder');
    const overlayEl = document.getElementById('audit-overlay-container');
    
    // Resetear estados: ocultamos todo al empezar
    imgEl.style.display = 'none';
    if (placeholderEl) placeholderEl.style.display = 'none';
    if (overlayEl) overlayEl.style.display = 'none';

    // Configuramos los handlers antes de asignar el src
    imgEl.onload = () => {
        imgEl.style.display = 'block';
        if (overlayEl) overlayEl.style.display = 'block';
        if (placeholderEl) placeholderEl.style.display = 'none';
    };

    imgEl.onerror = () => {
        imgEl.style.display = 'none';
        if (overlayEl) overlayEl.style.display = 'none';
        if (placeholderEl) placeholderEl.style.display = 'flex';
        console.warn(`No se pudo cargar la imagen para el log ${logId}`);
    };

    imgEl.src = `/v1/system/capture/${logId}?t=${Date.now()}`;

    openModal('modal-log-detail');
}

// --- USER MANAGEMENT ACTIONS ---

async function toggleUserBlock(id, nombre, currentlyBlocked) {
    const action = currentlyBlocked ? 'DESBLOQUEAR' : 'BLOQUEAR';
    const confirm = await showConfirm(`${action} USUARIO`, `¿Estás seguro de ${action.toLowerCase()} al usuario <b>${nombre}</b>?`);
    if (!confirm) return;

    const res = await apiClient.post(`/admin/users/${id}/toggle-block`);
    if (res.ok) {
        showToast(res.data.message, 'success');
        loadUsers();
    } else {
        showToast(res.error || 'Error al procesar la solicitud', 'danger');
    }
}

async function deleteUserAdmin(id) {
    const confirm = await showConfirm('Eliminar Usuario', `¿Estás seguro de eliminar este usuario permanentemente? Esta acción no se puede deshacer.`);
    if (!confirm) return;

    const res = await apiClient.post(`/admin/users/${id}/delete`); // Asumo que el endpoint es POST por convención del proyecto
    if (res.ok) {
        showToast(`Usuario eliminado correctamente.`);
        loadUsers();
    } else {
        // Si falló el POST, intentamos DELETE por si acaso
        const resDel = await apiClient.delete(`/admin/users/${id}`);
        if (resDel.ok) {
            showToast(`Usuario eliminado.`);
            loadUsers();
        } else {
            showToast(resDel.error || 'Error al eliminar usuario');
        }
    }
}

async function changeUserRole(id, currentRole) {
    const newRole = currentRole === 'admin' ? 'staff' : (currentRole === 'staff' ? 'user' : 'admin');
    const confirm = await showConfirm('Cambiar Rol', `¿Cambiar el rol de este usuario a <b>${newRole.toUpperCase()}</b>?`);
    if (!confirm) return;

    const res = await apiClient.post(`/admin/users/${id}/role?nuevo_rol=${newRole}`);
    if (res.ok) {
        showToast('Rol actualizado correctamente.');
        loadUsers();
    } else {
        showToast(res.error);
    }
}

async function adjustUserBalance(id, nombre) {
    const amount = await showPrompt(`Ajustar Saldo: ${nombre}`, 'Ingresá el nuevo saldo total:');
    if (amount === null || amount === "") return;

    const res = await apiClient.post(`/admin/users/${id}/balance?monto=${amount}`);
    if (res.ok) {
        showToast('Saldo actualizado.');
        loadUsers();
    } else {
        showToast(res.error);
    }
}
