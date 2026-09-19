/**
 * AUTOPASS - FORMATEO DE NOTIFICACIONES
 * Submodulo de notifications.js: iconos, clases de categoria, acciones inline
 * y tiempo relativo para la representacion visual de cada notificacion.
 */

import { getVirtualNow } from './virtual-time.js';

export function getNotifIcon(tipo) {
    switch (tipo) {
        case 'REMINDER_PAID': return 'fa-clock';
        case 'REMINDER_UNPAID': return 'fa-exclamation-triangle';
        case 'RESERVATION_STARTED': return 'fa-play-circle';
        case 'AUTO_CANCELLED':
        case 'RESERVATION_CANCELLED': return 'fa-times-circle';
        case 'RESERVATION_CONFIRMED': return 'fa-check-circle';
        case 'RESERVATION_MODIFIED': return 'fa-calendar-check';
        case 'RESERVATION_CREATED_ADMIN': return 'fa-calendar-plus';
        case 'BALANCE_RECHARGED':
        case 'BALANCE_ADJUSTED_ADMIN': return 'fa-wallet';
        case 'STAY_PAID': return 'fa-receipt';
        case 'STAY_CANCELLED_ADMIN': return 'fa-ban';
        case 'SUPPORT_RESPONSE': return 'fa-headset';
        case 'SUPPORT_TICKET': return 'fa-ticket';
        case 'SUPPORT_STATUS_CHANGED': return 'fa-info-circle';
        case 'NEW_DEVICE_LOGIN':
        case 'PASSWORD_CHANGED_ADMIN':
        case 'SECURITY_PASSWORD_CHANGED': return 'fa-shield-halved';
        case 'USER_PROFILE_UPDATED': return 'fa-user-edit';
        case 'USER_ROLE_CHANGED': return 'fa-user-tag';
        case 'USER_BLOCK_STATUS_CHANGED': return 'fa-user-lock';
        case 'PROMO_REDEEMED':
        case 'PROMO_CANCELLED':
        case 'POINTS_EARNED': return 'fa-gift';
        case 'VEHICLE_REGISTERED':
        case 'VEHICLE_REMOVED':
        case 'VEHICLE_ENTRY':
        case 'VEHICLE_EXIT': return 'fa-car';
        default: return 'fa-bell';
    }
}

export function getNotifCategoryClass(tipo) {
    switch (tipo) {
        case 'RESERVATION_CONFIRMED':
        case 'RESERVATION_CREATED_ADMIN':
        case 'BALANCE_RECHARGED':
        case 'STAY_PAID':
        case 'VEHICLE_REGISTERED': return 'notif-cat-success';
        case 'REMINDER_UNPAID':
        case 'NEW_DEVICE_LOGIN':
        case 'PASSWORD_CHANGED_ADMIN':
        case 'SECURITY_PASSWORD_CHANGED':
        case 'USER_BLOCK_STATUS_CHANGED': return 'notif-cat-warning';
        case 'AUTO_CANCELLED':
        case 'RESERVATION_CANCELLED':
        case 'STAY_CANCELLED_ADMIN':
        case 'PROMO_CANCELLED':
        case 'VEHICLE_REMOVED': return 'notif-cat-danger';
        case 'SUPPORT_RESPONSE':
        case 'SUPPORT_TICKET':
        case 'SUPPORT_STATUS_CHANGED': return 'notif-cat-support';
        case 'REMINDER_PAID':
        case 'RESERVATION_MODIFIED':
        case 'PROMO_REDEEMED':
        case 'POINTS_EARNED':
        case 'BALANCE_ADJUSTED_ADMIN':
        case 'USER_PROFILE_UPDATED':
        case 'USER_ROLE_CHANGED': return 'notif-cat-gold';
        default: return 'notif-cat-default';
    }
}

