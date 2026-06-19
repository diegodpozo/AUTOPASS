import api from './api.js';
import { normalizeSystemName, showToast } from './utils.js';

/**
 * DASHBOARD UI MODULE
 * Gestión de elementos visuales, navegación y salud del sistema.
 */

export function initClock() {
    const clockEl = document.getElementById('clock');
    if (!clockEl) return;
    
    const update = () => {
        const now = new Date();
        clockEl.innerText = now.toLocaleTimeString('es-AR', { hour12: false });
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
        
        // Aislamiento: Buscar estados de la sucursal actual (Normalizado)
        const sucursal = normalizeSystemName(sucursalRaw);
        const entryKey = sucursal ? `${sucursal}_ENTRADA` : 'ENTRADA_PRINCIPAL';
        const exitKey = sucursal ? `${sucursal}_SALIDA` : 'SALIDA_PRINCIPAL';

        const entryOnline = data.alpr?.[entryKey] === 'ONLINE';
        const exitOnline = data.alpr?.[exitKey] === 'ONLINE';

        updateHealthNode('node-ocr-entry', entryOnline);
        updateHealthNode('node-ocr-exit', exitOnline);

        // Actualizar indicadores "LIVE" sobre los cuadros de video
        const indEntry = document.getElementById('indicator-entry');
        const indExit = document.getElementById('indicator-exit');
        if (indEntry) indEntry.className = entryOnline ? 'live-indicator online' : 'live-indicator';
        if (indExit) indExit.className = exitOnline ? 'live-indicator online' : 'live-indicator';
    }
}

/**
 * Actualiza visualmente un nodo de salud (dot + texto).
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

export function initVideoStreams() {
    const sucursalRaw = localStorage.getItem('sucursal') || '';
    const token = localStorage.getItem('token');
    
    // Normalizar la sucursal para armar los IDs de cámara
    const sucursal = normalizeSystemName(sucursalRaw);
    
    // Si no hay sucursal (Admin Global), usamos los IDs principales
    const entryId = sucursal ? `${sucursal}_ENTRADA` : 'ENTRADA_PRINCIPAL';
    const exitId = sucursal ? `${sucursal}_SALIDA` : 'SALIDA_PRINCIPAL';

    setupSocket('entry', entryId, token);
    setupSocket('exit', exitId, token);
}

function setupSocket(type, cameraId, token) {
    if (videoSockets[type]) {
        videoSockets[type].close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/v1/system/ws/video/${cameraId}?token=${token}`;
    
    // Si no hay token, no intentamos conectar para evitar entrar en modo "sender" (ALPR Node)
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
            // Si el onerror del HTML la ocultó (opacity:0), la volvemos a mostrar
            if (img.style.opacity === '0') {
                img.style.opacity = '1';
            }
        }
    };

    socket.onclose = () => {
        const tab = document.getElementById('tab-live');
        if (tab && tab.classList.contains('active')) {
            setTimeout(() => {
                 // Solo reintentar si el socket sigue siendo el actual
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

    // Bucle de Diagnóstico para la pestaña de Configuración
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
 * GESTIÓN DE CÁMARAS (V8.9.5 - MIGRADO A SETTINGS)
 */

export async function loadCameraSettings() {
    const sucursalRaw = localStorage.getItem('sucursal') || '';
    const sucursal = normalizeSystemName(sucursalRaw);
    
    const gates = ['ENTRADA', 'SALIDA'];
    
    for (const type of gates) {
        const gateId = sucursal ? `${sucursal}_${type}` : `${type}_PRINCIPAL`;
        const res = await api.get(`/system/camera-config/${gateId}`);
        
        if (res.ok) {
            const typeLower = type.toLowerCase();
            const sourceInput = document.getElementById(`cam-source-${typeLower}`);
            if (sourceInput) {
                sourceInput.value = res.data.source;
                // Si ya tiene valor, bloqueamos el input y ponemos icono de editar
                if (res.data.source) {
                    sourceInput.disabled = true;
                    const btn = document.getElementById(`btn-save-cam-${typeLower}`);
                    if (btn) btn.innerHTML = '<i class="fas fa-pen" style="font-size: 0.9rem;"></i>';
                }
            }
            updateCameraServiceSettingsUI(type, gateId, res.data.is_running);
        }
    }
}

export function updateCameraServiceSettingsUI(type, gateId, isRunning) {
    const typeLower = type.toLowerCase();
    const badgeEl = document.getElementById(`cam-status-${typeLower}-badge`);
    const actionsEl = document.getElementById(`cam-actions-${typeLower}`);
    
    if (!badgeEl || !actionsEl) return;
    
    if (isRunning) {
        badgeEl.innerHTML = `<span class="badge-status badge-success-light"><i class="fas fa-check-circle mr-5"></i> ONLINE</span>`;
        actionsEl.innerHTML = `
            <button class="btn btn-outline danger sm" onclick="toggleCameraServiceSettings('${type}', '${gateId}', 'stop')" title="Detener Servicio" style="padding: 5px 12px; font-size: 0.65rem;">
                <i class="fas fa-stop"></i>
            </button>
        `;
    } else {
        badgeEl.innerHTML = `<span class="badge-status badge-danger-light"><i class="fas fa-times-circle mr-5"></i> OFFLINE</span>`;
        actionsEl.innerHTML = `
            <button class="btn btn-outline success sm" onclick="toggleCameraServiceSettings('${type}', '${gateId}', 'start')" title="Iniciar Servicio" style="padding: 5px 12px; font-size: 0.65rem;">
                <i class="fas fa-play"></i>
            </button>
        `;
    }
}

