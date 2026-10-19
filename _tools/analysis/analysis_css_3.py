"""Explicaciones analizadas de CSS de páginas (landing + dashboard) (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "static/css/pages/landing/landing-features.css": {
        "proposito": 'Estiliza la sección de características de la landing y las subpáginas públicas (p. ej. Nuestra Red): el grid de tarjetas de features con iconos dorados y hover con elevación, los héroes de subpágina (.page-hero con título en degradado blanco-dorado) y los bloques de contenido en columna única. Incluye la lista horizontal de chips de features y el título de sección premium (.section-title-center) con líneas y viñeta dorada decorativas.',
        "simbolos": {
        },
    },
    "static/css/pages/landing/landing-hero.css": {
        "proposito": 'Define el hero principal de la landing y su carrusel de imágenes de fondo: el contenedor del carrusel a pantalla casi completa con items superpuestos que hacen cross-fade por opacidad, las flechas circulares de navegación (anterior/siguiente) con efecto hover dorado y el texto del hero superpuesto (título con degradado y sombras, subtítulo). También estiliza la franja de frase destacada con animación de parpadeo dorado.',
        "simbolos": {
        },
    },
    "static/css/pages/landing/landing-map.css": {
        "proposito": 'Estiliza el mapa de sucursales de la landing (Leaflet): el contenedor #map con bordes redondeados, los popups personalizados con tema oscuro y borde dorado, el overlay de información al seleccionar una sucursal y el hint flotante animado que apunta al botón de geolocalización. También cubre el directorio de sucursales en lista de dos columnas (tarjetas con logo circular, estado activo/inactivo, datos de contacto y botón de ubicar en el mapa) y el control de búsqueda por localidad con autocompletado y su desplegable de resultados.',
        "simbolos": {
        },
    },
    "static/css/pages/landing/landing-modals.css": {
        "proposito": 'Contiene los estilos de la página de contacto de la landing (layout de dos columnas con información de contacto e iconos) y la animación de apertura/cierre del contenedor del formulario de reserva (#reserva-form-container con transición de max-height y opacidad). A su vez centraliza las adaptaciones responsivas globales de la landing para 768px y 640px: encabezado, carrusel, footer, CTA, features y títulos de sección.',
        "simbolos": {
        },
    },
    "static/css/pages/landing/landing-nav.css": {
        "proposito": 'Estiliza el header fijo de la landing y su navegación: barra transparente con degradado que se vuelve sólida con blur al hacer scroll (.scrolled), enlaces con subrayado dorado animado al hover, y los botones de sesión (login, registro, perfil, logout) con variantes doradas y de peligro. En mobile (≤1024px) transforma el nav en un menú lateral tipo sidebar deslizante con encabezado propio, backdrop oscuro y botón hamburguesa que se oculta al abrir.',
        "simbolos": {
        },
    },
    "static/css/pages/dashboard/dashboard-admin-tour.css": {
        "proposito": 'Estiliza el tour guiado de administración y el modal de ayuda operativa del staff: el overlay fijo con recorte SVG que resalta el elemento en foco (rectángulo dorado brillante), el tooltip del tour con badge de paso, título, texto, y botones anterior/siguiente/finalizar, más la flecha indicadora. En el modal de ayuda, define el hero con buscador, las pills de categorías, la grilla de guías rápidas con iconos de colores por módulo (CCTV, reservas, usuarios, finanzas, tickets, ajustes) y los acordeones de preguntas frecuentes agrupadas por categoría.',
        "simbolos": {
        },
    },
    "static/css/pages/dashboard/dashboard-base.css": {
        "proposito": 'Base del dashboard: controla la visibilidad por rol (RBAC) ocultando con !important bloques según las clases del body (staff, admin, local_admin) y la navegación por pestañas del dashboard (.tab-view activa/inactiva). Incluye el colapsable de estadísticas de usuarios en mobile, el ajuste responsivo de los headers de cards (búsqueda, filtros y botones a ancho completo), la revelación de acciones de fila al hover y detalles del modal de detalle de reserva y placeholders.',
        "simbolos": {
        },
    },
    "static/css/pages/dashboard/dashboard-cards.css": {
        "proposito": 'Define el header premium de las tarjetas del dashboard (icono, título dorado y acciones) que se extiende a todo el ancho de la card, las grillas de KPIs (3, 4, 6 y automática con responsive) con valores en fuente monoespaciada y etiquetas que envuelven, y las tarjetas de desglose financiero por canal de pago con estadísticas internas. También define el desglose por método de pago con solapas (tabs) y paneles animados, y los tonos peligro/claro para KPIs de alerta en la pestaña de finanzas.',
        "simbolos": {
        },
    },
    "static/css/pages/dashboard/dashboard-live.css": {
        "proposito": 'Estiliza la pestaña de monitoreo en vivo del dashboard: el layout principal (columna principal + lateral) con responsivo, las sub-pestañas (vehículos estacionados / últimos movimientos) y la grilla de estadísticas por tipo de vehículo (autos, motos, camionetas) en una sola card de varias columnas con celdas monoespaciadas. También cubre el panel de operaciones manuales (ingreso por patente con selector de piso/sector oculto por defecto) y los bloques de barreras físicas de entrada/salida con botones mini, más la paginación de la tabla en vivo.',
        "simbolos": {
        },
    },
    "static/css/pages/dashboard/dashboard-metrics.css": {
        "proposito": 'Estiliza la pestaña de métricas del dashboard: el menú de tarjetas de métricas (grid con icono, título, descripción y badge de disponibilidad, con hover y estado deshabilitado) y la vista de detalle con gráfico de entradas/salidas (leyenda con puntos de color, cuerpo del gráfico de 340px, controles de rango temporal, toggle de seguimiento en vivo y filtros desde/hasta). Incluye el mapa de calor de ocupación (grilla de días del mes × horas con celdas coloreadas, leyenda y toggle mapa/barras) y los informes de recaudación y OCR con sus notas al pie.',
        "simbolos": {
        },
    },
    "static/css/pages/dashboard/dashboard-settings.css": {
        "proposito": 'Estiliza la pestaña de ajustes del dashboard: los botones de sub-pestañas (tarifas, pisos, monitoreo, sistema), el formulario de tarifas en dos columnas y la gestión de pisos/plazas mediante bloques por nivel (indicator de piso, capacidad total, plazas por tipo editables inline con estados editing) con soporte de drag. También cubre la configuración de cámaras IP (grilla responsive de tarjetas arrastrables con acciones de habilitar/deshabilitar) y la sección de diagnóstico del sistema con tarjetas de estado de barreras (puntos online/offline con animación de pulso).',
        "simbolos": {
        },
    },
    "static/css/pages/dashboard/dashboard-tables.css": {
        "proposito": 'Reúne estilos transversales de tablas, modales y controles del dashboard: badges de estado (peligro/éxito/advertencia), anchos mínimos de columnas por pestaña, filas de reembolso y alturas uniformes en el registro de reservas admin, selects y filtros premium, el switch deslizante y el picker de iconos. También define los modales especiales: auditoría de captura (imagen + datos), salida impaga ALPR, chat de tickets de soporte (burbujas de mensajes estilo chat), modales de usuarios, sucursales (con mapa Leaflet y selector de logo) y promociones (con mapa y formulario en dos columnas).',
        "simbolos": {
        },
    },
}
