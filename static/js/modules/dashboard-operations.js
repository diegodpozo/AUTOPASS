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
