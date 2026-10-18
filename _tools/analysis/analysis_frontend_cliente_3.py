"""Explicaciones analizadas de frontend-cliente (parte 3): análisis del código real."""

ANALISIS: dict[str, dict] = {
    "static/js/modules/reservas-list.js": {
        "proposito": 'Listado e historial de reservas del cliente: separa las reservas activas (pendientes o en curso) de las finalizadas, pinta las tarjetas con barra de progreso de la estadía y pagina el historial con filtros por fecha.',
        "simbolos": {
            "getHistoryData": (
                '💡 LA IDEA: Es el baúl de reservas finalizadas guardado en la memoria de la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que otros módulos (como el botón de repetir reserva) lean rápidamente los datos del viaje anterior sin volver a pedirlos al servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el array en memoria `historyData` (reservas que ya no están Pendientes ni Activas) cargado por `loadReservations`; otros módulos lo usan, por ejemplo, para repetir una reserva del historial.'
            ),
            "loadReservations": (
                '💡 LA IDEA: Es el organizador de turnos: separa las reservas activas (las que estás usando o por usar) del historial de viajes concluidos.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra en primer plano tu auto en el predio o tu próxima llegada, manteniendo las estadísticas de tu cuenta al día.\n\n'
                '⚙️ FUNCIONAMIENTO: Pide GET /user/reservations y divide el resultado en activas (estado Pendiente o Activa) e historial. Con el tiempo virtual calcula cuáles están en curso y cuáles futuras, actualiza los contadores de estadísticas de la página, muestra la reserva en curso como tarjeta destacada, pinta el resto en la grilla de activas (con estado vacío si no hay) y refresca el historial con los filtros vigentes.'
            ),
            "applyHistoryFilters": (
                '💡 LA IDEA: Es el filtro por fechas del historial de reservas para buscar viajes realizados en un período determinado.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita revisar cuánto gastaste o qué días estacionaste en un rango de fechas específico.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee los campos de fecha `history-filter-from` y `history-filter-to`, filtra `historyData` por `fecha_inicio` dentro del rango seleccionado (día completo de inicio) y vuelve a renderizar el historial con el resultado.'
            ),
            "renderReservaCard": (
                '💡 LA IDEA: Es la tarjeta interactiva de reserva: muestra la patente, su estado (en predio, pagada), una barra de progreso del tiempo y sus botones de acción.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda al conductor un control total de su reserva con accesos rápidos para pagar, editar, ver el pase QR o cancelar.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el HTML de una tarjeta de reserva: calcula el porcentaje de progreso entre fecha_inicio y fecha_fin usando el tiempo virtual, y arma encabezado con patente, badges (EN CURSO, EN PREDIO, estado de pago), importe neto (monto_total menos monto_reembolsado), barra de progreso, datos de la estadía y botones de pase QR, pago con saldo o Mercado Pago, edición y cancelación, deshabilitados según el estado de la reserva.'
            ),
            "renderHistory": (
                '💡 LA IDEA: Es la planilla de viajes pasados paginada de a 5 filas con iconos, fechas e importes netos.\n\n'
                '🎯 POR QUE FUE GENERADA: Presenta el historial de manera compacta y ordenada, ofreciendo un botón para repetir cualquier reserva con un solo clic.\n\n'
                '⚙️ FUNCIONAMIENTO: Pagina el historial en bloques de 5 elementos y pinta cada fila (icono según estado, sucursal, patente, fecha, importe neto, píldora de estado y botón de repetir reserva) dentro de `reservation-list-history`; además actualiza el texto de página y habilita o deshabilita los botones anterior/siguiente.'
            ),
            "historialPage": (
                '💡 LA IDEA: Es el cambio de página del historial para avanzar a los viajes más antiguos o regresar a los recientes.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite recorrer años de historial de estacionamiento de forma ágil y liviana.\n\n'
                '⚙️ FUNCIONAMIENTO: Avanza o retrocede la página del historial según la dirección indicada (+1 o -1) y repinta aplicando los filtros de fecha vigentes.'
            ),
            "resetHistoryFilters": (
                '💡 LA IDEA: Es la limpieza de los filtros de fecha para volver a ver todo el historial completo de viajes.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite deshacer la búsqueda con un solo toque y regresar a la vista panorámica de reservas.\n\n'
                '⚙️ FUNCIONAMIENTO: Vacía los dos inputs de filtro de fecha del historial y vuelve a renderizar la lista completa sin filtros.'
            ),
        },
    },
    "static/js/modules/reservas-pass.js": {
        "proposito": 'Comprobante / Pase Digital de la reserva: arma el modal del ticket (con o sin QR) según el estado de pago, calcula los datos financieros y ofrece los botones de pago directo cuando la reserva está pendiente.',
        "simbolos": {
            "resolveBranchAddress": (
                '💡 LA IDEA: Es el cartero de la reserva: busca la dirección postal exacta y el horario de atención del estacionamiento para ponerlos en el ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el conductor tenga la dirección física y sepa si la sucursal es 24 horas antes de salir.\n\n'
                "⚙️ FUNCIONAMIENTO: Obtiene la dirección de la sucursal para el comprobante: si `sucursalInfo` ya es una dirección real la devuelve tal cual; si es un placeholder, consulta GET /parking/branches (cacheado en `_branchesListCache`), busca la sucursal por nombre (igualdad o coincidencia parcial) y arma 'dirección. horario' (o 'Abierto 24hs'); si nada coincide devuelve 'Dirección no disponible'."
            ),
            "duracionHoras": (
                "💡 LA IDEA: Es el reloj que calcula la duración total de la reserva y la escribe de forma humana (como '2h 30min' o '45 min').\n\n"
                '🎯 POR QUE FUE GENERADA: Facilita leer el tiempo contratado de un vistazo rápido sin hacer cuentas mentales con las horas de inicio y fin.\n\n'
                "⚙️ FUNCIONAMIENTO: Calcula la diferencia en horas entre dos fechas y la formatea de forma legible: 'X min' si es menos de una hora, 'Xh' si es exacto, 'Xh 30min' para media hora o 'Xh Ymin' en general."
            ),
            "formatCurrency": (
                "💡 LA IDEA: Es el formateador de dinero que redondea el monto y le estampa el signo pesos y los puntos de miles (ej: '$1.500').\n\n"
                '🎯 POR QUE FUE GENERADA: Presenta los importes con el formato bancario tradicional argentino.\n\n'
                "⚙️ FUNCIONAMIENTO: Redondea el importe y lo devuelve como texto monetario '$n' con separador de miles, reutilizando `formatNum`."
            ),
            "metodoPagoLabel": (
                "💡 LA IDEA: Es el cartel que traduce códigos técnicos al nombre comercial del medio de pago (como 'Billetera AUTOPASS' o 'Mercado Pago').\n\n"
                '🎯 POR QUE FUE GENERADA: Brinda total claridad al cliente en su comprobante digital sobre cómo abonó el servicio.\n\n'
                "⚙️ FUNCIONAMIENTO: Traduce el código de método de pago de la reserva a un rótulo legible (SALDO/DIGITAL/WALLET → 'Billetera AUTOPASS', CAJA → 'Efectivo en caja', MERCADOPAGO, EFECTIVO, TRANSFERENCIA, TARJETA, etc.); devuelve '---' si no hay método y respeta la clave original si no está en el mapa."
            ),
            "estadoBadgeClass": (
                '💡 LA IDEA: Es la cucarda de color del ticket: verde para pagado, amarillo para pendiente y rojo para cancelado.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario y al personal de garita verificar al instante el estado del comprobante por su color.\n\n'
                "⚙️ FUNCIONAMIENTO: Mapea el estado de la reserva o del pago a la clase CSS del badge del ticket (Pagado, Pendiente, Cancelada/Fallido → cancelado, Reembolsado); usa 'ticket-badge-pendiente' como valor por defecto."
            ),
            "tipoEstadiaLabel": (
                "💡 LA IDEA: Es la etiqueta legible de la modalidad contratada ('Por Hora', 'Por Día', 'Por Mes').\n\n"
                '🎯 POR QUE FUE GENERADA: Reemplaza identificadores internos por descripciones profesionales en el comprobante.\n\n'
                "⚙️ FUNCIONAMIENTO: Traduce el tipo de estadía crudo (hora, dia, semana, quincena, mes) a la etiqueta visible 'Por Hora', 'Por Día', etc., con el propio valor o '---' de respaldo."
            ),
            "showDigitalPass": (
                '💡 LA IDEA: Es el comprobante digital completo con código QR gigante, datos del vehículo, horario e instrucciones de acceso.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee un pase de ingreso oficial para mostrar en el lector de la barrera o al empleado de garita.\n\n'
                "⚙️ FUNCIONAMIENTO: Carga la reserva por id desde GET /user/reservations y arma el modal del pase: aplica la clase del ticket según estado (pagado/cancelado/impago), pinta el banner de estado, genera el QR con la librería QRCode (texto 'AUTOPASS|ID:<id>|PLATE:<patente>') solo si no está cancelado, completa todos los campos (patente, vehículo, sucursal y dirección resuelta, fechas, tipo y duración), la sección financiera (total neto, tarifa por hora derivada, método de pago y puntos = floor(total/100)), las instrucciones de ingreso y la visibilidad de los botones de pago y compartir; luego abre `modal-pase-digital` y emite el evento 'digitalpass:open'."
            ),
            "closeDigitalPass": (
                '💡 LA IDEA: Es el repliegue del modal del pase digital para regresar al listado de reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Cierra el comprobante de forma limpia y libera la memoria de la pantalla.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra el modal del pase digital si existe, limpia la reserva activa (`_currentPassResId`) y emite el evento 'digitalpass:closed'."
            ),
            "shareTicket": (
                '💡 LA IDEA: Es el botón para guardar el pase digital como foto en el teléfono o compartirlo por WhatsApp.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el conductor tenga su comprobante y código QR a mano incluso si se queda sin señal de internet en el subsuelo del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Captura el ticket como imagen con html2canvas (ocultando previamente los elementos `.no-print` y restaurándolos al final): si el navegador lo soporta comparte el PNG con `navigator.share`, si no lo descarga; muestra toast de error si falla la generación.'
            ),
            "payReservationFromPass": (
                "💡 LA IDEA: Es el botón de 'Pagar con Saldo' dentro del mismo pase digital cuando la reserva aún está impaga.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite abonar la reserva directamente desde el ticket para que se genere el código QR habilitante sin salir de la pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Paga la reserva que está abierta en el pase con saldo de billetera: pide confirmación, hace POST /user/reservations/{id}/pay y, si sale bien, avisa con toast y vuelve a abrir el pase actualizado; si no, muestra el detalle del error.'
            ),
            "payReservationMpFromPass": (
                "💡 LA IDEA: Es el botón de 'Pagar con Mercado Pago' dentro del pase digital.\n\n"
                '🎯 POR QUE FUE GENERADA: Habilita abonar con tarjetas de crédito o débito de inmediato y desbloquear el pase de entrada.\n\n'
                "⚙️ FUNCIONAMIENTO: Inicia el pago de la reserva del pase con Mercado Pago: hace POST /user/mercadopago/checkout con `tipo: 'reserva'` y el id, y redirige al navegador a `init_point`; si falla muestra el error en un toast."
            ),
        },
    },
    "static/js/modules/reservas.js": {
        "proposito": (
            "💡 LA IDEA: Es la ventanilla integral de reservas para los conductores. Agrupa todo lo que un cliente necesita: elegir fecha y hora para asegurar su lugar, consultar sus reservas activas y pasadas, abonar con saldo o Mercado Pago y mostrar su Pase Digital QR para abrir la barrera.\n\n"
            "🎯 POR QUE FUE GENERADA: Las reservas son el corazón del negocio de AUTOPASS. Para mantener un código limpio y mantenible, las cuatro etapas del ciclo de reserva (el formulario interactivo, el listado histórico, los pagos/cancelaciones y el comprobante digital con QR) se programaron en módulos independientes. Este archivo provee una fachada única para que el resto de la web interactúe con el subsistema de reservas sin conocer su división interna.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Reexporta 14 funciones del formulario desde `reservas-form.js` (como `initReservationForm`, `updatePeriodEnd`, `toggleReservaForm`, `fetchRates`, `updateReservationPrice`, `createReservation`, `repeatReservation`). 2. Reexporta 7 funciones del historial desde `reservas-list.js` (como `loadReservations`, `applyHistoryFilters`, `renderReservaCard`, `renderHistory`, `historialPage`, `resetHistoryFilters`). 3. Reexporta las operaciones de caja y cancelación desde `reservas-actions.js` (`cancelReservation`, `payReservation`, `payReservationWithMp`). 4. Reexporta las funciones del comprobante digital desde `reservas-pass.js` (`showDigitalPass`, `closeDigitalPass`, `shareTicket`, `payReservationFromPass`)."
        ),
        "simbolos": {
        },
    },
    "static/js/modules/tour-steps.js": {
        "proposito": 'Repositorio de datos puro del tour guiado: define los arrays de pasos (selector, título, texto, alineación, interactividad y callback `beforeShow`) de todos los recorridos de onboarding y ayuda, más los helpers `ensure*` que preparan la interfaz antes de mostrar cada paso. Es consumido por tour.js, que es el motor de recorrido.',
        "simbolos": {
            "noVehiclesTourSteps": (
                '💡 LA IDEA: Es el libreto de bienvenida para usuarios nuevos que aún no cargaron ningún auto.\n\n'
                '🎯 POR QUE FUE GENERADA: Guía al cliente paso a paso para que registre su primer vehículo y conozca el mapa y los puntos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cinco pasos de bienvenida automáticos para usuarios sin vehículos: saludo, formulario de alta de vehículo, mapa de sucursales, tarjeta de puntos y cierre; cada paso navega a su sección con `window.showSection` y el segundo despliega el formulario de alta.'
            ),
            "mainTourSteps": (
                '💡 LA IDEA: Es el libreto que se enciende apenas diste de alta tu primer auto.\n\n'
                '🎯 POR QUE FUE GENERADA: Te enseña a elegir el horario, la sucursal y a confirmar tu primera reserva de estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Seis pasos del recorrido de bienvenida que se lanza tras crear el primer vehículo: formulario de reserva, selector de vehículo, sucursal, tipo de estadía, botón de confirmación y mapa; el primer paso abre el formulario de reserva si está cerrado.'
            ),
            "reservationsTourSteps": (
                '💡 LA IDEA: Es la visita guiada por la pantalla de reservas: te muestra dónde está el pase QR, cómo pagar y cómo ver tus puntos ganados.\n\n'
                '🎯 POR QUE FUE GENERADA: Familiariza al conductor con todas las herramientas disponibles una vez contratado el servicio.\n\n'
                '⚙️ FUNCIONAMIENTO: Ocho pasos que se muestran en la sección Mis Reservas después de crear una reserva: la lista de reservas, los botones de acción (pase digital, pago con Mercado Pago, editar, cancelar), la tarjeta de puntos, el catálogo de promociones, el historial de puntos y el cierre del recorrido.'
            ),
            "noVehiclesHelpTourSteps": (
                '💡 LA IDEA: Es el manual interactivo completo accesible desde el menú de ayuda para usuarios sin vehículos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite repasar el funcionamiento de la plataforma en cualquier momento si te quedó alguna duda.\n\n'
                '⚙️ FUNCIONAMIENTO: Diez pasos del tour manual que se lanza desde Ayuda y Soporte para usuarios sin vehículos: recorre ayuda, alta del primer vehículo (abriendo el formulario rápido), mapa, sección de flota, reservas con pase QR, billetera, puntos, notificaciones, tickets de soporte y cierre.'
            ),
            "existingVehiclesHelpTourSteps": (
                '💡 LA IDEA: Es el manual interactivo para usuarios habituales que ya tienen autos cargados.\n\n'
                '🎯 POR QUE FUE GENERADA: Explica funciones avanzadas como la gestión de flota, billetera virtual y tickets de soporte.\n\n'
                '⚙️ FUNCIONAMIENTO: Once pasos del tour manual de Ayuda para usuarios que ya tienen vehículos: flota, alta de nuevos vehículos (abriendo el formulario), formulario de reserva, mapa, reservas con pase QR, billetera, puntos, notificaciones, soporte y cierre.'
            ),
            "ensureVehicleFormOpen": (
                '💡 LA IDEA: Es el asistente de escena que te lleva a la sección de vehículos y abre el formulario de alta antes de que hable el tour.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el globito explicativo apunte a un formulario que está cerrado o escondido.\n\n'
                "⚙️ FUNCIONAMIENTO: Helper `beforeShow`: navega a la sección de vehículos y despliega el formulario de alta (`#vehicle-form-container` con clase 'open') ocultando su botón disparador, para que el paso del tour apunte siempre a un formulario visible."
            ),
            "addVehicleTourSteps": (
                '💡 LA IDEA: Es la secuencia de globitos que te indica dónde escribir la patente, qué tipo de auto es y qué botón tocar para guardar.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace imposible equivocarse al dar de alta un vehículo en la cuenta.\n\n'
                '⚙️ FUNCIONAMIENTO: Seis pasos que guían el alta de vehículo (sección, formulario, categoría, patente, marca/modelo y botón CONTINUAR), todos con `beforeShow = ensureVehicleFormOpen` para mantener el formulario abierto durante el recorrido.'
            ),
            "ensureReservationFormOpen": (
                '💡 LA IDEA: Es el preparador que despliega el formulario de reservas en pantalla antes de señalarlo con el tour.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que los controles de horario y sucursal estén completamente visibles para el usuario.\n\n'
                "⚙️ FUNCIONAMIENTO: Helper `beforeShow`: cambia a la sección Inicio y abre el formulario de reserva invocando `window.toggleReservaForm()` si el contenedor no tiene la clase 'open'."
            ),
            "createReservationTourSteps": (
                '💡 LA IDEA: Es la guía interactiva que te acompaña campo por campo mientras completás tu reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Enseña a utilizar el selector de horarios y las modalidades de reserva de forma práctica.\n\n'
                '⚙️ FUNCIONAMIENTO: Seis pasos que guían la creación de una reserva (sección Inicio, formulario, selección de vehículo, sucursal, tipo de estadía y confirmación), todos con `beforeShow = ensureReservationFormOpen`.'
            ),
            "ensureRechargeModalOpen": (
                '💡 LA IDEA: Es el asistente que abre la ventanita de carga de saldo antes de explicar cómo fondear la cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra la pantalla correcta para que la explicación coincida con lo que estás viendo.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper `beforeShow`: abre el modal de carga de saldo llamando a `window.openRechargeModal()` si está disponible.'
            ),
            "rechargeBalanceTourSteps": (
                '💡 LA IDEA: Es el recorrido que enseña cómo funciona la billetera virtual y cómo cargar crédito en la cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Explica el beneficio de pagar sin efectivo y de forma automática al salir de la cochera.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuatro pasos de la recarga de saldo: badge de billetera, modal de recarga, selección o ingreso del monto y botón de confirmación; los últimos tres abren el modal con `ensureRechargeModalOpen`.'
            ),
            "ensurePointsTabOpen": (
                '💡 LA IDEA: Es el cambio de solapa que te posiciona en la sección del Club de Puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el tour te lleve al lugar exacto donde se encuentran las recompensas.\n\n'
                "⚙️ FUNCIONAMIENTO: Helper `beforeShow`: cambia la navegación a la sección de Puntos con `window.showSection('puntos', ...)`."
            ),
            "redeemPointsTourSteps": (
                '💡 LA IDEA: Es el tutorial de canje de puntos: enseña a mirar las ofertas, el costo en puntos y cómo obtener el cupón.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra a los conductores cómo sacar provecho a los puntos que acumulan por estacionar.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuatro pasos del tour de canje de puntos: tarjeta principal de puntos, barra de progreso, catálogo de promociones y botón CANJEAR, todos anclados a la sección de puntos que abre `ensurePointsTabOpen`.'
            ),
            "ensureReservationsTabOpen": (
                '💡 LA IDEA: Es el atajo que te traslada a la solapa de Mis Reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Posiciona la vista en los turnos agendados para poder mostrar el pase QR.\n\n'
                "⚙️ FUNCIONAMIENTO: Helper `beforeShow`: cambia la navegación a la sección Mis Reservas con `window.showSection('reservas', ...)`."
            ),
            "ensureDigitalPassModalOpen": (
                '💡 LA IDEA: Es el proyector que abre el pase digital en pantalla (incluso generando uno de prueba si no tenés reservas).\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el usuario pueda ver cómo luce el código QR de entrada durante la explicación educativa.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper `beforeShow` asíncrono que garantiza que el modal del pase esté visible: primero intenta invocar `showDigitalPass` con el id extraído del botón de la tarjeta, luego con la primera reserva de `window.userReservations` y, como último recurso, pinta datos demo (id, patente, sucursal, vencimiento) y genera un QR de ejemplo si el contenedor está vacío.'
            ),
            "qrPassTourSteps": (
                '💡 LA IDEA: Es el recorrido explicativo del Pase Digital: señala el código QR, explica cómo acercarlo al lector y cómo guardarlo como foto.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda total seguridad al usuario sobre cómo ingresar al predio sin tocar botones ni sacar tickets de papel.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuatro pasos del tour del Pase Digital: botón para abrirlo (con `ensureReservationsTabOpen`), sección del código QR, datos de la estadía y botón de compartir/descargar (estos dos últimos abren el modal con `ensureDigitalPassModalOpen`).'
            ),
            "quickAddSteps": (
                '💡 LA IDEA: Es la guía rápida del formulario exprés de alta de auto desde la portada de inicio.\n\n'
                '🎯 POR QUE FUE GENERADA: Agiliza la primera carga vehicular sin obligar al usuario a desplazarse hasta la sección de perfil.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuatro pasos del formulario de alta rápida de vehículo en Inicio: tipo de vehículo, patente, marca/modelo y botón CONTINUAR.'
            ),
        },
    },
    "static/js/modules/tour.js": {
        "proposito": 'Motor del tour guiado: crea el overlay con recorte SVG, el tooltip y la flecha, posiciona cada paso sobre el elemento objetivo, maneja navegación (botones y teclado), auto-avance al interactuar con el formulario y las distintas secuencias de recorrido; también encadena el tour de reservas después de crear una reserva.',
        "simbolos": {
            "createTourElements": (
                '💡 LA IDEA: Es el iluminador de teatro: oscurece toda la pantalla con una máscara negra y deja un foco de luz dorado sobre el botón a explicar.\n\n'
                '🎯 POR QUE FUE GENERADA: Guía la mirada del usuario de forma irresistible hacia el elemento exacto que se le está enseñando a usar.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea (eliminando antes un overlay duplicado si existe) el overlay del tour con un SVG de recorte, un rectángulo dorado de resaltado, el tooltip con botones Anterior/Siguiente/Omitir/Cerrar y la flecha indicadora; conecta los botones y registra los listeners de resize, scroll y teclado.'
            ),
            "handleTourKeydown": (
                '💡 LA IDEA: Es el control remoto del tour con las flechas del teclado y la tecla Escape para salir.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite recorrer la guía cómodamente con el teclado sin necesidad de apuntar con el mouse.\n\n'
                '⚙️ FUNCIONAMIENTO: Teclado del tour: con Escape lo termina, con flecha derecha avanza y con flecha izquierda retrocede; solo actúa si el tour está activo y el overlay no está oculto.'
            ),
            "updateSvgCutout": (
                '💡 LA IDEA: Es la tijera digital que recorta el agujero en la cortina negra para encuadrar con precisión el botón destacado.\n\n'
                '🎯 POR QUE FUE GENERADA: Se adapta con esquinas redondeadas al tamaño real del botón o campo resaltado en pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Recalcula el path del SVG del overlay para oscurecer toda la pantalla dejando un hueco con esquinas redondeadas alrededor del elemento resaltado (con 8px de padding), o cubre todo y oculta el resaltado si no hay objetivo; mantiene sincronizado el rectángulo dorado.'
            ),
            "handleWindowReposition": (
                '💡 LA IDEA: Es el estabilizador de imagen que reacomoda el foco y el globito si cambiás el tamaño de la ventana o girás el celular.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que las explicaciones queden desfasadas o flotando en el aire al cambiar de orientación.\n\n'
                '⚙️ FUNCIONAMIENTO: Al producirse resize o scroll, encola con requestAnimationFrame un reposicionado del paso activo, usando la bandera `isPositioningActive` para evitar llamadas superpuestas.'
            ),
            "getVisibleTarget": (
                '💡 LA IDEA: Es el rastreador que comprueba si el elemento a explicar está realmente a la vista en la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite encontrar el botón tanto en versiones de computadora como en versiones móviles de la interfaz.\n\n'
                '⚙️ FUNCIONAMIENTO: Recibe un selector con comas y devuelve el primer elemento con dimensiones visibles entre todos los selectores; si ninguno es visible, devuelve como respaldo el primer elemento del primer selector.'
            ),
            "repositionActiveStep": (
                '💡 LA IDEA: Es el acomodador del globito explicativo: lo coloca arriba, abajo o al costado del botón asegurándose de que nunca se salga de la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el texto y la flecha indicadora apunten siempre con total nitidez al elemento explicado.\n\n'
                '⚙️ FUNCIONAMIENTO: Posiciona tooltip y flecha respecto del objetivo: respeta `step.align`, centra si `step.center` o si el elemento no tiene dimensiones, en pantallas menores a 680px fuerza alineación top/bottom, corrige si se sale del viewport, clampa la posición dentro de los márgenes y ubica la flecha (con sus bordes CSS) del lado correcto apuntando al centro del objetivo.'
            ),
            "showTourStep": (
                '💡 LA IDEA: Es el presentador que lee el paso actual, mueve la pantalla suavemente hacia el elemento y enciende el cartel explicativo.\n\n'
                '🎯 POR QUE FUE GENERADA: Orquesta el paso a paso del tutorial coordinando animaciones, lectura de textos y desplazamientos suaves.\n\n'
                "⚙️ FUNCIONAMIENTO: Muestra el paso indicado: ejecuta su `beforeShow` (esperando promesas), escribe título y texto, aplica la interactividad del overlay, espera hasta 12 intentos a que el objetivo sea visible, observa sus cambios de tamaño con ResizeObserver, hace scroll suave si queda fuera del viewport, anima el reposicionado durante y después del scroll, actualiza el estado de los botones (Anterior deshabilitado en el primero, Siguiente como 'Finalizar' en el último) y hace foco si el paso es interactivo; si el objetivo nunca aparece salta al siguiente paso o termina el tour."
            ),
            "handleVehicleChange": (
                '💡 LA IDEA: Es el sensor de auto-avance que detecta cuando elegiste un auto y pasa automáticamente al siguiente paso del tour.\n\n'
                "🎯 POR QUE FUE GENERADA: Acompaña tus acciones reales sin obligarte a apretar 'Siguiente' cada vez que completás un campo.\n\n"
                '⚙️ FUNCIONAMIENTO: Auto-avance: si el paso actual apunta al selector de vehículo de la reserva, espera 250ms y pasa al siguiente paso.'
            ),
            "handleSucursalChange": (
                '💡 LA IDEA: Es el sensor que avanza el tour apenas seleccionás el estacionamiento al que querés ir.\n\n'
                '🎯 POR QUE FUE GENERADA: Dinamiza el aprendizaje guiado respondiendo de inmediato a tus elecciones en el formulario.\n\n'
                '⚙️ FUNCIONAMIENTO: Auto-avance: si el paso actual apunta al selector de sucursal, avanza el tour tras 250ms.'
            ),
            "handleTypeChange": (
                '💡 LA IDEA: Es el sensor que salta al siguiente paso al elegir si querés estacionar por hora, día o mes.\n\n'
                '🎯 POR QUE FUE GENERADA: Fluye de manera natural con el ritmo de carga del usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Auto-avance: si el paso actual apunta al selector de tipo de estadía, avanza el tour tras 250ms.'
            ),
            "handlePuntosNavClick": (
                '💡 LA IDEA: Es el sensor que avanza la explicación cuando hacés clic en la pestaña de puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Conecta la navegación manual con el libreto del tutorial educativo.\n\n'
                '⚙️ FUNCIONAMIENTO: Auto-avance: si el paso actual apunta al ítem de navegación de Puntos, avanza el tour tras 250ms al hacer clic.'
            ),
            "startTourAutoAdvance": (
                '💡 LA IDEA: Es el encendido de los sensores de avance automático mientras estás realizando el recorrido guiado.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace que la experiencia se sienta mágica e interactiva mientras vas completando los campos.\n\n'
                '⚙️ FUNCIONAMIENTO: Suscribe los listeners de cambio (vehículo, sucursal, tipo) y de clic (nav de Puntos) que disparan el auto-avance del tour mientras el usuario interactúa.'
            ),
            "stopTourAutoAdvance": (
                '💡 LA IDEA: Es el apagado de los sensores cuando termina el tour para devolver el formulario a su comportamiento estándar.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el formulario siga cambiando de paso o disparando efectos cuando ya terminaste la guía.\n\n'
                '⚙️ FUNCIONAMIENTO: Quita los listeners de auto-avance instalados por `startTourAutoAdvance`, devolviendo los controles a su comportamiento normal.'
            ),
            "startAddVehicleTour": (
                '💡 LA IDEA: Es el disparo del tutorial interactivo para registrar un nuevo rodado en la cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a conductores novatos a empadronar su auto sin confusiones.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicia el tour de alta de vehículo: marca el tour y la sesión de onboarding como activos, carga `addVehicleTourSteps`, crea el overlay si hace falta y muestra el primer paso tras 15ms de transición.'
            ),
            "startQrPassTour": (
                '💡 LA IDEA: Es el lanzamiento del tutorial del Pase Digital QR.\n\n'
                '🎯 POR QUE FUE GENERADA: Enseña a utilizar el código de acceso digital para ingresar por la barrera automática.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicia el tour del Pase Digital QR con `qrPassTourSteps`, con el mismo patrón de arranque que el resto de los tours.'
            ),
            "startCreateReservationTour": (
                '💡 LA IDEA: Es el arranque del recorrido que te enseña a reservar tu lugar de estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Instruye sobre cómo elegir horarios y asegurar una plaza antes de salir de viaje.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicia el tour de creación de reserva con `createReservationTourSteps` y muestra su primer paso.'
            ),
            "startRechargeBalanceTour": (
                '💡 LA IDEA: Es el inicio de la guía interactiva para cargar saldo en la billetera virtual.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra las ventajas del pago digital sin esperas en caja.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicia el tour de recarga de saldo con `rechargeBalanceTourSteps`.'
            ),
            "startRedeemPointsTour": (
                '💡 LA IDEA: Es la puesta en marcha de la guía para canjear beneficios con tus puntos acumulados.\n\n'
                '🎯 POR QUE FUE GENERADA: Enseña a disfrutar del programa de recompensas de la empresa.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicia el tour de canje de puntos con `redeemPointsTourSteps`.'
            ),
            "startReservationTour": (
                '💡 LA IDEA: Es el cerebro maestro que evalúa si tenés autos o no para lanzarte el recorrido de ayuda más adecuado a tu situación.\n\n'
                '🎯 POR QUE FUE GENERADA: Personaliza el aprendizaje según el perfil del conductor para no aburrirlo con pasos irrelevantes.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicia el tour de ayuda general: según el usuario tenga vehículos (en `window.userVehicles` o en el DOM) elige `existingVehiclesHelpTourSteps` o `noVehiclesHelpTourSteps`, y arranca desde el índice recibido (por defecto 0).'
            ),
            "startPostAddReservationTour": (
                '💡 LA IDEA: Es el festejo y continuación que te invita a hacer tu primera reserva apenas terminaste de registrar tu auto.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene el impulso del usuario para que complete su primera reserva exitosa en el sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicia el recorrido `mainTourSteps` que se muestra después de registrar el primer vehículo.'
            ),
            "startReservationTourAtReservations": (
                '💡 LA IDEA: Es la continuación del recorrido directamente en la lista de reservas tras haber creado un turno.\n\n'
                '🎯 POR QUE FUE GENERADA: Conecta el final de la compra con la revisión del comprobante digital.\n\n'
                "⚙️ FUNCIONAMIENTO: Continúa el tour directamente en el paso de Mis Reservas: evita doble inicio mediante la bandera `reservationsTourInitialized`, solo procede si el onboarding está activo en la sesión o es la primera vez (localStorage 'seen_reservation_onboarding'), restaura los pasos guardados si venía de un tour quick-add, busca el paso cuyo selector corresponda a las listas de reservas y, si no lo encuentra, cae a `startReservationTour(0)`."
            ),
            "nextTourStep": (
                '💡 LA IDEA: Es el avance al siguiente paso de la guía interactiva.\n\n'
                "🎯 POR QUE FUE GENERADA: Permite recorrer la explicación a tu propio ritmo con el botón de 'Siguiente'.\n\n"
                '⚙️ FUNCIONAMIENTO: Avanza al siguiente paso o finaliza el tour si estaba en el último.'
            ),
            "prevTourStep": (
                '💡 LA IDEA: Es el botón para volver a leer el paso anterior si te quedó alguna duda.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga libertad para retroceder en la explicación sin tener que reiniciar todo el tour.\n\n'
                '⚙️ FUNCIONAMIENTO: Retrocede un paso si no se está en el primero.'
            ),
            "_baseEndTour": (
                '💡 LA IDEA: Es la rutina de despedida que desvanece la cortina negra, apaga las luces y recuerda que ya viste el tutorial.\n\n'
                '🎯 POR QUE FUE GENERADA: Cierra el tour con suavidad y guarda la preferencia en el navegador para no volver a interrumpirte.\n\n'
                "⚙️ FUNCIONAMIENTO: Rutina común de cierre: marca el tour inactivo, desconecta el ResizeObserver, cancela la sesión de onboarding si el usuario omitió el tour o si se llegó al bloque de reservas (si terminó el main tour o el quick-add queda activa a la espera de la reserva), quita los listeners de auto-avance, oculta overlay, tooltip y flecha con transición de 300ms y guarda la marca 'seen_reservation_onboarding' en localStorage."
            ),
            "startQuickAddTour": (
                '💡 LA IDEA: Es la versión exprés del tutorial pensada para el formulario rápido de la portada principal.\n\n'
                '🎯 POR QUE FUE GENERADA: Enseña a dar de alta el auto y reservar en menos de un minuto directamente desde el inicio.\n\n'
                "⚙️ FUNCIONAMIENTO: Inicia el tour del formulario de alta rápida: guarda los pasos actuales en `_savedTourSteps`, usa `quickAddSteps` y registra un listener temporal del evento 'reservation:created' que, al crearse la reserva, restaura los pasos guardados y deja cargados `reservationsTourSteps` para continuar en Mis Reservas."
            ),
            "endTour": (
                "💡 LA IDEA: Es el botón de 'Cerrar o Finalizar' del tour que concluye la experiencia educativa.\n\n"
                '🎯 POR QUE FUE GENERADA: Devuelve el control absoluto de la aplicación al usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Expone el cierre del tour: llama a `_baseEndTour` y, si era el tour quick-add, restaura los pasos originales; limpia los flags de estado al final.'
            ),
            "_handleReservationCreated": (
                '💡 LA IDEA: Es el detector que celebra cuando terminaste de crear tu reserva y te lleva a ver tu nuevo comprobante.\n\n'
                '🎯 POR QUE FUE GENERADA: Encadena de forma inteligente el final del formulario con la explicación de cómo usar el pase digital.\n\n'
                "⚙️ FUNCIONAMIENTO: Manejador del evento 'reservation:created': si la sesión de onboarding está activa, destruye el tour anterior (overlay, tokens, listeners), carga `reservationsTourSteps` y reintenta hasta 10 veces cada 300ms esperando a que existan en el DOM los selectores de listas de reservas para crear el overlay y mostrar el paso correspondiente; si no aparecen, recurre a `startReservationTourAtReservations`. Al final del archivo se registran además los listeners globales de 'reservation:created', 'reservation:created:debug' y Escape."
            ),
        },
    },
    "static/js/modules/vehicles.js": {
        "proposito": 'Gestión de la flota vehicular del usuario: carga y pinta las tarjetas de vehículos, sincroniza los selects de reserva, alta de vehículos con validación de patente, favoritos, eliminación y detección automática del tipo de vehículo al escribir la patente.',
        "simbolos": {
            "loadVehicles": (
                '💡 LA IDEA: Es el garaje virtual que busca tus autos en el servidor y te dibuja sus tarjetas con opciones de favorito o borrar.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene al día la lista de tus autos y precarga automáticamente tu vehículo preferido en las reservas.\n\n'
                '⚙️ FUNCIONAMIENTO: Pide GET /user/vehicles y arma la sección Mis Vehículos: inicializa la autodetección de tipo, actualiza el contador `stat-vehicles`, pinta las tarjetas de cada vehículo (o un estado vacío si no hay), refresca todos los selects `.res-vehicle` conservando la selección actual, auto-selecciona el único vehículo o el marcado como favorito, y devuelve el array de vehículos.'
            ),
            "toggleVehicleForm": (
                '💡 LA IDEA: Es el acordeón para abrir o cerrar el formulario de alta de un nuevo vehículo.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene ordenada la pantalla mostrando los campos de carga solo cuando vas a sumar un coche.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra u oculta el formulario de alta de vehículo junto a su botón disparador; al cerrarlo limpia el formulario y restablece el icono de tipo a vacío.'
            ),
            "updateVehicleTypeIcon": (
                '💡 LA IDEA: Es el dibujito que cambia solo entre auto, moto o camioneta al costado del campo de patente.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga confirmación visual inmediata sobre qué tipo de vehículo estás dando de alta.\n\n'
                "⚙️ FUNCIONAMIENTO: Cambia el icono del formulario según el tipo elegido (Auto → auto, Moto → moto, Camioneta → camioneta) y ajusta el padding izquierdo del input de patente según el prefijo ('quick-' para el formulario rápido); si no hay tipo oculta el icono y el padding mínimo. Busca el formulario por su propio nodo o desde el icono."
            ),
            "addVehicle": (
                '💡 LA IDEA: Es el empadronamiento del vehículo: valida la patente según las leyes de tránsito y lo guarda en tu cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene errores de tipeo y habilita tu auto para que las cámaras de las barreras lo reconozcan al llegar.\n\n'
                "⚙️ FUNCIONAMIENTO: Maneja el submit del formulario de alta: valida que haya campos, comprueba el formato de patente con `validatePlate` según el tipo, muestra un resumen en la confirmación y hace POST /user/vehicles. En éxito limpia el form, refresca la flota, y según el flujo: si es alta rápida abre el formulario de reserva y pre-selecciona el vehículo nuevo; si no, cierra el formulario de vehículos. Siempre dispara el evento global 'vehicle:added' y restaura el botón al final."
            ),
            "setFavoriteVehicle": (
                '💡 LA IDEA: Es la estrella que asigna a un coche como tu auto favorito de uso diario.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra tiempo en futuras reservas seleccionando automáticamente este auto por defecto.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca o desmarca un vehículo como favorito con POST /user/vehicles/{patente}/favorite, recarga la flota, refresca el estado del formulario de reserva y notifica con toast según el resultado devuelto.'
            ),
            "deleteVehicle": (
                '💡 LA IDEA: Es la eliminación de un vehículo que ya vendiste o no utilizás más.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpia tu lista de rodados asegurando antes que no tenga estadías impagas o reservas activas.\n\n'
                '⚙️ FUNCIONAMIENTO: Pide confirmación, elimina el vehículo con DELETE /user/vehicles/{patente}, recarga la lista y refresca el formulario de reserva; informa el éxito o el error con toast.'
            ),
            "initAutoDetection": (
                '💡 LA IDEA: Es el detector automático que deduce si lo que estás escribiendo es una moto o un auto mientras tipeás la patente.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra clics al usuario cambiando el tipo de rodado por sí solo según el formato de la patente.\n\n'
                "⚙️ FUNCIONAMIENTO: Engancha una sola vez (controlado por `autoDetectionInitialized`) un listener de 'input' en el campo patente de los formularios `add-vehicle-form` y `quick-add-vehicle-form` que detecta el tipo de vehículo con `detectVehicleType`, lo escribe en el select de tipo y actualiza el icono correspondiente."
            ),
        },
    },
    "static/js/modules/virtual-time.js": {
        "proposito": "Provee un reloj virtual compartido por todo el frontend: sincroniza con el offset que expone el servidor y entrega fechas 'virtuales' para que los cálculos de reservas coincidan con el reloj de pruebas del backend (offset 0 = tiempo real).",
        "simbolos": {
            "_sync": (
                '💡 LA IDEA: Es el llamado silencioso al servidor para averiguar cuál es la hora virtual de simulación escolar actual.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene al navegador sincronizado con las pruebas de tiempo acelerado sin colgar la interfaz.\n\n'
                '⚙️ FUNCIONAMIENTO: Pide GET /system/virtual-time y guarda `offset_seconds` convertido a milisegundos en `_offsetMs`, registrando el momento de la sincronización; cualquier error se silencia para no romper la UI.'
            ),
            "initVirtualTime": (
                '💡 LA IDEA: Es el reloj que cada 60 segundos renueva la sincronización con el tiempo virtual del backend.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que todos los cálculos de estadías y turnos en pantalla coincidan exactamente con la hora del servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta una sincronización inicial y programa `_sync` cada 60 segundos con `setInterval` para mantener el offset fresco.'
            ),
            "getVirtualNow": (
                '💡 LA IDEA: Es el reloj virtual en vivo que entrega la fecha y hora simulada para cualquier cálculo del frontend.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace que los contadores, fechas y comprobantes muestren la hora de la simulación en lugar de la hora real de la computadora.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve un `Date` construido con `Date.now() + _offsetMs`: con offset 0 coincide con el tiempo real, con offset positivo/negativo adelanta o atrasa el reloj que usan listados, tarjetas y formularios.'
            ),
        },
    },
    "static/js/perfil.js": {
        "proposito": (
            "💡 LA IDEA: Es el gran director de orquesta del portal del cliente. Cuando un conductor inicia sesión y entra a `/perfil`, este archivo toma el control para levantar todas las solapas (inicio, reservas, puntos, vehículos, notificaciones y ayuda), dibujar el mapa satelital de playas y activar los asistentes interactivos.\n\n"
            "🎯 POR QUE FUE GENERADA: El portal de autoservicio de los conductores tiene múltiples secciones y widgets interactivos (recargar saldo con Mercado Pago, canjear puntos de fidelidad por estadías gratis, editar el DNI o teléfono, registrar autos y abrir el pase QR). Este archivo centraliza la navegación fluida entre pestañas, previene errores globales y ejecuta la secuencia ordenada de arranque para que la pantalla esté lista en milisegundos.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Importa todos los submódulos de usuario (`profile`, `reservas`, `vehicles`, `notifications`, `tour`, `profile-help`, `onboarding-helpers`, `ui`, `utils`). 2. Publica en `window` decenas de funciones invocadas por botones HTML (como `showSection`, `openFullMap`, `enterEditMode`, `saveField`, `changePassword`, `processRecharge`, `openCurrentPass`, `redeemPoints`, tickets de soporte y tours). 3. Captura y registra errores globales (`window.onerror` y `unhandledrejection`) para alertar al usuario si falla una red. 4. En `DOMContentLoaded`, inicia el mapa Leaflet, carga el perfil del usuario (`loadProfile`), su flota de vehículos (`loadVehicles`) y sus reservas (`loadReservations`). 5. Verifica si es la primera vez que el cliente ingresa para ofrecerle el tutorial de bienvenida (`checkFirstLoginOnboarding`). 6. Si el usuario llegó desde la portada con una sucursal preseleccionada (`?reserva_sucursal=...`), abre automáticamente el formulario de reserva con esa cochera cargada. 7. Si regresa de pagar en Mercado Pago (`?mp_status=approved`), muestra el cartel de confirmación correspondiente."
        ),
        "simbolos": {
        },
    },
    "static/js/reservas.js": {
        "proposito": (
            "💡 LA IDEA: Es el puente de enlace de reservas en el navegador. Conecta las tarjetas y botones visuales de la pantalla con las funciones de cálculo, creación y pago de turnos, y mantiene un reloj que refresca las reservas automáticamente en segundo plano.\n\n"
            "🎯 POR QUE FUE GENERADA: En las páginas web que usan botones tradicionales con eventos `onclick=\"...\"`, las funciones deben estar registradas en el objeto global `window`. Además, si un conductor deja la pantalla abierta mientras su auto está estacionado, el sistema necesita actualizar el tiempo transcurrido y el estado de la reserva sin obligarlo a recargar la página a mano.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Importa el catálogo de reservas desde `./modules/reservas.js` y las acciones financieras desde `./modules/reservas-actions.js`. 2. Expone en `window` todas las operaciones del cliente (como `toggleReservaForm`, `createReservation`, `loadReservations`, `applyHistoryFilters`, `cancelReservation`, `payReservation`, `payReservationWithMp`, `showDigitalPass`). 3. Configura un temporizador con `setInterval` que cada 60 segundos comprueba si el usuario está conectado y tiene abierta la pestaña de Reservas o de Inicio; si es así, invoca `loadReservations()` de forma silenciosa para actualizar barras de progreso y estados en tiempo real."
        ),
        "simbolos": {
        },
    },
    "static/js/vehicles.js": {
        "proposito": (
            "💡 LA IDEA: Es el encargado de la cochera personal del usuario. Maneja la lista de autos, motos o camionetas que el conductor tiene registrados en su cuenta, permitiéndole dar de alta patentes nuevas, elegir su vehículo favorito o dar de baja rodados antiguos.\n\n"
            "🎯 POR QUE FUE GENERADA: Para que las cámaras de las barreras reconozcan la patente al llegar al estacionamiento, el vehículo debe estar previamente asociado a la cuenta del usuario. Este archivo enlaza la interfaz gráfica con el módulo de rodados y le da dinamismo al acordeón donde se registran los nuevos autos.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Importa las funciones del módulo `./modules/vehicles.js`. 2. Registra en `window` los métodos `loadVehicles` (consulta de rodados al servidor), `addVehicle` (envío del formulario de alta con validación de patente Mercosur), `deleteVehicle` (baja de un vehículo), `toggleVehicleForm` y `updateVehicleTypeIcon` (cambio dinámico del dibujito de auto/moto/camioneta). 3. Define la función interactiva `window.toggleNuevoVinculo()`, que abre o pliega el contenedor de nuevo vehículo con una animación suave, rotando la flecha del botón según el tamaño de la pantalla (girando 90° o 180° si es computadora de escritorio o teléfono móvil)."
        ),
        "simbolos": {
        },
    },
}
