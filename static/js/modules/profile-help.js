import api from './api.js';
import { showToast, toTitle, formatDayTime } from './utils.js';

/**
 * PERFIL HELP MODULE (v9.8.5)
 * Lógica interactiva para la sección de Ayuda y Soporte.
 */

let helpBranchesLoaded = false;

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
        const bgColor = isMine ? 'rgba(223, 186, 107, 0.10)' : 'rgba(76, 175, 80, 0.12)';
        const borderColor = isMine ? 'var(--dorado)' : '#4caf50';
        const borderSide = isMine ? 'border-left' : 'border-right';
        const label = isMine ? 'Vos' : 'Soporte';
        const time = m.created_at ? formatDayTime(new Date(m.created_at)) : '';
        let attachHtml = '';
        if (m.adjunto_url) {
            const isImage = /\.(png|jpe?g|gif|webp)$/i.test(m.adjunto_url);
            const adjUrl = encodeURI(m.adjunto_url);
            attachHtml = isImage
                ? `<div style="margin-top:8px;font-size:0.8rem;"><a href="${adjUrl}" target="_blank" style="color:${isMine?'var(--dorado)':'#8bc34a'};text-decoration:none;"><i class="fas fa-image"></i> ${m.adjunto_nombre || 'Adjunto'}</a></div>`
                : `<div style="margin-top:8px;font-size:0.8rem;"><a href="${adjUrl}" target="_blank" style="color:${isMine?'var(--dorado)':'#8bc34a'};text-decoration:none;"><i class="fas fa-file-pdf"></i> ${m.adjunto_nombre || 'Adjunto'}</a></div>`;
        }
        return `
            <div style="display:flex;align-self:${align};flex-direction:column;max-width:75%;margin-left:${isMine?'8px':'0'};margin-right:${isMine?'0':'8px'};">
                <div style="background:${bgColor};border-radius:12px;padding:10px 12px;${borderSide}:3px solid ${borderColor};">
                    <div style="font-size:0.7rem;color:#888;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;display:flex;justify-content:space-between;gap:8px;">
                        <span>${label} — ${m.autor}</span>
                        <span>${time}</span>
                    </div>
                    <div style="font-size:0.88rem;color:#eee;line-height:1.5;white-space:pre-wrap;text-align:left;">${m.mensaje}</div>
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

    document.getElementById('modal-ticket-id').textContent = ticketId;
    document.getElementById('modal-ticket-subject').textContent = 'Cargando...';
    document.getElementById('modal-ticket-meta').textContent = '';
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
        document.getElementById('modal-ticket-id').textContent = t.id;
        document.getElementById('modal-ticket-subject').textContent = t.asunto;
        document.getElementById('modal-ticket-meta').textContent = `${toTitle(t.categoria)} · ${toTitle(t.sucursal)} · ${t.estado}`;

        renderTicketMessages(t.messages);

        const replyBox = document.getElementById('modal-ticket-reply-box');
        if (t.estado === 'Resuelto' || t.estado === 'Cerrado') {
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
