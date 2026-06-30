import api from './api.js';
import { showToast, showConfirm, formatDate, formatPlate, formatNum } from './utils.js';

/**
 * PANEL ADMIN MODULO
 * OPERACIONES ADMINISTRATIVAS, GESTION DE USUARIOS Y CONFIGURACIONES.
 */

let userPage = 1;
const userPageSize = 10;
let allUsersData = [];
let allBranchesData = []; // CACHE LOCAL PARA SUCURSALES
let branchMap = null;
let branchMarker = null;

export function initBranchMap() {
    const mapEl = document.getElementById('branch-map-picker');
    if (!mapEl || branchMap || !window.L) return;

    // COORDENADAS INICIALES (BUENOS AIRES)
    const initialCoords = [-34.5888, -58.3900];
    branchMap = L.map('branch-map-picker').setView(initialCoords, 13);

    // TILES PREMIUM (DARK MATTER)
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(branchMap);

    // CLICK PARA UBICAR MANUALMENTE
    branchMap.on('click', function(e) {
        updateBranchMarker(e.latlng.lat, e.latlng.lng);
    });
}

function updateBranchMarker(lat, lng) {
    if (!branchMap) return;

    if (branchMarker) {
        branchMarker.setLatLng([lat, lng]);
    } else {
        const goldIcon = L.divIcon({
            className: 'custom-div-icon',
            html: `<div style="background-color: #C5A059; width: 15px; height: 15px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px #C5A059;"></div>`,
            iconSize: [15, 15],
            iconAnchor: [7, 7]
        });
        branchMarker = L.marker([lat, lng], { icon: goldIcon }).addTo(branchMap);
    }

    document.getElementById('branch-latitude').value = lat.toFixed(6);
    document.getElementById('branch-longitude').value = lng.toFixed(6);
}

export async function searchAddress() {
    const address = document.getElementById('branch-direccion').value;
    if (!address) return showToast('Ingresá una dirección para buscar');

    try {
        const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(address)}&limit=1`;
        const res = await fetch(url);
        const data = await res.json();

        if (data && data.length > 0) {
            const lat = parseFloat(data[0].lat);
            const lng = parseFloat(data[0].lon);

            initBranchMap(); // ASEGURAR QUE EL MAPA EXISTE
            updateBranchMarker(lat, lng);
            branchMap.setView([lat, lng], 16);
            showToast('Ubicación encontrada');
        } else {
            showToast('No se encontró la dirección. Intentá ser más específico.');
        }
    } catch (err) {
        console.error('Error en geocoding:', err);
        showToast('Error al buscar la dirección');
    }
}

export async function loadUsers() {
    try {
        // RESTRICCION VISUAL DE FILTROS PARA ADMIN LOCAL (ELIMINACION FISICA)
        const myRol = localStorage.getItem('rol');
        if (myRol !== 'admin') {
            const adminOption = document.querySelector('#user-filter-rol option[value="admin"]');
            if (adminOption) adminOption.remove();
        }

        const res = await api.get('/admin/users');
        if (res && res.ok) {
            
            // DEFINIMOS LA JERARQUIA DE ROLES PARA EL ORDENAMIENTO
            const roleOrder = {
                'admin': 1,
                'local_admin': 2,
                'staff': 3,
                'user': 4
            };

            // ORDENAMOS LA DATA POR ROL Y LUEGO POR NOMBRE/APELLIDO
            allUsersData = (res.data || []).sort((a, b) => {
                const orderA = roleOrder[a.rol] || 99;
                const orderB = roleOrder[b.rol] || 99;
                if (orderA !== orderB) return orderA - orderB;
                return a.apellido.localeCompare(b.apellido);
            });

            renderUserTable();
            updateUserKPIs();
        } else {
            console.error('Error al cargar usuarios:', res?.error);
            const tbody = document.getElementById('user-list');
            if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center py-20 text-danger">Error: ${res?.error || 'No se pudo obtener datos'}</td></tr>`;
        }
    } catch (err) {
        console.error('Excepción en loadUsers:', err);
    }
}

function updateUserKPIs() {
    try {
        const total = allUsersData.length;
        const admins = allUsersData.filter(u => u.rol === 'admin' || u.rol === 'local_admin').length;
        const staff = allUsersData.filter(u => u.rol === 'staff').length;
        const customers = allUsersData.filter(u => u.rol === 'user').length;

        const elTotal = document.getElementById('stat-total-users');
        const elAdmin = document.getElementById('stat-admin-users');
        const elStaff = document.getElementById('stat-staff-users');
        const elCustomer = document.getElementById('stat-customer-users');

        if (elTotal) elTotal.innerText = formatNum(total);
        if (elAdmin) elAdmin.innerText = formatNum(admins);
        if (elStaff) elStaff.innerText = formatNum(staff);
        if (elCustomer) elCustomer.innerText = formatNum(customers);
    } catch (err) {
        console.warn('Error actualizando KPIs de usuarios:', err);
    }
}

