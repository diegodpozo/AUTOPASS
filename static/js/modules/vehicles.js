import api from './api.js';
import { showToast, showConfirm, formatPlate, validatePlate, detectVehicleType, formatNum } from './utils.js';
import { toggleReservaForm } from './reservas.js'; 

/**
 * VEHICLES MODULO
 * GESTION DE LA FLOTA VEHICULAR DEL USUARIO.
 */

export async function loadVehicles() {
    const list = document.getElementById('vehicle-list');
    const statVehicles = document.getElementById('stat-vehicles');
    
    if (!list) return;

    // INICIALIZAR AUTO-DETECCION SI NO SE HA HECHO
    initAutoDetection();

    const res = await api.get('/user/vehicles');
    if (!res.ok) {
        list.innerHTML = '<p style="color: var(--danger);">Error al cargar flota.</p>';
        return;
    }
    
    const vehicles = res.data;
    if (statVehicles) statVehicles.innerText = formatNum(vehicles.length);
    
    if (vehicles.length === 0) {
        list.innerHTML = `
            <div class="empty-state-card" style="display: flex; flex-direction: column; align-items: center; grid-column: 1 / -1; text-align: center; padding: 40px 0;">
                <div style="display: flex; align-items: center; justify-content: center; gap: 25px; margin-bottom: 25px;">
                    <i class="fas fa-motorcycle" style="font-size: 1.5rem; color: #444;"></i>
                    <i class="fas fa-car-rear" style="font-size: 2.5rem; color: #444;"></i>
                    <i class="fas fa-truck-pickup" style="font-size: 1.5rem; color: #444;"></i>
                </div>
                <h4 style="color: #fff; font-family: 'Montserrat'; font-weight: 800; letter-spacing: 1px; margin-bottom: 10px;">¡UPS! NO TENÉS VEHÍCULOS</h4>
                <p style="color: #666; font-size: 0.95rem; max-width: 300px; line-height: 1.5;">Agregá tu primer vehículo para empezar a operar en la red AutoPass.</p>
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
            <div class="vehicle-actions-overlay">
                <button class="fav-btn-modern ${v.is_favorite ? 'active' : ''}" title="${v.is_favorite ? 'Quitar favorito' : 'Marcar como favorito'}" onclick="setFavoriteVehicle('${v.patente}')">
                    <i class="fas fa-star"></i>
                </button>
                <button class="delete-btn-modern" title="Eliminar vehículo" onclick="deleteVehicle('${v.patente}')">
                    <i class="fas fa-xmark"></i>
                </button>
            </div>
        </div>
    `).join('');

    // ACTUALIZAR SELECTORES EN FORMULARIOS DE RESERVA
    const selects = document.querySelectorAll('.res-vehicle');
    selects.forEach(select => {
        const currentVal = select.value;
        select.innerHTML = '<option value="">Seleccioná tu vehículo...</option>' + 
            vehicles.map(v => `<option value="${v.patente}">${formatPlate(v.patente)} - ${v.marca_modelo}</option>`).join('');
        if (currentVal) select.value = currentVal;
    });
    // AUTO-SELECT SI TIENE UN SOLO VEHICULO O UNO MARCADO COMO FAVORITO
    if (vehicles.length === 1) {
        selects.forEach(select => select.value = vehicles[0].patente);
    } else {
        const fav = vehicles.find(v => v.is_favorite);
        if (fav) {
            selects.forEach(select => select.value = fav.patente);
        }
    }
}

export async function toggleVehicleForm() {
    const container = document.getElementById('vehicle-form-container');
    const trigger = document.getElementById('vehicle-form-trigger');
    if (!container || !trigger) return;

    const isHidden = container.style.display === 'none' || container.style.display === '';
    
    if (isHidden) {
        // MOSTRAR FORM, OCULTAR BOTON
        trigger.style.display = 'none';
        container.style.display = 'block';
        container.classList.add('open');
    } else {
        // OCULTAR FORM, MOSTRAR BOTON
        container.style.display = 'none';
        container.classList.remove('open');
        trigger.style.display = 'flex';
        const form = document.getElementById('add-vehicle-form');
        if (form) form.reset();
        updateVehicleTypeIcon('', '', form);
    }
}

