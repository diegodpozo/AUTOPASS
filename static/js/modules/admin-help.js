/**
 * AUTOPASS - CENTRO DE AYUDA DEL ADMINISTRADOR
 * Submodulo de admin-tour.js: modal de ayuda, FAQ colapsable y filtros
 * por categoria y busqueda libre de tarjetas/preguntas.
 */

export function openAdminHelpModal() {
    if (window.openModal) {
        window.openModal('modal-admin-help');
    } else {
        const modal = document.getElementById('modal-admin-help');
        if (modal) modal.style.display = 'flex';
    }
}

export function toggleAdminFaq(el) {
    const item = el.closest('.admin-faq-item');
    if (item) {
        item.classList.toggle('open');
    }
}

export function filterAdminHelpCategory(category, buttonEl) {
    const pills = document.querySelectorAll('.admin-help-pill');
    pills.forEach(p => p.classList.remove('active'));
    if (buttonEl) buttonEl.classList.add('active');

    const cards = document.querySelectorAll('.admin-help-quick-card');
    cards.forEach(card => {
        const cardCat = card.getAttribute('data-category');
        if (category === 'all' || cardCat === category || cardCat === 'all') {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });

    const faqGroups = document.querySelectorAll('.admin-faq-category-group');
    faqGroups.forEach(group => {
        const groupCat = group.getAttribute('data-category');
        if (category === 'all' || groupCat === category) {
            group.style.display = '';
        } else {
            group.style.display = 'none';
        }
    });
}

export function filterAdminHelpSearch(query) {
    const term = (query || '').toLowerCase().trim();
    const cards = document.querySelectorAll('.admin-help-quick-card');
    cards.forEach(card => {
        const text = card.textContent.toLowerCase();
        if (!term || text.includes(term)) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });

    const faqItems = document.querySelectorAll('.admin-faq-item');
    faqItems.forEach(item => {
        const text = item.textContent.toLowerCase();
        if (!term || text.includes(term)) {
            item.style.display = '';
            const group = item.closest('.admin-faq-category-group');
            if (group) group.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
}