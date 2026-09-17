/**
 * MÓDULO RESERVAS - FACHADA / PUENTE (FACADE PATTERN)
 * Re-exporta los submódulos especializados de reservas para mantener 100% de compatibilidad.
 */

export {
    initReservationForm,
    updatePeriodEnd,
    toggleReservaForm,
    refreshReservationFormState,
    resetReservaForm,
    prepareEditReservation,
    fetchRates,
    updateReservationPrice,
    updateFormGroups,
    createReservation,
    repeatReservation,
    getEditingReservaId,
    setEditingReservaId,
    getUserVehicles
} from './reservas-form.js';

export {
    loadReservations,
    applyHistoryFilters,
    renderReservaCard,
    renderHistory,
    historialPage,
    resetHistoryFilters,
    getHistoryData
} from './reservas-list.js';

export {
    cancelReservation,
    payReservation,
    payReservationWithMp
} from './reservas-actions.js';

export {
    showDigitalPass,
    closeDigitalPass,
    shareTicket,
    payReservationFromPass,
    payReservationMpFromPass
} from './reservas-pass.js';












