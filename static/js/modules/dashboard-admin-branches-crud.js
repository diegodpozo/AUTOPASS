import api from './api.js';
import { showToast, showConfirm, formatNum } from './utils.js';

/**
 * MÓDULO SUCURSALES - CRUD Y GEOLOCALIZACIÓN (MAPA LEAFLET)
 * Gestión de la red de sucursales, alta/baja/modificación, logo upload y mapa interactivo.
 */

let allBranchesData = [];
let branchMap = null;
let branchMarker = null;

export function getAllBranchesData() {
    return allBranchesData;
}

export function setAllBranchesData(data) {
    allBranchesData = data;
}

export function initBranchMap() {
    const mapEl = document.getElementById('branch-map-picker');
    if (!mapEl || branchMap || !window.L) return;

    const initialCoords = [-34.5888, -58.3900];
    branchMap = window.L.map('branch-map-picker').setView(initialCoords, 13);

    const googleStreets = window.L.tileLayer('https://{s}.google.com/vt/lyrs=m&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '&copy; <a href="https://www.google.com/maps" target="_blank">Google Maps</a>'
    });

    const googleHybrid = window.L.tileLayer('https://{s}.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', {
        maxZoom: 20,
        subdomains: ['mt0', 'mt1', 'mt2', 'mt3'],
        attribution: '&copy; <a href="https://www.google.com/maps" target="_blank">Google Maps</a>'
    });

    const cartoDark = window.L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 20,
        subdomains: 'abcd',
        attribution: '&copy; <a href="https://carto.com/">CARTO</a>'
    });

    googleStreets.addTo(branchMap);

    const baseMaps = {
        "🗺️ Google Calles": googleStreets,
        "🌍 Google Híbrido": googleHybrid,
        "🌙 CartoDB Oscuro": cartoDark
    };
    window.L.control.layers(baseMaps, null, { position: 'topleft' }).addTo(branchMap);

    branchMap.on('click', function(e) {
        updateBranchMarker(e.latlng.lat, e.latlng.lng);
    });
}

function updateBranchMarker(lat, lng) {
    if (!branchMap || !window.L) return;

    if (branchMarker) {
        branchMarker.setLatLng([lat, lng]);
    } else {
        const goldIcon = window.L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color: #C5A059; width: 15px; height: 15px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #C5A059;"></div>`,
            iconSize: [15, 15],
            iconAnchor: [7, 7]
        });
        branchMarker = window.L.marker([lat, lng], { icon: goldIcon }).addTo(branchMap);
    }

    const elLat = document.getElementById('branch-latitude');
    const elLng = document.getElementById('branch-longitude');
    if (elLat) elLat.value = lat.toFixed(6);
    if (elLng) elLng.value = lng.toFixed(6);
}

