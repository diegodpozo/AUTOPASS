/**
 * MÓDULO RESERVAS - FORMULARIO Y TARIFAS (FACHADA)
 * Orquesta el ciclo de vida del formulario (init, toggle, refresh, reset,
 * edición, creación y repetición) delegando tarifas y grilla horaria a los
 * submódulos temáticos. Re-exporta toda la API histórica para mantener
 * 100% de compatibilidad con modules/reservas.js.
 */

import api from './api.js';
import { formatDate, formatPlate, showToast, showConfirm, formatNum, scrollToElement, capitalizarFrase } from './utils.js';
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
    getReservationQuote,
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
let currentBookingStep = 1;

export function getBookingStep() {
    return currentBookingStep;
}

export function updateStepSummaries() {
    const vehicleSelect = document.querySelector('.res-vehicle');
    const sucursalSelect = document.querySelector('.res-sucursal');
    const typeSelect = document.querySelector('.res-type');
    const pane3 = document.getElementById('res-step-pane-3');

    const chipVehVal = document.getElementById('summary-val-vehicle');
    if (chipVehVal && vehicleSelect) {
        const opt = vehicleSelect.selectedOptions ? vehicleSelect.selectedOptions[0] : null;
        chipVehVal.textContent = (opt && opt.value) ? opt.textContent.trim() : '--';
    }

    const chipSucVal = document.getElementById('summary-val-sucursal');
    const chipSucIcon = document.getElementById('summary-chip-step3-icon');
    const chipSucWrapper = document.getElementById('summary-chip-sucursal');
    const btnBack2 = document.getElementById('btn-back-to-step-2');

    if (pane3 && pane3.classList.contains('is-type-selected')) {
        if (chipSucVal && typeSelect) {
            const opt = typeSelect.selectedOptions ? typeSelect.selectedOptions[0] : null;
            chipSucVal.textContent = (opt && opt.value) ? opt.textContent.trim() : 'Hora';
        }
        if (chipSucIcon) {
            chipSucIcon.className = 'fas fa-clock';
        }
        if (chipSucWrapper) {
            chipSucWrapper.title = 'Estadía seleccionada (clic para cambiar)';
        }
        if (btnBack2) {
            btnBack2.title = 'Cambiar tipo de estadía';
        }
    } else {
        if (chipSucVal && sucursalSelect) {
            const opt = sucursalSelect.selectedOptions ? sucursalSelect.selectedOptions[0] : null;
            chipSucVal.textContent = (opt && opt.value) ? opt.textContent.trim() : '--';
        }
        if (chipSucIcon) {
            chipSucIcon.className = 'fas fa-location-dot';
        }
        if (chipSucWrapper) {
            chipSucWrapper.title = 'Sucursal seleccionada (clic para cambiar)';
        }
        if (btnBack2) {
            btnBack2.title = 'Volver a seleccionar sucursal';
        }
    }
}

export function updateStepButtons() {
    const vehicle = document.querySelector('.res-vehicle')?.value;
    const sucursal = document.querySelector('.res-sucursal')?.value;

    const btnNext2 = document.getElementById('btn-next-to-step-2');
    if (btnNext2) {
        btnNext2.disabled = !vehicle;
    }

    const btnNext3 = document.getElementById('btn-next-to-step-3');
    if (btnNext3) {
        btnNext3.disabled = !sucursal;
    }
}

export function goToBookingStep(step) {
    currentBookingStep = Math.max(1, Math.min(3, step));

    const pane1 = document.getElementById('res-step-pane-1');
    const pane2 = document.getElementById('res-step-pane-2');
    const pane3 = document.getElementById('res-step-pane-3');

    if (pane1) pane1.classList.toggle('is-active', currentBookingStep === 1);
    if (pane2) pane2.classList.toggle('is-active', currentBookingStep === 2);
    if (pane3) pane3.classList.toggle('is-active', currentBookingStep === 3);

    updateStepSummaries();
    updateStepButtons();
    updateReservationStepper();
    syncStepperToCardHeight();
}

// Texto de ayuda de los campos de fecha. El input que se ve en pantalla NO es
// el del HTML sino el "altInput" que crea Flatpickr: ese hereda las clases,
// pero NO el placeholder, asi que hay que escribirlo a mano (si no, el campo
// arranca vacio y sin ninguna pista de que hay que elegir una fecha).
const PLACEHOLDER_ELEGIR_DIA = 'Elegí el día';

