import api from './api.js';
import { toTitle, formatDate, showToast, showConfirm } from './utils.js';

/**
 * RESERVAS MODULE
 * Lógica compleja de gestión de reservas, tarifas y pases digitales.
 */

let historialCurrentPage = 1;
const HISTORIAL_PAGE_SIZE = 5;
let currentRates = { hora: 1500, dia: 15000, semana: 70000, quincena: 120000, mes: 200000 };
let editingReservaId = null;
let historyData = [];

export function initReservationForm() {
    if (!window.flatpickr) return;

    // Configurar idioma español globalmente si está cargado
    if (window.flatpickr.l10ns?.es) {
        window.flatpickr.localize(window.flatpickr.l10ns.es);
    }

    const commonConfig = {
        minDate: "today",
        disableMobile: "true",
        onChange: () => updateReservationPrice()
    };

    flatpickr(".res-date-only", { ...commonConfig, dateFormat: "Y-m-d" });
    flatpickr(".res-day-only", { ...commonConfig, dateFormat: "Y-m-d" });
    flatpickr(".res-week-start", { ...commonConfig, dateFormat: "Y-m-d", onChange: (sd, ds) => updatePeriodEnd(ds, 7, '.res-week-end') });
    flatpickr(".res-fortnight-start", { ...commonConfig, dateFormat: "Y-m-d", onChange: (sd, ds) => updatePeriodEnd(ds, 15, '.res-fortnight-end') });
    flatpickr(".res-month-start", { ...commonConfig, dateFormat: "Y-m-d", onChange: (sd, ds) => updatePeriodEnd(ds, 30, '.res-month-end') });
    flatpickr(".res-start", { ...commonConfig, enableTime: true, dateFormat: "Y-m-d H:i" });
    flatpickr(".res-end", { ...commonConfig, enableTime: true, dateFormat: "Y-m-d H:i" });

    const typeSelect = document.querySelector('.res-type');
    if (typeSelect) {
        typeSelect.addEventListener('change', (e) => updateFormGroups(e.target.value));
    }

    const sucursalSelect = document.querySelector('.res-sucursal');
    if (sucursalSelect) {
        sucursalSelect.addEventListener('change', (e) => {
            const sucursalId = e.target.value; // Enviar el nombre completo (ej: "AUTOPASS Castelar")
            fetchRates(sucursalId);
        });
    }

    const hoursInput = document.querySelector('.res-hours-qty');
    if (hoursInput) {
        hoursInput.addEventListener('input', () => updateReservationPrice());
    }

    const timeInput = document.querySelector('.res-time-only');
    if (timeInput) {
        timeInput.addEventListener('change', () => updateReservationPrice());
    }
}

function updatePeriodEnd(startDateStr, days, targetSelector) {
    if (!startDateStr) return;
    const endInput = document.querySelector(targetSelector);
    if (!endInput) return;
    
    const start = new Date(startDateStr.replace(/-/g, "/"));
    const end = new Date(start.getTime() + (days - 1) * 24 * 60 * 60 * 1000);
    const day = end.getDate().toString().padStart(2, '0');
    const month = (end.getMonth() + 1).toString().padStart(2, '0');
    const year = end.getFullYear();
    endInput.value = `${day}/${month}/${year} 23:59`;
    updateReservationPrice();
}

export async function toggleReservaForm() {
    const container = document.getElementById('reserva-form-container');
    const arrow = document.getElementById('reserva-form-arrow');
    if (!container) return;

    const isOpen = container.classList.toggle('open');
    if (arrow) arrow.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0deg)';

    if (isOpen) {
        await refreshReservationFormState();
    } else {
        resetReservaForm();
    }
}