export function renderUserTable(filteredData = null) {
    try {
        const data = filteredData || allUsersData;
        const tbody = document.getElementById('user-list');
        if (!tbody) return;

        const totalPages = Math.ceil(data.length / userPageSize);
        if (userPage > totalPages) userPage = Math.max(1, totalPages);

        const start = (userPage - 1) * userPageSize;
        const paged = data.slice(start, start + userPageSize);

        tbody.innerHTML = paged.map(u => {
            const isStaffOrAdmin = u.rol === 'admin' || u.rol === 'local_admin' || u.rol === 'staff';
            const puntosDisplay = isStaffOrAdmin ? '<span class="text-muted">---</span>' : `<div class="points-badge-sm mx-auto" style="display:inline-flex;"><i class="fas fa-star"></i> ${formatNum(u.puntos_acumulados || 0)}</div>`;
            const saldoDisplay = isStaffOrAdmin ? '<span class="text-muted">---</span>' : `<span class="text-success">$${(u.saldo || 0).toLocaleString()}</span>`;

            // PERSONALIZACION DE ETIQUETAS DE ROL
            let roleLabel = (u.rol || 'user').toUpperCase();
            const sedeLimpia = (u.sucursal || '').replace('AUTOPASS ', '').trim();

            if (u.rol === 'admin') roleLabel = 'Admin Global';
            else if (u.rol === 'local_admin') roleLabel = `Admin ${sedeLimpia || 'Sucursal'}`;
            else if (u.rol === 'staff') roleLabel = `Empleado ${sedeLimpia || 'Sucursal'}`;
            else if (u.rol === 'user') roleLabel = 'Cliente';

            return `
            <tr>
                <td data-label="Usuario">
                    <div class="user-info-cell flex-col items-center">
                        <div class="text-center">
                            <div class="user-name text-center">${u.nombre || 'S/N'} ${u.apellido || 'S/A'}</div>
                            <div class="user-dni">DNI: ${u.dni || '---'}</div>
                        </div>
                    </div>
                </td>
                <td data-label="Contacto">
                    <div class="user-contact text-center">
                        <span class="text-center"><i class="fas fa-envelope"></i> ${u.email || '---'}</span>
                    </div>
                </td>
                <td data-label="Rol" class="text-center"><span class="role-badge ${u.rol || 'user'} mx-auto">${roleLabel}</span></td>
                <td data-label="Puntos" class="text-center">${puntosDisplay}</td>
                <td data-label="Saldo" class="text-bold text-center">
                    <div class="flex-row justify-center w-full">
                        ${saldoDisplay}
                    </div>
                </td>
                <td data-label="Acciones">
                    <div class="flex-row gap-5 user-actions justify-center">
                        <button class="btn-icon-premium sm" onclick="openEditUserModal(${u.id})" title="Editar Información">
                            <i class="fas fa-user-pen"></i>
                        </button>
                        <button class="btn-icon-premium sm" onclick="openPasswordModal(${u.id}, '${u.nombre} ${u.apellido}')" title="Cambiar Contraseña">
                            <i class="fas fa-key"></i>
                        </button>
                        <button class="btn-icon-premium sm" onclick="toggleUserBlock(${u.id}, '${u.nombre}', ${u.is_blocked})" title="${u.is_blocked ? 'Desbloquear' : 'Bloquear'}">
                            <i class="fas ${u.is_blocked ? 'fa-user-check' : 'fa-user-slash'}"></i>
                        </button>
                        <button class="btn-icon-premium sm danger" onclick="deleteUserAdmin(${u.id})" title="Eliminar">
                            <i class="fas fa-trash-can"></i>
                        </button>
                    </div>
                </td>
            </tr>`;
        }).join('') || '<tr><td colspan="6" class="text-center py-20">No se encontraron usuarios.</td></tr>';

        const info = document.getElementById('user-page-info');
        if (info) info.innerText = `Página ${userPage} de ${totalPages || 1}`;

        const prev = document.getElementById('prev-user-btn');
        const next = document.getElementById('next-user-btn');
        if (prev) prev.disabled = userPage === 1;
        if (next) next.disabled = userPage >= totalPages;
    } catch (err) {
        console.error('Error renderizando tabla de usuarios:', err);
        const tbody = document.getElementById('user-list');
        if (tbody) tbody.innerHTML = `<tr><td colspan="6" class="text-center py-20 text-danger">Error crítico al renderizar la tabla</td></tr>`;
    }
}

export function filterUserList() {
    const query = document.getElementById('user-search')?.value.toLowerCase() || '';
    const roleFilter = document.getElementById('user-filter-rol')?.value || '';

    const filtered = allUsersData.filter(u => {
        const matchesQuery = !query || 
            u.nombre.toLowerCase().includes(query) || 
            u.apellido.toLowerCase().includes(query) || 
            u.email.toLowerCase().includes(query) || 
            u.dni.toString().includes(query);
        
        const matchesRole = !roleFilter || u.rol === roleFilter;

        return matchesQuery && matchesRole;
    });

    userPage = 1;
    renderUserTable(filtered);
}

export function prevUserPage() { if (userPage > 1) { userPage--; renderUserTable(); } }
export function nextUserPage() { 
    const totalPages = Math.ceil(allUsersData.length / userPageSize);
    if (userPage < totalPages) { userPage++; renderUserTable(); } 
}

export async function openBarrier(gateId) {
    // CONFIRMACION MEDIANTE ALERTA PREMIUM (ESTILO UNIFICADO)
    const confirmed = await showConfirm(
        '', 
        `<div class="flex-col items-center gap-10" style="padding: 10px 0; font-size: 1.25rem; font-weight: 600;">
            <div class="text-secondary" style="letter-spacing: 1px; text-transform: uppercase;">
                BARRERA ${gateId}
            </div>
            <div style="opacity: 0.9; margin-top: 5px;">
                ¿Abrir la barrera?
            </div>
        </div>`
    );
    if (!confirmed) return;

    const iconId = gateId === 'ENTRADA' ? 'icon-barrier-entry' : 'icon-barrier-exit';
    const iconEl = document.getElementById(iconId);
    if (iconEl) iconEl.src = '/static/images/barrera alta.png';

    const res = await api.post(`/admin/open-barrier?gate_id=${gateId}`);
    if (res && res.ok) {
        showToast(`Barrera ${gateId} abierta.`);
        setTimeout(() => { if (iconEl) iconEl.src = '/static/images/barrera baja.png'; }, 3000);
    } else {
        showToast(`Error: ${res?.error || 'Desconocido'}`);
        if (iconEl) iconEl.src = '/static/images/barrera baja.png';
    }
}

