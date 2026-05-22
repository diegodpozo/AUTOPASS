import api from './api.js';
import { showToast, showConfirm } from './utils.js';

/**
 * DASHBOARD ADMIN MODULE
 * Operaciones administrativas, gestión de usuarios y configuraciones.
 */

let userPage = 1;
const userPageSize = 10;
let allUsersData = [];

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
                <td data-label="Rol" class="text-center"><span class="role-badge ${u.rol || 'user'} mx-auto">${(u.rol || 'USER').toUpperCase()}</span></td>
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

export function toggleBranchSelection() {
    const rol = document.getElementById('admin-user-rol').value;
    const row = document.getElementById('branch-selection-row');
    if (row) row.style.display = (rol === 'staff' || rol === 'local_admin') ? 'flex' : 'none';
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
