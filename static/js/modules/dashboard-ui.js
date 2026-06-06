import api from './api.js';
import { normalizeSystemName } from './utils.js';

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

        updateHealthNode('node-ocr-entry', data.alpr?.[entryKey] === 'ONLINE');
        updateHealthNode('node-ocr-exit', data.alpr?.[exitKey] === 'ONLINE');
    }
}

let videoSockets = { entry: null, exit: null };

export function initVideoStreams() {
    const rol = localStorage.getItem('rol');
    const sucursalRaw = localStorage.getItem('sucursal') || '';
    const token = localStorage.getItem('token');
    
    // Si es admin global, no necesita ver las cámaras (según requerimiento)
    if (rol === 'admin') {
        console.log("[WS] El Administrador Global no tiene acceso a streaming de video local.");
        return;
    }

    const sucursal = normalizeSystemName(sucursalRaw);
    if (!sucursal) {
        console.warn("[WS] No se pudo determinar la sede para el video.");
        return;
    }

    console.log(`[*] Iniciando streaming operativo para sede: ${sucursal}`);
    
    const entryId = `${sucursal}_ENTRADA`;
    const exitId = `${sucursal}_SALIDA`;

    setupSocket('entry', entryId, token);
    setupSocket('exit', exitId, token);
}

function setupSocket(type, cameraId, token) {
    if (videoSockets[type]) {
        videoSockets[type].close();
    }

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/v1/system/ws/video/${cameraId}?token=${token}`;
    
    console.log(`[WS] Conectando ${type}: ${wsUrl}`);
    
    const socket = new WebSocket(wsUrl);
    videoSockets[type] = socket;

    socket.onopen = () => console.log(`[WS] ✅ Conectado: ${cameraId}`);

    socket.onmessage = (event) => {
        const img = document.getElementById(`cam-${type}`);
        if (img) {
            img.src = `data:image/jpeg;base64,${event.data}`;
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
