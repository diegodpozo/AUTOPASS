// Mini-tour module: simple guided walkthrough for reservation flow
// Exposes startReservationTour() globally

// Tour for users who have 0 vehicles registered
const noVehiclesTourSteps = [
    {
        selector: '#section-vehiculos .welcome-card',
        title: '¡Bienvenido a AutoPass!',
        text: 'Para comenzar a realizar reservas en nuestras sucursales, primero necesitamos registrar la patente de tu vehículo.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
        }
    },
    {
        selector: '#vehicle-form-container',
        title: 'Registrá tu Vehículo',
        text: 'Desplegamos el formulario para que ingresés la patente y marca de tu vehículo. Pulsá CONTINUAR para darlo de alta.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
            const container = document.getElementById('vehicle-form-container');
            const trigger = document.getElementById('vehicle-form-trigger');
            if (container) {
                container.style.display = 'block';
                container.classList.add('open');
            }
            if (trigger) {
                trigger.style.display = 'none';
            }
        }
    },
    {
        selector: '#portal-map',
        title: 'Mapa de Sucursales',
        text: 'Mientras registrás tu vehículo, podés explorar la ubicación exacta de nuestras sucursales en este mapa interactivo.',
        align: 'left',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#section-puntos .points-main-card',
        title: 'Puntos AutoPass & Beneficios',
        text: 'En cada estadía que realicés acumulás puntos que podés canjear por cupones de descuento o estacionamientos gratis.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    {
        selector: '#section-puntos',
        title: '¡Listo para Empezar!',
        text: 'Una vez que registrés tu primer vehículo, el formulario de reservas quedará activo inmediatamente.',
        align: 'top',
        interactive: false,
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    }
];

// Main tour post vehicle creation (used in initial onboarding after user adds their first vehicle)
const mainTourSteps = [
    { 
        selector: '#reserva-form-container', 
        title: 'Formulario de Reserva', 
        text: '¡Excelente! Ahora que registraste tu vehículo, podés generar tu primera reserva: elegí sucursal y tipo de estadía.', 
        align: 'bottom', 
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
            const container = document.getElementById('reserva-form-container');
            if (container && !container.classList.contains('open') && window.toggleReservaForm) {
                try { window.toggleReservaForm(); } catch(e){}
            }
        }
    },
    { selector: '#reserva-form-content .res-vehicle', title: 'Seleccioná vehículo', text: 'Tu nuevo vehículo ya aparece seleccionado por defecto.', align: 'right', interactive: true },
    { selector: '.res-sucursal', title: 'Elegí punto', text: 'Seleccioná el punto AutoPass donde querés estacionar.', align: 'left', interactive: true },
    { selector: '.res-type', title: 'Tipo de estadía', text: 'Elegí si reservás por hora, día, semana, quincena o mes. Los campos cambiarán acorde al tipo.', align: 'left', interactive: true },
    { selector: '.reservation-footer-premium .btn-confirm-premium', title: 'Confirmar reserva', text: 'Revisá el total y pulsá "Continuar" para confirmar la reserva.', align: 'top', interactive: true },
    { selector: '#portal-map', title: 'Mapa y ubicación', text: 'En este mapa podés ver la ubicación de las sucursales y elegir una cercana.', align: 'left', interactive: false }
];

// Steps that run specifically inside 'Mis Reservas' after reservation is created
const reservationsTourSteps = [
    { 
        selector: '#reservation-featured-list, #reservation-list-active, #reservation-list-history', 
        title: 'Mis Reservas', 
        text: 'Acá verás tus reservas recientes y activas. Podés ver el pase digital, editar o cancelar según corresponda.', 
        align: 'top', 
        interactive: true, 
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
                window.showSection('reservas', navItem);
            }
        }
    },
    { selector: '.reserva-actions-ultra .btn-ultra.btn-ultra-primary, .reserva-card-ultra .btn-ultra.btn-ultra-primary', title: 'Acciones principales', text: 'Aquí podés ver el pase digital o pagar la reserva. Probá pulsar el botón principal para ver más opciones.', align: 'left', interactive: true, waitForEnabled: true },
    { selector: '.reserva-actions-ultra .btn-ultra.btn-ultra-secondary, .reserva-card-ultra .btn-ultra.btn-ultra-secondary', title: 'Editar reserva', text: 'Usá este botón para editar la reserva si necesitás cambiar fecha o sucursal.', align: 'left', interactive: true },
    { selector: '.reserva-actions-ultra .btn-ultra.btn-ultra-danger, .reserva-card-ultra .btn-ultra.btn-ultra-danger', title: 'Eliminar / Cancelar', text: 'Si querés cancelar la reserva, usá este botón. Te mostraremos la confirmación y posibles reembolsos.', align: 'left', interactive: true },
    { 
        selector: '.nav-item[onclick*="puntos"]', 
        title: 'Puntos AutoPass', 
        text: 'Al realizar reservas y estacionar, sumás puntos. Hacé click en "Mis Puntos" en el menú para ver tus beneficios.', 
        align: 'right', 
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
                window.showSection('reservas', navItem);
            }
        }
    },
    { 
        selector: '#section-puntos .points-main-card', 
        title: 'Tus Puntos', 
        text: 'Acá podés ver tus puntos AutoPass disponibles. ¡Acumulás 10 puntos por cada $1000 abonados en estadías!', 
        align: 'bottom', 
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    { 
        selector: '#section-puntos #promotions-grid', 
        title: 'Promociones y Canjes', 
        text: 'En esta sección tenés el catálogo de beneficios. Podés canjear tus puntos por cupones de descuento o estadías gratuitas.', 
        align: 'top', 
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    { 
        selector: '#section-puntos #pts-history-container', 
        title: 'Historial de Puntos', 
        text: 'Revisá los detalles de tus puntos ganados y canjeados en esta lista.', 
        align: 'top', 
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    { 
        selector: '#section-puntos', 
        title: '¡Felicitaciones!', 
        text: 'Completaste el recorrido por tu portal de cliente de AutoPass. ¡Ya estás listo para empezar a reservar!', 
        align: 'top', 
        interactive: false, 
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    }
];

// Steps that run for users who already have 1 or more vehicles added
const existingVehiclesTourSteps = [
    {
        selector: '#section-vehiculos .welcome-card',
        title: 'Mis Vehículos',
        text: '¡Aquí tenés registrada tu flota! Podés administrar tus autos, motos o camionetas y elegir tu vehículo favorito.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
        }
    },
    {
        selector: '#vehicle-form-container',
        title: '¿Agregar un Nuevo Vehículo?',
        text: 'Desplegamos el formulario por si querés agregar un nuevo vehículo a tu flota en este momento. Podés cargarlo ahora o pulsar "Continuar" para avanzar con el recorrido.',
        align: 'bottom',
        interactive: true,
        nextText: 'Continuar',
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
            const container = document.getElementById('vehicle-form-container');
            const trigger = document.getElementById('vehicle-form-trigger');
            if (container) {
                container.style.display = 'block';
                container.classList.add('open');
            }
            if (trigger) {
                trigger.style.display = 'none';
            }
        }
    },
    {
        selector: '#reserva-form-container',
        title: 'Reserva de Estacionamiento',
        text: 'En el menú Inicio podés generar reservas en cualquiera de las sucursales del sistema.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
            const container = document.getElementById('reserva-form-container');
            if (container && !container.classList.contains('open') && window.toggleReservaForm) {
                try { window.toggleReservaForm(); } catch(e){}
            }
        }
    },
    {
        selector: '#reserva-form-content .res-vehicle',
        title: 'Selección de Vehículo',
        text: 'Tu vehículo favorito ya estará seleccionado por defecto. Solo indicá la sucursal y el tipo de estadía.',
        align: 'right',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#portal-map',
        title: 'Mapa de Sucursales',
        text: 'Visualizá la ubicación geográfica exacta de nuestras sedes y consultá su disponibilidad en tiempo real.',
        align: 'left',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#reservation-featured-list, #reservation-list-active, #reservation-list-history, #section-reservas',
        title: 'Mis Reservas & Pase QR',
        text: 'Obtené tu Pase Digital QR para escanear en las barreras, editar datos o cancelar tu estadía.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
                window.showSection('reservas', navItem);
            }
        }
    },
    {
        selector: '#section-puntos .points-main-card',
        title: 'Puntos AutoPass & Beneficios',
        text: 'Sumás 10 puntos por cada $1000 abonados. Canjealos por cupones de descuento o estadías gratuitas.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    {
        selector: '#section-puntos',
        title: '¡Recorrido Completado!',
        text: '¡Excelente! Ya conocés todas las secciones principales de tu portal AutoPass.',
        align: 'top',
        interactive: false,
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    }
];

