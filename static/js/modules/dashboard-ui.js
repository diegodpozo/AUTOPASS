import api from './api.js';
import { normalizeSystemName, showToast, showConfirm } from './utils.js';
import { getVirtualNow } from './virtual-time.js';

/**
 * PANEL UI MODULO
 * GESTION DE ELEMENTOS VISUALES, NAVEGACION Y SALUD DEL SISTEMA.
 */

export function initClock() {
    const clockEl = document.getElementById('clock');
    if (!clockEl) return;
    
    const update = () => {
        clockEl.innerText = getVirtualNow().toLocaleTimeString('es-AR', { hour12: false });
    };
    
    update();
    setInterval(update, 1000);
}

export async function checkSystemHealth() {
    const mainDot = document.getElementById('health-db');
    const res = await api.get('/system/health');
    const sucursalRaw = localStorage.getItem('sucursal') || '';
    
    if (res && res.ok) {
        const data = res.data;
        if (mainDot) {
            const isOnline = data.database === 'ONLINE' && data.api === 'ONLINE';
            mainDot.style.background = isOnline ? '#10b981' : '#ef4444';
            if (isOnline) mainDot.classList.add('online');
            else mainDot.classList.remove('online');
        }

        updateHealthNode('node-db', data.database === 'ONLINE');
        updateHealthNode('node-api', data.api === 'ONLINE');
        
        // AISLAMIENTO: BUSCAR ESTADOS DE LA SUCURSAL ACTUAL (NORMALIZADO)
        const sucursal = normalizeSystemName(sucursalRaw);
        const entryKey = sucursal ? `${sucursal}_ENTRADA` : 'ENTRADA_PRINCIPAL';
        const exitKey = sucursal ? `${sucursal}_SALIDA` : 'SALIDA_PRINCIPAL';

        const entryOnline = data.alpr?.[entryKey] === 'ONLINE';
        const exitOnline = data.alpr?.[exitKey] === 'ONLINE';

        updateHealthNode('node-ocr-entry', entryOnline);
        updateHealthNode('node-ocr-exit', exitOnline);

        // ACTUALIZAR INDICADORES "LIVE" SOBRE LOS CUADROS DE VIDEO
        const indEntry = document.getElementById('indicator-entry');
        const indExit = document.getElementById('indicator-exit');
        if (indEntry) indEntry.className = entryOnline ? 'live-indicator online' : 'live-indicator';
        if (indExit) indExit.className = exitOnline ? 'live-indicator online' : 'live-indicator';
    }
}

/**
 * ACTUALIZA VISUALMENTE UN NODO DE SALUD (DOT + TEXTO).
 */
function updateHealthNode(id, isOnline) {
    const node = document.getElementById(id);
    if (!node) return;
    
    const dot = node.querySelector('.health-dot');
    const label = node.querySelector('.health-label');
    
    if (dot) {
        dot.style.background = isOnline ? '#10b981' : '#ef4444';
        if (isOnline) dot.classList.add('online');
        else dot.classList.remove('online');
    }
    
    if (label) {
        label.innerText = isOnline ? 'ONLINE' : 'OFFLINE';
        label.style.color = isOnline ? '#10b981' : '#ef4444';
    }
}

let videoSockets = { entry: null, exit: null };

