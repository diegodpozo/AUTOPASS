/**
 * AUTOPASS - ESTADO COMPARTIDO DE NOTIFICACIONES
 * Submodulo de notifications.js: estado mutable compartido entre render,
 * badge, acciones, dropdown y polling.
 */

export const notifState = {
    pollInterval: null,
    lastNotifCount: 0,
    currentFilter: 'ALL',
    cachedNotifications: [],
    isUpdatingBadge: false,
};