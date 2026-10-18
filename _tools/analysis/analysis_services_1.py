"""Explicaciones analizadas de services (parte 1 de 2, análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "services/access_occupancy.py": {
        "proposito": 'Contabilidad de plazas compartida por todos los flujos de acceso (ALPR, QR y manuales): suma y resta ocupación física y plazas de reserva por tipo de vehículo sobre el aforo de planta baja o un piso, con contadores que nunca quedan en negativo.',
        "simbolos": {
            "AccessOccupancyMixin": (
                '💡 LA IDEA: Es el ábaco de la entrada: suma y resta autos en tiempo real para saber exactamente cuántas cocheras libres quedan sin permitir que los números bajen a negativo.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita inconsistencias matemáticas en el aforo causadas por salidas no registradas o conteos desfasados.\n\n'
                '⚙️ FUNCIONAMIENTO: Mixin sin estado (métodos estáticos y de clase) del que hereda AccessService: administra los contadores de ocupación física (ocupacion_actual/motos/camionetas) y de plazas de reserva (ocupacion_reservas*) de un registro de aforo o de un piso, tolerando atributos ausentes o nulos con getattr.'
            ),
            "_tipo_lower": (
                "💡 LA IDEA: Es el clasificador que convierte el tipo de rodado a minúsculas estándar para no confundir 'Auto' con 'auto'.\n\n"
                '🎯 POR QUE FUE GENERADA: Garantiza que el contador correcto (autos, motos o camionetas) se actualice sin importar cómo se escribió el texto.\n\n'
                "⚙️ FUNCIONAMIENTO: Normaliza un tipo de vehículo a minúsculas: si recibe un enum (VehicleType) toma su .value, si no usa el str del valor o 'Auto' por defecto; es la base para decidir a qué contador corresponde el vehículo."
            ),
            "_inc_reserva_occ": (
                '💡 LA IDEA: Ocupa una plaza del cupón de reserva: suma 1 al contador de cocheras reservadas ocupadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el sistema sepa cuántos de los autos que están adentro tenían reserva previa.\n\n'
                "⚙️ FUNCIONAMIENTO: Suma 1 a ocupacion_reservas y al contador por tipo (moto si el texto contiene 'moto', camioneta si contiene 'camioneta', si no autos) sobre el objeto recibido, inicializando en 0 los contadores faltantes."
            ),
            "_dec_reserva_occ": (
                '💡 LA IDEA: Libera una plaza de reserva cuando el auto reservado sale del predio, cuidando de nunca bajar de cero.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene los cupos de reserva exactos y protegidos contra números negativos.\n\n'
                '⚙️ FUNCIONAMIENTO: Resta 1 a los mismos contadores de reserva solo cuando son mayores a cero (protección anti-negativos), según el tipo de vehículo.'
            ),
            "_asignar_plaza": (
                '💡 LA IDEA: Es el acomodador que le da una cochera al auto que acaba de cruzar la barrera.\n\n'
                '🎯 POR QUE FUE GENERADA: Descuenta inmediatamente la plaza libre disponible para que la pantalla de la entrada se actualice.\n\n'
                '⚙️ FUNCIONAMIENTO: Asigna una plaza al ingresar: si es_reserva delega en _inc_reserva_occ; si no incrementa la ocupación física del contador que corresponde al tipo (motos, camionetas o auto general).'
            ),
            "_liberar_plaza": (
                '💡 LA IDEA: Es el acomodador despidiendo al auto en la salida y dejando la cochera lista para el próximo cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Devuelve el lugar libre al sistema en el instante en que el vehículo sale a la calle.\n\n'
                '⚙️ FUNCIONAMIENTO: Libera una plaza al egresar: si es_reserva decrementa reservas vía _dec_reserva_occ, si no la ocupación física correspondiente, nunca por debajo de cero.'
            ),
            "_capacidad_por_tipo": (
                '💡 LA IDEA: Consulta el límite máximo y la ocupación actual del tipo de vehículo que quiere entrar (auto, moto o camioneta).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al portero saber si hay espacio específico para una moto o camioneta antes de abrirle la barrera.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la tupla (capacidad, ocupación) según el tipo: capacidad_motos/ocupacion_motos para motos, capacidad_camionetas (default 5) para camionetas y capacidad_total/ocupacion_actual para autos; la usa el ingreso para validar si hay lugar.'
            ),
        },
    },
    "services/access_service.py": {
        "proposito": 'Orquesta los flujos de acceso físico al predio —entrada y salida por patente ALPR, pase QR de reservas y operaciones manuales del staff— aplicando validaciones (formato de patente, si ya está dentro, capacidad del aforo, deuda pendiente), registrando access_logs, notificando al dashboard y disparando la barrera.',
        "simbolos": {
            "AccessService": (
                '💡 LA IDEA: Es el jefe de operaciones de la barrera: cuando un auto llega a la entrada o salida, decide si la barrera se levanta, anota la foto, descuenta la cochera y avisa al panel de control.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza todo el circuito de ingreso y egreso físico, garantizando que nadie entre sin plaza ni salga sin pagar.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio que hereda AccessOccupancyMixin y concentra los flujos de acceso físico. Cada flujo consulta repositorios de accesos, reservas, vehículos y sucursales, ajusta el aforo (o un piso), persiste el AccessLog, emite notificaciones al dashboard (NotificationService) y abre la barrera (HardwareService).'
            ),
            "_save_image": (
                '💡 LA IDEA: Es el fotógrafo de la entrada: guarda la foto de la patente tomada por la cámara en la carpeta del servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite conservar la evidencia visual de cada vehículo para auditoría y reclamos.\n\n'
                '⚙️ FUNCIONAMIENTO: Decodifica la imagen en base64 que envía el lector ALPR y la guarda en settings.IMAGE_DIR con nombre patente_HHMMSS.jpg (crea el directorio si no existe); devuelve el nombre del archivo o None si no vino imagen.'
            ),
            "_publish_mqtt": (
                '💡 LA IDEA: Es la señal de radio rápida enviada a la barrera para que se mueva.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona comunicación ultrarrápida con los motores electromecánicos del portón.\n\n'
                '⚙️ FUNCIONAMIENTO: Publica un payload JSON en un topic MQTT usando el cliente embebido en la app (request.app.mqtt_client); es un acceso directo puntual, ya que el cierre de barreras está centralizado en HardwareService.'
            ),
            "_branch_from_gate_id": (
                "💡 LA IDEA: Deduce en qué sucursal está parada la barrera a partir de su código (ej: de 'ITUZAINGO_ENTRADA_1' deduce 'Ituzaingó').\n\n"
                '🎯 POR QUE FUE GENERADA: Permite que un solo servidor controle barreras distribuidas en distintas ciudades sin confundirlas.\n\n'
                "⚙️ FUNCIONAMIENTO: Resuelve el nombre completo de la sucursal a partir del prefijo del gate_id ALPR (todo antes del primer '_'): lo normaliza y lo compara con los nombres normalizados de todas las sucursales; devuelve None si no matchea o si hay error, sin cortar el flujo."
            ),
            "_unclosed_last_entry": (
                '💡 LA IDEA: Busca si ese auto ya está adentro del predio sin haber registrado su salida.\n\n'
                "🎯 POR QUE FUE GENERADA: Evita que el mismo auto 'entre dos veces' sin haber salido, lo que arruinaría las cuentas de estadía.\n\n"
                '⚙️ FUNCIONAMIENTO: Devuelve la última ENTRADA de la patente en la sucursal que no tiene una SALIDA posterior (el vehículo sigue adentro), o None si no hay ingreso abierto.'
            ),
            "_get_aforo": (
                '💡 LA IDEA: Lee el cartel de ocupación actual de la sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite verificar la disponibilidad de cocheras antes de tomar decisiones de paso.\n\n'
                '⚙️ FUNCIONAMIENTO: Trae el registro de aforo de la sucursal vía BranchRepository.get_aforo_by_sucursal.'
            ),
            "_get_or_create_aforo": (
                '💡 LA IDEA: Trae el aforo de la sede o crea uno con valores por defecto si la playa recién se instala.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita caídas del sistema en sucursales nuevas que todavía no terminaron su configuración.\n\n'
                '⚙️ FUNCIONAMIENTO: Igual que _get_aforo pero si la sucursal no tiene aforo crea en memoria uno por defecto (20 autos, 10 motos) y lo agrega a la sesión para que las asignaciones de plaza tengan dónde impactar.'
            ),
            "_suc_key": (
                '💡 LA IDEA: Normaliza el nombre de la sucursal para los canales de notificación en vivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los mensajes WebSocket lleguen al canal correcto del panel del guardia.\n\n'
                "⚙️ FUNCIONAMIENTO: Clave normalizada de sucursal para los diccionarios de notificación, usando 'GLOBAL' cuando la sucursal es None."
            ),
            "_emit_pending_exit": (
                '💡 LA IDEA: Es la alarma de cobro: cuando un auto intenta salir sin haber pagado, le frena la barrera y hace saltar una ventana en la pantalla del cajero con el monto adeudado.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que los clientes se retiren sin abonar la estadía, dándole al personal la herramienta para cobrar en el acto.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma el evento de salida con deuda: calcula el monto con BillingService.preview_pending_amount, identifica al dueño del vehículo (VehicleRepository) y emite notify_pending_exit al dashboard con patente, log_id, deuda, usuario, sucursal y gate; cualquier error solo se loguea para no interrumpir el intento de salida.'
            ),
            "validate_plate": (
                '💡 LA IDEA: Es el circuito completo de entrada por cámara: lee la patente, verifica que sea válida, revisa si tiene reserva o si hay lugar libre, guarda la foto, descuenta la cochera y abre la barrera.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el cerebro del ingreso 100% automatizado y sin tickets de papel de AUTOPASS.\n\n'
                '⚙️ FUNCIONAMIENTO: Flujo de entrada ALPR: normaliza la patente y la valida con is_valid_plate (rechaza sin registrar si el formato es inválido), comprueba con _unclosed_last_entry que el vehículo no esté ya dentro, detecta tipo de vehículo y reserva vigente en el rango actual, guarda la foto y asigna plaza (de reserva si hay reserva, activándola si estaba PENDIENTE; si no, física mientras haya capacidad por tipo; sin capacidad rechaza). Registra el AccessLog ENTRADA, notifica evento y aforo, dispara la barrera de ENTRADA vía HardwareService y devuelve {status, action, message}.'
            ),
            "exit_plate": (
                '💡 LA IDEA: Es el circuito completo de salida por cámara: comprueba que el auto haya entrado, verifica si pagó la estadía o si está dentro de los 10 minutos de cortesía, libera la cochera y abre el portón de salida.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza salidas fluidas y automatizadas cobrando hasta el último minuto a quien corresponda.\n\n'
                '⚙️ FUNCIONAMIENTO: Flujo de salida ALPR: exige un último evento ENTRADA en la sucursal (si no, error); si el log no está pagado y la reserva tampoco aplica cortesía de 10 minutos y, pasado ese plazo, niega la salida emitiendo el popup de deuda con _emit_pending_exit. Si pasa, libera la plaza del aforo (reserva o física), registra el AccessLog SALIDA, notifica aforo y dispara la barrera de SALIDA.'
            ),
            "validate_qr": (
                '💡 LA IDEA: Es el molinete que lee el pase digital QR: valida la reserva desde la pantalla del celular y abre la barrera de entrada o de salida.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los clientes entrar y salir sin depender de la cámara ALPR si la patente está embarrada o de noche.\n\n'
                "⚙️ FUNCIONAMIENTO: Flujo del pase digital QR: resuelve la sucursal desde el gate_id, valida el formato 'AUTOPASS|ID:x|PLATE:y', que la reserva exista, que la patente coincida y que la reserva sea de esa sede, y decide entrada o salida según el gate_id. En entrada rechaza si ya está dentro, si la reserva está completada/cancelada o fuera de su rango horario, asigna plaza (activando la reserva PENDIENTE) y registra ENTRADA; en salida exige ingreso previo, aplica la cortesía de 10 minutos contra deuda, libera plaza y registra SALIDA. En ambos casos notifica y abre la barrera; las excepciones HTTP se repropagan y el resto se captura devolviendo status error."
            ),
            "manual_entry": (
                '💡 LA IDEA: Es el botón de auxilio del guardia: permite dar ingreso manual a un vehículo desde la pantalla del operador si la cámara falló.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el estacionamiento nunca se trabe ante problemas climáticos o fallas de visión artificial.\n\n'
                '⚙️ FUNCIONAMIENTO: Alta manual de ingreso por staff: valida el formato de patente (HTTPException 400 si es inválida), si el vehículo ya está dentro devuelve el registro existente sin duplicar, busca reserva vigente y asigna plaza en el piso indicado (floor_id, 404 si no existe) o en el aforo de la sucursal, registrando el AccessLog con sucursal y piso. Notifica aforo y barrera dejando los errores de hardware solo en el log.'
            ),
            "manual_exit": (
                '💡 LA IDEA: Es el botón de salida forzada del operador: permite dar salida manual en ventanilla cobrando la deuda o validando el ticket en mano.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve contingencias físicas en el egreso de vehículos.\n\n'
                '⚙️ FUNCIONAMIENTO: Salida manual por staff: exige un ingreso previo en la sede (HTTPException 400) y, si el log no está pagado y ya pasó la cortesía de 10 minutos, responde 403 con el detalle de la deuda. Libera la plaza del aforo y del piso si corresponde, registra la SALIDA (con costo 0 si cayó en cortesía) y notifica aforo y barrera.'
            ),
            "cancel_stay": (
                '💡 LA IDEA: Es la anulación de una estadía: si el auto entró por error y se fue antes de los 10 minutos, cancela la estadía sin cargo; si se quedó más tiempo, liquida la deuda antes de cerrar.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve el caso común del conductor que ingresa equivocadamente y sale de inmediato sin generarle una deuda injusta.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancela una estadía activa desde caja/admin: exige ingreso previo (400) y libera la plaza del aforo y del piso. Si la estadía duró 10 minutos o menos la cierra sin cargo; si excedió la cortesía y no está pagada calcula la deuda con BillingService.calculate_debt y lanza 402 con el monto (409 si la sucursal no tiene tarifario); si estaba pagada la cierra normalmente. Al final avisa al dueño del vehículo con UserNotificationService (notificación STAY_CANCELLED_ADMIN).'
            ),
        },
    },
    "services/availability.py": {
        "proposito": 'Motor de disponibilidad de reservas: calcula la capacidad de plazas de reserva por tipo de vehículo (PB + pisos), la ocupación máxima simultánea con un algoritmo sweep-line y las fechas/horas que hay que deshabilitar en los selectores del front, con caché corta para no recalcular en cada request.',
        "simbolos": {
            "_capacidad_reservas_para_tipo": (
                '💡 LA IDEA: Cuenta cuántas cocheras exclusivas para reservas tiene la sucursal sumando la planta baja y todos los pisos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite conocer el límite exacto de turnos que se pueden vender por adelantado.\n\n'
                '⚙️ FUNCIONAMIENTO: Capacidad total de plazas exclusivas de reserva de una sede para un tipo de vehículo: si hay pisos suma su capacidad_reservas_{autos,motos,camionetas} (y la usa cuando da > 0); si no lee el aforo de PB. Devuelve 5 por defecto sin dato y 0 si el aforo existe pero está en cero.'
            ),
            "capacidad_reservas": (
                '💡 LA IDEA: Es la ventanilla pública para consultar el cupo máximo de reservas de una sede.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que otras capas del sistema tengan que sumar pisos a mano.\n\n'
                '⚙️ FUNCIONAMIENTO: Fachada pública de _capacidad_reservas_para_tipo: capacidad de reservas de la sede para el tipo indicado (PB + pisos).'
            ),
            "_reservas_activas_tipo": (
                '💡 LA IDEA: Busca todas las reservas vigentes que coinciden con un horario y las filtra por tipo de vehículo.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que una reserva de camioneta ocupe el cupo pensado para autos chicos.\n\n'
                "⚙️ FUNCIONAMIENTO: Trae las reservas activas/pendientes que se solapan con el rango [desde, hasta) en la sede (ReservationRepository.get_active_overlapping, con exclude_id opcional) y las filtra por tipo de vehículo real: cruza las patentes con VehicleRepository.get_tipos_by_patentes y se queda solo con las del tipo pedido (fallback al tipo guardado en la reserva o 'Auto')."
            ),
            "_get_cached_availability": (
                '💡 LA IDEA: Es la memoria rápida de 30 segundos: si 50 personas preguntan la disponibilidad al mismo tiempo, calcula una sola vez y le muestra la misma respuesta a todos.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita saturar el servidor con cálculos matemáticos repetitivos durante horarios pico de reservas.\n\n'
                '⚙️ FUNCIONAMIENTO: Caché en memoria con TTL de 30 segundos (_CACHE_AVAILABILITY) para los cálculos de disponibilidad: si la clave existe y no venció devuelve el valor guardado; si no ejecuta el generador y almacena el resultado con su timestamp monótono.'
            ),
            "_calcular_ocupacion_maxima_simultanea": (
                "💡 LA IDEA: Es el algoritmo de la 'línea de tiempo' (sweep-line): simula minuto a minuto cuántos autos habrá estacionados a la vez para encontrar el momento de mayor congestión.\n\n"
                '🎯 POR QUE FUE GENERADA: Es el corazón matemático que impide sobrevender turnos que se solapan parcialmente.\n\n'
                '⚙️ FUNCIONAMIENTO: Ocupación máxima simultánea de reservas dentro de un intervalo con sweep-line: convierte cada reserva en eventos +1 (entrada) y -1 (salida) recortados al intervalo, los ordena (salidas antes que entradas en empates) y calcula la máxima corrida acumulada. Las reservas que empiezan antes del intervalo cuentan en el conteo base y, si las fechas no se pueden parsear, devuelve len(reservas) como estimación conservadora.'
            ),
            "verificar_disponibilidad": (
                "💡 LA IDEA: Responde con total certeza: 'Sí, hay lugar' o 'No, el estacionamiento está lleno para ese horario'.\n\n"
                '🎯 POR QUE FUE GENERADA: Da la luz verde para permitir al cliente continuar con el pago de su reserva.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve {disponible, capacidad_total, ocupada, restan, mensaje} para un periodo y tipo de vehículo: toma la capacidad de reservas de la sede, filtra las reservas solapadas por tipo y calcula la ocupación máxima con sweep-line; si la capacidad es cero informa que la sede no tiene plazas para ese tipo.'
            ),
            "obtener_fechas_deshabilitadas": (
                '💡 LA IDEA: Es el calendario con días tachados en gris: pinta en gris los días donde ya no queda ninguna cochera libre para que el usuario no pierda tiempo haciendo clic.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda una experiencia de usuario ágil y visualmente clara en el selector de fechas.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista las fechas (YYYY-MM-DD) a bloquear en el selector de fechas (hasta 90 días por defecto, desde hoy o desde fecha_desde) porque para esa fecha y tipo de estadía no queda plaza libre; normaliza la fecha base con TimeService y cachea el cálculo con clave por sede, tipo, estadía, fecha y días.'
            ),
            "_calcular_fechas_deshabilitadas": (
                '💡 LA IDEA: Hace la matemática pesada para revisar los próximos 90 días y detectar cuáles están totalmente colmados.\n\n'
                '🎯 POR QUE FUE GENERADA: Optimiza el escaneo de disponibilidad a futuro en una sola pasada.\n\n'
                "⚙️ FUNCIONAMIENTO: Núcleo del bloqueo de fechas: con una única consulta de reservas solapadas sobre toda la ventana evaluada recorre cada día y marca deshabilitado si la ocupación máxima iguala la capacidad —para 'hora' solo si ninguna de las 24 horas tiene lugar, para día/semana/quincena/mes chequeando la ventana de duración correspondiente (1/7/15/30 días)—. Si la capacidad es cero, todas las fechas quedan deshabilitadas."
            ),
            "obtener_horas_deshabilitadas": (
                '💡 LA IDEA: Tacha los horarios ocupados del día seleccionado (ej: 14:00 a 16:00 lleno).\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el cliente elija un turno en una franja horaria saturada.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve los slots HH:MM de un día que no se pueden reservar (paso configurable, 30 min por defecto); limpia la fecha recibida y delega en _calcular_horas_deshabilitadas con caché corta.'
            ),
            "obtener_horas_deshabilitadas_con_reservas": (
                '💡 LA IDEA: Dibuja la grilla horaria distinguiendo qué bloques están ocupados por reservas y cuáles por margen de seguridad.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta los gráficos interactivos de turnos del panel de clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Combina los slots deshabilitados con los rangos realmente ocupados por reservas del día ({disabled_hours, reserved_ranges}) para que la grille del front distinga lo reservado de lo solo bloqueado por solapamiento o margen; exclude_id permite editar una reserva sin contar su propio rango.'
            ),
            "_obtener_rangos_reservados_dia": (
                '💡 LA IDEA: Extrae los intervalos de inicio y fin de las reservas del día.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite dibujar las barritas ocupadas en la agenda visual.\n\n'
                '⚙️ FUNCIONAMIENTO: Rangos [inicio, fin) en HH:MM de las reservas activas del tipo que tocan el día, recortados a los límites del día (fechas inválidas o invertidas se descartan); es lo que la grille pinta como ocupado por reserva.'
            ),
            "_calcular_horas_deshabilitadas": (
                '💡 LA IDEA: Revisa cada fracción de 30 minutos del día y bloquea las que superen el cupo o las que violen el tiempo mínimo de anticipación.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que alguien reserve un turno para dentro de 5 minutos si la regla exige 30 minutos de antelación.\n\n'
                '⚙️ FUNCIONAMIENTO: Recorre el día en pasos y marca cada slot si la ocupación máxima de su rango (slot más duración) alcanza la capacidad de reservas, o si es hoy y el slot no respeta la anticipación mínima settings.RESERVA_HORA_MIN_SEGUNDOS (incluye los ya pasados, mínimo el actual). Si la capacidad es cero bloquea todos los slots; las reservas se consultan una sola vez con una ventana que cubre el día completo más la duración máxima de un slot para no perder los que cruzan la medianoche.'
            ),
        },
    },
    "services/billing_service.py": {
        "proposito": 'Tarifación y cobros: resuelve tarifas por sede, modalidad y tipo de vehículo desde settings (con caché TTL), aplica la regla escalonada por fracciones de 30 minutos, calcula deudas y montos de reserva, otorga puntos de fidelización y confirma pagos de estadías, incluido el pago por Mercado Pago.',
        "simbolos": {
            "BillingService": (
                '💡 LA IDEA: Es el cajero automático y calculador de tarifas: aplica las reglas de precios por hora y fracción, liquida estadías y acredita puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la matemática del dinero para asegurar que nunca se cobre de más ni de menos.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio estático de facturación: tarifas, montos, deudas, puntos y confirmación de cobros de estadías y reservas en predio. Sigue la política de no inventar precios: si la sede no tiene tarifario configurado devuelve None o un mensaje de error para que la capa superior decida.'
            ),
            "_tipo_key": (
                '💡 LA IDEA: Es el selector de tarifa por vehículo: clasifica en Auto, Moto o Camioneta para buscar la fila de precios correcta.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita cobrarle tarifa de camioneta a una moto por un error de texto.\n\n'
                "⚙️ FUNCIONAMIENTO: Normaliza cualquier variante de tipo de vehículo ('MOTO', 'moto', 'camioneta', 'utilitario', enum, etc.) a la clave canónica 'Auto', 'Moto' o 'Camioneta' para armar la clave de settings."
            ),
            "get_rate": (
                '💡 LA IDEA: Busca el precio oficial de una modalidad (hora, día, mes) para una playa y rodado puntual.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite consultar tarifas actualizadas respetando los precios propios de cada sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Tarifa de una modalidad (hora/dia/semana/quincena/mes) para sede y tipo de vehículo: arma la clave precio_<modalidad>[_moto|_camioneta] y la lee con SettingsRepository.get_by_clave_and_sucursal (estricta por sede: no hereda la global; con sucursal None usa la global). Cachea 300 segundos en ttl_cache y devuelve None si no existe.'
            ),
            "get_hourly_rate": (
                '💡 LA IDEA: Obtiene la tarifa de la primera hora base.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el valor fundamental para cotizaciones rápidas de estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Tarifa por hora base de la sede/tipo (precio_hora con sufijo _moto o _camioneta) con el mismo caché de 300 segundos y la política de no inventar precio (None si falta).'
            ),
            "get_30min_rate": (
                '💡 LA IDEA: Obtiene el costo de la fracción de media hora (o la mitad de la hora si no está configurada).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite fraccionar el cobro de forma justa según el tiempo real utilizado.\n\n'
                '⚙️ FUNCIONAMIENTO: Tarifa de la fracción de 30 minutos (precio_30min...); si no está configurada usa la mitad de la tarifa por hora y solo devuelve None cuando no existe ninguna de las dos.'
            ),
            "hourly_amount_from_rates": (
                '💡 LA IDEA: Es la fórmula escalonada de cobro: divide el tiempo en bloques de 30 minutos y va cobrando horas y fracciones en escala.\n\n'
                '🎯 POR QUE FUE GENERADA: Cumple con las regulaciones de fraccionamiento comercial de estacionamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Regla escalonada de cobro por hora dadas las tarifas: n = ceil(horas*2) bloques de 30 minutos con mínimo 1; con 1 bloque cobra la fracción, con n>=2 alterna hora/fracción partiendo por hora: (n//2)*hora + ((n-1)//2)*fraccion. Si falta una tarifa la deriva de la otra (fraccion = hora/2 o hora = fraccion*2); None si no hay ninguna.'
            ),
            "calculate_hourly_amount": (
                '💡 LA IDEA: Calcula cuánto debe pagar un auto por estar cierta cantidad de horas estacionado.\n\n'
                '🎯 POR QUE FUE GENERADA: Es la función que le pone precio a cada estadía espontánea.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica la regla escalonada a una duración en horas usando las tarifas reales de la sede y tipo de vehículo; devuelve None si la sede no tiene tarifario.'
            ),
            "calculate_debt": (
                '💡 LA IDEA: Es el taxímetro en vivo: calcula cuánto debe un auto desde que cruzó la barrera hasta este instante.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cliente o al cajero ver la cuenta en tiempo real antes de salir.\n\n'
                '⚙️ FUNCIONAMIENTO: Deuda de una estadía abierta: calcula las horas transcurridas desde entry_time hasta TimeService.now() (reloj virtual) y devuelve el monto con calculate_hourly_amount; None si falta tarifario.'
            ),
            "preview_pending_amount": (
                '💡 LA IDEA: Es el presupuesto de salida en pantalla: muestra cuánto debe pagar el auto sin tocar la base de datos todavía.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra el importe en el cartel de la barrera o en la ventanilla del cajero.\n\n'
                '⚙️ FUNCIONAMIENTO: Previsualiza sin modificar nada lo que debe una estadía impaga (para el popup de caja): si el log tiene reserva impaga cobra el monto_total de la reserva y, si ya venció, le suma el extra desde fecha_fin; sin reserva, cobra la deuda desde la entrada. Devuelve None si falta tarifario.'
            ),
            "calculate_total_amount": (
                '💡 LA IDEA: Calcula el costo total de una reserva según si es por horas, días, semanas o meses.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el cálculo oficial de presupuesto que se cobra al momento de reservar.\n\n'
                "⚙️ FUNCIONAMIENTO: Monto total de una reserva según duración y modalidad: 'hora' usa la regla escalonada; el resto multiplica la tarifa por la cantidad de períodos (ceil de días/24, semanas, quincenas o meses de 30 días) con mínimo 1 día. Devuelve 0 si la duración es ≤ 0 y None si falta la tarifa."
            ),
            "snapshot_tarifas": (
                "💡 LA IDEA: Es la 'foto' del precio al momento de contratar: guarda qué tarifa regía el día que el cliente reservó.\n\n"
                '🎯 POR QUE FUE GENERADA: Protege al cliente para que si la empresa aumenta los precios la semana que viene, a él se le respete el precio congelado al reservar.\n\n'
                '⚙️ FUNCIONAMIENTO: Foto de las tarifas vigentes (hora, fracción y aplicada) junto a las horas usadas al cotizar una reserva; se persiste en la reserva para reconstruir el precio histórico aunque después cambie el tarifario.'
            ),
            "calculate_points": (
                '💡 LA IDEA: Es la máquina de sumar puntos de regalo: otorga 10 puntos por cada $1.000 gastados en estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Premia la fidelidad de los conductores incentivándolos a volver.\n\n'
                '⚙️ FUNCIONAMIENTO: Puntos ganados por un pago: 10 puntos por cada $1000 (int(monto/100)), mínimo 1 si monto > 0 y 0 si no se pagó nada.'
            ),
            "apply_stay_mp_payment": (
                '💡 LA IDEA: Confirma el pago de una estadía abonada mediante Mercado Pago y le otorga los puntos al titular.\n\n'
                '🎯 POR QUE FUE GENERADA: Cierra la cuenta y deja la barrera lista para levantarse cuando el auto llegue a la salida.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca una estadía como pagada por Mercado Pago (Checkout Pro) sin descontar saldo: si ya estaba pagada devuelve aplicado False; si no, actualiza el log (pago_confirmado, metodo MERCADOPAGO, costo y fecha), acredita puntos al dueño del vehículo (o al usuario recibido) con PointsLog, notifica STAY_PAID y POINTS_EARNED (errores solo logueados) y hace commit. Devuelve monto_cobrado y puntos_ganados.'
            ),
            "_extra_vencimiento_ya_cobrado": (
                '💡 LA IDEA: Revisa si el tiempo extra que el auto se quedó después de vencer su reserva ya fue pagado.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita cobrarle dos veces el recargo por retraso al cliente.\n\n'
                '⚙️ FUNCIONAMIENTO: Indica si el extra por reserva vencida ya fue cobrado para esta estadía: compara la fecha_pago del log con la fecha_fin de la reserva y devuelve True si el pago ocurrió después del vencimiento (ese tramo ya está incluido). Fechas ausentes o inválidas dan False.'
            ),
            "process_payment": (
                '💡 LA IDEA: Es el cobro en efectivo por mostrador: recibe la patente, cobra la deuda, otorga puntos y marca la estadía como saldada.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los empleados de cabina despachar autos que pagan en mano rápidamente.\n\n'
                '⚙️ FUNCIONAMIENTO: Cobra una estadía pendiente en caja por patente (valida formato con is_valid_plate): trae la última entrada y distingue cuatro casos —log ya pagado con reserva vencida: cobra solo el extra desde fecha_fin, una sola vez (control con _extra_vencimiento_ya_cobrado); reserva impaga ya ingresada: cobra monto_total más extra si venció y marca la reserva PAGADA y ACTIVA; reserva pagada online pero log sin pagar: solo el extra; sin reserva: deuda desde la entrada—. Si falta tarifario responde error sin cobrar; al confirmar suma puntos, registra PointsLog, notifica al titular (STAY_PAID y POINTS_EARNED) y hace commit. Devuelve {status, monto_cobrado, puntos_ganados}.'
            ),
        },
    },
    "services/branch_service.py": {
        "proposito": 'Fachada de sucursales para las vistas y operaciones del admin: datos de contacto y horario, tarifario completo, resumen de capacidad/ocupación (PB + pisos), verificación de ocupación previa a operaciones destructivas y renombrado que propaga el cambio a las cámaras ALPR.',
        "simbolos": {
            "BranchService": (
                '💡 LA IDEA: Es el administrador general de sucursales: entrega resúmenes de sedes, tarifas, capacidad de pisos y gestiona mudanzas o cambios de nombre.\n\n'
                '🎯 POR QUE FUE GENERADA: Agrupa toda la gestión operativa de playas en un solo lugar.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio estático que expone las sucursales como vistas listas para el front (info, tarifas, resúmenes) y realiza operaciones administrativas sensibles como renombrar la sede; delega en BranchRepository, SettingsRepository, UserRepository y BillingService.'
            ),
            "get_branch_info_str": (
                "💡 LA IDEA: Es la tarjeta de dirección y horarios en texto legible para el cliente (ej: 'Av. Rivadavia 1234. Abierto 24hs').\n\n"
                '🎯 POR QUE FUE GENERADA: Facilita mostrar la dirección completa en tickets y avisos de confirmación.\n\n'
                "⚙️ FUNCIONAMIENTO: Texto de dirección y horario de una sede: busca por nombre exacto, luego por LIKE y por último por coincidencia parcial entre todas; si hay dirección devuelve 'direccion. Abierto 24hs|horario.', si no 'Dirección no disponible'."
            ),
            "get_branch_tariffs": (
                '💡 LA IDEA: Arma la tabla de precios completa de una sucursal para autos, motos y camionetas.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta la cartelera de precios visible en la web.\n\n'
                '⚙️ FUNCIONAMIENTO: Diccionario de tarifas de la sede: 5 modalidades (hora, dia, semana, quincena, mes) por 3 tipos de vehículo (auto, moto, camioneta) consultando BillingService.get_rate, con claves tarifa_<modalidad>[_moto|_camioneta] (None cuando la sede no tiene esa tarifa).'
            ),
            "get_branch_capacity_summary": (
                "💡 LA IDEA: Suma las plazas de todos los pisos para decir: 'Esta sucursal tiene 150 cocheras en total'.\n\n"
                '🎯 POR QUE FUE GENERADA: Entrega los números totales para los reportes de aforo del panel admin.\n\n'
                '⚙️ FUNCIONAMIENTO: Suma capacidades y ocupaciones de la sucursal con sus pisos usando getattr con defaults para atributos inexistentes: totales por tipo de vehículo y de plazas de reserva, generando 14 claves capacidad_*_total y ocupacion_*_total para el panel.'
            ),
            "has_physical_occupancy": (
                '💡 LA IDEA: Es el detector de autos presentes: avisa si todavía hay vehículos adentro de la playa.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que un administrador borre o deshabilite una sucursal que todavía tiene autos estacionados adentro.\n\n'
                '⚙️ FUNCIONAMIENTO: True si la sede tiene vehículos estacionados: revisa la ocupación física y de reservas del aforo de planta baja y luego la suma de todas las ocupaciones de los pisos; se usa como guarda antes de operaciones como eliminar o renombrar.'
            ),
            "rename_branch": (
                '💡 LA IDEA: Es el trámite de cambio de nombre de una playa: renombra la sede y avisa a las cámaras para que cambien sus canales de transmisión.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que al cambiarle el nombre a una sede las cámaras de video queden mudas o desconectadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Renombra la sede validando que no exista otra con ese nombre (HTTPException 400) y renombra en parking_branches (las tablas dependientes referencian por sucursal_id, que no cambia). Si el prefijo normalizado varía, remapea las claves de settings CAMERA_SOURCE_<viejo> a <nuevo> y detiene los procesos ALPR del prefijo viejo (taskkill en Windows, terminate en el resto) para que el espectador y el proceso converjan al mismo canal.'
            ),
            "list_branches_with_summary": (
                '💡 LA IDEA: Prepara la lista de todas las playas con su administrador a cargo, ocupación y precios para el panel de control.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona la vista global de control para el dueño de la cadena de estacionamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Listado de sucursales (filtrable por organización) enriquecido para el admin: adjunta a cada una el nombre del administrador de sede (o 'Sin asignar'), el resumen de capacidad/ocupación y el tarifario completo, seteando todo como atributos sobre el objeto para el template."
            ),
        },
    },
    "services/email_service.py": {
        "proposito": 'Envío de correos transaccionales por SMTP con plantillas Jinja2 de templates/emails: genera el HTML, incrusta el logo en base64 y el QR del pase digital, y despacha cada envío en un hilo aparte para no bloquear la respuesta de la API.',
        "simbolos": {
            "EmailService": (
                '💡 LA IDEA: Es la oficina de correos: redacta y despacha los emails con logos, pases digitales QR y recordatorios de pago.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los mensajes viajen de forma asíncrona sin frenar la velocidad del sitio web.\n\n'
                '⚙️ FUNCIONAMIENTO: Servicio estático de correo electrónico: renderiza plantillas, arma mensajes MIME multipart y los envía por SMTP (configurado en settings) desde un hilo daemon. No lanza errores al llamador: los fallos de envío solo se loguean con el correo enmascarado.'
            ),
            "_render_template": (
                '💡 LA IDEA: Rellena la plantilla del correo con el nombre del cliente y los datos de su turno.\n\n'
                '🎯 POR QUE FUE GENERADA: Produce correos con diseño visual profesional y personalizado.\n\n'
                '⚙️ FUNCIONAMIENTO: Renderiza una plantilla de templates/emails con el entorno Jinja2 global y el contexto indicado, devolviendo el HTML resultante.'
            ),
            "_get_logo_base64": (
                '💡 LA IDEA: Empaqueta la imagen del logo dentro del propio correo electrónico.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el logo se vea siempre, incluso si el cliente abre el email sin conexión a internet.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee el logo del disco desde settings.LOGO_PATH y lo devuelve en base64 para incrustarlo en los correos; si no existe o falla la lectura devuelve cadena vacía y loguea el error.'
            ),
            "_send_email": (
                '💡 LA IDEA: Se conecta al servidor de correo (SMTP) y despacha el mensaje hacia la casilla del destinatario.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el motor de transmisión de correos electrónicos del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Envío sincrónico real (corre dentro del hilo): arma un MIMEMultipart con el HTML, conecta a settings.SMTP_SERVER:SMTP_PORT, hace STARTTLS si SMTP_TLS, autentica con SMTP_USER/SMTP_PASSWORD si están definidos y envía desde SMTP_FROM. Cualquier excepción se captura y registra con mask_email.'
            ),
            "send_async_email": (
                '💡 LA IDEA: Despacha el correo en un hilo secundario para que el servidor web responda al instante al usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el cliente espere 3 segundos frente a la pantalla mientras se envía un email.\n\n'
                '⚙️ FUNCIONAMIENTO: Lanza _send_email en un hilo daemon para que la API no espere la respuesta del servidor SMTP.'
            ),
            "send_recovery_email": (
                '💡 LA IDEA: Envía el enlace secreto para que el usuario pueda restablecer su contraseña olvidada.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite recuperar el acceso a la cuenta de forma autónoma y segura.\n\n'
                '⚙️ FUNCIONAMIENTO: Correo de recuperación de contraseña (plantilla recovery.html) con el nombre del usuario y el enlace de recuperación, enviado de forma asíncrona.'
            ),
            "send_admin_invitation": (
                '💡 LA IDEA: Envía la invitación formal a un nuevo empleado o administrador para que active su cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite dar de alta personal de forma profesional y segura.\n\n'
                '⚙️ FUNCIONAMIENTO: Invitación a un nuevo Admin General a configurar su clave (admin_invitation.html) con la URL de activación.'
            ),
            "send_registration_confirmation": (
                '💡 LA IDEA: Es la carta de bienvenida que confirma que la cuenta de usuario ya está lista para usarse.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda una confirmación clara al cliente tras completar su registro.\n\n'
                '⚙️ FUNCIONAMIENTO: Confirma que el registro terminó porque el usuario ya definio su clave (registration_confirmation.html) con la URL de login.'
            ),
            "send_reservation_confirmation": (
                '💡 LA IDEA: Envía el voucher de reserva con el código QR para ingresar por la barrera.\n\n'
                '🎯 POR QUE FUE GENERADA: Entrega al usuario el pase digital que necesita para entrar al estacionamiento.\n\n'
                "⚙️ FUNCIONAMIENTO: Confirmación de reserva con el Pase Digital: genera el QR con contenido 'AUTOPASS|ID:x|PLATE:y' en PNG base64 con la librería qrcode, carga el logo del sistema y envía el plantilla reservation_confirmation.html."
            ),
            "send_reservation_reminder": (
                '💡 LA IDEA: Es el recordatorio preventivo 30 minutos antes del turno: avisa que el turno está por comenzar o recuerda abonar la seña.\n\n'
                '🎯 POR QUE FUE GENERADA: Reduce el ausentismo (no-show) y ayuda al cliente a llegar a tiempo.\n\n'
                "⚙️ FUNCIONAMIENTO: Recordatorio 30 minutos antes de la reserva: el asunto cambia según res_data['pagada'] (inicio de la reserva vs recordatorio de pago) y usa la plantilla reservation_reminder.html con la bandera pagada."
            ),
            "send_auto_cancelled_notification": (
                '💡 LA IDEA: Notifica al conductor que su reserva fue cancelada automáticamente porque no se presentó en horario.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene informado al cliente de que su plaza fue liberada por vencimiento del tiempo de tolerancia.\n\n'
                '⚙️ FUNCIONAMIENTO: Avisa al usuario que su reserva fue cancelada automáticamente por no ingresar a tiempo (plantilla reservation_auto_cancelled.html).'
            ),
        },
    },
    "services/hardware_service.py": {
        "proposito": 'Orquestador único del hardware de barreras: publica los comandos en los topics MQTT de entrada/salida y/o envía la orden por serie USB al Arduino Uno, con resolución explícita de portón y conexión serie thread-safe con auto-reconexión.',
        "simbolos": {
            "HardwareService": (
                '💡 LA IDEA: Es el chofer que aprieta los botones de las barreras físicas: envía órdenes por red MQTT o por cable USB al Arduino.\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica el control de portones y barreras para que el resto del sistema no tenga que lidiar con electrónica.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase con estado de clase (puerto serie, lock, nombre del puerto conectado) que unifica el control de barreras por MQTT y Serie USB. Expone trigger_barrier como punto único de apertura/cierre que intenta ambos canales.'
            ),
            "resolve_gate": (
                "💡 LA IDEA: Es el intérprete de portones: traduce palabras como 'ENTRY', 'INGRESO' o 'PUERTA_1' al comando oficial 'ENTRADA' o 'SALIDA'.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita abrir por error la barrera equivocada ante diferencias en los nombres de las cámaras.\n\n'
                "⚙️ FUNCIONAMIENTO: Traduce el gate_id a 'ENTRADA' o 'SALIDA' usando alias (INGRESO, ENTRY, IN, EGRESO, EXIT, OUT, etc.): tokeniza el id y solo acepta si todas las palabras resueltas apuntan a un único portón; si no, lanza HTTPException 400 (nunca asume SALIDA por defecto)."
            ),
            "get_serial_connection": (
                '💡 LA IDEA: Enchufa y mantiene viva la comunicación por cable USB con la plaqueta Arduino.\n\n'
                '🎯 POR QUE FUE GENERADA: Se reconecta automáticamente si el cable USB de la barrera se desconecta y se vuelve a conectar.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve y mantiene la conexión serie al Arduino bajo un lock: si ya está abierta la reutiliza; si no, con SERIAL_PORT AUTO escanea los puertos buscando Arduino/CH340/FT232/ttyACM/COM, la abre a SERIAL_BAUDRATE esperando 2 segundos por el reset del bootloader. Sin pyserial o con SERIAL_ENABLED falso devuelve None; los errores dejan la conexión en None para reintentar después.'
            ),
            "send_serial_command": (
                "💡 LA IDEA: Le manda un mensaje de texto corto al Arduino (ej: 'OPEN_ENTRADA\\n') para accionar el relé del motor.\n\n"
                '🎯 POR QUE FUE GENERADA: Levanta físicamente la barrera mecánica a través del microcontrolador.\n\n'
                '⚙️ FUNCIONAMIENTO: Envía una línea terminada en salto de línea al Arduino con la conexión activa (bajo el lock) y devuelve True si se escribió; False si no hay conexión o si la escritura falla, caso en el que invalida la conexión para forzar la reconexión.'
            ),
            "publish_mqtt": (
                '💡 LA IDEA: Manda la orden de apertura a través de la red local por ondas inalámbricas MQTT.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite comandar barreras inteligentes conectadas por Wi-Fi sin necesidad de cables largos hasta el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Publica el payload JSON en el topic indicado: usa el cliente MQTT de la aplicación (request.app.mqtt_client) si viene en el request, si no el cliente global de core.mqtt; los errores solo se loguean.'
            ),
            "trigger_barrier": (
                '💡 LA IDEA: Es el botón de apertura maestro: intenta mandar la orden tanto por MQTT como por cable USB para asegurar que la barrera se levante sí o sí.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda máxima redundancia de hardware; si un canal falla, el otro abre el paso igualmente.\n\n'
                "⚙️ FUNCIONAMIENTO: Orquesta abrir o cerrar una barrera: resuelve el portón (puede lanzar 400), normaliza el comando a OPEN/CLOSE, arma el payload (command, gate, method, timestamp más los details), lo publica en MQTT_TOPIC_ENTRADA o MQTT_TOPIC_SALIDA y envía el comando serie '<CMD>_<GATE>' al Arduino. Devuelve {status, gate, command, method, timestamp}; los dos canales se intentan siempre, independientemente del resultado de cada uno."
            ),
        },
    },
    "services/mercadopago_service.py": {
        "proposito": 'Integración con la API de Mercado Pago (Checkout Pro): creación de preferencias de pago para reservas y estadías, verificación idempotente de las acreditaciones y aplicación del cobro interno desde el webhook o los back_urls.',
        "simbolos": {
            "_headers": (
                '💡 LA IDEA: Son las credenciales y el sello de seguridad con el que AUTOPASS se presenta ante los servidores de Mercado Pago.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite autenticar cada pedido de cobro en la API de pagos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cabecera Authorization Bearer con settings.MP_ACCESS_TOKEN junto a Content-Type application/json, requerida por toda llamada a la API de Mercado Pago.'
            ),
            "_mp_request": (
                '💡 LA IDEA: Es la llamada telefónica segura hacia Mercado Pago: manda los datos y traduce cualquier error a un mensaje entendible para el usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita pantallas de error técnicas si la pasarela de pagos está caída o rechaza una operación.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta una llamada a api.mercadopago.com con timeout de 15 segundos: los errores de red y las respuestas con status >= 400 se traducen en HTTPException 502 con mensajes aptos para el usuario (lee el body JSON para el detalle del rechazo) y devuelve la respuesta JSON cuando todo va bien.'
            ),
            "_generar_external_reference": (
                '💡 LA IDEA: Es el número de comprobante único que le pegamos al cobro para no confundirlo jamás con otro.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber con exactitud matemática a qué auto y reserva pertenece cada pago que entra.\n\n'
                "⚙️ FUNCIONAMIENTO: Genera la referencia única 'AP-<TIPO>-<id>-<8 hex de uuid>' del pago interno, que se le entrega a Mercado Pago y devuelve el webhook para conciliar la notificación."
            ),
            "_get_payment_from_mp": (
                '💡 LA IDEA: Consulta a Mercado Pago cuál es el estado final de una transacción (aprobada, rechazada o pendiente).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite verificar la veracidad del cobro directamente en la fuente antes de autorizar la salida del auto.\n\n'
                '⚙️ FUNCIONAMIENTO: Consulta el pago en Mercado Pago: por payment_id (GET /v1/payments/<id>) o por external_reference (GET /v1/payments/search tomando el primer resultado); si la llamada falla devuelve None en lugar de lanzar.'
            ),
            "_monto_reserva_con_descuento": (
                '💡 LA IDEA: Aplica el descuento de los cupones de puntos sobre el precio final de la reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que a Mercado Pago se le mande a cobrar el valor exacto con la rebaja aplicada.\n\n'
                '⚙️ FUNCIONAMIENTO: Monto a cobrar por una reserva aplicando eventual descuento por canje: valida el ticket con ReservationService.validate_redemption_ticket y devuelve (monto redondeado con el porcentaje, ticket); sin ticket devuelve (monto_total, None).'
            ),
            "create_payment": (
                '💡 LA IDEA: Genera el botón de pago oficial de Checkout Pro y devuelve el link para que el usuario pague desde su celular.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite cobrar reservas y estadías con tarjetas de crédito, débito o dinero en cuenta de Mercado Pago.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea la preferencia Checkout Pro y registra la intención de pago. Valida MP_ENABLED (503); para 'reserva' exige que exista, que no esté cancelada/completada ni pagada y aplica el descuento de canje; para 'estadia' que la patente pertenezca a un vehículo del usuario (403), que no esté pagada y que haya tarifario (409 si no). Persiste MercadoPagoPayment en PENDIENTE con external_reference, exige BASE_URL https para los back_urls (400), arma la preferencia con items, expiración MP_PREFERENCE_EXPIRE_MINUTES y webhook (MP_WEBHOOK_URL); si la creación falla marca el pago FALLIDO. Devuelve init_point, external_reference, monto y preference_id."
            ),
            "confirm_payment": (
                '💡 LA IDEA: Es el inspector que revisa el comprobante de acreditación de Mercado Pago y confirma que el dinero ingresó.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el servicio se active inmediatamente cuando la pasarela avisa que el cobro fue exitoso.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica y aplica el pago de forma idempotente: si el registro ya está aplicado responde ok sin repetir; consulta a MP (por payment_id o external_reference) y ante 'approved' valida que el monto coincida (tolerancia de $1; si no, 409 y estado FALLIDO) y llama a _aplicar_pago. Los estados no cobrables (rejected, refunded, charged_back → FALLIDO; cancelled → CANCELADO) o pendientes devuelven status pending sin acreditar."
            ),
            "_aplicar_pago": (
                '💡 LA IDEA: Aplica el cobro aprobado a la cuenta interna: marca la reserva como pagada, cancela la deuda de la estadía y suma los puntos de regalo.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace efectivo el impacto contable del cobro sin tocar el saldo particular del cliente.\n\n'
                "⚙️ FUNCIONAMIENTO: Acredita el pago confirmado sin tocar el saldo del usuario: para 'reserva' delega en ReservationService.pay_reservation_mp y para 'estadia' en BillingService.apply_stay_mp_payment (404 si falta usuario, reserva o estadía; 400 si el tipo es inválido). Después marca el pago APROBADO con su payment_id y fecha de confirmación y hace commit."
            ),
        },
    },
    "services/notification_service.py": {
        "proposito": 'Bus de notificaciones en memoria del servidor: guarda el último evento de detección y las salidas impagas por sucursal, y despacha por WebSocket los broadcasts de aforo y eventos al dashboard, soportando llamadas desde hilos síncronos de FastAPI.',
        "simbolos": {
            "NotificationService": (
                '💡 LA IDEA: Es la sirena y los parlantes de la estación: avisa al instante a todas las pantallas de los empleados cuando un auto entra, sale o intenta escapar con deuda.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene a todo el personal de playa sincronizado en tiempo real a través de WebSockets sin recargar pantallas.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase con estado de clase (sin instancias) que mantiene el manager de ocupación que hace los broadcast por WebSocket, el event loop principal y diccionarios por sucursal normalizada con el último evento y las salidas impagas pendientes. La usan los services de acceso y de reservas.'
            ),
            "set_occupancy_manager": (
                '💡 LA IDEA: Conecta el altavoz WebSocket al servicio de notificaciones.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite difundir cambios de ocupación a todos los navegadores conectados.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra el manager de ocupación encargado de difundir las actualizaciones a los dashboards conectados.'
            ),
            "set_event_loop": (
                '💡 LA IDEA: Guarda el reloj de eventos asíncronos para poder mandar avisos desde cualquier rincón del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita problemas de concurrencia entre hilos de FastAPI y el servidor de WebSockets.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el event loop principal de Uvicorn para poder programar corrutinas desde hilos síncronos.'
            ),
            "_dispatch": (
                '💡 LA IDEA: Es el despachador que mete un mensaje en la cola de envío en tiempo real sin trabar el paso de los autos.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que si una notificación titila, la barrera se levante igual sin demora.\n\n'
                '⚙️ FUNCIONAMIENTO: Programa una corrutina en el loop principal: si hay loop guardado y corriendo usa asyncio.run_coroutine_threadsafe (apto desde handlers sync); si no intenta create_task sobre el loop actual; sin loop disponible o ante un error solo loguea, nunca rompe el flujo de acceso.'
            ),
            "set_last_event": (
                '💡 LA IDEA: Anota en la pizarra el último auto que pasó por la cámara para mostrarlo en el monitor del guardia.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra la última patente detectada con su foto en el tablero de control.\n\n'
                '⚙️ FUNCIONAMIENTO: Almacena el último evento de detección de una sucursal (tipo, patente, mensaje, estado y timestamp) para el cartel del dashboard.'
            ),
            "get_last_event": (
                '💡 LA IDEA: Lee el último evento de paso de la playa mientras no tenga más de 10 segundos de antigüedad.\n\n'
                '🎯 POR QUE FUE GENERADA: Oculta eventos viejos para que la pantalla del guardia solo muestre autos recién llegados.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el último evento de la sucursal solo si tiene menos de 10 segundos; si expiró devuelve None.'
            ),
            "notify_occupancy_change": (
                "💡 LA IDEA: Avisa a todos los monitores: '¡Cambió el aforo!' para que el número de cocheras libres se actualice solo.\n\n"
                '🎯 POR QUE FUE GENERADA: Mantiene los tableros de disponibilidad sincronizados al segundo en toda la red.\n\n'
                '⚙️ FUNCIONAMIENTO: Dispara de forma asíncrona el broadcast de aforo (broadcast_update con force_refresh) vía _dispatch; el parámetro db ya no se utiliza.'
            ),
            "set_pending_exit": (
                '💡 LA IDEA: Anota en la lista roja un auto que intentó salir sin pagar para abrir el popup de cobro en la cabina del cajero.\n\n'
                '🎯 POR QUE FUE GENERADA: Pone en alerta inmediata al personal cuando un vehículo con deuda llega a la barrera de salida.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra en memoria la salida impaga detectada por ALPR para la sucursal, con su payload y timestamp.'
            ),
            "get_pending_exit": (
                '💡 LA IDEA: Consulta si hay algún auto esperando en la salida con cobro pendiente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cajero ver el detalle de la deuda del auto detenido en la barrera.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el payload de la salida impaga mientras no venza su TTL de 120 segundos; si no hay o expiró devuelve None.'
            ),
            "clear_pending_exit": (
                '💡 LA IDEA: Borra la alerta de deuda una vez que el conductor pagó en efectivo en la cabina.\n\n'
                '🎯 POR QUE FUE GENERADA: Apaga la alarma y levanta la barrera para que el cliente se retire.\n\n'
                '⚙️ FUNCIONAMIENTO: Descarta la salida impaga de la sucursal, tras cobrarla en caja.'
            ),
            "notify_pending_exit": (
                '💡 LA IDEA: Dispara la ventana emergente con el cartel de cobro en la pantalla del cajero.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite cobrar en menos de 5 segundos sin que el cajero tenga que tipear la patente a mano.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda la salida impaga (set_pending_exit) y emite el evento PENDING_EXIT al dashboard para que abra el popup de cobro.'
            ),
        },
    },
    "services/oauth_service.py": {
        "proposito": 'Login social con Google y Facebook: configuración de proveedores, construcción de la URL de autorización, state firmado tipo CSRF sin cookies, intercambio de code por token, obtención y normalización del perfil, y registro de usuario mediante un código JWT de un solo uso.',
        "simbolos": {
            "_provider": (
                '💡 LA IDEA: Busca las llaves maestras de Google o Facebook configuradas en el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el sistema sepa cómo comunicarse con cada red social.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve la configuración del proveedor ('google' o 'facebook') del diccionario _PROVIDERS —client_id y client_secret se leen como lambdas para permitir monkeypatch en tests— o lanza HTTPException 404 si el nombre no está soportado."
            ),
            "is_provider_configured": (
                '💡 LA IDEA: Revisa si el botón de Google o Facebook está habilitado y con credenciales válidas.\n\n'
                '🎯 POR QUE FUE GENERADA: Oculta los botones de inicio social si la empresa no cargó las claves de esas plataformas.\n\n'
                '⚙️ FUNCIONAMIENTO: True si el proveedor tiene client_id y client_secret no vacíos en settings.'
            ),
            "enabled_providers": (
                '💡 LA IDEA: Entrega la lista de redes sociales disponibles para mostrar en la pantalla de inicio de sesión.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra solo los botones que realmente funcionan en la interfaz web.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista de [{id, label}] de los proveedores con credenciales cargadas, para mostrar en el front; ignora los HTTPException de proveedores no soportados.'
            ),
            "get_redirect_uri": (
                '💡 LA IDEA: Es la dirección de regreso a la que Google debe enviar al usuario tras iniciar sesión.\n\n'
                '🎯 POR QUE FUE GENERADA: Cumple con los protocolos internacionales de seguridad OAuth.\n\n'
                '⚙️ FUNCIONAMIENTO: URL de callback del proveedor: BASE_URL más /v1/auth/oauth/<nombre>/callback.'
            ),
            "get_authorize_url": (
                '💡 LA IDEA: Arma el link oficial de Google o Facebook al que se redirige al cliente para que ponga su huella o contraseña.\n\n'
                '🎯 POR QUE FUE GENERADA: Inicia el viaje seguro de autenticación social sin tocar la contraseña de Google del usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Construye la URL de autorización con client_id, redirect_uri, response_type=code, scope y state (y prompt=select_account en Google). Lanza 503 si el proveedor no está configurado y 404 si no existe.'
            ),
            "_hmac": (
                '💡 LA IDEA: Es el sello de lacre digital con firma secreta para evitar que piratas informáticos intercepten el login.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la autenticación contra ataques de falsificación de peticiones (CSRF).\n\n'
                '⚙️ FUNCIONAMIENTO: Firma HMAC-SHA256 del mensaje con settings.SECRET_KEY devolviendo el hash en hexadecimal.'
            ),
            "sign_state": (
                '💡 LA IDEA: Fabrica un código de seguridad firmado que viaja a Google y vuelve intacto.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite verificar la identidad del usuario sin necesidad de guardar cookies en el navegador.\n\n'
                "⚙️ FUNCIONAMIENTO: State firmado y sin estado para el flujo OAuth: 'nombre.nonce.expiracion.firma_hmac' con nonce aleatorio y expiración settings.OAUTH_STATE_TTL_SECONDS, de modo que el servidor no necesite cookies."
            ),
            "verify_state": (
                '💡 LA IDEA: Revisa el código de seguridad cuando Google devuelve al usuario para comprobar que nadie lo alteró.\n\n'
                '🎯 POR QUE FUE GENERADA: Bloquea intentos de suplantación de identidad en el inicio de sesión.\n\n'
                '⚙️ FUNCIONAMIENTO: Valida el state: estructura de 4 partes, firma con hmac.compare_digest, que no esté vencido y que el proveedor coincida; devuelve False ante cualquier problema.'
            ),
            "exchange_code": (
                '💡 LA IDEA: Canjea el código que entregó Google por el pase de acceso real a los datos del perfil.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el apretón de manos formal entre AUTOPASS y los servidores de Google.\n\n'
                '⚙️ FUNCIONAMIENTO: Intercambia el code de autorización por un access_token vía POST al token_url del proveedor (timeout 15 s). Errores de red, respuesta HTTP fallida o token ausente → HTTPException 502.'
            ),
            "fetch_user_info": (
                '💡 LA IDEA: Lee el nombre, apellido y correo electrónico del perfil del usuario en Google o Facebook.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra al cliente tener que tipear sus datos personales a mano al registrarse.\n\n'
                '⚙️ FUNCIONAMIENTO: Obtiene el perfil del proveedor (cabecera Bearer para Google, access_token por query para Facebook con fields id/first_name/last_name/email) y lo normaliza: email en minúsculas, nombre y apellido según el proveedor (Google parte el name completo), todos pasados por normalize_user_name. Sin email devuelve 502; el resultado es {provider_id, email, nombre, apellido}.'
            ),
            "issue_oauth_signup_code": (
                '💡 LA IDEA: Es el pase temporal de 15 minutos que se le da al cliente para que termine de anotar su DNI y teléfono.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el registro social sea completado con los datos requeridos por la ley.\n\n'
                "⚙️ FUNCIONAMIENTO: Emite un JWT de un solo uso con purpose 'oauth_signup' que contiene email, proveedor, nombre y apellido, y expira en settings.OAUTH_SIGNUP_EXPIRE_MINUTES; sirve para pedir DNI y teléfono después del login social."
            ),
            "decode_oauth_signup_code": (
                '💡 LA IDEA: Abre el pase temporal y recupera los datos de Google para finalizar la creación de la cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que los datos del registro provengan legítimamente del paso social previo.\n\n'
                "⚙️ FUNCIONAMIENTO: Decodifica el JWT con la clave y algoritmo de settings y devuelve el payload solo si purpose == 'oauth_signup'; cualquier JWTError (expirado o inválido) u otro propósito devuelven None."
            ),
            "complete_oauth_signup": (
                '💡 LA IDEA: Es el alta definitiva: crea la cuenta en la base de datos con el correo de Google, el DNI y el teléfono ingresados.\n\n'
                '🎯 POR QUE FUE GENERADA: Deja al usuario 100% registrado y con sesión iniciada en AUTOPASS en dos simples clics.\n\n'
                "⚙️ FUNCIONAMIENTO: Completa el registro social: valida el código (400 si expiró o es inválido), que el email y el DNI normalizado no pertenezcan a usuarios activos (400) y crea el usuario con rol USER, teléfono y una contraseña aleatoria con prefijo 'oauth:' hasheada con get_password_hash —el acceso es por red social y la recuperación puede reestablecerla—. Devuelve el usuario creado."
            ),
        },
    },
}