export async function refreshReservationFormState() {
    const container = document.getElementById('reserva-form-container');
    if (!container || !container.classList.contains('open')) return;

    fetchRates();
    
    // 1. Cargar Vehículos
    const resVehicles = await api.get('/user/vehicles');
    if (resVehicles.ok) {
        const vehicles = resVehicles.data;
        const noVehiclesSec = document.getElementById('reserva-no-vehicles');
        const mainForm = document.getElementById('reserva-form-content');

        if (vehicles.length === 0) {
            if (noVehiclesSec) noVehiclesSec.style.display = 'block';
            if (mainForm) mainForm.style.display = 'none';
        } else {
            if (noVehiclesSec) noVehiclesSec.style.display = 'none';
            if (mainForm) mainForm.style.display = 'block';
            const selects = document.querySelectorAll('.res-vehicle');
            selects.forEach(select => {
                const currentVal = select.value;
                select.innerHTML = '<option value="">Seleccioná vehículo...</option>' + 
                    vehicles.map(v => `<option value="${v.patente}">${v.patente} - ${v.marca_modelo}</option>`).join('');
                if (currentVal) select.value = currentVal;
            });
        }
    }

    // 2. Cargar Sucursales Dinámicamente
    const resBranches = await api.get('/admin/branches');
    if (resBranches.ok) {
        const branches = resBranches.data;
        const sucursalSelects = document.querySelectorAll('.res-sucursal');
        sucursalSelects.forEach(select => {
            const currentVal = select.value;
            select.innerHTML = '<option value="">Seleccioná sucursal...</option>' + 
                branches.map(b => `<option value="${b.nombre}">${b.nombre}</option>`).join('');
            if (currentVal) select.value = currentVal;
        });
    }
}

export function resetReservaForm() {
    editingReservaId = null;
    const form = document.querySelector('.reservation-form-modern');
    if (form) {
        form.reset();
        updateFormGroups("");
    }
    const btnSpan = document.querySelector('.btn-confirm-premium span');
    if (btnSpan) btnSpan.innerText = 'CONFIRMAR RESERVA';
    const headerTitle = document.querySelector('.header-text h3');
    if (headerTitle) headerTitle.innerText = 'GENERAR NUEVA RESERVA';
    updateReservationPrice();
}

export async function prepareEditReservation(id) {
    const res = await api.get('/user/reservations');
    if (!res.ok) return;
    const all = res.data;
    const r = all.find(item => item.id === id);
    if (!r) return;

    const now = new Date();
    const start = new Date(r.fecha_inicio.replace(/-/g, "/"));
    if ((start - now) < 7200000) {
        return showToast('No se puede modificar con menos de 2 horas de antelación');
    }

    editingReservaId = id;
    
    if (window.showSection) {
        const inicioNavItem = document.querySelector('.nav-item[onclick*="inicio"]');
        window.showSection('inicio', inicioNavItem);
    }

    const container = document.getElementById('reserva-form-container');
    if (!container.classList.contains('open')) await toggleReservaForm();
    container.scrollIntoView({ behavior: 'smooth' });

    document.querySelector('.header-text h3').innerText = `MODIFICAR RESERVA #${id}`;
    document.querySelector('.btn-confirm-premium span').innerText = 'ACTUALIZAR RESERVA';

    setTimeout(() => {
        const vehicleSelect = document.querySelector('.res-vehicle');
        const sucursalSelect = document.querySelector('.res-sucursal');
        const typeSelect = document.querySelector('.res-type');
        
        if (vehicleSelect) vehicleSelect.value = r.patente;
        if (sucursalSelect) sucursalSelect.value = r.sucursal_nombre;
        if (typeSelect) {
            typeSelect.value = r.tipo_estadia;
            updateFormGroups(r.tipo_estadia);
        }
        
        if (r.tipo_estadia === 'hora') {
            const dtParts = r.fecha_inicio.split(' ');
            document.querySelector('.res-date-only').value = dtParts[0];
            document.querySelector('.res-time-only').value = dtParts[1];
            const startDt = new Date(r.fecha_inicio.replace(/-/g, "/"));
            const endDt = new Date(r.fecha_fin.replace(/-/g, "/"));
            const hours = Math.round((endDt - startDt) / (1000 * 60 * 60));
            document.querySelector('.res-hours-qty').value = hours || 1;
        } else if (r.tipo_estadia === 'dia') {
            document.querySelector('.res-day-only').value = r.fecha_inicio.split(' ')[0];
        } else {
            const periodInputs = { 'semana': '.res-week-start', 'quincena': '.res-fortnight-start', 'mes': '.res-month-start' };
            const specificInput = document.querySelector(periodInputs[r.tipo_estadia]);
            if (specificInput) {
                specificInput.value = r.fecha_inicio.split(' ')[0];
                specificInput.dispatchEvent(new Event('change'));
            } else {
                document.querySelector('.res-start').value = r.fecha_inicio;
                document.querySelector('.res-end').value = r.fecha_fin;
            }
        }
        updateReservationPrice();
    }, 500);
}

