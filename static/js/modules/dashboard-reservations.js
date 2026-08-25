import api from './api.js';
import * as utils from './utils.js';
import * as baseUi from './ui.js';
import { getVirtualNow } from './virtual-time.js';

/**
 * Módulo de Gestión de Reservas Administrativas
 */

let allReservations = [];
let editPickersInitialized = false;

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
                <td data-label="Estado Reserva"><span class="badge-status badge-${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</span></td>
                <td data-label="Acciones">
                    <div class="flex-row gap-8 justify-center actions-reveal">
                        ${r.estado_reserva !== 'Completada' && r.estado_reserva !== 'Cancelada' ? `
                        <button class="btn-icon-premium sm" onclick="openEditReservationModal(${r.id})" title="Editar Reserva">
                            <i class="fas fa-pen-to-square"></i>
                        </button>
                        <button class="btn-icon-premium sm danger" onclick="cancelReservationAdmin(${r.id})" title="Cancelar Reserva">
                            <i class="fas fa-xmark"></i>
                        </button>
                        ` : `<span class="text-xs text-muted">—</span>`}
                    </div>
                </td>
            </tr>`).join('') || '<tr><td colspan="8" class="text-center py-20">No hay reservas.</td></tr>';
        
        const statTotal = document.getElementById('admin-res-stat-total');
        const statPending = document.getElementById('admin-res-stat-pending');
        if (statTotal) statTotal.innerText = utils.formatNum(res.data.length);
        if (statPending) statPending.innerText = utils.formatNum(res.data.filter(r => r.estado_reserva === 'Pendiente').length);
    }
}

export async function updateEditReservationPrice() {
    const typeEl = document.getElementById('edit-res-tipo');
    const resIdEl = document.getElementById('edit-res-id');
    if (!typeEl || !resIdEl) return;

    const type = typeEl.value;
    const resId = resIdEl.value;
    const r = allReservations.find(x => x.id == resId) || window.allReservations?.find(x => x.id == resId);
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
            if (type === 'hora') {
                const qty = parseInt(document.getElementById('edit-res-hours-qty').value);
                if (isNaN(qty) || qty <= 0) {
                    const elMonto = document.getElementById('edit-res-monto-total');
                    if (elMonto) elMonto.innerText = `$ ---`;
                    return;
                }
            }

            const durationHours = (fin - inicio) / 3600000;
            
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
            if (elMonto) elMonto.innerText = `$ ${utils.formatNum(total)}`;
        } else {
            const elMonto = document.getElementById('edit-res-monto-total');
            if (elMonto) elMonto.innerText = `$ ---`;
        }
    } catch (e) { 
        console.error("Error recalc price:", e);
        const elMonto = document.getElementById('edit-res-monto-total');
        if (elMonto) elMonto.innerText = `$ 0`;
    }
}

export function updateEditFormGroups(type) {
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
        activeSection.style.display = activeSection.dataset.display || 'grid';
    }
    updateEditReservationPrice();
}

export function updateEditPeriodEnd(startDateStr, days, targetSelector) {
    if (!startDateStr) return;
    const endInput = document.querySelector(targetSelector);
    if (!endInput) return;
    
    const start = new Date(startDateStr.replace(/-/g, "/"));
    const end = new Date(start.getTime() + (days - 1) * 24 * 60 * 60 * 1000);
    const day = end.getDate().toString().padStart(2, '0');
    const month = (end.getMonth() + 1).toString().padStart(2, '0');
    const year = end.getFullYear().toString().slice(-2);
    endInput.value = `${day}-${month}-${year} 23:59`;
    updateEditReservationPrice();
}

export function openEditReservationModal(resId) {
    const r = allReservations.find(x => x.id === resId) || window.allReservations?.find(x => x.id === resId);
    if (!r) return;

    if (window.flatpickr && !editPickersInitialized) {
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
            onChange: () => updateEditReservationPrice() 
        };
        flatpickr("#edit-res-date-only", common);
        flatpickr("#edit-res-day-only", common);
        flatpickr("#edit-res-time-only", { 
            enableTime: true, 
            noCalendar: true, 
            dateFormat: "H:i",
            defaultDate: now,
            disableMobile: "true",
            onChange: () => updateEditReservationPrice() 
        });
        flatpickr("#edit-res-week-start", { ...common, onChange: (sd, ds) => updateEditPeriodEnd(ds, 7, '#edit-res-week-end') });
        flatpickr("#edit-res-fortnight-start", { ...common, onChange: (sd, ds) => updateEditPeriodEnd(ds, 15, '#edit-res-fortnight-end') });
        flatpickr("#edit-res-month-start", { ...common, onChange: (sd, ds) => updateEditPeriodEnd(ds, 30, '#edit-res-month-end') });
        
        const todayYmd = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
        updateEditPeriodEnd(todayYmd, 7, '#edit-res-week-end');
        updateEditPeriodEnd(todayYmd, 15, '#edit-res-fortnight-end');
        updateEditPeriodEnd(todayYmd, 30, '#edit-res-month-end');
        
        document.getElementById('edit-res-hours-qty')?.addEventListener('input', () => updateEditReservationPrice());
        
        const editQtyWrapper = document.querySelector('#edit-hourly-fields .num-input-wrapper');
        if (editQtyWrapper) {
            const inp = editQtyWrapper.querySelector('#edit-res-hours-qty');
            const up = editQtyWrapper.querySelector('.num-btn.up');
            const down = editQtyWrapper.querySelector('.num-btn.down');
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
        
        editPickersInitialized = true;
    }

    document.getElementById('edit-res-id').value = r.id;
    document.getElementById('edit-res-sucursal').value = r.sucursal_nombre || '';
    document.getElementById('edit-res-title').innerText = `EDITAR RESERVA #${r.id}`;
    document.getElementById('edit-res-patente').value = r.patente;
    document.getElementById('edit-res-tipo').value = r.tipo_estadia;
    document.getElementById('edit-res-pago').value = r.estado_pago;
    document.getElementById('edit-res-reserva').value = r.estado_reserva;

    updateEditFormGroups(r.tipo_estadia);

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
    if (elMonto) elMonto.innerText = `$ ${utils.formatNum(r.monto_total)}`;

    if (baseUi.openModal) baseUi.openModal('modal-edit-reservation');
}

