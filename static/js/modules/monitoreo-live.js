/*Centro de monitoreo DVR: grilla de camaras, WebSockets, eventos y consola*/


import api from './api.js';						// Importa el cliente HTTP `api` para hablar con el backend
import { normalizeSystemName, escapeHtml } from './utils.js';		// Importa helpers para normalizar sucursales y escapar HTML


let camerasList = [];							// Lista de camaras que se muestran en la grilla
let activeWebSockets = {};						// WebSockets de video abiertos, indexados por id de camara
let wsGeneral = null;							// WebSocket general que recibe eventos de acceso
let lastEventData = null;						// Ultimo evento recibido, usado para el HUD

export function initMonitoreoLive() {					// Arranca la pantalla de monitoreo en vivo
    const token = localStorage.getItem('token');			// Token del usuario logueado
    const rol = localStorage.getItem('rol');				// Rol del usuario (admin, local_admin o staff)
    if (!token || !['admin', 'local_admin', 'staff'].includes(rol)) {	// Si falta token o el rol no esta permitido
        window.location.href = '/';					// Vuelve a la pantalla de inicio
        return;								// Corta la inicializacion
    }									// Fin del control de acceso

    const userSucursal = localStorage.getItem('sucursal') || '';	// Sucursal guardada del usuario (si no es admin)
    if (rol === 'admin') {						// El admin global puede elegir cualquier sucursal
        const branchWrapper = document.getElementById('branch-selector-wrapper');
									// Contenedor del selector de sucursal
        if (branchWrapper) branchWrapper.style.display = 'flex';	// Muestra el selector de sucursales
        loadBranchesSelect();						// Carga las sucursales en el selector
    } else {								// Los demas roles ven su sucursal fija
        const wrapperLabel = document.getElementById('sucursal-label-wrapper');
									// Contenedor de la etiqueta de sucursal
        const displayLabel = document.getElementById('sucursal-display-name');
									// Texto donde se muestra la sucursal
        if (wrapperLabel && displayLabel) {				// Si existen ambos elementos, los actualiza
            wrapperLabel.style.display = 'block';			// Muestra la etiqueta de sucursal
            displayLabel.innerText = userSucursal.toUpperCase();	// Pinta el nombre de la sucursal en mayusculas
        }								// Fin del if de etiqueta
        loadCameras();							// Carga las camaras de esa sucursal
    }									// Fin del if de rol

    connectGeneralWS();							// Abre el WebSocket general de eventos

    let cctvResizeTimer = null;						// Timer para no recalcular la grilla en cada pixel
    window.addEventListener('resize', () => {				// Escucha los cambios de tamano de la ventana
        clearTimeout(cctvResizeTimer);					// Cancela el ajuste pendiente
        cctvResizeTimer = setTimeout(() => {				// Espera 150 ms antes de recalcular
            if (camerasList.length > 0) applyCctvGridSize();		// Si hay camaras, recalcula la grilla
        }, 150);							// Fin del timer de resize
    });									// Fin del listener de resize
}									// Fin de la inicializacion

async function loadBranchesSelect() {					// Pide al backend la lista de sucursales
    const res = await api.get('/admin/branches');			// Llama al endpoint de sucursales
    if (res.ok) {							// Si la respuesta fue correcta
        const select = document.getElementById('monitoring-branch-select');
									// Selector de sucursal del monitoreo
        if (!select) return;						// Si no existe el selector, no hace nada
        select.innerHTML = res.data.map(b => `<option value="${escapeHtml(b.nombre)}">${escapeHtml(b.nombre)}</option>`).join('');
									// Crea una opcion por sucursal, escapando el HTML
        
        const activeBranch = localStorage.getItem('activeMonitoringBranch') || res.data[0]?.nombre || '';
									// Ultima sucursal elegida o la primera de la lista
        if (activeBranch) {						// Si hay una sucursal activa
            select.value = activeBranch;				// La deja seleccionada en el combo
        }								// Fin del if de sucursal activa
        await loadCameras();						// Carga las camaras de esa sucursal
    }									// Fin del if de respuesta correcta
}									// Fin de la carga de sucursales

