"""Explicaciones analizadas de base/ y layout/ + style.css (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "static/css/base/animations.css": {
        "proposito": 'Reúne los @keyframes compartidos de uso transversal (handBounce para el rebote del puntero del mapa, fadeInSlideUp para apariciones suaves y hintPulseAnim para el halo pulsante de las pistas de mapa), definidos una sola vez para no duplicarlos entre landing-map.css y profile-tour.css. Su bloque más importante es el de prefers-reduced-motion: reduce a 0.01ms con una sola iteración todas las animaciones y transiciones del sitio para que personas con sensibilidad vestibular puedan usar la app sin movimiento sostenido (WCAG 2.3.3). El valor 0.01ms (y no none/0s) y el selector html:root * (y no *) son decisiones deliberadas para que las animaciones que revelan elementos terminen en su estado final y para ganarle a las ~5 declaraciones !important de clase sin depender del orden de carga.',
        "simbolos": {
        },
    },
    "static/css/base/reset.css": {
        "proposito": 'Es el hoja de reset y base de accesibilidad del sistema: aplica box-sizing global, fija la tipografía raíz (Montserrat/Inter) y los colores de fondo/texto sobre los tokens de variables.css, y hace heredar la fuente a todos los controles de formulario. Define el anillo de foco institucional dorado en :focus-visible y una segunda regla con especificidad :root :focus-visible (0,2,0) que gana a las ~20 reglas de página que anulan outline, más excepciones puntuales de controles que ya se maquillan con :focus propio o reglas de foco que fallaban el contraste 3:1 (WCAG 1.4.11). También estandariza los estados interactivos: feedback táctil :active con scale(0.97) y estados disabled uniformes (opacidad 0.45, grises, sin puntero) para todos los botones e inputs del proyecto.',
        "simbolos": {
        },
    },
    "static/css/base/typography.css": {
        "proposito": 'Carga las familias tipográficas del proyecto desde Google Fonts (Montserrat para títulos, Inter para cuerpo y JetBrains Mono para datos monoespaciados como relojes y patentes) y fija los tamaños base de h1, h2 y h3 en función de los tokens de escala. Además provee las clases utilitarias de texto reutilizadas en todo el sitio: colores semánticos (.text-dorado, .text-danger, .text-success, .text-muted, etc.), pesos (.text-bold, .fw-800) y tamaños reducidos (.text-sm, .text-small, .text-xs). Es la capa tipográfica mínima sobre la que se apoyan componentes y páginas.',
        "simbolos": {
        },
    },
    "static/css/base/utilities.css": {
        "proposito": 'Define el repertorio de clases utilitarias atómicas para maquetar sin escribir CSS nuevo: flex (.flex-row, .flex-col, .items-center, .justify-between, .flex-1...), spacing de gap y margin/padding en escala numérica (.gap-10, .mt-20, .mb-30, .mx-auto, .p-20...), alineación y transformación de texto (.text-center, .uppercase, .font-mono) y utilidades responsivas (.flex-wrap-mobile y .hidden-mobile bajo 768px, .no-print para impresión). Incluye además el estilo del botón .cap-toggle-btn que usa el helper list-pagination.js para expandir listas con tope de filas. Su comentario explícita que pesos y tamaños de fuente viven en typography.css para evitar duplicación (DRY).',
        "simbolos": {
        },
    },
    "static/css/base/variables.css": {
        "proposito": 'Es el archivo de tokens del sistema de diseño: declara en :root toda la paleta Champagne Gold & Royal Velvet (dorados de marca, violeta premium, fondos obsidian, jerarquía de textos neutros, bordes translúcidos y colores semánticos success/danger/warning/info), el gradiente dorado, la escala tipográfica, la escala de radios, alturas estándar de controles y anchos de modal. También concentra el sistema de capas z-index ordenado (sidebar 2000 → tour 10003 → FAB 99999), los safe-areas de PWA con env() para iOS, parámetros dinámicos que sobrescribe JS (--hm-cols del mapa de calor), ~24 sombras tokenizadas y un bloque de aliases legados (--blanco, --gris-card, --secondary...) que mapean variables antiguas para no romper código preexistente. Es la hoja que carga primero en base.html: sin ella nada lo que sigue resuelve sus var().',
        "simbolos": {
        },
    },
    "static/css/layout/grid.css": {
        "proposito": 'Construye el esqueleto de dos columnas del dashboard: .layout-with-sidebar es un grid de 100vh (sidebar fija de 240px + área principal) que se anima a 80px con la clase .collapsed, y .main-content-scroll es el contenedor de scroll del contenido con degradado de fondo, overscroll-behavior contain y padding-bottom por safe-area para iOS (AC-3). Dentro, .content da el espaciado interior y .content-wrapper centra el contenido con máximo 1200px. En pantallas <=768px el grid colapsa a una sola columna y el padding se reduce, dejando paso al sidebar-drawer definido en sidebar.css.',
        "simbolos": {
        },
    },
    "static/css/layout/header.css": {
        "proposito": 'Estiliza el header sticky del dashboard: barra translúcida con backdrop-filter blur, padding que suma el safe-area superior (AC-3) y z-index 1000. Su zona izquierda (.header-left) agrupa icono decorativo en caja dorada, título principal en mayúsculas y subtítulo dorado; la derecha (.header-right) muestra el grupo de estado del sistema con el punto de salud .health-dot online pulsante (keyframes pulseStatus), el reloj monoespaciado .clock-display y la insignia dorada .admin-badge. Declara también sus propios keyframes (pulseStatus) y tres breakpoints responsivos: en <=1024px oculta el grupo de estado y el blur, y en <=768px pasa a columna centrada, esconde el icono y reduce la badge a solo su glifo.',
        "simbolos": {
        },
    },
    "static/css/layout/sidebar.css": {
        "proposito": 'Define la barra lateral de navegación del dashboard: fondo degradado, columna flexible de 100vh con logo dorado arriba, grupo de items .nav-item (con estado .active en gradiente dorado y hover tenue), separador dorado para el item de ayuda operativa (.nav-item-help) y footer rojo de cerrar sesión. El botón circular .sidebar-toggle, posicionado sobre el borde, alterna el modo colapsado (que oculta textos) mediante la clase .collapsed que maneja grid.css. En <=1024px se transforma en drawer fijo fuera de cuadro (left: -280px) que entra con .mobile-open, acompañado del botón hamburguesa .mobile-nav-toggle y el velo .sidebar-overlay, con safe-areas iOS y z-index tokenizado.',
        "simbolos": {
        },
    },
    "static/css/layout/standalone.css": {
        "proposito": 'Corrige el layout cuando la app PWA se abre instalada (display-mode: standalone) en ventanas de >=700px: fuerza con !important el layout de escritorio aunque el viewport arranque angosto, evitando que caiga en el modo móvil por el ancho de la ventana. Restaura el grid de dos columnas, devuelve la sidebar al flujo normal sin drawer ni velo, habilita el toggle de colapso y re-pliega el header a su fila horizontal completa con el grupo de estado visible. Conserva el inset de safe-area en el padding del header (paridad con header.css) para que el !important no lo anule y el contenido no quede bajo la status bar de iOS.',
        "simbolos": {
        },
    },
    "static/css/style.css": {
        "proposito": "Es el stylesheet global 'legacy' que base.html carga al final (después de components/ y layout/, junto a landing-map.css): no importa los demás —el orden de carga vive en templates/base.html:13-39— sino que conserva los estilos transversales que nunca se migraron a un módulo: el logo y .logo-text dorados, los enlaces genéricos de nav y el sistema de toasts premium (contenedor fijo arriba a la derecha con z-index --z-toast, glassmorphism, variantes success/error/info/warning/default con su color de borde e icono, y keyframes toast-entrance/toast-exit con clase .hiding para retirada). Cierra con el marcador de sucursal del mapa Leaflet (.branch-marker-logo con drop-shadow dorado y logo circular) y un ajuste responsivo puntual de .form-row <=640px. Está marcado para irse vaciando hacia los módulos por archivo.",
        "simbolos": {
        },
    },
}
