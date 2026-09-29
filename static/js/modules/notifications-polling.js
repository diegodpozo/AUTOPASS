/**
 * AUTOPASS - POLLING DEL BADGE DE NOTIFICACIONES
 * Submodulo de notifications.js: refresco periodico del conteo no leido.
 */

import { updateNotifBadge } from './notifications-badge.js';
import { notifState } from './notifications-state.js';

export function startNotifPolling() {
    if (notifState.pollInterval) return;
    notifState.lastNotifCount = -1;
    updateNotifBadge();
    notifState.pollInterval = setInterval(updateNotifBadge, 30000);
}
