import api from './api.js';
import { showToast, showConfirm } from './utils.js';
import { getVirtualNow } from './virtual-time.js';

let pollInterval = null;
let lastNotifCount = 0;
let currentFilter = 'ALL';
let cachedNotifications = [];

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
    cachedNotifications = notifications || [];

    updateNotifActionButtonsState();
    renderNotificationList();
}

function updateNotifActionButtonsState() {
    const hasUnread = cachedNotifications.some(n => !n.leido);
    const hasRead = cachedNotifications.some(n => n.leido);

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

function renderNotificationList() {
    const container = document.getElementById('notifications-container');
    if (!container) return;

    const filtered = filterNotificationsArray(cachedNotifications, currentFilter);

    if (!filtered || filtered.length === 0) {
        let msg = 'No tenés notificaciones.';
        if (currentFilter === 'UNREAD') msg = 'No tenés notificaciones sin leer.';
        else if (currentFilter === 'RESERVATION') msg = 'No hay notificaciones de reservas.';
        else if (currentFilter === 'FINANCE') msg = 'No hay notificaciones de pagos o saldo.';
        else if (currentFilter === 'SUPPORT') msg = 'No hay notificaciones de soporte.';

        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-bell-slash" style="font-size: 3rem; color: var(--dorado); opacity:0.5; margin-bottom:15px;"></i>
                <p>${msg}</p>
            </div>`;
        return;
    }

    let html = '<div class="notif-list">';
    for (const n of filtered) {
        const isUnread = !n.leido;
        const timeAgo = getTimeAgo(n.created_at);
        const actions = getNotifActions(n);
        const catClass = getNotifCategoryClass(n.tipo);
        const iconClass = getNotifIcon(n.tipo);

        html += `
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
    }
    html += '</div>';
    container.innerHTML = html;
}

function filterNotificationsArray(list, filter) {
    if (!list) return [];
    if (filter === 'UNREAD') return list.filter(n => !n.leido);
    if (filter === 'RESERVATION') return list.filter(n => ['REMINDER_PAID', 'REMINDER_UNPAID', 'RESERVATION_STARTED', 'AUTO_CANCELLED', 'RESERVATION_CONFIRMED', 'RESERVATION_CANCELLED'].includes(n.tipo));
    if (filter === 'FINANCE') return list.filter(n => ['BALANCE_RECHARGED', 'PROMO_REDEEMED', 'POINTS_EARNED'].includes(n.tipo));
    if (filter === 'SUPPORT') return list.filter(n => n.tipo === 'SUPPORT_RESPONSE' || n.tipo === 'SUPPORT_TICKET');
    return list;
}

window.filterNotifs = function(filterType, btn) {
    currentFilter = filterType;
    document.querySelectorAll('.notif-chip').forEach(c => c.classList.remove('active'));
    if (btn) btn.classList.add('active');
    renderNotificationList();
};

function getNotifIcon(tipo) {
    switch (tipo) {
        case 'REMINDER_PAID': return 'fa-clock';
        case 'REMINDER_UNPAID': return 'fa-exclamation-triangle';
        case 'RESERVATION_STARTED': return 'fa-play-circle';
        case 'AUTO_CANCELLED':
        case 'RESERVATION_CANCELLED': return 'fa-times-circle';
        case 'RESERVATION_CONFIRMED': return 'fa-check-circle';
        case 'BALANCE_RECHARGED': return 'fa-wallet';
        case 'SUPPORT_RESPONSE': return 'fa-headset';
        case 'SUPPORT_TICKET': return 'fa-ticket';
        case 'NEW_DEVICE_LOGIN': return 'fa-shield-halved';
        case 'PROMO_REDEEMED':
        case 'POINTS_EARNED': return 'fa-gift';
        default: return 'fa-bell';
    }
}

function getNotifCategoryClass(tipo) {
    switch (tipo) {
        case 'RESERVATION_CONFIRMED':
        case 'BALANCE_RECHARGED': return 'notif-cat-success';
        case 'REMINDER_UNPAID': return 'notif-cat-warning';
        case 'AUTO_CANCELLED':
        case 'RESERVATION_CANCELLED': return 'notif-cat-danger';
        case 'SUPPORT_RESPONSE': return 'notif-cat-support';
        case 'SUPPORT_TICKET': return 'notif-cat-support';
        case 'NEW_DEVICE_LOGIN': return 'notif-cat-warning';
        case 'REMINDER_PAID':
        case 'PROMO_REDEEMED': return 'notif-cat-gold';
        default: return 'notif-cat-default';
    }
}

function getNotifActions(n) {
    if (n.tipo === 'REMINDER_UNPAID' && n.reserva_id) {
        return `
            <button class="notif-btn notif-btn-confirm" onclick="confirmReminder(${n.id}, ${n.reserva_id}, this)">
                <i class="fas fa-check"></i> CONFIRMAR
            </button>
            <button class="notif-btn notif-btn-pay" onclick="payFromNotif(${n.reserva_id})">
                <i class="fas fa-credit-card"></i> PAGAR
            </button>`;
    }
    if ((n.tipo === 'REMINDER_PAID' || n.tipo === 'RESERVATION_CONFIRMED' || n.tipo === 'RESERVATION_STARTED') && n.reserva_id) {
        return `
            <button class="notif-btn notif-btn-view" onclick="goToReservation(${n.reserva_id})">
                <i class="fas fa-eye"></i> VER RESERVA
            </button>`;
    }
    if (n.tipo === 'SUPPORT_RESPONSE' || n.tipo === 'SUPPORT_TICKET') {
        const ticketId = n.ticket_id || '';
        return `
            <button class="notif-btn notif-btn-support" onclick="openSupportTicketModal(${ticketId})">
                <i class="fas fa-headset"></i> IR A SOPORTE
            </button>`;
    }
    return null;
}

function getTimeAgo(dateStr) {
    if (!dateStr) return '';
    const now = getVirtualNow();
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    const diffMs = now - d;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'Ahora';
    if (diffMin < 60) return `Hace ${diffMin} min`;
    const diffHs = Math.floor(diffMin / 60);
    if (diffHs < 24) return `Hace ${diffHs}h`;
    const diffDays = Math.floor(diffHs / 24);
    if (diffDays === 1) return 'Ayer';
    return `Hace ${diffDays} días`;
}

export async function fetchUnreadCount() {
    const res = await api.get('/user/profile/notifications/unread');
    if (!res.ok) return 0;
    return res.data.count;
}

export async function updateNotifBadge() {
    const count = await fetchUnreadCount();
    // La burbuja del header/campana (perfil) y del sidebar de USUARIO/CLIENTE reflejan
    // el conteo global de notificaciones.
    const badgeSidebarUser = document.getElementById('notif-badge-sidebar-user');
    const badgeHeader = document.getElementById('notif-badge-header');
    const badges = [badgeSidebarUser, badgeHeader].filter(Boolean);
    for (const badge of badges) {
        if (count > 0) {
            badge.style.display = 'inline-flex';
            badge.textContent = count > 99 ? '99+' : count;
            badge.classList.add('pulse');
        } else {
            badge.style.display = 'none';
            badge.classList.remove('pulse');
        }
    }

    // DETECTAR SI LLEGARON NOTIFICACIONES NUEVAS
    if (count > lastNotifCount && lastNotifCount !== -1) {
        showToast(`Tenés ${count} notificación${count !== 1 ? 'es' : ''} sin leer`, 'info');
    }
    lastNotifCount = count;
}

export async function markNotifRead(notifId, el) {
    el = el?.closest?.('.notif-item') || el;
    if (el && !el.classList.contains('notif-unread')) return;
    if (el) {
        el.classList.remove('notif-unread');
        const dot = el.querySelector('.notif-unread-dot');
        if (dot) dot.remove();
    }
    const target = cachedNotifications.find(n => n.id === notifId);
    if (target) target.leido = true;

    updateNotifActionButtonsState();
    updateNotifBadge();
    await api.patch(`/user/profile/notifications/${notifId}/read`);
}
window.markNotifRead = markNotifRead;

export async function markAllNotifRead() {
    const res = await api.post('/user/profile/notifications/read-all');
    if (!res.ok) {
        console.error('[NOTIF READ ALL ERROR]', res);
        showToast(res.error || 'Error al marcar notificaciones', 'error');
        return;
    }
    cachedNotifications.forEach(n => n.leido = true);
    renderNotificationList();
    updateNotifActionButtonsState();
    updateNotifBadge();
    showToast('Todas las notificaciones marcadas como leídas', 'success');
}
window.markAllNotifRead = markAllNotifRead;

export async function deleteNotif(notifId, e, btn) {
    if (e) e.stopPropagation();
    const res = await api.delete(`/user/profile/notifications/${notifId}`);
    if (!res.ok) {
        console.error('[NOTIF DELETE ERROR]', res);
        showToast(res.error || 'Error al eliminar notificación', 'error');
        return;
    }
    cachedNotifications = cachedNotifications.filter(n => n.id !== notifId);
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
window.deleteNotif = deleteNotif;

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
    cachedNotifications = cachedNotifications.filter(n => !n.leido);
    renderNotificationList();
    updateNotifActionButtonsState();
    updateNotifBadge();
    showToast('Se han borrado todas las notificaciones', 'success');
}
window.clearReadNotifs = clearReadNotifs;

window.confirmReminder = async function(notifId, reservaId, btn) {
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

window.payFromNotif = async function(reservaId) {
    window.showSection?.('reservas');
    setTimeout(async () => {
        const card = document.querySelector(`[data-reserva-id="${reservaId}"]`);
        if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            card.style.boxShadow = '0 0 0 3px var(--dorado), 0 8px 32px rgba(212, 175, 55, 0.3)';
            setTimeout(() => { card.style.boxShadow = ''; }, 2000);
        }
        const { payReservation } = await import('./reservas.js');
        payReservation(reservaId);
    }, 600);
};

window.goToReservation = function(reservaId) {
    window.showSection?.('reservas');
    setTimeout(() => {
        const card = document.querySelector(`[data-reserva-id="${reservaId}"]`);
        if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 500);
};

// DROPDOWN DE NOTIFICACIONES EN HEADER
window.toggleNotifDropdown = function(e) {
    if (e) e.stopPropagation();
    const dropdown = document.getElementById('notif-dropdown');
    if (!dropdown) return;
    const isVisible = dropdown.classList.contains('visible');
    if (isVisible) {
        closeNotifDropdown();
        return;
    }
    dropdown.classList.add('visible');
    loadNotifDropdown();
};

window.closeNotifDropdown = function() {
    const dropdown = document.getElementById('notif-dropdown');
    if (dropdown) dropdown.classList.remove('visible');
};

async function loadNotifDropdown() {
    const body = document.getElementById('notif-dropdown-body');
    if (!body) return;
    body.innerHTML = '<div class="notif-dropdown-loading"><i class="fas fa-spinner fa-spin"></i> Cargando...</div>';
    const res = await api.get('/user/profile/notifications?limit=5');
    if (!res.ok) {
        body.innerHTML = '<div class="notif-dropdown-empty">Error al cargar</div>';
        return;
    }
    const { notifications } = res.data;
    if (!notifications || notifications.length === 0) {
        body.innerHTML = '<div class="notif-dropdown-empty">Sin notificaciones</div>';
        return;
    }
    let html = '<div class="notif-list dropdown-list">';
    for (const n of notifications) {
        const isUnread = !n.leido;
        const timeAgo = getTimeAgo(n.created_at);
        const actions = getNotifActions(n);
        const catClass = getNotifCategoryClass(n.tipo);
        const iconClass = getNotifIcon(n.tipo);

        html += `
            <div class="notif-item dropdown-item ${isUnread ? 'notif-unread' : ''} ${catClass}" data-id="${n.id}" ${isUnread ? `onclick="markNotifRead(${n.id}, this)"` : ''}>
                <div class="notif-icon-box sm ${catClass}">
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
            </div>`;
    }
    html += '</div>';
    body.innerHTML = html;
}

document.addEventListener('click', function(e) {
    const bell = document.querySelector('.notif-header-bell');
    const dropdown = document.getElementById('notif-dropdown');
    if (bell && dropdown && dropdown.classList.contains('visible') && !bell.contains(e.target)) {
        dropdown.classList.remove('visible');
    }
});

window.loadNotifications = loadNotifications;

export function startNotifPolling() {
    if (pollInterval) clearInterval(pollInterval);
    lastNotifCount = -1;
    updateNotifBadge();
    pollInterval = setInterval(updateNotifBadge, 30000);
}

export function stopNotifPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('token')) {
        if (sessionStorage.getItem('autopass_device_alert') === '1') {
            sessionStorage.removeItem('autopass_device_alert');
            setTimeout(() => {
                showToast('Iniciaste sesión en un dispositivo nuevo', 'warning');
            }, 800);
        }
        startNotifPolling();
    }
});
