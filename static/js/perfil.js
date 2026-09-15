import * as prof from './modules/profile.js?v=9.19.0';
import * as res from './modules/reservas.js?v=9.10.1';
import * as v from './modules/vehicles.js?v=9.3.0';
import * as ui from './modules/ui.js?v=9.3.0';
import { initPasswordValidation } from './modules/auth.js?v=9.3.0';
import { showToast } from './modules/utils.js?v=9.3.0';
import { initMap } from './modules/landing.js?v=9.3.0';
import * as notif from './modules/notifications.js?v=9.8.6';
import * as onboarding from './modules/onboarding_helpers.js?v=9.3.0';
import { startReservationTour, startAddVehicleTour, startCreateReservationTour, startRechargeBalanceTour, startRedeemPointsTour, startQrPassTour } from './modules/tour.js?v=9.3.0';
import * as help from './modules/profile-help.js?v=9.8.5';

/**
 * PUENTE: PERFIL.JS
 * ORQUESTADOR PRINCIPAL DEL PORTAL DE USUARIO.
 */

// TOUR & AYUDA
window.startReservationTour = startReservationTour;
window.startAddVehicleTour = startAddVehicleTour;
window.startCreateReservationTour = startCreateReservationTour;
window.startRechargeBalanceTour = startRechargeBalanceTour;
window.startRedeemPointsTour = startRedeemPointsTour;
window.startQrPassTour = startQrPassTour;
window.toggleFaq = help.toggleFaq;
window.filterHelpCategory = help.filterHelpCategory;
window.filterHelpContent = help.filterHelpContent;
window.clearHelpSearch = help.clearHelpSearch;
window.submitSupportTicket = help.submitSupportTicket;
window.loadHelpBranches = help.loadHelpBranches;

// NOTIFICACIONES
window.loadNotifications = notif.loadNotifications;
window.markAllNotifRead = notif.markAllNotifRead;
window.clearReadNotifs = notif.clearReadNotifs;
window.deleteNotif = notif.deleteNotif;

// PERFIL
window.loadProfile = prof.loadProfile;
window.loadPointsData = prof.loadPointsData;
window.redeemPoints = prof.redeemPoints;
window.loadPointsHistory = prof.loadPointsHistory;
window.changePtsPage = prof.changePtsPage;
window.loadPromotions = prof.loadPromotions;
window.applyPromoBranchFilter = prof.applyPromoBranchFilter;
window.loadVouchers = prof.loadVouchers;
window.switchVoucherTab = prof.switchVoucherTab;
window.renderVouchers = prof.renderVouchers;
window.getVoucherVencimiento = prof.getVoucherVencimiento;
window.cancelVoucher = prof.cancelVoucher;
window.showCanjeTicket = prof.showCanjeTicket;
window.showCanjeTicketById = prof.showCanjeTicketById;
window.closeCanjeModal = prof.closeCanjeModal;
window.shareCanjeTicket = prof.shareCanjeTicket;

// MERCADO PAGO (PAGO DIRECTO DE ESTADIAS)
window.loadActiveStays = prof.loadActiveStays;
window.payStayWithMp = prof.payStayWithMp;

// RESERVAS
window.loadReservations = res.loadReservations;
window.initReservationForm = res.initReservationForm;
window.toggleReservaForm = res.toggleReservaForm;
window.createReservation = res.createReservation;
window.prepareEditReservation = res.prepareEditReservation;
window.cancelReservation = res.cancelReservation;
window.payReservation = res.payReservation;
window.payReservationWithMp = res.payReservationWithMp;
window.showDigitalPass = res.showDigitalPass;
window.closeDigitalPass = res.closeDigitalPass;
window.shareTicket = res.shareTicket;
window.payReservationFromPass = res.payReservationFromPass;
window.payReservationMpFromPass = res.payReservationMpFromPass;
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
    if (sectionId === 'perfil') { prof.loadProfile(); if (window.loadActiveStays) loadActiveStays(); }
    if (sectionId === 'vehiculos') v.loadVehicles();
    if (sectionId === 'notificaciones') loadNotifications();
    if (sectionId === 'ayuda') help.loadHelpBranches();
};