export async function fetchRates(sucursal = null) {
    const url = sucursal ? `/user/rates?sucursal=${sucursal}` : '/user/rates';
    const res = await api.get(url);
    if (res.ok) {
        currentRates = res.data;
        updateReservationPrice();
    }
}

export function updateReservationPrice() {
    const typeSelect = document.querySelector('.res-type');
    if (!typeSelect) return;
    const type = typeSelect.value;
    const totalEl = document.getElementById('reserva-total-est');
    let total = 0;

    let inicio, fin;
    try {
        if (type === 'hora') {
            const fecha = document.querySelector('.res-date-only')?.value;
            const hora = document.querySelector('.res-time-only')?.value;
            const hoursQtyInput = document.querySelector('.res-hours-qty');
            const hoursQty = parseInt(hoursQtyInput?.value);
            
            if (fecha && hora && !isNaN(hoursQty) && hoursQty > 0) {
                inicio = new Date(`${fecha}T${hora}`);
                fin = new Date(inicio.getTime() + hoursQty * 60 * 60 * 1000);
            }
        } else if (type === 'dia') {
            const fecha = document.querySelector('.res-day-only')?.value;
            if (fecha) {
                inicio = new Date(`${fecha}T00:00`);
                fin = new Date(`${fecha}T23:59`);
            }
        } else {
            const periods = { 'semana': 7, 'quincena': 15, 'mes': 30 };
            const periodClasses = { 'semana': '.res-week-start', 'quincena': '.res-fortnight-start', 'mes': '.res-month-start' };
            const selector = periodClasses[type];
            const fechaInput = selector ? document.querySelector(selector) : null;
            const fecha = fechaInput?.value;
            if (fecha) {
                inicio = new Date(`${fecha}T00:00`);
                fin = new Date(inicio.getTime() + periods[type] * 24 * 60 * 60 * 1000);
                fin.setSeconds(fin.getSeconds() - 1);
            }
        }

        if (inicio && fin) {
            const durationHours = (fin - inicio) / 3600000;
            const rate = currentRates[type] || 0;
            
            if (type === 'hora') total = Math.ceil(durationHours) * rate;
            else if (type === 'dia') total = Math.max(1, Math.ceil(durationHours / 24)) * rate;
            else if (type === 'semana') total = Math.ceil(durationHours / (24 * 7)) * rate;
            else if (type === 'quincena') total = Math.ceil(durationHours / (24 * 15)) * rate;
            else if (type === 'mes') total = Math.ceil(durationHours / (24 * 30)) * rate;
            else total = Math.ceil(durationHours) * rate;
        }
    } catch (e) { console.error("Error calculando precio:", e); }

    if (totalEl) totalEl.innerText = total > 0 ? `$ ${total.toLocaleString()}` : '$ ---';
}

export function updateFormGroups(type) {
    const sections = {
        'hora': document.getElementById('hourly-fields'),
        'dia': document.getElementById('daily-fields'),
        'semana': document.getElementById('weekly-fields'),
        'quincena': document.getElementById('fortnight-fields'),
        'mes': document.getElementById('month-fields'),
        'standard': document.getElementById('standard-fields')
    };

    Object.values(sections).forEach(s => { if(s) s.style.display = 'none'; });
    const activeSection = sections[type] || sections['standard'];
    if (activeSection) activeSection.style.display = 'grid';
    updateReservationPrice();
}