export async function changeBranch(branchName) {			// Cambia la sucursal que se esta monitoreando
    localStorage.setItem('activeMonitoringBranch', branchName);		// Guarda la sucursal elegida en el navegador
    await loadCameras();						// Recarga la grilla con las camaras de esa sucursal
}									// Fin del cambio de sucursal

function clearVideoWebSockets() {					// Cierra todos los WebSockets de video abiertos
    Object.keys(activeWebSockets).forEach(id => {			// Recorre cada camara conectada
        if (activeWebSockets[id]) {					// Si el socket existe
            activeWebSockets[id].close();				// Lo cierra
            delete activeWebSockets[id];				// Lo quita del registro
        }								// Fin del if del socket
    });									// Fin del recorrido
}									// Fin del cierre de sockets

async function loadCameras() {						// Carga las camaras segun el rol y la sucursal
    clearVideoWebSockets();						// Primero cierra los videos anteriores
    
    const rol = localStorage.getItem('rol');				// Rol actual del usuario
    let selectedBranch = '';						// Sucursal que se va a mostrar
    
    if (rol === 'admin') {						// Si es admin, usa el selector
        const select = document.getElementById('monitoring-branch-select');
									// Selector de sucursal
        selectedBranch = select ? select.value : '';			// Toma la sucursal elegida
    } else {								// Si no es admin
        selectedBranch = localStorage.getItem('sucursal') || '';	// Usa la sucursal guardada del usuario
    }									// Fin del if de rol

    const res = await api.get('/system/cameras');			// Pide todas las camaras al backend
    if (res.ok) {							// Si la respuesta fue correcta
        camerasList = res.data;						// Guarda la lista recibida
        if (selectedBranch) {						// Si hay una sucursal seleccionada
            camerasList = camerasList.filter(c => c.sucursal === selectedBranch);
									// Deja solo las camaras de esa sucursal
        }								// Fin del filtro por sucursal
        arrangeCctvGrid();						// Dibuja la grilla con las camaras
    }									// Fin del if de respuesta
}									// Fin de la carga de camaras

/**
 * Elige columnas/filas para que la grilla llene toda la pantalla (las celdas se
 * reparten el espacio con 1fr) buscando que cada celda quede con una proporción
 * parecida a la del video (16:9) y dejando la menor cantidad de huecos. Se
 * pondera: primero la cercanía a 16:9 y, con menor peso, los espacios vacíos.
 */
function computeCctvGrid(n) {						// Calcula la mejor cantidad de columnas y filas
    const W = window.innerWidth;					// Ancho disponible de la ventana
    const H = window.innerHeight;					// Alto disponible de la ventana
    const target = 16 / 9;						// Proporcion ideal del video (16:9)
    let best = null;							// Guarda la mejor combinacion encontrada
    for (let cols = 1; cols <= n; cols++) {				// Prueba con 1, 2, ... hasta n columnas
        const rows = Math.ceil(n / cols);				// Filas necesarias para esas columnas
        const empties = cols * rows - n;				// Celdas vacias que quedarian
        const aspect = (W / cols) / (H / rows);				// Proporcion real de cada celda
        const score = Math.abs(aspect - target) + empties * 0.25;	// Puntaje: prioriza 16:9 y castiga huecos
        if (!best || score < best.score) {				// Si es mejor que la anterior
            best = { cols, rows, score };				// Guarda esta combinacion
        }								// Fin del if de mejor
    }									// Fin del recorrido de columnas
    return best || { cols: 1, rows: 1 };				// Devuelve la mejor opcion o una grilla 1x1
}									// Fin del calculo de grilla

