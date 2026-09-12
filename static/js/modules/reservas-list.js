import api from './api.js';
import { toTitle, formatDate, formatPlate, formatNum } from './utils.js';
import { getVirtualNow } from './virtual-time.js';

/**
 * MÓDULO RESERVAS - LISTADO E HISTORIAL
 * Manejo de la lista de reservas activas, pendientes, tarjetas visuales e historial con paginación.
 */

let historialCurrentPage = 1;
const HISTORIAL_PAGE_SIZE = 5;
let historyData = [];

export function getHistoryData() {
    return historyData;
}

export async function loadReservations() {
    const res = await api.get('/user/reservations');
    if (!res.ok) return;
    
    const all = res.data;
    const active = all.filter(r => r.estado_reserva === 'Pendiente' || r.estado_reserva === 'Activa');
    historyData = all.filter(r => r.estado_reserva !== 'Pendiente' && r.estado_reserva !== 'Activa');
    
    const now = getVirtualNow();
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
    const now = getVirtualNow();
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
                    ${r.en_predio ? '<span class="status-badge-ultra" style="background:rgba(16,185,129,0.12);color:#10b981;border:1px solid #10b981;"><i class="fas fa-circle-dot"></i> EN PREDIO</span>' : ''}
                </div>
            </div>
            <div class="reserva-status-ultra">
                <div class="status-badge-ultra ${r.estado_pago.toLowerCase()}">${r.estado_pago}</div>
                <div class="price-container-ultra"><span class="price-value-ultra">$${formatNum((r.monto_total || 0) - (r.monto_reembolsado || 0))}</span></div>
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
            <button class="btn-ultra btn-ultra-primary" onclick="showDigitalPass(${r.id})"><i class="fas fa-ticket"></i> VER COMPROBANTE + QR</button>
            ${r.estado_pago === 'Pendiente' && r.estado_reserva !== 'Cancelada' ? `
            <button class="btn-ultra btn-ultra-mp" onclick="payReservationWithMp(${r.id})"><i class="fab fa-google-pay"></i> PAGAR CON MP</button>` : ''}
            <button class="btn-ultra btn-ultra-secondary" onclick="prepareEditReservation(${r.id})" ${isStarted || r.estado_reserva === 'Activa' ? 'disabled' : ''}><i class="fas fa-pen"></i></button>
            <button class="btn-ultra btn-ultra-danger" onclick="cancelReservation(${r.id})" ${r.estado_reserva === 'Cancelada' || r.estado_reserva === 'Fallido' ? 'disabled' : ''}><i class="fas fa-trash"></i></button>
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
            <div class="hist-amount-info">
                <span class="hist-value">$${formatNum((r.monto_total || 0) - (r.monto_reembolsado || 0))}</span>
                <div class="status-pill ${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</div>
            </div>
            <div class="hist-actions-group"><button class="btn-repeat-express" onclick="repeatReservation('${r.patente}','${r.sucursal_nombre}','${r.tipo_estadia}')"><i class="fas fa-rotate-right"></i></button></div>
        </div>`).join('');

    if (document.getElementById('historial-page-info')) document.getElementById('historial-page-info').innerText = `Página ${historialCurrentPage} de ${totalPages || 1}`;
    const prevBtn = document.getElementById('historial-prev'); if (prevBtn) prevBtn.disabled = historialCurrentPage === 1;
    const nextBtn = document.getElementById('historial-next'); if (nextBtn) nextBtn.disabled = historialCurrentPage >= totalPages;
}

export function historialPage(dir) { 
    historialCurrentPage += dir; 
    applyHistoryFilters(); 
}

export function resetHistoryFilters() {
    const f1 = document.getElementById('history-filter-from'); if (f1) f1.value = '';
    const f2 = document.getElementById('history-filter-to'); if (f2) f2.value = '';
    applyHistoryFilters();
}
