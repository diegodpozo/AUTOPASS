/**
 * AUTOPASS - CENTRO DE NOTIFICACIONES (FACHADA)
 * Notificaciones push en tiempo real: lista, filtros, badge no leido, acciones,
 * navegacion, dropdown del header y polling del conteo.
 * Fachada que orquesta los submodulos:
 *   - notifications-state:     estado compartido (filtro, cache, badge, polling)
 *   - notifications-format:    iconos, categorias, acciones inline y tiempo relativo
 *   - notifications-render:    carga, filtros y render de la lista
 *   - notifications-badge:     conteo no leido y burbujas del header/sidebar
 *   - notifications-actions:   marcar leidas, eliminar, borrar leidas, confirmar
 *   - notifications-nav:       redirecciones a la seccion destino de cada accion
 *   - notifications-dropdown:  desplegable del header con las ultimas notificaciones
 *   - notifications-polling:   refresco periodico del badge (30 seg)
 */

import { startNotifPolling } from './notifications-polling.js';
import { showToast } from './utils.js';

export { loadNotifications, filterNotifs } from './notifications-render.js';
export { fetchUnreadCount, updateNotifBadge } from './notifications-badge.js';
export { markNotifRead, markAllNotifRead, deleteNotif, clearReadNotifs, confirmReminder } from './notifications-actions.js';
export { payFromNotif, goToReservation, goToChangePassword, goToBalance, goToPoints, goToVoucher, goToNewReservation, goToReservationsList, goToVehicles, goToProfile, goToStays } from './notifications-nav.js';
export { toggleNotifDropdown, closeNotifDropdown } from './notifications-dropdown.js';
export { startNotifPolling, stopNotifPolling } from './notifications-polling.js';

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