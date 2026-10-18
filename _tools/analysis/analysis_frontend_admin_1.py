"""Explicaciones analizadas de frontend-admin (parte 1): análisis del código real."""

ANALISIS: dict[str, dict] = {
    "static/js/dashboard.js": {
        "proposito": (
            "💡 LA IDEA: Es el comandante en jefe de la cabina de control de AUTOPASS. Coordina y pone en marcha todas las pantallas del panel de administración: monitoreo en vivo de barreras, control de ocupación, cobro en caja, reservas de clientes, reportes de recaudación, gestión de personal, sucursales y configuración de cámaras.\n\n"
            "🎯 POR QUE FUE GENERADA: El panel de administración es la interfaz más compleja de la plataforma. Para que los botones del menú y las tablas interactivas funcionen de forma instantánea sin recargar la página, se requiere un orquestador central que conecte cada botón con su módulo especialista y mantenga sincronizada toda la operatoria del estacionamiento.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Importa todos los módulos funcionales del panel (`dashboard-ui`, `dashboard-stats`, `dashboard-operations`, `dashboard-reservations`, `dashboard-finance`, `dashboard-metrics`, `dashboard-informes`, `dashboard-tickets`, `admin-tour`, `virtual-time`, `operator-alerts`, etc.). 2. Publica en el objeto global `window` decenas de funciones operativas (como `switchTab`, `manualEntry`, `manualExit`, `payOccupancy`, `openBarrier`, `loadUsers`, `loadFinanceData`, tours guiados y filtros). 3. Conecta el sistema de alertas del operador (`initOperatorAlerts`) y sincroniza el reloj virtual de simulación (`initVirtualTime`). 4. Al cargarse la página (`DOMContentLoaded`), detecta el rol del usuario (administrador general, administrador local o personal de garita), oculta las pestañas restringidas según sus permisos de acceso (RBAC), inicializa el canal en tiempo real de ocupación y dispara la carga de datos de la pestaña activa (`loadTabData`)."
        ),
        "simbolos": {
        },
    },
    "static/js/modules/admin-help.js": {
        "proposito": 'Centro de ayuda del administrador: modal con tarjetas de accesos rápidos y FAQ colapsable. Permite filtrar el contenido por categoría y por búsqueda libre, ocultando o mostrando tarjetas y preguntas según coincidan con el filtro.',
        "simbolos": {
            "openAdminHelpModal": (
                '💡 LA IDEA: Es la ventanilla de ayuda del administrador: abre un centro de asistencia con accesos directos y respuestas rápidas a dudas operativas.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda soporte inmediato al personal de garita y gerentes sin obligarlos a consultar manuales externos en papel.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el modal `modal-admin-help` usando el helper global `window.openModal` si está disponible; si no, lo muestra directamente con `display: flex`.'
            ),
            "toggleAdminFaq": (
                '💡 LA IDEA: Es el fuelle de preguntas frecuentes del panel: tocás una duda y se despliega su explicación paso a paso.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpia la ventana de ayuda, permitiendo leer solo la respuesta que te interesa en ese momento.\n\n'
                '⚙️ FUNCIONAMIENTO: Alterna la clase `open` en el ítem de FAQ más cercano al elemento clickeado (`.admin-faq-item`), expandiendo o colapsando su respuesta.'
            ),
            "filterAdminHelpCategory": (
                '💡 LA IDEA: Es el selector temático de ayuda técnica (cámaras, tarifas, usuarios o cobros).\n\n'
                '🎯 POR QUE FUE GENERADA: Agiliza encontrar soluciones filtrando los temas no relacionados con tu problema operativo actual.\n\n'
                "⚙️ FUNCIONAMIENTO: Marca la píldora de categoría seleccionada como activa y muestra u oculta las tarjetas rápidas (`.admin-help-quick-card`) y los grupos de FAQ según su `data-category`: con `'all'` se muestran todas, incluidas las marcadas `'all'`."
            ),
            "filterAdminHelpSearch": (
                '💡 LA IDEA: Es el buscador de ayuda administrativa que filtra tarjetas y respuestas a medida que escribís.\n\n'
                "🎯 POR QUE FUE GENERADA: Permite resolver imprevistos en segundos buscando palabras clave como 'barrera', 'factura' o 'reembolso'.\n\n"
                '⚙️ FUNCIONAMIENTO: Filtra tarjetas rápidas y preguntas de FAQ por coincidencia de texto (en minúsculas) contra la consulta ingresada; un término vacío muestra todo, y al mostrar un ítem de FAQ también revela su grupo contenedor.'
            ),
        },
    },
    "static/js/modules/admin-tour-engine.js": {
        "proposito": 'Motor del recorrido guiado del admin: crea el overlay oscuro con recorte SVG alrededor del elemento destacado, el tooltip y la flecha; resuelve el selector visible del paso, posiciona el tooltip con alineación y desbordes, y gestiona la navegación (teclado, botones, resize/scroll) hasta finalizar el tour. Mantiene estado interno (pasos activos, índice, overlay) en variables del módulo.',
        "simbolos": {
            "createAdminTourElements": (
                '💡 LA IDEA: Es el proyector de foco del panel administrativo: oscurece el fondo y coloca un halo dorado alrededor del botón a explicar.\n\n'
                '🎯 POR QUE FUE GENERADA: Enseña a utilizar el panel de control guiando la mirada del empleado sin que se desoriente en una interfaz llena de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea (o recrea si ya existe) el overlay del tour: `div` con un `svg` que tiene un `path` de recorte y un rectángulo de resalte dorado, más tooltip y flecha con sus botones Anterior/Siguiente/Omitir. Registra los listeners de click y los eventos globales de `resize`, `scroll` y `keydown`.'
            ),
            "handleAdminTourKeydown": (
                '💡 LA IDEA: Es el comando de navegación con teclado para avanzar, retroceder o salir de la capacitación con las flechas o Escape.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace cómodo el aprendizaje permitiendo recorrer los pasos con una sola mano en el teclado.\n\n'
                '⚙️ FUNCIONAMIENTO: Maneja el teclado durante el tour: `Escape` lo termina, `ArrowRight` avanza y `ArrowLeft` retrocede; solo actúa si el tour está activo y el overlay visible.'
            ),
            "updateAdminSvgCutout": (
                '💡 LA IDEA: Es el marco inteligente que se ajusta a las dimensiones del gráfico o tabla que se está explicando.\n\n'
                '🎯 POR QUE FUE GENERADA: Resalta con precisión matemática cualquier control del panel independientemente de su tamaño.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja en el `path` del SVG la ventana oscura: si no hay rectángulo (paso centrado) tapa toda la pantalla; si hay, arma un `path` con esquinas redondeadas que deja libre el elemento destino con 8 px de padding y posiciona el rectángulo de resalte sobre esa zona.'
            ),
            "handleAdminWindowReposition": (
                '💡 LA IDEA: Es el sensor de movimiento que recoloca el cartel explicativo si el operador cambia el tamaño del navegador o hace scroll.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que las explicaciones queden flotando en el lugar equivocado al moverse por el dashboard.\n\n'
                '⚙️ FUNCIONAMIENTO: Reposiciona el paso activo ante `resize` o `scroll`, con un guard `isPositioningActive` y `requestAnimationFrame` para no encolar llamadas.'
            ),
            "getVisibleTarget": (
                '💡 LA IDEA: Es el rastreador de controles visibles entre diferentes resoluciones de pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el tour funcione tanto en monitores de garita como en tablets o notebooks de supervisión.\n\n'
                '⚙️ FUNCIONAMIENTO: Resuelve el primer elemento visible de un selector que puede traer varias alternativas separadas por comas: recorre cada selector y devuelve el primer elemento con dimensiones reales; si ninguno es visible, devuelve el primero encontrado (o `null` si no hay selector).'
            ),
            "repositionActiveAdminStep": (
                '💡 LA IDEA: Es el acomodador del cartel informativo: lo sitúa arriba, abajo o al costado del control destacado asegurando que no se corte en los bordes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza una lectura cómoda de cada lección sin tapar información crucial de la pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula la posición final del tooltip y la flecha para el paso actual: si el paso es `center` o el destino no tiene tamaño, centra el tooltip sin recorte; si no, recorta el SVG, alinea el tooltip (`top`/`bottom`/`left`/`right`, con ajuste en pantallas angostas <680 px), corrige desbordes contra los bordes de la ventana y ubica la flecha apuntando al centro del destino según la alineación efectiva.'
            ),
            "showAdminTourStep": (
                '💡 LA IDEA: Es el instructor que cambia de pestaña automáticamente, desplaza la vista y enciende la explicación del paso actual.\n\n'
                '🎯 POR QUE FUE GENERADA: Automatiza la capacitación del personal mostrando cada sección del sistema en vivo.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra un paso: actualiza índice, ejecuta el hook `beforeShow` (puede ser asíncrono, por ejemplo cambiar de pestaña), rellena badge/título/texto, aplica modo `interactive`, espera hasta 12 intentos a que el selector sea visible (token anti-carrera), observa cambios de tamaño con `ResizeObserver`, scrollea al destino si queda fuera de pantalla, reposiciona durante ~40 frames y habilita/deshabilita el botón Anterior según sea el primer paso.'
            ),
            "nextAdminTourStep": (
                '💡 LA IDEA: Es el botón para pasar al siguiente punto del entrenamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al empleado avanzar a su propio ritmo de comprensión.\n\n'
                '⚙️ FUNCIONAMIENTO: Avanza al siguiente paso o finaliza el tour si estaba en el último.'
            ),
            "prevAdminTourStep": (
                '💡 LA IDEA: Es el botón para repasar el concepto anterior si algo no quedó claro.\n\n'
                '🎯 POR QUE FUE GENERADA: Da flexibilidad para retroceder y fijar conocimientos operativos.\n\n'
                '⚙️ FUNCIONAMIENTO: Retrocede al paso anterior si no está en el primero.'
            ),
            "endAdminTour": (
                '💡 LA IDEA: Es el cierre de la capacitación guiada que apaga el halo dorado y devuelve el control total del panel.\n\n'
                '🎯 POR QUE FUE GENERADA: Concluye el tutorial dejando el dashboard listo para la operación real del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Finaliza el tour: marca inactivo, desconecta el `ResizeObserver`, quita las clases de animación y oculta el overlay al cabo de 300 ms.'
            ),
            "launchAdminTour": (
                '💡 LA IDEA: Es el encendido del motor de recorridos guiados con la lista de pasos elegida.\n\n'
                '🎯 POR QUE FUE GENERADA: Inicia cualquiera de las capacitaciones disponibles desde el centro de ayuda con un solo clic.\n\n'
                '⚙️ FUNCIONAMIENTO: Punto de entrada exportado: recibe la lista de pasos, la copia al estado interno, crea el overlay si no existe, lo muestra y arranca en el paso 0 tras un pequeño delay para la animación de entrada.'
            ),
        },
    },
    "static/js/modules/admin-tour-steps.js": {
        "proposito": 'Definición pura de los 7 recorridos guiados del panel: cada tour es un array de pasos con selector CSS (con alternativas separadas por comas), título, texto, alineación del tooltip, si es interactivo y un hook `beforeShow` que cambia de pestaña/sub-sección para que el destino exista antes de resaltarlo.',
        "simbolos": {
            "adminLiveTourSteps": (
                '💡 LA IDEA: Es el libreto de capacitación para monitoreo en vivo: enseña a vigilar cámaras, controlar barreras y ver ocupación en tiempo real.\n\n'
                '🎯 POR QUE FUE GENERADA: Entrena al personal de garita en el manejo seguro de los accesos vehiculares diarios.\n\n'
                '⚙️ FUNCIONAMIENTO: Tour de Monitoreo y Operaciones: indica de disponibilidad en vivo, monitor multi-cámara, tabla de vehículos estacionados, log de lecturas ALPR, panel de ingreso manual y apertura manual de barreras; cada paso salta a la pestaña `live` (y sub-tab de monitor cuando corresponde).'
            ),
            "adminReservationsTourSteps": (
                '💡 LA IDEA: Es el libreto de gestión de reservas: enseña a cobrar, cancelar turnos y buscar conductores registrados.\n\n'
                '🎯 POR QUE FUE GENERADA: Capacita a los cajeros en la administración de reservas telefónicas y en mostrador.\n\n'
                '⚙️ FUNCIONAMIENTO: Tour de Reservas: KPIs de reservas, filtros y búsqueda, tabla de comprobantes, confirmación manual de pago y cancelación administrativa; todos los pasos navegan a la pestaña `admin-reservations`.'
            ),
            "adminUsersTourSteps": (
                '💡 LA IDEA: Es el libreto de administración de usuarios: explica roles, asignación de saldo, bloqueos y altas de personal.\n\n'
                '🎯 POR QUE FUE GENERADA: Enseña a los supervisores cómo gestionar de forma segura los accesos de clientes y empleados.\n\n'
                '⚙️ FUNCIONAMIENTO: Tour de Usuarios: resumen de roles, buscador/filtro, alta de usuarios, directorio con billetera, bloqueo de cuentas, ajuste de saldo y edición de perfil/permisos; siempre salta a la pestaña `users`.'
            ),
            "adminFinanceTourSteps": (
                '💡 LA IDEA: Es el libreto de finanzas y auditoría: muestra gráficos de recaudación, balances diarios y exportación a Excel.\n\n'
                '🎯 POR QUE FUE GENERADA: Capacita a los gerentes en la revisión contable y control de ingresos de la red.\n\n'
                '⚙️ FUNCIONAMIENTO: Tour Financiero: KPIs ejecutivos, desglose por canal de cobro, filtros por período/método/vehículo, auditoría de transacciones y exportación a CSV, sobre la pestaña `finance`.'
            ),
            "adminTicketsTourSteps": (
                '💡 LA IDEA: Es el libreto de atención al cliente: enseña a revisar reclamos y responder a los usuarios por mensajería interna.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura una respuesta rápida y profesional ante inconvenientes reportados por conductores.\n\n'
                '⚙️ FUNCIONAMIENTO: Tour de Soporte: métricas de tickets, filtros en tiempo real, tabla de atenciones y respuesta directa con notificación push, en la pestaña `tickets`.'
            ),
            "adminBranchesSettingsTourSteps": (
                '💡 LA IDEA: Es el libreto de configuración: explica cómo gestionar pisos, ajustar el tarifario por hora y calibrar cámaras ALPR.\n\n'
                '🎯 POR QUE FUE GENERADA: Guía en la puesta a punto de nuevas sucursales y mantenimiento técnico de hardware.\n\n'
                '⚙️ FUNCIONAMIENTO: Tour de Sucursales y Configuración: red de sucursales, gestión multi-piso, matriz de tarifas y control de cámaras/ALPR. El primer paso salta a `branches` solo para rol `admin` (sino a `settings`); los demás usan `switchSettingsTab` para abrir la sub-sección correspondiente.'
            ),
            "adminFullDashboardTourSteps": (
                '💡 LA IDEA: Es el curso maestro integral que recorre todas las áreas del panel administrativo de corrido.\n\n'
                '🎯 POR QUE FUE GENERADA: Ideal para la inducción completa de un nuevo gerente general en la plataforma.\n\n'
                '⚙️ FUNCIONAMIENTO: Tour integral: concatena el tour completo de Monitoreo con los pasos (a partir del segundo) de los otros seis tours, evitando repetir la intro de cada sección.'
            ),
        },
    },
    "static/js/modules/admin-tour.js": {
        "proposito": 'Fachada del sistema de tours y ayuda: reexporta el modal de ayuda y ofrece una función `start*` por cada recorrido, que cierra el modal de ayuda y delega en `launchAdminTour` con los pasos correspondientes. Agrupa los submódulos de pasos, motor y ayuda en una única superficie para `dashboard.js`.',
        "simbolos": {
            "startAdminLiveTour": (
                '💡 LA IDEA: Es el botón de inicio del tour de monitoreo y barreras en tiempo real.\n\n'
                '🎯 POR QUE FUE GENERADA: Cierra la ventana de ayuda y arranca la capacitación práctica sobre la pantalla de cámaras.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal de ayuda (si `window.closeModal` existe) e inicia el tour de Monitoreo con `adminLiveTourSteps`.'
            ),
            "startAdminReservationsTour": (
                '💡 LA IDEA: Es el botón de inicio del tour del módulo de reservas administrativas.\n\n'
                '🎯 POR QUE FUE GENERADA: Lleva al usuario a la pestaña de reservas y enciende los pasos educativos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal de ayuda e inicia el tour de Reservas con `adminReservationsTourSteps`.'
            ),
            "startAdminUsersTour": (
                '💡 LA IDEA: Es el botón de inicio del tour de administración de cuentas y empleados.\n\n'
                '🎯 POR QUE FUE GENERADA: Conduce a la pestaña de usuarios para comenzar la capacitación de personal.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal de ayuda e inicia el tour de Usuarios con `adminUsersTourSteps`.'
            ),
            "startAdminFinanceTour": (
                '💡 LA IDEA: Es el botón de inicio del tour de reportes de facturación y cobros.\n\n'
                '🎯 POR QUE FUE GENERADA: Ubica la pantalla en el módulo financiero y explica cada métrica contable.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal de ayuda e inicia el tour Financiero con `adminFinanceTourSteps`.'
            ),
            "startAdminTicketsTour": (
                '💡 LA IDEA: Es el botón de inicio del tour de soporte y resolución de reclamos.\n\n'
                '🎯 POR QUE FUE GENERADA: Posiciona la vista en la bandeja de tickets de consulta de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal de ayuda e inicia el tour de Tickets con `adminTicketsTourSteps`.'
            ),
            "startAdminBranchesSettingsTour": (
                '💡 LA IDEA: Es el botón de inicio del tour de ajuste de tarifas, pisos y sucursales.\n\n'
                '🎯 POR QUE FUE GENERADA: Guía en la administración de la infraestructura física del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal de ayuda e inicia el tour de Sucursales/Configuración con `adminBranchesSettingsTourSteps`.'
            ),
            "startAdminFullDashboardTour": (
                '💡 LA IDEA: Es el botón de inicio del tour panorámico completo adaptado según el rol del operador conectado.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda una inducción exhaustiva mostrando solo las secciones a las que el empleado tiene permiso de acceso.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el modal de ayuda e inicia el tour integral: para rol `staff` arma una versión recortada (Monitoreo completo + solo el primer paso de Reservas, ya que staff no accede al resto de las secciones); para los demás roles lanza `adminFullDashboardTourSteps` completo.'
            ),
        },
    },
    "static/js/modules/dashboard-admin-branches-crud.js": {
        "proposito": 'CRUD de sucursales con geolocalización: lista las sedes en la tabla (con ocupación por tipo de vehículo según rol), alta/edición vía modal con mapa Leaflet (click o geocodificación por dirección vía Nominatim), subida o limpieza de logo, activación/suspensión y baja con confirmación. Cachea la lista en `allBranchesData` para reutilizarla en selects y otros módulos.',
        "simbolos": {
            "getAllBranchesData": (
                '💡 LA IDEA: Es la memoria de sucursales en el panel que entrega la lista de estacionamientos sin consultar a la red.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que los selectores de pisos o tarifas se carguen al instante con los datos ya descargados.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el array cacheado `allBranchesData` (última carga de sucursales) para que otros módulos (pisos, promos, usuarios) lo reutilizen sin volver a la API.'
            ),
            "setAllBranchesData": (
                '💡 LA IDEA: Es el archivador que guarda la lista actualizada de sucursales tras crear o editar una sede.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene sincronizada la memoria del navegador con los cambios recientes de infraestructura.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplaza el array cacheado `allBranchesData` con datos externos.'
            ),
            "initBranchMap": (
                '💡 LA IDEA: Es el mapa interactivo para posicionar geográficamente una nueva sucursal con un pin en la calle exacta.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita definir las coordenadas GPS del estacionamiento para que los clientes lleguen guiados por el mapa.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa el mapa Leaflet `branch-map-picker` una sola vez (guard con `branchMap`), centrado en Buenos Aires con tiles de Google Maps, y registra un click que mueve el marcador. No hace nada si el elemento o `window.L` no existen.'
            ),
            "updateBranchMarker": (
                '💡 LA IDEA: Es el marcador dorado del mapa que anota la latitud y longitud con 6 decimales al hacer clic sobre una calle.\n\n'
                '🎯 POR QUE FUE GENERADA: Traduce el clic visual del administrador en coordenadas geográficas de altísima precisión.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea o mueve el marcador dorado en el mapa a la latitud/longitud dadas y sincroniza los inputs `branch-latitude`/`branch-longitude` con 6 decimales.'
            ),
            "searchAddress": (
                '💡 LA IDEA: Es el buscador de direcciones postales que ubica el mapa en la calle y número tipeados automáticamente.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra buscar manualmente en el mapa, posicionando el pin directamente en la dirección indicada.\n\n'
                '⚙️ FUNCIONAMIENTO: Geocodifica la dirección ingresada en `branch-direccion` contra Nominatim (OpenStreetMap); si encuentra resultado, inicializa el mapa, coloca el marcador, hace zoom a nivel 16 y avisa con toast; si no o si falla el fetch, muestra error. Sin dirección, pide que se ingrese una.'
            ),
            "populateBranchSelect": (
                '💡 LA IDEA: Es el llenador de menús desplegables de sucursales en formularios de empleados o cámaras.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita tener que tipear nombres de estacionamientos a mano previniendo errores de tipeo.\n\n'
                "⚙️ FUNCIONAMIENTO: Rellena un `<select>` con los nombres de sucursales: usa el cache local si tiene datos, o consulta `GET /admin/branches` y lo cachea; con lista vacía inserta la opción '-- Sin sucursales --'."
            ),
            "_renderBranchOptions": (
                '💡 LA IDEA: Es la fábrica de opciones HTML para menús de sucursales.\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica el formato de los desplegables de sedes en todo el panel de administración.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper interno: vacía el select y agrega una opción por sucursal con `value` y texto igual al nombre.'
            ),
            "showCreateBranchModal": (
                '💡 LA IDEA: Es la ficha de inauguración de una sucursal nueva: abre el formulario limpio con el mapa listo para marcar la sede.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite dar de alta estacionamientos de forma ordenada y verificando sus datos de contacto y logo.\n\n'
                '⚙️ FUNCIONAMIENTO: Prepara el modal en modo alta: limpia el formulario, borra el id de edición, restaura título/ícono/logo por defecto, abre el modal y, tras 300 ms, inicializa el mapa quitando el marcador previo y centrándolo en la vista por defecto.'
            ),
            "loadBranches": (
                '💡 LA IDEA: Es la cartelera de estacionamientos: lista todas las sucursales con su logo, dirección, horarios y aforos.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga a la gerencia un panorama global de todas las sedes con accesos para editar o suspender locales.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga `GET /admin/branches`, cachea el resultado y pinta la tabla de sucursales con logo, dirección, admin asignado, ocupación/capacidad (solo para no-admin, con barra de progreso), teléfono, horario (24hs o texto), switch de activación y acciones de pisos (solo no-admin), editar y eliminar. Maneja lista vacía y error.'
            ),
            "editBranch": (
                '💡 LA IDEA: Es el editor de datos de la sucursal: carga la ficha de la sede con su mapa y foto para cambiar horarios o teléfonos.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita mantener al día la información pública del local.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el modal en modo edición con los datos de la sucursal buscada por id en el cache: completa formulario, logo (y botón de limpiar si tiene logo propio), horario/24hs (deshabilita el input si es 24hs) y, tras abrir, inicializa el mapa con el marcador y zoom 15 en su ubicación.'
            ),
            "toggleBranch": (
                '💡 LA IDEA: Es la persiana de la sucursal: permite pausar la actividad del estacionamiento sin borrar sus registros.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite poner una sede en mantenimiento temporal de forma controlada.\n\n'
                '⚙️ FUNCIONAMIENTO: Alterna el estado activo de la sucursal vía `POST /admin/branches/{id}/toggle`; en éxito muestra toast con el nuevo estado, en error notifica y recarga la tabla para revertir visualmente el switch.'
            ),
            "toggleBranchHorario": (
                "💡 LA IDEA: Es el interruptor 'Abierto 24hs' que bloquea los campos de hora de apertura y cierre cuando el local no duerme.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita confusiones horarias en predios de atención ininterrumpida.\n\n'
                '⚙️ FUNCIONAMIENTO: Sincroniza el input de horario con el checkbox 24hs: si está marcado lo deshabilita y vacía (con opacidad reducida), si no lo rehabilita.'
            ),
            "previewBranchLogo": (
                '💡 LA IDEA: Es la vista previa del logo comercial elegido antes de guardarlo en el servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite confirmar que la imagen elegida se vea nítida y bien encuadrada.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra una vista previa del logo seleccionado leyendo el archivo con `FileReader` como data URL y revela el botón de limpiar logo.'
            ),
            "clearBranchLogo": (
                '💡 LA IDEA: Es el borrador de foto que restaura el logo oficial por defecto de la empresa.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita quitar fotos obsoletas o defectuosas de una sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Restaura el logo por defecto, vacía el input de archivo, oculta el botón de limpiar y marca `branch-logo-clear=true` para que el backend borre el logo guardado.'
            ),
            "handleCreateBranch": (
                '💡 LA IDEA: Es el envío definitivo del alta o edición de la sucursal hacia la base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida los campos, sube la imagen y actualiza la lista de estacionamientos al instante.\n\n'
                '⚙️ FUNCIONAMIENTO: Submit del formulario de sucursal: arma un `FormData` con nombre, dirección, teléfono, horario/24hs, coordenadas y (opcional) archivo de logo o marca `logo_clear`; envía `POST /admin/branches` si es alta o `PATCH /admin/branches/{id}` si `branch-id-edit` tiene valor; en éxito limpia el modal, recarga la tabla y muestra toast; bloquea el botón durante la petición.'
            ),
            "deleteBranch": (
                '💡 LA IDEA: Es la orden de demolición controlada que da de baja una sucursal del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Exige confirmación estricta para evitar borrados accidentales de locales activos.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina una sucursal con confirmación previa (`DELETE /admin/branches/{id}`); en éxito recarga la tabla, en caso contrario muestra el error del backend.'
            ),
        },
    },
    "static/js/modules/dashboard-admin-branches-floors.js": {
        "proposito": 'Gestión de la estructura vertical de las sucursales (ParkingFloor): modal de niveles por sucursal, cuadrícula de arquitectura del edificio para el admin local (planta baja y pisos con capacidades editables por tipo de vehículo) y CRUD de pisos contra la API. Deriva la ocupación/capacidad de Planta Baja como los totales de la sucursal menos la suma de sus pisos.',
        "simbolos": {
            "showBranchFloors": (
                '💡 LA IDEA: Es el ascensor virtual que muestra la ocupación piso por piso (Planta Baja, Piso 1, Terraza) de un estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ver en qué pisos quedan lugares libres para derivar los autos hacia niveles desocupados.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el modal `modal-branch-floors` con los niveles de la sucursal indicada por id: calcula la fila de Planta Baja restando a los totales de la sucursal la suma de ocupación y capacidad de autos, motos, camionetas y reservas de sus pisos, y pinta una fila por piso con sus valores, marcando en rojo cuando la ocupación alcanza o supera la capacidad.'
            ),
            "loadFloors": (
                '💡 LA IDEA: Es el plano arquitectónico editable del predio para que el administrador local ajuste las plazas de cada nivel.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite reorganizar la capacidad por tipo de vehículo (autos, motos, camionetas) en cada piso.\n\n'
                '⚙️ FUNCIONAMIENTO: Renderiza la cuadrícula de arquitectura (`building-architecture-grid`) solo para rol `local_admin`: trae sucursales y ajustes, identifica la sucursal propia por nombre (localStorage como respaldo), pinta la Planta Baja con inputs de capacidad deshabilitados y un bloque por piso ordenado por id con inputs por tipo de vehículo y botones de editar/guardar. Muestra mensajes de error si la API falla o la sede no se identifica.'
            ),
            "toggleLevelEdit": (
                '💡 LA IDEA: Es el candado de edición de un piso: desbloquea los campos de capacidad para modificarlos con un botón de aplicar.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene modificaciones accidentales en los aforos de los pisos del edificio.\n\n'
                '⚙️ FUNCIONAMIENTO: Alterna el modo edición del bloque de nivel `level-block-{id}`: habilita/deshabilita los inputs, cambia el ícono del botón (lápiz/cerrar) y muestra/oculta el botón APLICAR; al salir de edición recarga la cuadrícula con `loadFloors` para descartar cambios no guardados.'
            ),
            "savePBCapacity": (
                '💡 LA IDEA: Es el guardado de plazas asignadas a la Planta Baja del estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Actualiza las capacidades del nivel principal y recalcula las reservas disponibles.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda las capacidades de Planta Baja: valida que autos, motos y camionetas no queden vacíos y luego envía seis `POST /admin/settings/prices?clave=...&valor=...` (capacidades y reservas por tipo); solo si todas responden OK muestra éxito y recarga la cuadrícula.'
            ),
            "updateFloorCapacity": (
                '💡 LA IDEA: Es el ajuste de pintura de un piso superior para ampliar o reducir lugares de autos, motos o camionetas.\n\n'
                '🎯 POR QUE FUE GENERADA: Adapta los pisos a la demanda real de vehículos en ese sector del edificio.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda las capacidades de un piso con `PATCH /admin/floors/{id}` pasando autos, motos, camionetas y reservas por tipo como query string; recarga la cuadrícula en éxito o muestra el error.'
            ),
            "openAddFloorModal": (
                '💡 LA IDEA: Es la orden de construcción de un piso nuevo dentro del estacionamiento digital.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite sumar niveles a la estructura del estacionamiento de forma sencilla.\n\n'
                '⚙️ FUNCIONAMIENTO: Prepara el modal `modal-add-floor` en modo alta: limpia el id de edición, deja el nombre vacío, capacidades por defecto (20/10/5 y 0 reservas) y títulos/botón de crear, y abre el modal.'
            ),
            "openEditFloorModal": (
                '💡 LA IDEA: Es el formulario para cambiarle el nombre o las capacidades máximas a un piso ya existente.\n\n'
                "🎯 POR QUE FUE GENERADA: Permite renombrar sectores (por ejemplo 'Piso 2' a 'Terraza Cubierta') y actualizar sus límites.\n\n"
                '⚙️ FUNCIONAMIENTO: Prepara el mismo modal en modo edición: busca la sucursal propia y el piso por id, carga nombre y capacidades (con defaults 5 y 0) y ajusta títulos/botón a guardar cambios. No hace nada si no encuentra sucursal o piso.'
            ),
            "handleCreateFloor": (
                '💡 LA IDEA: Es el envío de los datos del piso hacia el servidor para registrar el nuevo nivel en la base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Consolida la arquitectura del edificio y actualiza el aforo general de la sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Submit del formulario de piso: identifica la sucursal propia, arma el payload con nombre y capacidades enteras; si hay `edit-floor-id` envía `PATCH /admin/floors/{id}` con las capacidades por query, si no `POST /admin/{branchId}/floors` con el payload. En éxito cierra el modal y recarga; bloquea el botón durante la petición.'
            ),
            "deleteFloor": (
                '💡 LA IDEA: Es la eliminación de un piso que ya no forma parte del estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite remover niveles en desuso previa confirmación de seguridad.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina un piso con confirmación (`DELETE /admin/floors/{id}`); recarga la cuadrícula en éxito o muestra el error del backend.'
            ),
        },
    },
    "static/js/modules/dashboard-admin-branches.js": {
        "proposito": (
            "💡 LA IDEA: Es la ventanilla única para el manejo de sucursales y pisos del estacionamiento. Centraliza la creación de nuevas playas de estacionamiento, su ubicación geográfica en el mapa y la distribución de cocheras por piso (planta baja, subsuelos o terrazas).\n\n"
            "🎯 POR QUE FUE GENERADA: Manejar un estacionamiento implica dos tareas distintas: por un lado los datos comerciales y de ubicación de la sucursal (dirección, horarios, logo, geolocalización), y por el otro la arquitectura física interna (cuántos pisos tiene y cuántos autos entran por piso). Para mantener el código ordenado se programaron en módulos separados, y este archivo actúa como fachada unificadora para que el panel administrativo acceda a ambos de forma transparente.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Importa y reexporta 14 funciones de gestión de sedes desde `dashboard-admin-branches-crud.js` (como `loadBranches`, `handleCreateBranch`, `initBranchMap`, `searchAddress`, `toggleBranch`, `deleteBranch`). 2. Importa y reexporta 9 funciones de distribución edilicia desde `dashboard-admin-branches-floors.js` (como `showBranchFloors`, `loadFloors`, `savePBCapacity`, `updateFloorCapacity`, `handleCreateFloor`, `deleteFloor`). 3. Permite que el panel de administración invoque cualquier acción sobre las sucursales sin preocuparse por la división interna de archivos."
        ),
        "simbolos": {
        },
    },
    "static/js/modules/dashboard-admin-settings.js": {
        "proposito": 'Configuración del sistema: apertura remota de barreras por MQTT, diagnóstico en vivo (API, base de datos, barreras y cámaras ALPR de la sucursal), carga de parámetros en los inputs de ajustes, pestañas de secciones y tarifas, guardado del tarifario por grupo o individual, reinicio del sistema y exportación de movimientos financieros a CSV con filtros de período, vehículo y método de pago.',
        "simbolos": {
            "openBarrier": (
                '💡 LA IDEA: Es el pulsador de control remoto para levantar o bajar la barrera de ingreso o egreso desde la computadora.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite habilitar el paso manualmente ante emergencias o fallas de lectura de patente.\n\n'
                "⚙️ FUNCIONAMIENTO: Pide confirmación y envía `POST /admin/open-barrier?gate_id=...&command=OPEN|CLOSE` para abrir o cerrar la barrera indicada. Actualiza el ícono de la barrera al estado pedido y, si fue apertura, lo revierte a 'baja' a los 5 s; en error restaura el ícono y muestra toast."
            ),
            "refreshSystemDiagnostics": (
                '💡 LA IDEA: Es el panel de semáforos de salud técnica que indica si la base de datos, las barreras y las cámaras están online.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda certeza operativa inmediata al personal sobre el estado de todo el hardware de la sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Consulta `GET /system/health` y pinta los puntos de estado: API, base de datos y barreras (asociadas al estado de la API), más las cámaras ALPR de entrada/salida de la sucursal actual (claves `{SUCURSAL}_ENTRADA`/`_SALIDA`); el badge global queda ESTABLE solo si API y base están ONLINE.'
            ),
            "loadSettings": (
                '💡 LA IDEA: Es la carga de la pizarra general de precios y límites de capacidad en los campos de configuración.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al administrador revisar las tarifas actuales antes de aplicar cualquier ajuste económico.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga `GET /admin/settings` y vuelca cada clave a su input `cfg-{clave}`; luego recarga la cuadrícula de pisos (`loadFloors`) y refresca el diagnóstico del sistema.'
            ),
            "switchSettingsTab": (
                '💡 LA IDEA: Es el selector de solapa de configuración (tarifas, monitoreo de cámaras o parámetros generales).\n\n'
                '🎯 POR QUE FUE GENERADA: Organiza las distintas áreas de administración del sistema para no mezclar ajustes de precios con hardware.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia la sub-sección visible de Ajustes (`set-section-{tabId}`) y marca el botón activo; si la sección es `monitoring` además dispara `window.loadCameraSettings` para refrescar las cámaras.'
            ),
            "switchRatesTab": (
                '💡 LA IDEA: Es el conmutador de tarifas por tipo de vehículo (autos, motos o camionetas).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite visualizar y editar por separado las tarifas según el porte del rodado.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia el grupo de tarifas visible (`rate-group-{type}`: autos, motos o camionetas) y actualiza la pestaña sub-activa.'
            ),
            "saveAllRates": (
                '💡 LA IDEA: Es el guardado del tarifario completo (las 15 tarifas de media hora, hora, día, semana y mes de todos los vehículos).\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita actualizar toda la lista de precios de la empresa de un solo tirón ante aumentos generales.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el tarifario completo (15 claves: 30 min/hora/día/semana/mes por auto, moto y camioneta): muestra un resumen en la confirmación, y por cada input envía `POST /admin/settings/prices?clave=...&valor=...`; un campo de 30 min vacío se salta (equivale a la mitad de la hora). Si todo sale bien, saca la UI de edición y bloquea los inputs.'
            ),
            "toggleRateEdit": (
                '💡 LA IDEA: Es el desbloqueo de edición de un grupo de tarifas específico para permitir modificar sus valores.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege los precios contra clics involuntarios exigiendo activar el modo edición para modificarlos.\n\n'
                '⚙️ FUNCIONAMIENTO: Activa la edición del grupo de tarifas `type` (habilita inputs, cambia el botón a APLICAR con color de éxito); si ya estaba en edición, en su lugar llama a `saveRateGroup` para guardar.'
            ),
            "saveRateGroup": (
                '💡 LA IDEA: Es el guardado puntual de las tarifas de una sola categoría de vehículo (por ejemplo, solo motos).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ajustar precios específicos sin alterar las tarifas de los demás tipos de vehículos.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda solo las 5 claves del grupo `type` (elegidas entre autos/motos/camionetas) tras confirmar con resumen; envía cada clave a `/admin/settings/prices`, saltea 30 min vacíos y siempre restaura la UI de solo-lectura al terminar, con toast de éxito o error según la respuesta.'
            ),
            "saveSystemParam": (
                '💡 LA IDEA: Es el guardado de un parámetro suelto del sistema (como tolerancias de tiempo o claves operativas).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite afinar configuraciones individuales de forma inmediata.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda un único parámetro de sistema: lee `cfg-{param}` y lo envía a `/admin/settings/prices?clave=...&valor=...`, notificando éxito o error.'
            ),
            "saveCapacities": (
                '💡 LA IDEA: Es el ajuste de los aforos máximos permitidos en el estacionamiento para autos y motos.\n\n'
                '🎯 POR QUE FUE GENERADA: Fija el límite a partir del cual el sistema avisa que el predio se encuentra completo.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda las capacidades de autos y motos (`cfg-capacidad_total` y `cfg-capacidad_motos`) en dos POST a `/admin/settings/prices`; si falta alguno de los dos valores pide completarlos.'
            ),
            "resetSys": (
                '💡 LA IDEA: Es el disyuntor de reinicio total exclusivo para pruebas escolares que limpia autos y cobros para empezar de nuevo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite vaciar la base de datos de pruebas para realizar una demostración escolar limpia.\n\n'
                '⚙️ FUNCIONAMIENTO: Reinicia el sistema con confirmación (elimina logs de acceso y ocupación): envía POST /system/reset y recarga la página en éxito.'
            ),
            "exportFinanceData": (
                '💡 LA IDEA: Es el botón de exportación a Excel (CSV) de todos los tickets cobrados en el período filtrado.\n\n'
                '🎯 POR QUE FUE GENERADA: Genera planillas contables para balances administrativos y auditorías impositivas.\n\n'
                '⚙️ FUNCIONAMIENTO: Exporta movimientos a CSV: arma los parámetros de consulta (período, fecha específica como rango día completo, tipo de vehículo y método de pago), llama a `GET /reports/payment-history` sin límite, arma el CSV con BOM UTF-8 (fecha, patente, monto, método y tipo) y lo descarga como `reporte_financiero_{sucursal}_{período}_{fecha}.csv` usando la hora virtual del sistema.'
            ),
        },
    },
    "static/js/modules/dashboard-admin-users.js": {
        "proposito": 'CRUD administrativo de usuarios: carga y ordena el directorio por rol, calcula KPIs, pagina y filtra la tabla, y gestiona alta (con modo invitación para admin global), edición con restricciones RBAC por rol (un local_admin solo crea clientes y no cambia roles/sucursales), bloqueo, borrado, cambio de contraseña y selección de sucursales.',
        "simbolos": {
            "loadUsers": (
                '💡 LA IDEA: Es el padrón de usuarios: descarga clientes y empleados ordenándolos por jerarquía y apellido.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite administrar cuentas con los filtros adecuados según el rol de quien está mirando.\n\n'
                "⚙️ FUNCIONAMIENTO: Carga `GET /admin/users`; si el rol actual no es `admin` elimina la opción de filtro 'Administrador General', ordena por jerarquía de rol (admin → local_admin → staff → user) y apellido, y refresca tabla y KPIs. En error pinta una fila de error en la tabla."
            ),
            "updateUserKPIs": (
                '💡 LA IDEA: Es el contador de métricas de personal: muestra el total de usuarios discriminando cuántos son clientes, staff o administradores.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona un resumen numérico rápido del volumen de cuentas en la plataforma.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualiza los cuatro contadores del resumen: total, administradores (admin + local_admin), staff y clientes, formateando con `formatNum`.'
            ),
            "renderUserTable": (
                '💡 LA IDEA: Es la planilla de usuarios con fotos, saldos, puntos y botones de edición, clave, bloqueo y borrado.\n\n'
                '🎯 POR QUE FUE GENERADA: Ofrece una tabla completa e interactiva para gestionar las cuentas del estacionamiento.\n\n'
                "⚙️ FUNCIONAMIENTO: Pinta la tabla de usuarios paginada (10 por página): muestra datos de contacto, badge de rol rotulado con la sucursal, puntos y saldo (solo para clientes; para personal muestra '---') y botones de editar, contraseña, bloquear/desbloquear y eliminar. Actualiza el indicador de página y deshabilita Anterior/Siguiente según corresponda; acepta una lista filtrada alternativa."
            ),
            "filterUserList": (
                '💡 LA IDEA: Es el filtro de búsqueda de usuarios por nombre, apellido, correo, documento o rol.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite hallar la cuenta de cualquier persona en milisegundos sin importar el tamaño del padrón.\n\n'
                '⚙️ FUNCIONAMIENTO: Filtra `allUsersData` por texto (nombre, apellido, email o DNI) y por rol, vuelve a la página 1 y rederiza con el resultado filtrado.'
            ),
            "prevUserPage": (
                '💡 LA IDEA: Es el retroceso a la página anterior de la tabla de usuarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita recorrer listas extensas de clientes de a 10 elementos por pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Retrocede una página si no está en la primera y vuelve a renderizar.'
            ),
            "nextUserPage": (
                '💡 LA IDEA: Es el avance a la página siguiente de la tabla de usuarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene fluida la navegación entre páginas de cuentas registradas.\n\n'
                '⚙️ FUNCIONAMIENTO: Avanza una página si no supera el total y rederiza.'
            ),
            "_applyInviteMode": (
                "💡 LA IDEA: Es el cambio a modo 'invitación': oculta el campo de clave para que el nuevo administrador reciba un correo de activación.\n\n"
                '🎯 POR QUE FUE GENERADA: Garantiza la seguridad en altas ejecutivas permitiendo que cada nuevo administrador cree su propia contraseña privada.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper del modo invitación en el modal de alta: si el checkbox está marcado oculta el grupo de contraseña (lo limpia y lo marca no requerido) y muestra el campo de organización; si no, al revés.'
            ),
            "_setInviteRowVisible": (
                '💡 LA IDEA: Es el interruptor que muestra la opción de invitación únicamente cuando se está dando de alta a un administrador.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita ofrecer invitaciones por correo para cuentas que no requieren ese protocolo de seguridad.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper que muestra/oculta la fila de invitación y su pista; al ocultarla desmarca el checkbox y reaplica el estado con `_applyInviteMode`.'
            ),
            "toggleInviteMode": (
                '💡 LA IDEA: Es el clic sobre la casilla de invitar por correo en el formulario de alta.\n\n'
                '🎯 POR QUE FUE GENERADA: Alterna el formulario entre crear con contraseña manual o enviar invitación por email.\n\n'
                '⚙️ FUNCIONAMIENTO: Punto de entrada del checkbox de invitación: solo delega en `_applyInviteMode`.'
            ),
            "showCreateUserModal": (
                '💡 LA IDEA: Es el formulario de alta de nuevo usuario adaptado a los permisos del operador conectado.\n\n'
                '🎯 POR QUE FUE GENERADA: Cumple con las reglas de jerarquía impidiendo que un empleado cree administradores o usuarios fuera de su sede.\n\n'
                "⚙️ FUNCIONAMIENTO: Prepara el modal de alta según el rol actual: el Admin Global ve los cuatro roles y puede elegir sucursal libremente; un `local_admin` solo ve 'Cliente' y su sucursal queda fija y deshabilitada (regla RBAC: el personal lo da de alta el admin global). Cierra el modo invitación y abre el modal."
            ),
            "toggleBranchSelection": (
                '💡 LA IDEA: Es el selector de sede laboral que se activa solo cuando estás dando de alta a personal de garita o gerentes locales.\n\n'
                '🎯 POR QUE FUE GENERADA: Vincula a los empleados con el estacionamiento en el que prestarán servicio.\n\n'
                '⚙️ FUNCIONAMIENTO: Al cambiar el rol en el alta: muestra la fila de sucursal solo para staff/local_admin (cargando el select con `populateBranchSelect`) y la fila de invitación solo para `admin`; un `local_admin` no alterna nada (rol forzado).'
            ),
            "handleAdminCreateUser": (
                '💡 LA IDEA: Es el guardado formal del nuevo usuario o el despacho de la carta de invitación por correo.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida los requisitos de identidad y registra la cuenta en el sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Submit del alta: arma el payload (nombre, apellido, email, DNI, teléfono fijo y sucursal si aplica) con contraseña si es alta normal u organización si es invitación; envía `POST /admin/users/invite` o `POST /admin/users?rol=...`, maneja errores de validación en formato lista de FastAPI y recarga la lista en éxito. Bloquea el botón durante la petición.'
            ),
            "toggleUserBlock": (
                '💡 LA IDEA: Es el derecho de admisión digital: bloquea o desbloquea una cuenta con confirmación previa.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite suspender temporalmente a infractores o morosos impidiéndoles operar en el estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Bloquea o desbloquea un usuario con confirmación previa vía `POST /admin/users/{id}/toggle-block` y recarga el listado.'
            ),
            "deleteUserAdmin": (
                '💡 LA IDEA: Es la baja definitiva de una cuenta de usuario del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite eliminar usuarios obsoletos o de prueba con todas las precauciones de seguridad.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina un usuario con confirmación vía `POST /admin/users/{id}/delete` y recarga la tabla.'
            ),
            "openPasswordModal": (
                '💡 LA IDEA: Es la ventana de reseteo administrativo de contraseña de un usuario en el mostrador.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ayudar a clientes que olvidaron su clave y no pueden ingresar a su correo.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el modal de cambio de contraseña guardando el id del usuario en un input oculto y rotulando su nombre.'
            ),
            "handleAdminChangePassword": (
                '💡 LA IDEA: Es el guardado cifrado de la nueva contraseña fijada por el administrador.\n\n'
                '🎯 POR QUE FUE GENERADA: Aplica el cambio de clave de forma segura y notifica al titular de la cuenta.\n\n'
                '⚙️ FUNCIONAMIENTO: Submit del cambio de contraseña: envía `POST /admin/users/{id}/password` con `new_password`, cierra el modal y limpia el formulario en éxito; bloquea el botón durante la operación.'
            ),
            "openEditUserModal": (
                '💡 LA IDEA: Es la ficha de edición de datos de una persona (nombre, teléfono, rol o sucursal de trabajo).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite corregir datos personales o ascender empleados respetando las reglas de privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga los datos del usuario (buscado en el cache) en el modal de edición. Para `local_admin` deja el rol y la sucursal fijos y deshabilitados (solo edita datos personales); para el resto habilita los cuatro roles y llena el select de sucursales. Llama a `toggleEditBranchSelection` para sincronizar la fila de sucursal según el rol del usuario.'
            ),
            "toggleEditBranchSelection": (
                '💡 LA IDEA: Es el selector de cambio de sucursal en la edición de empleados de garita.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite trasladar a un empleado a otra sede laboral únicamente si el editor tiene permisos globales.\n\n'
                '⚙️ FUNCIONAMIENTO: En el modal de edición muestra la fila de sucursal solo si el rol del usuario es staff o local_admin, poblando el select salvo que el editor sea un `local_admin` (que no debe cambiar de sede).'
            ),
            "handleAdminEditUser": (
                '💡 LA IDEA: Es el guardado de las modificaciones de un usuario hacia la base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Actualiza el perfil de la persona y refresca la tabla al instante.\n\n'
                '⚙️ FUNCIONAMIENTO: Submit de la edición: envía `PATCH /admin/users/{id}` con datos personales, incluye `rol` solo si el editor no es `local_admin` (RBAC) y `sucursal` solo para staff/local_admin; recarga la lista en éxito y bloquea el botón durante la petición.'
            ),
        },
    },
    "static/js/modules/dashboard-admin.js": {
        "proposito": (
            "💡 LA IDEA: Es el distribuidor mayorista del área de administración. Actúa como una compuerta única que agrupa y ofrece todos los servicios internos del panel administrativo para que quien los necesite no tenga que buscar archivo por archivo.\n\n"
            "🎯 POR QUE FUE GENERADA: En la arquitectura modular de software, cuando un área crece mucho se subdivide en carpetas y archivos especializados (gestión de usuarios, configuración de sucursales, parámetros generales). Si el archivo principal tuviera que importar 30 archivos individuales, el código se volvería caótico e inmanejable. Este archivo implementa el patrón 'Fachada' reuniéndolo todo en un solo paquete prolijo.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Reexporta de forma íntegra (`export *`) los submódulos de gestión de usuarios (`dashboard-admin-users.js`). 2. Reexporta las operaciones de sucursales y niveles (`dashboard-admin-branches.js`). 3. Reexporta las herramientas de configuración del sistema (`dashboard-admin-settings.js`). De esta manera, `dashboard.js` sólo necesita escribir un único import para disponer de todas las funciones de administración."
        ),
        "simbolos": {
        },
    },
    "static/js/modules/dashboard-cameras.js": {
        "proposito": 'Administración de cámaras IP del sistema de monitoreo: normaliza las fuentes de video (IP suelta a URL `http://ip:puerto/video` y viceversa), lista las cámaras en tarjetas con estado online/offline, reordenamiento por drag & drop, menú de acciones, y su alta/edición/borrado y control de arranque/parada del servicio de visión.',
        "simbolos": {
            "buildCameraSource": (
                '💡 LA IDEA: Es el traductor de direcciones de cámara: convierte una simple IP tipeada en una dirección oficial de streaming de video.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el usuario tenga que acordarse de escribir protocolos o puertos complicados al conectar una cámara.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte lo que el usuario escribe en fuente válida: si es una IP con puerto opcional arma `http://{ip}:{puerto|8080}/video`; si ya es una URL completa o vacía la devuelve sin tocar.'
            ),
            "cameraSourceToInput": (
                '💡 LA IDEA: Es el simplificador visual que muestra solo la IP en el formulario para que sea fácil de leer y editar.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpia la vista del operador ocultando detalles técnicos innecesarios en el campo de texto.\n\n'
                '⚙️ FUNCIONAMIENTO: Inverso de `buildCameraSource`: de una URL `http(s)://host[:puerto]/video` extrae `host` o `host:puerto` para mostrarla en el input (omite el puerto 8080 por ser el default); otras cadenas pasan sin cambios.'
            ),
            "loadCameraSettings": (
                '💡 LA IDEA: Es la búsqueda de todas las cámaras IP configuradas con sus estados de conexión en vivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite supervisar qué cámaras están trabajando y cuáles están desconectadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga `GET /system/cameras` mostrando un spinner en la lista y delega el render en `renderCameraSettingsTable`; en error pinta el mensaje en la lista.'
            ),
            "renderCameraSettingsTable": (
                '💡 LA IDEA: Es el mosaico de tarjetas de cámaras con sus nombres, cucardas ONLINE/OFFLINE y botones de acción.\n\n'
                '🎯 POR QUE FUE GENERADA: Presenta el parque de cámaras de forma moderna y permite arrastrarlas para reorganizar el orden en pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Pinta una tarjeta por cámara con nombre, badge ONLINE/OFFLINE según `is_running` y la fuente abreviada; con lista vacía muestra un estado placeholder. Conecta el menú de acciones (editar/eliminar) vía `enableActionMenu` y el reordenamiento por drag vía `enableDragSort`, cuyo callback es `saveCameraOrder`.'
            ),
            "saveCameraOrder": (
                '💡 LA IDEA: Es el guardado del nuevo orden de cámaras tras haberlas arrastrado con el mouse.\n\n'
                '🎯 POR QUE FUE GENERADA: Fija la disposición preferida por los operadores para que las cámaras principales aparezcan siempre primero.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el nuevo orden tras un drag: extrae los ids válidos de los elementos y los envía con `PUT /system/cameras/order`; si falla notifica y recarga la lista para restaurar el orden anterior.'
            ),
            "showCreateCameraModal": (
                '💡 LA IDEA: Es la ficha de instalación para dar de alta una nueva cámara indicando su ubicación y función (entrada, salida, QR).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite sumar puntos de reconocimiento de patentes a la red de estacionamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Prepara el modal en modo alta: limpia el formulario y el id de edición, y según el rol configura la sucursal: el `admin` puede elegir entre todas las sedes (o GLOBAL) con campo obligatorio, el resto queda fijado a su sucursal y oculto.'
            ),
            "showEditCameraModal": (
                '💡 LA IDEA: Es el editor de configuración de una cámara instalada para cambiar su IP o su nombre.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita mantener al día la configuración de video cuando se sustituye un equipo dañado.\n\n'
                '⚙️ FUNCIONAMIENTO: Prepara el modal en modo edición con los datos de la cámara (nombre con `toTitle`, tipo, fuente abreviada, sucursal y estado activo), con la misma lógica de visibilidad de sucursal por rol que en alta.'
            ),
            "handleSaveCameraConfig": (
                '💡 LA IDEA: Es el guardado definitivo de la cámara en el sistema, conectando la dirección de video con el motor de visión artificial.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida los parámetros de red y actualiza el servicio de lectura de patentes.\n\n'
                '⚙️ FUNCIONAMIENTO: Submit del formulario de cámara: arma `{nombre, tipo, source, sucursal, activa}` (la fuente se normaliza con `buildCameraSource`) y envía `PUT /system/cameras/{id}` si hay edición o `POST /system/cameras` si es alta; recarga la lista en éxito y bloquea el botón durante la petición.'
            ),
            "deleteCamera": (
                '💡 LA IDEA: Es la desinstalación de una cámara apagando su proceso de reconocimiento y quitándola del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina cámaras dadas de baja asegurándose de detener sus programas asociados para no consumir CPU.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina una cámara con confirmación (avisa que se detiene el proceso de lectura) vía `DELETE /system/cameras/{id}` y recarga la lista.'
            ),
            "toggleDynamicCameraService": (
                '💡 LA IDEA: Es el botón de arranque o parada del motor de inteligencia artificial de una cámara puntual.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite reiniciar el servicio de lectura ante bloqueos de video o tareas de mantenimiento en la barrera.\n\n'
                "⚙️ FUNCIONAMIENTO: Arranca o detiene el servicio de una cámara: muestra 'INICIANDO.../DETENIENDO...' en su badge, envía `POST /system/cameras/{id}/control/{start|stop}` y recarga la lista tanto en éxito como en error."
            ),
        },
    },
}
