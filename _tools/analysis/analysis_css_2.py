"""Explicaciones analizadas de CSS de componentes (análisis del código real).

Lote 2: los 14 archivos de static/css/components/ (menús de acción, badges,
botones, tarjetas, controles de ventana de gráficos, pie de página, formularios,
modales, primitivas premium, saludo del portal, select-field, skeleton loaders,
tablas y tiempo virtual). En CSS no se explica selector por selector: cada
entrada lleva un `proposito` exhaustivo y `simbolos` vacío.
"""

ANALISIS: dict[str, dict] = {
    "static/css/components/action-menu.css": {
        "proposito": 'Estiliza el componente de menú de acciones por elemento (patrón "⋮" / overflow menu) que colapsa acciones repetidas como Editar y Eliminar de listas y tarjetas en un único botón desplegable, reutilizado por modules/action-menu.js. Define el disparador .card-action-trigger con su estado hover/abierto en dorado y su popover .card-action-menu (position:fixed para que un ancestro con overflow:hidden no lo recorte, con borde, sombra y estado .is-open) más los ítems .card-action-menu__item con su variante .danger para la acción destructiva. El wrapper .card-action-menu-wrapper ancla el botón arriba a la derecha de la tarjeta.',
        "simbolos": {
        },
    },
    "static/css/components/badges.css": {
        "proposito": 'Reúne las etiquetas/chips de todo el sitio: los badges de saldo y puntos (.balance-badge, .points-badge y su versión compacta .points-badge-sm), los de rol de usuario (.role-badge con variantes .admin, .local_admin, .staff y .user, cada una con su color), los de estado de reservas (.badge-status y .badge-pagado/.badge-completada/.badge-active/.badge-pendiente/.badge-activa/.badge-cancelada/.badge-inactive/.badge-reembolsado), los de tickets (.badge y sus variantes .badge-warning, .badge-info, .badge-success, .badge-outline) y los de tipo de beneficio .badge-voucher y .badge-discount. Además define las patentes de vehículo con .plate-style (aspecto de chapa, tipografía monoespaciada y variante grande .plate-style.lg).',
        "simbolos": {
        },
    },
    "static/css/components/buttons.css": {
        "proposito": 'Define el sistema de botones del proyecto siguiendo la convención BEM .btn--modificador: la base .btn y las variantes de color .btn--primary (dorado sólido), .btn--outline (borde translúcido con blur) y .btn--secondary (borde dorado que se rellena al hover), más los tamaños .btn--sm y .btn--full. Incluye la familia premium .btn--premium (degradado dorado, sombra y microinteracción, con .btn--premium.sm), los botones circulares .btn--icon y los botones compactos de tablas/monitoreo .btn--mini (con variantes .success y .danger y un pseudo-elemento que amplía el área táctil a 40px por WCAG 2.5.5). Cierra con el bloque de login social OAuth 2.0: .oauth-block, .oauth-buttons, .btn-oauth con colores de marca por proveedor (Google, Facebook), el divisor .oauth-divider y la nota .oauth-note.',
        "simbolos": {
        },
    },
    "static/css/components/cards.css": {
        "proposito": 'Estiliza las tarjetas genéricas y de métricas reutilizadas en el portal y el dashboard: la tarjeta base .card (fondo en degradado oscuro, borde que se ilumina al hover, blur y padding) con sus variantes .card--flush (sin padding) y .card-body, y el título interno .card-title en dorado. Suma las tarjetas estadísticas .stat-card (etiqueta pequeña y valor dorado grande), las tarjetas KPI .kpi-card con icono .kpi-icon, bloque .kpi-data y variante .kpi-card.highlight que resalta el valor en dorado, y las tarjetas de información/auditoría .info-card-premium (fondo translúcido y borde izquierdo dorado) con su label.',
        "simbolos": {
        },
    },
    "static/css/components/chart-window.css": {
        "proposito": 'Estiliza los controles comunes de los gráficos móviles del dashboard: el contenedor .chart-window-controls y su fila .chart-window-row que agrupan la ventana de tiempo, el seguimiento en vivo (.chart-window-live con su checkbox), las etiquetas .chart-window-label, el desplegable .chart-window-select, el deslizador de rango .chart-window-range con su pista .chart-window-range-hint y el texto de ayuda .chart-window-helper. Añade utilidades de la limpieza inline v9.34.36 (componentes/components/chart_window_controls.html): el grupo de campos .chart-window-field-group, el grupo de navegación .chart-window-nav-group con sus botones y el color dorado del icono del helper.',
        "simbolos": {
        },
    },
    "static/css/components/footer.css": {
        "proposito": 'Estiliza el pie de página modular reutilizable en la landing y las páginas públicas: el contenedor .main-footer y la grilla de columnas .footer-grid, los títulos de columna .footer-col h4, el logotipo .footer-logo con su imagen, la descripción .footer-desc y la lista de enlaces .footer-links con su efecto de desplazamiento al pasar el mouse. Incluye los iconos sociales .footer-social/.social-link (círculos que se rellenan de dorado al hover), la franja de botones de la aplicación .app-badges/.app-btn y la línea inferior .footer-bottom con la marca resaltada. Cierra con las adaptaciones responsivas a 1024px (dos columnas) y 768px (una columna, todo centrado).',
        "simbolos": {
        },
    },
    "static/css/components/forms.css": {
        "proposito": 'Da estilo a los formularios base y premium del sitio: los grupos .form-group y .form-row, las etiquetas, el contenedor con icono .input-with-icon (que reserva el espacio del icono guía pero excluye el toggle de contraseña), el texto de ayuda .field-hint y el mensaje de error .error-msg. Define la apariencia base de input/select/textarea (fondo negro, borde y foco dorado, foco visible accesible) y la familia premium del dashboard: .form-group-premium, .input-premium y .select-premium (con chevron SVG propio y opciones oscuras), el buscador .search-box-premium (que se ensancha al enfocar) y el override del tema oscuro de Flatpickr. También incluye el input numérico con flechas doradas personalizadas (.num-input-wrapper, .num-btn con sus triángulos up/down) y modificadores como .input-premium--plain y las filas de período .dynamic-row-premium--period.',
        "simbolos": {
        },
    },
    "static/css/components/modals.css": {
        "proposito": 'Estiliza los modales de todo el sitio, tanto los genéricos como los premium: el overlay .modal (cubrepantalla, blur, safe-area y overscroll contenido), el contenido .modal-content con sus tamaños .modal-content-wide y .modal-content-large, la disposición centrada .modal--centered y la variante de cabecera en banda .modal-content--banded reutilizando .card-header-premium (con subtítulos, icono, título y badge). Añade botones de cierre .close-btn, utilidades de texto y enlaces, el toggle de contraseña (como button sin cromo nativo), el área de validación con requisitos .req-item/.satisfied y el medidor de fuerza .strength-meter (weak/medium/strong), los estilos del modal de confirmación .confirm-modal-content y del de elección .choice-modal-content, la barra de acciones sticky .modal-actions-sticky y la familia .modal-premium con .modal-content-premium y .modal-close-top. El z-index de #modal-choice y #modal-confirm se documenta como relación intencional, no como token duplicable.',
        "simbolos": {
        },
    },
    "static/css/components/premium.css": {
        "proposito": 'Reúne primitivas premium reutilizables por el portal y el dashboard (extraídas de profile-base.css y profile-vehicles.css): la grilla de acciones rápidas .quick-actions-grid y los botones cuadrados con icono y etiqueta .action-btn-premium con su realce al hover. Define además el estado vacío .empty-state-premium, compuesto por el cuadro de icono pulsante .empty-icon-box (con variante .empty-icon-box--sm), su animación @keyframes iconPulse, el foco visible accesible y los textos de título y descripción.',
        "simbolos": {
        },
    },
    "static/css/components/saludo.css": {
        "proposito": 'Estiliza el saludo unificado del portal (v9.34.71), un encabezado de página compartido por las siete pestañas de /perfil que reemplaza a los antiguos welcome-card, greeting-premium, cabecera de cuenta y hero de ayuda. Define el contenedor .saludo, el icono/lead .saludo-lead con sus variantes .saludo-lead--avatar y .saludo-lead--hero, el bloque .saludo-body, el título .saludo-title y el subtítulo .saludo-sub, más el bloque de contenido adicional .saludo-extra. La variante alta .saludo--hero (pantalla de Ayuda) conserva el padillón de categorías y la paleta azul, con ajustes responsivos a 640px.',
        "simbolos": {
        },
    },
    "static/css/components/select-field.css": {
        "proposito": 'Define el componente <select> con icono leading y chevron propio, compartido por /perfil y el dashboard (selects de reserva del perfil y los cuatro de los modales de reserva del dashboard). Unifica en una base única los tres patrones de select del portal — .select-wrapper-premium select (con icono), .form-control-custom (sin icono, formulario de Ayuda) y .promo-branch-select (sin icono, barra de filtros) — con su superficie, borde, radio y chevron SVG en una variable --select-chevron, su estado de foco dorado, su popup nativo oscuro (color-scheme y accent-color) y su estado de error/obligatorio vacío (:user-invalid y .is-invalid) con borde y halo en --danger. Incluye el wrapper .select-wrapper-premium con su icono leading y las medidas específicas de cada variante.',
        "simbolos": {
        },
    },
    "static/css/components/skeleton.css": {
        "proposito": 'Estiliza los marcadores de carga (skeleton loaders) usados durante la espera de datos: el bloque base .skeleton con su brillo animado (::after y @keyframes skeleton-shimmer) y el estado .skeleton-loading que inhabilita puntero y selección. Incluye la fila de tabla .skeleton-cells (barras de ancho variable que simulan celdas), el avatar circular .skeleton-avatar, y la grilla de tarjetas .skeleton-grid con la tarjeta .skeleton-card y el ítem de lista .skeleton-list-item.',
        "simbolos": {
        },
    },
    "static/css/components/tables.css": {
        "proposito": 'Define la estética base de las tablas (cabeceras centradas en mayúsculas y celdas con borde inferior) y las utilidades de alineación .text-center, .justify-center y .table-centered. Añade las acciones que aparecen al pasar el mouse sobre una fila (tr:hover .user-actions) y los estilos de datos de usuario (.user-name, .user-dni, .ticket-email-text y .user-contact). Sobre todo incluye el layout responsivo: por debajo de 1024px cada fila se convierte en tarjeta, se ocultan las cabeceras y cada celda muestra su etiqueta con td::before generada desde data-label, con ajustes específicos por columna (Contacto, Acciones, Estado, Patente, Monto, Método de Pago, etc.).',
        "simbolos": {
        },
    },
    "static/css/components/virtual-time.css": {
        "proposito": 'Estiliza el control de tiempo virtual (herramienta de pruebas/debug): el botón flotante .vt-fab con sus estados hover y .active (en rojo y con animación @keyframes vt-pulse) y su badge .vt-fab-badge. Define el cuerpo del modal con el reloj grande .vt-big-clock (.vt-big-time y .vt-big-date), la grilla de información .vt-info-grid con sus ítems (.vt-info-label/.vt-info-value), el divisor .vt-divider, la etiqueta y botonera de acciones (.vt-actions-label, .vt-actions, .vt-btn con variantes .vt-btn-full y .vt-btn-danger) y el bloque de feedback .vt-feedback. Cierra con los ajustes de la limpieza inline v9.34.33 (components/virtual_time_banner.html) para #vt-modal y #vt-feedback (ancho del modal, labels dorado/ámbar/azul, fila de destino y botón de fijar).',
        "simbolos": {
        },
    },
}