// active tour steps (mutable)
let tourSteps = noVehiclesTourSteps.slice();

let currentTourIndex = 0;
let tourOverlay = null;
let tourTooltip = null;
let tourArrow = null;
let positioningToken = 0;
let isPositioningActive = false;
let _savedTourSteps = null;
let _isQuickAddTour = false;
let reservationsTourInitialized = false;
let isTourActive = false;
let onboardingSessionActive = false;

function createTourElements() {
    // EVITAR DUPLICADOS EN EL DOM ELIMINANDO EL OVERLAY EXISTENTE SI HAY UNO
    const existingOverlay = document.getElementById('autopass-tour-overlay');
    if (existingOverlay) {
        existingOverlay.remove();
    }

    // overlay container using class from profile.css
    tourOverlay = document.createElement('div');
    tourOverlay.id = 'autopass-tour-overlay';
    tourOverlay.className = 'tour-overlay-svg';
    
    // Create SVG element for mask cutout
    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, 'svg');
    svg.id = 'autopass-tour-svg';
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';
    
    const path = document.createElementNS(svgNS, 'path');
    path.setAttribute('fill', 'rgba(0, 0, 0, 0.65)');
    path.setAttribute('fill-rule', 'evenodd');
    
    // Highlight rect overlay border glow
    const highlightRect = document.createElementNS(svgNS, 'rect');
    highlightRect.id = 'autopass-tour-highlight-rect';
    highlightRect.setAttribute('fill', 'none');
    highlightRect.setAttribute('stroke', '#C5A059');
    highlightRect.setAttribute('stroke-width', '2');
    highlightRect.setAttribute('rx', '10');
    highlightRect.setAttribute('ry', '10');
    highlightRect.style.display = 'none';
    highlightRect.style.filter = 'drop-shadow(0 0 8px rgba(197, 160, 89, 0.45))';
    highlightRect.style.transition = 'all 0.25s ease';

    svg.appendChild(path);
    svg.appendChild(highlightRect);
    tourOverlay.appendChild(svg);
    document.body.appendChild(tourOverlay);

    // tooltip
    tourTooltip = document.createElement('div');
    tourTooltip.id = 'autopass-tour-tooltip';
    tourTooltip.className = 'tour-tooltip-premium';
    tourOverlay.appendChild(tourTooltip);

    // arrow to point at target
    tourArrow = document.createElement('div');
    tourArrow.id = 'autopass-tour-arrow';
    tourArrow.className = 'tour-arrow-premium';
    tourOverlay.appendChild(tourArrow);

    // tooltip inner
    tourTooltip.innerHTML = `
        <button id="tour-close" class="tour-close-btn" aria-label="Cerrar tour" title="Cerrar tour">×</button>
        <div id="tour-title" class="tour-tooltip-title-premium"></div>
        <div id="tour-text" class="tour-tooltip-text-premium"></div>
        <div id="tour-buttons" class="tour-tooltip-buttons-premium">
            <button id="tour-prev" class="btn btn-outline">Anterior</button>
            <button id="tour-next" class="btn btn-primary">Siguiente</button>
            <button id="tour-end" class="btn btn-plain">Omitir</button>
        </div>
    `;

    document.getElementById('tour-prev').addEventListener('click', prevTourStep);
    document.getElementById('tour-next').addEventListener('click', nextTourStep);
    document.getElementById('tour-end').addEventListener('click', () => endTour(true));
    document.getElementById('tour-close').addEventListener('click', () => endTour(true));

    // Listen to resize and scroll to reposition tooltip
    window.addEventListener('resize', handleWindowReposition, { passive: true });
    window.addEventListener('scroll', handleWindowReposition, { passive: true });
    window.addEventListener('keydown', handleTourKeydown);
}

function handleTourKeydown(e) {
    if (!isTourActive || !tourOverlay || tourOverlay.style.display === 'none') return;
    if (e.key === 'Escape') {
        endTour(true);
    } else if (e.key === 'ArrowRight') {
        nextTourStep();
    } else if (e.key === 'ArrowLeft') {
        prevTourStep();
    }
}

function updateSvgCutout(rect) {
    const svg = document.getElementById('autopass-tour-svg');
    if (!svg) return;
    const path = svg.querySelector('path');
    const highlightRect = document.getElementById('autopass-tour-highlight-rect');
    if (!path) return;

    const w = window.innerWidth;
    const h = window.innerHeight;

    if (!rect || rect.width === 0 || rect.height === 0) {
        path.setAttribute('d', `M 0,0 L ${w},0 L ${w},${h} L 0,${h} Z`);
        if (highlightRect) highlightRect.style.display = 'none';
        return;
    }

    const padding = 8;
    const x = rect.left - padding;
    const y = rect.top - padding;
    const width = rect.width + (padding * 2);
    const height = rect.height + (padding * 2);
    const r = 10; // corner radius for cutout

    const innerW = Math.max(0, width - (r * 2));
    const innerH = Math.max(0, height - (r * 2));

    // Full screen outer path (clockwise) + cutout path (counter-clockwise)
    const outerPath = `M 0,0 h ${w} v ${h} h ${-w} z`;
    const cutoutPath = `
        M ${x + r},${y}
        h ${innerW}
        a ${r},${r} 0 0 1 ${r},${r}
        v ${innerH}
        a ${r},${r} 0 0 1 ${-r},${r}
        h ${-innerW}
        a ${r},${r} 0 0 1 ${-r},${-r}
        v ${-innerH}
        a ${r},${r} 0 0 1 ${r},${-r}
        z
    `.trim().replace(/\s+/g, ' ');

    path.setAttribute('d', `${outerPath} ${cutoutPath}`);

    // Update gold highlight border
    if (highlightRect) {
        highlightRect.setAttribute('x', x);
        highlightRect.setAttribute('y', y);
        highlightRect.setAttribute('width', width);
        highlightRect.setAttribute('height', height);
        highlightRect.style.display = 'block';
    }
}

function handleWindowReposition() {
    if (!tourOverlay || tourOverlay.style.display === 'none' || currentTourIndex === -1) return;
    if (isPositioningActive) return;
    isPositioningActive = true;
    requestAnimationFrame(() => {
        repositionActiveStep();
        isPositioningActive = false;
    });
}

