import * as prof from './modules/profile.js?v=9.3.0';
import * as res from './modules/reservas.js?v=9.3.0';
import * as v from './modules/vehicles.js?v=9.3.0';
import * as ui from './modules/ui.js?v=9.3.0';
import { initPasswordValidation } from './modules/auth.js?v=9.3.0';
import { showToast } from './modules/utils.js?v=9.3.0';
import { initMap } from './modules/landing.js?v=9.3.0';
import { loadNotifications, updateNotifBadge, startNotifPolling } from './modules/notifications.js?v=9.3.0';
import * as onboarding from './modules/onboarding_helpers.js?v=9.3.0';
import { startReservationTour } from './modules/tour.js?v=9.3.0';

/**
 * PUENTE: PERFIL.JS
 * ORQUESTADOR PRINCIPAL DEL PORTAL DE USUARIO.
 */

// PERFIL
window.loadProfile = prof.loadProfile;
window.loadPointsData = prof.loadPointsData;
window.redeemPoints = prof.redeemPoints;
window.loadPointsHistory = prof.loadPointsHistory;
window.changePtsPage = prof.changePtsPage;
window.loadPromotions = prof.loadPromotions;

// RESERVAS
window.loadReservations = res.loadReservations;
window.initReservationForm = res.initReservationForm;
window.toggleReservaForm = res.toggleReservaForm;
window.createReservation = res.createReservation;
window.prepareEditReservation = res.prepareEditReservation;
window.cancelReservation = res.cancelReservation;
window.payReservation = res.payReservation;
window.showDigitalPass = res.showDigitalPass;
window.closeDigitalPass = res.closeDigitalPass;
window.shareTicket = res.shareTicket;
window.repeatReservation = res.repeatReservation;
window.applyHistoryFilters = res.applyHistoryFilters;
window.resetHistoryFilters = res.resetHistoryFilters;
window.historialPage = res.historialPage;

// VEHICULOS
window.loadVehicles = v.loadVehicles;
window.addVehicle = v.addVehicle;
window.deleteVehicle = v.deleteVehicle;
window.setFavoriteVehicle = v.setFavoriteVehicle;

//UI HELPERS (VIENEN DE UI.JS O LOGICA LOCAL)
window.toggleNuevoVinculo = ui.toggleNuevoVinculo;
window.toggleHistorial = ui.toggleHistorial;
window.openModal = ui.openModal;
window.closeModal = ui.closeModal;

window.showSection = function(sectionId, el) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    if (el) el.classList.add('active');
    document.querySelectorAll('.profile-section').forEach(s => s.classList.remove('active'));
    const sectionEl = document.getElementById(`section-${sectionId}`);
    if (sectionEl) sectionEl.classList.add('active');

    if (sectionId === 'reservas') res.loadReservations();
    if (sectionId === 'puntos') prof.loadPointsData();
    if (sectionId === 'inicio') {
        prof.loadProfile();
        res.loadReservations();
        if (typeof res.refreshReservationFormState === 'function') {
            res.refreshReservationFormState();
        } else if (typeof window.refreshReservationFormState === 'function') {
            window.refreshReservationFormState();
        }
    }
    if (sectionId === 'perfil') prof.loadProfile();
    if (sectionId === 'vehiculos') v.loadVehicles();
    if (sectionId === 'notificaciones') loadNotifications();
};

window.openFullMap = function() {
    const overlay = document.getElementById('map-fullscreen-overlay');
    if (!overlay) return;
    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    setTimeout(() => {
        const fsMap = document.getElementById('portal-map-fullscreen');
        if (fsMap && !fsMap.classList.contains('map-initialized')) {
            fsMap.classList.add('map-initialized');
            initMap('portal-map-fullscreen', '#map-fullscreen-overlay .map-overlay', true);
        }
    }, 150);
};

window.closeFullMap = function() {
    const overlay = document.getElementById('map-fullscreen-overlay');
    if (overlay) overlay.style.display = 'none';
    document.body.style.overflow = '';
};

