import api from './api.js';
import * as utils from './utils.js';
import * as baseUi from './ui.js';
import { getVirtualNow } from './virtual-time.js';
import { renderCappedList } from './list-pagination.js';

/**
 * Módulo de Gestión de Reservas Administrativas
 */

let allReservations = [];
let resBadgeInterval = null;

export function getAllReservations() {
    return allReservations;
}

export async function loadAdminReservations() {
    const status = document.getElementById('admin-res-filter-status')?.value || '';
    const res = await api.get(`/admin/reservations?estado=${status}`);
    
    if (res.ok) {
        const tbody = document.getElementById('admin-res-list');
        if (!tbody) return;
        
allReservations = res.data;

        if (allReservations.length > 0 && allReservations[0].id) {
            const storageKey = getStorageKey();
            const currentLastSeen = parseInt(localStorage.getItem(storageKey), 10) || 0;
            if (allReservations[0].id > currentLastSeen) {
                localStorage.setItem(storageKey, allReservations[0].id);
            }
        }

        const rowsHtml = allReservations.map(r => `
            <tr class="row-premium">
                <td data-label="Cliente"><div class="user-name">${r.usuario_nombre || 'S/N'} ${r.usuario_apellido || ''}</div></td>
                <td data-label="Patente"><span class="plate-style">${utils.formatPlate(r.patente)}</span></td>
                <td data-label="Fecha">
                    <div class="flex-col items-center gap-8">
                        <div class="text-small text-light">${utils.formatDate(r.fecha_inicio)}</div>
                        <div class="text-xs text-muted" style="border-top: 1px solid rgba(255,255,255,0.05); padding-top: 5px;">${utils.formatDate(r.fecha_fin)}</div>
                    </div>
                </td>
                <td data-label="Tipo">
                    <div class="flex-col items-center gap-8">
                        <div class="text-small text-dorado font-bold uppercase" style="letter-spacing: 1px;">${utils.toTitle(r.tipo_estadia)}</div>
                    </div>
                </td>
                <td data-label="Monto" class="text-bold text-white">
                    $${utils.formatNum((r.monto_total || 0) - (r.monto_reembolsado || 0))}
                    ${(r.monto_reembolsado || 0) > 0 ? `<div class="text-xs text-muted" style="border-top:1px solid rgba(255,255,255,0.05); margin-top:4px; padding-top:4px; text-align:center;">Pagado $${utils.formatNum(r.monto_total)} · Reemb. -$${utils.formatNum(r.monto_reembolsado)}</div>` : ''}
                </td>
                <td data-label="Estado Pago"><span class="badge-status badge-${r.estado_pago.toLowerCase()}">${r.estado_pago}</span></td>
                <td data-label="Estado Reserva">
                    <div class="flex-col items-center gap-8">
                        <span class="badge-status badge-${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</span>
                        ${r.estado_reserva !== 'Completada' && r.estado_reserva !== 'Cancelada'
                            ? (r.en_predio
                                ? '<span style="display:inline-flex; align-items:center; gap:6px; font-size:0.7rem; font-weight:700; color:#10b981;"><i class="fas fa-circle-dot"></i> EN PREDIO</span>'
                                : '<span style="display:inline-flex; align-items:center; gap:6px; font-size:0.7rem; font-weight:700; color:#8b93a6;"><i class="fas fa-circle" style="font-size:0.5rem;"></i> FUERA</span>')
                            : ''}
                    </div>
                </td>
                <td data-label="Acciones">
                    <div class="flex-row gap-8 justify-center actions-reveal">
                        ${r.estado_reserva !== 'Completada' && r.estado_reserva !== 'Cancelada' ? `
                        ${r.origen === 'manual' ? `
                        <button class="btn--icon sm" onclick="editReservationAdmin(${r.id})" title="Editar Reserva">
                            <i class="fas fa-pen"></i>
                        </button>
                        ` : ''}
                        ${r.estado_pago === 'Pendiente' ? `
                        <button class="btn--icon sm btn-confirm-payment" onclick="payReservationAdmin(${r.id})" title="Pago Manual">
                            <i class="fas fa-money-bill-wave"></i>
                        </button>
                        ` : ''}
                        <button class="btn--icon sm danger" onclick="cancelReservationAdmin(${r.id})" title="Cancelar Reserva">
                            <i class="fas fa-xmark"></i>
                        </button>
                        ` : `<span class="text-xs text-muted">—</span>`}
                    </div>
                </td>
            </tr>`);
        const drawList = () => renderCappedList(tbody, rowsHtml, {
            pageSize: 8,
            tag: 'tr',
            colspan: 8,
            toggleAll: total => `Ver todas las reservas (${total})`,
            toggleLess: 'Ver menos',
            onToggle: drawList
        });
        drawList();
        
        const statTotal = document.getElementById('admin-res-stat-total');
        const statPending = document.getElementById('admin-res-stat-pending');
        const statToday = document.getElementById('admin-res-stat-today');
        if (statTotal) statTotal.innerText = utils.formatNum(res.data.length);
        if (statPending) statPending.innerText = utils.formatNum(res.data.filter(r => r.estado_reserva === 'Pendiente').length);
        if (statToday) {
            const now = getVirtualNow();
            const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
            const todayEnd = new Date(now.getFullYear(), now.getMonth(), now.getDate(), 23, 59, 59);
            const countToday = res.data.filter(r => {
                if (r.estado_reserva === 'Completada' || r.estado_reserva === 'Cancelada') return false;
                const ini = new Date(String(r.fecha_inicio || '').replace(/-/g, '/'));
                const fin = new Date(String(r.fecha_fin || '').replace(/-/g, '/'));
                if (isNaN(ini.getTime()) || isNaN(fin.getTime())) return false;
                return ini <= todayEnd && fin >= todayStart;
            }).length;
            statToday.innerText = utils.formatNum(countToday);
        }
    }
}

