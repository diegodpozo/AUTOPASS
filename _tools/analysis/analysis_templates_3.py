"""Explicaciones analizadas de templates (emails + páginas sueltas), lote 3."""

ANALISIS: dict[str, dict] = {
    "templates/emails/admin_invitation.html": {
        "proposito": 'Correo de invitación que se envía a una persona designada como Administrador General para que configure su contraseña y acceda al panel. Es un HTML autónomo (tabla de 600px, estética negro/dorado de AUTOPASS) con un único botón que apunta a `activation_url` y una nota de que el enlace vence a las 72 horas; saluda por `user_name`.',
        "simbolos": {
        },
    },
    "templates/emails/recovery.html": {
        "proposito": 'Correo de recuperación de contraseña: avisa al usuario (`user_name`) que se recibió una solicitud de restablecimiento y le ofrece un botón hacia `recovery_url`, aclarando que si él no la hizo puede ignorarlo. Plantilla autónoma con la misma estética de tablas que el resto de los correos y aviso de vencimiento del enlace a los 30 minutos.',
        "simbolos": {
        },
    },
    "templates/emails/registration_confirmation.html": {
        "proposito": 'Confirmación de registro: notifica a `user_name` que su cuenta en AUTOPASS quedó activa y su contraseña configurada, e incluye un botón hacia `login_url` para ingresar. HTML autónomo de bienvenida con la franja dorada del encabezado y el pie de copyright 2026.',
        "simbolos": {
        },
    },
    "templates/emails/reservation_auto_cancelled.html": {
        "proposito": 'Aviso de cancelación automática de una reserva (`user_name`): explica que no fue abonada y que no se detectó el ingreso del vehículo en el plazo, y muestra un recuadro con la sucursal, la patente y la fecha de inicio. Recibe el objeto `res_data` (campos `id`, `sucursal`, `patente`, `fecha_inicio`) e invita a reservar de nuevo desde el panel.',
        "simbolos": {
        },
    },
    "templates/emails/reservation_confirmation.html": {
        "proposito": 'Pase digital de la reserva: correo tipo ticket con el logo embebido en base64 (`logo_base64`) y el código QR (`qr_data_url`) que se presenta en el lector si falla el reconocimiento de patente. Arma la grilla de datos desde `res_data` (`id` formateado a 6 dígitos, `patente`, `fecha_fin`, `sucursal`, `direccion`) y usa una tipografía monoespaciada para la patente y el número de reserva.',
        "simbolos": {
        },
    },
    "templates/emails/reservation_reminder.html": {
        "proposito": 'Recordatorio que se envía 30 minutos antes del inicio de la reserva: si el booleano `pagada` es verdadero indica presentar el pase QR; si es falso advierte en color que la reserva impaga se cancelará automáticamente si no se abona ni se ingresa, y pide pagarla desde el panel. Muestra sucursal, patente y `fecha_inicio` tomados de `res_data`, con el saludo `user_name`.',
        "simbolos": {
        },
    },
    "templates/contacto.html": {
        "proposito": 'Página pública de contacto de AUTOPASS: hereda de base.html y presenta un hero de soporte, los canales de atención (correos tomados de `settings.CONTACT_SUPPORT` y `settings.CONTACT_EXPANSION`) y un formulario de consulta; el envío lo maneja `contacto.js`.',
        "simbolos": {
            "title": (
                "💡 LA IDEA: Asignar el título 'AUTOPASS - Contacto' a la pestaña del navegador.\n\n"
                '🎯 POR QUE FUE GENERADA: Facilita que el usuario reconozca de inmediato la pestaña de atención al cliente y soporte comercial.\n\n'
                "⚙️ FUNCIONAMIENTO: Título de la pestaña: fija 'AUTOPASS - Contacto' en el bloque `title` de base.html."
            ),
            "body_class": (
                '💡 LA IDEA: Aplicar la clase visual de fondo difuminado al elemento raíz de la página.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona el fondo estético oscuro y homogéneo característico de las páginas públicas del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica la clase `bg-blur` al body para el fondo desenfocado de las páginas públicas.'
            ),
            "extra_head": (
                '💡 LA IDEA: Vincular los estilos de la landing y la hoja CSS específica del formulario de contacto.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura la correcta diagramación de las tarjetas de canales de comunicación y campos de consulta.\n\n'
                '⚙️ FUNCIONAMIENTO: Inyecta en el head los estilos de la landing compartida (`components/css_landing.html`) más el CSS específico `/static/css/pages/contacto.css`.'
            ),
            "content": (
                '💡 LA IDEA: Estructurar la sección principal con canales de correo y formulario de mensajes.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a visitantes y usuarios enviar preguntas, solicitudes comerciales o reclamos técnicos directamente al equipo.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo de la página: incluye la navbar, el hero 'CENTRO DE SOPORTE', la grilla de canales de atención (email de soporte y de alianzas comerciales desde `settings`), el formulario de consulta (`#contactForm` con nombre, email, motivo y mensaje), el footer y los modales de autenticación."
            ),
            "extra_scripts": (
                '💡 LA IDEA: Cargar los scripts encargados de validar y enviar el formulario de contacto.\n\n'
                '🎯 POR QUE FUE GENERADA: Da interactividad a la pantalla enviando las consultas al backend de forma asíncrona sin recargar la página.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga los módulos JS `auth.js`, `landing.js` y `contacto.js`, que gestionan la autenticación, la landing y el envío del formulario de contacto.'
            ),
        },
    },
    "templates/estadisticas_ocr.html": {
        "proposito": 'Panel interno de métricas del motor OCR/ALPR: muestra KPIs de latencia de reconocimiento de patentes (promedio, mínimo, máximo, percentil 90 y total de lecturas), la curva de latencia en un gráfico y el historial detallado de lecturas con filtros. Está pensado para el personal técnico y se alimenta en vivo desde `estadisticas-ocr.js`.',
        "simbolos": {
            "title": (
                "💡 LA IDEA: Fijar el título 'AUTOPASS - Estadísticas OCR & ALPR' en el navegador.\n\n"
                '🎯 POR QUE FUE GENERADA: Identifica el tablero técnico de telemetría y reconocimiento de patentes para el personal operativo.\n\n'
                "⚙️ FUNCIONAMIENTO: Título de pestaña: 'AUTOPASS - Estadísticas OCR & ALPR'."
            ),
            "body_class": (
                '💡 LA IDEA: Asignar el estilo de fondo desenfocado general al cuerpo del documento.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene la coherencia visual con el resto de los módulos de monitoreo del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica `bg-blur` al body con el fondo desenfocado de las vistas internas.'
            ),
            "extra_head": (
                '💡 LA IDEA: Cargar la hoja de estilos de métricas y gráficos de rendimiento OCR.\n\n'
                '🎯 POR QUE FUE GENERADA: Da soporte visual a la grilla de percentiles, cronogramas de latencia y tablas históricas.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga la hoja específica `/static/css/pages/estadisticas-ocr.css` con el parámetro `cache_buster` para invalidar la caché de estilos.'
            ),
            "content": (
                '💡 LA IDEA: Construir el panel con indicadores de latencia, gráfico temporal y tabla de lecturas de cámaras.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los ingenieros evaluar la precisión y velocidad del algoritmo de lectura de patentes en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Estructura del panel: navegación superior con reloj en vivo y badge de motor activo, hero con toggle de auto-refresco (5s), la grilla de cinco KPIs (`#kpi-avg`, `#kpi-min`, `#kpi-max`, `#kpi-p90`, `#kpi-count`), la toolbar de filtros (búsqueda, evento ENTRADA/SALIDA y límite de registros), el canvas `#ocrChart` con los controles compartidos de ventana temporal (`chart_window_controls.html`) y la tabla `#ocr-table-body` del historial de lecturas.'
            ),
            "extra_scripts": (
                '💡 LA IDEA: Inicializar el módulo JavaScript de monitoreo estadístico y refresco periódico.\n\n'
                '🎯 POR QUE FUE GENERADA: Conecta los gráficos con la API para actualizar automáticamente las curvas de latencia cada pocos segundos.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga como módulo `estadisticas-ocr.js` (con `cache_buster`), expone `actualizarEstadisticasOcr` y `filtrarTablaOcr` en `window` para los handlers inline y arranca con `initEstadisticasOcr()`.'
            ),
        },
    },
    "templates/index.html": {
        "proposito": 'Landing pública de AUTOPASS: la primera pantalla que ve cualquier visitante. Presenta el carrusel, las features (reservas, reconocimiento de patentes, control y pago online) y un mapa de puntos de la red, con llamados a la acción para reservar o iniciar sesión a través de los modales de autenticación.',
        "simbolos": {
            "title": (
                "💡 LA IDEA: Establecer el título principal 'AUTOPASS - Estacionamiento Inteligente' en la pestaña.\n\n"
                '🎯 POR QUE FUE GENERADA: Posiciona la marca y la propuesta de valor en el navegador de los visitantes.\n\n'
                "⚙️ FUNCIONAMIENTO: Título de pestaña: 'AUTOPASS - Estacionamiento Inteligente'."
            ),
            "body_class": (
                '💡 LA IDEA: Incorporar la clase de desenfoque de fondo al cuerpo de la portada.\n\n'
                '🎯 POR QUE FUE GENERADA: Logra una transición visual suave entre las imágenes del carrusel y las tarjetas informativas.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica `bg-blur` al body para el fondo desenfocado de la landing.'
            ),
            "extra_head": (
                '💡 LA IDEA: Enlazar los estilos comunes de navegación, hero y modales de la portada.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la estética de la landing page sin duplicar definiciones CSS.\n\n'
                '⚙️ FUNCIONAMIENTO: Incluye los estilos de la landing (`components/css_landing.html`).'
            ),
            "content": (
                '💡 LA IDEA: Desplegar la vitrina completa con carrusel, ventajas del servicio, mapa de sucursales y accesos rápidos.\n\n'
                '🎯 POR QUE FUE GENERADA: Convierte visitantes en clientes guiándolos de forma intuitiva a reservar o consultar los puntos de la red.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo de la landing: navbar compartida; sección de carrusel (`#contenedorCarrusel` con flechas prev/next, poblado por JS); frase destacada; hero con título, frase animada y botones 'RESERVÁ YA' (`irAReserva()`) y 'Conocé Más' (`/nuestra-red`); las cuatro tarjetas de features; la sección de mapa (`#map` con hint flotante y overlay de ejemplo); el footer y los modales de auth."
            ),
            "extra_scripts": (
                '💡 LA IDEA: Importar los módulos JavaScript que manejan la autenticación, animaciones y mapa interactivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda dinamismo a la portada permitiendo abrir modales de login y ubicar estacionamientos cercanos en el mapa.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga `auth.js` y `landing.js?v={{ cache_buster }}`, que dan vida al carrusel, la frase animada y el mapa de la portada.'
            ),
        },
    },
    "templates/instalar.html": {
        "proposito": 'Página suelta (sin base.html) de instalación de la PWA: muestra un código QR generado en el cliente con la URL de `settings.BASE_URL`, un botón para descargarlo en PNG y una guía paso a paso para agregar la app a Android/iPhone. Está pensada para abrirse desde el propio celular y ofrece también un enlace para abrir la app en el navegador.',
        "simbolos": {
        },
    },
    "templates/monitoreo_live.html": {
        "proposito": 'Vista de monitoreo en vivo de las cámaras y barreras: hereda de base.html y delega casi todo el markup al partial `components/monitoreo_controls.html`, que renderiza los controles de cámara y la apertura de portones. El comportamiento lo aporta el módulo `monitoreo-live.js`.',
        "simbolos": {
            "title": (
                "💡 LA IDEA: Asignar el título 'AUTOPASS - Surveillance Pro' a la pestaña del monitor de seguridad.\n\n"
                '🎯 POR QUE FUE GENERADA: Distingue la pantalla de videovigilancia y control de barreras para los operadores de playa.\n\n'
                "⚙️ FUNCIONAMIENTO: Título de pestaña: 'AUTOPASS - Surveillance Pro'."
            ),
            "body_class": (
                '💡 LA IDEA: Configurar la página a pantalla completa y suprimir el banner de instalación de PWA.\n\n'
                '🎯 POR QUE FUE GENERADA: Maximiza el espacio de visualización de video y evita distracciones en pantallas de seguridad dedicadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica `monitoreo-body no-pwa-install` para el layout a pantalla completa del monitoreo y para ocultar el aviso de instalación de la PWA en esta vista.'
            ),
            "extra_head": (
                '💡 LA IDEA: Cargar la hoja de estilos exclusiva del centro de monitoreo en vivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Estiliza la grilla de transmisiones de cámara, botones de apertura remota y estados de conexión.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga la hoja específica `/static/css/pages/monitoreo-live.css` con `cache_buster`.'
            ),
            "content": (
                '💡 LA IDEA: Disponer el contenedor de la grilla de cámaras de circuito cerrado (CCTV) y controles de barrera.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda al guardia o supervisor una visión unificada de todos los accesos vehiculares en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Incluye el partial `components/monitoreo_controls.html`, que concentra los controles de selección de sucursal, cámaras y apertura/cierre de barreras.'
            ),
            "extra_scripts": (
                '💡 LA IDEA: Cargar el controlador de recepción de transmisiones de video y comandos de portón.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite alternar cámaras, inspeccionar flujos de video y accionar barreras de entrada o salida al instante.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga `monitoreo-live.js`, expone `changeBranch`, `toggleCamera` y `openGate` en `window` para los handlers inline y arranca con `initMonitoreoLive()` al terminar el DOM.'
            ),
        },
    },
    "templates/nuestra_red.html": {
        "proposito": "Página pública 'Nuestra Red': describe el ecosistema de estacionamientos inteligentes y lista las sucursales adheridas (nombre, logo, dirección, teléfono y horario/24hs) con un enlace para verlas en el mapa; si no hay datos muestra una sucursal de ejemplo como fallback.",
        "simbolos": {
            "title": (
                "💡 LA IDEA: Mostrar 'AUTOPASS - Conocé Más' en el encabezado de la pestaña.\n\n"
                '🎯 POR QUE FUE GENERADA: Identifica la sección informativa sobre la cobertura física y expansión de la red de estacionamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Título de pestaña: 'AUTOPASS - Conocé Más'."
            ),
            "body_class": (
                '💡 LA IDEA: Aplicar la clase de fondo con efecto desenfocado.\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica el estilo gráfico con las demás páginas informativas de la plataforma.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica `bg-blur` al body para el fondo desenfocado público.'
            ),
            "extra_head": (
                '💡 LA IDEA: Incorporar las hojas de estilo compartidas de la landing institucional.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza la correcta renderización de tipografías, barras de navegación y tarjetas de sedes.\n\n'
                '⚙️ FUNCIONAMIENTO: Incluye los estilos de la landing (`components/css_landing.html`).'
            ),
            "content": (
                '💡 LA IDEA: Mostrar el catálogo de sucursales disponibles con direcciones, horarios, teléfonos y enlace al mapa.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a los conductores a encontrar el estacionamiento más conveniente antes de iniciar un viaje.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo de la página: navbar; hero 'NUESTRA RED'; bloque de innovación con lista de beneficios; y la grilla de sucursales que itera `branches` mostrando logo, nombre, estado (`branch.activa`), dirección, teléfono y horario (`is_24h`/`horario`), con enlace a `/?branch=...#map`; si `branches` está vacío dibuja una sucursal fallback 'AUTOPASS CENTRAL'. Cierra con footer y modales de auth."
            ),
            "extra_scripts": (
                '💡 LA IDEA: Cargar los scripts de soporte de navegación y modales de autenticación.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el usuario inicie sesión o reserve directamente desde la ficha de cualquier sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga `auth.js` y `landing.js?v={{ cache_buster }}` para autenticación y efectos de la landing.'
            ),
        },
    },
    "templates/perfil.html": {
        "proposito": 'Portal del cliente (entrypoint de `/perfil`): es el shell que arma el layout con barra lateral de usuario, header con notificaciones/saldo/puntos, las siete solapas del perfil (inicio, vehículos, reservas, puntos, cuenta, notificaciones, ayuda), el mapa a pantalla completa y la navegación inferior móvil. Rechaza el acceso si no hay token en `localStorage`.',
        "simbolos": {
            "title": (
                "💡 LA IDEA: Fijar el título 'AUTOPASS - Mi Perfil' en la pestaña del portal del conductor.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite al cliente saber que está administrando sus datos personales, vehículos y reservas.\n\n'
                "⚙️ FUNCIONAMIENTO: Título de pestaña: 'AUTOPASS - Mi Perfil'."
            ),
            "extra_head": (
                '💡 LA IDEA: Cargar los estilos del portal de usuario y el componente unificado de saludo.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee la apariencia de las pestañas de saldo, puntos de fidelización, reservas activas y vehículos.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga `components/css_profile.html` y, además, el CSS `saludo.css` (que solo usa esta página porque el saludo unificado no se muestra en el dashboard, aunque compartan css_profile).'
            ),
            "body_class": (
                '💡 LA IDEA: Aplicar la clase de diseño con menú lateral fijo para cuentas de usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Adapta el espacio en pantalla para ofrecer un menú lateral en computadoras y barra inferior en celulares.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica `layout-with-sidebar`, activando el layout de dos columnas con barra lateral.'
            ),
            "content": (
                '💡 LA IDEA: Montar la interfaz del portal de autoservicio del cliente con todas sus solapas de gestión.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza en un solo lugar la carga de saldo, consulta de tickets con QR, alta de patentes y soporte.\n\n'
                '⚙️ FUNCIONAMIENTO: Esqueleto del portal: script que redirige a `/` si no hay token; sidebar de usuario (`sidebar_user.html`) y su overlay móvil; header con campana de notificaciones (`#notif-badge-header`), saldo (`#balance-val`) y puntos (`#points-val`); el contenedor que incluye las solapas de `profile/tabs/*.html`; el overlay `#map-fullscreen-overlay` para el mapa de sucursales; la barra de navegación inferior (`user-footer-nav`) con accesos a inicio, reservas, pase QR y notificaciones; y cierra con `profile/modals.html`.'
            ),
            "extra_scripts": (
                '💡 LA IDEA: Cargar los scripts de gestión de saldo, canjes de puntos, vehículos y reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Conecta cada acción del cliente con la API para reflejar cambios y pagos en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Expone `settings.RESERVA_HORA_MIN_SEGUNDOS` en `window` y carga los módulos `landing.js`, `perfil.js`, `reservas.js` y `vehicles.js` (con `cache_buster`), que dan comportamiento a las solapas y al mapa.'
            ),
        },
    },
    "templates/privacidad.html": {
        "proposito": 'Página legal de Políticas de Privacidad: pagina en un artículo el texto de las cláusulas (datos recolectados, finalidad, protección, derechos del usuario y cookies), con fecha de última actualización y el correo de contacto de privacidad desde `settings.CONTACT_PRIVACY`.',
        "simbolos": {
            "title": (
                "💡 LA IDEA: Definir el título 'AUTOPASS - Políticas de Privacidad' en la ventana del navegador.\n\n"
                '🎯 POR QUE FUE GENERADA: Identifica claramente el documento legal de protección de datos personales.\n\n'
                "⚙️ FUNCIONAMIENTO: Título de pestaña: 'AUTOPASS - Políticas de Privacidad'."
            ),
            "body_class": (
                '💡 LA IDEA: Aplicar el fondo oscuro difuminado al marco del documento.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda una estética sobria y legible acorde al contenido contractual y regulatorio.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica `bg-blur` al body para el fondo desenfocado de las páginas públicas.'
            ),
            "extra_head": (
                '💡 LA IDEA: Cargar la hoja de estilos de artículos y textos legales.\n\n'
                '🎯 POR QUE FUE GENERADA: Formatea las cláusulas en columnas de lectura cómoda y con tipografía optimizada.\n\n'
                '⚙️ FUNCIONAMIENTO: Incluye los estilos de la landing y la hoja legal `/static/css/pages/legal.css`.'
            ),
            "content": (
                '💡 LA IDEA: Desplegar el articulado completo sobre tratamiento de datos, cookies y derechos ARCO.\n\n'
                '🎯 POR QUE FUE GENERADA: Cumple con los requisitos legales de transparencia informando al usuario cómo se protegen sus patentes y datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo legal: navbar, hero del título, el artículo `.legal-content` con la fecha y el texto de las cinco secciones (datos recolectados, finalidad, protección según Ley 25.326, derechos del usuario con `settings.CONTACT_PRIVACY` y cookies), el footer y los modales de autenticación.'
            ),
            "extra_scripts": (
                '💡 LA IDEA: Cargar los scripts estándar de autenticación y navegación.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el usuario inicie sesión o interactúe con el menú sin perder la lectura legal.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga `auth.js` y `landing.js` para autenticación y comportamiento de la landing.'
            ),
        },
    },
    "templates/reset_password.html": {
        "proposito": 'Página de restablecimiento de contraseña a la que llega el usuario desde el correo de recuperación: muestra un formulario de nueva clave con confirmación, validación en vivo de requisitos y un panel de éxito tras cambiarla. Se comunica con el backend vía `reset-password.js`. No define `body_class` porque no hereda el fondo `bg-blur`.',
        "simbolos": {
            "title": (
                "💡 LA IDEA: Establecer el título 'Restablecer Contraseña - AUTOPASS' en la pestaña.\n\n"
                '🎯 POR QUE FUE GENERADA: Guía al usuario en el paso final de recuperación de su cuenta de acceso.\n\n'
                "⚙️ FUNCIONAMIENTO: Título de pestaña: 'Restablecer Contraseña - AUTOPASS'."
            ),
            "extra_head": (
                '💡 LA IDEA: Incorporar estilos específicos para centrar la tarjeta de cambio de clave en pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Enfoca la atención exclusivamente en el formulario de seguridad sin elementos distractores.\n\n'
                '⚙️ FUNCIONAMIENTO: Incluye los estilos de la landing y un bloque `<style>` propio con el layout del `.reset-container`/`.reset-card`, el header y el panel de éxito.'
            ),
            "content": (
                '💡 LA IDEA: Disponer el formulario de ingreso de nueva contraseña con medidor de seguridad y confirmación.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario fijar una nueva clave segura y recibir confirmación inmediata del restablecimiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo de la página: tarjeta centrada con el panel de formulario (`#reset-form-panel`: logo, campos `#reset-password` y `#reset-password-confirm` con toggle de visibilidad, los indicadores de requisitos de contraseña y el botón de actualizar) y el panel oculto de éxito (`#reset-success-panel`) con enlace de vuelta al inicio.'
            ),
            "extra_scripts": (
                '💡 LA IDEA: Importar el script que valida los requisitos de la contraseña y envía la nueva clave encriptada.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica en tiempo real que la contraseña cumpla con mayúsculas, números y longitud mínima antes del envío.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga el módulo `reset-password.js?v={{ cache_buster }}`, que valida la clave, llama al endpoint de recuperación y alterna al panel de éxito.'
            ),
        },
    },
    "templates/terminos.html": {
        "proposito": 'Página legal de Términos y Condiciones: presenta en un artículo las seis cláusulas del servicio (objeto, registro de usuario, uso de la tecnología ALPR, tarifas y pagos, política de cancelación y reembolsos, y responsabilidad), con fecha de última actualización.',
        "simbolos": {
            "title": (
                "💡 LA IDEA: Asignar el título 'AUTOPASS - Términos y Condiciones' en el navegador.\n\n"
                '🎯 POR QUE FUE GENERADA: Identifica formalmente el contrato de servicio y normas de uso del estacionamiento.\n\n'
                "⚙️ FUNCIONAMIENTO: Título de pestaña: 'AUTOPASS - Términos y Condiciones'."
            ),
            "body_class": (
                '💡 LA IDEA: Configurar la clase de fondo oscuro general para la vista legal.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura consistencia visual con el resto de las secciones informativas del portal.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica `bg-blur` al body para el fondo desenfocado de las páginas públicas.'
            ),
            "extra_head": (
                '💡 LA IDEA: Cargar las reglas de diseño para la diagramación de textos legales y reglamentarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita una lectura clara de las secciones, responsabilidades y alcances del servicio.\n\n'
                '⚙️ FUNCIONAMIENTO: Incluye los estilos de la landing y la hoja legal `/static/css/pages/legal.css`.'
            ),
            "content": (
                '💡 LA IDEA: Presentar las cláusulas sobre uso de cámaras ALPR, tarifas, cancelaciones y reembolsos.\n\n'
                '🎯 POR QUE FUE GENERADA: Establece el marco jurídico y operativo que rige el uso de los estacionamientos de la red.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo legal: navbar, hero del título, el artículo `.legal-content` con la fecha y las seis secciones de los términos, el footer y los modales de autenticación.'
            ),
            "extra_scripts": (
                '💡 LA IDEA: Cargar los módulos base de autenticación y navegación superior.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene accesible el menú y los accesos de usuario mientras se consulta la normativa.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga `auth.js` y `landing.js` para autenticación y comportamiento de la landing.'
            ),
        },
    },
}
