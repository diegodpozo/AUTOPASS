import api from './api.js';
import * as utils from './utils.js';
import * as baseUi from './ui.js';
import { getVirtualNow } from './virtual-time.js';
import { loadAdminReservations, getAllReservations } from './reservations-admin-list.js';
import { THEME } from './theme.js';

// ==========================================================================
// NUEVA RESERVA MANUAL (PANEL ADMIN / STAFF) - CREAR + PAGAR EN UN PASO
// ==========================================================================

let newResPickersInitialized = false;
let newResBranches = [];
let newResLinkedUserId = null;
let newResPatenteLookupTimer = null;
let newResRatesFallback = { hora: 1500, dia: 15000, semana: 70000, quincena: 120000, mes: 200000 };
// TARIFAS AUTORITATIVAS POR SUCURSAL (fuente: /user/rates, igual que el front de usuario).
// Evita divergencias con el backend (p.ej. fracción de 30 min configurada explícitamente).
let newResRatesByBranch = {};
// COTIZACIÓN VIGENTE DEL FORM MANUAL (se envía al backend para revalidar y persistir).
let newResQuote = { base: 0, horas: 0, tarifaHora: 0, tarifaFraccion: 0, tarifaAplicada: 0 };
let editingResId = null;
let newResPickers = {};
let editingOriginalReserva = null;
let newResCalculatedTotal = 0;
let newResLiveDiscount = null;
let newResDiscountReq = 0;
let newResSucursalListenerInit = false;
let pendingEditResumo = null;
let pendingEditResumoMetodo = null;

// RANGO DE LA GRILLA HORARIA SEGÚN EL HORARIO DE LA SUCURSAL SELECCIONADA.
// RESPETA is_24h (00:00 → 23:30) Y el horario configurado (ej. "07:00 A 23:00" → 07:00 → 22:30).
// Fallback al rango legado 07:00 → 23:30 si no hay info de horario disponible.
function _newBranchSlotRange() {
    const sucursal = document.getElementById('new-res-sucursal')?.value;
    const branch = (newResBranches || []).find(b => b.nombre === sucursal);
    if (branch && branch.is_24h) {
        return { start: 0, end: 23 * 60 + 30 }; // 00:00 → 23:30
    }
    if (branch && branch.horario) {
        const m = String(branch.horario).toUpperCase().trim().match(/^(\d{1,2}):(\d{2})\s+(?:A|UN)\s+(\d{1,2}):(\d{2})$/);
        if (m) {
            let start = parseInt(m[1], 10) * 60 + parseInt(m[2], 10);
            let end = parseInt(m[3], 10) * 60 + parseInt(m[4], 10);
            if (end === 0) end = 24 * 60; // cierre 00:00 = final del día (grilla hasta 23:30)
            // último slot de inicio: un paso (30 min) antes del cierre, sin pasar de 23:30
            const lastStart = Math.max(start, Math.min(end - 30, 23 * 60 + 30));
            return { start, end: lastStart };
        }
    }
    return { start: 7 * 60, end: 23 * 60 + 30 }; // fallback legado
}

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
    refreshNewResLiveDiscount();
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
        badge.style.color = THEME.success;
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
        badge.style.color = THEME.danger;
        badge.style.background = 'transparent';
        badge.style.display = 'inline-flex';
    }
    refreshNewResLiveDiscount();
}