export async function handleAdminEditReservation(event) {
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
        return utils.showToast(e.message, 'error');
    }

    const payload = {
        patente: document.getElementById('edit-res-patente').value.toUpperCase(),
        tipo_estadia: tipo,
        fecha_inicio: inicio,
        fecha_fin: fin,
        estado_pago: document.getElementById('edit-res-pago').value,
        estado_reserva: document.getElementById('edit-res-reserva').value
    };

    const sucursal = document.getElementById('edit-res-sucursal')?.value;
    if (sucursal) {
        const av = await api.get('/user/reservations/check-availability', {
            params: {
                sucursal_nombre: sucursal,
                fecha_inicio: inicio,
                fecha_fin: fin,
                exclude_id: parseInt(resId) || undefined
            }
        });
        if (av.ok && av.data && !av.data.disponible) {
            btn.disabled = false;
            return utils.showToast(av.data.mensaje || 'No hay disponibilidad para el horario solicitado.', 'info');
        }
    }

    btn.disabled = true;
    const res = await api.patch(`/admin/reservations/${resId}`, payload);
    if (res.ok) {
        utils.showToast('Reserva actualizada correctamente', 'success');
        if (baseUi.closeModal) baseUi.closeModal('modal-edit-reservation');
        loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al actualizar reserva', 'error');
    }
    btn.disabled = false;
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
        `;
    }

    if (baseUi.openModal) baseUi.openModal('modal-res-detail');
}
