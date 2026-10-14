import api from './api.js';
import { showToast, toTitle, formatDayTime, escapeHtml } from './utils.js';
import { renderCappedList, resetCappedState } from './list-pagination.js';

/**
 * PERFIL HELP MODULE (v9.8.5)
 * Lógica interactiva para la sección de Ayuda y Soporte.
 */

let helpBranchesLoaded = false;
let myTicketsLoaded = false;

const TERMINAL_TICKET_STATES = ['resuelto', 'resuelta', 'cerrado', 'cancelado'];

export async function loadHelpBranches() {
    const branchSelect = document.getElementById('ticket-branch');
    if (!branchSelect || helpBranchesLoaded) return;

    try {
        const res = await api.get('/parking/branches');
        if (res.ok && Array.isArray(res.data)) {
            const currentVal = branchSelect.value;
            branchSelect.innerHTML = '<option value="General">Todas las sucursales / Consulta General</option>';
            
            res.data.forEach(b => {
                const opt = document.createElement('option');
                opt.value = b.nombre;
                opt.textContent = toTitle(b.nombre);
                branchSelect.appendChild(opt);
            });
            if (currentVal) branchSelect.value = currentVal;
            helpBranchesLoaded = true;
        }
    } catch (e) {
        console.error('[HELP] Error al cargar sucursales para ticket:', e);
    }
}

function ticketStateClass(estado) {
    const e = (estado || '').toLowerCase();
    if (e === 'resuelto' || e === 'resuelta') return 'is-resolved';
    if (TERMINAL_TICKET_STATES.includes(e)) return 'is-closed';
    if (e === 'en proceso') return 'is-process';
    if (e === 'en revisión') return 'is-review';
    return 'is-pending';
}

export async function loadMyTickets() {
    const container = document.getElementById('my-tickets');
    if (!container || myTicketsLoaded) return;
    myTicketsLoaded = true;

    container.innerHTML = '<div class="my-tickets-empty"><i class="fas fa-spinner fa-spin"></i> Cargando tus consultas...</div>';

    try {
        const res = await api.get('/user/support-tickets');
        if (!res.ok || !Array.isArray(res.data)) {
            container.innerHTML = '<div class="my-tickets-empty">No se pudieron cargar tus consultas.</div>';
            return;
        }
        myTicketsAll = [...res.data].sort((a, b) => (b.created_at || '').localeCompare(a.created_at || ''));
        renderMyTickets();
    } catch (e) {
        myTicketsLoaded = false;
        container.innerHTML = '<div class="my-tickets-empty">Error de conexión al cargar tus consultas.</div>';
    }
}

const MY_TICKETS_MAX_VISIBLE = 6;
let myTicketsAll = [];
let myTicketsFilter = 'all';

function myTicketMatchesFilter(t) {
    const e = (t.estado || '').toLowerCase();
    switch (myTicketsFilter) {
        case 'pendiente': return e === 'pendiente';
        case 'en_revision': return e === 'en revisión';
        case 'en_proceso': return e === 'en proceso';
        case 'resuelto': return e === 'resuelto' || e === 'resuelta';
        case 'cerrado': return e === 'cerrado' || e === 'cancelado';
        default: return true;
    }
}

function renderMyTickets() {
    const container = document.getElementById('my-tickets');
    const countEl = document.getElementById('my-tickets-count');
    if (!container) return;

    if (myTicketsAll.length === 0) {
        container.innerHTML = '<div class="my-tickets-empty"><i class="fas fa-inbox"></i> Todavía no tenés consultas. Usá el formulario para abrir tu primer ticket.</div>';
        if (countEl) countEl.textContent = '';
        return;
    }
    if (countEl) countEl.textContent = `(${myTicketsAll.length})`;

    const filtered = myTicketsAll.filter(myTicketMatchesFilter);
    if (filtered.length === 0) {
        container.innerHTML = '<div class="my-tickets-empty"><i class="fas fa-filter-circle-xmark"></i> No hay consultas en este estado.</div>';
        return;
    }

    renderCappedList(container, filtered.map(t => `
            <div class="my-ticket-card" onclick="openSupportTicketModal(${t.id})">
                <div class="my-ticket-head">
                    <span class="my-ticket-nro">#${t.id}</span>
                    <span class="my-ticket-state ${ticketStateClass(t.estado)}">${escapeHtml(t.estado || 'Pendiente')}</span>
                </div>
                <div class="my-ticket-subject">${escapeHtml(t.asunto || 'Sin asunto')}</div>
                <div class="my-ticket-meta">
                    <span>${toTitle(t.categoria)} · ${escapeHtml(toTitle(t.sucursal))}</span>
                    <span>${t.created_at ? formatDayTime(new Date(t.created_at)) : ''}</span>
                </div>
            </div>
        `), {
        pageSize: MY_TICKETS_MAX_VISIBLE,
        tag: 'div',
        toggleClass: 'my-tickets-toggle',
        toggleAll: total => `Ver todas las consultas (${total})`,
        toggleLess: 'Ver menos',
        onToggle: () => renderMyTickets()
    });
}

