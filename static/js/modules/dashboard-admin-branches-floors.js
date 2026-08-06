import api from './api.js';
import { showToast, showConfirm, formatNum } from './utils.js';
import { getAllBranchesData } from './dashboard-admin-branches-crud.js';

/**
 * MÓDULO SUCURSALES - NIVELES / PISOS Y ARQUITECTURA
 * Gestión de la estructura vertical de las sedes (Pisos, capacidades por piso y Planta Baja).
 */

export function showBranchFloors(id) {
    const allBranchesData = getAllBranchesData();
    const b = allBranchesData.find(x => x.id === id);
    if (!b) return;

    document.getElementById('branch-floors-title').innerText = `NIVELES: ${b.nombre.toUpperCase()}`;
    const tbody = document.getElementById('branch-floors-body');
    if (!tbody) return;

    const floorsSumAutos = (b.floors || []).reduce((acc, f) => acc + f.ocupacion_actual, 0);
    const floorsSumMotos = (b.floors || []).reduce((acc, f) => acc + f.ocupacion_motos, 0);
    const floorsSumCamionetas = (b.floors || []).reduce((acc, f) => acc + (f.ocupacion_camionetas || 0), 0);
    
    const pbOccAutos = Math.max(0, b.ocupacion_autos_total - floorsSumAutos);
    const pbOccMotos = Math.max(0, b.ocupacion_motos_total - floorsSumMotos);
    const pbOccCamionetas = Math.max(0, (b.ocupacion_camionetas_total || 0) - floorsSumCamionetas);
    
    const floorsCapAutos = (b.floors || []).reduce((acc, f) => acc + f.capacidad_total, 0);
    const floorsCapMotos = (b.floors || []).reduce((acc, f) => acc + f.capacidad_motos, 0);
    const floorsCapCamionetas = (b.floors || []).reduce((acc, f) => acc + (f.capacidad_camionetas || 0), 0);
    const pbCapAutos = b.capacidad_autos_total - floorsCapAutos;
    const pbCapMotos = b.capacidad_motos_total - floorsCapMotos;
    const pbCapCamionetas = (b.capacidad_camionetas_total || 0) - floorsCapCamionetas;

    let rows = `
        <tr class="row-premium" style="background: rgba(197,160,89,0.05);">
            <td>
                <div class="flex-col">
                    <b class="text-dorado">PLANTA BAJA (PB)</b>
                    <span class="text-xs text-muted">Acceso Principal</span>
                </div>
            </td>
            <td class="text-center">
                <span class="text-xs ${pbOccAutos >= pbCapAutos ? 'text-danger' : 'text-success'} font-bold">
                    ${pbOccAutos} / ${pbCapAutos}
                </span>
            </td>
            <td class="text-center">
                <span class="text-xs ${pbOccMotos >= pbCapMotos ? 'text-danger' : 'text-success'} font-bold">
                    ${pbOccMotos} / ${pbCapMotos}
                </span>
            </td>
            <td class="text-center">
                <span class="text-xs ${pbOccCamionetas >= pbCapCamionetas ? 'text-danger' : 'text-success'} font-bold">
                    ${pbOccCamionetas} / ${pbCapCamionetas}
                </span>
            </td>
        </tr>
    `;

    if (b.floors && b.floors.length > 0) {
        rows += b.floors.map(f => `
            <tr class="row-premium">
                <td><span class="text-white">${f.nombre}</span></td>
                <td class="text-center">
                    <span class="text-xs ${f.ocupacion_actual >= f.capacidad_total ? 'text-danger' : ''}">
                        ${formatNum(f.ocupacion_actual)} / ${formatNum(f.capacidad_total)}
                    </span>
                </td>
                <td class="text-center">
                    <span class="text-xs ${f.ocupacion_motos >= f.capacidad_motos ? 'text-danger' : ''}">
                        ${formatNum(f.ocupacion_motos)} / ${formatNum(f.capacidad_motos)}
                    </span>
                </td>
                <td class="text-center">
                    <span class="text-xs ${(f.ocupacion_camionetas || 0) >= (f.capacidad_camionetas || 5) ? 'text-danger' : ''}">
                        ${formatNum(f.ocupacion_camionetas || 0)} / ${formatNum(f.capacidad_camionetas || 5)}
                    </span>
                </td>
            </tr>
        `).join('');
    }

    tbody.innerHTML = rows;
    if (window.openModal) window.openModal('modal-branch-floors');
}

