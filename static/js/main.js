import * as utils from './modules/utils.js';
import * as ui from './modules/ui.js';

/**
 * PUENTE: MAIN.JS
 * EXPONE UTILIDADES AL AMBITO GLOBAL PARA COMPATIBILIDAD CON EVENTOS INLINE (ONCLICK).
 */

// UTILIDADES
window.toTitle = utils.toTitle;
window.formatDate = utils.formatDate;
window.showToast = utils.showToast;
window.showConfirm = utils.showConfirm;
window.formatNum = utils.formatNum;
window.formatTime = utils.formatTime;
window.formatTimeSeconds = utils.formatTimeSeconds;
window.formatDateTime = utils.formatDateTime;
window.formatDayTime = utils.formatDayTime;
window.formatLocalDateTime = utils.formatLocalDateTime;

// INTERFAZ
window.openModal = ui.openModal;
window.closeModal = ui.closeModal;
window.switchModal = ui.switchModal;
window.togglePasswordVisibility = ui.togglePasswordVisibility;
window.toggleSidebar = ui.toggleSidebar;
window.toggleMobileNav = ui.toggleMobileNav;
window.closeMobileNav = ui.closeMobileNav;
window.logout = ui.logout;

/**
 * GESTION DE AUTENTICACION EN UI (MANTENER AQUI POR AHORA O MOVER UN UI.JS)
 */
window.updateAuthNav = function() {
    const loggedIn = !!localStorage.getItem('token');
    const login = document.getElementById('nav-login');
    const register = document.getElementById('nav-register');
    const profile = document.getElementById('nav-profile');
    const logout = document.getElementById('nav-logout');

    if (login) login.style.display = loggedIn ? 'none' : '';
    if (register) register.style.display = loggedIn ? 'none' : '';
    if (profile) {
        profile.style.display = loggedIn ? 'inline-block' : 'none';
        if (loggedIn) {
            const rol = localStorage.getItem('rol');
            const isStaffOrAdmin = ['admin', 'local_admin', 'staff'].includes(rol);
            profile.href = isStaffOrAdmin ? '/dashboard' : '/perfil';
        }
    }
    if (logout) logout.style.display = loggedIn ? 'inline-block' : 'none';
};

//--- INICIALIZACION GLOBAL ---
document.addEventListener('DOMContentLoaded', () => {
    window.updateAuthNav();

    // RESTAURAR ESTADO DEL SIDEBAR COLAPSADO
    if (localStorage.getItem('sidebarCollapsed') === 'true') {
        const layout = document.querySelector('.layout-with-sidebar');
        const sidebar = document.querySelector('.sidebar');
        const toggleIcon = document.querySelector('.sidebar-toggle i');
        if (layout && sidebar) {
            layout.classList.add('collapsed');
            sidebar.classList.add('collapsed');
            if (toggleIcon) toggleIcon.className = 'fas fa-chevron-right';
        }
    }
});

// MANEJO DE NAVEGACIÓN ATRÁS/ADELANTE Y RESTAURACIÓN DE BFCACHE
window.addEventListener('pageshow', () => {
    const loggedIn = !!localStorage.getItem('token');
    if (loggedIn) {
        ui.closeModal('loginModal');
        ui.closeModal('registerModal');
    }

    document.querySelectorAll('.modal button[type="submit"]').forEach(btn => {
        btn.disabled = false;
        if (btn.dataset.originalHtml) {
            btn.innerHTML = btn.dataset.originalHtml;
        } else if (btn.closest('#loginModal')) {
            btn.innerHTML = 'INICIAR SESIÓN';
        } else if (btn.closest('#registerModal')) {
            btn.innerHTML = 'REGISTRARME';
        }
    });

    window.updateAuthNav();
});

// CERRAR MODALES CON TECLA ESCAPE
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal[style*="display: block"]').forEach(m => {
            m.style.display = 'none';
            m.querySelectorAll('.error-msg').forEach(el => el.style.display = 'none');
        });
    }
});
