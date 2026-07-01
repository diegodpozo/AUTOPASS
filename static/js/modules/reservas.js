import api from './api.js';
import { toTitle, formatDate, formatPlate, showToast, showConfirm, formatNum } from './utils.js';

/**
 * RESERVAS MODULO
 * LOGICA COMPLEJA DE GESTION DE RESERVAS, TARIFAS Y PASES DIGITALES.
 */

let historialCurrentPage = 1;
const HISTORIAL_PAGE_SIZE = 5;
const RESERVA_MIN_MS = (window.RESERVA_HORA_MIN_SEGUNDOS || 1800) * 1000;
const RESERVA_MIN_MIN = (window.RESERVA_HORA_MIN_SEGUNDOS || 1800) / 60;
let currentRates = { hora: 1500, dia: 15000, semana: 70000, quincena: 120000, mes: 200000 };
let editingReservaId = null;
let historyData = [];

export function initReservationForm() {
    if (!window.flatpickr) return;

    // CONFIGURAR IDIOMA ESPANOL GLOBALMENTE SI ESTA CARGADO
    if (window.flatpickr.l10ns?.es) {
        window.flatpickr.localize(window.flatpickr.l10ns.es);
    }

    const now = typeof window.getVirtualNow === 'function' ? window.getVirtualNow() : new Date();
    const maxDate = new Date(now.getFullYear(), now.getMonth() + 3, now.getDate());
    const commonConfig = {
        minDate: "today",
        maxDate: maxDate,
        disableMobile: "true",
        altInput: true,
        altFormat: "d-m-y",
        dateFormat: "Y-m-d",
        defaultDate: now,
        onChange: () => updateReservationPrice()
    };

    flatpickr(".res-date-only", { ...commonConfig });
    flatpickr(".res-day-only", { ...commonConfig });
    flatpickr(".res-time-only", { 
        enableTime: true, 
        noCalendar: true, 
        dateFormat: "H:i",
        defaultDate: now,
        disableMobile: "true",
        onChange: () => updateReservationPrice()
    });
    flatpickr(".res-week-start", { ...commonConfig, onChange: (sd, ds) => updatePeriodEnd(ds, 7, '.res-week-end') });
    flatpickr(".res-fortnight-start", { ...commonConfig, onChange: (sd, ds) => updatePeriodEnd(ds, 15, '.res-fortnight-end') });
    flatpickr(".res-month-start", { ...commonConfig, onChange: (sd, ds) => updatePeriodEnd(ds, 30, '.res-month-end') });
    flatpickr(".res-start", { ...commonConfig, enableTime: true, altFormat: "d-m-y H:i", dateFormat: "Y-m-d H:i" });
    flatpickr(".res-end", { ...commonConfig, enableTime: true, altFormat: "d-m-y H:i", dateFormat: "Y-m-d H:i" });

    // CALCULAR FECHAS DE FIN PARA PERIODOS CON LA FECHA POR DEFECTO
    const todayYmd = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;
    updatePeriodEnd(todayYmd, 7, '.res-week-end');
    updatePeriodEnd(todayYmd, 15, '.res-fortnight-end');
    updatePeriodEnd(todayYmd, 30, '.res-month-end');

    const typeSelect = document.querySelector('.res-type');
    if (typeSelect) {
        typeSelect.addEventListener('change', (e) => updateFormGroups(e.target.value));
    }

    const vehicleSelect = document.querySelector('.res-vehicle');
    if (vehicleSelect) {
        vehicleSelect.addEventListener('change', () => updateReservationPrice());
    }

    const sucursalSelect = document.querySelector('.res-sucursal');
    if (sucursalSelect) {
        sucursalSelect.addEventListener('change', (e) => {
            const sucursalId = e.target.value; // ENVIAR EL NOMBRE COMPLETO (EJ: "AUTOPASS CASTELAR")
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

    // FLECHAS CUSTOM PARA CANTIDAD DE HORAS
    document.querySelectorAll('.num-input-wrapper').forEach(wrapper => {
        const input = wrapper.querySelector('.res-hours-qty');
        const up = wrapper.querySelector('.num-btn.up');
        const down = wrapper.querySelector('.num-btn.down');
        if (input && up) up.addEventListener('click', () => {
            const max = parseInt(input.max) || 24;
            const val = parseInt(input.value) || 0;
            if (val < max) { input.value = val + 1; input.dispatchEvent(new Event('input', { bubbles: true })); }
        });
        if (input && down) down.addEventListener('click', () => {
            const min = parseInt(input.min) || 1;
            const val = parseInt(input.value) || 0;
            if (val > min) { input.value = val - 1; input.dispatchEvent(new Event('input', { bubbles: true })); }
        });
    });
}

function updatePeriodEnd(startDateStr, days, targetSelector) {
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
        // ABRIR: OCULTAR TRIGGER CON FADE Y MOSTRAR CONTAINER
        trigger.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
        trigger.style.opacity = '0';
        trigger.style.transform = 'translateY(-10px)';
        
        setTimeout(async () => {
            trigger.style.display = 'none';
            container.style.display = 'block';
            container.style.opacity = '0';
            container.style.transform = 'translateY(10px)';
            container.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
            
            // FORZAR REFLOW PARA LA TRANSICION
            container.offsetHeight;
            
            container.classList.add('open');
            container.style.opacity = '1';
            container.style.transform = 'translateY(0)';
            
            await refreshReservationFormState();
        }, 300);
    } else {
        // CERRAR: OCULTAR CONTAINER Y MOSTRAR TRIGGER
        container.style.opacity = '0';
        container.style.transform = 'translateY(10px)';
        
        setTimeout(() => {
            container.classList.remove('open');
            container.style.display = 'none';
            resetReservaForm();
            
            trigger.style.display = 'block';
            // FORZAR REFLOW
            trigger.offsetHeight;
            trigger.style.opacity = '1';
            trigger.style.transform = 'translateY(0)';
        }, 400);
    }
}

let userVehicles = [];
let branchesData = [];

export async function refreshReservationFormState() {
    const container = document.getElementById('reserva-form-container');
    if (!container) return;

    fetchRates();
    
    // 1. CARGAR VEHICULOS
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
                // Si solo hay un vehículo, auto-seleccionarlo para acelerar el flujo
                if (userVehicles.length === 1) {
                    select.value = userVehicles[0].patente;
                }
            });
            // AUTO-SELECT SI TIENE UN SOLO VEHICULO O UNO MARCADO COMO FAVORITO
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

            // SI SOLO HAY UN VEHICULO, AUTO-ABRIR FORMULARIO
            try {
                if (userVehicles.length === 1) {
                    const container = document.getElementById('reserva-form-container');
                    if (container && !container.classList.contains('open') && typeof toggleReservaForm === 'function') {
                        toggleReservaForm();
                        setTimeout(() => {
                            const dateInput = document.querySelector('.res-date-only') || document.querySelector('.res-start');
                            if (dateInput) dateInput.focus();
                            if (typeof showToast === 'function') showToast('Seleccionamos tu vehículo para acelerar la reserva');
                        }, 400);
                    }
                }
            } catch (e) { console.error('[AUTOSELECT] ', e); }
        }
    }

    // 2. CARGAR SUCURSALES DINAMICAMENTE
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
}

