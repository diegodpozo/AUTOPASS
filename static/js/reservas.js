import * as res from './modules/reservas.js';

/**
 * PUENTE: RESERVAS.JS
 * MANTIENE COMPATIBILIDAD GLOBAL CON EVENTOS INLINE.
 */

window.toggleReservaForm = res.toggleReservaForm;
window.refreshReservationFormState = res.refreshReservationFormState;
window.resetReservaForm = res.resetReservaForm;
window.prepareEditReservation = res.prepareEditReservation;
window.fetchRates = res.fetchRates;
window.updateReservationPrice = res.updateReservationPrice;
window.updateFormGroups = res.updateFormGroups;
window.createReservation = res.createReservation;
window.loadReservations = res.loadReservations;
window.applyHistoryFilters = res.applyHistoryFilters;
window.cancelReservation = res.cancelReservation;
window.payReservation = res.payReservation;
window.historialPage = res.historialPage;

//UI HELPERS MOVIDOS AL MODULO
window.showDigitalPass = res.showDigitalPass;
window.closeDigitalPass = res.closeDigitalPass;
window.shareTicket = res.shareTicket;
window.repeatReservation = res.repeatReservation;
window.resetHistoryFilters = res.resetHistoryFilters;

// REFRESCO AUTOMATICO
setInterval(() => {
    const token = localStorage.getItem('token');
    if (token && (document.getElementById('section-reservas')?.classList.contains('active') || document.getElementById('section-inicio')?.classList.contains('active'))) {
        res.loadReservations();
    }
}, 60000);