export function filterMyTickets(estado, pillBtn) {
    myTicketsFilter = estado || 'all';
    document.querySelectorAll('.my-tickets-pill').forEach(p =>
        p.classList.toggle('active', p.dataset.estado === myTicketsFilter));
    resetCappedState(document.getElementById('my-tickets'));
    renderMyTickets();
}

function refreshMyTickets() {
    myTicketsLoaded = false;
    loadMyTickets();
}

export function toggleFaq(btn) {
    if (!btn) return;
    const item = btn.closest('.faq-item');
    if (!item) return;

    const isOpen = item.classList.contains('open');

    // Cerrar otros faq-items dentro del mismo grupo si se desea un acordeón exclusivo
    const container = item.closest('.faq-category-group');
    if (container) {
        container.querySelectorAll('.faq-item').forEach(i => {
            if (i !== item) i.classList.remove('open');
        });
    }

    item.classList.toggle('open', !isOpen);
}

let activeCategory = 'all';

export function filterHelpCategory(category, pillBtn) {
    activeCategory = category;

    // Actualizar pills activas
    const container = document.getElementById('help-category-pills');
    if (container) {
        container.querySelectorAll('.help-pill').forEach(btn => btn.classList.remove('active'));
    }
    if (pillBtn) pillBtn.classList.add('active');

    // Filtrar contenido
    applyHelpFilters();
}

export function filterHelpContent() {
    const searchInput = document.getElementById('help-search-input');
    const clearBtn = document.getElementById('help-search-clear');
    if (clearBtn && searchInput) {
        clearBtn.style.display = searchInput.value.trim() ? 'block' : 'none';
    }

    applyHelpFilters();
}

export function clearHelpSearch() {
    const searchInput = document.getElementById('help-search-input');
    if (searchInput) searchInput.value = '';

    const clearBtn = document.getElementById('help-search-clear');
    if (clearBtn) clearBtn.style.display = 'none';

    applyHelpFilters();
}

function applyHelpFilters() {
    const searchInput = document.getElementById('help-search-input');
    const query = searchInput ? searchInput.value.toLowerCase().trim() : '';

    const categoryGroups = document.querySelectorAll('.faq-category-group');
    const quickGrid = document.querySelector('.help-quick-grid');
    const contactWrapper = document.querySelector('.help-contact-wrapper');
    const emptyState = document.getElementById('help-empty-search');

    let totalMatches = 0;

    categoryGroups.forEach(group => {
        const groupCategory = group.getAttribute('data-category');
        const matchCategory = (activeCategory === 'all' || activeCategory === groupCategory);

        let groupMatches = 0;

        const items = group.querySelectorAll('.faq-item');
        items.forEach(item => {
            const text = item.innerText.toLowerCase();
            const matchQuery = !query || text.includes(query);

            if (matchCategory && matchQuery) {
                item.style.display = 'block';
                groupMatches++;
                totalMatches++;
                if (query) item.classList.add('open');
            } else {
                item.style.display = 'none';
                if (query) item.classList.remove('open');
            }
        });

        if (groupMatches > 0 && matchCategory) {
            group.style.display = 'block';
        } else {
            group.style.display = 'none';
        }
    });

    // Gestionar visibilidad de Guías y Contacto según categoría y búsqueda
    if (quickGrid) {
        quickGrid.style.display = (!query && (activeCategory === 'all' || activeCategory === 'reservas')) ? 'grid' : (query ? 'none' : 'none');
    }

    if (contactWrapper) {
        const showContact = (activeCategory === 'all' || activeCategory === 'soporte') || (query && ('contacto'.includes(query) || 'soporte'.includes(query) || 'mensaje'.includes(query)));
        contactWrapper.style.display = showContact ? 'grid' : 'none';
        const soporteTitle = document.getElementById('soporte-section');
        if (soporteTitle) soporteTitle.style.display = showContact ? 'flex' : 'none';
        const misConsultasTitle = document.getElementById('mis-consultas-section');
        if (misConsultasTitle) misConsultasTitle.style.display = showContact ? 'flex' : 'none';
        const myTicketsPills = document.getElementById('my-tickets-pills');
        if (myTicketsPills) myTicketsPills.style.display = showContact ? 'flex' : 'none';
        const myTicketsEl = document.getElementById('my-tickets');
        if (myTicketsEl) myTicketsEl.style.display = showContact ? 'grid' : 'none';
    }

    // Estado vacío
    if (emptyState) {
        emptyState.style.display = (totalMatches === 0 && query !== '') ? 'block' : 'none';
    }
}

