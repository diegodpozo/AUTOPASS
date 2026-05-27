import api from './api.js';
import { toTitle, showToast } from './utils.js';
import { switchModal } from './ui.js';

/**
 * AUTH MODULE
 * Lógica de inicio de sesión, registro y validación de seguridad.
 */

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
            const val = regPass.value;
            const confirmVal = regPassConfirm ? regPassConfirm.value : "";
            
            if (strengthMeter) strengthMeter.className = 'strength-meter';
            
            const isLen = val.length >= 8;
            const isUp = /[A-Z]/.test(val);
            const isSpec = /[!@#$%^&*(),.?":{}|<>]/.test(val);
            const isMatch = val.length > 0 && val === confirmVal;

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
            
            updateReq(reqLen, isLen); 
            updateReq(reqUp, isUp); 
            updateReq(reqSpec, isSpec); 
            updateReq(reqMatch, isMatch);
            
            if (strengthMeter) {
                if (val.length === 0) return;
                let strength = (isLen ? 1 : 0) + (isUp ? 1 : 0) + (isSpec ? 1 : 0);
                if (strength === 1) strengthMeter.classList.add('strength-weak');
                if (strength === 2) strengthMeter.classList.add('strength-medium');
                if (strength === 3) strengthMeter.classList.add('strength-strong');
            }
        };
        regPass.addEventListener('input', validatePass);
        if (regPassConfirm) regPassConfirm.addEventListener('input', validatePass);
    }
}

export async function handleLogin(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;
    const errorMsg = document.getElementById('login-error');
    const originalText = btn.innerHTML;

    errorMsg.style.display = 'none';
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Ingresando...';
    btn.disabled = true;

    const res = await api.post('/auth/login', { email, password });
    
    if (res && res.ok) {
        const data = res.data;
        localStorage.setItem('token', data.access_token);
        localStorage.setItem('rol', data.rol);
        localStorage.setItem('nombre', toTitle(data.nombre));
        localStorage.setItem('apellido', toTitle(data.apellido));
        
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
    
    const passwordRegex = /^(?=.*[A-Z])(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$/;
    if (!passwordRegex.test(password)) {
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
        showToast('¡Registro exitoso! Bienvenido a AUTOPASS');
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