export function showCreateUserModal() {
    const rol = localStorage.getItem('rol');
    const sucursal = localStorage.getItem('sucursal') || '';
    
    const roleSelect = document.getElementById('admin-user-rol');
    const branchRow = document.getElementById('branch-selection-row');
    const branchSelect = document.getElementById('admin-user-sucursal');

    if (!roleSelect) return;

    // REINICIAR OPCIONES
    roleSelect.innerHTML = `
        <option value="user" style="background: #111;">Cliente</option>
        <option value="staff" style="background: #111;">Empleado</option>
        <option value="local_admin" style="background: #111;">Administrador de Sucursal</option>
        <option value="admin" style="background: #111;">Administrador General</option>
    `;

    if (rol === 'local_admin') {
        // LOS ADMINISTRADORES LOCALES SOLO CREAN PERSONAL PARA SU PUNTO
        roleSelect.innerHTML = `
            <option value="staff" style="background: #111;">Empleado</option>
            <option value="local_admin" style="background: #111;">Administrador de Sucursal</option>
        `;
        
        if (branchRow) branchRow.style.display = 'block';
        if (branchSelect) {
            branchSelect.innerHTML = `<option value="${sucursal}">${sucursal.toUpperCase()}</option>`;
            branchSelect.value = sucursal;
            branchSelect.disabled = true;
        }
    } else {
        //ADMIN GLOBAL VE TODO
        if (branchRow) branchRow.style.display = 'none';
        if (branchSelect) branchSelect.disabled = false;
        roleSelect.value = 'user';
    }

    if (window.openModal) window.openModal('modal-create-user');
}

export function toggleBranchSelection() {
    const rol = document.getElementById('admin-user-rol').value;
    const branchRow = document.getElementById('branch-selection-row');
    const userRol = localStorage.getItem('rol');

    // SI EL QUE ESTA CREANDO ES UN ADMIN LOCAL, LA FILA DE SEDE YA ESTA VISIBLE Y BLOQUEADA
    if (userRol === 'local_admin') return;

    if (branchRow) {
        branchRow.style.display = (rol === 'staff' || rol === 'local_admin') ? 'block' : 'none';
    }
}

export async function handleAdminCreateUser(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const rol = document.getElementById('admin-user-rol').value;
    const sucursal = (rol === 'staff' || rol === 'local_admin') ? document.getElementById('admin-user-sucursal').value : null;

    const payload = {
        nombre: document.getElementById('admin-user-nombre').value,
        apellido: document.getElementById('admin-user-apellido').value,
        email: document.getElementById('admin-user-email').value,
        dni: document.getElementById('admin-user-dni').value,
        password: document.getElementById('admin-user-password').value,
        telefono: "1112345678",
        sucursal: sucursal
    };

    btn.disabled = true;
    const res = await api.post(`/admin/users?rol=${rol}`, payload);
    if (res && res.ok) {
        showToast('Usuario creado.');
        if (window.closeModal) window.closeModal('modal-create-user');
        event.target.reset();
        if (window.loadUsers) window.loadUsers(); 
    } else {
        showToast(`Error: ${res?.error || 'Desconocido'}`);
    }
    btn.disabled = false;
}

export async function toggleUserBlock(id, nombre, currentlyBlocked) {
    const action = currentlyBlocked ? 'DESBLOQUEAR' : 'BLOQUEAR';
    if (!await showConfirm(`${action} USUARIO`, `¿Estás seguro?`)) return;

    const res = await api.post(`/admin/users/${id}/toggle-block`);
    if (res && res.ok) { showToast(res.data.message); if (window.loadUsers) window.loadUsers(); }
    else showToast(res?.error || 'Error');
}

export async function refreshSystemDiagnostics() {
    try {
        const res = await api.get('/system/health');
        if (!res.ok) throw new Error("Health check failed");

        const data = res.data;
        const sucursal = (localStorage.getItem('sucursal') || '').replace('AUTOPASS ', '').toUpperCase().trim();

        // 1. NUCLEO Y BARRERAS
        const updateDot = (id, status) => {
            const dot = document.getElementById(`diag-${id}-dot`);
            if (!dot) return;
            dot.className = status === 'ONLINE' ? 'status-dot-mini online' : 'status-dot-mini offline';
        };

        updateDot('api', data.api);
        updateDot('db', data.database);
        
        // BARRERAS (SIMULAMOS CON API/MQTT POR AHORA)
        updateDot('barrera-entrada', data.api);
        updateDot('barrera-salida', data.api);

        // 2. LECTORES DE PATENTE (ALPR)
        const updateALPRDot = (type, status) => {
            const dot = document.getElementById(`diag-cam-${type}-dot`);
            if (!dot) return;
            dot.className = status === 'ONLINE' ? 'status-dot-mini online' : 'status-dot-mini offline';
        };

        const entryKey = sucursal ? `${sucursal}_ENTRADA` : 'ENTRADA';
        const exitKey = sucursal ? `${sucursal}_SALIDA` : 'SALIDA';

        updateALPRDot('entrada', data.alpr[entryKey] || 'OFFLINE');
        updateALPRDot('salida', data.alpr[exitKey] || 'OFFLINE');

        // OVERALL STATUS
        const overall = document.getElementById('sys-overall-status');
        if (overall) {
            const allOk = data.api === 'ONLINE' && data.database === 'ONLINE';
            overall.innerText = allOk ? 'ESTABLE' : 'ALERTA';
            overall.className = `badge-status ${allOk ? 'badge-success-light' : 'badge-danger-light'}`;
        }

    } catch (err) {
        console.warn("Error en diagnóstico:", err);
    }
}

export async function loadSettings() {
    const res = await api.get('/admin/settings');
    if (res.ok) {
        const cfg = res.data;
        Object.keys(cfg).forEach(key => {
            const el = document.getElementById(`cfg-${key}`);
            if (el) el.value = cfg[key];
        });
        loadFloors();
        refreshSystemDiagnostics(); // CARGA INICIAL
    }
}

