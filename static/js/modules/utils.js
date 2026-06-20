/**
 * UTILS MODULO
 * FUNCIONES DE UTILIDAD TRANSVERSALES PARA TODO EL SISTEMA.
 */

/**
 * CONVIERTE UN STRING A FORMATO DE TITULO (CAPITALIZACION DE CADA PALABRA).
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
 * FORMATEA UNA FECHA ISO O STRING (YYYY-MM-DD HH:MM) A FORMATO LEGIBLE (DD/MM/YYYY HH:MM).
 */
export function formatDate(isoStr) {
    if (!isoStr) return '---';
    // REEMPLAZAMOS 'T' POR UN ESPACIO PARA QUE EL CONSTRUCTOR DE DATE SEA COMPATIBLE UNIVERSALMENTE
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
 * MUESTRA UNA NOTIFICACION PREMIUM (TOAST).
 * TIPOS: 'SUCCESS', 'ERROR', 'INFO', 'POR DEFECTO'
 */
export function showToast(msg, type = 'default') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    // CREAR ELEMENTO
    const t = document.createElement('div');
    t.className = `toast ${type}`;

    // ASIGNAR ICONO SEGUN TIPO
    let icon = 'fa-bell';
    if (type === 'success') icon = 'fa-circle-check';
    else if (type === 'error') icon = 'fa-circle-exclamation';
    else if (type === 'info') icon = 'fa-circle-info';

    t.innerHTML = `
        <i class="fas ${icon} toast-icon"></i>
        <span>${msg}</span>
    `;

    container.appendChild(t);

    // FUNCION PARA CERRAR CON ANIMACION
    const closeToast = () => {
        if (t.classList.contains('hiding')) return;
        t.classList.add('hiding');
        setTimeout(() => { if (t.parentNode) t.remove(); }, 400);
    };

    // CIERRE AL HACER CLICK EN CUALQUIER PARTE DE LA PANTALLA
    const handleDocumentClick = (e) => {
        if (!t.contains(e.target)) {
            closeToast();
            document.removeEventListener('click', handleDocumentClick);
        }
    };
    
    document.addEventListener('click', handleDocumentClick);
    
    // LIMPIAR LISTENER SI EL TOAST SE REMUEVE DE OTRA FORMA
    const observer = new MutationObserver(() => {
        if (!t.parentNode) {
            document.removeEventListener('click', handleDocumentClick);
            observer.disconnect();
        }
    });
    observer.observe(container, { childList: true });
}

/**
 * MUESTRA UN MODAL DE CONFIRMACION CON PROMESA.
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
 * NORMALIZA UN TEXTO PARA ID DE SISTEMA (QUITA TILDES Y PREFIJOS).
 */
export function normalizeSystemName(str) {
    if (!str || str === 'null' || str === 'undefined') return '';
    let clean = str.replace('AUTOPASS ', '').trim().toUpperCase();
    // QUITAR TILDES/ACENTOS
    return clean.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
}

/**
 * APLICA FORMATO VISUAL ESTANDAR A LA PATENTE MERCOSUR (EJ: AB 123 CD).
 */
