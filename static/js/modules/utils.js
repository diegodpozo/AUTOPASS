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
    // Reemplazamos 'T' por un espacio para que el constructor de Date sea compatible universalmente
    const normalizedStr = isoStr.replace('T', ' ').replace(/-/g, "/");
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

        if (title === '') {
            titleEl.style.display = 'none';
        } else {
            titleEl.style.display = 'block';
            titleEl.innerText = title || '¿Estás seguro?';
        }
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
 * Aplica formato visual estándar a la patente Mercosur (Ej: AB 123 CD).
 */
export function formatPlate(p) {
    if (!p) return '---';
    // Limpiar caracteres especiales y a mayúsculas
    let clean = p.toUpperCase().replace(/[^A-Z0-9]/g, '');
    
    // Formato AAA 111 (Arg Antigua)
    if (clean.length === 6) return `${clean.slice(0, 3)} ${clean.slice(3)}`;
    
    // Formatos de 7 caracteres
    if (clean.length === 7) {
        // AB 123 CD (Arg Mercosur)
        if (!isNaN(clean.substring(2, 5))) {
            return `${clean.slice(0, 2)} ${clean.slice(2, 5)} ${clean.slice(5)}`;
        }
        // ABC 1D23 (Brasil Mercosur)
        if (!isNaN(clean[3]) && isNaN(clean[4])) {
            return `${clean.slice(0, 3)} ${clean.slice(3)}`;
        }
        // ABC 1234 (Uruguay)
        if (!isNaN(clean.substring(3))) {
            return `${clean.slice(0, 3)} ${clean.slice(3)}`;
        }
        // ABCD 123 (Paraguay Autos)
        if (isNaN(clean.substring(0, 4)) && !isNaN(clean.substring(4))) {
            return `${clean.slice(0, 4)} ${clean.slice(4)}`;
        }
        // 123 ABCD (Paraguay Motos)
        if (!isNaN(clean.substring(0, 3)) && isNaN(clean.substring(3))) {
            return `${clean.slice(0, 3)} ${clean.slice(3)}`;
        }
    }
    
    return clean;
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

/**
 * Valida la patente según el tipo y país.
 */
export function validatePlate(plate, tipo) {
    const p = plate.toUpperCase().replace(/[^A-Z0-9]/g, '');
    
    if (tipo === 'Moto') {
        // Argentina: 1 letra, 3 números, 3 letras (Ej: A123ABC)
        const argMoto = /^[A-Z]{1}[0-9]{3}[A-Z]{3}$/;
        return argMoto.test(p);
    } else {
        // Autos
        // Argentina antigua: 3 letras, 3 números (AAA111)
        const argOld = /^[A-Z]{3}[0-9]{3}$/;
        // Argentina Mercosur: 2 letras, 3 números, 2 letras (AA111AA)
        const argMercosur = /^[A-Z]{2}[0-9]{3}[A-Z]{2}$/;
        // Brasil Mercosur: 3 letras, 1 número, 1 letra, 2 números (ABC1D23)
        const braMercosur = /^[A-Z]{3}[0-9]{1}[A-Z]{1}[0-9]{2}$/;
        // Paraguay: 4 letras, 3 números (ABCD123)
        const par = /^[A-Z]{4}[0-9]{3}$/;
        // Uruguay: 3 letras, 4 números (ABC1234)
        const uru = /^[A-Z]{3}[0-9]{4}$/;
        
        return argOld.test(p) || argMercosur.test(p) || braMercosur.test(p) || par.test(p) || uru.test(p);
    }
}


