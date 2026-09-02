import api from './api.js';
import { showToast, showConfirm, formatNum } from './utils.js';
import { loadReservations } from './reservas-list.js';

/**
 * MÓDULO RESERVAS - ACCIONES (PAGO Y CANCELACIÓN)
 * Lógica de cancelación con simulación de reembolso y pago de reservas con saldo.
 */

export async function cancelReservation(id) {
    // 1. OBTENER PREVISUALIZACIÓN DEL REEMBOLSO
    const resSim = await api.get(`/user/reservations/${id}/cancel-simulation`);
    let confirmMsg = '¿Estás seguro de cancelar esta reserva? Esta acción no se puede deshacer.';
    
    if (resSim.ok) {
        const { reembolso, error } = resSim.data;
        if (error) {
            return showToast(`No se puede cancelar: ${error}`, 'error');
        }
        if (reembolso > 0) {
            confirmMsg = `Al cancelar ahora, se te reembolsarán <b style="color:var(--dorado);">$${formatNum(reembolso)}</b> en tu saldo AutoPass.<br><br>¿Deseás continuar?`;
        }
    }

    if (!await showConfirm('CANCELAR RESERVA', confirmMsg)) return;

    const res = await api.post(`/user/reservations/${id}/cancel`);
    if (res.ok) { 
        showToast('Reserva cancelada con éxito', 'success'); 
        loadReservations(); 
        if (window.loadProfile) window.loadProfile(); 
    }
    else { showToast(res.error || 'Error al cancelar', 'error'); }
}

export async function payReservation(id) {
    // 1. BUSCAR DESCUENTOS DE RESERVA DISPONIBLES DEL USUARIO PARA ESTA RESERVA
    let redemptionTicketId = null;
    let montoMsg = '';

    const resRes = await api.get('/user/reservations');
    if (resRes.ok) {
        const r = resRes.data.find(item => item.id === id);
        if (r && r.sucursal_nombre) {
            try {
                const resAvail = await api.get(`/user/redemptions/available?sucursal=${encodeURIComponent(r.sucursal_nombre)}`);
                if (resAvail.ok && resAvail.data.length > 0) {
                    const t = resAvail.data[0];
                    redemptionTicketId = t.id;
                    const porc = t.valor_descuento || 0;
                    montoMsg = `<br><br>¡Aplicás tu <b style="color:var(--dorado);">descuento de ${porc}%</b> en estacionamiento (${t.titulo})!`;
                }
            } catch (e) {}
        }
    }

    if (!await showConfirm('PAGAR RESERVA', `¿Deseás pagar con tu saldo AutoPass?${montoMsg}`)) return;

    const payUrl = redemptionTicketId
        ? `/user/reservations/${id}/pay?redemption_ticket_id=${redemptionTicketId}`
        : `/user/reservations/${id}/pay`;
    const res = await api.post(payUrl);
    if (res.ok) { 
        const pts = res.puntos_ganados || 0;
        if (redemptionTicketId) {
            showToast(`¡Pago exitoso! Descuento aplicado. Ganaste ${pts} puntos AutoPass`, 'success');
        } else {
            showToast(pts > 0 ? `¡Pago exitoso! Ganaste ${pts} puntos AutoPass` : '¡Pago exitoso!', 'success'); 
        }
        loadReservations(); 
        if (window.loadProfile) window.loadProfile(); 
        // DISPARAR EVENTO PARA EL TOUR
        try { document.dispatchEvent(new CustomEvent('reservation:paid', { detail: { id } })); } catch (e) {}
    }
    else { showToast(res.error || 'Error en el pago', 'error'); }
}

export async function payReservationWithMp(id) {
    // 1. REUTILIZAR DESCUENTO DE RESERVA DISPONIBLE (si aplica)
    let redemptionTicketId = null;

    const resRes = await api.get('/user/reservations');
    if (resRes.ok) {
        const r = resRes.data.find(item => item.id === id);
        if (r && r.sucursal_nombre) {
            try {
                const resAvail = await api.get(`/user/redemptions/available?sucursal=${encodeURIComponent(r.sucursal_nombre)}`);
                if (resAvail.ok && resAvail.data.length > 0) {
                    const t = resAvail.data[0];
                    redemptionTicketId = t.id;
                }
            } catch (e) {}
        }
    }

    if (!await showConfirm('PAGAR CON MERCADO PAGO', 'Serás redirigido a Mercado Pago para abonar esta reserva de forma segura.')) return;

    const res = await api.post('/user/mercadopago/checkout', {
        tipo: 'reserva',
        reserva_id: id,
        redemption_ticket_id: redemptionTicketId,
    });
    if (res.ok && res.data && res.data.init_point) {
        showToast('Redirigiendo a Mercado Pago...', 'info');
        window.location.href = res.data.init_point;
    } else {
        showToast(res.error || 'Error al crear el pago', 'error');
    }
}
