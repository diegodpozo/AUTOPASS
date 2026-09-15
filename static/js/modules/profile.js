import api from './api.js';
import { toTitle, formatDate, formatNum, formatPlate, showToast, showConfirm } from './utils.js';
import { closeModal } from './ui.js';

/**
 * PERFIL MODULO
 * GESTION DE PERFIL DE USUARIO, PUNTOS Y RECARGA DE SALDO.
 */

export async function loadProfile() {
    const res = await api.get('/user/me');
    if (!res.ok) return;

    const user = res.data;
    localStorage.setItem('userData', JSON.stringify(user));
    localStorage.setItem('nombre', toTitle(user.nombre));
    localStorage.setItem('apellido', toTitle(user.apellido));
    
    const welcomeEl = document.getElementById('welcome-greeting');
    if (welcomeEl) welcomeEl.innerText = `¡HOLA, ${user.nombre.toUpperCase()}!`;
    
    const pts = document.getElementById('points-val'); if (pts) pts.innerText = formatNum(user.puntos_acumulados || 0);
    const pagePts = document.getElementById('points-page-val'); if (pagePts) pagePts.innerText = formatNum(user.puntos_acumulados || 0);
    const balance = document.getElementById('balance-val'); if (balance) balance.innerText = `$${formatNum(user.saldo || 0)}`;
    
    const initials = (user.nombre[0] || '') + (user.apellido[0] || '');
    const initialsEl = document.getElementById('user-initials'); if (initialsEl) initialsEl.innerText = initials.toUpperCase();
    const fullNameEl = document.getElementById('profile-full-name'); if (fullNameEl) fullNameEl.innerText = `${toTitle(user.nombre)} ${toTitle(user.apellido)}`;
    
    const memberSinceEl = document.getElementById('user-member-since');
    if (memberSinceEl) {
        const date = user.created_at ? new Date(user.created_at) : new Date();
        const d = date.getDate().toString().padStart(2,'0');
        const m = (date.getMonth()+1).toString().padStart(2,'0');
        const y = date.getFullYear().toString().slice(-2);
        memberSinceEl.innerText = `Miembro desde: ${d}-${m}-${y}`;
    }

    updatePointsProgress(user.puntos_acumulados || 0);

    const resStays = await api.get('/user/payment-history');
    if (resStays.ok) {
        const staysEl = document.getElementById('acc-stat-stays'); if (staysEl) staysEl.innerText = formatNum(resStays.data.length);
    }

    const fields = ['nombre', 'apellido', 'email', 'telefono', 'dni'];
    fields.forEach(f => {
        const disp = document.getElementById(`display-${f}`);
        if (disp) {
            let val = user[f];
            if (f === 'nombre' || f === 'apellido') val = toTitle(val);
            if (f === 'telefono' && val) val = val.replace(/(\d{2})(\d{4})(\d+)/, "$1 $2 $3");
            if (f === 'dni' && val) val = val.toString().replace(/(\d{2})(\d{3})(\d{3})/, "$1.$2.$3");
            disp.innerText = val || 'S/D';
        }
    });

    const rol = localStorage.getItem('rol');
    if (rol === 'admin' || rol === 'staff') {
        const headerRight = document.querySelector('.profile-header-right');
        if (headerRight && !document.getElementById('btn-go-admin')) {
            const btn = document.createElement('button');
            btn.id = 'btn-go-admin';
            btn.className = 'btn-premium';
            btn.style.marginRight = '15px';
            btn.innerHTML = `<i class="fas fa-gauge-high"></i> ${rol === 'admin' ? 'PANEL ADMIN' : 'PANEL CONTROL'}`;
            btn.onclick = () => window.location.href = '/dashboard';
            headerRight.prepend(btn);
        }
    }
}

export function updatePointsProgress(currentPts) {
    const progressBar = document.getElementById('points-progress-bar');
    const targetEl = document.getElementById('points-next-reward');
    const footerText = document.getElementById('points-progress-text');
    
    if (!progressBar) return;

    const targets = [500, 1000, 2500, 5000, 10000];
    const nextTarget = targets.find(t => t > currentPts) || targets[targets.length - 1];
    const prevTarget = targets[targets.indexOf(nextTarget) - 1] || 0;
    
    const progress = ((currentPts - prevTarget) / (nextTarget - prevTarget)) * 100;
    progressBar.style.width = `${Math.min(100, progress)}%`;
    
    if (targetEl) targetEl.innerText = `Prox: ${formatNum(nextTarget)} pts`;
    if (footerText) {
        const remaining = nextTarget - currentPts;
        footerText.innerText = remaining > 0 ? 
            `¡Te faltan solo ${formatNum(remaining)} puntos para tu próximo beneficio AutoPass!` : 
            `¡Llegaste al nivel máximo! Canjeá tus puntos por estadías gratis.`;
    }
}