async function refreshNewResLiveDiscount() {
    const token = ++newResDiscountReq;
    if (editingResId) return;
    if (newResLinkedUserId) {
        const sucursal = document.getElementById('new-res-sucursal')?.value;
        if (!sucursal) {
            newResLiveDiscount = null;
            updateNewReservationPrice();
            return;
        }
        try {
            const res = await api.get('/admin/redemptions/available', { params: { user_id: newResLinkedUserId, sucursal } });
            if (token !== newResDiscountReq) return;
            newResLiveDiscount = (res.ok && Array.isArray(res.data) && res.data.length)
                ? { porc: res.data[0].valor_descuento || 0, fuente: 'vigente', ticketId: res.data[0].id }
                : null;
        } catch (e) {
            if (token !== newResDiscountReq) return;
            newResLiveDiscount = null;
        }
    } else {
        newResLiveDiscount = null;
    }
    updateNewReservationPrice();
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
    editingResId = null;
    editingOriginalReserva = null;
    newResCalculatedTotal = 0;
    newResLiveDiscount = null;
    pendingEditResumo = null;
    setNewResModalMode(false);
    const formEl = document.getElementById('form-new-reservation');
    if (formEl) formEl.reset();
    const payRow = document.getElementById('new-res-metodo-total-row');
    if (payRow) payRow.style.justifyContent = 'space-between';

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
        if (!newResSucursalListenerInit) {
            newResSucursalListenerInit = true;
            sucursalInput.addEventListener('change', () => { refreshNewResLiveDiscount(); loadNewResRates(sucursalInput.value); });
        }
    }
    updateNewHourlySlotsUI();
    refreshNewResLiveDiscount();
    loadNewResRates(sucursalInput?.value);

    if (!newResPickersInitialized && window.flatpickr) {
        initNewReservationPickers();
    }

    if (baseUi.openModal) baseUi.openModal('modal-new-reservation');
    updateNewReservationPrice();
}

function setNewResModalMode(editing) {
    const title = document.getElementById('new-res-modal-title');
    const subtitle = document.getElementById('new-res-modal-subtitle');
    const submit = document.getElementById('new-res-submit-btn');
    if (title) title.innerText = editing ? 'EDITAR RESERVA MANUAL' : 'NUEVA RESERVA MANUAL';
    if (subtitle) subtitle.innerText = editing ? 'Modificá los datos de la reserva' : 'Reserva y pago en la sucursal asignada';
    if (submit) {
        const span = submit.querySelector('span');
        if (span) span.innerText = editing ? 'GUARDAR CAMBIOS' : 'CREAR Y PAGAR';
    }
}