export async function loadFloors() {
    const container = document.getElementById('building-architecture-grid');
    if (!container) return;

    const rol = localStorage.getItem('rol');
    if (rol !== 'local_admin') return;

    const resBranches = await api.get('/admin/branches');
    const resSettings = await api.get('/admin/settings');
    
    if (!resBranches.ok) {
        container.innerHTML = `<div class="text-center p-50 text-danger fw-800">ERROR DE CONEXIÓN</div>`;
        return;
    }

    let mySucursal = resSettings.ok ? resSettings.data.sucursal_nombre : '';
    if (!mySucursal) {
        mySucursal = localStorage.getItem('sucursal') || '';
        mySucursal = mySucursal.replace('AUTOPASS ', '').trim();
    }

    const branch = resBranches.data.find(b => 
        b.nombre.trim().toLowerCase() === mySucursal.trim().toLowerCase() ||
        b.nombre.trim().toLowerCase().includes(mySucursal.trim().toLowerCase())
    );
    
    if (!branch) {
        container.innerHTML = `<div class="text-center p-50 text-muted fw-800 uppercase">SEDE "${mySucursal}" NO IDENTIFICADA</div>`;
        return;
    }

    const pbCapAutos = resSettings.ok ? (resSettings.data.capacidad_total || 20) : 20;
    const pbCapMotos = resSettings.ok ? (resSettings.data.capacidad_motos || 10) : 10;
    const pbCapCamionetas = resSettings.ok ? (resSettings.data.capacidad_camionetas ?? 5) : 5;
    
    let cardsHtml = `
        <div class="level-block pb" id="level-block-pb" style="grid-template-columns: 1fr auto;">
            <div class="level-main-content" style="justify-content: space-around; width: 100%;">
                <div class="level-stats-grid" style="gap: 40px; width: 100%; justify-content: space-around;">
                    <div class="stat-item items-center text-center">
                        <span class="text-sm text-white uppercase fw-900"><i class="fas fa-car mr-8 text-dorado" style="font-size: 1.2rem;"></i> Autos</span>
                        <div class="stat-val-box justify-center">
                            <input type="number" id="pb-cap-autos" class="stat-val-input" value="${pbCapAutos}" min="0" disabled style="width: 100px; font-size: 1.6rem; text-align: center;">
                        </div>
                    </div>
                    <div class="stat-item items-center text-center">
                        <span class="text-sm text-white uppercase fw-900"><i class="fas fa-motorcycle mr-8 text-dorado" style="font-size: 1.2rem;"></i> Motos</span>
                        <div class="stat-val-box justify-center">
                            <input type="number" id="pb-cap-motos" class="stat-val-input" value="${pbCapMotos}" min="0" disabled style="width: 100px; font-size: 1.6rem; text-align: center;">
                        </div>
                    </div>
                    <div class="stat-item items-center text-center">
                        <span class="text-sm text-white uppercase fw-900"><i class="fas fa-truck-pickup mr-8 text-dorado" style="font-size: 1.2rem;"></i> Camionetas</span>
                        <div class="stat-val-box justify-center">
                            <input type="number" id="pb-cap-camionetas" class="stat-val-input" value="${pbCapCamionetas}" min="0" disabled style="width: 100px; font-size: 1.6rem; text-align: center;">
                        </div>
                    </div>
                </div>
            </div>
            <div class="level-actions">
                <button class="btn-icon-premium sm btn-save-level" onclick="savePBCapacity()" style="display:none;" title="Guardar Cambios">
                    <i class="fas fa-floppy-disk"></i>
                </button>
                <button class="btn-icon-premium sm btn-edit-level" onclick="toggleLevelEdit('pb')" title="Editar Plazas">
                    <i class="fas fa-pen-to-square"></i>
                </button>
            </div>
        </div>
    `;

    if (branch.floors && branch.floors.length > 0) {
        const sortedFloors = [...branch.floors].sort((a, b) => a.id - b.id);
        
        cardsHtml += sortedFloors.map((f, index) => `
            <div class="level-block" id="level-block-${f.id}">
                <div class="level-indicator">
                    <i class="fas fa-layer-group level-icon-bg"></i>
                    <span class="level-code">L${index + 1}</span>
                    <span class="level-label">UPPER</span>
                </div>
                <div class="level-main-content">
                    <div class="level-identity">
                        <span class="level-title">${f.nombre.toUpperCase()}</span>
                        <span class="level-subtitle">Sector Elevado</span>
                    </div>
                    <div class="level-stats-grid">
                        <div class="stat-item">
                            <span class="text-xxs text-muted uppercase fw-700"><i class="fas fa-car mr-5"></i> Autos</span>
                            <div class="stat-val-box">
                                <input type="number" id="cap-autos-${f.id}" class="stat-val-input" value="${f.capacidad_total}" min="0" disabled>
                                <span class="stat-unit">u.</span>
                            </div>
                        </div>
                        <div class="stat-item">
                            <span class="text-xxs text-muted uppercase fw-700"><i class="fas fa-motorcycle mr-5"></i> Motos</span>
                            <div class="stat-val-box">
                                <input type="number" id="cap-motos-${f.id}" class="stat-val-input" value="${f.capacidad_motos}" min="0" disabled>
                                <span class="stat-unit">u.</span>
                            </div>
                        </div>
                        <div class="stat-item">
                            <span class="text-xxs text-muted uppercase fw-700"><i class="fas fa-truck-pickup mr-5"></i> Camionetas</span>
                            <div class="stat-val-box">
                                <input type="number" id="cap-camionetas-${f.id}" class="stat-val-input" value="${f.capacidad_camionetas ?? 5}" min="0" disabled>
                                <span class="stat-unit">u.</span>
                            </div>
                        </div>
                    </div>
                </div>
                <div class="level-actions">
                    <button class="btn-icon-premium sm btn-edit-level" onclick="toggleLevelEdit(${f.id})" title="Editar Plazas">
                        <i class="fas fa-pen-to-square"></i>
                    </button>
                    <button class="btn btn-primary sm btn-save-level" onclick="updateFloorCapacity(${f.id})" style="display:none; height: 32px; border-radius: 8px;">
                        APLICAR
                    </button>
                    <button class="btn-icon-premium sm" onclick="openEditFloorModal(${f.id})" title="Configuración Avanzada" style="display: none;">
                        <i class="fas fa-gear"></i>
                    </button>
                    <button class="btn-icon-premium sm danger" onclick="deleteFloor(${f.id})" title="Remover Nivel" style="display: none;">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `).join('');
    }

    container.innerHTML = cardsHtml;
}