function getVisibleTarget(selector) {
    if (!selector) return null;
    const parts = selector.split(',').map(s => s.trim());
    for (const sel of parts) {
        const elements = document.querySelectorAll(sel);
        for (const el of elements) {
            if (el && el.getBoundingClientRect) {
                const rect = el.getBoundingClientRect();
                const isVisible = (el.offsetWidth > 0 || el.offsetHeight > 0) && rect.width > 0 && rect.height > 0;
                if (isVisible) {
                    return el;
                }
            }
        }
    }
    return document.querySelector(parts[0]);
}

function repositionActiveStep() {
    if (currentTourIndex < 0 || currentTourIndex >= tourSteps.length) return;
    const step = tourSteps[currentTourIndex];
    if (!step) return;
    const target = getVisibleTarget(step.selector);
    if (!target) return;

    const rect = target.getBoundingClientRect();

    // SI EL PASO ES CENTRADO O EL ELEMENTO NO TIENE DIMENSIONES, POSICIONAMOS EN EL CENTRO
    if (step.center || (rect.width === 0 && rect.height === 0)) {
        updateSvgCutout(null);
        tourTooltip.style.position = 'fixed';
        tourTooltip.style.left = '50%';
        tourTooltip.style.top = '50%';
        tourTooltip.style.transform = 'translate(-50%, -50%)';
        if (tourArrow) {
            tourArrow.classList.remove('active');
            tourArrow.style.display = 'none';
        }
        return;
    }

    updateSvgCutout(rect);

    tourTooltip.style.position = 'fixed';
    tourTooltip.style.transform = '';

    const padding = 8;
    const targetLeft = rect.left - padding;
    const targetTop = rect.top - padding;
    const targetWidth = rect.width + (padding * 2);
    const targetHeight = rect.height + (padding * 2);

    const tooltipWidth = tourTooltip.offsetWidth || 320;
    const tooltipHeight = tourTooltip.offsetHeight || 160;

    const vw = window.innerWidth;
    const vh = window.innerHeight;

    // Adaptación responsive: en pantallas angostas (< 680px) priorizar top/bottom
    let effectiveAlign = step.align || 'bottom';
    if (vw < 680 && (effectiveAlign === 'left' || effectiveAlign === 'right')) {
        effectiveAlign = (targetTop + targetHeight / 2 > vh / 2) ? 'top' : 'bottom';
    }

    let ttLeft = targetLeft + (targetWidth / 2) - (tooltipWidth / 2);
    let ttTop = targetTop + targetHeight + 14; // default: bottom

    if (effectiveAlign === 'top') {
        ttTop = targetTop - tooltipHeight - 14;
    } else if (effectiveAlign === 'left') {
        ttLeft = targetLeft - tooltipWidth - 14;
        ttTop = targetTop + (targetHeight / 2) - (tooltipHeight / 2);
    } else if (effectiveAlign === 'right') {
        ttLeft = targetLeft + targetWidth + 14;
        ttTop = targetTop + (targetHeight / 2) - (tooltipHeight / 2);
    }

    // Fallbacks si se sale verticalmente del viewport
    if (effectiveAlign === 'top' && ttTop < 12) {
        ttTop = targetTop + targetHeight + 14;
        effectiveAlign = 'bottom';
    } else if (effectiveAlign === 'bottom' && ttTop + tooltipHeight > vh - 12) {
        if (targetTop - tooltipHeight - 14 > 12) {
            ttTop = targetTop - tooltipHeight - 14;
            effectiveAlign = 'top';
        }
    }

    // Clampar posición del tooltip strictly dentro del viewport
    const margin = 12;
    const finalLeft = Math.max(margin, Math.min(ttLeft, vw - tooltipWidth - margin));
    const finalTop = Math.max(margin, Math.min(ttTop, vh - tooltipHeight - margin));

    tourTooltip.style.left = finalLeft + 'px';
    tourTooltip.style.top = finalTop + 'px';

    // Posicionar flecha indicadora
    if (tourArrow) {
        tourArrow.style.display = 'block';
        tourArrow.style.position = 'fixed';
        tourArrow.className = 'tour-arrow-premium active';
        tourArrow.style.borderLeft = '';
        tourArrow.style.borderRight = '';
        tourArrow.style.borderTop = '';
        tourArrow.style.borderBottom = '';

        const arrowSize = 10;
        const targetCenterX = targetLeft + (targetWidth / 2);
        const targetCenterY = targetTop + (targetHeight / 2);

        if (effectiveAlign === 'top') {
            tourArrow.style.borderLeft = `${arrowSize}px solid transparent`;
            tourArrow.style.borderRight = `${arrowSize}px solid transparent`;
            tourArrow.style.borderTop = `${arrowSize}px solid rgba(11, 11, 11, 0.92)`;

            let arrowLeft = targetCenterX - arrowSize;
            arrowLeft = Math.max(finalLeft + 16, Math.min(arrowLeft, finalLeft + tooltipWidth - 16 - (arrowSize * 2)));

            tourArrow.style.left = arrowLeft + 'px';
            tourArrow.style.top = (finalTop + tooltipHeight) + 'px';
        } else if (effectiveAlign === 'left') {
            tourArrow.style.borderTop = `${arrowSize}px solid transparent`;
            tourArrow.style.borderBottom = `${arrowSize}px solid transparent`;
            tourArrow.style.borderLeft = `${arrowSize}px solid rgba(11, 11, 11, 0.92)`;

            let arrowTop = targetCenterY - arrowSize;
            arrowTop = Math.max(finalTop + 16, Math.min(arrowTop, finalTop + tooltipHeight - 16 - (arrowSize * 2)));

            tourArrow.style.left = (finalLeft + tooltipWidth) + 'px';
            tourArrow.style.top = arrowTop + 'px';
        } else if (effectiveAlign === 'right') {
            tourArrow.style.borderTop = `${arrowSize}px solid transparent`;
            tourArrow.style.borderBottom = `${arrowSize}px solid transparent`;
            tourArrow.style.borderRight = `${arrowSize}px solid rgba(11, 11, 11, 0.92)`;

            let arrowTop = targetCenterY - arrowSize;
            arrowTop = Math.max(finalTop + 16, Math.min(arrowTop, finalTop + tooltipHeight - 16 - (arrowSize * 2)));

            tourArrow.style.left = (finalLeft - (arrowSize * 2)) + 'px';
            tourArrow.style.top = arrowTop + 'px';
        } else {
            // default: bottom
            tourArrow.style.borderLeft = `${arrowSize}px solid transparent`;
            tourArrow.style.borderRight = `${arrowSize}px solid transparent`;
            tourArrow.style.borderBottom = `${arrowSize}px solid rgba(11, 11, 11, 0.92)`;

            let arrowLeft = targetCenterX - arrowSize;
            arrowLeft = Math.max(finalLeft + 16, Math.min(arrowLeft, finalLeft + tooltipWidth - 16 - (arrowSize * 2)));

            tourArrow.style.left = arrowLeft + 'px';
            tourArrow.style.top = (finalTop - (arrowSize * 2)) + 'px';
        }
    }
}

let activeResizeObserver = null;

