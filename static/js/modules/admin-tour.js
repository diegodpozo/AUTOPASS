/**
 * AUTOPASS - TOUR DE ADMINISTRACION Y GUIA OPERATIVA (FACHADA)
 * Repositorio de los recorridos guiados e instruccion operativa para
 * Personal Staff, Administradores Locales y Administradores Generales.
 * Fachada que orquesta los submodulos:
 *   - admin-tour-steps:   definicion de los 7 recorridos (pasos por pestaña)
 *   - admin-tour-engine:  overlay, tooltip, posicionamiento y navegacion
 *   - admin-help:         modal de ayuda operativa con FAQ y filtros
 */

import {
    adminLiveTourSteps,
    adminReservationsTourSteps,
    adminUsersTourSteps,
    adminFinanceTourSteps,
    adminTicketsTourSteps,
    adminBranchesSettingsTourSteps,
    adminFullDashboardTourSteps
} from './admin-tour-steps.js';
import { launchAdminTour } from './admin-tour-engine.js';

export { openAdminHelpModal, toggleAdminFaq, filterAdminHelpCategory, filterAdminHelpSearch } from './admin-help.js';

export function startAdminLiveTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminLiveTourSteps);
}
export function startAdminReservationsTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminReservationsTourSteps);
}
export function startAdminUsersTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminUsersTourSteps);
}
export function startAdminFinanceTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminFinanceTourSteps);
}
export function startAdminTicketsTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminTicketsTourSteps);
}
export function startAdminBranchesSettingsTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    launchAdminTour(adminBranchesSettingsTourSteps);
}
export function startAdminFullDashboardTour() {
    if (window.closeModal) window.closeModal('modal-admin-help');
    const rol = localStorage.getItem('rol');
    if (rol === 'staff') {
        const staffFullSteps = [
            ...adminLiveTourSteps,
            ...adminReservationsTourSteps.slice(1)
        ];
        launchAdminTour(staffFullSteps);
    } else {
        launchAdminTour(adminFullDashboardTourSteps);
    }
}