function applyCctvGridSize() {						// Aplica el tamano calculado a la grilla
    const grid = document.getElementById('cctv-grid');			// Contenedor de la grilla CCTV
    if (!grid || camerasList.length === 0) return;			// Si no hay grilla o camaras, no hace nada
    const n = camerasList.length;					// Cantidad de camaras
    const { cols, rows } = computeCctvGrid(n);				// Obtiene columnas y filas ideales
    grid.style.gridTemplateColumns = '';				// Limpia las columnas fijas anteriores
    grid.style.gridTemplateRows = '';					// Limpia las filas fijas anteriores
    grid.style.setProperty('--cctv-cols', cols);			// Publica la cantidad de columnas en CSS
    grid.style.setProperty('--cctv-rows', rows);			// Publica la cantidad de filas en CSS

    // Centrar la última fila cuando queda incompleta.
    const boxes = grid.querySelectorAll('.cctv-box');			// Todas las celdas de la grilla
    boxes.forEach(b => { b.style.gridRow = ''; b.style.gridColumn = ''; });
									// Limpia la posicion manual de cada celda
    const rem = n % cols;						// Cuantas camaras sobran en la ultima fila
    if (cols > 1 && rem > 0) {						// Si la ultima fila queda incompleta
        const offset = Math.floor((cols - rem) / 2);			// Desplazamiento para centrarla
        for (let i = 0; i < rem; i++) {					// Recorre las camaras sobrantes
            const box = boxes[n - rem + i];				// Celda que hay que centrar
            if (box) {							// Si la celda existe
                box.style.gridRow = String(rows);			// La coloca en la ultima fila
                box.style.gridColumn = String(offset + i + 1);		// La centra en la columna correspondiente
            }								// Fin del if de celda
        }								// Fin del recorrido de sobrantes
    }									// Fin del if de fila incompleta
}									// Fin del ajuste de grilla

function arrangeCctvGrid() {						// Dibuja la grilla completa de camaras
    const grid = document.getElementById('cctv-grid');			// Contenedor de la grilla
    if (!grid) return;							// Si no existe, no hace nada
    grid.innerHTML = '';						// Vacia la grilla anterior

    if (camerasList.length === 0) {					// Si no hay camaras configuradas
        grid.style.gridTemplateColumns = '1fr';				// Deja una sola columna
        grid.style.gridTemplateRows = '1fr';				// Deja una sola fila
									// Sin camaras: contenedor centrado del aviso
									// Icono de camara tachada en rojo
									// Titulo: "NO SE ENCONTRARON CAMARAS CONFIGURADAS"
									// Ayuda: configurarlas en Ajustes > Monitoreo
									// Cierre del contenedor
        grid.innerHTML = `
            <div class="no-cameras-screen">
                <i class="fas fa-video-slash" style="font-size: 3rem; color: #f43f5e;"></i>
                <div class="no-cameras-title">NO SE ENCONTRARON CÁMARAS CONFIGURADAS</div>
                <div style="font-size: 0.8rem; color: #888;">Configura tus cámaras IP desde Ajustes > Monitoreo</div>
            </div>
        `;								// Fin del HTML de pantalla vacia
        return;								// Sale sin dibujar camaras
    }									// Fin del caso sin camaras

    camerasList.forEach((cam, idx) => {					// Recorre las camaras cargadas
        const slotId = idx + 1;						// Numero de slot visible (1, 2, 3...)
        const box = document.createElement('div');			// Crea la celda de la camara
        box.className = 'cctv-box';					// Le asigna la clase de celda CCTV
        box.id = `cctv-slot-${slotId}`;					// Le asigna un id unico por slot
        renderActiveSlot(box, slotId, cam);				// Dibuja el contenido de la celda
        grid.appendChild(box);						// Agrega la celda a la grilla
    });									// Fin del recorrido de camaras

    applyCctvGridSize();						// Ajusta el tamano final de la grilla
}									// Fin del dibujo de la grilla

