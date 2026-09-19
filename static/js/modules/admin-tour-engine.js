/**
 * AUTOPASS - MOTOR DE RECORRIDO GUIADO DEL ADMINISTRADOR
 * Submodulo de admin-tour.js: estado, creacion del overlay/tooltip y toda la
 * logica de posicionamiento, navegacion entre pasos y resolucion de targets.
 */

let activeTourSteps = [];
let currentAdminStepIndex = 0;
let adminTourOverlay = null;
let adminTourTooltip = null;
let adminTourArrow = null;
let positioningToken = 0;
let isPositioningActive = false;
let isAdminTourActive = false;
let activeResizeObserver = null;

function createAdminTourElements() {
    const existing = document.getElementById('autopass-admin-tour-overlay');
    if (existing) existing.remove();

    adminTourOverlay = document.createElement('div');
    adminTourOverlay.id = 'autopass-admin-tour-overlay';

    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, 'svg');
    svg.id = 'autopass-admin-tour-svg';
    svg.setAttribute('width', '100%');
    svg.setAttribute('height', '100%');
    svg.style.position = 'absolute';
    svg.style.top = '0';
    svg.style.left = '0';
    svg.style.width = '100%';
    svg.style.height = '100%';

    const path = document.createElementNS(svgNS, 'path');
    path.setAttribute('fill', 'rgba(3, 7, 18, 0.75)');
    path.setAttribute('fill-rule', 'evenodd');

    const highlightRect = document.createElementNS(svgNS, 'rect');
    highlightRect.id = 'autopass-admin-tour-highlight-rect';
    highlightRect.setAttribute('fill', 'none');
    highlightRect.setAttribute('stroke', '#dfba6b');
    highlightRect.setAttribute('stroke-width', '2');
    highlightRect.setAttribute('rx', '10');
    highlightRect.setAttribute('ry', '10');
    highlightRect.style.display = 'none';

    svg.appendChild(path);
    svg.appendChild(highlightRect);
    adminTourOverlay.appendChild(svg);
    document.body.appendChild(adminTourOverlay);

    // Tooltip
    adminTourTooltip = document.createElement('div');
    adminTourTooltip.id = 'autopass-admin-tour-tooltip';
    adminTourTooltip.className = 'admin-tour-tooltip';
    adminTourOverlay.appendChild(adminTourTooltip);

    // Arrow
    adminTourArrow = document.createElement('div');
    adminTourArrow.id = 'autopass-admin-tour-arrow';
    adminTourArrow.className = 'admin-tour-arrow';
    adminTourOverlay.appendChild(adminTourArrow);

    adminTourTooltip.innerHTML = `
        <div class="admin-tour-header">
            <span id="admin-tour-badge" class="admin-tour-badge"><i class="fas fa-gauge-high"></i> PASO 1 DE 5</span>
            <button id="admin-tour-end" class="btn-admin-tour-end" title="Cerrar tour"><i class="fas fa-xmark"></i> Omitir</button>
        </div>
        <div id="admin-tour-title" class="admin-tour-title"></div>
        <div id="admin-tour-text" class="admin-tour-text"></div>
        <div class="admin-tour-footer">
            <button id="admin-tour-prev" class="btn-admin-tour-prev"><i class="fas fa-arrow-left"></i> Anterior</button>
            <div class="admin-tour-buttons-group">
                <button id="admin-tour-next" class="btn-admin-tour-next">Siguiente <i class="fas fa-arrow-right"></i></button>
            </div>
        </div>
    `;

    document.getElementById('admin-tour-prev').addEventListener('click', prevAdminTourStep);
    document.getElementById('admin-tour-next').addEventListener('click', nextAdminTourStep);
    document.getElementById('admin-tour-end').addEventListener('click', endAdminTour);

    window.addEventListener('resize', handleAdminWindowReposition, { passive: true });
    window.addEventListener('scroll', handleAdminWindowReposition, { passive: true });
    window.addEventListener('keydown', handleAdminTourKeydown);
}

