"""Explicaciones analizadas de repositories (parte 1 de 2, análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "repositories/access_log_repository.py": {
        "proposito": 'Capa de datos de los accesos físicos del predio (entradas y salidas detectadas por cámaras ALPR o manualmente) sobre la tabla access_logs: última actividad por patente, estado de los vehículos dentro del predio y datos crudos para el dashboard operativo. Centraliza además el filtrado por sucursal/organización que reutilizan casi todos sus métodos.',
        "simbolos": {
            "AccessRepository": (
                '💡 LA IDEA: Es el bibliotecario del libro de entradas y salidas de la cochera: se encarga de buscar, revisar y filtrar todos los pasos de vehículos registrados por las cámaras o por el guardia.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza todas las consultas a la base de datos de accesos en un solo lugar seguro, aislando la lógica SQL del resto del programa.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático (sin estado) con todas las consultas sobre access_logs. Cada método recibe la sesión de SQLAlchemy y aplica a través de un helper común el filtro de sucursal con prioridad por sucursal_id y fallback legado por nombre.'
            ),
            "_sucursal_id_filter": (
                '💡 LA IDEA: Es la lupa que enfoca únicamente los autos de una playa de estacionamiento o de una empresa en particular, ignorando los autos de otras sedes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que un encargado solo vea los autos de su propia sucursal y no mezcle movimientos de otras playas.\n\n'
                '⚙️ FUNCIONAMIENTO: Construye la condición SQL de aislamiento por sede: si se pasa un nombre de sucursal, resuelve su id con BranchRepository.get_id_by_name y devuelve (sucursal_id == id) OR (sucursal_id IS NULL AND sucursal == nombre) para no perder registros legados sin id. Si el nombre no corresponde a ninguna sede y hay organization_id devuelve false() (no matchea nada); sin organización cae al igualdad de nombre legado. Con organization_id y sin sucursal, acota a todas las sedes de esa empresa (in_ de ids) o false() si aún no tiene sedes; sin ninguno de los dos devuelve None (sin filtro).'
            ),
            "get_by_id": (
                '💡 LA IDEA: Es la búsqueda rápida por número de ticket o renglón de registro.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite consultar el detalle exacto de un paso de barrera cuando se conoce su identificador numérico.\n\n'
                '⚙️ FUNCIONAMIENTO: Trae un registro de access_logs por su id único; devuelve None si no existe.'
            ),
            "get_last_by_patente_and_sucursal": (
                "💡 LA IDEA: Es la pregunta: '¿Qué fue lo último que hizo este auto en esta playa?' (si entró o si salió).\n\n"
                '🎯 POR QUE FUE GENERADA: Permite saber si un vehículo está adentro o afuera para no registrar dos entradas seguidas.\n\n'
                '⚙️ FUNCIONAMIENTO: Último evento físico de cualquier tipo (entrada o salida) de una patente ya normalizada en una sucursal: filtra por normalized_patente y el filtro de sede, ordena por id descendente y devuelve el primero. Sirve para saber cuál fue el último paso por torniquete/cámara de un vehículo.'
            ),
            "get_last_detected_by_patente_and_sucursal": (
                '💡 LA IDEA: Igual al anterior, pero buscando la patente tal cual la leyó la cámara con sus espacios o guiones originales.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite contrastar lecturas directas de la cámara antes de que pasen por el filtro de normalización.\n\n'
                '⚙️ FUNCIONAMIENTO: Igual que el anterior pero comparando contra patente_detectada (el texto tal como lo leyó la cámara, sin normalizar), útil cuando se busca por la patente cruda detectada en el momento.'
            ),
            "get_reserva_ids_with_entry": (
                '💡 LA IDEA: Es el listado en bloque de reservas que ya pusieron un pie en el predio: toma cien reservas juntas y averigua cuáles ya ingresaron en un solo viaje a la base de datos.\n\n'
                "🎯 POR QUE FUE GENERADA: Evita el problema 'N+1', donde la computadora haría 100 consultas separadas haciendo que la pantalla tarde segundos en cargar.\n\n"
                '⚙️ FUNCIONAMIENTO: Consulta batch que devuelve un set con los reserva_id que tienen al menos un evento de tipo ENTRADA en access_logs. Evita el patrón N+1 de preguntar reserva por reserva (una sola query con IN sobre los ids recibidos); si la lista viene vacía devuelve set() sin consultar.'
            ),
            "get_en_predio_ids": (
                '💡 LA IDEA: Es el censo de autos adentro: devuelve la lista de todos los vehículos cuyo último movimiento fue entrar y que todavía no salieron.\n\n'
                '🎯 POR QUE FUE GENERADA: Es fundamental para saber la ocupación real del predio y proyectar los cobros pendientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve un set con los reserva_id cuyo último evento físico fue una ENTRADA, es decir vehículos que están dentro del predio. Arma una subconsulta con max(id) agrupada por reserva_id, la une a access_logs y filtra que ese registro máximo sea ENTRADA.'
            ),
            "get_last_entry": (
                '💡 LA IDEA: Es la búsqueda del ticket de ingreso: busca la hora exacta en que el auto entró a la cochera para poder calcular cuántas horas estuvo estacionado al momento de salir.\n\n'
                '🎯 POR QUE FUE GENERADA: Sin esta función sería imposible calcular el tiempo de estadía ni cobrar la tarifa correspondiente al salir.\n\n'
                '⚙️ FUNCIONAMIENTO: Última ENTRADA de una patente normalizada en una sucursal (normalized_patente + tipo_evento ENTRADA + filtro de sede, orden id descendente). Base para calcular la duración de la estadía al cruzarla con la salida correspondiente.'
            ),
            "get_last_entry_by_patente": (
                '💡 LA IDEA: Busca la última entrada de un auto en cualquiera de las sucursales de la red.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite resolver casos donde un cliente extravió su ticket o no recuerda en qué portón ingresó.\n\n'
                '⚙️ FUNCIONAMIENTO: Última ENTRADA de una patente detectada sin filtrar por sucursal: busca en todas las sedes por patente_detectada, ordenado por id descendente.'
            ),
            "get_exit_after": (
                '💡 LA IDEA: Busca la salida que le corresponde a una entrada determinada.\n\n'
                "🎯 POR QUE FUE GENERADA: Permite 'cerrar el ciclo' de la estadía uniendo la foto de entrada con la foto de salida.\n\n"
                '⚙️ FUNCIONAMIENTO: Primera SALIDA de una patente detectada posterior al evento indicado (id > after_id) dentro de la misma sucursal. Se usa para cerrar una estadía abierta: dado el registro de entrada, encontrar la salida que la sigue.'
            ),
            "get_paid_logs_by_patentes": (
                '💡 LA IDEA: Es el historial de recibos pagados para los autos de un cliente.\n\n'
                "🎯 POR QUE FUE GENERADA: Alimenta la pestaña de 'Mis Pagos y Estadías' en el perfil del usuario.\n\n"
                '⚙️ FUNCIONAMIENTO: Lista de registros de access_logs de un conjunto de patentes que tienen pago confirmado (pago_confirmado verdadero) y costo de estadía mayor a cero, ordenados del más reciente al más viejo. Alimenta el historial de cobros de estadias.'
            ),
            "get_last_entries_by_patentes": (
                '💡 LA IDEA: Consulta la última entrada de una lista de vehículos de una sola vez.\n\n'
                '🎯 POR QUE FUE GENERADA: Acelera la carga de la pantalla del cliente cuando tiene varios autos registrados en su cuenta.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la última ENTRADA de cada patente de una lista en una sola consulta: subconsulta agrupada por patente_detectada con max(id) y join de vuelta a access_logs para recuperar la fila completa.'
            ),
            "get_exit_times_by_patentes": (
                '💡 LA IDEA: Es la planilla de horarios de salida de varios autos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite auditar si los autos cumplieron con los horarios de su reserva o si se quedaron de más.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve las tuplas (patente_detectada, fecha_hora) de todas las SALIDAS de un conjunto de patentes, para calcular tiempos de permanencia o cruzarlas con reservas en lote.'
            ),
            "get_current_entries": (
                '💡 LA IDEA: Es el monitor en vivo del guardia: muestra la lista de todos los autos que están actualmente estacionados con su foto y hora de ingreso.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda al personal de seguridad el control visual inmediato de qué vehículos están dentro del predio.\n\n'
                '⚙️ FUNCIONAMIENTO: Tablero de vehículos en el predio: subconsulta con la ENTRADA más reciente por patente_detectada (con filtro opcional de sucursal u organización aplicado dentro de la subconsulta), join a access_logs cargando el piso con selectinload y orden por fecha_hora descendente. Sin sucursal y sin organización trae la última entrada de todas las sedes.'
            ),
            "get_exit_max_by_patente_sucursal": (
                '💡 LA IDEA: Es un diccionario rápido de las salidas más recientes de cada auto.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite descartar velozmente del tablero de autos presentes a aquellos que ya se retiraron.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrupa las SALIDAS por (patente_detectada, sucursal) y devuelve un diccionario con el id máximo de salida de cada par. Se usa para excluir del listado de ingresos abiertos aquellas entradas que ya tienen una salida posterior registrada.'
            ),
            "get_last_entry_clean": (
                '💡 LA IDEA: Es el rastreador flexible de ingresos: busca la última entrada ignorando si la patente fue anotada con espacios, minúsculas o guiones.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve búsquedas difíciles cuando el cliente o el operador escribieron la patente de forma desprolija.\n\n'
                "⚙️ FUNCIONAMIENTO: Última ENTRADA comparando la patente 'limpia' en SQL: aplica replace(upper(patente_detectada), ' ', '') y lo iguala al parámetro sin espacios ni mayúsculas. Permite encontrar el ingreso aunque la patente guardada tenga espacios o distintas cajas (no usa índice, es búsqueda full sobre la columna)."
            ),
            "get_exit_after_clean": (
                '💡 LA IDEA: Encuentra la salida posterior a un ingreso usando la comparación flexible sin espacios ni mayúsculas.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura encontrar la salida correspondiente incluso ante variaciones menores de tipeo.\n\n'
                "⚙️ FUNCIONAMIENTO: Primera SALIDA posterior al evento given (id > after_id) usando la misma comparación 'limpia' de patente (sin espacios ni mayúsculas) sobre patente_detectada, sin filtro de sucursal."
            ),
        },
    },
    "repositories/branch_repository.py": {
        "proposito": 'Capa de datos de las sucursales/sedes (tabla parking_branches) junto a sus relacionadas de pisos (parking_floors) y aforos/capacidades (parking_aforo): búsquedas por nombre o id, listados activos para selects y mapa, y el scoping multiempresa que reutilizan otros repositorios.',
        "simbolos": {
            "BranchRepository": (
                '💡 LA IDEA: Es el catálogo maestro de playas de estacionamiento: administra las sucursales, sus pisos y sus capacidades máximas.\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica todas las consultas de sedes y pisos en un único componente confiable.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático de sedes. Casi todos sus métodos aceptan organization_id opcional y delegan el acotado a la empresa en el helper scope_by_organization, para que cada organización solo vea sus propias sucursales.'
            ),
            "get_all": (
                '💡 LA IDEA: Trae la lista completa de todas las sucursales registradas en el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta los listados globales de sedes para los administradores.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve todas las sucursales (o solo las de la organización indicada con scope_by_organization), sin filtros adicionales.'
            ),
            "get_by_name_like": (
                "💡 LA IDEA: Es la búsqueda por coincidencia parcial: encuentra una sucursal aunque el usuario solo escriba una parte del nombre (ej: 'Caste' para 'Castelar').\n\n"
                '🎯 POR QUE FUE GENERADA: Facilita encontrar playas rápidamente en buscadores predictivos o barras de búsqueda.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca la primera sucursal cuyo nombre contenga el texto recibido (LIKE case-insensitive con ILIKE %texto%), opcionalmente acotada a una organización.'
            ),
            "get_floor_by_id": (
                '💡 LA IDEA: Consulta la información de un piso específico por su número identificador.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite actualizar las plazas o nombres de un piso sin tocar el resto de la sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Trae un piso de la tabla parking_floors por su id único.'
            ),
            "get_by_name_with_floors": (
                '💡 LA IDEA: Trae una sucursal junto con todos sus pisos en una sola consulta relacional optimizada.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra consultas lentas a la base cuando se necesita dibujar el edificio completo con sus niveles.\n\n'
                '⚙️ FUNCIONAMIENTO: Sucursal por nombre exacto con sus pisos precargados mediante joinedload, para recorrer la jerarquía sede → pisos sin consultas extra. Acepta acote por organización.'
            ),
            "get_by_name": (
                '💡 LA IDEA: Busca una sucursal por su nombre exacto.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite asociar reservas y configuraciones a una playa conocida por su denominación oficial.\n\n'
                '⚙️ FUNCIONAMIENTO: Sucursal por nombre exacto (primera coincidencia), opcionalmente acotada a una organización.'
            ),
            "get_id_by_name": (
                "💡 LA IDEA: Es el conversor de nombre a número: recibe 'Castelar' y devuelve su ID numérico (ej: 4).\n\n"
                '🎯 POR QUE FUE GENERADA: Permite que módulos que solo conocen el texto de la sucursal obtengan la clave primaria necesaria para guardar relaciones en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve solo el id de la sucursal con ese nombre exacto, o None si el nombre está vacío o no existe. Si se indica organization_id filtra también por empresa, lo necesario para tolerar nombres repetidos entre organizaciones distintas. Es el punto de entrada que usan otros repositorios (access_log, promotion, redemption, report) para convertir un nombre de sede en sucursal_id.'
            ),
            "get_first_active": (
                '💡 LA IDEA: Es la sucursal de respaldo por defecto: elige la primera playa activa si el usuario no especificó ninguna.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el sistema falle con valores nulos cuando se inicia una pantalla sin selección previa.\n\n'
                '⚙️ FUNCIONAMIENTO: Primera sucursal con activa verdadero (fallback cuando no se especificó un nombre de sede), acotable a una organización.'
            ),
            "get_all_active": (
                '💡 LA IDEA: Lista todas las playas que están abiertas y operativas al público.\n\n'
                '🎯 POR QUE FUE GENERADA: Llena los menús desplegables de reservas para que los usuarios no elijan sedes cerradas o en refacción.\n\n'
                '⚙️ FUNCIONAMIENTO: Todas las sucursales activas, opcionalmente solo las de una organización; alimenta los selectores de sede del admin.'
            ),
            "get_all_active_with_location": (
                '💡 LA IDEA: Es la canasta de pines para el mapa: devuelve todas las sucursales activas que tienen coordenadas GPS cargadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta el mapa interactivo de la portada pública de AUTOPASS.\n\n'
                '⚙️ FUNCIONAMIENTO: Sucursales activas que tienen latitude y longitude cargadas (no nulas), con sus pisos mediante joinedload; es la fuente de puntos para el mapa del panel.'
            ),
            "get_by_id": (
                '💡 LA IDEA: Busca la ficha de una sucursal por su código numérico identificador.\n\n'
                '🎯 POR QUE FUE GENERADA: Es la consulta estándar de acceso directo a una sede desde el panel administrativo.\n\n'
                '⚙️ FUNCIONAMIENTO: Sucursal por su id único.'
            ),
            "get_aforo_by_sucursal": (
                '💡 LA IDEA: Consulta el contador de capacidad máxima y lugares ocupados de una sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber al instante si una playa tiene cocheras libres o si está llena.\n\n'
                '⚙️ FUNCIONAMIENTO: Registro de aforo/capacidades de una sucursal: primero resuelve el id por nombre con get_id_by_name y luego filtra parking_aforo.sucursal_id igual a ese id. Si no hay nombre, busca el aforo con sucursal_id nulo (registro global por defecto).'
            ),
            "get_aforo_by_branch_id": (
                '💡 LA IDEA: Igual al anterior pero usando directamente el ID de la sucursal para mayor velocidad.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita la ambigüedad si hubiera dos sucursales con nombres idénticos en distintas empresas.\n\n'
                '⚙️ FUNCIONAMIENTO: Aforo de una sucursal directamente por su id, evitando la ambigüedad de los nombres repetidos.'
            ),
            "get_all_aforos": (
                '💡 LA IDEA: Trae la lista de capacidades de todas las sucursales de la red juntas.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta el panel central de estadísticas de ocupación de la empresa.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve todos los registros de parking_aforo (capacidades por sede) sin filtrar.'
            ),
            "get_other_by_name": (
                '💡 LA IDEA: Es el detector de nombres repetidos al editar: revisa si ya existe OTRA sucursal con el mismo nombre que se le quiere poner a la actual.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que dos sucursales de la misma empresa tengan el mismo nombre y confundan a los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve otra sucursal que tenga exactamente el mismo nombre pero distinto id (y opcionalmente dentro de la misma organización). Se usa al editar una sede para detectar duplicados de nombre sin tomar su propio registro como conflicto.'
            ),
        },
    },
    "repositories/camera_repository.py": {
        "proposito": 'Capa de datos del hardware de cámaras (tabla parking_cameras): lista las cámaras registradas con su orden manual de visualización y permite recuperar una por id.',
        "simbolos": {
            "CameraRepository": (
                '💡 LA IDEA: Es el organizador del circuito cerrado de televisión: maneja la lista de cámaras y su orden en la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Aísla las consultas de cámaras de seguridad del resto de la lógica del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático mínimo con las dos consultas de lectura de cámaras; la alta y edición viven en el servicio de configuración.'
            ),
            "get_all": (
                '💡 LA IDEA: Trae todas las cámaras del estacionamiento ordenadas exactamente como el operador las acomodó en su grilla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el centro de monitoreo muestre las cámaras en el orden deseado sin desacomodarse al refrescar.\n\n'
                "⚙️ FUNCIONAMIENTO: Todas las cámaras ordenadas por la columna 'orden' con coalesce a un valor enorme, de modo que las que no tienen orden definido (NULL) queden al final; el id desempata para que cámaras con la misma posición tengan un orden estable."
            ),
            "get_by_id": (
                '💡 LA IDEA: Trae los datos de conexión y stream de una cámara en particular.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite editar o calibrar una cámara puntual desde el panel web.\n\n'
                '⚙️ FUNCIONAMIENTO: Cámara por su id único; devuelve None si no existe.'
            ),
        },
    },
    "repositories/mercadopago_repository.py": {
        "proposito": 'Capa de datos de los pagos de Mercado Pago (tabla mercadopago_payments): acceso puntual a las intenciones de pago creadas y a sus confirmaciones cuando el checkout o el webhook las referencian.',
        "simbolos": {
            "MercadoPagoPaymentRepository": (
                '💡 LA IDEA: Es el libro diario de cobros electrónicos: busca comprobantes de pago emitidos a través de la pasarela de Mercado Pago.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite verificar si un cobro ya fue asentado en la base de datos sin duplicar transacciones.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático de solo lectura para pagos de Mercado Pago; la creación y actualización de registros la hace el servicio de pagos.'
            ),
            "get_by_external_reference": (
                '💡 LA IDEA: Es el localizador por número de orden: cuando Mercado Pago avisa por webhook que alguien pagó, busca la reserva correspondiente usando ese código único.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el eslabón indispensable para acreditar el dinero a la reserva correcta en el instante en que el cliente termina de pagar.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca el pago por su external_reference (identificador único que Mercado Pago recibe al crear la intención y que reenvía en el webhook), devolviendo la primera coincidencia. Es la vía principal para conciliar una notificación de Mercado Pago con el pago interno.'
            ),
            "get_by_id": (
                '💡 LA IDEA: Busca un comprobante de Mercado Pago por su número de registro interno.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite consultar el detalle contable de un cobro desde las pantallas de auditoría.\n\n'
                '⚙️ FUNCIONAMIENTO: Pago de Mercado Pago por su id interno en la base.'
            ),
        },
    },
    "repositories/notification_repository.py": {
        "proposito": 'Capa de datos de las notificaciones del usuario (tabla user_notifications): consulta paginada, conteos para los contadores del navbar, marcado en lote como leídas y purga de las leídas. Cubre notificaciones de reservas y de tickets de soporte.',
        "simbolos": {
            "NotificationRepository": (
                '💡 LA IDEA: Es el cartero de la aplicación: guarda, busca, cuenta y limpia los avisos y notificaciones de cada usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la persistencia de notificaciones garantizando que los contadores de no leídas se actualicen al instante.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático que agrupa todas las operaciones de lectura/escritura de user_notifications; los updates en lote usan synchronize_session=False para no refrescar la sesión de ORM.'
            ),
            "get_by_reserva_and_types": (
                '💡 LA IDEA: Es el filtro antispam: revisa si ya se le envió un recordatorio específico a una reserva para no mandarle el mismo aviso dos veces.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita molestar al usuario con notificaciones repetidas sobre el mismo suceso.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve la primera notificación de una reserva cuyo tipo está en la lista recibida. Permite comprobar si ya existe (por ejemplo, 'recordatorio enviado') y evitar duplicar la notificación."
            ),
            "save": (
                '💡 LA IDEA: Guarda una notificación en la base de datos y la deja lista con su fecha de emisión.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el aviso quede guardado permanentemente para que el usuario pueda verlo cuando abra la app.\n\n'
                '⚙️ FUNCIONAMIENTO: Persiste una notificación nueva o los cambios de una existente: add, commit y refresh para devolverla con id y timestamps cargados.'
            ),
            "get_user_notifications": (
                '💡 LA IDEA: Es la bandeja de entrada paginada: lista las notificaciones del usuario de la más nueva a la más vieja de a 10 o 20 por página.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite navegar el historial de avisos sin ralentizar el celular trayendo miles de mensajes juntos.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista las notificaciones de un usuario ordenadas por created_at descendente con offset/limit, para el listado paginado de la campana o centro de avisos.'
            ),
            "get_by_id_and_user": (
                '💡 LA IDEA: Busca un aviso asegurándose de que le pertenezca al usuario que lo pide.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que un usuario curioso pueda leer o borrar las notificaciones privadas de otra persona.\n\n'
                '⚙️ FUNCIONAMIENTO: Trae una notificación filtrando por id y user_id a la vez, de forma que un usuario solo pueda tocar sus propias notificaciones.'
            ),
            "get_unread_count": (
                '💡 LA IDEA: Cuenta cuántas notificaciones sin abrir tiene el cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra el número rojo sobre la campana del menú de navegación.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuenta las notificaciones sin leído del usuario; alimenta el badge numérico de la campana.'
            ),
            "get_total_count": (
                '💡 LA IDEA: Cuenta la cantidad total de mensajes históricos del usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite calcular la cantidad de páginas en la vista de notificaciones.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuenta el total de notificaciones del usuario sin importar si están leídas.'
            ),
            "mark_as_read": (
                "💡 LA IDEA: Marca un aviso como 'Visto' cuando el usuario hace clic sobre él.\n\n"
                '🎯 POR QUE FUE GENERADA: Descuenta inmediatamente ese aviso del contador de no leídos.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca como leída la notificación ya cargada en memoria (poniendo leido en True) y hace commit.'
            ),
            "mark_all_as_read": (
                "💡 LA IDEA: Es el botón 'Marcar todo como leído': pone en visto todos los avisos pendientes en un solo paso.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite al cliente limpiar su campanita con un solo clic.\n\n'
                "⚙️ FUNCIONAMIENTO: Update masivo que pone leido=True en todas las notificaciones sin leer del usuario y devuelve cuántas filas afectó (lo que muestra el front tras 'marcar todas como leídas')."
            ),
            "mark_reservation_notifications_as_read": (
                '💡 LA IDEA: Marca como leídos todos los avisos vinculados a una reserva cuando el cliente entra a verla.\n\n'
                '🎯 POR QUE FUE GENERADA: Mejora la comodidad del usuario evitando que tenga que abrir cada aviso individualmente.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca como leídas las notificaciones de una reserva de un usuario, filtrando opcionalmente por tipo cuando se pasa; devuelve la cantidad actualizada. Sirve al abrir el detalle de la reserva.'
            ),
            "mark_ticket_notifications_as_read": (
                '💡 LA IDEA: Apaga las alertas de respuesta en los tickets de soporte cuando el usuario abre la conversación.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpia la lista de reclamos una vez atendidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca como leídas las notificaciones sin leer que pertenecen a un conjunto de tickets (ticket_id IN). Con la lista vacía devuelve 0 sin ejecutar el update.'
            ),
            "mark_ticket_read_for_user": (
                '💡 LA IDEA: Marca como leídas las notificaciones de un ticket puntual para un usuario específico.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la lectura impacte únicamente en la cuenta del destinatario correspondiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca como leídas las notificaciones de un ticket específico de un usuario concreto (solo las que aún no estaban leídas); devuelve el número de filas afectadas.'
            ),
            "get_unread_ticket_ids_by_user": (
                '💡 LA IDEA: Devuelve la lista de números de ticket que tienen respuestas nuevas sin leer.\n\n'
                "🎯 POR QUE FUE GENERADA: Permite pintar un puntito verde o badge de 'Nuevo mensaje' al lado de cada ticket en la lista de soporte.\n\n"
                "⚙️ FUNCIONAMIENTO: Devuelve la lista de ticket_id (no nulos) que tienen notificaciones sin leer para el usuario; se usa para pintar los puntos de 'sin leer' en la bandeja de tickets de soporte."
            ),
            "delete": (
                '💡 LA IDEA: Elimina un aviso específico de la casilla del usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario descartar notificaciones que ya no le interesan.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina una notificación concreta de la sesión y hace commit.'
            ),
            "clear_read_notifications": (
                '💡 LA IDEA: Es el vaciador de papelera: borra de un solo golpe todas las notificaciones que ya fueron leídas.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene la base de datos liviana y la bandeja del usuario despejada.\n\n'
                "⚙️ FUNCIONAMIENTO: Borra todas las notificaciones ya leídas del usuario con un delete masivo y devuelve cuántas se eliminaron (acción de 'limpiar notificaciones')."
            ),
        },
    },
    "repositories/points_repository.py": {
        "proposito": 'Capa de datos del historial de puntos de fidelización (tabla points_log): devuelve el listado paginado de movimientos junto con los totales de puntos ganados y canjeados/reembolsados del usuario.',
        "simbolos": {
            "PointsRepository": (
                '💡 LA IDEA: Es el contador del club de puntos: calcula cuántos puntos ganó y cuántos canjeó el cliente en cada estadía.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona la lógica de resumen y paginación para el extracto de fidelización.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático con la única consulta de reporte de puntos del sistema.'
            ),
            "get_history": (
                '💡 LA IDEA: Es el resumen de cuenta completo: calcula los puntos totales ganados, los puntos gastados en premios y la lista detallada de movimientos.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra al cliente el extracto transparente de su saldo de puntos en la app móvil.\n\n'
                '⚙️ FUNCIONAMIENTO: Para un usuario calcula cuatro cosas en base a points_log: el total de movimientos, la suma de los positivos (ganados), la suma de los negativos (canjeados o reembolsados, devuelta como negativa) y los ítems de la página actual ordenados por id descendente. La paginación es por offset/limit y el resultado es un diccionario con claves total, earned, redeemed y items.'
            ),
        },
    },
    "repositories/promotion_repository.py": {
        "proposito": 'Capa de datos de las promociones de fidelización (tabla promotions): lista las promos de una sede u organización, distinguiendo las globales (sucursal_id nulo) de las asignadas a una sede concreta, y solo expone las activas cuando corresponde.',
        "simbolos": {
            "PromotionRepository": (
                '💡 LA IDEA: Es el catálogo de ofertas y beneficios de la empresa: busca qué descuentos están vigentes para canjear con puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite filtrar qué promociones corresponden a cada sucursal o aplican a nivel nacional.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático de promociones; delega en BranchRepository la conversión de nombre de sede a id y filtra por organization_id para el modo multiempresa.'
            ),
            "_sucursal_predicate": (
                '💡 LA IDEA: Es la regla de alcance: decide si una promoción se aplica solo en una playa específica o si es válida en todas las sucursales del país.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que los usuarios intenten canjear promociones locales en playas que no tienen el beneficio adherido.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma el predicado SQL de sede para promotions: si no hay nombre de sucursal devuelve None (sin filtro). Resuelve el id con BranchRepository.get_id_by_name y, si la sede existe, compara sucursal_id con ese id; si no existe devuelve false() para que no se hereden promos de otras sedes. Con include_global agrega también las promos globales (sucursal_id nulo).'
            ),
            "get_all": (
                '💡 LA IDEA: Trae todas las promociones registradas para el panel de administración, tanto activas como pausadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los administradores gestionar y editar el catálogo completo de recompensas.\n\n'
                '⚙️ FUNCIONAMIENTO: Todas las promociones con filtros opcionales: sede exacta (cuando se pasa sucursal) y organization_id. Pensado para el listado de administración.'
            ),
            "get_active": (
                '💡 LA IDEA: Trae solo las promociones activas que los clientes pueden canjear en este momento.\n\n'
                '🎯 POR QUE FUE GENERADA: Oculta promociones dadas de baja o vencidas de la vista de los usuarios.\n\n'
                '⚙️ FUNCIONAMIENTO: Promociones con activa verdadero; si se indica una sede incluye además las globales (include_global=True) para que el usuario vea los beneficios aplicables en su parking, y acota por organización si se pasa.'
            ),
            "get_by_id": (
                '💡 LA IDEA: Busca una promoción por su código identificador.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ver o editar el detalle de una promoción específica.\n\n'
                '⚙️ FUNCIONAMIENTO: Promoción por su id único, sin condición de activa (para verla aunque esté desactivada).'
            ),
            "get_active_by_id": (
                '💡 LA IDEA: Busca una promoción por su ID pero exige que esté activa.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que un cliente intente canjear una promoción desactivada enviando su código directo.\n\n'
                '⚙️ FUNCIONAMIENTO: Promoción por id solo si está activa; devuelve None si existe pero está desactivada, lo que impide aplicar un beneficio dado de baja.'
            ),
        },
    },
    "repositories/redemption_repository.py": {
        "proposito": 'Capa de datos de los tickets de canje (tabla redemption_tickets): descuentos de reserva ganados por los usuarios, su vigencia por sede y su vínculo con promociones y reservas. Incluye la cláusula de filtrado por sede con id y fallback legado por nombre.',
        "simbolos": {
            "RedemptionRepository": (
                '💡 LA IDEA: Es la billetera de cupones canjeados: almacena los vouchers de descuento que los usuarios ya compraron con sus puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Controla qué cupones están vigentes, cuáles ya fueron utilizados y cuáles están vencidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático de tickets de canje; resuelve la sede con BranchRepository y distingue los tickets globales (sin sede) de los de una sede concreta.'
            ),
            "redemption_sucursal_clause": (
                '💡 LA IDEA: Es la cláusula de validación territorial: comprueba si un cupón de descuento es aceptado en la sucursal donde el cliente quiere estacionar.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que un descuento exclusivo de una sede se use indebidamente en otra playa.\n\n'
                "⚙️ FUNCIONAMIENTO: Construye la condición SQL de sede sobre redemption_tickets. Sin sucursal devuelve que el nombre sea NULL o vacío (solo globales). Si la sede existe, permite el ticket global (nombre NULL) o sucursal_id igual al id resuelto: un ticket con nombre cuya sede no existe conserva id NULL sin por eso ser global. Si el nombre no corresponde a ninguna sede, cae en el fallback legado comparando el nombre crudo, NULL y una versión normalizada en minúsculas sin espacios ni el prefijo 'autopass ', tanto de la columna como del parámetro, para seguir matcheando datos de prueba escritos a mano."
            ),
            "list_discounts_by_user": (
                '💡 LA IDEA: Muestra la lista de cupones de descuento vigentes que el cliente tiene guardados en su teléfono.\n\n'
                "🎯 POR QUE FUE GENERADA: Alimenta el menú desplegable 'Aplicar cupón de descuento' al momento de reservar una cochera.\n\n"
                "⚙️ FUNCIONAMIENTO: Descuentos de reserva (%) vigentes de un usuario: filtra por user_id, tipo_canje 'descuento_reserva' y estado 'VIGENTE', agrega la cláusula de sede si se pasa sucursal, y ordena por id descendente (los más nuevos primero)."
            ),
            "get_by_user": (
                '💡 LA IDEA: Trae el historial completo de cupones del usuario (vigentes, usados y vencidos).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cliente auditar en qué gastó cada cupón en su perfil.\n\n'
                '⚙️ FUNCIONAMIENTO: Todos los tickets de canje de un usuario (cualquier tipo y estado), ordenados por id descendente.'
            ),
            "get_by_id_and_user": (
                '💡 LA IDEA: Busca un cupón asegurándose de que pertenezca a la persona que intenta usarlo.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que un usuario intente aplicar o ver cupones pertenecientes a otra cuenta.\n\n'
                '⚙️ FUNCIONAMIENTO: Ticket por id restringido a su dueño (user_id), para que nadie pueda usar un ticket ajeno.'
            ),
            "get_valid_discount": (
                '💡 LA IDEA: Es el escáner del cajero: revisa que el cupón no esté usado, que no esté vencido y que sirva para esa playa antes de descontar plata.\n\n'
                '🎯 POR QUE FUE GENERADA: Es la barrera de seguridad que garantiza que ningún descuento se aplique dos veces o fuera de regla.\n\n'
                "⚙️ FUNCIONAMIENTO: Validación completa del descuento al reservar: devuelve el ticket solo si el id coincide, pertenece al usuario, es de tipo 'descuento_reserva', está 'VIGENTE' y pasa la cláusula de sede. Con id vacío devuelve None sin consultar."
            ),
            "get_used_discount_for_reserva": (
                '💡 LA IDEA: Consulta qué cupón exacto se usó para pagar una reserva determinada.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite reintegrar los puntos o liberar el cupón si la reserva es cancelada a tiempo.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve el ticket de descuento ya aplicado (estado 'USADO') a una reserva concreta, para mostrar en el detalle o liberarlo si la reserva se modifica."
            ),
            "unlink_promotion": (
                '💡 LA IDEA: Es el protector de cupones emitidos: si el administrador borra una promoción del catálogo, desvincula los cupones viejos para que la base de datos no falle y los clientes no pierdan lo que ya pagaron.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita errores de clave foránea en la base de datos y protege los derechos de los clientes que ya canjearon su beneficio.\n\n'
                '⚙️ FUNCIONAMIENTO: Pone promotion_id en NULL en todos los tickets que referencian esa promoción y hace commit, desvinculándolos antes de eliminar la promoción para no dejar claves foráneas huérfanas. Devuelve la cantidad de filas actualizadas.'
            ),
        },
    },
    "repositories/report_repository.py": {
        "proposito": 'Capa de reportes e inteligencia de negocio: consultas agregadas (sumas, conteos y desgloses) sobre access_logs y reservations con filtros combinables de sede/organización, rango de fechas, tipo de vehículo y método de pago. Incluye helpers para normalizar variantes de método, tipo de vehículo y nombres de sede, el historial unificado de pagos por UNION y las series que alimentan los gráficos del dashboard.',
        "simbolos": {
            "_canonical_method": (
                "💡 LA IDEA: Es el traductor de formas de pago: convierte anotaciones desordenadas como 'Efectivo', 'caja' o 'CAJA' a la forma estándar oficial 'CAJA'.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite que los gráficos y balances contables sumen correctamente sin separar el dinero en categorías duplicadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Normaliza un método de pago guardado en la base a su nombre canónico (CAJA, DIGITAL, MERCADOPAGO, TRANSFERENCIA, TARJETA, OTRO) buscándolo en la tabla de variantes PAYMENT_METHOD_VARIANTS; un NULL legado se interpreta como DIGITAL. Si no matchea directo, reintenta con el valor en mayúsculas y sin espacios, y termina devolviendo DIGITAL.'
            ),
            "_vehicle_type_key": (
                "💡 LA IDEA: Es el clasificador estándar de rodados para reportes: agrupa variantes como 'motocicleta' o 'moto' bajo la etiqueta limpia 'Moto'.\n\n"
                '🎯 POR QUE FUE GENERADA: Asegura estadísticas de ocupación y recaudación limpias y consistentes.\n\n'
                "⚙️ FUNCIONAMIENTO: Reduce el tipo de vehículo a una clave canónica: 'Moto' (moto/motocicleta), 'Camioneta' (camioneta/utilitario) o 'Auto' para todo lo demás; los vacíos o 'all' devuelven 'all' para indicar sin filtro."
            ),
            "_vehicle_type_condition": (
                '💡 LA IDEA: Convierte el filtro de vehículo en una condición SQL insensible a mayúsculas o minúsculas.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita filtrar los gráficos de recaudación por auto, moto o camioneta sin errores de tipeo.\n\n'
                "⚙️ FUNCIONAMIENTO: Convierte la clave canónica en condición SQL comparando lower(columna) con lower(clave) para que no importe la caja del valor guardado; con 'all' devuelve None, lo que hace que el llamador no aplique filtro."
            ),
            "_es_reembolso_parcial": (
                '💡 LA IDEA: Es la lupa contable de devoluciones: detecta reservas donde se devolvió parte del dinero por cancelación o estadía más corta.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite deducir los reembolsos de los ingresos brutos para mostrar la ganancia neta real del estacionamiento.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve la condición SQL de 'hubo reemplazo': estado REEMBOLSADO (reembolso total) o estado PAGADO con monto_reembolsado mayor a cero (reembolso parcial). Recibe las columnas como parámetros para poder aplicarse a reservas en distintas consultas."
            ),
            "_payment_method_filter": (
                '💡 LA IDEA: Es el filtro de medios de cobro para reportes: permite ver solo lo recaudado en efectivo, con tarjeta o por Mercado Pago.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita el arqueo de caja físico al final del turno separando el dinero en mano de los cobros digitales.\n\n'
                "⚙️ FUNCIONAMIENTO: Filtro SQL por método de pago canónico: con 'all' o vacío devuelve None (sin filtro); con DIGITAL acepta la columna nula o cualquier valor que no sea efectivo (CAJA/Caja/Efectivo), de modo que los NULL legados cuenten como digital; con un método conocido filtra por todas sus variantes; si no, igualdad exacta."
            ),
            "_unaccent": (
                "💡 LA IDEA: Es el eliminador de tildes en SQL: permite que una búsqueda por 'Morón' encuentre 'Moron' sin importar cómo esté configurada la base de datos.\n\n"
                '🎯 POR QUE FUE GENERADA: Garantiza que los informes financieros no dejen afuera sucursales por una diferencia ortográfica.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve la expresión SQL que reemplaza uno por uno los acentos y la ñ (ambas cajas) de una columna con func.replace, para poder comparar nombres de sede como 'Ituzaingó' e 'Ituzaingo' sin depender de funciones de la base."
            ),
            "_branch_key": (
                '💡 LA IDEA: Genera el nombre limpio de una sede para comparaciones en memoria.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita cruces rápidos de datos entre diferentes tablas del sistema.\n\n'
                "⚙️ FUNCIONAMIENTO: Clave canónica de un nombre de sede en Python: quita el prefijo 'AUTOPASS ', recorta espacios, pasa a minúsculas y elimina acentos. Se usa para construir los patrones LIKE del filtro legado y para comparar nombres normalizados."
            ),
            "_branch_filter": (
                '💡 LA IDEA: Es el guardián de sucursal en reportes: aplica el filtro de playa o empresa a cualquier consulta de métricas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el balance contable muestre únicamente los números correspondientes a la sede seleccionada.\n\n'
                '⚙️ FUNCIONAMIENTO: Aislamiento por sede aplicable a cualquier tabla con columna de nombre y columna de id. Con sucursal: si la sede existe combina sucursal_id igual al id con el fallback legado (fila sin id y LIKE sin acentos ni prefijo sobre el nombre); si no existe y hay organización devuelve false(); sin organización solo el LIKE legado. Con organization_id y sin sucursal arma un OR con el id de todas las sedes de la empresa más las condiciones LIKE de cada nombre para filas legadas sin id (false() si la empresa aún no tiene sedes). Sin sucursal ni organización devuelve None (sin filtro).'
            ),
            "ReportRepository": (
                '💡 LA IDEA: Es el contador general del sistema: procesa los millones de datos de ingresos, egresos y pagos para generar las estadísticas del panel de control.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza todas las consultas analíticas pesadas garantizando reportes rápidos y confiables.\n\n'
                '⚙️ FUNCIONAMIENTO: Repositorio estático con todas las consultas de los reportes; cada método acepta el mismo conjunto de filtros opcionales (sucursal, organization_id, tipo de vehículo, fechas y método de pago) y aplica los helpers del módulo según corresponda.'
            ),
            "paid_logs_aggregate": (
                '💡 LA IDEA: Suma el dinero total cobrado por estadías espontáneas (las que entraron por cámara ALPR) en un rango de fechas.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta los gráficos de facturación diaria y mensual del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Recaudación de estadias ALPR: suma de costo_estadia y conteo de registros de access_logs con pago_confirmado y costo mayor a cero, filtrados por método, tipo de vehículo, sede/organización y rango de fechas. Las fechas se evalúan sobre fecha_pago y, si es nula, sobre fecha_hora; devuelve una tupla (suma, cantidad).'
            ),
            "paid_reservations_aggregate": (
                '💡 LA IDEA: Suma el dinero total cobrado por reservas anticipadas en un período determinado.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite medir el impacto y crecimiento del canal digital de reservas.\n\n'
                '⚙️ FUNCIONAMIENTO: Recaudación de reservas: suma de monto_total y conteo de reservations en estado PAGADO o REEMBOLSADO, con join outer a vehicles por patente para poder filtrar por tipo de vehículo, más los filtros de sede, fechas (fecha_pago con fallback a fecha_inicio) y método. Devuelve (suma, cantidad).'
            ),
            "refunds_total": (
                '💡 LA IDEA: Suma toda la plata devuelta a clientes por cancelaciones o ajustes de estadía.\n\n'
                '🎯 POR QUE FUE GENERADA: Es indispensable para calcular la ganancia neta real descontando las devoluciones.\n\n'
                '⚙️ FUNCIONAMIENTO: Suma de monto_reembolsado de las reservas que cumplan la condición de reembolso total o parcial, aplicando exactamente los mismos filtros de vehículo, sede, fechas y método que la recaudación; devuelve el escalar (None si no hay reembolsos).'
            ),
            "cancelled_reservations": (
                '💡 LA IDEA: Lista las reservas que fueron canceladas por el cliente o por el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite analizar la tasa de deserción y cuántas cocheras quedaron desaprovechadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista las reservas con estado CANCELADA filtradas por vehículo, sede y rango de fechas sobre fecha_inicio; alimenta el cálculo de la tasa de cancelación y los ingresos por incumplimiento.'
            ),
            "total_reservations_count": (
                '💡 LA IDEA: Cuenta la cantidad total de reservas realizadas en un período.\n\n'
                '🎯 POR QUE FUE GENERADA: Sirve como base para calcular el porcentaje de reservas efectivas vs canceladas.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuenta el total de reservas con los mismos filtros de vehículo, sede y fechas (por fecha_inicio) que cancelled_reservations; es el denominador de la tasa de cancelación. Devuelve 0 si no hay filas.'
            ),
            "unpaid_entries_without_exit": (
                '💡 LA IDEA: Es el radar de cobros pendientes: autos que están adentro del predio y todavía no pagaron su estadía.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite estimar la recaudación proyectada que se cobrará cuando los vehículos se retiren.\n\n'
                '⚙️ FUNCIONAMIENTO: Vehículos físicamente presentes y sin pagar: entradas de access_logs con pago_confirmado falso para las que NO existe una salida posterior de la misma patente en la misma sede (subconsulta EXISTS correlacionada con un alias de access_logs que compara sucursal_id o, si es nulo, el nombre de sucursal). Acepta filtro de tipo de vehículo y sede; se usa para proyectar la deuda en curso.'
            ),
            "grouped_logs_by_method": (
                '💡 LA IDEA: Es el gráfico de torta de estadías: divide la plata según si se cobró en efectivo (Caja) o por medios digitales.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda al gerente a saber cuánto efectivo debe haber en la caja física al cierre de jornada.\n\n'
                '⚙️ FUNCIONAMIENTO: Desglose de la recaudación de estadias agrupando access_logs pagados por metodo_pago: devuelve filas (método, suma de costo_estadia, cantidad) con los mismos filtros de vehículo, sede y fechas.'
            ),
            "grouped_reservations_by_method": (
                '💡 LA IDEA: Es el gráfico de medios de pago exclusivo para las reservas web y móviles.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite analizar las preferencias de pago digital de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Desglose de reservas PAGADAS/REEMBOLSADAS agrupadas por metodo_pago con join a vehicles: filas (método, suma de monto_total, cantidad) para el gráfico de medios de pago.'
            ),
            "grouped_refunds_by_method": (
                '💡 LA IDEA: Desglosa los reembolsos según el medio por el cual se devolvió el dinero.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene auditadas las salidas de caja y las reversiones de tarjetas de crédito.\n\n'
                '⚙️ FUNCIONAMIENTO: Desglose de reembolsos agrupado por metodo_pago: (método, suma de monto_reembolsado con coalesce a 0, cantidad) sobre las reservas con reembolso total o parcial y los mismos filtros.'
            ),
            "payment_history": (
                '💡 LA IDEA: Es el libro mayor contable unificado: junta en una sola lista cronológica los pagos de estadías, los pagos de reservas y las devoluciones.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda al administrador una cartola financiera única con todos los movimientos de dinero de la empresa.\n\n'
                "⚙️ FUNCIONAMIENTO: Historial unificado y paginado de movimientos financieros: arma tres consultas con columnas homogéneas (id con prefijo 'L', 'R' o 'REF' para no chocar, fecha con coalesce de fecha_pago y fecha de inicio/entrada, patente, monto, tipo literal y método normalizado) y las une con union_all. Los reembolsos se muestran en negativo y solo se incluyen reservas PAGADO en la rama de reservas; ordena por fecha descendente y aplica offset/limit (con limit menor o igual a 0 trae todo)."
            ),
            "access_logs_history": (
                '💡 LA IDEA: Es el registro de auditoría visual de los últimos 300 autos que pasaron por las barreras.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al operador consultar rápidamente quién entró o salió en las últimas horas sin colapsar el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Historial de accesos ALPR ordenado por id descendente con límite server-side de 300 por defecto (evita traer la tabla completa y el crecimiento del IN de patentes del dashboard). Filtra por sede/organización y opcionalmente por patente con LIKE %PATENTE% en mayúsculas.'
            ),
            "logs_with_ocr": (
                '💡 LA IDEA: Es el informe de velocidad de la inteligencia artificial: mide cuántos segundos tardó la cámara en leer cada patente.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta los gráficos de rendimiento del OCR para detectar si una cámara está perdiendo nitidez o tardando de más.\n\n'
                "⚙️ FUNCIONAMIENTO: Registros de access_logs con ocr_time cargado (tiempo de OCR medido), filtrados por sede. Si ascending es verdadero devuelve la serie completa ordenada por id ascendente; si no, los últimos 'limit' registros en orden descendente para el gráfico de rendimiento de OCR."
            ),
            "access_event_rows": (
                '💡 LA IDEA: Es el sismógrafo de tráfico: devuelve los horarios de entradas y salidas para dibujar el mapa de calor (heatmap) de horas pico.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al dueño del estacionamiento saber qué días y horarios se llena la playa para ajustar las tarifas o el personal.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve solo los pares (fecha_hora, tipo_evento) de todos los accesos filtrados por sede, la fuente mínima para armar la serie temporal de entradas y salidas en el cliente.'
            ),
            "reservation_activity_rows": (
                '💡 LA IDEA: Es el calendario de reservas: muestra qué autos tienen turnos reservados en una semana o mes determinado.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta la vista de agenda para planificar la capacidad del estacionamiento con días de anticipación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve columnas de reservations (fechas de inicio y fin, estados de reserva y pago, monto, tipo de vehículo y patente) que solapan el rango pedido (fecha_fin >= start y fecha_inicio <= end), filtradas por sede; alimenta la vista de actividad/calendario.'
            ),
            "entrance_patent_events": (
                '💡 LA IDEA: Es el detector de ausencias (no-show): cruza las patentes que tenían reserva con los ingresos reales por barrera para detectar quién no vino.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite cancelar o liberar plazas reservadas cuando el cliente nunca se presentó a su turno.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve los pares (normalized_patente, fecha_hora) de los eventos de tipo ENTRADA de access_logs dentro de un rango de fechas y sede; se cruza con las reservas para detectar vehículos que no se presentaron (no-show) o confirmar ingresos.'
            ),
        },
    },
}
