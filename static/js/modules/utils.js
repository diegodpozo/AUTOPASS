/**
 * UTILS MODULO
 * FUNCIONES DE UTILIDAD TRANSVERSALES PARA TODO EL SISTEMA.
 */

// Los dialogos de confirmacion/eleccion se abren y cierran por la puerta unica
// (ui.js) para que tengan encierro de foco, Escape y devolucion del foco.
import { openModal, closeModal } from './ui.js';

/**
 * CONVIERTE UN STRING A FORMATO DE TITULO (CAPITALIZACION DE CADA PALABRA).
 */
/**
 * FORMATEA UN NUMERO CON SEPARADORES DE MILES (USA PUNTO, EJ: 1.500).
 */
export const formatNum = (n) => {
    if (n === undefined || n === null) return '0';
    const num = typeof n === 'number' ? n : parseFloat(n);
    if (isNaN(num)) return '0';
    const [entera, decimal] = Math.round(num).toString().split('.');
    return entera.replace(/\B(?=(\d{3})+(?!\d))/g, '.') + (decimal ? ',' + decimal : '');
};

/**
 * MONTO DE UNA ESTADIA/RESERVA POR HORA (REGLA ESCALONADA POR BLOQUES DE 30 MIN).
 * n = ceil(horas * 2) con minimo 1 bloque. n == 1 -> fraccion de 30 min.
 * n >= 2 -> (n // 2) * hora + ((n - 1) // 2) * fraccion (alterna hora, fraccion...).
 * Debe espejar BillingService.hourly_amount_from_rates del backend.
 */
export function computeHourlyAmount(durationHours, hora, fraccion) {
    const n = Math.max(1, Math.ceil((durationHours || 0) * 2));
    if (n === 1) return fraccion;
    return Math.floor(n / 2) * hora + Math.floor((n - 1) / 2) * fraccion;
}

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
    const year = d.getFullYear().toString().slice(-2);
    const hours = d.getHours().toString().padStart(2, '0');
    const mins = d.getMinutes().toString().padStart(2, '0');
    return `${day}-${month}-${year} ${hours}:${mins}`;
}

/**
 * FORMATEADORES DE FECHA/HORA UNIFICADOS (SIEMPRE 24H).
 * Todos los campos fijan `hour12: false` para que el formato NO dependa del
 * default del locale (es-AR resuelve 12h en algunos engines si no se aclara).
 * Usan las mismas opciones que las llamadas originales para no cambiar la
 * apariencia de las horas que ya eran 24h.
 */
const _TIME_FMT = {
    // HH:MM (ej: "14:05")
    time: new Intl.DateTimeFormat('es-AR', { hour: '2-digit', minute: '2-digit', hour12: false }),
    // HH:MM:SS (ej: "14:05:07")
    timeSec: new Intl.DateTimeFormat('es-AR', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }),
    // DD/MM/YYYY HH:MM:SS (ej: "11/09/2026, 14:05:07")
    dateTime: new Intl.DateTimeFormat('es-AR', { year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false }),
    // DD/MM HH:MM (ej: "11/9, 14:05")
    dayTime: new Intl.DateTimeFormat('es-AR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }),
    // D/M/YYYY HH:MM:SS (ej: "11/9/2026, 14:05:07")
    localDateTime: new Intl.DateTimeFormat('es-AR', { year: 'numeric', month: 'numeric', day: 'numeric', hour: 'numeric', minute: 'numeric', second: 'numeric', hour12: false })
};

/**
 * CONVIERTE UN STRING DE FECHA A Date DE FORMA SEGURA EN TODOS LOS ENGINES.
 * NORMALIZA EL FORMATO CANONICO DE BACKEND 'YYYY-MM-DD HH:MM:SS' (SPACE) A ISO CON 'T'
 * (SIN ESO, SAFARI/ALGUNOS ENGINES DEVUELVEN Invalid Date PARA SPACE-STRINGS).
 */
export function parseFecha(s) {
    if (s instanceof Date) return s;
    if (typeof s === 'number') return new Date(s);
    const str = String(s ?? '');
    return new Date(/^\d{4}-\d{2}-\d{2} /.test(str) ? str.replace(' ', 'T') : str);
}

function _coerceDate(d) {
    if (!d) return null;
    const dt = parseFecha(d);
    return isNaN(dt.getTime()) ? null : dt;
}

