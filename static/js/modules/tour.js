// Mini-tour module: simple guided walkthrough for reservation flow
// Exposes startReservationTour() globally

// Main tour (initial onboarding before 'Mis Reservas')
const mainTourSteps = [
    { selector: '#reserva-form-container', title: 'Formulario de Reserva', text: 'Aquí podés generar una nueva reserva: elegí vehículo, sucursal y tipo de estadía.', align: 'bottom', interactive: false },
    { selector: '#reserva-form-content .res-vehicle', title: 'Seleccioná vehículo', text: 'Seleccioná tu vehículo (o confirmá el preseleccionado). Podés continuar completando la reserva ahora.', align: 'right', interactive: true },
    { selector: '.res-sucursal', title: 'Elegí punto', text: 'Seleccioná el punto AutoPass donde querés estacionar.', align: 'left', interactive: true },
    { selector: '.res-type', title: 'Tipo de estadía', text: 'Elegí si reservás por hora, día, semana, quincena o mes. Los campos cambiarán acorde al tipo.', align: 'left', interactive: true },
    { selector: '.reservation-footer-premium .btn-confirm-premium', title: 'Confirmar reserva', text: 'Revisá el total estimado y pulsá "Continuar" para confirmar la reserva.', align: 'top', interactive: true },
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

// active tour steps (mutable)
let tourSteps = mainTourSteps.slice();

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

    // Listen to resize and scroll to reposition tooltip
    window.addEventListener('resize', handleWindowReposition, { passive: true });
    window.addEventListener('scroll', handleWindowReposition, { passive: true });
}

