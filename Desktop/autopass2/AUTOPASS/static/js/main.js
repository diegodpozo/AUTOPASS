/* --- UTILIDADES GLOBALES Y MANEJO DE UI --- */

/**
 * Convierte un string a Formato de Título (Capitalización de cada palabra).
 */
const toTitle = s => {
    if (!s || typeof s !== 'string') return '---';
    return s.toLowerCase()
            .split(' ')
            .filter(word => word.length > 0)
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
};

/**
 * Formatea una fecha ISO o string (YYYY-MM-DD HH:MM) a formato legible (DD/MM/YYYY HH:MM).
 */
function formatDate(isoStr) {
    if (!isoStr) return '---';
    // Reemplazamos guiones por barras y espacios por T si es necesario para asegurar compatibilidad
    const normalizedStr = isoStr.replace(/-/g, "/");
    const d = new Date(normalizedStr);
    
    if (isNaN(d.getTime())) return isoStr; // Fallback al original si falla el parseo

    const day = d.getDate().toString().padStart(2, '0');
    const month = (d.getMonth() + 1).toString().padStart(2, '0');
    const year = d.getFullYear();
    const hours = d.getHours().toString().padStart(2, '0');
    const mins = d.getMinutes().toString().padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${mins}`;
}

// --- LÓGICA DE BARRA LATERAL (SIDEBAR) ---
function toggleMobileNav() {
    const sidebar = document.getElementById('main-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.toggle('mobile-open');
    if (overlay) overlay.classList.toggle('active');
}

function closeMobileNav() {
    const sidebar = document.getElementById('main-sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar) sidebar.classList.remove('mobile-open');
    if (overlay) overlay.classList.remove('active');
}

function toggleSidebar() {
    const layout = document.querySelector('.layout-with-sidebar');
    const sidebar = document.querySelector('.sidebar');
    const toggleIcon = document.querySelector('.sidebar-toggle i');
    const isCollapsed = layout.classList.toggle('collapsed');
    sidebar.classList.toggle('collapsed');
    
    if (toggleIcon) {
        toggleIcon.className = isCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
    }
    
    localStorage.setItem('sidebarCollapsed', isCollapsed);
}

// --- GESTIÓN DE AUTENTICACIÓN EN UI ---
function updateAuthNav() {
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
            profile.href = localStorage.getItem('rol') === 'admin' ? '/dashboard' : '/perfil';
        }
    }
    if (logout) logout.style.display = loggedIn ? 'inline-block' : 'none';
}

// --- MANEJO DE MODALES ---
function switchModal(oldId, newId) { 
    closeModal(oldId); 
    openModal(newId); 
}

function togglePasswordVisibility(inputId, iconEl) {
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

function openModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.display = 'block';
    const emailInput = el.querySelector('input[type="email"]');
    if (emailInput) setTimeout(() => emailInput.focus(), 100);
}

function closeModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.display = 'none';
    document.querySelectorAll('.error-msg').forEach(e => e.style.display = 'none');
}

function logout() {
    localStorage.clear();
    window.location.href = '/';
}

// --- NOTIFICACIONES Y CONFIRMACIONES ---
function showToast(msg) {
    const container = document.getElementById('toast-container'); 
    if (!container) return;
    const t = document.createElement('div'); 
    t.className = 'toast'; 
    t.innerText = msg;
    container.appendChild(t); 
    setTimeout(() => t.remove(), 3000);
}

function showConfirm(title, msg) {
    return new Promise((resolve) => {
        const modal = document.getElementById('modal-confirm');
        const titleEl = document.getElementById('confirm-title');
        const msgEl = document.getElementById('confirm-msg');
        const btnOk = document.getElementById('confirm-btn-ok');
        const btnCancel = document.getElementById('confirm-btn-cancel');

        if (!modal || !btnOk || !btnCancel) return resolve(false);

        titleEl.innerText = title || '¿Estás seguro?';
        if (msg.includes('<')) {
            msgEl.innerHTML = msg;
        } else {
            msgEl.innerText = msg || 'Esta acción no se puede deshacer.';
        }
        
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';

        const handleResponse = (result) => {
            modal.style.display = 'none';
            btnOk.onclick = null;
            btnCancel.onclick = null;
            resolve(result);
        };

        btnOk.onclick = () => handleResponse(true);
        btnCancel.onclick = () => handleResponse(false);
        
        modal.onclick = (e) => { if(e.target === modal) handleResponse(false); };
    });
}

// --- INICIALIZACIÓN GLOBAL ---
document.addEventListener('DOMContentLoaded', () => {
    updateAuthNav();

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
