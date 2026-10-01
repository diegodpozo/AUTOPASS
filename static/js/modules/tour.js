// Mini-tour module: simple guided walkthrough for reservation flow
// Exposes startReservationTour() globally

import {
    noVehiclesTourSteps,
    existingVehiclesHelpTourSteps,
    noVehiclesHelpTourSteps,
    addVehicleTourSteps,
    qrPassTourSteps,
    createReservationTourSteps,
    rechargeBalanceTourSteps,
    redeemPointsTourSteps,
    mainTourSteps,
    reservationsTourSteps,
    quickAddSteps,
} from './tour-steps.js';
import { THEME } from './theme.js';
import { scrollToElement } from './utils.js';


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
    highlightRect.setAttribute('stroke', THEME.gold);
    highlightRect.setAttribute('stroke-width', '2');
    highlightRect.setAttribute('rx', '10');
    highlightRect.setAttribute('ry', '10');
    highlightRect.style.display = 'none';
    highlightRect.style.filter = 'drop-shadow(0 0 8px rgba(223, 186, 107, 0.45))';
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
            <button id="tour-prev" class="btn btn--outline">Anterior</button>
            <button id="tour-next" class="btn btn--primary">Siguiente</button>
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
                    scrollToElement(resolvedTarget, { block: 'nearest' });
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
    if (step && step.selector && step.selector.includes('.nav-item[onclick*="puntos"]')) {
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

