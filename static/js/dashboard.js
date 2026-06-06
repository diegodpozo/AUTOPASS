import * as ui from './modules/dashboard-ui.js';
import * as stats from './modules/dashboard-stats.js';
import * as admin from './modules/dashboard-admin.js';
import * as promos from './modules/dashboard-promotions.js';
import * as baseUi from './modules/ui.js';
import api from './modules/api.js';
import * as utils from './modules/utils.js';

/**
 * BRIDGE: dashboard.js
 * Mantiene la interfaz operativa centralizando la lógica modular.
 */

// UI & Navigation
window.switchTab = ui.switchTab;
window.toggleMobileNav = ui.toggleMobileNav;
window.closeMobileNav = ui.closeMobileNav;
window.toggleSidebar = ui.toggleSidebar;
window.toggleManualOps = () => ui.toggleCollapsible('manual-ops-content', 'manual-ops-chevron', '400px');
window.toggleOccupancy = () => ui.toggleCollapsible('occupancy-content', 'occupancy-chevron', '1000px');

// Global UI Modals
window.openModal = baseUi.openModal;
window.closeModal = baseUi.closeModal;

// Utilities
window.filterTable = utils.filterTable;
window.formatDate = utils.formatDate;

// Admin Actions & Settings
window.openBarrier = admin.openBarrier;
window.loadUsers = admin.loadUsers;
window.filterUserList = admin.filterUserList;
window.prevUserPage = admin.prevUserPage;
window.nextUserPage = admin.nextUserPage;
window.toggleBranchSelection = admin.toggleBranchSelection;
window.toggleUserBlock = admin.toggleUserBlock;
window.deleteUserAdmin = admin.deleteUserAdmin;
window.handleAdminCreateUser = admin.handleAdminCreateUser;
window.openPasswordModal = admin.openPasswordModal;
window.handleAdminChangePassword = admin.handleAdminChangePassword;
window.openEditUserModal = admin.openEditUserModal;
window.toggleEditBranchSelection = admin.toggleEditBranchSelection;
window.handleAdminEditUser = admin.handleAdminEditUser;

// Branches
window.loadBranches = admin.loadBranches;
window.handleCreateBranch = admin.handleCreateBranch;
window.deleteBranch = admin.deleteBranch;
window.toggleBranchHorario = admin.toggleBranchHorario;
window.editBranch = admin.editBranch;
window.toggleBranch = admin.toggleBranch;
window.previewBranchLogo = admin.previewBranchLogo;
window.searchAddress = admin.searchAddress;

// Promotions
window.loadPromotionsAdmin = promos.loadPromotionsAdmin;
window.showCreatePromotionModal = promos.showCreatePromotionModal;
window.handleCreatePromotion = promos.handleCreatePromotion;
window.togglePromotion = promos.togglePromotion;
window.deletePromotion = promos.deletePromotion;
window.selectPromoIcon = promos.selectPromoIcon;

window.loadTabData = async (tabId) => {
    switch (tabId) {
        case 'live':
            stats.loadLiveStats();
            stats.loadRecentLogs();
            stats.loadOccupancy();
            break;
        case 'admin-reservations':
            window.loadAdminReservations();
            break;
        case 'users':
            admin.loadUsers();
            break;
        case 'finance':
            window.loadFinanceData();
            break;
        case 'promotions':
            promos.loadPromotionsAdmin();
            break;
        case 'branches':
            admin.loadBranches();
            break;
        case 'settings':
            admin.loadSettings();
            break;
    }
};

window.manualEntry = async () => {
    const plate = document.getElementById('manual-plate').value.trim().toUpperCase();
    if (!plate) return utils.showToast('Ingresá una patente');

    const res = await api.post(`/admin/manual-entry?plate=${plate}`);
    if (res.ok) {
        utils.showToast('Ingreso registrado');
        document.getElementById('manual-plate').value = '';
        stats.loadOccupancy();
        stats.loadLiveStats();
    } else {
        utils.showToast(res.error);
    }
};

