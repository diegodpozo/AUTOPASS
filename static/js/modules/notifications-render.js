/**
 * AUTOPASS - RENDERIZADO DE NOTIFICACIONES
 * Submodulo de notifications.js: carga de la lista, filtros por tipo,
 * render del listado en el panel y actualizacion de los botones de accion.
 */

import api from './api.js';
import { notifState } from './notifications-state.js';
import { getNotifIcon, getNotifCategoryClass, getNotifActions, getTimeAgo } from './notifications-format.js';
import { renderCappedList, resetCappedState } from './list-pagination.js';

const NOTIF_PAGE_SIZE = 8;

export async function loadNotifications() {
    const container = document.getElementById('notifications-container');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Cargando notificaciones...</div>';

    const res = await api.get('/user/profile/notifications?limit=200');
    if (!res.ok) {
        container.innerHTML = '<div class="empty-state">Error al cargar notificaciones.</div>';
        return;
    }

    const { notifications } = res.data;
    notifState.cachedNotifications = notifications || [];

    resetCappedState(container);
    updateNotifActionButtonsState();
    renderNotificationList();
}

export function updateNotifActionButtonsState() {
    const hasUnread = notifState.cachedNotifications.some(n => !n.leido);
    const hasRead = notifState.cachedNotifications.some(n => n.leido);

    const markBtn = document.getElementById('btn-mark-all-read');
    if (markBtn) {
        markBtn.style.display = 'inline-flex';
        markBtn.disabled = !hasUnread;
    }

    const clearReadBtn = document.getElementById('btn-clear-read-notifs');
    if (clearReadBtn) {
        clearReadBtn.style.display = 'inline-flex';
        clearReadBtn.disabled = !hasRead;
    }
}

export function renderNotificationList() {
    const container = document.getElementById('notifications-container');
    if (!container) return;

    const filtered = filterNotificationsArray(notifState.cachedNotifications, notifState.currentFilter);

    let msg = 'No tenés notificaciones.';
    if (notifState.currentFilter === 'UNREAD') msg = 'No tenés notificaciones sin leer.';
    else if (notifState.currentFilter === 'RESERVATION') msg = 'No hay notificaciones de reservas.';
    else if (notifState.currentFilter === 'FINANCE') msg = 'No hay notificaciones de pagos o saldo.';
    else if (notifState.currentFilter === 'SUPPORT') msg = 'No hay notificaciones de soporte.';
    else if (notifState.currentFilter === 'SECURITY') msg = 'No hay notificaciones de seguridad.';

    const emptyHtml = `
            <div class="empty-state">
                <i class="fas fa-bell-slash" style="font-size: 3rem; color: var(--dorado); opacity:0.5; margin-bottom:15px;"></i>
                <p>${msg}</p>
            </div>`;

    const items = (filtered || []).map(n => {
        const isUnread = !n.leido;
        const timeAgo = getTimeAgo(n.created_at);
        const actions = getNotifActions(n);
        const catClass = getNotifCategoryClass(n.tipo);
        const iconClass = getNotifIcon(n.tipo);

        return `
            <div class="notif-item ${isUnread ? 'notif-unread' : ''} ${catClass}" data-id="${n.id}" ${isUnread ? `onclick="markNotifRead(${n.id}, this)"` : ''}>
                <div class="notif-icon-box ${catClass}">
                    <i class="fas ${iconClass}"></i>
                </div>
                <div class="notif-content">
                    <div class="notif-header-row">
                        <div class="notif-title">${n.titulo}</div>
                        <span class="notif-time">${timeAgo}</span>
                    </div>
                    <div class="notif-message">${n.mensaje}</div>
                    ${actions ? `<div class="notif-actions">${actions}</div>` : ''}
                </div>
                <div class="notif-side-actions">
                    ${isUnread ? `<span class="notif-unread-dot" title="Sin leer"></span>` : ''}
                    <button class="notif-delete-btn" onclick="deleteNotif(${n.id}, event, this)" title="Eliminar notificación">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>`;
    });

    renderCappedList(container, items, {
        pageSize: NOTIF_PAGE_SIZE,
        wrapperClass: 'notif-list',
        toggleAll: (total) => `Ver todas las notificaciones (${total})`,
        emptyHtml,
        onToggle: () => renderNotificationList()
    });
}

function filterNotificationsArray(list, filter) {
    if (!list) return [];
    if (filter === 'UNREAD') return list.filter(n => !n.leido);
    if (filter === 'RESERVATION') return list.filter(n => [
        'REMINDER_PAID', 'REMINDER_UNPAID', 'RESERVATION_STARTED',
        'AUTO_CANCELLED', 'RESERVATION_CONFIRMED', 'RESERVATION_CANCELLED',
        'RESERVATION_MODIFIED', 'RESERVATION_CREATED_ADMIN'
    ].includes(n.tipo));
    if (filter === 'FINANCE') return list.filter(n => [
        'BALANCE_RECHARGED', 'BALANCE_ADJUSTED_ADMIN', 'PROMO_REDEEMED',
        'PROMO_CANCELLED', 'POINTS_EARNED', 'STAY_PAID', 'STAY_CANCELLED_ADMIN'
    ].includes(n.tipo));
    if (filter === 'SUPPORT') return list.filter(n => [
        'SUPPORT_RESPONSE', 'SUPPORT_TICKET', 'SUPPORT_STATUS_CHANGED'
    ].includes(n.tipo));
    if (filter === 'SECURITY') return list.filter(n => [
        'NEW_DEVICE_LOGIN', 'PASSWORD_CHANGED_ADMIN', 'SECURITY_PASSWORD_CHANGED',
        'USER_PROFILE_UPDATED', 'USER_ROLE_CHANGED', 'USER_BLOCK_STATUS_CHANGED',
        'VEHICLE_REGISTERED', 'VEHICLE_REMOVED', 'VEHICLE_ENTRY', 'VEHICLE_EXIT'
    ].includes(n.tipo));
    return list;
}

export function filterNotifs(filterType, btn) {
    notifState.currentFilter = filterType;
    document.querySelectorAll('.notif-chip').forEach(c => c.classList.remove('active'));
    if (btn) btn.classList.add('active');
    resetCappedState(document.getElementById('notifications-container'));
    renderNotificationList();
};