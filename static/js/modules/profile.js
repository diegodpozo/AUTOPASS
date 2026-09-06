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

// LISTA DE VOUCHERS/TICKETS DE CANJE DEL USUARIO (TODOS, SIN FILTRO DE ESTADO)
export async function loadVouchers() {
    const list = document.getElementById('vouchers-list');
    if (!list) return;
    const res = await api.get('/user/redemption-tickets');
    if (!res.ok) { list.innerHTML = '<p class="text-danger" style="padding: 30px; text-align: center;">Error al cargar tus vouchers.</p>'; return; }

    const tickets = res.data;
    if (tickets.length === 0) {
        const c = document.getElementById('vouchers-container');
        if (c) c.style.display = 'none';
        return;
    }
    const c = document.getElementById('vouchers-container');
    if (c) c.style.display = '';

    list.innerHTML = tickets.map(t => `
        <div class="pts-item">
            <div class="pts-item-info">
                <span class="pts-item-reason">${t.titulo || 'Beneficio AutoPass'}</span>
                <span class="pts-item-date">Canjeado: ${formatDate(t.created_at)} · Suc. ${(t.sucursal || 'GLOBAL').replace('AUTOPASS ', '')}</span>
            </div>
            <div class="pts-voucher-actions">
                <button class="btn-redeem" style="min-width: auto; padding: 6px 12px;" onclick="showCanjeTicketById(${t.id})">VER QR</button>
            </div>
        </div>`).join('');
}

// REABRE EL MODAL DE UN VOUCHER PREVIAMENTE CANJEADO BUSCANDOLO EN LA BD
export async function showCanjeTicketById(id) {
    const res = await api.get('/user/redemption-tickets');
    if (!res.ok) return;
    const t = res.data.find(x => x.id === id);
    if (!t) { showToast('No se encontró el voucher', 'error'); return; }
    showCanjeTicket(t);
}

export async function loadPromotions() {
    const grid = document.getElementById('promotions-grid');
    if (!grid) return;
    const res = await api.get('/user/promotions');
    if (!res.ok) { grid.innerHTML = '<p class="text-danger">Error al cargar promociones.</p>'; return; }

    const promos = res.data;
    const userData = JSON.parse(localStorage.getItem('userData') || '{}');
    const currentPts = userData.puntos_acumulados || 0;

    if (promos.length === 0) {
        grid.innerHTML = '<div class="empty-state-minimal"><p>No hay promociones activas.</p></div>';
        return;
    }

    grid.innerHTML = promos.map(p => {
        const branchName = p.sucursal ? p.sucursal.replace('AUTOPASS ', '').toUpperCase() : 'GLOBAL';
        const isGlobal = !p.sucursal;
        const isDiscount = p.tipo_canje === 'descuento_reserva';
        const badge = isDiscount
            ? `<div class="promo-type-badge discount"><i class="fas fa-percent"></i> ${p.valor_descuento || 0}% DESC</div>`
            : `<div class="promo-type-badge voucher"><i class="fas fa-ticket"></i> VOUCHER</div>`;

        return `
        <div class="promo-card">
            ${badge}
            <div class="branch-badge ${isGlobal ? 'global' : ''}">
                <i class="fas ${isGlobal ? 'fa-globe' : 'fa-location-dot'}"></i> ${branchName}
            </div>
            <div class="promo-header">
                <div class="promo-icon"><i class="${p.icono}"></i></div>
                <div class="promo-title">${p.titulo}</div>
            </div>
            <div class="promo-body">
                <p class="promo-desc">${p.descripcion}</p>
                <div class="promo-cost">${formatNum(p.costo_puntos)} <span>puntos</span></div>
            </div>
            <div class="promo-footer">
                <button class="btn-redeem" onclick="redeemPoints(${p.id}, ${p.costo_puntos}, '${p.tipo_canje || 'voucher'}')" 
                    ${currentPts < p.costo_puntos ? 'disabled' : ''}>CANJEAR</button>
            </div>
        </div>`;
    }).join('');
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

// AJUSTE MANUAL DE PUNTOS (PRUEBAS): +10 / -10
export async function adjustPoints(delta) {
    const res = await api.post(`/user/points-adjust?delta=${delta}`);
    if (res.ok) {
        showToast(delta > 0 ? `+${delta} puntos` : `${delta} puntos`, 'success');
        await loadPointsData();
    } else {
        showToast(res.error || 'Error al ajustar puntos', 'error');
    }
}

// MODAL DE TICKET DE CANJE (VOUCHER)
export function showCanjeTicket(t) {
    const modal = document.getElementById('modal-canje');
    if (!modal) return;
    document.getElementById('canje-codigo-display').innerText = `#${String(t.codigo || '').replace('#', '').padStart(6, '0')}`;
    document.getElementById('canje-titulo').innerText = t.titulo || 'Beneficio AutoPass';
    document.getElementById('canje-descripcion').innerText = t.descripcion || '';
    document.getElementById('canje-fecha').innerText = t.created_at ? formatDate(t.created_at) : 'Hoy';
    document.getElementById('canje-sucursal').innerText = t.sucursal || 'GLOBAL';
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
