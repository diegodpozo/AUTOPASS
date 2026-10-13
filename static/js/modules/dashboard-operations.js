import api from './api.js';
import * as utils from './utils.js';
import * as stats from './dashboard-stats.js';
import * as baseUi from './ui.js';

/**
 * Módulo de Operaciones Manuales y Gestión de Accesos
 */

export async function manualEntry() {
    const plateInput = document.getElementById('manual-plate');
    if (!plateInput) return;
    let plate = plateInput.value.trim().toUpperCase().replace(/[^A-Z0-9]/g, '');
    let type = document.getElementById('manual-type')?.value || 'Auto';
    const floorId = document.getElementById('manual-floor')?.value;
    
    if (!plate) return utils.showToast('Ingresá una patente', 'error');

    // DETECCION AUTOMATICA DE MOTO (FORMATO: 1 LETRA, 3 NUMEROS, 3 LETRAS)
    const isMoto = /^[A-Z]{1}[0-9]{3}[A-Z]{3}$/.test(plate);
    if (isMoto) {
        type = 'Moto';
    }

    // CONFIRMACION MEDIANTE ALERTA PREMIUM
    const confirmed = await utils.showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-dorado" style="letter-spacing: 1px;">
                ${utils.formatPlate(plate)}
            </div>
            <div style="text-transform: uppercase;">
                TIPO: ${isMoto ? 'MOTO' : 'AUTO'}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Confirmar el registro?
            </div>
        </div>`
    );
    
    if (!confirmed) return;

    let url = `/admin/manual-entry?plate=${plate}&tipo_vehiculo=${type}`;
    if (floorId) url += `&floor_id=${floorId}`;

    const res = await api.post(url);
    if (res.ok) {
        utils.showToast('Ingreso registrado con éxito', 'success');
        plateInput.value = '';
        stats.loadOccupancy();
        stats.loadLiveStats();
    } else {
        utils.showToast(res.error || 'Error al registrar ingreso', 'error');
    }
}

export async function payOccupancy(plate, amount, onPaidCallback) {
    const metodo = await utils.showChoice(
        'Pago de Estadía',
        `${utils.formatPlate(plate)} — MONTO: $${utils.formatNum(amount || 0)} — ¿Con qué método abonó el cliente?`,
        [
            { label: 'Efectivo', icon: 'fa-money-bill-wave' },
            { label: 'Mercado Pago', icon: 'fa-wallet' },
            { label: 'Transferencia', icon: 'fa-building-columns' },
            { label: 'Tarjeta', icon: 'fa-credit-card' },
            { label: 'Otro', icon: 'fa-circle-question' },
        ]
    );

    if (!metodo) return;

    const confirmed = await utils.showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-dorado" style="letter-spacing: 1px;">
                ${utils.formatPlate(plate)}
            </div>
            <div>
                MONTO: $${utils.formatNum(amount || 0)}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Confirmar el pago con ${metodo}?
            </div>
        </div>`
    );

    if (!confirmed) return;

    const res = await api.post(`/access/pay-stay?plate=${plate}&metodo=${encodeURIComponent(metodo)}`);
    if (res.ok) { 
        utils.showToast(`Pago procesado (${metodo})`, 'success'); 
        stats.loadOccupancy(); 
        stats.loadLiveStats();
        if (typeof onPaidCallback === 'function') {
            onPaidCallback();
        }
    } else {
        utils.showToast(res.error || 'Error al procesar pago', 'error');
    }
}

export async function manualExit(plate, type) {
    const confirmed = await utils.showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-dorado" style="letter-spacing: 1px;">
                ${utils.formatPlate(plate)}
            </div>
            <div style="text-transform: uppercase;">
                TIPO: ${type || 'AUTO'}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Confirmar la salida?
            </div>
        </div>`
    );

    if (!confirmed) return;
    
    const res = await api.post(`/admin/manual-exit?plate=${plate}`);
    if (res.ok) { 
        utils.showToast('Salida registrada', 'success'); 
        stats.loadOccupancy(); 
        stats.loadLiveStats();
    } else {
        utils.showToast(res.error || 'Error al registrar salida', 'error');
    }
}

export async function showLogDetail(logId) {
    const res = await api.get('/reports/access');
    if (!res.ok) return;
    
    const log = res.data.find(l => l.id === logId);
    if (!log) return;

    const plateEl = document.getElementById('audit-plate');
    if (plateEl) plateEl.innerText = log.patente_detectada;
    const d = utils.parseFecha(log.fecha_hora);
    document.getElementById('audit-time').innerText = `${String(d.getDate()).padStart(2,'0')}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getFullYear()).slice(-2)} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
    document.getElementById('audit-type').innerText = log.tipo_evento;
    document.getElementById('audit-payment').innerText = log.pago_confirmado ? 'PAGADO' : 'PENDIENTE';
    document.getElementById('audit-res-id').innerText = log.reserva_id ? `#${log.reserva_id}` : 'SIN RESERVA';
    const usuarioEl = document.getElementById('audit-usuario');
    if (usuarioEl) usuarioEl.innerText = log.es_registrado ? log.usuario : 'INVITADO';

    const imgEl = document.getElementById('audit-image');
    if (imgEl) {
        const token = localStorage.getItem('token');
        imgEl.src = `/v1/system/capture/${logId}?token=${encodeURIComponent(token || '')}&t=${Date.now()}`;
    }
    
    if (baseUi.openModal) baseUi.openModal('modal-log-detail');
}