function setPlaceholderVisible(instance, texto) {
    const fpObj = Array.isArray(instance) ? instance[0] : instance;
    if (fpObj && fpObj.altInput) {
        fpObj.altInput.placeholder = texto;
    }
}

// Flatpickr formatea el campo "DIA" como "Jue 22 de Octubre" (cada palabra en
// mayuscula). Aca se deja "Jue 22 de octubre": primera letra en mayuscula y el
// resto en minuscula. Es solo cosmetico (el .value real sigue siendo YYYY-MM-DD).
function embellecerFechaVisible(instance) {
    const fpObj = Array.isArray(instance) ? instance[0] : instance;
    if (fpObj && fpObj.altInput) {
        fpObj.altInput.value = capitalizarFrase(fpObj.altInput.value);
    }
}

// Pone una fecha en un calendario y refresca el input visible (altInput).
// Con triggerChange=true se dispara el onChange del picker, que recalcula la
// fecha de "Finaliza", el precio, el badge de disponibilidad y el stepper.
function setPickerDate(instance, fecha) {
    const fpObj = Array.isArray(instance) ? instance[0] : instance;
    if (fpObj && typeof fpObj.setDate === 'function') {
        fpObj.setDate(fecha, true);
    }
}

let lastBaseCardHeight = 0;

/**
 * P2.5 UX/UI: el rail del stepper calca el largo/alto de la card de reserva en su
 * estado base. Al elegir "por hora" la card crece con la grilla de horarios
 * (slots) y este sync no acompaña la expansion, manteniendo el stepper al
 * alto base de la tarjeta. Al volver a otra modalidad o resetear, vuelve a
 * emparejar con el alto de la tarjeta.
 */
export function syncStepperToCardHeight() {
    const stepper = document.getElementById('reservation-stepper');
    const card = document.querySelector('.modern-reservation-card') || document.getElementById('reserva-form-container');
    if (!stepper || !card) return;
    if (!window.matchMedia('(min-width: 1281px)').matches) {
        stepper.style.removeProperty('height');
        return;
    }
    const tipoHora = document.querySelector('.res-type')?.value === 'hora';
    if (tipoHora) {
        if (lastBaseCardHeight > 0) {
            stepper.style.setProperty('height', `${lastBaseCardHeight}px`);
            return;
        }
        const slotsGrid = document.getElementById('hourly-slots-grid');
        const slotsHeight = slotsGrid && slotsGrid.offsetHeight > 0 ? slotsGrid.offsetHeight : 0;
        const alto = Math.max(card.getBoundingClientRect().height - slotsHeight, 380);
        lastBaseCardHeight = alto;
        stepper.style.setProperty('height', `${alto}px`);
        return;
    }
    const alto = card.getBoundingClientRect().height;
    if (alto > 0) {
        lastBaseCardHeight = alto;
        stepper.style.setProperty('height', `${alto}px`);
    }
}