window.loadAdminReservations = async () => {
    const status = document.getElementById('admin-res-filter-status')?.value || '';
    const sucursal = document.getElementById('admin-res-filter-sucursal')?.value || '';
    const res = await api.get(`/admin/reservations?estado=${status}&sucursal=${sucursal}`);
    
    if (res.ok) {
        const tbody = document.getElementById('admin-res-list');
        if (!tbody) return;
        
        // Guardamos globalmente para consulta de detalle sin re-petición si es necesario
        window.allReservations = res.data;

        tbody.innerHTML = res.data.map(r => `
            <tr>
                <td data-label="Cliente"><div class="user-name">${r.usuario_nombre || 'S/N'} ${r.usuario_apellido || ''}</div></td>
                <td data-label="Patente"><span class="plate-style">${r.patente}</span></td>
                <td data-label="Fecha">
                    <div class="flex-col gap-8">
                        <div class="text-small text-light">${utils.formatDate(r.fecha_inicio)}</div>
                        <div class="text-xs text-muted" style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 5px;">${utils.formatDate(r.fecha_fin)}</div>
                    </div>
                </td>
                <td data-label="Sucursal/Tipo">
                    <div class="flex-col gap-8">
                        <div class="text-small text-dorado font-bold">${r.sucursal_nombre}</div>
                        <div class="text-xs text-muted uppercase" style="letter-spacing: 1px;">${utils.toTitle(r.tipo_estadia)}</div>
                    </div>
                </td>
                <td data-label="Monto" class="text-bold text-white">$${r.monto_total.toLocaleString()}</td>
                <td data-label="Estado Pago"><span class="badge-status badge-${r.estado_pago.toLowerCase()}">${r.estado_pago}</span></td>
                <td data-label="Estado Reserva"><span class="badge-status badge-${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</span></td>
                <td data-label="Info">
                    <button class="btn-icon-premium sm" onclick="showReservationDetail(${r.id})" title="Ver detalle completo de la reserva"><i class="fas fa-eye"></i></button>
                </td>
            </tr>`).join('') || '<tr><td colspan="8" class="text-center py-20">No hay reservas.</td></tr>';
        
        const statTotal = document.getElementById('admin-res-stat-total');
        const statPending = document.getElementById('admin-res-stat-pending');
        if (statTotal) statTotal.innerText = res.data.length;
        if (statPending) statPending.innerText = res.data.filter(r => r.estado_reserva === 'Pendiente').length;
    }
};

window.showReservationDetail = (resId) => {
    const r = window.allReservations?.find(x => x.id === resId);
    if (!r) return;

    document.getElementById('res-detail-id').innerText = `#${r.id}`;
    document.getElementById('res-detail-user').innerText = `${r.usuario_nombre || 'S/N'} ${r.usuario_apellido || ''}`;
    document.getElementById('res-detail-plate').innerText = r.patente;
    document.getElementById('res-detail-start').innerText = utils.formatDate(r.fecha_inicio);
    document.getElementById('res-detail-end').innerText = utils.formatDate(r.fecha_fin);
    document.getElementById('res-detail-sucursal').innerText = r.sucursal_nombre;
    document.getElementById('res-detail-type').innerText = utils.toTitle(r.tipo_estadia);
    document.getElementById('res-detail-amount').innerText = `$${r.monto_total.toLocaleString()}`;

    const badgeContainer = document.getElementById('res-detail-status-badges');
    badgeContainer.innerHTML = `
        <span class="badge-status badge-${r.estado_pago.toLowerCase()}">${r.estado_pago}</span>
        <span class="badge-status badge-${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</span>
    `;

    if (window.openModal) window.openModal('modal-res-detail');
};

