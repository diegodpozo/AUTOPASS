/**
 * AUTOPASS - BADGE DE NOTIFICACIONES SIN LEER
 * Submodulo de notifications.js: conteo no leido y actualizacion de la
 * burbuja del header/campana y del sidebar de USUARIO/CLIENTE.
 */

import api from './api.js';
import { showToast } from './utils.js';
import { notifState } from './notifications-state.js';

export async function fetchUnreadCount() {
    const res = await api.get('/user/profile/notifications/unread');
    if (!res.ok) return 0;
    return res.data.count;
}

export async function updateNotifBadge() {
    if (notifState.isUpdatingBadge) return;
    notifState.isUpdatingBadge = true;
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
        if (notifState.lastNotifCount !== -1 && count > notifState.lastNotifCount) {
            showToast(`Tenés ${count} notificación${count !== 1 ? 'es' : ''} sin leer`, 'info');
        }
        notifState.lastNotifCount = count;
    } finally {
        notifState.isUpdatingBadge = false;
    }
}