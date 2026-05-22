import api from './api.js';
import { showToast, showConfirm } from './utils.js';
import { toggleReservaForm } from './reservas.js'; // Necesitaremos exportarla después

/**
 * VEHICLES MODULE
 * Gestión de la flota vehicular del usuario.
 */

export async function loadVehicles() {
    const list = document.getElementById('vehicle-list');
    const statVehicles = document.getElementById('stat-vehicles');
    
    if (!list) return;

    const res = await api.get('/user/vehicles');
    if (!res.ok) {
        list.innerHTML = '<p style="color: var(--danger);">Error al cargar flota.</p>';
        return;
    }
    
    const vehicles = res.data;
    if (statVehicles) statVehicles.innerText = vehicles.length;
    
    if (vehicles.length === 0) {
        list.innerHTML = `
            <div class="empty-state-card" style="display: block; grid-column: 1 / -1; text-align: center; padding: 40px;">
                <i class="fas fa-car-side" style="font-size: 3rem; color: #333; margin-bottom: 15px; display: block;"></i>
                <p style="color: #666; font-weight: 600;">No tenés vehículos registrados aún.</p>
            </div>`;
        return;
    }

    list.innerHTML = vehicles.map(v => `
        <div class="vehicle-card">
            <div class="vehicle-card-bg"></div>
            <div class="vehicle-card-main">
                <div class="vehicle-data-group">
                    <div class="plate-badge-modern">${v.patente}</div>
                    <div class="vehicle-info-block">
                        <div class="vehicle-brand">${v.marca_modelo}</div>
                    </div>
                </div>
                <button class="delete-btn-modern" title="Eliminar vehículo" onclick="deleteVehicle('${v.patente}')">
                    <i class="fas fa-xmark"></i>
                </button>
            </div>
        </div>
    `).join('');

    // Actualizar selectores en formularios de reserva
    const selects = document.querySelectorAll('.res-vehicle');
    selects.forEach(select => {
        const currentVal = select.value;
        select.innerHTML = '<option value="">Seleccioná tu vehículo...</option>' + 
            vehicles.map(v => `<option value="${v.patente}">${v.patente} - ${v.marca_modelo}</option>`).join('');
        if (currentVal) select.value = currentVal;
    });
}

export async function addVehicle(e, isQuickAdd = false) {
    e.preventDefault();
    const form = e.target;
    const btn = form.querySelector('button[type="submit"]');
    const originalContent = btn.innerHTML;
    
    const patente = form.querySelector('[name="patente"]').value.trim().toUpperCase();
    const marca_modelo = form.querySelector('[name="marca_modelo"]').value.trim();

    if (!patente || !marca_modelo) {
        showToast('Completá todos los campos');
        return;
    }

    const resumenHtml = `
        <div style="text-align: left; background: rgba(255,255,255,0.03); padding: 20px; border-radius: 15px; border: 1px solid rgba(197,160,89,0.2); margin-top: 10px;">
            <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-id-card" style="color: var(--dorado);"></i>
                <span>Patente: <b style="color: #fff;">${patente}</b></span>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-car-side" style="color: var(--dorado);"></i>
                <span>Marca/Modelo: <b style="color: #fff;">${marca_modelo}</b></span>
            </div>
        </div>
    `;

    const confirmed = await showConfirm('CONFIRMAR NUEVO VEHÍCULO', resumenHtml);
    if (!confirmed) return;

    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
    btn.disabled = true;

    const res = await api.post(`/user/vehicles?patente=${encodeURIComponent(patente)}&marca_modelo=${encodeURIComponent(marca_modelo)}`);
    if (res.ok) {
        showToast('Vehículo registrado con éxito');
        form.reset();
        
        if (isQuickAdd) {
            if (typeof toggleReservaForm === 'function') {
                const container = document.getElementById('reserva-form-container');
                if (container) container.classList.remove('open');
                await toggleReservaForm();
            }
        } else {
            if (window.toggleNuevoVinculo) window.toggleNuevoVinculo();
        }
        
        await loadVehicles();
    } else {
        showToast(res.error || 'Error al registrar vehículo');
    }
    
    btn.innerHTML = originalContent;
    btn.disabled = false;
}

export async function deleteVehicle(patente) {
    const confirmed = await showConfirm(
        'ELIMINAR VEHÍCULO',
        `¿Estás seguro de que querés eliminar el vehículo con patente ${patente}? Esta acción no se puede deshacer.`
    );
    if (!confirmed) return;

    const res = await api.delete(`/user/vehicles/${encodeURIComponent(patente)}`);
    if (res.ok) {
        showToast('Vehículo eliminado');
        await loadVehicles();
        if (window.refreshReservationFormState) window.refreshReservationFormState();
    } else {
        showToast(res.error || 'Error al eliminar');
    }
}