export function switchSettingsTab(tabId, btn) {
    // 1. ALTERNAR SECCIONES
    document.querySelectorAll('.settings-section').forEach(s => s.style.display = 'none');
    const target = document.getElementById(`set-section-${tabId}`);
    if (target) target.style.display = 'block';

    // 2. ALTERNAR BOTONES
    document.querySelectorAll('.btn-tab-mini').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    // 3. CARGA ESPECIFICA DE MONITOREO
    if (tabId === 'monitoring' && window.loadCameraSettings) {
        window.loadCameraSettings();
    }
}

export function switchRatesTab(type, btn) {
    // 1. ALTERNAR GRUPOS
    document.querySelectorAll('.rate-group').forEach(g => g.style.display = 'none');
    const target = document.getElementById(`rate-group-${type}`);
    if (target) target.style.display = 'block';

    // 2. ALTERNAR BOTONES
    document.querySelectorAll('.btn-tab-sub').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');
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
    
    // 1. BLOQUE PLANTA BAJA (PB)
    let cardsHtml = `
        <div class="level-block pb" id="level-block-pb">
            <div class="level-indicator">
                <span class="level-code">PB</span>
            </div>
            <div class="level-main-content" style="justify-content: center;">
                <div class="level-stats-grid" style="gap: 50px;">
                    <div class="stat-item">
                        <span class="text-sm text-white uppercase fw-900"><i class="fas fa-car mr-10 text-dorado" style="font-size: 1.2rem;"></i> Autos</span>
                        <div class="stat-val-box">
                            <input type="number" id="pb-cap-autos" class="stat-val-input" value="${pbCapAutos}" min="0" disabled style="width: 100px; font-size: 1.6rem;">
                        </div>
                    </div>
                    <div class="stat-item">
                        <span class="text-sm text-white uppercase fw-900"><i class="fas fa-motorcycle mr-10 text-dorado" style="font-size: 1.2rem;"></i> Motos</span>
                        <div class="stat-val-box">
                            <input type="number" id="pb-cap-motos" class="stat-val-input" value="${pbCapMotos}" min="0" disabled style="width: 100px; font-size: 1.6rem;">
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

    // 2. BLOQUES NIVELES SUPERIORES (L1, L2, ...)
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
                    </div>
                </div>
                <div class="level-actions">
                    <button class="btn-icon-premium sm btn-edit-level" onclick="toggleLevelEdit(${f.id})" title="Editar Plazas">
                        <i class="fas fa-pen-to-square"></i>
                    </button>
                    <button class="btn btn-primary sm btn-save-level" onclick="updateFloorCapacity(${f.id})" style="display:none; height: 32px; border-radius: 8px;">
                        APLICAR
                    </button>
                    <!-- Oculto para simplificar a un solo nivel -->
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
    // ENCONTRAR TODOS LOS INPUTS DENTRO DEL NIVEL ESPECIFICO
    const inputs = block.querySelectorAll('.stat-val-input');
    const btnEdit = block.querySelector('.btn-edit-level');
    const btnSave = block.querySelector('.btn-save-level');

    inputs.forEach(inp => inp.disabled = !isEditing);
    
    if (isEditing) {
        btnEdit.innerHTML = '<i class="fas fa-times"></i>';
        btnEdit.classList.add('danger');
        if (btnSave) btnSave.style.display = 'flex';
        // FOCO EN EL PRIMER INPUT SI EXISTE
        if (inputs.length > 0) inputs[0].focus();
    } else {
        btnEdit.innerHTML = '<i class="fas fa-pen-to-square"></i>';
        btnEdit.classList.remove('danger');
        if (btnSave) btnSave.style.display = 'none';
        loadFloors(); // RECARGAR PARA RESETEAR ESTADOS
    }
}


export async function savePBCapacity() {
    const capAutos = document.getElementById('pb-cap-autos').value;
    const capMotos = document.getElementById('pb-cap-motos').value;

    if (!capAutos || !capMotos) return showToast('Completá las plazas de PB');

    const resAutos = await api.post(`/admin/settings/prices?clave=capacidad_total&valor=${capAutos}`);
    const resMotos = await api.post(`/admin/settings/prices?clave=capacidad_motos&valor=${capMotos}`);

    if (resAutos.ok && resMotos.ok) {
        showToast('Capacidad de Planta Baja actualizada');
        loadFloors();
    } else {
        showToast('Error al actualizar Planta Baja');
    }
}

export async function updateFloorCapacity(id) {
    const capAutos = document.getElementById(`cap-autos-${id}`).value;
    const capMotos = document.getElementById(`cap-motos-${id}`).value;

    const res = await api.patch(`/admin/floors/${id}?cap_autos=${capAutos}&cap_motos=${capMotos}`);
    if (res.ok) {
        showToast('Capacidad de nivel actualizada');
        loadFloors();
    } else {
        showToast(res.error || 'Error al actualizar nivel');
    }
}



export function openAddFloorModal() {
    document.getElementById('edit-floor-id').value = '';
    document.getElementById('floor-nombre').value = '';
    document.getElementById('floor-cap-autos').value = '20';
    document.getElementById('floor-cap-motos').value = '10';
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
    
    document.getElementById('floor-modal-title').innerText = 'EDITAR NIVEL';
    document.getElementById('btn-floor-submit').innerText = 'GUARDAR CAMBIOS';
    
    if (window.openModal) window.openModal('modal-add-floor');
}

export async function handleCreateFloor(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const editId = document.getElementById('edit-floor-id').value;
    
    //NECESITAMOS EL BRANCH_ID
    const resBranches = await api.get('/admin/branches');
    const mySucursal = localStorage.getItem('sucursal')?.replace('AUTOPASS ', '').trim() || '';
    
    const branch = resBranches.data.find(b => 
        b.nombre.trim().toLowerCase() === mySucursal.trim().toLowerCase() ||
        b.nombre.trim().toLowerCase().includes(mySucursal.trim().toLowerCase())
    );

    if (!branch) return showToast('Error: No se pudo identificar la sucursal activa');

    const payload = {
        nombre: document.getElementById('floor-nombre').value,
        capacidad_total: parseInt(document.getElementById('floor-cap-autos').value),
        capacidad_motos: parseInt(document.getElementById('floor-cap-motos').value)
    };

    btn.disabled = true;
    let res;
    if (editId) {
        res = await api.patch(`/admin/floors/${editId}?cap_autos=${payload.capacidad_total}&cap_motos=${payload.capacidad_motos}`);
    } else {
        res = await api.post(`/admin/${branch.id}/floors`, payload);
    }

    if (res.ok) {
        showToast(editId ? 'Nivel actualizado' : 'Piso agregado correctamente');
        if (window.closeModal) window.closeModal('modal-add-floor');
        loadFloors();
    } else {
        showToast(res.error || 'Error al procesar');
    }
    btn.disabled = false;
}

export async function deleteFloor(id) {
    if (!await showConfirm('Eliminar Piso', '¿Estás seguro? Se perderá la configuración de capacidad de este nivel.')) return;
    
    const res = await api.delete(`/admin/floors/${id}`);
    if (res.ok) {
        showToast('Piso eliminado');
        loadFloors();
    } else {
        showToast(res.error || 'Error al eliminar');
    }
}

export async function saveAllRates() {
    const keys = [
        'precio_hora', 'precio_dia', 'precio_semana', 'precio_mes',
        'precio_hora_moto', 'precio_dia_moto', 'precio_semana_moto', 'precio_mes_moto',
        'precio_hora_camioneta', 'precio_dia_camioneta', 'precio_semana_camioneta', 'precio_mes_camioneta'
    ];
    
    const labels = {
        'precio_hora': 'Hora', 'precio_dia': 'Día', 'precio_semana': 'Semana', 'precio_mes': 'Mes',
        'precio_hora_moto': 'Hora', 'precio_dia_moto': 'Día', 'precio_semana_moto': 'Semana', 'precio_mes_moto': 'Mes',
        'precio_hora_camioneta': 'Hora', 'precio_dia_camioneta': 'Día', 'precio_semana_camioneta': 'Semana', 'precio_mes_camioneta': 'Mes'
    };

    let summary = '<div style="text-align: left; margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; max-height: 200px; overflow-y: auto;">';
    keys.forEach(key => {
        const val = document.getElementById(`cfg-${key}`)?.value || 0;
        summary += `<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="color: #fff; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">${labels[key]}:</span>
                        <b style="color: var(--dorado); font-size: 0.75rem;">$${parseFloat(val).toLocaleString()}</b>
                    </div>`;
    });
    summary += '</div>';

    if (!await showConfirm('Confirmar Tarifario', summary)) return;

    let success = true;
    for (const key of keys) {
        const input = document.getElementById(`cfg-${key}`);
        if (!input) continue;
        const val = parseFloat(input.value) || 0;
        const res = await api.post(`/admin/settings/prices?clave=${key}&valor=${val}`);
        if (!res.ok) success = false;
    }

    if (success) {
        showToast('Tarifas actualizadas correctamente.');
        // SI HAY GRUPOS EN EDICION, CERRARLOS
        document.querySelectorAll('.rate-group').forEach(g => {
            g.classList.remove('editing');
            g.querySelectorAll('input').forEach(i => i.disabled = true);
        });
        document.querySelectorAll('[id^="btn-save-rates-"]').forEach(b => b.style.display = 'none');
        document.querySelectorAll('[id^="btn-edit-rates-"]').forEach(b => b.style.display = 'inline-flex');
    }
    else showToast('Error al actualizar algunas tarifas.');
}

export function toggleRateEdit(type) {
    const group = document.getElementById(`rate-group-${type}`);
    const btn = document.getElementById(`btn-edit-rates-${type}`);
    const inputs = group.querySelectorAll('input');

    const isEditing = group.classList.contains('editing');

    if (!isEditing) {
        // ENTRAR EN MODO EDICION
        inputs.forEach(input => input.disabled = false);
        group.classList.add('editing');
        btn.innerHTML = '<i class="fas fa-check mr-8"></i> APLICAR';
        btn.style.borderColor = '#4CAF50';
        btn.style.color = '#4CAF50';
        if (inputs.length > 0) inputs[0].focus();
    } else {
        // AL PRESIONAR "APLICAR", DISPARAMOS EL GUARDADO
        saveRateGroup(type);
    }
}

export async function saveRateGroup(type) {
    const group = document.getElementById(`rate-group-${type}`);
    const btn = document.getElementById(`btn-edit-rates-${type}`);
    const inputs = group.querySelectorAll('input');

    const isAutos = type === 'autos';
    const isMotos = type === 'motos';
    const keys = isAutos ? 
        ['precio_hora', 'precio_dia', 'precio_semana', 'precio_mes'] :
        (isMotos ? 
            ['precio_hora_moto', 'precio_dia_moto', 'precio_semana_moto', 'precio_mes_moto'] :
            ['precio_hora_camioneta', 'precio_dia_camioneta', 'precio_semana_camioneta', 'precio_mes_camioneta']);

    const labels = {
        'precio_hora': 'Hora', 'precio_dia': 'Día', 'precio_semana': 'Semana', 'precio_mes': 'Mes',
        'precio_hora_moto': 'Hora', 'precio_dia_moto': 'Día', 'precio_semana_moto': 'Semana', 'precio_mes_moto': 'Mes',
        'precio_hora_camioneta': 'Hora', 'precio_dia_camioneta': 'Día', 'precio_semana_camioneta': 'Semana', 'precio_mes_camioneta': 'Mes'
    };

    let summary = '<div style="text-align: left; margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px; max-height: 200px; overflow-y: auto;">';
    keys.forEach(key => {
        const val = document.getElementById(`cfg-${key}`)?.value || 0;
        summary += `<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="color: #fff; font-size: 0.75rem; text-transform: uppercase; font-weight: 700;">${labels[key]}:</span>
                        <b style="color: var(--dorado); font-size: 0.75rem;">$${parseFloat(val).toLocaleString()}</b>
                    </div>`;
    });
    summary += '</div>';

    // FUNCION PARA RESETEAR LA UI DEL GRUPO (BLOQUEAR)
    const resetUI = () => {
        inputs.forEach(input => input.disabled = true);
        group.classList.remove('editing');
        btn.innerHTML = '<i class="fas fa-edit mr-8"></i> EDITAR';
        btn.style.borderColor = 'var(--dorado)';
        btn.style.color = '#aaa';
    };

    if (!await showConfirm(`Confirmar Tarifas ${type.toUpperCase()}`, summary)) {
        resetUI();
        return;
    }

    let success = true;
    for (const key of keys) {
        const input = document.getElementById(`cfg-${key}`);
        if (!input) continue;
        const val = parseFloat(input.value) || 0;
        const res = await api.post(`/admin/settings/prices?clave=${key}&valor=${val}`);
        if (!res.ok) success = false;
    }

    if (success) {
        showToast(`Tarifas de ${type} actualizadas correctamente.`);
    } else {
        showToast('Error al actualizar algunas tarifas.');
    }
    
    resetUI();
}

export async function saveSystemParam(param) {
    const val = document.getElementById(`cfg-${param}`).value;
    const res = await api.post(`/admin/settings/prices?clave=${param}&valor=${val}`);
    if (res.ok) showToast('Configuración guardada.');
    else showToast(res.error);
}

export async function saveCapacities() {
    const capAutos = document.getElementById('cfg-capacidad_total').value;
    const capMotos = document.getElementById('cfg-capacidad_motos').value;

    if (!capAutos || !capMotos) return showToast('Completá ambos valores de plazas');

    let success = true;
    
    // ACTUALIZAR AUTOS
    const resAutos = await api.post(`/admin/settings/prices?clave=capacidad_total&valor=${capAutos}`);
    if (!resAutos.ok) success = false;

    // ACTUALIZAR MOTOS
    const resMotos = await api.post(`/admin/settings/prices?clave=capacidad_motos&valor=${capMotos}`);
    if (!resMotos.ok) success = false;

    if (success) showToast('Plazas actualizadas correctamente.');
    else showToast('Error al actualizar plazas.');
}

export async function resetSys() {
    if (!await showConfirm('REINICIAR SISTEMA', 'Esto eliminará logs de acceso y ocupación actual. ¿Continuar?')) return;
    const res = await api.post('/system/reset');
    if (res && res.ok) {
        showToast('Sistema reiniciado.');
        window.location.reload();
    } else showToast(res?.error || 'Error');
}

export async function exportFinanceData() {
    const period = document.getElementById('fin-period')?.value || 'month';
    showToast('Generando reporte...');
    
    const res = await api.get(`/reports/payment-history?period=${period}&limit=0`);
    if (!res || !res.ok) {
        showToast('Error al obtener datos para exportar');
        return;
    }
    
    const data = res.data;
    if (data.length === 0) {
        showToast('No hay transacciones para exportar en este período');
        return;
    }
    
    // GENERAR CSV
    const headers = ['Fecha y Hora', 'Vehículo / Patente', 'Monto Abonado', 'Método de Pago', 'Estado/Tipo'];
    const rows = data.map(p => {
        const dateStr = formatDate(p.fecha_pago);
        const amount = p.costo_estadia;
        const method = (p.tipo === 'Reserva' || p.tipo === 'Reembolso') ? 'MERCADO PAGO / ABONO' : 'SISTEMA DIGITAL';
        const type = p.tipo;
        return [
            `"${dateStr}"`,
            `"${formatPlate(p.patente_detectada)}"`,
            amount,
            `"${method}"`,
            `"${type}"`
        ];
    });
    
    const csvContent = "\uFEFF" + [headers.join(','), ...rows.map(e => e.join(','))].join('\n');
    
    // CREAR Y DESCARGAR ARCHIVO
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");
    const url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    
    const branchName = localStorage.getItem('sucursal') || 'global';
    const cleanBranch = branchName.replace('AUTOPASS ', '').toLowerCase().replace(/\s+/g, '_');
    link.setAttribute("download", `reporte_financiero_${cleanBranch}_${period}_${new Date().toISOString().split('T')[0]}.csv`);
    
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast('Reporte descargado correctamente.');
}

export async function deleteUserAdmin(id) {
    if (!await showConfirm('Eliminar Usuario', `¿Estás seguro?`)) return;
    const res = await api.post(`/admin/users/${id}/delete`);
    if (res && res.ok) { showToast('Eliminado.'); if (window.loadUsers) window.loadUsers(); }
    else showToast(res?.error || 'Error');
}

// --- GESTION DE SUCURSALES ---

export function showCreateBranchModal() {
    document.getElementById('form-add-branch').reset();
    document.getElementById('branch-id-edit').value = '';
    document.getElementById('branch-modal-title').innerText = 'NUEVA SUCURSAL';
    document.getElementById('branch-modal-icon').className = 'fas fa-building';
    document.getElementById('branch-logo-preview').querySelector('img').src = '/static/images/logo.png';
    
    if (window.openModal) window.openModal('modal-add-branch');

    // INICIALIZAR MAPA (MORON POR DEFECTO)
    setTimeout(() => {
        initBranchMap();
        if (branchMarker) {
            branchMap.removeLayer(branchMarker);
            branchMarker = null;
        }
        branchMap.setView([-34.6508, -58.6228], 13);
    }, 300);
}

export async function loadBranches() {
    try {
        console.log("[*] Cargando sucursales...");
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

export function showBranchFloors(id) {
    const b = allBranchesData.find(x => x.id === id);
    if (!b) return;

    document.getElementById('branch-floors-title').innerText = `NIVELES: ${b.nombre.toUpperCase()}`;
    const tbody = document.getElementById('branch-floors-body');
    if (!tbody) return;

    // CALCULAR PLANTA BAJA (PB) - RESTAMOS LA OCUPACION DE LOS PISOS A LA TOTAL REPORTADA
    const floorsSumAutos = (b.floors || []).reduce((acc, f) => acc + f.ocupacion_actual, 0);
    const floorsSumMotos = (b.floors || []).reduce((acc, f) => acc + f.ocupacion_motos, 0);
    
    // B.OCUPACION_AUTOS_TOTAL ES EL TOTAL REAL DE LA SEDE (INCLUYE PB)
    const pbOccAutos = Math.max(0, b.ocupacion_autos_total - floorsSumAutos);
    const pbOccMotos = Math.max(0, b.ocupacion_motos_total - floorsSumMotos);
    
    // LA CAPACIDAD DE PB ES B.CAPACIDAD_AUTOS_TOTAL - SUM(CAP_PISOS)
    const floorsCapAutos = (b.floors || []).reduce((acc, f) => acc + f.capacidad_total, 0);
    const floorsCapMotos = (b.floors || []).reduce((acc, f) => acc + f.capacidad_motos, 0);
    const pbCapAutos = b.capacidad_autos_total - floorsCapAutos;
    const pbCapMotos = b.capacidad_motos_total - floorsCapMotos;

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
            </tr>
        `).join('');
    }

    tbody.innerHTML = rows;
    if (window.openModal) window.openModal('modal-branch-floors');
}

