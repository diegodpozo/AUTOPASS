import api from './api.js';
import { formatPlate, normalizeSystemName } from './utils.js';

/**
 * Módulo de Monitoreo CCTV DVR Live (Surveillance Pro)
 */

let camerasList = [];
let activeWebSockets = {};
let wsGeneral = null;
let clockInterval = null;
let durationInterval = null;

export function initMonitoreoLive() {
    const token = localStorage.getItem('token');
    const rol = localStorage.getItem('rol');
    if (!token || !['admin', 'local_admin', 'staff'].includes(rol)) {
        window.location.href = '/';
        return;
    }

    initClock();
    startDurationTicker();

    const userSucursal = localStorage.getItem('sucursal') || '';
    if (rol === 'admin') {
        const branchWrapper = document.getElementById('branch-selector-wrapper');
        if (branchWrapper) branchWrapper.style.display = 'flex';
        loadBranchesSelect();
    } else {
        const wrapperLabel = document.getElementById('sucursal-label-wrapper');
        const displayLabel = document.getElementById('sucursal-display-name');
        if (wrapperLabel && displayLabel) {
            wrapperLabel.style.display = 'block';
            displayLabel.innerText = userSucursal.toUpperCase();
        }
        loadCameras();
    }

    connectGeneralWS();
}

function initClock() {
    const clockEl = document.getElementById('monitoreo-clock');
    if (!clockEl) return;
    const update = () => {
        const now = new Date();
        const dateStr = now.getFullYear() + '/' + 
            String(now.getMonth() + 1).padStart(2, '0') + '/' + 
            String(now.getDate()).padStart(2, '0');
        const timeStr = now.toTimeString().split(' ')[0];
        clockEl.innerText = `${dateStr}   ${timeStr}`;
    };
    update();
    clockInterval = setInterval(update, 1000);
}

function startDurationTicker() {
    durationInterval = setInterval(() => {
        const now = new Date();
        const dateStr = now.getFullYear() + '/' + 
            String(now.getMonth() + 1).padStart(2, '0') + '/' + 
            String(now.getDate()).padStart(2, '0');
        const timeStr = now.toTimeString().split(' ')[0];
        
        document.querySelectorAll('.cctv-hud-time').forEach(el => {
            el.innerText = `${dateStr}   ${timeStr}`;
        });

        document.querySelectorAll('.cctv-hud-duration').forEach(el => {
            let ticks = parseInt(el.dataset.ticks || '0') + 1;
            el.dataset.ticks = ticks;
            
            const hrs = Math.floor(ticks / 3600);
            const mins = Math.floor((ticks % 3600) / 60);
            const secs = ticks % 60;
            const frames = Math.floor(Math.random() * 30);
            
            el.innerHTML = `<span style="color: #ffffff; margin-right: 6px; font-size: 0.65rem;">■</span>DUR : ${String(hrs).padStart(2, '0')}:${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}:${String(frames).padStart(2, '0')}`;
        });
    }, 1000);
}

async function loadBranchesSelect() {
    const res = await api.get('/admin/branches');
    if (res.ok) {
        const select = document.getElementById('monitoring-branch-select');
        if (!select) return;
        select.innerHTML = res.data.map(b => `<option value="${b.nombre}">${b.nombre}</option>`).join('');
        
        const activeBranch = localStorage.getItem('activeMonitoringBranch') || res.data[0]?.nombre || '';
        if (activeBranch) {
            select.value = activeBranch;
        }
        await loadCameras();
    }
}

export async function changeBranch(branchName) {
    localStorage.setItem('activeMonitoringBranch', branchName);
    await loadCameras();
}

function clearVideoWebSockets() {
    Object.keys(activeWebSockets).forEach(id => {
        if (activeWebSockets[id]) {
            activeWebSockets[id].close();
            delete activeWebSockets[id];
        }
    });
}

async function loadCameras() {
    clearVideoWebSockets();
    
    const rol = localStorage.getItem('rol');
    let selectedBranch = '';
    
    if (rol === 'admin') {
        const select = document.getElementById('monitoring-branch-select');
        selectedBranch = select ? select.value : '';
    } else {
        selectedBranch = localStorage.getItem('sucursal') || '';
    }

    const res = await api.get('/system/cameras');
    if (res.ok) {
        camerasList = res.data;
        if (selectedBranch) {
            camerasList = camerasList.filter(c => c.sucursal === selectedBranch);
        }
        arrangeCctvGrid();
    }
}

