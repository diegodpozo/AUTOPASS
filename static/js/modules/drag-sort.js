// HELPER REUTILIZABLE DE ORDENAMIENTO POR ARRASTRE (HTML5 DRAG & DROP).
// Habilita reordenar los hijos de un contenedor (flex/grid) arrastrándolos.
// Reutilizable en cualquier lista de tarjetas: se configura con selectores.
//
// Uso:
//   enableDragSort(container, {
//       itemSelector: '.mi-tarjeta',
//       handleSelector: '.mi-handle',   // opcional: si se define, solo arrastra desde ahí
//       onReorder: (items) => { ... }   // recibe los nodos ya reordenados en el DOM
//   });

// Elementos interactivos: no inician arrastre (para no romper clics de botones).
const NO_DRAG_SELECTOR = 'button, a, input, select, textarea, label';

export function enableDragSort(container, { itemSelector, handleSelector, onReorder } = {}) {
    if (!container || !itemSelector) return;

    // Idempotente: los listeners se delegan en el contenedor, así que alcanza con
    // inicializarlo una sola vez aunque la lista se vuelva a renderizar.
    if (container.dataset.dragSortReady === '1') return;
    container.dataset.dragSortReady = '1';

    let dragged = null;
    let autoScrollRAF = null;
    let autoScroller = null;
    let lastPoint = { x: 0, y: 0 };

    const items = () => Array.from(container.querySelectorAll(itemSelector));

    // Reubica el nodo arrastrado según la última posición conocida del puntero.
    const applyInsertion = () => {
        if (!dragged) return;
        const target = _findInsertionPoint(container, itemSelector, dragged, lastPoint.x, lastPoint.y);
        if (target === null) container.appendChild(dragged);
        else container.insertBefore(dragged, target);
    };

    // Auto-scroll: mientras se arrastra cerca del borde del contenedor scrolleable,
    // lo desplaza solo (para mover una tarjeta lejos sin soltar el mouse).
    const stopAutoScroll = () => {
        if (autoScrollRAF !== null) cancelAnimationFrame(autoScrollRAF);
        autoScrollRAF = null;
        autoScroller = null;
    };

    const startAutoScroll = () => {
        if (autoScrollRAF !== null) return;
        const step = () => {
            if (!dragged || !autoScroller) { autoScrollRAF = null; return; }
            const isDoc = autoScroller === (document.scrollingElement || document.documentElement);
            const rect = isDoc
                ? { top: 0, bottom: window.innerHeight }
                : autoScroller.getBoundingClientRect();
            const threshold = 80;
            const speed = 16;
            let dy = 0;
            if (lastPoint.y < rect.top + threshold) dy = -speed;
            else if (lastPoint.y > rect.bottom - threshold) dy = speed;
            if (dy) {
                autoScroller.scrollTop += dy;
                applyInsertion();
            }
            autoScrollRAF = requestAnimationFrame(step);
        };
        autoScrollRAF = requestAnimationFrame(step);
    };

    container.addEventListener('dragstart', (e) => {
        const item = e.target.closest(itemSelector);
        if (!item || !container.contains(item)) return;
        if (handleSelector && !e.target.closest(handleSelector)) {
            e.preventDefault();
            return;
        }
        if (e.target.closest(NO_DRAG_SELECTOR)) {
            e.preventDefault();
            return;
        }
        dragged = item;
        lastPoint = { x: e.clientX, y: e.clientY };
        autoScroller = _findScroller(container);
        item.classList.add('dragging');
        if (e.dataTransfer) {
            e.dataTransfer.effectAllowed = 'move';
            try { e.dataTransfer.setData('text/plain', ''); } catch (_) { /* noop */ }
        }
        startAutoScroll();
    });

    container.addEventListener('dragover', (e) => {
        if (!dragged) return;
        e.preventDefault();
        if (e.dataTransfer) e.dataTransfer.dropEffect = 'move';
        lastPoint = { x: e.clientX, y: e.clientY };
        applyInsertion();
    });

    container.addEventListener('drop', (e) => {
        if (dragged) e.preventDefault();
    });

    container.addEventListener('dragend', () => {
        if (!dragged) return;
        stopAutoScroll();
        dragged.classList.remove('dragging');
        dragged = null;
        if (typeof onReorder === 'function') onReorder(items());
    });
}

// Busca el ancestro scrolleable vertical más cercano (o el documento como fallback).
function _findScroller(el) {
    let node = el.parentElement;
    while (node && node !== document.body) {
        const oy = getComputedStyle(node).overflowY;
        if ((oy === 'auto' || oy === 'scroll' || oy === 'overlay') && node.scrollHeight > node.clientHeight) {
            return node;
        }
        node = node.parentElement;
    }
    return document.scrollingElement || document.documentElement;
}

// Devuelve el nodo ANTES del cual debe insertarse el arrastrado, o null para el
// final. Usa ORDEN DE LECTURA (fila por fila) en vez de distancia al centro: en
// grillas, comparar contra el centro de cada tarjeta obliga a enganchar el punto
// exacto al mover hacia izquierda/arriba/abajo y hace que las tarjetas se
// superpongan. Acá alcanza con cruzar el borde inferior de una fila o el centro
// horizontal de la tarjeta.
function _findInsertionPoint(container, itemSelector, dragged, x, y) {
    const candidates = Array.from(container.querySelectorAll(itemSelector)).filter(el => el !== dragged);
    for (const el of candidates) {
        const box = el.getBoundingClientRect();
        const inRow = y >= box.top && y <= box.bottom;
        const after = (y > box.bottom) || (inRow && x > box.left + box.width / 2);
        if (!after) return el; // el puntero está antes de esta tarjeta
    }
    return null;
}