export async function createReservation(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const originalContent = btn.innerHTML;
    
    const patente = e.target.querySelector('.res-vehicle').value;
    const sucursal = e.target.querySelector('.res-sede').value;
    const tipo = e.target.querySelector('.res-type').value;
    
    if (!patente) return showToast('Seleccioná un vehículo');

    let inicio, fin;

    if (tipo === 'hora') {
        const fecha = e.target.querySelector('.res-date-only').value;
        const hora = e.target.querySelector('.res-time-only').value;
        const hoursQty = parseInt(e.target.querySelector('.res-hours-qty').value) || 1;
        if (!fecha || !hora) return showToast('Seleccioná fecha y hora');
        inicio = `${fecha} ${hora}`;
        const now = new Date();
        const startDt = new Date(inicio.replace(/-/g, "/"));
        if ((startDt - now) < (2 * 60 * 60 * 1000)) return showToast('Mínimo 2 horas de anticipación.');
        const endDt = new Date(startDt.getTime() + hoursQty * 60 * 60 * 1000);
        fin = `${endDt.getFullYear()}-${(endDt.getMonth() + 1).toString().padStart(2, '0')}-${endDt.getDate().toString().padStart(2, '0')} ${endDt.getHours().toString().padStart(2, '0')}:${endDt.getMinutes().toString().padStart(2, '0')}`;
    } else if (tipo === 'dia') {
        const fecha = e.target.querySelector('.res-day-only').value;
        if (!fecha) return showToast('Seleccioná un día');
        inicio = `${fecha} 00:00`;
        const now = new Date();
        const startDt = new Date(inicio.replace(/-/g, "/"));
        if ((startDt - now) < (2 * 60 * 60 * 1000)) return showToast('Mínimo 2 horas de anticipación.');
        fin = `${fecha} 23:59`;
    } else {
        const periods = { 'semana': 7, 'quincena': 15, 'mes': 30 };
        const periodClasses = { 'semana': '.res-week-start', 'quincena': '.res-fortnight-start', 'mes': '.res-month-start' };
        if (periods[tipo]) {
            const selector = periodClasses[tipo];
            const fecha = e.target.querySelector(selector).value;
            if (!fecha) return showToast('Seleccioná día de inicio');
            inicio = `${fecha} 00:00`;
            const now = new Date();
            const startDtCheck = new Date(fecha.replace(/-/g, "/"));
            if ((startDtCheck - now) < (2 * 60 * 60 * 1000)) return showToast('Mínimo 2 horas de anticipación.');
            const startDt = new Date(fecha.replace(/-/g, "/"));
            const endDt = new Date(startDt.getTime() + (periods[tipo] - 1) * 24 * 60 * 60 * 1000);
            fin = `${endDt.getFullYear()}-${(endDt.getMonth() + 1).toString().padStart(2, '0')}-${endDt.getDate().toString().padStart(2, '0')} 23:59`;
        } else {
            inicio = e.target.querySelector('.res-start').value;
            fin = e.target.querySelector('.res-end').value;
            const now = new Date();
            const startDt = new Date(inicio.replace(/-/g, "/"));
            if ((startDt - now) < (2 * 60 * 60 * 1000)) return showToast('Mínimo 2 horas de anticipación.');
        }
    }

    const resumenHtml = `
        <div style="text-align: left; background: rgba(255,255,255,0.03); padding: 20px; border-radius: 15px; border: 1px solid rgba(197,160,89,0.2); margin-top: 10px;">
            <div style="margin-bottom: 12px;"><i class="fas fa-car" style="color: var(--dorado);"></i> Vehículo: <b style="color: #fff;">${patente}</b></div>
            <div style="margin-bottom: 12px;"><i class="fas fa-location-dot" style="color: var(--dorado);"></i> Sucursal: <b style="color: #fff;">${sucursal}</b></div>
            <div style="margin-bottom: 12px;"><i class="fas fa-calendar-day" style="color: var(--dorado);"></i> Estadía: <b style="color: #fff; text-transform: capitalize;">${tipo}</b></div>
            <div style="margin-bottom: 12px;"><i class="fas fa-clock" style="color: var(--dorado);"></i> Desde: <b style="color: #eee;">${formatDate(inicio)}</b></div>
            <div style="margin-bottom: 12px;"><i class="fas fa-hourglass-end" style="color: var(--dorado);"></i> Hasta: <b style="color: #eee;">${formatDate(fin)}</b></div>
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between;">
                <span style="font-weight: 800;">TOTAL:</span>
                <b style="color: var(--dorado); font-size: 1.2rem;">${document.getElementById('reserva-total-est').innerText}</b>
            </div>
        </div>`;

    if (!await showConfirm('REVISÁ TU RESERVA', resumenHtml)) return;

    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> PROCESANDO...';
    btn.disabled = true;

    const payload = { patente, fecha_inicio: inicio, fecha_fin: fin, sucursal_nombre: sucursal, tipo_estadia: tipo };
    const res = editingReservaId ? 
        await api.patch(`/user/reservations/${editingReservaId}`, payload) : 
        await api.post('/user/reservations', payload);

    if (res.ok) {
        showToast(editingReservaId ? '¡Reserva actualizada!' : '¡Reserva creada con éxito!');
        resetReservaForm();
        toggleReservaForm();
        if (window.showSection) window.showSection('reservas', document.querySelector('.nav-item[onclick*="reservas"]'));
        else loadReservations();
        if (window.loadProfile) window.loadProfile();
    } else { showToast(res.error || 'Error al procesar reserva'); }
    
    btn.innerHTML = originalContent;
    btn.disabled = false;
}

