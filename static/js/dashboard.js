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
window.switchMonitorTab = (tabId, element) => {
    // Buttons
    element.parentElement.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    element.classList.add('active');
    
    // Contents & Search Boxes
    document.querySelectorAll('.monitor-tab-content').forEach(content => content.classList.remove('active'));
    
    const targetTable = document.getElementById(`monitor-tab-${tabId}`);
    const targetSearch = document.getElementById(`search-container-${tabId}`);
    
    if (targetTable) targetTable.classList.add('active');
    if (targetSearch) targetSearch.classList.add('active');
};
window.toggleMobileNav = ui.toggleMobileNav;

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
window.showCreateUserModal = admin.showCreateUserModal;
window.deleteUserAdmin = admin.deleteUserAdmin;
window.handleAdminCreateUser = admin.handleAdminCreateUser;
window.openPasswordModal = admin.openPasswordModal;
window.handleAdminChangePassword = admin.handleAdminChangePassword;
window.openEditUserModal = admin.openEditUserModal;
window.toggleEditBranchSelection = admin.toggleEditBranchSelection;
window.handleAdminEditUser = admin.handleAdminEditUser;

// Settings & Navigation
window.switchSettingsTab = admin.switchSettingsTab;
window.switchRatesTab = admin.switchRatesTab;
window.refreshSystemDiagnostics = admin.refreshSystemDiagnostics;