export async function initVideoStreams() {
    const sucursalRaw = localStorage.getItem('sucursal') || '';
    const token = localStorage.getItem('token');
    const rol = localStorage.getItem('rol');
    
    // Normalizar la sucursal
    const sucursal = normalizeSystemName(sucursalRaw);
    
    const res = await api.get('/system/cameras');
    if (res.ok) {
        let cameras = res.data;
        if (rol !== 'admin' && sucursal) {
            cameras = cameras.filter(c => normalizeSystemName(c.sucursal) === sucursal);
        }
        
        const firstEntry = cameras.find(c => c.tipo === 'ENTRADA' && c.is_running);
        const firstExit = cameras.find(c => c.tipo === 'SALIDA' && c.is_running);
        
        if (firstEntry) {
            const normSuc = normalizeSystemName(firstEntry.sucursal || '');
            const procId = `${normSuc}_ENTRADA_${firstEntry.id}`.toUpperCase();
            setupSocket('entry', procId, token);
        } else {
            const entryId = sucursal ? `${sucursal}_ENTRADA` : 'ENTRADA_PRINCIPAL';
            setupSocket('entry', entryId, token);
        }
        
        if (firstExit) {
            const normSuc = normalizeSystemName(firstExit.sucursal || '');
            const procId = `${normSuc}_SALIDA_${firstExit.id}`.toUpperCase();
            setupSocket('exit', procId, token);
        } else {
            const exitId = sucursal ? `${sucursal}_SALIDA` : 'SALIDA_PRINCIPAL';
            setupSocket('exit', exitId, token);
        }
    } else {
        const entryId = sucursal ? `${sucursal}_ENTRADA` : 'ENTRADA_PRINCIPAL';
        const exitId = sucursal ? `${sucursal}_SALIDA` : 'SALIDA_PRINCIPAL';
        setupSocket('entry', entryId, token);
        setupSocket('exit', exitId, token);
    }
}