export async function loadPointsData() {
    await loadProfile(); 
    loadPromotions();
    loadVouchers();
    loadPointsHistory();
}

let cachedUserTickets = [];
let currentVoucherTab = 'VIGENTES';

// CAMBIAR PESTAÑA DE VOUCHERS (VIGENTES / FINALIZADOS)
export function switchVoucherTab(tab) {
    currentVoucherTab = tab;
    const btnVig = document.getElementById('btn-vouchers-vigentes');
    const btnFin = document.getElementById('btn-vouchers-finalizados');
    if (btnVig && btnFin) {
        btnVig.classList.toggle('active', tab === 'VIGENTES');
        btnFin.classList.toggle('active', tab === 'FINALIZADOS');
    }
    renderVouchers();
}

// RENDERIZADO REACTIVO DE VOUCHERS SEGUN PESTAÑA SELECCIONADA
export function renderVouchers() {
    const grid = document.getElementById('vouchers-grid') || document.getElementById('vouchers-list');
    if (!grid) return;

    // SI HAY TICKETS SIN UBICACION PROPIA PERO CON SUCURSAL, GARANTIZAR CACHE DE SUCURSALES PARA EL FALLBACK DE DIRECCION
    const needsBranchCache = cachedUserTickets.some(t => !((t.latitude && t.longitude) || t.direccion) && t.sucursal && String(t.sucursal) !== 'GLOBAL');
    if (needsBranchCache && !cachedBranches && !_branchesCachePromise) {
        getBranchesCache().then(() => renderVouchers());
        return;
    }

    const vigentes = cachedUserTickets.filter(t => (t.estado || '').toUpperCase() === 'VIGENTE');
    const finalizados = cachedUserTickets.filter(t => (t.estado || '').toUpperCase() !== 'VIGENTE');

    // Actualizar contadores en las pestañas
    const countVig = document.getElementById('count-vouchers-vigentes');
    const countFin = document.getElementById('count-vouchers-finalizados');
    if (countVig) countVig.innerText = vigentes.length;
    if (countFin) countFin.innerText = finalizados.length;

    const tabsBar = document.getElementById('voucher-tabs-bar');
    if (tabsBar) {
        tabsBar.style.display = cachedUserTickets.length > 0 ? 'flex' : 'none';
    }

    if (cachedUserTickets.length === 0) {
        grid.innerHTML = `
            <div class="empty-state-minimal" style="grid-column: 1 / -1; padding: 35px 20px; text-align: center;">
                <i class="fas fa-ticket" style="font-size: 2.2rem; color: #444; margin-bottom: 12px; display: block;"></i>
                <p style="color: #888; font-size: 0.85rem; margin: 0;">Aún no tenés vouchers canjeados. ¡Canjeá tus puntos por los beneficios disponibles abajo!</p>
            </div>`;
        return;
    }

    const filteredTickets = currentVoucherTab === 'VIGENTES' ? vigentes : finalizados;

    if (filteredTickets.length === 0) {
        if (currentVoucherTab === 'VIGENTES') {
            grid.innerHTML = `
                <div class="empty-state-minimal" style="grid-column: 1 / -1; padding: 35px 20px; text-align: center;">
                    <i class="fas fa-ticket-simple" style="font-size: 2rem; color: #444; margin-bottom: 10px; display: block;"></i>
                    <p style="color: #888; font-size: 0.85rem; margin: 0;">No tenés vouchers vigentes en este momento. ¡Canjeá tus puntos por beneficios abajo!</p>
                </div>`;
        } else {
            grid.innerHTML = `
                <div class="empty-state-minimal" style="grid-column: 1 / -1; padding: 35px 20px; text-align: center;">
                    <i class="fas fa-history" style="font-size: 2rem; color: #444; margin-bottom: 10px; display: block;"></i>
                    <p style="color: #888; font-size: 0.85rem; margin: 0;">No tenés vouchers finalizados o utilizados en tu historial.</p>
                </div>`;
        }
        return;
    }

    grid.innerHTML = filteredTickets.map(t => {
        const estado = (t.estado || 'VIGENTE').toUpperCase();
        const isVigente = estado === 'VIGENTE';
        const isUsado = estado === 'USADO';
        const isDiscount = t.tipo_canje === 'descuento_reserva';
        const branchName = t.sucursal ? t.sucursal.replace(/AUTOPASS\s+/i, '').trim().toUpperCase() : 'GLOBAL';
        const isGlobal = !t.sucursal;

        // DESCUENTO DE RESERVA: se renderiza como beneficio de descuento,
        // no como voucher con ticket/código QR (se aplica solo al abonar la reserva).
        if (isDiscount) {
            return renderDiscountCard(t, { estado, isVigente, isUsado, branchName, isGlobal });
        }

        let statusBadge = '';
        if (!isVigente) {
            if (isUsado) {
                statusBadge = '<span class="voucher-status-badge status-usado"><i class="fas fa-check-double"></i> UTILIZADO</span>';
            } else {
                statusBadge = `<span class="voucher-status-badge status-cancelado"><i class="fas fa-ban"></i> ${estado}</span>`;
            }
        }

        const branchBadge = `<span class="voucher-branch-badge ${isGlobal ? 'global' : ''}"><i class="fas ${isGlobal ? 'fa-globe' : 'fa-location-dot'}"></i> ${branchName}</span>`;

        // UBICACION DE CANJE (LINK A GOOGLE MAPS DESDE LAS COORDENADAS O LA DIRECCION)
        const mapsUrl = buildMapsUrl(t);
        const direccionMostrar = getVoucherDireccion(t);

        const escapedTitulo = formatTitulo(t.titulo).replace(/'/g, "\\'");
        const vencimientoStr = getVoucherVencimiento(t);

        return `
        <div class="voucher-card ${estado.toLowerCase()}">
            <div class="voucher-card-body">
                <div class="voucher-icon-wrap">
                    <i class="${t.icono || 'fas fa-gift'}"></i>
                </div>
                <div class="voucher-content-wrap">
                    <div class="voucher-content-header discount-header">
                        <div class="voucher-tags-group discount-tags">
                            ${statusBadge}
                        </div>
                        <h3 class="voucher-card-title discount-card-title">${formatTitulo(t.titulo)}</h3>
                        ${branchBadge}
                    </div>
                    ${t.descripcion ? `<p class="voucher-card-desc">${t.descripcion}</p>` : ''}
                    ${mapsUrl && direccionMostrar ? `<a class="voucher-address-link" href="${mapsUrl}" target="_blank" rel="noopener"><i class="fas fa-location-dot"></i> ${direccionMostrar}</a>` : ''}
                    <div class="voucher-card-meta">
                        ${vencimientoStr ? `<span>Vto.: ${vencimientoStr}</span>` : ''}
                        ${t.fecha_uso ? `<span><i class="fas fa-check"></i> Usado: ${formatDate(t.fecha_uso)}</span>` : ''}
                    </div>
                </div>
            </div>

            <div class="voucher-card-divider">
                <div class="voucher-cutout left"></div>
                <div class="voucher-cutout right"></div>
            </div>

            <div class="voucher-card-footer">
                <button class="btn-voucher-action btn-voucher-qr" onclick="showCanjeTicketById(${t.id})" title="Ver comprobante y código QR">
                    <i class="fas fa-ticket"></i> ${isVigente ? 'TICKET DE CANJE' : 'VER TICKET'}
                </button>
                ${isVigente ? `
                <button class="btn-voucher-action btn-voucher-cancel" onclick="cancelVoucher(${t.id}, '${escapedTitulo}')" title="Cancelar beneficio y recuperar puntos">
                    <i class="fas fa-undo"></i> CANCELAR
                </button>` : ''}
            </div>
        </div>`;
    }).join('');
}

// CARD ESPECIAL PARA DESCUENTOS DE RESERVA (tipo_canje = 'descuento_reserva').
// No es un voucher canjeable en puerta: es un beneficio que se descuenta solo al pagar/reservar.
function renderDiscountCard(t, { estado, isVigente, isUsado, branchName, isGlobal }) {
    const val = t.valor_descuento || 0;
    const escapedTitulo = formatTitulo(t.titulo).replace(/'/g, "\\'");

    let statusBadge = '';
    if (!isVigente) {
        statusBadge = isUsado
            ? '<span class="voucher-status-badge status-usado"><i class="fas fa-check-double"></i> UTILIZADO</span>'
            : `<span class="voucher-status-badge status-cancelado"><i class="fas fa-ban"></i> ${estado}</span>`;
    }

    let usadoMeta = '';
    if (t.fecha_uso) {
        usadoMeta = isUsado && t.reserva_id
            ? `<span><i class="fas fa-check"></i> Aplicado en reserva #${t.reserva_id} · ${formatDate(t.fecha_uso)}</span>`
            : `<span><i class="fas fa-check"></i> Usado: ${formatDate(t.fecha_uso)}</span>`;
    }

    const vencimientoStr = getVoucherVencimiento(t);

    const metaInfo = isVigente
        ? `<div class="discount-meta-pct">
            <span class="discount-pct-row"><span class="discount-pct">${val}% </span><span class="discount-pct-suffix">DE DESCUENTO</span></span>
            <span class="discount-auto-label">SE APLICA AUTOMÁTICAMENTE AL RESERVAR</span>
            ${vencimientoStr ? `<span class="discount-vencimiento">Vto.: <b>${vencimientoStr}</b></span>` : ''}
        </div>`
        : `<span><i class="far fa-calendar-alt"></i> Canjeado: ${formatDate(t.created_at)}</span>`;

    const autoNote = isVigente
        ? ''
        : (isUsado
            ? `<div class="discount-auto-note muted"><i class="fas fa-check-double"></i> ${t.reserva_id ? `Aplicado a la reserva #${t.reserva_id}.` : 'Beneficio ya utilizado.'}</div>`
            : `<div class="discount-auto-note muted"><i class="fas fa-ban"></i> Cancelado y puntos reintegrados.</div>`);

    return `
    <div class="voucher-card discount-card ${estado.toLowerCase()}">
        <div class="voucher-card-body">
            <div class="voucher-icon-wrap discount">
                <i class="${t.icono || 'fas fa-percent'}"></i>
            </div>
            <div class="voucher-content-wrap">
                <div class="voucher-content-header discount-header">
                    <div class="voucher-tags-group discount-tags">
                        ${statusBadge}
                    </div>
                    <h3 class="voucher-card-title discount-card-title">${formatTitulo(t.titulo)}</h3>
                    <span class="voucher-branch-badge ${isGlobal ? 'global' : ''}"><i class="fas ${isGlobal ? 'fa-globe' : 'fa-location-dot'}"></i> ${branchName}</span>
                </div>
                ${t.descripcion ? `<p class="voucher-card-desc">${t.descripcion}</p>` : ''}
                ${getVoucherDireccion(t) ? `<a class="voucher-address-link" href="${buildMapsUrl(t)}" target="_blank" rel="noopener"><i class="fas fa-location-dot"></i> ${getVoucherDireccion(t)}</a>` : ''}
                <div class="voucher-card-meta">
                    ${metaInfo}
                    ${usadoMeta}
                </div>
            </div>
        </div>

        <div class="voucher-card-divider">
            <div class="voucher-cutout left"></div>
            <div class="voucher-cutout right"></div>
        </div>

        <div class="voucher-card-footer">
            ${autoNote}
            ${isVigente ? `
            <div class="discount-cancel-wrap">
                <button class="btn-voucher-action btn-voucher-cancel" onclick="cancelVoucher(${t.id}, '${escapedTitulo}')" title="Cancelar beneficio y recuperar puntos">
                    <i class="fas fa-undo"></i> CANCELAR
                </button>
            </div>` : ''}
        </div>
    </div>`;
}

const TITULO_STOPWORDS = new Set(['de', 'del', 'en', 'la', 'el', 'los', 'las', 'y', 'a', 'al', 'por', 'para', 'con']);

// NORMALIZA TITULOS ESCRITOS EN MAYUSCULAS A TIPO TITULO ("LAVADO" -> "Lavado")
function formatTitulo(titulo) {
    if (!titulo) return 'Beneficio AutoPass';
    if (titulo !== titulo.toUpperCase()) return titulo;
    return titulo
        .toLowerCase()
        .split(/\s+/)
        .filter(Boolean)
        .map(w => TITULO_STOPWORDS.has(w) ? w : w.charAt(0).toUpperCase() + w.slice(1))
        .join(' ');
}

// ---------------------------------------------------------------------------
// UBICACION DE CANJE: CACHE DE SUCURSALES PARA RESOLVER DIRECCIONES
// ---------------------------------------------------------------------------
let cachedBranches = null;
let _branchesCachePromise = null;

export function getBranchesCache() {
    if (cachedBranches) return Promise.resolve(cachedBranches);
    if (!_branchesCachePromise) {
        _branchesCachePromise = fetch('/v1/parking/branches')
            .then(r => r.ok ? r.json() : [])
            .then(data => { cachedBranches = data || []; return cachedBranches; })
            .catch(() => { cachedBranches = []; _branchesCachePromise = null; return cachedBranches; });
    }
    return _branchesCachePromise;
}

// RESUELVE LA UBICACION DEL VOUCHER: SI EL TICKET NO GUARDO COORDENADAS/DIRECCION,
// FALLBACK A LA DIRECCION DE LA SUCURSAL ASIGNADA EN SU SNAPSHOT.
function resolveVoucherLocation(t) {
    if (!t) return null;

    if (t.latitude && t.longitude) {
        return { lat: parseFloat(t.latitude), lng: parseFloat(t.longitude), direccion: t.direccion || '' };
    }

    if (t.sucursal && t.sucursal !== 'GLOBAL' && cachedBranches && cachedBranches.length) {
        const b = cachedBranches.find(x => String(x.nombre || '').toLowerCase() === String(t.sucursal).toLowerCase());
        if (b) {
            if (b.latitude && b.longitude) {
                return { lat: parseFloat(b.latitude), lng: parseFloat(b.longitude), direccion: b.direccion || '' };
            }
            if (b.direccion) {
                return { lat: null, lng: null, direccion: b.direccion };
            }
        }
    }

    if (t.direccion) return { lat: null, lng: null, direccion: t.direccion };

    return null;
}

// DEVUELVE EL LINK A GOOGLE MAPS (MAPA COMUN DE CALLES / ROADMAP).
// OJO: NO agregar el sufijo "data=!3m1!1e3" porque ese token activa la vista AEREA (satelite/render 3D).
// Sin el token, "place/direccion/@lat,lng" ancla el pin en las coordenadas exactas con el mapa de calles plano.
function buildMapsUrl(t) {
    const loc = resolveVoucherLocation(t);
    if (!loc) return null;

    if (loc.direccion && loc.lat && loc.lng) {
        return `https://www.google.com/maps/place/${encodeURIComponent(loc.direccion)}/@${loc.lat},${loc.lng},16z`;
    }
    if (loc.direccion) {
        return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(loc.direccion)}`;
    }
    if (loc.lat && loc.lng) {
        return `https://www.google.com/maps?q=${loc.lat},${loc.lng}&z=16`;
    }
    return null;
}

// DEVUELVE LA DIRECCION RESUELTA (PROPIA DEL TICKET O FALLBACK DE LA SUCURSAL) PARA MOSTRAR AL USUARIO.
function getVoucherDireccion(t) {
    const loc = resolveVoucherLocation(t);
    return (loc && loc.direccion) || '';
}

// CALCULA LA FECHA DE VENCIMIENTO DEL VOUCHER (30 DIAS DESDE SU EMISION)
export function getVoucherVencimiento(t) {
    if (!t) return '';
    if (t.fecha_vencimiento) return formatDate(t.fecha_vencimiento);
    if (!t.created_at) return '';
    try {
        const d = new Date(t.created_at.replace('T', ' ').replace(/-/g, '/'));
        if (isNaN(d.getTime())) return '';
        d.setDate(d.getDate() + 30);
        const day = d.getDate().toString().padStart(2, '0');
        const month = (d.getMonth() + 1).toString().padStart(2, '0');
        const year = d.getFullYear().toString().slice(-2);
        const hours = d.getHours().toString().padStart(2, '0');
        const mins = d.getMinutes().toString().padStart(2, '0');
        return `${day}-${month}-${year} ${hours}:${mins}`;
    } catch (e) {
        return '';
    }
}

// LISTA DE VOUCHERS/TICKETS DE CANJE DEL USUARIO (GRILLA DE TARJETAS TIPO TICKET)
export async function loadVouchers() {
    const grid = document.getElementById('vouchers-grid') || document.getElementById('vouchers-list');
    if (!grid) return;
    const res = await api.get('/user/redemption-tickets');
    if (!res.ok) { 
        grid.innerHTML = '<p class="text-danger" style="grid-column: 1 / -1; padding: 30px; text-align: center;">Error al cargar tus vouchers.</p>'; 
        return; 
    }

    cachedUserTickets = res.data || [];
    await getBranchesCache();
    renderVouchers();
}

// CANCELAR CANJE DE BENEFICIO (VOUCHER VIGENTE)
export async function cancelVoucher(ticketId, titulo) {
    const ok = await showConfirm(
        '¿Cancelar beneficio?',
        `¿Estás seguro de que deseás cancelar "${titulo || 'este beneficio'}"? Los puntos canjeados serán reembolsados a tu cuenta.`
    );
    if (!ok) return;

    const res = await api.post(`/user/redemptions/${ticketId}/cancel`);
    if (res.ok) {
        showToast('Beneficio cancelado y puntos reembolsados.', 'success');
        await loadPointsData();
    } else {
        showToast(res.error || 'Error al cancelar el beneficio', 'error');
    }
}

// REABRE EL MODAL DE UN VOUCHER PREVIAMENTE CANJEADO BUSCANDOLO EN LA BD
export async function showCanjeTicketById(id) {
    const res = await api.get('/user/redemption-tickets');
    if (!res.ok) return;
    const t = res.data.find(x => x.id === id);
    if (!t) { showToast('No se encontró el voucher', 'error'); return; }
    await getBranchesCache();
    showCanjeTicket(t);
}

let cachedPromotions = [];
let promoBranchFilter = '';
const PROMO_FILTER_GLOBAL = '__GLOBALES__';

// COMPLETA/REFRESCA EL SELECTOR DE SUCURSAL DEL FILTRO DE PROMOS
function populatePromoBranchFilter(promos) {
    const sel = document.getElementById('promo-branch-filter');
    const bar = document.getElementById('promo-filter-bar');
    if (!sel) return;
    const branches = [...new Set(
        promos.filter(p => p.sucursal).map(p => p.sucursal.replace(/AUTOPASS\s+/i, '').trim())
    )];
    const hasGlobal = promos.some(p => !p.sucursal);
    if (promoBranchFilter === PROMO_FILTER_GLOBAL) {
        if (!hasGlobal) promoBranchFilter = '';
    } else if (!branches.includes(promoBranchFilter)) {
        promoBranchFilter = '';
    }
    let options = '<option value="">Todas las sucursales</option>';
    if (hasGlobal) {
        options += `<option value="${PROMO_FILTER_GLOBAL}">Globales</option>`;
    }
    options += branches.map(b => `<option value="${b}">${b}</option>`).join('');
    sel.innerHTML = options;
    sel.value = promoBranchFilter;
    if (bar) bar.style.display = promos.length ? 'flex' : 'none';
}

// RENDERIZA LA GRILLA DE PROMOS APLICANDO EL FILTRO DE SUCURSAL ACTUAL (las globales se ocultan al filtrar por sucursal)
function renderPromotionCards() {
    const grid = document.getElementById('promotions-grid');
    if (!grid) return;
    const promos = cachedPromotions || [];
    const filtered = promoBranchFilter === PROMO_FILTER_GLOBAL
        ? promos.filter(p => !p.sucursal)
        : promoBranchFilter
            ? promos.filter(p => p.sucursal && p.sucursal.replace(/AUTOPASS\s+/i, '').trim().toLowerCase() === promoBranchFilter.toLowerCase())
            : promos;

    if (filtered.length === 0) {
        grid.innerHTML = '<div class="empty-state-minimal"><p>No hay promociones para la sucursal seleccionada.</p></div>';
        return;
    }

    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    const currentPts = userData.puntos_acumulados || 0;

    grid.innerHTML = filtered.map(p => {
        const branchName = p.sucursal ? p.sucursal.replace(/AUTOPASS\s+/i, '').trim().toUpperCase() : 'GLOBAL';
        const isGlobal = !p.sucursal;
        const isDiscount = p.tipo_canje === 'descuento_reserva';

        const typeBadge = isDiscount
            ? `<div class="voucher-type-badge discount"><i class="fas fa-percent"></i> ${p.valor_descuento || 0}% DESC</div>`
            : `<div class="voucher-type-badge voucher"><i class="fas fa-ticket"></i> VOUCHER</div>`;

        const promoMapsUrl = buildMapsUrl(p);
        const promoDireccion = getVoucherDireccion(p);

        return `
        <div class="voucher-card promo-card">
            <div class="voucher-card-top">
                <div class="voucher-badges-group">
                    ${typeBadge}
                </div>
                <span class="voucher-branch-badge ${isGlobal ? 'global' : ''}">
                    <i class="fas ${isGlobal ? 'fa-globe' : 'fa-location-dot'}"></i> ${branchName}
                </span>
            </div>
            <div class="voucher-card-body">
                <div class="promo-card-title-row">
                    <div class="promo-icon"><i class="${p.icono || 'fas fa-gift'}"></i></div>
                    <h3 class="promo-title">${p.titulo}</h3>
                </div>
                <div class="voucher-content-wrap">
                    ${p.descripcion ? `<p class="voucher-card-desc">${p.descripcion}</p>` : ''}
                    ${promoMapsUrl && promoDireccion ? `<a class="voucher-address-link" href="${promoMapsUrl}" target="_blank" rel="noopener"><i class="fas fa-location-dot"></i> ${promoDireccion}</a>` : ''}
                    <div class="voucher-card-meta">
                        <span><i class="fas fa-coins"></i> ${formatNum(p.costo_puntos)} PUNTOS</span>
                    </div>
                </div>
            </div>
            <div class="voucher-card-divider">
                <div class="voucher-cutout left"></div>
                <div class="voucher-cutout right"></div>
            </div>
            <div class="voucher-card-footer">
                <button class="btn-voucher-action btn-voucher-qr btn-redeem" onclick="redeemPoints(${p.id}, ${p.costo_puntos}, '${p.tipo_canje || 'voucher'}')"
                    ${currentPts < p.costo_puntos ? 'disabled' : ''}>
                    <i class="fas fa-arrow-right"></i> CANJEAR
                </button>
            </div>
        </div>`;
    }).join('');
}

export async function loadPromotions() {
    const grid = document.getElementById('promotions-grid');
    if (!grid) return;
    const res = await api.get('/user/promotions');
    if (!res.ok) { grid.innerHTML = '<p class="text-danger">Error al cargar promociones.</p>'; return; }

    cachedPromotions = res.data || [];
    await getBranchesCache();
    populatePromoBranchFilter(cachedPromotions);

    if (cachedPromotions.length === 0) {
        grid.innerHTML = '<div class="empty-state-minimal"><p>No hay promociones activas.</p></div>';
        return;
    }
    renderPromotionCards();
}

// AL CAMBIAR EL FILTRO DE SUCURSAL SE RE-RENDERIZA LA GRILLA SIN VOLVER A FETCHEAR
export function applyPromoBranchFilter(value) {
    promoBranchFilter = value || '';
    renderPromotionCards();
}

let currentPtsPage = 1;

export async function loadPointsHistory(page = 1) {
    const list = document.getElementById('points-history-list');
    if (!list) return;
    
    currentPtsPage = page;
    const res = await api.get(`/user/points-history?page=${page}&limit=10`);
    if (!res.ok) return;

    const { items, total, pages, total_earned, total_redeemed } = res.data;

    if (items.length === 0 && page === 1) {
        list.innerHTML = '<p class="text-bold" style="padding: 30px; text-align: center;">No hay movimientos.</p>';
        const pag = document.getElementById('pts-pagination');
        if (pag) pag.style.display = 'none';
    } else {
        list.innerHTML = items.map(h => {
            const isPos = h.cantidad > 0;
            return `
                <div class="pts-item">
                    <div class="pts-item-info">
                        <span class="pts-item-reason">${h.motivo}</span>
                        <span class="pts-item-date">${formatDate(h.fecha)}</span>
                    </div>
                    <div class="pts-amount ${isPos ? 'pos' : 'neg'}">
                        ${isPos ? '+' : ''}${formatNum(h.cantidad)}
                    </div>
                </div>`;
        }).join('');

        // ACTUALIZAR NAVEGACION
        const pag = document.getElementById('pts-pagination');
        if (pag) {
            pag.style.display = 'flex'; // SIEMPRE MOSTRAR SI HAY ITEMS
            document.getElementById('pts-page-info').innerText = `Página ${page} de ${pages || 1}`;
            document.getElementById('btn-pts-prev').disabled = page === 1;
            document.getElementById('btn-pts-next').disabled = page >= pages;
        }
    }
    
    const e = document.getElementById('total-earned-pts'); if (e) e.innerText = formatNum(total_earned);
    const r = document.getElementById('total-redeemed-pts'); if (r) r.innerText = formatNum(total_redeemed);
}

export function changePtsPage(delta) {
    loadPointsHistory(currentPtsPage + delta);
}

export async function redeemPoints(promoId, cost, tipoCanje) {
    if (!await showConfirm('Confirmar Canje', `¿Canjear ${formatNum(cost)} puntos?`)) return;
    const res = await api.post(`/user/redeem/${promoId}`);
    if (res.ok) {
        showToast(res.data.message, 'success');
        await loadPointsData();

        const ticket = res.data.ticket;
        if (ticket) {
            if (tipoCanje === 'descuento_reserva') {
                showToast('Descuento canjeado. Se aplicará al abonar tu próxima reserva en la sucursal correspondiente.', 'info');
            } else {
                showCanjeTicket(ticket);
            }
        }
    } else {
        showToast(res.error, 'error');
    }
}

// MODAL DE TICKET DE CANJE (VOUCHER)
export function showCanjeTicket(t) {
    const modal = document.getElementById('modal-canje');
    if (!modal) return;
    document.getElementById('canje-codigo-display').innerText = `#${String(t.codigo || '').replace('#', '').padStart(6, '0')}`;
    document.getElementById('canje-titulo').innerText = formatTitulo(t.titulo);
    document.getElementById('canje-descripcion').innerText = t.descripcion || '';
    document.getElementById('canje-fecha').innerText = t.created_at ? formatDate(t.created_at) : 'Hoy';
    const vencEl = document.getElementById('canje-vencimiento');
    if (vencEl) vencEl.innerText = getVoucherVencimiento(t) || '---';
    document.getElementById('canje-sucursal').innerText = t.sucursal || 'GLOBAL';
    const dirEl = document.getElementById('canje-direccion');
    if (dirEl) {
        const mapsUrl = buildMapsUrl(t);
        const dirMostrar = getVoucherDireccion(t);
        dirEl.innerHTML = mapsUrl
            ? `<a href="${mapsUrl}" target="_blank" rel="noopener" style="color: var(--dorado); text-decoration: none; word-break: break-word;"><i class="fas fa-map-marked-alt"></i> ${dirMostrar || 'Ver en Google Maps'}</a>`
            : (dirMostrar || '---');
    }
    document.getElementById('canje-observacion').innerText = t.observacion || 'Será válido por 30 días desde la fecha de canje.';

    const qrContainer = document.getElementById('canje-qr');
    if (qrContainer) {
        qrContainer.innerHTML = '';
        if (window.QRCode) {
            new QRCode(qrContainer, { text: t.qr_data || `AUTOPASS|ID:${t.id}|CODE:${t.codigo}`, width: 160, height: 160, correctLevel: QRCode.CorrectLevel.H });
        }
    }
    modal.style.display = 'flex';
}

export function closeCanjeModal() {
    const modal = document.getElementById('modal-canje');
    if (modal) modal.style.display = 'none';
}

export async function shareCanjeTicket() {
    const ticket = document.getElementById('canje-to-capture');
    if (!ticket || !window.html2canvas) return;
    ticket.querySelectorAll('.no-print').forEach(el => el.style.opacity = '0');
    try {
        const canvas = await html2canvas(ticket, { backgroundColor: '#0a0a0a', scale: 3, useCORS: true });
        canvas.toBlob(async (blob) => {
            const file = new File([blob], `AutoPass_Canje_${Date.now()}.png`, { type: 'image/png' });
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({ files: [file], title: 'Mi Canje AutoPass' });
            } else {
                const link = document.createElement('a');
                link.download = `AutoPass_Canje_${Date.now()}.png`;
                link.href = URL.createObjectURL(blob);
                link.click();
            }
        });
    } catch (err) {
        showToast('Error al generar imagen', 'error');
        console.error(err);
    } finally {
        ticket.querySelectorAll('.no-print').forEach(el => el.style.opacity = '1');
    }
}