// Branches
window.loadBranches = admin.loadBranches;
window.handleCreateBranch = admin.handleCreateBranch;
window.deleteBranch = admin.deleteBranch;
window.toggleBranchHorario = admin.toggleBranchHorario;
window.editBranch = admin.editBranch;
window.showBranchFloors = admin.showBranchFloors;
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
    const plateInput = document.getElementById('manual-plate');
    let plate = plateInput.value.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
    let type = document.getElementById('manual-type')?.value || 'Auto';
    const floorId = document.getElementById('manual-floor')?.value;
    
    if (!plate) return utils.showToast('Ingresá una patente');

    // Detección automática de Moto (Formato: 1 letra, 3 números, 3 letras)
    const isMoto = /^[A-Z]{1}[0-9]{3}[A-Z]{3}$/.test(plate);
    if (isMoto) {
        type = 'Moto';
    }

    // Confirmación mediante alerta premium (Estilo unificado)
    const confirmed = await utils.showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-dorado" style="letter-spacing: 1px;">
                ${utils.formatPlate(plate)}
            </div>
            <div style="text-transform: uppercase;">
                TIPO: ${isMoto ? 'MOTO' : 'AUTO'}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Confirmar el registro?
            </div>
        </div>`
    );
    
    if (!confirmed) return;

    let url = `/admin/manual-entry?plate=${plate}&tipo_vehiculo=${type}`;
    if (floorId) url += `&floor_id=${floorId}`;

    const res = await api.post(url);
    if (res.ok) {
        utils.showToast('Ingreso registrado con éxito', 'success');
        plateInput.value = '';
        stats.loadOccupancy();
        stats.loadLiveStats();
    } else {
        utils.showToast(res.error || 'Error al registrar ingreso', 'error');
    }
};

window.loadAdminReservations = async () => {
    const status = document.getElementById('admin-res-filter-status')?.value || '';
    const res = await api.get(`/admin/reservations?estado=${status}`);
    
    if (res.ok) {
        const tbody = document.getElementById('admin-res-list');
        if (!tbody) return;
        
        // Guardamos globalmente para consulta de detalle sin re-petición si es necesario
        window.allReservations = res.data;

        tbody.innerHTML = res.data.map(r => `
            <tr class="row-premium">
                <td data-label="Cliente"><div class="user-name">${r.usuario_nombre || 'S/N'} ${r.usuario_apellido || ''}</div></td>
                <td data-label="Patente"><span class="plate-style">${r.patente}</span></td>
                <td data-label="Fecha">
                    <div class="flex-col items-center gap-8">
                        <div class="text-small text-light">${utils.formatDate(r.fecha_inicio)}</div>
                        <div class="text-xs text-muted" style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 5px;">${utils.formatDate(r.fecha_fin)}</div>
                    </div>
                </td>
                <td data-label="Tipo">
                    <div class="flex-col items-center gap-8">
                        <div class="text-small text-dorado font-bold uppercase" style="letter-spacing: 1px;">${utils.toTitle(r.tipo_estadia)}</div>
                    </div>
                </td>
                <td data-label="Monto" class="text-bold text-white">$${r.monto_total.toLocaleString()}</td>
                <td data-label="Estado Pago"><span class="badge-status badge-${r.estado_pago.toLowerCase()}">${r.estado_pago}</span></td>
                <td data-label="Estado Reserva"><span class="badge-status badge-${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</span></td>
                <td data-label="Acciones">
                    <div class="flex-row gap-8 justify-center actions-reveal">
                        <button class="btn-icon-premium sm" onclick="openEditReservationModal(${r.id})" title="Editar Reserva">
                            <i class="fas fa-pen-to-square"></i>
                        </button>
                        <button class="btn-icon-premium sm danger" onclick="cancelReservationAdmin(${r.id})" title="Cancelar Reserva">
                            <i class="fas fa-xmark"></i>
                        </button>
                    </div>
                </td>
            </tr>`).join('') || '<tr><td colspan="8" class="text-center py-20">No hay reservas.</td></tr>';
        
        const statTotal = document.getElementById('admin-res-stat-total');
        const statPending = document.getElementById('admin-res-stat-pending');
        if (statTotal) statTotal.innerText = res.data.length;
        if (statPending) statPending.innerText = res.data.filter(r => r.estado_reserva === 'Pendiente').length;
    }
};

window.updateEditReservationPrice = async () => {
    const type = document.getElementById('edit-res-tipo').value;
    const resId = document.getElementById('edit-res-id').value;
    const r = window.allReservations?.find(x => x.id == resId);
    if (!r) return;

    let inicio, fin;
    try {
        if (type === 'hora') {
            const fecha = document.getElementById('edit-res-date-only').value;
            const hora = document.getElementById('edit-res-time-only').value;
            const qty = parseInt(document.getElementById('edit-res-hours-qty').value) || 1;
            if (fecha && hora) {
                inicio = new Date(`${fecha}T${hora}`);
                fin = new Date(inicio.getTime() + qty * 3600000);
            }
        } else if (type === 'dia') {
            const fecha = document.getElementById('edit-res-day-only').value;
            if (fecha) {
                inicio = new Date(`${fecha}T00:00`);
                fin = new Date(`${fecha}T23:59`);
            }
        } else if (['semana', 'quincena', 'mes'].includes(type)) {
            const periods = { 'semana': 7, 'quincena': 15, 'mes': 30 };
            const startMap = { 'semana': 'edit-res-week-start', 'quincena': 'edit-res-fortnight-start', 'mes': 'edit-res-month-start' };
            const startVal = document.getElementById(startMap[type]).value;
            
            // Si no hay fecha, no mostrar precio todavía
            if (!startVal) {
                const elMonto = document.getElementById('edit-res-monto-total');
                if (elMonto) elMonto.innerText = `$ ---`;
                return;
            }

            inicio = new Date(startVal.replace(/-/g, "/"));
            fin = new Date(inicio.getTime() + (periods[type] - 1) * 24 * 60 * 60 * 1000);
            fin.setHours(23, 59, 59);
        } else {
            const sVal = document.getElementById('edit-res-inicio').value;
            const fVal = document.getElementById('edit-res-fin').value;
            if (sVal && fVal) {
                inicio = new Date(sVal);
                fin = new Date(fVal);
            }
        }

        if (inicio && fin && !isNaN(inicio.getTime()) && !isNaN(fin.getTime())) {
            // Lógica específica: Para 'hora', solo mostrar si hay cantidad de horas válida
            if (type === 'hora') {
                const qty = parseInt(document.getElementById('edit-res-hours-qty').value);
                if (isNaN(qty) || qty <= 0) {
                    const elMonto = document.getElementById('edit-res-monto-total');
                    if (elMonto) elMonto.innerText = `$ ---`;
                    return;
                }
            }

            const durationHours = (fin - inicio) / 3600000;
            
            // Usar API para obtener tarifas actualizadas de la sucursal
            const resRates = await api.get(`/admin/branches`);
            let rates = { hora: 1500, dia: 15000, semana: 70000, quincena: 120000, mes: 200000 };
            
            if (resRates.ok && Array.isArray(resRates.data)) {
                const branch = resRates.data.find(b => b.nombre.trim() === r.sucursal_nombre.trim());
                if (branch) {
                    rates = {
                        hora: branch.tarifa_hora || 1500,
                        dia: branch.tarifa_dia || 15000,
                        semana: branch.tarifa_semana || 70000,
                        quincena: branch.tarifa_quincena || 120000,
                        mes: branch.tarifa_mes || 200000
                    };
                }
            }

            let total = 0;
            if (type === 'hora') total = Math.ceil(durationHours) * rates.hora;
            else if (type === 'dia') total = Math.max(1, Math.ceil(durationHours / 24)) * rates.dia;
            else if (type === 'semana') total = Math.ceil(durationHours / (24 * 7)) * rates.semana;
            else if (type === 'quincena') total = Math.ceil(durationHours / (24 * 15)) * rates.quincena;
            else if (type === 'mes') total = Math.ceil(durationHours / (24 * 30)) * rates.mes;
            else total = Math.ceil(durationHours) * rates.hora;

            const elMonto = document.getElementById('edit-res-monto-total');
            if (elMonto) elMonto.innerText = `$ ${total.toLocaleString()}`;
        } else {
            const elMonto = document.getElementById('edit-res-monto-total');
            if (elMonto) elMonto.innerText = `$ ---`;
        }
    } catch (e) { 
        console.error("Error recalc price:", e);
        const elMonto = document.getElementById('edit-res-monto-total');
        if (elMonto) elMonto.innerText = `$ 0`;
    }
};

window.updateEditFormGroups = (type) => {
    const sections = {
        'hora': document.getElementById('edit-hourly-fields'),
        'dia': document.getElementById('edit-daily-fields'),
        'semana': document.getElementById('edit-weekly-fields'),
        'quincena': document.getElementById('edit-fortnight-fields'),
        'mes': document.getElementById('edit-month-fields'),
        'standard': document.getElementById('edit-standard-fields')
    };

    Object.values(sections).forEach(s => { if(s) s.style.display = 'none'; });
    const activeSection = sections[type] || sections['standard'];
    if (activeSection) {
        // Usar el atributo data-display si existe, sino grid por defecto
        activeSection.style.display = activeSection.dataset.display || 'grid';
    }
    window.updateEditReservationPrice();
};

const updateEditPeriodEnd = (startDateStr, days, targetSelector) => {
    if (!startDateStr) return;
    const endInput = document.querySelector(targetSelector);
    if (!endInput) return;
    
    const start = new Date(startDateStr.replace(/-/g, "/"));
    const end = new Date(start.getTime() + (days - 1) * 24 * 60 * 60 * 1000);
    const day = end.getDate().toString().padStart(2, '0');
    const month = (end.getMonth() + 1).toString().padStart(2, '0');
    const year = end.getFullYear();
    endInput.value = `${day}/${month}/${year} 23:59`;
    window.updateEditReservationPrice();
};

window.openEditReservationModal = (resId) => {
    const r = window.allReservations?.find(x => x.id === resId);
    if (!r) return;

    // Inicializar Flatpickrs si es necesario
    if (window.flatpickr && !window.editPickersInitialized) {
        const common = { 
            disableMobile: "true", 
            altInput: true,
            altFormat: "d-m-Y",
            dateFormat: "Y-m-d", 
            onChange: () => window.updateEditReservationPrice() 
        };
        flatpickr("#edit-res-date-only", common);
        flatpickr("#edit-res-day-only", common);
        flatpickr("#edit-res-time-only", { 
            enableTime: true, 
            noCalendar: true, 
            dateFormat: "H:i", 
            defaultHour: 12, 
            defaultMinute: 0,
            disableMobile: "true",
            onChange: () => window.updateEditReservationPrice() 
        });
        flatpickr("#edit-res-week-start", { ...common, onChange: (sd, ds) => updateEditPeriodEnd(ds, 7, '#edit-res-week-end') });
        flatpickr("#edit-res-fortnight-start", { ...common, onChange: (sd, ds) => updateEditPeriodEnd(ds, 15, '#edit-res-fortnight-end') });
        flatpickr("#edit-res-month-start", { ...common, onChange: (sd, ds) => updateEditPeriodEnd(ds, 30, '#edit-res-month-end') });
        
        document.getElementById('edit-res-hours-qty')?.addEventListener('input', () => window.updateEditReservationPrice());
        
        window.editPickersInitialized = true;
    }

    document.getElementById('edit-res-id').value = r.id;
    document.getElementById('edit-res-title').innerText = `EDITAR RESERVA #${r.id}`;
    document.getElementById('edit-res-patente').value = r.patente;
    document.getElementById('edit-res-tipo').value = r.tipo_estadia;
    document.getElementById('edit-res-pago').value = r.estado_pago;
    document.getElementById('edit-res-reserva').value = r.estado_reserva;

    window.updateEditFormGroups(r.tipo_estadia);

    // Poblar campos dinámicos
    const startParts = r.fecha_inicio.split(' ');
    const dateOnly = startParts[0];
    const timeOnly = startParts[1] ? startParts[1].substring(0, 5) : "00:00";

    if (r.tipo_estadia === 'hora') {
        document.getElementById('edit-res-date-only').value = dateOnly;
        document.getElementById('edit-res-time-only').value = timeOnly;
        const s = new Date(r.fecha_inicio.replace(/-/g, "/"));
        const e = new Date(r.fecha_fin.replace(/-/g, "/"));
        const hours = Math.ceil((e - s) / 3600000);
        document.getElementById('edit-res-hours-qty').value = hours || 1;
    } else if (r.tipo_estadia === 'dia') {
        document.getElementById('edit-res-day-only').value = dateOnly;
    } else if (r.tipo_estadia === 'semana') {
        document.getElementById('edit-res-week-start').value = dateOnly;
        updateEditPeriodEnd(dateOnly, 7, '#edit-res-week-end');
    } else if (r.tipo_estadia === 'quincena') {
        document.getElementById('edit-res-fortnight-start').value = dateOnly;
        updateEditPeriodEnd(dateOnly, 15, '#edit-res-fortnight-end');
    } else if (r.tipo_estadia === 'mes') {
        document.getElementById('edit-res-month-start').value = dateOnly;
        updateEditPeriodEnd(dateOnly, 30, '#edit-res-month-end');
    } else {
        const formatForInput = (dateStr) => {
            if (!dateStr) return '';
            const d = new Date(dateStr.replace(/-/g, "/"));
            if (isNaN(d.getTime())) return dateStr.replace(' ', 'T').substring(0, 16);
            return d.toISOString().substring(0, 16);
        };
        document.getElementById('edit-res-inicio').value = formatForInput(r.fecha_inicio);
        document.getElementById('edit-res-fin').value = formatForInput(r.fecha_fin);
    }

    const elMonto = document.getElementById('edit-res-monto-total');
    if (elMonto) elMonto.innerText = `$ ${r.monto_total.toLocaleString()}`;

    if (window.openModal) window.openModal('modal-edit-reservation');
};

