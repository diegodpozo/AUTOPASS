import api from './api.js';
import * as utils from './utils.js';
import * as baseUi from './ui.js';
import { getVirtualNow } from './virtual-time.js';

/**
 * Módulo de Gestión de Reservas Administrativas
 */

let allReservations = [];

export function getAllReservations() {
    return allReservations;
}

export async function loadAdminReservations() {
    const status = document.getElementById('admin-res-filter-status')?.value || '';
    const res = await api.get(`/admin/reservations?estado=${status}`);
    
    if (res.ok) {
        const tbody = document.getElementById('admin-res-list');
        if (!tbody) return;
        
        allReservations = res.data;
        window.allReservations = allReservations;

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
                <td data-label="Monto" class="text-bold text-white">$${utils.formatNum(r.monto_total)}</td>
                <td data-label="Estado Pago"><span class="badge-status badge-${r.estado_pago.toLowerCase()}">${r.estado_pago}</span></td>
                <td data-label="Estado Reserva">
                    <div class="flex-col items-center gap-8">
                        <span class="badge-status badge-${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</span>
                        ${r.estado_reserva !== 'Completada' && r.estado_reserva !== 'Cancelada'
                            ? (r.en_predio
                                ? '<span style="display:inline-flex; align-items:center; gap:6px; font-size:0.7rem; font-weight:700; color:#10b981;"><i class="fas fa-circle-dot"></i> EN PREDIO</span>'
                                : '<span style="display:inline-flex; align-items:center; gap:6px; font-size:0.7rem; font-weight:700; color:#8b93a6;"><i class="fas fa-circle" style="font-size:0.5rem;"></i> FUERA</span>')
                            : ''}
                    </div>
                </td>
                <td data-label="Acciones">
                    <div class="flex-row gap-8 justify-center actions-reveal">
                        ${r.estado_reserva !== 'Completada' && r.estado_reserva !== 'Cancelada' ? `
                        ${r.estado_pago === 'Pendiente' ? `
                        <button class="btn-icon-premium sm btn-confirm-payment" onclick="payReservationAdmin(${r.id})" title="Pago Manual">
                            <i class="fas fa-money-bill-wave"></i>
                        </button>
                        ` : ''}
                        <button class="btn-icon-premium sm danger" onclick="cancelReservationAdmin(${r.id})" title="Cancelar Reserva">
                            <i class="fas fa-xmark"></i>
                        </button>
                        ` : `<span class="text-xs text-muted">—</span>`}
                    </div>
                </td>
            </tr>`).join('') || '<tr><td colspan="8" class="text-center py-20">No hay reservas.</td></tr>';
        
        const statTotal = document.getElementById('admin-res-stat-total');
        const statPending = document.getElementById('admin-res-stat-pending');
        const statPresence = document.getElementById('admin-res-stat-presence');
        if (statTotal) statTotal.innerText = utils.formatNum(res.data.length);
        if (statPending) statPending.innerText = utils.formatNum(res.data.filter(r => r.estado_reserva === 'Pendiente').length);
        if (statPresence) statPresence.innerText = utils.formatNum(res.data.filter(r => r.en_predio).length);
    }
}

export async function payReservationAdmin(resId) {
    const metodo = await utils.showChoice('Pago Manual', '¿Con qué método abonó el cliente?', [
        { label: 'Efectivo', icon: 'fa-money-bill-wave' },
        { label: 'Mercado Pago', icon: 'fa-wallet' },
        { label: 'Transferencia', icon: 'fa-building-columns' },
        { label: 'Tarjeta', icon: 'fa-credit-card' },
        { label: 'Otro', icon: 'fa-circle-question' }
    ]);
    if (!metodo) return;
    
    const res = await api.post(`/admin/reservations/${resId}/confirm-payment`, { metodo_pago: metodo });
    if (res.ok) {
        utils.showToast('Pago registrado correctamente', 'success');
        loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al registrar pago', 'error');
    }
}

export async function cancelReservationAdmin(resId) {
    if (!await utils.showConfirm('Cancelar Reserva', '¿Estás seguro de cancelar esta reserva?')) return;
    
    const res = await api.post(`/admin/reservations/${resId}/cancel`);
    if (res.ok) {
        utils.showToast(res.data.message || 'Reserva cancelada', 'success');
        loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al cancelar reserva', 'error');
    }
}

export function showReservationDetail(resId) {
    const r = allReservations.find(x => x.id === resId) || window.allReservations?.find(x => x.id === resId);
    if (!r) return;

    document.getElementById('res-detail-id').innerText = `#${r.id}`;
    document.getElementById('res-detail-user').innerText = `${r.usuario_nombre || 'S/N'} ${r.usuario_apellido || ''}`;
    document.getElementById('res-detail-plate').innerText = r.patente;
    document.getElementById('res-detail-start').innerText = utils.formatDate(r.fecha_inicio);
    document.getElementById('res-detail-end').innerText = utils.formatDate(r.fecha_fin);
    document.getElementById('res-detail-sucursal').innerText = r.sucursal_nombre;
    document.getElementById('res-detail-type').innerText = utils.toTitle(r.tipo_estadia);
    document.getElementById('res-detail-amount').innerText = `$${utils.formatNum(r.monto_total)}`;

    const badgeContainer = document.getElementById('res-detail-status-badges');
    if (badgeContainer) {
        badgeContainer.innerHTML = `
            <span class="badge-status badge-${r.estado_pago.toLowerCase()}">${r.estado_pago}</span>
            <span class="badge-status badge-${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</span>
            ${r.estado_reserva !== 'Completada' && r.estado_reserva !== 'Cancelada'
                ? (r.en_predio
                    ? '<span style="display:inline-flex; align-items:center; gap:6px; font-size:0.72rem; font-weight:700; color:#10b981;"><i class="fas fa-circle-dot"></i> EN PREDIO</span>'
                    : '<span style="display:inline-flex; align-items:center; gap:6px; font-size:0.72rem; font-weight:700; color:#8b93a6;"><i class="fas fa-circle" style="font-size:0.5rem;"></i> FUERA DEL PREDIO</span>')
                : ''}
        `;
    }

    if (baseUi.openModal) baseUi.openModal('modal-res-detail');
}

// ==========================================================================
// NUEVA RESERVA MANUAL (PANEL ADMIN / STAFF) - CREAR + PAGAR EN UN PASO
// ==========================================================================

let newResPickersInitialized = false;
let newResBranches = [];
let newResLinkedUserId = null;
let newResPatenteLookupTimer = null;
let newResRatesFallback = { hora: 1500, dia: 15000, semana: 70000, quincena: 120000, mes: 200000 };

function _newResYmd(dt) {
    return `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`;
}

export function updateNewVehicleTypeIcon(type) {
    const icon = document.getElementById('new-res-veh-icon');
    if (icon) {
        if (type === 'Moto') icon.className = 'fas fa-motorcycle';
        else if (type === 'Camioneta') icon.className = 'fas fa-truck-pickup';
        else icon.className = 'fas fa-car-side';
    }
updateNewReservationPrice();
    if (typeof updateNewHourlySlotsUI === 'function') updateNewHourlySlotsUI();
}

export function resetNewResPatenteLookup() {
    clearTimeout(newResPatenteLookupTimer);
    newResLinkedUserId = null;
    const badge = document.getElementById('new-res-patente-owner-badge');
    if (badge) {
        badge.style.display = 'none';
        const span = badge.querySelector('span');
        if (span) span.textContent = '';
    }
    const iconEl = document.getElementById('new-res-veh-icon');
    if (iconEl) iconEl.className = 'fas fa-car-side';
}

export function clearNewResPatenteLookup() {
    resetNewResPatenteLookup();
    const tipo = document.getElementById('new-res-tipo-vehiculo');
    if (tipo) tipo.value = 'Auto';
    updateNewVehicleTypeIcon('Auto');
}

async function lookupNewResPatente() {
    const input = document.getElementById('new-res-patente');
    const badge = document.getElementById('new-res-patente-owner-badge');
    if (!badge) return;
    const patenteRaw = (input?.value || '').trim();
    if (patenteRaw.length < 4) {
        resetNewResPatenteLookup();
        return;
    }
    const res = await api.get('/admin/reservations/patente-lookup', { params: { patente: patenteRaw } });
    if (!res.ok) {
        resetNewResPatenteLookup();
        return;
    }
    const badgeIcon = badge.querySelector('i');
    const badgeText = badge.querySelector('span');
    if (res.data.encontrado) {
        newResLinkedUserId = res.data.user_id;
        badgeIcon.className = 'fas fa-user-check';
        badgeText.textContent = `${res.data.nombre} ${res.data.apellido} (${res.data.tipo_vehiculo})`;
        badge.style.color = '#27ae60';
        badge.style.background = 'transparent';
        badge.style.display = 'inline-flex';
        const tipo = document.getElementById('new-res-tipo-vehiculo');
        if (tipo && res.data.tipo_vehiculo) {
            tipo.value = res.data.tipo_vehiculo;
            updateNewVehicleTypeIcon(res.data.tipo_vehiculo);
        }
    } else {
        newResLinkedUserId = null;
        badgeIcon.className = 'fas fa-user-slash';
        badgeText.textContent = 'Patente no registrada';
        badge.style.color = '#e74c3c';
        badge.style.background = 'transparent';
        badge.style.display = 'inline-flex';
    }
}

export function initNewResPatenteLookup() {
    const input = document.getElementById('new-res-patente');
    if (!input) return;
    input.addEventListener('input', () => {
        clearTimeout(newResPatenteLookupTimer);
        newResPatenteLookupTimer = setTimeout(lookupNewResPatente, 450);
    });
}

export async function openNewReservationModal() {
    const formEl = document.getElementById('form-new-reservation');
    if (formEl) formEl.reset();

    const now = getVirtualNow();
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    const todayYmd = _newResYmd(now);
    const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };

    setVal('new-res-patente', '');
    resetNewResPatenteLookup();
    initNewResPatenteLookup();
    setVal('new-res-tipo', 'hora');
    setVal('new-res-tipo-vehiculo', 'Auto');
    setVal('new-res-metodo-pago', 'Efectivo');
    setVal('new-res-date-only', todayYmd);
    setVal('new-res-time-only', `${hh}:${mm}`);
    setVal('new-res-hours-qty', '1');
    setVal('new-res-day-only', todayYmd);
    setVal('new-res-week-start', todayYmd);
    setVal('new-res-fortnight-start', todayYmd);
    setVal('new-res-month-start', todayYmd);
    setVal('new-res-inicio', `${todayYmd}T${hh}:${mm}`);
    setVal('new-res-fin', `${todayYmd}T${hh}:${mm}`);
    updateNewVehicleTypeIcon('Auto');
    updateNewPeriodEnd(todayYmd, 7, '#new-res-week-end');
    updateNewPeriodEnd(todayYmd, 15, '#new-res-fortnight-end');
    updateNewPeriodEnd(todayYmd, 30, '#new-res-month-end');

    newSlotRangeStart = null;
    newSlotRangeEnd = null;
    newSlotRangeDate = null;
    const slotGrid = document.getElementById('new-hourly-slots-grid');
    const slotBadge = document.getElementById('new-availability-badge');
    const slotContainer = document.getElementById('new-availability-status-container');
    if (slotGrid) { slotGrid.innerHTML = ''; slotGrid.style.display = 'none'; }
    if (slotBadge) slotBadge.style.display = 'none';
    if (slotContainer) slotContainer.style.display = 'none';

    const montoEl = document.getElementById('new-res-monto-total');
    if (montoEl) montoEl.innerText = '$ ---';
    updateNewFormGroups('hora');

    const resBranches = await api.get('/admin/branches');
    if (resBranches.ok && Array.isArray(resBranches.data)) {
        newResBranches = resBranches.data;
    }

    const sucursalInput = document.getElementById('new-res-sucursal');
    if (sucursalInput) {
        const mySucursal = (localStorage.getItem('sucursal') || '').replace('AUTOPASS ', '').trim();
        const branch = (newResBranches || []).find(b =>
            b.nombre.trim().toLowerCase() === mySucursal.trim().toLowerCase() ||
            b.nombre.trim().toLowerCase().includes(mySucursal.trim().toLowerCase())
        );
        sucursalInput.value = branch ? branch.nombre : (mySucursal || newResBranches[0]?.nombre || '');
    }
    updateNewHourlySlotsUI();

    if (!newResPickersInitialized && window.flatpickr) {
        initNewReservationPickers();
    }

    if (baseUi.openModal) baseUi.openModal('modal-new-reservation');
    updateNewReservationPrice();
}

