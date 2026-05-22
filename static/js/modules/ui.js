/**
 * UI MODULE
 * Gestión de elementos comunes de la interfaz (Modales, Sidebar, Password).
 */

/**
 * Abre un modal por ID.
 */
export function openModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.display = 'block';
    const emailInput = el.querySelector('input[type="email"]');
    if (emailInput) setTimeout(() => emailInput.focus(), 100);
}

/**
 * Cierra un modal por ID.
 */
export function closeModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.display = 'none';
    document.querySelectorAll('.error-msg').forEach(e => e.style.display = 'none');
}

/**
 * Intercambia un modal por otro.
 */
export function switchModal(oldId, newId) { 
    closeModal(oldId); 
    openModal(newId); 
}

/**
 * Alterna visibilidad de campos de contraseña.
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
 * Lógica del Sidebar (Escritorio y Móvil).
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
 * Cierra la sesión del usuario.
 */
export function logout() {
    localStorage.clear();
    window.location.href = '/';
}
