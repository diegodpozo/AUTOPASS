// Helpers for reservation onboarding modal and actions
import { openModal, closeModal } from './ui.js';
export function openReservationOnboarding() {
    const modal = document.getElementById('reservation-onboarding-modal');
    if (!modal) return;
    // mover modal al body para que no sea afectado por el blur del contenedor
    try {
        if (modal.parentElement !== document.body) document.body.appendChild(modal);
    } catch (e) { console.warn('[ONBOARDING] no pude mover modal al body', e); }

    // asegurar que el modal sea visible y encima de todo mediante clase active
    openModal('reservation-onboarding-modal');
    setTimeout(() => {
        modal.classList.add('active');
    }, 15);

    // aplicar efecto blur al fondo (sección inicio)
    try {
        const section = document.getElementById('section-inicio');
        if (section) {
            section.dataset._prevPointer = section.style.pointerEvents || '';
            section.dataset._prevFilter = section.style.filter || '';
            section.style.filter = 'blur(6px)';
            section.style.pointerEvents = 'none';
            section.setAttribute('aria-hidden', 'true');
        }
    } catch (e) { console.warn('[ONBOARDING] no pude aplicar blur al fondo', e); }
}

export function closeReservationOnboarding() {
    const modal = document.getElementById('reservation-onboarding-modal');
    if (!modal) return;
    modal.classList.remove('active');
    
    // esperar que termine la transición de opacidad antes de ocultar
    setTimeout(() => {
        closeModal('reservation-onboarding-modal');
    }, 300);
    
    // quitar blur
    try {
        const section = document.getElementById('section-inicio');
        if (section) {
            section.style.filter = section.dataset._prevFilter || '';
            section.style.pointerEvents = section.dataset._prevPointer || '';
            section.removeAttribute('aria-hidden');
            delete section.dataset._prevFilter;
            delete section.dataset._prevPointer;
        }
    } catch (e) { console.warn('[ONBOARDING] no pude quitar blur', e); }
    // no marcar visto aquí — marcar sólo cuando usuario omite explícitamente o completa tour
}

export function checkFirstLoginOnboarding(user, vehicles = [], reservations = []) {
    const userId = user && user.id ? user.id : (user && user.email ? user.email : null);
    const userTourKey = userId ? `autopass_tour_seen_${userId}` : 'autopass_tour_seen_guest';

    const hasSeen = userId
        ? localStorage.getItem(userTourKey) === '1'
        : (localStorage.getItem(userTourKey) === '1' || localStorage.getItem('seen_reservation_onboarding') === '1');

    const hasExistingData = (Array.isArray(vehicles) && vehicles.length > 0) || (Array.isArray(reservations) && reservations.length > 0);

    if (hasSeen || hasExistingData) {
        try {
            if (userId) localStorage.setItem(userTourKey, '1');
            localStorage.setItem('seen_reservation_onboarding', '1');
        } catch (e) { /* ignore */ }
        return;
    }

    try {
        if (userId) localStorage.setItem(userTourKey, '1');
        localStorage.setItem('seen_reservation_onboarding', '1');
    } catch (e) { console.warn('[ONBOARDING] Error guardando visto flag:', e); }

    openReservationOnboarding();
}

export function skipReservationOnboarding() {
    // marcar como visto y cerrar
    try {
        localStorage.setItem('seen_reservation_onboarding','1');
        const userData = JSON.parse(localStorage.getItem('userData') || '{}');
        if (userData && userData.id) {
            localStorage.setItem(`autopass_tour_seen_${userData.id}`, '1');
        }
    } catch (e) { console.warn('[ONBOARDING] no pude setear seen flag', e); }
    closeReservationOnboarding();
}

export function startReservationOnboarding() {
    // Marcar como visto
    try {
        localStorage.setItem('seen_reservation_onboarding','1');
        const userData = JSON.parse(localStorage.getItem('userData') || '{}');
        if (userData && userData.id) {
            localStorage.setItem(`autopass_tour_seen_${userData.id}`, '1');
        }
    } catch (e) { console.warn('[ONBOARDING] no pude setear seen flag', e); }

    // Cerrar modal y quitar blur para que el quick-add sea totalmente usable
    try {
        closeReservationOnboarding();
    } catch (e) { console.warn('[ONBOARDING] closeReservationOnboarding falló', e); }

    if (window.showQuickAddVehicle) window.showQuickAddVehicle();
    setTimeout(() => {
        const input = document.querySelector('#quick-add-vehicle-form [name="patente"]');
        if (input) input.focus();
    }, 250);

    // intentar iniciar un mini-tour específico para quick-add si está disponible
    try {
        import('./tour.js')
            .then(m => {
                if (m && typeof m.startQuickAddTour === 'function') {
                    m.startQuickAddTour();
                }
            })
            .catch(err => console.warn('[ONBOARDING] no pude iniciar quick-add tour', err));
    } catch (e) { console.warn('[ONBOARDING] error importando tour para quick-add', e); }

    // Esperar evento global 'vehicle:added' para continuar el flujo principal del tour
    const handler = async (ev) => {
        try {
            document.removeEventListener('vehicle:added', handler);
            // pequeño delay para que la UI se estabilice y el formulario de reserva se abra
            // pequeño delay para que la UI se estabilice y el formulario de reserva se abra
            setTimeout(async () => {
                try {
                    const m = await import('./tour.js');
                    if (m && typeof m.startPostAddReservationTour === 'function') {
                        m.startPostAddReservationTour();
                    } else if (typeof window.startPostAddReservationTour === 'function') {
                        window.startPostAddReservationTour();
                    }
                } catch (err) { console.error('[ONBOARDING] Error iniciando tour post-add:', err); }
            }, 450);
        } catch (e) { console.error('[ONBOARDING] listener error', e); }
    };
    document.addEventListener('vehicle:added', handler);
}

export async function openLegalModal(type) {
    const modal = document.getElementById('modal-legal-terms');
    const titleEl = document.getElementById('legal-modal-title');
    const bodyEl = document.getElementById('legal-modal-body');
    if (!modal || !titleEl || !bodyEl) return;
    
    bodyEl.innerHTML = '<div style="text-align:center; padding:40px;"><i class="fas fa-spinner fa-spin" style="font-size:2rem; color:var(--dorado);"></i></div>';
    titleEl.innerText = type === 'privacidad' ? 'Políticas de Privacidad' : 'Términos y Condiciones';
    openModal('modal-legal-terms');
    
    try {
        const res = await fetch(type === 'privacidad' ? '/privacidad' : '/terminos');
        const html = await res.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const content = doc.querySelector('.legal-body');
        if (content) {
            let bodyHtml = content.innerHTML;
            bodyHtml = bodyHtml.replace('{{ settings.CONTACT_PRIVACY }}', 'privacidad@autopass.com.ar');
            bodyEl.innerHTML = bodyHtml;
        } else {
            bodyEl.innerHTML = '<p style="color:red; text-align:center; padding:20px;">Error al extraer el contenido legal.</p>';
        }
    } catch (e) {
        console.error('[LEGAL MODAL] Error:', e);
        bodyEl.innerHTML = '<p style="color:red; text-align:center; padding:20px;">Error de conexión al cargar el contenido.</p>';
    }
}

export function closeLegalModal() {
    if (document.getElementById('modal-legal-terms')) closeModal('modal-legal-terms');
}

