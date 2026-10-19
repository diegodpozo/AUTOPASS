"""Explicaciones analizadas de la sección CSS — lote 4 (análisis del código real).

Cubre: contacto, estadísticas OCR, páginas legales, monitoreo en vivo y las
zonas del perfil (base, ayuda, notificaciones, puntos, reservas, tour, vehículos).
En CSS no se explica selector por selector: cada entrada tiene un `proposito`
exhaustivo y `simbolos` vacío.
"""

ANALISIS: dict[str, dict] = {
    "static/css/pages/contacto.css": {
        "proposito": 'Estiliza la página de Contacto (Centro de Soporte): un layout de dos columnas en grid (1fr 1fr) que enfrenta la sección de información —título, párrafo y tarjetas de contacto con caja de icono, etiqueta dorada en mayúsculas y valor, con hover que desplaza la tarjeta— contra el contenedor del formulario premium (cabecera con título dorado, select con chevron SVG embebido y textarea sin redimensionar). Incluye un bloque de limpieza inline que centra toda la información y limita #contactForm a 400px, más los breakpoints responsivos que apilan las columnas a 1024px y reducen títulos/padding a 768px.',
        "simbolos": {
        },
    },
    "static/css/pages/estadisticas-ocr.css": {
        "proposito": 'Estiliza la página de Estadísticas OCR: barra de navegación superior con botón de volver, reloj en vivo y badge de estado; hero card con icono y acciones (toggle de auto-refresco con checkbox dorado); grilla de KPIs de latencia (mínimo, máximo, p90, conteo) con colores semánticos y tooltips flotantes construidos con pseudo-elementos ::before/::after que leen data-tooltip (variantes hacia abajo para KPIs y hacia arriba para encabezados, con ajuste para bordes izquierdos de tabla). También define la toolbar de filtros (búsqueda, evento, límite), la card del gráfico de latencia con leyenda de puntos de colores, y la tabla de eventos con badges de rendimiento (fast/medium/slow) y de tipo (entrada/salida), scroll horizontal/vertical y estado vacío.',
        "simbolos": {
        },
    },
    "static/css/pages/legal.css": {
        "proposito": 'Estiliza las páginas legales (Términos y Condiciones / Privacidad): contenedor centrado de hasta 1000px con una tarjeta oscura de radios grandes (40px) y sombra profunda, coronada por una franja dorada en degradado hecha con ::before. La fecha de actualización aparece centrada, en mayúsculas doradas y separada por un borde inferior; el cuerpo tipografía h2 dorados precedidos por una línea decorativa de 30px, párrafos con interlineado amplio y listas cuyas viñetas son el ícono check-circle de Font Awesome en dorado. A 768px se reduce el padding de la tarjeta y el tamaño de la fecha.',
        "simbolos": {
        },
    },
    "static/css/pages/monitoreo-live.css": {
        "proposito": "Estiliza la pantalla de Monitoreo en vivo (grilla CCTV): primero oculta los elementos flotantes (FAB de vídeo, modal VT y botón PWA) sobre body.monitoreo-body, y define la grilla que SIEMPRE ocupa 100vw x 100vh en fondo negro con columnas/filas gobernadas por variables --cctv-cols/--cctv-rows que setea JS. Cada caja de cámara muestra un HUD con el nombre encima del vídeo (aparece con opacidad al cargar el feed), una consola del subproceso ALPR en monoespaciada con líneas success/error resaltadas, pantalla de cámara offline o 'sin cámaras', acciones al hover (botones dorados/peligro), líneas de evento superpuestas (warning/reading con parpadeo/error) y el saludo grande de bienvenida/hasta luego sobre el video (verde para entrada, cian para salida) con animación de aparición.",
        "simbolos": {
        },
    },
    "static/css/pages/profile/profile-base.css": {
        "proposito": 'Base y layout compartido del perfil de usuario: muestra/oculta las secciones (.profile-section activa con animación slideUp) y alterna modo visualización vs. modo edición de cada campo (inputs compactos de 220px con icono, toggle de contraseña, requisitos en grilla 2 columnas y medidor de fuerza weak/medium/strong). Define los badges de saldo y puntos del header, títulos de tarjetas, el formulario de seguridad, la tarjeta de cuenta unificada (account-hub con grid 1fr auto 1fr, divisor vertical en degradado y filas de ítems con icono), el stepper de reserva (sticky bajo el header, que en ≥1281px se convierte en rail vertical al costado de la card), las estadías en curso de Mercado Pago, las stats de inicio, la paginación, y los modales de soporte/recarga/legal extraídos de los templates.',
        "simbolos": {
        },
    },
    "static/css/pages/profile/profile-help.css": {
        "proposito": "Estiliza la sección Ayuda y Soporte del perfil: buscador ancho con icono y botón de limpiar, pills de categorías (activa en degradado azul), títulos de sección, grilla de guías rápidas con tarjetas y badges de icono coloreados por tema (tour, vehículo, reserva, estrella, QR, billetera), y acordeón FAQ agrupado por categoría con transición de max-height e ícono que rota al abrir. Agrega el estado de 'búsqueda vacía', la sección de contacto en grid de dos columnas (cards de WhatsApp/email/sucursal con links) y toda la zona de tickets: formulario de consulta en dos columnas y el listado 'Mis Consultas' con pills de filtro por estado, contador, tarjetas de ticket con badge de estado coloreado (pendiente/en revisión/resuelto/cerrado) y asunto truncado a dos líneas.",
        "simbolos": {
        },
    },
    "static/css/pages/profile/profile-notifications.css": {
        "proposito": "Estiliza el sistema de notificaciones del perfil: barra de filtros con chips por categoría (activa en dorado) y botones 'marcar leídas' / 'limpiar leídas' con estados disabled; contenedor con estados vacío y spinner de carga. Cada notificación es una tarjeta con icono de categoría coloreado por tipo (success/warning/danger/support/gold), título, mensaje, hora, botones de acción internos según el tipo (confirmar, pagar, ver, soporte, seguridad, saldo, puntos, voucher, perfil, vehículos), punto dorado de no leído, botón de eliminar lateral y animación pulse para el badge de no leídas.",
        "simbolos": {
        },
    },
    "static/css/pages/profile/profile-points.css": {
        "proposito": 'Estiliza la pestaña Puntos y fidelización: la lista de vehículos con tarjetas de ancho fijo (fondo con imagen enmascarada en gris, patente estilo placa dorada, overlay de acciones favorito/eliminar que aparece al hover) y, sobre todo, la zona de puntos: overview en grid con el display del saldo y mini stats de ganados/canjeados, historial de movimientos (motivo, fecha y monto coloreado), y los vouchers —tabs con contador, grilla de cards estilo ticket con perforación y cutouts laterales, badges de estado/tipo/sucursal, botones QR y cancelar— más la variante de descuento en reserva con porcentaje grande, nota automática y correcciones ópticas de centrado para los distintos estados (vigente, usado, cancelado).',
        "simbolos": {
        },
    },
    "static/css/pages/profile/profile-reservations.css": {
        "proposito": "Estiliza Reservas e historial del perfil: el formulario de reserva (grid de 3 columnas, inputs centrados, resumen de precio oculto con .is-pendiente hasta que el JS calcula el total, botón confirmar dorado) y la lista de reservas 'ultra' (header con patente y badges de estado pagado/pendiente, timeline de progreso con pulso, grilla de detalles y actions primary/Mercado Pago/wallet/cancelar). Incluye el pase digital: modal ticket con QR sobre fondo blanco, cutouts y línea perforada, banner de estado (pendiente/cancelado/pagado/reembolsado), sección financiera con total y botones de pago wallet/MP, todo con layout horizontal compacto scoping a #ticket-to-capture y apilado en móvil; más filtros de historial, paginación, contenedores colapsables, stats de reservas, historial de ítems y la grilla horaria de disponibilidad (chips available/full/selected/in-range con distinción range-start/range-end y resumen del rango).",
        "simbolos": {
        },
    },
    "static/css/pages/profile/profile-tour.css": {
        "proposito": "Archivo multi-zona del portal del perfil: la tarjeta de puntos y la grilla de promociones/canjeo que reusa el look 'ticket' de los vouchers (costo grande en dorado, barra de filtro por sucursal, botón canjear con estado disabled); la integración del mapa (grid home de reserva+mapa, card con hint flotante y dedo indicador, overlay de sucursal, popups de Leaflet en negro con borde dorado, y layout de reserva que en ≥1281px lleva el stepper al costado); y las notificaciones in-app (badge rojo de la campana, dropdown del header con header/body/empty, botones de acción de notificación). Cierra con el auto-tour (overlay SVG con resaltado animado y tooltip premium glassmorphism con título/texto/botones), el modal de onboarding de bienvenida, la barra de navegación inferior responsive (user-footer-nav, solo ≤1024px) y el overlay de mapa a pantalla completa con su header.",
        "simbolos": {
        },
    },
    "static/css/pages/profile/profile-vehicles.css": {
        "proposito": "Estiliza la sección Vehículos del perfil: el botón 'registrar vehículo' dorado de altura generosa que alterna el formulario (su ícono chevron rota 180° al abrir y la card queda activa), con ajuste responsive a 640px donde los campos se apilan verticalmente. El contenedor del formulario nace oculto y aparece con animación fadeIn; el form compacto tiene borde dorado tenue, título centrado, labels en mayúsculas pequeñas centrados, fila de patente + marca/modelo con proporciones 35%/55%, icono de tipo de vehículo posicionado en absoluto dentro del select, y acciones centradas con botones outline (fondo negro) y primary.",
        "simbolos": {
        },
    },
}
