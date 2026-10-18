"""Explicaciones analizadas de templates/base.html + templates/components/ (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "templates/base.html": {
        "proposito": 'Layout raíz de toda la aplicación: define el documento HTML completo (head con las hojas de estilos base, componentes y layout, más las librerías CDN de Chart.js, flatpickr, QR y html2canvas), el banner de tiempo virtual y los modales globales que se inyectan en todas las páginas, y el bloque de scripts base con api_client.js y main.js. Las páginas concretas no escriben su propio <html>: usan {% extends "base.html" %} y rellenan sus bloques; solo se incluyen como está. Además embebe el botón de instalación PWA y el registro del service worker (/sw.js), con la condición de no mostrarse en layouts con sidebar ni en páginas marcadas .no-pwa-install.',
        "simbolos": {
            "title": (
                '💡 LA IDEA: Definir la etiqueta de título que se muestra en la pestaña del navegador web.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que cada página hija personalice su nombre en la pestaña manteniendo un título descriptivo por defecto.\n\n'
                '⚙️ FUNCIONAMIENTO: Contenido del <title> del documento; por defecto "AUTOPASS - Estacionamiento Inteligente". Cada página que extiende base.html lo sobreescribe con el título propio.'
            ),
            "extra_head": (
                '💡 LA IDEA: Dejar un espacio abierto al final de la cabecera HTML para estilos y librerías particulares.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que páginas complejas carguen sus propios archivos CSS y metaetiquetas sin sobrecargar la cabecera global.\n\n'
                '⚙️ FUNCIONAMIENTO: Hueco al final del <head> para que cada página agregue CSS específico, meta tags o scripts de cabecera sin alterar el head común (es donde suelen insertarse los include de css_landing / css_dashboard / css_profile).'
            ),
            "body_class": (
                '💡 LA IDEA: Inyectar nombres de clases CSS dinámicas en la etiqueta principal del cuerpo de la página.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite alternar estilos estructurales (como habilitar la barra lateral o temas oscuros) según la sección activa.\n\n'
                '⚙️ FUNCIONAMIENTO: Clases del elemento <body>; vacías por defecto. Las páginas las definen para activar variantes de layout o comportamiento (por ejemplo layout-with-sidebar en dashboard/perfil, que también condiciona la instalación PWA y el botón del reloj virtual).'
            ),
            "content": (
                '💡 LA IDEA: El contenedor central donde se ubica el contenido visual principal de cada pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Actúa como el lienzo principal que las vistas hijas rellenan con sus formularios, tablas y tarjetas.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo principal de la página: hueco central que cada plantilla hija rellena con su markup (landing, dashboard, perfil, etc.). Se renderiza entre el banner de tiempo virtual y los modales globales, que base.html incluye siempre.'
            ),
            "extra_scripts": (
                '💡 LA IDEA: Reservar una sección al pie del documento para cargar scripts y módulos JavaScript complementarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el código interactivo específico de cada vista se ejecute después de haberse cargado las librerías base y el DOM.\n\n'
                '⚙️ FUNCIONAMIENTO: Hueco de scripts posteriores a los scripts base (Leaflet, api_client.js, main.js) pero anteriores al bloque de PWA/service worker; cada página carga ahí sus módulos JS específicos.'
            ),
        },
    },
    "templates/components/auth_modals.html": {
        "proposito": 'Parcial de modales de autenticación de la landing: trae los cuatro diálogos de cuentas —login (con botones OAuth de Google/Facebook y formulario email+contraseña), recuperación de contraseña, registro completo (con validación visual de fortaleza de clave) y completamiento de registro social (OAuth con DNI/teléfono obligatorios)—. Se inyecta con {% include %} en las páginas públicas (index, nuestra_red, contacto, terminos, privacidad) y se abre/cierra con openModal/switchModal desde la navbar y los enlaces de texto de cada modal. No define bloques: es HTML fijo.',
        "simbolos": {
        },
    },
    "templates/components/chart_window_controls.html": {
        "proposito": 'Barra de controles de ventana de tiempo para los gráficos (Chart.js): checkbox "seguir en vivo", selector de ventana (6 a 168 horas o toda la historia), botones de salto a INICIO/FINAL, deslizador de rango para recorrer el histórico y una línea de ayuda. Es parametrizable: recibe prefix para los ids (así varios gráficos conviven en una misma página) y default_span para precargar la ventana seleccionada (por defecto "24"). Se incluye con {% include %} en estadisticas_ocr.html. No tiene bloques Jinja2.',
        "simbolos": {
        },
    },
    "templates/components/css_dashboard.html": {
        "proposito": 'Agrupador de las hojas de estilo exclusivas del dashboard: declara los siete <link> a static/css/pages/dashboard/ (base, live, cards, tables, settings, admin-tour y metrics), todos con ?v={{ cache_buster }} para invalidación de caché. Existe para que dashboard.html los cargue con un único {% include %} dentro de su bloque extra_head sin duplicar el listado. No tiene bloques: es solo marcado de enlaces.',
        "simbolos": {
        },
    },
    "templates/components/css_landing.html": {
        "proposito": 'Agrupador de las hojas de estilo de las páginas públicas/landing: carga con {% include %} los cuatro CSS de static/css/pages/landing/ (nav, hero, features y modals) con cache_buster, compartidos por index, nuestra_red, contacto, terminos, privacidad y reset_password para no repetir los <link> en cada una. No tiene bloques: es solo marcado de enlaces.',
        "simbolos": {
        },
    },
    "templates/components/css_profile.html": {
        "proposito": 'Agrupador de las hojas de estilo del portal de usuario: declara los siete <link> a static/css/pages/profile/ (base, vehicles, reservations, points, tour, help y notifications) con cache_buster. Se incluye desde perfil.html y también desde dashboard.html (que reutiliza el tour/notificaciones de perfil). No tiene bloques: es solo marcado de enlaces.',
        "simbolos": {
        },
    },
    "templates/components/footer.html": {
        "proposito": 'Pie de página común de la landing: marca y redes sociales, columnas de navegación, enlaces legales (términos/privacidad), soporte (teléfono y email tomado de {{ settings.CONTACT_INFO }}) y badges de descarga de apps, más la barra de copyright. Se agrega con {% include %} al final del bloque content de index, nuestra_red, contacto, terminos y privacidad. HTML fijo, sin bloques.',
        "simbolos": {
        },
    },
    "templates/components/modal_header.html": {
        "proposito": 'Macro Jinja2 modal_header: banda estándar de cabecera de los modales del dashboard y del perfil (icono + badge opcional + título + subtítulo opcional + botón de cierre), que unifica el header de todos los diálogos de contenido. Se importa con {% from ... import modal_header %} en dashboard.html, sus tabs/modals y profile/modals. Soporta ids opcionales para títulos/iconos/subtítulos que el JS rellena en caliente y bloque caller para acciones propias del modal; el onclick del cierre se emite con |safe. No tiene bloques: es una macro.',
        "simbolos": {
        },
    },
    "templates/components/modals_global.html": {
        "proposito": 'Infraestructura de avisos compartida por toda la app, incluida siempre desde base.html: el modal de confirmación genérico (#modal-confirm con botones CONFIRMAR/CANCELAR que usa el JS de confirm()), el contenedor de toasts (#toast-container con role=status y aria-live=polite para que el lector de pantalla anuncie los avisos de showToast) y el modal de elección (#modal-choice con cuadrícula de opciones inyectada por JS). HTML fijo, sin bloques.',
        "simbolos": {
        },
    },
    "templates/components/monitoreo_controls.html": {
        "proposito": 'Contenedor del mapa de cámaras del monitoreo en vivo: crea el div #cctv-grid vacío, que el JS de la página llena dinámicamente con los tiles de CCTV. Se incluye con {% include %} en monitoreo_live.html justo antes de sus scripts. Es marcado deliberadamente mínimo porque todo el contenido lo genera el frontend; no tiene bloques.',
        "simbolos": {
        },
    },
    "templates/components/navbar.html": {
        "proposito": 'Barra de navegación de la landing: botón de menú móvil, logo, enlaces a Inicio/Nuestra Red/Contacto (con clase active calculada según request.url.path) y el bloque de acciones de autenticación con dos estados: #auth-guest-actions (botones que abren loginModal y registerModal) y #auth-user-actions oculto por defecto (Mi Perfil y Cerrar Sesión), que el JS alterna según sesión. Se incluye con {% include %} en index, nuestra_red, contacto, terminos y privacidad. Sin bloques.',
        "simbolos": {
        },
    },
    "templates/components/saludo.html": {
        "proposito": 'Macro Jinja2 saludo: encabezado unificado de los siete tabs del portal /perfil (antes cada tab maquetaba el suyo propio). Compone un lead (icono de Font Awesome o iniciales de avatar), un h1 con título y opcionalmente subtítulo, y un slot extra vía {% call %} para botones a la derecha; acepta ids para que el JS rellene nombre e iniciales y clases para variantes (hero de ayuda, avatar de cuenta). Se importa con {% from ... import saludo %} en todos los tabs de profile/. El raíz es un <div> y no un <header> a propósito para no heredar el sticky del header del portal. Sin bloques: es una macro.',
        "simbolos": {
        },
    },
    "templates/components/sidebar_user.html": {
        "proposito": 'Barra lateral de navegación del portal de usuario (/perfil): logo, los siete items de sección (inicio, vehiculos, reservas, puntos, notificaciones con badge de no leídas, ayuda y perfil) que cambian de tab vía showSection(...) cerrando además el menú móvil, botón de colapso del sidebar y pie con Cerrar Sesión. Se incluye con {% include %} en perfil.html, dentro del layout con sidebar. HTML fijo, sin bloques.',
        "simbolos": {
        },
    },
    "templates/components/virtual_time_banner.html": {
        "proposito": 'Widget global de tiempo virtual (herramienta de administración para simular el reloj del sistema), incluido por base.html en todas las páginas: un botón flotante #vt-fab con badge ON y su modal con reloj grande, hora real, offset activo, botones de adelantar/retrasar, fijar fecha exacta y restaurar tiempo real, más todo el JS que consume /v1/system/virtual-time y /v1/admin/virtual-time/*, expone window.getVirtualNow() y refresca reservas/transacciones/badges tras cada cambio. El FAB solo se muestra en layouts con sidebar y para roles operativos (admin/local_admin/staff); el cierre pasa por openModal/closeModal de ui.js para devolver el foco. Sin bloques.',
        "simbolos": {
        },
    },
}
