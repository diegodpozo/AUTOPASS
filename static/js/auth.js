import * as auth from './modules/auth.js';

/**
 * PUENTE: AUTH.JS
 * EXPONE LA LOGICA DE AUTENTICACION AL AMBITO GLOBAL Y MANEJA LA INICIALIZACION DE FORMULARIOS.
 */

window.initPasswordValidation = auth.initPasswordValidation;
window.startOAuth = auth.startOAuth;

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

    const oauthForm = document.getElementById('oauthSignupForm');
    if (oauthForm) {
        oauthForm.onsubmit = auth.handleOAuthComplete;
    }

    auth.loadOAuthProviders();
    auth.processOAuthCallback();
});

const authBtnDefaults = {
    'loginForm': 'Ingresar',
    'registerForm': '<i class="fas fa-user-plus"></i> Finalizá tu Registro',
    'recoveryForm': '<i class="fas fa-paper-plane"></i> Enviar Enlace',
    'oauthSignupForm': '<i class="fas fa-user-check"></i> Finalizá tu Registro'
};

window.addEventListener('pageshow', () => {
    Object.entries(authBtnDefaults).forEach(([formId, html]) => {
        const form = document.getElementById(formId);
        if (!form) return;
        const btn = form.querySelector('button[type="submit"]');
        if (btn && btn.disabled) {
            btn.innerHTML = html;
            btn.disabled = false;
        }
    });
});
