// COMPONENTE REUTILIZABLE: MENÚ DE ACCIONES POR ELEMENTO (patrón "⋮" / overflow).
// Abre/cierra el menú de una tarjeta y lo posiciona como popover.
//
// Para que no lo recorte un ancestro con overflow:hidden NI se desplace por un
// ancestro con backdrop-filter/transform/filter (que redefinen el containing
// block de position:fixed), el menú se PORTA a document.body al abrir y se
// devuelve a su wrapper al cerrar.
//
// Markup esperado dentro de cada ítem del contenedor:
//   <div class="card-action-menu-wrapper">
//     <button class="card-action-trigger" aria-haspopup="true" aria-expanded="false">...</button>
//     <div class="card-action-menu" role="menu">
//       <button class="card-action-menu__item" role="menuitem" data-action="...">...</button>
//     </div>
//   </div>
//
// Uso (listeners delegados: las tarjetas pueden re-renderizarse sin recablear):
//   enableActionMenu(container, {
//       triggerSelector: '.card-action-trigger',
//       onSelect: (action, itemEl, triggerEl) => { ... }   // opcional
//   });

const OPEN_CLASS = 'is-open';

export function enableActionMenu(container, { triggerSelector = '.card-action-trigger', onSelect } = {}) {
    if (!container) return;

    // El callback se guarda en el elemento para que cada re-render use el último.
    container._actionMenuOnSelect = onSelect;
    if (container.dataset.actionMenuReady === '1') return;
    container.dataset.actionMenuReady = '1';

    let open = null; // { menu, trigger }

    const close = () => {
        if (!open) return;
        const { menu, trigger } = open;
        menu.classList.remove(OPEN_CLASS);
        if (trigger) trigger.setAttribute('aria-expanded', 'false');
        // Devolver el menú a su wrapper (o descartarlo si la tarjeta se re-renderizó).
        const wrapper = trigger ? trigger.closest('.card-action-menu-wrapper') : null;
        if (wrapper) wrapper.appendChild(menu);
        else menu.remove();
        open = null;
    };

    const openMenu = (menu, trigger) => {
        close();
        // Portal a body: el containing block de position:fixed pasa a ser el viewport.
        document.body.appendChild(menu);
        menu.classList.add(OPEN_CLASS);
        _position(menu, trigger);
        trigger.setAttribute('aria-expanded', 'true');
        open = { menu, trigger };
    };

    container.addEventListener('click', (e) => {
        const trigger = e.target.closest(triggerSelector);
        if (!trigger || !container.contains(trigger)) return;
        e.preventDefault();
        const wrapper = trigger.closest('.card-action-menu-wrapper');
        const menu = wrapper ? wrapper.querySelector('.card-action-menu') : null;
        if (!menu) return;
        if (open && open.trigger === trigger) close();
        else openMenu(menu, trigger);
    });

    document.addEventListener('click', (e) => {
        if (open && open.menu.contains(e.target)) {
            const item = e.target.closest('.card-action-menu__item');
            if (item) {
                const trigger = open.trigger;
                close();
                const cb = container._actionMenuOnSelect;
                if (typeof cb === 'function') cb(item.dataset.action, item, trigger);
            }
            return;
        }
        if (!container.contains(e.target)) close();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') close();
    });
    window.addEventListener('resize', close);
    window.addEventListener('scroll', close, true);
}

// Popover bajo el trigger, alineado a la derecha; se voltea arriba si no entra.
function _position(menu, trigger) {
    const t = trigger.getBoundingClientRect();
    menu.style.visibility = 'hidden';
    menu.style.top = '0px';
    menu.style.left = '0px';
    const m = menu.getBoundingClientRect();
    const gap = 6;
    let top = t.bottom + gap;
    if (top + m.height > window.innerHeight - gap) {
        top = Math.max(gap, t.top - m.height - gap);
    }
    let left = t.right - m.width;
    if (left < gap) left = gap;
    if (left + m.width > window.innerWidth - gap) {
        left = window.innerWidth - m.width - gap;
    }
    menu.style.top = top + 'px';
    menu.style.left = left + 'px';
    menu.style.visibility = '';
}