export function formatTime(d) {
    const dt = _coerceDate(d);
    return dt ? _TIME_FMT.time.format(dt) : '';
}

export function formatTimeSeconds(d) {
    const dt = _coerceDate(d);
    return dt ? _TIME_FMT.timeSec.format(dt) : '';
}

export function formatDateTime(d) {
    const dt = _coerceDate(d);
    return dt ? _TIME_FMT.dateTime.format(dt) : '';
}

export function formatDayTime(d) {
    const dt = _coerceDate(d);
    return dt ? _TIME_FMT.dayTime.format(dt) : '';
}

export function formatLocalDateTime(d) {
    const dt = _coerceDate(d);
    return dt ? _TIME_FMT.localDateTime.format(dt) : '';
}

/**
 * MUESTRA UNA NOTIFICACION PREMIUM (TOAST).
 * TIPOS: 'SUCCESS', 'ERROR', 'INFO', 'POR DEFECTO'
 */
export function showToast(msg, type = 'default', duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    // Evitar toasts duplicados idénticos en pantalla simultáneamente
    const existing = Array.from(container.querySelectorAll('.toast:not(.hiding)'))
        .some(el => el.querySelector('span')?.textContent?.trim() === (msg || '').trim());
    if (existing) return;

    // CREAR ELEMENTO
    const t = document.createElement('div');
    t.className = `toast ${type}`;
    // El contenedor ya es una live region "polite" (ver modals_global.html); los
    // error/warning se anuncian de inmediato con role="alert" para no quedar
    // detras de otro mensaje en curso.
    if (type === 'error' || type === 'warning') t.setAttribute('role', 'alert');

    // ASIGNAR ICONO SEGUN TIPO
    let icon = 'fa-bell';
    if (type === 'success') icon = 'fa-circle-check';
    else if (type === 'error') icon = 'fa-circle-exclamation';
    else if (type === 'info') icon = 'fa-circle-info';
    else if (type === 'warning') icon = 'fa-triangle-exclamation';

    t.innerHTML = `
        <i class="fas ${icon} toast-icon"></i>
        <span>${msg}</span>
    `;

    container.appendChild(t);

    // Los informativos se van solos: antes exigian un click en cualquier parte
    // de la pantalla para desaparecer. Los error/warning quedan fijos hasta que
    // el usuario los descarte, porque suelen pedir una accion.
    if (duration > 0 && type !== 'error' && type !== 'warning') {
        setTimeout(() => _dismissToast(t), duration);
    }
}

// DESCARTA UN TOAST CON SU ANIMACION DE SALIDA
function _dismissToast(t) {
    if (!t || t.classList.contains('hiding')) return;
    t.classList.add('hiding');
    setTimeout(() => { if (t.parentNode) t.remove(); }, 400);
}

// CERRAR TODOS LOS TOASTS AL HACER CLICK EN CUALQUIER LUGAR DE LA PANTALLA
function _closeAllToasts() {
    const container = document.getElementById('toast-container');
    if (!container) return;
    container.querySelectorAll('.toast:not(.hiding)').forEach(_dismissToast);
}

let _toastsClickBound = false;
if (!_toastsClickBound) {
    _toastsClickBound = true;
    document.addEventListener('click', _closeAllToasts, true);
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
        if (msg && msg.includes('<')) {
            msgEl.innerHTML = msg;
        } else {
            msgEl.innerText = msg || 'Esta acción no se puede deshacer.';
        }
        
        openModal('modal-confirm');

        const handleResponse = (result) => {
            closeModal('modal-confirm');
            btnOk.onclick = null;
            btnCancel.onclick = null;
            resolve(result);
        };

        btnOk.onclick = () => handleResponse(true);
        btnCancel.onclick = () => handleResponse(false);
        
        modal.onclick = (e) => { if(e.target === modal) handleResponse(false); };
    });
}