export async function payReservationAdmin(resId) {
    const metodo = await utils.showChoice('Pago Manual', '¿Con qué método abonó el cliente?', [
        { label: 'Efectivo', icon: 'fa-money-bill-wave' },
        { label: 'Mercado Pago', icon: 'fa-wallet' },
        { label: 'Transferencia', icon: 'fa-building-columns' },
        { label: 'Tarjeta', icon: 'fa-credit-card' },
        { label: 'Otro', icon: 'fa-circle-question' }
    ]);
    if (!metodo) return;

    // DETECTAR DESCUENTO DE RESERVA VIGENTE DEL CLIENTE PARA APLICARLO EN CAJA
    let redemptionTicketId = null;
    const discsRes = await api.get(`/admin/reservations/${resId}/redemptions`);
    if (discsRes.ok && Array.isArray(discsRes.data) && discsRes.data.length > 0) {
        const d = discsRes.data[0];
        const aplicar = await utils.showConfirm('Descuento aplicable', `
            <div style="text-align:left; font-size:0.85rem; line-height:1.8;">
                <div style="display:flex; justify-content:space-between; gap:12px;"><span style="color:#aaa;">Monto reserva</span><b>$${utils.formatNum(d.monto)}</b></div>
                <div style="display:flex; justify-content:space-between; gap:12px; color:#c084fc;"><span><i class="fas fa-percent" style="margin-right:4px;"></i>Descuento ${d.valor_descuento}%</span><b>-$ ${utils.formatNum(d.descuento_peso)}</b></div>
                <div style="border-top:1px solid rgba(255,255,255,0.1); margin:8px 0 6px; padding-top:8px; display:flex; justify-content:space-between; gap:12px;"><span style="color:#aaa;">Total a cobrar</span><b style="font-size:1.05rem;">$${utils.formatNum(d.monto_final)}</b></div>
            </div>
        `);
        if (aplicar) redemptionTicketId = d.id;
    }

    const res = await api.post(`/admin/reservations/${resId}/confirm-payment`, { metodo_pago: metodo, redemption_ticket_id: redemptionTicketId });
    if (res.ok) {
        const msg = redemptionTicketId
            ? `Pago registrado (descuento aplicado: -$ ${utils.formatNum(res.data.descuento || 0)})`
            : 'Pago registrado correctamente';
        utils.showToast(msg, 'success');
        loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al registrar pago', 'error');
    }
}

export async function cancelReservationAdmin(resId) {
    if (!await utils.showConfirm('Cancelar Reserva', '¿Estás seguro de cancelar esta reserva?')) return;
    
    const res = await api.post(`/admin/reservations/${resId}/cancel`);
    if (res.ok) {
        utils.showToast(res.data.message || 'Reserva cancelada', 'success');
        loadAdminReservations();
    } else {
        utils.showToast(res.error || 'Error al cancelar reserva', 'error');
    }
}

