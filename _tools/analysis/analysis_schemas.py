"""Explicaciones analizadas de schemas (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "schemas/__init__.py": {
        "proposito": (
            "💡 LA IDEA: Es la 'aduana de formularios y contratos de datos'. Convierte a la carpeta `schemas` en el centro de validación oficial de la API, donde se definen los moldes exactos que deben respetar los datos que entran y salen del servidor (Pydantic).\n\n"
            "🎯 POR QUE FUE GENERADA: En una API web moderna, no podés permitir que un usuario mande un número de tarjeta en el campo del nombre o una fecha en formato texto roto. Este archivo unifica el paquete para que cualquier ruta pueda importar esquemas de validación como `schemas.user` o `schemas.reservation`.\n\n"
            "⚙️ FUNCIONAMIENTO: Declara formalmente al directorio `schemas/` como paquete importable en Python, habilitando el acceso directo a todos los esquemas Pydantic que validan tipos de datos, correos, patentes y montos antes de que lleguen a la base de datos."
        ),
        "simbolos": {
        },
    },
    "schemas/auth.py": {
        "proposito": 'Esquemas Pydantic que modelan el cuerpo de las peticiones de autenticación y recuperación de contraseña en los endpoints de `routes/auth.py`. Validan que el DNI, el teléfono y el correo lleguen limpios y bien formados, y que la nueva contraseña cumpla la política de seguridad antes de que el servicio actúe.',
        "simbolos": {
            "OAuthComplete": (
                '💡 LA IDEA: Es el formulario complementario de ventanilla: cuando un usuario inicia sesión con Google o Microsoft por primera vez, el sistema ya tiene su email, pero necesita que complete su DNI y teléfono para terminar su ficha.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el registro con Google o Microsoft sea ágil sin dejar la cuenta incompleta de datos obligatorios para el estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo de la petición que completa un registro o login vía OAuth (Google/Facebook). Espera el `code` devuelto por el proveedor junto con el `dni` y el `telefono` del usuario que se está registrando en el paso manual; el DNI se normaliza a solo dígitos (7 u 8) y el teléfono se limpia a dígitos (10 a 13) antes de pasar al servicio.'
            ),
            "validate_dni": (
                '💡 LA IDEA: Es el detector de errores de DNI en el formulario web: exige que tenga 7 u 8 números y barre con cualquier punto o letra.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que se guarden números de documento inválidos en el inicio de sesión OAuth.\n\n'
                '⚙️ FUNCIONAMIENTO: Validador de campo que delega en `validate_dni_digits`: quita todo lo que no sea dígito y exige un DNI argentino de 7 u 8 dígitos, devolviendo el valor limpio. Se aplica al campo `dni` del esquema que lo declara.'
            ),
            "validate_telefono": (
                '💡 LA IDEA: Es el filtro de números de contacto: limpia guiones y paréntesis y comprueba que tenga entre 10 y 13 dígitos.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el número de teléfono sea apto para recibir alertas por WhatsApp o SMS.\n\n'
                '⚙️ FUNCIONAMIENTO: Validador de campo que delega en `validate_phone_digits`: deja solo dígitos y exige entre 10 y 13 (puede incluir el prefijo de país). Devuelve el teléfono normalizado para que se guarde sin espacios ni símbolos.'
            ),
            "ForgotPasswordRequest": (
                '💡 LA IDEA: Es el sobre cerrado del pedido de auxilio: solo contiene el correo del usuario que olvidó su clave.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el endpoint de recuperación reciba datos innecesarios, procesando únicamente el correo de destino.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo del endpoint público 'olvidé mi contraseña'. Lleva únicamente el `email` del usuario; el validador exige un formato correcto (una sola arroba, usuario, dominio y TLD, sin espacios) antes de que el servicio genere el token de recuperación."
            ),
            "validate_email": (
                '💡 LA IDEA: Es el cartero que revisa la dirección en el sobre: comprueba que tenga una sola arroba, dominio válido y sin espacios.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el servidor gaste recursos intentando enviar correos a direcciones inexistentes o mal tipeadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Validador de campo que delega en `validate_email_format`: recorta espacios y exige con regex un correo bien formado (patrón de una sola arroba, sin espacios, usuario, dominio y punto), lanzando ValueError con mensaje claro si no cumple. Devuelve el correo limpio.'
            ),
            "ResetPasswordRequest": (
                '💡 LA IDEA: Es la llave combinada para cambiar la cerradura: trae el pase temporal que llegó al email y la nueva contraseña elegida.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el usuario redefina su clave de manera segura sin exponer la sesión completa.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo del endpoint de restablecimiento de contraseña: recibe el `token` de un solo uso enviado por correo y la `new_password`. La contraseña nueva pasa por `validate_password_strength` (mínimo 8 caracteres, una mayúscula y un carácter especial) antes de que el servicio la reemplace.'
            ),
            "validate_password": (
                '💡 LA IDEA: Es el guardia que evalúa la dureza de la nueva clave elegida.\n\n'
                '🎯 POR QUE FUE GENERADA: Exige que la contraseña tenga mayúsculas, números y símbolos para que no sea fácil de vulnerar.\n\n'
                '⚙️ FUNCIONAMIENTO: Validador de campo sobre `new_password` que delega en `validate_password_strength`, aplicando la política completa de contraseñas al restablecer la cuenta desde el enlace del correo.'
            ),
        },
    },
    "schemas/mercadopago.py": {
        "proposito": 'Esquemas del checkout con Mercado Pago (Checkout Pro) que usa el endpoint de `routes/user/mercadopago.py`. Modelan la solicitud de creación de una preferencia de pago y la respuesta con el enlace de pago y los datos de referencia que el front necesita para redirigir al usuario.',
        "simbolos": {
            "MercadoPagoCheckout": (
                '💡 LA IDEA: Es el ticket de compra digital que se le manda a Mercado Pago: dice qué se está pagando (una reserva o una estadía ya consumida) y a qué auto corresponde.\n\n'
                '🎯 POR QUE FUE GENERADA: Estandariza la solicitud de cobro para que el backend arme el botón de pago con el importe exacto.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo de la solicitud de checkout. El campo `tipo` restringe el motivo del cobro a 'reserva' o 'estadia' (con default 'reserva') y según el tipo se acompaña de `reserva_id` (reserva existente), `access_log_id` (estadía en curso en el predio) o `redemption_ticket_id` (canje de ticket de descuento %, solo aplicable a reservas). Sin validadores adicionales: el servicio resuelve el monto a cobrar."
            ),
            "MercadoPagoCheckoutResponse": (
                '💡 LA IDEA: Es el pasaje al portal de pagos: devuelve el link (`init_point`) al que el navegador debe redirigir al usuario para que ponga su tarjeta.\n\n'
                '🎯 POR QUE FUE GENERADA: Entrega al frontend la URL oficial de Mercado Pago para abrir la pasarela de pagos segura.\n\n'
                '⚙️ FUNCIONAMIENTO: Respuesta del backend al crear la preferencia: `init_point` es la URL de pago de Mercado Pago, `external_reference` el identificador que MP devuelve en el webhook, `monto` el importe cobrado y `preference_id` el ID de la preferencia en MP. El front usa `init_point` para redirigir al usuario a la pantalla de pago.'
            ),
        },
    },
    "schemas/notification.py": {
        "proposito": 'Esquemas de salida del módulo de notificaciones del usuario (`routes/user/notifications.py`). Definen cómo se serializan las notificaciones almacenadas, la lista pagada con totales y el conteo de no leídas que usa el frontend para el ícono de campana.',
        "simbolos": {
            "NotificationResponse": (
                '💡 LA IDEA: Es la tarjetita que aparece en el centro de avisos: título, mensaje, fecha y si ya fue leída.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona al frontend la información exacta de cada aviso sin exponer datos internos de la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Representación de una notificación individual con `from_attributes=True` (se construye directamente desde el modelo ORM). Expone id, usuario dueño, tipo, título, mensaje, estado `leido`, y las referencias opcionales a `reserva_id` o `ticket_id` para que el front pueda navegar al detalle relacionado, más la fecha de creación.'
            ),
            "NotificationListResponse": (
                '💡 LA IDEA: Es la bandeja de entrada completa: agrupa la lista de notificaciones junto con el contador de cuántas quedan sin leer.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el celular o la computadora cargue la lista y el número de la campanita en un solo viaje de red.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrupación que devuelve el listado de notificaciones del usuario: la lista de `NotificationResponse`, el `total` de filas y el `unread` (cantidad de no leídas) en un solo payload, para que el panel cargue datos y contador de una sola llamada.'
            ),
            "UnreadCountResponse": (
                '💡 LA IDEA: Es el globito rojo sobre la campana: un simple número que dice cuántos avisos nuevos hay.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite actualizar el globito de notificaciones de forma ultra liviana cada pocos segundos sin recargar todos los textos.\n\n'
                '⚙️ FUNCIONAMIENTO: Payload mínimo del endpoint de conteo de no leídas: un único entero `count`. Lo consume el front para refrescar el badge de la campana sin descargar el listado completo.'
            ),
        },
    },
    "schemas/parking.py": {
        "proposito": 'Esquemas del dominio del estacionamiento: altas de vehículos, validaciones de acceso por patente o QR, estado de ocupación del predio, configuración de plantas y sucursales, y catálogo de cámaras. Se usan tanto en los endpoints de usuario (`routes/parking/*`, `routes/user/vehicles.py`) como en los de administración (`routes/admin/branches.py`, `routes/system/cameras.py`).',
        "simbolos": {
            "VehicleCreate": (
                '💡 LA IDEA: Es el formulario de alta de un auto en la cochera: patente, modelo y si es auto, moto o camioneta.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita registrar patentes en blanco o tipos de vehículo desconocidos que descalibren las tarifas.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo de alta de un vehículo del usuario en `routes/user/vehicles.py`: patente, marca/modelo y `tipo` restringido por Literal a 'Auto', 'Moto' o 'Camioneta' (default 'Auto'). El tipo determina después qué cupo y tarifa se aplican en la reserva."
            ),
            "PlateValidation": (
                '💡 LA IDEA: Es la foto y lectura que la cámara de la barrera le envía al servidor: patente, barrera y tiempo de lectura.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el backend evalúe si la barrera debe levantarse para dejar pasar al auto.\n\n'
                '⚙️ FUNCIONAMIENTO: Payload de validación de acceso por patente, usado por `routes/parking/access.py` y `services/access_service.py`. Lleva la `plate` leída, el `gate_id` de la barrera, y opcionalmente la `image_base64` de la foto del ALPR y su `ocr_time` (segundos que tardó el OCR) para trazabilidad. El servicio decide si abre, rechaza o pide QR.'
            ),
            "QRValidation": (
                '💡 LA IDEA: Es el paquete de datos del escaneo de un pase digital en el lector de la barrera.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite el ingreso o egreso cuando la patente está sucia o cuando el cliente reservó con QR.\n\n'
                '⚙️ FUNCIONAMIENTO: Payload de validación de acceso por código QR: solo `qr_data` (contenido escaneado) y `gate_id`. Se consume en el mismo endpoint de acceso junto con PlateValidation para el flujo de salida o de usuarios sin cámara de patente.'
            ),
            "AccessResponse": (
                '💡 LA IDEA: Es la orden de respuesta que vuelve a la barrera: autorizar o denegar, mensaje para la pantalla y orden de apertura.\n\n'
                '🎯 POR QUE FUE GENERADA: Le indica al hardware de la barrera y a la pantalla del tótem qué mensaje mostrarle al conductor.\n\n'
                "⚙️ FUNCIONAMIENTO: Respuesta estándar del endpoint de acceso: `status` (allow/deny u análogo), `action` opcional (por ejemplo 'abrir_barrera') y un `message` legible para el operador o el usuario en la barrera."
            ),
            "ParkingStatus": (
                '💡 LA IDEA: Es el tablero de control de ocupación: muestra cuántas cocheras libres quedan para autos, motos y camionetas.\n\n'
                '🎯 POR QUE FUE GENERADA: Alimenta las pantallas gigantes de la entrada y el mapa web con la disponibilidad en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Snapshot de ocupación del predio para la página de estado: totales y ocupación de autos, motos y camionetas, más los cupos reservados por tipo (autos/motos/camionetas y total) y las disponibilidades resultantes. Los defaults de capacidad (por ejemplo 5 autos reservados, 3 motos, 2 camionetas, 10 total) son los valores de fallback del sistema.'
            ),
            "FloorBase": (
                '💡 LA IDEA: Es el molde base para describir un piso del estacionamiento con sus capacidades.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita repetir la lista de tipos de vehículo en cada esquema de pisos.\n\n'
                '⚙️ FUNCIONAMIENTO: Campos comunes de una planta del edificio: nombre y capacidades por tipo de vehículo y por tipo de reserva (autos, motos, camionetas y total). Es la base que reutilizan FloorCreate y FloorResponse para no duplicar la lista de capacidades.'
            ),
            "FloorCreate": (
                '💡 LA IDEA: Es el formulario para agregar un piso nuevo a una sucursal desde el panel de administración.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida que cada nuevo piso tenga definidos sus límites de autos, motos y camionetas.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo de alta de planta en el panel de administración de sucursales (`routes/admin/branches.py`): hereda exactamente FloorBase sin agregar campos, es decir, nombre y capacidades por tipo.'
            ),
            "FloorResponse": (
                '💡 LA IDEA: Es la ficha completa de un piso con su ocupación actual en vivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra a los operadores cuántos autos hay en cada piso en cualquier momento.\n\n'
                '⚙️ FUNCIONAMIENTO: Salida de una planta hacia el front: agrega a FloorBase el `id`, la `branch_id` dueña y las ocupaciones actuales por tipo (autos, motos, camionetas y reservas), con `from_attributes=True` para serializar el modelo ORM directamente.'
            ),
            "BranchBase": (
                '💡 LA IDEA: Es la tarjeta de presentación de una sucursal: dirección, teléfono, horarios y coordenadas de mapa.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la información física indispensable para mostrar las playas en la web.\n\n'
                '⚙️ FUNCIONAMIENTO: Campos comunes de una sucursal: nombre, dirección, teléfono, horario, indicador `is_24h`, logo opcional, estado `activa` y coordenadas `latitude`/`longitude` para el mapa. Es la base de las respuestas pública y admin.'
            ),
            "BranchResponse": (
                '💡 LA IDEA: Es el informe completo de la sucursal para el administrador: incluye pisos, aforo, recaudación y tarifario completo.\n\n'
                '🎯 POR QUE FUE GENERADA: Da al gerente de playa una visión 360° del estado de su estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Salida completa de sucursal para el panel admin (`routes/admin/branches.py`): hereda BranchBase y agrega id, nombre del admin a cargo, la lista de `floors` anidadas, todos los totales calculados de capacidad y ocupación por tipo de vehículo y reserva, y las tarifas por tipo (auto/moto/camioneta) por hora, día, semana, quincena y mes; los campos de tarifa en None significan que la sucursal no tiene tarifario configurado.'
            ),
            "BranchPublicResponse": (
                '💡 LA IDEA: Es el folleto público de la sucursal: muestra solo lo que le interesa al cliente (ubicación y si hay lugar libre), ocultando costos internos y datos del personal.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la información confidencial de la empresa mientras informa al público general.\n\n'
                '⚙️ FUNCIONAMIENTO: Versión reducida de sucursal para el público sin login: datos básicos de BranchBase más id, ocupaciones y capacidades actuales por tipo y de reserva, y las plantas anidadas; omite admin, totales y tarifas para no exponer información interna.'
            ),
            "CameraBase": (
                '💡 LA IDEA: Es la ficha técnica básica de una cámara de video del estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Estandariza la configuración de video para cualquier marca o modelo de cámara.\n\n'
                "⚙️ FUNCIONAMIENTO: Campos comunes de una cámara del sistema: nombre, `tipo` (cadena libre con valores conocidos 'ENTRADA', 'SALIDA', 'PREDIO', 'PATENTE', 'QR'), `source` (URL o path del stream), estado `activa` y etiqueta opcional `sucursal`."
            ),
            "CameraCreate": (
                '💡 LA IDEA: Es el formulario para dar de alta una cámara nueva en el centro de monitoreo.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida que la cámara tenga una dirección IP o de dispositivo válida antes de guardarla.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo de alta de cámara en `routes/system/cameras.py`: hereda CameraBase sin agregar nada, es decir, nombre, tipo, source, activa y sucursal.'
            ),
            "CameraResponse": (
                '💡 LA IDEA: Es el estado en vivo de una cámara para el monitor de seguridad: indica si está transmitiendo y su número de orden en la grilla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el panel de monitoreo dibuje las pantallas activas y avise si una cámara se desconectó.\n\n'
                '⚙️ FUNCIONAMIENTO: Salida de una cámara hacia el front: agrega el `id`, el `orden` opcional de visualización y el flag `is_running` que indica si el stream está activo en este momento.'
            ),
            "CameraOrderUpdate": (
                '💡 LA IDEA: Es la nueva lista ordenada de cámaras cuando el guardia las arrastra y suelta en la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite guardar el orden personalizado de las cámaras en el monitor sin recargar la página.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo del endpoint de reordenamiento de cámaras: recibe solo `ids`, la lista de ids en el nuevo orden de prioridad que el panel desea mostrar.'
            ),
        },
    },
    "schemas/reservation.py": {
        "proposito": "Esquemas del flujo de reservas: cotización de precio, alta por usuario y por admin, edición parcial, confirmación de pago y la respuesta completa hacia el front. Centralizan la 'foto histórica' de tarifas que el backend revalida y persiste para trazar el precio cotizado.",
        "simbolos": {
            "PriceQuoteInput": (
                '💡 LA IDEA: Es el presupuesto provisional calculado por el navegador del cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el servidor compare el precio cotizado en pantalla contra las tarifas oficiales y detecte si el precio fue alterado.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase base con la cotización que el front calculó al crear o editar la reserva: `tarifa_hora`, `tarifa_fraccion`, `tarifa_aplicada`, `horas_calculadas` y `monto_calculado`. El backend no confía en estos valores: el ReservationService los revalida contra su propio cálculo y los persiste como foto histórica del precio. Todos son opcionales por compatibilidad con clientes viejos.'
            ),
            "UserReservationCreate": (
                '💡 LA IDEA: Es la solicitud de reserva que llena el conductor desde su celular.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que la reserva traiga patente, fechas y sucursal bien definidas antes de bloquear una cochera.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo de alta de reserva desde el usuario (`routes/user/reservations.py`): patente, `fecha_inicio` y `fecha_fin` como strings, sucursal (default 'AUTOPASS Central'), tipo de estadía (default 'hora') y `dias_semana` opcional para estadías semanales; hereda la cotización de PriceQuoteInput."
            ),
            "AdminReservationCreate": (
                '💡 LA IDEA: Es la reserva manual que carga el empleado en la cabina para un auto que llegó sin reserva o por teléfono.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al personal registrar clientes presenciales, aplicar pagos en efectivo o bonificaciones especiales.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo de alta de reserva desde el panel admin (`routes/admin/reservations.py`): además de los campos de usuario, permite indicar el `user_id` o un `cliente_nombre` walk-in, `metodo_pago` y el flag `pagar` para cobrar de una, `tipo_vehiculo`, `redemption_ticket_id` para aplicar descuento por canje, y los métodos para cobrar o reembolsar diferencias (`cobrar_diferencia_metodo`, `reembolsar_diferencia_metodo`). La sucursal por defecto es 'AUTOPASS Ituzaingó'."
            ),
            "ReservationUpdate": (
                '💡 LA IDEA: Es la solicitud para cambiar de horario, cambiar de auto o extender la reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite modificar una reserva sin tener que cancelarla y crear una nueva desde cero.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo de edición parcial de una reserva (usuario o admin): todos los campos opcionales (fechas, patente, tipo de estadía, sucursal, estados de pago y reserva, método de pago y tipo de vehículo) más la cotización de PriceQuoteInput; lo que no se envía queda sin tocar.'
            ),
            "ConfirmPaymentRequest": (
                '💡 LA IDEA: Es el comprobante de caja que confirma que el cliente pagó su estadía en el mostrador.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el empleado marque como pagada una reserva en efectivo y aplique cupones de descuento.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo del endpoint de confirmación de pago de una reserva existente: `metodo_pago` con default 'Caja' (pago en efectivo en el local) y `redemption_ticket_id` opcional para marcar el canje de un ticket de descuento aplicado a esa reserva."
            ),
            "UserReservationResponse": (
                '💡 LA IDEA: Es el voucher digital completo de la reserva: incluye horarios, QR de acceso, total pagado y estado del auto.\n\n'
                '🎯 POR QUE FUE GENERADA: Es el documento digital que el cliente consulta en su teléfono para entrar y salir del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Salida completa de una reserva hacia el front (usuario y admin): identificadores, patente, fechas, tipo de estadía y días de semana, estados de pago y reserva, montos totales y reembolsados, datos de la sucursal y del usuario dueño, si está `en_predio`, el `origen` (cliente o admin) y el bloque de foto histórica de tarifas (tarifas, horas, monto cotizado, descuento porcentual y marca de cuándo se fijó el precio).'
            ),
        },
    },
    "schemas/support.py": {
        "proposito": 'Esquemas del sistema de tickets de soporte: el usuario abre un ticket desde `routes/user/support.py` y el admin lo actualiza desde `routes/admin/support.py`. Modelan el alta con categoría y mensaje, y la respuesta del operador.',
        "simbolos": {
            "SupportTicketCreate": (
                '💡 LA IDEA: Es el formulario de reclamo o consulta que escribe el cliente cuando tuvo un problema con un cobro o una barrera.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite canalizar las quejas de los usuarios de manera ordenada y tipificada por sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo de apertura de ticket por parte del usuario: `categoria` (tipo de consulta), `sucursal` con default 'General', `asunto` y `mensaje`. El servicio lo persiste en estado pendiente y notifica a los administradores."
            ),
            "SupportTicketUpdate": (
                '💡 LA IDEA: Es la contestación oficial del equipo de atención al cliente junto con el cambio de estado del reclamo (Resuelto o Cerrado).\n\n'
                '🎯 POR QUE FUE GENERADA: Notifica al cliente la solución a su problema y deja asentada la respuesta en el historial.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo de actualización desde el panel admin: obliga el nuevo `estado` del ticket (por ejemplo 'Respondido' o 'Cerrado') y permite adjuntar una `respuesta` opcional que se notifica al usuario dueño."
            ),
        },
    },
    "schemas/user.py": {
        "proposito": 'Esquemas Pydantic del ciclo de vida del usuario: registro, login, edición de perfil y por admin, invitación, cambio de contraseña, recarga de saldo, y el catálogo de promociones de fidelización con sus tickets de canje. Aplican en los endpoints de `routes/auth.py`, `routes/user/*` y `routes/admin/users.py` / `promotions.py` la política de validación de DNI, teléfono, email y contraseña.',
        "simbolos": {
            "UserBase": (
                '💡 LA IDEA: Es el molde con los datos personales compartidos de cualquier usuario del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita duplicar las validaciones de nombre, email, teléfono y DNI en múltiples pantallas.\n\n'
                "⚙️ FUNCIONAMIENTO: Campos comunes de un usuario con `from_attributes=True` (se serializa desde el modelo ORM): identidad (nombre, apellido, DNI, teléfono, email), rol (default 'user'), sucursal, dirección, puntos acumulados, saldo y flag `is_blocked`. Valida teléfono y email con los validadores compartidos de `schemas.validators`."
            ),
            "validate_telefono": (
                '💡 LA IDEA: Es el filtro de limpieza telefónica en los datos del usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura números de teléfono limpios y listos para comunicaciones automáticas.\n\n'
                '⚙️ FUNCIONAMIENTO: Validador de campo que delega en `validate_phone_digits`: deja solo dígitos y exige entre 10 y 13, devolviendo el valor normalizado. Se aplica al campo `telefono` de UserBase, UserUpdate, UserAdminUpdate y UserInvite.'
            ),
            "validate_email": (
                '💡 LA IDEA: Es el filtro de formato de correo electrónico para usuarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide registros con correos inválidos que no puedan recibir confirmaciones.\n\n'
                '⚙️ FUNCIONAMIENTO: Validador de campo que delega en `validate_email_format`: recorta espacios y exige con regex un correo bien formado (una sola arroba, usuario, dominio y TLD). Se aplica al campo `email` de UserBase, UserUpdate, UserAdminUpdate y UserLogin.'
            ),
            "UserUpdate": (
                '💡 LA IDEA: Es el formulario donde el cliente actualiza su teléfono, dirección o apellido desde su perfil.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario editar sus datos de contacto sin darle permiso de modificar su rol, saldo o bloqueo.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo de edición del propio perfil (`routes/user/profile.py`): solo nombre, apellido, teléfono, email y dirección, todos opcionales; valida teléfono y email igual que UserBase. No permite tocar rol, saldo ni bloqueo.'
            ),
            "UserAdminUpdate": (
                '💡 LA IDEA: Es el formulario del panel de control donde el administrador gestiona la cuenta de un empleado o cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite cambiar roles, sucursales asignadas y datos personales con privilegios de gestión.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo de edición de un usuario por parte del admin (`routes/admin/users.py`, con UserAdminUpdate en services/user_service.py): además de identidad y sucursal permite cambiar el `rol`; valida DNI (7 u 8 dígitos), teléfono y email.'
            ),
            "validate_dni": (
                '💡 LA IDEA: Es el verificador de DNI en las altas y modificaciones de usuarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que cada persona registrada tenga un número de documento válido y sin símbolos.\n\n'
                '⚙️ FUNCIONAMIENTO: Validador de campo que delega en `validate_dni_digits`: quita todo lo no numérico y exige un DNI argentino de 7 u 8 dígitos, devolviendo el valor limpio. Se aplica al campo `dni` de UserAdminUpdate, UserCreate y UserInvite.'
            ),
            "UserCreate": (
                '💡 LA IDEA: Es el formulario de registro de un nuevo usuario con su contraseña inicial.\n\n'
                '🎯 POR QUE FUE GENERADA: Exige que el registro cumpla con todos los requisitos de seguridad antes de crear la cuenta.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo de registro de usuario (`routes/auth.py` y alta desde admin): hereda todos los campos de UserBase y agrega el `password`, que debe cumplir la política de fortaleza (mínimo 8 caracteres, una mayúscula y un carácter especial).'
            ),
            "validate_password": (
                '💡 LA IDEA: Es el validador de seguridad de contraseñas al crear una cuenta.\n\n'
                "🎯 POR QUE FUE GENERADA: Impide que los usuarios elijan contraseñas débiles como '123456' que comprometan su cuenta.\n\n"
                '⚙️ FUNCIONAMIENTO: Validador de campo sobre `password` de UserCreate que delega en `validate_password_strength`, asegurando la política de contraseñas en el registro.'
            ),
            "UserInvite": (
                '💡 LA IDEA: Es la invitación que se le manda a un empleado nuevo para que se sume al sistema y elija su propia clave por email.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite incorporar personal al estacionamiento de manera segura sin que el administrador conozca su clave personal.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo de alta de un usuario invitado sin contraseña: la define el propio destinatario desde el enlace de correo. Recoge identidad, DNI, teléfono y email (con los tres validadores) y un campo opcional `organizacion`; al ser Admin General da de alta su propia organización (multiempresa).'
            ),
            "ChangePassword": (
                '💡 LA IDEA: Es el formulario de cambio voluntario de clave: exige escribir la clave vieja para demostrar identidad antes de poner la nueva.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que alguien que encuentre una sesión abierta en una computadora ajena cambie la clave del titular.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo del cambio de contraseña desde el perfil (`routes/user/profile.py`): exige la `current_password` actual y la `new_password`, validando la fortaleza de la nueva antes de que el servicio verifique la actual y la reemplace.'
            ),
            "validate_new_password": (
                '💡 LA IDEA: Es el validador de robustez de la nueva clave elegida.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que la nueva contraseña sea tan segura como la política de la empresa lo exige.\n\n'
                '⚙️ FUNCIONAMIENTO: Validador de campo que delega en `validate_password_strength` sobre `new_password`. Se usa en ChangePassword y en UserPasswordChange (reseteo por admin).'
            ),
            "UserLogin": (
                '💡 LA IDEA: Es el formulario de inicio de sesión: correo, contraseña y el identificador del dispositivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona las credenciales necesarias para autenticar al usuario y auditar desde qué celular ingresa.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo del login (`routes/auth.py`): `email` (validado con el formato compartido), `password` y un `device_id` opcional para identificar el dispositivo en la sesión o en bloqueos multi-dispositivo.'
            ),
            "RechargeBalance": (
                '💡 LA IDEA: Es el cupón de carga de dinero a la billetera digital del estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite validar el monto que el usuario desea acreditar antes de abrir la pasarela de pagos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo de recarga de saldo de un usuario (`routes/user/balance.py`): un único `monto` float, sin validadores en el esquema; la lógica de mínimo/máximo y de imputación al saldo vive en el servicio.'
            ),
            "UserPasswordChange": (
                '💡 LA IDEA: Es el restablecimiento administrativo de contraseña cuando un empleado o cliente perdió el acceso.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al administrador desbloquear a un usuario asignándole una nueva clave temporal segura.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo del reseteo de contraseña hecho por un admin sobre otra cuenta (`routes/admin/users.py`): solo `new_password`, validada con la política de fortaleza. No pide la contraseña actual porque la realiza un administrador.'
            ),
            "PromotionCreate": (
                "💡 LA IDEA: Es el formulario para publicar una recompensa nueva (ej: '50% de descuento por 200 puntos').\n\n"
                '🎯 POR QUE FUE GENERADA: Valida que la promoción tenga costo en puntos positivo, porcentaje coherente y ubicación clara.\n\n'
                "⚙️ FUNCIONAMIENTO: Cuerpo de alta de una promoción de fidelización en `routes/admin/promotions.py`: título, descripción, `costo_puntos` obligatorio mayor a cero (Field gt=0), icono y categoría con defaults, sucursal opcional, `tipo_canje` ('voucher' o 'descuento_reserva'), y para descuento el porcentaje `valor_descuento` acotado entre 1 y 100; agrega además dirección y coordenadas para ubicar el canje en el mapa."
            ),
            "PromotionResponse": (
                '💡 LA IDEA: Es la ficha de la promoción en el catálogo de beneficios que el usuario ve en la app.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra los beneficios vigentes con sus íconos y requisitos de puntos de forma atractiva.\n\n'
                '⚙️ FUNCIONAMIENTO: Salida de una promoción hacia el panel admin y hacia el catálogo de `routes/user/fidelization.py`: todos los campos de alta más el `id` y el estado `activa`, con `from_attributes=True` para serializar el ORM.'
            ),
            "RedemptionTicketResponse": (
                '💡 LA IDEA: Es el comprobante digital del cupón canjeado con su código QR y fecha de expiración.\n\n'
                '🎯 POR QUE FUE GENERADA: Da al cliente el comprobante visual que debe presentar para gozar de su descuento.\n\n'
                "⚙️ FUNCIONAMIENTO: Salida de un ticket de canje generado al canjear puntos: id, usuario, promoción asociada, código y QR, datos de la promoción (título, tipo, valor, sucursal, dirección y coordenadas), estado ('VIGENTE', usado, etc.), fechas de creación, vencimiento y uso, y la `reserva_id` si el ticket se aplicó como descuento a una reserva."
            ),
        },
    },
    "schemas/validators.py": {
        "proposito": 'Funciones de validación y normalización compartidas por todos los esquemas de usuarios y autenticación (user.py y auth.py). Aíslan en un solo lugar las reglas de DNI argentino, teléfono, correo y fortaleza de contraseña, para que cada esquema solo las delegue y el criterio sea único en el sistema.',
        "simbolos": {
            "validate_password_strength": (
                '💡 LA IDEA: Es la balanza de seguridad de contraseñas: exige al menos 8 letras, una mayúscula y un símbolo especial (como !, @ o #).\n\n'
                '🎯 POR QUE FUE GENERADA: Protege a todo el sistema contra ataques automáticos de fuerza bruta que intentan adivinar claves simples.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica la política de contraseñas: mínimo 8 caracteres, al menos una mayúscula (regex [A-Z]) y al menos un carácter especial de la lista [!@#$%^&*(),.?":{}|<>]. Ante el primer incumplimiento lanza ValueError con el mensaje correspondiente; si pasa todo devuelve la contraseña sin modificar.'
            ),
            "validate_dni_digits": (
                '💡 LA IDEA: Es el limpiador y calibrador de documentos: elimina puntos y espacios y exige exactamente 7 u 8 números.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que los DNIs argentinos queden uniformes en toda la base de datos para evitar duplicados.\n\n'
                '⚙️ FUNCIONAMIENTO: Normaliza y valida un DNI argentino: quita todo carácter no numérico con re.sub y exige con fullmatch que queden exactamente 7 u 8 dígitos (constantes DNI_MIN_DIGITS/DNI_MAX_DIGITS). Devuelve el valor ya limpio (sin puntos ni espacios); si no cumple lanza ValueError. Permite None para no romper campos opcionales.'
            ),
            "validate_phone_digits": (
                '💡 LA IDEA: Es el formateador de teléfonos: deja solo dígitos numéricos y verifica que tenga entre 10 y 13 dígitos.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita teléfonos incompletos o con formatos extraños que impidan enviar notificaciones o mensajes de auxilio.\n\n'
                '⚙️ FUNCIONAMIENTO: Normaliza y valida un teléfono: elimina todo lo no numérico y exige un largo de 10 a 13 dígitos (constantes PHONE_MIN_DIGITS/PHONE_MAX_DIGITS), lo que cubre números argentinos y con prefijo de país. Devuelve solo los dígitos; lanza ValueError si el largo queda fuera del rango, y devuelve None si el valor original era None.'
            ),
            "validate_email_format": (
                '💡 LA IDEA: Es el verificador postal digital: comprueba que el texto tenga una estructura de email real (usuario@servidor.com).\n\n'
                '🎯 POR QUE FUE GENERADA: Frena errores de tipeo comunes antes de que el correo se registre en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Valida el formato del correo: recorta espacios y aplica con re.fullmatch el patrón [^\\s@]+@[^\\s@]+\\.[^\\s@]+ (una sola arroba, sin espacios, usuario, dominio y TLD). Si no coincide lanza ValueError con un mensaje de ejemplo; si coincide devuelve el correo recortado. Devuelve None si el valor era None.'
            ),
        },
    },
}
