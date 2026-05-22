import * as utils from './modules/utils.js';
import * as ui from './modules/ui.js';

/**
 * BRIDGE: main.js
 * Expone utilidades al ámbito global para compatibilidad con eventos inline (onclick).
 */

// Utilidades
window.toTitle = utils.toTitle;
window.formatDate = utils.formatDate;
window.showToast = utils.showToast;
window.showConfirm = utils.showConfirm;

// Interfaz
window.openModal = ui.openModal;
window.closeModal = ui.closeModal;
window.switchModal = ui.switchModal;
window.togglePasswordVisibility = ui.togglePasswordVisibility;
window.toggleSidebar = ui.toggleSidebar;
window.toggleMobileNav = ui.toggleMobileNav;
window.closeMobileNav = ui.closeMobileNav;
window.logout = ui.logout;

/**
 * GESTIÓN DE AUTENTICACIÓN EN UI (Mantener aquí por ahora o mover a ui.js)
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

// --- INICIALIZACIÓN GLOBAL ---
document.addEventListener('DOMContentLoaded', () => {
    window.updateAuthNav();

    // Restaurar estado del sidebar colapsado
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

// Cerrar modales con tecla Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal[style*="display: block"]').forEach(m => {
            m.style.display = 'none';
            m.querySelectorAll('.error-msg').forEach(el => el.style.display = 'none');
        });
    }
});
