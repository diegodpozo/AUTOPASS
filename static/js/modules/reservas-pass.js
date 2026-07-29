import api from './api.js';
import { formatDate, formatPlate, showToast } from './utils.js';

/**
 * MÓDULO RESERVAS - PASE DIGITAL Y QR
 * Renderizado del pase digital, generación de código QR y compartir ticket.
 */

export async function showDigitalPass(id) {
    const res = await api.get('/user/reservations');
    if (!res.ok) return;
    const r = res.data.find(item => item.id === id);
    if (!r) return;

    document.getElementById('ticket-id-display').innerText = `#${r.id.toString().padStart(6, '0')}`;
    document.getElementById('ticket-patente').innerText = formatPlate(r.patente);
    document.getElementById('ticket-vence').innerText = formatDate(r.fecha_fin).split(',')[0];
    document.getElementById('ticket-sucursal').innerText = r.sucursal_nombre;
    document.getElementById('ticket-direccion').innerText = r.sucursal_info || 'Dirección no disponible';

    const qrContainer = document.getElementById('ticket-qr');
    if (qrContainer) {
        qrContainer.innerHTML = '';
        if (window.QRCode) {
            new QRCode(qrContainer, { text: `AUTOPASS|ID:${r.id}|PLATE:${r.patente}`, width: 180, height: 180, correctLevel: QRCode.CorrectLevel.H });
        }
    }
    const modal = document.getElementById('modal-pase-digital');
    if (modal) {
        modal.style.display = 'flex';
        // DISPARAR EVENTO PARA EL TOUR
        try { document.dispatchEvent(new CustomEvent('digitalpass:open', { detail: { id } })); } catch (e) {}
    }
}

export function closeDigitalPass() {
    const modal = document.getElementById('modal-pase-digital');
    if (modal) {
        modal.style.display = 'none';
        // DISPARAR EVENTO PARA EL TOUR
        try { document.dispatchEvent(new CustomEvent('digitalpass:closed')); } catch (e) {}
    }
}

export async function shareTicket() {
    const ticket = document.getElementById('ticket-to-capture');
    if (!ticket || !window.html2canvas) return;
    ticket.querySelectorAll('.no-print').forEach(el => el.style.opacity = '0');
    try {
        const canvas = await html2canvas(ticket, { backgroundColor: '#0a0a0a', scale: 3, useCORS: true });
        canvas.toBlob(async (blob) => {
            const file = new File([blob], `AutoPass_Ticket_${Date.now()}.png`, { type: 'image/png' });
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({ files: [file], title: 'Mi Pase AutoPass' });
            } else {
                const link = document.createElement('a');
                link.download = `AutoPass_Ticket_${Date.now()}.png`;
                link.href = URL.createObjectURL(blob);
                link.click();
            }
        });
    } catch (err) { 
        showToast('Error al generar imagen', 'error'); 
        console.error(err);
    } finally { 
        ticket.querySelectorAll('.no-print').forEach(el => el.style.opacity = '1'); 
    }
}