function arrangeCctvGrid() {
    const grid = document.getElementById('cctv-grid');
    if (!grid) return;
    grid.innerHTML = '';

    if (camerasList.length === 0) {
        grid.style.gridTemplateColumns = '1fr';
        grid.style.gridTemplateRows = '1fr';
        grid.innerHTML = `
            <div class="no-cameras-screen">
                <i class="fas fa-video-slash" style="font-size: 3rem; color: #ef4444;"></i>
                <div class="no-cameras-title">NO SE ENCONTRARON CÁMARAS CONFIGURADAS</div>
                <div style="font-size: 0.8rem; color: #888;">Configura tus cámaras IP desde Ajustes > Monitoreo</div>
            </div>
        `;
        return;
    }

    const N = camerasList.length;
    let cols = 1;
    let rows = 1;

    if (N === 2) {
        cols = 2;
        rows = 1;
    } else if (N > 2 && N <= 4) {
        cols = 2;
        rows = 2;
    } else if (N > 4 && N <= 6) {
        cols = 3;
        rows = 2;
    } else if (N > 6) {
        cols = 3;
        rows = 3;
    }

    grid.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    grid.style.gridTemplateRows = `repeat(${rows}, 1fr)`;

    camerasList.forEach((cam, idx) => {
        const slotId = idx + 1;
        const box = document.createElement('div');
        box.className = 'cctv-box';
        box.id = `cctv-slot-${slotId}`;
        renderActiveSlot(box, slotId, cam);
        grid.appendChild(box);
    });

    loadLatestDetections();
}

function renderActiveSlot(box, slotId, cam) {
    const cctvCode = `CCTV ${String(slotId).padStart(3, '0')}`;
    
    let functionLabel = 'VIGILANCIA';
    if (cam.tipo === 'ENTRADA') functionLabel = 'LECTURA PATENTE (ENTRADA)';
    else if (cam.tipo === 'SALIDA') functionLabel = 'LECTURA PATENTE (SALIDA)';
    else if (cam.tipo === 'PATENTE') functionLabel = 'LECTURA PATENTE';
    else if (cam.tipo === 'QR') functionLabel = 'LECTURA QR';
    else if (cam.tipo === 'PREDIO') functionLabel = 'VIGILANCIA';

    const cameraLabel = `${cctvCode} - ${cam.nombre.toUpperCase()} [${functionLabel}]`;
    const ticksOffset = Math.floor(Math.random() * 3600);

    if (cam.is_running) {
        box.innerHTML = `
            <div class="cctv-hud-header">
                <span>${cameraLabel}</span>
                <div class="cctv-rec-indicator">
                    <span class="cctv-rec-dot"></span>
                    <span>REC</span>
                    <i class="fas fa-wifi" style="margin-left: 5px; font-size: 0.7rem; color: #ffffff;"></i>
                </div>
            </div>
            <img id="img-${cam.id}" class="cctv-video-feed" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7">
            <div class="cctv-scanlines"></div>
            <div class="cctv-hud-footer">
                <span class="cctv-hud-duration" data-ticks="${ticksOffset}"><span style="color: #ffffff; margin-right: 6px; font-size: 0.65rem;">■</span>DUR: 00:00:00:00</span>
                <span class="cctv-hud-time">---/--/-- --:--:--</span>
            </div>
            <div class="cctv-hover-actions">
                <button class="cctv-btn danger" onclick="toggleCamera(${cam.id}, 'stop')" title="Detener Cámara">
                    <i class="fas fa-stop"></i>
                </button>
                <button class="cctv-btn" onclick="openGate(${slotId})" title="Abrir Barrera">
                    <i class="fas fa-door-open"></i>
                </button>
            </div>
        `;
        connectCameraWebSocket(cam);
    } else {
        box.innerHTML = `
            <div class="cctv-hud-header">
                <span>${cameraLabel}</span>
                <span style="color: #ecc94b; font-weight: bold;">[STANDBY]</span>
            </div>
            <div class="test-pattern">
                <div class="test-pattern-bars">
                    <div class="test-pattern-bar bar-white"></div>
                    <div class="test-pattern-bar bar-yellow"></div>
                    <div class="test-pattern-bar bar-cyan"></div>
                    <div class="test-pattern-bar bar-green"></div>
                    <div class="test-pattern-bar bar-magenta"></div>
                    <div class="test-pattern-bar bar-red"></div>
                    <div class="test-pattern-bar bar-blue"></div>
                </div>
                <div class="test-pattern-bottom">
                    <div class="test-pattern-text">STANDBY DEVICE</div>
                </div>
            </div>
            <div class="cctv-scanlines"></div>
            <div class="cctv-hud-footer">
                <span><span style="color: #ffffff; margin-right: 6px; font-size: 0.65rem;">■</span>DUR: 00:00:00:00</span>
                <span class="cctv-hud-time">---/--/-- --:--:--</span>
            </div>
            <div class="cctv-hover-actions">
                <button class="cctv-btn" onclick="toggleCamera(${cam.id}, 'start')" title="Iniciar Cámara">
                    <i class="fas fa-play" style="color: #10b981;"></i>
                </button>
            </div>
        `;
    }
}