export function updateVehicleTypeIcon(typeValue, prefix = '', form = null) {
    const icon = document.getElementById(`${prefix}vehicle-type-icon`);
    if (!icon) return;

    // SI NO SE PASA EL FORM, INTENTAMOS ENCONTRARLO POR EL ICONO
    const targetForm = form || icon.closest('form');
    if (!targetForm) return;

    const plateInput = targetForm.querySelector('[name="patente"]');
    if (!plateInput) return;

    if (typeValue === 'Auto') {
        icon.className = 'fas fa-car-side';
        icon.style.display = 'block';
        if (plateInput) plateInput.style.paddingLeft = (prefix === 'quick-') ? '35px' : '45px';
    } else if (typeValue === 'Moto') {
        icon.className = 'fas fa-motorcycle';
        icon.style.display = 'block';
        if (plateInput) plateInput.style.paddingLeft = (prefix === 'quick-') ? '35px' : '45px';
    } else if (typeValue === 'Camioneta') {
        icon.className = 'fas fa-truck-pickup';
        icon.style.display = 'block';
        if (plateInput) plateInput.style.paddingLeft = (prefix === 'quick-') ? '35px' : '45px';
    } else {
        icon.style.display = 'none';
        plateInput.style.paddingLeft = (prefix === 'quick-') ? '10px' : '15px';
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

    // VALIDAR FORMATO DE PATENTE
    if (!validatePlate(patente, tipo)) {
        showToast('Formato de patente no válido.');
        return;
    }

    const resumenHtml = `
        <div style="text-align: left; background: rgba(255,255,255,0.03); padding: 20px; border-radius: 15px; border: 1px solid rgba(197, 160, 89, 0.2); margin-top: 10px;">
            <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-id-card" style="color: var(--dorado);"></i>
                <span>Patente: <b style="color: #fff;">${formatPlate(patente)}</b></span>
            </div>
            <div style="margin-bottom: 12px; display: flex; align-items: center; gap: 10px;">
                <i class="fas ${tipo === 'Moto' ? 'fa-motorcycle' : 'fa-car-side'}" style="color: var(--dorado);"></i>
                <span>Tipo: <b style="color: #fff;">${tipo}</b></span>
            </div>
            <div style="display: flex; align-items: center; gap: 10px;">
                <i class="fas fa-tag" style="color: var(--dorado);"></i>
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

        // RESETEAR ICONO Y PADDING (TIPO AHORA ES HIDDEN)
        updateVehicleTypeIcon('', isQuickAdd ? 'quick-' : '', form);

        if (isQuickAdd) {
            // REFRESCAR ESTADO PARA QUE APAREZCA EL FORMULARIO DE RESERVA
            if (typeof window.refreshReservationFormState === 'function') {
                await window.refreshReservationFormState();
            }
        } else {
            // CERRAR EL FORMULARIO SI ESTABA ABIERTO (EN LA PESTANA DE MIS VEHICULOS)
            const container = document.getElementById('vehicle-form-container');
            if (container && container.classList.contains('open')) {
                if (typeof window.toggleVehicleForm === 'function') window.toggleVehicleForm();
            }
        }

        await loadVehicles();
    }
 else {
        showToast(res.error || 'Error al registrar vehículo');
    }

    btn.innerHTML = originalContent;
    btn.disabled = false;
}

export async function setFavoriteVehicle(patente) {
    const res = await api.post(`/user/vehicles/${encodeURIComponent(patente)}/favorite`);
    if (res.ok) {
        await loadVehicles();
        if (window.refreshReservationFormState) window.refreshReservationFormState();
        showToast(res.data.is_favorite ? 'Vehículo marcado como favorito' : 'Favorito removido');
    } else {
        showToast(res.error || 'Error al actualizar favorito');
    }
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

/**
 * INICIALIZA LA DETECCION AUTOMATICA DE TIPO DE VEHICULO EN LOS FORMULARIOS.
 */
let autoDetectionInitialized = false;
export function initAutoDetection() {
    if (autoDetectionInitialized) return;

    const attachListener = (formId, prefix = '') => {
        const form = document.getElementById(formId);
        if (!form) return;

        const plateInput = form.querySelector('[name="patente"]');
        const typeSelect = form.querySelector('[name="tipo"]');

        if (plateInput && typeSelect) {
            plateInput.addEventListener('input', (e) => {
                const detectedType = detectVehicleType(e.target.value);
                if (detectedType) {
                    typeSelect.value = detectedType;
                    updateVehicleTypeIcon(detectedType, prefix, form);
                }
            });
        }
    };

    attachListener('add-vehicle-form');
    attachListener('quick-add-vehicle-form', 'quick-');

    autoDetectionInitialized = true;
}
