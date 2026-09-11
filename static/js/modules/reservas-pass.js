import api from './api.js';
import { formatDate, formatPlate, formatNum, showToast, showConfirm } from './utils.js';

/**
 * MÓDULO RESERVAS - COMPROBANTE / PASE DIGITAL
 * Renderizado del comprobante según estado (impago, pagado, cancelado).
 * Incluye botones de pago directo cuando la reserva está pendiente.
 */

let _currentPassResId = null;

function duracionHoras(fechaInicio, fechaFin) {
    const diff = new Date(fechaFin.replace(/-/g, "/")) - new Date(fechaInicio.replace(/-/g, "/"));
    const h = diff / (1000 * 60 * 60);
    if (h < 1) return `${Math.round(h * 60)} min`;
    const enteras = Math.floor(h);
    const decimales = h - enteras;
    if (decimales < 0.01) return `${enteras}h`;
    if (Math.abs(decimales - 0.5) < 0.01) return `${enteras}h 30min`;
    return `${enteras}h ${Math.round(decimales * 60)}min`;
}

function formatCurrency(val) {
    return `$${formatNum(Math.round(val))}`;
}

function metodoPagoLabel(metodo) {
    if (!metodo) return '---';
    const map = {
        'SALDO': 'Billetera AUTOPASS',
        'DIGITAL': 'Billetera AUTOPASS',
        'WALLET': 'Billetera AUTOPASS',
        'Caja': 'Efectivo en caja',
        'CAJA': 'Efectivo en caja',
        'MERCADOPAGO': 'Mercado Pago',
        'MERCADO PAGO': 'Mercado Pago',
        'EFECTIVO': 'Efectivo',
        'TRANSFERENCIA': 'Transferencia',
        'TARJETA': 'Tarjeta',
        'OTRO': 'Otro'
    };
    const key = String(metodo).toUpperCase();
    return map[metodo] || map[key] || metodo;
}

function estadoBadgeClass(estado) {
    const map = {
        'Pagado': 'ticket-badge-pagado',
        'Pendiente': 'ticket-badge-pendiente',
        'Cancelada': 'ticket-badge-cancelado',
        'Fallido': 'ticket-badge-cancelado',
        'Reembolsado': 'ticket-badge-reembolsado'
    };
    return map[estado] || 'ticket-badge-pendiente';
}

function tipoEstadiaLabel(tipo) {
    const map = {
        'hora': 'Por Hora',
        'dia': 'Por Día',
        'semana': 'Por Semana',
        'quincena': 'Por Quincena',
        'mes': 'Por Mes'
    };
    return map[tipo] || tipo || '---';
}