export function getNotifActions(n) {
    // 1. RECORDATORIO DE PAGO PENDIENTE
    if (n.tipo === 'REMINDER_UNPAID' && n.reserva_id) {
        return `
            <button class="notif-btn notif-btn-confirm" onclick="confirmReminder(${n.id}, ${n.reserva_id}, this)">
                <i class="fas fa-check"></i> CONFIRMAR
            </button>
            <button class="notif-btn notif-btn-pay" onclick="payFromNotif(${n.reserva_id})">
                <i class="fas fa-credit-card"></i> PAGAR
            </button>`;
    }

    // 2. RESERVAS CONFIRMADAS / RECORDATORIO PAGADO / EN CURSO / MODIFICADAS / CREADAS POR ADMIN
    if (['REMINDER_PAID', 'RESERVATION_CONFIRMED', 'RESERVATION_STARTED', 'RESERVATION_MODIFIED', 'RESERVATION_CREATED_ADMIN'].includes(n.tipo) && n.reserva_id) {
        return `
            <button class="notif-btn notif-btn-view" onclick="goToReservation(${n.reserva_id})">
                <i class="fas fa-eye"></i> VER RESERVA
            </button>`;
    }

    // 3. RESERVAS AUTO-CANCELADAS
    if (n.tipo === 'AUTO_CANCELLED') {
        return `
            <button class="notif-btn notif-btn-confirm" onclick="goToNewReservation()">
                <i class="fas fa-calendar-plus"></i> NUEVA RESERVA
            </button>
            ${n.reserva_id ? `
            <button class="notif-btn notif-btn-view" onclick="goToReservation(${n.reserva_id})">
                <i class="fas fa-eye"></i> VER DETALLE
            </button>` : ''}`;
    }

    // 4. RESERVAS CANCELADAS
    if (n.tipo === 'RESERVATION_CANCELLED') {
        const hasRefund = n.mensaje && (n.mensaje.toLowerCase().includes('saldo') || n.mensaje.toLowerCase().includes('reembols'));
        return `
            ${hasRefund ? `
            <button class="notif-btn notif-btn-balance" onclick="goToBalance()">
                <i class="fas fa-wallet"></i> VER MI SALDO
            </button>` : ''}
            ${n.reserva_id ? `
            <button class="notif-btn notif-btn-view" onclick="goToReservation(${n.reserva_id})">
                <i class="fas fa-eye"></i> VER DETALLE
            </button>` : `
            <button class="notif-btn notif-btn-view" onclick="goToReservationsList()">
                <i class="fas fa-calendar-alt"></i> VER RESERVAS
            </button>`}`;
    }

    // 5. CANJE DE BENEFICIOS / VOUCHERS
    if (n.tipo === 'PROMO_REDEEMED') {
        const vMatch = n.mensaje?.match(/Voucher #(\d+)/i) || n.mensaje?.match(/#([0-9a-fA-F]{6,16})/);
        const vId = vMatch ? vMatch[1] : '';
        return `
            <button class="notif-btn notif-btn-voucher" onclick="goToVoucher('${vId}')">
                <i class="fas fa-ticket"></i> VER VOUCHER
            </button>
            <button class="notif-btn notif-btn-points" onclick="goToPoints()">
                <i class="fas fa-gift"></i> MIS PUNTOS
            </button>`;
    }

    // 6. CANJE CANCELADO O PUNTOS GANADOS
    if (['PROMO_CANCELLED', 'POINTS_EARNED'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-points" onclick="goToPoints()">
                <i class="fas fa-gift"></i> VER MIS PUNTOS
            </button>`;
    }

    // 7. PAGO DE ESTADÍA
    if (n.tipo === 'STAY_PAID') {
        return `
            <button class="notif-btn notif-btn-balance" onclick="goToStays()">
                <i class="fas fa-receipt"></i> VER ESTADÍAS
            </button>
            <button class="notif-btn notif-btn-balance" onclick="goToBalance()">
                <i class="fas fa-wallet"></i> MI SALDO
            </button>`;
    }

    // 8. ESTADÍA CANCELADA POR ADMIN
    if (n.tipo === 'STAY_CANCELLED_ADMIN') {
        return `
            <button class="notif-btn notif-btn-vehicles" onclick="goToVehicles()">
                <i class="fas fa-car"></i> MIS VEHÍCULOS
            </button>
            <button class="notif-btn notif-btn-support" onclick="openSupportTicketModal()">
                <i class="fas fa-headset"></i> AYUDA
            </button>`;
    }

    // 9. EVENTOS DE VEHÍCULOS
    if (['VEHICLE_REGISTERED', 'VEHICLE_REMOVED'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-vehicles" onclick="goToVehicles()">
                <i class="fas fa-car"></i> MIS VEHÍCULOS
            </button>`;
    }
    if (['VEHICLE_ENTRY', 'VEHICLE_EXIT'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-vehicles" onclick="goToVehicles()">
                <i class="fas fa-car"></i> MIS VEHÍCULOS
            </button>
            <button class="notif-btn notif-btn-balance" onclick="goToStays()">
                <i class="fas fa-clock-rotate-left"></i> VER ESTADÍA
            </button>`;
    }

    // 10. TICKETS DE SOPORTE
    if (['SUPPORT_RESPONSE', 'SUPPORT_TICKET', 'SUPPORT_STATUS_CHANGED'].includes(n.tipo)) {
        const ticketId = n.ticket_id || '';
        return `
            <button class="notif-btn notif-btn-support" onclick="openSupportTicketModal(${ticketId})">
                <i class="fas fa-headset"></i> IR A SOPORTE
            </button>`;
    }

    // 11. SEGURIDAD: NUEVO DISPOSITIVO O CONTRASEÑA MODIFICADA POR ADMIN
    if (['NEW_DEVICE_LOGIN', 'PASSWORD_CHANGED_ADMIN'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-security" onclick="goToChangePassword()">
                <i class="fas fa-key"></i> CAMBIAR CONTRASEÑA
            </button>`;
    }

    // 12. SEGURIDAD: CONTRASEÑA MODIFICADA POR USUARIO O CUENTA BLOQUEADA/DESBLOQUEADA
    if (['SECURITY_PASSWORD_CHANGED', 'USER_BLOCK_STATUS_CHANGED'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-support" onclick="openSupportTicketModal()">
                <i class="fas fa-headset"></i> CONTACTAR SOPORTE
            </button>`;
    }

    // 13. PERFIL O ROL ACTUALIZADO
    if (['USER_PROFILE_UPDATED', 'USER_ROLE_CHANGED'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-profile" onclick="goToProfile()">
                <i class="fas fa-user"></i> VER MI PERFIL
            </button>`;
    }

    // 14. RECARGA O AJUSTE DE SALDO
    if (['BALANCE_RECHARGED', 'BALANCE_ADJUSTED_ADMIN'].includes(n.tipo)) {
        return `
            <button class="notif-btn notif-btn-balance" onclick="goToBalance()">
                <i class="fas fa-wallet"></i> VER MI SALDO
            </button>`;
    }

    return null;
}

export function getTimeAgo(dateStr) {
    if (!dateStr) return '';
    const now = getVirtualNow();
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '';
    const diffMs = now - d;
    const diffMin = Math.floor(diffMs / 60000);
    if (diffMin < 1) return 'Ahora';
    if (diffMin < 60) return `Hace ${diffMin} min`;
    const diffHs = Math.floor(diffMin / 60);
    if (diffHs < 24) return `Hace ${diffHs}h`;
    const diffDays = Math.floor(diffHs / 24);
    if (diffDays === 1) return 'Ayer';
    return `Hace ${diffDays} días`;
}