function setupSocket(type, cameraId, token) {
    if (videoSockets[type]) {
        videoSockets[type].close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/v1/system/ws/video/${cameraId}?token=${token}`;
    
    if (!token) {
        console.warn(`[WS] Abortando conexión para ${cameraId}: Token no encontrado.`);
        return;
    }

    const socket = new WebSocket(wsUrl);
    videoSockets[type] = socket;

    socket.onmessage = (event) => {
        const img = document.getElementById(`cam-${type}`);
        if (img) {
            img.src = `data:image/jpeg;base64,${event.data}`;
            if (img.style.opacity === '0') {
                img.style.opacity = '1';
            }
        }
    };

    socket.onclose = () => {
        const tab = document.getElementById('tab-live');
        if (tab && tab.classList.contains('active')) {
            setTimeout(() => {
                 if (videoSockets[type] === socket) {
                     setupSocket(type, cameraId, token);
                 }
            }, 5000);
        }
    };

    socket.onerror = (err) => {
        console.error(`WS Error [${cameraId}]:`, err);
    };
}

export function switchTab(tabId, element) {
    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    element.classList.add('active');
    
    document.querySelectorAll('.tab-view').forEach(view => view.classList.remove('active'));
    const activeTab = document.getElementById(`tab-${tabId}`);
    if (activeTab) activeTab.classList.add('active');
    
    const titleEl = document.getElementById('view-title');
    if (titleEl) {
        const titles = {
            'live': 'Monitoreo',
            'admin-reservations': 'Reservas',
            'users': 'Gestión de Usuarios',
            'finance': 'Reporte Financiero',
            'promotions': 'Promociones',
            'branches': 'Gestión de Sucursales',
            'settings': 'Configuración'
        };
        titleEl.innerText = titles[tabId] || 'Dashboard';
    }
    
    localStorage.setItem('activeAdminTab', tabId);
    if (window.loadTabData) window.loadTabData(tabId);

    if (tabId === 'settings') {
        if (!window._diagInterval) {
            window._diagInterval = setInterval(() => {
                if (localStorage.getItem('activeAdminTab') === 'settings' && window.refreshSystemDiagnostics) {
                    window.refreshSystemDiagnostics();
                }
            }, 5000);
        }
    }

    if (tabId === 'live') {
        initVideoStreams();
    } else {
        Object.keys(videoSockets).forEach(k => {
            if (videoSockets[k]) {
                videoSockets[k].close();
                videoSockets[k] = null;
            }
        });
    }

    if (window.innerWidth <= 768) {
        closeMobileNav();
    }
}

export function toggleMobileNav() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar && overlay) {
        sidebar.classList.toggle('mobile-open');
        overlay.classList.toggle('active');
    }
}

export function closeMobileNav() {
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.getElementById('sidebar-overlay');
    if (sidebar && overlay) {
        sidebar.classList.remove('mobile-open');
        overlay.classList.remove('active');
    }
}

export function toggleSidebar() {
    const sidebar = document.querySelector('.sidebar');
    const layout = document.querySelector('.layout-with-sidebar');
    if (sidebar && layout) {
        const isCollapsed = sidebar.classList.toggle('collapsed');
        layout.classList.toggle('collapsed');
        
        const icon = sidebar.querySelector('.sidebar-toggle i');
        if (icon) {
            icon.className = isCollapsed ? 'fas fa-chevron-right' : 'fas fa-chevron-left';
        }
        localStorage.setItem('sidebarCollapsed', isCollapsed);
    }
}

export function toggleCollapsible(contentId, chevronId, maxHeight = '400px') {
    const content = document.getElementById(contentId);
    const chevron = document.getElementById(chevronId);
    if (!content || !chevron) return;

    content.classList.toggle('expanded');
    const isExpanded = content.classList.contains('expanded');

    if (isExpanded) {
        content.style.maxHeight = maxHeight;
        chevron.style.transform = 'rotate(180deg)';
    } else {
        content.style.maxHeight = '0px';
        chevron.style.transform = 'rotate(0deg)';
    }
}

/**
 * GESTION DE CAMARAS (V9.2.0 - REFACTORIZACIÓN DINÁMICA MULTI-CÁMARA)
 */

export async function loadCameraSettings() {
    const listEl = document.getElementById('camera-settings-list');
    if (!listEl) return;
    listEl.innerHTML = `<tr><td colspan="5" class="text-center py-20"><i class="fas fa-spinner fa-spin text-dorado"></i> Cargando dispositivos...</td></tr>`;

    const res = await api.get('/system/cameras');
    if (res.ok) {
        renderCameraSettingsTable(res.data);
    } else {
        listEl.innerHTML = `<tr><td colspan="5" class="text-center py-20 text-danger">Error al cargar dispositivos: ${res.error || 'Desconocido'}</td></tr>`;
    }
}

export function renderCameraSettingsTable(cameras) {
    const listEl = document.getElementById('camera-settings-list');
    if (!listEl) return;
    
    if (cameras.length === 0) {
        listEl.innerHTML = `<tr><td colspan="5" class="text-center py-20 text-muted">No hay cámaras registradas.</td></tr>`;
        return;
    }
    
    listEl.innerHTML = cameras.map(cam => {
        const badgeClass = cam.is_running ? 'badge-success-light' : 'badge-danger-light';
        const badgeText = cam.is_running ? 'ONLINE' : 'OFFLINE';
        
        return `
            <tr>
                <td class="text-bold">${cam.nombre}</td>
                <td>
                    <span class="badge-status badge-info-light">${cam.tipo}</span>
                </td>
                <td style="font-family: var(--font-mono); font-size: 0.8rem;">${cam.source}</td>
                <td>
                    <span class="badge-status ${badgeClass}" id="settings-cam-badge-${cam.id}">
                        <i class="fas ${cam.is_running ? 'fa-check-circle' : 'fa-times-circle'} mr-5"></i> ${badgeText}
                    </span>
                </td>
                <td>
                    <div style="display: flex; gap: 8px; justify-content: center; align-items: center;">
                        <button class="btn-action-mini ${cam.is_running ? 'danger' : 'success'}" 
                                id="settings-cam-btn-control-${cam.id}"
                                onclick="toggleDynamicCameraService(${cam.id}, '${cam.is_running ? 'stop' : 'start'}')"
                                title="${cam.is_running ? 'Detener Servicio' : 'Iniciar Servicio'}">
                            <i class="fas ${cam.is_running ? 'fa-stop' : 'fa-play'}"></i>
                        </button>
                        <button class="btn-action-mini" 
                                id="settings-cam-btn-edit-${cam.id}"
                                title="Editar Cámara">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="btn-action-mini danger" 
                                onclick="deleteCamera(${cam.id})" 
                                title="Eliminar Cámara">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');

    // Agregar event listeners para evitar inline stringify bugs con objetos
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
    if (nombreInput) nombreInput.value = cam.nombre;

    const tipoSelect = document.getElementById('camera-tipo');
    if (tipoSelect) tipoSelect.value = cam.tipo;

    const sourceInput = document.getElementById('camera-source');
    if (sourceInput) sourceInput.value = cam.source;

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
    const nombre = document.getElementById('camera-nombre').value;
    const tipo = document.getElementById('camera-tipo').value;
    const source = document.getElementById('camera-source').value;
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

