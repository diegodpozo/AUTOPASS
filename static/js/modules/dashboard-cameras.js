import api from './api.js';
import { showToast, showConfirm, toTitle } from './utils.js';
import { enableDragSort } from './drag-sort.js';
import { enableActionMenu } from './action-menu.js';

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
    
    listEl.innerHTML = cameras.map(cam => {
        const badgeClass = cam.is_running ? 'badge-success-light' : 'badge-danger-light';
        const badgeText = cam.is_running ? 'ONLINE' : 'OFFLINE';
        return `
            <div class="camera-card-premium glass-premium" draggable="true" data-camera-id="${cam.id}">
                <div class="card-action-menu-wrapper">
                    <button class="card-action-trigger" data-camera-id="${cam.id}" aria-haspopup="true" aria-expanded="false" aria-label="Acciones de la cámara" title="Acciones">
                        <i class="fas fa-ellipsis-vertical"></i>
                    </button>
                    <div class="card-action-menu" role="menu">
                        <button class="card-action-menu__item" role="menuitem" data-action="edit">
                            <i class="fas fa-pen-to-square"></i> Editar
                        </button>
                        <button class="card-action-menu__item danger" role="menuitem" data-action="delete">
                            <i class="fas fa-trash-alt"></i> Eliminar
                        </button>
                    </div>
                </div>
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
                    <div class="flex-row items-center justify-center">
                        <span class="text-xs font-mono text-white" title="${cam.source}">${cameraSourceToInput(cam.source)}</span>
                    </div>
                </div>

            </div>
        `;
    }).join('');

    enableActionMenu(listEl, {
        triggerSelector: '.card-action-trigger',
        onSelect: (action, itemEl, triggerEl) => {
            const id = parseInt((triggerEl || itemEl)?.dataset.cameraId, 10);
            const cam = cameras.find(c => c.id === id);
            if (action === 'edit' && cam) showEditCameraModal(cam);
            else if (action === 'delete' && Number.isInteger(id)) deleteCamera(id);
        }
    });

    enableDragSort(listEl, {
        itemSelector: '.camera-card-premium',
        onReorder: saveCameraOrder
    });
}

export async function saveCameraOrder(items) {
    const ids = items
        .map(el => parseInt(el.dataset.cameraId, 10))
        .filter(id => Number.isInteger(id));
    if (ids.length === 0) return;

    const res = await api.put('/system/cameras/order', { ids });
    if (!res.ok) {
        showToast(res.error || 'No se pudo guardar el orden', 'error');
        loadCameraSettings();
    }
}

export async function showCreateCameraModal() {
    const modalTitle = document.getElementById('camera-modal-title');
    if (modalTitle) modalTitle.innerText = 'AGREGAR CÁMARA';

    const btnSubmit = document.getElementById('btn-camera-submit');
    if (btnSubmit) btnSubmit.innerText = 'GUARDAR';

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

    const btnSubmit = document.getElementById('btn-camera-submit');
    if (btnSubmit) btnSubmit.innerText = 'ACTUALIZAR';

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