export async function loadReservations() {
    const res = await api.get('/user/reservations');
    if (!res.ok) return;
    
    const all = res.data;
    const active = all.filter(r => r.estado_reserva === 'Pendiente' || r.estado_reserva === 'Activa');
    historyData = all.filter(r => r.estado_reserva !== 'Pendiente' && r.estado_reserva !== 'Activa');
    
    const now = new Date();
    const inProgress = active.filter(r => now >= new Date(r.fecha_inicio.replace(/-/g, "/")) && now < new Date(r.fecha_fin.replace(/-/g, "/")));
    const upcoming = active.filter(r => now < new Date(r.fecha_inicio.replace(/-/g, "/")));

    if (document.getElementById('stat-reservations')) document.getElementById('stat-reservations').innerText = active.length;
    if (document.getElementById('stat-res-active')) document.getElementById('stat-res-active').innerText = inProgress.length;
    if (document.getElementById('stat-res-upcoming')) document.getElementById('stat-res-upcoming').innerText = upcoming.length;

    const featuredList = document.getElementById('reservation-featured-list');
    if (inProgress.length > 0) {
        document.getElementById('container-res-featured').style.display = 'block';
        if (featuredList) featuredList.innerHTML = renderReservaCard(inProgress[0], true);
    } else {
        document.getElementById('container-res-featured').style.display = 'none';
    }

    const activeList = document.getElementById('reservation-list-active');
    const listToRender = active.filter(r => inProgress.length > 0 ? r.id !== inProgress[0].id : true);

    if (activeList) {
        if (listToRender.length === 0 && inProgress.length === 0) {
            activeList.style.display = 'block';
            activeList.innerHTML = `<div class="empty-state-minimal" style="padding:40px;"><i class="fas fa-calendar-xmark" style="font-size:3rem;color:#222;margin-bottom:15px;"></i><p>No tenés reservas activas.</p></div>`;
        } else {
            activeList.style.display = 'grid';
            activeList.innerHTML = listToRender.map(r => renderReservaCard(r, false)).join('');
        }
    }
    applyHistoryFilters();
}

export function applyHistoryFilters() {
    const fromVal = document.getElementById('history-filter-from')?.value;
    const toVal = document.getElementById('history-filter-to')?.value;
    let filtered = [...historyData];
    
    if (fromVal) {
        const d = new Date(fromVal); d.setHours(0,0,0,0);
        filtered = filtered.filter(r => new Date(r.fecha_inicio.replace(/-/g, "/")) >= d);
    }
    if (toVal) {
        const d = new Date(toVal); d.setHours(23,59,59,999);
        filtered = filtered.filter(r => new Date(r.fecha_inicio.replace(/-/g, "/")) <= d);
    }
    renderHistory(filtered);
}

