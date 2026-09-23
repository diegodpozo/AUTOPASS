import api from './api.js';
import { showToast, formatDate, toTitle, formatTime } from './utils.js';
import { openModal, closeModal } from './ui.js';
import { updateNotifBadge } from './notifications.js';

/**
 * DASHBOARD TICKETS MODULE (v9.8.6)
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
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center p-20 text-danger">Error al cargar tickets: ${res.error}</td></tr>`;
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
    updateTicketBadge();
}

export async function updateTicketBadge() {
    const badge = document.getElementById('notif-badge-sidebar');
    if (!badge) return;
    const res = await api.get('/admin/support-tickets/pending-count');
    const count = res.ok ? (res.data.count || 0) : 0;
    if (count > 0) {
        badge.style.display = 'inline-flex';
        badge.textContent = count > 99 ? '99+' : count;
        badge.classList.add('pulse');
    } else {
        badge.style.display = 'none';
        badge.classList.remove('pulse');
    }
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
        tableBody.innerHTML = `<tr><td colspan="7" class="text-center p-30 text-muted"><i class="fas fa-inbox font-24 mb-10 block"></i>No hay tickets registrados con los filtros seleccionados.</td></tr>`;
        return;
    }

    tableBody.innerHTML = tickets.map(t => {
        const isUnread = !!t.has_unread;
        const isProcess = t.estado.toLowerCase() === 'en proceso';
        const isResolved = t.estado.toLowerCase() === 'resuelto';

        let rowClass = 'row-premium';

        let badgeClass = 'badge-warning';
        let badgeIcon = 'fa-clock';
        if (isProcess) { badgeClass = 'badge-info'; badgeIcon = 'fa-spinner fa-spin'; }
        if (isResolved) { badgeClass = 'badge-success'; badgeIcon = 'fa-check-circle'; }

        const unreadTag = isUnread 
            ? `<span class="ticket-unread-tag" title="Tenés notificaciones sin leer de este ticket"><i class="fas fa-bell pulse"></i> SIN LEER</span>` 
            : '';

        return `
            <tr class="${rowClass}">
                <td data-label="Ticket" class="text-bold text-dorado">
                    <div class="flex-row items-center gap-5">
                        ${t.nro_sucursal || ('#' + t.id)}
                        ${unreadTag}
                    </div>
                </td>
                <td data-label="Cliente">
                    <div class="flex-col">
                        <span class="text-bold">${toTitle(t.cliente_nombre) !== '---' ? toTitle(t.cliente_nombre) : 'S/D'}</span>
                        <span class="text-muted text-small ticket-email-text" title="${t.cliente_email || ''}">${t.cliente_email || ''}</span>
                    </div>
                </td>
                <td data-label="Categoría"><span class="text-bold">${toTitle(t.categoria)}</span></td>
                <td data-label="Asunto">
                    <div class="text-truncate" style="max-width: 200px;" title="${toTitle(t.asunto)}">
                        ${toTitle(t.asunto)}
                    </div>
                </td>
                <td data-label="Estado">
                    <span class="badge ${badgeClass}">
                        <i class="fas ${badgeIcon}" style="margin-right: 4px;"></i> ${t.estado}
                    </span>
                </td>
                <td data-label="Fecha" class="text-small text-muted">${formatDate(t.created_at)}</td>
                <td data-label="Acciones" class="text-center"><div style="display: flex; justify-content: center;"><button class="btn-edit actions-reveal" style="cursor: pointer;" onclick="openTicketAnswerModal(${t.id})" title="Ver detalle del ticket"><i class="fas fa-eye"></i></button></div></td>
            </tr>
        `;
    }).join('');
}

function renderAdminTicketMessages(messages) {
    const container = document.getElementById('ticket-admin-messages');
    if (!container) return;
    if (!messages || messages.length === 0) {
        container.innerHTML = '<div class="ticket-msg-empty">Sin mensajes aún</div>';
        return;
    }
    let lastDay = '';
    container.innerHTML = messages.map(m => {
        const isMine = m.is_admin;
        const autor = toTitle(m.autor || (isMine ? 'Soporte' : 'Usuario'));
        const label = isMine ? `Soporte — ${autor}` : autor;
        const dt = m.created_at ? new Date(m.created_at) : null;
        const time = dt ? formatTime(dt) : '';
        const dayKey = dt ? `${dt.getFullYear()}-${dt.getMonth()}-${dt.getDate()}` : '';
        let datePill = '';
        if (dt && dayKey !== lastDay) {
            lastDay = dayKey;
            datePill = `<div class="ticket-msg-date">${dt.toLocaleDateString('es-AR', { day:'2-digit', month:'2-digit', year:'numeric' })}</div>`;
        }
        let attachHtml = '';
        if (m.adjunto_url) {
            const isImage = /\.(png|jpe?g|gif|webp)$/i.test(m.adjunto_url);
            attachHtml = `<div class="ticket-msg-attach"><a href="${encodeURI(m.adjunto_url)}" target="_blank" rel="noopener"><i class="fas ${isImage ? 'fa-image' : 'fa-file-pdf'}"></i> ${m.adjunto_nombre || 'Adjunto'}</a></div>`;
        }
        return `
            ${datePill}
            <div class="ticket-msg ${isMine ? 'mine' : ''}">
                <div class="ticket-msg-bubble">
                    <div class="ticket-msg-meta">
                        <span><i class="fas ${isMine ? 'fa-headset' : 'fa-user'}"></i> ${label}</span>
                        <span>${time}</span>
                    </div>
                    <div class="ticket-msg-text">${m.mensaje}</div>
                    ${attachHtml}
                </div>
            </div>`;
    }).join('');
    container.scrollTop = container.scrollHeight;
}

function setTicketAnswerLocked(locked) {
    const statusSel = document.getElementById('ticket-answer-status');
    const textArea = document.getElementById('ticket-answer-text');
    const footerBtns = document.querySelector('#modal-ticket-answer .modal-footer-buttons');
    const lockMsg = document.getElementById('ticket-answer-locked');
    const formGroups = document.querySelectorAll('#modal-ticket-answer form .form-group');

    if (statusSel) statusSel.disabled = locked;
    if (textArea) { textArea.disabled = locked; textArea.placeholder = locked ? 'Ticket resuelto y bloqueado. No se pueden enviar más mensajes.' : 'Escribí aquí la respuesta o resolución enviada al cliente...'; }
    if (footerBtns) footerBtns.style.display = locked ? 'none' : 'flex';
    if (lockMsg) lockMsg.style.display = locked ? 'flex' : 'none';
    formGroups.forEach(g => { g.style.display = locked ? 'none' : ''; });
}

export async function openTicketAnswerModal(ticketId) {
    const ticket = allTickets.find(t => t.id === ticketId);
    if (!ticket) return;

    document.getElementById('ticket-modal-id').value = ticket.id;
    const nroTicket = ticket.nro_sucursal || ('#' + ticket.id);
    document.getElementById('ticket-modal-title').innerText = 'ATENDER TICKET';
    const nroEl = document.getElementById('ticket-modal-nro');
    if (nroEl) nroEl.innerText = nroTicket;
    const clienteNombre = toTitle(ticket.cliente_nombre);
    document.getElementById('ticket-modal-client').innerText = (clienteNombre && clienteNombre !== '---') ? clienteNombre : 'Cliente';
    document.getElementById('ticket-modal-email').innerText = ticket.cliente_email || '';
    document.getElementById('ticket-modal-category').innerText = toTitle(ticket.categoria);
    document.getElementById('ticket-modal-subject').innerText = toTitle(ticket.asunto);
    
    document.getElementById('ticket-answer-status').value = ticket.estado;
    document.getElementById('ticket-answer-text').value = '';

    const isResolved = (ticket.estado || '').toLowerCase() === 'resuelto';
    setTicketAnswerLocked(isResolved);

    openModal('modal-ticket-answer');

    const res = await api.get(`/admin/support-tickets/${ticketId}`);
    if (res.ok && res.data.messages) {
        renderAdminTicketMessages(res.data.messages);
    } else {
        renderAdminTicketMessages(ticket.messages);
    }

    await api.patch(`/admin/support-tickets/${ticketId}/read-notifs`);
    await updateNotifBadge();
}

export async function submitTicketAnswer(event) {
    event.preventDefault();

    const ticketId = document.getElementById('ticket-modal-id')?.value;
    const status = document.getElementById('ticket-answer-status')?.value;
    const responseText = document.getElementById('ticket-answer-text')?.value?.trim();
    const btn = document.getElementById('btn-save-ticket-answer');

    if (!ticketId || !status) return;

    if (!responseText) {
        showToast('Escribí una respuesta antes de enviar', 'info');
        return;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
    }

    const res = await api.patch(`/admin/support-tickets/${ticketId}`, {
        estado: status,
        respuesta: responseText
    });

    if (res.ok) {
        showToast(`Ticket #${ticketId} actualizado`, 'success');
        document.getElementById('ticket-answer-text').value = '';
        if (res.data.messages) {
            renderAdminTicketMessages(res.data.messages);
        }
        await updateNotifBadge();
        await loadAdminTickets();
        updateTicketBadge();
    } else {
        showToast(res.error || 'Error al actualizar el ticket', 'error');
    }

    if (btn) {
        btn.disabled = false;
        btn.innerHTML = 'ENVIAR RESPUESTA';
    }
}
