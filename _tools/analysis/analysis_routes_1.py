"""Explicaciones analizadas de la capa de rutas del panel admin (parte 1): montaje
de routers y endpoints FastAPI de sucursales, operaciones, promociones, reservas,
configuración, soporte, usuarios y hora virtual."""

ANALISIS: dict[str, dict] = {
    "routes/__init__.py": {
        "proposito": (
            "💡 LA IDEA: Es la 'central telefónica o conmutador principal' de la API web. Recibe todas las líneas de comunicación externas (autos, usuarios, cobros, cámaras, reportes) y las agrupa en un único mostrador para que el servidor web las conecte al arrancar.\n\n"
            "🎯 POR QUE FUE GENERADA: En lugar de que `main.py` tenga que importar 20 archivos de rutas individuales uno por uno, este archivo empaqueta todos los routers por dominio (`auth`, `admin`, `user`, `parking`, `system`, `reports`) y los expone ordenadamente.\n\n"
            "⚙️ FUNCIONAMIENTO: Importa los routers de cada subdirectorio y los reúne en variables limpias (`admin_router`, `user_router`, `parking_router`, `auth_router`, `reports_router`, `system_router`), permitiendo que `main.py` registre toda la API completa con un simple bucle de inclusión."
        ),
        "simbolos": {
        },
    },
    "routes/admin/__init__.py": {
        "proposito": (
            "💡 LA IDEA: Es la 'puerta de entrada a la oficina de administración'. Pone un guardia en la puerta que exige credenciales de jefe (`role: admin`) y le coloca el cartelito oficial `/v1/admin/` a todas las salas y pasillos administrativos.\n\n"
            "🎯 POR QUE FUE GENERADA: Evita tener que repetir la palabra `/v1/admin` en cada una de las 8 secciones de gestión (usuarios, tarifas, sucursales, promociones, reservas) y garantiza que todas las pantallas administrativas compartan las mismas etiquetas de documentación OpenAPI.\n\n"
            "⚙️ FUNCIONAMIENTO: Instancia un `APIRouter` con prefijo `/v1/admin` y etiqueta 'Administration'. Conecta e incluye a los 8 subrouters de gestión: usuarios (`users`), reservas (`reservations`), configuración (`settings`), sucursales (`branches`), promociones (`promotions`), operaciones (`operations`), hora virtual (`virtual_time`) y soporte (`support`)."
        ),
        "simbolos": {
        },
    },
    "routes/admin/branches.py": {
        "proposito": 'Endpoints del panel admin para gestionar sucursales (estacionamientos) y sus pisos: listado con resumen de ocupación, alta/baja/edición de sucursales, carga de logo con validación, alta/baja de pisos y ajuste de capacidades por tipo de vehículo. Las operaciones destructivas exigen super-admin y verifican que no haya vehículos físicos ni reservas activas antes de borrar o suspender.',
        "simbolos": {
            "_save_branch_logo": (
                '💡 LA IDEA: Es el encargado de recibir y revisar la foto del logo de una sucursal, asegurándose de que sea una imagen válida, que no pese una barbaridad y guardándola en la carpeta de subidas del servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que alguien suba archivos maliciosos (ejecutables) o imágenes gigantescas que colapsen el disco del servidor o la memoria de FastAPI.\n\n'
                "⚙️ FUNCIONAMIENTO: Función auxiliar privada que recibe un archivo subido (UploadFile), valida que la extensión sea png/jpg/jpeg/webp y que no supere los 2 MB escribiendo en bloques de 64 KB; si el archivo está vacío o excede el límite lo elimina y lanza HTTP 400. Devuelve la ruta pública '/static/uploads/branches/...' del logo persistido."
            ),
            "list_branches": (
                '💡 LA IDEA: Es la cartelera que muestra la lista de todas las sucursales que administra la empresa, junto con un resumen en vivo de cuántos autos hay en cada una.\n\n'
                '🎯 POR QUE FUE GENERADA: El personal administrativo necesita un mapa general rápido para ver el aforo y estado de sus locales sin tener que consultar local por local.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /branches: lista las sucursales con un resumen de ocupación, filtradas por la organización del usuario actual (guard get_operational_user). Delega en BranchService.list_branches_with_summary y devuelve BranchResponse.'
            ),
            "add_floor": (
                '💡 LA IDEA: Es el constructor que da de alta un piso nuevo dentro de un estacionamiento, definiendo cuántos autos, motos o camionetas entran allí.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite modelar estacionamientos multinivel de manera modular y actualizar de inmediato el aforo disponible para los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /{branch_id}/floors: agrega un piso nuevo a una sucursal. Valora que exista la sucursal (404 si no), aplica los guards validate_local_admin_branch (jurisdicción de sede) y enforce_organization_scope (aislamiento multiempresa), y crea un ParkingFloor con las capacidades totales y por tipo de vehículo (autos/motos/camionetas, con y sin reserva). Tras commit notifica el cambio de ocupación vía NotificationService (best-effort).'
            ),
            "delete_floor": (
                '💡 LA IDEA: Es la orden de demolición controlada: permite eliminar un piso del sistema, pero únicamente si está completamente vacío de vehículos y no tiene reservas pendientes.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita inconsistencias críticas y pérdida de datos; si se borrara un piso con vehículos adentro, esos autos quedarían en un limbo sin poder salir ni cobrarse.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint DELETE /floors/{floor_id}: elimina un piso solo si no tiene vehículos estacionados (ni autos, motos, camionetas ni reservas); si la ocupación es mayor a cero lanza 400. Valora 404 si el piso no existe y aplica los guards de sede y organización sobre la sucursal dueña del piso. Notifica el cambio de ocupación tras borrar.'
            ),
            "update_floor_capacity": (
                '💡 LA IDEA: Es el ajuste de pintura en las líneas del piso: permite ampliar o reducir los lugares para autos, motos o camionetas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite adaptar el espacio a la demanda real, pero impidiendo que un administrador configure una capacidad menor a la cantidad de vehículos que ya están estacionados.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint PATCH /floors/{floor_id}: actualiza las capacidades de un piso (autos, motos, camionetas y reservas por tipo). Valora que cada capacidad nueva no sea menor a la ocupación actual correspondiente (400 con mensaje descriptivo), recalcula capacidad_reservas como suma de autos+motos+camionetas cuando se envían los valores por tipo, y notifica el cambio de ocupación. Guards: get_local_manager, validate_local_admin_branch y enforce_organization_scope.'
            ),
            "create_branch": (
                '💡 LA IDEA: Es el formulario de inauguración de una nueva sucursal del estacionamiento, guardando su nombre, dirección y logo identificador.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el superadministrador sume nuevos locales al sistema de manera sencilla y segura, verificando que no existan nombres duplicados.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /branches: crea una sucursal (multipart con campos de formulario y logo opcional). Solo para super-admin (get_super_admin). Valora que el nombre no exista ya en la organización (400), guarda el logo con _save_branch_logo si se envió y crea el ParkingBranch activo con la organización del admin. Devuelve confirmación con el nombre de la sucursal creada.'
            ),
            "delete_branch": (
                '💡 LA IDEA: Es el cierre definitivo y baja de un estacionamiento completo del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un cierre seguro, impidiendo borrar una sucursal si todavía tiene coches adentro o reservas activas, y limpiando además sus imágenes del disco.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint DELETE /branches/{branch_id}: elimina una sucursal de forma segura. Solo super-admin; aplica enforce_organization_scope. Verifica en orden: 404 si no existe, 400 si tiene vehículos físicos (BranchService.has_physical_occupancy) o reservas activas/pendientes (ReservationRepository.get_active_by_sucursal). Borra el archivo de logo del disco (si no es el por defecto) y luego la fila de la sucursal.'
            ),
            "update_branch": (
                '💡 LA IDEA: Es la ficha de renovación de una sucursal: permite cambiar su dirección, teléfonos, horarios de atención, coordenadas o renovar su logo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite mantener al día la información pública que ven los conductores cuando buscan estacionamiento en el mapa o en la app.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint PATCH /branches/{branch_id}: actualiza los datos de una sucursal (nombre, dirección, teléfono, horario, 24h, coordenadas) y su logo. Solo super-admin con enforce_organization_scope. Si cambió el nombre delega en BranchService.rename_branch (propaga a reservas/estancias). El logo nuevo se guarda primero y recién después se borra el anterior; con logo_clear solo borra y restaura el logo por defecto.'
            ),
            "toggle_branch_status": (
                '💡 LA IDEA: Es la persiana metálica del local: permite poner la sucursal en mantenimiento o suspenderla temporalmente sin borrar su historial ni sus datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite frenar el ingreso de nuevos clientes ante una emergencia o feriado, pero bloqueando la suspensión si aún quedan vehículos adentro.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /branches/{branch_id}/toggle: activa o suspende una sucursal alternando el flag activa. Solo super-admin con enforce_organization_scope. Si se va a desactivar y la sucursal tiene vehículos en su interior, lanza 400 para no dejar clientes varados. Devuelve el nuevo estado activa.'
            ),
        },
    },
    "routes/admin/operations.py": {
        "proposito": 'Operaciones manuales del personal de sede desde el dashboard admin: abrir/cerrar barreras por hardware, registrar entradas y salidas manuales de vehículos y cancelar estadías. Todos los endpoints requieren permisos operativos (staff de la sede) y aplican rate limit estricto por minuto.',
        "simbolos": {
            "open_barrier": (
                '💡 LA IDEA: Es el pulsador de control remoto para levantar o bajar una barrera específica desde la computadora del operador.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al empleado resolver manualmente imprevistos (como un vehículo de auxilio o un ticket trabado) sin tener que ir físicamente hasta el motor de la barrera.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /open-barrier: envía un comando de apertura o cierre de barrera (OPEN/CLOSE) para un gate_id determinado. Valida permisos con get_operational_user y limita a 30 pedidos por minuto. Delega en HardwareService.trigger_barrier (MQTT y serial/Arduino) registrando como método MANUAL_OP el id y la sede del staff; devuelve el resultado del hardware.'
            ),
            "manual_entry": (
                '💡 LA IDEA: Es la libreta de guardia para anotar el ingreso forzado de un vehículo cuando la cámara automática no logró leer la patente.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que un cliente quede frenado en la entrada cuando tiene la patente sucia, doblada o de formato especial, iniciando su estadía de inmediato.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /manual-entry: registra un ingreso forzado al predio de la sede donde trabaja el staff (se usa cuando el lector de patentes no funcionó). Recibe patente, tipo de vehículo y piso opcional; delega en AccessService.manual_entry pasando la sucursal del usuario autenticado. Guard get_operational_user y rate limit 30/min.'
            ),
            "manual_exit": (
                '💡 LA IDEA: Es la orden de salida manual desde la garita para cobrar y habilitar el egreso de un auto cuya patente no fue captada al salir.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cajero procesar el cobro correspondiente, liberar la plaza en el sistema y levantar la barrera de egreso sin demorar la fila.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /manual-exit: registra una salida manual de la sede para una patente dada, usando la sucursal del staff autenticado. Delega todo el cálculo de cobro y cierre en AccessService.manual_exit. Guard get_operational_user y rate limit 30/min.'
            ),
            "cancel_stay": (
                '💡 LA IDEA: Es la anulación inmediata de un ingreso erróneo o un cliente que entró por error y se retira dentro de la tolerancia de cortesía.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el cliente tenga que pagar si dio la vuelta de inmediato (primeros 10 minutos) o corregir un ingreso anotado por equivocación.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /cancel-stay: cancela la estadía activa de una patente en la sede del staff; si el vehículo está dentro del período de cortesía (10 minutos) no se cobra. Delega en AccessService.cancel_stay. Guard get_operational_user y rate limit 30/min.'
            ),
        },
    },
    "routes/admin/promotions.py": {
        "proposito": 'CRUD administrativo de promociones (canjes de puntos por vouchers o descuentos de reserva) del panel admin. Aplica doble aislamiento: por organización (enforce_organization_scope) y, para administradores locales, por sucursal (solo operan promos de su sede).',
        "simbolos": {
            "_check_promo_org": (
                '💡 LA IDEA: Es el guardia de seguridad que corrobora que una promoción pertenezca a la empresa del administrador que intenta manipularla.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que un administrador modifique, active o borre promociones de otra compañía que comparte la misma plataforma.\n\n'
                "⚙️ FUNCIONAMIENTO: Auxiliar que aplica enforce_organization_scope entre el admin y la promoción, con detalle 'Promoción no encontrada' y código 404 si la promo pertenece a otra empresa. Es tolerante cuando alguno de los dos no tiene organización (datos legacy o de tests)."
            ),
            "list_promotions_admin": (
                '💡 LA IDEA: Es el catálogo de ofertas y canjes de puntos que el personal de la empresa puede consultar desde su panel de control.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los administradores locales ver sus promociones y a los generales supervisar los beneficios vigentes de toda la red.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /promotions: lista las promociones visibles para el admin. Los locales (rol != ADMIN) solo ven las de su sucursal; el admin global ve las de toda su organización. Normaliza promos antiguas marcando activa=True cuando el campo es None. Guard get_local_manager.'
            ),
            "create_promotion": (
                '💡 LA IDEA: Es la imprenta de nuevos cupones: da de alta un beneficio (por ejemplo, descuento en reservas o regalos) a cambio de puntos acumulados.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a las sucursales lanzar campañas de fidelización para premiar a sus clientes frecuentes y atraer más conductores.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint POST /promotions: crea una promoción. Los admins locales la atan a su propia sucursal (ignoran el campo sucursal del body); el admin global puede elegir sucursal o dejarla global. Solo conserva valor_descuento si el tipo de canje es 'descuento_reserva'. Asigna la organización del admin. Guard get_local_manager y rate limit."
            ),
            "toggle_promotion": (
                '💡 LA IDEA: Es el interruptor de encendido y apagado de una promoción sin necesidad de borrarla del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite pausar una oferta cuando se agota el stock o volver a activarla en fechas especiales sin tener que cargar todo desde cero.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /promotions/{promo_id}/toggle: activa o desactiva una promoción. Valora 404 si no existe, aplica el aislamiento de organización (_check_promo_org) y, si el admin no es global, verifica con same_branch que la promo sea de su sede (403 si no). Devuelve el nuevo estado activa.'
            ),
            "update_promotion": (
                '💡 LA IDEA: Es el editor de términos y condiciones: permite cambiar la cantidad de puntos requerida, el porcentaje de descuento o el texto de la promoción.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita corregir errores de tipeo o actualizar el costo en puntos de una recompensa sin perder el historial de canjes.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint PUT /promotions/{promo_id}: actualiza todos los campos de una promoción existente con las mismas validaciones de 404, organización y sucursal que el toggle. Solo el admin global puede reasignar la sucursal de la promo; igual que en la creación, valor_descuento solo se guarda si el tipo de canje es 'descuento_reserva'."
            ),
            "delete_promotion": (
                '💡 LA IDEA: Es la eliminación definitiva de una promoción que ya no volverá a usarse en el estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpia la lista de ofertas y desvincula ordenadamente los cupones antiguos para no violar restricciones de clave foránea en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint DELETE /promotions/{promo_id}: elimina una promoción tras las validaciones de existencia, organización y sucursal. Antes de borrar, desasocia los tickets de canje poniendo promotion_id en NULL (RedemptionRepository.unlink_promotion) porque los tickets guardan un snapshot del beneficio y la FK impediría el borrado.'
            ),
        },
    },
    "routes/admin/reservations.py": {
        "proposito": 'Gestión de reservas desde el panel admin y caja: listado filtrado, creación y edición manuales, confirmación de pago, cancelación y consulta de descuentos (redenciones) aplicables al cliente. Todos los endpoints exigen permisos operativos y delegan la lógica de negocio en ReservationService, que a su vez filtra por jurisdicción de sede según el rol.',
        "simbolos": {
            "patente_lookup": (
                '💡 LA IDEA: Es el identificador rápido de clientes: al tipear una patente en la caja, dice al instante si pertenece a un usuario registrado.\n\n'
                '🎯 POR QUE FUE GENERADA: Agiliza la carga de reservas en el mostrador para asociar al conductor a su cuenta sin obligarlo a dictar todos sus datos personales.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /reservations/patente-lookup: busca si una patente está registrada a un usuario para vincularla a una reserva manual en caja. Devuelve solo lo necesario para el badge (sin email ni otros datos sensibles). Delega en ReservationService.lookup_patente. Guard get_operational_user y rate limit admin.'
            ),
            "get_new_reservations_count": (
                '💡 LA IDEA: Es la campanita roja de notificaciones que avisa cuántas reservas nuevas entraron desde la última vez que miraste la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al operador de garita enterarse al instante de nuevas llegadas sin tener que refrescar toda la página web continuamente.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /reservations/new-count: devuelve cuántas reservas nuevas hay desde un since_id opcional y el último id registrado; alimenta la burbuja de notificación de la pestaña Reservas del dashboard. Delega en ReservationService.get_new_reservations_count y filtra según el staff.'
            ),
            "list_reservations": (
                '💡 LA IDEA: Es la planilla de turnos y reservas del estacionamiento, donde se pueden filtrar reservas pasadas, presentes y futuras por estado y fecha.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga al personal una visión clara de los vehículos que van a ingresar para organizar el espacio y no sobrepasar la capacidad.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /reservations: lista todas las reservas con filtros opcionales de estado y sucursal. Los administradores locales solo ven las de su sede (el filtrado lo hace ReservationService.list_admin_reservations según el rol). Devuelve UserReservationResponse. Guard get_operational_user.'
            ),
            "create_admin_reservation": (
                '💡 LA IDEA: Es el talonario de reservas telefónicas o presenciales que el empleado carga a mano a pedido de un cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite asegurar una plaza a clientes que llaman por teléfono o se acercan al mostrador sin usar la aplicación móvil.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /reservations: permite al admin o empleado crear una reserva manual (por ejemplo, teléfono o presencial) con los datos de AdminReservationCreate. Delega en ReservationService.create_admin_reservation. Guard get_operational_user y rate limit.'
            ),
            "update_admin_reservation": (
                '💡 LA IDEA: Es el borrador de modificaciones de reservas manuales para cambiar fechas, horarios o patentes solicitadas por el cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite corregir imprevistos o cambios de planes del conductor antes de que empiece el horario reservado.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint PUT /reservations/{res_id}: edita una reserva creada por administrador o empleado; no aplica a reservas creadas por clientes. Delega en ReservationService.update_admin_reservation. Guard get_operational_user y rate limit.'
            ),
            "confirm_reservation_payment": (
                "💡 LA IDEA: Es el sello de 'PAGADO' que estampa el cajero cuando el cliente abona su reserva en efectivo o tarjeta física en la garita.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite registrar cobros por fuera de Mercado Pago, dejando la reserva confirmada y lista para que la barrera reconozca el auto al llegar.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /reservations/{res_id}/confirm-payment: confirma manualmente el pago de una reserva (caja física, transferencia, etc.) con un ConfirmPaymentRequest opcional. Delega en ReservationService.confirm_reservation_payment. Guard get_operational_user y rate limit.'
            ),
            "cancel_reservation_admin": (
                '💡 LA IDEA: Es la orden de cancelación de una reserva ejecutada por el personal administrativo por pedido del cliente o fuerza mayor.\n\n'
                '🎯 POR QUE FUE GENERADA: Libera la plaza reservada para que otros conductores puedan utilizarla y actualiza el estado contable y operativo del turno.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint POST /reservations/{res_id}/cancel: cancela una reserva desde el panel. Primero verifica la jurisdicción con ReservationService.get_permissioned_reservation (lanza 403 si la reserva no le corresponde), luego llama a ReservationService.cancel_reservation pasando None como usuario (es una cancelación administrativa). Si el servicio devuelve estado distinto de 'ok', responde 400 con el mensaje."
            ),
            "reservation_available_redemptions": (
                '💡 LA IDEA: Es la billetera de cupones del cliente vinculada a su reserva actual, mostrando qué descuentos tiene acumulados por puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al cajero ofrecer y descontar beneficios del programa de puntos directamente en el momento de liquidar la cuenta.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /reservations/{res_id}/redemptions: lista los descuentos de reserva (%) vigentes del cliente vinculado a la reserva y aplicables a su sucursal, para ofrecerlos al registrar el pago en caja. Calcula para cada descuento el monto en pesos y el monto final redondeado. Guard get_operational_user.'
            ),
            "reservation_redemption_info": (
                '💡 LA IDEA: Es la lupa que revisa el ticket de cobro para verificar si a una reserva se le aplicó un descuento por puntos y de cuánto fue.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza transparencia contable al mostrar con exactitud por qué se cobró un monto menor al valor de tarifa estándar.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint GET /reservations/{res_id}/redemption-info: informa si a una reserva le aplica un descuento, con fuente 'vigente' (el cliente tiene un canje de descuento sin consumir) o 'aplicado' (la reserva ya se pagó en caja con un ticket consumido vía RedemptionRepository.get_used_discount_for_reserva). Devuelve el porcentaje, el ticket y el monto total. Guard get_operational_user."
            ),
            "admin_available_redemptions": (
                '💡 LA IDEA: Es el asistente de promociones que consulta qué beneficios por puntos tiene un usuario antes de crearle una reserva nueva en caja.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita que el operador le informe al cliente sus descuentos disponibles mientras le toma la reserva en el mostrador.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /redemptions/available: lista los descuentos de reserva (%) vigentes de un user_id determinado aplicables a una sucursal opcional; se usa en el flujo de nueva reserva manual en caja para ofrecer el descuento antes de crear y pagar la reserva. Delega en ReservationService.get_admin_available_redemptions. Guard get_operational_user y rate limit.'
            ),
        },
    },
    "routes/admin/settings.py": {
        "proposito": 'Lectura y escritura de la configuración del estacionamiento (tarifas por tipo de vehículo y aforo/capacidades) desde el panel admin. Todo está aislado por organización y, para los locales, por sucursal; las claves editables vienen de un catálogo fijo para evitar inyección de claves arbitrarias en la tabla Settings.',
        "simbolos": {
            "_aforo_vigente": (
                '💡 LA IDEA: Es el registro del libro de capacidades que busca la configuración de plazas de la sucursal asegurando que pertenezca a la empresa correcta.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita mezclar o exponer los aforos de una empresa ajena en entornos compartidos multiempresa.\n\n'
                '⚙️ FUNCIONAMIENTO: Auxiliar que trae la fila de aforo (ParkingAforo) de una sucursal o global. Si la fila es global (sucursal=None) pero pertenece a otra organización, devuelve None para no filtrar datos de otra empresa; es tolerante con filas sin organización (legacy/tests).'
            ),
            "get_admin_settings": (
                '💡 LA IDEA: Es la pantalla de configuración general donde el encargado ve las tarifas por hora actuales y los límites de capacidad de cada tipo de vehículo.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda al administrador una visión centralizada de los precios vigentes y los aforos asignados para poder gestionarlos.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /settings: devuelve la configuración vigente como diccionario clave→valor para la organización del admin (los locales solo ven su sucursal). Agrega el nombre de la sucursal y, si hay fila de aforo, completa las capacidades y ocupaciones actuales por tipo de vehículo (autos, motos, camionetas y reservas). Guard get_local_manager.'
            ),
            "update_price": (
                '💡 LA IDEA: Es la pizarra de precios y aforos donde el administrador actualiza el valor de la hora o ajusta las plazas disponibles.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite modificar tarifas y capacidades de forma segura, recalculando los aforos, limpiando la memoria caché y notificando al instante a todo el sistema.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint POST /settings/prices: actualiza o crea una clave de configuración (precio o capacidad) para la organización/sucursal del admin. Valora que el valor no sea negativo (400) y que la clave esté en ALLOWED_SETTINGS_KEYS (400). Si la clave es de aforo, crea la fila ParkingAforo por defecto si no existe, recalcula capacidad_reservas como suma de las capacidades por tipo y notifica el cambio de ocupación; si es una tarifa, hace upsert en Settings y invalida la caché de tarifas (ttl_cache 'rate_'). Guard get_local_manager y rate limit."
            ),
        },
    },
    "routes/admin/support.py": {
        "proposito": 'Módulo de soporte y tickets del panel admin: el personal puede ver los tickets de soporte que le corresponden (por sucursal/rol), consultar el detalle con la conversación, responder, cambiar el estado y revisar el contador de pendientes que alimenta la burbuja del menú. La lógica de jurisdicción vive en SupportService.',
        "simbolos": {
            "get_admin_support_pending_count": (
                '💡 LA IDEA: Es el marcador numérico de la bandeja de entrada que muestra cuántos tickets de consulta de clientes quedan por responder.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al equipo de soporte notar de un vistazo rápido si hay clientes esperando ayuda y priorizar su atención.\n\n'
                "⚙️ FUNCIONAMIENTO: Endpoint GET /support-tickets/pending-count: devuelve la cantidad de tickets de soporte no resueltos que el admin actual puede ver; alimenta la burbuja de 'Soporte & Tickets' del dashboard. Delega en SupportService.get_admin_pending_count. Guard get_operational_user."
            ),
            "mark_ticket_notifications_read": (
                '💡 LA IDEA: Es el gesto de marcar los mensajes recibidos como leídos para que dejen de brillar en la lista de pendientes del operador.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el personal pierda tiempo reabriendo conversaciones que ya fueron atendidas o revisadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint PATCH /support-tickets/{ticket_id}/read-notifs: marca como leídas las notificaciones de un ticket para el admin actual, respetando la misma jurisdicción por sucursal que el listado y el detalle. Devuelve la cantidad de notificaciones marcadas. Guard get_operational_user y rate limit.'
            ),
            "get_admin_support_ticket": (
                '💡 LA IDEA: Es el historial completo de la conversación entre el cliente y el personal de atención técnica de la sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al operador leer todo el contexto del problema antes de responder, garantizando una respuesta coherente y rápida.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /support-tickets/{ticket_id}: devuelve el detalle de un ticket con todos sus mensajes (historial de la conversación). Si SupportService.get_admin_support_ticket_detail no encuentra el ticket dentro de la jurisdicción responde 404. Incluye datos del cliente (nombre, email) tolerando usuarios eliminados. Guard get_operational_user.'
            ),
            "get_admin_support_tickets": (
                '💡 LA IDEA: Es la bandeja de entrada de reclamos y consultas que permite filtrar tickets abiertos, en proceso o resueltos.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a organizar y distribuir los pedidos de soporte de los usuarios entre los empleados de cada estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /support-tickets: lista los tickets de soporte filtrados por sucursal y estado opcionales, aplicando la visibilidad según el rol del usuario actual. Delega en SupportService.get_admin_tickets. Guard get_operational_user.'
            ),
            "update_support_ticket": (
                "💡 LA IDEA: Es la respuesta del operador al cliente, permitiendo enviar un mensaje explicativo y cambiar el estado del reclamo (por ejemplo a 'resuelto').\n\n"
                '🎯 POR QUE FUE GENERADA: Facilita el diálogo fluido para solucionar los inconvenientes que reportan los conductores y archivar los reclamos cerrados.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint PATCH /support-tickets/{ticket_id}: permite responder un ticket y/o cambiar su estado (abierto, respondido, resuelto, etc.) con un SupportTicketUpdate. Si el servicio no encuentra el ticket en la jurisdicción responde 404; devuelve el estado actualizado y el historial de mensajes. Guard get_operational_user y rate limit.'
            ),
        },
    },
    "routes/admin/users.py": {
        "proposito": 'Gestión de usuarios del panel admin: listado, creación, invitación de administradores, edición de datos, cambio de rol, bloqueo, ajuste de saldo, reseteo de contraseña y baja. Centraliza las validaciones de jurisdicción (solo operar usuarios de tu sucursal/org) y de roles (solo el super-admin crea o promueve personal) en dos helpers reutilizados por todos los endpoints.',
        "simbolos": {
            "validate_local_admin_user_permission": (
                '💡 LA IDEA: Es la regla de jerarquía que impide que un administrador de una sede modifique cuentas de usuarios de otra sede o de administradores globales.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la privacidad de las cuentas y evita que un encargado de sucursal acceda o altere usuarios fuera de su jurisdicción.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper que valida que un admin tenga permisos de jurisdicción sobre un usuario objetivo. Aplica enforce_organization_scope (mismo tenant); el admin global pasa siempre; los locales solo pueden operar usuarios de su propia sucursal (normalizando nombres con normalize_branch_name), nunca a otro Administrador Global (403) ni a personal de otra sede (403).'
            ),
            "validate_staff_role_assignment": (
                '💡 LA IDEA: Es el candado de nombramientos que reserva exclusivamente al superadministrador el poder de designar nuevos empleados o gerentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que un empleado o encargado local ascienda a otras personas o a sí mismo a cargos con mayores privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper que controla quién puede asignar roles: solo el Administrador Global puede crear o promover personal (STAFF, LOCAL_ADMIN); un admin local solo puede trabajar con el rol base USER (clientes). Cualquier intento contrario responde 403.'
            ),
            "list_users": (
                '💡 LA IDEA: Es el padrón de clientes y empleados registrados en el sistema, adaptado a lo que cada administrador tiene permiso de ver.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita la búsqueda y gestión de cuentas, filtrando automáticamente para que ningún operador vea usuarios de otras organizaciones.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /users: lista los usuarios activos. El super-admin de la organización principal ve usuarios de todas las organizaciones; el resto se limita a su organización. Los administradores locales ven los clientes (USER) más el personal de su propia sucursal. Devuelve UserBase. Guard get_local_manager.'
            ),
            "create_user_admin": (
                '💡 LA IDEA: Es el formulario de alta manual de usuarios desde el panel de control para registrar clientes o personal autorizado.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite sumar usuarios directamente en garita sin obligarlos a registrarse ellos mismos desde la aplicación móvil.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /users: crea un usuario nuevo desde el panel. Los locales no pueden crear Administrador Global (403) y se les fuerza la sucursal a la suya; validate_staff_role_assignment controla que solo el global cree personal. Delega en UserService.create_user con la organización del admin. Guard get_local_manager y rate limit.'
            ),
            "invite_admin_user": (
                '💡 LA IDEA: Es la carta de invitación formal por correo electrónico para incorporar a un nuevo administrador a la plataforma.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un ingreso seguro: la persona recibe un enlace temporal para crear su propia contraseña sin que nadie conozca su clave secreta.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /users/invite: invita a un nuevo administrador general. Solo para super-admin (get_super_admin). UserService.invite_admin crea la cuenta sin clave usable, se genera un token de activación con caducidad y se envía un correo con el enlace /reset-password?token=... para que la persona defina su contraseña. Devuelve confirmación del envío.'
            ),
            "update_user_admin": (
                '💡 LA IDEA: Es la ficha de edición de datos de una persona (nombre, teléfono, rol o sucursal) desde el panel administrativo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite corregir datos de clientes o actualizar la sede de trabajo de un empleado de manera controlada.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint PATCH /users/{user_id}: actualiza datos de un usuario desde el panel. Valora 404 si no existe, aplica validate_local_admin_user_permission y, si se cambia el rol o la sucursal, las validaciones de staff y jurisdicción (los locales no pueden asignar ADMIN ni mover usuarios fuera de su sede). Si el usuario es cliente, notifica el cambio de perfil vía UserNotificationService. Delega en UserService.update_user. Guard get_local_manager y rate limit.'
            ),
            "change_user_role": (
                '💡 LA IDEA: Es el acta de ascenso o cambio de puesto de un miembro del equipo (por ejemplo, de cliente a empleado de garita).\n\n'
                '🎯 POR QUE FUE GENERADA: Permite modificar los niveles de acceso de un usuario verificando rigurosamente que el solicitante tenga permisos para otorgar dicho rol.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /users/{user_id}/role: cambia el rol de un usuario. Valora existencia (404), jurisdicción (validate_local_admin_user_permission), que el admin pueda asignar el rol nuevo (validate_staff_role_assignment) y que los locales no asignen ADMIN (403). Si el rol resultante es USER notifica al cliente. Límite 30/min y guard get_local_manager.'
            ),
            "toggle_user_block": (
                '💡 LA IDEA: Es el derecho de admisión digital: bloquea temporalmente el acceso a un usuario para que no pueda ingresar ni reservar en el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite frenar cuentas sospechosas, morosas o infractoras sin borrar su historial ni sus registros de estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /users/{user_id}/toggle-block: alterna el bloqueo de una cuenta (is_blocked). Valora 404, jurisdicción y que el admin no se bloquee a sí mismo (400). Si el usuario es cliente, le notifica el cambio de estado. Devuelve el nuevo estado y un mensaje. Límite 30/min y guard get_local_manager.'
            ),
            "adjust_user_balance": (
                '💡 LA IDEA: Es la acreditación o corrección manual de saldo en la billetera virtual de un cliente desde la garita.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite cargar saldo a conductores que pagan en efectivo en caja o compensar saldos por fallas del servicio.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /users/{user_id}/balance: ajusta (asigna) el saldo de un usuario a un monto indicado. Valora 404, jurisdicción y que el monto no sea negativo (400). Si es cliente, notifica el ajuste de saldo. Límite 30/min y guard get_local_manager.'
            ),
            "change_user_password": (
                '💡 LA IDEA: Es el reseteo de emergencia de la contraseña de un usuario que no puede acceder a su correo para recuperarla por su cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al administrador resolver trabas de acceso inmediatas en el mostrador asegurando un nuevo cifrado seguro de la contraseña.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /users/{user_id}/password: permite al admin cambiar la contraseña de un usuario (reset administrativo) hasheando la nueva con get_password_hash. Valora 404 y jurisdicción; si el usuario es cliente, le notifica que su contraseña fue cambiada. Límite 30/min y guard get_local_manager.'
            ),
            "delete_user": (
                '💡 LA IDEA: Es la baja definitiva de una cuenta de usuario del sistema cuando ya no utilizará el servicio.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite cumplir con solicitudes de baja o limpiar registros de prueba respetando las reglas de seguridad y jurisdicción.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint DELETE /users/{user_id} (también expuesto como POST /users/{user_id}/delete): elimina la cuenta de un usuario. Valora que no sea la propia cuenta del admin (404/400), 404 si no existe y jurisdicción con validate_local_admin_user_permission. Delega el borrado en UserService.delete_user. Límite 30/min y guard get_local_manager.'
            ),
        },
    },
    "routes/admin/virtual_time.py": {
        "proposito": 'Control del reloj virtual del sistema (solo entorno de pruebas escolar): permite adelantar, retroceder, fijar o reiniciar la hora virtual para poder probar flujos que dependen del tiempo (reservas, recordatorios, cobros por estadía). Tras cada ajuste ejecuta de inmediato todos los workers (recordatorios, inicio automático de reservas, auto-cancelaciones, limpieza y auto-finalización) contra la nueva hora.',
        "simbolos": {
            "TimeAdjustmentRequest": (
                '💡 LA IDEA: Es el paquete de datos que define cuántos días, horas o minutos se quiere hacer saltar el reloj del sistema hacia adelante o atrás.\n\n'
                '🎯 POR QUE FUE GENERADA: Estandariza las solicitudes de desplazamiento temporal para probar funciones del sistema sin tener que esperar días en la vida real.\n\n'
                '⚙️ FUNCIONAMIENTO: Modelo Pydantic del cuerpo de los endpoints de ajuste incremental: recibe cantidad de días, horas y minutos a sumar (avanzar) o restar (retroceder); todos con valor por defecto 0.'
            ),
            "SetOffsetRequest": (
                '💡 LA IDEA: Es el paquete de datos que especifica una diferencia exacta en segundos entre la hora real del servidor y la hora virtual.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite fijar un desfase temporal constante y preciso para sincronizar pruebas automatizadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Modelo Pydantic del endpoint /set: recibe offset_seconds, la diferencia en segundos entre la hora virtual y la hora real; fija el reloj virtual a esa diferencia.'
            ),
            "SetTargetRequest": (
                '💡 LA IDEA: Es el paquete de datos que transporta una fecha y hora específicas a las que se quiere teletransportar el sistema escolar.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite viajar instantáneamente a un día u horario particular (por ejemplo, año nuevo a medianoche) para ver cómo responde el estacionamiento.\n\n'
                "⚙️ FUNCIONAMIENTO: Modelo Pydantic del endpoint /set-target: recibe target_datetime como cadena ISO (por ejemplo '2026-10-15T14:30:00') con la fecha y hora absoluta a la que se quiere fijar el reloj virtual."
            ),
            "_run_all_checks": (
                '💡 LA IDEA: Es el despertador general que, tras mover el reloj, corre inmediatamente todos los procesos automáticos de vencimientos, recordatorios y multas.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita tener que esperar a los ciclos normales de los workers de fondo, aplicando al instante los efectos de la nueva hora sobre reservas y estadías.\n\n'
                '⚙️ FUNCIONAMIENTO: Auxiliar que abre una sesión de base de datos y ejecuta en secuencia todos los workers contra la hora virtual recién ajustada: procesamiento de recordatorios, inicio de reservas, auto-cancelaciones, limpieza de reservas vencidas y auto-finalización de estadías. Captura y loguea cualquier error sin interrumpir el endpoint.'
            ),
            "get_virtual_time": (
                '💡 LA IDEA: Es el reloj mural del panel de pruebas que indica cuál es la hora virtual actual y qué desfase tiene respecto de la hora real.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los evaluadores y profesores saber en qué momento temporal se encuentra operando el sistema escolar en todo momento.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint GET /virtual-time y /virtual-time/status: devuelve la información del reloj virtual actual (hora virtual, offset, etc.) vía TimeService.get_info. Protegido con get_operational_user (cualquier usuario del panel).'
            ),
            "advance_virtual_time": (
                '💡 LA IDEA: Es el botón de avance rápido para simular que pasaron horas o días en el estacionamiento en un abrir y cerrar de ojos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite verificar si se cobran estadías prolongadas, si se vencen reservas impagas o si se envían recordatorios sin esperar tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /virtual-time/advance: adelanta el reloj virtual por la cantidad de días/horas/minutos enviada (TimeService.advance), ejecuta todos los workers de inmediato y devuelve el estado del reloj. Guard get_operational_user y rate limit admin.'
            ),
            "rewind_virtual_time": (
                '💡 LA IDEA: Es el botón de rebobinar para regresar el reloj virtual hacia el pasado y reintentar pruebas.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita repetir escenarios de prueba o corregir simulaciones sin tener que reiniciar toda la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /virtual-time/rewind: retrocede el reloj virtual (TimeService.rewind) con el mismo flujo que advance: ajusta, corre los workers y devuelve la info del reloj. Guard get_operational_user y rate limit.'
            ),
            "set_target_virtual_time": (
                '💡 LA IDEA: Es la máquina del tiempo que fija una fecha y hora exactas en el sistema educativo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite posicionar el sistema en un momento clave de una demostración con un solo clic.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /virtual-time/set-target: fija el reloj virtual a una fecha y hora absolutas. Valida que target_datetime sea ISO válido (400 si no), llama a TimeService.set_target_datetime, ejecuta los workers y devuelve el estado. Guard get_operational_user y rate limit.'
            ),
            "set_virtual_time": (
                '💡 LA IDEA: Es el calibrador fino del desfase temporal en segundos para ajustar el reloj de pruebas con precisión milimétrica.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee una vía directa para que scripts de testing o paneles avanzados sincronicen el tiempo virtual.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /virtual-time/set: fija el reloj virtual a un desplazamiento en segundos respecto de la hora real (TimeService.set_offset), corre los workers y devuelve la información del reloj. Guard get_operational_user y rate limit.'
            ),
            "reset_virtual_time": (
                '💡 LA IDEA: Es el botón de retorno a la realidad que devuelve el reloj virtual a la hora y fecha reales del servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite concluir las sesiones de simulación y restablecer la sincronización con el tiempo presente.\n\n'
                '⚙️ FUNCIONAMIENTO: Endpoint POST /virtual-time/reset: reinicia el reloj virtual a cero (sin desfase con la hora real) con TimeService.reset, ejecuta todos los workers y devuelve el estado. Guard get_operational_user y rate limit.'
            ),
        },
    },
}