export function editBranch(id) {
    const b = allBranchesData.find(x => x.id === id);
    if (!b) return;

    document.getElementById('branch-id-edit').value = b.id;
    document.getElementById('branch-nombre').value = b.nombre;
    document.getElementById('branch-direccion').value = b.direccion;
    document.getElementById('branch-telefono').value = b.telefono;
    
    // COORDENADAS
    const lat = b.latitude || -34.6508;
    const lng = b.longitude || -58.6228;
    document.getElementById('branch-latitude').value = lat;
    document.getElementById('branch-longitude').value = lng;

    // CONFIGURAR LOGO
    const preview = document.querySelector('#branch-logo-preview img');
    const hasLogo = b.logo_url && b.logo_url !== '/static/images/logo.png';
    if (preview) {
        preview.src = b.logo_url || '/static/images/logo.png';
        preview.style.opacity = "1";
    }
    document.getElementById('branch-logo-file').value = ''; // LIMPIAR INPUT FILE
    document.getElementById('btn-clear-logo').style.display = hasLogo ? 'block' : 'none';

    document.getElementById('branch-is-24h').checked = b.is_24h;
    document.getElementById('branch-horario').value = b.is_24h ? '' : b.horario;
    document.getElementById('branch-horario').disabled = b.is_24h;

    document.getElementById('branch-modal-title').innerText = 'EDITAR SUCURSAL';
    document.getElementById('branch-modal-icon').className = 'fas fa-pen-to-square';
    
    if (window.openModal) window.openModal('modal-add-branch');

    // INICIALIZAR MAPA Y MARCADOR
    setTimeout(() => {
        initBranchMap();
        updateBranchMarker(lat, lng);
        if (branchMap) branchMap.setView([lat, lng], 15);
    }, 300);
}