export async function submitSupportTicket(event) {
    event.preventDefault();

    const category = document.getElementById('ticket-category')?.value;
    const branch = document.getElementById('ticket-branch')?.value || 'General';
    const subject = document.getElementById('ticket-subject')?.value;
    const message = document.getElementById('ticket-message')?.value;
    const btn = document.getElementById('btn-submit-ticket');

    if (!category || !subject || !message) {
        showToast('Por favor completá todos los campos del ticket.', 'error');
        return;
    }

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';
    }

    try {
        const res = await api.post('/user/support-tickets', {
            categoria: category,
            sucursal: branch,
            asunto: subject,
            mensaje: message
        });

        if (res.ok) {
            const branchNotice = branch !== 'General' ? ` sobre ${toTitle(branch)}` : '';
            showToast(`¡Ticket #${res.data.ticket_id}${branchNotice} enviado con éxito! Te responderemos a la brevedad.`, 'success');
            const form = document.getElementById('help-support-form');
            if (form) form.reset();
            refreshMyTickets();
        } else {
            showToast(res.error || 'Error al enviar el ticket de soporte', 'error');
        }
    } catch (e) {
        console.error('[SUPPORT TICKET ERROR]', e);
        showToast('Error de conexión al enviar el ticket', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-paper-plane"></i> ENVIAR TICKET DE SOPORTE';
        }
    }
}

let currentTicketId = null;
let currentAttachFile = null;

const ALLOWED_ATTACH_EXT = ['png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'];
const MAX_ATTACH_SIZE = 1 * 1024 * 1024; // 1 MB

function renderTicketMessages(messages) {
    const container = document.getElementById('modal-ticket-messages');
    if (!container) return;
    if (!messages || messages.length === 0) {
        container.innerHTML = '<div style="text-align:center;color:#888;padding:20px;">Sin mensajes</div>';
        return;
    }
    container.innerHTML = messages.map(m => {
        // ESTILO CHAT TIPO WHATSAPP (primera persona):
        // - el CLIENTE que mira: sus mensajes (no admin) van a la DERECHA
        // - los mensajes del SOPORTE/ADMIN van a la IZQUIERDA
        const isMine = !m.is_admin;
        const align = isMine ? 'flex-end' : 'flex-start';
        const bgColor = isMine ? 'rgba(223, 186, 107, 0.10)' : 'rgba(16, 185, 129, 0.12)';
        const borderColor = isMine ? 'var(--dorado)' : '#10b981';
        const borderSide = isMine ? 'border-left' : 'border-right';
        const label = isMine ? 'Vos' : 'Soporte';
        const time = m.created_at ? formatDayTime(new Date(m.created_at)) : '';
        let attachHtml = '';
        if (m.adjunto_url) {
            const isImage = /\.(png|jpe?g|gif|webp)$/i.test(m.adjunto_url);
            const adjUrl = encodeURI(m.adjunto_url);
            const adjName = escapeHtml(m.adjunto_nombre || 'Adjunto');
            attachHtml = isImage
                ? `<div style="margin-top:8px;font-size:0.8rem;"><a href="${adjUrl}" target="_blank" rel="noopener" style="color:${isMine?'var(--dorado)':'#8bc34a'};text-decoration:none;"><i class="fas fa-image"></i> ${adjName}</a></div>`
                : `<div style="margin-top:8px;font-size:0.8rem;"><a href="${adjUrl}" target="_blank" rel="noopener" style="color:${isMine?'var(--dorado)':'#8bc34a'};text-decoration:none;"><i class="fas fa-file-pdf"></i> ${adjName}</a></div>`;
        }
        return `
            <div style="display:flex;align-self:${align};flex-direction:column;max-width:75%;margin-left:${isMine?'8px':'0'};margin-right:${isMine?'0':'8px'};">
                <div style="background:${bgColor};border-radius:12px;padding:10px 12px;${borderSide}:3px solid ${borderColor};min-width:0;">
                    <div style="font-size:0.7rem;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap;">
                        <span>${label} — ${escapeHtml(m.autor || '')}</span>
                        <span>${time}</span>
                    </div>
                    <div style="font-size:0.88rem;color:#eee;line-height:1.5;white-space:pre-wrap;text-align:left;overflow-wrap:anywhere;word-break:break-word;">${escapeHtml(m.mensaje)}</div>
                    ${attachHtml}
                </div>
            </div>`;
    }).join('');
    container.scrollTop = container.scrollHeight;
}