function initNewReservationPickers() {
    const now = getVirtualNow();
    const maxDate = new Date(now.getFullYear(), now.getMonth() + 3, now.getDate());
    const common = {
        disableMobile: "true",
        altInput: true,
        altFormat: "d-m-y",
        dateFormat: "Y-m-d",
        minDate: "today",
        maxDate: maxDate,
        defaultDate: now,
        onChange: () => {
            updateNewReservationPrice();
            updateNewHourlySlotsUI();
        }
    };
    flatpickr("#new-res-date-only", common);
    flatpickr("#new-res-day-only", common);
    flatpickr("#new-res-week-start", { ...common, onChange: (sd, ds) => updateNewPeriodEnd(ds, 7, '#new-res-week-end') });
    flatpickr("#new-res-fortnight-start", { ...common, onChange: (sd, ds) => updateNewPeriodEnd(ds, 15, '#new-res-fortnight-end') });
    flatpickr("#new-res-month-start", { ...common, onChange: (sd, ds) => updateNewPeriodEnd(ds, 30, '#new-res-month-end') });

    document.getElementById('new-res-hours-qty')?.addEventListener('input', () => updateNewReservationPrice());

    const dateOnlyEl = document.getElementById('new-res-date-only');
    if (dateOnlyEl) {
        dateOnlyEl.addEventListener('focus', () => updateNewHourlySlotsUI());
        dateOnlyEl.addEventListener('click', () => updateNewHourlySlotsUI());
    }
    const timeOnlyEl = document.getElementById('new-res-time-only');
    if (timeOnlyEl) {
        timeOnlyEl.addEventListener('click', () => updateNewHourlySlotsUI());
        timeOnlyEl.addEventListener('focus', () => updateNewHourlySlotsUI());
    }
    initNewHourSlotDrag();

    const qtyWrapper = document.querySelector('#new-hourly-fields .num-input-wrapper');
    if (qtyWrapper) {
        const inp = qtyWrapper.querySelector('#new-res-hours-qty');
        const up = qtyWrapper.querySelector('.num-btn.up');
        const down = qtyWrapper.querySelector('.num-btn.down');
        if (inp && up) up.addEventListener('click', () => {
            const max = parseInt(inp.max) || 24;
            const val = parseInt(inp.value) || 0;
            if (val < max) { inp.value = val + 1; inp.dispatchEvent(new Event('input', { bubbles: true })); }
        });
        if (inp && down) down.addEventListener('click', () => {
            const min = parseInt(inp.min) || 1;
            const val = parseInt(inp.value) || 0;
            if (val > min) { inp.value = val - 1; inp.dispatchEvent(new Event('input', { bubbles: true })); }
        });
    }

    newResPickersInitialized = true;
}

