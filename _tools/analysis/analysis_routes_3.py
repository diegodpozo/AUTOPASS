"""Explicaciones analizadas de la sección routes, parte 3 (rutas de usuario y vistas)."""

ANALISIS: dict[str, dict] = {
    "routes/user/__init__.py": {
        "proposito": (
            "💡 LA IDEA: Es el 'portal del cliente' en la API. Conecta todo lo que un conductor puede hacer desde su teléfono celular: ver su saldo, registrar patentes, pagar con Mercado Pago, consultar reservas o pedir ayuda de soporte.\n\n"
            "🎯 POR QUE FUE GENERADA: Reúne bajo el prefijo unificado `/v1/user/` los 8 módulos de autoservicio para el usuario final, aislando la experiencia del cliente de las pantallas operativas de garita o administración.\n\n"
            "⚙️ FUNCIONAMIENTO: Crea un `APIRouter` con prefijo `/v1/user` y etiqueta 'User Actions'. Incluye e interconecta los subrouters de perfil (`profile`), autos (`vehicles`), saldo y tarifas (`balance`), reservas (`reservations`), puntos (`points`), notificaciones (`notifications`), soporte (`support`) y cobros (`mercadopago`)."
        ),
        "simbolos": {
        },
    },
    "routes/user/balance.py": {
        "proposito": 'Expone al cliente lo relacionado con saldo y estadías: estadias activas con su deuda calculada por tarifa, historial de pagos, tarifas vigentes de la sede y una carga de saldo simulada. Es la cara de usuario del módulo de facturación.',
        "simbolos": {
            "get_user_active_stays": (
                '💡 LA IDEA: Es el taxímetro del cliente: le muestra qué autos suyos están estacionados en este momento y cuánto dinero llevan acumulado por el tiempo transcurrido.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al conductor saber en vivo cuánto debe pagar antes de dirigirse a la salida, evitando sorpresas al llegar a la barrera.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/active-stays. Autenticado; toma las patentes del usuario normalizadas (normalize_plate) y en dos consultas obtiene la última entrada por patente y las salidas posteriores (AccessRepository). Devuelve solo las estadías sin salida válida (la salida debe ser posterior al ingreso), con id, patente, fecha de ingreso, deuda y pago_confirmado: la deuda es 0 si la entrada ya está pagada o se calcula con BillingService.calculate_debt(fecha, sucursal, tipo_vehiculo). Sin vehículos o sin ingresos devuelve lista vacía.'
            ),
            "get_user_payment_history": (
                '💡 LA IDEA: Es el resumen bancario personal donde el usuario puede consultar todos los tickets de estacionamiento que ya abonó en el pasado.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda transparencia y comprobantes de pago digitales para que el cliente lleve control de sus gastos de movilidad.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/payment-history. Autenticado; normaliza las patentes del usuario y delega en AccessRepository.get_paid_logs_by_patentes para devolver el historial cronológico de registros de acceso ya pagados.'
            ),
            "get_current_rates": (
                '💡 LA IDEA: Es el cartel de precios en la vereda que informa el valor de la media hora, hora, día o mes según el tipo de vehículo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a cualquier usuario consultar las tarifas vigentes de una sucursal específica o generales sin necesidad de haber iniciado sesión.\n\n'
                "⚙️ FUNCIONAMIENTO: GET /v1/user/rates. Endpoint público (sin usuario): recibe el query param opcional sucursal y lista las claves de settings precio_* (auto, _moto, _camioneta: 30min, hora, día, semana, quincena, mes) desde SettingsRepository.get_all_by_sucursal. Sin sucursal devuelve las tarifas globales; con sucursal solo las de esa sede (no hereda globales). Si falta '30min' pero existe 'hora' en alguna familia, lo completa como hora/2, y responde un dict nombre_de_tarifa -> valor."
            ),
            "recharge_balance": (
                '💡 LA IDEA: Es el monedero prepago virtual donde el cliente carga saldo para que los cobros de estacionamiento y reservas se debiten automáticamente.\n\n'
                '🎯 POR QUE FUE GENERADA: En este entorno de demostración escolar simula la acreditación inmediata de fondos para probar cobros automáticos sin dinero real.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/recharge-balance. Autenticado; recibe schemas.RechargeBalance y rechaza montos <= 0 con HTTP 400. Suma el monto a current_user.saldo, hace commit y, en modo best-effort (try/except que solo loguea), crea una notificación BALANCE_RECHARGED con el monto acreditado y el saldo resultante. Devuelve status/message con el importe cargado. Es una carga simulada (no hay pasarela de pago real en esta ruta).'
            ),
        },
    },
    "routes/user/fidelization.py": {
        "proposito": 'Implementa el programa de fidelización del cliente: catálogo de promociones de la sucursal, canje de puntos por vouchers o descuentos de reserva, listado y cancelación de tickets de canje, y historial paginado de puntos.',
        "simbolos": {
            "_generar_codigo_ticket": (
                '💡 LA IDEA: Es el grabador que estampa un código alfanumérico único e irrepetible en cada cupón de descuento o premio canjeado.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que los cupones puedan ser falsificados, adivinados o duplicados por otros usuarios.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera el código único del ticket de canje con secrets.token_hex(8).upper(): 16 caracteres alfanuméricos en mayúsculas, usado como identificador humano y dentro del QR.'
            ),
            "_crear_ticket": (
                '💡 LA IDEA: Es la fábrica de tickets digitales: genera el cupón con su código QR, fecha de vencimiento y ubicación del local donde canjearlo.\n\n'
                '🎯 POR QUE FUE GENERADA: Guarda un comprobante inmutable con los términos exactos de la promoción al momento del canje, independientemente de si la oferta cambia después.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea y persiste (db.add + flush, para obtener el id) un models.RedemptionTicket a partir de la promoción: copia título, descripción, tipo, valor de descuento (solo si es descuento_reserva), icono y sucursal; estado inicial VIGENTE y qr_data con el código. Si el tipo es voucher agrega la observación de vigencia de 30 días. Resuelve la ubicación de canje: si la promo no trae coordenadas propias, busca la sucursal asignada (BranchRepository.get_by_name, respetando organization_id) y rellena dirección/latitud/longitud desde ella. Al final reescribe el qr_data incluyendo también el id del ticket recién creado.'
            ),
            "get_promotions": (
                '💡 LA IDEA: Es la vidriera de recompensas disponibles que el cliente puede canjear usando los puntos que sumó por estacionar.\n\n'
                '🎯 POR QUE FUE GENERADA: Motiva la fidelidad del usuario mostrándole qué descuentos en reservas o vouchers de comercios aliados puede obtener.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/promotions. Autenticado; devuelve las promociones activas filtradas por la sucursal y la organización del usuario (PromotionRepository.get_active) como lista de schemas.PromotionResponse.'
            ),
            "redeem_points": (
                '💡 LA IDEA: Es el canje en ventanilla: descuenta los puntos acumulados de la cuenta del usuario y le entrega su ticket de beneficio digital con código QR.\n\n'
                '🎯 POR QUE FUE GENERADA: Materializa los beneficios del programa de fidelización verificando que el cliente tenga saldo suficiente de puntos antes de premiarlo.\n\n'
                "⚙️ FUNCIONAMIENTO: POST /v1/user/redeem/{promo_id}. Autenticado; busca la promoción activa (404 si no existe) y verifica que el usuario tenga puntos suficientes (400 'Puntos insuficientes'). Resta costo_puntos, registra el movimiento negativo en PointsLog, crea el ticket con _crear_ticket, notifica al usuario (best-effort) y hace commit. Devuelve status, mensaje, tipo_canje y el ticket serializado (RedemptionTicketResponse): por voucher genera un QR persistente; por descuento_reserva deja un descuento (%) disponible para pagar una reserva."
            ),
            "get_user_redemption_tickets": (
                '💡 LA IDEA: Es la billetera de cupones ganados donde el cliente guarda todos sus beneficios vigentes listos para usar en su próxima visita.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite mostrar en pantalla los pases y descuentos con sus códigos QR y mapas de cómo llegar a cada local.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/redemption-tickets. Autenticado; lista los tickets del usuario (RedemptionRepository.get_by_user) y enriquece la respuesta con ubicación sin tocar la BD: si un ticket no tiene coordenadas, las toma primero de su promoción y, en último término, de la sucursal del ticket/usuario (BranchRepository.get_by_name). Devuelve la lista de RedemptionTicketResponse con dirección, latitude y longitude completados.'
            ),
            "get_available_redemptions": (
                '💡 LA IDEA: Es el filtro de cupones válidos para el momento de pagar una reserva, mostrando únicamente los descuentos aplicables a la sucursal elegida.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita confusiones al usuario mostrando solo aquellos beneficios que son compatibles con el estacionamiento y vehículo seleccionados.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/redemptions/available. Autenticado; con query param opcional sucursal, devuelve los descuentos de reserva (%) ya canjeados y todavía vigentes del usuario, aptos para aplicar en una sucursal (RedemptionRepository.list_discounts_by_user).'
            ),
            "cancel_redemption_ticket": (
                '💡 LA IDEA: Es el arrepentimiento de compra: permite anular un cupón que todavía no fue utilizado y recuperar los puntos invertidos.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga flexibilidad al cliente si se equivoca de beneficio o cambia de planes, reintegrando sus puntos de manera justa y transparente.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/redemptions/{ticket_id}/cancel. Autenticado; busca el ticket propio (404 si no existe) y exige estado VIGENTE (400 si ya no lo está). Marca el ticket como CANCELADO, si la promoción original costaba puntos le devuelve ese costo al usuario y lo registra en PointsLog, notifica el reintegro (best-effort) y confirma. Responde con el detalle de puntos devueltos.'
            ),
            "get_points_history": (
                '💡 LA IDEA: Es el extracto de cuenta del club de puntos, mostrando cada punto ganado por estadías y cada punto gastado en canjes.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga total claridad al conductor sobre cómo se fue moviendo su puntaje a lo largo del tiempo.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/points-history. Autenticado; recibe page y limit, consulta PointsRepository.get_history y devuelve los ítems paginados junto con totales: total de movimientos, páginas (math.ceil, mínimo 1), total_earned y total_redeemed (valor absoluto).'
            ),
        },
    },
    "routes/user/mercadopago.py": {
        "proposito": 'Integra MercadoPago desde el cliente: crea la preferencia de checkout para pagar reservas o estadías y procesa los retornos del navegador y el webhook del proveedor, aplicando el pago a la intención correspondiente. Flujo: checkout -> sitio de MP -> retorno a success/pending/failure (o webhook) -> confirmación y redirección al perfil con el resultado.',
        "simbolos": {
            "create_mp_checkout": (
                '💡 LA IDEA: Es el pase a la caja registradora de Mercado Pago para abonar una reserva o una estadía con tarjeta de crédito, débito o dinero en cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Conecta la aplicación con la pasarela oficial de pagos de Mercado Pago, preparando la orden de compra y el enlace seguro de cobro.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/mercadopago/checkout. Autenticado; rechaza con 403 si la cuenta está bloqueada y delega en mp_service.create_payment(db, usuario, datos), que arma la preferencia de checkout pro (reserva o estadía) y devuelve schemas.MercadoPagoCheckoutResponse con la info para abrir la pasarela.'
            ),
            "_procesar_retorno": (
                '💡 LA IDEA: Es la aduana que recibe al cliente cuando vuelve del sitio de Mercado Pago, corrobora si el pago entró y lo manda a su perfil con el resultado.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la confirmación de las transacciones para evitar duplicar código entre los distintos estados de cobro (aprobado, pendiente o rechazado).\n\n'
                "⚙️ FUNCIONAMIENTO: Lógica común de los retornos del navegador. Abre su propia sesión (SessionLocal), localiza el pago por external_reference (MercadoPagoPaymentRepository) para saber el tipo (reserva/estadía) y llama a mp_service.confirm_payment para aplicar el cobro: 'approved' si quedó aplicado, 'pending' si MP lanzó HTTPException sin aplicar y 'failed' ante cualquier error (todo queda logueado). Cierra la sesión en finally y responde siempre con RedirectResponse a /perfil?mp_status=...&mp_tipo=..., para que la página muestre el resultado."
            ),
            "mp_success": (
                '💡 LA IDEA: Es la pantalla de felicitaciones que se activa cuando el pago en Mercado Pago se completó exitosamente.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que la reserva o estadía quede registrada como abonada al instante de recibir la confirmación de la pasarela.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/mercadopago/success. Retorno de MP cuando el pago fue aprobado: recibe external_reference y payment_id (o collection_id como alternativa) y delega en _procesar_retorno, que confirma el pago y redirige al perfil.'
            ),
            "mp_pending": (
                '💡 LA IDEA: Es la sala de espera para pagos en efectivo (como Pago Fácil o Rapipago) que aún no fueron acreditados en el banco.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene la reserva o estadía en espera sin cancelarla, aguardando la notificación bancaria de acreditación.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/mercadopago/pending. Retorno de MP cuando el pago quedó pendiente; recibe los mismos parámetros y delega en _procesar_retorno (el estado real se resuelve al confirmar, no por la URL).'
            ),
            "mp_failure": (
                '💡 LA IDEA: Es el aviso de pago fallido cuando la tarjeta del cliente fue rechazada o canceló la operación en la pasarela.\n\n'
                '🎯 POR QUE FUE GENERADA: Notifica con claridad al usuario sobre el problema para que pueda reintentar con otro medio de pago sin perder sus datos.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/mercadopago/failure. Retorno de MP cuando el pago fue rechazado o cancelado; delega en _procesar_retorno, que intentará confirmar y en todo caso redirige con mp_status=failed.'
            ),
            "mp_webhook": (
                '💡 LA IDEA: Es el buzón digital silencioso donde Mercado Pago avisa de servidor a servidor cada vez que entra un pago, sin depender del celular del cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que un pago quede acreditado incluso si el usuario cerró el navegador, se quedó sin batería o se le cortó internet en el camino.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/mercadopago/webhook. Recibe las notificaciones server-side de MP con límite de 60 por minuto (limiter). Parsea el JSON (si falla responde ok sin más), extrae payment_id de data.id o data_id, consulta a la API de MP (mp_service._mp_request GET /v1/payments/{id}) para obtener el external_reference y llama a mp_service.confirm_payment para aplicar el pago. Todos los errores (HTTPException o general) solo se registran; siempre responde {"status": "ok"} para no reintentar el webhook.'
            ),
        },
    },
    "routes/user/notifications.py": {
        "proposito": 'API de notificaciones del usuario logueado: listado pagado con contador de no leídas, consulta del badge, marcado de leídas (individual o masivo), limpieza y borrado. Toda la lógica y el acceso a datos están en UserNotificationService; las rutas solo delegan.',
        "simbolos": {
            "get_notifications": (
                '💡 LA IDEA: Es el buzón de correo personal donde el conductor revisa todas las alertas que le envió el estacionamiento (ingresos, pagos, recordatorios).\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene al usuario informado sobre la actividad de sus autos y reservas en una bandeja de entrada ordenada y paginada.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/profile/notifications. Autenticado; recibe limit (1..200, por defecto 50) y offset (>= 0), pide al servicio las notificaciones, el total y las no leídas, y responde schemas.NotificationListResponse con la lista serializada y los contadores.'
            ),
            "get_unread_count": (
                '💡 LA IDEA: Es el globo rojo con el número que avisa cuántas notificaciones nuevas hay sin abrir.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite mostrar de forma ultraliviana el contador en la campana de la barra de navegación sin tener que descargar todos los mensajes completos.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/profile/notifications/unread. Autenticado; devuelve solo el número de notificaciones no leídas (UnreadCountResponse) para pintar el indicador de la interfaz.'
            ),
            "mark_as_read": (
                '💡 LA IDEA: Es el gesto de abrir una carta: marca un mensaje específico como leído para que no figure más como novedad pendiente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cliente gestionar sus mensajes a su propio ritmo sin perder de vista los avisos que aún no leyó.\n\n'
                '⚙️ FUNCIONAMIENTO: PATCH /v1/user/profile/notifications/{notif_id}/read. Autenticado; marca como leída la notificación indicada pasando también el id del usuario para que el servicio solo toque las propias. Responde 204 sin contenido.'
            ),
            "mark_all_as_read": (
                "💡 LA IDEA: Es el botón de 'marcar todo como leído' para vaciar los avisos pendientes de una sola vez.\n\n"
                '🎯 POR QUE FUE GENERADA: Facilita limpiar la bandeja de notificaciones cuando el usuario ya se enteró de todo y no quiere cliquear una por una.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/profile/notifications/read-all. Autenticado; marca todas las notificaciones del usuario como leídas y responde 204.'
            ),
            "clear_read_notifications": (
                '💡 LA IDEA: Es el cesto de papeles que elimina todos los avisos viejos que ya fueron leídos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite mantener prolija la bandeja de entrada descartando notificaciones antiguas que ya cumplieron su propósito.\n\n'
                '⚙️ FUNCIONAMIENTO: DELETE /v1/user/profile/notifications/clear-read. Autenticado; elimina todas las notificaciones ya leídas del usuario y responde 204.'
            ),
            "delete_notification": (
                '💡 LA IDEA: Es el tachado individual de una notificación puntual que el usuario ya no desea conservar.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga control total al usuario sobre su historial de mensajes, asegurando que solo pueda borrar sus propias alertas.\n\n'
                '⚙️ FUNCIONAMIENTO: DELETE /v1/user/profile/notifications/{notif_id}. Autenticado; elimina una notificación concreta del usuario (el servicio valida pertenencia) y responde 204.'
            ),
        },
    },
    "routes/user/profile.py": {
        "proposito": 'Operaciones básicas del perfil del usuario autenticado: leer sus datos, editarlos y cambiar la contraseña verificando la actual. Es el endpoint /me que consume el frontend para mostrar y guardar el perfil.',
        "simbolos": {
            "get_me": (
                '💡 LA IDEA: Es el espejo del perfil: devuelve todos los datos del usuario logueado (nombre, correo, saldo, puntos y sucursal preferida).\n\n'
                "🎯 POR QUE FUE GENERADA: Alimenta la pantalla de 'Mi Cuenta' y permite a la aplicación conocer el estado actual del conductor conectado.\n\n"
                '⚙️ FUNCIONAMIENTO: GET /v1/user/me. Autenticado; devuelve directamente el objeto current_user serializado como schemas.UserBase (nombre, email, sucursal, saldo, puntos, etc.).'
            ),
            "update_me": (
                '💡 LA IDEA: Es el formulario de edición de datos personales para cambiar teléfono, dirección o corregir el nombre.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite mantener al día la información de contacto, normalizando automáticamente mayúsculas y limpiando espacios indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: PUT /v1/user/me. Autenticado; recibe schemas.UserUpdate y aplica solo los campos enviados: nombre y apellido pasan por normalize_name (importado de routes.parking) para normalizar mayúsculas, email se pasa a minúsculas y sin espacios, teléfono y dirección se copian tal cual. Hace commit, refresca el usuario y lo devuelve como UserBase.'
            ),
            "change_password": (
                '💡 LA IDEA: Es la cerradura de seguridad para renovar la contraseña, exigiendo ingresar primero la clave anterior para evitar accesos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la cuenta ante descuidos y despacha un correo de seguridad alertando sobre el cambio de credenciales.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/change-password. Autenticado; recibe schemas.ChangePassword y valida la contraseña actual con verify_password: si no coincide lanza HTTP 400. Si es correcta guarda el hash de la nueva (get_password_hash), confirma y crea, de forma best-effort, una notificación de seguridad SECURITY_PASSWORD_CHANGED avisando el cambio. Responde con status y mensaje de éxito.'
            ),
        },
    },
    "routes/user/reservations.py": {
        "proposito": 'Expone al cliente todo el ciclo de reservas: consulta de disponibilidad, fechas y horas bloqueadas para el calendario, alta, modificación, pago con saldo (y canje), confirmación de recordatorio, simulación y cancelación con reembolso. Las rutas son delgadas y delegan en ReservationService y sus helpers de reservation_service.',
        "simbolos": {
            "check_availability": (
                '💡 LA IDEA: Es la consulta previa al mostrador: verifica si habrá lugar libre para un auto en el día y horario que el cliente desea reservar.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el usuario inicie un proceso de reserva o pago en un momento en que el estacionamiento ya se encuentra repleto.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/reservations/check-availability. Autenticado; recibe sucursal_nombre, fechas de inicio/fin, tipo_vehiculo (por defecto Auto) y exclude_id opcional (al editar, para ignorar la propia reserva) y devuelve el resultado de verificar_disponibilidad: si hay lugares para ese rango.'
            ),
            "get_disabled_dates": (
                '💡 LA IDEA: Es el calendario interactivo que tacha con una cruz gris los días que ya están completamente agotados o cerrados.\n\n'
                '🎯 POR QUE FUE GENERADA: Agiliza la reserva impidiendo que el usuario pierda tiempo seleccionando días sin disponibilidad de plazas.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/reservations/disabled-dates. Autenticado; parámetros de sucursal, tipo de vehículo, tipo de estadía (dia), fecha desde y hasta 365 días a evaluar (Query 1..365, por defecto 90). Llama a obtener_fechas_deshabilitadas y responde un objeto con los filtros usados y la lista disabled_dates (YYYY-MM-DD) de días sin capacidad, para tacharlas en el calendario.'
            ),
            "get_disabled_hours": (
                '💡 LA IDEA: Es el reloj que bloquea los horarios específicos en los que no hay plazas disponibles para la duración deseada.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que no se superpongan reservas y ayuda al usuario a encontrar los huecos de horario disponibles para estacionar.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/reservations/disabled-hours. Autenticado; para una fecha concreta recibe duración (hasta 24 h), paso en minutos (5..120, por defecto 30) y exclude_id opcional. Invoca obtener_horas_deshabilitadas_con_reservas y devuelve los slots deshabilitados (HH:MM) y además los rangos realmente reservados (reserved_ranges), de modo que la interfaz distingue ocupación de margen de solapamiento. exclude_id evita que la reserva que se está editando aparezca como ocupada.'
            ),
            "get_user_reservations": (
                '💡 LA IDEA: Es el listado de turnos agendados del cliente, mostrando reservas pasadas, confirmadas y las que están por comenzar.\n\n'
                '🎯 POR QUE FUE GENERADA: Ofrece al conductor un panel claro para revisar sus turnos, ver estados de pago y acceder a sus comprobantes de reserva.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/reservations. Autenticado; devuelve las reservas del usuario (schemas.UserReservationResponse) llamando a ReservationService.list_user_reservations, que además actualiza estados automáticamente (vencidas, confirmadas, etc.).'
            ),
            "create_user_reservation": (
                '💡 LA IDEA: Es el contrato de reserva digital: bloquea una plaza para el auto del cliente y procesa el cobro con su saldo disponible si le alcanza.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura el lugar de estacionamiento antes de salir de casa, evitando dar vueltas buscando dónde dejar el vehículo.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/reservations. Autenticado; recibe schemas.UserReservationCreate y delega en ReservationService.create_user_reservation, que crea la reserva y procesa el cobro con el saldo de la cuenta cuando alcanza.'
            ),
            "modify_reservation": (
                '💡 LA IDEA: Es el cambio de turno: permite al cliente reprogramar el día, la hora o el vehículo de una reserva previamente realizada.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga flexibilidad ante imprevistos cotidianos, compensando automáticamente las diferencias de saldo o puntos correspondientes.\n\n'
                '⚙️ FUNCIONAMIENTO: PATCH /v1/user/reservations/{res_id}. Autenticado; recibe schemas.ReservationUpdate y delega en ReservationService.modify_user_reservation, que reajusta la reserva y compensa saldo y puntos según corresponda al cambio.'
            ),
            "pay_reservation": (
                '💡 LA IDEA: Es la confirmación de pago de una reserva pendiente usando el saldo de la billetera y aplicando posibles cupones de descuento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario liquidar sus reservas adeudadas para que su patente quede habilitada en las barreras al momento de llegar.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/reservations/{res_id}/pay. Autenticado; rechaza con 403 si la cuenta está bloqueada. Abona una reserva pendiente con el saldo del usuario mediante ReservationService.pay_reservation, aceptando además redemption_ticket_id opcional para aplicar un descuento (%) de un canje previo.'
            ),
            "confirm_reservation_reminder": (
                "💡 LA IDEA: Es el botón de 'Voy en camino' que presiona el usuario cuando recibe la alerta previa al inicio de su reserva.\n\n"
                '🎯 POR QUE FUE GENERADA: Confirma la asistencia del conductor y evita que el sistema libere su lugar a otros clientes por considerarlo ausente.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/reservations/{res_id}/confirm-reminder. Autenticado; llama a ReservationService.confirm_reminder para confirmar que el usuario vio el recordatorio: detiene los avisos y prepara la auto-cancelación si no se confirma a tiempo.'
            ),
            "simulate_reservation_cancel": (
                '💡 LA IDEA: Es la vista previa del reembolso que le muestra al usuario exactamente cuánto dinero recuperará si decide cancelar su reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda total transparencia antes de confirmar la cancelación, informando si aplican retenciones por cancelaciones de último momento.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/reservations/{res_id}/cancel-simulation. Autenticado; busca la reserva propia (get_reservation_or_404, 404 si no existe o no es del usuario) y devuelve ReservationService.simulate_refund: el monto que se reembolsaría, sin cancelar nada, para previsualizar la operación.'
            ),
            "cancel_reservation": (
                '💡 LA IDEA: Es la anulación definitiva de una reserva por parte del cliente antes de su inicio.\n\n'
                '🎯 POR QUE FUE GENERADA: Libera la plaza inmediatamente para otros usuarios y devuelve el dinero correspondiente al saldo de la cuenta.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/reservations/{res_id}/cancel. Autenticado; delega en ReservationService.cancel_reservation, que anula la reserva y reintegra el monto si ya había sido pagada.'
            ),
        },
    },
    "routes/user/support.py": {
        "proposito": 'Permite al cliente abrir tickets de soporte, listarlos, verlos con su hilo de mensajes y responder adjuntando archivos (imágenes o PDF de hasta 1 MB) guardados en static/uploads/support. La persistencia y los estados están en SupportService; aquí se validan la pertenencia y el adjunto.',
        "simbolos": {
            "create_support_ticket": (
                '💡 LA IDEA: Es el formulario de reclamos o dudas donde el cliente describe un problema indicando la sucursal y la categoría de la consulta.\n\n'
                '🎯 POR QUE FUE GENERADA: Canaliza de manera ordenada los pedidos de ayuda de los usuarios para que el equipo de soporte los atienda sin perder nada.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/support-tickets (201). Autenticado; recibe schemas.SupportTicketCreate y delega en SupportService.create_ticket; responde con mensaje, id, sucursal y estado del ticket recién creado.'
            ),
            "get_my_support_tickets": (
                '💡 LA IDEA: Es la bandeja de tickets del cliente donde puede ver el estado de todas sus consultas abiertas y resueltas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario hacer seguimiento de sus reclamos sin tener que llamar por teléfono o consultar en persona.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/support-tickets. Autenticado; pide al servicio los tickets del usuario (SupportService.get_user_tickets) y los convierte en una lista de dicts con id, categoría, sucursal, asunto, mensaje, estado y fechas ISO creada/actualizada.'
            ),
            "get_support_ticket": (
                '💡 LA IDEA: Es la pantalla de chat del reclamo, donde se muestra el intercambio completo de mensajes entre el cliente y el personal de ayuda.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite releer las explicaciones dadas y continuar la conversación con el operador de forma fluida.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/support-tickets/{ticket_id}. Autenticado; busca el ticket del usuario (404 si no existe o no es suyo) con SupportService.get_ticket_by_id y agrega el hilo completo de mensajes (get_ticket_messages) en la respuesta.'
            ),
            "reply_to_support_ticket": (
                '💡 LA IDEA: Es la respuesta del cliente a una consulta de soporte, permitiendo además adjuntar fotos del ticket o comprobantes en PDF.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita aportar pruebas visuales o aclaraciones para destrabar reclamos complejos, cuidando el tamaño y formato de los archivos subidos.\n\n'
                '⚙️ FUNCIONAMIENTO: PATCH /v1/user/support-tickets/{ticket_id}/reply. Autenticado y asíncrono; recibe el mensaje como Form y un adjunto opcional (File). Valida la extensión contra ALLOWED_EXTENSIONS jpg/jpeg/png/gif/webp/pdf (400 si no está permitida), guarda el archivo con nombre uuid en static/uploads/support escribiendo por bloques de 64 KB y abortando (borrando el archivo) si supera MAX_FILE_SIZE de 1 MB o si queda vacío (400 en ambos casos). Luego delega en SupportService.reply_to_ticket con la URL y nombre originales (404 si el ticket no existe) y devuelve el estado actualizado y todos los mensajes del ticket.'
            ),
        },
    },
    "routes/user/vehicles.py": {
        "proposito": 'CRUD de vehículos vinculados a la cuenta del usuario (patente, marca/modelo y tipo): listado, alta, marcar favorito y desvincular, con toda la validación delegada en UserService.',
        "simbolos": {
            "get_user_vehicles": (
                '💡 LA IDEA: Es el garaje virtual del usuario donde figuran todos los autos, motos o camionetas que tiene registrados a su nombre.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a la aplicación saber qué vehículos pertenecen al conductor para asignarlos rápidamente a reservas o pagos automáticos.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/user/vehicles. Autenticado; devuelve la lista de vehículos del usuario mediante UserService.list_vehicles.'
            ),
            "add_user_vehicle": (
                '💡 LA IDEA: Es el empadronamiento de un vehículo nuevo: anota la patente, marca, modelo y categoría en la cuenta del cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida que la patente tenga un formato oficial argentino y asocia el rodado al conductor para el reconocimiento automático por cámara.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/vehicles. Autenticado; recibe schemas.VehicleCreate (patente, marca_modelo, tipo) y delega en UserService.add_vehicle, que valida el formato de la patente y el tipo antes de vincular el vehículo a la cuenta.'
            ),
            "set_favorite_vehicle": (
                '💡 LA IDEA: Es la estrella de vehículo predilecto que marca cuál es el auto principal con el que se mueve el conductor habitualmente.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra tiempo al cliente completando su patente preferida por defecto al momento de hacer una nueva reserva.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/user/vehicles/{patente}/favorite. Autenticado; marca como favorito el vehículo indicado (solo puede haber uno por usuario) y, si ya lo estaba, lo desmarca, vía UserService.set_favorite_vehicle.'
            ),
            "delete_user_vehicle": (
                '💡 LA IDEA: Es el borrado de un auto vendido o dado de baja de la cuenta del usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpia la lista de vehículos del conductor, impidiendo borrar autos que todavía tengan estadías impagas o reservas activas.\n\n'
                '⚙️ FUNCIONAMIENTO: DELETE /v1/user/vehicles/{patente}. Autenticado; desvincula el vehículo de la cuenta con UserService.delete_vehicle, que verifica que no tenga reservas ni estadías activas antes de eliminarlo.'
            ),
        },
    },
    "routes/views.py": {
        "proposito": 'Sirve las páginas HTML del frontend con Jinja2: cada ruta GET devuelve la plantilla correspondiente desde templates/, con la configuración global (settings) y un cache_buster (timestamp) inyectados en todos los contextos. Solo la vista de red inyecta datos de BD (sucursales); el resto son páginas estáticas que consumen la API por JS.',
        "simbolos": {
            "get_instalar": (
                '💡 LA IDEA: Es la guía interactiva para instalar la aplicación web en el celular o computadora como una app nativa (PWA).\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita el acceso rápido de los conductores desde la pantalla de inicio de su teléfono sin pasar por las tiendas de apps.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /instalar. Devuelve la plantilla instalar.html (pantalla de instalación/PWA).'
            ),
            "get_index": (
                '💡 LA IDEA: Es la vidriera principal del sitio web con la presentación de la empresa, buscador de estacionamientos y accesos rápidos.\n\n'
                '🎯 POR QUE FUE GENERADA: Recibe a los visitantes casuales y clientes recurrentes, ofreciéndoles una experiencia moderna y fluida desde el navegador.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /. Devuelve la plantilla index.html, la página principal del sitio.'
            ),
            "get_dashboard": (
                '💡 LA IDEA: Es el centro de mando operativo donde los empleados de garita y administradores supervisan barreras, cámaras y aforos.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza todas las herramientas de gestión del estacionamiento en una interfaz web ágil y en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /dashboard. Devuelve la plantilla dashboard.html, el panel operativo del estacionamiento.'
            ),
            "get_perfil": (
                '💡 LA IDEA: Es el portal personal del cliente donde administra sus reservas, vehículos, pagos, puntos y datos personales.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga al conductor autoservicio integral para resolver todas sus necesidades de estacionamiento sin intermediarios.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /perfil. Devuelve la plantilla perfil.html, la cuenta del usuario; es además el destino de la redirección tras los retornos de MercadoPago (?mp_status=&mp_tipo=).'
            ),
            "get_nuestra_red": (
                '💡 LA IDEA: Es el mapa interactivo de sucursales que muestra la ubicación de cada estacionamiento, horarios, servicios y accesos.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a los conductores a descubrir estacionamientos cercanos a su destino y conocer sus comodidades.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /nuestra-red. Única vista con datos: consulta BranchRepository.get_all(db) y renderiza nuestra_red.html con la lista de sucursales (context branches) para mostrar la red de estacionamientos.'
            ),
            "get_contacto": (
                '💡 LA IDEA: Es el canal de comunicación comercial para que empresas o conductores envíen mensajes a la administración central.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita el contacto con clientes corporativos o consultas generales por fuera del sistema de tickets de soporte.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /contacto. Devuelve la plantilla contacto.html (formulario e información de contacto).'
            ),
            "get_terminos": (
                '💡 LA IDEA: Es el contrato legal de términos y condiciones de uso del servicio de estacionamiento y la plataforma digital.\n\n'
                '🎯 POR QUE FUE GENERADA: Cumple con los requisitos legales y normativos de defensa al consumidor y delimitación de responsabilidades.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /terminos. Devuelve la plantilla terminos.html (términos y condiciones).'
            ),
            "get_privacidad": (
                '💡 LA IDEA: Es la declaración formal sobre el tratamiento y resguardo de datos personales, patentes y fotos captadas por cámaras.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga seguridad jurídica y transparencia a los clientes sobre cómo se almacenan y protegen sus datos.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /privacidad. Devuelve la plantilla privacidad.html (política de privacidad).'
            ),
            "get_reset_password": (
                '💡 LA IDEA: Es la pantalla donde el usuario escribe su nueva contraseña al ingresar desde el enlace que recibió en su correo.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee una interfaz limpia y aislada para completar la recuperación de clave de forma intuitiva.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /reset-password. Devuelve la plantilla reset_password.html, la pantalla para establecer una contraseña nueva desde el enlace enviado por correo.'
            ),
            "get_monitoreo": (
                '💡 LA IDEA: Es la sala de monitoreo visual en vivo para supervisar las cámaras de las barreras y las lecturas de patentes en directo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los supervisores de seguridad vigilar el flujo de vehículos y el desempeño de la visión artificial en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /monitoreo. Devuelve la plantilla monitoreo_live.html, la vista de monitoreo en vivo de cámaras/estadía.'
            ),
            "get_estadisticas_ocr": (
                '💡 LA IDEA: Es el tablero de analítica técnica que expone gráficos de precisión, tiempos de respuesta y volumen de lecturas de patentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los ingenieros de software auditar el rendimiento del motor ALPR y detectar demoras o descalibraciones en los nodos.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /estadisticas-ocr. Devuelve la plantilla estadisticas_ocr.html, el reporte de métricas del reconocimiento de patentes.'
            ),
        },
    },
}
