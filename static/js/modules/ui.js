/**
 * UI MODULO
 * GESTION DE ELEMENTOS COMUNES DE LA INTERFAZ (MODALES, SIDEBAR, PASSWORD).
 */

/**
 * ABRE UN MODAL POR ID.
 */
export function openModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.display = 'block';

    // Restablecer botones de submit que hayan quedado deshabilitados o con spinner
    const submitBtn = el.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = false;
        if (submitBtn.dataset.originalHtml) {
            submitBtn.innerHTML = submitBtn.dataset.originalHtml;
        } else if (id === 'loginModal') {
            submitBtn.innerHTML = 'INICIAR SESIÓN';
        } else if (id === 'registerModal') {
            submitBtn.innerHTML = 'REGISTRARME';
        }
    }

    const emailInput = el.querySelector('input[type="email"]');
    if (emailInput) setTimeout(() => emailInput.focus(), 100);
}

/**
 * CIERRA UN MODAL POR ID.
 */
export function closeModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.display = 'none';
    document.querySelectorAll('.error-msg').forEach(e => e.style.display = 'none');
}

/**
 * INTERCAMBIA UN MODAL POR OTRO.
 */
export function switchModal(oldId, newId) { 
    closeModal(oldId); 
    openModal(newId); 
}

/**
 * ALTERNA VISIBILIDAD DE CAMPOS DE CONTRASENA.
 */
export function togglePasswordVisibility(inputId, iconEl) {
    const input = document.getElementById(inputId);
    if (!input || !iconEl) return;
    
    if (input.type === 'password') {
        input.type = 'text';
        iconEl.classList.remove('fa-eye');
        iconEl.classList.add('fa-eye-slash');
    } else {
        input.type = 'password';
        iconEl.classList.remove('fa-eye-slash');
        iconEl.classList.add('fa-eye');
    }
}

/**
 * LOGICA DEL SIDEBAR (ESCRITORIO Y MOVIL).
 */
export function toggleSidebar() {
    const layout = document.querySelector('.layout-with-sidebar');
    const sidebar = document.querySelector('.sidebar');
    const toggleIcon = document.querySelector('.sidebar-toggle i');
    if (!layout || !sidebar) return;

    const isCollapsed = layout.classList.toggle('collapsed');
    sidebar.classList.toggle('collapsed');
    
    if (toggleIcon) {
        toggleIcon.className = isCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
    }
    localStorage.setItem('sidebarCollapsed', isCollapsed);
}

export function toggleMobileNav() {
    const sidebar = document.getElementById('main-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.toggle('mobile-open');
    if (overlay) overlay.classList.toggle('active');
}

export function closeMobileNav() {
    const sidebar = document.getElementById('main-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('active');
}

export function toggleNuevoVinculo() {
    const container = document.getElementById('vinculo-container');
    const trigger = document.querySelector('.register-trigger-card');
    const arrow = document.getElementById('vinculo-arrow');
    
    if (!container) return;

    const isOpen = container.classList.toggle('open');
    if (trigger) trigger.classList.toggle('open');
    if (arrow) {
        const isMobile = window.innerWidth <= 900;
        if (isMobile) {
            arrow.style.transform = isOpen ? 'rotate(270deg)' : 'rotate(90deg)';
        } else {
            arrow.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0deg)';
        }
    }
}

export function toggleHistorial() {
    const container = document.getElementById('historial-container');
    const arrow = document.getElementById('historial-arrow');
    if (!container) return;
    const isOpen = container.classList.toggle('open');
    if (arrow) arrow.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0deg)';
}

/**
 * CIERRA LA SESION DEL USUARIO.
 */
export function logout() {
    // Preservar flags de tour visto por usuario antes de limpiar localStorage
    const tourKeys = {};
    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (key && (key.startsWith('autopass_tour_seen_') || key.startsWith('seen_reservation_onboarding'))) {
            tourKeys[key] = localStorage.getItem(key);
        }
    }

    localStorage.clear();

    // Restaurar los flags de tour para no reiniciar la guía en posteriores inicios de sesión
    Object.keys(tourKeys).forEach(k => localStorage.setItem(k, tourKeys[k]));

    window.location.href = '/';
}
