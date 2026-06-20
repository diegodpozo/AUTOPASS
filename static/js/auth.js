import * as auth from './modules/auth.js';

/**
 * PUENTE: AUTH.JS
 * EXPONE LA LOGICA DE AUTENTICACION AL AMBITO GLOBAL Y MANEJA LA INICIALIZACION DE FORMULARIOS.
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

    const recoveryForm = document.getElementById('recoveryForm');
    if (recoveryForm) {
        recoveryForm.onsubmit = auth.handleRecovery;
    }
});