function handleAdminTourKeydown(e) {
    if (!isAdminTourActive || !adminTourOverlay || adminTourOverlay.style.display === 'none') return;
    if (e.key === 'Escape') endAdminTour();
    else if (e.key === 'ArrowRight') nextAdminTourStep();
    else if (e.key === 'ArrowLeft') prevAdminTourStep();
}

function updateAdminSvgCutout(rect) {
    const svg = document.getElementById('autopass-admin-tour-svg');
    if (!svg) return;
    const path = svg.querySelector('path');
    const highlightRect = document.getElementById('autopass-admin-tour-highlight-rect');
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
    const r = 10;

    const innerW = Math.max(0, width - (r * 2));
    const innerH = Math.max(0, height - (r * 2));

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

    if (highlightRect) {
        highlightRect.setAttribute('x', x);
        highlightRect.setAttribute('y', y);
        highlightRect.setAttribute('width', width);
        highlightRect.setAttribute('height', height);
        highlightRect.style.display = 'block';
    }
}

function handleAdminWindowReposition() {
    if (!adminTourOverlay || adminTourOverlay.style.display === 'none' || currentAdminStepIndex === -1) return;
    if (isPositioningActive) return;
    isPositioningActive = true;
    requestAnimationFrame(() => {
        repositionActiveAdminStep();
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
                if (isVisible) return el;
            }
        }
    }
    return document.querySelector(parts[0]);
}