export function updateNewFormGroups(type) {
    const sections = {
        'hora': document.getElementById('new-hourly-fields'),
        'dia': document.getElementById('new-daily-fields'),
        'semana': document.getElementById('new-weekly-fields'),
        'quincena': document.getElementById('new-fortnight-fields'),
        'mes': document.getElementById('new-month-fields'),
        'standard': document.getElementById('new-standard-fields')
    };

    Object.values(sections).forEach(s => { if (s) s.style.display = 'none'; });
    const activeSection = sections[type] || sections['standard'];
    if (activeSection) {
        activeSection.style.display = activeSection.dataset.display || 'grid';
    }
    const diaGroup = document.getElementById('new-res-date-only-group');
    if (diaGroup) diaGroup.style.display = type === 'hora' ? 'flex' : 'none';
    if (type === 'hora') {
        updateNewHourlySlotsUI();
    } else {
        const slotGrid = document.getElementById('new-hourly-slots-grid');
        const slotBadge = document.getElementById('new-availability-badge');
        const slotContainer = document.getElementById('new-availability-status-container');
        if (slotGrid) { slotGrid.innerHTML = ''; slotGrid.style.display = 'none'; }
        if (slotBadge) slotBadge.style.display = 'none';
        if (slotContainer) slotContainer.style.display = 'none';
    }
    updateNewReservationPrice();
}

