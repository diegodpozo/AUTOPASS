import * as auth from './modules/auth.js';

/**
 * BRIDGE: auth.js
 * Expone la lógica de autenticación al ámbito global y maneja la inicialización de formularios.
 */

window.initPasswordValidation = auth.initPasswordValidation;

document.addEventListener('DOMContentLoaded', () => {
    auth.initPasswordValidation('reg-password', 'reg-password-confirm', 'reg-password-strength', 'reg-req-len', 'reg-req-up', 'reg-req-spec', 'reg-req-match');

    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.onsubmit = auth.handleLogin;
    }

    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.onsubmit = auth.handleRegister;
    }
});