export function showReservationDetail(resId) {
    const r = allReservations.find(x => x.id === resId);
    if (!r) return;

    document.getElementById('res-detail-id').innerText = `#${r.id}`;
    document.getElementById('res-detail-user').innerText = `${r.usuario_nombre || 'S/N'} ${r.usuario_apellido || ''}`;
    document.getElementById('res-detail-plate').innerText = utils.formatPlate(r.patente);
    document.getElementById('res-detail-start').innerText = utils.formatDate(r.fecha_inicio);
    document.getElementById('res-detail-end').innerText = utils.formatDate(r.fecha_fin);
    document.getElementById('res-detail-sucursal').innerText = r.sucursal_nombre;
    document.getElementById('res-detail-type').innerText = utils.toTitle(r.tipo_estadia);
    document.getElementById('res-detail-amount').innerText = `$${utils.formatNum((r.monto_total || 0) - (r.monto_reembolsado || 0))}`;

    const refundNote = document.getElementById('res-detail-amount-refund');
    if (refundNote) {
        if ((r.monto_reembolsado || 0) > 0) {
            refundNote.style.display = '';
            refundNote.innerText = `Pagado $${utils.formatNum(r.monto_total)} · Reembolsado -$${utils.formatNum(r.monto_reembolsado)}`;
        } else {
            refundNote.style.display = 'none';
        }
    }

    const badgeContainer = document.getElementById('res-detail-status-badges');
    if (badgeContainer) {
        badgeContainer.innerHTML = `
            <span class="badge-status badge-${r.estado_pago.toLowerCase()}">${r.estado_pago}</span>
            <span class="badge-status badge-${r.estado_reserva.toLowerCase()}">${r.estado_reserva}</span>
            ${r.estado_reserva !== 'Completada' && r.estado_reserva !== 'Cancelada'
                ? (r.en_predio
                    ? '<span style="display:inline-flex; align-items:center; gap:6px; font-size:0.72rem; font-weight:700; color:#10b981;"><i class="fas fa-circle-dot"></i> EN PREDIO</span>'
                    : '<span style="display:inline-flex; align-items:center; gap:6px; font-size:0.72rem; font-weight:700; color:#8b93a6;"><i class="fas fa-circle" style="font-size:0.5rem;"></i> FUERA DEL PREDIO</span>')
                : ''}
        `;
    }

    if (baseUi.openModal) baseUi.openModal('modal-res-detail');
}


function getStorageKey() {
    const scope = (localStorage.getItem('rol') || 'admin') + '_' + (localStorage.getItem('sucursal') || 'all');
    return 'autopass_last_seen_res_id_' + scope;
}

export async function updateReservationBadge() {
    const badge = document.getElementById('reservation-badge-sidebar');
    if (!badge) return;

    const activeTab = localStorage.getItem('activeAdminTab');
    const storageKey = getStorageKey();
    let lastSeenId = parseInt(localStorage.getItem(storageKey), 10);

    // Si el usuario está actualmente en la pestaña de reservas, ocultar badge y registrar latest_id
    if (activeTab === 'admin-reservations') {
        badge.style.display = 'none';
        badge.classList.remove('pulse');
        const res = await api.get('/admin/reservations/new-count');
        if (res && res.ok && res.data && res.data.latest_id !== undefined) {
            localStorage.setItem(storageKey, res.data.latest_id);
        }
        return;
    }

    // Primera vez en este navegador/sesión: inicializar con el ID actual para no mostrar reservas históricas
    if (isNaN(lastSeenId)) {
        const res = await api.get('/admin/reservations/new-count');
        if (res && res.ok && res.data && res.data.latest_id !== undefined) {
            localStorage.setItem(storageKey, res.data.latest_id);
        }
        badge.style.display = 'none';
        badge.classList.remove('pulse');
        return;
    }

    // Consultar cantidad de reservas nuevas desde lastSeenId
    const res = await api.get(`/admin/reservations/new-count?since_id=${lastSeenId}`);
    if (!res || !res.ok || !res.data) return;

    const count = res.data.count || 0;
    if (count > 0) {
        badge.style.display = 'inline-flex';
        badge.textContent = count > 99 ? '99+' : count;
        badge.classList.add('pulse');
    } else {
        badge.style.display = 'none';
        badge.classList.remove('pulse');
    }
}

export async function clearReservationBadge() {
    const badge = document.getElementById('reservation-badge-sidebar');
    if (badge) {
        badge.style.display = 'none';
        badge.classList.remove('pulse');
    }
    const storageKey = getStorageKey();
    try {
        const res = await api.get('/admin/reservations/new-count');
        if (res && res.ok && res.data && res.data.latest_id !== undefined) {
            localStorage.setItem(storageKey, res.data.latest_id);
        }
} catch (e) {
        console.error('[clearReservationBadge Error]', e);
    }
}

if (!resBadgeInterval) {
    resBadgeInterval = setInterval(() => {
        updateReservationBadge();
    }, 10000);
}
