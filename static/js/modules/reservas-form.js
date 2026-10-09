/**
 * MÓDULO RESERVAS - FORMULARIO Y TARIFAS (FACHADA)
 * Orquesta el ciclo de vida del formulario (init, toggle, refresh, reset,
 * edición, creación y repetición) delegando tarifas y grilla horaria a los
 * submódulos temáticos. Re-exporta toda la API histórica para mantener
 * 100% de compatibilidad con modules/reservas.js.
 */

import api from './api.js';
import { formatDate, formatPlate, showToast, showConfirm, formatNum, scrollToElement } from './utils.js';
import { getVirtualNow } from './virtual-time.js';
import { loadReservations } from './reservas-list.js';
import {
    getEditingReservaId,
    setEditingReservaId,
    getUserVehicles,
    setUserVehicles,
    getBranchesData,
    setBranchesData,
    setReservationDiscount,
    getReservationTotals,
    getFpInstances,
    bumpDiscountToken,
    RESERVA_MIN_MS,
    RESERVA_MIN_MIN
} from './reservas-form-state.js';
import { fetchRates, updateReservationPrice } from './reservas-form-price.js';
import {
    updateDisabledDatesInPicker,
    updateHourlySlotsUI,
    selectHourRange,
    initHourlySlotDrag,
    updatePeriodAvailabilityBadge,
    resetSlotRange,
    setSlotRange
} from './reservas-form-slot.js';