function initStepperHeightSync() {
    const card = document.getElementById('reserva-form-container');
    if (!card || !('ResizeObserver' in window)) return;
    new ResizeObserver(syncStepperToCardHeight).observe(card);
    window.addEventListener('resize', syncStepperToCardHeight);
    syncStepperToCardHeight();
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
            fechaReservaTocada = true;
            updateReservationPrice();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
            updateReservationStepper();
        }
    };

    getFpInstances().hourlyDate = flatpickr(".res-date-only", {
        ...commonConfig,
        // El campo arranca VACIO (placeholder "Elegí el día") en vez de
        // precargar hoy: asi el usuario elige el dia a proposito.
        defaultDate: null,
        // El campo "DIA" muestra la fecha en palabras ("Jue 22 de octubre").
        // Se logra con el propio Flatpickr: D=jue, j=22, F=octubre (segun l10n es).
        // Las letras sueltas de "de" van escapadas con \\.
        altFormat: "D j \\d\\e F",
        // OJO: este onChange REEMPLAZA al de commonConfig, no se suma. Por eso
        // repite aqui lo que aquel hacia (precio, grilla de horarios, badge y
        // stepper) y ademas normaliza el texto visible de la fecha.
        onChange: () => {
            fechaReservaTocada = true;
            updateReservationPrice();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
            updateReservationStepper();
            embellecerFechaVisible(getFpInstances().hourlyDate);
        },
        onReady: (ds, a, inst) => {
            setPlaceholderVisible(inst, PLACEHOLDER_ELEGIR_DIA);
            embellecerFechaVisible(inst);
        },
        onValueUpdate: (ds, a, inst) => embellecerFechaVisible(inst),
    });

    // Selectores de PERIODO (dia, semana, quincena, mes).
    // Arrancan VACIOS (antes se precargaba hoy): la fecha la elige el usuario a
    // proposito, y el input visible muestra el icono de calendario con el texto
    // "Elegí el día". `dias` es la duracion del periodo (null en "dia", que es
    // un solo dia) y `finSelector` el campo "Finaliza" que se calcula solo.
    const configPeriodo = (dias, finSelector) => ({
        ...commonConfig,
        defaultDate: null,
        // OJO: este onChange REEMPLAZA al de commonConfig, no se suma. Por eso
        // repite aqui lo que aquel hacia (precio, badge y stepper).
        onChange: (sd, ds) => {
            fechaReservaTocada = true;
            if (dias) updatePeriodEnd(ds, dias, finSelector);
            updateReservationPrice();
            updatePeriodAvailabilityBadge();
            updateReservationStepper();
        },
        onReady: (sd, a, inst) => setPlaceholderVisible(inst, PLACEHOLDER_ELEGIR_DIA),
    });

    getFpInstances().day = flatpickr(".res-day-only", configPeriodo());
    getFpInstances().week = flatpickr(".res-week-start", configPeriodo(7, '.res-week-end'));
    getFpInstances().fortnight = flatpickr(".res-fortnight-start", configPeriodo(15, '.res-fortnight-end'));
    getFpInstances().month = flatpickr(".res-month-start", configPeriodo(30, '.res-month-end'));
    getFpInstances().start = flatpickr(".res-start", { ...commonConfig, enableTime: true, altFormat: "d-m-y H:i", dateFormat: "Y-m-d H:i" });
    getFpInstances().end = flatpickr(".res-end", { ...commonConfig, enableTime: true, altFormat: "d-m-y H:i", dateFormat: "Y-m-d H:i" });

    // Las fechas de "Finaliza" de los periodos ya NO se precargan: los campos de
    // inicio arrancan vacios y el final se calcula cuando el usuario elige el
    // inicio (en el onChange de cada picker).

    const typeSelect = document.querySelector('.res-type');
    if (typeSelect) {
        typeSelect.addEventListener('change', (e) => {
            resetSlotRange();
            const val = e.target.value;
            const pane3 = document.getElementById('res-step-pane-3');
            if (val) {
                if (pane3) pane3.classList.add('is-type-selected');
            } else {
                if (pane3) pane3.classList.remove('is-type-selected');
            }
            updateFormGroups(val);
            updateDisabledDatesInPicker();
            updateHourlySlotsUI();
            updatePeriodAvailabilityBadge();
            updateStepSummaries();
            updateReservationStepper();
            syncStepperToCardHeight();
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
            updateStepSummaries();
            updateStepButtons();
            updateReservationStepper();
            if (vehicleSelect.value) {
                setTimeout(() => goToBookingStep(2), 120);
            }
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
            updateStepSummaries();
            updateStepButtons();
            updateReservationStepper();
            if (sucursalSelect.value) {
                setTimeout(() => goToBookingStep(3), 120);
            }
        });
    }

    // Botones de avance y retroceso entre pasos
    const btnNext2 = document.getElementById('btn-next-to-step-2');
    if (btnNext2) {
        btnNext2.addEventListener('click', () => {
            const v = document.querySelector('.res-vehicle')?.value;
            if (v) goToBookingStep(2);
        });
    }

    const btnNext3 = document.getElementById('btn-next-to-step-3');
    if (btnNext3) {
        btnNext3.addEventListener('click', () => {
            const s = document.querySelector('.res-sucursal')?.value;
            if (s) goToBookingStep(3);
        });
    }

    const btnBack1 = document.getElementById('btn-back-to-step-1');
    if (btnBack1) {
        btnBack1.addEventListener('click', () => goToBookingStep(1));
    }

    const btnBack2 = document.getElementById('btn-back-to-step-2');
    if (btnBack2) {
        btnBack2.addEventListener('click', () => {
            const pane3 = document.getElementById('res-step-pane-3');
            if (pane3 && pane3.classList.contains('is-type-selected')) {
                pane3.classList.remove('is-type-selected');
                const tSelect = document.querySelector('.res-type');
                if (tSelect) tSelect.value = '';
                updateFormGroups('');
                resetSlotRange();
                updateStepSummaries();
                updateReservationStepper();
                syncStepperToCardHeight();
            } else {
                goToBookingStep(2);
            }
        });
    }

    const chipVeh = document.getElementById('summary-chip-vehicle');
    if (chipVeh) {
        chipVeh.addEventListener('click', () => goToBookingStep(1));
        chipVeh.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                goToBookingStep(1);
            }
        });
    }

    const chipSuc = document.getElementById('summary-chip-sucursal');
    if (chipSuc) {
        const handleChipStep3Click = () => {
            const pane3 = document.getElementById('res-step-pane-3');
            if (pane3 && pane3.classList.contains('is-type-selected')) {
                pane3.classList.remove('is-type-selected');
                const tSelect = document.querySelector('.res-type');
                if (tSelect) tSelect.value = '';
                updateFormGroups('');
                resetSlotRange();
                updateStepSummaries();
                updateReservationStepper();
                syncStepperToCardHeight();
            } else {
                goToBookingStep(2);
            }
        };
        chipSuc.addEventListener('click', handleChipStep3Click);
        chipSuc.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleChipStep3Click();
            }
        });
    }

    // Clic en pasos del stepper para volver a pasos completados o disponibles
    const stepperEl = document.getElementById('reservation-stepper');
    if (stepperEl) {
        const stepItems = stepperEl.querySelectorAll('.stepper-step');
        stepItems.forEach(s => {
            s.addEventListener('click', () => {
                const targetStep = parseInt(s.dataset.step, 10);
                const vehicle = document.querySelector('.res-vehicle')?.value;
                const sucursal = document.querySelector('.res-sucursal')?.value;
                if (targetStep === 1) {
                    goToBookingStep(1);
                } else if (targetStep === 2 && vehicle) {
                    goToBookingStep(2);
                } else if (targetStep === 3 && sucursal) {
                    goToBookingStep(3);
                }
            });
            s.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    s.click();
                }
            });
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
    window.goToBookingStep = goToBookingStep;
    goToBookingStep(1);
    initStepperHeightSync();
}

