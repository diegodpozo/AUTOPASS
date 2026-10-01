/**
 * AUTOPASS - NAVEGACION DESDE NOTIFICACIONES
 * Submodulo de notifications.js: redireccion directa a la seccion destino
 * de cada accion (reserva, saldo, puntos, voucher, vehiculos, perfil, etc).
 */

import api from './api.js';
import { closeNotifDropdown } from './notifications-dropdown.js';
import { scrollToElement } from './utils.js';

export async function payFromNotif(reservaId) {
    window.showSection?.('reservas');
    setTimeout(async () => {
        const card = document.querySelector(`[data-reserva-id="${reservaId}"]`);
        if (card) {
            scrollToElement(card, { block: 'center' });
            card.style.boxShadow = '0 0 0 3px var(--dorado), 0 8px 32px rgba(212, 175, 55, 0.3)';
            setTimeout(() => { card.style.boxShadow = ''; }, 2000);
        }
        const { payReservation } = await import('./reservas.js');
        payReservation(reservaId);
    }, 600);
};

export function goToReservation(reservaId) {
    closeNotifDropdown?.();
    window.showSection?.('reservas');
    setTimeout(() => {
        const card = document.querySelector(`[data-reserva-id="${reservaId}"]`);
        if (card) {
            scrollToElement(card, { block: 'center' });
            card.style.boxShadow = '0 0 0 3px var(--dorado), 0 8px 32px rgba(212, 175, 55, 0.3)';
            setTimeout(() => { card.style.boxShadow = ''; }, 2000);
        }
    }, 500);
};

export function goToChangePassword() {
    closeNotifDropdown?.();
    window.showSection?.('perfil');
    setTimeout(() => {
        const btnPass = document.getElementById('current-password') || document.getElementById('btn-change-password') || document.querySelector('[data-bs-target="#changePasswordModal"]') || document.querySelector('.form-security-premium');
        if (btnPass) {
            scrollToElement(btnPass, { block: 'center' });
            btnPass.focus?.();
        }
    }, 400);
};

export function goToBalance() {
    closeNotifDropdown?.();
    if (window.openRechargeModal) {
        window.openRechargeModal();
    } else {
        window.showSection?.('perfil');
    }
};

export function goToPoints() {
    closeNotifDropdown?.();
    window.showSection?.('puntos');
    setTimeout(() => {
        const ptsEl = document.getElementById('puntos-catalog-container') || document.querySelector('.fidelizacion-card') || document.getElementById('section-puntos');
        if (ptsEl) scrollToElement(ptsEl, { block: 'center' });
    }, 400);
};

export async function goToVoucher(voucherId) {
    closeNotifDropdown?.();
    window.showSection?.('puntos');
    setTimeout(async () => {
        const vContainer = document.getElementById('vouchers-container');
        if (vContainer) {
            scrollToElement(vContainer, { block: 'center' });
        }
        try {
            const { showCanjeTicket, showCanjeTicketById } = await import('./profile.js');
            if (voucherId) {
                const num = Number(voucherId);
                if (!isNaN(num) && num > 0) {
                    await showCanjeTicketById(num);
                    return;
                }
            }
            // Fallback: abrir el voucher más reciente o el que coincida
            const res = await api.get('/user/redemption-tickets');
            if (res.ok && res.data && res.data.length > 0) {
                if (voucherId) {
                    const match = res.data.find(x => x.codigo === voucherId || String(x.id) === String(voucherId));
                    if (match) {
                        showCanjeTicket(match);
                        return;
                    }
                }
                showCanjeTicket(res.data[0]);
            }
        } catch (e) {
            console.error('[NOTIF VOUCHER ERROR]', e);
        }
    }, 450);
};

export function goToNewReservation() {
    closeNotifDropdown?.();
    window.showSection?.('inicio');
    setTimeout(() => {
        const formContainer = document.getElementById('reserva-form-container') || document.getElementById('section-inicio');
        if (formContainer) {
            scrollToElement(formContainer, { block: 'center' });
        }
    }, 400);
};

export function goToReservationsList() {
    closeNotifDropdown?.();
    window.showSection?.('reservas');
    setTimeout(() => {
        const resList = document.getElementById('reservas-list') || document.getElementById('section-reservas');
        if (resList) {
            scrollToElement(resList, { block: 'start' });
        }
    }, 400);
};

export function goToVehicles() {
    closeNotifDropdown?.();
    window.showSection?.('vehiculos');
    setTimeout(() => {
        const vContainer = document.getElementById('vehicles-grid') || document.getElementById('vehicle-form-container') || document.getElementById('section-vehiculos');
        if (vContainer) {
            scrollToElement(vContainer, { block: 'center' });
        }
    }, 400);
};

export function goToProfile() {
    closeNotifDropdown?.();
    window.showSection?.('perfil');
    setTimeout(() => {
        const pCard = document.querySelector('.account-hub-card') || document.getElementById('section-perfil');
        if (pCard) {
            scrollToElement(pCard, { block: 'center' });
        }
    }, 400);
};

export function goToStays() {
    closeNotifDropdown?.();
    window.showSection?.('perfil');
    setTimeout(() => {
        const staysCard = document.getElementById('container-active-stays') || document.querySelector('.account-hub-card') || document.getElementById('section-perfil');
        if (staysCard) {
            scrollToElement(staysCard, { block: 'center' });
        }
    }, 400);
};