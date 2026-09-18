/**
 * Módulo de Gestión de Reservas Administrativas - FACHADA
 * Re-exporta los submódulos de listado y de formulario de alta/edición
 * para mantener 100% de compatibilidad con el namespace de dashboard.js.
 */

export {
    getAllReservations,
    loadAdminReservations,
    payReservationAdmin,
    cancelReservationAdmin,
    showReservationDetail,
    updateReservationBadge,
    clearReservationBadge
} from './reservations-admin-list.js';

export {
    updateNewVehicleTypeIcon,
    resetNewResPatenteLookup,
    clearNewResPatenteLookup,
    initNewResPatenteLookup,
    openNewReservationModal,
    openEditReservationModal,
    updateNewFormGroups,
    updateNewPeriodEnd,
    updateNewReservationPrice,
    selectNewHourRange,
    handleAdminNewReservation,
    confirmEditResumoProceed,
    cancelEditResumo
} from './reservations-admin-form.js';