function connectCameraWebSocket(cam) {
    const token = localStorage.getItem('token');
    const normSuc = normalizeSystemName(cam.sucursal || localStorage.getItem('sucursal') || '');
    const procId = `${normSuc}_${cam.tipo}_${cam.id}`.toUpperCase();
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/v1/system/ws/video/${procId}?token=${token}`;
    
    if (activeWebSockets[cam.id]) {
        activeWebSockets[cam.id].close();
    }
    
    const socket = new WebSocket(wsUrl);
    activeWebSockets[cam.id] = socket;
    
    socket.onmessage = (event) => {
        const img = document.getElementById(`img-${cam.id}`);
        if (img) {
            img.src = `data:image/jpeg;base64,${event.data}`;
            if (!img.classList.contains('loaded')) {
                img.classList.add('loaded');
            }
        }
    };
    
    socket.onclose = () => {
        const currentCam = camerasList.find(c => c.id === cam.id);
        if (currentCam && currentCam.is_running && activeWebSockets[cam.id] === socket) {
            setTimeout(() => connectCameraWebSocket(cam), 5000);
        }
    };
    
    socket.onerror = (err) => {
        console.error(`Error WS Cámara ${cam.nombre}:`, err);
    };
}

export async function toggleCamera(camId, action) {
    const res = await api.post(`/system/cameras/${camId}/control/${action}`);
    if (res.ok) {
        const camIdx = camerasList.findIndex(c => c.id === camId);
        if (camIdx !== -1) {
            camerasList[camIdx].is_running = (action === 'start');
        }
        arrangeCctvGrid();
    } else {
        alert(res.error || 'Error al cambiar estado de la cámara');
    }
}

export async function openGate(slotId) {
    const camera = camerasList[slotId - 1];
    if (!camera) return;

    const gateType = camera.tipo.toUpperCase() === 'ENTRADA' ? 'ENTRADA' : 'SALIDA';
    const res = await api.post(`/admin/open-barrier?gate=${gateType}`);
    if (res.ok) {
        alert(`Acción remota: Apertura de barrera ${gateType} enviada correctamente.`);
    } else {
        alert(`Error al abrir barrera: ${res.error}`);
    }
}

async function loadLatestDetections() {
    const res = await api.get('/reports/access');
    if (!res || !res.ok) return;

    const logs = res.data;
    const lastEntry = logs.find(l => l.tipo_evento === 'ENTRADA');
    const lastExit = logs.find(l => l.tipo_evento === 'SALIDA');
    const lastQR = logs.find(l => l.reserva_id !== null);

    camerasList.forEach((cam, idx) => {
        const slotId = idx + 1;
        const box = document.getElementById(`cctv-slot-${slotId}`);
        if (!box) return;

        const footer = box.querySelector('.cctv-hud-footer');
        if (!footer) return;

        let plateOverlay = box.querySelector('.cctv-plate-hud');
        if (plateOverlay) plateOverlay.remove();

        let text = '';
        if (cam.tipo === 'ENTRADA' || cam.tipo === 'PATENTE') {
            if (lastEntry) text = formatPlate(lastEntry.patente_detectada);
        } else if (cam.tipo === 'SALIDA') {
            if (lastExit) text = formatPlate(lastExit.patente_detectada);
        } else if (cam.tipo === 'QR') {
            if (lastQR) text = `QR: ${formatPlate(lastQR.patente_detectada)}`;
        }

        if (text) {
            const plateDiv = document.createElement('div');
            plateDiv.className = 'cctv-plate-hud';
            plateDiv.style.position = 'absolute';
            plateDiv.style.bottom = '30px';
            plateDiv.style.left = '10px';
            plateDiv.style.background = 'rgba(0, 0, 0, 0.8)';
            plateDiv.style.border = '1px solid #C5A059';
            plateDiv.style.padding = '2px 8px';
            plateDiv.style.fontSize = '0.75rem';
            plateDiv.style.color = '#C5A059';
            plateDiv.style.zIndex = '15';
            plateDiv.style.pointerEvents = 'none';
            plateDiv.innerText = `LAST DETECT: ${text}`;
            
            box.appendChild(plateDiv);
        }
    });
}

function connectGeneralWS() {
    const token = localStorage.getItem('token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/v1/parking/ws?token=${token}`;
    
    wsGeneral = new WebSocket(wsUrl);
    wsGeneral.onmessage = () => {
        loadLatestDetections();
    };

    wsGeneral.onclose = () => {
        setTimeout(connectGeneralWS, 5000);
    };
}