export function updateNewPeriodEnd(startDateStr, days, targetSelector) {
    if (!startDateStr) return;
    const endInput = document.querySelector(targetSelector);
    if (!endInput) return;

    const start = new Date(startDateStr.replace(/-/g, "/"));
    const end = new Date(start.getTime() + (days - 1) * 24 * 60 * 60 * 1000);
    const day = end.getDate().toString().padStart(2, '0');
    const month = (end.getMonth() + 1).toString().padStart(2, '0');
    const year = end.getFullYear().toString().slice(-2);
    endInput.value = `${day}-${month}-${year} 23:59`;
    updateNewReservationPrice();
}

export async function updateNewReservationPrice() {
    const typeEl = document.getElementById('new-res-tipo');
    if (!typeEl) return;

    const type = typeEl.value;
    const sucursal = document.getElementById('new-res-sucursal')?.value;
    let inicio, fin;

    try {
        if (type === 'hora') {
            const fecha = document.getElementById('new-res-date-only').value;
            const hora = document.getElementById('new-res-time-only').value;
            const qty = parseInt(document.getElementById('new-res-hours-qty').value) || 1;
            if (fecha && hora) {
                inicio = new Date(`${fecha}T${hora}`);
                fin = new Date(inicio.getTime() + qty * 3600000);
            }
        } else if (type === 'dia') {
            const fecha = document.getElementById('new-res-day-only').value;
            if (fecha) {
                inicio = new Date(`${fecha}T00:00`);
                fin = new Date(`${fecha}T23:59`);
            }
        } else if (['semana', 'quincena', 'mes'].includes(type)) {
            const periods = { 'semana': 7, 'quincena': 15, 'mes': 30 };
            const startMap = { 'semana': 'new-res-week-start', 'quincena': 'new-res-fortnight-start', 'mes': 'new-res-month-start' };
            const startVal = document.getElementById(startMap[type]).value;
            if (startVal) {
                inicio = new Date(startVal.replace(/-/g, "/"));
                fin = new Date(inicio.getTime() + (periods[type] - 1) * 24 * 60 * 60 * 1000);
                fin.setHours(23, 59, 59);
            }
        }
    } catch (e) {
        console.error("Error recalc new price:", e);
    }

    const elMonto = document.getElementById('new-res-monto-total');
    if (!inicio || !fin || isNaN(inicio.getTime()) || isNaN(fin.getTime())) {
        if (elMonto) elMonto.innerText = `$ ---`;
        return;
    }

    if (type === 'hora') {
        const qty = parseInt(document.getElementById('new-res-hours-qty').value);
        if (isNaN(qty) || qty <= 0) {
            if (elMonto) elMonto.innerText = `$ ---`;
            return;
        }
    }

    const durationHours = (fin - inicio) / 3600000;
    const tipoVehiculo = document.getElementById('new-res-tipo-vehiculo')?.value || 'Auto';
    const tarifaSuffix = tipoVehiculo === 'Moto' ? '_moto' : (tipoVehiculo === 'Camioneta' ? '_camioneta' : '');
    const periodicKeys = ['hora', 'dia', 'semana', 'quincena', 'mes'];
    let rates = { ...newResRatesFallback };

    if (sucursal) {
        const branch = (newResBranches || []).find(b => b.nombre.trim() === sucursal.trim());
        if (branch) {
            const nextRates = {};
            for (const pk of periodicKeys) {
                const baseKey = `tarifa_${pk}`;
                const typedKey = baseKey + tarifaSuffix;
                const val = parseFloat(branch[typedKey]) || parseFloat(branch[baseKey]) || newResRatesFallback[pk];
                nextRates[pk] = val;
            }
            rates = { ...rates, ...nextRates };
        }
    }

    let total = 0;
    if (type === 'hora') total = Math.max(1, Math.ceil(durationHours * 2)) * (rates.hora / 2);
    else if (type === 'dia') total = Math.max(1, Math.ceil(durationHours / 24)) * rates.dia;
    else if (type === 'semana') total = Math.ceil(durationHours / (24 * 7)) * rates.semana;
    else if (type === 'quincena') total = Math.ceil(durationHours / (24 * 15)) * rates.quincena;
    else if (type === 'mes') total = Math.ceil(durationHours / (24 * 30)) * rates.mes;
    else total = Math.ceil(durationHours) * rates.hora;

    if (elMonto) elMonto.innerText = `$ ${utils.formatNum(total)}`;
}

