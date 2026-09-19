/**
 * AUTOPASS - ACCIONES SOBRE NOTIFICACIONES
 * Submodulo de notifications.js: marcar leidas, marcar todas, eliminar,
 * borrar leidas y confirmar recordatorio de pago.
 */

import api from './api.js';
import { showToast, showConfirm } from './utils.js';
import { notifState } from './notifications-state.js';
import { updateNotifActionButtonsState, renderNotificationList } from './notifications-render.js';
import { updateNotifBadge } from './notifications-badge.js';

export async function markNotifRead(notifId, el) {
    el = el?.closest?.('.notif-item') || el;
    if (el && !el.classList.contains('notif-unread')) return;
    if (el) {
        el.classList.remove('notif-unread');
        const dot = el.querySelector('.notif-unread-dot');
        if (dot) dot.remove();
    }
    const target = notifState.cachedNotifications.find(n => n.id === notifId);
    if (target) target.leido = true;

    updateNotifActionButtonsState();
    updateNotifBadge();
    await api.patch(`/user/profile/notifications/${notifId}/read`);
}
export async function markAllNotifRead() {
    const res = await api.post('/user/profile/notifications/read-all');
    if (!res.ok) {
        console.error('[NOTIF READ ALL ERROR]', res);
        showToast(res.error || 'Error al marcar notificaciones', 'error');
        return;
    }
    notifState.cachedNotifications.forEach(n => n.leido = true);
    renderNotificationList();
    updateNotifActionButtonsState();
    updateNotifBadge();
    showToast('Todas las notificaciones marcadas como leídas', 'success');
}
export async function deleteNotif(notifId, e, btn) {
    if (e) e.stopPropagation();
    const res = await api.delete(`/user/profile/notifications/${notifId}`);
    if (!res.ok) {
        console.error('[NOTIF DELETE ERROR]', res);
        showToast(res.error || 'Error al eliminar notificación', 'error');
        return;
    }
    notifState.cachedNotifications = notifState.cachedNotifications.filter(n => n.id !== notifId);
    const item = btn?.closest('.notif-item');
    if (item) {
        item.style.transform = 'translateX(50px)';
        item.style.opacity = '0';
        setTimeout(() => {
            renderNotificationList();
            updateNotifActionButtonsState();
            updateNotifBadge();
        }, 300);
    } else {
        renderNotificationList();
        updateNotifActionButtonsState();
        updateNotifBadge();
    }
    showToast('Notificación eliminada', 'info');
}
export async function clearReadNotifs() {
    const confirmed = await showConfirm(
        '¿Borrar notificaciones?',
        '¿Deseás borrar permanentemente todas las notificaciones leídas?',
        'Borrar',
        'Cancelar'
    );
    if (!confirmed) return;

    const res = await api.delete('/user/profile/notifications/clear-read');
    if (!res.ok) {
        console.error('[NOTIF CLEAR READ ERROR]', res);
        showToast(res.error || 'Error al borrar notificaciones', 'error');
        return;
    }
    notifState.cachedNotifications = notifState.cachedNotifications.filter(n => !n.leido);
    renderNotificationList();
    updateNotifActionButtonsState();
    updateNotifBadge();
    showToast('Se han borrado todas las notificaciones', 'success');
}
export async function confirmReminder(notifId, reservaId, btn) {
    const res = await api.post(`/user/reservations/${reservaId}/confirm-reminder`);
    if (!res.ok) {
        showToast('Error al confirmar recordatorio', 'error');
        return;
    }
    const item = btn.closest('.notif-item');
    if (item) {
        item.classList.remove('notif-unread');
        const actionsDiv = item.querySelector('.notif-actions');
        if (actionsDiv) actionsDiv.remove();
    }
    updateNotifBadge();
    showToast('Reserva confirmada. Te esperamos!', 'success');
};