async function showTourStep(index) {
    currentTourIndex = index;

    if (index < 0) index = 0;
    if (index >= tourSteps.length) return endTour();

    const step = tourSteps[index];
    if (!step) return;

    if (activeResizeObserver) {
        try { activeResizeObserver.disconnect(); } catch(e){}
        activeResizeObserver = null;
    }

    // EJECUTAR ACCIONES DE PREPARACION SI ESTAN DEFINIDAS PARA EL PASO
    if (typeof step.beforeShow === 'function') {
        try {
            const res = step.beforeShow();
            if (res && typeof res.then === 'function') {
                await res;
            }
        } catch (e) { console.warn('[TOUR] Error en beforeShow del paso:', e); }
    }

    // update tooltip content
    document.getElementById('tour-title').innerText = step.title || '';
    document.getElementById('tour-text').innerText = step.text || '';

    // hide elements temporarily to avoid layout jumps
    if (tourTooltip) {
        tourTooltip.classList.remove('active');
    }
    if (tourArrow) {
        tourArrow.classList.remove('active');
    }

    // configure interactivity using pointerEvents on the SVG path
    if (step.interactive) {
        tourOverlay.classList.add('interactive');
    } else {
        tourOverlay.classList.remove('interactive');
    }

    const waitForVisible = (sel, attempts = 0) => {
        const target = getVisibleTarget(sel);
        if (target) {
            const rect = target.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) {
                return target;
            }
        }
        if (attempts >= 12) return null;
        return new Promise(resolve => setTimeout(() => resolve(waitForVisible(sel, attempts + 1)), 150));
    };

    positioningToken = (typeof positioningToken === 'number' ? positioningToken + 1 : 1);
    const myToken = positioningToken;

    Promise.resolve(waitForVisible(step.selector)).then(async (resolvedTarget) => {
        if (myToken !== positioningToken) return;

        if (!resolvedTarget) {
            console.warn('[TOUR] Target no visible ni encontrado, saltando paso:', step.selector);
            if (index < tourSteps.length - 1) return showTourStep(index + 1);
            return endTour();
        }

        if (window.ResizeObserver && resolvedTarget) {
            try {
                activeResizeObserver = new ResizeObserver(() => {
                    if (myToken === positioningToken) {
                        repositionActiveStep();
                    }
                });
                activeResizeObserver.observe(resolvedTarget);
                if (resolvedTarget.parentElement) {
                    activeResizeObserver.observe(resolvedTarget.parentElement);
                }
            } catch(e){}
        }

        // Scroll suave al objetivo solo si no está en el viewport
        if (!step.center) {
            try {
                const rect = resolvedTarget.getBoundingClientRect();
                const isVisible = (rect.top >= 0) && (rect.bottom <= window.innerHeight);
                if (!isVisible) {
                    resolvedTarget.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            } catch (e) {}
        }

        // Animación suave de posicionamiento mientras se realiza el scroll
        let frameCount = 0;
        const trackScroll = () => {
            if (myToken !== positioningToken) return;
            repositionActiveStep();
            frameCount++;
            if (frameCount < 40) {
                requestAnimationFrame(trackScroll);
            }
        };

        requestAnimationFrame(trackScroll);

        // Re-verificaciones de respaldo para renderizado asíncrono
        setTimeout(() => { if (myToken === positioningToken) repositionActiveStep(); }, 300);
        setTimeout(() => { if (myToken === positioningToken) repositionActiveStep(); }, 650);

        // Mostrar elementos con transición
        setTimeout(() => {
            if (myToken !== positioningToken) return;
            repositionActiveStep();
            tourTooltip.classList.add('active');
            if (tourArrow && !step.center) {
                tourArrow.classList.add('active');
            }
        }, 120);
    });

    // buttons setup
    document.getElementById('tour-prev').disabled = index === 0;
    document.getElementById('tour-next').innerText = index === tourSteps.length - 1 ? 'Finalizar' : (step.nextText || 'Siguiente');
    const endBtn = document.getElementById('tour-end');
    if (endBtn) endBtn.style.display = (index === 0) ? 'inline-block' : 'none';

    // focus element if interactive
    if (step.interactive) {
        try {
            const focusable = (target.querySelector && (target.querySelector('select, input, button, textarea'))) || target;
            if (focusable && typeof focusable.focus === 'function') focusable.focus();
        } catch (e) {}
    }
}

// Auto-advance change handlers
function handleVehicleChange() {
    const step = tourSteps[currentTourIndex];
    if (step && step.selector.includes('.res-vehicle')) {
        setTimeout(nextTourStep, 250);
    }
}

function handleSucursalChange() {
    const step = tourSteps[currentTourIndex];
    if (step && step.selector.includes('.res-sucursal')) {
        setTimeout(nextTourStep, 250);
    }
}

function handleTypeChange() {
    const step = tourSteps[currentTourIndex];
    if (step && step.selector.includes('.res-type')) {
        setTimeout(nextTourStep, 250);
    }
}

// Auto-advance click handler para nav item de puntos
function handlePuntosNavClick() {
    const step = tourSteps[currentTourIndex];
    if (step && step.selector.includes('puntos')) {
        setTimeout(nextTourStep, 250);
    }
}

function startTourAutoAdvance() {
    const vehicleSelect = document.querySelector('#reserva-form-content .res-vehicle');
    const sucursalSelect = document.querySelector('.res-sucursal');
    const typeSelect = document.querySelector('.res-type');
    const puntosNavItem = document.querySelector('.nav-item[onclick*="puntos"]');

    if (vehicleSelect) {
        vehicleSelect.addEventListener('change', handleVehicleChange);
    }
    if (sucursalSelect) {
        sucursalSelect.addEventListener('change', handleSucursalChange);
    }
    if (typeSelect) {
        typeSelect.addEventListener('change', handleTypeChange);
    }
    if (puntosNavItem) {
        puntosNavItem.addEventListener('click', handlePuntosNavClick);
    }
}

function stopTourAutoAdvance() {
    const vehicleSelect = document.querySelector('#reserva-form-content .res-vehicle');
    const sucursalSelect = document.querySelector('.res-sucursal');
    const typeSelect = document.querySelector('.res-type');
    const puntosNavItem = document.querySelector('.nav-item[onclick*="puntos"]');

    if (vehicleSelect) {
        vehicleSelect.removeEventListener('change', handleVehicleChange);
    }
    if (sucursalSelect) {
            sucursalSelect.removeEventListener('change', handleSucursalChange);
    }
    if (typeSelect) {
        typeSelect.removeEventListener('change', handleTypeChange);
    }
    if (puntosNavItem) {
        puntosNavItem.removeEventListener('click', handlePuntosNavClick);
    }
}

