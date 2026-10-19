"""Explicaciones analizadas de repositories (parte 2 de 2, análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "repositories/reservation_repository.py": {
        "proposito": 'Capa de datos de las reservas de estacionamiento (tabla reservations). Concentra el control de solapamiento de turnos (para no vender dos veces el mismo horario), las consultas de vigencia que usan las tareas programadas (recordatorios, activación, cancelación por impago) y los listados del panel staff con aislamiento por sucursal y organización. Los predicados de sede que definen ese aislamiento viven en el propio archivo para reutilizarlos en todos sus métodos.',
        "simbolos": {
            "ReservationRepository": (
                '💡 LA IDEA: Es el encargado de la libreta de reservas: anota, busca y verifica turnos de estacionamiento para que ningún auto se quede sin su lugar reservado.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la lógica de reservas en la base de datos protegiendo la coherencia de fechas y horarios.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático con todas las consultas de reservas; en vez de filtrar la sede a mano, casi todos sus métodos delegan en los predicados privados del mismo archivo (_sucursal_id_predicate, _otra_sucursal_predicate, _org_branch_predicate) que combinan sucursal_id con el nombre legado y el acote multiempresa.'
            ),
            "_org_branch_predicate": (
                '💡 LA IDEA: Es el cerco perimetral de la empresa: se asegura de que un administrador solo pueda ver las reservas de las playas pertenecientes a su propia compañía.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza la estricta privacidad multiempresa en la gestión de turnos.\n\n'
                '⚙️ FUNCIONAMIENTO: Predicado multiempresa: consulta los ids de parking_branches cuya organization_id es la pedida y devuelve Reservation.sucursal_id.in_(ids); si la empresa todavía no tiene sedes devuelve false() (no matchea nada). Sirve para que un Admin General solo vea reservas de sus propias sedes.'
            ),
            "_sucursal_id_predicate": (
                '💡 LA IDEA: Es la mira telescópica sobre una playa: filtra las reservas que corresponden exactamente a esa sede.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el panel de una sucursal muestre autos reservados para otra ciudad.\n\n'
                '⚙️ FUNCIONAMIENTO: Construye la condición de aislamiento por sede sobre reservations: si no se pasa nombre, pide sucursal_id nulo; si se pasa, resuelve el id con BranchRepository.get_id_by_name (acotado a organization_id si corresponde) y arma or_(sucursal_id == branch_id, sucursal_id nulo AND sucursal_nombre == nombre) para no perder registros legados sin id. Con include_global agrega además las reservas sin sucursal; si la sede no existe y hay organización devuelve false(). Es el filtro que usan la mayoría de las consultas de este repositorio.'
            ),
            "_otra_sucursal_predicate": (
                "💡 LA IDEA: Es el detector de 'desdoblamiento': busca si un mismo cliente intentó reservar una cochera en dos playas distintas al mismo tiempo.\n\n"
                '🎯 POR QUE FUE GENERADA: Impide que un usuario reserve dos cocheras lejanas a la misma hora para el mismo auto.\n\n'
                '⚙️ FUNCIONAMIENTO: Predicado inverso al anterior: reservas de CUALQUIER otra sede, excluyendo la sede objetivo y las globales (~or_(sucursal_id == id, sucursal_nombre == nombre)). Se usa para detectar turnos del mismo usuario solapados en un parking distinto.'
            ),
            "ReservationRepository.get_by_id": (
                '💡 LA IDEA: Busca una reserva por su número de comprobante único, verificando que pertenezca al usuario consultante si se indica.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite acceder al detalle de una reserva protegiendo la privacidad del cliente.\n\n'
                '⚙️ FUNCIONAMIENTO: Trae una reserva por id. El archivo tiene dos definiciones: una primera (db, res_id) y una segunda (db, res_id, user_id=None) que la pisa en tiempo de ejecución; la vigente filtra por id y, si se pasa user_id, agrega la condición user_id igual para que nadie lea una reserva ajena. Devuelve la primera coincidencia o None.'
            ),
            "get_by_user_and_id": (
                '💡 LA IDEA: Busca la reserva por ID exigiendo que coincida el dueño de la cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que un cliente curioso pueda mirar o cancelar la reserva de otra persona adivinando el número.\n\n'
                '⚙️ FUNCIONAMIENTO: Reserva por id restringida a su dueño mediante and_(id == res_id, user_id == user_id); devuelve la primera coincidencia o None. Es el control de propiedad que usan los endpoints de usuario.'
            ),
            "get_past_reservations": (
                '💡 LA IDEA: Es el canasto de turnos vencidos: busca reservas que ya pasaron de horario para archivarlas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite limpiar la agenda liberando lugares que ya no están vigentes.\n\n'
                '⚙️ FUNCIONAMIENTO: Reservas del usuario en estado PENDIENTE o ACTIVA cuya fecha_fin ya quedó antes del instante recibido (comparación de las fechas guardadas como texto ordenable). Sirve para listar o procesar reservas vencidas que nunca se completaron.'
            ),
            "get_all_by_user": (
                '💡 LA IDEA: Es el historial completo de reservas del cliente: pasadas, presentes y futuras.\n\n'
                "🎯 POR QUE FUE GENERADA: Alimenta la pestaña 'Mis Reservas' en el panel del usuario.\n\n"
                '⚙️ FUNCIONAMIENTO: Historial completo de reservas del usuario (sin filtrar estado), ordenado por id descendente para que las más nuevas aparezcan primero.'
            ),
            "get_active_overlapping": (
                '💡 LA IDEA: Es el detector de choques de horario: revisa si el horario pedido se pisa con otra reserva existente en esa misma playa.\n\n'
                '🎯 POR QUE FUE GENERADA: Es la barrera que impide sobrevender el estacionamiento (overbooking).\n\n'
                '⚙️ FUNCIONAMIENTO: Reservas de la sede en estados PENDIENTE/ACTIVA y pago PENDIENTE/PAGADO cuyo rango se superpone con el pedido: fecha_inicio < hasta AND fecha_fin > desde (intervalos semiabiertos). Es la consulta antichoque al crear o mover una reserva; exclude_id permite ignorar la propia reserva al editarla.'
            ),
            "get_overlap_by_patente": (
                '💡 LA IDEA: Revisa si ESA misma patente ya tiene un turno reservado en ese rango de tiempo.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el mismo conductor saque dos reservas duplicadas para el mismo vehículo.\n\n'
                "⚙️ FUNCIONAMIENTO: Igual que get_active_overlapping pero además exige que la patente coincida normalizada en SQL (replace(upper(patente),' ','') == patente_norm), de modo que detecta si ESA patente ya tiene un turno solapado en la sede. Devuelve la primera coincidencia o None y acepta exclude_id."
            ),
            "get_user_overlap_other_branch": (
                '💡 LA IDEA: Detecta si el cliente ya tiene una reserva activa en otra sucursal distinta para el mismo horario.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita reservas fantasmas o incompatibles físicamente.\n\n'
                '⚙️ FUNCIONAMIENTO: Primera reserva vigente del usuario que se superpone con el rango PERO en otra sede (usa _otra_sucursal_predicate) y con pago vigente. Bloquea reservar en un parking si el usuario ya tiene ocupado ese horario en otro.'
            ),
            "get_expired": (
                '💡 LA IDEA: Busca reservas que llegaron a su fin sin que el auto haya salido o sin haberse completado.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta el robot de fondo que marca turnos como completados o caducados.\n\n'
                '⚙️ FUNCIONAMIENTO: Reservas en PENDIENTE/ACTIVA cuya fecha_fin ya pasó, sin filtrar por usuario ni sede. Alimenta el proceso que expira reservas vencidas.'
            ),
            "get_paid_current_by_sucursal": (
                '💡 LA IDEA: Cuenta cuántos autos con reserva paga deberían estar adentro del predio en este minuto exacto.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite calcular cuántas cocheras libres quedan disponibles para autos que llegan sin reserva.\n\n'
                '⚙️ FUNCIONAMIENTO: Reservas ya pagadas (estado_pago PAGADO) en PENDIENTE/ACTIVA cuyo horario contiene al instante actual (fecha_inicio <= now <= fecha_fin) en la sede indicada. Refleja la ocupación actual reservada y pagada.'
            ),
            "get_pending_reminders": (
                '💡 LA IDEA: Busca las reservas que están a punto de empezar en la próxima hora y que todavía no recibieron su recordatorio.\n\n'
                "🎯 POR QUE FUE GENERADA: Alimenta el robot que despacha emails o notificaciones con el aviso: 'Tu turno comienza pronto'.\n\n"
                '⚙️ FUNCIONAMIENTO: Reservas vigentes (PENDIENTE/ACTIVA) cuya fecha_inicio cae dentro de la ventana [inicio_min, inicio_max] y que todavía no tienen recordatorio enviado (recordatorio_confirmado falso), con el usuario precargado por selectinload. Es la fuente del job que manda el aviso previo.'
            ),
            "get_pending_started": (
                '💡 LA IDEA: Reservas cuyo horario ya comenzó pero que aún figuran como pendientes.\n\n'
                "🎯 POR QUE FUE GENERADA: Permite cambiar automáticamente el estado de la reserva a 'Activa'.\n\n"
                '⚙️ FUNCIONAMIENTO: Reservas aún en PENDIENTE cuyo inicio ya llegó y cuya fecha_fin todavía no pasó, con el usuario precargado. Son las candidatas a pasar automáticamente a ACTIVA.'
            ),
            "get_unpaid_overdue": (
                '💡 LA IDEA: Es el cronómetro de tolerancia de pago: reservas impagas cuyo tiempo de gracia ya expiró.\n\n'
                '🎯 POR QUE FUE GENERADA: Cancela automáticamente reservas abandonadas para devolver la cochera al público general.\n\n'
                '⚙️ FUNCIONAMIENTO: Reservas vigentes sin pagar (estado_pago PENDIENTE) cuya fecha_inicio quedó antes del límite de gracia, con el usuario precargado. Las usa el proceso de cancelación automática por falta de pago.'
            ),
            "get_active_by_user": (
                '💡 LA IDEA: Comprueba si el usuario tiene alguna reserva en curso en este momento.\n\n'
                "🎯 POR QUE FUE GENERADA: Permite mostrar accesos rápidos o el botón de 'Ver mi pase actual' en el inicio de la app.\n\n"
                '⚙️ FUNCIONAMIENTO: Primera reserva vigente del usuario (PENDIENTE/ACTIVA con fecha_fin >= now). Permite saber si ya tiene un turno en curso antes de dejarle crear otro.'
            ),
            "get_active_by_clean_patente": (
                '💡 LA IDEA: Busca si la patente que acaba de enfocar la cámara tiene un turno reservado vigente.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el chequeo relámpago que hace la barrera para decidir si le levanta el paso al auto reservado.\n\n'
                "⚙️ FUNCIONAMIENTO: Primera reserva vigente por patente normalizada en SQL (replace(upper(patente),' ','') == patente_clean) con fecha_fin >= now. La usa el flujo ALPR, que dispone de la patente limpia, para saber si ese vehículo tiene reserva activa."
            ),
            "get_active_by_sucursal": (
                '💡 LA IDEA: Verifica rápidamente si hay alguna reserva activa en una playa determinada.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber si una sucursal tiene actividad antes de realizar tareas de mantenimiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Primera reserva vigente (PENDIENTE/ACTIVA y fecha_fin >= now) en la sede indicada, usando el predicado de sede. Responde de forma rápida si hay alguna reserva activa en ese parking.'
            ),
            "get_by_ids": (
                '💡 LA IDEA: Trae un conjunto de reservas en una sola consulta de base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Acelera drásticamente la carga de pantallas que muestran listados de reservas.\n\n'
                '⚙️ FUNCIONAMIENTO: Reservas cuyos ids están en la lista recibida, en una sola consulta; si la lista viene vacía devuelve [] sin tocar la base. Evita el patrón N+1 en armados de tableros.'
            ),
            "get_active_in_range_by_normalized_patente": (
                '💡 LA IDEA: Es la comprobación definitiva de entrada: confirma que la patente normalizada tiene turno válido en este instante y en esta playa.\n\n'
                '🎯 POR QUE FUE GENERADA: Autoriza la apertura automática de la barrera de entrada al vehículo reservado.\n\n'
                '⚙️ FUNCIONAMIENTO: Reserva vigente de una patente normalizada cuyo horario contiene al instante recibido (fecha_inicio <= now <= fecha_fin), aplicando el predicado de sede con include_global=True (permite la sede concreta o una reserva global). Confirma que el vehículo detectado tiene reserva válida en ese momento al ingresar.'
            ),
            "_filtered_base_query": (
                '💡 LA IDEA: Es el motor de filtros del panel de administración: combina filtros de estado, sucursal, organización y fechas.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita repetir la misma lógica de filtrado en múltiples vistas del panel staff.\n\n'
                "⚙️ FUNCIONAMIENTO: Arma la query base de los listados del panel: parte de reservations y aplica, en orden de prioridad, filtro por estado; si se pasa staff_sucursal resuelve su id por nombre y filtra por sucursal_id, o —cuando normalized_staff y la sede no existe por id— cae a una comparación normalizada que ignora el prefijo 'autopass ' y espacios; si no, aplica el predicado de sucursal (con organización) o, si solo hay organization_id, todas las sedes de la empresa. Devuelve la Query sin ejecutar."
            ),
            "list_filtered": (
                '💡 LA IDEA: Ejecuta la búsqueda de reservas con todos los filtros de la pantalla del personal administrativo.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta la tabla principal de reservas del dashboard de los empleados.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta _filtered_base_query con el usuario precargado (selectinload) y orden por id descendente. Es el listado de reservas que consume el panel de staff/administración.'
            ),
            "latest_id_and_count": (
                '💡 LA IDEA: Es el detector de novedades: pregunta si entró alguna reserva nueva desde la última vez que la pantalla parpadeó.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite actualizar el panel en tiempo real sin recargar toda la página.\n\n'
                '⚙️ FUNCIONAMIENTO: Sobre la misma base filtrada (con staff_sucursal normalizado) devuelve una tupla (id máximo, cantidad de reservas con id > since_id); si no se pasa since_id la cuenta es 0. Sirve para que el tablero detecte novedades desde la última consulta (sondeo incremental).'
            ),
            "save": (
                '💡 LA IDEA: Guarda la reserva en la base de datos y la devuelve con su código y fecha asignados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la reserva quede asentada de forma permanente y segura en el disco.\n\n'
                '⚙️ FUNCIONAMIENTO: Persiste altas y cambios de reservas: agrega la instancia, hace commit y refresh, y la devuelve con el id y los campos generados ya cargados.'
            ),
        },
    },
    "repositories/scoping.py": {
        "proposito": 'Helper único de aislamiento multiempresa (multi-tenant): aplica a cualquier consulta SQLAlchemy el filtro por organización según cómo esté ligado el modelo —por columna organization_id directa o por join a parking_branches a través de sucursal_id—. Existe para no repetir el mismo predicado en cada repositorio y es tolerante: sin organización no filtra.',
        "simbolos": {
            "scope_by_organization": (
                '💡 LA IDEA: Es el filtro de privacidad multiempresa automático: inyecta a cualquier consulta el límite de la empresa correspondiente.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que una empresa de estacionamiento pueda consultar o modificar información de otra empresa competidora.\n\n'
                '⚙️ FUNCIONAMIENTO: Recibe una Query, el modelo y un organization_id; si el organization_id es None devuelve la query sin cambios (modo single-tenant usado por tests y datos previos a la migración). Si el modelo tiene columna organization_id filtra directo por esa columna; si tiene sucursal_id hace join con ParkingBranch por sucursal_id == id y filtra por la organización de la sede; si no tiene ninguna de las dos columnas devuelve la query tal cual.'
            ),
        },
    },
    "repositories/session_repository.py": {
        "proposito": 'Capa de datos de las sesiones multidispositivo (tabla user_sessions). Permite identificar la sesión de un dispositivo concreto, reconocer un navegador aunque haya cambiado de dispositivo y contar cuántos otros dispositivos activos tiene el usuario para aplicar el límite de sesiones simultáneas.',
        "simbolos": {
            "SessionRepository": (
                '💡 LA IDEA: Es el registro de dispositivos: anota desde qué computadoras o teléfonos se conectó cada usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Aísla el control de sesiones simultáneas y auditoría de accesos.\n\n'
                "⚙️ FUNCIONAMIENTO: Repositorio estático con las tres consultas de control de sesiones; todas reciben la ventana temporal 'since' (last_login_at >= since) para considerar solo sesiones recientes."
            ),
            "get_by_device": (
                '💡 LA IDEA: Busca si ese teléfono celular ya está registrado en la cuenta del cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite reconocer el dispositivo habitual del usuario para no pedirle verificaciones extra.\n\n'
                '⚙️ FUNCIONAMIENTO: Sesión del usuario en un dispositivo concreto, filtrando por user_id y device_id; devuelve la primera coincidencia o None.'
            ),
            "get_recent_by_user_agent": (
                '💡 LA IDEA: Reconoce el navegador del usuario aunque el identificador de dispositivo haya cambiado.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita bloqueos falsos cuando el navegador actualiza sus cookies.\n\n'
                "⚙️ FUNCIONAMIENTO: Sesión más reciente (order by last_login_at descendente) del usuario con el mismo user_agent y last_login_at >= since; devuelve la primera. Permite tratar como 'el mismo navegador' a una sesión cuyo device_id cambió."
            ),
            "count_other_devices": (
                '💡 LA IDEA: Cuenta cuántos otros celulares o computadoras tienen la sesión abierta al mismo tiempo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite aplicar límites de seguridad contra cuentas compartidas indebidamente.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuenta los device_id distintos del actual (device_id != el recibido, opcionalmente user_agent distinto) con last_login_at >= since. Devuelve cuántos otros dispositivos/navegadores tienen sesión activa, dato con el que se decide si hay que cerrar sesiones o bloquear un nuevo ingreso.'
            ),
        },
    },
    "repositories/settings_repository.py": {
        "proposito": 'Capa de datos de la configuración clave/valor del sistema (tabla settings): tarifas y parámetros guardados como globales o como variantes por sede. Centraliza la resolución de la sede por nombre y la preferencia de la variante de sucursal sobre la global, con acote opcional a la organización.',
        "simbolos": {
            "SettingsRepository": (
                '💡 LA IDEA: Es la pizarra de tarifas y configuraciones: busca los precios por hora y parámetros del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica la lectura de precios globales y precios especiales por sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático de settings; resuelve la sede con BranchRepository y usa false() para no heredar el tarifario global cuando se pide una sede que no existe.'
            ),
            "_sucursal_predicate": (
                '💡 LA IDEA: Regla de búsqueda que prioriza la tarifa propia de una sede sobre la tarifa nacional por defecto.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que una sucursal céntrica cobre más caro que una sucursal de las afueras sin duplicar código.\n\n'
                '⚙️ FUNCIONAMIENTO: Condición de sede sobre settings.sucursal_id: sin nombre pide sucursal_id nulo (configuración global); con nombre resuelve el id con BranchRepository.get_id_by_name (acotado a organization_id) y compara sucursal_id con él; si la sede no existe devuelve false(), de modo que no se herede el valor global de otra sede.'
            ),
            "get_by_clave": (
                "💡 LA IDEA: Busca un parámetro (ej: 'TARIFA_HORA_AUTO'); si la sucursal tiene un precio propio lo usa, y si no, usa el precio global.\n\n"
                '🎯 POR QUE FUE GENERADA: Es la consulta estándar de tarifas del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Configuración por clave. Si se pasa sucursal intenta primero la variante de esa sede (más el filtro de organización si corresponde) y, si no existe, se vuelve a llamar con sucursal=None para caer al valor global; sin sucursal busca directamente el registro global (sucursal_id nulo). Devuelve el primero o None.'
            ),
            "get_by_clave_global": (
                '💡 LA IDEA: Busca el valor base nacional de un parámetro, sin importar la sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Sirve como precio de referencia general cuando una playa abre por primera vez.\n\n'
                '⚙️ FUNCIONAMIENTO: Configuración global (sucursal_id nulo) por clave, sin fallback a ninguna sede.'
            ),
            "get_by_clave_and_sucursal": (
                '💡 LA IDEA: Pregunta si una sede tiene un precio especial configurado específicamente para ella.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al administrador ver qué tarifas fueron personalizadas en esa sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Configuración por clave y sede SIN herencia: aplica el predicado de sede (más organización si se indica) y devuelve el primero o None. Sirve para saber si esa sede tiene un override propio.'
            ),
            "get_all_by_sucursal": (
                '💡 LA IDEA: Trae el tarifario completo de una sucursal en una sola lista.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta la pantalla de edición de precios del panel de control.\n\n'
                '⚙️ FUNCIONAMIENTO: Todas las configuraciones de una sede (o las globales si no se pasa nombre), acotadas a la organización si se indica; alimenta pantallas que muestran el tarifario completo de una sede.'
            ),
            "get_rates_by_claves": (
                '💡 LA IDEA: Consulta en lote todas las tarifas de golpe (auto, moto, camioneta, hora, estadía).\n\n'
                '🎯 POR QUE FUE GENERADA: Acelera el cálculo de precios al cotizar reservas sin hacer diez consultas seguidas.\n\n'
                '⚙️ FUNCIONAMIENTO: Batch de tarifas por un conjunto de claves: filtra clave IN y, si se pasan sucursales, incluye las variantes de esas sedes resueltas (sucursal_id IN) más las globales (sucursal_id nulo) o, si no se pasan sucursales, solo las globales; suma el filtro de organización. Trae todo en una sola consulta para comparar valores globales y por sede.'
            ),
            "get_camera_sources_by_prefix": (
                '💡 LA IDEA: Busca los canales de video de las cámaras asociadas a una sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite conectar el reproductor de video a las cámaras de la sede correcta.\n\n'
                "⚙️ FUNCIONAMIENTO: Configuraciones cuya clave empieza con 'CAMERA_SOURCE_<prefijo>_' (LIKE), es decir los canales de cámara ALPR asociados a un prefijo de sucursal."
            ),
        },
    },
    "repositories/support_repository.py": {
        "proposito": 'Capa de datos del soporte (tablas support_tickets y support_ticket_messages): persistencia transaccional del ticket con su primer mensaje, y lecturas con el usuario/autor precargado para mostrar la conversación tanto al cliente como al panel de administración.',
        "simbolos": {
            "SupportRepository": (
                '💡 LA IDEA: Es la mesa de entradas del centro de ayuda: administra los tickets de reclamo y sus respuestas.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que cada mensaje quede registrado cronológicamente con su autor.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático de tickets y mensajes de soporte; usa joinedload para traer el usuario/autor en las consultas que lo necesitan y desc para ordenar por fecha.'
            ),
            "create_ticket": (
                '💡 LA IDEA: Abre un expediente de reclamo nuevo guardando la carátula y el primer mensaje del cliente en un solo paso.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita tickets vacíos o desenganchados si la conexión se interrumpe a la mitad.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un ticket con su primer mensaje en una sola transacción: hace add del ticket, flush para que reciba el id, construye el mensaje llamando a build_message(ticket) (que por eso recibe el ticket ya con id), lo agrega, hace commit y refresh, y devuelve el ticket persistido.'
            ),
            "save_message": (
                '💡 LA IDEA: Agrega un mensaje nuevo a la conversación existente de un ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Guarda las respuestas del personal o las réplicas del cliente en el chat de soporte.\n\n'
                '⚙️ FUNCIONAMIENTO: Persiste un mensaje nuevo (add + commit + refresh) y devuelve el mensaje; confirmar el mensaje también guarda el estado del ticket tocado en la misma sesión.'
            ),
            "get_user_tickets": (
                '💡 LA IDEA: Lista todos los reclamos iniciados por un usuario desde el más reciente.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta la bandeja de tickets en el perfil del cliente.\n\n'
                '⚙️ FUNCIONAMIENTO: Tickets de un usuario ordenados por created_at descendente (los más recientes primero).'
            ),
            "get_all_with_user": (
                '💡 LA IDEA: Lista todos los tickets de la empresa con los datos del cliente precargados.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta la bandeja de entrada del panel de atención al cliente de los operadores.\n\n'
                '⚙️ FUNCIONAMIENTO: Todos los tickets con su usuario cargado por joinedload y orden descendente por created_at, para el listado de administración sin consultas N+1.'
            ),
            "get_all": (
                '💡 LA IDEA: Trae todos los tickets sin cargar relaciones pesadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Para conteos o reportes estadísticos rápidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Todos los tickets, sin orden explícito ni relaciones cargadas.'
            ),
            "get_by_id": (
                '💡 LA IDEA: Busca un ticket por su número de seguimiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite abrir el expediente puntual solicitado.\n\n'
                '⚙️ FUNCIONAMIENTO: Ticket por su id único; devuelve None si no existe.'
            ),
            "get_by_id_with_user": (
                '💡 LA IDEA: Trae el ticket junto con el nombre, email y teléfono del cliente que lo abrió.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al operador ver los datos de contacto del cliente mientras redacta su respuesta.\n\n'
                '⚙️ FUNCIONAMIENTO: Ticket por id con su usuario cargado por joinedload, para la vista de detalle.'
            ),
            "get_by_id_and_user": (
                '💡 LA IDEA: Busca un ticket asegurándose de que pertenezca al usuario que lo consulta.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que un cliente lea reclamos o conversaciones de otras personas.\n\n'
                '⚙️ FUNCIONAMIENTO: Ticket por id restringido a su dueño (user_id): devuelve la primera coincidencia o None, de modo que un cliente solo acceda a sus propios tickets.'
            ),
            "get_messages_for_tickets": (
                '💡 LA IDEA: Carga todos los mensajes de una lista de tickets en una sola consulta.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita lentitud al mostrar la lista de reclamos en pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Mensajes cuyo ticket_id está en la lista recibida, con el autor cargado y ordenados por created_at ascendente; si la lista viene vacía devuelve [] sin consultar. Carga en lote la conversación de varios tickets.'
            ),
            "get_messages_by_ticket": (
                '💡 LA IDEA: Trae el diálogo cronológico completo de un reclamo de principio a fin.\n\n'
                '🎯 POR QUE FUE GENERADA: Dibuja el hilo del chat en la pantalla de soporte.\n\n'
                '⚙️ FUNCIONAMIENTO: Mensajes de un ticket concreto ordenados cronológicamente por created_at ascendente.'
            ),
        },
    },
    "repositories/system_repository.py": {
        "proposito": 'Operación de reinicio de datos del sistema (entorno de prueba): borra en bloque los datos operativos y los clientes registrados, dejando intacta la administración y la configuración.',
        "simbolos": {
            "SystemRepository": (
                '💡 LA IDEA: Es el botón de reinicio de fábrica para pruebas: borra todos los datos operativos sin tocar la configuración.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los desarrolladores y evaluadores limpiar autos y reservas de prueba con un solo clic.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático con la única tarea de reset de datos operativos.'
            ),
            "reset_all_data": (
                '💡 LA IDEA: Vacía los registros de entradas, salidas, autos y reservas de prueba, conservando a los administradores del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra horas de limpieza manual al reiniciar una demostración escolar o de testing.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina todas las filas de access_logs, parking_aforo, reservations y vehicles, y borra únicamente los usuarios con rol USER (no toca ADMIN ni LOCAL_ADMIN); cierra con un único commit. Devuelve None.'
            ),
        },
    },
    "repositories/user_repository.py": {
        "proposito": "Capa de datos de los usuarios (tabla users): búsquedas por id, email o DNI con la semántica de 'no eliminado', validaciones de unicidad que excluyen al propio usuario, listados de staff y mutaciones de saldo y puntos. El acote multiempresa se delega en scope_by_organization.",
        "simbolos": {
            "UserRepository": (
                '💡 LA IDEA: Es el padrón central de usuarios: busca, valida y actualiza las cuentas de clientes y empleados.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza el acceso seguro a las cuentas de usuario y sus saldos.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático de usuarios; normaliza el email recibido (minúsculas y sin espacios) en las búsquedas por correo y usa is_deleted para distinguir cuentas activas de borradas.'
            ),
            "get_by_id": (
                '💡 LA IDEA: Busca a una persona por su número de socio o ID interno.\n\n'
                '🎯 POR QUE FUE GENERADA: Es la consulta directa de cuenta para tareas administrativas.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuario por id único, sin filtrar is_deleted (acceso administrativo/auditoría); devuelve None si no existe.'
            ),
            "get_active_by_id": (
                '💡 LA IDEA: Busca un usuario por ID exigiendo que su cuenta no haya sido borrada.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita operar sobre cuentas que fueron dadas de baja.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuario por id con is_deleted falso: solo cuentas activas.'
            ),
            "get_all_active": (
                '💡 LA IDEA: Trae la lista de todos los usuarios activos de la empresa.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta la lista de usuarios del panel de administración.\n\n'
                '⚙️ FUNCIONAMIENTO: Todos los usuarios no eliminados, acotados a la organización si se indica (scope_by_organization).'
            ),
            "get_by_email": (
                '💡 LA IDEA: Busca un usuario por su correo electrónico.\n\n'
                '🎯 POR QUE FUE GENERADA: Utilizado para verificar si un email ya está en uso antes de un registro.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuario por email, comparando el parámetro en minúsculas y sin espacios con la columna; no excluye eliminados.'
            ),
            "get_active_by_email": (
                '💡 LA IDEA: Busca una cuenta activa por su email normalizado en minúsculas.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el corazón del inicio de sesión (login) del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuario no eliminado por email normalizado (minúsculas/sin espacios); es la búsqueda típica de login o registro.'
            ),
            "get_active_by_dni": (
                '💡 LA IDEA: Busca un cliente activo por su número de DNI.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al empleado de mostrador encontrar al cliente cuando este solo le da su documento.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuario no eliminado por DNI exacto (sin normalizar).'
            ),
            "get_other_by_email": (
                '💡 LA IDEA: Verifica si otro usuario ya está usando ese correo al editar un perfil.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que dos personas terminen con el mismo email registrado.\n\n'
                '⚙️ FUNCIONAMIENTO: Otro usuario (id distinto) no eliminado que tenga ese email; valida unicidad de correo al editar el perfil sin chocar con el propio registro.'
            ),
            "get_other_by_dni": (
                '💡 LA IDEA: Verifica si otro usuario ya tiene ese mismo DNI registrado.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide la duplicación de números de documento en el sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Otro usuario (id distinto) no eliminado que tenga ese DNI; valida unicidad de DNI al editar.'
            ),
            "get_staff": (
                '💡 LA IDEA: Trae la lista de empleados y administradores de la empresa.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite enviar alertas operativas al equipo de trabajo de la playa.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuarios con rol ADMIN o LOCAL_ADMIN que no estén eliminados; alimenta el listado de personal y los envíos a administradores.'
            ),
            "get_by_ids": (
                '💡 LA IDEA: Trae los datos de varios usuarios en una sola consulta relacional.\n\n'
                '🎯 POR QUE FUE GENERADA: Acelera el armado de tablas con nombres de clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuarios cuyos ids están en la lista, en una sola consulta; con lista vacía devuelve [] sin tocar la base.'
            ),
            "get_local_admin_by_sucursal": (
                '💡 LA IDEA: Busca al encargado o gerente responsable de una sucursal determinada.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite derivar consultas de clientes o problemas de barrera al responsable de esa sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Local admin (rol LOCAL_ADMIN) no eliminado asignado a la sucursal indicada por el nombre guardado en user.sucursal, opcionalmente acotado a la organización; devuelve el primero o None.'
            ),
            "update_balance": (
                '💡 LA IDEA: Suma o resta dinero al saldo de la billetera virtual del cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el cajero digital que acredita recargas de dinero o cobra estadías contra el saldo.\n\n'
                '⚙️ FUNCIONAMIENTO: Suma amount al saldo del usuario en memoria y hace commit (un monto negativo sirve para descontar); no devuelve nada.'
            ),
            "add_points": (
                '💡 LA IDEA: Suma puntos al programa de fidelización del cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Premia al usuario cada vez que completa una estadía en la red.\n\n'
                '⚙️ FUNCIONAMIENTO: Incrementa puntos_acumulados en points y hace commit, alimentando el programa de fidelización.'
            ),
        },
    },
    "repositories/vehicle_repository.py": {
        "proposito": "Capa de datos de vehículos (tabla vehicles) centrada en la normalización de patentes: los logs ALPR guardan la patente limpia ('AB123CD') y el alta de vehículo la guarda con formato visual ('AB 123 CD'), por lo que todos los cruces por patente comparan en SQL replace(upper(patente),' ','') para que ambas fuentes coincidan.",
        "simbolos": {
            "VehicleRepository": (
                '💡 LA IDEA: Es el registro del automotor de la plataforma: administra los autos de los clientes y sus patentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve el cruce inteligente entre patentes limpias de las cámaras y patentes con espacios de los usuarios.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático de vehículos; usa core.normalize.normalize_plate para preparar los parámetros en Python antes de consultar con la expresión normalizada en SQL.'
            ),
            "_norm_expr": (
                '💡 LA IDEA: Es la fórmula mágica que quita espacios y pone mayúsculas en SQL a cualquier patente.\n\n'
                "🎯 POR QUE FUE GENERADA: Permite que 'AB 123 CD' y 'AB123CD' se encuentren de inmediato sin importar cómo fueron escritas.\n\n"
                "⚙️ FUNCIONAMIENTO: Expresión SQL de la patente normalizada (mayúsculas y sin espacios: replace(upper(patente),' ','')). Es la base de casi todos los filtros del archivo y existe porque el match exacto entre el formato visual del alta y la patente limpia de los logs falla; por eso las búsquedas no usan igualdad cruda."
            ),
            "get_tipos_by_patentes": (
                '💡 LA IDEA: Es el clasificador masivo: toma una lista de patentes y devuelve si cada una es auto, moto o camioneta.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite calcular el aforo y las tarifas de varios autos en un solo paso.\n\n'
                '⚙️ FUNCIONAMIENTO: Mapa {patente normalizada: tipo} para la lista de patentes recibida: normaliza cada patente en Python, consulta con IN sobre la expresión normalizada y arma el diccionario; con lista vacía devuelve {} sin consultar. Etiqueta el tipo de vehículo en listados y tableros en lote.'
            ),
            "get_by_patente": (
                '💡 LA IDEA: Busca la ficha de un auto por su patente, sin importar si tiene espacios.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber quién es el dueño del auto cuando la cámara de la barrera lo lee.\n\n'
                '⚙️ FUNCIONAMIENTO: Vehículo por patente ignorando espacios y mayúsculas: normaliza el parámetro y delega en get_by_normalized_patente.'
            ),
            "get_by_normalized_patente": (
                '💡 LA IDEA: Busca un vehículo usando una patente que ya fue limpiada previamente.\n\n'
                '🎯 POR QUE FUE GENERADA: Es la consulta de máxima velocidad que usa el servicio ALPR de la entrada.\n\n'
                '⚙️ FUNCIONAMIENTO: Vehículo por patente ya normalizada; si el parámetro viene vacío devuelve None sin consultar, y si no devuelve la primera coincidencia o None.'
            ),
            "get_by_normalized_patentes": (
                '💡 LA IDEA: Busca varios vehículos por sus patentes limpias en una sola consulta.\n\n'
                '🎯 POR QUE FUE GENERADA: Optimiza la carga del panel de monitoreo de cámaras.\n\n'
                '⚙️ FUNCIONAMIENTO: Batch: todos los vehículos cuya patente normalizada está en la lista, en una sola consulta con IN; con lista vacía devuelve []. Es el equivalente en lote de get_by_normalized_patente y evita N+1.'
            ),
            "get_by_patente_and_user": (
                '💡 LA IDEA: Comprueba si esa patente pertenece al usuario que está queriendo operarla.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que un usuario cargue o borre un auto que pertenece a otra persona.\n\n'
                '⚙️ FUNCIONAMIENTO: Vehículo por patente normalizada en SQL y user_id, es decir restringido a su dueño; devuelve el primero o None.'
            ),
            "get_by_user_and_normalized_patente": (
                '💡 LA IDEA: Igual al anterior pero con la patente ya normalizada.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza la propiedad del vehículo en las validaciones de reserva.\n\n'
                '⚙️ FUNCIONAMIENTO: Igual que el anterior pero recibiendo la patente ya normalizada; filtra por user_id y por la expresión normalizada.'
            ),
            "get_by_normalized_patente_with_active_owner": (
                '💡 LA IDEA: Busca el auto por patente pero solo si el dueño tiene su cuenta activa y sin bloqueos.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que autos de usuarios dados de baja o morosos sigan abriendo las barreras automáticas.\n\n'
                '⚙️ FUNCIONAMIENTO: Vehículo por patente normalizada que además hace join con users y exige is_deleted falso del dueño: solo lo devuelve si su propietario sigue activo. Evita operar sobre vehículos de cuentas dadas de baja.'
            ),
            "get_plates_by_user": (
                '💡 LA IDEA: Lista todas las patentes registradas por un cliente en su cuenta.\n\n'
                "🎯 POR QUE FUE GENERADA: Llena el menú desplegable 'Elegir mi auto' al hacer una reserva rápida.\n\n"
                '⚙️ FUNCIONAMIENTO: Lista de patentes (columna patente, en su formato visual) de todos los vehículos del usuario.'
            ),
            "get_by_user": (
                '💡 LA IDEA: Trae todos los vehículos del usuario con su marca, modelo y si son favoritos.\n\n'
                "🎯 POR QUE FUE GENERADA: Alimenta la pestaña 'Mis Vehículos' en el perfil del cliente.\n\n"
                '⚙️ FUNCIONAMIENTO: Todos los vehículos pertenecientes al usuario.'
            ),
            "get_other_by_user": (
                '💡 LA IDEA: Comprueba si el usuario tiene algún otro vehículo registrado con un criterio específico.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite validar cambios al editar un vehículo sin chocar consigo mismo.\n\n'
                '⚙️ FUNCIONAMIENTO: Un vehículo del usuario distinto del id recibido; se usa al editar para detectar si el usuario ya tiene otro vehículo con ese criterio sin contarse a sí mismo.'
            ),
            "unset_favorite_for_user": (
                "💡 LA IDEA: Le saca la estrellita de 'favorito' a todos los autos del cliente antes de ponerle la estrella a uno nuevo.\n\n"
                '🎯 POR QUE FUE GENERADA: Asegura que el usuario tenga un único auto favorito principal para agilizar el ingreso.\n\n'
                '⚙️ FUNCIONAMIENTO: Update masivo que pone is_favorite=False en todos los vehículos favoritos del usuario (útil antes de marcar el nuevo favorito). No hace commit por sí mismo: el llamador es quien confirma.'
            ),
        },
    },
}
