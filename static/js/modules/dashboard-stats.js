import api from './api.js';
import { formatDate, formatPlate, formatNum } from './utils.js';

/**
 * PANEL ESTADISTICAS MODULO
 * CARGA DE DATOS EN TIEMPO REAL, OCUPACION Y METRICAS.
 */

export function initOccupancyWS() {
    const token = localStorage.getItem('token');
    if (!token) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/v1/parking/ws?token=${token}`;
    
    const socket = new WebSocket(wsUrl);

    socket.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('[WS Occupancy] Update received:', data);
        
        // REFRESCAR COMPONENTES CLAVE
        loadLiveStats();
        loadRecentLogs();
        loadOccupancy();
    };

    socket.onclose = () => {
        console.warn('[WS Occupancy] Connection closed. Retrying in 5s...');
        setTimeout(initOccupancyWS, 5000);
    };

    socket.onerror = (err) => {
        console.error('[WS Occupancy] Error:', err);
    };
}

export async function loadLiveStats() {
    const resStatus = await api.get('/parking/status');
    if (resStatus && resStatus.ok) {
        const { disponibilidad: free, ocupacion_actual: occupied, capacidad_total: total, ocupacion_motos: occMotos, capacidad_motos: capMotos, disponibilidad_motos: freeMotos, disponibilidad_camionetas: freeCamionetas, capacidad_camionetas: capCamionetas, ocupacion_camionetas: occCamionetas } = resStatus.data;

        // AUTOS
        const freeEl = document.getElementById('stat-free');
        if (freeEl) freeEl.innerText = formatNum(free);
        const totalEl = document.getElementById('stat-free-total');
        if (totalEl) totalEl.innerText = `Tot. Disp. ${formatNum(total)}`;
        const barFree = document.getElementById('bar-free');
        if (barFree) barFree.style.width = `${(free / total) * 100}%`;

        // MOTOS
        const freeMotosEl = document.getElementById('stat-free-motos');
        if (freeMotosEl) freeMotosEl.innerText = formatNum(freeMotos);
        const totalMotosEl = document.getElementById('stat-free-motos-total');
        if (totalMotosEl) totalMotosEl.innerText = `Tot. Disp. ${formatNum(capMotos)}`;
        const barFreeMotos = document.getElementById('bar-free-motos');
        if (barFreeMotos) barFreeMotos.style.width = `${(freeMotos / capMotos) * 100}%`;

        // CAMIONETAS
        const freeCamionetasEl = document.getElementById('stat-free-camionetas');
        if (freeCamionetasEl) freeCamionetasEl.innerText = formatNum(freeCamionetas);
        const totalCamionetasEl = document.getElementById('stat-free-camionetas-total');
        if (totalCamionetasEl) totalCamionetasEl.innerText = `Tot. Disp. ${formatNum(capCamionetas)}`;
        const barFreeCamionetas = document.getElementById('bar-free-camionetas');
        if (barFreeCamionetas) barFreeCamionetas.style.width = `${(freeCamionetas / capCamionetas) * 100}%`;

        // OCUPACION TOTAL Y KPI MOTO
        const occMotosEl = document.getElementById('occ-stat-motos');
        if (occMotosEl) occMotosEl.innerText = formatNum(occMotos);
    }

    const resFinance = await api.get('/reports/financial-summary?period=day');
    if (resFinance && resFinance.ok) {
        const entriesEl = document.getElementById('stat-entries');
        const moneyEl = document.getElementById('stat-money');
        if (entriesEl) entriesEl.innerText = formatNum(resFinance.data.cantidad_pagos);
        if (moneyEl) moneyEl.innerText = `$${resFinance.data.total_recaudado.toLocaleString('es-AR')}`;
    }
}

let fullLogsData = [];
let filteredLogsData = [];
let currentPageLogs = 1;
const itemsPerPageLogs = 10;
let currentLogsSearchQuery = '';

export async function loadRecentLogs() {
    const res = await api.get('/reports/access');
    if (!res || !res.ok) return;

    fullLogsData = res.data;
    
    // ACTUALIZAR PATENTES EN TIEMPO REAL (CAJAS DE CAMARA)
    const lastEntry = fullLogsData.find(l => l.tipo_evento === 'ENTRADA');
    const lastExit = fullLogsData.find(l => l.tipo_evento === 'SALIDA');

    const updateCameraDisplay = (log, type) => {
        const plateFooterEl = document.getElementById(`plate-${type}`);
        const overlayEl = document.getElementById(`overlay-plate-${type}`);
        const camBox = document.getElementById(`cam-box-${type}`);
        
        if (log) {
            const plate = formatPlate(log.patente_detectada);
            
            // 1. ACTUALIZAR FOOTER (PERSISTENTE)
            if (plateFooterEl) plateFooterEl.innerText = plate;

            // 2. MANEJAR OVERLAY INTERNO (PERSISTENTE EN ESQUINA)
            if (overlayEl) {
                const overlayValue = overlayEl.querySelector('.overlay-value');
                const lastPlate = overlayEl.getAttribute('data-last-plate');

                // SIEMPRE MOSTRAR LA ULTIMA DETECTADA
                if (overlayValue) overlayValue.innerText = plate;
                overlayEl.classList.add('active');

                // SI ES UNA PATENTE NUEVA, DISPARAR ANIMACION DE DETECCION
                if (plate !== lastPlate) {
                    overlayEl.setAttribute('data-last-plate', plate);
                    
                    if (camBox) {
                        camBox.classList.add('detecting');
                        setTimeout(() => camBox.classList.remove('detecting'), 3000);
                    }
                }
            }
        }
    };

    updateCameraDisplay(lastEntry, 'entry');
    updateCameraDisplay(lastExit, 'exit');

    applyLogsFilter();
}

function applyLogsFilter() {
    if (!currentLogsSearchQuery) {
        filteredLogsData = [...fullLogsData];
    } else {
        const q = currentLogsSearchQuery.toLowerCase();
        filteredLogsData = fullLogsData.filter(log => 
            log.patente_detectada.toLowerCase().includes(q) || 
            log.tipo_evento.toLowerCase().includes(q)
        );
    }
    
    const totalPages = Math.ceil(filteredLogsData.length / itemsPerPageLogs);
    if (currentPageLogs > totalPages) currentPageLogs = 1;
    if (currentPageLogs === 0 && totalPages > 0) currentPageLogs = 1;

    renderLogsTable();
}

export function renderLogsTable() {
    const tbody = document.getElementById('live-logs');
    if (!tbody) return;

    const start = (currentPageLogs - 1) * itemsPerPageLogs;
    const end = start + itemsPerPageLogs;
    const paginatedData = filteredLogsData.slice(start, end);

    tbody.innerHTML = paginatedData.map(log => {
        const time = new Date(log.fecha_hora).toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' });
        const badgeClass = log.tipo_evento === 'ENTRADA' ? 'text-secondary' : 'text-danger';
        const statusBadge = log.pago_confirmado ? 
            `<span class="badge badge-success-light">PAGADO</span>` : 
            `<span class="badge badge-danger-light">PENDIENTE</span>`;

        return `
            <tr class="row-animate">
                <td data-label="Hora" class="text-center">${time}</td>
                <td data-label="Patente" class="text-center"><span class="plate-style">${formatPlate(log.patente_detectada)}</span></td>
                <td data-label="Evento" class="${badgeClass} text-bold text-center">${log.tipo_evento}</td>
                <td data-label="Abono" class="text-center">${statusBadge}</td>
                <td data-label="Info" class="text-center"><button class="btn-edit" onclick="showLogDetail(${log.id})" title="Ver detalle y captura del evento"><i class="fas fa-eye"></i></button></td>
            </tr>`;
    }).join('') || '<tr><td colspan="5" class="text-center py-20">No hay movimientos.</td></tr>';

    renderLogsPagination();
}

function renderLogsPagination() {
    const totalPages = Math.ceil(filteredLogsData.length / itemsPerPageLogs);
    const container = document.getElementById('logs-pagination');
    
    if (!container) return;
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }

    let html = `
        <button class="btn-icon-premium sm" ${currentPageLogs === 1 ? 'disabled' : ''} onclick="changePageLogs(${currentPageLogs - 1})">
            <i class="fas fa-chevron-left"></i>
        </button>
        <span class="text-xs text-light flex items-center px-10">Página ${currentPageLogs} de ${totalPages}</span>
        <button class="btn-icon-premium sm" ${currentPageLogs === totalPages ? 'disabled' : ''} onclick="changePageLogs(${currentPageLogs + 1})">
            <i class="fas fa-chevron-right"></i>
        </button>
    `;
    container.innerHTML = html;
}

window.changePageLogs = (page) => {
    currentPageLogs = page;
    renderLogsTable();
};

window.filterLogs = (query) => {
    currentLogsSearchQuery = query;
    currentPageLogs = 1;
    applyLogsFilter();
};

let fullOccupancyData = [];
let filteredOccupancyData = [];
let currentPageOcc = 1;
const itemsPerPageOcc = 10;
let currentSearchQuery = '';

export async function loadOccupancy() {
    const res = await api.get('/parking/current-occupancy');
    const resBranches = await api.get('/parking/branches');
    
    if (res.ok) {
        fullOccupancyData = res.data;
        
        // 1. MANEJO DE PISOS EN EL FORMULARIO MANUAL
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

        applyOccupancyFilter();

        const countEl = document.getElementById('occ-stat-count');
        const motosEl = document.getElementById('occ-stat-motos');
        const debtEl = document.getElementById('occ-stat-debt');
        
        let totalDebt = fullOccupancyData.reduce((acc, curr) => acc + (curr.deuda || 0), 0);
        
        if (countEl) countEl.innerText = formatNum(fullOccupancyData.filter(v => v.tipo_vehiculo !== 'Moto').length);
        if (motosEl) motosEl.innerText = formatNum(fullOccupancyData.filter(v => v.tipo_vehiculo === 'Moto').length);
        if (debtEl) debtEl.innerText = `$${totalDebt.toLocaleString('es-AR')}`;
    }
}

function applyOccupancyFilter() {
    if (!currentSearchQuery) {
        filteredOccupancyData = [...fullOccupancyData];
    } else {
        const q = currentSearchQuery.toLowerCase();
        filteredOccupancyData = fullOccupancyData.filter(occ => 
            occ.patente.toLowerCase().includes(q) || 
            (occ.floor_nombre && occ.floor_nombre.toLowerCase().includes(q))
        );
    }
    
    // SI LA PAGINA ACTUAL QUEDA FUERA DE RANGO TRAS FILTRAR, VOLVEMOS A LA 1
    const totalPages = Math.ceil(filteredOccupancyData.length / itemsPerPageOcc);
    if (currentPageOcc > totalPages) currentPageOcc = 1;
    if (currentPageOcc === 0 && totalPages > 0) currentPageOcc = 1;

    renderOccupancyTable();
}

export function renderOccupancyTable() {
    const tbody = document.getElementById('occ-list');
    if (!tbody) return;

    const start = (currentPageOcc - 1) * itemsPerPageOcc;
    const end = start + itemsPerPageOcc;
    const paginatedData = filteredOccupancyData.slice(start, end);
    const now = new Date();

    tbody.innerHTML = paginatedData.map(occ => {
        const date = new Date(occ.ingreso);
        const diffMs = now - date;
        const duration = `${Math.floor(diffMs / 3600000)}h ${Math.floor((diffMs % 3600000) / 60000)}m`;

        const statusBadge = occ.ya_pago ? 
            `<span class="text-secondary text-bold">PAGADO</span>` :
            `<span class="text-danger text-bold">$${occ.deuda.toLocaleString('es-AR')}</span>`;

        const floorInfo = occ.floor_nombre ? `<div class="text-xs text-muted mt-2">${occ.floor_nombre}</div>` : '';

        return `
        <tr class="row-animate">
            <td data-label="Vehículo" class="text-center">
                <div class="flex-col items-center">
                    <span class="plate-style">${formatPlate(occ.patente)}</span>
                    ${floorInfo}
                </div>
            </td>
            <td data-label="Ingreso" class="text-center">${date.toLocaleTimeString('es-AR', { hour: '2-digit', minute: '2-digit' })}</td>
            <td data-label="Permanencia" class="text-bold text-light text-center">${duration}</td>
            <td data-label="Deuda" class="text-center">${statusBadge}</td>
            <td data-label="Acciones" class="text-center">
                <div class="flex-row gap-5 justify-center">
                    ${!occ.ya_pago ? `<button class="btn-icon-premium sm" onclick="payOccupancy('${occ.patente}', ${formatNum(occ.deuda)})" title="Registrar pago de estadía"><i class="fas fa-cash-register"></i></button>` : ''}
                    <button class="btn-icon-premium sm warning" onclick="manualExit('${occ.patente}', '${occ.tipo_vehiculo}')" title="Registrar salida manual de vehículo"><i class="fas fa-door-open"></i></button>
                    ${(!(occ.reserva && occ.reserva.tipo_estadia && occ.reserva.estado_pago) || !(occ.reserva.tipo_estadia !== 'hora' && occ.reserva.estado_pago === 'Pagado')) ? `<button class="btn-icon-premium sm danger" onclick="cancelStay('${occ.patente}', '${occ.tipo_vehiculo}', ${formatNum(occ.deuda)}, '${occ.ingreso}')" title="Cancelar estadía (Cortesía 10 min)"><i class="fas fa-times"></i></button>` : ''}
                </div>
            </td>
        </tr>`;
    }).join('') || '<tr><td colspan="5" class="text-center py-20">Sin vehículos.</td></tr>';

    renderOccupancyPagination();
}

function renderOccupancyPagination() {
    const totalPages = Math.ceil(filteredOccupancyData.length / itemsPerPageOcc);
    const containers = [document.getElementById('occ-pagination'), document.getElementById('occ-pagination-tab')];
    
    containers.forEach(container => {
        if (!container) return;
        if (totalPages <= 1) {
            container.innerHTML = '';
            return;
        }

        let html = `
            <button class="btn-icon-premium sm" ${currentPageOcc === 1 ? 'disabled' : ''} onclick="changePageOcc(${currentPageOcc - 1})">
                <i class="fas fa-chevron-left"></i>
            </button>
            <span class="text-xs text-light flex items-center px-10">Página ${currentPageOcc} de ${totalPages}</span>
            <button class="btn-icon-premium sm" ${currentPageOcc === totalPages ? 'disabled' : ''} onclick="changePageOcc(${currentPageOcc + 1})">
                <i class="fas fa-chevron-right"></i>
            </button>
        `;
        container.innerHTML = html;
    });
}

window.changePageOcc = (page) => {
    currentPageOcc = page;
    renderOccupancyTable();
};

window.filterOccupancy = (query) => {
    currentSearchQuery = query;
    currentPageOcc = 1;
    applyOccupancyFilter();
};



export async function cancelStay(plate, type, debt, ingreso) {
    const { showConfirm, showToast, formatPlate } = await import('./utils.js');
    
    // CALCULAR SI ESTA EN CORTESIA (10 MIN) PARA MOSTRAR DEUDA 0 EN EL MENSAJE
    const entryDate = new Date(ingreso);
    const minutesElapsed = (new Date() - entryDate) / 60000;
    const displayDebt = minutesElapsed <= 10 ? 0 : debt;

    // CONFIRMACION MEDIANTE ALERTA PREMIUM (ESTILO UNIFICADO)
    const confirmed = await showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-dorado" style="letter-spacing: 1px;">
                ${formatPlate(plate)}
            </div>
            <div style="text-transform: uppercase;">
                TIPO: ${type || 'AUTO'}
            </div>
            <div class="${displayDebt === 0 ? 'text-secondary' : 'text-danger'}" style="font-size: 1.1rem;">
                DEUDA: $${(displayDebt || 0).toLocaleString('es-AR')}
            </div>
            <div style="opacity: 0.9; margin-top: 5px; font-size: 1.1rem;">
                ¿Confirmar la cancelación?
            </div>
            <div style="font-size: 0.75rem; font-weight: 400; color: var(--blanco); margin-top: 5px;">
                Cortesía de 10 min sin cargo.
            </div>
        </div>`
    );

    if (!confirmed) return;

    const res = await api.post(`/admin/cancel-stay?plate=${plate}`);
    if (res.ok) {
        showToast(res.data.message, 'success');
        loadOccupancy();
        loadLiveStats();
    } else {
        showToast(res.error, 'error');
    }
}
