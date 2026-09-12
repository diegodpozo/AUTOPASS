import api from './api.js';
import { normalizeSystemName, formatTimeSeconds } from './utils.js';
import { getVirtualNow } from './virtual-time.js';
import { loadCameraSettings, renderCameraSettingsTable, showCreateCameraModal, showEditCameraModal, handleSaveCameraConfig, deleteCamera, toggleDynamicCameraService } from './dashboard-cameras.js';
import { toggleMobileNav, closeMobileNav } from './ui.js';

export { loadCameraSettings, renderCameraSettingsTable, showCreateCameraModal, showEditCameraModal, handleSaveCameraConfig, deleteCamera, toggleDynamicCameraService };

export function initClock() {
    const clockEl = document.getElementById('clock');
    if (!clockEl) return;
    
    const update = () => {
        clockEl.innerText = formatTimeSeconds(getVirtualNow());
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
        
        const sucursal = normalizeSystemName(sucursalRaw);
        const entryKey = sucursal ? `${sucursal}_ENTRADA` : 'ENTRADA_PRINCIPAL';
        const exitKey = sucursal ? `${sucursal}_SALIDA` : 'SALIDA_PRINCIPAL';

        const entryOnline = data.alpr?.[entryKey] === 'ONLINE';
        const exitOnline = data.alpr?.[exitKey] === 'ONLINE';

        updateHealthNode('node-ocr-entry', entryOnline);
        updateHealthNode('node-ocr-exit', exitOnline);
    }
}

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

export async function initVideoStreams() {
}

export function switchTab(tabId, element) {
    const rol = localStorage.getItem('rol');
    if (rol === 'staff') {
        const restrictedStaff = ['users', 'finance', 'promotions', 'tickets', 'settings', 'branches', 'metricas'];
        if (restrictedStaff.includes(tabId)) {
            tabId = 'live';
            element = document.querySelector(`.nav-item[onclick*="'live'"]`);
        }
    }

    document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
    if (element) {
        element.classList.add('active');
    } else {
        const item = document.querySelector(`.nav-item[onclick*="'${tabId}'"]`);
        if (item) item.classList.add('active');
    }
    
    document.querySelectorAll('.tab-view').forEach(view => {
        view.classList.remove('active');
        view.style.display = 'none';
    });
    const activeTab = document.getElementById(`tab-${tabId}`);
    if (activeTab) {
        activeTab.classList.add('active');
        activeTab.style.display = '';
    }
    
    const titleEl = document.getElementById('view-title');
    if (titleEl) {
        const titles = {
            'live': 'Monitoreo',
            'admin-reservations': 'Reservas',
            'users': 'Gestión de Usuarios',
            'finance': 'Reporte Financiero',
            'metricas': 'Métricas',
            'promotions': 'Promociones',
            'branches': 'Gestión de Sucursales',
            'settings': 'Configuración',
            'tickets': 'Soporte & Tickets'
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
    } else {
        if (window._diagInterval) {
            clearInterval(window._diagInterval);
            window._diagInterval = null;
        }
    }

    if (tabId === 'live') {
        initVideoStreams();
    }

    if (window.innerWidth <= 768) {
        closeMobileNav();
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
