import api from './api.js';
import { showToast, showConfirm, toTitle } from './utils.js';

const CAMERA_DEFAULT_PORT = '8080';
const CAMERA_DEFAULT_PATH = '/video';
const CAMERA_BARE_IP_RE = /^(\d{1,3}(?:\.\d{1,3}){3})(?::(\d+))?$/;
const CAMERA_FULL_URL_RE = /^https?:\/\/([^/]+?)(?::(\d+))?\/video\/?$/;

export function buildCameraSource(raw) {
    const value = (raw || '').trim();
    if (!value) return value;
    const match = value.match(CAMERA_BARE_IP_RE);
    if (match) {
        const port = match[2] || CAMERA_DEFAULT_PORT;
        return `http://${match[1]}:${port}${CAMERA_DEFAULT_PATH}`;
    }
    return value;
}

export function cameraSourceToInput(source) {
    const value = (source || '').trim();
    if (!value) return value;
    const match = value.match(CAMERA_FULL_URL_RE);
    if (match) {
        return match[2] && match[2] !== CAMERA_DEFAULT_PORT ? `${match[1]}:${match[2]}` : match[1];
    }
    return value;
}

export async function loadCameraSettings() {
    const listEl = document.getElementById('camera-settings-list');
    if (!listEl) return;
    listEl.innerHTML = `<div class="text-center py-20 text-muted" style="grid-column: 1 / -1; width: 100%;"><i class="fas fa-spinner fa-spin text-dorado mr-8"></i> Cargando dispositivos...</div>`;

    const res = await api.get('/system/cameras');
    if (res.ok) {
        renderCameraSettingsTable(res.data);
    } else {
        listEl.innerHTML = `<div class="text-center py-20 text-danger" style="grid-column: 1 / -1; width: 100%;">Error al cargar dispositivos: ${res.error || 'Desconocido'}</div>`;
    }
}

export function renderCameraSettingsTable(cameras) {
    const listEl = document.getElementById('camera-settings-list');
    if (!listEl) return;
    
    if (cameras.length === 0) {
        listEl.innerHTML = `
            <div class="text-center py-30 text-muted" style="grid-column: 1 / -1; width: 100%;">
                <i class="fas fa-video-slash mb-10" style="font-size: 2.2rem; opacity: 0.3; display: block;"></i>
                <p class="text-xs uppercase fw-800">No hay cámaras registradas</p>
            </div>`;
        return;
    }
    
    const typeLabels = {
        'PATENTE_INGRESO': 'LECTURA DE PATENTE - ENTRADA',
        'PATENTE_EGRESO': 'LECTURA DE PATENTE - SALIDA',
        'QR_INGRESO': 'LECTOR DE QR - ENTRADA',
        'QR_EGRESO': 'LECTOR DE QR - SALIDA',
        'PREDIO': 'VIGILANCIA',
        'ENTRADA': 'LECTURA DE PATENTE - ENTRADA',
        'SALIDA': 'LECTURA DE PATENTE - SALIDA',
        'PATENTE': 'LECTURA DE PATENTE - ENTRADA',
        'QR': 'LECTOR DE QR - ENTRADA'
    };

    listEl.innerHTML = cameras.map(cam => {
        const badgeClass = cam.is_running ? 'badge-success-light' : 'badge-danger-light';
        const badgeText = cam.is_running ? 'ONLINE' : 'OFFLINE';
        const tipoLabel = typeLabels[(cam.tipo || '').toUpperCase()] || cam.tipo;
        return `
            <div class="camera-card-premium glass-premium">
                <div class="flex-col items-center text-center gap-10 mb-15">
                    <div class="flex-row items-center justify-center gap-10">
                        <div class="header-icon-box sm">
                            <i class="fas fa-video text-dorado"></i>
                        </div>
                        <h4 class="text-white text-bold m-0 text-center" style="font-size: 1rem; letter-spacing: 0.5px;">${toTitle(cam.nombre)}</h4>
                    </div>
                    <span class="badge-status ${badgeClass}" id="settings-cam-badge-${cam.id}">
                        <i class="fas ${cam.is_running ? 'fa-check-circle' : 'fa-times-circle'} mr-5"></i> ${badgeText}
                    </span>
                </div>
                
                <div class="camera-card-info p-12 mb-15" style="background: rgba(0,0,0,0.25); border-radius: 12px; border: 1px solid rgba(255,255,255,0.04);">
                    <div class="flex-row justify-between items-center mb-10 flex-wrap gap-5">
                        <span class="text-xxs text-muted uppercase fw-800">FUNCIÓN</span>
                        <span class="badge-status badge-info-light" style="font-size: 0.68rem;">${tipoLabel}</span>
                    </div>
                    <div class="flex-row justify-between items-center flex-wrap gap-5">
                        <span class="text-xxs text-muted uppercase fw-800">IP</span>
                        <span class="text-xs font-mono text-white text-truncate" style="max-width: 220px;" title="${cam.source}">${cameraSourceToInput(cam.source)}</span>
                    </div>
                </div>

                <div class="flex-row justify-center gap-10 camera-card-actions">
                    <button class="btn-tab-sub btn-edit-cam" id="settings-cam-btn-edit-${cam.id}" style="padding: 6px 14px; font-size: 0.7rem;">
                        <i class="fas fa-pen-to-square mr-5"></i> EDITAR
                    </button>
                    <button class="btn-tab-sub danger" onclick="deleteCamera(${cam.id})" style="padding: 6px 14px; font-size: 0.7rem; border-color: rgba(244, 63, 94, 0.4); color: #f43f5e;">
                        <i class="fas fa-trash-alt mr-5"></i> ELIMINAR
                    </button>
                </div>
            </div>
        `;
    }).join('');

    cameras.forEach(cam => {
        const btnEdit = document.getElementById(`settings-cam-btn-edit-${cam.id}`);
        if (btnEdit) {
            btnEdit.addEventListener('click', () => showEditCameraModal(cam));
        }
    });
}

