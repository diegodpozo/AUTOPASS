/**
 * LIST PAGINATION (v1.0)
 * Helper DRY para listas/grillas que acumulan muchos items: muestra las primeras N
 * con un toggle "Ver todas (M) / Ver menos" y empty configurable. Se reutiliza en
 * perfil (mis consultas, vouchers) y dashboard admin (tickets, reservas).
 * Tambien expone renderPaginatedList: muestra de a N con barra navegadora (reservas admin).
 *
 * container   : elemento donde se inyectan los items (debe tener id).
 * itemsHtml   : array de strings HTML (un elemento por item).
 * config      : {
 *     pageSize  (6)          : cantidad visible por defecto.
 *     emptyHtml (scene)      : HTML del estado vacío cuando no hay items.
 *     tag       ('div'|'tr') : envoltorio del toggle (grilla o fila de tabla).
 *     colspan   (1)          : colspan cuando tag='tr'.
 *     wrapperClass           : clase del contenedor que envuelve los items (ej. notif-list).
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

    const body = visible.join('') + toggleHtml;
    if (tag !== 'tr' && config.wrapperClass) {
        container.innerHTML = `<div class="${config.wrapperClass}">${body}</div>`;
    } else {
        container.innerHTML = body;
    }
    return container.innerHTML;
}

export function resetCappedState(container) {
    if (container && container.id) capState[container.id] = false;
}

/**
 * LISTA PAGINADA (v1.0)
 * Alternativa a renderCappedList: en vez de "Ver todas / Ver menos", muestra de a
 * N items con una barra navegadora (anterior / numeros de pagina / siguiente).
 *
 * config: {
 *     pageSize  (10)      : items por pagina.
 *     tag       ('div'|'tr'): tipo de item.
 *     colspan   (1)       : colspan del renglon del pager cuando no hay navContainer y tag='tr'.
 *     navContainer        : elemento (o id) donde va la barra; si falta, se inyecta junto a los items.
 *     wrapperClass        : clase del contenedor que envuelve los items.
 *     emptyHtml           : HTML del estado vacio.
 *     fillRow             : HTML de una fila/celda vacia para rellenar la ultima pagina
 *                           (solo si hay mas de una pagina) y mantener altura estable.
 *     onPage (fn)         : re-render del caller al cambiar de pagina.
 * }
 */
const pageState = {};
const pageRenders = {};

export function renderPaginatedList(container, itemsHtml, config = {}) {
    if (!container) return;
    const navTarget = _resolveNav(container, config);

    if (!itemsHtml || itemsHtml.length === 0) {
        container.innerHTML = config.emptyHtml != null ? config.emptyHtml : '';
        if (navTarget && navTarget !== container) navTarget.innerHTML = '';
        return;
    }

    const pageSize = config.pageSize || 10;
    const tag = config.tag || 'div';
    const colspan = config.colspan > 0 ? config.colspan : 1;
    const id = container.id || (container.id = 'paged-list-' + (++capSeq));

    const pages = Math.max(1, Math.ceil(itemsHtml.length / pageSize));
    let page = pageState[id] || 1;
    if (page > pages) page = pages;
    if (page < 1) page = 1;
    pageState[id] = page;

    pageRenders[id] = () => renderPaginatedList(container, itemsHtml, config);

    const slice = itemsHtml.slice((page - 1) * pageSize, page * pageSize);
    let body = slice.join('');
    if (config.fillRow && pages > 1 && page === pages && slice.length < pageSize) {
        body += config.fillRow.repeat(pageSize - slice.length);
    }
    container.innerHTML = (tag !== 'tr' && config.wrapperClass)
        ? `<div class="${config.wrapperClass}">${body}</div>` : body;

    if (navTarget) {
        if (pages > 1) {
            const pager = _buildPager(id, page, pages);
            if (navTarget !== container) {
                navTarget.innerHTML = pager;
            } else if (tag === 'tr') {
                container.innerHTML += `<tr><td colspan="${colspan}"><div class="pagination-premium flex-row items-center justify-center gap-20 py-20">${pager}</div></td></tr>`;
            } else {
                container.innerHTML += `<div class="pagination-premium flex-row items-center justify-center gap-20 py-20">${pager}</div>`;
            }
        } else if (navTarget !== container) {
            navTarget.innerHTML = '';
        }
    }
}

function _resolveNav(container, config) {
    if (config.navContainer) {
        return (typeof config.navContainer === 'string')
            ? document.getElementById(config.navContainer)
            : config.navContainer;
    }
    return container;
}

function _buildPager(id, page, pages) {
    return `
        <button class="btn--icon sm" ${page <= 1 ? 'disabled' : ''} onclick="__pageGoto('${id}',${page - 1})" title="Página anterior">
            <i class="fas fa-chevron-left"></i>
        </button>
        <span class="text-small text-muted font-bold">Página ${page} de ${pages}</span>
        <button class="btn--icon sm" ${page >= pages ? 'disabled' : ''} onclick="__pageGoto('${id}',${page + 1})" title="Página siguiente">
            <i class="fas fa-chevron-right"></i>
        </button>`;
}

export function resetPaginatedState(container) {
    if (container && container.id) pageState[container.id] = 1;
}

window.__capToggleList = (id) => {
    const fn = capToggleIds[id];
    if (typeof fn === 'function') fn();
};

window.__pageGoto = (id, p) => {
    const fn = pageRenders[id];
    if (typeof fn === 'function') { pageState[id] = p; fn(); }
};