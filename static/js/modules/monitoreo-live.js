import api from './api.js';
import { normalizeSystemName, escapeHtml } from './utils.js';

/**
 * Módulo de Monitoreo CCTV DVR Live (Surveillance Pro)
 */

let camerasList = [];
let activeWebSockets = {};
let wsGeneral = null;
let lastEventData = null;

export function initMonitoreoLive() {
    const token = localStorage.getItem('token');
    const rol = localStorage.getItem('rol');
    if (!token || !['admin', 'local_admin', 'staff'].includes(rol)) {
        window.location.href = '/';
        return;
    }

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

    let cctvResizeTimer = null;
    window.addEventListener('resize', () => {
        clearTimeout(cctvResizeTimer);
        cctvResizeTimer = setTimeout(() => {
            if (camerasList.length > 0) applyCctvGridSize();
        }, 150);
    });
}

async function loadBranchesSelect() {
    const res = await api.get('/admin/branches');
    if (res.ok) {
        const select = document.getElementById('monitoring-branch-select');
        if (!select) return;
        select.innerHTML = res.data.map(b => `<option value="${escapeHtml(b.nombre)}">${escapeHtml(b.nombre)}</option>`).join('');
        
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

/**
 * Elige columnas/filas para que la grilla llene toda la pantalla (las celdas se
 * reparten el espacio con 1fr) buscando que cada celda quede con una proporción
 * parecida a la del video (16:9) y dejando la menor cantidad de huecos. Se
 * pondera: primero la cercanía a 16:9 y, con menor peso, los espacios vacíos.
 */
function computeCctvGrid(n) {
    const W = window.innerWidth;
    const H = window.innerHeight;
    const target = 16 / 9;
    let best = null;
    for (let cols = 1; cols <= n; cols++) {
        const rows = Math.ceil(n / cols);
        const empties = cols * rows - n;
        const aspect = (W / cols) / (H / rows);
        const score = Math.abs(aspect - target) + empties * 0.25;
        if (!best || score < best.score) {
            best = { cols, rows, score };
        }
    }
    return best || { cols: 1, rows: 1 };
}

function applyCctvGridSize() {
    const grid = document.getElementById('cctv-grid');
    if (!grid || camerasList.length === 0) return;
    const n = camerasList.length;
    const { cols, rows } = computeCctvGrid(n);
    grid.style.gridTemplateColumns = '';
    grid.style.gridTemplateRows = '';
    grid.style.setProperty('--cctv-cols', cols);
    grid.style.setProperty('--cctv-rows', rows);

    // Centrar la última fila cuando queda incompleta.
    const boxes = grid.querySelectorAll('.cctv-box');
    boxes.forEach(b => { b.style.gridRow = ''; b.style.gridColumn = ''; });
    const rem = n % cols;
    if (cols > 1 && rem > 0) {
        const offset = Math.floor((cols - rem) / 2);
        for (let i = 0; i < rem; i++) {
            const box = boxes[n - rem + i];
            if (box) {
                box.style.gridRow = String(rows);
                box.style.gridColumn = String(offset + i + 1);
            }
        }
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
                <i class="fas fa-video-slash" style="font-size: 3rem; color: #f43f5e;"></i>
                <div class="no-cameras-title">NO SE ENCONTRARON CÁMARAS CONFIGURADAS</div>
                <div style="font-size: 0.8rem; color: #888;">Configura tus cámaras IP desde Ajustes > Monitoreo</div>
            </div>
        `;
        return;
    }

    camerasList.forEach((cam, idx) => {
        const slotId = idx + 1;
        const box = document.createElement('div');
        box.className = 'cctv-box';
        box.id = `cctv-slot-${slotId}`;
        renderActiveSlot(box, slotId, cam);
        grid.appendChild(box);
    });

    applyCctvGridSize();
}

function renderActiveSlot(box, slotId, cam) {
    const cctvCode = `CCTV ${String(slotId).padStart(3, '0')}`;
    
    let functionLabel = 'VIGILANCIA';
    const cameraLabel = cam.nombre.toUpperCase();

    if (cam.is_running) {
        box.innerHTML = `
            <div class="cctv-hud-header">
                <span>${cameraLabel}</span>
            </div>
            <img id="img-${cam.id}" class="cctv-video-feed" src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7">
            <div class="cctv-console-log" id="console-${cam.id}"></div>
            <div class="cctv-scanlines"></div>
            <div class="cctv-hover-actions">
                <button class="cctv-btn danger" onclick="toggleCamera(${cam.id}, 'stop')" title="Detener Cámara">
                    <i class="fas fa-stop"></i>
                </button>
            </div>
        `;
        connectCameraWebSocket(cam);
    } else {
        box.innerHTML = `
            <div class="cctv-hud-header">
                <span>${cameraLabel}</span>
            </div>

            <div class="cctv-offline-container">
                <div class="cctv-offline-icon-box">
                    <i class="fas fa-video-slash" style="font-size: 1.4rem; color: #64748b;"></i>
                </div>
                <div class="cctv-offline-title">CÁMARA DESCONECTADA</div>
                <div class="cctv-offline-sub">Pasa el cursor para iniciar transmisión</div>
            </div>
            <div class="cctv-scanlines"></div>
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
        // 0. LINEA DE CONSOLA DEL SUBPROCESO ALPR (JSON con __console__) -> overlay de log
        try {
            const parsed = JSON.parse(event.data);
            if (parsed && parsed.__console__) {
                appendCameraConsoleLine(cam.id, parsed.line);
                return;
            }
        } catch (e) { /* no es JSON: es el frame base64 */ }

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

function connectGeneralWS() {
    const token = localStorage.getItem('token');
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/v1/parking/ws?token=${token}`;
    
    wsGeneral = new WebSocket(wsUrl);
    wsGeneral.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            // RUTA RAPIDA: solo ultimo evento sin recargar aforo/latencia
            if (msg.type === 'LAST_EVENT' && msg.last_event) {
                lastEventData = msg.last_event;
                showLastEventOnCameras();
                return;
            }
            if (msg.data && msg.data.last_event) {
                lastEventData = msg.data.last_event;
                showLastEventOnCameras();
            }
        } catch (e) {}
    };

    wsGeneral.onclose = (event) => {
        if (event && event.code === 4003) return;
        setTimeout(connectGeneralWS, 5000);
    };
}

function showLastEventOnCameras() {
    if (!lastEventData) return;

    const { message, status, type, plate } = lastEventData;
    const isOk = status === 'ok';
    const isWarning = status === 'warning';
    const isReading = status === 'reading';
    const msgUpper = (message || '').toUpperCase();

    camerasList.forEach((cam, idx) => {
        const slotId = idx + 1;
        const box = document.getElementById(`cctv-slot-${slotId}`);
        if (!box) return;

        // SALUDO GRANDE DE BIENVENIDA (INGRESO) / HASTA LUEGO (SALIDA) sobre el video
        if (isOk && (type === 'INGRESO' || type === 'SALIDA')) {
            const matchType = type === 'INGRESO' ? 'PATENTE_INGRESO' : 'PATENTE_EGRESO';
            if (cam.tipo === matchType) {
                showCameraGreeting(box, type, plate || '');
                let eventLine = box.querySelector('.cctv-event-line');
                if (eventLine) {
                    if (eventLine._hideTimer) clearTimeout(eventLine._hideTimer);
                    eventLine.style.opacity = '0';
                }
            }
            return;
        }

        hideCameraGreeting(box);

        // LINEA DE EVENTO CENTRAL (HUD SOBRE EL VIDEO)
        // Solo se muestra para estados que NO son OK. Los OK (franja verde al
        // detectar) se suprimen para no tapar el video con la franja superior.
        let eventLine = box.querySelector('.cctv-event-line');
        if (isOk) {
            if (eventLine) {
                if (eventLine._hideTimer) clearTimeout(eventLine._hideTimer);
                eventLine.style.opacity = '0';
            }
            return;
        }

        if (!eventLine) {
            eventLine = document.createElement('div');
            eventLine.className = 'cctv-event-line';
            box.appendChild(eventLine);
        }

        const stateClass = isWarning ? 'event-warning' : (isReading ? 'event-reading' : 'event-error');
        eventLine.className = `cctv-event-line ${stateClass}`;
        const icon = isWarning ? '&#9888;' : (isReading ? '&#9203;' : '&#10007;');

        eventLine.innerHTML = `<span class="event-icon">${icon}</span> ${msgUpper}`;

        if (eventLine._hideTimer) clearTimeout(eventLine._hideTimer);
        eventLine.style.opacity = '1';
        eventLine._hideTimer = setTimeout(() => {
            eventLine.style.opacity = '0';
        }, isReading ? 3000 : 7000);
    });
}

// --- SALUDO GRANDE SOBRE EL VIDEO (BIENVENIDA / HASTA LUEGO) ---
const CAMERA_GREETINGS = { INGRESO: 'BIENVENIDO', SALIDA: 'HASTA LUEGO' };
const GREETING_MS = 4000;

function showCameraGreeting(box, type, plate) {
    let greeting = box.querySelector('.cctv-greeting');
    if (!greeting) {
        greeting = document.createElement('div');
        greeting.className = 'cctv-greeting';
        box.appendChild(greeting);
    }
    greeting.classList.toggle('exit', type === 'SALIDA');
    greeting.innerHTML = `
        <span class="greeting-word">${CAMERA_GREETINGS[type] || 'OK'}</span>
        ${plate ? `<span class="greeting-plate">${escapeHtml(plate)}</span>` : ''}
    `;
    greeting.offsetHeight;
    greeting.classList.add('show');
    if (greeting._hideTimer) clearTimeout(greeting._hideTimer);
    greeting._hideTimer = setTimeout(() => {
        greeting.classList.remove('show');
    }, GREETING_MS);
}

function hideCameraGreeting(box) {
    const greeting = box.querySelector('.cctv-greeting');
    if (greeting) greeting.remove();
}

// --- LOG EN VIVO DE LA CONSOLA DEL SUBPROCESO ALPR (ruta paralela a los mensajes actuales) ---

const MAX_CONSOLE_LINES = 12;

function appendCameraConsoleLine(camId, line) {
    const logEl = document.getElementById(`console-${camId}`);
    if (!logEl) return;

    const isError = /(ERROR|EXCEPTION|FAIL|fatal|FATAL)/i.test(line);
    const isSuccess = /(ACEPTADA|ACEITADA|ACEPTADO|BIENVENIDO|HASTA LUEGO|CODIGO QR LEIDO|INGRESO|SALIDA|\[OK\]|CONF: 0\.[5-9])/i.test(line);

    const div = document.createElement('div');
    if (isError) {
        div.className = 'cctv-console-line error';
    } else if (isSuccess) {
        div.className = 'cctv-console-line success';
    } else {
        div.className = 'cctv-console-line';
    }
    div.textContent = line;

    logEl.appendChild(div);
    while (logEl.children.length > MAX_CONSOLE_LINES) {
        logEl.removeChild(logEl.firstChild);
    }
    logEl.scrollTop = logEl.scrollHeight;
}
