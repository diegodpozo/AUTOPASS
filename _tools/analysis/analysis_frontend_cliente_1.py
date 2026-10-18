"""Explicaciones analizadas de frontend-cliente, parte 1 (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "static/js/modules/action-menu.js": {
        "proposito": 'Componente reutilizable del menú de acciones por elemento (patrón "⋮" / overflow) usado en las tarjetas del portal cliente. Gestiona apertura, cierre y posicionamiento como popover; para evitar que un ancestro con overflow:hidden o backdrop-filter lo recorte, el menú se porta a document.body al abrir y se devuelve a su wrapper al cerrar.',
        "simbolos": {
            "enableActionMenu": (
                "💡 LA IDEA: Es el botón de tres puntitos verticales ('⋮') de las tarjetas que despliega un menú flotante con opciones como editar o borrar.\n\n"
                '🎯 POR QUE FUE GENERADA: Ahorra espacio visual en las tarjetas de vehículos o reservas concentrando las acciones secundarias en un menú desplegable.\n\n'
                '⚙️ FUNCIONAMIENTO: Configura el menú de acciones sobre un contenedor con listeners delegados de click, teclado (Escape) y resize/scroll (cierra el popover). Es idempotente: marca el contenedor con data-action-menu-ready para no duplicar listeners aunque se re-rendericen las tarjetas, y guarda el callback onSelect en el propio contenedor para que cada re-render use el último. Al hacer click en un trigger abre/cierra su menú; al elegir un ítem invoca onSelect(action, itemEl, triggerEl).'
            ),
            "_position": (
                '💡 LA IDEA: Es el compás de dibujo que calcula las coordenadas exactas de la pantalla donde debe abrirse el menú flotante sin salirse de los bordes.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el menú quede cortado o escondido detrás de los marcos de la tarjeta o del navegador.\n\n'
                '⚙️ FUNCIONAMIENTO: Coloca el menú como popover debajo del trigger alineado a su borde derecho, con un margen de 6px. Se voltea arriba del trigger si no entra abajo y se ajusta horizontalmente a los bordes de la ventana; mide el menú oculto (visibility:hidden) antes de asignar las coordenadas finales.'
            ),
        },
    },
    "static/js/modules/chart-window.js": {
        "proposito": 'Clase reutilizable que implementa los gráficos de métricas con ventana temporal desplazable (seguir en vivo, selector de ventana en horas, ir a inicio/final y deslizador de posición del fin). La página solo instancia la clase, alimenta la serie con setSeries() y la clase se encarga del filtrado por ventana, el eje X lineal de tiempo real, los tooltips y el refresco del gráfico de Chart.js.',
        "simbolos": {
            "WindowedChart": (
                '💡 LA IDEA: Es la cinta transportadora de gráficos que te permite mirar las últimas horas de actividad o rebobinar en el tiempo con una barra deslizadora.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita amontonar cientos de puntos en un gráfico apretado, permitiendo deslizarse suavemente por el historial sin perder detalle.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase que envuelve un Chart.js de tipo línea con eje X lineal (marcas de tiempo). El constructor recibe un prefijo de ids de controles, el id del canvas, callbacks buildDatasets/tooltipTitle/tooltipLabel y propiedades extra de la escala Y; cablea los controles del DOM (_wire) y deja el gráfico en vivo por defecto. setSeries reemplaza y ordena la serie; liveSiguiente/irInicio/irFinal/updateSpan cambian entre modo vivo y ventana fija; _range calcula el rango permitido (con 5% de colchón al final), _visible filtra los puntos dentro de la ventana, _syncSlider ajusta el deslizador al rango y render reconstruye el gráfico completo (destruye el anterior y crea uno nuevo con tema THEME, o un gráfico vacío si no hay puntos). destroy limpia el gráfico y la serie.'
            ),
        },
    },
    "static/js/modules/drag-sort.js": {
        "proposito": 'Helper reutilizable de reordenamiento por arrastre (HTML5 drag & drop) para listas o grillas de tarjetas del portal cliente. Se configura con selectores de ítem y de asa (opcional) y notifica con onReorder cuando el usuario suelta; incluye auto-scroll al arrastrar cerca del borde de un contenedor scrolleable.',
        "simbolos": {
            "enableDragSort": (
                '💡 LA IDEA: Es la mano virtual que te permite agarrar una tarjeta con el mouse o dedo y arrastrarla para cambiar el orden de la lista.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita ordenar vehículos o cámaras a gusto del usuario con un gesto natural e intuitivo.\n\n'
                "⚙️ FUNCIONAMIENTO: Habilita el reordenamiento por arrastre de los hijos de un contenedor. Es idempotente (marca data-drag-sort-ready) porque los listeners se delegan en el contenedor. En dragstart valida que el arranque sea desde el asa (si se definió handleSelector) y que no sea desde un elemento interactivo (botones, enlaces, inputs, etc.); marca el ítem con la clase 'dragging' e inicia el auto-scroll. En dragover recalcula la posición de inserción según el puntero; en dragend detiene el auto-scroll, quita la clase y llama a onReorder con los nodos ya reordenados en el DOM."
            ),
            "_findScroller": (
                '💡 LA IDEA: Es el buscador del marco deslizable para saber qué caja de la pantalla tiene barra de desplazamiento activa.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que la pantalla suba o baje sola automáticamente mientras estás arrastrando una tarjeta hacia los bordes.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca desde el elemento hacia arriba el ancestro con overflow-y auto/scroll/overlay que tenga scroll real (scrollHeight > clientHeight); si no hay ninguno devuelve el elemento scrolleable del documento como fallback.'
            ),
            "_findInsertionPoint": (
                '💡 LA IDEA: Es el detector del hueco exacto entre dos tarjetas donde debe soltarse el elemento que estás moviendo.\n\n'
                '🎯 POR QUE FUE GENERADA: Logra que las tarjetas se reacomoden prolijamente en tiempo real mientras arrastrás, sin superponerse ni vibrar.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el nodo antes del cual insertar el ítem arrastrado, o null para insertarlo al final. Recorre los candidatos en orden de lectura (fila por fila) en vez de usar distancia al centro: basta con que el puntero esté debajo del borde inferior de una fila o a la derecha del centro horizontal de la tarjeta, lo que evita que las tarjetas se superpongan al reordenar grillas.'
            ),
        },
    },
    "static/js/modules/list-pagination.js": {
        "proposito": 'Helper DRY de listas que acumulan muchos ítems en el portal cliente y en el dashboard admin. Expone dos estrategias: renderCappedList (muestra las primeras N con toggle "Ver todas / Ver menos") y renderPaginatedList (barra de paginación anterior/siguiente); el estado de expansión y de página se guarda por id de contenedor, y los botones usan callbacks globales de window para poder invocarse desde onclick generados con HTML.',
        "simbolos": {
            "renderCappedList": (
                "💡 LA IDEA: Es el fuelle de 'Ver más / Ver menos': muestra solo las primeras 6 filas de una lista y te da un botón para desplegar el resto.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita pantallas interminables que abruman al usuario, manteniendo el diseño compacto y ordenado.\n\n'
                '⚙️ FUNCIONAMIENTO: Inyecta en el contenedor hasta pageSize ítems (default 6) con un botón toggle "Ver todas (M) / Ver menos" solo si hay más que la página. Genera ids automáticos para contenedores sin id, respeta el estado de expansión por contenedor (capState), soporta items en div o en filas de tabla (tag \'tr\' con colspan) y un estado vacío configurable (emptyHtml). Registra en capToggleIds la función que alterna la expansión y dispara el callback onToggle del caller.'
            ),
            "resetCappedState": (
                '💡 LA IDEA: Es el cierre del acordeón que vuelve a encoger la lista a su tamaño inicial cuando cambiás de filtro o búsqueda.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene que una lista quede expandida con espacios vacíos tras aplicar un filtro con pocos resultados.\n\n'
                '⚙️ FUNCIONAMIENTO: Colapsa la lista del contenedor dado (fuerza capState[id] = false), por ejemplo al cambiar de filtro o recargar datos.'
            ),
            "renderPaginatedList": (
                "💡 LA IDEA: Es el paginador clásico de libros con botones de 'Anterior', 'Siguiente' y número de página.\n\n"
                '🎯 POR QUE FUE GENERADA: Organiza tablas con cientos de registros (como cobros o estadías) en páginas de 10 elementos fáciles de recorrer.\n\n'
                '⚙️ FUNCIONAMIENTO: Alternativa paginada: muestra pageSize ítems (default 10) de la página actual, recortándola si quedó fuera de rango. La barra de navegación puede ir en un contenedor aparte (navContainer como elemento o id) o inyectarse junto a los items, como fila de tabla o como div; si es la última página y tiene menos items que pageSize, rellena con config.fillRow para mantener altura estable. Registra en pageRenders la función de re-render de esa página.'
            ),
            "_resolveNav": (
                "💡 LA IDEA: Es el buscador del lugar donde debe colocarse la botonera de 'Anterior / Siguiente' en el diseño.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite reutilizar el mismo sistema de paginación tanto al pie de tablas complejas como dentro de listas simples.\n\n'
                '⚙️ FUNCIONAMIENTO: Resuelve el elemento destino de la barra de paginación: si config.navContainer es un id (string) busca el elemento por document.getElementById, si es un elemento lo devuelve tal cual, y si no está definido usa el mismo contenedor de los items.'
            ),
            "_buildPager": (
                "💡 LA IDEA: Es la imprenta que dibuja el texto de 'Página 2 de 10' y los botones de avance o retroceso.\n\n"
                '🎯 POR QUE FUE GENERADA: Estandariza la botonera de paginado para que luzca idéntica y con el mismo estilo dorado en todo el sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera el HTML del pager: botón de página anterior (deshabilitado en la primera), texto "Página X de Y" y botón de página siguiente (deshabilitado en la última); ambos llaman a window.__pageGoto con el id de la lista y la página destino.'
            ),
            "resetPaginatedState": (
                '💡 LA IDEA: Es el salto automático a la primera página cada vez que el usuario aplica un nuevo criterio de búsqueda.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el usuario quede varado en una página inexistente (por ejemplo, página 5 de una búsqueda que solo tiene 1 página).\n\n'
                '⚙️ FUNCIONAMIENTO: Vuelve a la página 1 el estado del contenedor dado (pageState[id] = 1).'
            ),
        },
    },
    "static/js/modules/notifications-actions.js": {
        "proposito": 'Submódulo del sistema de notificaciones del portal cliente con las operaciones mutables sobre notificaciones: marcar como leída, marcar todas, eliminar, borrar las leídas y confirmar un recordatorio de pago. Cada acción actualiza el estado local (notifState.cachedNotifications), refresca la lista, los botones de acción y el badge, y hace su llamada a la API correspondiente.',
        "simbolos": {
            "markNotifRead": (
                '💡 LA IDEA: Es el gesto de apagar el punto brillante de un mensaje apenas el usuario le presta atención.\n\n'
                '🎯 POR QUE FUE GENERADA: Actualiza la pantalla al instante sin esperar la respuesta de la red (respuesta optimista) y avisa en paralelo a la base de datos.\n\n'
                "⚙️ FUNCIONAMIENTO: Marca una notificación como leída de forma optimista: quita la clase 'notif-unread' y el punto del ítem en el DOM, pone leido=true en la caché local, actualiza botones y badge, y luego envía PATCH a /user/profile/notifications/{id}/read. Si el elemento no estaba sin leer, no hace nada."
            ),
            "markAllNotifRead": (
                "💡 LA IDEA: Es el botón de 'Limpiar novedades' que apaga todos los puntos brillantes de las notificaciones juntas.\n\n"
                '🎯 POR QUE FUE GENERADA: Ahorra tiempo al conductor permitiéndole despejar su bandeja de entrada con un único clic.\n\n'
                '⚙️ FUNCIONAMIENTO: POST a /user/profile/notifications/read-all; si falla muestra un toast de error, y si sale bien marca todas las notificaciones cacheadas como leídas, re-renderiza la lista, actualiza botones y badge y muestra toast de éxito.'
            ),
            "deleteNotif": (
                '💡 LA IDEA: Es el tachado suave que desliza una notificación hacia afuera de la pantalla antes de eliminarla del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga una animación elegante al descartar mensajes y actualiza el contador de la campana en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina la notificación con DELETE al endpoint de la notificación. Detiene la propagación del click, y si el ítem existe en el DOM lo anima saliendo (translateX + opacidad 0) durante 300 ms antes de re-renderizar; si no, re-renderiza directo. Filtra la caché local y actualiza botones y badge; muestra toast de éxito o de error según la respuesta.'
            ),
            "clearReadNotifs": (
                '💡 LA IDEA: Es la limpieza a fondo que tira a la papelera todos los avisos viejos que ya fueron leídos.\n\n'
                '🎯 POR QUE FUE GENERADA: Despeja la vista dejando únicamente las notificaciones importantes que aún requieren atención.\n\n'
                '⚙️ FUNCIONAMIENTO: Pide confirmación con showConfirm y luego envía DELETE a /user/profile/notifications/clear-read. Filtra la caché local dejando solo las no leídas, re-renderiza la lista, actualiza botones y badge y muestra toast de éxito; si el usuario cancela o la API falla, no hace nada más (toast de error en ese caso).'
            ),
            "confirmReminder": (
                "💡 LA IDEA: Es el botón de 'Confirmo asistencia' que aparece en la notificación de recordatorio antes del turno.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite asegurar la reserva directamente desde el mensaje sin tener que navegar por todo el menú de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: POST a /user/reservations/{reservaId}/confirm-reminder para confirmar un recordatorio de pago. Al confirmar con éxito quita la clase \'notif-unread\' del ítem, elimina sus botones de acción (.notif-actions), actualiza el badge y muestra toast "Reserva confirmada". Si falla, muestra toast de error.'
            ),
        },
    },
    "static/js/modules/notifications-badge.js": {
        "proposito": 'Submódulo del sistema de notificaciones que consulta y refleja el conteo de notificaciones sin leer en la burbuja del header (campana) y en la del sidebar de USUARIO/CLIENTE, y avisa con un toast cuando aparecen notificaciones nuevas.',
        "simbolos": {
            "fetchUnreadCount": (
                '💡 LA IDEA: Es la consulta rápida al servidor para saber cuántos avisos sin leer tiene el cliente en este momento.\n\n'
                '🎯 POR QUE FUE GENERADA: Pide únicamente el número para no gastar datos móviles descargando los textos completos.\n\n'
                '⚙️ FUNCIONAMIENTO: Consulta GET /user/profile/notifications/unread y devuelve el count de no leídas; si la llamada falla devuelve 0.'
            ),
            "updateNotifBadge": (
                '💡 LA IDEA: Es el número que titila sobre la campana de la barra superior y avisa con un cartelito si llegó una novedad nueva.\n\n'
                '🎯 POR QUE FUE GENERADA: Llama la atención del usuario de inmediato ante sucesos relevantes (como la apertura de barrera o un cobro debitado).\n\n'
                '⚙️ FUNCIONAMIENTO: Obtiene el conteo sin leer y lo refleja en los badges #notif-badge-sidebar-user y #notif-badge-header: los muestra con el número (o \'99+\' si supera 99) y una clase \'pulse\' cuando hay pendientes, o los oculta si es cero. Usa notifState.isUpdatingBadge como candado para evitar peticiones concurrentes (se libera en finally). Si el conteo subió respecto al anterior (lastNotifCount, inicializado en -1 por startNotifPolling para no avisar al arrancar) muestra un toast informativo "Tenés N notificaciones sin leer".'
            ),
        },
    },
    "static/js/modules/notifications-dropdown.js": {
        "proposito": 'Submódulo del sistema de notificaciones con el desplegable del timbre del header: al abrirlo carga y muestra las 5 notificaciones más recientes con su icono, categoría, acciones inline y tiempo relativo, y se cierra automáticamente al hacer click fuera del timbre.',
        "simbolos": {
            "toggleNotifDropdown": (
                '💡 LA IDEA: Es la persianita que se despliega debajo de la campana del header al hacer clic para ver los últimos mensajes.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite revisar las últimas 5 novedades en un instante sin abandonar la pantalla en la que estás trabajando.\n\n'
                '⚙️ FUNCIONAMIENTO: Alterna la visibilidad del dropdown #notif-dropdown: si estaba visible lo cierra; si no, lo marca visible y carga las últimas 5 notificaciones con loadNotifDropdown. Detiene la propagación del click para que el listener global de cierre no lo cierre inmediatamente.'
            ),
            "closeNotifDropdown": (
                '💡 LA IDEA: Es el repliegue de la ventanita de mensajes cuando hacés clic en cualquier otra parte de la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpia la interfaz cerrando el menú automáticamente sin estorbar la lectura del contenido principal.\n\n'
                "⚙️ FUNCIONAMIENTO: Quita la clase 'visible' del dropdown #notif-dropdown si existe, cerrándolo sin tocar su contenido."
            ),
            "loadNotifDropdown": (
                '💡 LA IDEA: Es el repartidor que busca las 5 notificaciones más recientes y las acomoda prolijamente dentro de la persianita.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra las novedades más urgentes con sus íconos de color y botones de acción rápida.\n\n'
                "⚙️ FUNCIONAMIENTO: Carga asíncronamente las últimas 5 notificaciones (GET con limit=5) y las pinta en #notif-dropdown-body con un spinner mientras espera. Cada ítem usa las funciones de notifications-format (icono, clase de categoría, acciones y tiempo relativo); si es no leída agrega la clase 'notif-unread' y un onclick que llama a markNotifRead. Si la API falla o no hay notificaciones muestra un mensaje acorde."
            ),
        },
    },
    "static/js/modules/notifications-format.js": {
        "proposito": 'Submódulo del sistema de notificaciones con la representación visual de cada notificación: mapa de iconos FontAwesome por tipo, clases CSS de categoría (success, warning, danger, support, gold), botones de acción inline según el tipo de evento y tiempo relativo ("Hace 5 min", "Ayer"). Es la fuente única de verdad de formato para el dropdown y para el panel de notificaciones.',
        "simbolos": {
            "getNotifIcon": (
                '💡 LA IDEA: Es el diseñador gráfico que le asigna un ícono representativo a cada aviso (un ticket para cobros, un auto para ingresos, un escudo para seguridad).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite identificar de qué se trata la notificación en una fracción de segundo gracias al impacto visual del dibujo.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la clase de icono FontAwesome correspondiente al tipo de notificación (por ejemplo RESERVATION_CONFIRMED → fa-check-circle, STAY_PAID → fa-receipt) mediante un switch sobre todos los tipos soportados; para tipos desconocidos devuelve fa-bell.'
            ),
            "getNotifCategoryClass": (
                '💡 LA IDEA: Es la paleta de colores semántica: verde para pagos exitosos, amarillo para advertencias, rojo para cancelaciones y dorado para puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Guía la atención del usuario coloreando los mensajes según su nivel de urgencia o importancia.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la clase CSS de color de categoría (notif-cat-success, notif-cat-warning, notif-cat-danger, notif-cat-support, notif-cat-gold o notif-cat-default) agrupando los tipos de notificación según su semántica: reservas/pagos positivos, alertas de seguridad, cancelaciones, soporte y eventos de puntos/perfil.'
            ),
            "getNotifActions": (
                "💡 LA IDEA: Es el sastre que cose botones interactivos al pie de cada mensaje (como 'Pagar ahora', 'Ver mapa' o 'Revisar reserva').\n\n"
                '🎯 POR QUE FUE GENERADA: Transforma un mensaje estático en un atajo directo para que el conductor resuelva su trámite en un solo paso.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el HTML de los botones de acción inline de una notificación según su tipo, invocando vía onclick a las funciones de navegación/acciones del portal (confirmReminder, payFromNotif, goToReservation, goToBalance, goToVoucher, etc.). Maneja casos como recordatorios de pago (CONFIRMAR/PAGAR), reservas canceladas con reembolso (detecta "saldo"/"reembols" en el mensaje), canjes de voucher (extrae el id del mensaje con regex) y eventos de vehículos, soporte, seguridad y perfil. Devuelve null si el tipo no tiene acciones.'
            ),
            "getTimeAgo": (
                "💡 LA IDEA: Es el reloj humano que escribe 'Hace 5 min', 'Ayer' o 'Hace 2 horas' en lugar de mostrar números de fecha difíciles de interpretar.\n\n"
                '🎯 POR QUE FUE GENERADA: Facilita saber de inmediato qué tan reciente es un aviso teniendo en cuenta además el tiempo virtual de simulación.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte una fecha ISO en texto relativo ("Ahora", "Hace N min", "Hace Nh", "Ayer", "Hace N días") usando getVirtualNow de virtual-time.js como referencia de "ahora" (soporta el tiempo virtual de pruebas). Devuelve cadena vacía si la fecha falta o no es válida.'
            ),
        },
    },
    "static/js/modules/notifications-nav.js": {
        "proposito": 'Submódulo del sistema de notificaciones con las funciones de navegación que responden a los botones de las notificaciones: llevan al usuario a la sección destino (reservas, perfil, puntos, vehículos, saldo, voucher, etc.), cierran el dropdown, cambian de sección con window.showSection y hacen scroll con resaltado dorado (box-shadow) hacia el elemento relevante.',
        "simbolos": {
            "payFromNotif": (
                '💡 LA IDEA: Es el salto directo al pago: te lleva a la pantalla de reservas, ilumina tu reserva con un brillo dorado y abre la pasarela de pago.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el usuario tenga que buscar manualmente entre todas sus reservas cuál es la que debe pagar.\n\n'
                "⚙️ FUNCIONAMIENTO: Cambia a la sección 'reservas', busca la tarjeta de la reserva (data-reserva-id), la scrollea al centro y la resalta con un borde dorado durante 2 segundos; a los 600 ms (dejando tiempo a que se renderice la lista) importa dinámicamente payReservation de reservas.js y abre el pago de esa reserva."
            ),
            "goToReservation": (
                '💡 LA IDEA: Es el teletransporte a una reserva: abre la pestaña de reservas y enfoca la tarjeta exacta del turno seleccionado.\n\n'
                '🎯 POR QUE FUE GENERADA: Conecta los avisos de llegada o cancelación directamente con la reserva correspondiente en pantalla.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el dropdown, cambia a la sección 'reservas' y, tras 500 ms, scrollea al centro la tarjeta de la reserva indicada (data-reserva-id) resaltándola con sombra dorada 2 segundos."
            ),
            "goToChangePassword": (
                '💡 LA IDEA: Es el atajo de seguridad que te lleva directo al formulario de cambio de clave ante una alerta de acceso sospechoso.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la cuenta permitiendo reaccionar en segundos ante cualquier aviso de seguridad.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el dropdown, cambia a la sección 'perfil' y tras 400 ms busca el campo o botón de cambio de contraseña (input #current-password, botón, disparador de modal o formulario de seguridad), lo scrollea al centro y lo enfoca."
            ),
            "goToBalance": (
                '💡 LA IDEA: Es el acceso directo a la billetera virtual: abre de inmediato la ventana para cargar dinero en la cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita fondear la cuenta cuando recibís un aviso de saldo insuficiente para estacionar.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el dropdown y abre el modal de recarga con window.openRechargeModal si existe; si no, cambia a la sección 'perfil'."
            ),
            "goToPoints": (
                '💡 LA IDEA: Es el pasaje al club de fidelización para mirar el catálogo de recompensas y canjear tus puntos acumulados.\n\n'
                '🎯 POR QUE FUE GENERADA: Lleva al conductor directamente a disfrutar de sus beneficios tras recibir una notificación de puntos ganados.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el dropdown, cambia a la sección 'puntos' y tras 400 ms scrollea al centro el contenedor del catálogo de puntos (o la tarjeta de fidelización / la sección como fallback)."
            ),
            "goToVoucher": (
                '💡 LA IDEA: Es el atajo que te abre el cupón con su código QR en pantalla listo para mostrar en el comercio o garita.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita demoras en la caja abriendo el cupón canjeado en un solo toque.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el dropdown, cambia a la sección 'puntos' y tras 450 ms scrollea al contenedor de vouchers e intenta abrir el voucher: si el id es numérico llama a showCanjeTicketById (importado dinámicamente de profile.js); si no, consulta /user/redemption-tickets y abre el que coincida por código/id o, en su defecto, el más reciente. Los errores se registran por console.error."
            ),
            "goToNewReservation": (
                '💡 LA IDEA: Es el salto directo al formulario de inicio para reservar un nuevo lugar de estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Agiliza volver a reservar cuando recibís una sugerencia o aviso de una estadía finalizada.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el dropdown, cambia a la sección 'inicio' y tras 400 ms scrollea al centro el contenedor del formulario de reserva (o la sección de inicio como fallback), llevando al usuario a crear una nueva reserva."
            ),
            "goToReservationsList": (
                '💡 LA IDEA: Es el camino rápido hacia la cartelera de todas tus reservas pasadas y futuras.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite consultar el estado general de tus turnos desde cualquier aviso de la campana.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el dropdown, cambia a la sección 'reservas' y tras 400 ms scrollea al inicio (#reservas-list o la sección) el listado de reservas."
            ),
            "goToVehicles": (
                '💡 LA IDEA: Es el acceso directo a tu garaje digital para agregar una nueva patente o cambiar tu vehículo favorito.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita resolver avisos relacionados con vehículos no reconocidos o dados de alta.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el dropdown, cambia a la sección 'vehiculos' y tras 400 ms scrollea al centro la grilla de vehículos (o el formulario de alta / la sección como fallback)."
            ),
            "goToProfile": (
                '💡 LA IDEA: Es el puente hacia tu ficha de cuenta donde figuran tus datos de contacto y configuración personal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite acceder rápidamente a revisar tus datos tras un aviso de modificación de perfil.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el dropdown, cambia a la sección 'perfil' y tras 400 ms scrollea al centro la tarjeta principal del perfil (.account-hub-card o la sección como fallback)."
            ),
            "goToStays": (
                '💡 LA IDEA: Es el atajo hacia la tarjeta de tu auto actualmente estacionado para ver el taxímetro de tiempo y deuda en vivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda al conductor a verificar el tiempo de su estadía en curso con un solo clic.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el dropdown, cambia a la sección 'perfil' y tras 400 ms scrollea al contenedor de estadías activas (#container-active-stays, con la tarjeta del perfil o la sección como fallback)."
            ),
        },
    },
    "static/js/modules/notifications-polling.js": {
        "proposito": 'Submódulo del sistema de notificaciones que implementa el refresco periódico del badge de no leídas: al iniciar hace una consulta inmediata y luego repite updateNotifBadge cada 30 segundos, guardando el id del intervalo en notifState para que solo exista uno.',
        "simbolos": {
            "startNotifPolling": (
                '💡 LA IDEA: Es el centinela silencioso que cada 30 segundos le pregunta al servidor si tenés alguna novedad o mensaje nuevo.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene actualizado el indicador de la campanita mientras navegás por la aplicación sin necesidad de recargar la página.\n\n'
                '⚙️ FUNCIONAMIENTO: Arranca el polling del badge de forma idempotente: si ya hay un intervalo activo no hace nada. Inicializa lastNotifCount en -1 para que la primera carga no dispare el toast de "notificaciones nuevas", ejecuta updateNotifBadge de inmediato y agenda updateNotifBadge cada 30000 ms en notifState.pollInterval.'
            ),
        },
    },
    "static/js/modules/notifications-render.js": {
        "proposito": 'Submódulo del sistema de notificaciones con el renderizado del panel completo de notificaciones del portal cliente: carga la lista desde la API, aplica filtros por categoría (todas, sin leer, reservas, finanzas, soporte, seguridad), genera el HTML de cada ítem y habilita/deshabilita los botones de acción masiva según haya leídas o no leídas.',
        "simbolos": {
            "loadNotifications": (
                '💡 LA IDEA: Es la carga del buzón completo de notificaciones con su ruedita de espera mientras llegan los datos del servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Descarga los mensajes de la cuenta y los prepara para mostrarlos clasificados en la pantalla de notificaciones.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga hasta 200 notificaciones (GET /user/profile/notifications?limit=200) en el contenedor #notifications-container con spinner previo, guarda el resultado en notifState.cachedNotifications, resetea la expansión de la lista, actualiza los botones de acción y renderiza. Si la API falla muestra un estado vacío con mensaje de error.'
            ),
            "updateNotifActionButtonsState": (
                "💡 LA IDEA: Es el evaluador de botones masivos que prende o apaga 'Marcar todo leído' o 'Borrar leídas' según haya mensajes para procesar.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita que el usuario haga clic en botones que no tendrían ningún efecto porque la bandeja ya está limpia.\n\n'
                '⚙️ FUNCIONAMIENTO: Habilita o deshabilita los botones de acción masiva del panel: #btn-mark-all-read se deshabilita si no hay notificaciones sin leer y #btn-clear-read-notifs se deshabilita si no hay leídas; ambos se fuerzan visibles (display inline-flex).'
            ),
            "renderNotificationList": (
                '💡 LA IDEA: Es el maquetador visual que dibuja cada tarjeta de notificación con sus botones, fecha y estado de lectura.\n\n'
                '🎯 POR QUE FUE GENERADA: Presenta los mensajes con un diseño atractivo, prolijo y con la opción de desplegar más elementos si la lista es larga.\n\n'
                '⚙️ FUNCIONAMIENTO: Filtra la caché con el filtro actual (notifState.currentFilter), construye el HTML de cada notificación (icono, categoría, acciones inline, tiempo relativo, punto de no leída y botón de eliminar que llama a deleteNotif) y lo pinta con renderCappedList (pageSize 8, wrapper notif-list, toggle "Ver todas las notificaciones"). El mensaje del estado vacío varía según el filtro activo. Los onclick generados llaman a funciones globales (markNotifRead, deleteNotif).'
            ),
            "filterNotificationsArray": (
                '💡 LA IDEA: Es el clasificador que separa las notificaciones en grupos: solo reservas, solo pagos, soporte o seguridad.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cliente filtrar rápidamente los avisos según el tema que necesita revisar en ese momento.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve una nueva lista con las notificaciones que cumplen el filtro: 'UNREAD' (sin leer), 'RESERVATION' (todos los tipos de reserva y recordatorios), 'FINANCE' (saldo, canjes, puntos, pagos y cancelaciones de estadía), 'SUPPORT' (tickets de soporte), 'SECURITY' (login nuevo, contraseñas, perfil, rol, bloqueo y eventos de vehículos) o cualquier otro valor (devuelve la lista completa)."
            ),
            "filterNotifs": (
                '💡 LA IDEA: Es el selector de solapa de filtros que activa la pastilla elegida y redibuja la lista al instante.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee una navegación ágil y sin demoras entre los diferentes tipos de mensajes recibidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica un filtro del panel: guarda el tipo en notifState.currentFilter, marca como activa la chip correspondiente (.notif-chip.active), resetea la expansión de la lista y la re-renderiza con el nuevo filtro.'
            ),
        },
    },
}
