import api from './api.js';
import { showToast, showConfirm, formatPlate, validatePlate } from './utils.js';
import { toggleReservaForm } from './reservas.js'; 

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
                    <div class="plate-badge-modern">${formatPlate(v.patente)}</div>
                    <div class="vehicle-info-block">
                        <div class="vehicle-brand">${v.marca_modelo}</div>
                    </div>
                </div>
            </div>
            <button class="delete-btn-modern" title="Eliminar vehículo" onclick="deleteVehicle('${v.patente}')">
                <i class="fas fa-xmark"></i>
            </button>
        </div>
    `).join('');

    // Actualizar selectores en formularios de reserva
    const selects = document.querySelectorAll('.res-vehicle');
    selects.forEach(select => {
        const currentVal = select.value;
        select.innerHTML = '<option value="">Seleccioná tu vehículo...</option>' + 
            vehicles.map(v => `<option value="${v.patente}">${formatPlate(v.patente)} - ${v.marca_modelo}</option>`).join('');
        if (currentVal) select.value = currentVal;
    });
}

export async function toggleVehicleForm() {
    const container = document.getElementById('vehicle-form-container');
    const arrow = document.getElementById('vehicle-form-arrow');
    const trigger = document.getElementById('vehicle-form-trigger');
    if (!container) return;

    const isOpen = container.classList.toggle('open');
    if (arrow) arrow.style.transform = isOpen ? 'rotate(180deg)' : 'rotate(0deg)';
    if (trigger) trigger.classList.toggle('active');
}

export function updateVehicleTypeIcon(select, prefix = '') {
    const icon = document.getElementById(`${prefix}vehicle-type-icon`);
    if (!icon) return;

    if (select.value === 'Auto') {
        icon.className = 'fas fa-car-side';
        icon.style.display = 'block';
        select.style.paddingLeft = '45px';
    } else if (select.value === 'Moto') {
        icon.className = 'fas fa-motorcycle';
        icon.style.display = 'block';
        select.style.paddingLeft = '45px';
    } else {
        icon.style.display = 'none';
        select.style.paddingLeft = '15px';
    }
}

export async function addVehicle(e, isQuickAdd = false) {
    e.preventDefault();
    const form = e.target;
    const btn = form.querySelector('button[type="submit"]');
    const originalContent = btn.innerHTML;

    const patente = form.querySelector('[name="patente"]').value.trim().toUpperCase();
    const marca_modelo = form.querySelector('[name="marca_modelo"]').value.trim();
    const tipo = form.querySelector('[name="tipo"]')?.value || "Auto";

    if (!patente || !marca_modelo || !tipo) {
        showToast('Completá todos los campos');
        return;
    }

    // Validar formato de patente
    if (!validatePlate(patente, tipo)) {
        showToast('Formato de patente no válido para el tipo de vehículo seleccionado.');
        return;
    }

    const resumenHtml = `
        <div style="text-align: left; background: rgba(255,255,255,0.03); padding: 20px; border-radius: 15px; border: 1px solid rgba(197, 160, 89, 0.2); margin-top: 10px;">
            <p style="margin-bottom: 15px; color: #fff;">¿Estás seguro que los datos son correctos?</p>
            <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-id-card" style="color: var(--dorado);"></i>
                <span>Patente: <b style="color: #fff;">${formatPlate(patente)}</b></span>
            </div>
            <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">
                <i class="fas ${tipo === 'Moto' ? 'fa-motorcycle' : 'fa-car-side'}" style="color: var(--dorado);"></i>
                <span>Tipo: <b style="color: #fff;">${tipo}</b></span>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-car-rear" style="color: var(--dorado);"></i>
                <span>Marca/Modelo: <b style="color: #fff;">${marca_modelo}</b></span>
            </div>
        </div>
    `;

    const confirmed = await showConfirm('CONFIRMAR NUEVO VEHÍCULO', resumenHtml);
    if (!confirmed) return;

    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i>';
    btn.disabled = true;

    const res = await api.post(`/user/vehicles?patente=${encodeURIComponent(patente)}&marca_modelo=${encodeURIComponent(marca_modelo)}&tipo=${encodeURIComponent(tipo)}`);
    if (res.ok) {
        showToast('Vehículo registrado con éxito');
        form.reset();

        // Resetear icono y padding del selector
        const typeSelect = document.getElementById('vehicle-type-select');
        if (typeSelect) updateVehicleTypeIcon(typeSelect);

        if (isQuickAdd) {
            if (window.hideQuickAddVehicle) window.hideQuickAddVehicle();
            if (typeof toggleReservaForm === 'function') {
                const container = document.getElementById('reserva-form-container');
                if (container) container.classList.remove('open');
                await toggleReservaForm();
            }
        } else {
            // Cerrar el formulario si estaba abierto
            const container = document.getElementById('vehicle-form-container');
            if (container && container.classList.contains('open')) {
                toggleVehicleForm();
            }
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
        `¿Estás seguro de que querés eliminar el vehículo con patente ${formatPlate(patente)}? Esta acción no se puede deshacer.`
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