export async function showDigitalPass(id) {
    _currentPassResId = id;
    const res = await api.get('/user/reservations');
    if (!res.ok) return;
    const r = res.data.find(item => item.id === id);
    if (!r) return;

    const isPaid = r.estado_pago === 'Pagado';
    const isCancelled = ['Cancelada', 'Fallido'].includes(r.estado_reserva) || ['Cancelado', 'Fallido'].includes(r.estado_pago);
    const isPending = r.estado_pago === 'Pendiente' && !isCancelled;

    const container = document.getElementById('ticket-to-capture');
    container.className = `modal-content-premium ticket-container ${isPaid ? 'ticket-paid' : isCancelled ? 'ticket-cancelled' : 'ticket-unpaid'}`;

    /* BADGE DE ESTADO */
    const banner = document.getElementById('ticket-status-banner');
    banner.style.display = 'flex';
    const badgeState = isCancelled ? (r.estado_reserva || r.estado_pago) : r.estado_pago;
    banner.className = `ticket-status-banner ${estadoBadgeClass(badgeState)}`;
    if (isPaid) {
        banner.innerHTML = `<i class="fas fa-check-circle"></i> PAGADO`;
    } else if (isCancelled) {
        banner.innerHTML = `<i class="fas fa-ban"></i> ${r.estado_reserva || r.estado_pago}`;
    } else {
        banner.innerHTML = `<i class="fas fa-exclamation-triangle"></i> NO PAGO`;
    }

    /* QR O SIN QR */
    const qrSection = document.getElementById('ticket-qr-section');
    const noQrSection = document.getElementById('ticket-no-qr-section');
    const idDisplay = document.getElementById('ticket-id-display');
    const idDisplayAlt = document.getElementById('ticket-id-display-alt');

    if (!isCancelled) {
        qrSection.style.display = 'flex';
        noQrSection.style.display = 'none';
        idDisplay.style.display = 'block';
        idDisplayAlt.style.display = 'none';
        idDisplay.innerText = `#${r.id.toString().padStart(6, '0')}`;
        const qrContainer = document.getElementById('ticket-qr');
        qrContainer.innerHTML = '';
        if (window.QRCode) {
            new QRCode(qrContainer, {
                text: `AUTOPASS|ID:${r.id}|PLATE:${r.patente}`,
                width: 120, height: 120,
                correctLevel: QRCode.CorrectLevel.H
            });
        }
    } else {
        qrSection.style.display = 'none';
        noQrSection.style.display = 'flex';
        idDisplay.style.display = 'none';
        idDisplayAlt.style.display = 'block';
        idDisplayAlt.innerText = `#${r.id.toString().padStart(6, '0')}`;
    }

    /* CAMPOS COMUNES */
    document.getElementById('ticket-patente').innerText = formatPlate(r.patente);
    document.getElementById('ticket-tipo-vehiculo').innerText = r.tipo_vehiculo || 'Auto';
    document.getElementById('ticket-sucursal').innerText = r.sucursal_nombre || '---';
    let dirText = r.sucursal_info;
    if (!dirText || dirText === 'Sede no especificada.' || dirText.startsWith('Sede no especificada')) {
        dirText = r.sucursal_nombre ? `Sucursal ${r.sucursal_nombre}` : 'Dirección no disponible';
    }
    document.getElementById('ticket-direccion').innerText = dirText;
    document.getElementById('ticket-inicio').innerText = formatDate(r.fecha_inicio);
    document.getElementById('ticket-vence').innerText = formatDate(r.fecha_fin).split(',')[0];
    document.getElementById('ticket-tipo-estadia').innerText = tipoEstadiaLabel(r.tipo_estadia);
    document.getElementById('ticket-duracion').innerText = duracionHoras(r.fecha_inicio, r.fecha_fin);

    /* SECCIÓN FINANCIERA */
    const total = r.monto_total || 0;
    document.getElementById('ticket-total').innerText = formatCurrency(total);

    if (isPaid) {
        const horas = (new Date(r.fecha_fin.replace(/-/g, "/")) - new Date(r.fecha_inicio.replace(/-/g, "/"))) / (1000 * 60 * 60);
        const tarifaHora = horas > 0 ? total / horas : total;
        document.getElementById('ticket-tarifa').innerText = `${formatCurrency(tarifaHora)}/hora`;
        document.getElementById('ticket-calculo').innerText = `${duracionHoras(r.fecha_inicio, r.fecha_fin)} × ${formatCurrency(tarifaHora)}`;
        document.getElementById('ticket-metodo-pago').innerText = metodoPagoLabel(r.metodo_pago);
        const puntos = Math.floor(total / 100);
        document.getElementById('ticket-puntos').innerText = puntos > 0 ? `+${puntos} pts` : '---';
    } else if (isPending) {
        document.getElementById('ticket-tarifa').innerText = 'Estimado';
        document.getElementById('ticket-calculo').innerText = `A confirmar al abonar (${duracionHoras(r.fecha_inicio, r.fecha_fin)})`;
        document.getElementById('ticket-metodo-pago').innerText = 'Pendiente de pago';
        document.getElementById('ticket-puntos').innerText = '---';
    } else {
        document.getElementById('ticket-tarifa').innerText = '---';
        document.getElementById('ticket-calculo').innerText = '---';
        document.getElementById('ticket-metodo-pago').innerText = '---';
        document.getElementById('ticket-puntos').innerText = '---';
    }

    /* INSTRUCCIONES */
    const instructions = document.getElementById('ticket-instructions');
    if (isPaid) {
        instructions.innerText = 'Presentá este código en el lector de la entrada si el reconocimiento de patente falla.';
    } else if (isCancelled) {
        instructions.innerText = 'Esta reserva fue cancelada y no es válida para ingreso.';
    } else {
        instructions.innerText = 'QR válido para ingresar al predio. Aboná antes de retirar tu vehículo.';
    }

    /* ACCIONES */
    document.getElementById('ticket-payment-actions').style.display = isPending ? 'flex' : 'none';
    document.getElementById('ticket-share-actions').style.display = !isCancelled ? 'flex' : 'none';

    /* ABRIR MODAL */
    const modal = document.getElementById('modal-pase-digital');
    if (modal) {
        modal.style.display = 'flex';
        try { document.dispatchEvent(new CustomEvent('digitalpass:open', { detail: { id } })); } catch (e) {}
    }
}

export function closeDigitalPass() {
    const modal = document.getElementById('modal-pase-digital');
    if (modal) {
        modal.style.display = 'none';
        _currentPassResId = null;
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
            const file = new File([blob], `AutoPass_Comprobante_${Date.now()}.png`, { type: 'image/png' });
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({ files: [file], title: 'Comprobante AutoPass' });
            } else {
                const link = document.createElement('a');
                link.download = `AutoPass_Comprobante_${Date.now()}.png`;
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

export async function payReservationFromPass() {
    if (!_currentPassResId) return;
    const ok = await showConfirm('¿Confirmar pago con saldo de billetera?');
    if (!ok) return;
    const res = await api.post(`/user/reservations/${_currentPassResId}/pay`);
    if (res.ok) {
        showToast('Pago registrado correctamente', 'success');
        showDigitalPass(_currentPassResId);
    } else {
        showToast(res.data?.detail || 'Error al procesar pago', 'error');
    }
}

export async function payReservationMpFromPass() {
    if (!_currentPassResId) return;
    showToast('Redirigiendo a Mercado Pago...', 'info');
    const res = await api.post('/user/mercadopago/checkout', { tipo: 'reserva', reserva_id: _currentPassResId });
    if (res.ok && res.data?.init_point) {
        window.location.href = res.data.init_point;
    } else {
        showToast(res.data?.detail || 'No se pudo iniciar el pago', 'error');
    }
}
