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
    const sidebar = document.getElementById('main-sidebar') || document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (!sidebar) return;
    const isOpen = sidebar.classList.toggle('mobile-open');
    if (overlay) overlay.classList.toggle('active', isOpen);
    document.body.style.overflow = isOpen ? 'hidden' : '';
}

export function closeMobileNav() {
    const sidebar = document.getElementById('main-sidebar') || document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('active');
    document.body.style.overflow = '';
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
    const token = localStorage.getItem('token');

    // Preservar flags de tour y device_id antes de limpiar localStorage
    const savedKeys = {};
    const keepPrefixes = ['autopass_tour_seen_'];
    const keepExact = ['autopass_device_id'];

    for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        if (!key) continue;
        if (keepExact.includes(key) || keepPrefixes.some(p => key.startsWith(p))) {
            savedKeys[key] = localStorage.getItem(key);
        }
    }

    // REVOCAR SESION EN EL BACKEND (best-effort, no bloquea el logout local)
    if (token) {
        try {
            fetch('/v1/auth/logout', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ device_id: savedKeys['autopass_device_id'] || '' }),
            }).catch(() => {});
        } catch (e) { /* ignora fallos de red */ }
    }

    localStorage.clear();

    // Restaurar los flags y device_id preservados
    Object.keys(savedKeys).forEach(k => localStorage.setItem(k, savedKeys[k]));

    window.location.href = '/';
}