export async function openEditReservationModal(resId) {
    const r = getAllReservations().find(x => x.id === resId);
    if (!r) return;

    await openNewReservationModal();
    editingResId = resId;
    editingOriginalReserva = r;
    setNewResModalMode(true);

    // CARGAR SITUACIÓN DE DESCUENTO PARA MOSTRAR EL TOTAL CON DESCUENTO EN EDICIÓN
    newResLiveDiscount = null;
    try {
        const infoRes = await api.get(`/admin/reservations/${resId}/redemption-info`);
        if (infoRes.ok && infoRes.data && infoRes.data.aplica) {
            newResLiveDiscount = { porc: infoRes.data.valor_descuento || 0, fuente: infoRes.data.fuente, ticketId: infoRes.data.ticket_id };
        }
    } catch (e) { /* el total se muestra sin descuento */ }

    const setVal = (id, v) => { const el = document.getElementById(id); if (el) el.value = v; };

    const sucursalInput = document.getElementById('new-res-sucursal');
    if (sucursalInput && r.sucursal_nombre) sucursalInput.value = r.sucursal_nombre;

    const tipoEl = document.getElementById('new-res-tipo');
    const tipoVehEl = document.getElementById('new-res-tipo-vehiculo');
    const patenteEl = document.getElementById('new-res-patente');
    if (patenteEl) patenteEl.value = r.patente || '';
    resetNewResPatenteLookup();
    initNewResPatenteLookup();
    if (r.user_id) {
        newResLinkedUserId = r.user_id;
        const badge = document.getElementById('new-res-patente-owner-badge');
        if (badge) {
            const span = badge.querySelector('span');
            if (span) span.textContent = `${r.usuario_nombre || 'Cliente'} ${r.usuario_apellido || ''}`;
            const icon = badge.querySelector('i');
            if (icon) icon.className = 'fas fa-user-check';
            badge.style.color = THEME.success;
            badge.style.display = 'inline-flex';
        }
    }
    // RE-DETECCION AUTOMATICA DEL DUEÑO SEGUN LA PATENTE (IGUAL QUE AL CREAR)
    setTimeout(async () => {
        await lookupNewResPatente();
        updateNewReservationPrice();
    }, 60);
    if (tipoEl) {
        tipoEl.value = r.tipo_estadia || 'hora';
        updateNewFormGroups(tipoEl.value);
    }
    if (tipoVehEl && r.tipo_vehiculo) {
        tipoVehEl.value = r.tipo_vehiculo;
        updateNewVehicleTypeIcon(r.tipo_vehiculo);
    }

    const tipoEstadia = r.tipo_estadia || 'hora';
    const sDate = (r.fecha_inicio || '').split(' ')[0];
    const eDate = (r.fecha_fin || '').split(' ')[0];

    if (tipoEstadia === 'hora') {
        const sTime = ((r.fecha_inicio || '').split(' ')[1] || '08:00').slice(0, 5);
        const eTime = ((r.fecha_fin || '').split(' ')[1] || '09:00').slice(0, 5);
        const start = new Date(`${sDate}T${sTime}`);
        const end = new Date(`${eDate}T${eTime}`);
        const qty = !isNaN(start.getTime()) && !isNaN(end.getTime())
            ? Math.max(0.5, Math.round(((end - start) / 3600000) * 10) / 10)
            : 1;
        if (newResPickers.dateOnly) newResPickers.dateOnly.setDate(sDate || 'today', true);
        else setVal('new-res-date-only', sDate);
        setVal('new-res-time-only', sTime);
        setVal('new-res-hours-qty', qty);
    } else if (tipoEstadia === 'dia') {
        if (newResPickers.dayOnly) newResPickers.dayOnly.setDate(sDate || 'today', true);
        else setVal('new-res-day-only', sDate);
    } else {
        const days = { 'semana': 7, 'quincena': 15, 'mes': 30 };
        const pickerNames = { 'semana': 'weekStart', 'quincena': 'fortnightStart', 'mes': 'monthStart' };
        const endIds = { 'semana': 'new-res-week-end', 'quincena': 'new-res-fortnight-end', 'mes': 'new-res-month-end' };
        const startIds = { 'semana': 'new-res-week-start', 'quincena': 'new-res-fortnight-start', 'mes': 'new-res-month-start' };
        const picker = newResPickers[pickerNames[tipoEstadia]];
        if (picker) picker.setDate(sDate || 'today', true);
        else setVal(startIds[tipoEstadia], sDate);
        updateNewPeriodEnd(sDate, days[tipoEstadia], `#${endIds[tipoEstadia]}`);
    }

    const payGroup = document.getElementById('new-res-metodo-pago-group');
    const payRow = document.getElementById('new-res-metodo-total-row');
    if (r.estado_pago === 'Pagado') {
        if (payGroup) payGroup.style.display = 'none';
        if (payRow) payRow.style.justifyContent = 'center';
    } else {
        if (payGroup) payGroup.style.display = '';
        if (payRow) payRow.style.justifyContent = 'space-between';
        setVal('new-res-metodo-pago', r.metodo_pago || 'Efectivo');
    }

    newSlotRangeStart = null;
    newSlotRangeEnd = null;
    newSlotRangeDate = null;

    updateNewReservationPrice();
    updateNewHourlySlotsUI();

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
    newResPickers.dateOnly = flatpickr("#new-res-date-only", common);
    newResPickers.dayOnly = flatpickr("#new-res-day-only", common);
    newResPickers.weekStart = flatpickr("#new-res-week-start", { ...common, onChange: (sd, ds) => updateNewPeriodEnd(ds, 7, '#new-res-week-end') });
    newResPickers.fortnightStart = flatpickr("#new-res-fortnight-start", { ...common, onChange: (sd, ds) => updateNewPeriodEnd(ds, 15, '#new-res-fortnight-end') });
    newResPickers.monthStart = flatpickr("#new-res-month-start", { ...common, onChange: (sd, ds) => updateNewPeriodEnd(ds, 30, '#new-res-month-end') });

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

// CARGA (Y CACHEA) LAS TARIFAS AUTORITATIVAS DE LA SUCURSAL DESDE /user/rates,
// la misma fuente que usa el front de usuario. Evita divergencias con el backend
// (por ejemplo, una fracción de 30 min configurada distinta de la mitad de la hora).
async function loadNewResRates(sucursal) {
    if (!sucursal) return;
    if (newResRatesByBranch[sucursal]) { updateNewReservationPrice(); return; }
    try {
        const res = await api.get('/user/rates', { params: { sucursal } });
        if (res.ok && res.data) {
            newResRatesByBranch[sucursal] = res.data;
            updateNewReservationPrice();
        }
    } catch (e) { /* fallback: tarifas de la sucursal o valores por defecto */ }
}

// RESUELVE LAS TARIFAS DE UNA SUCURSAL PARA UN TIPO DE VEHÍCULO, priorizando /user/rates
// (caché en newResRatesByBranch) y cayendo a las tarifas del DTO de sucursal.
function _newResRatesFor(sucursal, tipoVehiculo) {
    const suffix = tipoVehiculo === 'Moto' ? '_moto' : (tipoVehiculo === 'Camioneta' ? '_camioneta' : '');
    const raw = sucursal ? newResRatesByBranch[sucursal] : null;
    const branch = (newResBranches || []).find(b => b.nombre.trim() === (sucursal || '').trim());
    const periodic = ['hora', 'dia', 'semana', 'quincena', 'mes'];
    const out = { suffix };
    for (const k of periodic) {
        let val;
        if (raw && (raw[k + suffix] !== undefined || raw[k] !== undefined)) {
            val = parseFloat(raw[k + suffix] !== undefined ? raw[k + suffix] : raw[k]);
        } else if (branch) {
            val = parseFloat(branch['tarifa_' + k + suffix]) || parseFloat(branch['tarifa_' + k]);
        }
        out[k] = (val !== undefined && !isNaN(val) && val > 0) ? val : newResRatesFallback[k];
    }
    if (raw) {
        const h = parseFloat(raw['hora' + suffix] !== undefined ? raw['hora' + suffix] : raw['hora']);
        out.horaBase = (!isNaN(h) && h > 0) ? h : 0;
        const f = parseFloat(raw['30min' + suffix] !== undefined ? raw['30min' + suffix] : raw['30min']);
        out.fraccionBase = (!isNaN(f) && f > 0) ? f : out.horaBase / 2;
    } else {
        out.horaBase = out.hora;
        out.fraccionBase = out.hora / 2;
    }
    return out;
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
            const qty = parseFloat(document.getElementById('new-res-hours-qty').value) || 1;
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
        const qty = parseFloat(document.getElementById('new-res-hours-qty').value);
        if (isNaN(qty) || qty <= 0) {
            if (elMonto) elMonto.innerText = `$ ---`;
            return;
        }
    }

    const durationHours = (fin - inicio) / 3600000;
    const tipoVehiculo = document.getElementById('new-res-tipo-vehiculo')?.value || 'Auto';
    const rates = _newResRatesFor(sucursal, tipoVehiculo);

    let total = 0;
    if (type === 'hora') total = utils.computeHourlyAmount(durationHours, rates.hora, rates.fraccionBase);
    else if (type === 'dia') total = Math.max(1, Math.ceil(durationHours / 24)) * rates.dia;
    else if (type === 'semana') total = Math.ceil(durationHours / (24 * 7)) * rates.semana;
    else if (type === 'quincena') total = Math.ceil(durationHours / (24 * 15)) * rates.quincena;
    else if (type === 'mes') total = Math.ceil(durationHours / (24 * 30)) * rates.mes;
    else total = Math.ceil(durationHours) * rates.hora;

    const base = Math.round(total * 100) / 100;

    // FOTO DE LA COTIZACIÓN (base pre-descuento) que se envía al backend al guardar.
    newResQuote = {
        base,
        horas: durationHours,
        tarifaHora: rates.horaBase,
        tarifaFraccion: rates.fraccionBase,
        tarifaAplicada: rates[type] || rates.hora
    };
    const dis = newResLiveDiscount;
    const porc = dis && dis.porc > 0 ? dis.porc : 0;
    let desc = 0;
    let final = base;
    if (porc > 0) {
        desc = Math.round(base * porc / 100 * 100) / 100;
        final = Math.round((base - desc) * 100) / 100;
    }
    // EN EDICIÓN EL MONTO CÁLCULADO VIENE DESCONTADO (EL BACKEND RECALCULA IGUAL);
    // EN ALTA QUEDA EN BASE (EL DIÁLOGO DE CONFIRMAR PAGO RE-DERIVA EL DESCUENTO).
    newResCalculatedTotal = editingResId ? final : base;

    if (elMonto) elMonto.innerText = `$ ${utils.formatNum(final)}`;

    const discLine = document.getElementById('new-res-discount-line');
    if (discLine) {
        if (porc > 0) {
            discLine.style.display = 'flex';
            discLine.innerHTML = `
                <span style="color: #777; text-decoration: line-through; font-weight: 700; font-size: 0.95rem;">$ ${utils.formatNum(base)}</span>
                <span style="color: #c084fc; font-weight: 700; letter-spacing: 0.5px;">DESC ${porc}% · -$ ${utils.formatNum(desc)}</span>`;
            discLine.style.alignItems = 'center';
            discLine.style.gap = '8px';
        } else {
            discLine.style.display = 'none';
            discLine.innerHTML = '';
        }
    }
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

function _newHourlySelectionSummary() {
    if (!newSlotRangeStart) {
        return '<div class="hourly-range-summary hint">Elegí el <b>INICIO</b> (verde) y después el <b>FIN</b> (rojo) de la estadía:</div>';
    }
    let dur = '';
    if (newSlotRangeEnd && _newSlotToMin(newSlotRangeEnd) > _newSlotToMin(newSlotRangeStart)) {
        const horas = Math.round((_newSlotToMin(newSlotRangeEnd) - _newSlotToMin(newSlotRangeStart)) / 60 * 10) / 10;
        dur = `<span class="hsum-dur">(${utils.formatDuracionLarga(horas)})</span>`;
    }
    return `<div class="hourly-range-summary">
        <span class="hsum-chip hsum-start"><i class="fas fa-arrow-right-to-bracket"></i> INICIO ${newSlotRangeStart}</span>
        <span class="hsum-arrow"><i class="fas fa-arrow-right"></i></span>
        <span class="hsum-chip hsum-end"><i class="fas fa-arrow-right-from-bracket"></i> FIN ${newSlotRangeEnd || '— toca la hora de <b>fin</b>'}</span>
        ${dur}
    </div>`;
}

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
        const params = {
            sucursal_nombre: sucursal,
            fecha: fecha,
            tipo_vehiculo: tipoVehiculo,
            duracion_horas: 1,
            paso_minutos: 30
        };
        if (editingResId) params.exclude_id = editingResId;
        const res = await api.get('/user/reservations/disabled-hours', { params });

        const reservedRanges = (res.ok && res.data && Array.isArray(res.data.reserved_ranges)) ? res.data.reserved_ranges : [];

        const now = getVirtualNow();
        const fechaHoy = _newResYmd(now);
        const blockedToday = [];
        if (fecha === fechaHoy) {
            const minInicioMs = now.getTime() + _newReservaMinMs;
            const rangoNew = _newBranchSlotRange();
            for (let min = rangoNew.start; min <= rangoNew.end; min += 30) {
                const hStr = `${String(Math.floor(min / 60)).padStart(2, '0')}:${String(min % 60).padStart(2, '0')}`;
                if (new Date(`${fecha}T${hStr}`).getTime() < minInicioMs) {
                    blockedToday.push(hStr);
                }
            }
        }

        let html = `
            <div style="width:100%; display:flex; flex-direction:column; align-items:center; gap:6px; margin-bottom:8px;">
                <div style="font-size:0.75rem; color:#aaa; text-align:center;">
                    <i class="fas fa-clock" style="color:var(--dorado); margin-right:4px;"></i> Tocá la hora de <b>inicio</b> y luego la de <b>fin</b>, o <b>arrastrá</b> sobre las casillas:
                </div>
                ${_newHourlySelectionSummary()}
            </div>
            <div class="chips-container-premium" style="display:grid; grid-template-columns:repeat(6, 1fr); gap:4px; width:100%;">
        `;

        let countTotal = 0;
        let countLibres = 0;

        const rangoNew = _newBranchSlotRange();
        for (let min = rangoNew.start; min <= rangoNew.end; min += 30) {
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

            const inRange = newSlotRangeStart && newSlotRangeEnd && hourStr > newSlotRangeStart && hourStr < newSlotRangeEnd;
            const isStart = newSlotRangeStart === hourStr;
            const isEnd = newSlotRangeEnd === hourStr;

            if (isReserved && !isBoundaryEnd) {
                html += `<span class="hourly-chip-premium full" title="Horario reservado">${hourStr}</span>`;
            } else if (isBlockedToday) {
                html += `<span class="hourly-chip-premium full" title="Horario ya pasado o con anticipación mínima">${hourStr}</span>`;
            } else if (isStart || isEnd) {
                const cls = isStart ? 'hourly-chip-premium available range-start' : 'hourly-chip-premium available range-end';
                const tip = isStart ? 'Hora de INICIO de tu estadía' : 'Hora de FIN de tu estadía';
                html += `<span class="${cls}" data-hora="${hourStr}" title="${tip}">${hourStr}</span>`;
            } else if (inRange) {
                html += `<span class="hourly-chip-premium available in-range" data-hora="${hourStr}">${hourStr}</span>`;
            } else {
                const title = isBoundaryEnd ? 'Inicio de otra reserva. Elegilo como FIN para terminar tu estadía acá' : '';
                html += `<span class="hourly-chip-premium available" title="${title}" data-hora="${hourStr}">${hourStr}</span>`;
            }
        }

        const resto = countTotal % 6;
        if (resto > 0) for (let i = 0; i < 6 - resto; i++) html += `<span class="hourly-chip-premium placeholder"></span>`;

        html += `</div>`;
        if (countLibres === 0) html += `<div style="width:100%; text-align:center; font-size:0.78rem; color:#f43f5e; margin-top:8px;"><i class="fas fa-triangle-exclamation"></i> Sin horarios libres para este día</div>`;

        grid.innerHTML = html;
        badge.style.display = 'none';
    } catch (e) {
        console.warn('[NUEVA RESERVA] Error cargando disponibilidad horaria:', e);
        grid.innerHTML = '<div style="width:100%; text-align:center; font-size:0.8rem; color:#f43f5e; padding:8px;"><i class="fas fa-triangle-exclamation"></i> Error al consultar disponibilidad</div>';
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
            const qty = parseFloat(document.getElementById('new-res-hours-qty').value) || 1;
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

    const avParams = {
        sucursal_nombre: sucursal,
        fecha_inicio: inicio,
        fecha_fin: fin,
        tipo_vehiculo: tipoVehiculo
    };
    if (editingResId) avParams.exclude_id = editingResId;

    const av = await api.get('/user/reservations/check-availability', { params: avParams });
    if (av.ok && av.data && !av.data.disponible) {
        return utils.showToast(av.data.mensaje || 'No hay disponibilidad para el horario solicitado.', 'info');
    }

    const payload = {
        patente,
        tipo_estadia: tipo,
        fecha_inicio: inicio,
        fecha_fin: fin,
        sucursal_nombre: sucursal,
        tipo_vehiculo: tipoVehiculo,
        horas_calculadas: newResQuote.horas || null,
        monto_calculado: newResQuote.base || null,
        tarifa_hora: newResQuote.tarifaHora || null,
        tarifa_fraccion: newResQuote.tarifaFraccion || null,
        tarifa_aplicada: newResQuote.tarifaAplicada || null
    };

    if (editingResId) {
        if (document.getElementById('new-res-metodo-pago-group')?.style.display !== 'none') {
            payload.metodo_pago = metodoPago;
        }
        payload.user_id = newResLinkedUserId || null;
    } else {
        payload.metodo_pago = metodoPago;
        payload.pagar = true;
        if (newResLinkedUserId) {
            payload.user_id = newResLinkedUserId;
        }
    }

    // AVISO DE CONFIRMACION AL EDITAR UNA RESERVA PAGADA (DIFERENCIA DE IMPORTE)
    if (editingResId && editingOriginalReserva && String(editingOriginalReserva.estado_pago).toLowerCase() === 'pagado') {
        const totalAnterior = (editingOriginalReserva.monto_total || 0) - (editingOriginalReserva.monto_reembolsado || 0);
        const diferencia = Math.round((newResCalculatedTotal - totalAnterior) * 100) / 100;

        const resumoEl = document.getElementById('edit-confirm-resumo');
        const actual = editingOriginalReserva;
        if (resumoEl) {
            const rows = [
                ['Reserva', `#${editingResId}`],
                ['Patente', actual.patente || patente],
                ['Sucursal', actual.sucursal_nombre || sucursal],
                ['Estadía', `${inicio} → ${fin}`],
                ['Total pagado', `$ ${utils.formatNum(actual.monto_total || 0)}${(actual.monto_reembolsado || 0) > 0 ? ` (ya reembolsado -$ ${utils.formatNum(actual.monto_reembolsado)})` : ''}`],
                ['Total nuevo', `$ ${utils.formatNum(newResCalculatedTotal)}`]
            ];
            resumoEl.innerHTML = rows.map(r => `<div style="display:flex; justify-content:space-between; gap:12px;"><span style="color:#aaa;">${r[0]}</span><b>${r[1]}</b></div>`).join('');
        }

        const diffEl = document.getElementById('edit-confirm-diff');
        if (diffEl) {
            if (diferencia > 0) {
                diffEl.innerHTML = `<i class="fas fa-arrow-up" style="margin-right:6px;"></i>Se cobran $ ${utils.formatNum(diferencia)} por la diferencia`;
                diffEl.style.color = THEME.success;
            } else if (diferencia < 0) {
                diffEl.innerHTML = `<i class="fas fa-arrow-down" style="margin-right:6px;"></i>Se reembolsan $ ${utils.formatNum(Math.abs(diferencia))}`;
                diffEl.style.color = THEME.danger;
            } else {
                diffEl.innerHTML = '<i class="fas fa-equals" style="margin-right:6px;"></i>Sin diferencias de importe';
                diffEl.style.color = '#aaa';
            }
        }

        const methodGroup = document.getElementById('edit-confirm-method-group');
        if (methodGroup) {
            const needsMethod = diferencia !== 0;
            methodGroup.style.display = needsMethod ? '' : 'none';
            const label = methodGroup.querySelector('label');
            if (label) label.textContent = diferencia > 0 ? '¿Con qué método se cobra la diferencia?' : '¿Con qué método se reembolsa la diferencia?';
        }

        const methodSelect = document.getElementById('edit-confirm-metodo');
        if (methodSelect) {
            if (diferencia < 0) {
                const origMetodo = String(actual.metodo_pago || '').toUpperCase().replace(/\s+/g, '');
                methodSelect.value = ['CAJA', 'EFECTIVO'].includes(origMetodo) ? 'Efectivo' : 'Saldo';
            } else if (diferencia > 0) {
                methodSelect.value = ['CAJA', 'EFECTIVO'].includes(String(actual.metodo_pago || '').toUpperCase().replace(/\s+/g, '')) ? 'Efectivo' : 'Saldo';
            }
        }

        pendingEditResumo = { payload, diferencia };
        if (baseUi.openModal) baseUi.openModal('modal-edit-resumo');
        return;
    }

    // DETECTAR DESCUENTO DE RESERVA VIGENTE PARA APLICARLO EN CAJA (NUEVA RESERVA + PAGO)
    if (!editingResId && newResLinkedUserId && newResCalculatedTotal > 0) {
        const avail = await api.get('/admin/redemptions/available', { params: { user_id: newResLinkedUserId, sucursal } });
        if (avail.ok && Array.isArray(avail.data) && avail.data.length > 0) {
            const d = avail.data[0];
            const pct = d.valor_descuento || 0;
            const descuentoValor = Math.round(newResCalculatedTotal * pct / 100 * 100) / 100;
            const montoFinal = Math.round((newResCalculatedTotal - descuentoValor) * 100) / 100;
            const aplicar = await utils.showConfirm('Descuento aplicable', `
                <div style="text-align:left; font-size:0.85rem; line-height:1.8;">
                    <div style="display:flex; justify-content:space-between; gap:12px;"><span style="color:#aaa;">Monto reserva</span><b>$${utils.formatNum(newResCalculatedTotal)}</b></div>
                    <div style="display:flex; justify-content:space-between; gap:12px; color:#c084fc;"><span><i class="fas fa-percent" style="margin-right:4px;"></i>Descuento ${pct}% (${d.titulo || ''})</span><b>-$ ${utils.formatNum(descuentoValor)}</b></div>
                    <div style="border-top:1px solid rgba(255,255,255,0.1); margin:8px 0 6px; padding-top:8px; display:flex; justify-content:space-between; gap:12px;"><span style="color:#aaa;">Total a pagar</span><b style="font-size:1.05rem;">$${utils.formatNum(montoFinal)}</b></div>
                </div>
            `);
            if (aplicar) payload.redemption_ticket_id = d.id;
        }
    }

    await _submitReservationPayload(payload);
}