function renderActiveSlot(box, slotId, cam) {				// Dibuja una celda segun el estado de la camara
    const cctvCode = `CCTV ${String(slotId).padStart(3, '0')}`;		// Codigo CCTV visible (CCTV 001, 002...)
    
    let functionLabel = 'VIGILANCIA';					// Etiqueta de funcion por defecto
    const cameraLabel = cam.nombre.toUpperCase();			// Nombre de la camara en mayusculas

    if (cam.is_running) {						// Si la camara esta encendida
									// Camara encendida: HUD de video en vivo
									// Barra superior con el nombre de la camara
									// Nombre de la camara en mayusculas
									// Cierre de la barra superior
									// Imagen que recibe los frames JPEG por WebSocket
									// Consola flotante con el log del subproceso ALPR
									// Lineas de escaneo para el efecto CCTV
									// Acciones que aparecen al pasar el cursor
									// Boton rojo para detener la camara
									// Icono de stop
									// Cierre del boton
									// Cierre de las acciones
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
        `;								// Fin del HTML de camara encendida
        connectCameraWebSocket(cam);					// Abre el WebSocket de video de esa camara
    } else {								// Si la camara esta apagada
									// Camara apagada: aviso y boton para iniciarla
									// Barra superior con el nombre de la camara
									// Nombre de la camara en mayusculas
									// Cierre de la barra superior
									// Separacion visual
									// Contenedor del aviso de camara desconectada
									// Caja del icono de camara tachada
									// Icono gris de camara apagada
									// Cierre de la caja del icono
									// Titulo: "CAMARA DESCONECTADA"
									// Subtitulo: invita a pasar el cursor para iniciar
									// Cierre del aviso
									// Lineas de escaneo para el efecto CCTV
									// Acciones que aparecen al pasar el cursor
									// Boton verde para iniciar la camara
									// Icono de play
									// Cierre del boton
									// Cierre de las acciones
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
        `;								// Fin del HTML de camara apagada
    }									// Fin del if de estado

}									// Fin del dibujo de la celda

function connectCameraWebSocket(cam) {					// Conecta el video en vivo de una camara
    const token = localStorage.getItem('token');			// Token del usuario para autenticar el WebSocket
    const normSuc = normalizeSystemName(cam.sucursal || localStorage.getItem('sucursal') || '');
									// Normaliza la sucursal de la camara
    const procId = `${normSuc}_${cam.tipo}_${cam.id}`.toUpperCase();	// Arma el id de proceso: sucursal_tipo_id
    
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
									// Usa wss si la pagina es HTTPS
    const wsUrl = `${protocol}//${window.location.host}/v1/system/ws/video/${procId}?token=${token}`;
									// URL del WebSocket de video con token
    
    if (activeWebSockets[cam.id]) {					// Si ya habia un socket para esa camara
        activeWebSockets[cam.id].close();				// Lo cierra para no duplicar
    }									// Fin del cierre del socket anterior
    
    const socket = new WebSocket(wsUrl);				// Crea el nuevo WebSocket
    activeWebSockets[cam.id] = socket;					// Lo guarda en el registro por camara
    
    socket.onmessage = (event) => {					// Cuando llega un mensaje del WebSocket
        // 0. LINEA DE CONSOLA DEL SUBPROCESO ALPR (JSON con __console__) -> overlay de log
        try {								// Intenta interpretar el mensaje como JSON
            const parsed = JSON.parse(event.data);			// Convierte el texto a objeto
            if (parsed && parsed.__console__) {				// Si es una linea de consola del ALPR
                appendCameraConsoleLine(cam.id, parsed.line);		// La agrega al log de la camara
                return;							// No sigue con el frame
            }								// Fin del if de consola
        } catch (e) { /* no es JSON: es el frame base64 */ }

        const img = document.getElementById(`img-${cam.id}`);		// Imagen donde se pinta el video
        if (img) {							// Si la imagen existe
            img.src = `data:image/jpeg;base64,${event.data}`;		// Pinta el frame JPEG que llego en Base64
            if (!img.classList.contains('loaded')) {			// Si es el primer frame
                img.classList.add('loaded');				// Marca la imagen como cargada
            }								// Fin del primer frame
        }								// Fin del if de imagen
    };									// Fin del manejo de mensajes
    
    socket.onclose = () => {						// Cuando se cierra el WebSocket
        const currentCam = camerasList.find(c => c.id === cam.id);	// Busca la camara actual en la lista
        if (currentCam && currentCam.is_running && activeWebSockets[cam.id] === socket) {
									// Si sigue encendida y es el mismo socket
            setTimeout(() => connectCameraWebSocket(cam), 5000);	// Reintenta conectarse en 5 segundos
        }								// Fin del if de reconexion
    };									// Fin del cierre del WebSocket
    
    socket.onerror = (err) => {						// Si el WebSocket da error
        console.error(`Error WS Cámara ${cam.nombre}:`, err);		// Lo muestra en la consola del navegador
    };									// Fin del manejo de error
}									// Fin de la conexion de video

