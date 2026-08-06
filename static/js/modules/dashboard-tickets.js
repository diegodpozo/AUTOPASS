import api from './api.js';
import { showToast, formatDate, toTitle } from './utils.js';
import { openModal, closeModal } from './ui.js';

/**
 * DASHBOARD TICKETS MODULE (v9.8.5)
 * Gestión y resolución de tickets de soporte desde el panel de administración.
 */

let allTickets = [];

let autoRefreshInterval = null;

export async function loadAdminTickets() {
    const tableBody = document.getElementById('tickets-admin-table-body');
    if (!tableBody) return;

    const statusFilter = document.getElementById('ticket-admin-status-filter')?.value || 'TODOS';

    let url = '/admin/support-tickets?';
    if (statusFilter && statusFilter !== 'TODOS') url += `estado=${encodeURIComponent(statusFilter)}&`;

    const res = await api.get(url);
    if (!res.ok) {
        tableBody.innerHTML = `<tr><td colspan="8" class="text-center p-20 text-danger">Error al cargar tickets: ${res.error}</td></tr>`;
        return;
    }

    allTickets = res.data;
    const searchVal = document.getElementById('ticket-admin-search')?.value || '';
    if (searchVal) {
        filterTicketList(searchVal);
    } else {
        renderAdminTickets(allTickets);
    }
    updateTicketStats(allTickets);
}

export function filterTicketList(query = '') {
    if (!query) {
        renderAdminTickets(allTickets);
        return;
    }
    const q = query.toLowerCase().trim();
    const filtered = allTickets.filter(t => 
        (t.asunto && t.asunto.toLowerCase().includes(q)) ||
        (t.cliente_nombre && t.cliente_nombre.toLowerCase().includes(q)) ||
        (t.cliente_email && t.cliente_email.toLowerCase().includes(q)) ||
        (t.categoria && t.categoria.toLowerCase().includes(q)) ||
        (t.sucursal && t.sucursal.toLowerCase().includes(q))
    );
    renderAdminTickets(filtered);
}

// Exponer globalmente para integrarse con WebSockets, inputs de búsqueda y bridge
window.loadAdminTickets = loadAdminTickets;
window.filterTicketList = filterTicketList;

// Auto-actualización periódica cada 10 segundos
if (!autoRefreshInterval) {
    autoRefreshInterval = setInterval(() => {
        const ticketsTab = document.getElementById('tab-tickets');
        if (ticketsTab && ticketsTab.style.display !== 'none') {
            loadAdminTickets();
        }
    }, 10000);
}

function updateTicketStats(tickets) {
    const totalEl = document.getElementById('stat-tickets-total');
    const pendingEl = document.getElementById('stat-tickets-pending');
    const processEl = document.getElementById('stat-tickets-process');
    const resolvedEl = document.getElementById('stat-tickets-resolved');
    const countEl = document.getElementById('ticket-admin-count');

    const pending = tickets.filter(t => t.estado.toLowerCase() === 'pendiente').length;
    const process = tickets.filter(t => t.estado.toLowerCase() === 'en proceso').length;
    const resolved = tickets.filter(t => t.estado.toLowerCase() === 'resuelto').length;

    if (totalEl) totalEl.innerText = tickets.length;
    if (pendingEl) pendingEl.innerText = pending;
    if (processEl) processEl.innerText = process;
    if (resolvedEl) resolvedEl.innerText = resolved;
    if (countEl) countEl.innerText = `${tickets.length} ticket${tickets.length !== 1 ? 's' : ''}`;
}

function renderAdminTickets(tickets) {
    const tableBody = document.getElementById('tickets-admin-table-body');
    if (!tableBody) return;

    if (tickets.length === 0) {
        tableBody.innerHTML = `<tr><td colspan="8" class="text-center p-30 text-muted"><i class="fas fa-inbox font-24 mb-10 block"></i>No hay tickets registrados con los filtros seleccionados.</td></tr>`;
        return;
    }

    tableBody.innerHTML = tickets.map(t => {
        let badgeClass = 'badge-warning';
        if (t.estado.toLowerCase() === 'en proceso') badgeClass = 'badge-info';
        if (t.estado.toLowerCase() === 'resuelto') badgeClass = 'badge-success';

        return `
            <tr>
                <td class="text-bold text-dorado">#${t.id}</td>
                <td>
                    <div class="flex-col">
                        <span class="text-bold">${t.cliente_nombre || 'S/D'}</span>
                        <span class="text-muted text-small">${t.cliente_email || ''}</span>
                    </div>
                </td>
                <td><span class="badge badge-outline">${toTitle(t.sucursal)}</span></td>
                <td><span class="text-bold">${toTitle(t.categoria)}</span></td>
                <td>
                    <div class="text-truncate" style="max-width: 200px;" title="${t.asunto}">
                        ${t.asunto}
                    </div>
                </td>
                <td><span class="badge ${badgeClass}">${t.estado}</span></td>
                <td class="text-small text-muted">${formatDate(t.created_at)}</td>
                <td>
                    <button class="btn btn-primary sm" onclick="openTicketAnswerModal(${t.id})">
                        <i class="fas fa-edit"></i> Atender
                    </button>
                </td>
            </tr>
        `;
    }).join('');
}

export function openTicketAnswerModal(ticketId) {
    const ticket = allTickets.find(t => t.id === ticketId);
    if (!ticket) return;

    document.getElementById('ticket-modal-id').value = ticket.id;
    document.getElementById('ticket-modal-title').innerText = `ATENDER TICKET #${ticket.id}`;
    document.getElementById('ticket-modal-client').innerText = ticket.cliente_nombre || 'Cliente';
    document.getElementById('ticket-modal-email').innerText = ticket.cliente_email || '';
    document.getElementById('ticket-modal-branch').innerText = toTitle(ticket.sucursal);
    document.getElementById('ticket-modal-category').innerText = toTitle(ticket.categoria);
    document.getElementById('ticket-modal-subject').innerText = ticket.asunto;
    document.getElementById('ticket-modal-message').innerText = ticket.mensaje;
    
    document.getElementById('ticket-answer-status').value = ticket.estado;
    document.getElementById('ticket-answer-text').value = ticket.respuesta || '';

    openModal('modal-ticket-answer');
}

export async function submitTicketAnswer(event) {
    event.preventDefault();

    const ticketId = document.getElementById('ticket-modal-id')?.value;
    const status = document.getElementById('ticket-answer-status')?.value;
    const responseText = document.getElementById('ticket-answer-text')?.value;
    const btn = document.getElementById('btn-save-ticket-answer');

    if (!ticketId || !status) return;

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Guardando...';
    }

    const res = await api.patch(`/admin/support-tickets/${ticketId}`, {
        estado: status,
        respuesta: responseText
    });

    if (res.ok) {
        showToast(`Ticket #${ticketId} actualizado a '${status}'`, 'success');
        closeModal('modal-ticket-answer');
        await loadAdminTickets();
    } else {
        showToast(res.error || 'Error al actualizar el ticket', 'error');
    }

    if (btn) {
        btn.disabled = false;
        btn.innerHTML = 'GUARDAR CAMBIOS';
    }
}