export function resetReservaForm() {
    editingReservaId = null;
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

    const now = new Date();
    const start = new Date(r.fecha_inicio.replace(/-/g, "/"));
    if (r.tipo_estadia === 'hora' && (start - now) < RESERVA_MIN_MS) {
        return showToast(`No se puede modificar con menos de ${RESERVA_MIN_MIN} minutos de antelación`);
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
    const vehicleSelect = document.querySelector('.res-vehicle');
    if (!typeSelect) return;
    
    const type = typeSelect.value;
    const patente = vehicleSelect?.value;
    const totalEl = document.getElementById('reserva-total-est');
    let total = 0;

    // DETERMINAR SI ES MOTO
    const vehiculo = userVehicles.find(v => v.patente === patente);
    const isMoto = vehiculo && vehiculo.tipo === 'Moto';

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
            const key = isMoto ? `${type}_moto` : type;
            const rate = currentRates[key] || currentRates[type] || 0;
            
            if (type === 'hora') total = Math.ceil(durationHours) * rate;
            else if (type === 'dia') total = Math.max(1, Math.ceil(durationHours / 24)) * rate;
            else if (type === 'semana') total = Math.ceil(durationHours / (24 * 7)) * rate;
            else if (type === 'quincena') total = Math.ceil(durationHours / (24 * 15)) * rate;
            else if (type === 'mes') total = Math.ceil(durationHours / (24 * 30)) * rate;
            else total = Math.ceil(durationHours) * rate;
        }
    } catch (e) { console.error("Error calculando precio:", e); }

    if (totalEl) totalEl.innerText = total > 0 ? `$ ${formatNum(total)}` : '$ ---';
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
    // RECALCULAR FECHA DE FIN AL CAMBIAR A UN PERIODO
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
    
    // USAR DOCUMENT.QUERYSELECTOR PARA MAYOR ROBUSTEZ
    const patenteEl = document.querySelector('.res-vehicle');
    const sucursalEl = document.querySelector('.res-sucursal');
    const tipoEl = document.querySelector('.res-type');
    const btn = document.querySelector('.btn-confirm-premium');
    
    if (!patenteEl || !sucursalEl || !tipoEl || !btn) {
        console.error("[!] Error: No se encontraron los campos del formulario.");
        console.groupEnd();
        return showToast('Error interno: Formulario incompleto');
    }

    // Si el usuario no tiene vehículos registrados, guiar al quick-add antes de continuar
    if (!userVehicles || userVehicles.length === 0) {
        if (typeof window.showQuickAddVehicle === 'function') window.showQuickAddVehicle();
        console.groupEnd();
        return showToast('Agregá tu primer vehículo para poder reservar');
    }

    const patente = patenteEl.value;
    const sucursal = sucursalEl.value;
    const tipo = tipoEl.value;
    const originalContent = btn.innerHTML;
    
    if (!patente) { console.groupEnd(); return showToast('Seleccioná un vehículo'); }
    if (!sucursal) { console.groupEnd(); return showToast('Seleccioná una sucursal'); }
    if (!tipo) { console.groupEnd(); return showToast('Seleccioná tipo de estadía'); }

    let inicio, fin;

    try {
        if (tipo === 'hora') {
            const fecha = document.querySelector('.res-date-only').value;
            const hora = document.querySelector('.res-time-only').value;
            const hoursQty = parseInt(document.querySelector('.res-hours-qty').value) || 1;
            if (!fecha || !hora) { console.groupEnd(); return showToast('Seleccioná fecha y hora'); }
            inicio = `${fecha} ${hora}`;
            const now = new Date();
            const startDt = new Date(inicio.replace(/-/g, "/"));
            if ((startDt - now) < RESERVA_MIN_MS) { console.groupEnd(); return showToast(`Mínimo ${RESERVA_MIN_MIN} minutos de anticipación.`); }
            const endDt = new Date(startDt.getTime() + hoursQty * 60 * 60 * 1000);
            fin = `${endDt.getFullYear()}-${(endDt.getMonth() + 1).toString().padStart(2, '0')}-${endDt.getDate().toString().padStart(2, '0')} ${endDt.getHours().toString().padStart(2, '0')}:${endDt.getMinutes().toString().padStart(2, '0')}`;
            // VALIDAR HORARIO DE SUCURSAL
            const branch = branchesData.find(b => b.nombre === sucursal);
            if (branch && !branch.is_24h && branch.horario) {
                const hMatch = branch.horario.toUpperCase().trim().match(/^(\d{1,2}):(\d{2})\s+(?:A|UN)\s+(\d{1,2}):(\d{2})$/);
                if (hMatch) {
                    let open = parseInt(hMatch[1]) * 60 + parseInt(hMatch[2]);
                    let close = parseInt(hMatch[3]) * 60 + parseInt(hMatch[4]);
                    // SI CIERRE ES 00:00 SE TRATA COMO 24:00 (FINAL DEL DIA)
                    if (close === 0) close = 1439;
                    const startMin = startDt.getHours() * 60 + startDt.getMinutes();
                    const endMin = endDt.getHours() * 60 + endDt.getMinutes();
                    const endDateStr2 = `${endDt.getFullYear()}-${(endDt.getMonth() + 1).toString().padStart(2, '0')}-${endDt.getDate().toString().padStart(2, '0')}`;
                    if (endDateStr2 !== fecha) {
                        console.groupEnd();
                        return showToast(`La sucursal cierra a las ${hMatch[3]}:${hMatch[4]}. La estadía no puede extenderse más allá del cierre.`);
                    }
                    if (startMin < open || startMin >= close) {
                        console.groupEnd();
                        return showToast(`La sucursal abre de ${branch.horario}. La hora de inicio debe estar dentro del horario de atención.`);
                    }
                    if (endMin > close) {
                        console.groupEnd();
                        return showToast(`La sucursal cierra a las ${hMatch[3]}:${hMatch[4]}. La hora de fin no puede exceder el horario de cierre.`);
                    }
                }
            }
        } else if (tipo === 'dia') {
            const fecha = document.querySelector('.res-day-only').value;
            if (!fecha) { console.groupEnd(); return showToast('Seleccioná un día'); }
            inicio = `${fecha} 00:00`;
            fin = `${fecha} 23:59`;
        } else {
            const periods = { 'semana': 7, 'quincena': 15, 'mes': 30 };
            const periodClasses = { 'semana': '.res-week-start', 'quincena': '.res-fortnight-start', 'mes': '.res-month-start' };
            if (periods[tipo]) {
                const selector = periodClasses[tipo];
                const fecha = document.querySelector(selector).value;
                if (!fecha) { console.groupEnd(); return showToast('Seleccioná día de inicio'); }
                inicio = `${fecha} 00:00`;
                const now = new Date();
                const startDt = new Date(fecha.replace(/-/g, "/"));
                const endDt = new Date(startDt.getTime() + (periods[tipo] - 1) * 24 * 60 * 60 * 1000);
                fin = `${endDt.getFullYear()}-${(endDt.getMonth() + 1).toString().padStart(2, '0')}-${endDt.getDate().toString().padStart(2, '0')} 23:59`;
            } else {
                inicio = document.querySelector('.res-start').value;
                fin = document.querySelector('.res-end').value;
                const now = new Date();
            }
        }
    } catch (err) {
        console.error("[!] Error procesando fechas:", err);
        console.groupEnd();
        return showToast('Error en el formato de fecha');
    }

    // VERIFICAR DISPONIBILIDAD ANTES DE MOSTRAR EL CONFIRM
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
            return showToast(av.data.mensaje || 'No hay disponibilidad para el horario solicitado.');
        }
        if (av.data.restan !== undefined && av.data.restan <= 3) {
            showToast(av.data.mensaje, 'warning');
        }
    }

    const resumenHtml = `
        <div style="text-align: left; padding: 5px; font-family: 'Montserrat', sans-serif;">
            
            <div style="display: flex; flex-direction: column; gap: 20px; margin-bottom: 35px;">
                <!-- VEHÍCULO -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <i class="fas fa-car" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Vehículo</span>
                    </div>
                    <b style="color: #fff; font-size: 1.1rem; letter-spacing: 1px; font-family: 'Montserrat';">${formatPlate(patente)}</b>
                </div>

                <!-- SUCURSAL -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <i class="fas fa-location-dot" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Sucursal</span>
                    </div>
                    <b style="color: #fff; font-size: 0.95rem;">${sucursal}</b>
                </div>

                <div style="height: 1px; background: rgba(255,255,255,0.08); margin: 5px 0;"></div>

                <!-- TIPO -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <i class="fas fa-calendar-day" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Estadía</span>
                    </div>
                    <b style="color: #fff; text-transform: capitalize; font-size: 1rem;">${tipo}</b>
                </div>

                <!-- DESDE -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 15px;">
                        <i class="fas fa-clock" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Desde</span>
                    </div>
                    <b style="color: #eee; font-size: 0.95rem;">${formatDate(inicio)}</b>
                </div>

                <!-- HASTA -->
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 0 5px;">
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <i class="fas fa-hourglass-end" style="color: var(--dorado); font-size: 1.1rem; width: 25px; text-align: center;"></i>
                        <span style="color: #aaa; font-size: 0.95rem;">Hasta</span>
                    </div>
                    <b style="color: #eee; font-size: 0.95rem;">${formatDate(fin)}</b>
                </div>
            </div>

            <!-- TOTAL -->
            <div style="padding-top: 25px; border-top: 2px solid rgba(197,160,89,0.2); display: flex; justify-content: space-between; align-items: center;">
                <span style="font-weight: 900; letter-spacing: 1.5px; color: #fff; font-size: 0.9rem; text-transform: uppercase;">TOTAL ESTIMADO</span>
                <b style="color: var(--dorado); font-size: 1.8rem; text-shadow: 0 0 15px rgba(197,160,89,0.3); font-family: 'Montserrat'; white-space: nowrap;">${document.getElementById('reserva-total-est').innerText}</b>
            </div>
        </div>`;

    if (!await showConfirm('REVISÁ TU RESERVA', resumenHtml)) { console.groupEnd(); return; }

    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> PROCESANDO...';
    btn.disabled = true;

    const payload = { patente, fecha_inicio: inicio, fecha_fin: fin, sucursal_nombre: sucursal, tipo_estadia: tipo };
    console.log('[RESERVAS] Enviando payload:', payload);
    const result = editingReservaId ? 
        await api.patch(`/user/reservations/${editingReservaId}`, payload) : 
        await api.post('/user/reservations', payload);

    console.log('[RESERVAS] Resultado createReservation:', result);

    if (result.ok) {
        showToast(editingReservaId ? '¡Reserva actualizada!' : '¡Reserva creada con éxito!');
        resetReservaForm();
        toggleReservaForm();
        try {
            if (window.showSection) {
                // navigate to reservas and wait for reservations to load before dispatch
                window.showSection('reservas', document.querySelector('.nav-item[onclick*="reservas"]'));
                try { await loadReservations(); } catch (e) { console.warn('[RESERVAS] loadReservations error after create:', e); }
            } else {
                try { await loadReservations(); } catch (e) { console.warn('[RESERVAS] loadReservations error after create (no showSection):', e); }
            }
        } catch (e) { console.warn('[RESERVAS] error esperando render de reservas:', e); }
        if (window.loadProfile) window.loadProfile();

        // Disparar evento para notificar a listeners (p. ej. tour) que se creó una reserva
        try {
            console.log('[RESERVAS] Dispatching reservation:created with data:', result.data);
            document.dispatchEvent(new CustomEvent('reservation:created', { detail: result.data || {} }));
        } catch (e) { console.warn('[RESERVAS] no se pudo dispatch reservation:created', e); }

        // Intento directo: si existe helper del tour, pedir que inicie el paso de 'Mis Reservas' (fallback)
        try {
            if (window.startReservationTourAtReservations && typeof window.startReservationTourAtReservations === 'function') {
                console.log('[RESERVAS] Llamando startReservationTourAtReservations() como fallback');
                setTimeout(() => { try { window.startReservationTourAtReservations(); } catch (e) { console.warn('[RESERVAS] startReservationTourAtReservations error', e); } }, 350);
            }
        } catch (e) { /* noop */ }
    } else { 
        console.log('[RESERVAS] createReservation failed:', result.error || result);
        showToast(result.error || 'Error al procesar reserva'); 
    }

    // Always emit a debug event so listeners can inspect final state
    try { document.dispatchEvent(new CustomEvent('reservation:created:debug', { detail: result || {} })); } catch (e) { /* noop */ }
    
    btn.innerHTML = originalContent;
    btn.disabled = false;
    console.groupEnd();
}

