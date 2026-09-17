import api from './api.js';
import { toTitle, formatDate, formatPlate, showToast, showConfirm, formatNum } from './utils.js';
import { getVirtualNow } from './virtual-time.js';
import { loadReservations } from './reservas-list.js';

/**
 * MÓDULO RESERVAS - FORMULARIO Y TARIFAS
 * Gestión del formulario de creación/edición, cálculo dinámico de tarifas y validaciones.
 */

const RESERVA_MIN_MS = (window.RESERVA_HORA_MIN_SEGUNDOS || 1800) * 1000;
const RESERVA_MIN_MIN = (window.RESERVA_HORA_MIN_SEGUNDOS || 1800) / 60;

// CACHE CORTO PARA CONSULTAS DE DISPONIBILIDAD (EVITA RE-QUERYS EN CADA focus/click/change)
const availabilityCache = new Map();
const AVAILABILITY_CACHE_TTL_MS = 30000;

async function cachedAvailabilityGet(url, params) {
    const key = `${url}?${new URLSearchParams(params).toString()}`;
    const now = Date.now();
    const hit = availabilityCache.get(key);
    if (hit && (now - hit.t) < AVAILABILITY_CACHE_TTL_MS) {
        return hit.res;
    }
    const res = await api.get(url, { params });
    if (res && res.ok) {
        availabilityCache.set(key, { t: now, res });
        if (availabilityCache.size > 50) {
            const firstKey = availabilityCache.keys().next().value;
            availabilityCache.delete(firstKey);
        }
    }
    return res;
}

let currentRates = { '30min': 750, hora: 1500, dia: 15000, semana: 70000, quincena: 120000, mes: 200000 };
let editingReservaId = null;
let userVehicles = [];
let branchesData = [];
// DESCUENTO DE RESERVA VIGENTE PARA LA SUCURSAL SELECCIONADA (se refleja en el total estimado)
let currentReservationDiscount = { pct: 0, sucursal: '', fetchedFor: '' };
// TOTALES DEL ÚLTIMO CÁLCULO ESTIMADO (original, descuento y final)
let currentReservationTotals = { original: 0, discount: 0, final: 0 };
// TOKEN ANTI-RACE PARA CONSULTAS CONCURRENTES DE DESCUENTO POR SUCURSAL
let discountFetchToken = 0;