// ==========================================================================
// SELECTOR DE HORARIOS (CHIPS, IGUAL QUE EN EL FORMULARIO DE USUARIO)
// ==========================================================================

let newSlotRangeStart = null;
let newSlotRangeEnd = null;
let newSlotRangeDate = null;
let newSlotDragActive = false;

const _newReservaMinMs = (window.RESERVA_HORA_MIN_SEGUNDOS || 1800) * 1000;

const _newSlotToMin = (t) => {
    const [hh, mm] = (t || '00:00').split(':').map(Number);
    return hh * 60 + mm;
};

async function updateNewHourlySlotsUI() {
    const typeSelect = document.getElementById('new-res-tipo');
    const container = document.getElementById('new-availability-status-container');
    const badge = document.getElementById('new-availability-badge');
    const grid = document.getElementById('new-hourly-slots-grid');
    if (!container || !badge || !grid) return;

    if (!typeSelect || typeSelect.value !== 'hora') {
        grid.innerHTML = '';
        grid.style.display = 'none';
        container.style.display = 'none';
        return;
    }

    container.style.display = 'flex';
    grid.style.display = 'flex';

    const sucursal = document.getElementById('new-res-sucursal')?.value;
    const fecha = document.getElementById('new-res-date-only')?.value;
    const tipoVehiculo = document.getElementById('new-res-tipo-vehiculo')?.value || 'Auto';

    if (!sucursal) {
        grid.innerHTML = '<div style="width:100%; text-align:center; font-size:0.8rem; color:var(--dorado); padding:8px;"><i class="fas fa-info-circle" style="margin-right:6px;"></i> No tenés una sucursal asignada</div>';
        badge.style.display = 'none';
        return;
    }

    if (!fecha) {
        grid.innerHTML = '<div style="width:100%; text-align:center; font-size:0.8rem; color:var(--dorado); padding:8px;"><i class="fas fa-calendar-day" style="margin-right:6px;"></i> Seleccioná la fecha en el calendario para ver los horarios libres</div>';
        badge.style.display = 'none';
        return;
    }

    if (newSlotRangeDate && newSlotRangeDate !== fecha) {
        newSlotRangeStart = null;
        newSlotRangeEnd = null;
        newSlotRangeDate = null;
    }

    try {
        const res = await api.get('/user/reservations/disabled-hours', {
            params: {
                sucursal_nombre: sucursal,
                fecha: fecha,
                tipo_vehiculo: tipoVehiculo,
                duracion_horas: 1,
                paso_minutos: 30
            }
        });

        const reservedRanges = (res.ok && res.data && Array.isArray(res.data.reserved_ranges)) ? res.data.reserved_ranges : [];

        const now = getVirtualNow();
        const fechaHoy = _newResYmd(now);
        const blockedToday = [];
        if (fecha === fechaHoy) {
            const minInicioMs = now.getTime() + _newReservaMinMs;
            for (let min = 7 * 60; min <= 23 * 60 + 30; min += 30) {
                const hStr = `${String(Math.floor(min / 60)).padStart(2, '0')}:${String(min % 60).padStart(2, '0')}`;
                if (new Date(`${fecha}T${hStr}`).getTime() < minInicioMs) {
                    blockedToday.push(hStr);
                }
            }
        }

        let html = `
            <div style="width:100%; display:flex; flex-direction:column; align-items:center; gap:8px; margin-bottom:8px;">
                <div style="font-size:0.75rem; color:#aaa; text-align:center;">
                    <i class="fas fa-clock" style="color:var(--dorado); margin-right:4px;"></i> Tocá la hora de <b>inicio</b> y luego la de <b>fin</b>, o <b>arrastrá</b> sobre las casillas:
                </div>
            </div>
            <div class="chips-container-premium" style="display:grid; grid-template-columns:repeat(6, 1fr); gap:4px; width:100%;">
        `;

        let countTotal = 0;
        let countLibres = 0;

        for (let min = 7 * 60; min <= 23 * 60 + 30; min += 30) {
            const hourStr = `${String(Math.floor(min / 60)).padStart(2, '0')}:${String(min % 60).padStart(2, '0')}`;
            let isReserved = false;
            let isBoundaryEnd = false;
            for (const rg of reservedRanges) {
                if (hourStr >= rg.inicio && hourStr < rg.fin) isReserved = true;
                if (hourStr === rg.inicio) isBoundaryEnd = true;
            }
            const isBlockedToday = fecha === fechaHoy && blockedToday.includes(hourStr);
            if (!isReserved && !isBlockedToday) countLibres++;
            countTotal++;

            const inRange = newSlotRangeStart && newSlotRangeEnd && hourStr >= newSlotRangeStart && hourStr <= newSlotRangeEnd && hourStr !== newSlotRangeStart && hourStr !== newSlotRangeEnd;
            const isStart = newSlotRangeStart === hourStr;
            const isEnd = newSlotRangeEnd === hourStr;

            if (isReserved && !isBoundaryEnd) {
                html += `<span class="hourly-chip-premium full" title="Horario reservado">${hourStr}</span>`;
            } else if (isBlockedToday) {
                html += `<span class="hourly-chip-premium full" title="Horario ya pasado o con anticipación mínima">${hourStr}</span>`;
            } else if (inRange) {
                html += `<span class="hourly-chip-premium available in-range" data-hora="${hourStr}">${hourStr}</span>`;
            } else if (isStart || isEnd) {
                html += `<span class="hourly-chip-premium available selected" data-hora="${hourStr}">${hourStr}</span>`;
            } else {
                const title = isBoundaryEnd ? 'Inicio de otra reserva. Elegilo como FIN para terminar tu estadía acá' : '';
                html += `<span class="hourly-chip-premium available" title="${title}" data-hora="${hourStr}">${hourStr}</span>`;
            }
        }

        const resto = countTotal % 6;
        if (resto > 0) for (let i = 0; i < 6 - resto; i++) html += `<span class="hourly-chip-premium placeholder"></span>`;

        html += `</div>`;
        if (countLibres === 0) html += `<div style="width:100%; text-align:center; font-size:0.78rem; color:#e74c3c; margin-top:8px;"><i class="fas fa-triangle-exclamation"></i> Sin horarios libres para este día</div>`;

        grid.innerHTML = html;
        badge.style.display = 'none';
    } catch (e) {
        console.warn('[NUEVA RESERVA] Error cargando disponibilidad horaria:', e);
        grid.innerHTML = '<div style="width:100%; text-align:center; font-size:0.8rem; color:#e74c3c; padding:8px;"><i class="fas fa-triangle-exclamation"></i> Error al consultar disponibilidad</div>';
    }
}