export function toggleLevelEdit(id) {
    const block = document.getElementById(`level-block-${id}`);
    if (!block) return;

    const isEditing = block.classList.toggle('editing');
    const inputs = block.querySelectorAll('.stat-val-input');
    const btnEdit = block.querySelector('.btn-edit-level');
    const btnSave = block.querySelector('.btn-save-level');

    inputs.forEach(inp => inp.disabled = !isEditing);
    
    if (isEditing) {
        btnEdit.innerHTML = '<i class="fas fa-times"></i>';
        btnEdit.classList.add('danger');
        if (btnSave) btnSave.style.display = 'flex';
        if (inputs.length > 0) inputs[0].focus();
    } else {
        btnEdit.innerHTML = '<i class="fas fa-pen-to-square"></i>';
        btnEdit.classList.remove('danger');
        if (btnSave) btnSave.style.display = 'none';
        loadFloors();
    }
}

export async function savePBCapacity() {
    const capAutos = document.getElementById('pb-cap-autos').value;
    const capMotos = document.getElementById('pb-cap-motos').value;
    const capCamionetas = document.getElementById('pb-cap-camionetas').value;

    if (!capAutos || !capMotos || !capCamionetas) return showToast('Completá las plazas de PB');

    const resAutos = await api.post(`/admin/settings/prices?clave=capacidad_total&valor=${capAutos}`);
    const resMotos = await api.post(`/admin/settings/prices?clave=capacidad_motos&valor=${capMotos}`);
    const resCamionetas = await api.post(`/admin/settings/prices?clave=capacidad_camionetas&valor=${capCamionetas}`);

    if (resAutos.ok && resMotos.ok && resCamionetas.ok) {
        showToast('Capacidad de Planta Baja actualizada', 'success');
        loadFloors();
    } else {
        showToast('Error al actualizar Planta Baja', 'error');
    }
}

