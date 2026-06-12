import api from './api.js';
import { formatDate, formatPlate } from './utils.js';

/**
 * DASHBOARD STATS MODULE
 * Carga de datos en tiempo real, ocupación y métricas.
 */

export async function loadLiveStats() {
    const resStatus = await api.get('/parking/status');
    if (resStatus && resStatus.ok) {
        const { disponibilidad: free, ocupacion_actual: occupied, capacidad_total: total, ocupacion_motos: occMotos, capacidad_motos: capMotos, disponibilidad_motos: freeMotos } = resStatus.data;

        // Autos
        const freeEl = document.getElementById('stat-free');
        if (freeEl) freeEl.innerText = free;
        const barFree = document.getElementById('bar-free');
        if (barFree) barFree.style.width = `${(free / total) * 100}%`;

        // Motos
        const freeMotosEl = document.getElementById('stat-free-motos');
        if (freeMotosEl) freeMotosEl.innerText = freeMotos;
        const barFreeMotos = document.getElementById('bar-free-motos');
        if (barFreeMotos) barFreeMotos.style.width = `${(freeMotos / capMotos) * 100}%`;

        // Ocupación Total y KPI Moto
        const occMotosEl = document.getElementById('occ-stat-motos');
        if (occMotosEl) occMotosEl.innerText = occMotos;

        const totalCapacity = total + capMotos;
        const totalOccupied = occupied + occMotos;
        const occupiedPercent = totalCapacity > 0 ? Math.round((totalOccupied / totalCapacity) * 100) : 0;

        const occupiedPercentEl = document.getElementById('stat-occupied-percent');
        if (occupiedPercentEl) occupiedPercentEl.innerText = `${occupiedPercent}%`;

        const barOccupied = document.getElementById('bar-occupied');
        if (barOccupied) {
            barOccupied.style.width = `${occupiedPercent}%`;
            // Color dinámico según carga
            barOccupied.className = 'progress-fill';
            if (occupiedPercent > 90) barOccupied.classList.add('danger');
            else if (occupiedPercent > 70) barOccupied.classList.add('warning');
        }
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

    if (plateEntryEl && lastEntry) plateEntryEl.innerText = formatPlate(lastEntry.patente_detectada);
    if (plateExitEl && lastExit) plateExitEl.innerText = formatPlate(lastExit.patente_detectada);

    tbody.innerHTML = logs.slice(0, 10).map(log => {
        const time = new Date(log.fecha_hora).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
        const badgeClass = log.tipo_evento === 'ENTRADA' ? 'text-secondary' : 'text-dorado';
        const statusBadge = log.pago_confirmado ? 
            `<span class="badge badge-success-light">PAGADO</span>` : 
            `<span class="badge badge-danger-light">PENDIENTE</span>`;

        return `
            <tr>
                <td data-label="Hora" class="text-center">${time}</td>
                <td data-label="Patente" class="text-center"><span class="plate-style">${formatPlate(log.patente_detectada)}</span></td>
                <td data-label="Evento" class="${badgeClass} text-bold text-center">${log.tipo_evento}</td>
                <td data-label="Estado" class="text-center">${statusBadge}</td>
                <td data-label="Info" class="text-center"><button class="btn-edit" onclick="showLogDetail(${log.id})" title="Ver detalle y captura del evento"><i class="fas fa-eye"></i></button></td>
            </tr>`;
    }).join('') || '<tr><td colspan="5" class="text-center py-20">No hay movimientos.</td></tr>';
}

export async function loadOccupancy() {
    const res = await api.get('/parking/current-occupancy');
    const resBranches = await api.get('/parking/branches');
    
    if (res.ok) {
        const data = res.data;
        const tbody = document.getElementById('occ-list');
        if (!tbody) return;

        // 1. Manejo de pisos en el formulario manual
        const mySucursal = localStorage.getItem('sucursal')?.replace('AUTOPASS ', '').trim() || '';
        const branch = resBranches.ok ? resBranches.data.find(b => b.nombre === mySucursal) : null;
        
        const floorGroup = document.getElementById('manual-floor-group');
        const floorSelect = document.getElementById('manual-floor');
        
        if (branch && branch.floors && branch.floors.length > 0) {
            if (floorGroup) floorGroup.style.display = 'block';
            if (floorSelect) {
                const currentVal = floorSelect.value;
                floorSelect.innerHTML = '<option value="">Seleccioná piso...</option>' + 
                    branch.floors.map(f => `<option value="${f.id}">${f.nombre}</option>`).join('');
                if (currentVal) floorSelect.value = currentVal;
            }
        } else {
            if (floorGroup) floorGroup.style.display = 'none';
        }

        let totalDebt = 0;
        const now = new Date();

        tbody.innerHTML = data.map(occ => {
            const date = new Date(occ.ingreso);
            const diffMs = now - date;
            const duration = `${Math.floor(diffMs / 3600000)}h ${Math.floor((diffMs % 3600000) / 60000)}m`;
            totalDebt += occ.deuda || 0;

            const statusBadge = occ.ya_pago ? 
                `<span class="badge badge-success-light">PAGO CONFIRMADO</span>` :
                `<span class="badge badge-warning-light">$${occ.deuda.toLocaleString('es-AR')} PENDIENTE</span>`;

            const floorInfo = occ.floor_nombre ? `<div class="text-xs text-muted mt-2">${occ.floor_nombre}</div>` : '';

            return `
            <tr>
                <td data-label="Vehículo" class="text-center">
                    <div class="flex-row items-center justify-center gap-8">
                        <i class="fas ${occ.tipo_vehiculo === 'Moto' ? 'fa-motorcycle' : 'fa-car-side'} text-muted"></i>
                        <div class="flex-col items-center">
                            <span class="plate-style">${formatPlate(occ.patente)}</span>
                            ${floorInfo}
                        </div>
                    </div>
                </td>
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
    const motosEl = document.getElementById('occ-stat-motos');
    const debtEl = document.getElementById('occ-stat-debt');
    if (countEl) countEl.innerText = data.filter(v => v.tipo_vehiculo !== 'Moto').length;
    if (motosEl) motosEl.innerText = data.filter(v => v.tipo_vehiculo === 'Moto').length;
    if (debtEl) debtEl.innerText = `$${totalDebt.toLocaleString('es-AR')}`;
    }
}

export async function cancelStay(plate) {
    const { showConfirm, showToast } = await import('./utils.js');
    if (!await showConfirm('Cancelar Estadía', `¿Confirmás la cancelación de la estadía para <b>${formatPlate(plate)}</b>?<br><small>Se aplicará cortesía de 15 min si corresponde.</small>`)) return;

    const res = await api.post(`/admin/cancel-stay?plate=${plate}`);
    if (res.ok) {
        showToast(res.data.message, 'success');
        loadOccupancy();
        loadLiveStats();
    } else {
        showToast(res.error, 'error');
    }
}