export function selectNewHourRange(hourStr) {
    if (!newSlotDragActive) {
        if (!newSlotRangeStart || _newSlotToMin(hourStr) < _newSlotToMin(newSlotRangeStart)) {
            newSlotRangeStart = hourStr;
            newSlotRangeEnd = null;
        } else if (!newSlotRangeEnd) {
            newSlotRangeEnd = hourStr;
        } else {
            newSlotRangeStart = hourStr;
            newSlotRangeEnd = null;
        }
        _newSlotCommitRange();
    }
}

function _newSlotCommitRange() {
    const timeInput = document.getElementById('new-res-time-only');
    const hoursQtyInput = document.getElementById('new-res-hours-qty');
    const dateInput = document.getElementById('new-res-date-only');
    if (!timeInput || !hoursQtyInput) return;

    if (dateInput && dateInput.value) newSlotRangeDate = dateInput.value;

    if (newSlotRangeStart && newSlotRangeEnd && _newSlotToMin(newSlotRangeEnd) > _newSlotToMin(newSlotRangeStart)) {
        timeInput.value = newSlotRangeStart;
        hoursQtyInput.value = Math.round(((_newSlotToMin(newSlotRangeEnd) - _newSlotToMin(newSlotRangeStart)) / 60) * 10) / 10;
    } else {
        timeInput.value = '';
        hoursQtyInput.value = '1';
    }
    updateNewReservationPrice();
    updateNewHourlySlotsUI();
}

