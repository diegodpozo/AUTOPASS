import { showToast } from './modules/utils.js';

/**
 * CONTACTO PUENTE
 */

document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.onsubmit = (e) => {
            e.preventDefault();
            showToast('¡Mensaje enviado con éxito! Un asesor te contactará a la brevedad.', 'success');
            e.target.reset();
        };
    }
});