window.enterEditMode = function(field) {
    const item = document.getElementById(`item-${field}`);
    if (!item) return;
    item.querySelector('.display-mode').style.display = 'none';
    item.querySelector('.edit-mode').style.display = 'flex';
    let value = document.getElementById(`display-${field}`).innerText.trim();
    if (field === 'dni') value = value.replace(/\./g, '');
    document.getElementById(`input-${field}`).value = value;
};

window.exitEditMode = function(field) {
    const item = document.getElementById(`item-${field}`);
    if (!item) return;
    item.querySelector('.display-mode').style.display = 'flex';
    item.querySelector('.edit-mode').style.display = 'none';
};

window.saveField = async function(field, event) {
    const btn = event.target;
    const originalText = btn.innerText;
    const newValue = document.getElementById(`input-${field}`).value;
    btn.innerText = '...';
    btn.disabled = true;

    if (await prof.saveField(field, newValue)) {
        window.exitEditMode(field);
    }
    btn.innerText = originalText;
    btn.disabled = false;
};

window.changePassword = async function(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    const current = document.getElementById('current-password').value;
    const newPass = document.getElementById('new-password').value;
    const confirm = document.getElementById('confirm-new-password').value;
    
    if (newPass !== confirm) return showToast('Las contraseñas no coinciden', 'error');

    btn.disabled = true;
    if (await prof.changePassword(current, newPass)) {
        e.target.reset();
    }
    btn.disabled = false;
};

window.openRechargeModal = () => {
    const m = document.getElementById('rechargeModal');
    if (m) { m.style.display = 'block'; document.getElementById('recharge-amount').focus(); }
};

window.setRechargeAmount = (a) => {
    const i = document.getElementById('recharge-amount'); if (i) i.value = a;
};

window.processRecharge = async function(e) {
    e.preventDefault();
    const a = parseFloat(document.getElementById('recharge-amount').value);
    if (isNaN(a) || a <= 0) return showToast('Monto inválido');

    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    if (await prof.processRecharge(a)) {
        ui.closeModal('rechargeModal');
        e.target.reset();
    }
    btn.disabled = false;
};

window.togglePointsHistory = () => {
    const c = document.getElementById('pts-history-container');
    const a = document.getElementById('pts-history-arrow');
    if (!c) return;
    const isOpen = c.classList.toggle('open');
    if (a) a.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0deg)';
};

window.showQuickAddVehicle = () => {
    const info = document.getElementById('quick-add-info');
    const form = document.getElementById('quick-add-form-container');
    if (info) info.style.display = 'none';
    if (form) form.style.display = 'block';
};

window.hideQuickAddVehicle = () => {
    const info = document.getElementById('quick-add-info');
    const form = document.getElementById('quick-add-form-container');
    if (info) info.style.display = 'block';
    if (form) form.style.display = 'none';
};

// Exponer helpers del onboarding para que el HTML los invoque
window.openReservationOnboarding = onboarding.openReservationOnboarding;
window.closeReservationOnboarding = onboarding.closeReservationOnboarding;
window.skipReservationOnboarding = onboarding.skipReservationOnboarding;
window.startReservationOnboarding = onboarding.startReservationOnboarding;

// Global error hooks para detectar problemas de runtime y mostrar alerta en UI
window.addEventListener('error', (e) => {
    try {
        // IGNORAR ERRORES CROSS-ORIGEN (EJ: FLATPICKR CON CSS DE EXTENSIONES)
        if (e.message === 'Script error.' || e.message?.includes('cssRules')) return;
        console.error('[GLOBAL ERROR]', e.message, e.error);
        alert('Error en la página: ' + (e.message || 'Ver consola para detalles'));
    } catch (_) {}
});
window.addEventListener('unhandledrejection', (e) => {
    try {
        const msg = e.reason?.message || String(e.reason);
        if (msg.includes('cssRules') || msg === 'Script error.') return;
        console.error('[UNHANDLED REJECTION]', e.reason);
        alert('Error no manejado: ' + msg);
    } catch(_) {}
});

