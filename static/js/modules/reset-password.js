/**
 * RESET PASSWORD MODULO
 * VALIDACION EN VIVO DE NUEVA CLAVE Y ENVIO DEL TOKEN DE RECUPERACION.
 */
import api from './api.js';
import { evaluatePassword, initPasswordValidation } from './auth.js';

const form = document.getElementById('resetPasswordForm');
const passwordInput = document.getElementById('reset-password');
const confirmInput = document.getElementById('reset-password-confirm');

// Validación en vivo de requisitos (reutiliza la lógica de auth.js)
initPasswordValidation(
    'reset-password', 'reset-password-confirm', null,
    'reset-req-len', 'reset-req-up', 'reset-req-spec', 'reset-req-match'
);

// Obtener token de la URL
const urlParams = new URLSearchParams(window.location.search);
const token = urlParams.get('token');

// El link sirve tanto para recuperación como para la invitación de un Admin General.
// El propósito viene en el payload del JWT (no es secreto): si es "activation",
// se adapta el texto para dar la bienvenida en lugar del tono de recuperación.
function leerProposito(jwt) {
    try {
        const payload = JSON.parse(atob(jwt.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')));
        return payload.purpose;
    } catch {
        return null;
    }
}

if (token && leerProposito(token) === 'activation') {
    const subtitulo = document.getElementById('reset-subtitle');
    if (subtitulo) subtitulo.innerText = 'Bienvenido/a a AUTOPASS. Configurá tu contraseña para empezar a usar el panel.';
}

if (!token) {
    document.getElementById('reset-error').innerText = "Falta el token de recuperación. El enlace es inválido.";
    form.style.opacity = "0.5";
    form.style.pointerEvents = "none";
}

const esPasswordValida = () => evaluatePassword(passwordInput.value, confirmInput.value).valid;

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (!esPasswordValida()) return;

    const btn = form.querySelector('button');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Procesando...';

    const res = await api.post('/auth/reset-password', {
        token: token,
        new_password: passwordInput.value
    });

    if (res && res.ok) {
        document.getElementById('reset-form-panel').style.display = 'none';
        document.getElementById('reset-success-panel').style.display = 'block';
    } else {
        document.getElementById('reset-error').innerText = (res && res.error) || "Error al restablecer contraseña.";
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Actualizar Contraseña';
    }
});