export async function toggleCamera(camId, action) {			// Inicia o detiene una camara
    const res = await api.post(`/system/cameras/${camId}/control/${action}`);
									// Pide al backend cambiar el estado
    if (res.ok) {							// Si el backend acepto
        const camIdx = camerasList.findIndex(c => c.id === camId);	// Busca la camara en la lista
        if (camIdx !== -1) {						// Si la encontro
            camerasList[camIdx].is_running = (action === 'start');	// Actualiza su estado local
        }								// Fin del if de camara encontrada
        arrangeCctvGrid();						// Redibuja la grilla
    } else {								// Si el backend fallo
        alert(res.error || 'Error al cambiar estado de la cámara');	// Avisa el error al operador
    }									// Fin del if de respuesta
}									// Fin del control de camara

export async function openGate(slotId) {				// Abre la barrera asociada a un slot
    const camera = camerasList[slotId - 1];				// Camara de ese slot
    if (!camera) return;						// Si no existe, no hace nada

    const gateType = camera.tipo.toUpperCase() === 'ENTRADA' ? 'ENTRADA' : 'SALIDA';
									// Tipo de barrera: entrada o salida
    const res = await api.post(`/admin/open-barrier?gate=${gateType}`);
									// Pide al backend abrir la barrera
    if (res.ok) {							// Si el backend acepto
        alert(`Acción remota: Apertura de barrera ${gateType} enviada correctamente.`);
									// Confirma la apertura al operador
    } else {								// Si fallo
        alert(`Error al abrir barrera: ${res.error}`);			// Muestra el error
    }									// Fin del if de respuesta
}									// Fin de la apertura de barrera

function connectGeneralWS() {						// Abre el WebSocket general de eventos
    const token = localStorage.getItem('token');			// Token del usuario
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
									// Usa wss si la pagina es HTTPS
    const wsUrl = `${protocol}//${window.location.host}/v1/parking/ws?token=${token}`;
									// URL del WebSocket de eventos con token
    
    wsGeneral = new WebSocket(wsUrl);					// Crea el WebSocket general
    wsGeneral.onmessage = (event) => {					// Cuando llega un evento
        try {								// Intenta interpretar el mensaje
            const msg = JSON.parse(event.data);				// Convierte el texto a objeto
            // RUTA RAPIDA: solo ultimo evento sin recargar aforo/latencia
            if (msg.type === 'LAST_EVENT' && msg.last_event) {		// Si es el ultimo evento
                lastEventData = msg.last_event;				// Guarda el evento
                showLastEventOnCameras();				// Lo muestra en las camaras
                return;							// No procesa nada mas
            }								// Fin del if de ultimo evento
            if (msg.data && msg.data.last_event) {			// Si el mensaje trae un ultimo evento
                lastEventData = msg.data.last_event;			// Guarda el evento
                showLastEventOnCameras();				// Lo muestra en las camaras
            }								// Fin del if de evento
        } catch (e) {}							// Ignora mensajes que no son JSON
    };									// Fin del manejo de eventos

    wsGeneral.onclose = (event) => {					// Cuando se cierra el WebSocket general
        if (event && event.code === 4003) return;			// Si el cierre fue por no autorizado, no reintenta
        setTimeout(connectGeneralWS, 5000);				// Reintenta conectar en 5 segundos
    };									// Fin del cierre del WebSocket
}									// Fin del WebSocket general