export function confirmEditResumoProceed() {
    if (!pendingEditResumo) return;
    const { payload, diferencia } = pendingEditResumo;
    pendingEditResumo = null;
    const methodSelect = document.getElementById('edit-confirm-metodo');
    const metodo = methodSelect ? methodSelect.value : null;
    if (diferencia > 0) payload.cobrar_diferencia_metodo = metodo;
    else if (diferencia < 0) payload.reembolsar_diferencia_metodo = metodo;
    if (baseUi.closeModal) baseUi.closeModal('modal-edit-resumo');
    _submitReservationPayload(payload);
}

export function cancelEditResumo() {
    pendingEditResumo = null;
    if (baseUi.closeModal) baseUi.closeModal('modal-edit-resumo');
}

async function _submitReservationPayload(payload) {
    const btn = document.getElementById('new-res-submit-btn');
    const originalContent = btn ? btn.innerHTML : '';

    if (btn) {
        btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> PROCESANDO...';
        btn.disabled = true;
    }

    const res = editingResId
        ? await api.put(`/admin/reservations/${editingResId}`, payload)
        : await api.post('/admin/reservations', payload);
    if (res.ok) {
        let msg = editingResId ? `Reserva #${editingResId} actualizada` : `Reserva creada y pago registrado (${res.data?.metodo_pago || payload.metodo_pago || ''})`;
        if (editingResId && res.data && res.data.accion === 'cobro') {
            msg = `Reserva #${editingResId} actualizada. Se cobraron $ ${utils.formatNum(res.data.diferencia)} (${res.data.metodo_pago || 'Caja'})`;
        } else if (editingResId && res.data && res.data.accion === 'reembolso') {
            msg = `Reserva #${editingResId} actualizada. Se reembolsaron $ ${utils.formatNum(Math.abs(res.data.diferencia))} (${res.data.metodo_pago || 'Saldo'})`;
        }
        utils.showToast(msg, 'success');
        resetNewResPatenteLookup();
        editingResId = null;
        editingOriginalReserva = null;
        setNewResModalMode(false);
        if (baseUi.closeModal) baseUi.closeModal('modal-new-reservation');
        loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al guardar la reserva', 'error');
    }

    if (btn) {
        btn.innerHTML = originalContent;
        btn.disabled = false;
    }
}