export function renderReservaCard(r, isFeatured) {
    const now = new Date();
    const start = new Date(r.fecha_inicio.replace(/-/g, "/"));
    const end = new Date(r.fecha_fin.replace(/-/g, "/"));
    let progress = 0;
    let isStarted = now >= start;
    if (isStarted) progress = Math.min(100, Math.max(0, ((now - start) / (end - start)) * 100));

    return `
    <div class="reserva-card-ultra ${isFeatured ? 'featured' : ''}">
        <div class="reserva-header-ultra">
            <div class="reserva-info-main">
                <span class="reserva-tag-id">RESERVA #${r.id}</span>
                <div class="reserva-plate-container">
                    <div class="plate-badge-premium">${r.patente}</div>
                    ${isStarted && progress < 100 ? '<span class="status-badge-ultra active-pulse" style="background:rgba(16,185,129,0.1);color:#10b981;border:1px solid #10b981;">EN CURSO</span>' : ''}
                </div>
            </div>
            <div class="reserva-status-ultra">
                <div class="status-badge-ultra ${r.estado_pago.toLowerCase()}">${r.estado_pago}</div>
                <div class="price-container-ultra"><span class="price-value-ultra">$${r.monto_total.toLocaleString()}</span></div>
            </div>
        </div>
        <div class="reserva-timeline-container">
            <div class="timeline-labels"><span>${isStarted ? 'INGRESO' : 'INICIO'}</span><span>${isStarted ? (progress >= 100 ? 'FINALIZADA' : `PROGRESO: ${Math.round(progress)}%`) : ''}</span><span>${isStarted ? 'SALIDA' : 'FIN'}</span></div>
            <div class="timeline-progress-bg"><div class="timeline-progress-fill ${isStarted ? 'active' : ''}" style="width: ${isStarted ? progress : 0}%"></div></div>
        </div>
        <div class="reserva-details-ultra" ${isFeatured ? 'style="grid-template-columns: repeat(4, 1fr);"' : ''}>
            <div class="detail-item-ultra"><i class="fas fa-location-dot"></i><div class="detail-info-ultra"><span class="detail-label-ultra">Sucursal</span><span class="detail-value-ultra">${r.sucursal_nombre}</span></div></div>
            <div class="detail-item-ultra"><i class="fas fa-calendar-day"></i><div class="detail-info-ultra"><span class="detail-label-ultra">Estadía</span><span class="detail-value-ultra">${toTitle(r.tipo_estadia)}</span></div></div>
            <div class="detail-item-ultra"><i class="fas fa-clock"></i><div class="detail-info-ultra"><span class="detail-label-ultra">Desde</span><span class="detail-value-ultra">${formatDate(r.fecha_inicio)}</span></div></div>
            <div class="detail-item-ultra"><i class="fas fa-hourglass-end"></i><div class="detail-info-ultra"><span class="detail-label-ultra">Hasta</span><span class="detail-value-ultra">${formatDate(r.fecha_fin)}</span></div></div>
        </div>
        <div class="reserva-actions-ultra">
            ${r.estado_pago === 'Pagado' ? `<button class="btn-ultra btn-ultra-primary" onclick="showDigitalPass(${r.id})"><i class="fas fa-ticket"></i> MI PASE DIGITAL</button>` : `<button class="btn-ultra btn-ultra-primary" onclick="payReservation(${r.id})"><i class="fas fa-credit-card"></i> PAGAR AHORA</button>`}
            <button class="btn-ultra btn-ultra-secondary" onclick="prepareEditReservation(${r.id})" ${isStarted || r.estado_reserva === 'Activa' ? 'disabled' : ''}><i class="fas fa-pen"></i></button>
            <button class="btn-ultra btn-ultra-danger" onclick="cancelReservation(${r.id})" ${isStarted || r.estado_reserva === 'Activa' ? 'disabled' : ''}><i class="fas fa-trash"></i></button>
        </div>
    </div>`;
}

export function renderHistory(history) {
    const list = document.getElementById('reservation-list-history');
    if (!list) return;
    const totalPages = Math.ceil(history.length / HISTORIAL_PAGE_SIZE);
    if (history.length === 0) { list.innerHTML = '<p class="text-muted" style="padding:30px;">No hay historial.</p>'; return; }

    const paged = history.slice((historialCurrentPage - 1) * HISTORIAL_PAGE_SIZE, historialCurrentPage * HISTORIAL_PAGE_SIZE);
    list.innerHTML = paged.map(r => `
        <div class="historial-item">
            <div class="hist-icon"><i class="fas ${r.estado_reserva === 'Completada' ? 'fa-car-circle-check' : 'fa-ban'}"></i></div>
            <div class="hist-main-info"><span class="hist-title">${r.sucursal_nombre}</span><div class="hist-subtitle-group"><span class="hist-plate-badge">${r.patente}</span><span class="hist-date-info">${formatDate(r.fecha_inicio).split(',')[0]}</span></div></div>
            <div class="hist-amount-info"><span class="hist-value">$${r.monto_total.toLocaleString()}</span><div class="status-pill ${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</div></div>
            <div class="hist-actions-group"><button class="btn-repeat-express" onclick="repeatReservation('${r.patente}','${r.sucursal_nombre}','${r.tipo_estadia}')"><i class="fas fa-rotate-right"></i></button></div>
        </div>`).join('');

    if (document.getElementById('historial-page-info')) document.getElementById('historial-page-info').innerText = `Página ${historialCurrentPage} de ${totalPages || 1}`;
    const prevBtn = document.getElementById('historial-prev'); if (prevBtn) prevBtn.disabled = historialCurrentPage === 1;
    const nextBtn = document.getElementById('historial-next'); if (nextBtn) nextBtn.disabled = historialCurrentPage >= totalPages;
}

