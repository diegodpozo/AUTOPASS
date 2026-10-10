/**
 * LIST PAGINATION (v1.0)
 * Helper DRY para listas/grillas que acumulan muchos items: muestra las primeras N
 * con un toggle "Ver todas (M) / Ver menos" y empty configurable. Se reutiliza en
 * perfil (mis consultas, vouchers) y dashboard admin (tickets, reservas).
 *
 * container   : elemento donde se inyectan los items (debe tener id).
 * itemsHtml   : array de strings HTML (un elemento por item).
 * config      : {
 *     pageSize  (6)          : cantidad visible por defecto.
 *     emptyHtml (scene)      : HTML del estado vacío cuando no hay items.
 *     tag       ('div'|'tr') : envoltorio del toggle (grilla o fila de tabla).
 *     colspan   (1)          : colspan cuando tag='tr'.
 *     toggleClass            : clase del envoltorio div (default cap-toggle-grid).
 *     toggleAll (fn)         : (total) => etiqueta "Ver todas".
 *     toggleLess ('Ver menos'): etiqueta al colapsar.
 *     onToggle   (fn)        : re-render del caller al alternar.
 * }
 */
let capSeq = 0;
const capState = {};
const capToggleIds = {};

export function renderCappedList(container, itemsHtml, config = {}) {
    if (!container) return '';
    if (!itemsHtml || itemsHtml.length === 0) {
        container.innerHTML = config.emptyHtml != null ? config.emptyHtml : '';
        return '';
    }

    const pageSize = config.pageSize || 6;
    const tag = config.tag || 'div';
    const colspan = config.colspan > 0 ? config.colspan : 1;
    const toggleClass = config.toggleClass || 'cap-toggle-grid';
    const toggleAll = config.toggleAll || (total => `Ver todas (${total})`);
    const toggleLess = config.toggleLess || 'Ver menos';

    const id = container.id || (container.id = 'capped-list-' + (++capSeq));
    const expanded = !!capState[id];
    const showToggle = itemsHtml.length > pageSize;
    const visible = showToggle && !expanded ? itemsHtml.slice(0, pageSize) : itemsHtml;

    capToggleIds[id] = () => {
        capState[id] = !capState[id];
        if (typeof config.onToggle === 'function') config.onToggle();
    };

    let toggleHtml = '';
    if (showToggle) {
        const label = expanded ? toggleLess : toggleAll(itemsHtml.length);
        const btn = `<button type="button" class="cap-toggle-btn" onclick="__capToggleList('${id}')"><i class="fas fa-chevron-${expanded ? 'up' : 'down'}"></i> ${label}</button>`;
        toggleHtml = tag === 'tr'
            ? `<tr><td colspan="${colspan}">${btn}</td></tr>`
            : `<div class="${toggleClass}">${btn}</div>`;
    }

    container.innerHTML = visible.join('') + toggleHtml;
    return container.innerHTML;
}

export function resetCappedState(container) {
    if (container && container.id) capState[container.id] = false;
}

window.__capToggleList = (id) => {
    const fn = capToggleIds[id];
    if (typeof fn === 'function') fn();
};