export async function toggleBranch(id) {
    const res = await api.post(`/admin/branches/${id}/toggle`);
    if (res && res.ok) {
        showToast(`Sucursal ${res.data.activa ? 'Activada' : 'Suspendida'}`);
    } else {
        showToast(res?.error || 'Error al cambiar estado');
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
            preview.src = e.target.result;
            preview.style.opacity = "1";
        }
        reader.readAsDataURL(input.files[0]);
    }
    document.getElementById('btn-clear-logo').style.display = 'block';
}

export function clearBranchLogo() {
    const preview = document.querySelector('#branch-logo-preview img');
    preview.src = '/static/images/logo.png';
    document.getElementById('branch-logo-file').value = '';
    document.getElementById('btn-clear-logo').style.display = 'none';
    document.getElementById('branch-logo-clear').value = 'true';
}

export async function handleCreateBranch(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const editId = document.getElementById('branch-id-edit').value;
    
    // USAR FORMDATA PARA ENVIO DE ARCHIVOS
    const formData = new FormData();
    formData.append('nombre', document.getElementById('branch-nombre').value);
    formData.append('direccion', document.getElementById('branch-direccion').value);
    formData.append('telefono', document.getElementById('branch-telefono').value);
    formData.append('horario', document.getElementById('branch-horario').value || '---');
    formData.append('is_24h', document.getElementById('branch-is-24h').checked);
    
    const lat = document.getElementById('branch-latitude').value;
    const lng = document.getElementById('branch-longitude').value;
    if (lat) formData.append('latitude', lat);
    if (lng) formData.append('longitude', lng);
    
    const fileInput = document.getElementById('branch-logo-file');
    if (fileInput.files[0]) {
        formData.append('logo_file', fileInput.files[0]);
    }

    const logoClear = document.getElementById('branch-logo-clear');
    if (logoClear && logoClear.value === 'true') {
        formData.append('logo_clear', 'true');
    }

    btn.disabled = true;
    const url = editId ? `/admin/branches/${editId}` : '/admin/branches';
    const method = editId ? 'patch' : 'post';
    
    //LLAMADA DIRECTA UN FETCH PARA MANEJAR MULTIPART/FORM-DATA CORRECTAMENTE SI EL WRAPPER API.JS NO LO HACE
    // PERO API.JS PARECE SOPORTAR BODY INSTANCEOF FORMDATA
    const res = await api[method](url, formData);
    
    if (res && res.ok) {
        showToast(editId ? 'Sucursal actualizada.' : 'Sucursal creada exitosamente.');
        if (window.closeModal) window.closeModal('modal-add-branch');
        event.target.reset();
        document.getElementById('branch-logo-preview').querySelector('img').src = '/static/images/logo.png';
        document.getElementById('branch-id-edit').value = '';
        document.getElementById('branch-logo-clear').value = 'false';
        document.getElementById('btn-clear-logo').style.display = 'none';
        loadBranches();
    } else {
        showToast(`Error: ${res?.error || 'Desconocido'}`);
    }
    btn.disabled = false;
}