function showLastEventOnCameras() {					// Muestra el ultimo evento sobre las camaras
    if (!lastEventData) return;						// Si no hay evento, no hace nada

    const { message, status, type, plate } = lastEventData;		// Separa mensaje, estado, tipo y patente
    const isOk = status === 'ok';					// El evento fue exitoso
    const isWarning = status === 'warning';				// El evento es una advertencia
    const isReading = status === 'reading';				// El evento esta en proceso de lectura
    const msgUpper = (message || '').toUpperCase();			// Mensaje en mayusculas para el HUD

    camerasList.forEach((cam, idx) => {					// Recorre todas las camaras
        const slotId = idx + 1;						// Numero de slot de la camara
        const box = document.getElementById(`cctv-slot-${slotId}`);	// Celda de esa camara
        if (!box) return;						// Si no existe, sigue con la proxima

        // SALUDO GRANDE DE BIENVENIDA (INGRESO) / HASTA LUEGO (SALIDA) sobre el video
        if (isOk && (type === 'INGRESO' || type === 'SALIDA')) {	// Si fue un ingreso o salida exitoso
            const matchType = type === 'INGRESO' ? 'PATENTE_INGRESO' : 'PATENTE_EGRESO';
									// Tipo de camara que debe mostrar el saludo
            if (cam.tipo === matchType) {				// Si la camara coincide con el evento
                showCameraGreeting(box, type, plate || '');		// Muestra BIENVENIDO o HASTA LUEGO
                let eventLine = box.querySelector('.cctv-event-line');	// Linea de evento de la celda
                if (eventLine) {					// Si existe
                    if (eventLine._hideTimer) clearTimeout(eventLine._hideTimer);
									// Cancela el ocultamiento pendiente
                    eventLine.style.opacity = '0';			// La oculta para no tapar el saludo
                }							// Fin del if de linea
            }								// Fin del if de coincidencia
            return;							// No sigue con la linea de evento
        }								// Fin del if de ingreso/salida

        hideCameraGreeting(box);					// Quita el saludo si habia uno

        // LINEA DE EVENTO CENTRAL (HUD SOBRE EL VIDEO)
        // Solo se muestra para estados que NO son OK. Los OK (franja verde al
        // detectar) se suprimen para no tapar el video con la franja superior.
        let eventLine = box.querySelector('.cctv-event-line');		// Busca la linea de evento de la celda
        if (isOk) {							// Si el evento fue exitoso
            if (eventLine) {						// Si la linea existe
                if (eventLine._hideTimer) clearTimeout(eventLine._hideTimer);
									// Cancela el ocultamiento pendiente
                eventLine.style.opacity = '0';				// La oculta
            }								// Fin del if de linea
            return;							// No muestra la franja verde
        }								// Fin del if de evento exitoso

        if (!eventLine) {						// Si no existe la linea de evento
            eventLine = document.createElement('div');			// La crea
            eventLine.className = 'cctv-event-line';			// Le asigna la clase de linea
            box.appendChild(eventLine);					// La agrega a la celda
        }								// Fin de la creacion

        const stateClass = isWarning ? 'event-warning' : (isReading ? 'event-reading' : 'event-error');
									// Color segun advertencia, lectura o error
        eventLine.className = `cctv-event-line ${stateClass}`;		// Aplica la clase de estado
        const icon = isWarning ? '&#9888;' : (isReading ? '&#9203;' : '&#10007;');
									// Icono segun el estado

        eventLine.innerHTML = `<span class="event-icon">${icon}</span> ${msgUpper}`;
									// Pinta el icono y el mensaje

        if (eventLine._hideTimer) clearTimeout(eventLine._hideTimer);	// Cancela el ocultamiento pendiente
        eventLine.style.opacity = '1';					// Muestra la linea
        eventLine._hideTimer = setTimeout(() => {			// Programa su ocultamiento
            eventLine.style.opacity = '0';				// La oculta
        }, isReading ? 3000 : 7000);					// Dura 3 s si esta leyendo o 7 s si no
    });									// Fin del recorrido de camaras
}									// Fin del ultimo evento