// Manual tour steps for users with 0 vehicles (launched manually from Ayuda y Soporte)
const noVehiclesHelpTourSteps = [
    {
        selector: '#section-ayuda .help-hero-card, #section-ayuda',
        title: '¡Bienvenido al Tour de la App!',
        text: 'Te guiaremos paso a paso por todas las funciones de AutoPass: Alta de vehículo, Reservas, Mapa, Saldo, Puntos, Notificaciones y Soporte.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    },
    {
        selector: '#quick-add-form-container, #reserva-no-vehicles, #section-inicio',
        title: '1. Registrá tu Primer Vehículo',
        text: 'Como aún no tenés vehículos vinculados, desde este formulario en Inicio podés dar de alta tu primer auto, moto o camioneta ingresando patente y marca.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
            if (window.showQuickAddVehicle) {
                try { window.showQuickAddVehicle(); } catch(e){}
            }
        }
    },
    {
        selector: '#portal-map',
        title: 'Mapa Interactivo & Disponibilidad',
        text: 'Ubicá nuestras sucursales en el mapa y fijate si tienen lugar disponible mirando el color de cada sede.',
        align: 'left',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#section-vehiculos .welcome-card, #section-vehiculos',
        title: '2. Sección Mis Vehículos',
        text: 'En esta pestaña podrás administrar toda tu flota registrada, modificar patentes y elegir tu vehículo favorito.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
        }
    },
    {
        selector: '#section-reservas',
        title: '3. Mis Reservas & Pase Digital QR',
        text: 'Consultá tus reservas activas e historial. Cada reserva genera un Pase Digital con Código QR para mostrar en la entrada si la cámara no lee bien tu patente.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
                window.showSection('reservas', navItem);
            }
        }
    },
    {
        selector: '.balance-badge',
        title: '4. Billetera Virtual & Saldo',
        text: 'Mantené saldo disponible en tu Billetera Virtual AutoPass para agilizar tus ingresos y pagar estadías sin ingresar tarjetas cada vez.',
        align: 'bottom',
        interactive: true
    },
    {
        selector: '#section-puntos .points-main-card, #section-puntos .points-overview-grid',
        title: '5. Puntos AutoPass & Beneficios',
        text: 'Acumulás 10 puntos por cada $1000 abonados. Canjealos en esta sección por cupones de descuento o estadías 100% gratuitas.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    {
        selector: '#section-notificaciones',
        title: '6. Centro de Notificaciones',
        text: 'Acá recibirás avisos en tiempo real sobre confirmaciones de pago, recordatorios previos a tu reserva y respuestas de soporte.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="notificaciones"]');
                window.showSection('notificaciones', navItem);
            }
        }
    },
    {
        selector: '#section-ayuda #soporte-section, #section-ayuda .help-ticket-card, #section-ayuda',
        title: '7. Atención & Tickets de Soporte',
        text: 'Si tenés alguna duda o inconveniente en una sucursal, podés enviarnos un Ticket de Soporte directo a la administración o buscar en las FAQ.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    },
    {
        selector: '#section-ayuda .help-hero-card, #section-ayuda',
        title: '¡Recorrido Completado!',
        text: '¡Excelente! Ya conocés todas las secciones de tu portal AutoPass. Al registrar tu primer vehículo, el formulario de reservas quedará completamente activo.',
        align: 'bottom',
        interactive: false,
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    }
];

// Manual tour steps for users with 1+ vehicles (launched manually from Ayuda y Soporte)
const existingVehiclesHelpTourSteps = [
    {
        selector: '#section-ayuda .help-hero-card, #section-ayuda',
        title: '¡Bienvenido al Tour de la App!',
        text: 'Te guiaremos paso a paso por todas las funciones de AutoPass: Vehículos, Reservas, Pase QR, Saldo, Puntos, Notificaciones y Soporte.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    },
    {
        selector: '#section-vehiculos .welcome-card, #section-vehiculos',
        title: '1. Mis Vehículos & Flota',
        text: 'Como ya tenés vehículos registrados, acá podés administrar tu flota de Autos, Motos y Camionetas y seleccionar tu vehículo favorito.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
        }
    },
    {
        selector: '#vehicle-form-container, #section-vehiculos',
        title: 'Alta de Nuevos Vehículos',
        text: 'Desplegando este formulario podés agregar nuevos vehículos a tu flota ingresando la patente y marca.',
        align: 'bottom',
        interactive: true,
        nextText: 'Continuar',
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
                window.showSection('vehiculos', navItem);
            }
            const container = document.getElementById('vehicle-form-container');
            const trigger = document.getElementById('vehicle-form-trigger');
            if (container) {
                container.style.display = 'block';
                container.classList.add('open');
            }
            if (trigger) {
                trigger.style.display = 'none';
            }
        }
    },
    {
        selector: '#reserva-form-content, #reserva-form-container, #section-inicio',
        title: '2. Formulario de Reserva',
        text: 'En la sección Inicio podés seleccionar tu vehículo y generar reservas por Hora, Día, Semana, Quincena o Mes cotizando en tiempo real.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#portal-map',
        title: 'Mapa Interactivo & Disponibilidad',
        text: 'Ubicá nuestras sucursales en el mapa y fijate si tienen lugar disponible mirando el color de cada sede.',
        align: 'left',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
                window.showSection('inicio', navItem);
            }
        }
    },
    {
        selector: '#section-reservas',
        title: '3. Mis Reservas & Pase Digital QR',
        text: 'Consultá tus reservas activas e historial. Cada reserva te da un Pase Digital con Código QR para mostrar en la entrada si la cámara no reconoce tu patente.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
                window.showSection('reservas', navItem);
            }
        }
    },
    {
        selector: '.balance-badge',
        title: '4. Billetera Virtual & Saldo',
        text: 'Mantené saldo disponible en tu Billetera Virtual AutoPass para agilizar tus ingresos y pagar estadías sin ingresar tarjetas cada vez.',
        align: 'bottom',
        interactive: true
    },
    {
        selector: '#section-puntos .points-main-card, #section-puntos .points-overview-grid',
        title: '5. Puntos AutoPass & Beneficios',
        text: 'Acumulás 10 puntos por cada $1000 abonados. Canjealos en esta sección por cupones de descuento o estadías 100% gratuitas.',
        align: 'bottom',
        interactive: false,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
                window.showSection('puntos', navItem);
            }
        }
    },
    {
        selector: '#section-notificaciones',
        title: '6. Centro de Notificaciones',
        text: 'Acá recibirás avisos en tiempo real sobre confirmaciones de pago, recordatorios previos a tu reserva y respuestas de soporte.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="notificaciones"]');
                window.showSection('notificaciones', navItem);
            }
        }
    },
    {
        selector: '#section-ayuda #soporte-section, #section-ayuda .help-ticket-card, #section-ayuda',
        title: '7. Atención & Tickets de Soporte',
        text: 'Si tenés alguna duda o inconveniente en una sucursal, podés enviarnos un Ticket de Soporte directo a la administración o buscar en las FAQ.',
        align: 'bottom',
        interactive: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    },
    {
        selector: '#section-ayuda .help-hero-card, #section-ayuda',
        title: '¡Recorrido Completado!',
        text: '¡Felicitaciones! Ya conocés todas las herramientas del portal AutoPass. Podés volver a realizar este tour cuando lo necesites.',
        align: 'bottom',
        interactive: false,
        center: true,
        beforeShow: () => {
            if (window.showSection) {
                const navItem = document.querySelector('.nav-item[onclick*="ayuda"]');
                window.showSection('ayuda', navItem);
            }
        }
    }
];

// --- INTERACTIVE FEATURE TOURS FOR SPECIFIC MODULES ---

const ensureVehicleFormOpen = () => {
    if (window.showSection) {
        const navItem = document.querySelector('.nav-item[onclick*="vehiculos"]');
        window.showSection('vehiculos', navItem);
    }
    const container = document.getElementById('vehicle-form-container');
    const trigger = document.getElementById('vehicle-form-trigger');
    if (container) {
        container.style.display = 'block';
        container.classList.add('open');
    }
    if (trigger) trigger.style.display = 'none';
};