// P2.5 UX/UI: el stepper no debe "ganar" pasos solo. La fecha viene precargada
// (flatpickr defaultDate = hoy) y el total se calcula apenas hay datos; estos
// flags marcan la interacción real del usuario: tocar una fecha y confirmar.
let fechaReservaTocada = false;
let reservaConfirmada = false;

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
            fechaReservaTocada = true;
            updateReservationPrice();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
            updateReservationStepper();
        }
    };

    getFpInstances().hourlyDate = flatpickr(".res-date-only", { ...commonConfig });
    getFpInstances().day = flatpickr(".res-day-only", { ...commonConfig });
    getFpInstances().week = flatpickr(".res-week-start", { 
        ...commonConfig, 
        onChange: (sd, ds) => {
            fechaReservaTocada = true;
            updatePeriodEnd(ds, 7, '.res-week-end');
            updatePeriodAvailabilityBadge();
        } 
    });
    getFpInstances().fortnight = flatpickr(".res-fortnight-start", { 
        ...commonConfig, 
        onChange: (sd, ds) => {
            fechaReservaTocada = true;
            updatePeriodEnd(ds, 15, '.res-fortnight-end');
            updatePeriodAvailabilityBadge();
        } 
    });
    getFpInstances().month = flatpickr(".res-month-start", { 
        ...commonConfig, 
        onChange: (sd, ds) => {
            fechaReservaTocada = true;
            updatePeriodEnd(ds, 30, '.res-month-end');
            updatePeriodAvailabilityBadge();
        } 
    });
    getFpInstances().start = flatpickr(".res-start", { ...commonConfig, enableTime: true, altFormat: "d-m-y H:i", dateFormat: "Y-m-d H:i" });
    getFpInstances().end = flatpickr(".res-end", { ...commonConfig, enableTime: true, altFormat: "d-m-y H:i", dateFormat: "Y-m-d H:i" });

    // CALCULAR FECHAS DE FIN PARA PERÍODOS CON LA FECHA POR DEFECTO
    const todayYmd = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
    updatePeriodEnd(todayYmd, 7, '.res-week-end');
    updatePeriodEnd(todayYmd, 15, '.res-fortnight-end');
    updatePeriodEnd(todayYmd, 30, '.res-month-end');

    const typeSelect = document.querySelector('.res-type');
    if (typeSelect) {
        typeSelect.addEventListener('change', (e) => {
            resetSlotRange();
            updateFormGroups(e.target.value);
            updateDisabledDatesInPicker();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
            updateReservationStepper();
        });
    }

    const vehicleSelect = document.querySelector('.res-vehicle');
    if (vehicleSelect) {
        vehicleSelect.addEventListener('change', () => {
            resetSlotRange();
            updateReservationPrice();
            updateDisabledDatesInPicker();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
            updateReservationStepper();
        });
    }

    const sucursalSelect = document.querySelector('.res-sucursal');
    if (sucursalSelect) {
        sucursalSelect.addEventListener('change', (e) => {
            resetSlotRange();
            const sucursalId = e.target.value;
            fetchRates(sucursalId);
            updateDisabledDatesInPicker();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
            updateReservationStepper();
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

    // P2.5 UX/UI: stepper global disponible para el sincronizador de precio
    window.updateReservationStepper = updateReservationStepper;
    updateReservationStepper();
}

// P2.5 UX/UI: refleja el progreso de la reserva en el stepper.
// Calcula el estado según los datos ya completados en el formulario.
export function updateReservationStepper() {
    const stepper = document.getElementById('reservation-stepper');
    if (!stepper) return;
    const steps = Array.from(stepper.querySelectorAll('.stepper-step'));
    const lines = Array.from(stepper.querySelectorAll('.stepper-line'));

    const vehicle = document.querySelector('.res-vehicle')?.value;
    const sucursal = document.querySelector('.res-sucursal')?.value;
    const type = document.querySelector('.res-type')?.value;
    // La fecha llega precargada (flatpickr defaultDate = hoy) y el precio se
    // calcula apenas hay datos. Para no ganar pasos solo, "Horario" cuenta
    // únicamente cuando el usuario termina de elegirlo: en "hora" al
    // comprometer el rango (inicio Y fin; .res-time-only solo se llena ahí);
    // en las demás modalidades con tocar/confirmar la fecha.
    // "Confirmación" solo cuando la reserva se creó/editó de verdad.
    const horarioElegido = type === 'hora'
        ? Boolean(document.querySelector('.res-time-only')?.value)
        : fechaReservaTocada;

    let active = 1;
    if (vehicle) active = 2;
    if (vehicle && sucursal) active = 3;
    if (vehicle && sucursal && horarioElegido) active = 4;
    const complete = reservaConfirmada;

    steps.forEach((s, i) => {
        const idx = i + 1;
        s.classList.remove('is-active', 'is-done');
        if (complete || idx < active) s.classList.add('is-done');
        else if (idx === active) s.classList.add('is-active');
    });
    lines.forEach((l, i) => l.classList.toggle('is-done', complete || i + 1 < active));
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
    setReservationDiscount({ pct: 0, sucursal: '', fetchedFor: '' });
    bumpDiscountToken();

    fetchRates();
    
    // 1. CARGAR VEHÍCULOS
    const resVehicles = await api.get('/user/vehicles');
    if (resVehicles.ok) {
        setUserVehicles(resVehicles.data);
        const noVehiclesSec = document.getElementById('reserva-no-vehicles');
        const mainForm = document.getElementById('reserva-form-content');

        if (getUserVehicles().length === 0) {
            if (noVehiclesSec) noVehiclesSec.style.display = 'block';
            if (mainForm) mainForm.style.display = 'none';
        } else {
            if (noVehiclesSec) noVehiclesSec.style.display = 'none';
            if (mainForm) mainForm.style.display = 'block';
            const selects = document.querySelectorAll('.res-vehicle');
            selects.forEach(select => {
                const currentVal = select.value;
                select.innerHTML = '<option value="" selected disabled hidden>Seleccioná vehículo...</option>' + 
                    getUserVehicles().map(v => `<option value="${v.patente}">${formatPlate(v.patente)} - ${v.marca_modelo}</option>`).join('');
                if (currentVal) select.value = currentVal;
                if (getUserVehicles().length === 1) {
                    select.value = getUserVehicles()[0].patente;
                }
            });
            if (getUserVehicles().length === 1) {
                selects.forEach(select => select.value = getUserVehicles()[0].patente);
                updateReservationPrice();
            } else {
                const fav = getUserVehicles().find(v => v.is_favorite);
                if (fav) {
                    selects.forEach(select => select.value = fav.patente);
                    updateReservationPrice();
                }
            }

            try {
                if (getUserVehicles().length === 1) {
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
    // Endpoint público (RBAC): /admin/branches exige rol operativo y el portal
    // lo usa un CLIENT (rol=user), que obtiene 403 y deja el select colgado.
    const resBranches = await api.get('/parking/branches');
    if (resBranches.ok) {
        setBranchesData(resBranches.data);
        const sucursalSelects = document.querySelectorAll('.res-sucursal');
        sucursalSelects.forEach(select => {
            const currentVal = select.value;
            select.innerHTML = '<option value="" selected disabled hidden>Seleccioná sucursal...</option>' + 
                getBranchesData().map(b => `<option value="${b.nombre}">${b.nombre}</option>`).join('');
            if (currentVal) select.value = currentVal;
        });
    } else {
        // No dejar el select colgado en "Cargando sucursales..." ante un fallo.
        console.error('[!] Error al cargar sucursales:', resBranches.status, resBranches.error);
        document.querySelectorAll('.res-sucursal').forEach(select => {
            select.innerHTML = '<option value="" selected disabled hidden>Sucursales no disponibles</option>';
        });
        if (typeof showToast === 'function') showToast('No se pudieron cargar las sucursales. Reintentá en unos segundos.', 'error');
    }

    // YA CON LAS SUCURSALES CARGADAS: consulta tarifas + descuento para la sucursal seleccionada
    await fetchRates();
    updateReservationStepper();
}

export function resetReservaForm() {
    // P2.5 UX/UI: al resetear el formulario el stepper vuelve al paso 1.
    fechaReservaTocada = false;
    reservaConfirmada = false;
    setEditingReservaId(null);
    resetSlotRange();
    const form = document.querySelector('.reservation-form-modern');
    if (form) {
        form.reset();
        updateFormGroups("");
    }
    updateReservationStepper();
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

    setEditingReservaId(id);

    // P2.5 UX/UI: al editar una reserva existente todo se considera completado.
    fechaReservaTocada = true;
    reservaConfirmada = true;
    
    if (window.showSection) {
        const inicioNavItem = document.querySelector('.nav-item[onclick*="inicio"]');
        window.showSection('inicio', inicioNavItem);
    }

    const container = document.getElementById('reserva-form-container');
    if (!container.classList.contains('open')) await toggleReservaForm();
scrollToElement(container);

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
            setSlotRange({ start: dtParts[1], end: endParts[1] || null, date: dtParts[0] });
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

/**
 * Marca un campo obligatorio como faltante y avisa.
 *
 * El `required` del HTML alcanza para bloquear el submit, pero el aviso que
 * ve el usuario es el tooltip nativo del navegador: generico, en el idioma
 * del SO y sin decir que paso con AUTOPASS. Con `novalidate` en el form,
 * esta funcion pasa a ser la unica barrera y el aviso real.
 *
 * SeFocus no se usa a proposito: enfocar el select abre su popup en algunos
 * navegadores y el toast queda tapado. El borde rojo y el toast juntos ya
 * dicen que falta, sin stealar el foco.
 */
function marcarFaltaReserva(el, mensaje, tipoToast = 'info') {
    el.classList.add('is-invalid');
    el.setAttribute('aria-invalid', 'true');
    // Se saca solo en el proximo cambio, para no dejar el rojo pegado si el
    // usuario se arrepiente. Se escucha en vivo porque el select se llena
    // desde el fetch de flota/sucursales.
    const limpiar = () => {
        el.classList.remove('is-invalid');
        el.removeAttribute('aria-invalid');
        el.removeEventListener('change', limpiar);
    };
    el.addEventListener('change', limpiar);
    return showToast(mensaje, tipoToast);
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

    if (!getUserVehicles() || getUserVehicles().length === 0) {
        if (typeof window.showQuickAddVehicle === 'function') window.showQuickAddVehicle();
        console.groupEnd();
        return showToast('Agregá tu primer vehículo para poder reservar', 'info');
    }

    const patente = patenteEl.value;
    const sucursal = sucursalEl.value;
    const tipo = tipoEl.value;
    const originalContent = btn.innerHTML;
    
    if (!patente) { console.groupEnd(); return marcarFaltaReserva(patenteEl, 'Seleccioná un vehículo', 'info'); }
    if (!sucursal) { console.groupEnd(); return marcarFaltaReserva(sucursalEl, 'Seleccioná una sucursal', 'info'); }
    if (!tipo) { console.groupEnd(); return marcarFaltaReserva(tipoEl, 'Seleccioná tipo de estadía', 'info'); }

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
            
            const branch = getBranchesData().find(b => b.nombre === sucursal);
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
            exclude_id: getEditingReservaId() || undefined
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
    const totalOriginal = getReservationTotals().original || 0;

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
            <div style="padding-top: 25px; border-top: 2px solid rgba(223, 186, 107,0.2);">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 900; letter-spacing: 1.5px; color: #fff; font-size: 0.9rem; text-transform: uppercase;">TOTAL</span>
                    <b style="color: #777; font-size: 1.15rem; text-decoration: line-through; white-space: nowrap;">$ ${formatNum(totalOriginal)}</b>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding-top: 8px;">
                    <span style="color: #c084fc; font-size: 0.82rem; font-weight: 700; letter-spacing: 0.5px;"><i class="fas fa-percent"></i> DESCUENTO ${discountValue}%${discountSucursal ? ` · ${discountSucursal}` : ''}</span>
                    <b style="color: #c084fc; font-size: 1rem; white-space: nowrap;">- $ ${formatNum(discountAmount)}</b>
                </div>
                <div style="margin-top: 12px; padding-top: 12px; border-top: 1px dashed rgba(223, 186, 107,0.35); display: flex; justify-content: space-between; align-items: center;">
                    <span style="font-weight: 900; letter-spacing: 1.5px; color: #fff; font-size: 0.9rem; text-transform: uppercase;">TOTAL A PAGAR</span>
                    <b style="color: var(--dorado); font-size: 1.8rem; text-shadow: 0 0 15px rgba(223, 186, 107,0.3); white-space: nowrap;">$ ${formatNum(totalFinal)}</b>
                </div>
                <p style="margin: 10px 0 0 auto; text-align: right; color: #888; font-size: 0.7rem; max-width: 330px;"><i class="fas fa-bolt" style="color: var(--dorado); margin-right: 4px;"></i>El descuento se aplica automáticamente al abonar la reserva.</p>
            </div>` : `
            <div style="padding-top: 25px; border-top: 2px solid rgba(223, 186, 107,0.2); display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 900; letter-spacing: 1.5px; color: #fff; font-size: 0.9rem; text-transform: uppercase;">TOTAL</span>
                <b style="color: var(--dorado); font-size: 1.8rem; text-shadow: 0 0 15px rgba(223, 186, 107,0.3); white-space: nowrap;">$ ${formatNum(totalOriginal)}</b>
            </div>`;

    const resumenHtml = `
        <div style="text-align: left; padding: 5px; ">
            <div style="display: flex; flex-direction: column; gap: 20px; margin-bottom: 35px;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <i class="fas fa-car" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Vehículo</span>
                    </div>
                    <b style="color: #fff; font-size: 1.1rem; letter-spacing: 1px; ">${formatPlate(patente)}</b>
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
    const result = getEditingReservaId() ? 
        await api.patch(`/user/reservations/${getEditingReservaId()}`, payload) : 
        await api.post('/user/reservations', payload);

    if (result.ok) {
        showToast(getEditingReservaId() ? '¡Reserva actualizada!' : '¡Reserva creada con éxito!', 'success');
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
    if (container) scrollToElement(container);
    
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

export {
    updateDisabledDatesInPicker,
    updateHourlySlotsUI,
    selectHourRange,
    initHourlySlotDrag,
    updatePeriodAvailabilityBadge
} from './reservas-form-slot.js';

export {
    fetchRates,
    updateReservationPrice
} from './reservas-form-price.js';

export {
    getEditingReservaId,
    setEditingReservaId,
    getUserVehicles
} from './reservas-form-state.js';