function repositionActiveAdminStep() {
    if (currentAdminStepIndex < 0 || currentAdminStepIndex >= activeTourSteps.length) return;
    const step = activeTourSteps[currentAdminStepIndex];
    if (!step) return;
    const target = getVisibleTarget(step.selector);
    if (!target) return;

    const rect = target.getBoundingClientRect();

    if (step.center || (rect.width === 0 && rect.height === 0)) {
        updateAdminSvgCutout(null);
        adminTourTooltip.style.position = 'fixed';
        adminTourTooltip.style.left = '50%';
        adminTourTooltip.style.top = '50%';
        adminTourTooltip.style.transform = 'translate(-50%, -50%)';
        if (adminTourArrow) {
            adminTourArrow.classList.remove('active');
            adminTourArrow.style.display = 'none';
        }
        return;
    }

    updateAdminSvgCutout(rect);

    adminTourTooltip.style.position = 'fixed';
    adminTourTooltip.style.transform = '';

    const padding = 8;
    const targetLeft = rect.left - padding;
    const targetTop = rect.top - padding;
    const targetWidth = rect.width + (padding * 2);
    const targetHeight = rect.height + (padding * 2);

    const tooltipWidth = adminTourTooltip.offsetWidth || 380;
    const tooltipHeight = adminTourTooltip.offsetHeight || 180;

    const vw = window.innerWidth;
    const vh = window.innerHeight;

    let effectiveAlign = step.align || 'bottom';
    if (vw < 680 && (effectiveAlign === 'left' || effectiveAlign === 'right')) {
        effectiveAlign = (targetTop + targetHeight / 2 > vh / 2) ? 'top' : 'bottom';
    }

    let ttLeft = targetLeft + (targetWidth / 2) - (tooltipWidth / 2);
    let ttTop = targetTop + targetHeight + 14;

    if (effectiveAlign === 'top') {
        ttTop = targetTop - tooltipHeight - 14;
    } else if (effectiveAlign === 'left') {
        ttLeft = targetLeft - tooltipWidth - 14;
        ttTop = targetTop + (targetHeight / 2) - (tooltipHeight / 2);
    } else if (effectiveAlign === 'right') {
        ttLeft = targetLeft + targetWidth + 14;
        ttTop = targetTop + (targetHeight / 2) - (tooltipHeight / 2);
    }

    if (effectiveAlign === 'top' && ttTop < 12) {
        ttTop = targetTop + targetHeight + 14;
        effectiveAlign = 'bottom';
    } else if (effectiveAlign === 'bottom' && ttTop + tooltipHeight > vh - 12) {
        if (targetTop - tooltipHeight - 14 > 12) {
            ttTop = targetTop - tooltipHeight - 14;
            effectiveAlign = 'top';
        }
    }

    const margin = 12;
    const finalLeft = Math.max(margin, Math.min(ttLeft, vw - tooltipWidth - margin));
    const finalTop = Math.max(margin, Math.min(ttTop, vh - tooltipHeight - margin));

    adminTourTooltip.style.left = finalLeft + 'px';
    adminTourTooltip.style.top = finalTop + 'px';

    if (adminTourArrow) {
        adminTourArrow.style.display = 'block';
        adminTourArrow.style.position = 'fixed';
        adminTourArrow.className = 'admin-tour-arrow active';
        adminTourArrow.style.borderLeft = '';
        adminTourArrow.style.borderRight = '';
        adminTourArrow.style.borderTop = '';
        adminTourArrow.style.borderBottom = '';

        const arrowSize = 10;
        const targetCenterX = targetLeft + (targetWidth / 2);
        const targetCenterY = targetTop + (targetHeight / 2);

        if (effectiveAlign === 'top') {
            adminTourArrow.style.borderLeft = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderRight = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderTop = `${arrowSize}px solid rgba(10, 16, 26, 0.96)`;

            let arrowLeft = targetCenterX - arrowSize;
            arrowLeft = Math.max(finalLeft + 16, Math.min(arrowLeft, finalLeft + tooltipWidth - 16 - (arrowSize * 2)));

            adminTourArrow.style.left = arrowLeft + 'px';
            adminTourArrow.style.top = (finalTop + tooltipHeight) + 'px';
        } else if (effectiveAlign === 'left') {
            adminTourArrow.style.borderTop = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderBottom = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderLeft = `${arrowSize}px solid rgba(10, 16, 26, 0.96)`;

            let arrowTop = targetCenterY - arrowSize;
            arrowTop = Math.max(finalTop + 16, Math.min(arrowTop, finalTop + tooltipHeight - 16 - (arrowSize * 2)));

            adminTourArrow.style.left = (finalLeft + tooltipWidth) + 'px';
            adminTourArrow.style.top = arrowTop + 'px';
        } else if (effectiveAlign === 'right') {
            adminTourArrow.style.borderTop = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderBottom = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderRight = `${arrowSize}px solid rgba(10, 16, 26, 0.96)`;

            let arrowTop = targetCenterY - arrowSize;
            arrowTop = Math.max(finalTop + 16, Math.min(arrowTop, finalTop + tooltipHeight - 16 - (arrowSize * 2)));

            adminTourArrow.style.left = (finalLeft - (arrowSize * 2)) + 'px';
            adminTourArrow.style.top = arrowTop + 'px';
        } else {
            adminTourArrow.style.borderLeft = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderRight = `${arrowSize}px solid transparent`;
            adminTourArrow.style.borderBottom = `${arrowSize}px solid rgba(10, 16, 26, 0.96)`;

            let arrowLeft = targetCenterX - arrowSize;
            arrowLeft = Math.max(finalLeft + 16, Math.min(arrowLeft, finalLeft + tooltipWidth - 16 - (arrowSize * 2)));

            adminTourArrow.style.left = arrowLeft + 'px';
            adminTourArrow.style.top = (finalTop - (arrowSize * 2)) + 'px';
        }
    }
}