export async function loadReservations() {
    const res = await api.get('/user/reservations');
    if (!res.ok) return;
    
    const all = res.data;
    const active = all.filter(r => r.estado_reserva === 'Pendiente' || r.estado_reserva === 'Activa');
    historyData = all.filter(r => r.estado_reserva !== 'Pendiente' && r.estado_reserva !== 'Activa');
    
    const now = typeof window.getVirtualNow === 'function' ? window.getVirtualNow() : new Date();
    const inProgress = active.filter(r => now >= new Date(r.fecha_inicio.replace(/-/g, "/")) && now < new Date(r.fecha_fin.replace(/-/g, "/")));
    const upcoming = active.filter(r => now < new Date(r.fecha_inicio.replace(/-/g, "/")));

    if (document.getElementById('stat-reservations')) document.getElementById('stat-reservations').innerText = formatNum(active.length);
    if (document.getElementById('stat-res-active')) document.getElementById('stat-res-active').innerText = formatNum(inProgress.length);
    if (document.getElementById('stat-res-upcoming')) document.getElementById('stat-res-upcoming').innerText = formatNum(upcoming.length);

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
    const now = typeof window.getVirtualNow === 'function' ? window.getVirtualNow() : new Date();
    const start = new Date(r.fecha_inicio.replace(/-/g, "/"));
    const end = new Date(r.fecha_fin.replace(/-/g, "/"));
    let progress = 0;
    let isStarted = now >= start;
    if (isStarted) progress = Math.min(100, Math.max(0, ((now - start) / (end - start)) * 100));

    return `
    <div class="reserva-card-ultra ${isFeatured ? 'featured' : ''}" data-reserva-id="${r.id}">
        <div class="reserva-header-ultra">
            <div class="reserva-info-main">
                <span class="reserva-tag-id">RESERVA #${r.id}</span>
                <div class="reserva-plate-container">
                    <div class="plate-badge-premium">${formatPlate(r.patente)}</div>
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
            <button class="btn-ultra btn-ultra-danger" onclick="cancelReservation(${r.id})"><i class="fas fa-trash"></i></button>
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
            <div class="hist-main-info"><span class="hist-title">${r.sucursal_nombre}</span><div class="hist-subtitle-group"><span class="hist-plate-badge">${formatPlate(r.patente)}</span><span class="hist-date-info">${formatDate(r.fecha_inicio).split(',')[0]}</span></div></div>
            <div class="hist-amount-info"><span class="hist-value">$${r.monto_total.toLocaleString()}</span><div class="status-pill ${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</div></div>
            <div class="hist-actions-group"><button class="btn-repeat-express" onclick="repeatReservation('${r.patente}','${r.sucursal_nombre}','${r.tipo_estadia}')"><i class="fas fa-rotate-right"></i></button></div>
        </div>`).join('');

    if (document.getElementById('historial-page-info')) document.getElementById('historial-page-info').innerText = `Página ${historialCurrentPage} de ${totalPages || 1}`;
    const prevBtn = document.getElementById('historial-prev'); if (prevBtn) prevBtn.disabled = historialCurrentPage === 1;
    const nextBtn = document.getElementById('historial-next'); if (nextBtn) nextBtn.disabled = historialCurrentPage >= totalPages;
}