const addVehicleTourSteps = [
    {
        selector: '#section-vehiculos .welcome-card, #section-vehiculos',
        title: '¡Alta de Vehículo!',
        text: 'En esta sección podés administrar tu flota. Te guiaremos paso a paso para dar de alta tu auto, moto o camioneta en tiempo real.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    },
    {
        selector: '#vehicle-form-container, #add-vehicle-form, #section-vehiculos',
        title: '1. Formulario de Registro',
        text: 'Desplegamos el formulario para que ingresés los datos de tu vehículo.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    },
    {
        selector: '#add-vehicle-form select[name="tipo"], #quick-add-vehicle-form select[name="tipo"], select[name="tipo"]',
        title: '2. Categoría de Vehículo',
        text: 'Elegí la categoría de tu vehículo: Auto, Moto o Camioneta. Así se calcula la tarifa correcta.',
        align: 'right',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    },
    {
        selector: '#add-vehicle-form input[name="patente"], #quick-add-vehicle-form input[name="patente"], input[name="patente"]',
        title: '3. Ingresá la Patente',
        text: 'Escribí la patente de tu vehículo. Usá el formato oficial (ej: ABC 123 o AB 123 CD).',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    },
    {
        selector: '#add-vehicle-form input[name="marca_modelo"], #quick-add-vehicle-form input[name="marca_modelo"], input[name="marca_modelo"]',
        title: '4. Marca y Modelo',
        text: 'Escribí la marca y modelo para identificarlo en tu lista de flota.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    },
    {
        selector: '#add-vehicle-form button[type="submit"], #quick-add-vehicle-form button[type="submit"]',
        title: '5. Confirmá el Alta',
        text: 'Hacé click en "CONTINUAR" para registrar tu vehículo en vivo. Al completar la acción aparecerá en tu flota.',
        align: 'top',
        interactive: true,
        beforeShow: ensureVehicleFormOpen
    }
];

const ensureReservationFormOpen = () => {
    if (window.showSection) {
        const navItem = document.querySelector('.nav-item[onclick*="inicio"]');
        window.showSection('inicio', navItem);
    }
    const container = document.getElementById('reserva-form-container');
    if (container && !container.classList.contains('open') && window.toggleReservaForm) {
        try { window.toggleReservaForm(); } catch(e){}
    }
};

const createReservationTourSteps = [
    {
        selector: '#section-inicio .welcome-card, #section-inicio',
        title: '¡Crear una Reserva!',
        text: 'En el menú Inicio podés generar reservas en cualquiera de las sucursales de AutoPass cotizando en tiempo real.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    },
    {
        selector: '#reserva-form-container, #section-inicio',
        title: '1. Formulario de Reserva',
        text: 'Acá tenés el formulario interactivo. Elegí tu vehículo, la sucursal y el tipo de estadía.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    },
    {
        selector: '#reserva-form-content .res-vehicle, .res-vehicle',
        title: '2. Seleccioná tu Vehículo',
        text: 'Elegí con qué patente de tu flota vas a realizar la reserva.',
        align: 'right',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    },
    {
        selector: '.res-sucursal',
        title: '3. Elegí la Sucursal',
        text: 'Seleccioná la sede AutoPass donde querés estacionar.',
        align: 'left',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    },
    {
        selector: '.res-type',
        title: '4. Tipo de Estadía',
        text: 'Elegí si reservás por Hora, Día, Semana, Quincena o Mes. Verás cómo la tarifa estimada se actualiza al instante.',
        align: 'left',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    },
    {
        selector: '.reservation-footer-premium .btn-confirm-premium, #reserva-form-content button[type="submit"]',
        title: '5. Confirmar Reserva',
        text: 'Revisá la cotización y pulsá "CONTINUAR" para generar tu reserva y obtener tu Pase QR.',
        align: 'top',
        interactive: true,
        beforeShow: ensureReservationFormOpen
    }
];

const ensureRechargeModalOpen = () => {
    if (window.openRechargeModal) window.openRechargeModal();
};

const rechargeBalanceTourSteps = [
    {
        selector: '.balance-badge',
        title: '¡Billetera Virtual & Saldo!',
        text: 'Tu saldo te permite ingresar a las sucursales rápido y sin usar tarjetas. Te mostramos cómo cargar saldo.',
        align: 'bottom',
        interactive: true
    },
    {
        selector: '#rechargeModal .modal-content, #rechargeModal',
        title: '1. Modal de Carga de Saldo',
        text: 'Desplegamos el modal de recarga. Podés interactuar con los botones de monto predefinidos o ingresar un importe.',
        align: 'center',
        interactive: true,
        beforeShow: ensureRechargeModalOpen
    },
    {
        selector: '#recharge-amount, #rechargeModal .recharge-preset-btn',
        title: '2. Seleccioná o Ingresá el Monto',
        text: 'Hacé click en un monto sugerido (ej: $5.000) o escribí la cifra que querés cargar.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensureRechargeModalOpen
    },
    {
        selector: '#rechargeModal button[type="submit"]',
        title: '3. Confirmá la Carga',
        text: 'Hacé click en "INGRESAR SALDO" y el dinero se acreditará en tu billetera al instante.',
        align: 'top',
        interactive: true,
        beforeShow: ensureRechargeModalOpen
    }
];

const ensurePointsTabOpen = () => {
    if (window.showSection) {
        const navItem = document.querySelector('.nav-item[onclick*="puntos"]');
        window.showSection('puntos', navItem);
    }
};

const redeemPointsTourSteps = [
    {
        selector: '#section-puntos .points-main-card, #section-puntos',
        title: '¡Puntos AutoPass & Beneficios!',
        text: 'Acumulás 10 puntos por cada $1000 abonados. Te mostramos cómo ver tus puntos y canjear premios.',
        align: 'bottom',
        interactive: true,
        beforeShow: ensurePointsTabOpen
    },
    {
        selector: '#points-progress-bar, #section-puntos .points-overview-grid, #section-puntos',
        title: '1. Tus Puntos & Progreso',
        text: 'Acá podés ver tus puntos acumulados y tu avance hacia el próximo beneficio.',
        align: 'bottom',
        interactive: false,
        beforeShow: ensurePointsTabOpen
    },
    {
        selector: '#section-puntos #promotions-grid, #promotions-grid, #section-puntos',
        title: '2. Catálogo de Promociones',
        text: 'Explorá los cupones activos. Podés canjear tus puntos por descuentos o estadías gratuitas.',
        align: 'top',
        interactive: true,
        beforeShow: ensurePointsTabOpen
    },
    {
        selector: '.promo-card .btn-redeem, #promotions-grid, #section-puntos',
        title: '3. Canjear Beneficio',
        text: 'Cuando tengas puntos suficientes, pulsá "CANJEAR" en el beneficio que prefieras.',
        align: 'top',
        interactive: true,
        beforeShow: ensurePointsTabOpen
    }
];

const ensureReservationsTabOpen = () => {
    if (window.showSection) {
        const navItem = document.querySelector('.nav-item[onclick*="reservas"]');
        window.showSection('reservas', navItem);
    }
};

const ensureDigitalPassModalOpen = async () => {
    ensureReservationsTabOpen();
    const modal = document.getElementById('modal-pase-digital');
    if (modal) {
        // Garantizar visibilidad inmediata en 0ms para evitar parpadeo o cierre/reapertura
        modal.style.display = 'flex';

        // 1. Buscar botón que invoque directamente showDigitalPass
        const passBtn = document.querySelector('button[onclick*="showDigitalPass"]');
        if (passBtn) {
            const match = passBtn.getAttribute('onclick')?.match(/\d+/);
            if (match && typeof window.showDigitalPass === 'function') {
                try { await window.showDigitalPass(parseInt(match[0], 10)); return; } catch(e){}
            }
        }

        // 2. Buscar si hay reservas en memoria
        if (window.userReservations && Array.isArray(window.userReservations) && window.userReservations.length > 0) {
            const firstRes = window.userReservations[0];
            if (typeof window.showDigitalPass === 'function') {
                try { await window.showDigitalPass(firstRes.id); return; } catch(e){}
            }
        }

        // 3. Fallback directo con QR listo
        const idDisp = document.getElementById('ticket-id-display');
        if (idDisp) idDisp.innerText = '#000001';
        const patenteDisp = document.getElementById('ticket-patente');
        if (patenteDisp) patenteDisp.innerText = 'AA 123 BB';
        const venceDisp = document.getElementById('ticket-vence');
        if (venceDisp) venceDisp.innerText = 'Hoy, 23:59hs';
        const sucursalDisp = document.getElementById('ticket-sucursal');
        if (sucursalDisp) sucursalDisp.innerText = 'AutoPass Central';
        const dirDisp = document.getElementById('ticket-direccion');
        if (dirDisp) dirDisp.innerText = 'Av. Corrientes 1234';

        const qrContainer = document.getElementById('ticket-qr');
        if (qrContainer && window.QRCode && qrContainer.children.length === 0) {
            qrContainer.innerHTML = '';
            try { new QRCode(qrContainer, { text: 'AUTOPASS|DEMO|PLATE:AA123BB', width: 180, height: 180 }); } catch(e){}
        }
    }
};

const qrPassTourSteps = [
    {
        selector: 'button[onclick*="showDigitalPass"], #section-reservas .btn-ultra-primary, #section-reservas .reserva-card-ultra, #section-reservas',
        title: 'Pase Digital QR',
        text: 'Hacé click en "MI PASE DIGITAL" en tu reserva para desplegar el ticket de acceso.',
        align: 'top',
        interactive: true,
        beforeShow: () => {
            ensureReservationsTabOpen();
        }
    },
    {
        selector: '#modal-pase-digital .ticket-qr-section, #ticket-qr, #modal-pase-digital',
        title: '1. Código QR para Tótems',
        text: 'Este recuadro contiene tu código QR. Mostralo en la entrada si la cámara no reconoce tu patente.',
        align: 'right',
        interactive: true,
        beforeShow: ensureDigitalPassModalOpen
    },
    {
        selector: '#modal-pase-digital .ticket-info-grid, #modal-pase-digital',
        title: '2. Datos de la Estadía',
        text: 'Acá verificás los datos clave de tu reserva: Patente registrada, fecha de vencimiento, sucursal y dirección exacta.',
        align: 'left',
        interactive: true,
        beforeShow: ensureDigitalPassModalOpen
    },
    {
        selector: '#modal-pase-digital .btn-download, #modal-pase-digital .ticket-actions, #modal-pase-digital',
        title: '3. Compartir / Descargar Pase',
        text: 'Pulsá "COMPARTIR PASE" para generar una imagen PNG del ticket. Podés guardarla en tu celular o enviársela por WhatsApp a quien vaya a usar el vehículo.',
        align: 'top',
        interactive: true,
        beforeShow: ensureDigitalPassModalOpen
    }
];

export function startAddVehicleTour() {
    isTourActive = true;
    onboardingSessionActive = true;
    tourSteps = addVehicleTourSteps.slice();
    if (!tourOverlay) createTourElements();
    tourOverlay.style.display = 'block';
    setTimeout(() => {
        tourOverlay.classList.add('active');
        startTourAutoAdvance();
        showTourStep(0);
    }, 15);
}
window.startAddVehicleTour = startAddVehicleTour;

export function startQrPassTour() {
    isTourActive = true;
    onboardingSessionActive = true;
    tourSteps = qrPassTourSteps.slice();
    if (!tourOverlay) createTourElements();
    tourOverlay.style.display = 'block';
    setTimeout(() => {
        tourOverlay.classList.add('active');
        startTourAutoAdvance();
        showTourStep(0);
    }, 15);
}
window.startQrPassTour = startQrPassTour;

export function startCreateReservationTour() {
    isTourActive = true;
    onboardingSessionActive = true;
    tourSteps = createReservationTourSteps.slice();
    if (!tourOverlay) createTourElements();
    tourOverlay.style.display = 'block';
    setTimeout(() => {
        tourOverlay.classList.add('active');
        startTourAutoAdvance();
        showTourStep(0);
    }, 15);
}
window.startCreateReservationTour = startCreateReservationTour;

export function startRechargeBalanceTour() {
    isTourActive = true;
    onboardingSessionActive = true;
    tourSteps = rechargeBalanceTourSteps.slice();
    if (!tourOverlay) createTourElements();
    tourOverlay.style.display = 'block';
    setTimeout(() => {
        tourOverlay.classList.add('active');
        startTourAutoAdvance();
        showTourStep(0);
    }, 15);
}
window.startRechargeBalanceTour = startRechargeBalanceTour;

export function startRedeemPointsTour() {
    isTourActive = true;
    onboardingSessionActive = true;
    tourSteps = redeemPointsTourSteps.slice();
    if (!tourOverlay) createTourElements();
    tourOverlay.style.display = 'block';
    setTimeout(() => {
        tourOverlay.classList.add('active');
        startTourAutoAdvance();
        showTourStep(0);
    }, 15);
}
window.startRedeemPointsTour = startRedeemPointsTour;

export function startReservationTour(startIndex = 0) {
    // MARCAR QUE EL TOUR ESTA ACTIVO
    isTourActive = true;
    onboardingSessionActive = true;

    // Determinar si el usuario ya cuenta con vehículos registrados
    const vehiclesCount = (window.userVehicles && Array.isArray(window.userVehicles))
        ? window.userVehicles.length
        : document.querySelectorAll('#vehicle-list .vehicle-card').length;

    if (vehiclesCount > 0) {
        tourSteps = existingVehiclesHelpTourSteps.slice();
    } else {
        tourSteps = noVehiclesHelpTourSteps.slice();
    }

    if (!tourOverlay) createTourElements();
    tourOverlay.style.display = 'block';
    
    // Smooth fade in
    setTimeout(() => {
        tourOverlay.classList.add('active');
        startTourAutoAdvance();
        showTourStep(typeof startIndex === 'number' ? startIndex : 0);
    }, 15);
}

export function startPostAddReservationTour() {
    isTourActive = true;
    onboardingSessionActive = true;

    tourSteps = mainTourSteps.slice();
    if (!tourOverlay) createTourElements();
    tourOverlay.style.display = 'block';

    setTimeout(() => {
        tourOverlay.classList.add('active');
        startTourAutoAdvance();
        showTourStep(0);
    }, 15);
}
window.startPostAddReservationTour = startPostAddReservationTour;

export function startReservationTourAtReservations() {
    try {
        // SI YA FUE INICIALIZADO POR EL EVENTO DIRECTO, EVITAMOS COLISION
        if (reservationsTourInitialized) {
            reservationsTourInitialized = false;
            return;
        }

        // SOLO MOSTRAR EL TOUR EN LAS RESERVAS SI EL ONBOARDING ESTA ACTIVO O SI ES LA PRIMERA VEZ (ONBOARDING INICIAL)
        if (localStorage.getItem('seen_reservation_onboarding') === '1' && !onboardingSessionActive) {
            return;
        }

        if (!tourOverlay) createTourElements();
        if (_isQuickAddTour && _savedTourSteps) {
            tourSteps = _savedTourSteps;
            _isQuickAddTour = false;
            _savedTourSteps = null;
        }
        const idx = tourSteps.findIndex(s => /reservation-featured-list|reservation-list-active|reservation-list-history/.test(s.selector));
        if (idx !== -1) {
            tourOverlay.style.display = 'block';
            setTimeout(() => {
                tourOverlay.classList.add('active');
                startTourAutoAdvance();
                showTourStep(idx);
            }, 15);
        } else {
            console.warn('[TOUR] startReservationTourAtReservations: no reservation selector found, starting full tour as fallback');
            startReservationTour(0);
        }
    } catch (e) { console.error('[TOUR] startReservationTourAtReservations error', e); }
}

window.startReservationTourAtReservations = startReservationTourAtReservations;

function nextTourStep() {
    if (currentTourIndex < tourSteps.length - 1) showTourStep(currentTourIndex + 1);
    else endTour();
}

function prevTourStep() { if (currentTourIndex > 0) showTourStep(currentTourIndex - 1); }

function _baseEndTour(isOmitted = false) {
    // MARCAR QUE EL TOUR YA NO ESTA ACTIVO
    isTourActive = false;
    if (activeResizeObserver) {
        try { activeResizeObserver.disconnect(); } catch(e){}
        activeResizeObserver = null;
    }

    // SI EL USUARIO OMITIO EL TOUR O SI TERMINAMOS EL TOUR DE RESERVAS, SE CANCELA LA SESION DE ONBOARDING
    // SI LLEGO AL FINAL DE MAIN TOUR STEPS O QUICK ADD STEPS, DEJAMOS onboardingSessionActive EN true A LA ESPERA DE LA RESERVA
    const isAtReservations = tourSteps === reservationsTourSteps;
    if (isOmitted || isAtReservations) {
        onboardingSessionActive = false;
    }

    stopTourAutoAdvance();
    if (tourOverlay) {
        tourOverlay.classList.remove('active');
        if (tourTooltip) tourTooltip.classList.remove('active');
        if (tourArrow) tourArrow.classList.remove('active');
        setTimeout(() => {
            tourOverlay.style.display = 'none';
        }, 300);
    }
    // save seen flag
    try { localStorage.setItem('seen_reservation_onboarding','1'); } catch(e) { /* noop */ }
}

window.startReservationTour = startReservationTour;

// QUICK-ADD TOUR: steps to guide through add-vehicle form
const quickAddSteps = [
    { selector: '#quick-add-form-container .select-wrapper-premium select[name="tipo"]', title: 'Tipo de vehículo', text: 'Seleccioná si es Auto, Moto o Camioneta. Así se calcula la tarifa correcta.', align: 'right', interactive: true },
    { selector: '#quick-add-vehicle-form input[name="patente"]', title: 'Patente', text: 'Ingresá la patente de tu vehículo. Usá el formato correcto (ej: ABC 123).', align: 'bottom', interactive: true },
    { selector: '#quick-add-vehicle-form input[name="marca_modelo"]', title: 'Marca / Modelo', text: 'Escribí la marca y modelo para identificar tu vehículo fácilmente.', align: 'bottom', interactive: true },
    { selector: '#quick-add-vehicle-form button[type="submit"]', title: 'Continuar', text: 'Cuando completes los datos, pulsá CONTINUAR para registrar el vehículo.', align: 'top', interactive: true }
];


export async function startQuickAddTour() {
    try {
        const quick = document.getElementById('quick-add-form-container');
        if (!quick) {
            console.warn('[TOUR] quick-add container no encontrado');
            return;
        }

        // MARCAR QUE EL TOUR ESTA ACTIVO
        isTourActive = true;
        onboardingSessionActive = true;

        _savedTourSteps = tourSteps;
        tourSteps = quickAddSteps;
        _isQuickAddTour = true;
        if (!tourOverlay) createTourElements();
        
        tourOverlay.style.display = 'block';
        setTimeout(() => {
            tourOverlay.classList.add('active');
            startTourAutoAdvance();
            showTourStep(0);
        }, 15);

        const onReservationCreated = async (ev) => {
            try {
                if (_savedTourSteps) tourSteps = _savedTourSteps;
                _isQuickAddTour = false;
                _savedTourSteps = null;

                tourSteps = reservationsTourSteps.slice();
            } catch (e) { console.error('[TOUR] onReservationCreated error', e); }
            finally { document.removeEventListener('reservation:created', onReservationCreated); }
        };
        document.addEventListener('reservation:created', onReservationCreated);
    } catch (e) { console.error('[TOUR] startQuickAddTour error', e); }
}

export function endTour(isOmitted = false) {
    try {
        _baseEndTour(isOmitted);
    } catch (e) { console.error('[TOUR] error in base endTour', e); }
    try {
        if (_isQuickAddTour && _savedTourSteps) {
            tourSteps = _savedTourSteps;
        }
    } catch (e) { console.warn('[TOUR] error restoring tour steps', e); }
    _savedTourSteps = null;
    _isQuickAddTour = false;
}

window.endReservationTour = endTour;

function _handleReservationCreated(ev) {
    try {
        // SI EL ONBOARDING NO ESTA ACTIVA EN ESTA SESION, NO CONTINUAMOS A MIS RESERVAS
        if (!onboardingSessionActive) return;

        // MARCAR QUE EL TOUR DE RESERVAS SE VA A INICIALIZAR DIRECTAMENTE DESDE EL EVENTO
        reservationsTourInitialized = true;

        // DESTRUIR COMPLETAMENTE EL TOUR ANTERIOR PARA EVITAR ARTEFACTOS VISUALES
        stopTourAutoAdvance();
        positioningToken++;
        if (tourOverlay) {
            tourOverlay.remove();
        }
        tourOverlay = null;
        tourTooltip = null;
        tourArrow = null;
        currentTourIndex = 0;

        tourSteps = reservationsTourSteps.slice();

        const tryShow = (attempt = 0) => {
            try {
                const idx = tourSteps.findIndex(s => /reservation-featured-list|reservation-list-active|reservation-list-history/.test(s.selector));
                const anySelector = tourSteps[idx] ? tourSteps[idx].selector : null;
                const found = anySelector && document.querySelector(anySelector);

                if (idx !== -1 && found) {
                    createTourElements();
                    tourOverlay.style.display = 'block';
                    setTimeout(() => {
                        tourOverlay.classList.add('active');
                        startTourAutoAdvance();
                    }, 15);
                    setTimeout(() => showTourStep(idx), 50);
                    return;
                }

                if (attempt >= 10) {
                    console.warn('[TOUR] No se encontraron selectores en tiempo — iniciando tour de reservas como fallback');
                    startReservationTourAtReservations();
                    return;
                }

                setTimeout(() => tryShow(attempt + 1), 300);
            } catch (e) { console.error('[TOUR] error en tryShow:', e); startReservationTourAtReservations(); }
        };

        setTimeout(() => tryShow(0), 300);

    } catch (err) { console.error('[TOUR] handler reservation created error', err); }
}

document.addEventListener('reservation:created', _handleReservationCreated);
document.addEventListener('reservation:created:debug', (ev) => {
    console.log('[TOUR][DEBUG] reservation:created:debug recibido — detail:', ev && ev.detail ? ev.detail : ev);
    _handleReservationCreated(ev);
});

document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && isTourActive) {
        endTour(true);
    }
});