export async function deleteBranch(id) {
    if (!await showConfirm('Eliminar Sucursal', '¿Estás seguro de eliminar esta sucursal? Esto no afectará los registros históricos pero impedirá nuevas operaciones en ella.')) return;
    
    const res = await api.delete(`/admin/branches/${id}`);
    if (res && res.ok) {
        showToast('Sucursal eliminada.');
        loadBranches();
    } else {
        showToast(res?.error || 'Error al eliminar sucursal');
    }
}

export function openPasswordModal(userId, userName) {
    const elId = document.getElementById('admin-pass-userid');
    const elName = document.getElementById('admin-pass-username');
    if (elId) elId.value = userId;
    if (elName) elName.innerText = userName;
    if (window.openModal) window.openModal('modal-change-password-admin');
}

export async function handleAdminChangePassword(event) {
    event.preventDefault();
    const userId = document.getElementById('admin-pass-userid').value;
    const newPassword = document.getElementById('admin-new-password').value;
    const btn = event.target.querySelector('button[type="submit"]');

    btn.disabled = true;
    const res = await api.post(`/admin/users/${userId}/password`, { new_password: newPassword });
    if (res && res.ok) {
        showToast('Contraseña actualizada.');
        if (window.closeModal) window.closeModal('modal-change-password-admin');
        event.target.reset();
    } else {
        showToast(res?.error || 'Error al cambiar contraseña');
    }
    btn.disabled = false;
}