document.addEventListener('DOMContentLoaded', async () => {
    try {

    if (document.getElementById('balance-val') && localStorage.getItem('token')) {
        
        // 1. INICIALIZAR MAPA (PRIMERO PARA ASEGURAR VISUALIZACION)
        try {
            if (document.getElementById('portal-map')) {
                initMap('portal-map', null, true);
            }
        } catch (e) {
            console.error("[MAP ERROR] No se pudo cargar el mapa:", e);
        }

        // 2. CARGAR DATOS
        await prof.loadProfile();
        const vehicles = await v.loadVehicles();
        await res.loadReservations();
        res.initReservationForm();
        
        // evitar bloqueo por scripts terceros: pequeño log
        console.log('[PROFILE] Datos cargados: vehicles=', (vehicles && vehicles.length) || 0);
        
        // Si el usuario no tiene vehículos y es la primera vez que entra, mostrar modal onboarding amigable
        try {
            if (vehicles && vehicles.length === 0) {
                            // Mostrar modal siempre cuando el usuario no tenga vehículos (por petición)
                            try {
                                onboarding.openReservationOnboarding();
                            }
                            catch (e) { console.error('[ONBOARDING OPEN]', e); }

                            // Dejar que el flujo de onboarding maneje cuándo iniciar el tour (post-add)
                            console.log('[PROFILE] Tour start deferred to onboarding flow.');
                        }
        } catch (e) { console.error('[ONBOARDING] ', e); }
        
        // REFRESCAR ESTADO DE LOS FORMULARIOS DE RESERVA/VEHICULOS (AHORA SIEMPRE VISIBLES)
        if (typeof res.refreshReservationFormState === 'function') {
            await res.refreshReservationFormState();
        }

        // 3. INICIAR POLLING DE NOTIFICACIONES
        startNotifPolling();

        // 4. VERIFICAR SI VENIMOS DEL MAPA CON UNA SUCURSAL PRE-SELECCIONADA
        const urlParams = new URLSearchParams(window.location.search);
        const preBranch = urlParams.get('reserva_sucursal');
        if (preBranch) {
            console.log(`[*] Detectado parámetro de reserva: ${preBranch}`);
            if (window.showSection) {
                window.showSection('inicio', document.querySelector('.nav-item[onclick*="inicio"]'));
            }

            const autoFillSequence = async () => {
                const container = document.getElementById('reserva-form-container');
                if (!container) return;
                if (!container.classList.contains('open') && window.toggleReservaForm) {
                    await window.toggleReservaForm();
                }

                let attempts = 0;
                const maxAttempts = 15;
                const fillFields = () => {
                    const sucursalSelect = document.querySelector('.res-sucursal');
                    const vehicleSelect = document.querySelector('.res-vehicle');
                    if (sucursalSelect && sucursalSelect.options.length > 1 && sucursalSelect.options[0].value === "") {
                        const targetOption = Array.from(sucursalSelect.options).find(opt => opt.value === preBranch);
                        if (targetOption) {
                            sucursalSelect.value = preBranch;
                            sucursalSelect.dispatchEvent(new Event('change'));
                        }
                        if (vehicleSelect && vehicleSelect.options.length === 2) vehicleSelect.selectedIndex = 1;
                        if (container) container.scrollIntoView({ behavior: 'smooth' });
                        showToast(`Preparado para reservar en ${preBranch}`);
                        return true;
                    }
                    attempts++;
                    if (attempts < maxAttempts) setTimeout(fillFields, 300);
                    return false;
                };
                fillFields();
            };
            autoFillSequence();
        }

        //4. INICIALIZAR VALIDACION DE CONTRASENA
        initPasswordValidation(
            'new-password', 'confirm-new-password', 'password-strength', 
            'req-len', 'req-up', 'req-spec', 'req-match'
        );
    }
    } catch (e) { console.error('[DOMREADY ERROR]', e); try { alert('Error al inicializar perfil: ' + (e && e.message ? e.message : e)); } catch(_){} }
});