export async function searchAddress() {
    const address = document.getElementById('branch-direccion')?.value;
    if (!address) return showToast('Ingresá una dirección para buscar');

    try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`;
        const res = await fetch(url);
        const data = await res.json();

        if (data && data.length > 0) {
            const lat = parseFloat(data[0].lat);
            const lng = parseFloat(data[0].lon);

            initBranchMap();
            updateBranchMarker(lat, lng);
            if (branchMap) branchMap.setView([lat, lng], 16);
            showToast('Ubicación encontrada', 'success');
        } else {
            showToast('No se encontró la dirección. Intentá ser más específico.', 'error');
        }
    } catch (err) {
        console.error('Error en geocoding:', err);
        showToast('Error al buscar la dirección', 'error');
    }
}

export async function populateBranchSelect(selectEl) {
    if (!selectEl) return;

    if (allBranchesData.length > 0) {
        _renderBranchOptions(selectEl, allBranchesData);
        return;
    }

    try {
        const res = await api.get('/admin/branches');
        if (res && res.ok) {
            const data = Array.isArray(res.data) ? res.data : (res.data?.data || []);
            if (data.length > 0) {
                allBranchesData = data;
                _renderBranchOptions(selectEl, data);
            } else {
                selectEl.innerHTML = '<option value="" style="background: #111;">-- Sin sucursales --</option>';
            }
        }
    } catch (e) {
        console.error('[populateBranchSelect] Error:', e);
    }
}

function _renderBranchOptions(selectEl, data) {
    selectEl.innerHTML = '';
    data.forEach(b => {
        const opt = document.createElement('option');
        opt.value = b.nombre;
        opt.textContent = b.nombre;
        selectEl.appendChild(opt);
    });
}

export function showCreateBranchModal() {
    const form = document.getElementById('form-add-branch');
    if (form) form.reset();
    
    document.getElementById('branch-id-edit').value = '';
    document.getElementById('branch-modal-title').innerText = 'NUEVA SUCURSAL';
    document.getElementById('branch-modal-icon').className = 'fas fa-building';
    
    const preview = document.querySelector('#branch-logo-preview img');
    if (preview) preview.src = '/static/images/logo.png';
    
    if (window.openModal) window.openModal('modal-add-branch');

    setTimeout(() => {
        initBranchMap();
        if (branchMarker && branchMap) {
            branchMap.removeLayer(branchMarker);
            branchMarker = null;
        }
        if (branchMap) branchMap.setView([-34.6508, -58.6228], 13);
    }, 300);
}

export async function loadBranches() {
    try {
        const res = await api.get('/admin/branches');
        const tbody = document.getElementById('branches-table-body');
        if (!tbody) return;

        if (res && res.ok) {
            allBranchesData = res.data || [];
            if (allBranchesData.length === 0) {
                tbody.innerHTML = '<tr><td colspan="7" class="text-center py-40 text-muted">No hay sucursales registradas en la red.</td></tr>';
                return;
            }

            const rol = localStorage.getItem('rol');
            const isAdmin = rol === 'admin';

            tbody.innerHTML = allBranchesData.map(b => {
                const plazasCell = isAdmin ? 
                    `<td class="text-center"><span class="text-muted text-xs">---</span></td>` :
                    `<td data-label="Plazas (A/M)" class="text-center">
                        <div class="flex-col items-center">
                            <div class="flex-row gap-5 items-center">
                                <span class="text-xs ${b.ocupacion_autos_total >= b.capacidad_autos_total ? 'text-danger' : 'text-success'}">
                                    <i class="fas fa-car"></i> ${formatNum(b.ocupacion_autos_total)}/${formatNum(b.capacidad_autos_total)}
                                </span>
                                <span class="text-xs ${b.ocupacion_motos_total >= b.capacidad_motos_total ? 'text-danger' : 'text-success'}">
                                    <i class="fas fa-motorcycle"></i> ${formatNum(b.ocupacion_motos_total)}/${formatNum(b.capacidad_motos_total)}
                                </span>
                            </div>
                            <div class="progress-bar-mini" style="width: 80px; height: 3px; background: rgba(255,255,255,0.05); margin-top: 5px; border-radius: 2px; overflow: hidden;">
                                <div style="width: ${Math.min(100, (b.ocupacion_autos_total / (b.capacidad_autos_total || 1)) * 100)}%; height: 100%; background: var(--dorado);"></div>
                            </div>
                        </div>
                    </td>`;

                const levelsAction = isAdmin ? '' : `
                    <button class="btn-icon-premium sm" onclick="showBranchFloors(${b.id})" title="Ver Niveles / Pisos">
                        <i class="fas fa-layer-group"></i>
                    </button>`;

                return `
                <tr class="row-premium">
                    <td data-label="Sucursal">
                        <div class="flex-row items-center gap-10">
                            <div class="branch-logo-sm">
                                <img src="${b.logo_url || '/static/images/logo.png'}" alt="Logo" onerror="this.src='/static/images/logo.png'">
                            </div>
                            <div class="flex-col">
                                <b class="text-white text-small">${b.nombre}</b>
                            </div>
                        </div>
                    </td>
                    <td data-label="Dirección"><span class="text-xs text-light">${b.direccion}</span></td>
                    <td data-label="Administrador" class="text-center">
                        <div class="flex-row items-center justify-center gap-5">
                            <i class="fas fa-user-tie text-xs text-muted"></i>
                            <span class="text-xs font-bold text-dorado">${(b.admin_name || 'Sin asignar').toUpperCase()}</span>
                        </div>
                    </td>
                    ${plazasCell}
                    <td data-label="Teléfono" class="text-center hidden-mobile"><span class="text-xs font-mono">${b.telefono}</span></td>
                    <td data-label="Horario" class="text-center">
                        <div class="flex-row items-center justify-center gap-5">
                            <i class="fas fa-clock text-xs text-muted"></i>
                            <span class="text-xs">${b.is_24h ? '24hs' : b.horario}</span>
                        </div>
                    </td>
                    <td data-label="Estado" class="text-center">
                        <label class="switch-premium" title="${b.activa ? 'Sede Activa' : 'Sede Suspendida'}">
                            <input type="checkbox" ${b.activa ? 'checked' : ''} onchange="toggleBranch(${b.id})">
                            <span class="slider-premium"></span>
                        </label>
                    </td>
                    <td data-label="Acciones">
                        <div class="flex-row gap-8 justify-center actions-reveal">
                            ${levelsAction}
                            <button class="btn-icon-premium sm" onclick="editBranch(${b.id})" title="Editar Configuración">
                                <i class="fas fa-pen-to-square"></i>
                            </button>
                            <button class="btn-icon-premium sm danger" onclick="deleteBranch(${b.id})" title="Eliminar Sucursal">
                                <i class="fas fa-xmark"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;}).join('');
        } else {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center py-40 text-danger">Error al cargar sucursales: ${res?.error || 'Error desconocido'}</td></tr>`;
        }
    } catch (err) {
        console.error('Error al cargar sucursales:', err);
    }
}