// RANGO DE LA GRILLA HORARIA SEGÚN EL HORARIO DE LA SUCURSAL SELECCIONADA.
// RESPETA is_24h (00:00 → 23:30) Y el horario configurado (ej. "07:00 A 23:00" → 07:00 → 22:30).
// Fallback al rango legado 07:00 → 23:30 si no hay info de horario disponible.
function _branchSlotRange() {
    const sucursalSelect = document.querySelector('.res-sucursal');
    const sucursal = sucursalSelect ? sucursalSelect.value : '';
    const branch = branchesData.find(b => b.nombre === sucursal);
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

export function getEditingReservaId() {
    return editingReservaId;
}

export function setEditingReservaId(val) {
    editingReservaId = val;
}

export function getUserVehicles() {
    return userVehicles;
}

let fpInstances = {};

export async function updateDisabledDatesInPicker() {
    const sucursalSelect = document.querySelector('.res-sucursal');
    const vehicleSelect = document.querySelector('.res-vehicle');
    const typeSelect = document.querySelector('.res-type');

    if (!sucursalSelect || !vehicleSelect || !typeSelect) return;

    const sucursal = sucursalSelect.value;
    const patente = vehicleSelect.value;
    const tipoEstadia = typeSelect.value;

    if (!sucursal || !patente || !tipoEstadia) return;

    const veh = userVehicles.find(v => v.patente === patente);
    const tipoVehiculo = veh ? veh.tipo : 'Auto';

    try {
        const res = await cachedAvailabilityGet('/user/reservations/disabled-dates', {
            sucursal_nombre: sucursal,
            tipo_vehiculo: tipoVehiculo,
            tipo_estadia: tipoEstadia
        });

        if (res.ok && res.data && Array.isArray(res.data.disabled_dates)) {
            const disabledDates = res.data.disabled_dates;
            const fpMap = {
                'hora': fpInstances.hourlyDate,
                'dia': fpInstances.day,
                'semana': fpInstances.week,
                'quincena': fpInstances.fortnight,
                'mes': fpInstances.month
            };

            Object.values(fpMap).forEach(fpRef => {
                if (fpRef) {
                    const fpObj = Array.isArray(fpRef) ? fpRef[0] : fpRef;
                    if (fpObj && typeof fpObj.set === 'function') {
                        fpObj.set('disable', disabledDates);
                    }
                }
            });
        }
    } catch (err) {
        console.warn('[RESERVAS] Error cargando fechas deshabilitadas:', err);
    }
}

let slotRangeStart = null;
let slotRangeEnd = null;
let slotRangeDate = null;

export async function updateHourlySlotsUI() {
    const sucursalSelect = document.querySelector('.res-sucursal');
    const vehicleSelect = document.querySelector('.res-vehicle');
    const typeSelect = document.querySelector('.res-type');
    const dateInput = document.querySelector('.res-date-only');
    const timeInput = document.querySelector('.res-time-only');
    const hoursQtyInput = document.querySelector('.res-hours-qty');

    const container = document.getElementById('availability-status-container');
    const badge = document.getElementById('availability-badge');
    const grid = document.getElementById('hourly-slots-grid');

    if (!container || !badge || !grid) return;

    if (!typeSelect || typeSelect.value !== 'hora') {
        grid.style.display = 'none';
        grid.innerHTML = '';
        return;
    }

    container.style.display = 'flex';

    if (!sucursalSelect || !sucursalSelect.value) {
        grid.innerHTML = '<div style="width:100%; text-align:center; font-size:0.8rem; color:var(--dorado); padding:8px;"><i class="fas fa-info-circle" style="margin-right:6px;"></i> Seleccioná tu sucursal para ver la disponibilidad horaria en vivo</div>';
        grid.style.display = 'flex';
        badge.style.display = 'none';
        return;
    }

    if (!vehicleSelect || !vehicleSelect.value) {
        grid.innerHTML = '<div style="width:100%; text-align:center; font-size:0.8rem; color:var(--dorado); padding:8px;"><i class="fas fa-info-circle" style="margin-right:6px;"></i> Seleccioná tu vehículo para consultar la disponibilidad de plazas</div>';
        grid.style.display = 'flex';
        badge.style.display = 'none';
        return;
    }

    const sucursal = sucursalSelect.value;
    const patente = vehicleSelect.value;
    const fecha = dateInput ? dateInput.value : '';

    if (slotRangeDate && slotRangeDate !== fecha) {
        slotRangeStart = null;
        slotRangeEnd = null;
        slotRangeDate = null;
        if (timeInput) timeInput.value = '';
        if (hoursQtyInput) hoursQtyInput.value = '1';
    }

    if (!fecha) {
        grid.innerHTML = '<div style="width:100%; text-align:center; font-size:0.8rem; color:var(--dorado); padding:8px;"><i class="fas fa-calendar-day" style="margin-right:6px;"></i> Seleccioná la fecha en el calendario para consultar los horarios libres</div>';
        grid.style.display = 'flex';
        badge.style.display = 'none';
        return;
    }

    const veh = userVehicles.find(v => v.patente === patente);
    const tipoVehiculo = veh ? veh.tipo : 'Auto';
    const duracionHoras = 1;

    try {
        const res = await cachedAvailabilityGet('/user/reservations/disabled-hours', {
            sucursal_nombre: sucursal,
            fecha: fecha,
            tipo_vehiculo: tipoVehiculo,
            duracion_horas: duracionHoras,
            paso_minutos: 30
        });

        if (res.ok && res.data && Array.isArray(res.data.disabled_hours)) {
            const reservedRanges = Array.isArray(res.data.reserved_ranges) ? res.data.reserved_ranges : [];
            // SLOTS DESHABILITADOS POR CAPACIDAD CALCULADOS EN EL SERVER (OCUPADA >= CAPACIDAD):
            // NO SON SOLO LOS RANGOS DE RESERVAS, POR ESO HAY QUE RESPETARLOS ADEMÁS DE reservedRanges.
            const disabledSet = new Set(Array.isArray(res.data.disabled_hours) ? res.data.disabled_hours : []);

            // HOY: BLOQUEAR LOS SLOTS QUE YA PASARON O NO RESPETAN LA ANTICIPACION MINIMA
            // (EL SERVER TAMBIEN LOS FILTRA, PERO EL CACHE DE 30s PUEDE ESTAR DESACTUALIZADO)
            const now = getVirtualNow();
            const fechaHoy = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
            const blockedToday = [];
            if (fecha === fechaHoy) {
                const rango = _branchSlotRange();
                const minInicioMs = now.getTime() + RESERVA_MIN_MS;
                for (let min = rango.start; min <= rango.end; min += 30) {
                    const hh = Math.floor(min / 60);
                    const mm = min % 60;
                    const hStr = `${String(hh).padStart(2, '0')}:${String(mm).padStart(2, '0')}`;
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
                    ${_hourlySelectionSummary()}
                </div>
                <div class="chips-container-premium" style="display:grid; grid-template-columns:repeat(6, 1fr); gap:4px; width:100%;">
            `;

            let countTotal = 0;
            let countLibres = 0;

            const rango = _branchSlotRange();
            for (let min = rango.start; min <= rango.end; min += 30) {
                const h = Math.floor(min / 60);
                const m = min % 60;
                const hourStr = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;

                let isReserved = false;
                let isBoundaryEnd = false;
                for (const rg of reservedRanges) {
                    if (hourStr >= rg.inicio && hourStr < rg.fin) isReserved = true;
                    if (hourStr === rg.inicio) isBoundaryEnd = true;
                }
                // SI EL SERVER LO DESHABILITÓ POR CAPACIDAD, EL SLOT NO PUEDE USARSE NI COMO INICIO NI COMO FIN
                if (disabledSet.has(hourStr)) {
                    isReserved = true;
                    isBoundaryEnd = false;
                }
                const isBlockedToday = fecha === fechaHoy && blockedToday.includes(hourStr);
                if (!isReserved && !isBlockedToday) countLibres++;
                countTotal++;

                const inRange = slotRangeStart && slotRangeEnd
                    && hourStr > slotRangeStart && hourStr < slotRangeEnd;
                const isStart = slotRangeStart === hourStr;
                const isEnd = slotRangeEnd === hourStr;

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

            // COMPLETAR LA ULTIMA FILA CON CELDAS VACIAS PARA MANTENER LA GRILLA ALINEADA (6 COLUMNAS)
            const resto = countTotal % 6;
            if (resto > 0) {
                for (let i = 0; i < 6 - resto; i++) {
                    html += `<span class="hourly-chip-premium placeholder"></span>`;
                }
            }

            html += `</div>`;

            grid.innerHTML = html;
            grid.style.display = 'flex';
            badge.style.display = 'none';
        }
    } catch (e) {
        console.warn('[RESERVAS] Error cargando disponibilidad horaria:', e);
    }
}

function _hourlySelectionSummary() {
    if (!slotRangeStart) {
        return '<div class="hourly-range-summary hint">Elegí el <b>INICIO</b> (verde) y después el <b>FIN</b> (rojo) de tu estadía:</div>';
    }
    let dur = '';
    if (slotRangeEnd && _slotToMin(slotRangeEnd) > _slotToMin(slotRangeStart)) {
        const horas = Math.round((_slotToMin(slotRangeEnd) - _slotToMin(slotRangeStart)) / 60 * 10) / 10;
        dur = `<span class="hsum-dur">(${horas} hs)</span>`;
    }
    return `<div class="hourly-range-summary">
        <span class="hsum-chip hsum-start"><i class="fas fa-arrow-right-to-bracket"></i> INICIO ${slotRangeStart}</span>
        <span class="hsum-arrow"><i class="fas fa-arrow-right"></i></span>
        <span class="hsum-chip hsum-end"><i class="fas fa-arrow-right-from-bracket"></i> FIN ${slotRangeEnd || '— toca la hora de <b>fin</b>'}</span>
        ${dur}
    </div>`;
}

let slotDragActive = false;

const _slotToMin = (t) => {
    const [hh, mm] = (t || '00:00').split(':').map(Number);
    return hh * 60 + mm;
};

const _slotCommitRange = function() {
    const timeInput = document.querySelector('.res-time-only');
    const hoursQtyInput = document.querySelector('.res-hours-qty');
    const dateInput = document.querySelector('.res-date-only');
    if (!timeInput || !hoursQtyInput) return;

    if (dateInput && dateInput.value) slotRangeDate = dateInput.value;

    if (slotRangeStart && slotRangeEnd && _slotToMin(slotRangeEnd) > _slotToMin(slotRangeStart)) {
        timeInput.value = slotRangeStart;
        hoursQtyInput.value = Math.round((_slotToMin(slotRangeEnd) - _slotToMin(slotRangeStart)) / 60 * 10) / 10;
    } else {
        timeInput.value = '';
        hoursQtyInput.value = '1';
    }
    updateReservationPrice();
    updateHourlySlotsUI();
};

export function selectHourRange(hourStr) {
    if (!slotDragActive) {
        if (!slotRangeStart || _slotToMin(hourStr) < _slotToMin(slotRangeStart)) {
            slotRangeStart = hourStr;
            slotRangeEnd = null;
        } else if (!slotRangeEnd) {
            slotRangeEnd = hourStr;
        } else {
            slotRangeStart = hourStr;
            slotRangeEnd = null;
        }
        _slotCommitRange();
    }
};

export function initHourlySlotDrag() {
    const grid = document.getElementById('hourly-slots-grid');
    if (!grid) return;

    grid.addEventListener('pointerdown', (ev) => {
        if (ev.button !== undefined && ev.button !== 0 && ev.type === 'pointerdown') return;
        const chip = ev.target.closest('.hourly-chip-premium');
        if (!chip || chip.classList.contains('full')) return;
        const hourStr = chip.dataset.hora;
        if (!hourStr) return;

        ev.preventDefault();
        slotDragActive = true;

        try { grid.setPointerCapture(ev.pointerId); } catch (e) { /* noop */ }

        if (!slotRangeStart || _slotToMin(hourStr) < _slotToMin(slotRangeStart)) {
            slotRangeStart = hourStr;
            slotRangeEnd = null;
        } else if (!slotRangeEnd) {
            if (hourStr === slotRangeStart) {
                slotRangeEnd = null;
            } else {
                slotRangeEnd = hourStr;
            }
        } else {
            slotRangeStart = hourStr;
            slotRangeEnd = null;
        }
        _slotCommitRange();
    });

    grid.addEventListener('pointermove', (ev) => {
        if (!slotDragActive) return;
        const el = document.elementFromPoint(ev.clientX, ev.clientY);
        const chip = el && el.closest('.hourly-chip-premium');
        if (!chip || chip.classList.contains('full')) return;
        const hourStr = chip.dataset.hora;
        if (!hourStr) return;

        if (_slotToMin(hourStr) > _slotToMin(slotRangeStart)) {
            if (!slotRangeEnd || slotRangeEnd !== hourStr) {
                slotRangeEnd = hourStr;
                _slotCommitRange();
            }
        } else if (_slotToMin(hourStr) < _slotToMin(slotRangeStart)) {
            slotRangeStart = hourStr;
            slotRangeEnd = null;
            _slotCommitRange();
        }
    });

    const finishDrag = () => {
        if (!slotDragActive) return;
        slotDragActive = false;
        _slotCommitRange();
    };
    grid.addEventListener('pointerup', finishDrag);
    grid.addEventListener('pointercancel', finishDrag);
}

export async function updatePeriodAvailabilityBadge() {
    const sucursalSelect = document.querySelector('.res-sucursal');
    const vehicleSelect = document.querySelector('.res-vehicle');
    const typeSelect = document.querySelector('.res-type');
    const container = document.getElementById('availability-status-container');
    const badge = document.getElementById('availability-badge');
    const grid = document.getElementById('hourly-slots-grid');

    if (!container || !badge || !grid) return;

    if (!typeSelect || typeSelect.value === 'hora' || !sucursalSelect || !sucursalSelect.value || !vehicleSelect || !vehicleSelect.value) {
        if (typeSelect && typeSelect.value !== 'hora') {
            container.style.display = 'none';
            badge.style.display = 'none';
        }
        return;
    }

    const type = typeSelect.value;
    let inicio, fin;

    if (type === 'dia') {
        const fecha = document.querySelector('.res-day-only')?.value;
        if (fecha) { inicio = `${fecha} 00:00`; fin = `${fecha} 23:59`; }
    } else {
        const selectorMap = { 'semana': '.res-week-start', 'quincena': '.res-fortnight-start', 'mes': '.res-month-start' };
        const fecha = document.querySelector(selectorMap[type])?.value;
        const periodDays = { 'semana': 7, 'quincena': 15, 'mes': 30 }[type];
        if (fecha && periodDays) {
            inicio = `${fecha} 00:00`;
            const startDt = new Date(fecha.replace(/-/g, "/"));
            const endDt = new Date(startDt.getTime() + (periodDays - 1) * 24 * 60 * 60 * 1000);
            fin = `${endDt.getFullYear()}-${String(endDt.getMonth()+1).padStart(2,'0')}-${String(endDt.getDate()).padStart(2,'0')} 23:59`;
        }
    }

    if (!inicio || !fin) return;

    container.style.display = 'flex';
    grid.style.display = 'none';

    const sucursal = sucursalSelect.value;
    const patente = vehicleSelect.value;
    const veh = userVehicles.find(v => v.patente === patente);
    const tipoVehiculo = veh ? veh.tipo : 'Auto';

    try {
        const av = await api.get('/user/reservations/check-availability', {
            params: {
                sucursal_nombre: sucursal,
                fecha_inicio: inicio,
                fecha_fin: fin,
                tipo_vehiculo: tipoVehiculo
            }
        });

        if (av.ok && av.data) {
            if (av.data.disponible) {
                badge.className = 'availability-badge-premium success';
                badge.innerHTML = `<i class="fas fa-check-circle"></i> Disponibilidad confirmada en ${sucursal} (${av.data.restan} de ${av.data.capacidad_total} plazas libres para ${tipoVehiculo}s)`;
            } else {
                badge.className = 'availability-badge-premium danger';
                badge.innerHTML = `<i class="fas fa-triangle-exclamation"></i> Sin disponibilidad de plazas de ${tipoVehiculo} en ${sucursal} para este período`;
            }
            badge.style.display = 'inline-flex';
        }
    } catch (e) {
        console.warn('[RESERVAS] Error verificando disponibilidad de período:', e);
    }
}

export function initReservationForm() {
    if (!window.flatpickr) return;

    // CONFIGURAR IDIOMA ESPAÑOL GLOBALMENTE SI ESTÁ CARGADO
    if (window.flatpickr.l10ns?.es) {
        window.flatpickr.localize(window.flatpickr.l10ns.es);
    }

    const now = getVirtualNow();
    const maxDate = new Date(now.getFullYear(), now.getMonth() + 3, now.getDate());
    const commonConfig = {
        minDate: "today",
        maxDate: maxDate,
        disableMobile: "true",
        altInput: true,
        altFormat: "d-m-y",
        dateFormat: "Y-m-d",
        defaultDate: now,
        onChange: () => {
            updateReservationPrice();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
        }
    };

    fpInstances.hourlyDate = flatpickr(".res-date-only", { ...commonConfig });
    fpInstances.day = flatpickr(".res-day-only", { ...commonConfig });
    fpInstances.week = flatpickr(".res-week-start", { 
        ...commonConfig, 
        onChange: (sd, ds) => {
            updatePeriodEnd(ds, 7, '.res-week-end');
            updatePeriodAvailabilityBadge();
        } 
    });
    fpInstances.fortnight = flatpickr(".res-fortnight-start", { 
        ...commonConfig, 
        onChange: (sd, ds) => {
            updatePeriodEnd(ds, 15, '.res-fortnight-end');
            updatePeriodAvailabilityBadge();
        } 
    });
    fpInstances.month = flatpickr(".res-month-start", { 
        ...commonConfig, 
        onChange: (sd, ds) => {
            updatePeriodEnd(ds, 30, '.res-month-end');
            updatePeriodAvailabilityBadge();
        } 
    });
    fpInstances.start = flatpickr(".res-start", { ...commonConfig, enableTime: true, altFormat: "d-m-y H:i", dateFormat: "Y-m-d H:i" });
    fpInstances.end = flatpickr(".res-end", { ...commonConfig, enableTime: true, altFormat: "d-m-y H:i", dateFormat: "Y-m-d H:i" });

    // CALCULAR FECHAS DE FIN PARA PERÍODOS CON LA FECHA POR DEFECTO
    const todayYmd = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
    updatePeriodEnd(todayYmd, 7, '.res-week-end');
    updatePeriodEnd(todayYmd, 15, '.res-fortnight-end');
    updatePeriodEnd(todayYmd, 30, '.res-month-end');

    const typeSelect = document.querySelector('.res-type');
    if (typeSelect) {
        typeSelect.addEventListener('change', (e) => {
            slotRangeStart = null;
            slotRangeEnd = null;
            updateFormGroups(e.target.value);
            updateDisabledDatesInPicker();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
        });
    }

    const vehicleSelect = document.querySelector('.res-vehicle');
    if (vehicleSelect) {
        vehicleSelect.addEventListener('change', () => {
            slotRangeStart = null;
            slotRangeEnd = null;
            updateReservationPrice();
            updateDisabledDatesInPicker();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
        });
    }

    const sucursalSelect = document.querySelector('.res-sucursal');
    if (sucursalSelect) {
        sucursalSelect.addEventListener('change', (e) => {
            slotRangeStart = null;
            slotRangeEnd = null;
            const sucursalId = e.target.value;
            fetchRates(sucursalId);
            updateDisabledDatesInPicker();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
        });
    }

    const hoursInput = document.querySelector('.res-hours-qty');
    if (hoursInput) {
        hoursInput.addEventListener('input', () => updateReservationPrice());
    }

    const timeInput = document.querySelector('.res-time-only');
    if (timeInput) {
        timeInput.addEventListener('change', () => {
            updateReservationPrice();
            updateHourlySlotsUI();
        });
        timeInput.addEventListener('focus', () => updateHourlySlotsUI());
        timeInput.addEventListener('click', () => updateHourlySlotsUI());
    }

    const dateInput = document.querySelector('.res-date-only');
    if (dateInput) {
        dateInput.addEventListener('focus', () => updateHourlySlotsUI());
        dateInput.addEventListener('click', () => updateHourlySlotsUI());
    }

    initHourlySlotDrag();
}

export function updatePeriodEnd(startDateStr, days, targetSelector) {
    if (!startDateStr) return;
    const endInput = document.querySelector(targetSelector);
    if (!endInput) return;
    
    const start = new Date(startDateStr.replace(/-/g, "/"));
    const end = new Date(start.getTime() + (days - 1) * 24 * 60 * 60 * 1000);
    const day = end.getDate().toString().padStart(2, '0');
    const month = (end.getMonth() + 1).toString().padStart(2, '0');
    const year = end.getFullYear().toString().slice(-2);
    endInput.value = `${day}-${month}-${year} 23:59`;
    updateReservationPrice();
}

export async function toggleReservaForm() {
    const container = document.getElementById('reserva-form-container');
    const trigger = document.querySelector('.reserva-trigger-card');
    if (!container || !trigger) return;

    const isOpen = container.classList.contains('open');

    if (!isOpen) {
        trigger.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        trigger.style.opacity = '0';
        trigger.style.transform = 'translateY(-10px)';
        
        setTimeout(async () => {
            trigger.style.display = 'none';
            container.style.display = 'block';
            container.style.opacity = '0';
            container.style.transform = 'translateY(10px)';
            container.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            
            container.offsetHeight; // Reflow
            
            container.classList.add('open');
            container.style.opacity = '1';
            container.style.transform = 'translateY(0)';
            
            await refreshReservationFormState();
        }, 300);
    } else {
        container.style.opacity = '0';
        container.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            container.classList.remove('open');
            container.style.display = 'none';
            resetReservaForm();
            
            trigger.style.display = 'block';
            trigger.offsetHeight; // Reflow
            trigger.style.opacity = '1';
            trigger.style.transform = 'translateY(0)';
        }, 400);
    }
}

export async function refreshReservationFormState() {
    const container = document.getElementById('reserva-form-container');
    if (!container) return;

    // REINICIA EL CACHE DE DESCUENTO (siempre se consulta el estado actual al abrir el formulario)
    currentReservationDiscount = { pct: 0, sucursal: '', fetchedFor: '' };
    discountFetchToken++;

    fetchRates();
    
    // 1. CARGAR VEHÍCULOS
    const resVehicles = await api.get('/user/vehicles');
    if (resVehicles.ok) {
        userVehicles = resVehicles.data;
        const noVehiclesSec = document.getElementById('reserva-no-vehicles');
        const mainForm = document.getElementById('reserva-form-content');

        if (userVehicles.length === 0) {
            if (noVehiclesSec) noVehiclesSec.style.display = 'block';
            if (mainForm) mainForm.style.display = 'none';
        } else {
            if (noVehiclesSec) noVehiclesSec.style.display = 'none';
            if (mainForm) mainForm.style.display = 'block';
            const selects = document.querySelectorAll('.res-vehicle');
            selects.forEach(select => {
                const currentVal = select.value;
                select.innerHTML = '<option value="" selected disabled hidden>Seleccioná vehículo...</option>' + 
                    userVehicles.map(v => `<option value="${v.patente}">${formatPlate(v.patente)} - ${v.marca_modelo}</option>`).join('');
                if (currentVal) select.value = currentVal;
                if (userVehicles.length === 1) {
                    select.value = userVehicles[0].patente;
                }
            });
            if (userVehicles.length === 1) {
                selects.forEach(select => select.value = userVehicles[0].patente);
                updateReservationPrice();
            } else {
                const fav = userVehicles.find(v => v.is_favorite);
                if (fav) {
                    selects.forEach(select => select.value = fav.patente);
                    updateReservationPrice();
                }
            }

            try {
                if (userVehicles.length === 1) {
                    const container = document.getElementById('reserva-form-container');
                    if (container && !container.classList.contains('open') && typeof toggleReservaForm === 'function') {
                        toggleReservaForm();
                        setTimeout(() => {
                            const dateInput = document.querySelector('.res-date-only') || document.querySelector('.res-start');
                            if (dateInput) dateInput.focus();
                            if (typeof showToast === 'function') showToast('Seleccionamos tu vehículo para acelerar la reserva', 'info');
                        }, 400);
                    }
                }
            } catch (e) { console.error('[AUTOSELECT] ', e); }
        }
    }

    // 2. CARGAR SUCURSALES DINÁMICAMENTE
    const resBranches = await api.get('/admin/branches');
    if (resBranches.ok) {
        branchesData = resBranches.data;
        const sucursalSelects = document.querySelectorAll('.res-sucursal');
        sucursalSelects.forEach(select => {
            const currentVal = select.value;
            select.innerHTML = '<option value="" selected disabled hidden>Seleccioná sucursal...</option>' + 
                branchesData.map(b => `<option value="${b.nombre}">${b.nombre}</option>`).join('');
            if (currentVal) select.value = currentVal;
        });
    }

    // YA CON LAS SUCURSALES CARGADAS: consulta tarifas + descuento para la sucursal seleccionada
    await fetchRates();
}

export function resetReservaForm() {
    editingReservaId = null;
    slotRangeStart = null;
    slotRangeEnd = null;
    slotRangeDate = null;
    const form = document.querySelector('.reservation-form-modern');
    if (form) {
        form.reset();
        updateFormGroups("");
    }
    const btnSpan = document.querySelector('.btn-confirm-premium span');
    if (btnSpan) btnSpan.innerText = 'CONTINUAR';
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

    const now = getVirtualNow();
    const start = new Date(r.fecha_inicio.replace(/-/g, "/"));
    if (r.tipo_estadia === 'hora' && (start - now) < RESERVA_MIN_MS) {
        return showToast(`No se puede modificar con menos de ${RESERVA_MIN_MIN} minutos de antelación`, 'info');
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
            const endParts = r.fecha_fin.split(' ');
            document.querySelector('.res-date-only').value = dtParts[0];
            document.querySelector('.res-time-only').value = dtParts[1];
            slotRangeStart = dtParts[1];
            slotRangeEnd = endParts[1] || null;
            slotRangeDate = dtParts[0];
            const startDt = new Date(r.fecha_inicio.replace(/-/g, "/"));
            const endDt = new Date(r.fecha_fin.replace(/-/g, "/"));
            const minutes = Math.round((endDt - startDt) / 60000);
            const hours = minutes / 60;
            document.querySelector('.res-hours-qty').value = hours > 0 ? hours : 1;
            updateHourlySlotsUI();
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
    }
    await lazyLoadDiscount(sucursal);
    updateReservationPrice();
}

// CONSULTA EL DESCUENTO DE RESERVA (%) VIGENTE PARA LA SUCURSAL Y LO CACHEA.
// Lazy: si ya se cargó para esa sucursal no se vuelve a consultar; al completar la consulta
// re-renderiza el total (evita que quede "Total sin descuento" si se eligió la hora antes).
async function lazyLoadDiscount(sucursal = null) {
    const branch = sucursal || document.querySelector('.res-sucursal')?.value || '';
    if (!branch) {
        currentReservationDiscount = { pct: 0, sucursal: '', fetchedFor: '' };
        return;
    }
    if (currentReservationDiscount.fetchedFor === branch) return;
    const token = ++discountFetchToken;
    let pct = 0;
    let suc = '';
    try {
        const res = await api.get(`/user/redemptions/available?sucursal=${encodeURIComponent(branch)}`);
        if (res.ok && res.data && res.data.length > 0) {
            pct = res.data[0].valor_descuento || 0;
            suc = res.data[0].sucursal || '';
        }
    } catch (e) { /* noop */ }

    if (token === discountFetchToken) {
        currentReservationDiscount = { pct, sucursal: suc, fetchedFor: branch };
        updateReservationPrice();
    }
}

export function updateReservationPrice() {
    const typeSelect = document.querySelector('.res-type');
    const vehicleSelect = document.querySelector('.res-vehicle');
    if (!typeSelect) return;
    
    const type = typeSelect.value;
    const patente = vehicleSelect?.value;
    const totalEl = document.getElementById('reserva-total-est');
    const ratesDetailEl = document.getElementById('reserva-rates-detail');
    let total = 0;

    const vehiculo = userVehicles.find(v => v.patente === patente);
    const isMoto = vehiculo && vehiculo.tipo === 'Moto';

    const key = isMoto ? `${type}_moto` : type;
    const rate = currentRates[key] || currentRates[type] || 0;
    const rate30 = currentRates[isMoto ? '30min_moto' : '30min'] || rate / 2;

    if (ratesDetailEl) {
        if (type === 'hora' && rate > 0) {
            ratesDetailEl.style.display = 'block';
            ratesDetailEl.innerHTML = `1 hora = <b style="color:#dfba6b;">$${formatNum(rate)}</b> &nbsp;·&nbsp; 30 min = <b style="color:#dfba6b;">$${formatNum(rate30)}</b>`;
        } else {
            ratesDetailEl.style.display = 'none';
            ratesDetailEl.innerHTML = '';
        }
    }

    let inicio, fin;
    try {
        if (type === 'hora') {
            const fecha = document.querySelector('.res-date-only')?.value;
            const hora = document.querySelector('.res-time-only')?.value;
            const hoursQtyInput = document.querySelector('.res-hours-qty');
            const hoursQty = parseFloat(hoursQtyInput?.value);
            
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
            const key = isMoto ? `${type}_moto` : type;
            const rate = currentRates[key] || currentRates[type] || 0;
            const rate30 = currentRates[isMoto ? '30min_moto' : '30min'] || rate / 2;
            
            if (type === 'hora') total = Math.max(1, Math.ceil(durationHours * 2)) * rate30;
            else if (type === 'dia') total = Math.max(1, Math.ceil(durationHours / 24)) * rate;
            else if (type === 'semana') total = Math.ceil(durationHours / (24 * 7)) * rate;
            else if (type === 'quincena') total = Math.ceil(durationHours / (24 * 15)) * rate;
            else if (type === 'mes') total = Math.ceil(durationHours / (24 * 30)) * rate;
            else total = Math.ceil(durationHours) * rate;
        }
    } catch (e) { console.error("Error calculando precio:", e); }

    const originalEl = document.getElementById('reserva-total-original');
    const discountLineEl = document.getElementById('reserva-discount-line');
    const labelEl = document.getElementById('reserva-total-label');
    const pct = currentReservationDiscount.pct || 0;

    if (total > 0 && pct > 0) {
        const discountAmount = Math.round(total * pct) / 100;
        const finalTotal = total - discountAmount;
        currentReservationTotals = { original: total, discount: discountAmount, final: finalTotal };
        if (originalEl) { originalEl.innerText = `$ ${formatNum(total)}`; originalEl.style.display = 'inline-block'; }
        if (discountLineEl) {
            discountLineEl.innerHTML = `<i class="fas fa-percent"></i> DESCUENTO ${pct}%${currentReservationDiscount.sucursal ? ` · ${currentReservationDiscount.sucursal}` : ''} &nbsp;·&nbsp; - $ ${formatNum(discountAmount)}`;
            discountLineEl.style.display = 'block';
        }
        if (labelEl) labelEl.innerText = 'Total a pagar:';
        if (totalEl) totalEl.innerText = `$ ${formatNum(finalTotal)}`;
    } else {
        currentReservationTotals = { original: total, discount: 0, final: total };
        if (originalEl) { originalEl.innerText = ''; originalEl.style.display = 'none'; }
        if (discountLineEl) { discountLineEl.innerHTML = ''; discountLineEl.style.display = 'none'; }
        if (labelEl) labelEl.innerText = 'Total:';
        if (totalEl) totalEl.innerText = total > 0 ? `$ ${formatNum(total)}` : '$ ---';
    }

    // GARANTIZA QUE EL DESCUENTO DE LA SUCURSAL ESTÉ CARGADO (carga lazy + re-render cuando llega)
    const selBranch = document.querySelector('.res-sucursal')?.value || '';
    if (total > 0) lazyLoadDiscount(selBranch);
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
    if (activeSection) {
        activeSection.style.display = activeSection.dataset.display || 'grid';
    }
    if (type === 'semana') {
        const v = document.querySelector('.res-week-start')?.value;
        if (v) updatePeriodEnd(v, 7, '.res-week-end');
    } else if (type === 'quincena') {
        const v = document.querySelector('.res-fortnight-start')?.value;
        if (v) updatePeriodEnd(v, 15, '.res-fortnight-end');
    } else if (type === 'mes') {
        const v = document.querySelector('.res-month-start')?.value;
        if (v) updatePeriodEnd(v, 30, '.res-month-end');
    }
    updateReservationPrice();
}

export async function createReservation(e) {
    if (e) e.preventDefault();
    console.group("AutoPass: Creando Reserva");
    
    const patenteEl = document.querySelector('.res-vehicle');
    const sucursalEl = document.querySelector('.res-sucursal');
    const tipoEl = document.querySelector('.res-type');
    const btn = document.querySelector('.btn-confirm-premium');
    
    if (!patenteEl || !sucursalEl || !tipoEl || !btn) {
        console.error("[!] Error: No se encontraron los campos del formulario.");
        console.groupEnd();
        return showToast('Error interno: Formulario incompleto', 'error');
    }

    if (!userVehicles || userVehicles.length === 0) {
        if (typeof window.showQuickAddVehicle === 'function') window.showQuickAddVehicle();
        console.groupEnd();
        return showToast('Agregá tu primer vehículo para poder reservar', 'info');
    }

    const patente = patenteEl.value;
    const sucursal = sucursalEl.value;
    const tipo = tipoEl.value;
    const originalContent = btn.innerHTML;
    
    if (!patente) { console.groupEnd(); return showToast('Seleccioná un vehículo', 'info'); }
    if (!sucursal) { console.groupEnd(); return showToast('Seleccioná una sucursal', 'info'); }
    if (!tipo) { console.groupEnd(); return showToast('Seleccioná tipo de estadía', 'info'); }

    let inicio, fin;

    try {
        if (tipo === 'hora') {
            const fecha = document.querySelector('.res-date-only').value;
            const hora = document.querySelector('.res-time-only').value;
            const hoursQty = parseFloat(document.querySelector('.res-hours-qty').value) || 1;
            if (!fecha || !hora) { console.groupEnd(); return showToast('Seleccioná fecha y hora', 'info'); }
            inicio = `${fecha} ${hora}`;
            const now = getVirtualNow();
            const startDt = new Date(inicio.replace(/-/g, "/"));
            if ((startDt - now) < RESERVA_MIN_MS) { console.groupEnd(); return showToast(`Mínimo ${RESERVA_MIN_MIN} minutos de anticipación.`, 'info'); }
            const endDt = new Date(startDt.getTime() + hoursQty * 60 * 60 * 1000);
            fin = `${endDt.getFullYear()}-${(endDt.getMonth() + 1).toString().padStart(2, '0')}-${endDt.getDate().toString().padStart(2, '0')} ${endDt.getHours().toString().padStart(2, '0')}:${endDt.getMinutes().toString().padStart(2, '0')}`;
            
            const branch = branchesData.find(b => b.nombre === sucursal);
            if (branch && !branch.is_24h && branch.horario) {
                const hMatch = branch.horario.toUpperCase().trim().match(/^(\d{1,2}):(\d{2})\s+(?:A|UN)\s+(\d{1,2}):(\d{2})$/);
                if (hMatch) {
                    let open = parseInt(hMatch[1]) * 60 + parseInt(hMatch[2]);
                    let close = parseInt(hMatch[3]) * 60 + parseInt(hMatch[4]);
                    if (close === 0) close = 1439;
                    const startMin = startDt.getHours() * 60 + startDt.getMinutes();
                    const endMin = endDt.getHours() * 60 + endDt.getMinutes();
                    const endDateStr2 = `${endDt.getFullYear()}-${(endDt.getMonth() + 1).toString().padStart(2, '0')}-${endDt.getDate().toString().padStart(2, '0')}`;
                    if (endDateStr2 !== fecha) {
                        console.groupEnd();
                        return showToast(`La sucursal cierra a las ${hMatch[3]}:${hMatch[4]}. La estadía no puede extenderse más allá del cierre.`, 'info');
                    }
                    if (startMin < open || startMin >= close) {
                        console.groupEnd();
                        return showToast(`La sucursal abre de ${branch.horario}. La hora de inicio debe estar dentro del horario de atención.`, 'info');
                    }
                    if (endMin > close) {
                        console.groupEnd();
                        return showToast(`La sucursal cierra a las ${hMatch[3]}:${hMatch[4]}. La hora de fin no puede exceder el horario de cierre.`, 'info');
                    }
                }
            }
        } else if (tipo === 'dia') {
            const fecha = document.querySelector('.res-day-only').value;
            if (!fecha) { console.groupEnd(); return showToast('Seleccioná un día', 'info'); }
            inicio = `${fecha} 00:00`;
            fin = `${fecha} 23:59`;
        } else {
            const periods = { 'semana': 7, 'quincena': 15, 'mes': 30 };
            const periodClasses = { 'semana': '.res-week-start', 'quincena': '.res-fortnight-start', 'mes': '.res-month-start' };
            if (periods[tipo]) {
                const selector = periodClasses[tipo];
                const fecha = document.querySelector(selector).value;
                if (!fecha) { console.groupEnd(); return showToast('Seleccioná día de inicio', 'info'); }
                inicio = `${fecha} 00:00`;
                const startDt = new Date(fecha.replace(/-/g, "/"));
                const endDt = new Date(startDt.getTime() + (periods[tipo] - 1) * 24 * 60 * 60 * 1000);
                fin = `${endDt.getFullYear()}-${(endDt.getMonth() + 1).toString().padStart(2, '0')}-${endDt.getDate().toString().padStart(2, '0')} 23:59`;
            } else {
                inicio = document.querySelector('.res-start').value;
                fin = document.querySelector('.res-end').value;
            }
        }
    } catch (err) {
        console.error("[!] Error procesando fechas:", err);
        console.groupEnd();
        return showToast('Error en el formato de fecha', 'error');
    }

    const av = await api.get('/user/reservations/check-availability', {
        params: {
            sucursal_nombre: sucursal,
            fecha_inicio: inicio,
            fecha_fin: fin,
            exclude_id: editingReservaId || undefined
        }
    });
    if (av.ok && av.data) {
        if (!av.data.disponible) {
            console.groupEnd();
            return showToast(av.data.mensaje || 'No hay disponibilidad para el horario solicitado.', 'info');
        }
        if (av.data.restan !== undefined && av.data.restan <= 3) {
            showToast(av.data.mensaje, 'info');
        }
    }

    // DESCUENTO DE RESERVA DISPONIBLE: se refleja en el total (tachado + descuento + total final)
    const totalOriginal = currentReservationTotals.original || 0;

    let discountValue = 0;
    let discountSucursal = '';
    try {
        const resAvail = await api.get(`/user/redemptions/available?sucursal=${encodeURIComponent(sucursal)}`);
        if (resAvail.ok && resAvail.data && resAvail.data.length > 0) {
            const desc = resAvail.data[0];
            discountValue = desc.valor_descuento || 0;
            discountSucursal = desc.sucursal || '';
        }
    } catch (e) { /* noop */ }

    const discountAmount = discountValue > 0 ? Math.round(totalOriginal * discountValue) / 100 : 0;
    const totalFinal = totalOriginal - discountAmount;
    const hasDiscount = discountAmount > 0;

    const totalBlock = hasDiscount ? `
            <div style="padding-top: 25px; border-top: 2px solid rgba(197,160,89,0.2);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 900; letter-spacing: 1.5px; color: #fff; font-size: 0.9rem; text-transform: uppercase;">TOTAL</span>
                    <b style="color: #777; font-size: 1.15rem; text-decoration: line-through; font-family: 'Montserrat'; white-space: nowrap;">$ ${formatNum(totalOriginal)}</b>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 8px;">
                    <span style="color: #c084fc; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.5px;"><i class="fas fa-percent"></i> DESCUENTO ${discountValue}%${discountSucursal ? ` · ${discountSucursal}` : ''}</span>
                    <b style="color: #c084fc; font-size: 1rem; font-family: 'Montserrat'; white-space: nowrap;">- $ ${formatNum(discountAmount)}</b>
                </div>
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px dashed rgba(197,160,89,0.35); display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 900; letter-spacing: 1.5px; color: #fff; font-size: 0.9rem; text-transform: uppercase;">TOTAL A PAGAR</span>
                    <b style="color: var(--dorado); font-size: 1.8rem; text-shadow: 0 0 15px rgba(197,160,89,0.3); font-family: 'Montserrat'; white-space: nowrap;">$ ${formatNum(totalFinal)}</b>
                </div>
                <p style="margin: 10px 0 0 auto; text-align: right; color: #888; font-size: 0.7rem; max-width: 330px;"><i class="fas fa-bolt" style="color: var(--dorado); margin-right: 4px;"></i>El descuento se aplica automáticamente al abonar la reserva.</p>
            </div>` : `
            <div style="padding-top: 25px; border-top: 2px solid rgba(197,160,89,0.2); display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 900; letter-spacing: 1.5px; color: #fff; font-size: 0.9rem; text-transform: uppercase;">TOTAL</span>
                <b style="color: var(--dorado); font-size: 1.8rem; text-shadow: 0 0 15px rgba(197,160,89,0.3); font-family: 'Montserrat'; white-space: nowrap;">$ ${formatNum(totalOriginal)}</b>
            </div>`;

    const resumenHtml = `
        <div style="text-align: left; padding: 5px; font-family: 'Montserrat', sans-serif;">
            <div style="display: flex; flex-direction: column; gap: 20px; margin-bottom: 35px;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <i class="fas fa-car" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Vehículo</span>
                    </div>
                    <b style="color: #fff; font-size: 1.1rem; letter-spacing: 1px; font-family: 'Montserrat';">${formatPlate(patente)}</b>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <i class="fas fa-location-dot" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Sucursal</span>
                    </div>
                    <b style="color: #fff; font-size: 0.95rem;">${sucursal}</b>
                </div>
                <div style="height: 1px; background: rgba(255,255,255,0.08); margin: 5px 0;"></div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <i class="fas fa-calendar-day" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Estadía</span>
                    </div>
                    <b style="color: #fff; text-transform: capitalize; font-size: 1rem;">${tipo}</b>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <i class="fas fa-clock" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Desde</span>
                    </div>
                    <b style="color: #eee; font-size: 0.95rem;">${formatDate(inicio)}</b>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <i class="fas fa-hourglass-end" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Hasta</span>
                    </div>
                    <b style="color: #eee; font-size: 0.95rem;">${formatDate(fin)}</b>
                </div>
            </div>
            ${totalBlock}
        </div>`;

    if (!await showConfirm('REVISÁ TU RESERVA', resumenHtml)) { console.groupEnd(); return; }

    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> PROCESANDO...';
    btn.disabled = true;

    const payload = { patente, fecha_inicio: inicio, fecha_fin: fin, sucursal_nombre: sucursal, tipo_estadia: tipo };
    const result = editingReservaId ? 
        await api.patch(`/user/reservations/${editingReservaId}`, payload) : 
        await api.post('/user/reservations', payload);

    if (result.ok) {
        showToast(editingReservaId ? '¡Reserva actualizada!' : '¡Reserva creada con éxito!', 'success');
        resetReservaForm();
        toggleReservaForm();
        try {
            if (window.showSection) {
                window.showSection('reservas', document.querySelector('.nav-item[onclick*="reservas"]'));
                try { await loadReservations(); } catch (e) { console.warn('[RESERVAS] loadReservations error after create:', e); }
            } else {
                try { await loadReservations(); } catch (e) { console.warn('[RESERVAS] loadReservations error after create (no showSection):', e); }
            }
        } catch (e) { console.warn('[RESERVAS] error esperando render de reservas:', e); }
        if (window.loadProfile) window.loadProfile();

        try {
            document.dispatchEvent(new CustomEvent('reservation:created', { detail: result.data || {} }));
        } catch (e) { console.warn('[RESERVAS] no se pudo dispatch reservation:created', e); }

        try {
            if (window.startReservationTourAtReservations && typeof window.startReservationTourAtReservations === 'function') {
                setTimeout(() => { try { window.startReservationTourAtReservations(); } catch (e) { console.warn('[RESERVAS] startReservationTourAtReservations error', e); } }, 350);
            }
        } catch (e) { /* noop */ }
    } else { 
        showToast(result.error || 'Error al procesar reserva', 'error'); 
    }

    try { document.dispatchEvent(new CustomEvent('reservation:created:debug', { detail: result || {} })); } catch (e) { /* noop */ }
    
    btn.innerHTML = originalContent;
    btn.disabled = false;
    console.groupEnd();
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
        showToast('¡Datos cargados! Seleccioná la nueva fecha.', 'info');
    }, 500);
}