window.handleAdminEditReservation = async (event) => {
    event.preventDefault();
    const resId = document.getElementById('edit-res-id').value;
    const btn = event.target.querySelector('button[type="submit"]');
    const tipo = document.getElementById('edit-res-tipo').value;

    let inicio, fin;
    try {
        if (tipo === 'hora') {
            const fecha = document.getElementById('edit-res-date-only').value;
            const hora = document.getElementById('edit-res-time-only').value;
            const qty = parseInt(document.getElementById('edit-res-hours-qty').value) || 1;
            if (!fecha || !hora) throw new Error("Seleccioná fecha y hora");
            inicio = `${fecha} ${hora}`;
            const s = new Date(`${fecha}T${hora}`);
            const f = new Date(s.getTime() + qty * 3600000);
            fin = `${f.getFullYear()}-${(f.getMonth()+1).toString().padStart(2,'0')}-${f.getDate().toString().padStart(2,'0')} ${f.getHours().toString().padStart(2,'0')}:${f.getMinutes().toString().padStart(2,'0')}`;
        } else if (tipo === 'dia') {
            const fecha = document.getElementById('edit-res-day-only').value;
            if (!fecha) throw new Error("Seleccioná un día");
            inicio = `${fecha} 00:00`;
            fin = `${fecha} 23:59`;
        } else if (['semana', 'quincena', 'mes'].includes(tipo)) {
            const periods = { 'semana': 7, 'quincena': 15, 'mes': 30 };
            const startMap = { 'semana': 'edit-res-week-start', 'quincena': 'edit-res-fortnight-start', 'mes': 'edit-res-month-start' };
            const startVal = document.getElementById(startMap[tipo]).value;
            if (!startVal) throw new Error("Seleccioná fecha de inicio");
            inicio = `${startVal} 00:00`;
            const s = new Date(startVal.replace(/-/g, "/"));
            const f = new Date(s.getTime() + (periods[tipo] - 1) * 24 * 60 * 60 * 1000);
            fin = `${f.getFullYear()}-${(f.getMonth()+1).toString().padStart(2,'0')}-${f.getDate().toString().padStart(2,'0')} 23:59`;
        } else {
            inicio = document.getElementById('edit-res-inicio').value.replace('T', ' ');
            fin = document.getElementById('edit-res-fin').value.replace('T', ' ');
        }
    } catch (e) {
        return utils.showToast(e.message);
    }

    const payload = {
        patente: document.getElementById('edit-res-patente').value.toUpperCase(),
        tipo_estadia: tipo,
        fecha_inicio: inicio,
        fecha_fin: fin,
        estado_pago: document.getElementById('edit-res-pago').value,
        estado_reserva: document.getElementById('edit-res-reserva').value
    };

    btn.disabled = true;
    const res = await api.patch(`/admin/reservations/${resId}`, payload);
    if (res.ok) {
        utils.showToast('Reserva actualizada correctamente');
        if (window.closeModal) window.closeModal('modal-edit-reservation');
        window.loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al actualizar reserva');
    }
    btn.disabled = false;
};

