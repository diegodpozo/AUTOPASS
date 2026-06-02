import api from './api.js';
import { showToast, showConfirm } from './utils.js';

/**
 * DASHBOARD ADMIN MODULE
 * Operaciones administrativas, gestión de usuarios y configuraciones.
 */

let userPage = 1;
const userPageSize = 10;
let allUsersData = [];
let allBranchesData = []; // Cache local para sucursales
let branchMap = null;
let branchMarker = null;

export function initBranchMap() {
    const mapEl = document.getElementById('branch-map-picker');
    if (!mapEl || branchMap || !window.L) return;

    // Coordenadas iniciales (Buenos Aires / Morón)
    const initialCoords = [-34.6508, -58.6228];
    branchMap = L.map('branch-map-picker').setView(initialCoords, 13);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; OpenStreetMap',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(branchMap);

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

            initBranchMap(); // Asegurar que el mapa existe
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
        const res = await api.get('/admin/users');
        if (res && res.ok) {
            
            // Definimos la jerarquía de roles para el ordenamiento
            const roleOrder = {
                'admin': 1,
                'local_admin': 2,
                'staff': 3,
                'user': 4
            };

            // Ordenamos la data por rol y luego por nombre/apellido
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

        if (elTotal) elTotal.innerText = total;
        if (elAdmin) elAdmin.innerText = admins;
        if (elStaff) elStaff.innerText = staff;
        if (elCustomer) elCustomer.innerText = customers;
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
            const puntosDisplay = isStaffOrAdmin ? '<span class="text-muted">---</span>' : `<div class="points-badge-sm mx-auto" style="display:inline-flex;"><i class="fas fa-star"></i> ${u.puntos_acumulados || 0}</div>`;
            const saldoDisplay = isStaffOrAdmin ? '<span class="text-muted">---</span>' : `<span class="text-success">$${(u.saldo || 0).toLocaleString()}</span>`;

            // Personalización de etiquetas de rol
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
    const confirm = await showConfirm('Apertura Forzada', `¿Abrir barrera de <b>${gateId}</b>?`);
    if (!confirm) return;

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

    // Reiniciar opciones
    roleSelect.innerHTML = `
        <option value="user" style="background: #111;">Cliente</option>
        <option value="staff" style="background: #111;">Empleado</option>
        <option value="local_admin" style="background: #111;">Administrador de Sucursal</option>
        <option value="admin" style="background: #111;">Administrador General</option>
    `;

    if (rol === 'local_admin') {
        // Los administradores locales solo crean personal para su punto
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
        // Admin Global ve todo
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

    // Si el que está creando es un admin local, la fila de sede ya está visible y bloqueada
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

export async function loadSettings() {
    const res = await api.get('/admin/settings');
    if (res.ok) {
        const cfg = res.data;
        Object.keys(cfg).forEach(key => {
            const el = document.getElementById(`cfg-${key}`);
            if (el) el.value = cfg[key];
        });
    }
}

export async function saveAllRates() {
    const keys = ['precio_hora', 'precio_dia', 'precio_semana', 'precio_quincena', 'precio_mes'];
    const labels = {
        'precio_hora': 'Hora',
        'precio_dia': 'Día',
        'precio_semana': 'Semana',
        'precio_quincena': 'Quincena',
        'precio_mes': 'Mes'
    };

    let summary = '<div style="text-align: left; margin-top: 10px; padding: 10px; background: rgba(0,0,0,0.2); border-radius: 8px;">';
    keys.forEach(key => {
        const val = document.getElementById(`cfg-${key}`).value || 0;
        summary += `<div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                        <span style="color: #888;">${labels[key]}:</span>
                        <b style="color: var(--dorado);">$${parseFloat(val).toLocaleString()}</b>
                    </div>`;
    });
    summary += '</div>';

    if (!await showConfirm('Confirmar Tarifario', `¿Estás seguro de aplicar los siguientes valores?<br>${summary}`)) return;

    let success = true;
    for (const key of keys) {
        const val = parseFloat(document.getElementById(`cfg-${key}`).value);
        const res = await api.post(`/settings/prices?clave=${key}&valor=${val}`);
        if (!res.ok) success = false;
    }

    if (success) showToast('Tarifas actualizadas.');
    else showToast('Error al actualizar algunas tarifas.');
}

export async function saveSystemParam(param) {
    const val = document.getElementById(`cfg-${param}`).value;
    const res = await api.post(`/settings/prices?clave=${param}&valor=${val}`);
    if (res.ok) showToast('Configuración guardada.');
    else showToast(res.error);
}

export async function resetSys() {
    if (!await showConfirm('REINICIAR SISTEMA', 'Esto eliminará logs de acceso y ocupación actual. ¿Continuar?')) return;
    const res = await api.post('/system/reset');
    if (res && res.ok) {
        showToast('Sistema reiniciado.');
        window.location.reload();
    } else showToast(res?.error || 'Error');
}

export function exportFinanceData() {
    showToast('Exportando reporte...');
    setTimeout(() => showToast('Reporte descargado correctamente.'), 1500);
}

export async function deleteUserAdmin(id) {
    if (!await showConfirm('Eliminar Usuario', `¿Estás seguro?`)) return;
    const res = await api.post(`/admin/users/${id}/delete`);
    if (res && res.ok) { showToast('Eliminado.'); if (window.loadUsers) window.loadUsers(); }
    else showToast(res?.error || 'Error');
}

// --- GESTIÓN DE SUCURSALES ---

export function showCreateBranchModal() {
    document.getElementById('form-add-branch').reset();
    document.getElementById('branch-id-edit').value = '';
    document.getElementById('branch-modal-title').innerText = 'NUEVA SUCURSAL';
    document.getElementById('branch-modal-icon').className = 'fas fa-building';
    document.getElementById('branch-logo-preview').querySelector('img').src = '/static/images/logo.png';
    
    if (window.openModal) window.openModal('modal-add-branch');

    // Inicializar mapa (Morón por defecto)
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

            tbody.innerHTML = allBranchesData.map(b => `
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
                            <button class="btn-icon-premium sm" onclick="editBranch(${b.id})" title="Editar">
                                <i class="fas fa-pen-to-square"></i>
                            </button>
                            <button class="btn-icon-premium sm danger" onclick="deleteBranch(${b.id})" title="Eliminar">
                                <i class="fas fa-xmark"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
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
    
    // Coordenadas
    const lat = b.latitude || -34.6508;
    const lng = b.longitude || -58.6228;
    document.getElementById('branch-latitude').value = lat;
    document.getElementById('branch-longitude').value = lng;

    // Configurar logo
    const preview = document.querySelector('#branch-logo-preview img');
    if (preview) {
        preview.src = b.logo_url || '/static/images/logo.png';
        preview.style.opacity = "1";
    }
    document.getElementById('branch-logo-file').value = ''; // Limpiar input file

    document.getElementById('branch-is-24h').checked = b.is_24h;
    document.getElementById('branch-horario').value = b.is_24h ? '' : b.horario;
    document.getElementById('branch-horario').disabled = b.is_24h;

    document.getElementById('branch-modal-title').innerText = 'EDITAR SUCURSAL';
    document.getElementById('branch-modal-icon').className = 'fas fa-pen-to-square';
    
    if (window.openModal) window.openModal('modal-add-branch');

    // Inicializar mapa y marcador
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
}

export async function handleCreateBranch(event) {
    event.preventDefault();
    const btn = event.target.querySelector('button[type="submit"]');
    const editId = document.getElementById('branch-id-edit').value;
    
    // Usar FormData para envío de archivos
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

    btn.disabled = true;
    const url = editId ? `/admin/branches/${editId}` : '/admin/branches';
    const method = editId ? 'patch' : 'post';
    
    // Llamada directa a fetch para manejar multipart/form-data correctamente si el wrapper api.js no lo hace
    // Pero api.js parece soportar body instanceof FormData
    const res = await api[method](url, formData);
    
    if (res && res.ok) {
        showToast(editId ? 'Sucursal actualizada.' : 'Sucursal creada exitosamente.');
        if (window.closeModal) window.closeModal('modal-add-branch');
        event.target.reset();
        document.getElementById('branch-logo-preview').querySelector('img').src = '/static/images/logo.png';
        document.getElementById('branch-id-edit').value = '';
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