export function editBranch(id) {
    const b = allBranchesData.find(x => x.id === id);
    if (!b) return;

    document.getElementById('branch-id-edit').value = b.id;
    document.getElementById('branch-nombre').value = b.nombre;
    document.getElementById('branch-direccion').value = b.direccion;
    document.getElementById('branch-telefono').value = b.telefono;
    
    const lat = b.latitude || -34.6508;
    const lng = b.longitude || -58.6228;
    document.getElementById('branch-latitude').value = lat;
    document.getElementById('branch-longitude').value = lng;

    const preview = document.querySelector('#branch-logo-preview img');
    const hasLogo = b.logo_url && b.logo_url !== '/static/images/logo.png';
    if (preview) {
        preview.src = b.logo_url || '/static/images/logo.png';
        preview.style.opacity = "1";
    }
    document.getElementById('branch-logo-file').value = '';
    const btnClear = document.getElementById('btn-clear-logo');
    if (btnClear) btnClear.style.display = hasLogo ? 'block' : 'none';

    document.getElementById('branch-is-24h').checked = b.is_24h;
    const horarioEl = document.getElementById('branch-horario');
    if (horarioEl) {
        horarioEl.value = b.is_24h ? '' : b.horario;
        horarioEl.disabled = b.is_24h;
    }

    document.getElementById('branch-modal-title').innerText = 'EDITAR SUCURSAL';
    document.getElementById('branch-modal-icon').className = 'fas fa-pen-to-square';
    
    if (window.openModal) window.openModal('modal-add-branch');

    setTimeout(() => {
        initBranchMap();
        updateBranchMarker(lat, lng);
        if (branchMap) branchMap.setView([lat, lng], 15);
    }, 300);
}