export async function showCreateCameraModal() {
    const modalTitle = document.getElementById('camera-modal-title');
    if (modalTitle) modalTitle.innerText = 'AGREGAR CÁMARA';

    const form = document.getElementById('form-camera-config');
    if (form) form.reset();

    const editIdInput = document.getElementById('edit-camera-id');
    if (editIdInput) editIdInput.value = '';

    const sucursalGroup = document.getElementById('camera-sucursal-group');
    const selectSucursal = document.getElementById('camera-sucursal');
    const rol = localStorage.getItem('rol');

    if (rol === 'admin') {
        if (sucursalGroup && selectSucursal) {
            sucursalGroup.style.display = 'block';
            selectSucursal.required = true;
            const res = await api.get('/admin/branches');
            if (res.ok) {
                selectSucursal.innerHTML = '<option value="">GLOBAL (Sin sucursal)</option>' + 
                    res.data.map(b => `<option value="${b.nombre}">${b.nombre}</option>`).join('');
            }
        }
    } else {
        if (sucursalGroup) sucursalGroup.style.display = 'none';
        if (selectSucursal) {
            selectSucursal.required = false;
            selectSucursal.value = localStorage.getItem('sucursal') || '';
        }
    }

    const checkActiva = document.getElementById('camera-activa');
    if (checkActiva) checkActiva.checked = true;

    if (window.openModal) window.openModal('modal-camera-config');
}

export async function showEditCameraModal(cam) {
    const modalTitle = document.getElementById('camera-modal-title');
    if (modalTitle) modalTitle.innerText = 'EDITAR CÁMARA';

    const editIdInput = document.getElementById('edit-camera-id');
    if (editIdInput) editIdInput.value = cam.id;

    const nombreInput = document.getElementById('camera-nombre');
    if (nombreInput) nombreInput.value = toTitle(cam.nombre);

    const tipoSelect = document.getElementById('camera-tipo');
    if (tipoSelect) tipoSelect.value = cam.tipo;

    const sourceInput = document.getElementById('camera-source');
    if (sourceInput) sourceInput.value = cameraSourceToInput(cam.source);

    const sucursalGroup = document.getElementById('camera-sucursal-group');
    const selectSucursal = document.getElementById('camera-sucursal');
    const rol = localStorage.getItem('rol');

    if (rol === 'admin') {
        if (sucursalGroup && selectSucursal) {
            sucursalGroup.style.display = 'block';
            selectSucursal.required = true;
            const res = await api.get('/admin/branches');
            if (res.ok) {
                selectSucursal.innerHTML = '<option value="">GLOBAL (Sin sucursal)</option>' + 
                    res.data.map(b => `<option value="${b.nombre}">${b.nombre}</option>`).join('');
                selectSucursal.value = cam.sucursal || '';
            }
        }
    } else {
        if (sucursalGroup) sucursalGroup.style.display = 'none';
        if (selectSucursal) {
            selectSucursal.required = false;
            selectSucursal.value = cam.sucursal || '';
        }
    }

    const checkActiva = document.getElementById('camera-activa');
    if (checkActiva) checkActiva.checked = cam.activa;

    if (window.openModal) window.openModal('modal-camera-config');
}

export async function handleSaveCameraConfig(event) {
    event.preventDefault();
    const btnSubmit = document.getElementById('btn-camera-submit');
    if (btnSubmit) btnSubmit.disabled = true;

    const editId = document.getElementById('edit-camera-id').value;
    const nombre = toTitle(document.getElementById('camera-nombre').value);
    const tipo = document.getElementById('camera-tipo').value;
    const source = buildCameraSource(document.getElementById('camera-source').value);
    const sucursal = document.getElementById('camera-sucursal').value || null;
    const activa = document.getElementById('camera-activa').checked;

    const payload = { nombre, tipo, source, sucursal, activa };
    
    let res;
    if (editId) {
        res = await api.put(`/system/cameras/${editId}`, payload);
    } else {
        res = await api.post('/system/cameras', payload);
    }

    if (res.ok) {
        showToast(editId ? 'Cámara actualizada' : 'Cámara registrada', 'success');
        if (window.closeModal) window.closeModal('modal-camera-config');
        loadCameraSettings();
    } else {
        showToast(res.error || 'Error al guardar la cámara', 'error');
    }

    if (btnSubmit) btnSubmit.disabled = false;
}

export async function deleteCamera(id) {
    const confirmed = await showConfirm('ELIMINAR CÁMARA', '¿Estás seguro de que deseas eliminar esta cámara? Se detendrá cualquier proceso de lectura activo.');
    if (!confirmed) return;

    const res = await api.delete(`/system/cameras/${id}`);
    if (res.ok) {
        showToast('Cámara eliminada', 'success');
        loadCameraSettings();
    } else {
        showToast(res.error || 'Error al eliminar la cámara', 'error');
    }
}

export async function toggleDynamicCameraService(id, action) {
    const badge = document.getElementById(`settings-cam-badge-${id}`);
    if (badge) {
        badge.innerHTML = `<i class="fas fa-spinner fa-spin mr-5"></i> ${action === 'start' ? 'INICIANDO...' : 'DETENIENDO...'}`;
    }

    const res = await api.post(`/system/cameras/${id}/control/${action}`);
    if (res.ok) {
        showToast(res.data.message, 'success');
        loadCameraSettings();
    } else {
        showToast(res.error || 'Error al cambiar estado de la cámara', 'error');
        loadCameraSettings();
    }
}
