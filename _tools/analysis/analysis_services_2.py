"""Explicaciones analizadas de services (parte 2 de 2, análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "services/occupancy_service.py": {
        "proposito": 'Consolida el estado de ocupación de cada sucursal para los dashboards: plazas por tipo de vehículo (planta baja + pisos), reservas vigentes que ocupan plaza exclusiva y lista de vehículos en el predio con su deuda calculada en vivo, todo con queries agrupadas para evitar N+1.',
        "simbolos": {
            "OccupancyService": (
                '💡 LA IDEA: Es el supervisor que cuenta los autos del estacionamiento: suma los lugares de la planta baja y de todos los pisos, cuenta las reservas vigentes y calcula cuánto debe cada auto estacionado.\n\n'
                "🎯 POR QUE FUE GENERADA: Evita el problema del 'N+1' (hacer cientos de consultas lentas a la base de datos) al agrupar la información en consultas relacionales rápidas.\n\n"
                '⚙️ FUNCIONAMIENTO: Servicio estático de ocupación y disponibilidad: cruza aforos (ParkingAforo), pisos de la sucursal, reservas pagadas vigentes y access_logs para producir los números que ven el dashboard público y el panel administrativo.'
            ),
            "ocupacion_reservas_vigentes": (
                '💡 LA IDEA: Cuenta cuántos turnos reservados están vigentes ahora mismo para reservarles el lugar físico antes de que lleguen.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que un auto que llega sin reserva ocupe el lugar de alguien que ya pagó su turno por adelantado.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuenta reservas pagadas cuyo horario contiene el momento actual (activas o pendientes) agrupadas por tipo de vehículo (autos/motos/camionetas) para descontarles la plaza exclusiva al dashboard sin depender del ALPR; consulta ReservationRepository.get_paid_current_by_sucursal con TimeService.now_str y, ante cualquier error, devuelve ceros en lugar de cortar el dashboard.'
            ),
            "default_capacities": (
                '💡 LA IDEA: Es el salvavidas numérico: entrega números razonables por defecto (20 autos, 10 motos, 5 camionetas) si una sucursal nueva no cargó sus límites.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que la pantalla se rompa o muestre errores en blanco en playas recién inauguradas.\n\n'
                '⚙️ FUNCIONAMIENTO: Diccionario de capacidades por defecto cuando no hay aforo ni sucursal: 20 autos, 10 motos, 5 camionetas, cero reservas, con ocupación en cero y disponibilidad igual a la capacidad; sirve como fallback para no romper la UI.'
            ),
            "capacities_from_aforo": (
                '💡 LA IDEA: Traduce la fila de la base de datos a un formato limpio y entendible para el navegador web.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege al sistema contra campos faltantes en bases de datos antiguas.\n\n'
                '⚙️ FUNCIONAMIENTO: Traduce un registro ParkingAforo al diccionario de capacidad/ocupación/disponibilidad que consume el front, leyendo cada campo con getattr para tolerar aforos viejos sin columnas nuevas; las disponibilidades de reserva se recortan en cero con max(0, ...).'
            ),
            "branch_by_normalized_name": (
                '💡 LA IDEA: Busca una sucursal reconociendo su nombre sin importar mayúsculas o acentos.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita desajustes de aforo por diferencias ortográficas.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la sucursal cuyo nombre normalizado coincide con el recibido (recorre BranchRepository.get_all comparando normalize_name), o None si no hay match.'
            ),
            "aforo_by_normalized_name": (
                '💡 LA IDEA: Es el rastreador de capacidad por nombre normalizado.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite asociar el aforo a la sucursal correcta cuando los nombres difieren en detalles mínimos.\n\n'
                '⚙️ FUNCIONAMIENTO: Igual que el anterior pero sobre los registros de aforo (BranchRepository.get_all_aforos), comparando el campo sucursal normalizado; es el fallback cuando el aforo no se encuentra por nombre exacto.'
            ),
            "calculate_branch_capacities": (
                "💡 LA IDEA: Es el consolidado final: suma planta baja, pisos y reservas para decir: 'Quedan 12 autos, 4 motos y 2 camionetas libres'.\n\n"
                '🎯 POR QUE FUE GENERADA: Alimenta los carteles digitales de entrada y el mapa web con datos 100% exactos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cálculo unificado de capacidad y ocupación de una sucursal: busca el aforo de planta baja (por nombre exacto y luego normalizado), suma las capacidades y ocupaciones de los pisos elevados por tipo, y recién entonces superpone las reservas vigentes (ocupacion_reservas_vigentes) tomando el máximo entre lo que dice el aforo y lo que dicen las reservas reales. Devuelve el diccionario completo con capacidades, ocupaciones y disponibilidades recortadas en cero; si no hay aforo aplica defaults (20 autos, 10 motos, 5 camionetas, 5/3/2 plazas de reserva).'
            ),
            "current_occupancy": (
                '💡 LA IDEA: Es la planilla de autos adentro: lista cada patente estacionada, su hora de llegada, si ya pagó y cuánta plata debe si se va ahora.\n\n'
                '🎯 POR QUE FUE GENERADA: Da al cajero y al guardia la información exacta para cobrar o verificar estadías en curso.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista de vehículos actualmente en el patio con su deuda: primero trae la última entrada sin salida por patente (AccessRepository.get_current_entries, acotada a sucursal u organización), descarta las que ya tienen salida posterior, precarga reservas y tarifas horarias en dos queries planas y calcula la deuda por vehículo. Reglas: con reserva pagada vigente la deuda es 0; si la reserva venció o se completó cobra solo el tiempo extra contra lo ya pagado; si nunca pagó debe el monto de la reserva más el extra; sin reserva, los primeros 10 minutos son cortesía y después acumula según tarifa (BillingService.hourly_amount_from_rates). Devuelve filas con patente, tipo, ingreso, deuda, ya_pago, en_cortesia, datos de reserva, sucursal y piso.'
            ),
        },
    },
    "services/organization_service.py": {
        "proposito": 'Alta y consulta de organizaciones (multi-tenant): cada Admin General administra una empresa aislada y solo la organización marcada como principal es la visible en el sitio público.',
        "simbolos": {
            "OrganizationService": (
                '💡 LA IDEA: Es el administrador de empresas: gestiona las compañías que operan dentro de la red de AUTOPASS.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura la separación total entre empresas dentro de la misma plataforma.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio estático con las operaciones básicas sobre models.Organization; centraliza el acceso para que el resto del código no consulte la tabla directamente.'
            ),
            "get_principal": (
                '💡 LA IDEA: Busca a la empresa dueña principal de la red, que es la que se muestra en la web pública.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el público general se registre en la empresa madre de la plataforma.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la organización con es_principal == True (la del sitio público), o None si no existe todavía.'
            ),
            "get_by_id": (
                '💡 LA IDEA: Busca los datos de una empresa por su código numérico.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita errores de base de datos si el código viene vacío.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca una organización por id; con id None devuelve None sin consultar, evitando filtros raros en la BD.'
            ),
            "get_by_nombre": (
                '💡 LA IDEA: Busca una empresa por su razón social o nombre exacto.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite validar que no se creen dos empresas con el mismo nombre.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la primera organización cuyo nombre coincide exactamente con el recibido, o None.'
            ),
            "create": (
                '💡 LA IDEA: Da de alta una nueva empresa en el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite incorporar nuevas cadenas de estacionamiento como clientes de la plataforma.\n\n'
                '⚙️ FUNCIONAMIENTO: Da de alta una organización nueva activa (y opcionalmente principal); con commit=True hace commit y refresh y devuelve la entidad, con commit=False solo hace flush para encadenarla en una transacción más grande (la usa invite_admin).'
            ),
            "get_or_create_principal": (
                "💡 LA IDEA: Crea la empresa principal 'AUTOPASS' si la base de datos está totalmente vacía.\n\n"
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema siempre tenga una empresa válida al arrancar desde cero.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la organización principal buscando primero por es_principal y luego por el nombre AUTOPASS (PRINCIPAL_NOMBRE); si no existe ninguna crea la organización AUTOPASS como principal y la devuelve. Es el punto de partida al que se asignan los datos cuando aún no hay organización cargada.'
            ),
        },
    },
    "services/payments.py": {
        "proposito": 'Ciclo de vida del dinero de una reserva: abono manual de caja, abono con saldo del usuario, pago confirmado por Mercado Pago, descuentos por canje de puntos (tickets de redención) y cancelación con reembolso proporcional, incluyendo la simulación previa.',
        "simbolos": {
            "ReservationPaymentsMixin": (
                '💡 LA IDEA: Es la caja registradora de reservas: maneja cobros en efectivo, cobros con saldo virtual, Mercado Pago y devoluciones de dinero.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita duplicar la lógica de cobro en múltiples archivos de reservas.\n\n'
                '⚙️ FUNCIONAMIENTO: Mixin de métodos estáticos del que hereda ReservationService: agrupa todas las operaciones de pago, descuento y reembolso de reservas para que el servicio de reservas las exponga como propias sin duplicar lógica.'
            ),
            "get_available_redemption_discounts": (
                '💡 LA IDEA: Busca qué cupones de descuento tiene el cliente en su billetera que sirvan para esta sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el cajero aplique el descuento de puntos directamente en el mostrador.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista los tickets de descuento por canje (%) vigentes de un usuario y aplicables a una sucursal (RedemptionRepository.list_discounts_by_user); devuelve lista vacía si no hay user_id. Se usa en caja para detectar qué descuento corresponde aplicar al cobrar.'
            ),
            "pay_reservation_manual": (
                '💡 LA IDEA: Registra el cobro en efectivo en la cabina: aplica cupones, descuenta la plata y premia al cliente con puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite despachar a clientes que pagan en mano sin pasar por internet.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca una reserva como pagada desde caja sin tocar saldo ni Mercado Pago. Si ya estaba pagada devuelve ok sin hacer nada. Con redemption_ticket_id valida el ticket (validate_redemption_ticket, 400 si no corresponde), calcula el descuento % sobre el monto_total, conserva el total base en monto_calculado (foto de precio), baja monto_total al valor cobrado, marca el ticket USADO y, si hay usuario, acredita puntos (BillingService.calculate_points) con PointsLog y notificación POINTS_EARNED. Pone estado_pago PAGADO, estado_reserva ACTIVA, hace commit y devuelve monto, monto_a_cobrar, descuento y método.'
            ),
            "redemption_sucursal_clause": (
                '💡 LA IDEA: Verifica que el cupón de descuento pertenezca a la sucursal donde se está cobrando.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita fraudes con cupones emitidos para otras sucursales.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la cláusula SQL de filtrado de tickets de canje por sucursal delegando en RedemptionRepository.redemption_sucursal_clause; expone la lógica del repositorio para quien necesite combinarla en otras consultas.'
            ),
            "validate_redemption_ticket": (
                '💡 LA IDEA: Es el control de autenticidad del cupón: revisa que no haya sido usado antes y que pertenezca al usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide usar dos veces el mismo cupón de descuento.\n\n'
                '⚙️ FUNCIONAMIENTO: Valida que el ticket de canje exista, esté vigente, pertenezca al usuario y sea compatible con la sucursal (RedemptionRepository.get_valid_discount); si no pasa devuelve HTTPException 400, y si no se envió id devuelve None.'
            ),
            "pay_reservation": (
                '💡 LA IDEA: Cobra la reserva debitando dinero de la billetera virtual del cliente y le manda el comprobante por email.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite pagar reservas al instante con el saldo prepago cargado en la cuenta.\n\n'
                '⚙️ FUNCIONAMIENTO: Abona una reserva con el saldo del usuario. Busca la reserva por usuario e id (404 si no existe), rechaza si está cancelada/completada (400) y devuelve ok si ya estaba pagada. Aplica descuento por canje si se envió (foto de precio en monto_calculado y descuento_pct), valida saldo suficiente (400 si falta), descuenta el saldo, pone PAGADO/ACTIVA con método SALDO, acredita puntos sobre lo efectivamente abonado, marca el ticket USADO, hace commit, envía el mail de confirmación (EmailService) y crea notificaciones RESERVATION_CONFIRMED y POINTS_EARNED. Devuelve status, mensaje y puntos ganados.'
            ),
            "pay_reservation_mp": (
                '💡 LA IDEA: Confirma la reserva cuando Mercado Pago avisa que la tarjeta de crédito pasó con éxito.\n\n'
                '🎯 POR QUE FUE GENERADA: Activa el turno y genera el QR de acceso sin tocar el saldo particular del cliente.\n\n'
                '⚙️ FUNCIONAMIENTO: Confirma una reserva como pagada por Mercado Pago Checkout Pro: el monto ya viene confirmado de MP con el descuento aplicado, así que no descuenta saldo. Rechaza reservas canceladas/completadas (400) y devuelve aplicado=False si ya estaba pagada. Valida y consume el ticket de canje si correspondió (foto de precio), pone PAGADO/ACTIVA con método MERCADOPAGO, acredita puntos, commit, mail de confirmación y notificaciones in-app.'
            ),
            "simulate_refund": (
                '💡 LA IDEA: Es la calculadora de devolución: calcula cuánta plata corresponde devolverle al cliente antes de cancelar.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra al cliente cuánto dinero recuperará antes de que confirme la cancelación.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula el reembolso potencial de una reserva sin ejecutar nada. Primero verifica presencia física: si hay entrada sin salida posterior en la sede devuelve reembolso 0 con error Vehículo en el predio. Si la reserva no está pagada devuelve 0. Con pago: antes del inicio reembolsa el total, después del fin 0, y dentro del rango devuelve la proporción del tiempo que falta (0 si es estadía por hora con vehículo ya ingresado). Devuelve {reembolso, error}.'
            ),
            "cancel_reservation": (
                '💡 LA IDEA: Cancela la reserva, devuelve la plata al saldo del usuario y ajusta los puntos de regalo otorgados.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario cancelar su turno de forma transparente y justa según el tiempo restante.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancela una reserva y ejecuta el reembolso: 404 si no existe, ok si ya estaba cancelada y status error si ya finalizó. Usa simulate_refund para el monto y, si hay error de presencia física, lanza 400. Si hay monto acredita el saldo, descuenta los puntos correspondientes (nunca por debajo de cero) con PointsLog negativo, pone estado CANCELADA y pago REEMBOLSADO (o CANCELADO si no hubo reembolso), registra monto_reembolsado, hace commit y notifica RESERVATION_CANCELLED. Devuelve mensaje y monto reembolsado.'
            ),
        },
    },
    "services/report_service.py": {
        "proposito": 'Inteligencia de negocio: resúmenes financieros (recaudación, reembolsos, tasas de cancelación, deuda proyectada, desglose por método y por sede), historial unificado de pagos, auditoría de accesos ALPR con usuario asociado, estadísticas y serie OCR, métricas horarias de tráfico, mapa de calor diario y ocupación de reservas vs capacidad con KPIs de no-show.',
        "simbolos": {
            "get_date_range": (
                "💡 LA IDEA: Convierte palabras como 'hoy', 'esta semana' o 'este mes' en fechas exactas de calendario.\n\n"
                '🎯 POR QUE FUE GENERADA: Estandariza los filtros de tiempo en todos los reportes de la empresa.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte un periodo (day/week/month/year o total) en el par (start_date, end_date) en ISO: si se pasa start/end explícitos se respetan; si no, calcula el inicio del día, de la semana (desde el lunes), del mes o del año según el periodo. Se usa como filtro de todos los reportes.'
            ),
            "_parse": (
                '💡 LA IDEA: Intérprete de fechas flexible que descarta datos corruptos sin voltear el reporte.\n\n'
                '🎯 POR QUE FUE GENERADA: Aumenta la robustez de los informes ante registros antiguos o con formatos raros.\n\n'
                '⚙️ FUNCIONAMIENTO: Parsea un timestamp flexible (ISO con T, con o sin segundos/microsegundos) con models.types.parse_fecha; devuelve None si está vacío o no se puede interpretar, para que los reportes descarten filas corruptas sin romperse.'
            ),
            "_boundary": (
                '💡 LA IDEA: Ajusta las fechas al primer segundo del día (00:00:00) o al último segundo de la noche (23:59:59).\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que queden afuera autos que salieron a última hora del día.\n\n'
                '⚙️ FUNCIONAMIENTO: Normaliza un borde de rango (YYYY-MM-DD o timestamp) a inicio (00:00:00) o fin (23:59:59) de día según is_end, y lo parsea con _parse; devuelve None si no hay valor.'
            ),
            "ReportService": (
                '💡 LA IDEA: Es el departamento de finanzas y analítica: prepara balances contables, mapas de calor y métricas operativas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la confidencialidad de datos asegurando que cada gerente solo vea los números de su sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio de reportes y analítica: resuelve permisos por rol (ADMIN global ve toda la red y su organización, LOCAL_ADMIN siempre su sucursal), arma los filtros de rango/tipo de vehículo/método de pago y delega los agregados en ReportRepository.'
            ),
            "get_financial_summary": (
                '💡 LA IDEA: Es el balance general de facturación: cuánto dinero entró, cuánto se reembolsó y cuánto se proyecta cobrar.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda al directorio la foto económica del negocio en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Puerta de entrada del resumen de recaudación: determina si el usuario es ADMIN global para acotar por sucursal y organización, llama a _financial_summary_core y, si el admin global pidió sin filtro de sucursal, agrega el desglose por_sucursal vía _financial_summary_by_branch.'
            ),
            "_financial_summary_core": (
                '💡 LA IDEA: Es el motor matemático que suma cobros de barrera, cobros de reservas y resta reembolsos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza cálculos contables consistentes en todas las vistas financieras.\n\n'
                '⚙️ FUNCIONAMIENTO: Núcleo del cálculo financiero para una sede (o toda la red con sucursal None): suma recaudación de estadías ALPR (paid_logs_aggregate, desglosando efectivo/digital según el método pedido), reservas pagadas menos reembolsos (neto nunca negativo), tasa de cancelación y de ingresos por incumplimiento (canceladas sin reembolso o con reembolso parcial), deuda proyectada de los vehículos sin pagar en el patio (unpaid_entries_without_exit + BillingService.calculate_hourly_amount) y el desglose por método de pago agrupando logs, reservas y reembolsos con canonicalización de variantes. Devuelve totales, ticket promedio, desglose de estadías/reservas y lista de métodos con saldo distinto de cero.'
            ),
            "_financial_summary_by_branch": (
                '💡 LA IDEA: Es el ranking de sucursales: compara qué playa recauda más dinero y cuál tiene más movimientos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite evaluar la rentabilidad individual de cada playa de estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Recorre las sedes activas de la organización (o todas) y llama a _financial_summary_core por cada una, quedándose con sucursal, total recaudado, cantidad de pagos, ticket promedio, efectivo, digital y reembolsado; devuelve las filas ordenadas de mayor a menor recaudación.'
            ),
            "get_payment_history": (
                '💡 LA IDEA: Es el extracto bancario de la empresa: lista cada peso que entró o salió con fecha, patente y método.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita auditorías contables y resolución de discrepancias en caja.\n\n'
                '⚙️ FUNCIONAMIENTO: Historial paginado unificado de pagos (estadías, reservas y reembolsos) acotado por rol: el LOCAL_ADMIN solo ve su sucursal, el ADMIN global toda su organización; calcula offset con page/limit y delega en ReportRepository.payment_history, devolviendo filas con id, fecha, patente, monto, tipo y método.'
            ),
            "get_access_logs": (
                '💡 LA IDEA: Es el libro de entradas y salidas enriquecido con el nombre del titular de cada auto.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber quién conducía el vehículo registrado por la cámara de seguridad.\n\n'
                '⚙️ FUNCIONAMIENTO: Historial de accesos ALPR (hasta limit, por defecto 300) filtrado por sucursal/rol y patente opcional, y enriquecido con el dueño del vehículo: normaliza las patentes de los logs, busca los vehículos correspondientes (VehicleRepository.get_by_normalized_patentes) y sus usuarios en dos queries, y agrega por cada fila usuario (nombre y apellido o email), es_registrado y todas las columnas de la tabla.'
            ),
            "get_ocr_stats": (
                '💡 LA IDEA: Es el velocímetro de la inteligencia artificial: mide el promedio de milisegundos que tarda la lectura de patentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite detectar cámaras lentas o descalibradas antes de que causen demoras en la barrera.\n\n'
                '⚙️ FUNCIONAMIENTO: Estadísticas de tiempos de procesamiento OCR sobre los últimos limit logs con OCR: devuelve la lista de logs (id, patente, evento, fecha, ocr_time redondeado a 3 decimales, sucursal) y el resumen count/avg/min/max/p90; sin datos devuelve un diccionario vacío en ceros.'
            ),
            "get_ocr_activity": (
                '💡 LA IDEA: Es la línea de tiempo de lecturas para el gráfico móvil de rendimiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite observar la evolución de la precisión del OCR a lo largo del día.\n\n'
                '⚙️ FUNCIONAMIENTO: Serie cronológica completa (ascendente, sin límite) de tiempos OCR para el gráfico móvil: lista de puntos con fecha, patente, sucursal y evento, más count, primera y última fecha.'
            ),
            "get_access_activity": (
                '💡 LA IDEA: Es el gráfico de ritmo cardíaco del estacionamiento: muestra picos de entradas y salidas hora por hora.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite planificar refuerzos de personal en las horas de mayor movimiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Serie horaria continua de accesos ENTRADA/SALIDA desde el primer registro hasta la hora actual (o el rango desde/hasta pedido, con bordes normalizados por _boundary): agrupa los eventos por hora, y si desde > hasta devuelve vacío. Recorre hora por hora completando huecos con cero para que el gráfico sea deslizable, y devuelve buckets con label, entradas, salidas y totales globales.'
            ),
            "_open_hours_de": (
                '💡 LA IDEA: Deduce los horarios de apertura y cierre de las playas seleccionadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que los gráficos solo muestren las horas en que el negocio estuvo efectivamente abierto.\n\n'
                '⚙️ FUNCIONAMIENTO: Resuelve el rango de horas de apertura (apertura, cierre) de las sedes seleccionadas: parsea el horario con regex admite formatos como 07:00 a 23:00 o 07:00 UN 23:00, trata sedes 24h o horarios ilegibles como (0, 23), convierte cierre 00 en 23 y devuelve el mínimo de aperturas y el máximo de cierres (union de todas las sedes si sucursal es None).'
            ),
            "get_traffic_heatmap": (
                '💡 LA IDEA: Es el mapa de calor: pinta de rojo los días y horas más congestionados y de verde los más tranquilos.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a diseñar promociones para llenar el estacionamiento en horarios muertos.\n\n'
                '⚙️ FUNCIONAMIENTO: Mapa de calor de tráfico: columnas = días del mes del rango (agrupados por mes con etiquetas en español), filas = horas de apertura resueltas con _open_hours_de, contando solo ENTRADAS. Determina el rango (si no se pasa, desde la primera entrada hasta hoy, y lo ordena si está invertido), arma la matriz, excluye entradas fuera del horario y devuelve labels, días, meses, matrix, totales por día/hora, total, máximo, sucursal y flag is_24h.'
            ),
            "get_occupancy_summary": (
                '💡 LA IDEA: Mide el porcentaje de ocupación y la tasa de clientes que faltaron a su turno (no-show).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ajustar la cantidad de cocheras reservadas para maximizar la ganancia.\n\n'
                '⚙️ FUNCIONAMIENTO: Ocupación de reservas vs capacidad por hora del día (promedio del rango) más KPIs: pagadas/pendientes/canceladas/activas, tasas de pago y cancelación, monto pagado, ticket promedio y no-show (reservas pagadas vencidas sin evento ENTRADA ALPR de esa patente dentro de su rango, cruzando entrance_patent_events). Para cada tipo de vehículo calcula la serie de ocupación absoluta por hora, la promedia sobre los días del rango y la expresa como porcentaje topeado en 100 contra la capacidad de reservas (capacidad_reservas de availability).'
            ),
        },
    },
    "services/reservation_service.py": {
        "proposito": 'Servicio central de reservas: crea, modifica, lista y cancela reservas de clientes y administración aplicando validaciones de cotización cliente-servidor (409), disponibilidad, horarios de sucursal, límites por usuario, snapshots de tarifa y ajustes de saldo/puntos, heredando los métodos de pago del mixin de payments.',
        "simbolos": {
            "ReservationService": (
                '💡 LA IDEA: Es el director de reservas: gobierna la creación, modificación, cobro y cancelación de turnos.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que ninguna reserva se cree sin verificar cupos, horarios y cotizaciones.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase que hereda ReservationPaymentsMixin y concentra todo el ciclo de vida de las reservas. Sus constantes COTIZACION_HORAS_TOLERANCIA (0.02 h ≈ 1 min) y COTIZACION_MONTO_TOLERANCIA (0.01) fijan la tolerancia con la que se compara lo que cotizó el front contra lo que recalcula el servidor.'
            ),
            "_validar_cotizacion": (
                '💡 LA IDEA: Es el detector de trampas en el precio: revisa que lo que el usuario vio en su pantalla coincida exactamente con la tarifa real.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que usuarios malintencionados alteren el código del navegador para pagar de menos.\n\n'
                '⚙️ FUNCIONAMIENTO: Control de integridad de precios: si el front envió horas_calculadas o monto_calculado y difieren del cálculo del servidor por más de las tolerancias (1 minuto de duración o 1 centavo), lanza HTTPException 409 pidiendo volver a cotizar (tarifario desactualizado o cálculo alterado). Si el front no envió los valores (None) no valida, por compatibilidad.'
            ),
            "_preferir_cliente": (
                '💡 LA IDEA: Respeta el valor cotizado al cliente una vez que fue validado por el servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene la coherencia entre lo que vio el usuario y lo que se guarda en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el valor que envió el front si está informado, si no el que calculó el servidor; se usa para persistir el snapshot de tarifas respetando lo cotizado una vez validado.'
            ),
            "_fijar_snapshot_tarifa": (
                '💡 LA IDEA: Es el congelador de precios: estampa la tarifa del día en la reserva para siempre.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que un aumento futuro de tarifas no afecte a turnos ya contratados.\n\n'
                '⚙️ FUNCIONAMIENTO: Persiste en la reserva la foto de la cotización: llama a BillingService.snapshot_tarifas y guarda tarifa_hora, tarifa_fraccion y tarifa_aplicada (priorizando las del front con _preferir_cliente), las horas y el monto cotizados, el descuento_pct si corresponde y la marca tarifa_fijada_en con TimeService.now_str. Así el historial conserva el precio con el que se vendió aunque la tarifa cambie después.'
            ),
            "create_reservation": (
                '💡 LA IDEA: Registra una reserva manual cargada por el empleado desde el panel de control.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite agendar turnos tomados por teléfono o presencialmente.\n\n'
                '⚙️ FUNCIONAMIENTO: Alta manual desde el panel admin: resuelve el tipo de vehículo (del dato o del vehículo por patente), calcula el monto con BillingService.calculate_total_amount (409 si la sucursal no tiene tarifario), recalcula la duración y valida la cotización del front (_validar_cotizacion, 409 si difiere), toma la dirección de la sede (BranchService) y crea la reserva PENDIENTE con origen manual y snapshot de tarifa. Hace commit, notifica el cambio de ocupación al dashboard y devuelve la entidad.'
            ),
            "cleanup_overdue_reservations": (
                '💡 LA IDEA: Es el limpiador de reservas abandonadas: cancela turnos impagos que ya pasaron de hora.\n\n'
                '🎯 POR QUE FUE GENERADA: Devuelve las cocheras bloqueadas al público general.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancela reservas impagas cuyo inicio pasó hace más de 2 horas (margen de gracia con TimeService.now): trae las vencidas (ReservationRepository.get_unpaid_overdue), consulta en batch qué ya ingresaron al predio (AccessRepository.get_reserva_ids_with_entry) y no cancela esas; a las demás les pone CANCELADA y pago FALLIDO. Devuelve cuántas canceló (incluye las que se saltaron).'
            ),
            "auto_finalize_reservations": (
                "💡 LA IDEA: Marca como 'Completadas' las reservas vencidas de un usuario al abrir su perfil.\n\n"
                '🎯 POR QUE FUE GENERADA: Mantiene la pantalla del cliente siempre actualizada con estados reales.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca como COMPLETADAS las reservas vencidas de un usuario concreto (ReservationRepository.get_past_reservations con la hora actual) y hace commit; la llama el listado de reservas del usuario para que siempre muestre estados frescos.'
            ),
            "auto_finalize_all_reservations": (
                '💡 LA IDEA: Finaliza todas las reservas vencidas del sistema y avisa a los paneles de control.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene la ocupación del sistema sincronizada sin intervención humana.\n\n'
                '⚙️ FUNCIONAMIENTO: Igual que la anterior pero para todo el sistema (ReservationRepository.get_expired): pone COMPLETADA toda reserva PENDIENTE o ACTIVA cuya fecha_fin ya pasó, y luego notifica a los dashboards de las sucursales afectadas (NotificationService.notify_occupancy_change) para que reflejen la deuda acumulada. Devuelve cuántas finalizó.'
            ),
            "get_en_predio_ids": (
                '💡 LA IDEA: Identifica qué reservas corresponden a autos que ya están adentro del predio.\n\n'
                "🎯 POR QUE FUE GENERADA: Permite pintar una etiqueta verde 'En el predio' en la lista de reservas.\n\n"
                '⚙️ FUNCIONAMIENTO: Devuelve el conjunto de ids de reservas cuyo último evento físico fue una ENTRADA (vehículo dentro del predio), delegando en AccessRepository.get_en_predio_ids; lo usan los listados para marcar en_predio.'
            ),
            "get_reservation_or_404": (
                '💡 LA IDEA: Busca una reserva o devuelve un mensaje de error claro si no existe.\n\n'
                '🎯 POR QUE FUE GENERADA: Frena operaciones sobre turnos inexistentes con códigos HTTP estándar.\n\n'
                '⚙️ FUNCIONAMIENTO: Trae una reserva por id (y opcionalmente por dueño) o lanza HTTPException 404 con detalle Reserva no encontrada.'
            ),
            "get_permissioned_reservation": (
                '💡 LA IDEA: Verifica que el empleado tenga permiso para ver o modificar esa reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que empleados de una sucursal modifiquen turnos de otra sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Obtiene una reserva validando jurisdicción: si el operador no es ADMIN y la sucursal de la reserva no coincide con la suya (same_branch) lanza 403; si es admin pasa sin filtro.'
            ),
            "lookup_patente": (
                '💡 LA IDEA: Es la búsqueda por patente en caja: busca quién es el dueño del auto y sus datos de contacto.\n\n'
                '🎯 POR QUE FUE GENERADA: Acelera la atención en ventanilla asociando al cliente con un solo clic.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca al dueño de una patente para la vinculación manual en caja: la normaliza (solo alfanuméricos, mínimo 4 caracteres) y consulta VehicleRepository.get_by_normalized_patente_with_active_owner; devuelve {encontrado, user_id, nombre, apellido, tipo_vehiculo, marca_modelo} o encontrado False si no hay vehículo con dueño activo.'
            ),
            "get_admin_available_redemptions": (
                '💡 LA IDEA: Consulta qué cupones de descuento tiene el cliente antes de cobrarle en la cabina.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite aplicar bonificaciones ganadas por puntos de forma transparente.\n\n'
                '⚙️ FUNCIONAMIENTO: Descuentos de canje disponibles de un usuario para caja, con validación anti enumeración: si se envía user_id primero verifica que el usuario exista y esté activo (404 si no) y recién entonces lista los descuentos (get_available_redemption_discounts del mixin).'
            ),
            "get_new_reservations_count": (
                '💡 LA IDEA: Es la campanita del panel: cuenta cuántas reservas nuevas entraron en los últimos minutos.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene al personal alertado de nuevos turnos en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Conteo para el polling de novedades del panel admin: para el ADMIN global acota a su organización y para el LOCAL_ADMIN a su sucursal, y llama a ReservationRepository.latest_id_and_count con since_id devolviendo {count, latest_id}.'
            ),
            "validar_horario_sucursal": (
                '💡 LA IDEA: Revisa que el turno solicitado caiga dentro del horario de apertura de la playa.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que los clientes reserven cocheras en horarios donde el portón está cerrado con candado.\n\n'
                '⚙️ FUNCIONAMIENTO: Valida que la estadía caiga dentro del horario de atención de la sucursal: si no hay sede, es 24h, no tiene horario o el formato no matchea la regex H:MM A/UN H:MM no valida; prohíbe cruzar de día (400), exige que el inicio esté dentro del horario y que el fin no exceda el cierre (400 con mensajes personalizados); cierre 00:00 se trata como 23:59.'
            ),
            "validate_manual_vinculacion": (
                '💡 LA IDEA: Comprueba que el auto pertenezca realmente al cliente antes de asignarle el turno.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita confusiones de patentes en reservas cargadas por el personal.\n\n'
                '⚙️ FUNCIONAMIENTO: Para vinculación manual en caja: si hay user_id valida que el usuario exista y esté activo (404) y que la patente normalizada esté entre sus vehículos (400 si no); devuelve (user, vehicle) para que el caller use el tipo de vehículo real.'
            ),
            "create_user_reservation": (
                '💡 LA IDEA: Es el circuito completo de reserva desde la app: valida cuenta, patente, cupo, horarios, calcula el precio y reserva la cochera.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el motor que permite a los clientes reservar su cochera desde el celular en segundos.\n\n'
                '⚙️ FUNCIONAMIENTO: Alta desde la app del cliente con todas las reglas: cuenta bloqueada 403, patente vinculada 400, formato de patente válido 400, máximo 5 reservas PENDIENTE/ACTIVA por usuario 400, sin solape de la patente en la misma sucursal 400, sin solape del usuario en otra sucursal 400, tarifario existente 409, anticipación máxima 90 días 400, para estadía por hora la anticipación mínima settings.RESERVA_HORA_MIN_SEGUNDOS y horario de sucursal, disponibilidad de plaza (verificar_disponibilidad) y duración positiva. Calcula el monto según modalidad (día/semana/quincena/mes con math.ceil de bloques; día con días_semana cuenta solo los días elegidos; hora con calculate_hourly_amount, 409 sin tarifario), valida la cotización del front, crea la reserva PENDIENTE con snapshot de tarifa, notifica ocupación y devuelve {status, monto, estado_pago}.'
            ),
            "modify_user_reservation": (
                '💡 LA IDEA: Permite al cliente cambiar el día, la hora o el auto de su reserva, ajustando la diferencia de dinero.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda total flexibilidad al usuario para reprogramar su turno sin tener que cancelarlo.\n\n'
                '⚙️ FUNCIONAMIENTO: Modificación por el cliente: bloqueo 403, reserva propia 404, no modificable si está COMPLETADA/CANCELADA 400; los campos no enviados mantienen el valor actual. Revalida anticipación máxima, anticipación/horario para hora, disponibilidad (excluyéndose a sí misma) y patente vinculada+válida si cambia. Recalcula el monto con las mismas reglas de modalidad (409 sin tarifario) y valida cotización. Si ya estaba pagada ajusta la diferencia: corrige puntos (con 400 si no alcanzan), debita al saldo si subió (400 si falta saldo) o acredita si bajó; si no estaba pagada la vuelve a PENDIENTE. Actualiza snapshot, notifica RESERVATION_MODIFIED y devuelve {status, monto_total, estado_pago}.'
            ),
            "list_user_reservations": (
                '💡 LA IDEA: Entrega al cliente la lista ordenada de sus reservas activas e históricas.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta la vista principal de turnos en el perfil del usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Listado del cliente: primero ejecuta las tareas de mantenimiento (cleanup_overdue_reservations y auto_finalize_reservations), trae las reservas, marca en_predio con get_en_predio_ids y repara sucursal_info incompleta con BranchService (commit solo si cambió algo y sin romper si falla).'
            ),
            "confirm_reminder": (
                "💡 LA IDEA: Es el botón 'Entendido' del cliente cuando recibe el aviso de que su turno empieza pronto.\n\n"
                '🎯 POR QUE FUE GENERADA: Apaga las alertas de recordatorio y confirma la asistencia del conductor.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca recordatorio_confirmado en True de la reserva (404 si no es del usuario) y pone como leídas las notificaciones de tipo REMINDER_UNPAID de esa reserva; devuelve {status, message}.'
            ),
            "list_admin_reservations": (
                '💡 LA IDEA: Prepara la lista de todas las reservas de la sucursal para la pantalla del personal de playa.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los operadores coordinar el ingreso diario de vehículos.\n\n'
                '⚙️ FUNCIONAMIENTO: Listado administrativo: ejecuta la limpieza de vencidas, filtra por estado/sucursal acotando al staff (LOCAL_ADMIN su sucursal, ADMIN global su organización), consulta ReservationRepository.list_filtered, agrega en_predio por batch y arma respuestas UserReservationResponse enriquecidas con nombre, apellido y email del dueño —o con cliente_nombre si la reserva es sin cuenta, partiendo el nombre en dos—.'
            ),
            "create_admin_reservation": (
                '💡 LA IDEA: Permite al empleado crear y cobrar una reserva en efectivo o tarjeta en el acto.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve reservas espontáneas de clientes que llegan directamente a la entrada.\n\n'
                '⚙️ FUNCIONAMIENTO: Alta desde caja/panel: normaliza y valida la patente (400), al LOCAL_ADMIN le fuerza su sucursal, valida vínculo usuario-patente (validate_manual_vinculacion), fechas ordenadas (400), sin solape en la sucursal (400) y disponibilidad por tipo (400). Crea la reserva vía create_reservation y, si data.pagar, la abona con pay_reservation_manual (aplicando descuento por canje si se envió). Notifica RESERVATION_CREATED_ADMIN al dueño y devuelve id, monto, pagado, método, descuento y monto_a_cobrar; repropaga las HTTPException y convierte otros errores en 400.'
            ),
            "update_admin_reservation": (
                '💡 LA IDEA: Permite al personal administrativo corregir horarios de una reserva y conciliar cobros o reembolsos de caja.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga herramientas al encargado para resolver cambios de planes de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Edición administrativa con conciliación financiera: solo reservas de origen manual (400) y no completadas/canceladas (400); jurisdicción por sucursal (403) y sucursal forzada al LOCAL_ADMIN. Revalida fechas, solape (exclude_id) y disponibilidad. Recalcula el monto (409 sin tarifario), valida la cotización y, si la reserva estaba pagada, recupera el ticket de canje usado para reaplicar el porcentaje al nuevo monto base. Calcula la diferencia contra el valor actual (monto_total menos ya reembolsado) y decide acción: cobro (suma la diferencia, registra método y fecha de pago), reembolso (acumula en monto_reembolsado y, si el método es saldo/digital/billetera, acredita al saldo del usuario y ajusta puntos con PointsLog) o sin cambio. Actualiza todos los campos de la reserva, commit, notifica al usuario según la acción y devuelve {status, monto, monto_anterior, diferencia, accion, metodo_pago, reembolsado_total}; ante error desconocido hace rollback y 400.'
            ),
            "confirm_reservation_payment": (
                "💡 LA IDEA: Es el sello de 'PAGADO' puesto por el empleado cuando recibe el dinero en efectivo.\n\n"
                '🎯 POR QUE FUE GENERADA: Habilita el pase digital del cliente para que la barrera lo deje entrar.\n\n'
                '⚙️ FUNCIONAMIENTO: Confirma el pago de una reserva desde admin: valida jurisdicción (403), toma método (por defecto Caja) y ticket de descuento opcionales, delega en pay_reservation_manual, notifica RESERVATION_CONFIRMED al dueño y devuelve mensaje, monto, descuento y monto_a_cobrar.'
            ),
        },
    },
    "services/support_service.py": {
        "proposito": 'Gestión de tickets de soporte con hilo de mensajes: alta por clientes, listado y detalle para administración con aislamiento multiempresa y por sucursal, respuestas, cambio de estado bloqueado en estados terminales y contador de pendientes para el menú lateral.',
        "simbolos": {
            "SupportService": (
                '💡 LA IDEA: Es la central de atención al cliente: gestiona reclamos, consultas y el chat entre el conductor y el personal.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la atención postventa asegurando que ningún problema quede sin resolver.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio estático de soporte que concentra las reglas de jurisdicción (quién ve qué ticket), la numeración correlativa por sucursal, el hilo de mensajes y las notificaciones a administración. TERMINAL_STATES marca los estados (resuelto/resuelta/cerrado/cancelado) en los que el ticket queda bloqueado.'
            ),
            "_org_branch_ids": (
                '💡 LA IDEA: Obtiene las sucursales de la empresa para acotar los reclamos de soporte.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que los mensajes de ayuda lleguen a los encargados correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve los ids de las sedes de la organización del usuario (None si no tiene organización, manteniendo el comportamiento single-tenant): consulta ParkingBranch por organization_id y se usa para aislar los tickets por empresa.'
            ),
            "_branch_prefix": (
                "💡 LA IDEA: Genera el código del ticket (ej: 'CAST-123' para Castelar).\n\n"
                '🎯 POR QUE FUE GENERADA: Facilita identificar la sucursal del problema a simple vista.\n\n'
                '⚙️ FUNCIONAMIENTO: Prefijo corto de la sucursal para la numeración del ticket (ej. CASTELAR -> CAST): normaliza el nombre, quita espacios y toma 4 caracteres, con fallback GENERAL/GEN.'
            ),
            "_notify_admins": (
                '💡 LA IDEA: Es la notificación de alerta que le llega al encargado cuando un cliente abre un reclamo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura una respuesta rápida del equipo de atención al cliente.\n\n'
                '⚙️ FUNCIONAMIENTO: Notifica por in-app a la administración que debe atender el ticket: parte de todo el staff, lo acota a la organización de la sucursal del ticket (aislamiento multiempresa), filtra por sucursal del ticket (o nombre normalizado si no hay id) sumando siempre a los ADMIN globales, y si no queda nadie avisa a todo el staff. Crea notificaciones SUPPORT_TICKET con UserNotificationService; cualquier error solo se imprime para no cortar el flujo.'
            ),
            "_build_message": (
                '💡 LA IDEA: Da formato al mensaje del chat con su fecha, autor y foto adjunta.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene el hilo de conversación ordenado y legible.\n\n'
                '⚙️ FUNCIONAMIENTO: Construye (sin persistir) un SupportTicketMessage con ticket, autor, texto, adjunto opcional y fecha local; el hilo support_ticket_messages es la única fuente de verdad de la conversación.'
            ),
            "create_ticket": (
                '💡 LA IDEA: Abre una nueva consulta de ayuda en el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cliente pedir ayuda sobre cobros, barreras o extravíos.\n\n'
                '⚙️ FUNCIONAMIENTO: Alta de ticket con estado Pendiente: arma la entidad con sucursal por defecto General y delega la persistencia en SupportRepository.create_ticket pasando una fábrica que crea el primer mensaje con el texto del ticket. Luego notifica a los admins con título y mensaje que incluyen la sucursal y el asunto.'
            ),
            "get_user_tickets": (
                '💡 LA IDEA: Muestra al cliente el estado de sus reclamos anteriores.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario hacer seguimiento de sus consultas.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve los tickets de un usuario delegando en SupportRepository.get_user_tickets.'
            ),
            "get_admin_tickets": (
                '💡 LA IDEA: Es la bandeja de entrada del personal con todos los reclamos pendientes de resolución.\n\n'
                '🎯 POR QUE FUE GENERADA: Organiza el trabajo del equipo de soporte clasificando por sucursal y urgencia.\n\n'
                '⚙️ FUNCIONAMIENTO: Listado admin de tickets con jurisdicción: el LOCAL_ADMIN filtra por sucursal_id (o nombre normalizado si no hay id); el ADMIN global con organización acota a las sedes de su empresa (por filtro de sucursal concreto o todas), y en single-tenant filtra por sucursal, TODAS, General o sin sucursal. Aplica filtro de estado opcional, auto-limpia las notificaciones de tickets ya resueltos o cancelados, precarga en una sola query los mensajes de todos los tickets (evita N+1) y arma filas con número correlativo por sucursal (prefijo-por día), datos del cliente (o Cliente Eliminado), bandera has_unread y el hilo completo con autor e is_admin por mensaje.'
            ),
            "_can_access_ticket": (
                '💡 LA IDEA: Es el control de privacidad: verifica si el empleado tiene autorización para ver ese reclamo.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la información privada de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Regla única de jurisdicción sobre un ticket: ADMIN global ve todos si no tiene organización, si no solo los de sus sedes; el staff compara sucursal_id cuando ambos lo tienen (migración por id) o cae al nombre normalizado de sucursal (fallback legacy).'
            ),
            "mark_ticket_notifications_read": (
                '💡 LA IDEA: Apaga la luz de alerta del reclamo cuando el operador entra a responderlo.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpio el contador de mensajes pendientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca como leídas las notificaciones del ticket para el admin actual; primero verifica con _can_access_ticket y lanza 403 si no tiene jurisdicción, luego delega en NotificationRepository.mark_ticket_read_for_user.'
            ),
            "get_admin_support_ticket_detail": (
                '💡 LA IDEA: Abre el expediente completo del reclamo con los datos del cliente y el chat.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda todo el contexto necesario para brindar una solución efectiva.\n\n'
                '⚙️ FUNCIONAMIENTO: Detalle de un ticket con sus datos de usuario respetando la jurisdicción: devuelve None si no existe o 403 si el admin no puede verlo.'
            ),
            "update_ticket_status": (
                "💡 LA IDEA: Permite al operador contestarle al cliente y cambiar el estado a 'Resuelto' o 'Cerrado'.\n\n"
                '🎯 POR QUE FUE GENERADA: Envía la solución al cliente y concluye la gestión del reclamo.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia el estado del ticket y opcionalmente agrega una respuesta: valida jurisdicción (403) y rechaza si el ticket ya está en estado terminal (400, bloqueado). Persiste estado y mensaje, marca todas las notificaciones del ticket como leídas, hace commit y notifica al cliente (SUPPORT_RESPONSE con el texto recortado a 100 caracteres, o SUPPORT_STATUS_CHANGED si no hubo respuesta). Devuelve None si no existe el ticket.'
            ),
            "get_ticket_by_id": (
                '💡 LA IDEA: Busca un ticket asegurando que pertenezca al usuario consultante.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que otros clientes lean reclamos privados.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el ticket si pertenece al usuario (SupportRepository.get_by_id_and_user), o None.'
            ),
            "get_ticket_messages": (
                '💡 LA IDEA: Trae el chat completo del reclamo ordenado cronológicamente.\n\n'
                '🎯 POR QUE FUE GENERADA: Dibuja la conversación en la pantalla del usuario o del operador.\n\n'
                '⚙️ FUNCIONAMIENTO: Hilo de mensajes de un ticket en formato lista de dicts con id, autoría, texto, adjunto, is_admin (rol admin/local_admin/staff) y fecha ISO.'
            ),
            "reply_to_ticket": (
                '💡 LA IDEA: Permite al cliente responder a las preguntas del soporte dentro del mismo reclamo.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita el diálogo continuo hasta resolver el problema.\n\n'
                '⚙️ FUNCIONAMIENTO: Responde un ticket del lado del cliente: busca el ticket del usuario (None si no es suyo), rechaza con 400 si el ticket está en estado terminal, agrega el mensaje, pone el estado a En Revisión, hace commit y notifica a los admins con los primeros 100 caracteres de la respuesta. Devuelve el ticket o None.'
            ),
            "get_admin_pending_count": (
                '💡 LA IDEA: Cuenta cuántos tickets sin contestar tiene el operador en su bandeja.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra el circulito rojo con el número de reclamos pendientes en el menú lateral.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuenta los tickets pendientes (fuera de TERMINAL_STATES) que puede ver el admin actual: el staff se acota por sucursal_id o nombre normalizado, el ADMIN global con organización a sus sedes y en single-tenant a los tickets General/sin sucursal. Alimenta la burbuja del menú lateral de Soporte & Tickets.'
            ),
        },
    },
    "services/time_service.py": {
        "proposito": 'Tiempo virtual del sistema: permite adelantar, retrasar o fijar la hora lógica (persistida en data/virtual_time_offset.json) para probar vencimientos y flujos sin esperar tiempo real; todo el backend consulta la hora por acá para que el offset aplique de forma uniforme.',
        "simbolos": {
            "TimeService": (
                '💡 LA IDEA: Es el reloj mágico del sistema: permite adelantar o atrasar el tiempo para probar cobros y vencimientos sin esperar horas reales.\n\n'
                '🎯 POR QUE FUE GENERADA: Es la herramienta fundamental para probar que las tarifas, multas y cancelaciones funcionen a la perfección.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio de clase con un offset en segundos que se suma a datetime.now en cada lectura. El offset se recarga desde disco en cada consulta, de modo que cambios hechos por otro proceso o pestaña se reflejen al instante.'
            ),
            "_load_offset": (
                '💡 LA IDEA: Lee del disco cuántos segundos está adelantado o atrasado el reloj de prueba.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene sincronizado el reloj virtual entre distintos procesos del servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee el offset del archivo JSON virtual_time_offset.json (data/ del proyecto); si no existe o falla el parseo deja 0 y solo loguea un warning/error.'
            ),
            "_save_offset": (
                '💡 LA IDEA: Guarda el desfase horario en un archivo de configuración.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el cambio de hora se mantenga activo mientras duren las pruebas.\n\n'
                '⚙️ FUNCIONAMIENTO: Escribe el offset actual al archivo JSON (creando el directorio data/ si no existe); los errores se loguean sin interrumpir.'
            ),
            "now": (
                '💡 LA IDEA: Devuelve la hora oficial del sistema considerando el reloj virtual de pruebas.\n\n'
                '🎯 POR QUE FUE GENERADA: Es la consulta de hora que usan todos los cobros y reservas de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Fecha y hora actual del sistema más el offset virtual; recarga el offset antes de devolver, por lo que es el punto de entrada que usan todos los servicios.'
            ),
            "now_str": (
                "💡 LA IDEA: Entrega la fecha y hora virtual en formato texto 'YYYY-MM-DD HH:MM:SS'.\n\n"
                '🎯 POR QUE FUE GENERADA: Facilita comparaciones directas de fecha en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: now() formateado como %Y-%m-%d %H:%M:%S, el formato que usan las comparaciones de fechas guardadas en la BD.'
            ),
            "set_offset": (
                '💡 LA IDEA: Adelanta o atrasa el reloj una cantidad fija de segundos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite simular saltos temporales precisos.\n\n'
                '⚙️ FUNCIONAMIENTO: Fija el offset en segundos exactos (positivo adelanta, negativo retrasa) y lo persiste.'
            ),
            "advance": (
                '💡 LA IDEA: Adelanta el reloj (ej: adelantar 3 horas o 2 días).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite verificar qué pasa cuando un auto se queda 3 días estacionado.\n\n'
                '⚙️ FUNCIONAMIENTO: Adelanta el tiempo virtual sumando un timedelta (acepta days/hours/minutes/… como kwargs) al offset y guarda.'
            ),
            "rewind": (
                '💡 LA IDEA: Atrasar el reloj hacia el pasado.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite repetir una prueba en el mismo instante anterior.\n\n'
                '⚙️ FUNCIONAMIENTO: Retrocede el tiempo virtual restando un timedelta del offset y guarda; sirve para simular el paso de días en pruebas.'
            ),
            "set_target_datetime": (
                '💡 LA IDEA: Fija el reloj exactamente en una fecha elegida (ej: Navidad a las 12:00).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite probar promociones o tarifas de feriados y fechas especiales.\n\n'
                '⚙️ FUNCIONAMIENTO: Fija el tiempo virtual a una fecha/hora exacta calculando la diferencia entre ese objetivo y la hora real, y persiste el offset resultante.'
            ),
            "reset": (
                '💡 LA IDEA: Devuelve el reloj a la hora real del planeta.\n\n'
                '🎯 POR QUE FUE GENERADA: Vuelve el sistema a la normalidad tras finalizar las pruebas.\n\n'
                '⚙️ FUNCIONAMIENTO: Vuelve el tiempo virtual a la hora real poniendo el offset en 0.'
            ),
            "get_offset": (
                '💡 LA IDEA: Consulta cuántos segundos de diferencia hay respecto a la hora real.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber si el reloj está alterado.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el offset vigente recargándolo desde disco (0 si no hay archivo o hay error).'
            ),
            "get_virtual_now": (
                '💡 LA IDEA: Entrega la hora virtual actual con confirmación de lectura.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita inspecciones de tiempo en paneles de desarrollo.\n\n'
                '⚙️ FUNCIONAMIENTO: Fecha y hora virtual actual (recarga el offset y llama a now); redundante con now pero expresa la intención de consulta.'
            ),
            "is_active": (
                '💡 LA IDEA: Avisa con una luz de alerta si el reloj virtual está encendido.\n\n'
                '🎯 POR QUE FUE GENERADA: Alerta al usuario en pantalla de que el sistema está operando en tiempo simulado.\n\n'
                '⚙️ FUNCIONAMIENTO: True si el offset de tiempo virtual es distinto de cero (es decir, el reloj está manipulado).'
            ),
            "get_info": (
                '💡 LA IDEA: Es el tablero de control del reloj: muestra hora real, hora simulada y desfase horario.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta la barra de herramientas del reloj virtual en el panel de control.\n\n'
                '⚙️ FUNCIONAMIENTO: Resumen para la UI del panel de tiempo virtual: offset en segundos, offset formateado con signo, días, horas y minutos (o 0h 0m), hora real e ISO, hora virtual e ISO formateada, y bandera active.'
            ),
        },
    },
    "services/user_notification_service.py": {
        "proposito": 'Fachada de notificaciones in-app del usuario: crear, listar, contar y marcar como leídas las notificaciones (pagos, recordatorios, soporte, puntos) delegando en NotificationRepository.',
        "simbolos": {
            "UserNotificationService": (
                '💡 LA IDEA: Es la ventanilla de avisos para el usuario: crea notificaciones y administra la campanita de la app.\n\n'
                '🎯 POR QUE FUE GENERADA: Aísla la entrega de notificaciones personales del resto de los servicios.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio estático delgado: construye las entidades UserNotification con fecha local y delega la persistencia y las consultas en NotificationRepository; no aplica reglas de negocio propias.'
            ),
            "create_notification": (
                "💡 LA IDEA: Emite una nueva notificación para un usuario (ej: 'Pago confirmado').\n\n"
                '🎯 POR QUE FUE GENERADA: Hace llegar avisos importantes directamente a la pantalla del cliente.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea y guarda una notificación no leída con tipo, título, mensaje y vínculos opcionales a reserva o ticket, usando localnow() para created_at; devuelve la entidad guardada.'
            ),
            "get_user_notifications": (
                '💡 LA IDEA: Trae el listado de notificaciones para la bandeja de entrada del usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cliente leer todos sus avisos en orden.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista las notificaciones de un usuario paginadas (limit 50 y offset 0 por defecto) delegando en el repositorio.'
            ),
            "get_unread_count": (
                '💡 LA IDEA: Cuenta los mensajes sin leer para mostrar el número en la campana.\n\n'
                '🎯 POR QUE FUE GENERADA: Avisa al usuario que tiene mensajes nuevos pendientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Cantidad de notificaciones sin leer de un usuario (alimenta la campanita del header).'
            ),
            "mark_as_read": (
                '💡 LA IDEA: Marca un mensaje como leído cuando el usuario lo abre.\n\n'
                '🎯 POR QUE FUE GENERADA: Descuenta el mensaje del contador de pendientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca una notificación como leída solo si existe y pertenece al usuario (get_by_id_and_user); devuelve False si no la encontró y True si la marcó.'
            ),
            "mark_all_as_read": (
                '💡 LA IDEA: Marca todos los mensajes como leídos de un solo golpe.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite limpiar la bandeja de notificaciones con un solo clic.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca todas las notificaciones del usuario como leídas y devuelve cuántas actualizaron.'
            ),
            "get_total_count": (
                '💡 LA IDEA: Cuenta la cantidad total de mensajes históricos del cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite armar la paginación del centro de notificaciones.\n\n'
                '⚙️ FUNCIONAMIENTO: Total de notificaciones del usuario sin importar si están leídas (para la vista de historial).'
            ),
            "delete_notification": (
                '💡 LA IDEA: Borra una notificación individual elegida por el usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cliente descartar avisos viejos.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina una notificación si existe y es del usuario; devuelve False si no corresponde.'
            ),
            "clear_read_notifications": (
                '💡 LA IDEA: Vacía todos los mensajes ya leídos de la bandeja.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene despejada la cuenta del usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Borra todas las notificaciones ya leídas del usuario y devuelve cuántas eliminó.'
            ),
            "mark_reservation_notifications_as_read": (
                '💡 LA IDEA: Marca como leídos los avisos de una reserva cuando el usuario entra a verla.\n\n'
                '🎯 POR QUE FUE GENERADA: Mejora la fluidez de uso de la app.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca como leídas todas las notificaciones de una reserva concreta, opcionalmente acotadas a un tipo (por ejemplo REMINDER_UNPAID al confirmar el recordatorio); devuelve el conteo.'
            ),
        },
    },
    "services/user_service.py": {
        "proposito": 'Alta, edición y baja de usuarios con validaciones de unicidad (email/DNI), creación de admins con su organización, y gestión de la flota de vehículos (alta, favorito, baja) con controles de bloqueo, límites y deudas.',
        "simbolos": {
            "UserService": (
                '💡 LA IDEA: Es la oficina de personal y padrón de clientes: da de alta usuarios, administra vehículos y cuida la privacidad.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la gestión de cuentas y asegura que ningún usuario se borre si tiene autos adentro o deudas.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio estático de usuarios y vehículos: normaliza datos (nombre, DNI, patente), valida reglas de negocio con HTTPException y delega las queries en UserRepository/VehicleRepository; también contiene los helpers de estadía abierta que usan sus validaciones.'
            ),
            "get_by_email": (
                '💡 LA IDEA: Busca un usuario por su dirección de correo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite recuperar la cuenta al iniciar sesión.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca un usuario por correo vía UserRepository.get_by_email.'
            ),
            "get_by_id": (
                '💡 LA IDEA: Busca un usuario por su código numérico interno.\n\n'
                '🎯 POR QUE FUE GENERADA: Utilizada para cargar los perfiles de los usuarios.\n\n'
                '⚙️ FUNCIONAMIENTO: Obtiene un usuario por id vía UserRepository.get_by_id.'
            ),
            "_validate_new_user": (
                '💡 LA IDEA: Revisa que el correo y el DNI no pertenezcan ya a otra persona antes de dar el alta.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita cuentas duplicadas o suplantación de identidad.\n\n'
                '⚙️ FUNCIONAMIENTO: Bloquea el alta si el correo ya está registrado (400) o si el DNI normalizado pertenece a otro usuario activo (400); se llama en create_user e invite_admin.'
            ),
            "_build_user": (
                '💡 LA IDEA: Da formato prolijo al nuevo usuario con sus nombres en mayúsculas y su clave encriptada.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que todas las cuentas nuevas nazcan con datos normalizados y seguros.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma la entidad User normalizando nombre y apellido, DNI, email en minúsculas y sin espacios, con el hash de contraseña recibido, rol, sucursal y organización; no persiste.'
            ),
            "create_user": (
                '💡 LA IDEA: Da de alta la cuenta definitiva en la base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite el registro de nuevos conductores en la red de estacionamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un usuario dentro de una organización: valida unicidad de email/DNI, construye el usuario con password hasheada, hace commit y refresh, y lo devuelve.'
            ),
            "invite_admin": (
                '💡 LA IDEA: Invita a un nuevo administrador creando su empresa y mandándole el link de activación por email.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite incorporar administradores de forma profesional y segura.\n\n'
                '⚙️ FUNCIONAMIENTO: Invita a un Admin General: valida unicidad, crea una organización nueva (nombre propio o el del invitado, con commit=False para que se guarde en la misma transacción) y da de alta al usuario con rol ADMIN, organización asignada y una contraseña aleatoria de 32 bytes que nadie conoce —el invitado define la suya en el enlace de activación, así la cuenta no puede entrar antes—.'
            ),
            "update_user": (
                '💡 LA IDEA: Actualiza los datos de contacto del usuario validando que no duplique el email de otro.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite mantener al día los datos de los conductores.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualiza datos de un usuario (activo, 404 si no existe): si cambia el email valida unicidad contra otros usuarios (400) y lo normaliza; ídem con el DNI normalizado; nombre, apellido, teléfono, sucursal y rol se aplican solo si vienen informados. Commit y refresh.'
            ),
            "delete_user": (
                '💡 LA IDEA: Da de baja la cuenta borrando datos personales (derecho al olvido) pero conservando los recibos contables sin romper la base.\n\n'
                '🎯 POR QUE FUE GENERADA: Cumple con las leyes de protección de datos personales impidiendo la baja si el cliente tiene un auto adentro del predio.\n\n'
                '⚙️ FUNCIONAMIENTO: Baja lógica con anonimización: rechaza si tiene reservas activas/pendientes (400) o si alguno de sus vehículos (incluida la patente propia) está físicamente dentro del estacionamiento (400, vía _last_entry_active). Si pasa, sobrescribe datos personales (Usuario Eliminado, email/dni eliminado-id), limpia teléfono, patente y dirección, marca is_deleted y hace commit; devuelve True, o False si el usuario no existía.'
            ),
            "_last_entry_active": (
                '💡 LA IDEA: Comprueba si alguno de los autos del cliente está actualmente estacionado en alguna cochera.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que alguien borre su cuenta o su auto mientras el vehículo sigue dentro del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper de estadía: devuelve (última entrada, salida posterior) si la patente tiene una entrada sin salida (estadía abierta), o None si no hay entrada; lo usan delete_user y delete_vehicle.'
            ),
            "list_vehicles": (
                '💡 LA IDEA: Lista todos los vehículos que el conductor tiene registrados.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta la lista de autos en la app del cliente.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista los vehículos de un usuario (VehicleRepository.get_by_user).'
            ),
            "add_vehicle": (
                '💡 LA IDEA: Asocia una nueva patente a la cuenta del usuario (hasta un máximo de 5 autos).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cliente ingresar automáticamente por cámara con cualquiera de sus autos familiares.\n\n'
                '⚙️ FUNCIONAMIENTO: Vincula un vehículo validando: cuenta no bloqueada (403), tipo válido Auto/Moto/Camioneta (400), máximo 5 vehículos por cuenta (400), formato de patente (400) y que la patente normalizada no esté ya registrada en el sistema (400). Guarda con patente y marca/modelo normalizados, notifica VEHICLE_REGISTERED y devuelve {status: ok}.'
            ),
            "set_favorite_vehicle": (
                '💡 LA IDEA: Elige el auto principal del conductor para que aparezca seleccionado por defecto al reservar.\n\n'
                '🎯 POR QUE FUE GENERADA: Agiliza el proceso de reserva eligiendo el auto que más usa el cliente.\n\n'
                '⚙️ FUNCIONAMIENTO: Alterna el vehículo favorito (toggle): si ya lo está lo desmarca; si no, primero desmarca el favorito anterior del usuario (unset_favorite_for_user) para que solo haya uno y luego lo marca. 403 si bloqueado, 404 si la patente no está en su flota. Devuelve estado final.'
            ),
            "delete_vehicle": (
                '💡 LA IDEA: Desvincula un auto de la cuenta, verificando que no esté adentro del predio ni tenga deudas impagas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cliente quitar autos que vendió sin dejar deudas colgadas en el estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Desvincula un vehículo tras validar: cuenta no bloqueada (403), que exista en la flota (404), sin reservas activas/pendientes de esa patente (400), que no esté físicamente dentro (400) y que no tenga la última estadía impaga (400). Reasigna el favorito a otro vehículo si corresponde y, si la patente borrada era la principal del usuario, la cambia por otra o la deja vacía; elimina la fila, notifica VEHICLE_REMOVED y devuelve {status: ok}.'
            ),
        },
    },
    "services/worker_service.py": {
        "proposito": 'Hilos daemon de mantenimiento en segundo plano: limpia y finaliza reservas vencidas, purga imágenes ALPR antiguas y procesa en ciclo los recordatorios, el paso a ACTIVA y la cancelación automática de reservas impagas.',
        "simbolos": {
            "WorkerService": (
                '💡 LA IDEA: Son los empleados invisibles que trabajan de noche y de día en segundo plano: limpian reservas viejas, mandan recordatorios y borran fotos viejas.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene el sistema ordenado y liviano de forma 100% automática sin necesidad de intervención manual.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio con los dos hilos de fondo de la aplicación (limpieza de reservas y notificaciones) y sus procesos periódicos; cada ciclo abre su propia sesión con SessionLocal y la cierra siempre en finally. NOTIFICATION_CHECK_INTERVAL (30 s) marca la cadencia del worker de notificaciones.'
            ),
            "start_reservation_cleanup": (
                '💡 LA IDEA: Enciende el robot de limpieza de reservas al arrancar el servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mantenimiento arranque automáticamente con el sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Arranca el hilo de mantenimiento de reservas como daemon y lo devuelve; se llama al iniciar la app.'
            ),
            "start_notification_worker": (
                '💡 LA IDEA: Enciende el robot despachador de recordatorios y avisos al iniciar el servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que los emails y notificaciones se envíen puntualmente.\n\n'
                '⚙️ FUNCIONAMIENTO: Arranca el hilo de recordatorios/auto-cancelación como daemon y lo devuelve.'
            ),
            "_reservation_cleanup_worker": (
                '💡 LA IDEA: Es el bucle periódico de limpieza: cada pocos minutos revisa y archiva turnos viejos y borra fotos pesadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Libera espacio en el disco rígido y mantiene la base de datos veloz.\n\n'
                '⚙️ FUNCIONAMIENTO: Bucle infinito: en cada iteración abre sesión, ejecuta cleanup_overdue_reservations (cancela impagas vencidas), auto_finalize_all_reservations (completa vencidas) y _cleanup_old_alpr_images, captura errores sin morir y duerme settings.MAINTENANCE_INTERVAL_SECONDS.'
            ),
            "_cleanup_old_alpr_images": (
                '💡 LA IDEA: Es la trituradora de fotos viejas: borra las fotos de patentes que tienen más de 30 días de antigüedad.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el disco de la computadora se llene con gigabytes de fotos viejas de autos.\n\n'
                '⚙️ FUNCIONAMIENTO: Borra de settings.IMAGE_DIR las imágenes con más de ALPR_IMAGE_RETENTION_DAYS días (30 por defecto) según su mtime; no hace nada si el directorio no existe o la retención es ≤ 0. Loguea cuántas purgó y tolera errores archivo por archivo.'
            ),
            "_notification_worker": (
                '💡 LA IDEA: Es el reloj que despierta cada 30 segundos para revisar si hay recordatorios pendientes de envío.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos lleguen exactamente a tiempo al teléfono del cliente.\n\n'
                '⚙️ FUNCIONAMIENTO: Bucle infinito cada 30 segundos: con sesión propia llama a _process_reminders, _process_started_reservations y _process_auto_cancellations, capturando errores y cerrando la sesión en finally.'
            ),
            "_process_reminders": (
                '💡 LA IDEA: Revisa si hay reservas que empiezan en la próxima media hora y manda el email con el código QR.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda al cliente a tener su pase digital listo en la mano antes de llegar a la barrera.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca reservas PENDIENTES que empiezan entre ahora y 31 minutos (ReservationRepository.get_pending_reminders): primero marca recordatorio_confirmado en True para no reprocesarla, salta si no hay usuario con email o si ya existe una notificación REMINDER_PAID/REMINDER_UNPAID (evita duplicados), crea la notificación in-app según esté pagada o no (presentar QR vs abonar) y envía el mail de recordatorio (EmailService). Errores por reserva solo se loguean.'
            ),
            "_process_started_reservations": (
                "💡 LA IDEA: Pasa a 'Activa' la reserva en el minuto exacto en que empieza el turno contratado.\n\n"
                '🎯 POR QUE FUE GENERADA: Deja la cochera formalmente ocupada en el sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Pasa a ACTIVA las reservas PENDIENTES cuyo horario de inicio ya llegó (get_pending_started): marca también recordatorio_confirmado, y si no existe ya una notificación RESERVATION_STARTED crea el aviso in-app de inicio (con texto distinto si está pagada o no). Sin usuario no hace nada; errores solo se loguean.'
            ),
            "_process_auto_cancellations": (
                '💡 LA IDEA: Cancela y libera la cochera si el cliente no llegó tras 30 minutos de tolerancia y no había pagado.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que una cochera quede vacía y perdida todo el día por culpa de alguien que no vino.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancela reservas impagas cuyo inicio pasó hace más de 30 minutos sin ingreso: trae candidatas con get_unpaid_overdue, consulta en batch qué reservas ya tuvieron entrada (AccessRepository.get_reserva_ids_with_entry) y salta esas; a las demás les pone CANCELADA y pago FALLIDO, hace commit y notifica al usuario in-app (AUTO_CANCELLED) y por mail (EmailService.send_auto_cancelled_notification). Errores por reserva solo se loguean.'
            ),
        },
    },
}