export function formatPlate(p) {
    if (!p) return '---';
    // LIMPIAR CARACTERES ESPECIALES Y A MAYUSCULAS
    let clean = p.toUpperCase().replace(/[^A-Z0-9]/g, '');
    
    // FORMATO AAA 111 (ARG ANTIGUA)
    if (clean.length === 6) return `${clean.slice(0, 3)} ${clean.slice(3)}`;
    
    // FORMATOS DE 7 CARACTERES
    if (clean.length === 7) {
        // AB 123 CD (ARG MERCOSUR)
        if (!isNaN(clean.substring(2, 5))) {
            return `${clean.slice(0, 2)} ${clean.slice(2, 5)} ${clean.slice(5)}`;
        }
        // ABC 1D23 (BRASIL MERCOSUR)
        if (!isNaN(clean[3]) && isNaN(clean[4])) {
            return `${clean.slice(0, 3)} ${clean.slice(3)}`;
        }
        // ABC 1234 (URUGUAY)
        if (!isNaN(clean.substring(3))) {
            return `${clean.slice(0, 3)} ${clean.slice(3)}`;
        }
        // ABCD 123 (PARAGUAY AUTOS)
        if (isNaN(clean.substring(0, 4)) && !isNaN(clean.substring(4))) {
            return `${clean.slice(0, 4)} ${clean.slice(4)}`;
        }
        // 123 ABCD (PARAGUAY MOTOS)
        if (!isNaN(clean.substring(0, 3)) && isNaN(clean.substring(3))) {
            return `${clean.slice(0, 3)} ${clean.slice(3)}`;
        }
    }
    
    return clean;
}

/**
 * FILTRA FILAS DE UNA TABLA BASANDOSE EN UNA BUSQUEDA.
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
 * VALIDA LA PATENTE SEGUN EL TIPO Y PAIS.
 */
export function validatePlate(plate, tipo) {
    const p = plate.toUpperCase().replace(/[^A-Z0-9]/g, '');
    
    if (tipo === 'Moto') {
        // ARGENTINA: 1 LETRA, 3 NUMEROS, 3 LETRAS (EJ: A123ABC)
        const argMoto = /^[A-Z]{1}[0-9]{3}[A-Z]{3}$/;
        return argMoto.test(p);
    } else {
        // AUTOS
        // ARGENTINA ANTIGUA: 3 LETRAS, 3 NUMEROS (AAA111)
        const argOld = /^[A-Z]{3}[0-9]{3}$/;
        // ARGENTINA MERCOSUR: 2 LETRAS, 3 NUMEROS, 2 LETRAS (AA111AA)
        const argMercosur = /^[A-Z]{2}[0-9]{3}[A-Z]{2}$/;
        // BRASIL MERCOSUR: 3 LETRAS, 1 NUMERO, 1 LETRA, 2 NUMEROS (ABC1D23)
        const braMercosur = /^[A-Z]{3}[0-9]{1}[A-Z]{1}[0-9]{2}$/;
        // PARAGUAY: 4 LETRAS, 3 NUMEROS (ABCD123)
        const par = /^[A-Z]{4}[0-9]{3}$/;
        // URUGUAY: 3 LETRAS, 4 NUMEROS (ABC1234)
        const uru = /^[A-Z]{3}[0-9]{4}$/;
        
        return argOld.test(p) || argMercosur.test(p) || braMercosur.test(p) || par.test(p) || uru.test(p);
    }
}

/**
 * DETECTA EL TIPO DE VEHICULO SEGUN LA PATENTE.
 */
export function detectVehicleType(plate) {
    if (!plate) return null;
    const p = plate.toUpperCase().replace(/[^A-Z0-9]/g, '');
    
    // SI CUMPLE EL PATRON DE MOTO ARGENTINA, ES MOTO
    const argMoto = /^[A-Z]{1}[0-9]{3}[A-Z]{3}$/;
    if (argMoto.test(p)) return 'Moto';
    
    // SI CUMPLE CUALQUIERA DE LOS DE AUTO, ES AUTO
    const argOld = /^[A-Z]{3}[0-9]{3}$/;
    const argMercosur = /^[A-Z]{2}[0-9]{3}[A-Z]{2}$/;
    const braMercosur = /^[A-Z]{3}[0-9]{1}[A-Z]{1}[0-9]{2}$/;
    const par = /^[A-Z]{4}[0-9]{3}$/;
    const uru = /^[A-Z]{3}[0-9]{4}$/;
    
    if (argOld.test(p) || argMercosur.test(p) || braMercosur.test(p) || par.test(p) || uru.test(p)) {
        return 'Auto';
    }
    
    return null; // INDETERMINADO
}