export async function saveField(field, newValue) {
    const res = await api.put('/user/me', { [field]: newValue });
    if (res.ok) { showToast(`${toTitle(field)} actualizado`, 'success'); await loadProfile(); return true; }
    else { showToast(res.error, 'error'); return false; }
}

export async function changePassword(current, newPass) {
    const res = await api.post('/user/change-password', { current_password: current, new_password: newPass });
    if (res.ok) { showToast('Contraseña actualizada', 'success'); return true; }
    else { showToast(res.error, 'error'); return false; }
}

export async function processRecharge(amount) {
    const res = await api.post('/user/recharge-balance', { monto: amount });
    if (res.ok) { showToast(`¡Carga de $${formatNum(amount)} exitosa!`, 'success'); await loadProfile(); return true; }
    else { showToast(res.error, 'error'); return false; }
}

export async function loadActiveStays() {
    const container = document.getElementById('active-stays-list');
    const wrap = document.getElementById('container-active-stays');
    if (!container) return;

    const res = await api.get('/user/balance/active-stays');
    if (!res.ok) {
        if (wrap) wrap.style.display = 'none';
        return;
    }
    const stays = (res.data || []).filter(s => !s.pago_confirmado);
    if (stays.length === 0) {
        if (wrap) wrap.style.display = 'none';
        return;
    }
    if (wrap) wrap.style.display = 'block';
    container.innerHTML = stays.map(s => `
        <div class="stay-item-premium">
            <div class="stay-plate">${formatPlate(s.patente)}</div>
            <div class="stay-info">
                <span class="stay-label">INGRESO</span>
                <span class="stay-value">${formatDate(s.ingreso || '')}</span>
            </div>
            <div class="stay-info">
                <span class="stay-label">DEUDA</span>
                <span class="stay-value" style="color:var(--dorado);">$${formatNum(s.deuda || 0)}</span>
            </div>
            <button class="btn-ultra btn-ultra-mp" onclick="payStayWithMp('${s.id}','${s.patente}')"><i class="fab fa-google-pay"></i> PAGAR CON MP</button>
        </div>`).join('');
}

export async function payStayWithMp(id, patente) {
    if (!await showConfirm('PAGAR ESTADÍA CON MERCADO PAGO', `Vas a abonar la estadía de la patente <b>${formatPlate(patente)}</b> con Mercado Pago.`)) return;
    const res = await api.post('/user/mercadopago/checkout', { tipo: 'estadia', access_log_id: id });
    if (res.ok && res.data && res.data.init_point) {
        showToast('Redirigiendo a Mercado Pago...', 'info');
        window.location.href = res.data.init_point;
    } else {
        showToast(res.error || 'Error al crear el pago', 'error');
    }
}
