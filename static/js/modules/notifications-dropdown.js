/**
 * AUTOPASS - DROPDOWN DE NOTIFICACIONES DEL HEADER
 * Submodulo de notifications.js: apertura/cierre del desplegable, carga de las
 * ultimas 5 notificaciones y cierre automatico al hacer click fuera del timbre.
 */

import api from './api.js';
import { getNotifIcon, getNotifCategoryClass, getNotifActions, getTimeAgo } from './notifications-format.js';

export function toggleNotifDropdown(e) {
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

export function closeNotifDropdown() {
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