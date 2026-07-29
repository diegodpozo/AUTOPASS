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
    if (!await showConfirm('PAGAR RESERVA', '¿Deseás pagar con tu saldo AutoPass?')) return;
    const res = await api.post(`/user/reservations/${id}/pay`);
    if (res.ok) { 
        showToast('¡Pago exitoso!', 'success'); 
        loadReservations(); 
        if (window.loadProfile) window.loadProfile(); 
        // DISPARAR EVENTO PARA EL TOUR
        try { document.dispatchEvent(new CustomEvent('reservation:paid', { detail: { id } })); } catch (e) {}
    }
    else { showToast(res.error || 'Error en el pago', 'error'); }
}
