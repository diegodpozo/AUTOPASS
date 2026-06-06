import api from './api.js';
import { formatDate } from './utils.js';

/**
 * DASHBOARD STATS MODULE
 * Carga de datos en tiempo real, ocupación y métricas.
 */

export async function loadLiveStats() {
    const resStatus = await api.get('/parking/status');
    if (resStatus && resStatus.ok) {
        const { disponibilidad: free, ocupacion_actual: occupied, capacidad_total: total } = resStatus.data;

        const freeEl = document.getElementById('stat-free');
        const occupiedEl = document.getElementById('stat-occupied');
        if (freeEl) freeEl.innerText = free;
        if (occupiedEl) occupiedEl.innerText = occupied;

        const barFree = document.getElementById('bar-free');
        const barOccupied = document.getElementById('bar-occupied');
        if (barFree) barFree.style.width = `${(free / total) * 100}%`;
        if (barOccupied) barOccupied.style.width = `${(occupied / total) * 100}%`;
    }

    const resFinance = await api.get('/reports/financial-summary?period=day');
    if (resFinance && resFinance.ok) {
        const entriesEl = document.getElementById('stat-entries');
        const moneyEl = document.getElementById('stat-money');
        if (entriesEl) entriesEl.innerText = resFinance.data.cantidad_pagos;
        if (moneyEl) moneyEl.innerText = `$${resFinance.data.total_recaudado.toLocaleString('es-AR')}`;
    }
}

export async function loadRecentLogs() {
    const res = await api.get('/reports/access');
    if (!res || !res.ok) return;

    const tbody = document.getElementById('live-logs');
    if (!tbody) return;

    const logs = res.data;
    
    // Actualizar patentes en tiempo real (Cajas de cámara)
    const lastEntry = logs.find(l => l.tipo_evento === 'ENTRADA');
    const lastExit = logs.find(l => l.tipo_evento === 'SALIDA');

    const plateEntryEl = document.getElementById('plate-entry');
    const plateExitEl = document.getElementById('plate-exit');

    if (plateEntryEl && lastEntry) plateEntryEl.innerText = lastEntry.patente_detectada;
    if (plateExitEl && lastExit) plateExitEl.innerText = lastExit.patente_detectada;

    tbody.innerHTML = logs.slice(0, 10).map(log => {
        const time = new Date(log.fecha_hora).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
        const badgeClass = log.tipo_evento === 'ENTRADA' ? 'text-secondary' : 'text-dorado';
        const statusBadge = log.pago_confirmado ? 
            `<span class="badge badge-success-light">PAGADO</span>` : 
            `<span class="badge badge-danger-light">PENDIENTE</span>`;

        return `
            <tr>
                <td data-label="Hora" class="text-center">${time}</td>
                <td data-label="Patente" class="text-center"><span class="plate-style">${log.patente_detectada}</span></td>
                <td data-label="Evento" class="${badgeClass} text-bold text-center">${log.tipo_evento}</td>
                <td data-label="Estado" class="text-center">${statusBadge}</td>
                <td data-label="Info" class="text-center"><button class="btn-edit" onclick="showLogDetail(${log.id})" title="Ver detalle y captura del evento"><i class="fas fa-eye"></i></button></td>
            </tr>`;
    }).join('') || '<tr><td colspan="5" class="text-center py-20">No hay movimientos.</td></tr>';
}

export async function loadOccupancy() {
    const res = await api.get('/parking/current-occupancy');
    if (!res || !res.ok) return;

    const data = res.data;
    const tbody = document.getElementById('occ-list');
    if (!tbody) return;

    let totalDebt = 0, totalMs = 0;

    tbody.innerHTML = data.map(occ => {
        const date = new Date(occ.ingreso);
        const diffMs = new Date() - date;
        totalMs += diffMs; totalDebt += occ.deuda;

        const duration = `${Math.floor(diffMs / 3600000)}h ${Math.floor((diffMs % 3600000) / 60000)}m`;
        const statusBadge = occ.ya_pago ? 
            `<span class="badge badge-success-light">PAGO CONFIRMADO</span>` :
            `<span class="badge badge-warning-light">$${occ.deuda.toLocaleString('es-AR')} PENDIENTE</span>`;

        return `
            <tr>
                <td data-label="Vehículo" class="text-center"><span class="plate-style">${occ.patente}</span></td>
                <td data-label="Ingreso" class="text-center">${date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}</td>
                <td data-label="Permanencia" class="text-bold text-light text-center">${duration}</td>
                <td data-label="Estado" class="text-center">${statusBadge}</td>
                <td data-label="Acciones" class="text-center">
                    <div class="flex-row gap-5 justify-center">
                        ${!occ.ya_pago ? `<button class="btn-icon-premium sm" onclick="payOccupancy('${occ.patente}')" title="Registrar pago de estadía"><i class="fas fa-cash-register"></i></button>` : ''}
                        <button class="btn-icon-premium sm danger" onclick="cancelStay('${occ.patente}')" title="Cancelar estadía (Cortesía 15 min)"><i class="fas fa-times"></i></button>
                        <button class="btn-icon-premium sm warning" onclick="manualExit('${occ.patente}')" title="Registrar salida manual de vehículo"><i class="fas fa-door-open"></i></button>
                    </div>
                </td>
            </tr>`;
    }).join('') || '<tr><td colspan="5" class="text-center py-20">Sin vehículos.</td></tr>';

    const countEl = document.getElementById('occ-stat-count');
    const debtEl = document.getElementById('occ-stat-debt');
    if (countEl) countEl.innerText = data.length;
    if (debtEl) debtEl.innerText = `$${totalDebt.toLocaleString('es-AR')}`;
}

export async function cancelStay(plate) {
    const { showConfirm, showToast } = await import('./utils.js');
    if (!await showConfirm('Cancelar Estadía', `¿Confirmás la cancelación de la estadía para <b>${plate}</b>?<br><small>Se aplicará cortesía de 15 min si corresponde.</small>`)) return;

    const res = await api.post(`/admin/cancel-stay?plate=${plate}`);
    if (res.ok) {
        showToast(res.data.message, 'success');
        loadOccupancy();
        loadLiveStats();
    } else {
        showToast(res.error, 'error');
    }
}