window.showLogDetail = async (logId) => {
    // Si no tenemos los logs cargados o necesitamos refrescar, pedimos
    const res = await api.get('/reports/access');
    if (!res.ok) return;
    
    const log = res.data.find(l => l.id === logId);
    if (!log) return;

    document.getElementById('audit-plate').innerText = log.patente_detectada;
    document.getElementById('audit-plate-overlay').innerText = log.patente_detectada;
    document.getElementById('audit-time').innerText = new Date(log.fecha_hora).toLocaleString('es-AR');
    document.getElementById('audit-type').innerText = log.tipo_evento;
    document.getElementById('audit-payment').innerText = log.pago_confirmado ? 'PAGADO' : 'PENDIENTE';
    document.getElementById('audit-res-id').innerText = log.reserva_id ? `#${log.reserva_id}` : 'SIN RESERVA';

    const imgEl = document.getElementById('audit-image');
    if (imgEl) {
        imgEl.src = `/v1/system/capture/${logId}?t=${Date.now()}`;
        // Ocultar overlay si no hay captura real
        document.getElementById('audit-overlay-container').style.display = 'block';
    }
    
    if (window.openModal) window.openModal('modal-log-detail');
};

let revenueChart = null;
let currentFinancePage = 1;
const financeLimit = 15;

window.loadFinanceData = async (resetPage = true) => {
    if (resetPage) currentFinancePage = 1;
    const period = document.getElementById('fin-period')?.value || 'month';
    
    // 1. Cargar Resumen (KPIs) - Siempre cargamos el total del periodo
    const resSum = await api.get(`/reports/financial-summary?period=${period}`);
    if (resSum.ok) {
        const data = resSum.data;
        const elTotal = document.getElementById('fin-total');
        const elRefund = document.getElementById('fin-refunded');
        const elCount = document.getElementById('fin-count');
        const elAvg = document.getElementById('fin-avg');

        if (elTotal) elTotal.innerText = `$${data.total_recaudado.toLocaleString()}`;
        if (elRefund) elRefund.innerText = `$${data.total_reembolsado.toLocaleString()}`;
        if (elCount) elCount.innerText = data.cantidad_pagos;
        if (elAvg) elAvg.innerText = `$${data.ticket_promedio.toLocaleString()}`;

        const elProy = document.getElementById('fin-proyectado');
        if (elProy) elProy.innerText = `$${data.ingresos_proyectados.toLocaleString()}`;

        const elCancel = document.getElementById('fin-cancel-rate');
        if (elCancel) elCancel.innerText = `${data.tasa_cancelacion || 0}%`;

        const elNoShow = document.getElementById('fin-noshow');
        if (elNoShow) elNoShow.innerText = `$${(data.ingresos_incumplimiento || 0).toLocaleString()}`;

        // Desglose por canal
        const d = data.desglose;
        if (d) {
            document.getElementById('fin-stay-monto').innerText = `$${(d.estadias?.monto || 0).toLocaleString()}`;
            document.getElementById('fin-stay-count').innerText = d.estadias?.cantidad || 0;
            document.getElementById('fin-stay-avg').innerText = `$${(d.estadias?.promedio || 0).toLocaleString()}`;

            document.getElementById('fin-res-monto').innerText = `$${(d.reservas?.monto || 0).toLocaleString()}`;
            document.getElementById('fin-res-count').innerText = d.reservas?.cantidad || 0;
            document.getElementById('fin-res-avg').innerText = `$${(d.reservas?.promedio || 0).toLocaleString()}`;
        }
    }

    // 2. Cargar Historial de Pagos (PAGINADO)
    const resHist = await api.get(`/reports/payment-history?period=${period}&page=${currentFinancePage}&limit=${financeLimit}`);
    if (resHist.ok) {
        const tbody = document.getElementById('payment-list');
        if (tbody) {
            tbody.innerHTML = resHist.data.map(p => {
                const isRefund = p.tipo === 'Reembolso';
                const rowClass = isRefund ? 'row-refund' : '';
                const amountClass = isRefund ? 'text-danger' : 'text-secondary';
                const badgeClass = isRefund ? 'badge-danger-light' : 'badge-success-light';
                
                return `
                <tr class="${rowClass}">
                    <td>${utils.formatDate(p.fecha_pago)}</td>
                    <td><span class="plate-style">${p.patente_detectada}</span>${isRefund ? ' <i class="fas fa-undo text-xs"></i>' : ''}</td>
                    <td class="text-bold ${amountClass}">$${p.costo_estadia.toLocaleString()}</td>
                    <td><span class="text-small">${p.tipo === 'Reserva' || p.tipo === 'Reembolso' ? 'MERCADO PAGO / ABONO' : 'SISTEMA DIGITAL'}</span></td>
                    <td><span class="${badgeClass}">${p.tipo.toUpperCase()}</span></td>
                </tr>
            `}).join('') || '<tr><td colspan="5" class="text-center py-20">No hay transacciones en este período.</td></tr>';
        }

        // 3. Actualizar UI Paginación
        const prevBtn = document.getElementById('prev-fin-btn');
        const nextBtn = document.getElementById('next-fin-btn');
        const pageInfo = document.getElementById('fin-page-info');

        if (prevBtn) prevBtn.disabled = currentFinancePage === 1;
        if (nextBtn) nextBtn.disabled = resHist.data.length < financeLimit;
        if (pageInfo) pageInfo.innerText = `Página ${currentFinancePage}`;

        // 4. Renderizar Gráfico con el total de transacciones (sin paginación) para mostrar la tendencia real
        const resChart = await api.get(`/reports/payment-history?period=${period}&limit=0`);
        if (resChart.ok) {
            renderRevenueChart(resChart.data, period);
        }
    }
};

