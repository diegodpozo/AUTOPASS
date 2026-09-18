/**
 * MÓDULO RESERVAS - GRILLA HORARIA Y DISPONIBILIDAD
 * Cache de disponibilidad, fechas deshabilitadas, selector de franja horaria
 * (chips + drag) y badge de disponibilidad por período.
 */

import api from './api.js';
import { getVirtualNow } from './virtual-time.js';
import {
    getUserVehicles,
    getBranchesData,
    getFpInstances,
    RESERVA_MIN_MS
} from './reservas-form-state.js';
import { updateReservationPrice } from './reservas-form-price.js';

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

// RANGO DE LA GRILLA HORARIA SEGÚN EL HORARIO DE LA SUCURSAL SELECCIONADA.
// RESPETA is_24h (00:00 → 23:30) Y el horario configurado (ej. "07:00 A 23:00" → 07:00 → 22:30).
// Fallback al rango legado 07:00 → 23:30 si no hay info de horario disponible.
function _branchSlotRange() {
    const sucursalSelect = document.querySelector('.res-sucursal');
    const sucursal = sucursalSelect ? sucursalSelect.value : '';
    const branch = getBranchesData().find(b => b.nombre === sucursal);
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

export async function updateDisabledDatesInPicker() {
    const sucursalSelect = document.querySelector('.res-sucursal');
    const vehicleSelect = document.querySelector('.res-vehicle');
    const typeSelect = document.querySelector('.res-type');

    if (!sucursalSelect || !vehicleSelect || !typeSelect) return;

    const sucursal = sucursalSelect.value;
    const patente = vehicleSelect.value;
    const tipoEstadia = typeSelect.value;

    if (!sucursal || !patente || !tipoEstadia) return;

    const veh = getUserVehicles().find(v => v.patente === patente);
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
                'hora': getFpInstances().hourlyDate,
                'dia': getFpInstances().day,
                'semana': getFpInstances().week,
                'quincena': getFpInstances().fortnight,
                'mes': getFpInstances().month
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

    const veh = getUserVehicles().find(v => v.patente === patente);
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
    const veh = getUserVehicles().find(v => v.patente === patente);
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

export function resetSlotRange() {
    slotRangeStart = null;
    slotRangeEnd = null;
    slotRangeDate = null;
}

export function setSlotRange({ start, end, date }) {
    slotRangeStart = start;
    slotRangeEnd = end;
    slotRangeDate = date;
}