async function showAdminTourStep(index) {
    currentAdminStepIndex = index;

    if (index < 0) index = 0;
    if (index >= activeTourSteps.length) return endAdminTour();

    const step = activeTourSteps[index];
    if (!step) return;

    if (activeResizeObserver) {
        try { activeResizeObserver.disconnect(); } catch(e){}
        activeResizeObserver = null;
    }

    if (typeof step.beforeShow === 'function') {
        try {
            const res = step.beforeShow();
            if (res && typeof res.then === 'function') await res;
        } catch (e) { console.warn('[ADMIN TOUR] Error en beforeShow:', e); }
    }

    const badgeEl = document.getElementById('admin-tour-badge');
    const titleEl = document.getElementById('admin-tour-title');
    const textEl = document.getElementById('admin-tour-text');

    if (badgeEl) badgeEl.innerHTML = `<i class="fas fa-gauge-high"></i> PASO ${index + 1} DE ${activeTourSteps.length}`;
    if (titleEl) titleEl.innerHTML = `<i class="fas fa-compass"></i> ${step.title || ''}`;
    if (textEl) textEl.innerText = step.text || '';

    if (adminTourTooltip) adminTourTooltip.classList.remove('active');
    if (adminTourArrow) adminTourArrow.classList.remove('active');

    if (step.interactive) {
        adminTourOverlay.classList.add('interactive');
    } else {
        adminTourOverlay.classList.remove('interactive');
    }

    const waitForVisible = (sel, attempts = 0) => {
        const target = getVisibleTarget(sel);
        if (target) {
            const rect = target.getBoundingClientRect();
            if (rect.width > 0 && rect.height > 0) return target;
        }
        if (attempts >= 12) return null;
        return new Promise(resolve => setTimeout(() => resolve(waitForVisible(sel, attempts + 1)), 150));
    };

    positioningToken = (typeof positioningToken === 'number' ? positioningToken + 1 : 1);
    const myToken = positioningToken;

    Promise.resolve(waitForVisible(step.selector)).then(async (resolvedTarget) => {
        if (myToken !== positioningToken) return;

        if (!resolvedTarget) {
            console.warn('[ADMIN TOUR] Target no encontrado:', step.selector);
            if (index < activeTourSteps.length - 1) return showAdminTourStep(index + 1);
            return endAdminTour();
        }

        if (window.ResizeObserver && resolvedTarget) {
            try {
                activeResizeObserver = new ResizeObserver(() => {
                    if (myToken === positioningToken) repositionActiveAdminStep();
                });
                activeResizeObserver.observe(resolvedTarget);
                if (resolvedTarget.parentElement) activeResizeObserver.observe(resolvedTarget.parentElement);
            } catch(e){}
        }

        if (!step.center) {
            try {
                const rect = resolvedTarget.getBoundingClientRect();
                const isVisible = (rect.top >= 0) && (rect.bottom <= window.innerHeight);
                if (!isVisible) {
                    resolvedTarget.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            } catch (e) {}
        }

        let frameCount = 0;
        const trackScroll = () => {
            if (myToken !== positioningToken) return;
            repositionActiveAdminStep();
            frameCount++;
            if (frameCount < 40) requestAnimationFrame(trackScroll);
        };
        requestAnimationFrame(trackScroll);

        setTimeout(() => { if (myToken === positioningToken) repositionActiveAdminStep(); }, 300);

        setTimeout(() => {
            if (myToken !== positioningToken) return;
            repositionActiveAdminStep();
            adminTourTooltip.classList.add('active');
            if (adminTourArrow && !step.center) adminTourArrow.classList.add('active');
        }, 120);
    });

    const prevBtn = document.getElementById('admin-tour-prev');
    const nextBtn = document.getElementById('admin-tour-next');

    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) nextBtn.innerHTML = index === activeTourSteps.length - 1 ? 'Finalizar <i class="fas fa-check"></i>' : 'Siguiente <i class="fas fa-arrow-right"></i>';
}

function nextAdminTourStep() {
    if (currentAdminStepIndex < activeTourSteps.length - 1) showAdminTourStep(currentAdminStepIndex + 1);
    else endAdminTour();
}

function prevAdminTourStep() {
    if (currentAdminStepIndex > 0) showAdminTourStep(currentAdminStepIndex - 1);
}

function endAdminTour() {
    isAdminTourActive = false;
    if (activeResizeObserver) {
        try { activeResizeObserver.disconnect(); } catch(e){}
        activeResizeObserver = null;
    }
    if (adminTourOverlay) {
        adminTourOverlay.classList.remove('active');
        if (adminTourTooltip) adminTourTooltip.classList.remove('active');
        if (adminTourArrow) adminTourArrow.classList.remove('active');
        setTimeout(() => {
            adminTourOverlay.style.display = 'none';
        }, 300);
    }
}

export function launchAdminTour(steps) {
    isAdminTourActive = true;
    activeTourSteps = steps.slice();
    if (!adminTourOverlay) createAdminTourElements();
    adminTourOverlay.style.display = 'block';
    setTimeout(() => {
        adminTourOverlay.classList.add('active');
        showAdminTourStep(0);
    }, 15);
}