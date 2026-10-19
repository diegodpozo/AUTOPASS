"""Explicaciones analizadas de models (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "models/__init__.py": {
        "proposito": (
            "💡 LA IDEA: Es el 'catálogo maestro y padrón electoral' de la base de datos. Si pensás en las tablas como fichas de un archivador (Usuarios, Autos, Reservas, Pagos, Cámaras), este archivo abre el archivador, toma lista de todas las fichas del sistema y las inscribe en el registro central de SQLAlchemy (`Base.metadata`).\n\n"
            "🎯 POR QUE FUE GENERADA: SQLAlchemy necesita conocer de antemano todas las tablas para poder tejer las relaciones entre ellas (por ejemplo, que un Usuario tiene muchos Autos y muchas Reservas). Si este archivo no importara todos los modelos juntos, al arrancar la app la base de datos no sabría cómo relacionar una patente con su dueño o con su ticket de acceso.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Importa todas las entidades del dominio: `User`, `Vehicle`, `Reservation`, `AccessLog`, `ParkingBranch`, `ParkingFloor`, `ParkingSlot`, `ParkingCamera`, `TariffSetting`, `Promotion`, etc. 2. Las deja inscriptas en `Base.metadata` para que `create_all()` y Alembic puedan crear las tablas en SQLite o PostgreSQL. 3. Registra los modelos vinculados a sucursales llamando a `register_branch_linked()`. 4. Expone todos los modelos en el espacio de nombres de `models` para permitir importaciones directas como `from models import User, Reservation`."
        ),
        "simbolos": {
        },
    },
    "models/branch_ref.py": {
        "proposito": 'Puente entre el nombre de sede que usan las llamadas viejas (API, seeds, tests) y la columna `sucursal_id` que es lo único que se guarda en la BD. El nombre real vive solo en `parking_branches`; este módulo expone un hybrid para leerlo y un traductor que, antes de cada flush, convierte el nombre pendiente a la sede correcta sin cruzar de organización.',
        "simbolos": {
            "branch_ref_property": (
                "💡 LA IDEA: Es el traductor simultáneo de sucursales: permite que el código viejo siga diciendo `auto.sucursal = 'Castelar'` como si fuera un simple texto, mientras por detrás el sistema busca el número de ID real de esa sede en la base de datos.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita tener que reescribir cientos de pantallas y llamadas viejas que usaban nombres de texto, manteniendo la base de datos relacional impecable y normalizada con IDs numéricos.\n\n'
                "⚙️ FUNCIONAMIENTO: Fábrica de hybrid_property que representa el nombre de la sede. El getter devuelve el valor pendiente sin persistir, o el nombre de la sede cargada (`self.branch`), o un fallback en memoria, o el `default` recibido (por ejemplo 'General' para tickets globales). El setter guarda el nombre en `_sucursal_input` y marca la instancia como dirty para que el traductor la vea aunque la columna ya no sea un atributo mapeado. La expresión `expr` construye un subselect sobre `parking_branches.nombre` (con COALESCE al default) para poder comparar `Modelo.sucursal == x` en consultas."
            ),
            "register_branch_linked": (
                '💡 LA IDEA: Es la lista de invitados VIP del traductor: anota qué modelos (Usuarios, Reservas, Logs, Cámaras) tienen que pasar obligatoriamente por la traducción automática de sucursales antes de guardarse.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que ningún registro quede huérfano de sede al insertarse en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrega los modelos indicados al conjunto global `_LINKED`, que es la lista que usa el traductor `before_flush` para saber qué instancias debe revisar. `models/__init__.py` lo llama pasándole User, Reservation, AccessLog, SupportTicket, RedemptionTicket, ParkingAforo, Settings, ParkingCamera y Promotion.'
            ),
            "_resolver_organizacion": (
                '💡 LA IDEA: Es el detective de pertenencia: investiga a qué empresa u organización dueña pertenece un registro (mirando al usuario, a la reserva o a la sede) para no mezclar datos.\n\n'
                "🎯 POR QUE FUE GENERADA: Esencial para evitar que una sucursal con el mismo nombre (ej: 'Centro') se confunda con la de otra empresa competidora en el sistema.\n\n"
                '⚙️ FUNCIONAMIENTO: Deduce a qué organización pertenece el objeto pendiente para acotar la búsqueda de sede: usa `organization_id` directo si existe; si no, busca la organización del `user_id`; y si tampoco, con `reservation_id` llega al usuario de la reserva y de ahí a su organización. Si no logra deducirla (p. ej. ParkingCamera) devuelve None.'
            ),
            "_elegir_sede": (
                '💡 LA IDEA: Es el árbitro que elige la sucursal exacta entre varias candidatas con nombres parecidos, asegurándose de que pertenezca a la misma empresa.\n\n'
                "🎯 POR QUE FUE GENERADA: Impide que una reserva de la empresa 'A' termine asignada por error a una playa de la empresa 'B'.\n\n"
                '⚙️ FUNCIONAMIENTO: Entre las sedes candidatas que tienen el mismo nombre normalizado, elige una. Si se conoce la organización del objeto, exige una sede de esa misma empresa (aunque el nombre sea globalmente único); si la organización es desconocida, solo resuelve cuando hay exactamente una candidata (comportamiento single-tenant). Nunca devuelve una sede de otra organización.'
            ),
            "_translate_branch_names": (
                '💡 LA IDEA: Es el empleado de aduana que se para justo antes de que la información baje al disco rígido (`before_flush`): revisa todos los registros que traen nombres escritos y les coloca su ID de sucursal correspondiente.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la base de datos nunca reciba datos a medio procesar ni errores de clave foránea.\n\n'
                '⚙️ FUNCIONAMIENTO: Listener de SQLAlchemy sobre `before_flush`: junta las instancias nuevas o modificadas que pertenecen a `_LINKED` y tienen `_sucursal_input` pendiente. Arma un índice de sedes por nombre normalizado (incluyendo las sedes nuevas del mismo flush, que aún no tienen id), y para cada objeto pendiente resuelve la sede con `_elegir_sede`, asigna `obj.branch` y, si no hubo match pero sí un nombre, guarda un fallback en memoria para poder mostrarlo.'
            ),
        },
    },
    "models/enums.py": {
        "proposito": 'Define como Enum de cadenas los valores fijos que circulan por todo AUTOPASS (roles, tipos de vehículo, eventos de acceso, estados de reserva y de pago, y tipos de notificación). Al centralizarlos se evita repetir literales sueltos y se garantiza que backend, servicios y notificaciones usen los mismos códigos.',
        "simbolos": {
            "UserRole": (
                '💡 LA IDEA: Es el catálogo de credenciales y uniformes: define los 4 tipos de personas en el sistema (Administrador Global, Gerente de Sucursal, Empleado de Barrera y Cliente).\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que alguien invente roles inexistentes o cometa errores de tipeo al asignar permisos en el panel.\n\n'
                '⚙️ FUNCIONAMIENTO: Roles posibles de una cuenta: ADMIN (admin general de la organización), LOCAL_ADMIN (administrador de una sede), STAFF (personal operativo) y USER (cliente). Se guarda en `User.rol` y gobierna los permisos del panel admin.'
            ),
            "VehicleType": (
                '💡 LA IDEA: Es la clasificación de vehículos: separa entre Auto, Moto y Camioneta para saber cuánto espacio ocupan y qué tarifa cobrarles.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve el cálculo diferenciado de precios y aforo según el tamaño del rodado.\n\n'
                '⚙️ FUNCIONAMIENTO: Tipos de vehículo soportados: Auto, Moto y Camioneta. Se usa en `Vehicle.tipo` y `Reservation.tipo_vehiculo` para tarifas, cupos y capacidad.'
            ),
            "AccessEventType": (
                "💡 LA IDEA: Es el sentido de paso del molinete: distingue si la cámara vio al auto entrando ('ENTRADA') o saliendo ('SALIDA').\n\n"
                '🎯 POR QUE FUE GENERADA: Es la clave para iniciar el reloj de cobro o calcular la cuenta final al egreso.\n\n'
                '⚙️ FUNCIONAMIENTO: Eventos de acceso registrados por las cámaras ALPR: ENTRADA y SALIDA. Es el valor de `AccessLog.tipo_evento` y decide cómo se calcula la estadía y el cobro.'
            ),
            "ReservationStatus": (
                '💡 LA IDEA: Es el semáforo de vida de una reserva: Pendiente, Activa, Completada o Cancelada.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el sistema sepa qué reservas tienen derecho a entrar, cuáles ya pasaron y cuáles liberar por falta de pago.\n\n'
                '⚙️ FUNCIONAMIENTO: Estados del ciclo de vida de una reserva: Pendiente, Activa, Completada y Cancelada. Corresponde al campo `Reservation.estado_reserva`.'
            ),
            "PaymentStatus": (
                '💡 LA IDEA: Es el estado contable del pago: Pendiente, Pagado, Fallido, Reembolsado o Cancelado.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que una reserva entre al estacionamiento si el cobro fue rechazado por la tarjeta de crédito.\n\n'
                '⚙️ FUNCIONAMIENTO: Estados del pago de una reserva: Pendiente, Pagado, Fallido, Reembolsado y Cancelado. Corresponde a `Reservation.estado_pago`.'
            ),
            "NotificationType": (
                '💡 LA IDEA: Es la clasificación de mensajes de la campanita: recordatorios de reserva, avisos de puntos ganados, tickets de ayuda o alertas de seguridad.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que la aplicación móvil y la web muestren el ícono, color y botón de acción correcto para cada aviso.\n\n'
                '⚙️ FUNCIONAMIENTO: Catálogo de todos los motivos de notificación al usuario agrupados por área (reservas, finanzas y puntos, estadías y vehículos, soporte, y seguridad/cuenta). Es el valor de `UserNotification.tipo` y le permite al frontend decidir ícono, texto y acción de cada aviso.'
            ),
        },
    },
    "models/mercadopago.py": {
        "proposito": 'Persiste el ciclo completo de un pago con Mercado Pago (Checkout Pro) vinculado a una reserva o a una estadía: desde la intención creada hasta su confirmación por webhook. Guarda tanto el estado interno como el `status` crudo que reporta Mercado Pago, para auditar y conciliar pagos.',
        "simbolos": {
            "MercadoPagoPayment": (
                '💡 LA IDEA: Es el comprobante oficial de caja de Mercado Pago: registra el número de preferencia, el ID de transacción, el monto en pesos y la patente asociada.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite auditar y conciliar el dinero que entró a la cuenta bancaria contra cada auto que usó el estacionamiento.\n\n'
                "⚙️ FUNCIONAMIENTO: Tabla `mercadopago_payments`. Campos: `user_id` (pagador), `tipo` ('reserva' o 'estadia'), `reserva_id` o `access_log_id` según corresponda, `redemption_ticket_id` para el descuento por canje (solo reservas), `patente`, `monto` (con CheckConstraint no negativo) y `moneda` (ARS por defecto). Para la integración guarda `external_reference` (único), `preference_id` y `payment_id`. El estado interno arranca en PENDIENTE y puede ser APROBADO/FALLIDO/CANCELADO, con `mp_status` como status textual de MP. Tiene fechas de creación y confirmación (`DateTimeAsStr`) y relaciones hacia User, Reservation y AccessLog."
            ),
            "aplicado": (
                "💡 LA IDEA: Es la luz verde de cobro: responde Sí únicamente cuando el pago fue efectivamente 'APROBADO' por Mercado Pago.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita levantar barreras o confirmar reservas con pagos pendientes de acreditación o en proceso.\n\n'
                "⚙️ FUNCIONAMIENTO: Propiedad calculada: devuelve True únicamente cuando `estado` es 'APROBADO'. Sirve para que el resto del código pregunte si el pago ya impactó (activar reserva, cerrar estadía) sin acoplarse al texto del estado."
            ),
        },
    },
    "models/notification.py": {
        "proposito": 'Guarda las notificaciones dirigidas a un usuario (avisos de reservas, puntos, estadías, soporte, seguridad). Es la tabla que alimenta la campanita/centro de notificaciones del panel del cliente.',
        "simbolos": {
            "UserNotification": (
                '💡 LA IDEA: Es la casilla de correo interna del cliente: guarda cada notificación con su título, mensaje, fecha y si ya fue leída o no.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene al usuario informado sobre sus reservas y estadías sin depender exclusivamente de que abra su email.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `user_notifications`. Registra `user_id` (destinatario), `tipo` (valores de NotificationType como REMINDER_PAID o AUTO_CANCELLED), `titulo` y `mensaje`, el flag `leido` (False por defecto) y `created_at`. Puede enlazar de forma opcional una reserva (`reserva_id`) o un ticket (`ticket_id`) para poder navegar al origen desde la notificación. Relaciona con User, Reservation y SupportTicket mediante backrefs.'
            ),
        },
    },
    "models/organization.py": {
        "proposito": 'Representa cada empresa (organización) dueña de sucursales, personal, clientes y beneficios. Es la raíz del aislamiento multiempresa: todo lo demás pertenece a una organización, y la marcada como principal es la que ve el sitio público.',
        "simbolos": {
            "_now_iso": (
                '💡 LA IDEA: Es el fechador automático: estampa la fecha y hora exacta en que se dio de alta una empresa en el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona una marca de tiempo confiable para auditoría de creación de empresas.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la fecha y hora actuales en formato ISO (`datetime.datetime.now().isoformat()`). Se usa como valor por defecto de `Organization.created_at`.'
            ),
            "Organization": (
                '💡 LA IDEA: Es la ficha legal de la empresa dueña de estacionamientos: define el nombre de la compañía y si es la empresa dueña principal de la plataforma.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el cimiento que permite que múltiples empresas de estacionamiento usen el mismo sistema con total privacidad entre sí.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `organizations`. Campos: `nombre` (único e indexado), `es_principal` (solo la organización principal se muestra en la landing y recibe los registros de clientes hechos desde la web), `activa` y `created_at`. Cada Admin General administra una única organización de forma aislada.'
            ),
        },
    },
    "models/parking.py": {
        "proposito": 'Reúne las tablas del funcionamiento físico del estacionamiento: capacidad y ocupación (aforo por sede y por piso), configuraciones y tarifas, cámaras de monitoreo, el registro de accesos ALPR y las sedes. Es el núcleo operativo que consultan los servicios de reserva, cobro y monitoreo.',
        "simbolos": {
            "ParkingAforo": (
                "💡 LA IDEA: Es el cartel luminoso que dice 'HAY LUGAR' en la puerta: lleva la cuenta de cuántos autos, motos y camionetas hay adentro en tiempo real y cuántas cocheras libres quedan.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita el colapso del estacionamiento impidiendo el paso de nuevos autos cuando la capacidad máxima está completa.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `parking_aforo`: control de capacidad y ocupación en tiempo real de una sede, separado por tipo (autos, motos, camionetas) y también para plazas de reserva de cada tipo. Guarda pares capacidad/ocupación (con CheckConstraint que los fuerza no negativos), `ultima_actualizacion` y `sucursal_id` único (una sola fila de aforo por sede). Expone `branch` y el hybrid `sucursal`.'
            ),
            "Settings": (
                '💡 LA IDEA: Es la pizarra de tarifas y parámetros: guarda el precio de la hora, la tolerancia de minutos y las direcciones de las cámaras para cada sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite cambiar los precios del estacionamiento desde el panel web sin necesidad de reprogramar el sistema ni reiniciar el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `settings`: configuraciones globales del sistema (precios, parámetros numéricos en `valor` y de texto en `valor_str` como las IP de cámaras). La clave `clave` puede repetirse entre sedes; un índice único sobre `clave` + `COALESCE(sucursal_id,-1)` + `COALESCE(organization_id,-1)` permite que cada organización y cada sede tengan su propio tarifario global sin colisionar. `valor` tiene CheckConstraint no negativo.'
            ),
            "ParkingCamera": (
                '💡 LA IDEA: Es la ficha de cada cámara de seguridad: anota su nombre, su dirección de video (IP o webcam) y si está vigilando la entrada, la salida o el predio.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite agregar, calibrar y reordenar cámaras en la pantalla de monitoreo con un simple formulario web.\n\n'
                "⚙️ FUNCIONAMIENTO: Tabla `parking_cameras`: configuración de las cámaras de monitoreo con `nombre`, `tipo` ('ENTRADA','SALIDA','PREDIO','PATENTE','QR'), `source` (IP, path de video o id de webcam), `sucursal_id`, `activa` y `orden` (posición manual en la grilla de monitoreo; NULL va al final)."
            ),
            "AccessLog": (
                '💡 LA IDEA: Es el libro de actas fotográfico: cada vez que pasa un auto, anota la patente leída, la hora exacta, el costo, la foto del vehículo y si pagó en caja o por app.\n\n'
                '🎯 POR QUE FUE GENERADA: Es la evidencia legal y financiera indispensable para resolver cualquier reclamo de clientes o extravío de vehículos.\n\n'
                "⚙️ FUNCIONAMIENTO: Tabla `access_logs`: auditoría cronológica de accesos detectados por ALPR. Cada fila guarda la `patente_detectada` y su versión `normalized_patente`, `tipo_evento` (ENTRADA/SALIDA), `tipo_vehiculo`, la `reserva_id` y `floor_id` opcionales, `fecha_hora`, la `fecha_pago` (para reportes financieros), `imagen_path`, `pago_confirmado`, `metodo_pago` ('DIGITAL' o 'CAJA'), `costo_estadia` (no negativo) y `ocr_time`. Tiene índices para búsquedas por patente/tipo/sede/fecha y por reserva, y relaciones con Reservation, ParkingFloor y ParkingBranch."
            ),
            "ParkingBranch": (
                '💡 LA IDEA: Es la ficha física de una playa de estacionamiento: dirección postal, teléfono, coordenadas GPS para el mapa, horarios de atención y si abre las 24 horas.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda a los clientes toda la información necesaria para encontrar y elegir la sucursal más conveniente en el mapa.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `parking_branches`: las sedes físicas de AUTOPASS (el nombre de la sucursal vive únicamente acá). Guarda `nombre`, `organization_id`, `direccion`, `telefono`, `horario`, `is_24h`, `logo_url`, `activa` y coordenadas `latitude`/`longitude`. Un índice único sobre nombre + organización permite que dos empresas repitan nombre de sede pero no dentro de la misma. Tiene relación `floors` en cascada (borrar la sede borra sus pisos).'
            ),
            "ParkingFloor": (
                '💡 LA IDEA: Es el plano por niveles: define los pisos (Planta Baja, 1° Piso, Subsuelo) y cuántas plazas tiene cada uno.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite guiar a los conductores hacia los pisos con lugares libres en edificios de estacionamiento grandes.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `parking_floors`: pisos o niveles dentro de una sede. Repite la estructura de capacidad/ocupación de `ParkingAforo` (total, motos, camionetas y reservas de cada tipo) pero por piso, más `branch_id` y el `nombre` del piso. Su relación `branch` vuelve a ParkingBranch, que es la dueña del ciclo de vida.'
            ),
        },
    },
    "models/reservation.py": {
        "proposito": "Registra las reservas de estacionamiento (puntuales, recurrentes o cargadas manualmente por el personal), incluyendo su estado de pago y los datos del vehículo y la sede. También guarda una 'foto' de las tarifas vigentes al momento de cotizar, para auditar el precio histórico.",
        "simbolos": {
            "Reservation": (
                '💡 LA IDEA: Es el contrato de reserva anticipada: asegura un lugar para una patente entre dos fechas y horarios determinados, cobrando una seña o el total.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza al conductor que encontrará una cochera vacía esperando por él al llegar, incluso en días de alta demanda o recitales.\n\n'
                "⚙️ FUNCIONAMIENTO: Tabla `reservations`. Guarda `user_id` y `patente`, el rango `fecha_inicio`/`fecha_fin` (con CheckConstraint que exige fin >= inicio) y `dias_semana` serializado para reservas recurrentes. El cobro se reparte entre `monto_total`, `monto_reembolsado` y `fecha_pago`, con `mp_preference_id` para Mercado Pago y los estados `estado_pago` y `estado_reserva`. Apunta a la sede por `sucursal_id` más un `sucursal_info` de respaldo. Distingue `tipo_estadia`, `tipo_vehiculo`, `cliente_nombre`, `metodo_pago` y `origen` ('cliente' o 'manual'). Además fija la tarifa histórica: `tarifa_hora`, `tarifa_fraccion`, `tarifa_aplicada`, `horas_calculadas`, `monto_calculado`, `descuento_pct` y `tarifa_fijada_en`. Relaciona con User (dueño), AccessLog y ParkingBranch, y expone el hybrid `sucursal_nombre`."
            ),
        },
    },
    "models/support.py": {
        "proposito": 'Modela el sistema de soporte: un ticket que abre el usuario ante un problema y los mensajes/adjuntos de la conversación con el equipo. Sirve tanto a reclamos de clientes como a consultas operativas.',
        "simbolos": {
            "SupportTicket": (
                '💡 LA IDEA: Es la carpeta de reclamo o consulta: agrupa el problema que tuvo el usuario con su estado de atención (Pendiente, En Proceso, Resuelto).\n\n'
                '🎯 POR QUE FUE GENERADA: Ordena las quejas de los clientes para que ningún pedido de ayuda quede olvidado sin respuesta.\n\n'
                "⚙️ FUNCIONAMIENTO: Tabla `support_tickets`: cabecera del reclamo con `user_id` (autor), `categoria`, `sucursal_id` opcional, `asunto`, `mensaje` y `estado` (arranca en 'Pendiente'). `created_at` y `updated_at` se cargan con `localnow` y la segunda se refresca en cada cambio. Relaciona con User (backref `tickets`) y con ParkingBranch, y expone el hybrid `sucursal` con default 'General' para tickets que no apuntan a una sede."
            ),
            "SupportTicketMessage": (
                '💡 LA IDEA: Es cada mensaje dentro del chat de soporte entre el cliente y el personal del estacionamiento, incluyendo fotos o comprobantes adjuntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Registra el diálogo cronológico completo para brindar una atención transparente y documentada.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `support_ticket_messages`: cada mensaje de la conversación de un ticket, con `ticket_id`, `user_id` (autor), `mensaje`, adjuntos opcionales (`adjunto_url` y `adjunto_nombre` original) y `created_at` con `localnow`. Relaciona con SupportTicket (backref `messages`) y con el User que lo escribió.'
            ),
        },
    },
    "models/types.py": {
        "proposito": "Utilidades de fecha compartidas por todos los modelos. Define un tipo de columna híbrido que en la BD se guarda como timestamp real pero en Python se comporta como string 'YYYY-MM-DD HH:MM:SS', para mantener compatibilidad con los JavaScripts del frontend sin perder el tipo de dato en la base.",
        "simbolos": {
            "parse_fecha": (
                "💡 LA IDEA: Es el traductor universal de calendarios: no importa si una fecha viene con letras 'T', guiones, microsegundos o espacios, la entiende y la convierte en un objeto fecha de Python.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita caídas del sistema por diferencias en los formatos de fecha que mandan los navegadores o teléfonos.\n\n'
                "⚙️ FUNCIONAMIENTO: Convierte a datetime un valor flexible: None o cadena vacía dan None; si ya es datetime lo devuelve tal cual; si es texto, lo normaliza (quita espacios y cambia la 'T' por espacio) y prueba formatos con microsegundos, con segundos y sin segundos, y por último `fromisoformat`. Si ninguno funciona lanza ValueError con 'Fecha invalida'."
            ),
            "formatear_fecha": (
                "💡 LA IDEA: Es el relojero de precisión: toma cualquier fecha y la convierte al formato prolijo estándar 'YYYY-MM-DD HH:MM:SS'.\n\n"
                '🎯 POR QUE FUE GENERADA: Asegura que todas las pantallas y reportes muestren las fechas con el mismo estilo uniforme.\n\n'
                "⚙️ FUNCIONAMIENTO: Normaliza un valor al formato canónico 'YYYY-MM-DD HH:MM:SS'. Si recibe texto, primero lo parsea con `parse_fecha`; si no hay valor devuelve None; si el parseo falló devuelve None. Es el formateador que usa el tipo de columna al leer."
            ),
            "DateTimeAsStr": (
                '💡 LA IDEA: Es el camaleón de fechas: en la base de datos se guarda como una fecha real de alta velocidad, pero hacia el código de Python y JavaScript se muestra como un texto sencillo y fácil de leer.\n\n'
                '🎯 POR QUE FUE GENERADA: Combina la velocidad de búsqueda de fechas en la base de datos con la simplicidad de manejo de texto en el frontend.\n\n'
                '⚙️ FUNCIONAMIENTO: TypeDecorator de SQLAlchemy con `impl = DateTime`: la columna es un timestamp en la base de datos, pero la capa Python la expone como string con segundos. `cache_ok` está activado para poder reutilizar la compilación. Se usa en las columnas de fecha de User, Reservation, AccessLog y MercadoPagoPayment.'
            ),
            "process_bind_param": (
                '💡 LA IDEA: Es el encargado de empaquetar la fecha justo antes de guardarla en la base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la base de datos siempre reciba una fecha válida y limpia.\n\n'
                '⚙️ FUNCIONAMIENTO: Método de DateTimeAsStr que se ejecuta al GUARDAR: convierte el valor recibido con `parse_fecha` para escribir un datetime válido en la base. Acepta indistintamente string o datetime.'
            ),
            "process_result_value": (
                '💡 LA IDEA: Es el encargado de desempaquetar la fecha al leerla de la base de datos para entregársela al usuario en formato texto.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el frontend reciba formatos extraños o incompatibles con los componentes visuales.\n\n'
                "⚙️ FUNCIONAMIENTO: Método de DateTimeAsStr que se ejecuta al LEER: si el valor es None lo deja en None; si existe, lo formatea con `strftime('%Y-%m-%d %H:%M:%S')`, de modo que el código Python y el frontend siempre reciben el string canónico."
            ),
        },
    },
    "models/user.py": {
        "proposito": 'Núcleo de identidad y fidelización de AUTOPASS: define el usuario (cliente o personal), su flota de vehículos, el historial de puntos, el catálogo de promociones canjeables y los tickets/vouchers emitidos al canjear. Es la base de la autenticación y del sistema de beneficios.',
        "simbolos": {
            "datetime_now_iso": (
                '💡 LA IDEA: Es el fechador automático para vouchers y tickets de puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Registra el momento exacto en que un usuario canjeó un beneficio.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la fecha y hora actuales como string ISO (`datetime.datetime.now().isoformat()`). Se usa como valor por defecto de `RedemptionTicket.created_at`.'
            ),
            "User": (
                '💡 LA IDEA: Es el legajo digital de cada persona: guarda sus datos personales, su contraseña protegida, sus puntos acumulados y su saldo en billetera.\n\n'
                '🎯 POR QUE FUE GENERADA: Es la entidad central de todo el sistema; sin usuario no hay cobros, reservas ni seguridad.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `users`: cuenta de cualquier persona del sistema (cliente o personal, según `rol`: ADMIN, LOCAL_ADMIN, STAFF, USER). Datos personales `nombre`, `apellido`, `dni` y `email` (ambos únicos e indexados), `telefono`, `patente` (referencia rápida), `direccion` y `password_hash`. Pertenencia multiempresa vía `organization_id` y `sucursal_id`. Estado de fidelización y cuenta: `puntos_acumulados` y `saldo` (CheckConstraint que impide negativos), `is_blocked` y `is_deleted`. Relaciona con ParkingBranch, Organization, sus `vehicles`, `reservations`, `points_logs` y `redemption_tickets`, y expone el hybrid `sucursal`.'
            ),
            "Vehicle": (
                '💡 LA IDEA: Es la cédula verde digital: vincula una patente con su dueño, indicando la marca, el modelo y si es su auto favorito.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el sistema reconozca al cliente apenas la cámara lee la patente y le cargue la estadía a su cuenta automáticamente.\n\n'
                "⚙️ FUNCIONAMIENTO: Tabla `vehicles`: un vehículo del usuario, con `user_id`, `patente` (única e indexada), `marca_modelo`, `tipo` ('Auto' por defecto) y `is_favorite` para marcar el principal. Relaciona con su `owner` (User)."
            ),
            "PointsLog": (
                '💡 LA IDEA: Es el extracto bancario de puntos: anota cada punto ganado por estacionar y cada punto gastado en promociones.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda total transparencia al cliente para que pueda auditar cómo sumó o gastó sus puntos de fidelización.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `points_log`: historial de movimientos del sistema de fidelización. Cada fila guarda a qué `user_id` pertenece, la `cantidad` de puntos (positiva o negativa), el `motivo` y la `fecha` (con DateTimeAsStr). Relaciona con User.'
            ),
            "Promotion": (
                '💡 LA IDEA: Es el escaparate de premios: lista los descuentos y beneficios que los clientes pueden conseguir a cambio de sus puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Fideliza a los usuarios incentivándolos a volver a estacionar en la red AUTOPASS para sumar recompensas.\n\n'
                "⚙️ FUNCIONAMIENTO: Tabla `promotions`: catálogo de beneficios canjeables por puntos. Guarda `titulo`, `descripcion`, `costo_puntos` (no negativo), `icono` y `categoria`, `activa`, y pertenencia por `organization_id`/`sucursal_id`. Distingue el `tipo_canje` ('descuento_reserva' que aplica un % al pago, o 'voucher' que genera un QR sin validación automática); `valor_descuento` (1 a 100, con CheckConstraint) solo aplica al primer tipo. Incluye la ubicación del canje (`direccion`, `latitude`, `longitude`). Relaciona con ParkingBranch y expone el hybrid `sucursal`."
            ),
            "RedemptionTicket": (
                '💡 LA IDEA: Es el cupón o voucher emitido: cuando el cliente canjea puntos, se genera este ticket digital con su propio código QR y una validez de 30 días.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el cliente presente su descuento en la barrera o en el comercio adherido sin riesgo de duplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `redemption_tickets`: voucher persistente emitido al canjear puntos. Guarda `user_id`, `promotion_id` opcional, un `codigo` único para el QR, y un snapshot del beneficio al momento del canje (`titulo`, `descripcion`, `tipo_canje`, `valor_descuento`, `icono`) para que editar la promoción después no altere los vouchers ya emitidos. Incluye `sucursal_id`, `estado` (VIGENTE/USADO/CANCELADO), `qr_data` (contenido AUTOPASS_REDEMPTION|...), `observacion`, `created_at`, `fecha_uso` y `reserva_id` si se aplicó a una reserva. También guarda el snapshot de ubicación (`direccion`, `latitude`, `longitude`) para el botón de Google Maps. Relaciona con User y ParkingBranch y expone el hybrid `sucursal`.'
            ),
            "fecha_vencimiento": (
                '💡 LA IDEA: Es la fecha límite del cupón: calcula exactamente 30 días posteriores al canje.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que los cupones queden vigentes de por vida, incentivando el consumo oportuno de las promociones.\n\n'
                '⚙️ FUNCIONAMIENTO: Propiedad de RedemptionTicket: si hay `created_at`, lo parsea con `fromisoformat` y devuelve la fecha 30 días después (ISO); si falta o el formato es inválido, devuelve None. Define hasta cuándo es válido el voucher.'
            ),
        },
    },
    "models/user_session.py": {
        "proposito": 'Registra las sesiones/dispositivos desde los que se conecta cada usuario, para poder detectar inicios de sesión en dispositivos nuevos y llevar un rastro de auditoría de accesos a la cuenta.',
        "simbolos": {
            "UserSession": (
                '💡 LA IDEA: Es el registro de dispositivos conocidos: recuerda si el usuario se conectó desde su celular de siempre o desde una computadora desconocida.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite alertar al usuario si alguien inició sesión en su cuenta desde un dispositivo sospechoso.\n\n'
                '⚙️ FUNCIONAMIENTO: Tabla `user_sessions`: asocia `user_id` con un `device_id` (indexado), y guarda datos de contexto como `user_agent` e `ip_address`, más `created_at` y `last_login_at` (indexado, con `localnow`). Relaciona con User mediante el backref `sessions`.'
            ),
        },
    },
}