// P2.5 UX/UI: refleja el progreso de la reserva en el stepper.
// Calcula el estado según los datos ya completados en el formulario y el paso actual.
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

    let active = currentBookingStep;
    if (currentBookingStep === 3 && horarioElegido) {
        active = 4;
    }
    const complete = reservaConfirmada;

    steps.forEach((s, i) => {
        const idx = i + 1;
        s.classList.remove('is-active', 'is-done');
        if (complete || idx < active) s.classList.add('is-done');
        else if (idx === active) s.classList.add('is-active');

        // Permite saltar con clic a los pasos completados o disponibles
        const isClickable = (idx === 1) ||
                            (idx === 2 && Boolean(vehicle)) ||
                            (idx === 3 && Boolean(vehicle && sucursal));
        s.classList.toggle('is-clickable', isClickable);
        s.setAttribute('role', 'button');
        s.setAttribute('tabindex', isClickable ? '0' : '-1');
    });
    lines.forEach((l, i) => l.classList.toggle('is-done', complete || i + 1 < active));
    syncStepperToCardHeight();
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

    // A partir de aca la tarjeta se abre/cierra en caliente (con trigger), asi que
    // ya no es el arranque estatico: se quita la marca que anulaba la animacion.
    container.classList.remove('is-static-open');

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
            updateStepSummaries();
            updateStepButtons();

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
            select.innerHTML = '<option value="" selected disabled hidden>Elegí</option>' + 
                getBranchesData().map(b => `<option value="${b.nombre}">${b.nombre}</option>`).join('');
            if (currentVal) select.value = currentVal;
        });
        updateStepSummaries();
        updateStepButtons();
    } else {
        // No dejar el select colgado en "Cargando sucursales..." ante un fallo.
        console.error('[!] Error al cargar sucursales:', resBranches.status, resBranches.error);
        document.querySelectorAll('.res-sucursal').forEach(select => {
            select.innerHTML = '<option value="" selected disabled hidden>Sucursales no disponibles</option>';
        });
        if (typeof showToast === 'function') showToast('No se pudieron cargar las sucursales. Reintentá en unos segundos.', 'error');
    }

    // YA CON LAS SUCURSALES CARGADAS: consulta tarifas + descuento para la sucursal seleccionada.
    // En finally (haya exito o error de red) se actualiza el stepper: asi nunca
    // queda sin los datos de la carga si la ultima consulta falla.
    try {
        const sucursal = document.querySelector('.res-sucursal')?.value || null;
        await fetchRates(sucursal);
    } finally {
        updateStepSummaries();
        updateStepButtons();
        updateReservationStepper();
    }
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
    // form.reset() no limpia el estado interno de Flatpickr: los campos de
    // fecha conservarian la fecha anterior en el input visible (y no volveria
    // el placeholder). clear() los deja vacios.
    ['hourlyDate', 'day', 'week', 'fortnight', 'month'].forEach(clave => {
        const fp = getFpInstances()[clave];
        const fpObj = Array.isArray(fp) ? fp[0] : fp;
        if (fpObj && typeof fpObj.clear === 'function') fpObj.clear();
    });
    const pane3 = document.getElementById('res-step-pane-3');
    if (pane3) pane3.classList.remove('is-type-selected');
    goToBookingStep(1);
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
            // setDate (no .value) para que Flatpickr refresque tambien el input
            // visible, que muestra la fecha en palabras ("jue 22 de octubre").
            const hourlyFp = getFpInstances().hourlyDate;
            const hourlyFpObj = Array.isArray(hourlyFp) ? hourlyFp[0] : hourlyFp;
            if (hourlyFpObj && typeof hourlyFpObj.setDate === 'function') {
                hourlyFpObj.setDate(dtParts[0], false);
                // setDate(..., false) NO dispara los hooks de Flatpickr, asi que
                // el texto visible se normaliza a mano aca.
                embellecerFechaVisible(hourlyFpObj);
            } else {
                document.querySelector('.res-date-only').value = dtParts[0];
            }
            document.querySelector('.res-time-only').value = dtParts[1];
            setSlotRange({ start: dtParts[1], end: endParts[1] || null, date: dtParts[0] });
            const startDt = new Date(r.fecha_inicio.replace(/-/g, "/"));
            const endDt = new Date(r.fecha_fin.replace(/-/g, "/"));
            const minutes = Math.round((endDt - startDt) / 60000);
            const hours = minutes / 60;
            document.querySelector('.res-hours-qty').value = hours > 0 ? hours : 1;
            updateHourlySlotsUI();
        } else if (r.tipo_estadia === 'dia') {
            // setDate (no .value) para que Flatpickr refresque tambien el input
            // visible (altInput), que es el que muestra la fecha elegida.
            setPickerDate(getFpInstances().day, r.fecha_inicio.split(' ')[0]);
        } else {
            const periodPickers = { 'semana': 'week', 'quincena': 'fortnight', 'mes': 'month' };
            const pickerKey = periodPickers[r.tipo_estadia];
            if (pickerKey) {
                // El onChange del picker recalcula el "Finaliza", el precio, el
                // badge y el stepper.
                setPickerDate(getFpInstances()[pickerKey], r.fecha_inicio.split(' ')[0]);
            } else {
                document.querySelector('.res-start').value = r.fecha_inicio;
                document.querySelector('.res-end').value = r.fecha_fin;
            }
        }
        const pane3 = document.getElementById('res-step-pane-3');
        if (pane3 && r.tipo_estadia) pane3.classList.add('is-type-selected');
        goToBookingStep(3);
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
    
    if (!patente) { goToBookingStep(1); console.groupEnd(); return marcarFaltaReserva(patenteEl, 'Seleccioná un vehículo', 'info'); }
    if (!sucursal) { goToBookingStep(2); console.groupEnd(); return marcarFaltaReserva(sucursalEl, 'Seleccioná una sucursal', 'info'); }
    if (!tipo) { goToBookingStep(3); console.groupEnd(); return marcarFaltaReserva(tipoEl, 'Seleccioná tipo de estadía', 'info'); }

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

    // COTIZACIÓN: el backend recalcula horas/total con las tarifas vigentes y las compara
    // con lo que enviamos (si no coinciden responde 409). También las persiste como foto histórica.
    const quote = getReservationQuote();
    const payload = {
        patente,
        fecha_inicio: inicio,
        fecha_fin: fin,
        sucursal_nombre: sucursal,
        tipo_estadia: tipo,
        horas_calculadas: quote.horas || null,
        monto_calculado: quote.base || null,
        tarifa_hora: quote.tarifaHora || null,
        tarifa_fraccion: quote.tarifaFraccion || null,
        tarifa_aplicada: quote.tarifaAplicada || null
    };
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
        const pane3 = document.getElementById('res-step-pane-3');
        if (pane3 && tipo) pane3.classList.add('is-type-selected');
        goToBookingStep(3);
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
