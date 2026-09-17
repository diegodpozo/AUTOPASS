import api from './api.js';
import { formatDate, formatPlate, formatNum, toTitle, formatTime } from './utils.js';
import { getVirtualNow } from './virtual-time.js';

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
        
        // REFRESCAR COMPONENTES CLAVE
        loadLiveStats();
        loadRecentLogs();
        loadOccupancy();
        if (typeof window.loadAdminTickets === 'function') {
            window.loadAdminTickets();
        }
        if (typeof window.updateReservationBadge === 'function') {
            window.updateReservationBadge();
        }
        const activeTab = localStorage.getItem('activeAdminTab');
        if (activeTab === 'admin-reservations' && typeof window.loadAdminReservations === 'function') {
            window.loadAdminReservations();
        }
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
    // STATUS Y RESUMEN FINANCIERO EN PARALELO (2 RTT ANTES EN SERIE)
    const [resStatus, resFinance] = await Promise.all([
        api.get('/parking/status'),
        api.get('/reports/financial-summary?period=day'),
    ]);

    if (resStatus && resStatus.ok) {
        const { 
            disponibilidad: free, ocupacion_actual: occupied, capacidad_total: total, 
            ocupacion_motos: occMotos, capacidad_motos: capMotos, disponibilidad_motos: freeMotos, 
            disponibilidad_camionetas: freeCamionetas, capacidad_camionetas: capCamionetas, ocupacion_camionetas: occCamionetas, 
            disponibilidad_reservas: freeReservas, capacidad_reservas: capReservas, ocupacion_reservas: occReservas,
            disponibilidad_reservas_autos: freeResAutos, capacidad_reservas_autos: capResAutos, ocupacion_reservas_autos: occResAutos,
            disponibilidad_reservas_motos: freeResMotos, capacidad_reservas_motos: capResMotos, ocupacion_reservas_motos: occResMotos,
            disponibilidad_reservas_camionetas: freeResCamionetas, capacidad_reservas_camionetas: capResCamionetas, ocupacion_reservas_camionetas: occResCamionetas
        } = resStatus.data;

        // HELPER PARA COLOR DE BARRA SEGUN DISPONIBILIDAD
        function setBarFill(bar, pct) {
            bar.style.width = `${pct}%`;
            bar.className = 'progress-fill';
            if (pct <= 10) bar.classList.add('danger');
            else if (pct <= 25) bar.classList.add('orange');
            else if (pct <= 50) bar.classList.add('warning');
        }

        // AUTOS
        const freeEl = document.getElementById('stat-free');
        const totalEl = document.getElementById('stat-total');
        if (freeEl) freeEl.innerText = formatNum(free);
        if (totalEl) totalEl.innerText = formatNum(total);
        const freeTotalEl = document.getElementById('stat-free-total');
        if (freeTotalEl) freeTotalEl.innerText = `${formatNum(free)} / ${formatNum(total)}`;
        const resAutosValEl = document.getElementById('stat-res-autos-val');
        if (resAutosValEl) resAutosValEl.innerText = `${formatNum(freeResAutos ?? 0)} / ${formatNum(capResAutos ?? 0)}`;
        const barFree = document.getElementById('bar-free');
        if (barFree) setBarFill(barFree, total > 0 ? (free / total) * 100 : 0);

        // MOTOS
        const freeMotosEl = document.getElementById('stat-free-motos');
        const totalMotosEl = document.getElementById('stat-total-motos');
        if (freeMotosEl) freeMotosEl.innerText = formatNum(freeMotos);
        if (totalMotosEl) totalMotosEl.innerText = formatNum(capMotos);
        const freeTotalMotosEl = document.getElementById('stat-free-total-motos');
        if (freeTotalMotosEl) freeTotalMotosEl.innerText = `${formatNum(freeMotos)} / ${formatNum(capMotos)}`;
        const resMotosValEl = document.getElementById('stat-res-motos-val');
        if (resMotosValEl) resMotosValEl.innerText = `${formatNum(freeResMotos ?? 0)} / ${formatNum(capResMotos ?? 0)}`;
        const barFreeMotos = document.getElementById('bar-free-motos');
        if (barFreeMotos) setBarFill(barFreeMotos, capMotos > 0 ? (freeMotos / capMotos) * 100 : 0);

        // CAMIONETAS
        const freeCamionetasEl = document.getElementById('stat-free-camionetas');
        const totalCamionetasEl = document.getElementById('stat-total-camionetas');
        if (freeCamionetasEl) freeCamionetasEl.innerText = formatNum(freeCamionetas);
        if (totalCamionetasEl) totalCamionetasEl.innerText = formatNum(capCamionetas);
        const freeTotalCamionetasEl = document.getElementById('stat-free-total-camionetas');
        if (freeTotalCamionetasEl) freeTotalCamionetasEl.innerText = `${formatNum(freeCamionetas)} / ${formatNum(capCamionetas)}`;
        const resCamionetasValEl = document.getElementById('stat-res-camionetas-val');
        if (resCamionetasValEl) resCamionetasValEl.innerText = `${formatNum(freeResCamionetas ?? 0)} / ${formatNum(capResCamionetas ?? 0)}`;
        const barFreeCamionetas = document.getElementById('bar-free-camionetas');
        if (barFreeCamionetas) setBarFill(barFreeCamionetas, capCamionetas > 0 ? (freeCamionetas / capCamionetas) * 100 : 0);

        // RESERVAS EXCLUSIVAS (SI EXISTE VISTA LEGACY)
        const fReservas = freeReservas ?? Math.max(0, (capReservas || 0) - (occReservas || 0));
        const cReservas = capReservas ?? 0;
        const freeReservasEl = document.getElementById('stat-free-reservas');
        const totalReservasEl = document.getElementById('stat-total-reservas');
        if (freeReservasEl) freeReservasEl.innerText = formatNum(fReservas);
        if (totalReservasEl) totalReservasEl.innerText = formatNum(cReservas);
        const freeTotalReservasEl = document.getElementById('stat-free-total-reservas');
        if (freeTotalReservasEl) freeTotalReservasEl.innerText = `${formatNum(fReservas)} / ${formatNum(cReservas)}`;
        const barFreeReservas = document.getElementById('bar-free-reservas');
        if (barFreeReservas) setBarFill(barFreeReservas, cReservas > 0 ? (fReservas / cReservas) * 100 : 0);

        const subResAutosEl = document.getElementById('stat-sub-res-autos');
        if (subResAutosEl) subResAutosEl.innerText = `A: ${freeResAutos ?? 0}/${capResAutos ?? 0}`;
        const subResMotosEl = document.getElementById('stat-sub-res-motos');
        if (subResMotosEl) subResMotosEl.innerText = `M: ${freeResMotos ?? 0}/${capResMotos ?? 0}`;
        const subResCamionetasEl = document.getElementById('stat-sub-res-camionetas');
        if (subResCamionetasEl) subResCamionetasEl.innerText = `C: ${freeResCamionetas ?? 0}/${capResCamionetas ?? 0}`;

        // OCUPACION TOTAL Y KPI MOTO
        const occMotosEl = document.getElementById('occ-stat-motos');
        if (occMotosEl) occMotosEl.innerText = formatNum(occMotos);
    }

    const entriesEl = document.getElementById('stat-entries');
    const moneyEl = document.getElementById('stat-money');
    if (entriesEl) entriesEl.innerText = formatNum(resFinance.data.cantidad_pagos);
    if (moneyEl) moneyEl.innerText = `$${formatNum(resFinance.data.total_recaudado)}`;
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
        const fecha = new Date(log.fecha_hora);
        const time = formatTime(fecha);
        const day = fecha.toLocaleDateString('es-AR', { day: '2-digit', month: '2-digit' });
        const badgeClass = log.tipo_evento === 'ENTRADA' ? 'text-secondary' : 'text-danger';
        const statusBadge = log.pago_confirmado 
            ? `<span class="badge badge-success-light">PAGADO</span>` 
            : log.tipo_evento === 'SALIDA'
                ? `<span class="badge" style="background: rgba(197,160,89,0.15); color: var(--dorado); border: 1px solid rgba(197,160,89,0.3); font-size:0.65rem; font-weight:800; padding:4px 10px; border-radius:8px; letter-spacing:0.5px;">CORTESÍA</span>`
                : `<span class="badge badge-danger-light">PENDIENTE</span>`;

        return `
            <tr class="row-animate">
                <td data-label="Hora" class="text-center">
                    <div class="flex-col items-center" style="gap: 2px;">
                        <span class="text-bold text-light">${time}</span>
                        <span class="text-xs text-muted">${day}</span>
                    </div>
                </td>
                <td data-label="Patente" class="text-center"><span class="plate-style">${formatPlate(log.patente_detectada)}</span></td>
                <td data-label="Evento" class="${badgeClass} text-bold text-center">${log.tipo_evento}</td>
                <td data-label="Abono" class="text-center">${statusBadge}</td>
                <td data-label="Info" class="text-center"><div style="display: flex; justify-content: center;"><button class="btn-edit" style="cursor: pointer;" onclick="showLogDetail(${log.id})" title="Ver detalle y captura del evento"><i class="fas fa-eye"></i></button></div></td>
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

export function changePageLogs(page) {
    currentPageLogs = page;
    renderLogsTable();
}

export function filterLogs(query) {
    currentLogsSearchQuery = query;
    currentPageLogs = 1;
    applyLogsFilter();
}

let fullOccupancyData = [];
let filteredOccupancyData = [];
let currentPageOcc = 1;
const itemsPerPageOcc = 10;
let currentSearchQuery = '';

export async function loadOccupancy() {
    // OCUPACION Y SUCURSALES EN PARALELO (2 RTT ANTES EN SERIE)
    const [res, resBranches] = await Promise.all([
        api.get('/parking/current-occupancy'),
        api.get('/parking/branches'),
    ]);
    
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
        if (debtEl) debtEl.innerText = `$${formatNum(totalDebt)}`;
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
    const html = buildOccupancyRows();
    const tbodies = [document.getElementById('occ-list'), document.getElementById('occ-list-tab')];
    tbodies.forEach(el => { if (el) el.innerHTML = html; });
    renderOccupancyPagination();
    if (document.querySelectorAll('[data-cortesia-ingreso]').length > 0) {
        startCortesiaTimer();
    }
}

let cortesiaTimer = null;

function getCortesiaRemainingMs(ingreso) {
    const entryDate = new Date(ingreso);
    const elapsedMs = getVirtualNow() - entryDate;
    return Math.max(0, 10 * 60 * 1000 - elapsedMs);
}

function formatCortesiaTimer(ms) {
    if (ms <= 0) return null;
    const totalSec = Math.ceil(ms / 1000);
    const min = Math.floor(totalSec / 60);
    const sec = totalSec % 60;
    return `${String(min).padStart(2, '0')}:${String(sec).padStart(2, '0')}`;
}

function startCortesiaTimer() {
    if (cortesiaTimer) return;
    cortesiaTimer = setInterval(() => {
        const badges = document.querySelectorAll('[data-cortesia-ingreso]');
        let anyActive = false;
        badges.forEach(el => {
            const ingreso = el.getAttribute('data-cortesia-ingreso');
            const remaining = getCortesiaRemainingMs(ingreso);
            const timeStr = formatCortesiaTimer(remaining);
            if (timeStr) {
                el.textContent = timeStr;
                anyActive = true;
            } else {
                renderOccupancyTable();
                anyActive = false;
            }
        });
        if (!anyActive && cortesiaTimer) {
            clearInterval(cortesiaTimer);
            cortesiaTimer = null;
        }
    }, 1000);
}

function buildOccupancyRows() {
    const start = (currentPageOcc - 1) * itemsPerPageOcc;
    const end = start + itemsPerPageOcc;
    const paginatedData = filteredOccupancyData.slice(start, end);
    const now = getVirtualNow();

    return paginatedData.map(occ => {
        const date = new Date(occ.ingreso);
        const diffMs = now - date;
        const duration = `${Math.floor(diffMs / 3600000)}h ${Math.floor((diffMs % 3600000) / 60000)}m`;

        const statusBadge = occ.ya_pago ?
            `<span class="text-secondary text-bold">PAGADO</span>` :
            occ.en_cortesia ?
                `<span class="text-bold" style="color: #10b981;" data-cortesia-ingreso="${occ.ingreso}">${formatCortesiaTimer(getCortesiaRemainingMs(occ.ingreso)) || '00:00'}</span>` :
                `<span class="text-danger text-bold">$${formatNum(occ.deuda)}</span>`;

        const floorInfo = occ.floor_nombre ? `<div class="text-xs text-muted mt-2">${occ.floor_nombre}</div>` : '';

        const vehicleTypeIcon = {
            'Auto': 'fa-car',
            'Moto': 'fa-motorcycle',
            'Camioneta': 'fa-truck-pickup'
        }[occ.tipo_vehiculo] || 'fa-car';

        const reservaBadge = occ.es_reserva && occ.reserva && occ.reserva.tipo_estadia
            ? `<span class="badge-status badge-activa"><i class="fas fa-calendar-check"></i> ${toTitle(occ.reserva.tipo_estadia)}</span>`
            : `<span class="text-secondary text-bold text-xs">SIN RESERVA</span>`;

        return `
        <tr class="row-animate">
            <td data-label="Vehículo" class="text-center">
                <div class="flex-col items-center">
                    <span class="plate-style">${formatPlate(occ.patente)}</span>
                    ${floorInfo}
                </div>
            </td>
            <td data-label="Tipo" class="text-center">
                <span class="text-bold text-light text-xs" style="display: inline-flex; align-items: center; gap: 6px; white-space: nowrap;">
                    <i class="fas ${vehicleTypeIcon}" style="color: var(--dorado);"></i>
                    ${toTitle(occ.tipo_vehiculo)}
                </span>
            </td>
            <td data-label="Reserva" class="text-center">${reservaBadge}</td>
            <td data-label="Ingreso" class="text-center">${formatTime(date)}</td>
            <td data-label="Permanencia" class="text-bold text-light text-center">${duration}</td>
            <td data-label="Deuda" class="text-center">${statusBadge}</td>
            <td data-label="Acciones" class="text-center">
                <div class="flex-row gap-5 justify-center">
                    ${(!occ.ya_pago && !occ.en_cortesia) ? `<button class="btn-icon-premium sm" onclick="payOccupancy('${occ.patente}', ${occ.deuda})" title="Registrar pago de estadía"><i class="fas fa-dollar-sign"></i></button>` : ''}
                    <button class="btn-icon-premium sm warning" onclick="manualExit('${occ.patente}', '${occ.tipo_vehiculo}')" title="Registrar salida manual de vehículo"><i class="fas fa-arrow-right-from-bracket"></i></button>
                    ${(!(occ.reserva && occ.reserva.tipo_estadia && occ.reserva.estado_pago) || !(occ.reserva.tipo_estadia !== 'hora' && occ.reserva.estado_pago === 'Pagado')) ? `<button class="btn-icon-premium sm danger" onclick="cancelStay('${occ.patente}', '${occ.tipo_vehiculo}', ${formatNum(occ.deuda)}, '${occ.ingreso}')" title="Cancelar estadía (Cortesía 10 min)"><i class="fas fa-times"></i></button>` : ''}
                </div>
            </td>
        </tr>`;
    }).join('') || '<tr><td colspan="7" class="text-center py-20">Sin vehículos.</td></tr>';
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

export function changePageOcc(page) {
    currentPageOcc = page;
    renderOccupancyTable();
}

export function filterOccupancy(query) {
    currentSearchQuery = query;
    currentPageOcc = 1;
    applyOccupancyFilter();
}



export async function cancelStay(plate, type, debt, ingreso) {
    const { showConfirm, showToast, formatPlate } = await import('./utils.js');
    
    // CALCULAR SI ESTA EN CORTESIA (10 MIN) PARA MOSTRAR DEUDA 0 EN EL MENSAJE
    const entryDate = new Date(ingreso);
    const minutesElapsed = (getVirtualNow() - entryDate) / 60000;
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
                DEUDA: $${formatNum(displayDebt || 0)}
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