function initNewHourSlotDrag() {
    const grid = document.getElementById('new-hourly-slots-grid');
    if (!grid) return;

    grid.addEventListener('pointerdown', (ev) => {
        if (ev.button !== undefined && ev.button !== 0 && ev.type === 'pointerdown') return;
        const chip = ev.target.closest('.hourly-chip-premium');
        if (!chip || chip.classList.contains('full')) return;
        const hourStr = chip.dataset.hora;
        if (!hourStr) return;

        ev.preventDefault();
        newSlotDragActive = true;
        try { grid.setPointerCapture(ev.pointerId); } catch (e) { /* noop */ }

        if (!newSlotRangeStart || _newSlotToMin(hourStr) < _newSlotToMin(newSlotRangeStart)) {
            newSlotRangeStart = hourStr;
            newSlotRangeEnd = null;
        } else if (!newSlotRangeEnd) {
            if (hourStr === newSlotRangeStart) {
                newSlotRangeEnd = null;
            } else {
                newSlotRangeEnd = hourStr;
            }
        } else {
            newSlotRangeStart = hourStr;
            newSlotRangeEnd = null;
        }
        _newSlotCommitRange();
    });

    grid.addEventListener('pointermove', (ev) => {
        if (!newSlotDragActive) return;
        const el = document.elementFromPoint(ev.clientX, ev.clientY);
        const chip = el && el.closest('.hourly-chip-premium');
        if (!chip || chip.classList.contains('full')) return;
        const hourStr = chip.dataset.hora;
        if (!hourStr) return;

        if (_newSlotToMin(hourStr) > _newSlotToMin(newSlotRangeStart)) {
            if (!newSlotRangeEnd || newSlotRangeEnd !== hourStr) {
                newSlotRangeEnd = hourStr;
                _newSlotCommitRange();
            }
        } else if (_newSlotToMin(hourStr) < _newSlotToMin(newSlotRangeStart)) {
            newSlotRangeStart = hourStr;
            newSlotRangeEnd = null;
            _newSlotCommitRange();
        }
    });

    const finishDrag = () => {
        if (!newSlotDragActive) return;
        newSlotDragActive = false;
        _newSlotCommitRange();
    };
    grid.addEventListener('pointerup', finishDrag);
    grid.addEventListener('pointercancel', finishDrag);
}