window.openFullMap = function(pushState = true) {
    const overlay = document.getElementById('map-fullscreen-overlay');
    if (!overlay) return;
    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';

    if (pushState && (!history.state || !history.state.mapFullscreenOpen)) {
        history.pushState({ mapFullscreenOpen: true }, '');
    }

    setTimeout(() => {
        const fsMap = document.getElementById('portal-map-fullscreen');
        if (fsMap && !fsMap.classList.contains('map-initialized')) {
            fsMap.classList.add('map-initialized');
            initMap('portal-map-fullscreen', '#map-fullscreen-overlay .map-overlay', true);
        }
    }, 150);
};

window.closeFullMap = function(popState = true) {
    const overlay = document.getElementById('map-fullscreen-overlay');
    if (overlay) overlay.style.display = 'none';
    document.body.style.overflow = '';

    if (popState && history.state && history.state.mapFullscreenOpen) {
        history.back();
    }
};

window.addEventListener('popstate', () => {
    const overlay = document.getElementById('map-fullscreen-overlay');
    if (overlay && overlay.style.display !== 'none') {
        overlay.style.display = 'none';
        document.body.style.overflow = '';
    }
});

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
    if (isNaN(a) || a <= 0) return showToast('Monto inválido', 'error');

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

window.selectQuickVehicleType = (tipo) => {
    showQuickAddVehicle();
    const form = document.getElementById('quick-add-vehicle-form');
    const select = form?.querySelector('select[name="tipo"]');
    if (!select) return;
    select.value = tipo;
    window.updateVehicleTypeIcon(tipo, 'quick-', form);
};

// Exponer helpers del onboarding para que el HTML los invoque
window.openReservationOnboarding = onboarding.openReservationOnboarding;
window.closeReservationOnboarding = onboarding.closeReservationOnboarding;
window.skipReservationOnboarding = onboarding.skipReservationOnboarding;
window.startReservationOnboarding = onboarding.startReservationOnboarding;
window.checkFirstLoginOnboarding = onboarding.checkFirstLoginOnboarding;

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
        
        // VERIFICAR PRIMER LOGUEO DEL USUARIO (tour de bienvenida automático solo primera vez)
        try {
            const userData = JSON.parse(localStorage.getItem('userData') || '{}');
            const reservations = window.userReservations || [];
            onboarding.checkFirstLoginOnboarding(userData, vehicles, reservations);
        } catch (e) { console.error('[ONBOARDING CHECK]', e); }
        
        // REFRESCAR ESTADO DE LOS FORMULARIOS DE RESERVA/VEHICULOS (AHORA SIEMPRE VISIBLES)
        if (typeof res.refreshReservationFormState === 'function') {
            await res.refreshReservationFormState();
        }

        // 3. INICIAR POLLING DE NOTIFICACIONES
        notif.startNotifPolling();

        // 4. VERIFICAR SI VENIMOS DEL MAPA CON UNA SUCURSAL PRE-SELECCIONADA
        const urlParams = new URLSearchParams(window.location.search);
        const preBranch = urlParams.get('reserva_sucursal');
        if (preBranch) {
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
                        showToast(`Preparado para reservar en ${preBranch}`, 'info');
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

        // 4.1 CARGAR ESTADIAS EN CURSO (PAGO CON MERCADO PAGO)
        if (window.loadActiveStays) {
            try { await loadActiveStays(); } catch (e) { console.error('[ACTIVE STAYS ERROR]', e); }
        }

        // 4.2 RETORNO DE MERCADO PAGO (CHECKOUT PRO)
        const mpStatus = urlParams.get('mp_status');
        const mpTipo = urlParams.get('mp_tipo');
        if (mpStatus) {
            const msgs = {
                approved: ['¡Pago aprobado con Mercado Pago!', 'success'],
                pending: ['El pago quedó pendiente de confirmación', 'info'],
                failed: ['El pago no se completó', 'error'],
            };
            const [msg, type] = msgs[mpStatus] || ['Resultado del pago', 'info'];
            setTimeout(() => showToast(msg, type), 600);
            history.replaceState({}, '', '/perfil');
            if (mpTipo === 'reserva') { if (window.loadReservations) loadReservations(); }
            else { if (window.loadActiveStays) loadActiveStays(); }
        }
    }
    } catch (e) { console.error('[DOMREADY ERROR]', e); try { alert('Error al inicializar perfil: ' + (e && e.message ? e.message : e)); } catch(_){} }
});