export async function toggleBranch(id) {
    const res = await api.post(`/admin/branches/${id}/toggle`);
    if (res && res.ok) {
        showToast(`Sucursal ${res.data.activa ? 'Activada' : 'Suspendida'}`, 'success');
    } else {
        showToast(res?.error || 'Error al cambiar estado', 'error');
        loadBranches();
    }
}

export function toggleBranchHorario(checkbox) {
    const horarioInput = document.getElementById('branch-horario');
    if (!horarioInput) return;
    horarioInput.disabled = checkbox.checked;
    if (checkbox.checked) {
        horarioInput.value = '';
        horarioInput.style.opacity = '0.5';
    } else {
        horarioInput.style.opacity = '1';
    }
}

export function previewBranchLogo(input) {
    const preview = document.querySelector('#branch-logo-preview img');
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        reader.onload = function(e) {
            if (preview) {
                preview.src = e.target.result;
                preview.style.opacity = "1";
            }
        }
        reader.readAsDataURL(input.files[0]);
    }
    const btnClear = document.getElementById('btn-clear-logo');
    if (btnClear) btnClear.style.display = 'block';
}

export function clearBranchLogo() {
    const preview = document.querySelector('#branch-logo-preview img');
    if (preview) preview.src = '/static/images/logo.png';
    const logoInput = document.getElementById('branch-logo-file');
    if (logoInput) logoInput.value = '';
    const btnClear = document.getElementById('btn-clear-logo');
    if (btnClear) btnClear.style.display = 'none';
    const logoClear = document.getElementById('branch-logo-clear');
    if (logoClear) logoClear.value = 'true';
}

export async function handleCreateBranch(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const editId = document.getElementById('branch-id-edit').value;
    
    const formData = new FormData();
    formData.append('nombre', document.getElementById('branch-nombre').value);
    formData.append('direccion', document.getElementById('branch-direccion').value);
    formData.append('telefono', document.getElementById('branch-telefono').value);
    formData.append('horario', document.getElementById('branch-horario')?.value || '---');
    formData.append('is_24h', document.getElementById('branch-is-24h').checked);
    
    const lat = document.getElementById('branch-latitude').value;
    const lng = document.getElementById('branch-longitude').value;
    if (lat) formData.append('latitude', lat);
    if (lng) formData.append('longitude', lng);
    
    const fileInput = document.getElementById('branch-logo-file');
    if (fileInput && fileInput.files[0]) {
        formData.append('logo_file', fileInput.files[0]);
    }

    const logoClear = document.getElementById('branch-logo-clear');
    if (logoClear && logoClear.value === 'true') {
        formData.append('logo_clear', 'true');
    }

    btn.disabled = true;
    const url = editId ? `/admin/branches/${editId}` : '/admin/branches';
    const method = editId ? 'patch' : 'post';
    
    const res = await api[method](url, formData);
    
    if (res && res.ok) {
        showToast(editId ? 'Sucursal actualizada.' : 'Sucursal creada exitosamente.', 'success');
        if (window.closeModal) window.closeModal('modal-add-branch');
        event.target.reset();
        const preview = document.querySelector('#branch-logo-preview img');
        if (preview) preview.src = '/static/images/logo.png';
        document.getElementById('branch-id-edit').value = '';
        if (logoClear) logoClear.value = 'false';
        const btnClear = document.getElementById('btn-clear-logo');
        if (btnClear) btnClear.style.display = 'none';
        loadBranches();
    } else {
        showToast(`Error: ${res?.error || 'Desconocido'}`, 'error');
    }
    btn.disabled = false;
}

export async function deleteBranch(id) {
    if (!await showConfirm('Eliminar Sucursal', '¿Estás seguro de eliminar esta sucursal? Esto no afectará los registros históricos pero impedirá nuevas operaciones en ella.')) return;
    
    const res = await api.delete(`/admin/branches/${id}`);
    if (res && res.ok) {
        showToast('Sucursal eliminada.', 'success');
        loadBranches();
    } else {
        showToast(res?.error || 'Error al eliminar sucursal', 'error');
    }
}
