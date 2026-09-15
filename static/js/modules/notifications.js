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
        else if (currentFilter === 'SECURITY') msg = 'No hay notificaciones de seguridad.';

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
        case 'RESERVATION_MODIFIED': return 'fa-calendar-check';
        case 'RESERVATION_CREATED_ADMIN': return 'fa-calendar-plus';
        case 'BALANCE_RECHARGED':
        case 'BALANCE_ADJUSTED_ADMIN': return 'fa-wallet';
        case 'STAY_PAID': return 'fa-receipt';
        case 'STAY_CANCELLED_ADMIN': return 'fa-ban';
        case 'SUPPORT_RESPONSE': return 'fa-headset';
        case 'SUPPORT_TICKET': return 'fa-ticket';
        case 'SUPPORT_STATUS_CHANGED': return 'fa-info-circle';
        case 'NEW_DEVICE_LOGIN':
        case 'PASSWORD_CHANGED_ADMIN':
        case 'SECURITY_PASSWORD_CHANGED': return 'fa-shield-halved';
        case 'USER_PROFILE_UPDATED': return 'fa-user-edit';
        case 'USER_ROLE_CHANGED': return 'fa-user-tag';
        case 'USER_BLOCK_STATUS_CHANGED': return 'fa-user-lock';
        case 'PROMO_REDEEMED':
        case 'PROMO_CANCELLED':
        case 'POINTS_EARNED': return 'fa-gift';
        case 'VEHICLE_REGISTERED':
        case 'VEHICLE_REMOVED':
        case 'VEHICLE_ENTRY':
        case 'VEHICLE_EXIT': return 'fa-car';
        default: return 'fa-bell';
    }
}

function getNotifCategoryClass(tipo) {
    switch (tipo) {
        case 'RESERVATION_CONFIRMED':
        case 'RESERVATION_CREATED_ADMIN':
        case 'BALANCE_RECHARGED':
        case 'STAY_PAID':
        case 'VEHICLE_REGISTERED': return 'notif-cat-success';
        case 'REMINDER_UNPAID':
        case 'NEW_DEVICE_LOGIN':
        case 'PASSWORD_CHANGED_ADMIN':
        case 'SECURITY_PASSWORD_CHANGED':
        case 'USER_BLOCK_STATUS_CHANGED': return 'notif-cat-warning';
        case 'AUTO_CANCELLED':
        case 'RESERVATION_CANCELLED':
        case 'STAY_CANCELLED_ADMIN':
        case 'PROMO_CANCELLED':
        case 'VEHICLE_REMOVED': return 'notif-cat-danger';
        case 'SUPPORT_RESPONSE':
        case 'SUPPORT_TICKET':
        case 'SUPPORT_STATUS_CHANGED': return 'notif-cat-support';
        case 'REMINDER_PAID':
        case 'RESERVATION_MODIFIED':
        case 'PROMO_REDEEMED':
        case 'POINTS_EARNED':
        case 'BALANCE_ADJUSTED_ADMIN':
        case 'USER_PROFILE_UPDATED':
        case 'USER_ROLE_CHANGED': return 'notif-cat-gold';
        default: return 'notif-cat-default';
    }
}

