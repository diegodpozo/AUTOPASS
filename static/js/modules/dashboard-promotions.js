import api from './api.js';
import { showToast, showConfirm } from './utils.js';

/**
 * DASHBOARD PROMOTIONS MODULE
 * Gestión de beneficios y promociones para el sistema de fidelización.
 */

export async function loadPromotionsAdmin() {
    const tbody = document.getElementById('promotions-admin-table-body');
    if (!tbody) return;

    const res = await api.get('/admin/promotions');
    if (res.ok) {
        tbody.innerHTML = res.data.map(p => `
            <tr>
                <td data-label="Beneficio">
                    <div class="flex-row items-center gap-10">
                        <div class="header-icon-box xs" style="background: rgba(197, 160, 89, 0.1); border: 1px solid rgba(197, 160, 89, 0.2);">
                            <i class="${p.icono || 'fas fa-gift'} text-dorado" style="font-size: 0.8rem;"></i>
                        </div>
                        <div class="flex-col">
                            <b class="text-white text-small">${p.titulo}</b>
                            <span class="text-xs text-muted" style="max-width: 180px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">${p.descripcion}</span>
                        </div>
                    </div>
                </td>
                <td data-label="Puntos" class="text-center">
                    <div class="points-badge-sm mx-auto"><i class="fas fa-star"></i> ${p.costo_puntos}</div>
                </td>
                <td data-label="Estado" class="text-center hidden-mobile">
                    <span class="badge-status badge-${p.activa ? 'active' : 'inactive'} mx-auto">${p.activa ? 'ACTIVA' : 'INACTIVA'}</span>
                </td>
                <td data-label="Acciones">
                    <div class="flex-row gap-8 justify-center">
                        <button class="btn-icon-premium sm" onclick="togglePromotion(${p.id})" title="${p.activa ? 'Desactivar' : 'Activar'}">
                            <i class="fas ${p.activa ? 'fa-toggle-on text-success' : 'fa-toggle-off text-muted'}"></i>
                        </button>
                        <button class="btn-icon-premium sm danger btn-delete-promo" onclick="deletePromotion(${p.id})" title="Eliminar">
                            <i class="fas fa-xmark"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `).join('') || '<tr><td colspan="4" class="text-center py-20">No hay promociones registradas.</td></tr>';
    } else {
        tbody.innerHTML = `<tr><td colspan="4" class="text-center py-20 text-danger">Error: ${res.error}</td></tr>`;
    }
}

export function showCreatePromotionModal() {
    const rol = localStorage.getItem('rol');
    const field = document.querySelector('.admin-only-field');
    if (field) {
        field.style.display = (rol === 'admin') ? 'block' : 'none';
    }
    
    // Reset icon picker
    document.querySelectorAll('.icon-option').forEach(opt => opt.classList.remove('active'));
    const defaultOpt = document.querySelector('.icon-option[data-icon="fas fa-gift"]');
    if (defaultOpt) defaultOpt.classList.add('active');
    document.getElementById('promo-icono').value = 'fas fa-gift';

    if (window.openModal) window.openModal('modal-create-promotion');
}

export function selectPromoIcon(element) {
    document.querySelectorAll('.icon-option').forEach(opt => opt.classList.remove('active'));
    element.classList.add('active');
    document.getElementById('promo-icono').value = element.dataset.icon;
}

export async function handleCreatePromotion() {
    const payload = {
        titulo: document.getElementById('promo-titulo').value,
        descripcion: document.getElementById('promo-descripcion').value,
        costo_puntos: parseInt(document.getElementById('promo-costo').value),
        icono: document.getElementById('promo-icono').value,
        sucursal: document.getElementById('promo-sucursal').value || null
    };

    const res = await api.post('/admin/promotions', payload);
    if (res.ok) {
        showToast('Promoción creada');
        if (window.closeModal) window.closeModal('modal-create-promotion');
        document.getElementById('form-create-promotion').reset();
        loadPromotionsAdmin();
    } else {
        showToast(res.error);
    }
}

export async function togglePromotion(id) {
    const res = await api.post(`/admin/promotions/${id}/toggle`);
    if (res.ok) {
        showToast(res.data.activa ? 'Promoción activada' : 'Promoción desactivada');
        loadPromotionsAdmin();
    } else {
        showToast(res.error);
    }
}

export async function deletePromotion(id) {
    if (!await showConfirm('Eliminar Promoción', '¿Estás seguro de eliminar este beneficio permanentemente?')) return;
    const res = await api.delete(`/admin/promotions/${id}`);
    if (res.ok) {
        showToast('Promoción eliminada');
        loadPromotionsAdmin();
    } else {
        showToast(res.error);
    }
}