export function showChoice(title, msg, options) {
    return new Promise((resolve) => {
        const modal = document.getElementById('modal-choice');
        const titleEl = document.getElementById('choice-title');
        const msgEl = document.getElementById('choice-msg');
        const optsEl = document.getElementById('choice-options');
        const btnCancel = document.getElementById('choice-btn-cancel');

        if (!modal || !optsEl || !btnCancel) return resolve(null);

        titleEl.innerText = title || 'Seleccioná una opción';
        msgEl.innerText = msg || '';

        optsEl.innerHTML = (options || []).map((o) => {
            const label = typeof o === 'object' ? (o.label || '') : o;
            const icon = typeof o === 'object' ? (o.icon || 'fa-circle') : 'fa-circle';
            return `
                <button type="button" class="choice-option" data-value="${label}">
                    <i class="fas ${icon}"></i>
                    <span>${label}</span>
                </button>
            `;
        }).join('');

        openModal('modal-choice');

        const cleanup = () => {
            closeModal('modal-choice');
            btnCancel.onclick = null;
            optsEl.querySelectorAll('.choice-option').forEach((b) => { b.onclick = null; });
            modal.onclick = null;
        };

        optsEl.querySelectorAll('.choice-option').forEach((b) => {
            b.onclick = () => { cleanup(); resolve(b.dataset.value); };
        });
        btnCancel.onclick = () => { cleanup(); resolve(null); };
        modal.onclick = (e) => { if (e.target === modal) { cleanup(); resolve(null); } };
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
 * HABILITA UN INPUT PARA ACEPTAR SOLO DIGITOS (EJ: DNI, TELEFONO).
 * Bloquea letras/simbolos al tipear y limpia lo pegado o autocompletado.
 */
export function bindDigitsOnly(input) {
    input.addEventListener('keydown', (e) => {
        if (e.ctrlKey || e.metaKey || e.altKey || e.key.length > 1) return;
        if (/\D/.test(e.key)) e.preventDefault();
    });
    input.addEventListener('input', () => {
        input.value = input.value.replace(/\D/g, '');
    });
}

// INPUTS DE SOLO DIGITOS: SE BINDER AUTOMATICAMENTE LOS MARCADOS CON LA CLASE "digits-only"
document.querySelectorAll('input.digits-only').forEach(bindDigitsOnly);

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

/**
 * ETIQUETA LEGIBLE DEL MÉTODO DE PAGO PARA EL REPORTE FINANCIERO.
 * p.metodo: CAJA | Caja | Efectivo | DIGITAL | SALDO | MERCADOPAGO | Mercado Pago | ...
 */
export function metodoPagoReport(metodo, tipo) {
    const m = String(metodo || '').toUpperCase().replace(/\s+/g, '');
    if (m === 'CAJA' || m === 'EFECTIVO') return 'PAGO EN CAJA';
    if (m === 'MERCADOPAGO') return 'MERCADO PAGO';
    if (m === 'SALDO' || m === 'DIGITAL') return 'PAGO DIGITAL';
    if (m === 'TRANSFERENCIA') return 'TRANSFERENCIA';
    if (m === 'TARJETA') return 'TARJETA';
    if (m === 'OTRO') return 'OTRO';
    if (m === 'BILLETERAAUTOPASS') return 'PAGO DIGITAL';
    if (tipo === 'Reembolso') return 'REEMBOLSO DIGITAL';
    return 'PAGO DIGITAL';
}

/**
 * ESCAPA HTML PARA INTERPOLAR DATOS DEL BACKEND EN innerHTML (XSS).
 */
export function escapeHtml(s) {
    return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

/**
 * SCROLL RESPETANDO `prefers-reduced-motion` (WCAG 2.3.3).
 *
 * El bloque CSS de `static/css/base/animations.css` frena transiciones y
 * animaciones, pero `scroll-behavior` NO alcanza a
 * `scrollIntoView({ behavior: 'smooth' })`: eso se resuelve en JS, no en CSS.
 * Por eso las llamadas del proyecto pasan por acá en vez de codificar
 * `behavior: 'smooth'` en cada sitio.
 *
 * Se usa `auto` y no `instant` porque `instant` no es un valor estandar de la
 * API: `auto` delega en el `scroll-behavior` computado, que el bloque de
 * reduced-motion ya fija en `auto`.
 */
const _motionQuery = typeof window !== 'undefined' && window.matchMedia
    ? window.matchMedia('(prefers-reduced-motion: reduce)')
    : null;

export function prefersReducedMotion() {
    return !!(_motionQuery && _motionQuery.matches);
}

export function scrollToElement(el, options = {}) {
    if (!el || typeof el.scrollIntoView !== 'function') return;
    // `behavior` va DESPUES del spread a proposito: si un llamador pasa uno,
    // la preferencia del usuario tiene que ganarle igual.
    el.scrollIntoView({
        ...options,
        behavior: prefersReducedMotion() ? 'auto' : 'smooth'
    });
}