// --- SALUDO GRANDE SOBRE EL VIDEO (BIENVENIDA / HASTA LUEGO) ---
const CAMERA_GREETINGS = { INGRESO: 'BIENVENIDO', SALIDA: 'HASTA LUEGO' };
									// Saludo segun el tipo de evento
const GREETING_MS = 4000;						// Duracion del saludo en pantalla (4 s)

function showCameraGreeting(box, type, plate) {				// Muestra el saludo grande en una celda
    let greeting = box.querySelector('.cctv-greeting');			// Busca el saludo existente
    if (!greeting) {							// Si no existe
        greeting = document.createElement('div');			// Lo crea
        greeting.className = 'cctv-greeting';				// Le asigna la clase de saludo
        box.appendChild(greeting);					// Lo agrega a la celda
    }									// Fin de la creacion
    greeting.classList.toggle('exit', type === 'SALIDA');		// Usa el estilo de salida si corresponde
									// Saludo grande sobre el video
									// Palabra: BIENVENIDO o HASTA LUEGO
									// Patente: se muestra si el evento la trae
    greeting.innerHTML = `
        <span class="greeting-word">${CAMERA_GREETINGS[type] || 'OK'}</span>
        ${plate ? `<span class="greeting-plate">${escapeHtml(plate)}</span>` : ''}
    `;									// Fin del HTML del saludo
    greeting.offsetHeight;						// Fuerza el navegador a recalcular el layout
    greeting.classList.add('show');					// Activa la animacion de aparicion
    if (greeting._hideTimer) clearTimeout(greeting._hideTimer);		// Cancela el ocultamiento pendiente
    greeting._hideTimer = setTimeout(() => {				// Programa quitar el saludo
        greeting.classList.remove('show');				// Quita la animacion
    }, GREETING_MS);							// Fin del timer de saludo
}									// Fin del saludo

function hideCameraGreeting(box) {					// Quita el saludo de una celda
    const greeting = box.querySelector('.cctv-greeting');		// Busca el saludo
    if (greeting) greeting.remove();					// Si existe, lo elimina
}									// Fin de quitar el saludo

// --- LOG EN VIVO DE LA CONSOLA DEL SUBPROCESO ALPR (ruta paralela a los mensajes actuales) ---

const MAX_CONSOLE_LINES = 12;						// Maximo de lineas visibles en la consola

function appendCameraConsoleLine(camId, line) {				// Agrega una linea al log de una camara
    const logEl = document.getElementById(`console-${camId}`);		// Caja de log de esa camara
    if (!logEl) return;							// Si no existe, no hace nada

    const isError = /(ERROR|EXCEPTION|FAIL|fatal|FATAL)/i.test(line);	// Detecta lineas de error
    const isSuccess = /(ACEPTADA|ACEITADA|ACEPTADO|BIENVENIDO|HASTA LUEGO|CODIGO QR LEIDO|INGRESO|SALIDA|\[OK\]|CONF: 0\.[5-9])/i.test(line);
									// Detecta lineas de exito o lectura aceptada

    const div = document.createElement('div');				// Crea el renglon del log
    if (isError) {							// Si es error
        div.className = 'cctv-console-line error';			// Lo pinta en rojo
    } else if (isSuccess) {						// Si es exito
        div.className = 'cctv-console-line success';			// Lo pinta en verde
    } else {								// Si es un mensaje normal
        div.className = 'cctv-console-line';				// Lo deja con el estilo normal
    }									// Fin del if de estilo
    div.textContent = line;						// Escribe el texto de la linea

    logEl.appendChild(div);						// Agrega el renglon al log
    while (logEl.children.length > MAX_CONSOLE_LINES) {			// Mientras haya mas lineas que el maximo
        logEl.removeChild(logEl.firstChild);				// Borra la mas vieja
    }									// Fin del recorte
    logEl.scrollTop = logEl.scrollHeight;				// Baja el scroll al final
}									// Fin de agregar linea
