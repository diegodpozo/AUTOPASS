/**
 * UTILS MODULE
 * Funciones de utilidad transversales para todo el sistema.
 */

/**
 * Convierte un string a Formato de Título (Capitalización de cada palabra).
 */
export const toTitle = s => {
    if (!s || typeof s !== 'string') return '---';
    return s.toLowerCase()
            .split(' ')
            .filter(word => word.length > 0)
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
};

/**
 * Formatea una fecha ISO o string (YYYY-MM-DD HH:MM) a formato legible (DD/MM/YYYY HH:MM).
 */
export function formatDate(isoStr) {
    if (!isoStr) return '---';
    const normalizedStr = isoStr.replace(/-/g, "/");
    const d = new Date(normalizedStr);
    
    if (isNaN(d.getTime())) return isoStr;

    const day = d.getDate().toString().padStart(2, '0');
    const month = (d.getMonth() + 1).toString().padStart(2, '0');
    const year = d.getFullYear();
    const hours = d.getHours().toString().padStart(2, '0');
    const mins = d.getMinutes().toString().padStart(2, '0');
    return `${day}/${month}/${year} ${hours}:${mins}`;
}

/**
 * Muestra una notificación premium (Toast).
 * Tipos: 'success', 'error', 'info', 'default'
 */
export function showToast(msg, type = 'default') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    // Crear elemento
    const t = document.createElement('div');
    t.className = `toast ${type}`;

    // Asignar ícono según tipo
    let icon = 'fa-bell';
    if (type === 'success') icon = 'fa-circle-check';
    else if (type === 'error') icon = 'fa-circle-exclamation';
    else if (type === 'info') icon = 'fa-circle-info';

    t.innerHTML = `
        <i class="fas ${icon} toast-icon"></i>
        <span>${msg}</span>
    `;

    container.appendChild(t);

    // Función para cerrar con animación
    const closeToast = () => {
        if (t.classList.contains('hiding')) return;
        t.classList.add('hiding');
        setTimeout(() => { if (t.parentNode) t.remove(); }, 400);
    };

    // Auto-cierre tras 5 segundos
    const autoClose = setTimeout(closeToast, 5000);

    // Cierre manual al hacer click
    t.onclick = () => {
        clearTimeout(autoClose);
        closeToast();
    };
}

/**
 * Muestra un modal de confirmación con promesa.
 */
export function showConfirm(title, msg) {
    return new Promise((resolve) => {
        const modal = document.getElementById('modal-confirm');
        const titleEl = document.getElementById('confirm-title');
        const msgEl = document.getElementById('confirm-msg');
        const btnOk = document.getElementById('confirm-btn-ok');
        const btnCancel = document.getElementById('confirm-btn-cancel');

        if (!modal || !btnOk || !btnCancel) return resolve(false);

        titleEl.innerText = title || '¿Estás seguro?';
        if (msg.includes('<')) {
            msgEl.innerHTML = msg;
        } else {
            msgEl.innerText = msg || 'Esta acción no se puede deshacer.';
        }
        
        modal.style.display = 'flex';
        modal.style.alignItems = 'center';
        modal.style.justifyContent = 'center';

        const handleResponse = (result) => {
            modal.style.display = 'none';
            btnOk.onclick = null;
            btnCancel.onclick = null;
            resolve(result);
        };

        btnOk.onclick = () => handleResponse(true);
        btnCancel.onclick = () => handleResponse(false);
        
        modal.onclick = (e) => { if(e.target === modal) handleResponse(false); };
    });
}

/**
 * Normaliza un texto para ID de sistema (Quita tildes y prefijos).
 */
export function normalizeSystemName(str) {
    if (!str || str === 'null' || str === 'undefined') return '';
    let clean = str.replace('AUTOPASS ', '').trim().toUpperCase();
    // Quitar tildes/acentos
    return clean.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

/**
 * Filtra filas de una tabla basándose en una búsqueda.
 */
export function filterTable(tbodyId, query) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;
    const rows = tbody.getElementsByTagName('tr');
    const q = query.toLowerCase();

    for (let i = 0; i < rows.length; i++) {
        const text = rows[i].innerText.toLowerCase();
        rows[i].style.display = text.includes(q) ? '' : 'none';
    }
}

