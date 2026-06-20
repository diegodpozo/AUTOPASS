import api from './api.js';
import { toTitle, formatDate, showToast, showConfirm } from './utils.js';
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
    
    const pts = document.getElementById('points-val'); if (pts) pts.innerText = user.puntos_acumulados || 0;
    const pagePts = document.getElementById('points-page-val'); if (pagePts) pagePts.innerText = user.puntos_acumulados || 0;
    const balance = document.getElementById('balance-val'); if (balance) balance.innerText = `$${(user.saldo || 0).toFixed(2)}`;
    
    const initials = (user.nombre[0] || '') + (user.apellido[0] || '');
    const initialsEl = document.getElementById('user-initials'); if (initialsEl) initialsEl.innerText = initials.toUpperCase();
    const fullNameEl = document.getElementById('profile-full-name'); if (fullNameEl) fullNameEl.innerText = `${toTitle(user.nombre)} ${toTitle(user.apellido)}`;
    
    const memberSinceEl = document.getElementById('user-member-since');
    if (memberSinceEl) {
        const date = user.created_at ? new Date(user.created_at) : new Date();
        memberSinceEl.innerText = `Miembro desde: ${date.toLocaleDateString()}`;
    }

    updatePointsProgress(user.puntos_acumulados || 0);

    const resStays = await api.get('/user/payment-history');
    if (resStays.ok) {
        const staysEl = document.getElementById('acc-stat-stays'); if (staysEl) staysEl.innerText = resStays.data.length;
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
    
    if (targetEl) targetEl.innerText = `Prox: ${nextTarget} pts`;
    if (footerText) {
        const remaining = nextTarget - currentPts;
        footerText.innerText = remaining > 0 ? 
            `¡Te faltan solo ${remaining} puntos para tu próximo beneficio AutoPass!` : 
            `¡Llegaste al nivel máximo! Canjeá tus puntos por estadías gratis.`;
    }
}

export async function loadPointsData() {
    await loadProfile(); 
    loadPromotions();
    loadPointsHistory();
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

        return `
        <div class="promo-card">
            <div class="branch-badge ${isGlobal ? 'global' : ''}">
                <i class="fas ${isGlobal ? 'fa-globe' : 'fa-location-dot'}"></i> ${branchName}
            </div>
            <div class="promo-header">
                <div class="promo-icon"><i class="${p.icono}"></i></div>
                <div class="promo-title">${p.titulo}</div>
            </div>
            <div class="promo-body">
                <p class="promo-desc">${p.descripcion}</p>
                <div class="promo-cost">${p.costo_puntos} <span>puntos</span></div>
            </div>
            <div class="promo-footer">
                <button class="btn-redeem" onclick="redeemPoints(${p.id}, ${p.costo_puntos})" 
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
                        ${isPos ? '+' : ''}${h.cantidad}
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
    
    const e = document.getElementById('total-earned-pts'); if (e) e.innerText = total_earned;
    const r = document.getElementById('total-redeemed-pts'); if (r) r.innerText = total_redeemed;
}

export function changePtsPage(delta) {
    loadPointsHistory(currentPtsPage + delta);
}

export async function redeemPoints(promoId, cost) {
    if (!await showConfirm('Confirmar Canje', `¿Canjear ${cost} puntos?`)) return;
    const res = await api.post(`/user/redeem/${promoId}`);
    if (res.ok) { showToast(res.data.message); await loadPointsData(); }
    else showToast(res.error, 'error');
}

export async function saveField(field, newValue) {
    const res = await api.put('/user/me', { [field]: newValue });
    if (res.ok) { showToast(`${toTitle(field)} actualizado`); await loadProfile(); return true; }
    else { showToast(res.error, 'error'); return false; }
}

export async function changePassword(current, newPass) {
    const res = await api.post('/user/change-password', { current_password: current, new_password: newPass });
    if (res.ok) { showToast('Contraseña actualizada'); return true; }
    else { showToast(res.error, 'error'); return false; }
}

export async function processRecharge(amount) {
    const res = await api.post('/user/recharge-balance', { monto: amount });
    if (res.ok) { showToast(`¡Carga de $${amount.toFixed(2)} exitosa!`); await loadProfile(); return true; }
    else { showToast(res.error, 'error'); return false; }
}