export function openEditUserModal(userId) {
    const u = allUsersData.find(x => x.id === userId);
    if (!u) return;

    document.getElementById('edit-user-id').value = u.id;
    document.getElementById('edit-user-nombre').value = u.nombre;
    document.getElementById('edit-user-apellido').value = u.apellido;
    document.getElementById('edit-user-email').value = u.email;
    document.getElementById('edit-user-dni').value = u.dni;
    document.getElementById('edit-user-tel').value = u.telefono || '';
    
    const roleSelect = document.getElementById('edit-user-rol');
    const myRol = localStorage.getItem('rol');
    const mySucursal = localStorage.getItem('sucursal') || '';

    if (myRol === 'local_admin') {
        if (u.rol === 'user') {
            //SI ES UN CLIENTE, EL ADMIN LOCAL NO PUEDE CAMBIARLE EL ROL
            roleSelect.innerHTML = `<option value="user" style="background: #111;">Cliente</option>`;
            roleSelect.disabled = true;
        } else {
            // RESTRICCION PARA ADMIN LOCAL CON PERSONAL
            roleSelect.innerHTML = `
                <option value="staff" style="background: #111;">Empleado</option>
                <option value="local_admin" style="background: #111;">Administrador de Sucursal</option>
            `;
            roleSelect.disabled = false;
        }
        
        const branchSelect = document.getElementById('edit-user-sucursal');
        if (branchSelect) {
            branchSelect.innerHTML = `<option value="${mySucursal}">${mySucursal.toUpperCase()}</option>`;
            branchSelect.value = mySucursal;
            branchSelect.disabled = true;
        }
    } else {
        //ADMIN GLOBAL
        roleSelect.disabled = false;
        roleSelect.innerHTML = `
            <option value="user" style="background: #111;">Cliente</option>
            <option value="staff" style="background: #111;">Empleado</option>
            <option value="local_admin" style="background: #111;">Administrador de Sucursal</option>
            <option value="admin" style="background: #111;">Administrador General</option>
        `;
    }

    roleSelect.value = u.rol;
    toggleEditBranchSelection();
    
    if (u.sucursal) {
        const branchSelect = document.getElementById('edit-user-sucursal');
        if (branchSelect) branchSelect.value = u.sucursal;
    }

    if (window.openModal) window.openModal('modal-edit-user');
}

export function toggleEditBranchSelection() {
    const rol = document.getElementById('edit-user-rol').value;
    const branchRow = document.getElementById('edit-branch-selection-row');
    const userRol = localStorage.getItem('rol');

    if (branchRow) {
        branchRow.style.display = (rol === 'staff' || rol === 'local_admin') ? 'block' : 'none';
    }
}

export async function handleAdminEditUser(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const userId = document.getElementById('edit-user-id').value;
    const rol = document.getElementById('edit-user-rol').value;
    const sucursal = (rol === 'staff' || rol === 'local_admin') ? document.getElementById('edit-user-sucursal').value : null;

    const payload = {
        nombre: document.getElementById('edit-user-nombre').value,
        apellido: document.getElementById('edit-user-apellido').value,
        email: document.getElementById('edit-user-email').value,
        dni: document.getElementById('edit-user-dni').value,
        telefono: document.getElementById('edit-user-tel').value,
        rol: rol,
        sucursal: sucursal
    };

    btn.disabled = true;
    const res = await api.patch(`/admin/users/${userId}`, payload);
    if (res && res.ok) {
        showToast('Información de usuario actualizada.');
        if (window.closeModal) window.closeModal('modal-edit-user');
        if (window.loadUsers) window.loadUsers(); 
    } else {
        showToast(`Error: ${res?.error || 'Desconocido'}`);
    }
    btn.disabled = false;
}