function getNotifActions(n) {
    // 1. RECORDATORIO DE PAGO PENDIENTE
    if (n.tipo === 'REMINDER_UNPAID' && n.reserva_id) {
        return `
            <button class="notif-btn notif-btn-confirm" onclick="confirmReminder(${n.id}, ${n.reserva_id}, this)">
                <i class="fas fa-check"></i> CONFIRMAR
            </button>
            <button class="notif-btn notif-btn-pay" onclick="payFromNotif(${n.reserva_id})">
                <i class="fas fa-credit-card"></i> PAGAR
            </button>`;
    }

    // 2. RESERVAS CONFIRMADAS / RECORDATORIO PAGADO / EN CURSO / MODIFICADAS / CREADAS POR ADMIN
    if (['REMINDER_PAID', 'RESERVATION_CONFIRMED', 'RESERVATION_STARTED', 'RESERVATION_MODIFIED', 'RESERVATION_CREATED_ADMIN'].includes(n.tipo) && n.reserva_id) {
        return `
            <button class="notif-btn notif-btn-view" onclick="goToReservation(${n.reserva_id})">
                <i class="fas fa-eye"></i> VER RESERVA
            </button>`;
    }

    // 3. RESERVAS AUTO-CANCELADAS
    if (n.tipo === 'AUTO_CANCELLED') {
        return `
            <button class="notif-btn notif-btn-confirm" onclick="goToNewReservation()">
                <i class="fas fa-calendar-plus"></i> NUEVA RESERVA
            </button>
            ${n.reserva_id ? `
            <button class="notif-btn notif-btn-view" onclick="goToReservation(${n.reserva_id})">
                <i class="fas fa-eye"></i> VER DETALLE
            </button>` : ''}`;
    }

    // 4. RESERVAS CANCELADAS
    if (n.tipo === 'RESERVATION_CANCELLED') {
        const hasRefund = n.mensaje && (n.mensaje.toLowerCase().includes('saldo') || n.mensaje.toLowerCase().includes('reembols'));
        return `
            ${hasRefund ? `
            <button class="notif-btn notif-btn-balance" onclick="goToBalance()">
                <i class="fas fa-wallet"></i> VER MI SALDO
            </button>` : ''}
            ${n.reserva_id ? `
            <button class="notif-btn notif-btn-view" onclick="goToReservation(${n.reserva_id})">
                <i class="fas fa-eye"></i> VER DETALLE
            </button>` : `
            <button class="notif-btn notif-btn-view" onclick="goToReservationsList()">
                <i class="fas fa-calendar-alt"></i> VER RESERVAS
            </button>`}`;
    }

    // 5. CANJE DE BENEFICIOS / VOUCHERS
    if (n.tipo === 'PROMO_REDEEMED') {
        const vMatch = n.mensaje?.match(/Voucher #(\d+)/i) || n.mensaje?.match(/#([0-9a-fA-F]{6,16})/);
        const vId = vMatch ? vMatch[1] : '';
        return `
            <button class="notif-btn notif-btn-voucher" onclick="goToVoucher('${vId}')">
                <i class="fas fa-ticket"></i> VER VOUCHER
            </button>
            <button class="notif-btn notif-btn-points" onclick="goToPoints()">
                <i class="fas fa-gift"></i> MIS PUNTOS
            </button>`;
    }

    // 6. CANJE CANCELADO O PUNTOS GANADOS
    if (['PROMO_CANCELLED', 'POINTS_EARNED'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-points" onclick="goToPoints()">
                <i class="fas fa-gift"></i> VER MIS PUNTOS
            </button>`;
    }

    // 7. PAGO DE ESTADÍA
    if (n.tipo === 'STAY_PAID') {
        return `
            <button class="notif-btn notif-btn-balance" onclick="goToStays()">
                <i class="fas fa-receipt"></i> VER ESTADÍAS
            </button>
            <button class="notif-btn notif-btn-balance" onclick="goToBalance()">
                <i class="fas fa-wallet"></i> MI SALDO
            </button>`;
    }

    // 8. ESTADÍA CANCELADA POR ADMIN
    if (n.tipo === 'STAY_CANCELLED_ADMIN') {
        return `
            <button class="notif-btn notif-btn-vehicles" onclick="goToVehicles()">
                <i class="fas fa-car"></i> MIS VEHÍCULOS
            </button>
            <button class="notif-btn notif-btn-support" onclick="openSupportTicketModal()">
                <i class="fas fa-headset"></i> AYUDA
            </button>`;
    }

    // 9. EVENTOS DE VEHÍCULOS
    if (['VEHICLE_REGISTERED', 'VEHICLE_REMOVED'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-vehicles" onclick="goToVehicles()">
                <i class="fas fa-car"></i> MIS VEHÍCULOS
            </button>`;
    }
    if (['VEHICLE_ENTRY', 'VEHICLE_EXIT'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-vehicles" onclick="goToVehicles()">
                <i class="fas fa-car"></i> MIS VEHÍCULOS
            </button>
            <button class="notif-btn notif-btn-balance" onclick="goToStays()">
                <i class="fas fa-clock-rotate-left"></i> VER ESTADÍA
            </button>`;
    }

    // 10. TICKETS DE SOPORTE
    if (['SUPPORT_RESPONSE', 'SUPPORT_TICKET', 'SUPPORT_STATUS_CHANGED'].includes(n.tipo)) {
        const ticketId = n.ticket_id || '';
        return `
            <button class="notif-btn notif-btn-support" onclick="openSupportTicketModal(${ticketId})">
                <i class="fas fa-headset"></i> IR A SOPORTE
            </button>`;
    }

    // 11. SEGURIDAD: NUEVO DISPOSITIVO O CONTRASEÑA MODIFICADA POR ADMIN
    if (['NEW_DEVICE_LOGIN', 'PASSWORD_CHANGED_ADMIN'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-security" onclick="goToChangePassword()">
                <i class="fas fa-key"></i> CAMBIAR CONTRASEÑA
            </button>`;
    }

    // 12. SEGURIDAD: CONTRASEÑA MODIFICADA POR USUARIO O CUENTA BLOQUEADA/DESBLOQUEADA
    if (['SECURITY_PASSWORD_CHANGED', 'USER_BLOCK_STATUS_CHANGED'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-support" onclick="openSupportTicketModal()">
                <i class="fas fa-headset"></i> CONTACTAR SOPORTE
            </button>`;
    }

    // 13. PERFIL O ROL ACTUALIZADO
    if (['USER_PROFILE_UPDATED', 'USER_ROLE_CHANGED'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-profile" onclick="goToProfile()">
                <i class="fas fa-user"></i> VER MI PERFIL
            </button>`;
    }

    // 14. RECARGA O AJUSTE DE SALDO
    if (['BALANCE_RECHARGED', 'BALANCE_ADJUSTED_ADMIN'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-balance" onclick="goToBalance()">
                <i class="fas fa-wallet"></i> VER MI SALDO
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

let isUpdatingBadge = false;

export async function updateNotifBadge() {
    if (isUpdatingBadge) return;
    isUpdatingBadge = true;
    try {
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
        if (lastNotifCount !== -1 && count > lastNotifCount) {
            showToast(`Tenés ${count} notificación${count !== 1 ? 'es' : ''} sin leer`, 'info');
        }
        lastNotifCount = count;
    } finally {
        isUpdatingBadge = false;
    }
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
    window.closeNotifDropdown?.();
    window.showSection?.('reservas');
    setTimeout(() => {
        const card = document.querySelector(`[data-reserva-id="${reservaId}"]`);
        if (card) {
            card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            card.style.boxShadow = '0 0 0 3px var(--dorado), 0 8px 32px rgba(212, 175, 55, 0.3)';
            setTimeout(() => { card.style.boxShadow = ''; }, 2000);
        }
    }, 500);
};

window.goToChangePassword = function() {
    window.closeNotifDropdown?.();
    window.showSection?.('perfil');
    setTimeout(() => {
        const btnPass = document.getElementById('current-password') || document.getElementById('btn-change-password') || document.querySelector('[data-bs-target="#changePasswordModal"]') || document.querySelector('.form-security-premium');
        if (btnPass) {
            btnPass.scrollIntoView({ behavior: 'smooth', block: 'center' });
            btnPass.focus?.();
        }
    }, 400);
};

window.goToBalance = function() {
    window.closeNotifDropdown?.();
    if (window.openRechargeModal) {
        window.openRechargeModal();
    } else {
        window.showSection?.('perfil');
    }
};

window.goToPoints = function() {
    window.closeNotifDropdown?.();
    window.showSection?.('puntos');
    setTimeout(() => {
        const ptsEl = document.getElementById('puntos-catalog-container') || document.querySelector('.fidelizacion-card') || document.getElementById('section-puntos');
        if (ptsEl) ptsEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }, 400);
};

window.goToVoucher = async function(voucherId) {
    window.closeNotifDropdown?.();
    window.showSection?.('puntos');
    setTimeout(async () => {
        const vContainer = document.getElementById('vouchers-container');
        if (vContainer) {
            vContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        try {
            const { showCanjeTicket, showCanjeTicketById } = await import('./profile.js');
            if (voucherId) {
                const num = Number(voucherId);
                if (!isNaN(num) && num > 0) {
                    await showCanjeTicketById(num);
                    return;
                }
            }
            // Fallback: abrir el voucher más reciente o el que coincida
            const res = await api.get('/user/redemption-tickets');
            if (res.ok && res.data && res.data.length > 0) {
                if (voucherId) {
                    const match = res.data.find(x => x.codigo === voucherId || String(x.id) === String(voucherId));
                    if (match) {
                        showCanjeTicket(match);
                        return;
                    }
                }
                showCanjeTicket(res.data[0]);
            }
        } catch (e) {
            console.error('[NOTIF VOUCHER ERROR]', e);
        }
    }, 450);
};

window.goToNewReservation = function() {
    window.closeNotifDropdown?.();
    window.showSection?.('inicio');
    setTimeout(() => {
        const formContainer = document.getElementById('reserva-form-container') || document.getElementById('section-inicio');
        if (formContainer) {
            formContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 400);
};

window.goToReservationsList = function() {
    window.closeNotifDropdown?.();
    window.showSection?.('reservas');
    setTimeout(() => {
        const resList = document.getElementById('reservas-list') || document.getElementById('section-reservas');
        if (resList) {
            resList.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 400);
};

window.goToVehicles = function() {
    window.closeNotifDropdown?.();
    window.showSection?.('vehiculos');
    setTimeout(() => {
        const vContainer = document.getElementById('vehicles-grid') || document.getElementById('vehicle-form-container') || document.getElementById('section-vehiculos');
        if (vContainer) {
            vContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 400);
};

window.goToProfile = function() {
    window.closeNotifDropdown?.();
    window.showSection?.('perfil');
    setTimeout(() => {
        const pCard = document.querySelector('.account-hub-card') || document.getElementById('section-perfil');
        if (pCard) {
            pCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 400);
};

window.goToStays = function() {
    window.closeNotifDropdown?.();
    window.showSection?.('perfil');
    setTimeout(() => {
        const staysCard = document.getElementById('container-active-stays') || document.querySelector('.account-hub-card') || document.getElementById('section-perfil');
        if (staysCard) {
            staysCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }, 400);
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
    if (window.__autopassNotifPollInterval) return;
    lastNotifCount = -1;
    updateNotifBadge();
    window.__autopassNotifPollInterval = setInterval(updateNotifBadge, 30000);
    pollInterval = window.__autopassNotifPollInterval;
}

export function stopNotifPolling() {
    if (window.__autopassNotifPollInterval) {
        clearInterval(window.__autopassNotifPollInterval);
        window.__autopassNotifPollInterval = null;
    }
    pollInterval = null;
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
