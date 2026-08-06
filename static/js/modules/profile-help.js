import api from './api.js';
import { showToast, toTitle } from './utils.js';

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