export async function cancelReservation(id) {
    if (!await showConfirm('CANCELAR RESERVA', '¿Estás seguro? Esta acción no se puede deshacer.')) return;
    const res = await api.post(`/user/reservations/${id}/cancel`);
    if (res.ok) { showToast('Reserva cancelada'); loadReservations(); if (window.loadProfile) window.loadProfile(); }
    else { showToast(res.error || 'Error al cancelar'); }
}

export async function payReservation(id) {
    if (!await showConfirm('PAGAR RESERVA', '¿Deseás pagar con tu saldo AutoPass?')) return;
    const res = await api.post(`/user/reservations/${id}/pay`);
    if (res.ok) { showToast('¡Pago exitoso!'); loadReservations(); if (window.loadProfile) window.loadProfile(); }
    else { showToast(res.error || 'Error en el pago'); }
}

export function historialPage(dir) { historialCurrentPage += dir; applyHistoryFilters(); }

export async function showDigitalPass(id) {
    const res = await api.get('/user/reservations');
    if (!res.ok) return;
    const r = res.data.find(item => item.id === id);
    if (!r) return;

    document.getElementById('ticket-id-display').innerText = `#${r.id.toString().padStart(6, '0')}`;
    document.getElementById('ticket-patente').innerText = r.patente;
    document.getElementById('ticket-vence').innerText = formatDate(r.fecha_fin).split(',')[0];
    document.getElementById('ticket-sucursal').innerText = r.sucursal_nombre;
    document.getElementById('ticket-direccion').innerText = r.sucursal_info || 'Dirección no disponible';

    const qrContainer = document.getElementById('ticket-qr');
    if (qrContainer) {
        qrContainer.innerHTML = '';
        if (window.QRCode) {
            new QRCode(qrContainer, { text: `AUTOPASS|ID:${r.id}|PLATE:${r.patente}`, width: 180, height: 180, correctLevel: QRCode.CorrectLevel.H });
        }
    }
    const modal = document.getElementById('modal-pase-digital');
    if (modal) modal.style.display = 'flex';
}

export function closeDigitalPass() {
    const modal = document.getElementById('modal-pase-digital');
    if (modal) modal.style.display = 'none';
}

export async function shareTicket() {
    const ticket = document.getElementById('ticket-to-capture');
    if (!ticket || !window.html2canvas) return;
    ticket.querySelectorAll('.no-print').forEach(el => el.style.opacity = '0');
    try {
        const canvas = await html2canvas(ticket, { backgroundColor: '#0a0a0a', scale: 3, useCORS: true });
        canvas.toBlob(async (blob) => {
            const file = new File([blob], `AutoPass_Ticket_${Date.now()}.png`, { type: 'image/png' });
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({ files: [file], title: 'Mi Pase AutoPass' });
            } else {
                const link = document.createElement('a');
                link.download = `AutoPass_Ticket_${Date.now()}.png`;
                link.href = URL.createObjectURL(blob);
                link.click();
            }
        });
    } catch (err) { 
        showToast('Error al generar imagen'); 
        console.error(err);
    } finally { 
        ticket.querySelectorAll('.no-print').forEach(el => el.style.opacity = '1'); 
    }
}

export async function repeatReservation(patente, sucursal, tipo) {
    if (window.showSection) {
        window.showSection('inicio', document.querySelector('.nav-item[onclick*="inicio"]'));
    }
    const container = document.getElementById('reserva-form-container');
    if (container && !container.classList.contains('open')) {
        await toggleReservaForm();
    }
    if (container) container.scrollIntoView({ behavior: 'smooth' });
    
    setTimeout(() => {
        const vSelect = document.querySelector('.res-vehicle');
        const sSelect = document.querySelector('.res-sucursal');
        const tSelect = document.querySelector('.res-type');
        if (vSelect) vSelect.value = patente;
        if (sSelect) sSelect.value = sucursal;
        if (tSelect) {
            tSelect.value = tipo;
            updateFormGroups(tipo);
        }
        showToast('¡Datos cargados! Seleccioná la nueva fecha.');
    }, 500);
}

export function resetHistoryFilters() {
    const f1 = document.getElementById('history-filter-from'); if (f1) f1.value = '';
    const f2 = document.getElementById('history-filter-to'); if (f2) f2.value = '';
    applyHistoryFilters();
}