export async function updateFloorCapacity(id) {
    const capAutos = document.getElementById(`cap-autos-${id}`).value;
    const capMotos = document.getElementById(`cap-motos-${id}`).value;
    const capCamionetas = document.getElementById(`cap-camionetas-${id}`).value;

    const res = await api.patch(`/admin/floors/${id}?cap_autos=${capAutos}&cap_motos=${capMotos}&cap_camionetas=${capCamionetas}`);
    if (res.ok) {
        showToast('Capacidad de nivel actualizada', 'success');
        loadFloors();
    } else {
        showToast(res.error || 'Error al actualizar nivel', 'error');
    }
}

export function openAddFloorModal() {
    document.getElementById('edit-floor-id').value = '';
    document.getElementById('floor-nombre').value = '';
    document.getElementById('floor-cap-autos').value = '20';
    document.getElementById('floor-cap-motos').value = '10';
    if (document.getElementById('floor-cap-camionetas')) document.getElementById('floor-cap-camionetas').value = '5';
    document.getElementById('floor-modal-title').innerText = 'NUEVO NIVEL';
    document.getElementById('btn-floor-submit').innerText = 'CREAR NIVEL';
    if (window.openModal) window.openModal('modal-add-floor');
}

export async function openEditFloorModal(id) {
    const resBranches = await api.get('/admin/branches');
    const mySucursal = localStorage.getItem('sucursal')?.replace('AUTOPASS ', '').trim() || '';
    
    const branch = resBranches.data.find(b => 
        b.nombre.trim().toLowerCase() === mySucursal.trim().toLowerCase() ||
        b.nombre.trim().toLowerCase().includes(mySucursal.trim().toLowerCase())
    );
    
    if (!branch) return;
    const floor = (branch.floors || []).find(f => f.id === id);
    if (!floor) return;

    document.getElementById('edit-floor-id').value = floor.id;
    document.getElementById('floor-nombre').value = floor.nombre;
    document.getElementById('floor-cap-autos').value = floor.capacidad_total;
    document.getElementById('floor-cap-motos').value = floor.capacidad_motos;
    if (document.getElementById('floor-cap-camionetas')) document.getElementById('floor-cap-camionetas').value = floor.capacidad_camionetas ?? 5;
    
    document.getElementById('floor-modal-title').innerText = 'EDITAR NIVEL';
    document.getElementById('btn-floor-submit').innerText = 'GUARDAR CAMBIOS';
    
    if (window.openModal) window.openModal('modal-add-floor');
}

export async function handleCreateFloor(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const editId = document.getElementById('edit-floor-id').value;
    
    const resBranches = await api.get('/admin/branches');
    const mySucursal = localStorage.getItem('sucursal')?.replace('AUTOPASS ', '').trim() || '';
    
    const branch = resBranches.data.find(b => 
        b.nombre.trim().toLowerCase() === mySucursal.trim().toLowerCase() ||
        b.nombre.trim().toLowerCase().includes(mySucursal.trim().toLowerCase())
    );

    if (!branch) return showToast('Error: No se pudo identificar la sucursal activa', 'error');

    const payload = {
        nombre: document.getElementById('floor-nombre').value,
        capacidad_total: parseInt(document.getElementById('floor-cap-autos').value),
        capacidad_motos: parseInt(document.getElementById('floor-cap-motos').value),
        capacidad_camionetas: parseInt(document.getElementById('floor-cap-camionetas')?.value || '5')
    };

    btn.disabled = true;
    let res;
    if (editId) {
        res = await api.patch(`/admin/floors/${editId}?cap_autos=${payload.capacidad_total}&cap_motos=${payload.capacidad_motos}&cap_camionetas=${payload.capacidad_camionetas}`);
    } else {
        res = await api.post(`/admin/${branch.id}/floors`, payload);
    }

    if (res.ok) {
        showToast(editId ? 'Nivel actualizado' : 'Piso agregado correctamente', 'success');
        if (window.closeModal) window.closeModal('modal-add-floor');
        loadFloors();
    } else {
        showToast(res.error || 'Error al procesar', 'error');
    }
    btn.disabled = false;
}

export async function deleteFloor(id) {
    if (!await showConfirm('Eliminar Piso', '¿Estás seguro? Se perderá la configuración de capacidad de este nivel.')) return;
    
    const res = await api.delete(`/admin/floors/${id}`);
    if (res.ok) {
        showToast('Piso eliminado', 'success');
        loadFloors();
    } else {
        showToast(res.error || 'Error al eliminar', 'error');
    }
}
