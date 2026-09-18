import api from './api.js';
import { toTitle, showToast } from './utils.js';
import { switchModal, openModal } from './ui.js';

/**
 * AUTH MODULO
 * LOGICA DE INICIO DE SESION, REGISTRO Y VALIDACION DE SEGURIDAD.
 */

/**
 * EVALUA LOS REQUISITOS DE SEGURIDAD DE UNA CONTRASEÑA (REUTILIZADO POR
 * initPasswordValidation, reset_password Y EL FLUJO DE REGISTRO).
 */
export function evaluatePassword(value, confirmValue) {
    const val = value || '';
    const isLen = val.length >= 8;
    const isUp = /[A-Z]/.test(val);
    const isSpec = /[!@#$%^&*(),.?":{}|<>]/.test(val);
    const isMatch = val.length > 0 && val === (confirmValue || '');
    return { isLen, isUp, isSpec, isMatch, valid: isLen && isUp && isSpec && isMatch };
}

export function initPasswordValidation(passId, confirmId, strengthId, reqLenId, reqUpId, reqSpecId, reqMatchId) {
    const regPass = document.getElementById(passId);
    const regPassConfirm = document.getElementById(confirmId);
    const strengthMeter = document.getElementById(strengthId);
    const reqLen = document.getElementById(reqLenId);
    const reqUp = document.getElementById(reqUpId);
    const reqSpec = document.getElementById(reqSpecId);
    const reqMatch = document.getElementById(reqMatchId);

    if (regPass) {
        const validatePass = () => {
            if (strengthMeter) strengthMeter.className = 'strength-meter';

            const r = evaluatePassword(regPass.value, regPassConfirm ? regPassConfirm.value : '');

            const updateReq = (el, condition) => {
                if (!el) return;
                const icon = el.querySelector('i');
                if (condition) { 
                    el.classList.add('satisfied'); 
                    if (icon) icon.className = 'fas fa-check-circle'; 
                } else { 
                    el.classList.remove('satisfied'); 
                    if (icon) icon.className = 'far fa-circle'; 
                }
            };
            
            updateReq(reqLen, r.isLen); 
            updateReq(reqUp, r.isUp); 
            updateReq(reqSpec, r.isSpec); 
            updateReq(reqMatch, r.isMatch);
            
            if (strengthMeter) {
                if (regPass.value.length === 0) return;
                let strength = (r.isLen ? 1 : 0) + (r.isUp ? 1 : 0) + (r.isSpec ? 1 : 0);
                if (strength === 1) strengthMeter.classList.add('strength-weak');
                if (strength === 2) strengthMeter.classList.add('strength-medium');
                if (strength === 3) strengthMeter.classList.add('strength-strong');
            }
        };
        regPass.addEventListener('input', validatePass);
        if (regPassConfirm) regPassConfirm.addEventListener('input', validatePass);
    }
}

function getDeviceId() {
    let id = localStorage.getItem('autopass_device_id');
    if (!id) {
        id = 'dev-' + Math.random().toString(36).slice(2) + '-' + Date.now().toString(36);
        localStorage.setItem('autopass_device_id', id);
    }
    return id;
}

export async function handleLogin(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorMsg = document.getElementById('login-error');
    const originalText = btn.innerHTML;
    btn.dataset.originalHtml = originalText;

    errorMsg.style.display = 'none';
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Ingresando...';
    btn.disabled = true;

    const res = await api.post('/auth/login', { email, password, device_id: getDeviceId() });
    
    if (res && res.ok) {
        const data = res.data;
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('rol', data.rol);
        localStorage.setItem('nombre', toTitle(data.nombre));
        localStorage.setItem('apellido', toTitle(data.apellido));
        localStorage.setItem('sucursal', data.sucursal || '');
        
        // Restablecer el estado del botón antes de navegar para evitar congelamientos en BFCache
        btn.innerHTML = originalText;
        btn.disabled = false;
        const modal = document.getElementById('loginModal');
        if (modal) modal.style.display = 'none';

        if (data.nuevo_dispositivo) {
            sessionStorage.setItem('autopass_device_alert', '1');
        }

        const isStaffOrAdmin = ['admin', 'local_admin', 'staff'].includes(data.rol);
        window.location.href = isStaffOrAdmin ? '/dashboard' : '/perfil';
    } else {
        errorMsg.innerText = res ? (res.error || 'Error al iniciar sesión') : 'Error de conexión';
        errorMsg.style.display = 'block';
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

export async function handleRegister(e) {
    e.preventDefault();
    const errorMsg = document.getElementById('register-error');
    errorMsg.style.display = 'none';

    const dni = document.getElementById('reg-dni').value.replace(/\D/g, '');
    const password = document.getElementById('reg-password').value;
    const passwordConfirm = document.getElementById('reg-password-confirm').value;
    const email = document.getElementById('reg-email').value;
    const telefono = document.getElementById('reg-tel').value.replace(/\D/g, '');

    if (password !== passwordConfirm) {
        errorMsg.innerText = 'Las contraseñas no coinciden';
        errorMsg.style.display = 'block';
        return;
    }

    if (dni.length < 7 || dni.length > 8) {
        errorMsg.innerText = 'El DNI debe tener 7 u 8 números';
        errorMsg.style.display = 'block';
        return;
    }

    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        errorMsg.innerText = 'Ingresá un correo electrónico válido';
        errorMsg.style.display = 'block';
        return;
    }

    if (telefono.length < 10) {
        errorMsg.innerText = 'El teléfono debe tener al menos 10 dígitos';
        errorMsg.style.display = 'block';
        return;
    }
    
    if (!evaluatePassword(password, passwordConfirm).valid) {
        errorMsg.innerText = 'La contraseña no cumple con los requisitos de seguridad';
        errorMsg.style.display = 'block';
        return;
    }

    const payload = {
        nombre: document.getElementById('reg-nombre').value,
        apellido: document.getElementById('reg-apellido').value,
        dni: dni,
        telefono: telefono,
        email: email,
        password: password
    };

    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerText;
    btn.innerText = 'Procesando...';
    btn.disabled = true;

    const res = await api.post('/auth/register', payload);

    if (res && res.ok) {
        showToast('¡Registro exitoso! Bienvenido a AUTOPASS', 'success');
        setTimeout(() => switchModal('registerModal', 'loginModal'), 1500);
    } else {
        errorMsg.innerText = res ? (res.error || 'Error en el registro') : 'Error de conexión';
        errorMsg.style.display = 'block';
        btn.innerText = originalText;
        btn.disabled = false;
    }
}

export async function handleRecovery(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const email = document.getElementById('recovery-email').value;
    const errorMsg = document.getElementById('recovery-error');
    const successMsg = document.getElementById('recovery-success');
    const originalText = btn.innerHTML;

    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Enviando...';
    btn.disabled = true;

    try {
        const res = await api.post('/auth/forgot-password', { email });
        
        if (res && res.ok) {
            successMsg.innerText = res.data.message;
            successMsg.style.display = 'block';
            e.target.reset();
        } else {
            errorMsg.innerText = res ? (res.error || 'Error al solicitar recuperación') : 'Error de conexión';
            errorMsg.style.display = 'block';
        }
    } catch (err) {
        errorMsg.innerText = 'Error inesperado. Intentá de nuevo más tarde.';
        errorMsg.style.display = 'block';
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

/**
 * LOGIN SOCIAL (OAUTH 2.0)
 */

let pendingOAuthCode = null;

export function startOAuth(provider) {
    window.location.href = `/v1/auth/oauth/${provider}/authorize`;
}

export async function loadOAuthProviders() {
    const res = await api.get('/auth/oauth/providers');
    if (!res || !res.ok) return;
    const enabled = (res.data.providers || []).map(p => p.id);

    document.querySelectorAll('.oauth-btn').forEach(btn => {
        const pid = btn.dataset.oauthProvider;
        btn.style.display = enabled.includes(pid) ? '' : 'none';
    });
    document.querySelectorAll('.oauth-block').forEach(block => {
        const anyVisible = Array.from(block.querySelectorAll('.oauth-btn'))
            .some(b => b.style.display !== 'none');
        block.style.display = anyVisible ? '' : 'none';
    });
}

export function processOAuthCallback() {
    if (!window.location.hash || !window.location.hash.startsWith('#oauth')) return;
    const params = new URLSearchParams(window.location.hash.substring(1));

    const token = params.get('oauth_token');
    if (token) {
        window.location.hash = '';
        localStorage.setItem('token', token);
        localStorage.setItem('rol', params.get('oauth_rol') || 'user');
        const nombre = params.get('oauth_nombre');
        const apellido = params.get('oauth_apellido');
        if (nombre) localStorage.setItem('nombre', toTitle(nombre));
        if (apellido) localStorage.setItem('apellido', toTitle(apellido));
        const isStaffOrAdmin = ['admin', 'local_admin', 'staff'].includes(localStorage.getItem('rol'));
        window.location.href = isStaffOrAdmin ? '/dashboard' : '/perfil';
        return;
    }

    const signupCode = params.get('oauth_signup');
    if (signupCode) {
        const data = {
            email: params.get('oauth_email') || '',
            provider: params.get('oauth_provider') || '',
            nombre: params.get('oauth_nombre') || '',
            apellido: params.get('oauth_apellido') || ''
        };
        window.location.hash = '';
        prefillOAuthSignup(signupCode, data);
        return;
    }

    const oauthError = params.get('oauth_error');
    if (oauthError) {
        window.location.hash = '';
        const messages = {
            denegado: 'Cancelaste el acceso con la red social. Podés seguir con tu correo y contraseña.',
            state_invalido: 'La solicitud no fue válida. Intentá de nuevo.',
            sin_codigo: 'La red social no devolvió el código de acceso.',
            bloqueado: 'Tu cuenta está suspendida. Contactá al administrador.'
        };
        showToast(messages[oauthError] || 'No se pudo completar el acceso con la red social.', 'error');
    }
}

export function prefillOAuthSignup(code, data) {
    pendingOAuthCode = code;
    const providerLabel = { google: 'Google', facebook: 'Facebook' }[data.provider] || 'tu red social';
    const providerEl = document.getElementById('oauth-signup-provider');
    if (providerEl) providerEl.textContent = providerLabel;
    const emailEl = document.getElementById('oauth-signup-email');
    const nombreEl = document.getElementById('oauth-signup-nombre');
    const apellidoEl = document.getElementById('oauth-signup-apellido');
    if (emailEl) emailEl.value = data.email || '';
    if (nombreEl) nombreEl.value = data.nombre || '';
    if (apellidoEl) apellidoEl.value = data.apellido || '';
    const dniEl = document.getElementById('oauth-signup-dni');
    const telEl = document.getElementById('oauth-signup-tel');
    if (dniEl) dniEl.value = '';
    if (telEl) telEl.value = '';
    const err = document.getElementById('oauth-signup-error');
    if (err) err.style.display = 'none';
    openModal('oauthSignupModal');
}

export async function handleOAuthComplete(e) {
    e.preventDefault();
    const errorMsg = document.getElementById('oauth-signup-error');
    if (errorMsg) errorMsg.style.display = 'none';

    const dni = document.getElementById('oauth-signup-dni').value.replace(/\D/g, '');
    const telefono = document.getElementById('oauth-signup-tel').value.replace(/\D/g, '');

    if (dni.length < 7 || dni.length > 8) {
        errorMsg.innerText = 'El DNI debe tener 7 u 8 números';
        errorMsg.style.display = 'block';
        return;
    }
    if (telefono.length < 10) {
        errorMsg.innerText = 'El teléfono debe tener al menos 10 dígitos';
        errorMsg.style.display = 'block';
        return;
    }
    if (!pendingOAuthCode) {
        errorMsg.innerText = 'La sesión de registro expiró. Volvé a intentarlo desde el inicio.';
        errorMsg.style.display = 'block';
        return;
    }

    const btn = e.target.querySelector('button[type="submit"]');
    const originalText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Finalizando...';
    btn.disabled = true;

    const res = await api.post('/auth/oauth/complete', { code: pendingOAuthCode, dni, telefono });

    if (res && res.ok) {
        const data = res.data;
        pendingOAuthCode = null;
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('rol', data.rol);
        localStorage.setItem('nombre', toTitle(data.nombre));
        localStorage.setItem('apellido', toTitle(data.apellido));
        localStorage.setItem('sucursal', data.sucursal || '');
        const modal = document.getElementById('oauthSignupModal');
        if (modal) modal.style.display = 'none';
        window.location.href = '/perfil';
    } else {
        pendingOAuthCode = null;
        errorMsg.innerText = res ? (res.error || 'Error al completar el registro') : 'Error de conexión';
        errorMsg.style.display = 'block';
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}
