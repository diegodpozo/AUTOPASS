import { showToast } from './utils.js';

/**
 * Módulo Web Serial para AUTOPASS (Control de maqueta Arduino directamente desde el navegador).
 * Permite que una laptop conectada remotamente al servidor (vía Cloudflare / Tailscale)
 * accione los servomotores del Arduino enchufado a su puerto USB sin instalar programas adicionales.
 */

let serialPort = null;
let hardwareWs = null;
let wsReconnectTimer = null;

export function isWebSerialSupported() {
    return 'serial' in navigator;
}

export function isSerialConnected() {
    return serialPort !== null && serialPort.readable !== null;
}

/**
 * Envía una cadena de comando terminada en \n al Arduino conectado vía USB.
 * @param {string} commandStr - Ejemplo: 'OPEN_ENTRADA', 'CLOSE_ENTRADA', 'OPEN_SALIDA', 'CLOSE_SALIDA'
 */
export async function sendWebSerialCommand(commandStr) {
    if (!serialPort || !serialPort.writable) {
        return false;
    }

    try {
        const encoder = new TextEncoder();
        const writer = serialPort.writable.getWriter();
        const line = commandStr.trim() + '\n';
        await writer.write(encoder.encode(line));
        writer.releaseLock();

        // Reflejo visual de barrera en el dashboard
        const isEntry = commandStr.toUpperCase().includes('ENTRADA') || commandStr.toUpperCase().includes('ENTRY');
        const iconId = isEntry ? 'icon-barrier-entry' : 'icon-barrier-exit';
        const iconEl = document.getElementById(iconId);
        if (iconEl) {
            if (commandStr.toUpperCase().includes('OPEN')) {
                iconEl.src = '/static/images/barrera-alta.png';
                setTimeout(() => {
                    if (iconEl) iconEl.src = '/static/images/barrera-baja.png';
                }, 5000);
            } else if (commandStr.toUpperCase().includes('CLOSE')) {
                iconEl.src = '/static/images/barrera-baja.png';
            }
        }
        return true;
    } catch (err) {
        console.error('[WEB SERIAL] Error al escribir en Arduino:', err);
        return false;
    }
}

/**
 * Conecta el WebSocket que recibe las órdenes de barrera del servidor en tiempo real.
 */
function connectHardwareWebSocket() {
    if (hardwareWs && (hardwareWs.readyState === WebSocket.OPEN || hardwareWs.readyState === WebSocket.CONNECTING)) {
        return;
    }

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const token = localStorage.getItem('token') || '';
    const wsUrl = `${proto}//${window.location.host}/v1/system/ws/hardware?token=${encodeURIComponent(token)}`;

    try {
        hardwareWs = new WebSocket(wsUrl);

        hardwareWs.onopen = () => {
            console.info('[WEB SERIAL WS] Conectado al canal de hardware del servidor.');
        };

        hardwareWs.onmessage = async (event) => {
            try {
                const data = JSON.parse(event.data);
                if (data.command && data.gate) {
                    const cmd = `${data.command}_${data.gate}`;
                    console.info('[WEB SERIAL] Evento de barrera recibido del servidor:', cmd);
                    await sendWebSerialCommand(cmd);
                }
            } catch (e) {
                // Mensajes de texto simples o pings
            }
        };

        hardwareWs.onclose = () => {
            hardwareWs = null;
            if (isSerialConnected()) {
                clearTimeout(wsReconnectTimer);
                wsReconnectTimer = setTimeout(connectHardwareWebSocket, 3000);
            }
        };

        hardwareWs.onerror = (err) => {
            console.debug('[WEB SERIAL WS] Error en WebSocket:', err);
        };
    } catch (e) {
        console.error('[WEB SERIAL WS] No se pudo inicializar WebSocket:', e);
    }
}

function updateUiStatus(connected) {
    const btn = document.getElementById('btn-web-serial-connect');
    const textEl = document.getElementById('web-serial-status-text');
    if (!btn || !textEl) return;

    if (connected) {
        btn.classList.add('success');
        textEl.textContent = 'Maqueta USB Conectada';
        btn.title = 'Arduino Uno conectado por USB a esta máquina. Clic para desconectar.';
    } else {
        btn.classList.remove('success');
        textEl.textContent = 'Conectar Maqueta USB';
        btn.title = 'Conectar Arduino Uno enchufado por USB a esta máquina.';
    }
}

/**
 * Alterna la conexión con el Arduino Uno vía Web Serial.
 */
export async function toggleWebSerialConnection() {
    if (!isWebSerialSupported()) {
        showToast('Tu navegador no soporta Web Serial. Usá Google Chrome o Microsoft Edge en tu laptop.', 'warning');
        return;
    }

    if (isSerialConnected()) {
        // Desconectar
        try {
            if (hardwareWs) {
                hardwareWs.close();
                hardwareWs = null;
            }
            if (serialPort) {
                await serialPort.close();
                serialPort = null;
            }
            updateUiStatus(false);
            showToast('Maqueta Arduino desconectada.', 'info');
        } catch (err) {
            console.error('[WEB SERIAL] Error al desconectar:', err);
            serialPort = null;
            updateUiStatus(false);
        }
        return;
    }

    // Solicitar permiso de conexión al puerto USB
    try {
        const port = await navigator.serial.requestPort();
        await port.open({ baudRate: 9600 });
        serialPort = port;

        updateUiStatus(true);
        connectHardwareWebSocket();
        showToast('¡Arduino Uno conectado exitosamente! Las barreras responderán en vivo.', 'success');

        // Escuchar desconexión física de cable USB
        navigator.serial.addEventListener('disconnect', (event) => {
            if (event.target === serialPort) {
                serialPort = null;
                updateUiStatus(false);
                showToast('Se desconectó el cable USB del Arduino.', 'warning');
            }
        });
    } catch (err) {
        if (err.name !== 'NotFoundError') { // NotFoundError ocurre si el usuario canceló la ventana
            console.error('[WEB SERIAL] Error conectando puerto:', err);
            showToast(`Error al abrir puerto USB: ${err.message || 'Verificá que el monitor serie de Arduino esté cerrado.'}`, 'error');
        }
    }
}

/**
 * Inicializa auto-detección si el usuario ya autorizó el puerto previamente en este navegador.
 */
export async function initWebSerial() {
    if (!isWebSerialSupported()) {
        const btn = document.getElementById('btn-web-serial-connect');
        if (btn) btn.style.display = 'none';
        return;
    }

    updateUiStatus(false);

    try {
        const ports = await navigator.serial.getPorts();
        if (ports && ports.length > 0) {
            // Hay un puerto previamente autorizado por el usuario
            const port = ports[0];
            try {
                await port.open({ baudRate: 9600 });
                serialPort = port;
                updateUiStatus(true);
                connectHardwareWebSocket();
                console.info('[WEB SERIAL] Auto-reconexión a Arduino Uno previa exitosa.');
            } catch (openErr) {
                // Puerto en uso o no disponible en este momento
                console.debug('[WEB SERIAL] Puerto previo no disponible automáticamente:', openErr);
            }
        }
    } catch (e) {
        // Silencioso al cargar
    }
}