export async function cancelReservation(id) {
    // 1. OBTENER PREVISUALIZACION DEL REEMBOLSO
    const resSim = await api.get(`/user/reservations/${id}/cancel-simulation`);
    let confirmMsg = '¿Estás seguro de cancelar esta reserva? Esta acción no se puede deshacer.';
    
    if (resSim.ok) {
        const { reembolso, error } = resSim.data;
        if (error) {
            return showToast(`No se puede cancelar: ${error}`);
        }
        if (reembolso > 0) {
            confirmMsg = `Al cancelar ahora, se te reembolsarán <b style="color:var(--dorado);">$${reembolso.toLocaleString()}</b> en tu saldo AutoPass.<br><br>¿Deseás continuar?`;
        }
    }

    if (!await showConfirm('CANCELAR RESERVA', confirmMsg)) return;

    const res = await api.post(`/user/reservations/${id}/cancel`);
    if (res.ok) { 
        showToast('Reserva cancelada con éxito'); 
        loadReservations(); 
        if (window.loadProfile) window.loadProfile(); 
    }
    else { showToast(res.error || 'Error al cancelar'); }
}

export async function payReservation(id) {
    if (!await showConfirm('PAGAR RESERVA', '¿Deseás pagar con tu saldo AutoPass?')) return;
    const res = await api.post(`/user/reservations/${id}/pay`);
    if (res.ok) { 
        showToast('¡Pago exitoso!'); 
        loadReservations(); 
        if (window.loadProfile) window.loadProfile(); 
        // DISPARAR EVENTO PARA EL TOUR
        try { document.dispatchEvent(new CustomEvent('reservation:paid', { detail: { id } })); } catch (e) {}
    }
    else { showToast(res.error || 'Error en el pago'); }
}

export function historialPage(dir) { historialCurrentPage += dir; applyHistoryFilters(); }

export async function showDigitalPass(id) {
    const res = await api.get('/user/reservations');
    if (!res.ok) return;
    const r = res.data.find(item => item.id === id);
    if (!r) return;

    document.getElementById('ticket-id-display').innerText = `#${r.id.toString().padStart(6, '0')}`;
    document.getElementById('ticket-patente').innerText = formatPlate(r.patente);
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
    if (modal) {
        modal.style.display = 'flex';
        // DISPARAR EVENTO PARA EL TOUR
        try { document.dispatchEvent(new CustomEvent('digitalpass:open', { detail: { id } })); } catch (e) {}
    }
}

export function closeDigitalPass() {
    const modal = document.getElementById('modal-pase-digital');
    if (modal) {
        modal.style.display = 'none';
        // DISPARAR EVENTO PARA EL TOUR
        try { document.dispatchEvent(new CustomEvent('digitalpass:closed')); } catch (e) {}
    }
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