window.nextFinancePage = () => {
    currentFinancePage++;
    window.loadFinanceData(false);
};

window.prevFinancePage = () => {
    if (currentFinancePage > 1) {
        currentFinancePage--;
        window.loadFinanceData(false);
    }
};

function renderRevenueChart(data, period) {
    const canvas = document.getElementById('revenueChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    if (revenueChart) {
        revenueChart.destroy();
    }

    // Agrupar y procesar datos cronológicamente
    const grouped = {};
    
    // Clonamos y damos vuelta para procesar de más viejo a más nuevo en el gráfico
    const sortedData = [...data].reverse();

    sortedData.forEach(p => {
        const date = new Date(p.fecha_pago || p.fecha_hora);
        let label;
        if (period === 'day') {
            label = date.getHours() + ':00';
        } else if (period === 'week' || period === 'month') {
            label = date.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' });
        } else {
            label = date.toLocaleDateString('es-AR', { month: 'short' });
        }
        grouped[label] = (grouped[label] || 0) + p.costo_estadia;
    });

    const labels = Object.keys(grouped);
    const values = Object.values(grouped);

    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Ingresos',
                data: values,
                borderColor: '#C5A059',
                backgroundColor: 'rgba(197, 160, 89, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: '#C5A059',
                pointBorderColor: '#000',
                pointBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: '#0a0a0a',
                    titleColor: '#C5A059',
                    bodyColor: '#fff',
                    borderColor: 'rgba(197, 160, 89, 0.3)',
                    borderWidth: 1,
                    displayColors: false,
                    callbacks: {
                        label: (context) => ` Recaudado: $${context.parsed.y.toLocaleString()}`
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: 'rgba(255,255,255,0.05)', drawBorder: false },
                    ticks: { 
                        color: '#666',
                        font: { size: 10 },
                        callback: (value) => '$' + value.toLocaleString()
                    }
                },
                x: {
                    grid: { display: false },
                    ticks: { color: '#666', font: { size: 10 } }
                }
            }
        }
    });
}

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', () => {
    // 1. Actualizar inmediatamente la UI con lo que tengamos en localStorage
    const rol = localStorage.getItem('rol');
    const sucursalRaw = localStorage.getItem('sucursal');
    
    // Debug: Eliminar en producción
    console.log(`[*] Sesión: Rol=${rol}, Sede=${sucursalRaw}`);

    // Limpieza profunda de la sede
    let sucursalLimpia = '';
    if (sucursalRaw && sucursalRaw !== 'null' && sucursalRaw !== 'undefined') {
        sucursalLimpia = sucursalRaw.replace('AUTOPASS ', '').trim();
    }
    
    // La clase de rol ya se aplica en el inline script de dashboard.html para evitar flicker
    
    const roleNameEl = document.getElementById('role-name');
    const settingsTitleEl = document.getElementById('settings-title');

    if (roleNameEl) {
        let label = 'Personal Autorizado';
        if (rol === 'admin') label = 'Administrador Global';
        else if (rol === 'local_admin') label = `Administrador ${sucursalLimpia || 'Sucursal'}`;
        else if (rol === 'staff') label = `Empleado ${sucursalLimpia || 'Sucursal'}`;
        roleNameEl.innerText = label;
    }

    if (settingsTitleEl) {
        if (rol === 'local_admin') {
            settingsTitleEl.innerText = `CONFIGURACIÓN DE SUCURSAL: ${sucursalLimpia.toUpperCase() || 'MI PUNTO'}`;
        } else {
            settingsTitleEl.innerText = 'CONFIGURACIÓN GLOBAL DEL SISTEMA';
        }
    }

    // 2. Iniciar servicios secundarios
    try {
        ui.initClock();
        ui.checkSystemHealth();
    } catch (e) { console.warn("Error en servicios UI:", e); }

    let lastTab = localStorage.getItem('activeAdminTab') || 'live';
    
    // Reglas de redirección por rol
    const restrictedStaff = ['users', 'finance', 'promotions', 'settings'];
    const restrictedAdmin = ['live', 'admin-reservations', 'finance', 'settings']; 

    if (rol === 'staff' && restrictedStaff.includes(lastTab)) {
        lastTab = 'live';
    } else if (rol === 'admin' && restrictedAdmin.includes(lastTab)) {
        lastTab = 'users'; 
    }

    const activeItem = document.querySelector(`.nav-item[onclick*="'${lastTab}'"]`);
    if (activeItem) ui.switchTab(lastTab, activeItem);

    // 3. Listeners de Formularios
    document.getElementById('form-add-branch')?.addEventListener('submit', window.handleCreateBranch);

    setInterval(() => {
        if (localStorage.getItem('activeAdminTab') === 'live') {
            stats.loadLiveStats();
            stats.loadRecentLogs();
            stats.loadOccupancy();
        }
    }, 10000);
});

