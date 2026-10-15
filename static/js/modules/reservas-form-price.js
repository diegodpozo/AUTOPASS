/**
 * MÓDULO RESERVAS - TARIFAS Y DESCUENTO
 * Cálculo dinámico del precio estimado, carga de tarifas por sucursal y
 * descuento de reserva vigente (consulta lazy con token anti-race).
 */

import api from './api.js';
import { formatNum, computeHourlyAmount } from './utils.js';
import {
    getCurrentRates,
    setCurrentRates,
    getUserVehicles,
    getReservationDiscount,
    setReservationDiscount,
    setReservationTotals,
    setReservationQuote,
    getDiscountToken,
    bumpDiscountToken
} from './reservas-form-state.js';

// SUFIJO DE CLAVE DE TARIFA SEGUN EL TIPO DE VEHICULO ('' / '_moto' / '_camioneta').
// Debe coincidir con BillingService._tipo_key del backend.
function vehicleRateSuffix(vehiculo) {
    const tipo = vehiculo?.tipo;
    if (tipo === 'Moto') return '_moto';
    if (tipo === 'Camioneta') return '_camioneta';
    return '';
}

export async function fetchRates(sucursal = null) {
    const url = sucursal ? `/user/rates?sucursal=${sucursal}` : '/user/rates';
    const res = await api.get(url);
    if (res.ok) {
        setCurrentRates(res.data);
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
        setReservationDiscount({ pct: 0, sucursal: '', fetchedFor: '' });
        return;
    }
    if (getReservationDiscount().fetchedFor === branch) return;
    const token = bumpDiscountToken();
    let pct = 0;
    let suc = '';
    try {
        const res = await api.get(`/user/redemptions/available?sucursal=${encodeURIComponent(branch)}`);
        if (res.ok && res.data && res.data.length > 0) {
            pct = res.data[0].valor_descuento || 0;
            suc = res.data[0].sucursal || '';
        }
    } catch (e) { /* noop */ }

    if (token === getDiscountToken()) {
        setReservationDiscount({ pct, sucursal: suc, fetchedFor: branch });
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

    const vehiculo = getUserVehicles().find(v => v.patente === patente);
    const suffix = vehicleRateSuffix(vehiculo);

    const rates = getCurrentRates();
    const rate = rates[`${type}${suffix}`] || rates[type] || 0;
    const rate30 = rates[`30min${suffix}`] || rate / 2;
    // TARIFAS DE REFERENCIA POR HORA/FRACCIÓN (para la foto histórica que enviamos al backend).
    const tarifaHora = rates[`hora${suffix}`] || 0;
    const tarifaFraccion = rates[`30min${suffix}`] || tarifaHora / 2;

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
    let durationHours = 0;
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
                /* El fin debe coincidir EXACTAMENTE con el que arma createReservation
                   (inicio + (periodos-1) días, cerrando a las 23:59) para que la
                   duración cotizada coincida con la que recalcula el backend. */
                inicio = new Date(`${fecha}T00:00`);
                fin = new Date(inicio.getTime() + ((periods[type] - 1) * 24 + 23) * 60 * 60 * 1000 + 59 * 60 * 1000);
            }
        }

        if (inicio && fin) {
            durationHours = (fin - inicio) / 3600000;
            
            if (type === 'hora') total = computeHourlyAmount(durationHours, rate, rate30);
            else if (type === 'dia') total = Math.max(1, Math.ceil(durationHours / 24)) * rate;
            else if (type === 'semana') total = Math.ceil(durationHours / (24 * 7)) * rate;
            else if (type === 'quincena') total = Math.ceil(durationHours / (24 * 15)) * rate;
            else if (type === 'mes') total = Math.ceil(durationHours / (24 * 30)) * rate;
            else total = Math.ceil(durationHours) * rate;
        }
    } catch (e) { console.error("Error calculando precio:", e); }

    // FOTO DE LA COTIZACIÓN VIGENTE: se envía al backend al confirmar la reserva para
    // que revalide el total y la persista como registro histórico del precio.
    setReservationQuote({
        base: total,
        horas: durationHours,
        tarifaHora,
        tarifaFraccion,
        tarifaAplicada: rate
    });

    const originalEl = document.getElementById('reserva-total-original');
    const discountLineEl = document.getElementById('reserva-discount-line');
    const labelEl = document.getElementById('reserva-total-label');
    const pct = getReservationDiscount().pct || 0;

    /* El bloque de total se oculta mientras falte sucursal o tipo de estadia.
       Antes se veía "Total: $ ---" en un form recien abierto, que es un precio
       que no existe todavia y no aporta nada. El gate es por los dos selects,
       no por `total > 0`: asi el "$ ---" sigue apareciendo cuando ya elegiste
       que estas reserving pero falta la fecha, que si es informacion util.

       Se oculta el contenedor y no los hijos, porque los hijos ya se togglean
       (original y descuento) y tocar sus display por separado los desincroniza
       del estado real del descuento. */
    const sucursalEl = document.querySelector('.res-sucursal');
    const resumenEl = document.querySelector('.price-summary-premium');
    if (resumenEl) {
        const faltanBases = !sucursalEl?.value || !type;
        /* Se saca la clase y NO se escribe style.display: la clase es la que
           apagaba el bloque en el markup, y escribir el display aparte dejaria
           un atributo inline que la regla de arriba vuelve a pelear. */
        resumenEl.classList.toggle('is-pendiente', faltanBases);
    }

    if (total > 0 && pct > 0) {
        const discountAmount = Math.round(total * pct) / 100;
        const finalTotal = total - discountAmount;
        setReservationTotals({ original: total, discount: discountAmount, final: finalTotal });
        if (originalEl) { originalEl.innerText = `$ ${formatNum(total)}`; originalEl.style.display = 'inline-block'; }
        if (discountLineEl) {
            discountLineEl.innerHTML = `<i class="fas fa-percent"></i> DESCUENTO ${pct}%${getReservationDiscount().sucursal ? ` · ${getReservationDiscount().sucursal}` : ''} &nbsp;·&nbsp; - $ ${formatNum(discountAmount)}`;
            discountLineEl.style.display = 'block';
        }
        if (labelEl) labelEl.innerText = 'Total a pagar:';
        if (totalEl) totalEl.innerText = `$ ${formatNum(finalTotal)}`;
    } else {
        setReservationTotals({ original: total, discount: 0, final: total });
        if (originalEl) { originalEl.innerText = ''; originalEl.style.display = 'none'; }
        if (discountLineEl) { discountLineEl.innerHTML = ''; discountLineEl.style.display = 'none'; }
        if (labelEl) labelEl.innerText = 'Total:';
        if (totalEl) totalEl.innerText = total > 0 ? `$ ${formatNum(total)}` : '$ ---';
    }

    // GARANTIZA QUE EL DESCUENTO DE LA SUCURSAL ESTÉ CARGADO (carga lazy + re-render cuando llega)
    const selBranch = document.querySelector('.res-sucursal')?.value || '';
    if (total > 0) lazyLoadDiscount(selBranch);

    // P2.5 UX/UI: sincroniza el stepper con el estado del total calculado
    if (typeof window.updateReservationStepper === 'function') window.updateReservationStepper();
}
