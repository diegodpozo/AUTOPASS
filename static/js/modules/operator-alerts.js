/**
 * AVISOS AL OPERADOR CON LA PESTAÑA OCULTA.
 *
 * Un evento operativo relevante (p. ej. una salida impaga detectada por ALPR)
 * abre su popup aunque la pestaña esté minimizada o en segundo plano, pero el
 * operador no lo ve. Este helper le avisa con cuatro recursos:
 *   1. Notificación del sistema (Notification API), visible aun con la pestaña oculta.
 *   2. Parpadeo del título del documento.
 *   3. Parpadeo del favicon con un círculo rojo.
 *   4. Alerta sonora (beeps), repetida hasta que el operador vuelve a la pestaña.
 * Si la pestaña está visible no hace nada: el popup ya cumple esa función.
 */

let _originalTitle = null;
let _flashTimer = null;

let _originalFavicon = null;
let _alertFaviconHref = null;
let _faviconTimer = null;

let _audioCtx = null;
let _activeOscillators = [];
let _soundActive = false;

/** Inicializa permisos, audio y el restablecimiento de avisos. Llamar una vez al cargar. */
export function initOperatorAlerts() {
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) stopOperatorAlerts();
    });
    window.addEventListener('focus', stopOperatorAlerts);

    // Algunos navegadores solo permiten pedir permiso y habilitar audio tras un
    // gesto del usuario.
    const unlock = () => {
        document.removeEventListener('pointerdown', unlock);
        if (typeof Notification !== 'undefined' && Notification.permission === 'default') {
            Notification.requestPermission().catch(() => {});
        }
        const ctx = _ensureAudioContext();
        if (ctx && ctx.state === 'suspended') ctx.resume().catch(() => {});
    };
    document.addEventListener('pointerdown', unlock, { once: true });
}

function startTitleFlash(message) {
    if (_flashTimer) return;
    if (_originalTitle === null) _originalTitle = document.title;
    let on = false;
    _flashTimer = setInterval(() => {
        on = !on;
        document.title = on ? message : _originalTitle;
    }, 1000);
    document.title = message;
}

function stopTitleFlash() {
    if (_flashTimer) {
        clearInterval(_flashTimer);
        _flashTimer = null;
    }
    if (_originalTitle !== null) {
        document.title = _originalTitle;
        _originalTitle = null;
    }
}

function _faviconLink() {
    let link = document.querySelector('link[rel~="icon"]');
    if (!link) {
        link = document.createElement('link');
        link.rel = 'icon';
        document.head.appendChild(link);
    }
    return link;
}

function _buildAlertFavicon() {
    const size = 64;
    const canvas = document.createElement('canvas');
    canvas.width = canvas.height = size;
    const g = canvas.getContext('2d');
    g.fillStyle = '#e53935';
    g.beginPath();
    g.arc(size / 2, size / 2, size / 2 - 2, 0, Math.PI * 2);
    g.fill();
    g.fillStyle = '#ffffff';
    g.font = 'bold 46px sans-serif';
    g.textAlign = 'center';
    g.textBaseline = 'middle';
    g.fillText('!', size / 2, size / 2 + 2);
    return canvas.toDataURL('image/png');
}

function startFaviconFlash() {
    if (_faviconTimer) return;
    const link = _faviconLink();
    _originalFavicon = link.getAttribute('href') || '/static/images/icons/icon-192.png';
    if (!_alertFaviconHref) _alertFaviconHref = _buildAlertFavicon();
    let on = false;
    _faviconTimer = setInterval(() => {
        on = !on;
        link.setAttribute('href', on ? _alertFaviconHref : _originalFavicon);
    }, 500);
}

function stopFaviconFlash() {
    if (_faviconTimer) {
        clearInterval(_faviconTimer);
        _faviconTimer = null;
    }
    if (_originalFavicon !== null) {
        _faviconLink().setAttribute('href', _originalFavicon);
        _originalFavicon = null;
    }
}

function _ensureAudioContext() {
    if (_audioCtx) return _audioCtx;
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return null;
    try { _audioCtx = new AudioCtx(); } catch (_) { _audioCtx = null; }
    return _audioCtx;
}

function _beep(ctx, at) {
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.type = 'sine';
    osc.frequency.setValueAtTime(880, at);
    gain.gain.setValueAtTime(0.0001, at);
    gain.gain.exponentialRampToValueAtTime(0.3, at + 0.02);
    gain.gain.exponentialRampToValueAtTime(0.0001, at + 0.35);
    osc.connect(gain);
    gain.connect(ctx.destination);
    osc.start(at);
    osc.stop(at + 0.4);
    _activeOscillators.push(osc);
    osc.onended = () => {
        const i = _activeOscillators.indexOf(osc);
        if (i >= 0) _activeOscillators.splice(i, 1);
        if (_activeOscillators.length === 0) _soundActive = false;
    };
}

// Se agenda por tiempo del AudioContext (no por setInterval): en pestañas en
// segundo plano los timers se frenan, pero el audio agendado sigue sonando.
function startAlertSound() {
    if (_soundActive) return;
    const ctx = _ensureAudioContext();
    if (!ctx) return;
    if (ctx.state === 'suspended') ctx.resume().catch(() => {});
    _soundActive = true;
    const now = ctx.currentTime;
    for (let rep = 0; rep < 12; rep++) {
        const base = now + rep * 2.5;
        _beep(ctx, base);
        _beep(ctx, base + 0.22);
        _beep(ctx, base + 0.44);
    }
}

function stopAlertSound() {
    _activeOscillators.forEach(o => { try { o.stop(); } catch (_) {} });
    _activeOscillators = [];
    _soundActive = false;
}

/** Detiene todos los avisos (título, favicon y sonido). */
export function stopOperatorAlerts() {
    stopTitleFlash();
    stopFaviconFlash();
    stopAlertSound();
}

/**
 * Avisa al operador solo si la pestaña está oculta. Con la pestaña visible no
 * hace nada (el popup/badge ya se encargan).
 * @param {{title?:string, body?:string, tag?:string}} opts
 */
export function notifyOperator({ title = 'AUTOPASS', body = '', tag = 'autopass-alert' } = {}) {
    if (!document.hidden) return;

    startTitleFlash(`ALERTA: ${title}`);
    startFaviconFlash();
    startAlertSound();

    if (typeof Notification !== 'undefined' && Notification.permission === 'granted') {
        try {
            const notif = new Notification(title, {
                body,
                tag,
                icon: '/static/images/icons/icon-192.png'
            });
            notif.onclick = () => { window.focus(); notif.close(); };
        } catch (_) { /* sin soporte de notificación nativa: el título alcanza */ }
    }
}