window.payOccupancy = async (plate) => {
    if (!await showConfirm('Confirmar Pago', `¿Registrar pago manual para la patente <b>${plate}</b>?`)) return;

    const res = await api.post(`/access/pay-stay?plate=${plate}`);
    if (res.ok) { 
        utils.showToast('Pago procesado'); 
        stats.loadOccupancy(); 
        stats.loadLiveStats();
        if (document.getElementById('tab-finance').style.display !== 'none') {
            window.loadFinanceData();
        }
    }
    else utils.showToast(res.error);
};

window.cancelStay = stats.cancelStay;

window.manualExit = async (plate) => {
    if (!await showConfirm('Salida Manual', `¿Registrar salida de ${plate}?`)) return;
    const res = await api.post(`/admin/manual-exit?plate=${plate}`);
    if (res.ok) { utils.showToast('Salida registrada'); stats.loadOccupancy(); }
    else utils.showToast(res.error);
};

window.showCreateUserModal = admin.showCreateUserModal;
window.showCreateBranchModal = admin.showCreateBranchModal;
window.loadSettings = admin.loadSettings;
window.saveAllRates = admin.saveAllRates;
window.saveSystemParam = admin.saveSystemParam;
window.resetSys = admin.resetSys;
window.exportFinanceData = admin.exportFinanceData;
