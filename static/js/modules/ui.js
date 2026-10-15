/**
 * UI MODULO
 * GESTION DE ELEMENTOS COMUNES DE LA INTERFAZ (MODALES, SIDEBAR, PASSWORD).
 */

// Los tres contenedores que se comportan como dialogo modal.
const SELECTOR_DIALOGO = '.modal, .modal-premium, .onboarding-overlay-premium';

// Clases que se abren con display: flex (centradas); el resto, con block.
const CLASES_FLEX = ['modal-premium', 'onboarding-overlay-premium', 'modal--centered'];

// Elementos que pueden recibir foco con Tab dentro de un dialogo.
const SELECTOR_FOCABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

// Disparador de cada dialogo abierto: { id del dialogo: elemento que lo abrio }.
// Es a quien hay que devolverle el foco al cerrar: el disparador queda tapado
// por el overlay mientras el dialogo esta encima.
const disparadores = new Map();

function visible(el) {
    return getComputedStyle(el).display !== 'none';
}

/**
 * DIALOGO DE ARRIBA: el visible de mayor z-index (empate: el ultimo del DOM, por
 * eso #modal-choice, declarado despues, gana sobre #modal-confirm).
 */
function dialogoDeArriba() {
    const abiertos = [...document.querySelectorAll(SELECTOR_DIALOGO)].filter(visible);
    if (!abiertos.length) return null;
    const z = (el) => parseInt(getComputedStyle(el).zIndex, 10) || 0;
    return abiertos.reduce((arriba, el) => (z(el) >= z(arriba) ? el : arriba));
}

function focables(raiz) {
    return [...raiz.querySelectorAll(SELECTOR_FOCABLE)].filter(el => el.getClientRects().length > 0);
}

/**
 * CONTROL DE CIERRE del dialogo: el que ui.js activa al cerrar con Escape.
 * data-modal-close es explicito; las clases cubren el boton del macro
 * modal_header y el cierre de los modales premium.
 */
function controlDeCierre(el) {
    return el.querySelector('[data-modal-close]') || el.querySelector('.close-btn, .modal-close-top');
}

function devolverFoco(id) {
    const disparador = disparadores.get(id);
    disparadores.delete(id);
    if (disparador && document.contains(disparador) && disparador.getClientRects().length > 0) {
        disparador.focus();
    }
}

/**
 * ABRE UN MODAL POR ID.
 */
export function openModal(id) {
    const el = document.getElementById(id);
    if (!el) return;

    // Quien abrio el modal, para devolverle el foco al cerrar. Si el modal se
    // abre solo (al cargar la pagina) no hay disparador y no se guarda nada.
    const activo = document.activeElement;
    if (el.id && activo && activo !== document.body && !el.contains(activo)) {
        disparadores.set(el.id, activo);
    }

    el.style.display = CLASES_FLEX.some(c => el.classList.contains(c)) ? 'flex' : 'block';

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

    // P2.6 UX/UI: autofocus al primer campo editable VISIBLE (input/select/textarea).
    // Se exige visible porque un campo oculto (pestana cerrada, bloque colapsado) no
    // se puede enfocar: antes se elegia el primero del DOM y el foco quedaba afuera
    // del dialogo. Si el dialogo no tiene campos (confirmacion, eleccion) se enfoca
    // el propio dialogo: sin foco adentro, el lector de pantalla no anuncia el
    // dialogo y el primer Tab se iria a la pagina de atras.
    const candidatos = el.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([disabled]), select:not([disabled]), textarea:not([disabled])');
    const objetivo = [...candidatos].find(c => c.getClientRects().length > 0) || el;
    if (objetivo === el && !el.hasAttribute('tabindex')) el.setAttribute('tabindex', '-1');
    setTimeout(() => objetivo.focus(), 100);
}

/**
 * CIERRA UN MODAL POR ID.
 */
export function closeModal(id) {
    const el = document.getElementById(id);
    if (!el) return;
    el.style.display = 'none';
    document.querySelectorAll('.error-msg').forEach(e => e.style.display = 'none');
    devolverFoco(id);
}

/**
 * ENCIERRO DEL FOCO (Tab) Y CIERRE CON ESCAPE (Escape).
 *
 * Un solo listener resuelve por DOM cual es el dialogo de arriba, asi tambien
 * cubre los que se muestran sin pasar por openModal (showConfirm/showChoice,
 * pase digital, ticket de soporte, onboarding). Solo intercepta Tab y Escape:
 * el foco programatico (tours, autofocus) no se toca.
 */
document.addEventListener('keydown', (e) => {
    const dialogo = dialogoDeArriba();
    if (!dialogo) return;

    if (e.key === 'Escape') {
        e.preventDefault();
        cerrarDialogoDeArriba(dialogo);
        return;
    }
    if (e.key !== 'Tab') return;

    const lista = focables(dialogo);
    if (!lista.length) {
        e.preventDefault();
        dialogo.focus();
        return;
    }
    const primero = lista[0];
    const ultimo = lista[lista.length - 1];
    const actual = document.activeElement;

    if (!dialogo.contains(actual)) {
        e.preventDefault();
        (e.shiftKey ? ultimo : primero).focus();
    } else if (e.shiftKey && actual === primero) {
        e.preventDefault();
        ultimo.focus();
    } else if (!e.shiftKey && actual === ultimo) {
        e.preventDefault();
        primero.focus();
    }
});

/**
 * CIERRA EL DIALOGO DE ARRIBA ACTIVANDO SU CONTROL DE CIERRE.
 *
 * Se activa el control en vez de ocultar el contenedor a mano para que corra la
 * logica propia de cada modal: resolver la promesa de showConfirm/showChoice,
 * sacar el blur del onboarding, frenar el reloj virtual, limpiar el ticket.
 */
function cerrarDialogoDeArriba(dialogo) {
    const control = controlDeCierre(dialogo);
    if (control) {
        control.click();
        if (visible(dialogo)) dialogo.style.display = 'none';  // cierre condicional
    } else {
        dialogo.style.display = 'none';
    }
    devolverFoco(dialogo.id);
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
 * `triggerEl` es el <button class="toggle-password"> que envuelve al icono
 * (accesible por teclado); se acepta tambien el <i> suelto por compatibilidad.
 * Mantiene aria-pressed/aria-label para que el cambio de estado se anuncie.
 */
export function togglePasswordVisibility(inputId, triggerEl) {
    const input = document.getElementById(inputId);
    if (!input || !triggerEl) return;

    const icon = triggerEl.tagName === 'BUTTON' ? triggerEl.querySelector('i') : triggerEl;

    const wasHidden = input.type === 'password';
    input.type = wasHidden ? 'text' : 'password';

    if (icon) {
        icon.classList.toggle('fa-eye', !wasHidden);
        icon.classList.toggle('fa-eye-slash', wasHidden);
    }

    if (triggerEl.hasAttribute('aria-pressed')) {
        triggerEl.setAttribute('aria-pressed', String(wasHidden));
        triggerEl.setAttribute('aria-label', wasHidden ? 'Ocultar contraseña' : 'Mostrar contraseña');
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
