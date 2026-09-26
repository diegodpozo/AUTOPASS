import api from './api.js';
import { showToast, showConfirm, formatNum } from './utils.js';
import { populateBranchSelect } from './dashboard-admin-branches.js';

/**
 * Módulo de Gestión Administrativa de Usuarios (CRUD, Roles, Bloqueo, Contraseñas)
 */

let userPage = 1;
const userPageSize = 10;
let allUsersData = [];

export function getAllUsersData() {
    return allUsersData;
}

export async function loadUsers() {
    try {
        const myRol = localStorage.getItem('rol');
        if (myRol !== 'admin') {
            const adminOption = document.querySelector('#user-filter-rol option[value="admin"]');
            if (adminOption) adminOption.remove();
        }

        const res = await api.get('/admin/users');
        if (res && res.ok) {
            const roleOrder = {
                'admin': 1,
                'local_admin': 2,
                'staff': 3,
                'user': 4
            };

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
            const saldoDisplay = isStaffOrAdmin ? '<span class="text-muted">---</span>' : `<span class="text-success">$${formatNum(u.saldo || 0)}</span>`;

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
                        <span class="user-email-text">${u.email || '---'}</span>
                        ${u.telefono ? `<div class="user-phone-text text-xs text-muted" style="margin-top: 3px;"><i class="fas fa-phone mr-4"></i>${u.telefono}</div>` : ''}
                    </div>
                </td>
                <td data-label="Rol" class="text-center"><span class="role-badge ${u.rol || 'user'} mx-auto">${roleLabel}</span></td>
                <td data-label="Puntos" class="text-center">${puntosDisplay}</td>
                <td data-label="Saldo" class="text-bold text-center">${saldoDisplay}</td>
                <td data-label="Acciones">
                    <div class="flex-row gap-5 user-actions justify-center">
                        <button class="btn--icon sm" onclick="openEditUserModal(${u.id})" title="Editar Información">
                            <i class="fas fa-user-pen"></i>
                        </button>
                        <button class="btn--icon sm" onclick="openPasswordModal(${u.id}, '${u.nombre} ${u.apellido}')" title="Cambiar Contraseña">
                            <i class="fas fa-key"></i>
                        </button>
                        <button class="btn--icon sm" onclick="toggleUserBlock(${u.id}, '${u.nombre}', ${u.is_blocked})" title="${u.is_blocked ? 'Desbloquear' : 'Bloquear'}">
                            <i class="fas ${u.is_blocked ? 'fa-user-check' : 'fa-user-slash'}"></i>
                        </button>
                        <button class="btn--icon sm danger" onclick="deleteUserAdmin(${u.id})" title="Eliminar">
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

export function prevUserPage() { 
    if (userPage > 1) { 
        userPage--; 
        renderUserTable(); 
    } 
}

export function nextUserPage() { 
    const totalPages = Math.ceil(allUsersData.length / userPageSize);
    if (userPage < totalPages) { 
        userPage++; 
        renderUserTable(); 
    } 
}

export async function showCreateUserModal() {
    const rol = localStorage.getItem('rol');
    const sucursal = localStorage.getItem('sucursal') || '';
    
    const roleSelect = document.getElementById('admin-user-rol');
    const branchRow = document.getElementById('branch-selection-row');
    const branchSelect = document.getElementById('admin-user-sucursal');

    if (!roleSelect) return;

    roleSelect.innerHTML = `
        <option value="user" style="background: #111;">Cliente</option>
        <option value="staff" style="background: #111;">Empleado</option>
        <option value="local_admin" style="background: #111;">Administrador de Sucursal</option>
        <option value="admin" style="background: #111;">Administrador General</option>
    `;

    if (rol === 'local_admin') {
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
        if (branchRow) branchRow.style.display = 'none';
        if (branchSelect) {
            branchSelect.innerHTML = '';
            branchSelect.disabled = false;
        }
        roleSelect.value = 'user';
    }

    if (window.openModal) window.openModal('modal-create-user');
}

export async function toggleBranchSelection() {
    const rol = document.getElementById('admin-user-rol').value;
    const branchRow = document.getElementById('branch-selection-row');
    const branchSelect = document.getElementById('admin-user-sucursal');
    const userRol = localStorage.getItem('rol');

    if (userRol === 'local_admin') return;

    if (branchRow) {
        const show = (rol === 'staff' || rol === 'local_admin');
        branchRow.style.display = show ? 'block' : 'none';
        if (show && branchSelect) {
            await populateBranchSelect(branchSelect);
        }
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
        showToast('Usuario creado.', 'success');
        if (window.closeModal) window.closeModal('modal-create-user');
        event.target.reset();
        loadUsers(); 
    } else {
        const errMsg = Array.isArray(res?.error) 
            ? res.error.map(e => `${e.loc?.slice(-1)[0]}: ${e.msg}`).join(' | ')
            : (res?.error || 'Desconocido');
        showToast(`Error: ${errMsg}`, 'error');
    }
    btn.disabled = false;
}

export async function toggleUserBlock(id, nombre, currentlyBlocked) {
    const action = currentlyBlocked ? 'DESBLOQUEAR' : 'BLOQUEAR';
    if (!await showConfirm(`${action} USUARIO`, `¿Estás seguro?`)) return;

    const res = await api.post(`/admin/users/${id}/toggle-block`);
    const type = currentlyBlocked ? 'success' : 'error';
    if (res && res.ok) { 
        showToast(res.data.message, type); 
        loadUsers(); 
    } else {
        showToast(res?.error || 'Error', 'error');
    }
}

export async function deleteUserAdmin(id) {
    if (!await showConfirm('Eliminar Usuario', `¿Estás seguro?`)) return;
    const res = await api.post(`/admin/users/${id}/delete`);
    if (res && res.ok) { 
        showToast('Eliminado.', 'success'); 
        loadUsers(); 
    } else {
        showToast(res?.error || 'Error', 'error');
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
        showToast('Contraseña actualizada.', 'success');
        if (window.closeModal) window.closeModal('modal-change-password-admin');
        event.target.reset();
    } else {
        showToast(res?.error || 'Error al cambiar contraseña', 'error');
    }
    btn.disabled = false;
}

export async function openEditUserModal(userId) {
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
            roleSelect.innerHTML = `<option value="user" style="background: #111;">Cliente</option>`;
            roleSelect.disabled = true;
        } else {
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
        roleSelect.disabled = false;
        roleSelect.innerHTML = `
            <option value="user" style="background: #111;">Cliente</option>
            <option value="staff" style="background: #111;">Empleado</option>
            <option value="local_admin" style="background: #111;">Administrador de Sucursal</option>
            <option value="admin" style="background: #111;">Administrador General</option>
        `;
        const branchSelect = document.getElementById('edit-user-sucursal');
        if (branchSelect) {
            await populateBranchSelect(branchSelect);
        }
    }

    roleSelect.value = u.rol;
    await toggleEditBranchSelection();
    
    if (u.sucursal) {
        const branchSelect = document.getElementById('edit-user-sucursal');
        if (branchSelect) branchSelect.value = u.sucursal;
    }

    if (window.openModal) window.openModal('modal-edit-user');
}

export async function toggleEditBranchSelection() {
    const rol = document.getElementById('edit-user-rol').value;
    const branchRow = document.getElementById('edit-branch-selection-row');
    const branchSelect = document.getElementById('edit-user-sucursal');
    const userRol = localStorage.getItem('rol');

    if (branchRow) {
        const show = (rol === 'staff' || rol === 'local_admin');
        branchRow.style.display = show ? 'block' : 'none';
        if (show && userRol !== 'local_admin' && branchSelect) {
            await populateBranchSelect(branchSelect);
        }
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
        showToast('Información de usuario actualizada.', 'success');
        if (window.closeModal) window.closeModal('modal-edit-user');
        loadUsers(); 
    } else {
        showToast(`Error: ${res?.error || 'Desconocido'}`, 'error');
    }
    btn.disabled = false;
}
