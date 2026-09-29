/**
 * MODULO DE TIEMPO VIRTUAL
 * PROVEE getVirtualNow() PARA QUE TODO EL FRONTEND USE EL MISMO TIEMPO QUE EL SERVER.
 * CUANDO EL OFFSET ES 0, COINCIDE CON EL TIEMPO REAL.
 * PARA VOLVER A TIEMPO REAL: BORRAR data/virtual_time_offset.json Y REINICIAR.
 */
import api from './api.js';

let _offsetMs = 0;
let _lastSync = 0;
const SYNC_INTERVAL = 60000; // RESINCAR CADA 1 MIN

async function _sync() {
    try {
        const res = await api.get('/system/virtual-time');
        if (res && res.ok) {
            _offsetMs = (res.data.offset_seconds || 0) * 1000;
            _lastSync = Date.now();
        }
    } catch (e) {
        // SILENCIOSO
    }
}

export async function initVirtualTime() {
    await _sync();
    // RESINCAR PERIODICAMENTE
    setInterval(_sync, SYNC_INTERVAL);
}

export function getVirtualNow() {
    return new Date(Date.now() + _offsetMs);
}