export async function handleAdminNewReservation(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const originalContent = btn ? btn.innerHTML : '';

    const sucursal = document.getElementById('new-res-sucursal')?.value;
    const patente = document.getElementById('new-res-patente')?.value.trim().toUpperCase();
    const tipo = document.getElementById('new-res-tipo')?.value;
    const tipoVehiculo = document.getElementById('new-res-tipo-vehiculo')?.value || 'Auto';
    const metodoPago = document.getElementById('new-res-metodo-pago')?.value || 'Otro';

    if (!patente) return utils.showToast('Ingresá la patente del vehículo', 'info');
    if (!sucursal) return utils.showToast('No tenés una sucursal asignada', 'error');

    let inicio, fin;
    try {
        if (tipo === 'hora') {
            const fecha = document.getElementById('new-res-date-only').value;
            const hora = document.getElementById('new-res-time-only').value;
            const qty = parseInt(document.getElementById('new-res-hours-qty').value) || 1;
            if (!fecha || !hora) throw new Error("Seleccioná fecha y hora");
            inicio = `${fecha} ${hora}`;
            const s = new Date(`${fecha}T${hora}`);
            const f = new Date(s.getTime() + qty * 3600000);
            fin = `${f.getFullYear()}-${(f.getMonth()+1).toString().padStart(2,'0')}-${f.getDate().toString().padStart(2,'0')} ${f.getHours().toString().padStart(2,'0')}:${f.getMinutes().toString().padStart(2,'0')}`;
        } else if (tipo === 'dia') {
            const fecha = document.getElementById('new-res-day-only').value;
            if (!fecha) throw new Error("Seleccioná un día");
            inicio = `${fecha} 00:00`;
            fin = `${fecha} 23:59`;
        } else if (['semana', 'quincena', 'mes'].includes(tipo)) {
            const periods = { 'semana': 7, 'quincena': 15, 'mes': 30 };
            const startMap = { 'semana': 'new-res-week-start', 'quincena': 'new-res-fortnight-start', 'mes': 'new-res-month-start' };
            const startVal = document.getElementById(startMap[tipo]).value;
            if (!startVal) throw new Error("Seleccioná fecha de inicio");
            inicio = `${startVal} 00:00`;
            const s = new Date(startVal.replace(/-/g, "/"));
            const f = new Date(s.getTime() + (periods[tipo] - 1) * 24 * 60 * 60 * 1000);
            fin = `${f.getFullYear()}-${(f.getMonth()+1).toString().padStart(2,'0')}-${f.getDate().toString().padStart(2,'0')} 23:59`;
        }
    } catch (e) {
        return utils.showToast(e.message, 'error');
    }

    const av = await api.get('/user/reservations/check-availability', {
        params: {
            sucursal_nombre: sucursal,
            fecha_inicio: inicio,
            fecha_fin: fin,
            tipo_vehiculo: tipoVehiculo
        }
    });
    if (av.ok && av.data && !av.data.disponible) {
        return utils.showToast(av.data.mensaje || 'No hay disponibilidad para el horario solicitado.', 'info');
    }

    const payload = {
        patente,
        tipo_estadia: tipo,
        fecha_inicio: inicio,
        fecha_fin: fin,
        sucursal_nombre: sucursal,
        metodo_pago: metodoPago,
        tipo_vehiculo: tipoVehiculo,
        pagar: true
    };

    if (newResLinkedUserId) {
        payload.user_id = newResLinkedUserId;
    }

    if (btn) {
        btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> PROCESANDO...';
        btn.disabled = true;
    }

    const res = await api.post('/admin/reservations', payload);
    if (res.ok) {
        utils.showToast(`Reserva creada y pago registrado (${metodoPago})`, 'success');
        resetNewResPatenteLookup();
        if (baseUi.closeModal) baseUi.closeModal('modal-new-reservation');
        loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al crear la reserva', 'error');
    }

    if (btn) {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}