window.cancelReservationAdmin = async (resId) => {
    if (!await utils.showConfirm('Cancelar Reserva', '¿Estás seguro de cancelar esta reserva?')) return;
    
    const res = await api.post(`/admin/reservations/${resId}/cancel`);
    if (res.ok) {
        utils.showToast(res.data.message || 'Reserva cancelada');
        window.loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al cancelar reserva');
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

window.toggleFinanceDateFilter = () => {
    const period = document.getElementById('fin-period').value;
    const dateGroup = document.getElementById('fin-date-group');
    const dateInput = document.getElementById('fin-date');
    
    if (period === 'specific') {
        dateGroup.style.display = 'flex';
        if (!dateInput.value) {
            dateInput.value = new Date().toISOString().split('T')[0];
        }
    } else {
        dateGroup.style.display = 'none';
    }
    window.loadFinanceData();
};

window.loadFinanceData = async (resetPage = true) => {
    if (resetPage) currentFinancePage = 1;
    const period = document.getElementById('fin-period')?.value || 'month';
    const specificDate = document.getElementById('fin-date')?.value;
    const vehicleType = document.getElementById('fin-vehicle-type')?.value || 'all';
    const paymentMethod = document.getElementById('fin-payment-method')?.value || 'all';
    
    let urlParams = `period=${period}&vehicle_type=${vehicleType}&payment_method=${paymentMethod}`;
    if (period === 'specific' && specificDate) {
        urlParams = `period=day&start=${specificDate}T00:00:00&end=${specificDate}T23:59:59&vehicle_type=${vehicleType}&payment_method=${paymentMethod}`;
    }
    
    // 1. Cargar Resumen (KPIs)
    const resSum = await api.get(`/reports/financial-summary?${urlParams}`);
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
    const resHist = await api.get(`/reports/payment-history?${urlParams}&page=${currentFinancePage}&limit=${financeLimit}`);
    if (resHist.ok) {
        const tbody = document.getElementById('payment-list');
        if (tbody) {
            tbody.innerHTML = resHist.data.map(p => {
                const isRefund = p.tipo === 'Reembolso';
                const rowClass = isRefund ? 'row-refund' : '';
                const amountClass = isRefund ? 'text-danger' : 'text-secondary';
                const badgeClass = isRefund ? 'badge-danger-light' : 'badge-success-light';
                
                let metodoPago = 'PAGO DIGITAL';
                if (p.metodo === 'CAJA') {
                    metodoPago = 'PAGO EN CAJA';
                }

                return `
                <tr class="${rowClass}">
                    <td><span class="text-light">${utils.formatDate(p.fecha_pago)}</span></td>
                    <td><span class="plate-style">${p.patente_detectada}</span>${isRefund ? ' <i class="fas fa-undo text-xs"></i>' : ''}</td>
                    <td class="text-bold ${amountClass}">$${p.costo_estadia.toLocaleString()}</td>
                    <td><span class="text-small">${metodoPago}</span></td>
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
        const resChart = await api.get(`/reports/payment-history?${urlParams}&limit=0`);
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
        revenueChart = null;
    }

    // Si no hay datos, mostrar mensaje o gráfico vacío limpio
    if (!data || data.length === 0) {
        // Opcional: mostrar un mensaje en el canvas o simplemente un gráfico vacío
        console.warn("No hay datos para el gráfico financiero");
    }

    // Agrupar y procesar datos cronológicamente
    const grouped = {};
    
    // Función auxiliar para parsear fechas de forma segura
    const parseDate = (str) => {
        if (!str) return new Date(NaN);
        // Normalizar formato: reemplaza espacios por T si es necesario (para Safari/otros)
        return new Date(str.replace(' ', 'T'));
    };

    // Clonamos y ordenamos cronológicamente (antiguo a nuevo)
    const sortedData = [...data].sort((a, b) => parseDate(a.fecha_pago) - parseDate(b.fecha_pago));

    sortedData.forEach(p => {
        const date = parseDate(p.fecha_pago);
        if (isNaN(date.getTime())) return;

        let label;
        if (period === 'day' || period === 'specific') {
            label = date.getHours() + ':00';
        } else if (period === 'week' || period === 'month') {
            label = date.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' });
        } else {
            label = date.toLocaleDateString('es-AR', { month: 'short' });
        }
        
        const monto = parseFloat(p.costo_estadia) || 0;
        grouped[label] = (grouped[label] || 0) + monto;
    });

    const labels = Object.keys(grouped);
    const values = Object.values(grouped);

    revenueChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels.length > 0 ? labels : ['Sin datos'],
            datasets: [{
                label: 'Ingresos',
                data: values.length > 0 ? values : [0],
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
                        label: (context) => {
                            const val = context.parsed.y || 0;
                            return ` Recaudado: $${val.toLocaleString()}`;
                        }
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
        settingsTitleEl.innerText = 'CONFIGURACIÓN';
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

window.payOccupancy = async (plate, amount) => {
    // Confirmación mediante alerta premium (Estilo unificado)
    const confirmed = await utils.showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-dorado" style="letter-spacing: 1px;">
                ${utils.formatPlate(plate)}
            </div>
            <div>
                MONTO: $${(amount || 0).toLocaleString('es-AR')}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Confirmar el pago?
            </div>
        </div>`
    );

    if (!confirmed) return;

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

window.manualExit = async (plate, type) => {
    // Confirmación mediante alerta premium (Estilo unificado)
    const confirmed = await utils.showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-dorado" style="letter-spacing: 1px;">
                ${utils.formatPlate(plate)}
            </div>
            <div style="text-transform: uppercase;">
                TIPO: ${type || 'AUTO'}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Confirmar la salida?
            </div>
        </div>`
    );

    if (!confirmed) return;
    
    const res = await api.post(`/admin/manual-exit?plate=${plate}`);
    if (res.ok) { 
        utils.showToast('Salida registrada'); 
        stats.loadOccupancy(); 
        stats.loadLiveStats();
    }
    else utils.showToast(res.error);
};

window.createBranch = admin.handleCreateBranch;
window.showCreateBranchModal = admin.showCreateBranchModal;
window.loadSettings = admin.loadSettings;
window.saveAllRates = admin.saveAllRates;
window.toggleRateEdit = admin.toggleRateEdit;
window.saveRateGroup = admin.saveRateGroup;
window.saveCapacities = admin.saveCapacities;
window.saveSystemParam = admin.saveSystemParam;
window.resetSys = admin.resetSys;
window.exportFinanceData = admin.exportFinanceData;

// Floors
window.openAddFloorModal = admin.openAddFloorModal;
window.openEditFloorModal = admin.openEditFloorModal;
window.handleCreateFloor = admin.handleCreateFloor;
window.deleteFloor = admin.deleteFloor;
window.updateFloorCapacity = admin.updateFloorCapacity;
window.savePBCapacity = admin.savePBCapacity;
window.toggleLevelEdit = admin.toggleLevelEdit;