/**
 * SALIDA IMPAGA POR LECTOR DE PATENTE (ALPR).
 * El backend emite PENDING_EXIT al denegar la salida por deuda; este popup
 * muestra usuario/foto/monto, permite elegir metodo de pago y al cobrar
 * registra la salida y abre la barrera automaticamente.
 */
let pendingExitData = null;

export function openPendingExitPopup(data) {
    if (!data || !data.patente) return;
    pendingExitData = data;

    const plateEl = document.getElementById('pending-exit-plate');
    if (plateEl) plateEl.innerText = utils.formatPlate(data.patente);

    const userEl = document.getElementById('pending-exit-user');
    if (userEl) userEl.innerText = data.es_registrado ? data.usuario : 'INVITADO';

    const amountEl = document.getElementById('pending-exit-amount');
    if (amountEl) {
        amountEl.innerText = (data.deuda === null || data.deuda === undefined)
            ? 'SIN TARIFARIO'
            : `$${utils.formatNum(data.deuda)}`;
    }

    const imgEl = document.getElementById('pending-exit-image');
    const placeholderEl = document.getElementById('pending-exit-placeholder');
    if (imgEl && data.log_id) {
        if (placeholderEl) placeholderEl.style.display = 'none';
        imgEl.style.display = '';
        imgEl.onerror = () => {
            imgEl.style.display = 'none';
            if (placeholderEl) placeholderEl.style.display = 'flex';
        };
        const token = localStorage.getItem('token');
        imgEl.src = `/v1/system/capture/${data.log_id}?token=${encodeURIComponent(token || '')}&t=${Date.now()}`;
    } else if (placeholderEl) {
        placeholderEl.style.display = 'flex';
    }

    const methodEl = document.getElementById('pending-exit-method');
    if (methodEl) methodEl.value = 'Efectivo';

    const confirmBtn = document.getElementById('pending-exit-confirm');
    if (confirmBtn) confirmBtn.disabled = false;

    if (baseUi.openModal) baseUi.openModal('modal-pending-exit');
}

export function closePendingExitPopup() {
    pendingExitData = null;
    if (baseUi.closeModal) baseUi.closeModal('modal-pending-exit');
}

export async function confirmPendingExit() {
    if (!pendingExitData || !pendingExitData.patente) return;
    const plate = pendingExitData.patente;
    const metodo = document.getElementById('pending-exit-method')?.value || 'Efectivo';
    const confirmBtn = document.getElementById('pending-exit-confirm');

    if (confirmBtn) {
        confirmBtn.disabled = true;
    }

    // 1. COBRAR LA ESTADÍA EN CAJA
    const pay = await api.post(`/access/pay-stay?plate=${encodeURIComponent(plate)}&metodo=${encodeURIComponent(metodo)}`);
    if (!pay.ok) {
        if (confirmBtn) confirmBtn.disabled = false;
        utils.showToast(pay.error || 'Error al procesar el pago', 'error');
        return;
    }

    // 2. REGISTRAR LA SALIDA Y ABRIR LA BARRERA
    const exit = await api.post(`/admin/manual-exit?plate=${encodeURIComponent(plate)}`);
    if (confirmBtn) confirmBtn.disabled = false;
    if (!exit.ok) {
        utils.showToast(exit.error || 'Pago registrado, pero no se pudo abrir la barrera', 'error');
        return;
    }

    closePendingExitPopup();
    const cobrado = pay.data && pay.data.monto_cobrado;
    utils.showToast(cobrado != null
        ? `Pago de $${utils.formatNum(cobrado)} registrado. Barrera abierta.`
        : 'Pago registrado. Barrera abierta.', 'success');
    stats.loadOccupancy();
    stats.loadLiveStats();
}