function updateSvgCutout(rect) {
    const svg = document.getElementById('autopass-tour-svg');
    if (!svg) return;
    const path = svg.querySelector('path');
    const highlightRect = document.getElementById('autopass-tour-highlight-rect');
    if (!path) return;

    const w = window.innerWidth;
    const h = window.innerHeight;

    if (!rect) {
        path.setAttribute('d', `M 0,0 L ${w},0 L ${w},${h} L 0,${h} Z`);
        if (highlightRect) highlightRect.style.display = 'none';
        return;
    }

    const padding = 6;
    const x = rect.left - padding;
    const y = rect.top - padding;
    const width = rect.width + (padding * 2);
    const height = rect.height + (padding * 2);
    const r = 10; // corner radius for cutout

    // Full screen outer path (clockwise) + cutout path (counter-clockwise)
    const outerPath = `M 0,0 h ${w} v ${h} h ${-w} z`;
    const cutoutPath = `
        M ${x + r},${y}
        h ${width - (r * 2)}
        a ${r},${r} 0 0 1 ${r},${r}
        v ${height - (r * 2)}
        a ${r},${r} 0 0 1 ${-r},${r}
        h ${-(width - (r * 2))}
        a ${r},${r} 0 0 1 ${-r},${-r}
        v ${-(height - (r * 2))}
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

function repositionActiveStep() {
    if (currentTourIndex < 0 || currentTourIndex >= tourSteps.length) return;
    const step = tourSteps[currentTourIndex];
    if (!step) return;
    const target = document.querySelector(step.selector);
    if (!target) return;

    const rect = target.getBoundingClientRect();

    // SI EL PASO ES CENTRADO, LIMPIAMOS EL CUTOUT Y RETORNAMOS PREVENTIVAMENTE
    if (step.center) {
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

    tourTooltip.style.position = 'absolute';
    tourTooltip.style.transform = '';

    const padding = 6;
    const targetLeft = rect.left - padding;
    const targetTop = rect.top - padding;
    const targetWidth = rect.width + (padding * 2);
    const targetHeight = rect.height + (padding * 2);

    let ttTop = targetTop + targetHeight + 12; // default: bottom
    let ttLeft = targetLeft + (targetWidth / 2) - (tourTooltip.offsetWidth / 2);

    if (step.align === 'top') {
        ttTop = targetTop - tourTooltip.offsetHeight - 12;
    } else if (step.align === 'left') {
        ttLeft = targetLeft - tourTooltip.offsetWidth - 12;
        ttTop = targetTop + (targetHeight / 2) - (tourTooltip.offsetHeight / 2);
    } else if (step.align === 'right') {
        ttLeft = targetLeft + targetWidth + 12;
        ttTop = targetTop + (targetHeight / 2) - (tourTooltip.offsetHeight / 2);
    }

    // scroll adjustment
    const margin = 10;
    const scrollY = window.scrollY;
    const scrollX = window.scrollX;

    let absLeft = ttLeft + scrollX;
    let absTop = ttTop + scrollY;

    absLeft = Math.max(margin + scrollX, Math.min(absLeft, window.innerWidth + scrollX - tourTooltip.offsetWidth - margin));
    absTop = Math.max(margin + scrollY, Math.min(absTop, window.innerHeight + scrollY - tourTooltip.offsetHeight - margin));

    tourTooltip.style.left = absLeft + 'px';
    tourTooltip.style.top = absTop + 'px';

    // Position arrow
    if (tourArrow) {
        tourArrow.style.display = 'block';
        tourArrow.className = 'tour-arrow-premium active';
        tourArrow.style.borderLeft = '';
        tourArrow.style.borderRight = '';
        tourArrow.style.borderTop = '';
        tourArrow.style.borderBottom = '';

        const arrowSize = 10;

        if (step.align === 'top') {
            tourArrow.style.borderLeft = `${arrowSize}px solid transparent`;
            tourArrow.style.borderRight = `${arrowSize}px solid transparent`;
            tourArrow.style.borderTop = `${arrowSize}px solid rgba(11, 11, 11, 0.88)`;
            const arrowLeft = absLeft + (tourTooltip.offsetWidth / 2) - arrowSize;
            tourArrow.style.left = arrowLeft + 'px';
            tourArrow.style.top = (absTop + tourTooltip.offsetHeight) + 'px';
        } else if (step.align === 'left') {
            tourArrow.style.borderTop = `${arrowSize}px solid transparent`;
            tourArrow.style.borderBottom = `${arrowSize}px solid transparent`;
            tourArrow.style.borderLeft = `${arrowSize}px solid rgba(11, 11, 11, 0.88)`;
            const arrowLeft = absLeft + tourTooltip.offsetWidth;
            const arrowTop = absTop + (tourTooltip.offsetHeight / 2) - arrowSize;
            tourArrow.style.left = arrowLeft + 'px';
            tourArrow.style.top = arrowTop + 'px';
        } else if (step.align === 'right') {
            tourArrow.style.borderTop = `${arrowSize}px solid transparent`;
            tourArrow.style.borderBottom = `${arrowSize}px solid transparent`;
            tourArrow.style.borderRight = `${arrowSize}px solid rgba(11, 11, 11, 0.88)`;
            const arrowLeft = absLeft - arrowSize;
            const arrowTop = absTop + (tourTooltip.offsetHeight / 2) - arrowSize;
            tourArrow.style.left = arrowLeft + 'px';
            tourArrow.style.top = arrowTop + 'px';
        } else {
            // default bottom
            tourArrow.style.borderLeft = `${arrowSize}px solid transparent`;
            tourArrow.style.borderRight = `${arrowSize}px solid transparent`;
            tourArrow.style.borderBottom = `${arrowSize}px solid rgba(11, 11, 11, 0.88)`;
            const arrowLeft = absLeft + (tourTooltip.offsetWidth / 2) - arrowSize;
            tourArrow.style.left = arrowLeft + 'px';
            tourArrow.style.top = (absTop - arrowSize) + 'px';
        }
    }
}

function showTourStep(index) {
    currentTourIndex = index;

    if (index < 0) index = 0;
    if (index >= tourSteps.length) return endTour();

    const step = tourSteps[index];
    if (!step) return;

    // EJECUTAR ACCIONES DE PREPARACION SI ESTAN DEFINIDAS PARA EL PASO
    if (typeof step.beforeShow === 'function') {
        try {
            step.beforeShow();
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

    // find target
    const target = document.querySelector(step.selector);
    if (!target) {
        console.warn('[TOUR] Target no encontrado, saltando paso:', step.selector);
        if (index < tourSteps.length - 1) return showTourStep(index + 1);
        return endTour();
    }

    // scroll into view
    try {
        const rect = target.getBoundingClientRect();
        const isVisible = (rect.top >= 0) && (rect.bottom <= window.innerHeight);
        if (!isVisible) {
            target.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    } catch (e) {}

    // configure interactivity using pointerEvents on the SVG path
    if (step.interactive) {
        // Cutout allows clics underneath, rest is blocked by path
        tourOverlay.classList.add('interactive');
    } else {
        // Blocks all clicks on elements
        tourOverlay.classList.remove('interactive');
    }

    const waitForVisible = (sel, attempts = 0) => {
        const el = document.querySelector(sel);
        if (el && el.getBoundingClientRect && el.offsetParent !== null) return el;
        if (attempts >= 8) return null;
        return new Promise(resolve => setTimeout(() => resolve(waitForVisible(sel, attempts + 1)), 150));
    };

    const ensureEnabled = async (el, attempts = 0) => {
        if (!el) return true;
        const disabled = el.disabled || el.classList.contains('disabled') || el.getAttribute('aria-disabled') === 'true';
        if (!disabled) return true;
        if (attempts >= 20) return false;
        await new Promise(r => setTimeout(r, 150));
        return ensureEnabled(el, attempts + 1);
    };

    const ensurePaid = async (selector, attempts = 0) => {
        const card = document.querySelector(selector);
        const hasPass = card && (card.querySelector && (card.querySelector('.btn-ultra-primary') && /pase digital|mi pase/i.test(card.innerText)));
        if (hasPass) return true;
        if (attempts >= 20) return false;
        await new Promise(r => setTimeout(r, 150));
        return ensurePaid(selector, attempts + 1);
    };

    positioningToken = (typeof positioningToken === 'number' ? positioningToken + 1 : 1);
    const myToken = positioningToken;

    Promise.resolve(waitForVisible(step.selector)).then(async (resolvedTarget) => {
        if (myToken !== positioningToken) return;
        const tgt = resolvedTarget || target;

        let sizeAttempts = 0;
        while ((tourTooltip.offsetWidth === 0 || tourTooltip.offsetHeight === 0) && sizeAttempts < 10) {
            await new Promise(r => requestAnimationFrame(r));
            sizeAttempts++;
            if (myToken !== positioningToken) return;
        }

        requestAnimationFrame(() => {
            requestAnimationFrame(async () => {
                try {
                    if (step.waitForEnabled) {
                        const focusEl = tgt.querySelector && (tgt.querySelector('button, input, select') ) || tgt;
                        const ok = await ensureEnabled(focusEl);
                        if (!ok) console.warn('[TOUR] waitForEnabled timed out for', step.selector);
                    }
                    if (step.waitForPaid) {
                        const ok = await ensurePaid(step.selector);
                        if (!ok) console.warn('[TOUR] waitForPaid timed out for', step.selector);
                    }

                    if (myToken !== positioningToken) return;

                    repositionActiveStep();

                    // Show elements with transition
                    tourTooltip.classList.add('active');
                    if (tourArrow && !step.center) {
                        tourArrow.classList.add('active');
                    }
                } catch (e) {
                    console.warn('[TOUR] error positioning steps', e);
                }
            });
        });
    });

    // buttons setup
    document.getElementById('tour-prev').disabled = index === 0;
    document.getElementById('tour-next').innerText = index === tourSteps.length - 1 ? 'Finalizar' : 'Siguiente';
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

export function startReservationTour(startIndex = 0) {
    // MARCAR QUE EL TOUR ESTA ACTIVO
    isTourActive = true;
    onboardingSessionActive = true;
    console.log('[TOUR] startReservationTour: isTourActive and onboardingSessionActive set to true');

    if (!tourOverlay) createTourElements();
    tourOverlay.style.display = 'block';
    
    // Smooth fade in
    setTimeout(() => {
        tourOverlay.classList.add('active');
        startTourAutoAdvance();
        showTourStep(typeof startIndex === 'number' ? startIndex : 0);
    }, 15);
}

export function startReservationTourAtReservations() {
    try {
        // SI YA FUE INICIALIZADO POR EL EVENTO DIRECTO, EVITAMOS COLISION
        if (reservationsTourInitialized) {
            console.log('[TOUR] startReservationTourAtReservations: ya inicializado por evento, ignorando fallback');
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
        console.log('[TOUR] startReservationTourAtReservations: found idx', idx);
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
    // MARCAR QUE EL TOUR YA NO ESTA ACTIVO E IMPRIMIR TRAZA DE DEPURACION
    isTourActive = false;
    console.log('[TOUR] _baseEndTour: isTourActive set to false. Stack trace:', new Error().stack);

    // SI EL USUARIO OMITIO EL TOUR O SI TERMINAMOS EL TOUR DE RESERVAS, SE CANCELA LA SESION DE ONBOARDING
    // SI LLEGO AL FINAL DE MAIN TOUR STEPS O QUICK ADD STEPS, DEJAMOS onboardingSessionActive EN true A LA ESPERA DE LA RESERVA
    const isAtReservations = tourSteps === reservationsTourSteps;
    if (isOmitted || isAtReservations) {
        onboardingSessionActive = false;
        console.log('[TOUR] _baseEndTour: onboardingSessionActive set to false (omitted or completed reservations)');
    } else {
        console.log('[TOUR] _baseEndTour: keeping onboardingSessionActive as true (waiting for reservation created)');
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
    { selector: '#quick-add-form-container .select-wrapper-premium select[name="tipo"]', title: 'Tipo de vehículo', text: 'Seleccioná si es Auto, Moto o Camioneta. Esto define iconos y validaciones.', align: 'right', interactive: true },
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
        console.log('[TOUR] startQuickAddTour: isTourActive and onboardingSessionActive set to true');

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
                console.log('[TOUR] quickAdd -> switching to reservationsTourSteps (deferred to _handleReservationCreated)');
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
        console.log('[TOUR] _handleReservationCreated: event recibido, onboardingSessionActive =', onboardingSessionActive);

        // SI EL ONBOARDING NO ESTA ACTIVA EN ESTA SESION, NO CONTINUAMOS A MIS RESERVAS
        if (!onboardingSessionActive) return;

        console.log('[TOUR] reservation created event recibido — detalle:', ev && ev.detail ? ev.detail : '(no detail)');

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
                console.log(`[TOUR] intento ${attempt}: idx=${idx}, selector=${anySelector}, found=${!!found}`);

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
