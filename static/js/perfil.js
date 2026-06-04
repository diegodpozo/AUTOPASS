import * as prof from './modules/profile.js';
import * as res from './modules/reservas.js';
import * as v from './modules/vehicles.js';
import * as ui from './modules/ui.js';
import { initPasswordValidation } from './modules/auth.js';
import { showToast } from './modules/utils.js';
import { initMap } from './modules/landing.js';

/**
 * BRIDGE: perfil.js
 * Orquestador principal del portal de usuario.
 */

// Perfil
window.loadProfile = prof.loadProfile;
window.loadPointsData = prof.loadPointsData;
window.redeemPoints = prof.redeemPoints;
window.loadPointsHistory = prof.loadPointsHistory;
window.changePtsPage = prof.changePtsPage;
window.loadPromotions = prof.loadPromotions;

// Reservas
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

// Vehículos
window.loadVehicles = v.loadVehicles;
window.addVehicle = v.addVehicle;
window.deleteVehicle = v.deleteVehicle;

// UI Helpers (vienen de ui.js o logic local)
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
        res.refreshReservationFormState();
    }
    if (sectionId === 'perfil') prof.loadProfile();
    if (sectionId === 'vehiculos') v.loadVehicles();
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

document.addEventListener('DOMContentLoaded', async () => {
    if (document.getElementById('balance-val') && localStorage.getItem('token')) {
        
        // 1. Inicializar Mapa (Primero para asegurar visualización)
        try {
            if (document.getElementById('portal-map')) {
                console.log("[MAP] Inicializando mapa del portal...");
                initMap('portal-map');
            }
        } catch (e) {
            console.error("[MAP ERROR] No se pudo cargar el mapa:", e);
        }

        // 2. Cargar Datos
        await prof.loadProfile();
        await v.loadVehicles();
        await res.loadReservations();
        res.initReservationForm();

        // 3. Verificar si venimos del mapa con una sucursal pre-seleccionada
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

        // 4. Inicializar validación de contraseña
        initPasswordValidation(
            'new-password', 'confirm-new-password', 'password-strength', 
            'req-len', 'req-up', 'req-spec', 'req-match'
        );
    }
});