export async function toggleCameraServiceSettings(type, gateId, action) {
    const res = await api.post(`/system/camera-service/${gateId}/${action}`);
    if (res.ok) {
        showToast(res.data.message, 'success');
        updateCameraServiceSettingsUI(type, gateId, action === 'start');
        if (action === 'start') {
            initVideoStreams(); // Refrescar feeds en la otra pestaña
        }
    } else {
        showToast(res.error || 'Error en el servicio', 'error');
    }
}

export async function saveCameraSettings(type, btn) {
    const typeLower = type.toLowerCase();
    const input = document.getElementById(`cam-source-${typeLower}`);
    
    // Si el input está bloqueado, lo desbloqueamos para editar
    if (input && input.disabled) {
        input.disabled = false;
        input.focus();
        if (btn) btn.innerHTML = '<i class="fas fa-check" style="font-size: 1.1rem;"></i>';
        return;
    }

    const sucursalRaw = localStorage.getItem('sucursal') || '';
    const sucursal = normalizeSystemName(sucursalRaw);
    const gateId = sucursal ? `${sucursal}_${type}` : `${type}_PRINCIPAL`;

    const source = input.value;

    const res = await api.post('/system/camera-config', { gate_id: gateId, source: source });
    if (res.ok) {
        showToast(`Configuración de ${type} guardada`, 'success');
        // Bloqueamos el input y cambiamos el icono a Lápiz (Editar)
        if (input) input.disabled = true;
        if (btn) btn.innerHTML = '<i class="fas fa-pen" style="font-size: 0.9rem;"></i>';
        initVideoStreams();
    } else {
        showToast(res.error || 'Error al guardar', 'error');
    }
}

/**
 * UI: TOGGLE LINK CAMARA (v9.1.5)
 */
export function toggleCameraLink(type, show) {
    const typeLower = type.toLowerCase();
    const btnLink = document.getElementById(`btn-link-${typeLower}`);
    const wrapper = document.getElementById(`wrapper-link-${typeLower}`);

    if (btnLink && wrapper) {
        btnLink.style.display = show ? 'none' : 'flex';
        wrapper.style.display = show ? 'flex' : 'none';
    }
}
/**
 * LEGACY - GESTIÓN DE CÁMARAS (CONFIGURACIÓN Y SERVICIO)
 */

export async function openCameraConfig(type) {
    const sucursalRaw = localStorage.getItem('sucursal') || '';
    const sucursal = normalizeSystemName(sucursalRaw);
    const gateId = sucursal ? `${sucursal}_${type}` : `${type}_PRINCIPAL`;
    
    const gateInput = document.getElementById('cam-config-gate');
    const titleEl = document.getElementById('cam-config-title');
    if (gateInput) gateInput.value = gateId;
    if (titleEl) titleEl.innerText = `CONFIGURAR ${type}`;
    
    const res = await api.get(`/system/camera-config/${gateId}`);
    if (res.ok) {
        const sourceInput = document.getElementById('cam-config-source');
        if (sourceInput) sourceInput.value = res.data.source;
        updateCameraServiceUI(gateId, res.data.is_running);
    }
    
    if (window.openModal) window.openModal('modal-cam-config');
}

export function updateCameraServiceUI(gateId, isRunning) {
    const statusEl = document.getElementById('cam-service-status');
    const actionsEl = document.getElementById('cam-service-actions');
    if (!statusEl || !actionsEl) return;
    
    if (isRunning) {
        statusEl.innerText = 'EJECUTÁNDOSE';
        statusEl.style.color = '#10b981';
        actionsEl.innerHTML = `
            <button type="button" class="btn-icon-premium sm danger" onclick="toggleCameraService('${gateId}', 'stop')" title="Detener Servicio">
                <i class="fas fa-stop"></i>
            </button>
        `;
    } else {
        statusEl.innerText = 'DETENIDO';
        statusEl.style.color = '#ef4444';
        actionsEl.innerHTML = `
            <button type="button" class="btn-icon-premium sm secondary" onclick="toggleCameraService('${gateId}', 'start')" title="Iniciar Servicio">
                <i class="fas fa-play" style="color: #10b981;"></i>
            </button>
        `;
    }
}

export async function toggleCameraService(gateId, action) {
    const statusEl = document.getElementById('cam-service-status');
    if (statusEl) statusEl.innerText = action === 'start' ? 'INICIANDO...' : 'DETENIENDO...';
    
    const res = await api.post(`/system/camera-service/${gateId}/${action}`);
    if (res.ok) {
        if (window.showToast) window.showToast(res.data.message, 'success');
        updateCameraServiceUI(gateId, action === 'start');
        
        // Si iniciamos, cerramos el modal para ver el feed
        if (action === 'start') {
            setTimeout(() => {
                if (window.closeModal) window.closeModal('modal-cam-config');
                initVideoStreams();
            }, 1000);
        }
    } else {
        if (window.showToast) window.showToast(res.error || 'Error en el servicio', 'error');
        // Refrescar estado real por si hubo error
        const statusRes = await api.get(`/system/camera-config/${gateId}`);
        if (statusRes.ok) updateCameraServiceUI(gateId, statusRes.data.is_running);
    }
}

export async function handleSaveCamConfig(event) {
    event.preventDefault();
    const gateId = document.getElementById('cam-config-gate').value;
    const source = document.getElementById('cam-config-source').value;
    
    const res = await api.post('/system/camera-config', { gate_id: gateId, source: source });
    if (res.ok) {
        if (window.showToast) window.showToast('Configuración guardada', 'success');
        if (window.closeModal) window.closeModal('modal-cam-config');
        // Refrescar streams por si cambió la IP
        initVideoStreams();
    } else {
        if (window.showToast) window.showToast(res.error || 'Error al guardar', 'error');
    }
}
