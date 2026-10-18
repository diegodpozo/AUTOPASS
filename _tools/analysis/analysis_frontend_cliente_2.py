"""Explicaciones analizadas de frontend-cliente (parte 2/3): notificaciones,
onboarding, alertas de operador, perfil/ayuda y formulario de reservas."""

ANALISIS: dict[str, dict] = {
    "static/js/modules/notifications-state.js": {
        "proposito": 'Submódulo de notificaciones que declara el único estado mutable compartido entre el render, el badge, las acciones, el dropdown y el polling: mantiene el intervalo de refresco, el último conteo de no leídas, el filtro activo, la cache de notificaciones y un flag para evitar refrescos concurrentes del badge.',
        "simbolos": {
            "notifState": (
                '💡 LA IDEA: Es el pizarrón central donde el sistema de notificaciones anota qué mensajes están en pantalla, si hay algún temporizador de actualización corriendo y qué filtro está activo.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que las distintas partes de las notificaciones (campana, panel, botones) se desincronicen o se pisen entre sí.\n\n'
                "⚙️ FUNCIONAMIENTO: Objeto exportado con el estado compartido del centro de notificaciones: `pollInterval` (id del timer de polling), `lastNotifCount` (último conteo no leído dibujado), `currentFilter` (filtro de la lista, por defecto 'ALL'), `cachedNotifications` (lista ya cargada) y `isUpdatingBadge` (semaforo para no pisar refrescos del badge entre sí)."
            ),
        },
    },
    "static/js/modules/notifications.js": {
        "proposito": (
            "💡 LA IDEA: Es la central de alarmas y avisos de AUTOPASS. Se encarga de hacer sonar la campanita cuando hay novedades importantes: avisos de estadías en curso, recordatorios de reservas próximas, alertas de cobro o advertencias de seguridad si alguien abrió la cuenta en un equipo nuevo.\n\n"
            "🎯 POR QUE FUE GENERADA: Un sistema de notificaciones moderno abarca muchas tareas: consultar al servidor periódicamente, actualizar la burbuja roja con el número de mensajes pendientes, desplegar el menú emergente del encabezado y ejecutar acciones rápidas (como pagar desde la notificación o saltar a la reserva). Para no sobrecargar un solo archivo, se subdividió en 8 submódulos y este archivo actúa como la fachada unificada que además pone a correr el reloj de chequeo automático.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Reexporta las funciones de listado y filtros (`loadNotifications`, `filterNotifs`), conteo en la campana (`updateNotifBadge`), marcado de leídas y eliminación (`markNotifRead`, `markAllNotifRead`, `deleteNotif`, `clearReadNotifs`, `confirmReminder`), redirecciones contextuales (`payFromNotif`, `goToReservation`, `goToVehicles`, `goToProfile`), y apertura del menú desplegable (`toggleNotifDropdown`). 2. Al completarse la carga de la página (`DOMContentLoaded`), si detecta un token de sesión activo, comprueba si existe una alerta de nuevo equipo en la memoria temporal (`sessionStorage.getItem('autopass_device_alert')`) y emite un cartel de seguridad tipo toast. 3. Inicia de inmediato el ciclo de consulta periódica (`startNotifPolling`), que cada 30 segundos pregunta al backend si hay mensajes nuevos para mantener el contador al día."
        ),
        "simbolos": {
        },
    },
    "static/js/modules/onboarding-helpers.js": {
        "proposito": 'Helpers del onboarding de reservas y de los modales legales: abre/cierra el modal de bienvenida con blur del fondo, decide si mostrarlo según primera sesión y datos del usuario, encadena el tour de alta de vehículo y carga términos/privacidad dentro de un modal desde el backend.',
        "simbolos": {
            "openReservationOnboarding": (
                '💡 LA IDEA: Es la bienvenida guiada para conductores novatos: abre una ventana elegante oscureciendo el fondo con un desenfoque tipo cine.\n\n'
                '🎯 POR QUE FUE GENERADA: Capta la atención del usuario que recién entra para enseñarle paso a paso cómo registrar su auto y hacer su primera reserva.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el modal `reservation-onboarding-modal`: lo mueve al body para que el blur de la sección no lo afecta, lo marca activo y aplica `blur(6px)` e `pointer-events:none` a la sección inicio guardando los estilos previos en `dataset` para poder restaurarlos.'
            ),
            "closeReservationOnboarding": (
                '💡 LA IDEA: Es la despedida suave de la guía de bienvenida, quitando el desenfoque del fondo y devolviendo el control al conductor.\n\n'
                '🎯 POR QUE FUE GENERADA: Cierra el tutorial de forma limpia restaurando la interacción habitual con la pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal de onboarding quitando la clase `active`, espera los 300 ms de la transición para llamar a `closeModal` y restaura filtro, eventos y `aria-hidden` de la sección inicio. No marca el tour como visto: eso solo ocurre al omitirlo o completarlo.'
            ),
            "checkFirstLoginOnboarding": (
                '💡 LA IDEA: Es el detector de primerizo: revisa si el usuario acaba de estrenar su cuenta y todavía no tiene autos ni reservas cargadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra la guía interactiva únicamente a quienes la necesitan, sin fastidiar a los clientes antiguos que ya saben usar la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Decide si corresponde mostrar el onboarding al iniciar sesión: arma una clave por usuario (`autopass_tour_seen_<id>`) o invitado y muestra el modal solo si nunca lo vio y no tiene vehículos ni reservas; en cualquier otro caso solo persiste las flags de 'ya visto' en localStorage."
            ),
            "skipReservationOnboarding": (
                "💡 LA IDEA: Es el botón de 'Omitir tour' para usuarios experimentados que prefieren explorar el sistema por su cuenta.\n\n"
                '🎯 POR QUE FUE GENERADA: Respeta la decisión del usuario anotando que ya vio la bienvenida para no volver a mostrársela nunca más.\n\n'
                "⚙️ FUNCIONAMIENTO: Acción de 'omitir' del onboarding: marca como visto el tour en localStorage (clave global y por id de usuario si existe en `userData`) y cierra el modal sin arrancar el flujo."
            ),
            "startReservationOnboarding": (
                '💡 LA IDEA: Es el inicio del paseo interactivo: abre el formulario de alta de patente y te señala con globitos explicativos dónde escribir.\n\n'
                '🎯 POR QUE FUE GENERADA: Acompaña al usuario en su primera carga vehicular para garantizar que complete su registro con éxito.\n\n'
                '⚙️ FUNCIONAMIENTO: Arranca el flujo guiado: marca el tour como visto, cierra el modal, abre el formulario rápido de vehículo con foco en patente, lanza dinámicamente el mini-tour de `quick-add` y escucha el evento global `vehicle:added` (una sola vez) para continuar con el tour posterior al alta del vehículo.'
            ),
            "openLegalModal": (
                '💡 LA IDEA: Es la ventana de lectura de Términos de Servicio o Política de Privacidad sin tener que abandonar la página.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite consultar las condiciones legales de forma inmediata en una ventana emergente sin perder lo que estabas haciendo.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga contenido legal en el modal `modal-legal-terms`: muestra un spinner, hace fetch de `/privacidad` o `/terminos`, parsea la página con DOMParser, extrae `.legal-body` e inserta su HTML (reemplazando el placeholder de contacto). Ante un error de red o de extracción escribe un mensaje de error en rojo en el cuerpo del modal.'
            ),
            "closeLegalModal": (
                '💡 LA IDEA: Es el cierre de la ventana de lectura legal que te devuelve exactamente a donde estabas en el formulario.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene un flujo de navegación ordenado y sin recargas innecesarias.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal de términos/privacidad con `closeModal` si el nodo existe en el DOM.'
            ),
        },
    },
    "static/js/modules/operator-alerts.js": {
        "proposito": 'Avisa al operador cuando la pestaña del navegador está oculta: si un evento operativo (por ejemplo una salida impaga detectada por ALPR) abre un popup con la pestaña minimizada, este helper dispara notificación del sistema, parpadeo del título, favicon rojo parpadeante y beeps de audio hasta que el operador vuelve a la pestaña. Con la pestaña visible no hace nada porque el popup ya cumple esa función.',
        "simbolos": {
            "initOperatorAlerts": (
                '💡 LA IDEA: Es la preparación del sistema de alarmas de guardia: pide permisos de sonido y notificaciones al primer clic del empleado.\n\n'
                '🎯 POR QUE FUE GENERADA: Cumple con las políticas de seguridad de los navegadores modernos para poder emitir sonidos y alertas cuando la pestaña está minimizada.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa el helper una sola vez: al volver el foco o visibilidad a la pestaña detiene todos los avisos, y en el primer `pointerdown` del usuario pide el permiso de notificaciones y desbloquea el AudioContext (requisito de los navegadores).'
            ),
            "startTitleFlash": (
                "💡 LA IDEA: Es el parpadeo del título de la pestaña del navegador que titila '¡ALERTA!' para llamar la atención del operador.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite que el empleado note un suceso urgente aunque esté trabajando en otra ventana o programa de su computadora.\n\n'
                '⚙️ FUNCIONAMIENTO: Arranca el parpadeo del título del documento: alterna cada 1 segundo entre el mensaje de alerta y el título original (guardado la primera vez); no hace nada si ya hay un timer activo.'
            ),
            "stopTitleFlash": (
                '💡 LA IDEA: Es el apagado del parpadeo del título cuando el operador hace clic y regresa a la pestaña.\n\n'
                '🎯 POR QUE FUE GENERADA: Restaura el nombre normal de la página apenas el personal atiende el aviso.\n\n'
                '⚙️ FUNCIONAMIENTO: Detiene el parpadeo del título y restaura el texto original si se había guardado.'
            ),
            "_faviconLink": (
                '💡 LA IDEA: Es el localizador del pequeño logo que aparece en la pestaña del navegador para poder cambiarle el color.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite manipular dinámicamente el ícono de la pestaña para emitir señales visuales de advertencia.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el `<link rel=icon>` del head, creándolo si no existe, para poder reemplazar su `href` durante el parpadeo.'
            ),
            "_buildAlertFavicon": (
                '💡 LA IDEA: Es el pintor de sellos rojos que dibuja un círculo rojo con un signo de admiración blanco en miniatura.\n\n'
                '🎯 POR QUE FUE GENERADA: Crea la imagen de alerta en memoria sin tener que descargar archivos pesados de internet.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja en un canvas de 64 px un círculo rojo con una exclamación blanca y devuelve su data URL PNG; el resultado se cachea para no redibujar en cada parpadeo.'
            ),
            "startFaviconFlash": (
                '💡 LA IDEA: Es la baliza visual de la pestaña: hace titilar el ícono de la página alternando entre el logo normal y el punto rojo de alarma.\n\n'
                '🎯 POR QUE FUE GENERADA: Refuerza visualmente que hay un auto esperando o un problema en la barrera si la pestaña está en segundo plano.\n\n'
                '⚙️ FUNCIONAMIENTO: Alterna el favicon cada 500 ms entre el favicon de alerta generado y el original (o el ícono 192 por defecto); no hace nada si el parpadeo ya está corriendo.'
            ),
            "stopFaviconFlash": (
                '💡 LA IDEA: Es el apagado de la baliza que devuelve el logo original a la pestaña del navegador.\n\n'
                '🎯 POR QUE FUE GENERADA: Quita las señales de emergencia cuando el operador ya está mirando la pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Detiene el parpadeo del favicon y restaura el `href` original.'
            ),
            "_ensureAudioContext": (
                '💡 LA IDEA: Es el encendido del parlante digital del navegador para habilitar la reproducción de efectos de sonido.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el sistema de audio esté disponible y despierte correctamente si el navegador lo puso a dormir.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea (o devuelve ya creado) el AudioContext del navegador, tolerando navegadores sin soporte o fallos al instanciarlo (devuelve `null` en ese caso).'
            ),
            "_beep": (
                '💡 LA IDEA: Es el generador del pitido sonoro de alarma sintetizado electrónicamente.\n\n'
                '🎯 POR QUE FUE GENERADA: Produce un tono audible claro sin depender de archivos de audio externos que podrían fallar al cargar.\n\n'
                '⚙️ FUNCIONAMIENTO: Programa un pitido de 880 Hz de 0,4 s en el reloj del AudioContext con un fade de ganancia, y lo registra en la lista de osciladores activos; al terminar se auto-elimina y apaga la bandera de sonido cuando queda sin osciladores.'
            ),
            "startAlertSound": (
                '💡 LA IDEA: Es la sirena intermitente que reproduce ráfagas de tres beeps cada pocos segundos para despertar la atención del operador.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sonido siga sonando en pestañas en segundo plano donde los temporizadores normales se suelen frenar.\n\n'
                '⚙️ FUNCIONAMIENTO: Agenda 12 repeticiones de tres beeps cada 2,5 s sobre el reloj del AudioContext (no con setInterval, porque en pestañas en segundo plano los timers se frenan mientras el audio agendado sigue sonando); reintentando el `resume` si el contexto está suspendido y evitándose a sí mismo si ya suena.'
            ),
            "stopAlertSound": (
                '💡 LA IDEA: Es el silenciador inmediato que corta todos los pitidos en el momento en que el operador atiende el llamado.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita ruidos molestos una vez que el personal ya tomó conocimiento del incidente.\n\n'
                '⚙️ FUNCIONAMIENTO: Detiene de golpe todos los osciladores en vuelo (tolerando errores al parar los que ya terminaron), vacía la lista y limpia la bandera de sonido.'
            ),
            "stopOperatorAlerts": (
                '💡 LA IDEA: Es el disyuntor general de alarmas: apaga el sonido, el parpadeo del título y el parpadeo del favicon de un solo golpe.\n\n'
                '🎯 POR QUE FUE GENERADA: Devuelve la interfaz a la calma total apenas el operador enfoca la ventana de trabajo.\n\n'
                '⚙️ FUNCIONAMIENTO: Detiene los tres tipos de aviso a la vez (título, favicon y sonido); es lo que se invoca al volver el foco o la visibilidad.'
            ),
            "notifyOperator": (
                '💡 LA IDEA: Es el centinela de guardia: detecta si el operador tiene la pestaña oculta y enciende todas las alertas sonoras y visuales a la vez.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que ningún auto quede trabado en la barrera por distracción del personal que esté usando otra aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Punto de entrada: solo actúa si `document.hidden` es verdadero. Enciende parpadeo de título (prefijo 'ALERTA:'), favicon y sonido, y si el permiso de notificaciones está concedido crea una notificación del sistema con el `tag` dado (que agrupa avisos repetidos) que al hacer clic enfoca la ventana; sin permiso o soporte, el título parpadeante alcanza como aviso."
            ),
        },
    },
    "static/js/modules/profile-help.js": {
        "proposito": "Lógica interactiva de la sección Ayuda y Soporte del perfil: FAQ con buscador y filtro por categoría, alta de tickets de soporte con adjuntos, listado paginado de 'mis consultas' con filtros por estado y modal de conversación tipo chat para responder tickets.",
        "simbolos": {
            "loadHelpBranches": (
                '💡 LA IDEA: Es la carga del selector de estacionamientos en el formulario de consultas de ayuda para indicar en qué sede ocurrió el problema.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite dirigir el ticket de soporte al personal del estacionamiento correspondiente para una respuesta más rápida.\n\n'
                "⚙️ FUNCIONAMIENTO: Carga una sola vez las sucursales en el select del ticket de soporte desde `GET /parking/branches`: precarga la opción 'General', agrega cada sucursal en formato título y respeta el valor ya elegido por el usuario."
            ),
            "ticketStateClass": (
                '💡 LA IDEA: Es la tintura de estados: asigna un color verde a resueltos, amarillo a revisiones y gris a cerrados.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita al usuario distinguir de un vistazo el avance de sus consultas.\n\n'
                "⚙️ FUNCIONAMIENTO: Mapea el estado de un ticket (ignorando mayúsculas) a la clase CSS: 'is-resolved' para resuelto/resuelta, 'is-closed' para estados terminales (cerrado/cancelado), 'is-process', 'is-review' o 'is-pending' por defecto."
            ),
            "loadMyTickets": (
                '💡 LA IDEA: Es el buzón que trae todas las consultas y reclamos realizados por el usuario ordenados desde la más reciente.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene un historial accesible de todas las conversaciones previas con el equipo de soporte.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga una sola vez las consultas del usuario desde `GET /user/support-tickets`, las ordena por fecha de creación descendente y las renderiza; muestra spinners o mensajes de error en el contenedor y libera la flag de cache si falla la conexión para poder reintentar.'
            ),
            "myTicketMatchesFilter": (
                '💡 LA IDEA: Es la lupa clasificadora que decide si un ticket debe mostrarse según la solapa activa (pendientes, en proceso o resueltos).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario ordenar su bandeja de reclamos y enfocarse en las consultas que siguen abiertas.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve si un ticket pertenece al filtro de estado activo (`myTicketsFilter`): 'pendiente', 'en_revision', 'en_proceso', 'resuelto' (incluye resuelta), 'cerrado' (incluye cancelado) o verdadero para 'all'."
            ),
            "renderMyTickets": (
                '💡 LA IDEA: Es el dibujante de las tarjetas de tickets de soporte, mostrando asunto, estado y fecha con opción de ver más o menos.\n\n'
                '🎯 POR QUE FUE GENERADA: Organiza los reclamos de forma clara y permite cliquear cualquiera de ellos para abrir la conversación.\n\n'
                "⚙️ FUNCIONAMIENTO: Dibuja la lista de tickets con sus estados, asunto, categoría, sucursal y fecha; usa `renderCappedList` para mostrar de a 6 y ofrecer 'Ver todas/Ver menos', cada tarjeta abre el modal con `openSupportTicketModal`. Sin tickets muestra un estado vacío y actualiza el contador."
            ),
            "filterMyTickets": (
                "💡 LA IDEA: Es el botón de alternar entre 'Ver pendientes', 'En proceso' o 'Todos' en la lista de soporte.\n\n"
                '🎯 POR QUE FUE GENERADA: Agiliza la búsqueda de reclamos específicos según su estado actual.\n\n'
                "⚙️ FUNCIONAMIENTO: Cambia el filtro de estado de 'mis consultas': actualiza el flag, marca la pill activa, reinicia la paginación capped y re-renderiza la lista."
            ),
            "refreshMyTickets": (
                '💡 LA IDEA: Es el botón de actualizar que vuelve a consultar al servidor para ver si el personal ya respondió tu consulta.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite comprobar respuestas nuevas al instante sin necesidad de recargar la página completa.\n\n'
                '⚙️ FUNCIONAMIENTO: Fuerza la recarga del listado de tickets limpiando la flag de cache y volviendo a llamar a `loadMyTickets`.'
            ),
            "toggleFaq": (
                '💡 LA IDEA: Es el acordeón de preguntas frecuentes: al hacer clic en una pregunta se abre su respuesta y se cierran las demás.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene la sección de ayuda prolija y fácil de leer sin abrumar con bloques gigantes de texto.\n\n'
                '⚙️ FUNCIONAMIENTO: Alterna la apertura de un ítem del FAQ y, si pertenece a una categoría, cierra los demás ítems del mismo grupo para comportarse como un acordeón exclusivo.'
            ),
            "filterHelpCategory": (
                '💡 LA IDEA: Es el selector temático de ayuda para ver solo preguntas sobre reservas, pagos o uso de la aplicación.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda al cliente a encontrar la solución a su problema puntual sin recorrer preguntas no relacionadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Selecciona la categoría de ayuda activa, marca la pill seleccionada y reaplica los filtros combinados con la búsqueda.'
            ),
            "filterHelpContent": (
                '💡 LA IDEA: Es el buscador de ayuda en tiempo real que filtra preguntas y respuestas a medida que vas escribiendo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite hallar respuestas instantáneas a dudas comunes simplemente tipeando una palabra clave.\n\n'
                '⚙️ FUNCIONAMIENTO: Al escribir en el buscador de ayuda muestra u oculta el botón de limpiar según haya texto y reaplica los filtros.'
            ),
            "clearHelpSearch": (
                '💡 LA IDEA: Es la cruz para vaciar el buscador de ayuda y volver a ver todas las categorías de preguntas.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita reiniciar la búsqueda con un solo clic.\n\n'
                '⚙️ FUNCIONAMIENTO: Vacía el buscador de ayuda, oculta el botón de limpiar y reaplica los filtros para restaurar todo el contenido.'
            ),
            "applyHelpFilters": (
                '💡 LA IDEA: Es el cerebro que combina la categoría elegida con el texto tipeado para decidir qué respuestas mostrar y cuáles ocultar.\n\n'
                '🎯 POR QUE FUE GENERADA: Ofrece una experiencia de autoservicio inteligente, abriendo automáticamente las respuestas que coinciden con tu búsqueda.\n\n'
                '⚙️ FUNCIONAMIENTO: Combina filtro de categoría y texto de búsqueda: muestra/oculta cada pregunta (y la abre si coincide con la búsqueda), oculta categorías sin coincidencias, decide la visibilidad de las guías rápidas y del bloque de contacto, y muestra el estado vacío cuando no hay resultados.'
            ),
            "submitSupportTicket": (
                '💡 LA IDEA: Es el envío de una nueva consulta o reclamo hacia el equipo de atención al cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Registra el reclamo formal en el sistema, entrega un número de ticket de seguimiento y limpia el formulario.\n\n'
                "⚙️ FUNCIONAMIENTO: Al enviar el formulario valida categoría, asunto y mensaje, desabilita el botón durante el envío a `POST /user/support-tickets` y, si salió bien, avisa con el número de ticket, limpia el formulario y refresca 'mis consultas'; en error muestra el motivo con un toast."
            ),
            "renderTicketMessages": (
                '💡 LA IDEA: Es el chat de conversación del reclamo: ubica tus mensajes a la derecha y las respuestas del personal a la izquierda con sus adjuntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga una experiencia moderna y fluida de mensajería para resolver dudas con el equipo técnico.\n\n'
                "⚙️ FUNCIONAMIENTO: Pinta la conversación del ticket en formato chat: los mensajes del cliente a la derecha (etiqueta 'Vos', borde dorado) y los de soporte a la izquierda (verde), con autor, hora, texto escapado y link a la imagen o PDF adjunto; al final baja el scroll al último mensaje."
            ),
            "handleTicketAttach": (
                '💡 LA IDEA: Es el inspector de comprobantes adjuntos: verifica que la foto o PDF elegido no supere 1 MB y tenga un formato permitido.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita el envío de archivos corruptos o gigantes que colapsen el almacenamiento o fallen al transferirse.\n\n'
                '⚙️ FUNCIONAMIENTO: Valida el archivo adjunto elegido para responder: rechaza con toast las extensiones fuera de PNG/JPG/GIF/WEBP/PDF o los archivos de más de 1 MB (limpiando el input), y si es válido lo guarda en `currentAttachFile` mostrando su nombre junto al selector.'
            ),
            "openSupportTicketModal": (
                '💡 LA IDEA: Es la apertura de la ventana de chat del reclamo, cargando todo el historial de mensajes intercambiados.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite leer las explicaciones del equipo de soporte y continuar el diálogo desde una ventana cómoda.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el modal de un ticket (sin `openModal` para no perder el scroll), lo precarga en estado de carga, hace `GET /user/support-tickets/<id>`, pinta encabezado, estado, mensajes y oculta la caja de respuesta si el ticket está en un estado terminal. Sin id, simplemente lleva a la sección ayuda.'
            ),
            "closeSupportTicketModal": (
                '💡 LA IDEA: Es el cierre de la ventana de chat del reclamo.\n\n'
                '🎯 POR QUE FUE GENERADA: Devuelve al usuario a la sección de ayuda manteniendo su navegación intacta.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal del ticket con `closeModal` y limpia el id actual.'
            ),
            "submitTicketReply": (
                '💡 LA IDEA: Es el botón de enviar mensaje dentro del chat de soporte, pudiendo adjuntar una foto de prueba.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita aportar respuestas o comprobantes para destrabar reclamos en curso.\n\n'
                '⚙️ FUNCIONAMIENTO: Envía la respuesta al ticket abierto como `FormData` (mensaje y/o adjunto) vía `PATCH .../reply`; en éxito limpia los campos, refresca la lista y vuelve a pintar los mensajes (del respuesta o recargando el ticket), dejando el botón deshabilitado solo durante la petición.'
            ),
        },
    },
    "static/js/modules/profile.js": {
        "proposito": 'Módulo del perfil de usuario: carga y muestra los datos personales, puntos y saldo, administra vouchers y promociones canjeables (con resolución de ubicación y QR de canje), el historial de puntos, la edición de campos, la contraseña, la recarga de saldo y el pago de estadías activas con Mercado Pago.',
        "simbolos": {
            "loadProfile": (
                '💡 LA IDEA: Es la carga del tablero de bienvenida del cliente: muestra su nombre, saldo, puntos acumulados y accesos a sus vehículos.\n\n'
                "🎯 POR QUE FUE GENERADA: Entrega la radiografía completa del usuario apenas entra a la sección de 'Mi Cuenta'.\n\n"
                '⚙️ FUNCIONAMIENTO: Carga `GET /user/me`, persiste el usuario en localStorage y actualiza saludo, iniciales, nombre, puntos, saldo, fecha de alta, campos de contacto (formateando teléfono y DNI) y el contador de estadías con el historial de pagos; si el rol es admin/staff inyecta el botón de acceso al panel de control.'
            ),
            "updatePointsProgress": (
                '💡 LA IDEA: Es la barra de nivel del programa de premios: muestra qué tan cerca estás de desbloquear tu próxima recompensa por puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Estimula la fidelidad del cliente informándole cuántos puntos le faltan para ganar su próximo beneficio.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja la barra de progreso hacia la siguiente recompensa usando los umbrales 500/1000/2500/5000/10000: calcula el porcentaje entre el escalón anterior y el siguiente (tope 100%) y escribe cuántos puntos faltan o el mensaje de nivel máximo.'
            ),
            "loadPointsData": (
                '💡 LA IDEA: Es el refresco total de la solapa de beneficios: recarga puntos, cupones activos y catálogo de premios.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene al día la billetera de premios tras realizar canjes o pagos.\n\n'
                '⚙️ FUNCIONAMIENTO: Refresco completo de la pestaña de puntos: recarga perfil, promociones, vouchers e historial de puntos en ese orden.'
            ),
            "switchVoucherTab": (
                "💡 LA IDEA: Es la pestaña para alternar entre cupones 'Vigentes' listos para usar y cupones 'Finalizados' que ya fueron consumidos.\n\n"
                '🎯 POR QUE FUE GENERADA: Separa las recompensas disponibles de las antiguas para no generar confusiones al momento de pagar.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia entre las pestañas VIGENTES/FINALIZADOS de vouchers, actualiza las clases de los botones, reinicia la paginación capped y re-renderiza la grilla.'
            ),
            "renderVouchers": (
                '💡 LA IDEA: Es el álbum de cupones digitales que dibuja cada beneficio con su código QR, fecha límite y botón de cómo llegar.\n\n'
                '🎯 POR QUE FUE GENERADA: Presenta tus premios con un diseño limpio y moderno para que puedas exhibirlos cómodamente en los comercios.\n\n'
                '⚙️ FUNCIONAMIENTO: Renderiza la grilla de tickets de canje según la pestaña activa: divide vigentes/finalizados, muestra contadores y estados vacíos, y por cada ticket arma la tarjeta (badge de estado y sucursal, link a Maps, vencimiento y acciones de ver ticket/cancelar). Los canjes de tipo `descuento_reserva` se delegan a `renderDiscountCard` y si falta la cache de sucursales la pide antes de volver a dibujar.'
            ),
            "renderDiscountCard": (
                '💡 LA IDEA: Es la tarjeta de descuento en reserva: un beneficio especial que se aplica de forma automática al reservar una plaza.\n\n'
                '🎯 POR QUE FUE GENERADA: Explica al conductor cómo aprovechar su porcentaje de descuento ganado sin necesidad de escanear ningún QR.\n\n'
                '⚙️ FUNCIONAMIENTO: Tarjeta especial para descuentos de reserva (no son vouchers con QR): muestra el porcentaje de descuento, la nota de que se aplica automáticamente al reservar, vencimiento y, según estado, si ya se aplicó a una reserva o se canceló; solo los vigentes tienen botón de cancelación.'
            ),
            "formatTitulo": (
                '💡 LA IDEA: Es el estilista de textos que transforma títulos en mayúsculas a una redacción armoniosa con mayúsculas y minúsculas prolijas.\n\n'
                '🎯 POR QUE FUE GENERADA: Mejora la calidad visual de las promociones en pantalla cuidando la tipografía de cada beneficio.\n\n'
                "⚙️ FUNCIONAMIENTO: Normaliza títulos en mayúsculas a tipo título ('LAVADO' → 'Lavado') dejando intactos los que ya tienen caja mixta y sin capitalizar las preposiciones de la lista de stopwords; sin título devuelve 'Beneficio AutoPass'."
            ),
            "getBranchesCache": (
                '💡 LA IDEA: Es la libreta de direcciones de sucursales en memoria para no pedir los mismos datos de estacionamientos una y otra vez.\n\n'
                '🎯 POR QUE FUE GENERADA: Acelera la apertura de cupones y mapas al reutilizar información ya descargada.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve en promesa la cache de sucursales (`GET /v1/parking/branches`), creándola una sola vez y reiniciándola en caso de error para poder reintentar; se usa para resolver direcciones de los vouchers.'
            ),
            "resolveVoucherLocation": (
                '💡 LA IDEA: Es el localizador del comercio adherido: averigua las coordenadas y dirección exacta donde tenés que ir a retirar tu premio.\n\n'
                '🎯 POR QUE FUE GENERADA: Orienta al conductor mostrándole con precisión la ubicación del local donde canjear su beneficio.\n\n'
                '⚙️ FUNCIONAMIENTO: Resuelve la ubicación de canje de un ticket: prioriza las coordenadas propias del ticket, luego las de la sucursal de su snapshot (cache de sucursales) y en última instancia solo la dirección; devuelve `{lat, lng, direccion}` o `null`.'
            ),
            "buildMapsUrl": (
                '💡 LA IDEA: Es el armador del enlace de Google Maps con la ruta hacia el local del premio.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite abrir el GPS del celular con un solo toque para llegar sin dar vueltas.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma el link de Google Maps desde la ubicación resuelta: con dirección y coordenadas usa `place/.../@lat,lng,16z` (sin el token de vista satelital), si solo hay dirección hace una búsqueda y si solo hay coordenadas una query por lat/lng.'
            ),
            "getVoucherDireccion": (
                '💡 LA IDEA: Es el texto de la calle y número donde se retira el premio para mostrarlo en la tarjeta del cupón.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda una referencia física clara antes de salir hacia el establecimiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la dirección a mostrar del voucher (propia o de la sucursal vía `resolveVoucherLocation`), vacío si no hay.'
            ),
            "getVoucherVencimiento": (
                '💡 LA IDEA: Es el recordatorio de vencimiento que calcula la fecha límite de validez (30 días) de cada cupón.\n\n'
                '🎯 POR QUE FUE GENERADA: Alerta al usuario sobre cuándo expira su recompensa para que no pierda sus puntos.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula el vencimiento del voucher: usa `fecha_vencimiento` si existe; si no, suma 30 días a `created_at` y devuelve la fecha formateada `dd-mm-aa hh:mm` (vacío ante fechas inválidas).'
            ),
            "loadVouchers": (
                '💡 LA IDEA: Es la descarga de todos los cupones ganados desde el servidor para exhibirlos en la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene sincronizada la billetera de beneficios con la base de datos de la empresa.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga los tickets de canje del usuario desde `GET /user/redemption-tickets`, los guarda en la cache, precarga la cache de sucursales y renderiza la grilla (con mensaje de error si falla).'
            ),
            "cancelVoucher": (
                '💡 LA IDEA: Es el arrepentimiento de canje: cancela un cupón no utilizado y te reintegra los puntos a tu saldo inmediatamente.\n\n'
                '🎯 POR QUE FUE GENERADA: Da tranquilidad al cliente permitiéndole recuperar sus puntos si cambió de opinión o no puede asistir al local.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancela un voucher vigente tras confirmar con el usuario: hace `POST /user/redemptions/<id>/cancel`, avisa el reembolso de puntos y recarga perfil, puntos, promos y vouchers; si falla muestra el error del backend.'
            ),
            "showCanjeTicketById": (
                '💡 LA IDEA: Es el buscador exprés que encuentra un cupón por su número y lo abre directamente en pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite acceder al QR de un beneficio directamente desde una notificación o enlace directo.\n\n'
                '⚙️ FUNCIONAMIENTO: Reabre el modal de un canje buscándolo por id en el listado completo de tickets (recargado), precarga la cache de sucursales y lo muestra con `showCanjeTicket`; avisa si no lo encuentra.'
            ),
            "populatePromoBranchFilter": (
                '💡 LA IDEA: Es el filtro de promociones por sucursal que llena el menú con los estacionamientos que tienen ofertas vigentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita encontrar beneficios exclusivos válidos en la zona por la que te movés habitualmente.\n\n'
                "⚙️ FUNCIONAMIENTO: Completa el select de filtro de promos con las sucursales existentes más la opción 'Globales' cuando hay promos sin sucursal, invalida el filtro guardado si ya no aplica y oculta la barra de filtro si no hay promos."
            ),
            "renderPromotionCards": (
                '💡 LA IDEA: Es el catálogo interactivo de recompensas donde podés mirar qué premios hay y cuánto cuesta cada uno en puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra claramente los botones de canje, deshabilitándolos si tus puntos no alcanzan para esa recompensa.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja la grilla de promociones aplicando el filtro de sucursal actual (las globales se ocultan al filtrar por sucursal), con badge de tipo (voucher o % desc), costo en puntos y botón CANJEAR deshabilitado si el usuario no alcanza el saldo de puntos.'
            ),
            "loadPromotions": (
                '💡 LA IDEA: Es la búsqueda de todas las ofertas y premios disponibles en la red de estacionamientos.\n\n'
                '🎯 POR QUE FUE GENERADA: Actualiza la vidriera de recompensas con las últimas campañas de fidelización lanzadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga las promos desde `GET /user/promotions`, guarda la cache, precarga sucursales, completa el filtro y renderiza (o muestra estados vacíos / error).'
            ),
            "applyPromoBranchFilter": (
                '💡 LA IDEA: Es el filtro instantáneo que esconde las ofertas que no corresponden a la sede seleccionada.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita hacer pedidos a internet al filtrar las ofertas directamente en la memoria del navegador.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el valor del filtro de sucursal de promos y re-renderiza la grilla sin volver a consultar al backend.'
            ),
            "loadPointsHistory": (
                '💡 LA IDEA: Es el extracto bancario de puntos: lista cada movimiento detallando cuándo ganaste o canjeaste puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza transparencia total sobre la procedencia y consumo de cada punto acumulado.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga una página del historial de puntos (`/user/points-history ?page&limit=10`), pinta cada movimiento con motivo, fecha y monto con signo, gestiona la paginación (info, botones anterior/siguiente) y actualiza los totales ganados/canjeados.'
            ),
            "changePtsPage": (
                '💡 LA IDEA: Es el paginado del historial de puntos para avanzar o retroceder entre páginas de movimientos.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene ordenada la lista de puntos sin saturar la pantalla con cientos de líneas.\n\n'
                '⚙️ FUNCIONAMIENTO: Navega el historial de puntos sumando `delta` (±1) a la página actual y recargándolo.'
            ),
            "redeemPoints": (
                '💡 LA IDEA: Es el canje confirmado: descuenta tus puntos, genera tu cupón con código QR y te muestra el comprobante.\n\n'
                '🎯 POR QUE FUE GENERADA: Concluye la operación de canje de forma segura, informando de inmediato el saldo de puntos restante.\n\n'
                '⚙️ FUNCIONAMIENTO: Canjea una promo con confirmación previa: `POST /user/redeem/<promoId>`, recarga el perfil y, si el canje es un descuento de reserva, informa que se aplicará al pagar; si es un voucher muestra el ticket con QR.'
            ),
            "showCanjeTicket": (
                '💡 LA IDEA: Es el pase digital en pantalla completa con su código QR gigante listo para que el cajero lo escanee con su teléfono.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita una lectura rápida del beneficio en garita o comercios asociados sin trabas técnicas.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el modal de ticket de canje con código normalizado a 6 dígitos, título, descripción, fechas, sucursal, dirección con link a Maps, observación y el QR del ticket (si la librería `QRCode` está cargada), usando `openModal`.'
            ),
            "closeCanjeModal": (
                '💡 LA IDEA: Es el cierre de la ventana del ticket de canje.\n\n'
                '🎯 POR QUE FUE GENERADA: Devuelve al usuario a su panel de puntos de manera limpia.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal de canje con `closeModal` si existe en el DOM.'
            ),
            "shareCanjeTicket": (
                "💡 LA IDEA: Es el botón de 'Compartir o Guardar': transforma el ticket en una foto para mandarla por WhatsApp o guardarla en el celular.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite tener el cupón a mano incluso si te quedás sin conexión de internet en el camino.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera una imagen del ticket con html2canvas (ocultando antes lo no imprimible y restaurándolo en `finally`) y la comparte con la Web Share API si el navegador soporta archivos; si no, la descarga como PNG.'
            ),
            "saveField": (
                '💡 LA IDEA: Es el guardado individual de un dato del perfil (como tu teléfono o dirección) sin recargar la página.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace ágil y moderna la edición de tu cuenta personal, avisando de inmediato si se guardó con éxito.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda un campo del perfil con `PUT /user/me` y el par campo/valor; devuelve true si salió bien (recargando el perfil) y false mostrando el error del backend.'
            ),
            "changePassword": (
                '💡 LA IDEA: Es el cambio seguro de contraseña, verificando tu clave actual antes de aceptar la nueva.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la cuenta del conductor garantizando que solo el titular legítimo pueda cambiar sus credenciales de acceso.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia la contraseña con `POST /user/change-password` enviando la actual y la nueva; devuelve true/false y avisa con toast.'
            ),
            "processRecharge": (
                '💡 LA IDEA: Es la carga simulada de fondos para abonar estadías con saldo virtual de la aplicación.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita probar flujos de pago automático dentro del entorno escolar sin dinero real.\n\n'
                '⚙️ FUNCIONAMIENTO: Recarga saldo con `POST /user/recharge-balance` por el monto indicado; en éxito recarga el perfil y devuelve true, en error muestra el motivo y devuelve false.'
            ),
            "loadActiveStays": (
                '💡 LA IDEA: Es el monitor de vehículos adentro del predio: muestra qué coches tuyos están estacionados y su importe acumulado.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber en vivo cuánto tenés que abonar para salir y ofrece el botón de pago digital anticipado.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga `GET /user/active-stays`, filtra las estadías sin pago confirmado y pinta cada una con patente, ingreso, deuda y botón de pago con Mercado Pago; oculta el contenedor si no hay resultados o error.'
            ),
            "payStayWithMp": (
                '💡 LA IDEA: Es el pago rápido de tu estadía con Mercado Pago desde la comodidad de tu celular antes de subirte al auto.\n\n'
                '🎯 POR QUE FUE GENERADA: Agiliza la salida del estacionamiento: pagás desde el teléfono y la barrera se levanta sola al llegar con la patente.\n\n'
                "⚙️ FUNCIONAMIENTO: Inicia el checkout de Mercado Pago para una estadía: tras confirmar, llama a `POST /user/mercadopago/checkout` con tipo 'estadia' y redirige a `init_point`; si falla, muestra el error."
            ),
        },
    },
    "static/js/modules/reservas-actions.js": {
        "proposito": 'Acciones sobre reservas ya creadas desde el listado del cliente: cancelación con simulación de reembolso y pago con saldo interno o con Mercado Pago, aplicando automáticamente el descuento vigente de la sucursal cuando el usuario tiene uno disponible.',
        "simbolos": {
            "cancelReservation": (
                '💡 LA IDEA: Es la anulación de una reserva con vista previa del reembolso antes de confirmar la baja.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita cancelaciones accidentales e informa al cliente cuánto dinero se le reintegrará según la política de cancelación.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancela una reserva: primero consulta `GET .../cancel-simulation` para anticipar el reembolso (y bloquear con toast si el backend indica que no se puede cancelar), pide confirmación con el monto, después hace `POST .../cancel` y en éxito recarga la lista de reservas y el perfil.'
            ),
            "payReservation": (
                '💡 LA IDEA: Es el pago de una reserva pendiente debitando el importe directamente del saldo de tu cuenta AutoPass.\n\n'
                '🎯 POR QUE FUE GENERADA: Habilita el pago instantáneo aprovechando además cualquier cupón de descuento por puntos que tengas activo.\n\n'
                '⚙️ FUNCIONAMIENTO: Paga la reserva con el saldo AutoPass: busca el descuento disponible de la sucursal de esa reserva (`GET /user/redemptions/available?sucursal=...`) para avisarlo en la confirmación, luego hace `POST .../pay` agregando `redemption_ticket_id` si aplica; en éxito informa puntos ganados, recarga reservas y perfil y dispara el evento `reservation:paid` para el tour.'
            ),
            "payReservationWithWallet": (
                '💡 LA IDEA: Es el acceso directo al pago con saldo prepago desde la lista de reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee una alternativa rápida y sin comisiones externas para asegurar tu lugar de estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Alias del pago con billetera interna: delega directamente en `payReservation` (mismo endpoint de saldo).'
            ),
            "payReservationWithMp": (
                '💡 LA IDEA: Es el botón para pagar tu reserva utilizando tarjetas de crédito, débito o dinero en cuenta de Mercado Pago.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda múltiples medios de pago bancarios a clientes que no disponen de saldo cargado en la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Paga la reserva con Mercado Pago: reutiliza el mismo descuento disponible de la sucursal, tras confirmar llama a `POST /user/mercadopago/checkout` con tipo 'reserva' (y el ticket de canje si hay) y redirige al `init_point` devuelto por MP."
            ),
        },
    },
    "static/js/modules/reservas-form-price.js": {
        "proposito": 'Tarifas y descuento del formulario de reservas: consulta las tarifas de la sucursal y el descuento vigente (con cache y token anti-race) y calcula en vivo el precio estimado por modalidad aplicando el porcentaje de descuento, dejando la foto de la cotización que luego se envía al backend para su revalidación.',
        "simbolos": {
            "vehicleRateSuffix": (
                '💡 LA IDEA: Es el selector de tarifa según manejes un auto, una moto o una camioneta.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que se aplique la tarifa justa según el tamaño del vehículo respetando la reglamentación del predio.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve el sufijo de clave tarifaria según el tipo de vehículo: '_moto' para Moto, '_camioneta' para Camioneta y '' para el resto; debe coincidir con `BillingService._tipo_key` del backend."
            ),
            "fetchRates": (
                '💡 LA IDEA: Es la consulta de precios vigentes de la sucursal elegida para saber el valor de la hora, día o mes.\n\n'
                '🎯 POR QUE FUE GENERADA: Descarga los valores actualizados de tarifas para poder cotizar tu estadía en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga las tarifas de la sucursal (o globales) desde `GET /user/rates` y las guarda en el estado, luego consulta el descuento vigente con `lazyLoadDiscount` y recalcula el precio mostrado.'
            ),
            "lazyLoadDiscount": (
                '💡 LA IDEA: Es el buscador de promociones disponibles que averigua si tenés algún descuento aplicable a la sucursal elegida.\n\n'
                '🎯 POR QUE FUE GENERADA: Aplica automáticamente tus beneficios de fidelización para que pagues menos sin tener que acordarte de cargar códigos.\n\n'
                '⚙️ FUNCIONAMIENTO: Consulta una sola vez por sucursal el descuento de reserva disponible (`GET /user/redemptions/available?sucursal=...`) y lo cachea en el estado con su `fetchedFor`; usa un token incremental (`bumpDiscountToken`) para descartar respuestas atrasadas de consultas concurrentes, y al aplicar la última vuelve a renderizar el total. Sin sucursal limpia el descuento.'
            ),
            "updateReservationPrice": (
                '💡 LA IDEA: Es el cotizador en vivo que calcula cuánto vas a pagar según el tiempo, tipo de vehículo y descuentos aplicados.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra con total claridad el desglose de precio antes de confirmar para que no haya sorpresas en el cobro.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula y pinta el precio estimado: elige la tarifa según tipo de estadía y vehículo (con fallback y media hora derivada), arma los intervalos según la modalidad (hora, día, semana, quincena o mes, con el mismo cierre 23:59 que usa el backend), aplica `computeHourlyAmount` en hora, muestra el detalle de tarifas solo en modo hora, guarda la foto de cotización (base, horas y tarifas) para enviarla al confirmar, aplica el descuento vigente con redondeo y pinta original/descuento/total (u oculta el resumen si falta sucursal o tipo), revalida el descuento lazy y sincroniza el stepper.'
            ),
        },
    },
    "static/js/modules/reservas-form-slot.js": {
        "proposito": 'Grilla horaria y disponibilidad del formulario de reservas: cachea las consultas de disponibilidad, marca fechas deshabilitadas en los calendarios, arma la grilla de slots de media hora (chips + selección por arrastre) y el badge de plazas para las estadías por período.',
        "simbolos": {
            "cachedAvailabilityGet": (
                '💡 LA IDEA: Es la memoria de disponibilidad que recuerda si había lugar en los últimos 30 segundos sin repetir consultas idénticas.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita saturar el servidor con preguntas repetidas cada vez que el usuario hace un clic en el calendario.\n\n'
                '⚙️ FUNCIONAMIENTO: Wrapper de `api.get` con cache en memoria de 30 s por URL+params para no repetir consultas en cada focus/click/change; si hay más de 50 entradas descarta la más vieja.'
            ),
            "_branchSlotRange": (
                '💡 LA IDEA: Es el cálculo del horario de atención del estacionamiento para no permitir reservas fuera de su franja operativa.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide seleccionar turnos cuando el estacionamiento está cerrado, adaptándose si la sucursal abre las 24 horas.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve el rango de la grilla horaria según la sucursal seleccionada: 00:00→23:30 si es 24 h, si no parsea el horario ('07:00 A 23:00') y devuelve desde la apertura hasta un último inicio 30 min antes del cierre (tope 23:30), con fallback legado 07:00→23:30."
            ),
            "updateDisabledDatesInPicker": (
                '💡 LA IDEA: Es el tachado de días completos en el calendario cuando el estacionamiento ya no tiene ninguna plaza libre.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra tiempo al conductor impidiendo que elija días en los que el predio ya está colmado.\n\n'
                '⚙️ FUNCIONAMIENTO: Con sucursal, vehículo y tipo elegidos, consulta `GET /user/reservations/disabled-dates` y aplica la lista de fechas bloqueadas al `disable` de cada flatpickr del formulario (hora, día, semana, quincena y mes).'
            ),
            "updateHourlySlotsUI": (
                '💡 LA IDEA: Es la grilla interactiva con botones de media hora que muestra qué horarios están libres, ocupados o reservados.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite elegir con precisión quirúrgica el horario de llegada y salida viendo la disponibilidad real de cada franja.\n\n'
                "⚙️ FUNCIONAMIENTO: Dibuja la grilla de slots solo en modalidad 'hora': pide `GET /user/reservations/disabled-hours`, combina los rangos reservados, los slots que el servidor deshabilitó por capacidad y los bloqueados en el día por anticipación mínima (reloj virtual), y pinta chips de 30 min con su estado (libre, reservado, pasado, inicio/fin y dentro del rango elegido), más un resumen de la selección y mensajes guía cuando faltan sucursal, vehículo o fecha. También reinicia el rango si cambió la fecha."
            ),
            "_hourlySelectionSummary": (
                "💡 LA IDEA: Es el cartelito de resumen horario que dice 'Inicio: 14:00 - Fin: 16:30 (Duración: 2h 30m)'.\n\n"
                '🎯 POR QUE FUE GENERADA: Brinda confirmación visual inmediata del rango horario seleccionado en los botoncitos de la grilla.\n\n'
                '⚙️ FUNCIONAMIENTO: HTML del resumen de la selección horaria: hint inicial si no hay inicio, o chips de INICIO/FIN con la duración en horas calculada en media hora.'
            ),
            "selectHourRange": (
                '💡 LA IDEA: Es la selección por clics en los bloques de horario para marcar el inicio y el final de la estadía.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita elegir el horario con un par de toques sencillos desde computadoras o celulares.\n\n'
                '⚙️ FUNCIONAMIENTO: Selección por clics (ignorada mientras hay drag): si no hay inicio o el clic es anterior, reinicia el rango; si falta el fin lo fija; si ya había rango completo vuelve a empezar. Commit en el DOM al final.'
            ),
            "initHourlySlotDrag": (
                '💡 LA IDEA: Es la selección por arrastre: tocás una hora y deslizás el dedo o mouse para abarcar todo el período deseado.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace sumamente intuitiva y rápida la reserva de múltiples horas consecutivas.\n\n'
                '⚙️ FUNCIONAMIENTO: Instala los handlers de pointer sobre la grilla para seleccionar el rango arrastrando: `pointerdown` fija el inicio (con captura de puntero), `pointermove` extiende el fin o retrocede el inicio según la posición, y `pointerup`/`pointercancel` finalizan; los chips ocupados no se pueden tocar.'
            ),
            "updatePeriodAvailabilityBadge": (
                '💡 LA IDEA: Es la cucarda de disponibilidad para reservas por día, semana o mes que avisa cuántas plazas quedan libres.\n\n'
                '🎯 POR QUE FUE GENERADA: Alerta al usuario si quedan pocos lugares disponibles para estadías prolongadas antes de que se agoten.\n\n'
                '⚙️ FUNCIONAMIENTO: Para las estadías por período (no hora), arma el rango inicio/fin según el tipo (día 00:00–23:59; semana/quincena/mes de a N días cerrando 23:59), consulta `GET /user/reservations/check-availability` y muestra el badge con plazas restantes sobre el total o el aviso de sin disponibilidad; oculta la grilla horaria.'
            ),
            "resetSlotRange": (
                '💡 LA IDEA: Es el borrador de horarios que limpia la selección cuando cambiás de sucursal o de día.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene que queden horarios viejos seleccionados que no pertenezcan al nuevo día o sucursal elegidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Limpia el rango horario seleccionado (inicio, fin y fecha) y los campos del DOM (`hora` vacío y cantidad de horas en 1) para que no quede un dato obsoleto al cambiar sucursal/vehículo/tipo o resetear el formulario.'
            ),
            "setSlotRange": (
                '💡 LA IDEA: Es la carga del horario original cuando estás editando una reserva previa para que aparezca marcado en la grilla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario ver qué horario tenía reservado antes de moverlo a uno nuevo.\n\n'
                '⚙️ FUNCIONAMIENTO: Fija el rango horario del estado ({start, end, date}); se usa al preparar la edición de una reserva para reflejar su horario original en la grilla.'
            ),
        },
    },
    "static/js/modules/reservas-form-state.js": {
        "proposito": 'Única fuente de verdad del estado mutable del formulario de reservas (tarifas, vehículo en edición, flota, sucursales, descuento, totales, cotización, token anti-race e instancias de flatpickr), expuesta con getters/setters para que la fachada y los submódulos temáticos la consuman sin importarse entre sí (evitando ciclos).',
        "simbolos": {
            "getCurrentRates": (
                '💡 LA IDEA: Es la lectura de las tarifas vigentes que tiene cargadas el formulario en este momento.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee los precios a todos los componentes del formulario para cotizar con coherencia.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el objeto de tarifas vigente de la sucursal, con valores por defecto (30 min, hora, día, semana, quincena, mes).'
            ),
            "setCurrentRates": (
                '💡 LA IDEA: Es la actualización de la lista de precios de la sucursal seleccionada.\n\n'
                '🎯 POR QUE FUE GENERADA: Almacena los nuevos precios cuando el conductor cambia de estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplaza las tarifas vigentes (respuesta de `GET /user/rates`).'
            ),
            "getEditingReservaId": (
                "💡 LA IDEA: Es la pregunta de control: '¿Estamos modificando una reserva existente o creando una nueva desde cero?'.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite saber si el botón de guardar debe actualizar el turno previo o crear uno nuevo.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el id de la reserva que se está editando, o `null` si el formulario está en modo alta.'
            ),
            "setEditingReservaId": (
                '💡 LA IDEA: Es la anotación del número de reserva que se va a editar.\n\n'
                '🎯 POR QUE FUE GENERADA: Pone al formulario en modo de edición para modificar datos de una reserva ya contratada.\n\n'
                '⚙️ FUNCIONAMIENTO: Fija (o limpia con `null`) el id de la reserva en edición, lo que hace que el envío haga PATCH en lugar de POST.'
            ),
            "getUserVehicles": (
                '💡 LA IDEA: Es la consulta de los autos y motos registrados a nombre del cliente en el formulario.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta el selector de patentes para que el usuario elija con qué auto va a ir a estacionar.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la flota del usuario cargada en el formulario.'
            ),
            "setUserVehicles": (
                '💡 LA IDEA: Es el guardado de los vehículos del cliente en la memoria del formulario.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace que los vehículos estén disponibles al instante sin tener que volver a pedirlos al servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda la flota del usuario obtenida de `GET /user/vehicles`.'
            ),
            "getBranchesData": (
                '💡 LA IDEA: Es la lista de todas las sucursales cargadas en la memoria del formulario de reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite consultar horarios y comodidades de cada sede durante el proceso de reserva.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve las sucursales cargadas en el formulario.'
            ),
            "setBranchesData": (
                '💡 LA IDEA: Es el guardado de la lista de sucursales en la memoria del formulario.\n\n'
                '🎯 POR QUE FUE GENERADA: Deja las sedes listas para llenar el menú desplegable del formulario.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda las sucursales obtenidas de `GET /parking/branches`.'
            ),
            "getReservationDiscount": (
                '💡 LA IDEA: Es la consulta de qué porcentaje de descuento por puntos tiene asignado el conductor para este estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Aplica el descuento correspondiente en la pantalla de cotización.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el descuento de reserva vigente `{pct, sucursal, fetchedFor}` para la sucursal seleccionada.'
            ),
            "setReservationDiscount": (
                '💡 LA IDEA: Es el registro del descuento aplicable a la sucursal actual.\n\n'
                '🎯 POR QUE FUE GENERADA: Guarda la rebaja para que se descuente del total de la reserva.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el descuento vigente, incluida la sucursal para la que se consultó (`fetchedFor`), que habilita la cache lazy.'
            ),
            "getReservationTotals": (
                '💡 LA IDEA: Es la lectura de los importes finales calculados: el precio sin descuento, la rebaja y el total a pagar.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta el cartel de confirmación final antes de autorizar el cobro.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve los últimos totales calculados: `{original, discount, final}`.'
            ),
            "setReservationTotals": (
                '💡 LA IDEA: Es el guardado de los montos totales definitivos de la cotización.\n\n'
                '🎯 POR QUE FUE GENERADA: Fija los valores que se enviarán al servidor para su facturación.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda los totales del último cálculo (monto original, importe descontado y total final) que luego consumen la confirmación y el resumen de creación.'
            ),
            "getReservationQuote": (
                '💡 LA IDEA: Es la foto instantánea de la cotización con la tarifa por hora, fracción y cantidad de tiempo calculadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el servidor reciba la misma base de cálculo que vio el cliente en su pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la foto de la cotización vigente: `{base, horas, tarifaHora, tarifaFraccion, tarifaAplicada}`.'
            ),
            "setReservationQuote": (
                '💡 LA IDEA: Es la actualización de la foto de cotización ante cambios de horario o vehículo.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene actualizada la fórmula matemática de cobro en cada paso de la reserva.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualiza la cotización con la tarifa y duración actuales; es lo que se envía al backend para que revalide el precio y lo persista como registro histórico.'
            ),
            "getDiscountToken": (
                '💡 LA IDEA: Es el número de serie de la última consulta de descuento realizada.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite descartar respuestas viejas si el usuario cambió rápidamente de sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el contador actual del token anti-race de descuentos.'
            ),
            "bumpDiscountToken": (
                '💡 LA IDEA: Es el avance del contador de seguridad para no mezclar descuentos de estacionamientos diferentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita carreras de respuestas en internet cuando se tocan varios botones rápidamente.\n\n'
                '⚙️ FUNCIONAMIENTO: Incrementa y devuelve el token: la respuesta de una consulta de descuento solo se aplica si su token sigue siendo el último, descartando carreras entre sucursales.'
            ),
            "getFpInstances": (
                '💡 LA IDEA: Es el acceso a los calendarios interactivos del formulario de reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el sistema bloquee fechas agotadas directamente sobre los calendarios en pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el objeto con las instancias de flatpickr del formulario, para que el módulo de slots aplique las fechas deshabilitadas.'
            ),
        },
    },
    "static/js/modules/reservas-form.js": {
        "proposito": 'Fachada del formulario de reservas: orquesta su ciclo de vida (init, apertura/cierre, refresco, reset, edición, creación y repetición) coordinando flatpickr, stepper, validaciones y disponibilidad, delegando tarifas y grilla horaria a los submódulos, y re-exporta su API histórica para mantener compatibilidad con `modules/reservas.js`.',
        "simbolos": {
            "syncStepperToCardHeight": (
                '💡 LA IDEA: Es la regla visual que empareja la altura de la barra de pasos con la tarjeta del formulario en pantallas grandes.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene una estética impecable y equilibrada en monitores de escritorio.\n\n'
                "⚙️ FUNCIONAMIENTO: Calca la altura del rail del stepper a la de la card del formulario solo en desktop (≥1281 px) y cuando la modalidad no es 'hora' (donde la card crece y el sync se congela para no acompañar la expansión)."
            ),
            "initStepperHeightSync": (
                '💡 LA IDEA: Es el sensor que vigila si el formulario se agranda o achica para ajustar la barra de pasos a la par.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el diseño no se rompa cuando se despliegan campos adicionales.\n\n'
                '⚙️ FUNCIONAMIENTO: Observa la card con un ResizeObserver y con el evento `resize` para re-sincronizar el alto del stepper, haciendo una primera sincronización inicial.'
            ),
            "initReservationForm": (
                '💡 LA IDEA: Es el director de puesta en marcha del formulario: configura calendarios en español, límites de fecha y detectores de cambio.\n\n'
                '🎯 POR QUE FUE GENERADA: Deja el sistema de reservas completamente armado y listo para recibir las elecciones del usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa todo el formulario: localiza flatpickr al español, crea los calendarios (hora, día, semana, quincena, mes y rango) con min hoy y máx +3 meses, calcula las fechas de fin por defecto, engancha los listeners de tipo/vehículo/sucursal/hora que refrescan precio, fechas bloqueadas, grilla, badge y stepper, instala el drag de slots y publica `window.updateReservationStepper`.'
            ),
            "updateReservationStepper": (
                '💡 LA IDEA: Es el marcador de progreso de 4 pasos que se ilumina a medida que completás vehículo, sede y horario.\n\n'
                '🎯 POR QUE FUE GENERADA: Orienta visualmente al conductor sobre qué paso completó y qué le falta definir antes de confirmar.\n\n'
                "⚙️ FUNCIONAMIENTO: Refleja el progreso en el stepper según los datos cargados: paso 1 inicial, 2 con vehículo, 3 con sucursal, 4 con horario (en 'hora' solo si se comprometió el rango, en el resto si el usuario tocó la fecha) y 'completo' solo cuando la reserva se creó/editó de verdad; pinta las clases de pasos y líneas."
            ),
            "updatePeriodEnd": (
                '💡 LA IDEA: Es la calculadora de fecha final para semanas o meses que calcula el último día cerrando a las 23:59.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita calcular estadías de períodos largos sin que el cliente tenga que contar días en un almanaque.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula la fecha de fin de un período (inicio + días - 1, cerrando a las 23:59), la escribe en el input destino formateada dd-mm-aa hh:mm y recalcula el precio.'
            ),
            "toggleReservaForm": (
                '💡 LA IDEA: Es la persiana que abre o repliega el formulario de reserva con una animación suave en pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite mostrar el formulario cuando se lo necesita y ocultarlo para despejar la vista principal.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre o cierra el formulario con transiciones de opacidad y desplazamiento: al abrir oculta la tarjeta trigger, muestra la card y refresca su estado (vehículos, sucursales, tarifas); al cerrar la oculta, resetea el formulario y vuelve a mostrar la tarjeta.'
            ),
            "refreshReservationFormState": (
                '💡 LA IDEA: Es el reaprovisionamiento del formulario al abrirlo: pide tus vehículos actualizados, las sucursales y las tarifas vigentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que al abrir la reserva veas tus autos recién agregados y los precios reales de este instante.\n\n'
                "⚙️ FUNCIONAMIENTO: Recarga el estado del formulario al abrirlo: limpia el descuento cacheado y su token, pide tarifas, vehículos (mostrando el estado 'sin vehículos' o precargando el selector, con autoselección y apertura automática si hay un solo vehículo) y sucursales (usando el endpoint público porque `/admin/branches` da 403 a un cliente); luego vuelve a traer tarifas + descuento y actualiza el stepper."
            ),
            "resetReservaForm": (
                '💡 LA IDEA: Es el borrador total que deja el formulario impecable y en blanco para una próxima reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Limpia campos y deselecciona opciones viejas para que no queden datos cruzados de operaciones anteriores.\n\n'
                "⚙️ FUNCIONAMIENTO: Resetea el formulario al cerrarlo o tras crear: limpia flags del stepper, id en edición y rango horario, vacía el form, oculta los grupos de campos, restaura títulos y botón ('CONTINUAR' / 'GENERAR NUEVA RESERVA') y recalcula el precio."
            ),
            "prepareEditReservation": (
                '💡 LA IDEA: Es el preparador de modificaciones: busca tu reserva previa, precarga tu auto, sucursal y horario para que los cambies a gusto.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita reprogramar turnos sin obligar a cargar todos los datos personales desde cero.\n\n'
                '⚙️ FUNCIONAMIENTO: Prepara la edición de una reserva existente: la busca en `GET /user/reservations`, bloquea si es por hora y falta menos de la anticipación mínima, marca el stepper como completado, navega a inicio, abre y desplaza al formulario, cambia títulos y, tras 500 ms, precarga vehículo, sucursal, tipo y fechas (en hora restaura también el rango de la grilla y las horas) recalculando el precio.'
            ),
            "updateFormGroups": (
                '💡 LA IDEA: Es el seleccionador de campos según quieras reservar por hora, por día entero, por semana o por mes.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra únicamente los campos relevantes para la modalidad elegida, escondiendo lo que no aplica.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra solo el grupo de campos de la modalidad elegida (hora, día, semana, quincena, mes o rango libre), recalcula la fecha de fin de los períodos con la fecha cargada y actualiza el precio.'
            ),
            "marcarFaltaReserva": (
                '💡 LA IDEA: Es el llamado de atención en rojo que destaca un campo obligatorio que te olvidaste de completar y te avisa con un cartelito.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a corregir errores al instante sin tapar la pantalla ni abrir desplegables molestos.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca un campo obligatorio como inválido (`is-invalid` + `aria-invalid`) y muestra un toast con el motivo; se limpia solo en el próximo cambio del campo y deliberadamente no roba el foco para no abrir el select y tapar el aviso.'
            ),
            "createReservation": (
                '💡 LA IDEA: Es el cierre del trato: valida todas las condiciones, te muestra el resumen con el precio final y envía la reserva al servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura tu plaza de estacionamiento de forma confiable, actualizando tu lista de reservas y perfil al instante.\n\n'
                '⚙️ FUNCIONAMIENTO: Valida y envía el formulario: chequea presencia de campos y flota, arma `inicio`/`fin` según la modalidad validando anticipación mínima y horario de atención de la sucursal (no atravesar el cierre), consulta la disponibilidad (avisando si quedan ≤3 plazas), recalcula el descuento disponible, muestra el resumen con total original, descuento y total final para confirmar, y envía con la foto de cotización a `POST /user/reservations` o `PATCH /<id>` en edición. En éxito resetea el formulario, navega a reservas, recarga lista y perfil, dispara `reservation:created` y opcionalmente el tour; en error muestra el motivo. Siempre restaura el botón y cierra el grupo de consola.'
            ),
            "repeatReservation": (
                "💡 LA IDEA: Es el botón de 'Repetir reserva anterior' que te precarga tu auto habitual y tu sucursal favorita para que solo elijas la nueva fecha.\n\n"
                '🎯 POR QUE FUE GENERADA: Ahorra muchísimo tiempo a conductores recurrentes que estacionan siempre en el mismo lugar con el mismo auto.\n\n'
                '⚙️ FUNCIONAMIENTO: Repite una reserva: lleva a la sección inicio, abre el formulario si estaba cerrado, lo desplaza a la vista y, tras 500 ms, precarga vehículo, sucursal y tipo (ajustando los grupos de campos) avisando que solo falta elegir la nueva fecha.'
            ),
        },
    },
}