export function handleTicketAttach(input) {
    const file = input && input.files && input.files[0];
    const nameEl = document.getElementById('modal-ticket-attach-name');
    if (!file) {
        currentAttachFile = null;
        if (nameEl) nameEl.textContent = '';
        return;
    }
    const ext = (file.name.split('.').pop() || '').toLowerCase();
    if (!ALLOWED_ATTACH_EXT.includes(ext)) {
        showToast('Formato no permitido. Adjuntá imágenes (PNG, JPG, GIF, WEBP) o PDF.', 'error');
        input.value = '';
        currentAttachFile = null;
        if (nameEl) nameEl.textContent = '';
        return;
    }
    if (file.size > MAX_ATTACH_SIZE) {
        showToast('El archivo supera el tamaño máximo de 1 MB.', 'error');
        input.value = '';
        currentAttachFile = null;
        if (nameEl) nameEl.textContent = '';
        return;
    }
    currentAttachFile = file;
    if (nameEl) nameEl.textContent = `📎 ${file.name}`;
};

export async function openSupportTicketModal(ticketId) {
    if (!ticketId) {
        window.showSection?.('ayuda');
        return;
    }
    currentTicketId = ticketId;

    const modal = document.getElementById('support-ticket-modal');
    if (!modal) return;
    modal.style.display = 'flex';
    modal.classList.add('active');

    document.getElementById('modal-ticket-id').textContent = 'Ticket #' + ticketId;
    document.getElementById('modal-ticket-subject').textContent = 'Cargando...';
    document.getElementById('modal-ticket-meta').textContent = '';
    const stateEl = document.getElementById('modal-ticket-state');
    if (stateEl) { stateEl.textContent = ''; stateEl.className = 'my-ticket-state'; }
    const msgContainer = document.getElementById('modal-ticket-messages');
    if (msgContainer) msgContainer.innerHTML = '<div style="text-align:center;padding:20px;"><i class="fas fa-spinner fa-spin"></i></div>';
    document.getElementById('modal-ticket-reply-input').value = '';
    currentAttachFile = null;
    const attachInput = document.getElementById('modal-ticket-attach');
    if (attachInput) attachInput.value = '';
    const attachNameEl = document.getElementById('modal-ticket-attach-name');
    if (attachNameEl) attachNameEl.textContent = '';

    try {
        const res = await api.get(`/user/support-tickets/${ticketId}`);
        if (!res.ok) {
            showToast('No se pudo cargar el ticket', 'error');
            closeSupportTicketModal();
            return;
        }
        const t = res.data;
        document.getElementById('modal-ticket-id').textContent = 'Ticket #' + t.id;
        document.getElementById('modal-ticket-subject').textContent = t.asunto;
        document.getElementById('modal-ticket-meta').textContent = `${toTitle(t.categoria)} · ${toTitle(t.sucursal)}`;
        const estado = t.estado || 'Pendiente';
        if (stateEl) {
            stateEl.className = 'my-ticket-state ' + ticketStateClass(estado);
            stateEl.textContent = estado;
        }

        renderTicketMessages(t.messages);

        const replyBox = document.getElementById('modal-ticket-reply-box');
        if (TERMINAL_TICKET_STATES.includes((t.estado || '').toLowerCase())) {
            replyBox.style.display = 'none';
        } else {
            replyBox.style.display = 'block';
        }
    } catch (e) {
        console.error('[SUPPORT MODAL]', e);
        showToast('Error de conexión', 'error');
        closeSupportTicketModal();
    }
};

export function closeSupportTicketModal() {
    const modal = document.getElementById('support-ticket-modal');
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
    currentTicketId = null;
};

export async function submitTicketReply() {
    if (!currentTicketId) return;
    const input = document.getElementById('modal-ticket-reply-input');
    const btn = document.getElementById('modal-ticket-reply-btn');
    const attachInput = document.getElementById('modal-ticket-attach');
    const msg = input?.value?.trim();
    if (!msg && !currentAttachFile) {
        showToast('Escribí tu respuesta o adjuntá un archivo', 'info');
        return;
    }
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>'; }
    try {
        const formData = new FormData();
        if (msg) formData.append('mensaje', msg);
        else formData.append('mensaje', '');
        if (currentAttachFile) formData.append('adjunto', currentAttachFile, currentAttachFile.name);
        const res = await api.patch(`/user/support-tickets/${currentTicketId}/reply`, formData);
        if (res.ok) {
            showToast('Respuesta enviada', 'success');
            input.value = '';
            currentAttachFile = null;
            if (attachInput) attachInput.value = '';
            const nameEl = document.getElementById('modal-ticket-attach-name');
            if (nameEl) nameEl.textContent = '';
            refreshMyTickets();
            if (res.data.messages) {
                renderTicketMessages(res.data.messages);
            } else {
                openSupportTicketModal(currentTicketId);
            }
        } else {
            showToast(res.error || 'Error al enviar', 'error');
        }
    } catch (e) {
        showToast('Error de conexión', 'error');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-reply"></i> ENVIAR RESPUESTA'; }
    }
};
