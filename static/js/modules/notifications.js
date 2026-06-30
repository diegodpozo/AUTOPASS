import api from './api.js';
import { showToast } from './utils.js';

let pollInterval = null;
let lastNotifCount = 0;

export async function loadNotifications() {
    const container = document.getElementById('notifications-container');
    if (!container) return;

    container.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Cargando notificaciones...</div>';

    const res = await api.get('/user/profile/notifications');
    if (!res.ok) {
        container.innerHTML = '<div class="empty-state">Error al cargar notificaciones.</div>';
        return;
    }

    const { notifications, unread } = res.data;

    const markBtn = document.getElementById('btn-mark-all-read');
    if (markBtn) {
        markBtn.style.display = unread > 0 ? 'inline-flex' : 'none';
    }

    if (!notifications || notifications.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-bell-slash" style="font-size: 3rem; color: var(--dorado); opacity:0.5; margin-bottom:15px;"></i>
                <p>No tenés notificaciones.</p>
            </div>`;
        return;
    }

    let html = '<div class="notif-list">';
    for (const n of notifications) {
        const isUnread = !n.leido;
        const timeAgo = getTimeAgo(n.created_at);
        const actions = getNotifActions(n);
        html += `
            <div class="notif-item ${isUnread ? 'notif-unread' : ''}" data-id="${n.id}" ${isUnread ? `onclick="markNotifRead(${n.id}, this)"` : ''}>
                <div class="notif-icon">
                    <i class="fas ${getNotifIcon(n.tipo)}"></i>
                </div>
                <div class="notif-content">
                    <div class="notif-title">${n.titulo}</div>
                    <div class="notif-message">${n.mensaje}</div>
                    <div class="notif-time">${timeAgo}</div>
                    ${actions ? `<div class="notif-actions">${actions}</div>` : ''}
                </div>
                ${isUnread ? `<span class="notif-unread-dot"></span>` : ''}
            </div>`;
    }
    html += '</div>';
    container.innerHTML = html;
}

function getNotifIcon(tipo) {
    switch (tipo) {
        case 'REMINDER_PAID': return 'fa-circle-check';
        case 'REMINDER_UNPAID': return 'fa-exclamation-triangle';
        case 'RESERVATION_STARTED': return 'fa-play-circle';
        case 'AUTO_CANCELLED': return 'fa-times-circle';
        default: return 'fa-bell';
    }
}

function getNotifActions(n) {
    if (n.tipo === 'REMINDER_UNPAID' && n.reserva_id) {
        return `
            <button class="notif-btn notif-btn-confirm" onclick="confirmReminder(${n.id}, ${n.reserva_id}, this)">
                <i class="fas fa-check"></i> CONFIRMAR RESERVA
            </button>
            <button class="notif-btn notif-btn-pay" onclick="payFromNotif(${n.reserva_id})">
                <i class="fas fa-credit-card"></i> PAGAR
            </button>`;
    }
    if (n.tipo === 'REMINDER_PAID' && n.reserva_id) {
        return `
            <button class="notif-btn notif-btn-view" onclick="goToReservation(${n.reserva_id})">
                <i class="fas fa-eye"></i> VER RESERVA
            </button>`;
    }
    return null;
}

function getTimeAgo(dateStr) {
    if (!dateStr) return '';
    const now = new Date();
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
    const badgeSidebar = document.getElementById('notif-badge-sidebar');
    const badgeHeader = document.getElementById('notif-badge-header');
    const badges = [badgeSidebar, badgeHeader].filter(Boolean);
    for (const badge of badges) {
        if (count > 0) {
            badge.style.display = 'inline-flex';
            badge.textContent = count > 99 ? '99+' : count;
        } else {
            badge.style.display = 'none';
        }
    }

    // DETECTAR SI LLEGARON NOTIFICACIONES NUEVAS
    if (count > lastNotifCount && lastNotifCount !== -1) {
        showNotifAlert(count);
    }
    lastNotifCount = count;
}

function showNotifAlert(count) {
    // REMOVER BANNER ANTERIOR SI EXISTE
    const old = document.getElementById('notif-alert-banner');
    if (old) old.remove();

    const banner = document.createElement('div');
    banner.id = 'notif-alert-banner';
    banner.className = 'notif-alert-banner';
    banner.innerHTML = `
        <div class="notif-alert-content">
            <div class="notif-alert-icon"><i class="fas fa-bell"></i></div>
            <div class="notif-alert-text">
                <strong>¡TENÉS ${count} MENSAJE${count !== 1 ? 'S' : ''}..!!</strong>
                <span>Hacé clic para ver</span>
            </div>
            <button class="notif-alert-close" onclick="dismissNotifAlert(event)"><i class="fas fa-times"></i></button>
        </div>
    `;

    // CLIC EN EL BANNER LLEVA A NOTIFICACIONES
    banner.addEventListener('click', (e) => {
        if (e.target.closest('.notif-alert-close')) return;
        goToNotifications();
    });

    document.body.appendChild(banner);

    // ANIMACION DE ENTRADA
    requestAnimationFrame(() => {
        banner.classList.add('visible');
    });

    // AUTO-DISMIIS A LOS 10 SEGUNDOS
    setTimeout(() => {
        if (banner.parentNode) {
            banner.classList.remove('visible');
            setTimeout(() => { if (banner.parentNode) banner.remove(); }, 500);
        }
    }, 10000);
}

function goToNotifications() {
    const bell = document.querySelector('.nav-item[onclick*="notificaciones"]');
    if (bell) {
        bell.click();
    } else {
        // FALLBACK: ABRIR SECCION NOTIFICACIONES
        const sectionBtn = document.querySelector('.notif-header-bell');
        if (sectionBtn) sectionBtn.click();
    }
    // REMOVER BANNER
    const banner = document.getElementById('notif-alert-banner');
    if (banner) banner.remove();
}

window.dismissNotifAlert = function(e) {
    if (e) e.stopPropagation();
    const banner = document.getElementById('notif-alert-banner');
    if (banner) {
        banner.classList.remove('visible');
        setTimeout(() => { if (banner.parentNode) banner.remove(); }, 500);
    }
};

window.markNotifRead = async function(notifId, el) {
    el = el.closest?.('.notif-item') || el;
    if (!el.classList.contains('notif-unread')) return;
    el.classList.remove('notif-unread');
    el.removeAttribute('onclick');
    el.style.cursor = 'default';
    const dot = el.querySelector('.notif-unread-dot');
    if (dot) dot.remove();
    updateNotifBadge();
    await api.patch(`/user/profile/notifications/${notifId}/read`);
};

window.markAllNotifRead = async function() {
    const res = await api.post('/user/profile/notifications/read-all');
    if (!res.ok) return;
    document.querySelectorAll('.notif-item.notif-unread').forEach(el => {
        el.classList.remove('notif-unread');
        const btn = el.querySelector('.notif-mark-read');
        if (btn) btn.remove();
    });
    document.getElementById('btn-mark-all-read').style.display = 'none';
    updateNotifBadge();
    showToast('Todas las notificaciones marcadas como leídas', 'success');
};

window.confirmReminder = async function(notifId, reservaId, btn) {
    const res = await api.post(`/user/reservations/${reservaId}/confirm-reminder`);
    if (!res.ok) {
        showToast('Error al confirmar recordatorio', 'error');
        return;
    }
    const item = btn.closest('.notif-item');
    if (item) {
        item.classList.remove('notif-unread');
        const markBtn = item.querySelector('.notif-mark-read');
        if (markBtn) markBtn.remove();
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
    let html = '<div class="notif-list">';
    for (const n of notifications) {
        const isUnread = !n.leido;
        const timeAgo = getTimeAgo(n.created_at);
        const actions = getNotifActions(n);
        html += `
            <div class="notif-item ${isUnread ? 'notif-unread' : ''}" data-id="${n.id}" ${isUnread ? `onclick="markNotifRead(${n.id}, this)"` : ''}>
                <div class="notif-icon">
                    <i class="fas ${getNotifIcon(n.tipo)}"></i>
                </div>
                <div class="notif-content">
                    <div class="notif-title">${n.titulo}</div>
                    <div class="notif-message">${n.mensaje}</div>
                    <div class="notif-time">${timeAgo}</div>
                    ${actions ? `<div class="notif-actions">${actions}</div>` : ''}
                </div>
                ${isUnread ? `<span class="notif-unread-dot"></span>` : ''}
            </div>`;
    }
    html += '</div>';
    body.innerHTML = html;
}

// CERRAR DROPDOWN AL HACER CLIC FUERA
document.addEventListener('click', function(e) {
    const bell = document.querySelector('.notif-header-bell');
    const dropdown = document.getElementById('notif-dropdown');
    if (bell && dropdown && dropdown.classList.contains('visible') && !bell.contains(e.target)) {
        dropdown.classList.remove('visible');
    }
});

window.loadNotifications = loadNotifications;

// POLLING CADA 30 SEGUNDOS PARA EL BADGE
export function startNotifPolling() {
    if (pollInterval) clearInterval(pollInterval);
    lastNotifCount = -1; // INICIALIZAR PARA NO DISPARAR ALERTA EN EL PRIMER POLL
    updateNotifBadge();
    pollInterval = setInterval(updateNotifBadge, 30000);
}

export function stopNotifPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

// INICIAR POLLING AUTOMATICAMENTE AL CARGAR EL MODULO
document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('token')) {
        startNotifPolling();
    }
});
