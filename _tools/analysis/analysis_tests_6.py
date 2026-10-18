"""Explicaciones analizadas de tests (parte 6 de 6): análisis del código real.

Cubre: salud del sistema, bloqueo de usuarios, fidelización, servicio de usuarios,
soporte del usuario, rutas de video, streamer de video, reloj virtual, cleanup de
workers y cliente WebSocket del ALPR.
"""

ANALISIS: dict[str, dict] = {
    "tests/test_system_health.py": {
        "proposito": 'Verifica routes/system/health.py con una FastAPI mínima montada a mano: el estado de salud /health según el rol (admin global, staff por sucursal o usuario común), el endpoint de heartbeat autenticado por secreto de nodo ALPR, el reset de datos de super admin y la lectura del reloj virtual. Prepara su propia app para poder simular una base de datos caída sin tocar la app real.',
        "simbolos": {
            "FakeUser": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de usuario para el override de get_current_user: solo guarda rol y sucursal en memoria, sin consultar la BD.'
            ),
            "FakeUser.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Recibe el rol (por defecto admin) y la sucursal, y los deja como atributos del doble.'
            ),
            "_build_app": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _build_app.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Construye una FastAPI que incluye únicamente el router de health. Sobreescribe get_db (con la session_factory de pruebas, o con un db_breaker que simula la BD caída) y get_current_user para que devuelva el usuario falso de CURRENT.'
            ),
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Fixture: crea un engine SQLite en memoria con todas las tablas, siembra la sucursal 'Centro', limpia el rate limiter y el diccionario ALPR_HEARTBEATS, y entrega (TestClient, sessionmaker). Al final libera los overrides y el estado global."
            ),
            "_reset_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reset_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Autouse: después de cada test restaura CURRENT a un FakeUser admin por defecto para no arrastrar rol o sucursal entre tests.'
            ),
            "_set_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _set_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia el usuario falso de CURRENT por uno con el rol indicado (enum UserRole o string) y la sucursal dada.'
            ),
            "_set_staff": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _set_staff.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Atajo de _set_user que coloca un usuario con rol STAFF y la sucursal indicada.'
            ),
            "_seed_heartbeat": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_heartbeat.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Escribe en el diccionario global ALPR_HEARTBEATS una puerta con marca de tiempo hace 'seconds_ago' segundos, para simular heartbeats viejos o frescos."
            ),
            "_seed_camera": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_camera.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea una ParkingCamera con el tipo, sucursal y flag de activa indicados, y devuelve su id.'
            ),
            "test_health_admin_sin_heartbeats": (
                '💡 LA IDEA: Comprobar el escenario de health admin sin heartbeats.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin global sin heartbeats registrados recibe database ONLINE, alpr vacío y api ONLINE.'
            ),
            "test_health_admin_gates_online_y_offline": (
                '💡 LA IDEA: Comprobar el escenario de health admin gates online y offline.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Con heartbeats sembrados, la puerta con 5 s de antigüedad sale ONLINE y la de 300 s sale OFFLINE: comprueba el umbral de antigüedad del estado ALPR.'
            ),
            "test_health_database_fallida_devuelve_offline": (
                '💡 LA IDEA: Comprobar el escenario de health database fallida devuelve offline.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con una sesión que lanza RuntimeError al ejecutar, /health responde igual con database OFFLINE en lugar de trazar el error.'
            ),
            "test_health_staff_sin_cameras_usa_prefijos_de_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de health staff sin cameras usa prefijos de sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un staff sin cámaras cargadas ve las claves prefijadas SUCURSAL_ENTRADA / SUCURSAL_SALIDA (según su sucursal), con ONLINE/OFFLINE por antigüedad.'
            ),
            "test_health_staff_con_camaras_usa_proc_id": (
                '💡 LA IDEA: Comprobar el escenario de health staff con camaras usa proc id.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con una cámara ENTRADA en su sucursal, la clave del heartbeat pasa a ser el proc id SUCURSAL_TIPO_ID de esa cámara y aparece ONLINE.'
            ),
            "test_health_staff_con_camaras_proc_id_offline_sin_heartbeat": (
                '💡 LA IDEA: Comprobar el escenario de health staff con camaras proc id offline sin heartbeat.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Una cámara sin heartbeat registrado aparece OFFLINE en la clave de su proc id.'
            ),
            "test_health_staff_camara_sin_sucursal_normaliza_global": (
                '💡 LA IDEA: Comprobar el escenario de health staff camara sin sucursal normaliza global.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Una cámara sin sucursal se normaliza al prefijo GLOBAL_TIPO_ID y su heartbeat reciente la marca ONLINE.'
            ),
            "test_health_usuario_comun_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un usuario con rol común no puede consultar /health: recibe 403.'
            ),
            "test_heartbeat_normaliza_y_registra": (
                '💡 LA IDEA: Comprobar el escenario de heartbeat normaliza y registra.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: POST /heartbeat con gate_id con espacios y minúsculas lo normaliza a mayúsculas sin espacios, lo registra en ALPR_HEARTBEATS con marca de tiempo fresca y responde {'status': 'ok'}."
            ),
            "test_heartbeat_rechaza_nodo_no_autorizado": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin header de secreto (y host no loopback) el heartbeat devuelve 403 y NO escribe en ALPR_HEARTBEATS: cierra el bug de endpoint público que permitía simular puertas online.'
            ),
            "test_heartbeat_rechaza_secreto_incorrecto": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un x-node-secret distinto del configurado devuelve 403 y no registra la puerta.'
            ),
            "test_heartbeat_acepta_query_param_node_secret": (
                '💡 LA IDEA: Comprobar el escenario de heartbeat acepta query param node secret.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: El secreto también puede llegar por query param 'node_secret' (como el resto de endpoints ALPR) y el heartbeat se registra igual."
            ),
            "test_reset_borra_datos_y_archivos": (
                '💡 LA IDEA: Comprobar el escenario de reset borra datos y archivos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                "⚙️ FUNCIONAMIENTO: POST /reset como admin global borra AccessLog, usuarios con rol user y aforos, y vacía el directorio IMAGE_DIR; responde {'status': 'ok'}."
            ),
            "test_reset_sin_directorio_no_rompe": (
                '💡 LA IDEA: Comprobar el escenario de reset sin directorio no rompe.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si IMAGE_DIR no existe, el reset igual borra los datos y devuelve 200 sin trazar excepción.'
            ),
            "test_reset_unlink_fallido_tolerado": (
                '💡 LA IDEA: Comprobar el escenario de reset unlink fallido tolerado.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si os.unlink lanza PermissionError al borrar una imagen, el reset igual responde 200 y el archivo queda en pie.'
            ),
            "test_reset_no_super_admin_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un staff (no super admin) que intenta /reset recibe 403 con el detalle 'Requiere permisos de Administrador Global'."
            ),
            "test_get_virtual_time_publico": (
                '💡 LA IDEA: Comprobar el escenario de get virtual time publico.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /virtual-time devuelve un diccionario con offset_seconds o time (endpoint accesible sin rol operativo).'
            ),
        },
    },
    "tests/test_toggle_block.py": {
        "proposito": 'Verifica POST /v1/admin/users/{id}/toggle-block contra la app real de main.app (con la BD en memoria sobreescrita): control de permisos, prohibición de autobloqueo y, sobre todo, que el JWT emitido antes del bloqueo deje de servir porque el estado se chequea en la base de datos.',
        "simbolos": {
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: crea un engine SQLite en memoria con todas las tablas, sobreescribe get_db en la app real (guardando y restaurando los overrides existentes) y resetea el rate limiter; entrega (TestClient, sessionmaker).'
            ),
            "_crear_usuario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un User con el rol y email indicados (is_blocked e is_deleted en False) y lo devuelve refrescado.'
            ),
            "_token": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _token.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Emite un JWT de acceso con sub=email y rol del usuario, igual que el login real.'
            ),
            "_toggle": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _toggle.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: POST al endpoint toggle-block con header Authorization Bearer del token dado.'
            ),
            "test_toggle_block_sin_token_es_401": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin token (Bearer vacío) el endpoint responde 401.'
            ),
            "test_toggle_block_rol_usuario_es_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un usuario con rol común intentando bloquear a otro recibe 403.'
            ),
            "test_toggle_block_no_autobloqueo": (
                '💡 LA IDEA: Comprobar el escenario de toggle block no autobloqueo.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin que intenta bloquearse a sí mismo recibe 400.'
            ),
            "test_toggle_block_invalida_tokens_emitidos": (
                '💡 LA IDEA: Comprobar el escenario de toggle block invalida tokens emitidos.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Caso central: el token del usuario funciona (200 en /v1/user/me), tras bloquearlo el MISMO token devuelve 403 con detalle que menciona 'suspendida' y la BD confirma is_blocked=True; al desbloquear, el token vuelve a 200. Prueba que la validación es por estado en BD y no por revocación de token."
            ),
            "test_toggle_block_admin_bloquea_staff": (
                '💡 LA IDEA: Comprobar el escenario de toggle block admin bloquea staff.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin global puede bloquear a un miembro del staff: responde 200 con is_blocked=True.'
            ),
        },
    },
    "tests/test_user_fidelization_routes.py": {
        "proposito": 'Cubre routes/user/fidelization.py (prefijo /v1/user) con la app real y un usuario falso: catálogo de beneficios, canje de puntos por voucher o descuento de reserva, listado de tickets con enriquecimiento de ubicación, descuentos disponibles, cancelación con devolución de puntos e historial de puntos.',
        "simbolos": {
            "FakeUser": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuario logueado fingido para los endpoints: expone id, sucursal y puntos_acumulados sin tocar la BD.'
            ),
            "FakeUser.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Recibe user_id (por defecto 1), sucursal ('Centro') y puntos acumulados (1500) y los deja como atributos."
            ),
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: SQLite en memoria con todas las tablas, sobreescribe get_db y get_current_user en la app real (guardando/restaurando overrides) y resetea el limiter; entrega (TestClient, sessionmaker).'
            ),
            "_reset_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reset_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Autouse: restaura CURRENT a un FakeUser por defecto después de cada test.'
            ),
            "_seed_branch": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_branch.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea una ParkingBranch (sucursal) con nombre, dirección y coordenadas, y devuelve su id.'
            ),
            "_seed_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un User con id, puntos acumulados y sucursal fijos, para que el canje tenga con qué validar.'
            ),
            "_seed_promo": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_promo.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea una Promotion y devuelve su id; parametriza tipo ('voucher' o 'descuento_reserva'), costo en puntos, valor del descuento, ubicación (dirección/lat/lon) y si está activa."
            ),
            "_seed_ticket": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea un RedemptionTicket (código UUID de 16 caracteres si no se pasa uno) con su qr_data 'AUTOPASS_REDEMPTION|ID:...' y devuelve su id."
            ),
            "_seed_points_log": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_points_log.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un PointsLog con cantidad y motivo, para alimentar el historial de puntos.'
            ),
            "test_list_promotions": (
                '💡 LA IDEA: Comprobar el escenario de list promotions.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /promotions devuelve los beneficios vigentes creados (voucher y descuento de reserva) con sus títulos.'
            ),
            "test_list_promotions_vacio": (
                '💡 LA IDEA: Comprobar el escenario de list promotions vacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin promociones, /promotions devuelve 200 con lista vacía.'
            ),
            "test_redeem_voucher_ok": (
                '💡 LA IDEA: Comprobar el escenario de redeem voucher ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Canjear una promo voucher descuenta puntos y crea un ticket VIGENTE cuyo qr_data contiene el código del ticket (verifica el formato AUTOPASS_REDEMPTION|ID:...).'
            ),
            "test_redeem_promo_descuento_reserva_ok": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: El canje de tipo descuento_reserva crea un ticket con tipo_canje y valor_descuento correctos.'
            ),
            "test_redeem_promo_sin_ubicacion_uso_direccion_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de redeem promo sin ubicacion uso direccion sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Promo sin coordenadas: el ticket toma la dirección de la sucursal (branch) como fallback.'
            ),
            "test_redeem_promo_no_encontrada": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                "⚙️ FUNCIONAMIENTO: Canjear una promo inexistente devuelve 404 con 'Promoción no encontrada'."
            ),
            "test_redeem_promo_inactiva_no_encontrada": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Una promo inactiva también responde 404 (no se filtra como existente).'
            ),
            "test_redeem_puntos_insuficientes": (
                '💡 LA IDEA: Comprobar el escenario de redeem puntos insuficientes.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Con un usuario falso de solo 10 puntos y promo de 100, el canje devuelve 400 'Puntos insuficientes'."
            ),
            "test_list_redemption_tickets": (
                '💡 LA IDEA: Comprobar el escenario de list redemption tickets.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /redemption-tickets lista los tickets propios del usuario.'
            ),
            "test_list_redemption_tickets_rellena_datos_por_promo": (
                '💡 LA IDEA: Comprobar el escenario de list redemption tickets rellena datos por promo.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Un ticket sin ubicación pero con promo que sí la define se enriquece con la dirección de la promo.'
            ),
            "test_list_redemption_tickets_sucursal_sin_promo": (
                '💡 LA IDEA: Comprobar el escenario de list redemption tickets sucursal sin promo.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Un ticket sin promo ni ubicación cae en el fallback final: toma dirección y coordenadas de la sucursal (branch).'
            ),
            "test_list_redemption_tickets_vacio": (
                '💡 LA IDEA: Comprobar el escenario de list redemption tickets vacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin tickets, el listado devuelve 200 con lista vacía.'
            ),
            "test_available_redemptions": (
                '💡 LA IDEA: Comprobar el escenario de available redemptions.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /redemptions/available devuelve solo los tickets de tipo descuento_reserva vigentes.'
            ),
            "test_available_redemptions_vacio": (
                '💡 LA IDEA: Comprobar el escenario de available redemptions vacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin descuentos vigentes devuelve lista vacía.'
            ),
            "test_cancel_redemption_ticket_ok": (
                '💡 LA IDEA: Comprobar el escenario de cancel redemption ticket ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancelar un ticket vigente devuelve puntos_devueltos igual al costo de la promo (100).'
            ),
            "test_cancel_redemption_ticket_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                "⚙️ FUNCIONAMIENTO: Cancelar un ticket inexistente devuelve 404 'Ticket no encontrado'."
            ),
            "test_cancel_redemption_ticket_no_vigente": (
                '💡 LA IDEA: Comprobar el escenario de cancel redemption ticket no vigente.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Cancelar un ticket en estado USADO devuelve 400 'El ticket ya no se encuentra vigente'."
            ),
            "test_points_history": (
                '💡 LA IDEA: Comprobar el escenario de points history.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /points-history resume total de movimientos, total_earned (suma de positivos), total_redeemed (absoluto de negativos) e items.'
            ),
            "test_points_history_vacio": (
                '💡 LA IDEA: Comprobar el escenario de points history vacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin movimientos devuelve total 0 e items vacíos.'
            ),
        },
    },
    "tests/test_user_service.py": {
        "proposito": 'Tests unitarios directos de UserService (alta/actualización de usuarios y gestión de vehículos) sobre una BD en memoria a nivel de módulo, más una verificación de los permisos del local admin invocando directamente los manejadores de routes/admin/users.py.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: crea todas las tablas en el engine SQLite en memoria compartido del módulo, entrega una sesión y dropea todo al terminar cada test.'
            ),
            "test_create_user_success": (
                '💡 LA IDEA: Comprobar el escenario de create user success.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: UserService.create_user persiste el usuario con el email dado y el rol pasado (UserRole.USER).'
            ),
            "test_update_user_success": (
                '💡 LA IDEA: Comprobar el escenario de update user success.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: UserService.update_user aplica el UserAdminUpdate y normaliza el nombre con capitalización: 'JuanNuevo' queda guardado como 'Juannuevo'."
            ),
            "test_local_admin_permissions_on_branch_users": (
                '💡 LA IDEA: Comprobar el escenario de local admin permissions on branch users.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Invoca directamente update_user_admin, change_user_role y delete_user de routes/admin/users con un Request de Starlette falso: el local admin edita y borra staff de su sede (con sucursal normalizada), NO puede asignar el rol staff (403) pero el admin global sí, y NO puede borrar a un admin global (403).'
            ),
            "_make_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _make_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper: crea un usuario de prueba estándar con UserCreate y rol USER.'
            ),
            "test_add_vehicle_success": (
                '💡 LA IDEA: Comprobar el escenario de add vehicle success.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Add_vehicle normaliza la patente: 'AB 123 CD' se guarda como 'AB123CD' junto a marca/modelo."
            ),
            "test_add_vehicle_invalid_plate": (
                '💡 LA IDEA: Comprobar el escenario de add vehicle invalid plate.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Una patente inválida ('XYZ') lanza HTTPException con status 400."
            ),
            "test_add_vehicle_acepta_patentes_mercosur_extranjeras": (
                '💡 LA IDEA: Comprobar el escenario de add vehicle acepta patentes mercosur extranjeras.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Parametrizado: acepta formatos de Brasil (viejo y Mercosur), Uruguay y Paraguay, verificando que la validación no es solo argentina.'
            ),
            "test_add_vehicle_duplicate": (
                '💡 LA IDEA: Comprobar el escenario de add vehicle duplicate.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Agregar la misma patente dos veces (aunque con distinto formato) lanza 400 por duplicado.'
            ),
            "test_set_favorite_vehicle_toggle": (
                '💡 LA IDEA: Comprobar el escenario de set favorite vehicle toggle.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Set_favorite_vehicle alterna: la primera llamada marca is_favorite=True y la segunda lo vuelve False.'
            ),
            "test_delete_vehicle_reassigns_favorite": (
                '💡 LA IDEA: Comprobar el escenario de delete vehicle reassigns favorite.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Al borrar el vehículo favorito, el vehículo restante queda marcado como favorito.'
            ),
            "test_delete_vehicle_blocks_active_reservation": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: No deja borrar un vehículo con reserva activa (ventana que incluye el ahora, estado Pendiente): lanza HTTPException 400.'
            ),
        },
    },
    "tests/test_user_support_routes.py": {
        "proposito": 'Cubre routes/user/support.py (prefijo /v1/user) con la app real y overrides: creación, listado, detalle y respuesta de tickets de soporte del usuario, incluido aislamiento entre usuarios y validación de adjuntos (extensión y tamaño).',
        "simbolos": {
            "FakeUser": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuario falso para el override de get_current_user: id, nombre, apellido, rol y sucursal en memoria.'
            ),
            "FakeUser.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Recibe user_id (1 por defecto), nombre, apellido, rol ('user') y sucursal (None) y los deja como atributos."
            ),
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: SQLite en memoria con todas las tablas, sobreescribe get_db y get_current_user en la app real (guardando/restaurando overrides) y resetea el limiter; entrega (TestClient, sessionmaker).'
            ),
            "_reset_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reset_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Autouse: restaura CURRENT al objeto USER global después de cada test.'
            ),
            "_seed_ticket": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un usuario seed (id=2) y un SupportTicket suyo con el estado, asunto y mensaje indicados; devuelve (user_id, ticket_id).'
            ),
            "_seed_message": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_message.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrega un SupportTicketMessage al ticket indicado, para probar el hilo de conversación.'
            ),
            "test_create_support_ticket": (
                '💡 LA IDEA: Comprobar el escenario de create support ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                "⚙️ FUNCIONAMIENTO: POST /support-tickets crea el ticket con 201, estado 'Pendiente', sucursal y ticket_id >= 1."
            ),
            "test_create_support_ticket_falta_campo": (
                '💡 LA IDEA: Comprobar el escenario de create support ticket falta campo.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin asunto/mensaje el endpoint rechaza con 400 o 422.'
            ),
            "test_list_my_support_tickets": (
                '💡 LA IDEA: Comprobar el escenario de list my support tickets.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: GET lista solo los tickets del usuario logueado (al menos el sembrado).'
            ),
            "test_list_my_support_tickets_vacio": (
                '💡 LA IDEA: Comprobar el escenario de list my support tickets vacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin tickets devuelve lista vacía con 200.'
            ),
            "test_get_my_support_ticket": (
                '💡 LA IDEA: Comprobar el escenario de get my support ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                "⚙️ FUNCIONAMIENTO: El detalle incluye id, estado y el listado 'messages' con los mensajes del ticket."
            ),
            "test_get_my_support_ticket_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un id inexistente devuelve 404 'Ticket no encontrado'."
            ),
            "test_get_ticket_ajeno_no_se_ve": (
                '💡 LA IDEA: Comprobar el escenario de get ticket ajeno no se ve.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: El detalle de un ticket de OTRO usuario también responde 404: aislamiento por dueño.'
            ),
            "test_reply_my_support_ticket": (
                '💡 LA IDEA: Comprobar el escenario de reply my support ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                "⚙️ FUNCIONAMIENTO: PATCH reply agrega el mensaje del usuario y cambia el estado del ticket a 'En Revisión'."
            ),
            "test_reply_ticket_resuelto_bloqueado": (
                '💡 LA IDEA: Comprobar el escenario de reply ticket resuelto bloqueado.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Responder un ticket Resuelto devuelve 400 con detalle que menciona 'bloqueado'."
            ),
            "test_reply_ticket_cancelado_bloqueado": (
                '💡 LA IDEA: Comprobar el escenario de reply ticket cancelado bloqueado.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Responder un ticket Cancelado también devuelve 400 'bloqueado'."
            ),
            "test_reply_support_ticket_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Responder un ticket inexistente devuelve 404.'
            ),
            "test_reply_support_ticket_sin_mensaje": (
                '💡 LA IDEA: Comprobar el escenario de reply support ticket sin mensaje.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Reply sin campo mensaje responde 400 o 422.'
            ),
            "test_reply_support_ticket_con_adjunto": (
                '💡 LA IDEA: Comprobar el escenario de reply support ticket con adjunto.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Reply con adjunto PNG válido devuelve 200 (o 400 si la validación lo rechaza) e incluye messages en la respuesta.'
            ),
            "test_reply_support_ticket_adjunto_extension_no_permitida_user": (
                '💡 LA IDEA: Comprobar el escenario de reply support ticket adjunto extension no permitida user.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Un adjunto .exe devuelve 400 con el mensaje de formatos permitidos (PNG, JPG, GIF, WEBP o PDF).'
            ),
            "test_reply_support_ticket_adjunto_demasiado_grande": (
                '💡 LA IDEA: Comprobar el escenario de reply support ticket adjunto demasiado grande.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Un PNG de más de 1 MB devuelve 400 'El archivo supera el tamaño máximo de 1 MB.' (la función está definida dos veces en el archivo con el mismo escenario; la segunda definición es la que se ejecuta)."
            ),
        },
    },
    "tests/test_video_routes.py": {
        "proposito": 'Cubre routes/system/video.py con una FastAPI mínima: WebSocket /ws/video para nodos ALPR y espectadores (rol y sucursal), el endpoint HTTP /update-frame, el stream MJPEG /video-feed, la descarga /capture y los helpers de confianza de red (_is_local_or_private, _is_trusted_alpr_node, _user_from_token).',
        "simbolos": {
            "OnceDict": (
                '💡 LA IDEA: Comprobar el escenario de OnceDict.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Subclase de dict usada como last_frames en los tests: sus valores se consumen una sola vez para cortar los generadores de forma determinista.'
            ),
            "OnceDict.get": (
                '💡 LA IDEA: Comprobar el escenario de OnceDict.get.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Dict que devuelve cada valor una sola vez (lo elimina al leerlo), usado como last_frames para poder cortar los generadores de frames de forma determinista.'
            ),
            "FakeUser": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de usuario con rol, sucursal y email, para los overrides de get_operational_user y los repositorios de usuarios.'
            ),
            "FakeUser.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Recibe rol ('admin' por defecto), sucursal (None) y email, y los deja como atributos."
            ),
            "FakeLog": (
                '💡 LA IDEA: Comprobar el escenario de FakeLog.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de AccessLog con id, sucursal e imagen_path, para /capture sin tocar la BD.'
            ),
            "FakeLog.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeLog.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Recibe id (1), sucursal ('Centro') e imagen_path (None) y los expone como atributos."
            ),
            "app_client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para app_client.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona un cliente HTTP preconfigurado con las credenciales necesarias para consultar los endpoints del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: FastAPI solo con el router de video, limpiando las conexiones activas y last_frames del manager global de WebSockets antes de arrancar.'
            ),
            "authed_staff": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Depende de app_client y sobreescribe get_operational_user con un FakeUser admin, para los tests autenticados de video-feed.'
            ),
            "test_is_local_or_private_loopback_y_privada": (
                '💡 LA IDEA: Comprobar el escenario de is local or private loopback y privada.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: _is_local_or_private acepta loopback y rangos privados (10.x, 192.168.x, 172.16.x).'
            ),
            "test_is_local_or_private_publica_e_invalida": (
                '💡 LA IDEA: Comprobar el escenario de is local or private publica e invalida.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Direcciones públicas, hostnames y cadenas vacías no se consideran locales/privadas.'
            ),
            "test_is_trusted_alpr_node_con_secreto": (
                '💡 LA IDEA: Comprobar el escenario de is trusted alpr node con secreto.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con ALPR_NODE_SECRET configurado, el nodo es de confianza solo si el secreto coincide exactamente.'
            ),
            "test_is_trusted_alpr_node_sin_secreto_usa_red": (
                '💡 LA IDEA: Comprobar el escenario de is trusted alpr node sin secreto usa red.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin secreto configurado, la confianza la decide la IP: loopback/privada acepta, pública no.'
            ),
            "test_ws_nodo_no_autorizado_cierra_4403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Conectar a /ws/video sin secreto ni token cierra el socket con código 4403.'
            ),
            "test_ws_nodo_autorizado_recibe_y_broadcast": (
                '💡 LA IDEA: Comprobar el escenario de ws nodo autorizado recibe y broadcast.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Un nodo autorizado puede enviar frames: el texto enviado queda guardado en manager.last_frames con la cámara en mayúsculas.'
            ),
            "test_ws_nodo_error_en_broadcast_no_crashea": (
                '💡 LA IDEA: Comprobar el escenario de ws nodo error en broadcast no crashea.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Si manager.broadcast_frame lanza excepción, el servidor la traga, registra 'Error en nodo ALPR CAM01' en el log y el socket no se rompe."
            ),
            "test_ws_espectador_role_denegado_cierra_4403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un espectador con rol 'cliente' recibe cierre 4403."
            ),
            "test_ws_espectador_aceptado_recibe_ultimo_frame": (
                '💡 LA IDEA: Comprobar el escenario de ws espectador aceptado recibe ultimo frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin espectador recibe apenas se conecta el último frame cacheado de la cámara; al desconectar, la lista de conexiones de esa cámara queda vacía.'
            ),
            "test_ws_espectador_sucursal_distinta_cierra_4003": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un staff de otra sucursal que intenta ver una cámara ajena se desconecta con código 4003.'
            ),
            "test_ws_error_al_resolver_usuario_trata_como_nodo": (
                '💡 LA IDEA: Comprobar el escenario de ws error al resolver usuario trata como nodo.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Si la BD falla al resolver el usuario del token, el servidor cae a la rama de nodo ALPR autorizado en lugar de trazar.'
            ),
            "test_update_frame_nodo_autorizado": (
                '💡 LA IDEA: Comprobar el escenario de update frame nodo autorizado.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: POST /update-frame con nodo autorizado guarda la imagen en last_frames y responde {'status': 'ok'}."
            ),
            "test_update_frame_sin_imagen_ok_sin_broadcast": (
                '💡 LA IDEA: Comprobar el escenario de update frame sin imagen ok sin broadcast.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Sin campo 'image' responde 200 pero no guarda ni difunde frame."
            ),
            "test_update_frame_nodo_no_autorizado_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin autorización el endpoint responde 403.'
            ),
            "_feed_gen": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _feed_gen.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta video_feed_legacy con asyncio.run y devuelve el body_iterator (generador async de frames MJPEG) de la Response.'
            ),
            "_drive_feed": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _drive_feed.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Consume n iteraciones del generador async dentro de un único event loop y devuelve los chunks.'
            ),
            "_drive_feed_raises": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _drive_feed_raises.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Consume el generador hasta que lance RuntimeError o termine; devuelve True si llegó al final esperado.'
            ),
            "test_video_feed_genera_frames_y_corta": (
                '💡 LA IDEA: Comprobar el escenario de video feed genera frames y corta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: El feed emite un chunk multipart con el frame decodificado de base64 ('--frame' y el contenido) y corta cuando time.sleep lanza la excepción de fin."
            ),
            "test_video_feed_sin_frame_todavia_corta": (
                '💡 LA IDEA: Comprobar el escenario de video feed sin frame todavia corta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin frames todavía en last_frames el generador igual termina limpio (no se cuelga).'
            ),
            "test_video_feed_sucursal_distinta_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Staff de 'Centro' pidiendo /video-feed/OTRA_1 recibe 403."
            ),
            "test_video_feed_sucursal_igual_ok": (
                '💡 LA IDEA: Comprobar el escenario de video feed sucursal igual ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El feed de la sucursal propia arranca y solo termina cuando el test fuerza el corte.'
            ),
            "test_user_from_token_ok": (
                '💡 LA IDEA: Comprobar el escenario de user from token ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: _user_from_token decodifica el JWT y devuelve el usuario activo de la BD.'
            ),
            "test_user_from_token_invalido_401": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Token que no decodifica → HTTPException 401.'
            ),
            "test_user_from_token_usuario_no_encontrado_401": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Token válido pero usuario inexistente → 401.'
            ),
            "test_user_from_token_role_denegado_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuario con rol no operativo (cliente) → 403.'
            ),
            "_capture_setup": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _capture_setup.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Prepara /capture: override de get_db, monkeypatch de AccessRepository.get_by_id con el log dado, decodificador de token y fábrica de usuario (admin por defecto).'
            ),
            "test_capture_sin_token_401": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin token ni header, /capture responde 401.'
            ),
            "_fake_fileresponse": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _fake_fileresponse.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplaza FileResponse por una Response simple cuyo contenido es el path, para inspeccionar qué archivo se serviría.'
            ),
            "test_capture_por_header_bearer_ok": (
                '💡 LA IDEA: Comprobar el escenario de capture por header bearer ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con Authorization: Bearer y archivo existente, /capture 200 y sirve la imagen pedida.'
            ),
            "test_capture_token_query_mal_401": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Token por query que no decodifica → 401.'
            ),
            "test_capture_log_no_existe_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: AccessLog inexistente → 404.'
            ),
            "test_capture_role_cliente_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un cliente no puede descargar capturas: 403.'
            ),
            "test_capture_sucursal_distinta_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Staff de otra sucursal que pide una captura ajena: 403.'
            ),
            "test_capture_misma_sucursal_distinto_formato_ok": (
                '💡 LA IDEA: Comprobar el escenario de capture misma sucursal distinto formato ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Compara sucursal normalizada: log en 'AUTOPASS Centro' y staff en 'Centro' → 200."
            ),
            "test_capture_image_no_existe_devuelve_logo": (
                '💡 LA IDEA: Comprobar el escenario de capture image no existe devuelve logo.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el archivo del log no existe en disco, responde 200 con el logo por defecto.'
            ),
            "test_capture_sin_imagen_path_devuelve_logo": (
                '💡 LA IDEA: Comprobar el escenario de capture sin imagen path devuelve logo.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el log ni siquiera tiene imagen_path, también cae en el logo.'
            ),
        },
    },
    "tests/test_video_streamer.py": {
        "proposito": 'Cubre alpr/video_streamer.py (VideoStreamer) con un VideoCapture y un Thread sintéticos: cómo se abre la fuente en __init__, el bucle _update con reescalado y reintentos, get_frame() thread-safe y stop() con liberación de recursos.',
        "simbolos": {
            "FakeCap": (
                '💡 LA IDEA: Comprobar el escenario de FakeCap.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: VideoCapture sintético que reemplaza al de OpenCV: consume una lista de respuestas de read() y registra las llamadas a set().'
            ),
            "FakeCap.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeCap.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: VideoCapture sintético: recibe la lista de respuestas de read(), registra las llamadas a set() y guarda si está abierto; opcionalmente se enlaza con el streamer para apagarse al agotar las respuestas.'
            ),
            "FakeCap.set": (
                '💡 LA IDEA: Comprobar el escenario de FakeCap.set.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra cada (clave, valor) configurado para poder asertar los CAP_PROP pedidos por el streamer.'
            ),
            "FakeCap.read": (
                '💡 LA IDEA: Comprobar el escenario de FakeCap.read.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la siguiente respuesta guardada (o lanza la excepción si el ítem es una excepción); si se agota, marca is_running=False del streamer enlazado y devuelve (False, None).'
            ),
            "FakeCap.isOpened": (
                '💡 LA IDEA: Comprobar el escenario de FakeCap.isOpened.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el flag de abierto/cerrado configurado.'
            ),
            "FakeCap.release": (
                '💡 LA IDEA: Comprobar el escenario de FakeCap.release.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca released=True para verificar que stop() libera el recurso.'
            ),
            "FakeThread": (
                '💡 LA IDEA: Comprobar el escenario de FakeThread.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplazo de threading.Thread que no ejecuta ningún hilo real: solo guarda su configuración en una lista de instancias.'
            ),
            "FakeThread.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeThread.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplazo de threading.Thread que NO ejecuta el target: solo registra args/kwargs y se agrega a la lista de instancias.'
            ),
            "FakeThread.start": (
                '💡 LA IDEA: Comprobar el escenario de FakeThread.start.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca started=True sin lanzar ningún hilo real.'
            ),
            "FakeThread.join": (
                '💡 LA IDEA: Comprobar el escenario de FakeThread.join.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite satisfacer las dependencias de la interfaz probada sin ejecutar operaciones reales.\n\n'
                '⚙️ FUNCIONAMIENTO: Implementar una variante inocua del método FakeThread.join que no produzca efectos colaterales.'
            ),
            "_small_frame": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _small_frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Numpy array uint8 de 180x240x3 (frame chica, no necesita reescalado con target 1280).'
            ),
            "_wide_frame": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _wide_frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Numpy array uint8 de 900x1600x3 (frame ancha, sí reescalada).'
            ),
            "_no_frame": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _no_frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Tupla (False, None) que imita un read() sin imagen.'
            ),
            "no_sleep": (
                '💡 LA IDEA: Comprobar el escenario de no sleep.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte time.sleep en no-op para que _update corra instantáneo.'
            ),
            "_make_streamer": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _make_streamer.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma un VideoStreamer con __init__ evitado (VideoStreamer.__new__): inyecta cap, target_width 1280, current_frame None, is_running y lock; opcionalmente enlaza cap con el streamer.'
            ),
            "test_init_http_source_usa_ffmpeg_y_timeouts": (
                '💡 LA IDEA: Comprobar el escenario de init http source usa ffmpeg y timeouts.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Una fuente http abre cv2.VideoCapture(url, CAP_FFMPEG) y configura BUFFERSIZE=1, OPEN/READ_TIMEOUT=5000 ms y tamaño 1280x720.'
            ),
            "test_init_fuente_local_usa_videocapture_simple": (
                '💡 LA IDEA: Comprobar el escenario de init fuente local usa videocapture simple.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Una fuente local (índice 0) abre cv2.VideoCapture(0) sin argumentos extra y deja is_running=True.'
            ),
            "test_start_lanza_hilo_daemon": (
                '💡 LA IDEA: Comprobar el escenario de start lanza hilo daemon.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Start() devuelve self, lanza un Thread con daemon=True y target=_update.'
            ),
            "test_update_guarda_frame_y_resetea_retries": (
                '💡 LA IDEA: Comprobar el escenario de update guarda frame y resetea retries.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: _update reintenta ante frames vacíos y al recibir una frame ancha la guarda reescalada a 1280x720; el bucle termina con is_running False.'
            ),
            "test_update_sin_reescalado_guarda_frame_small": (
                '💡 LA IDEA: Comprobar el escenario de update sin reescalado guarda frame small.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Una frame de 240x180 con target_width 640 se guarda sin reescalar (forma original).'
            ),
            "test_update_frame_vacio_reintenta_y_loguea": (
                '💡 LA IDEA: Comprobar el escenario de update frame vacio reintenta y loguea.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Ante dos frames vacíos imprime '[VideoStreamer] Frame no recibido (intento 1/3)' y '(intento 2/3)' y termina con la frame válida guardada."
            ),
            "test_update_excepcion_de_read_no_frena": (
                '💡 LA IDEA: Comprobar el escenario de update excepcion de read no frena.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Si read() lanza RuntimeError, se loguea '[VideoStreamer] Excepción: RuntimeError - boom' y _update sigue hasta guardar la siguiente frame."
            ),
            "test_get_frame_none_sin_frame": (
                '💡 LA IDEA: Comprobar el escenario de get frame none sin frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin frame recibido, get_frame() devuelve None.'
            ),
            "test_get_frame_devuelve_copia": (
                '💡 LA IDEA: Comprobar el escenario de get frame devuelve copia.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Get_frame() devuelve una copia: modificar la frame devuelta no toca current_frame original.'
            ),
            "test_stop_libera_capture_si_abierta": (
                '💡 LA IDEA: Comprobar el escenario de stop libera capture si abierta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Stop() pone is_running=False y llama release() al VideoCapture abierto.'
            ),
            "test_stop_no_libera_si_cerrada": (
                '💡 LA IDEA: Comprobar el escenario de stop no libera si cerrada.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el VideoCapture ya está cerrado, stop() no llama release().'
            ),
            "test_stop_cap_none_no_crashea": (
                '💡 LA IDEA: Comprobar el escenario de stop cap none no crashea.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con cap=None, stop() solo desactiva is_running sin lanzar excepción.'
            ),
        },
    },
    "tests/test_virtual_time.py": {
        "proposito": 'Verifica el servicio de reloj virtual TimeService (estado global en memoria): que avanzar, retroceder, fijar una fecha objetivo y resetear el offset produzcan los desplazamientos y el formato de salida esperados, ya que todo el sistema (reservas, workers) cuelga de ese offset.',
        "simbolos": {
            "test_time_service_advance_and_rewind": (
                '💡 LA IDEA: Comprobar el escenario de time service advance and rewind.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Ciclo completo: reset deja offset en 0; advance(hours=1) suma 3600 s; rewind(minutes=30) baja a 1800 s; get_info reporta offset_seconds 1800, active True y '+0h 30m' en el formato; reset vuelve a 0 y is_active False."
            ),
            "test_time_service_set_target_datetime": (
                '💡 LA IDEA: Comprobar el escenario de time service set target datetime.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que las estadías breves dentro del tiempo de cortesía puedan salir sin costo ni retención innecesaria.\n\n'
                "⚙️ FUNCIONAMIENTO: Set_target_datetime con una fecha a ahora + 2 días 3 horas produce un offset de ~183600 s (tolerancia ±10 s), el formato '+2d 3h' (o '+2d 2h 59m' por redondeo) y active True; al final resetea a 0."
            ),
        },
    },
    "tests/test_worker_cleanup.py": {
        "proposito": 'Verifica los workers de mantenimiento: auto-cancelación de reservas impagas sin ingreso, limpieza de vencidas con gracia de 2 horas, finalización automática de reservas terminadas y purga de imágenes ALPR antiguas, todo sobre SQLite en memoria con el reloj virtual como referencia de tiempo.',
        "simbolos": {
            "db_session": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db_session.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: crea un engine SQLite en memoria con todas las tablas y entrega (sesión, engine); cierra la sesión al terminar.'
            ),
            "_crear_usuario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un User de prueba (rol user, password_hash ficticio) y lo devuelve refrescado.'
            ),
            "_fmt": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _fmt.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea un datetime al patrón '%Y-%m-%d %H:%M' que usan las columnas de fecha de las reservas."
            ),
            "test_auto_cancela_reserva_impaga_vencida": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Reserva PENDIENTE impaga cuyo inicio fue hace 40 min y sin AccessLog de ENTRADA: _process_auto_cancellations la pasa a CANCELADA + FALLIDO y genera una notificación AUTO_CANCELLED al usuario (el email se mockea).'
            ),
            "test_auto_cancel_no_cancela_si_ya_ingreso": (
                '💡 LA IDEA: Comprobar el escenario de auto cancel no cancela si ya ingreso.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Si existe un AccessLog de ENTRADA con la patente de la reserva, la auto-cancelación la respeta (sigue PENDIENTE) y no dispara el email (spy vacío).'
            ),
            "test_cleanup_overdue_gracias_2h_cancela": (
                '💡 LA IDEA: Comprobar el escenario de cleanup overdue gracias 2h cancela.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Reserva por hora impaga con inicio hace 3 horas (fuera de la gracia de 2 h) → cleanup_overdue_reservations la cancela (CANCELADA + FALLIDO).'
            ),
            "test_cleanup_overdue_no_cancela_con_ingreso": (
                '💡 LA IDEA: Comprobar el escenario de cleanup overdue no cancela con ingreso.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: El mismo cleanup no cancela una reserva vencida cuyo vehículo ya ingresó al predio.'
            ),
            "test_auto_finalize_completa_reservas_vencidas": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Auto_finalize_all_reservations pasa a COMPLETADA la reserva ACTIVA y pagada con fecha_fin ya pasada, deja ACTIVA la vigente y devuelve un conteo >= 1.'
            ),
            "test_cleanup_purga_imagenes_antiguas": (
                '💡 LA IDEA: Comprobar el escenario de cleanup purga imagenes antiguas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: _cleanup_old_alpr_images borra de IMAGE_DIR las imágenes con más de ALPR_IMAGE_RETENTION_DAYS (30 días, forzados con os.utime) y conserva las nuevas.'
            ),
            "test_cleanup_no_borra_si_directorio_inexistente": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con IMAGE_DIR inexistente la purga no lanza excepción ni crea el directorio.'
            ),
        },
    },
    "tests/test_ws_client.py": {
        "proposito": 'Cubre alpr/ws_client.py (ws_monitoring_worker): el envío periódico de frames JPEG por WebSocket hacia el servidor de monitoreo, con overlay opcional, tolerancia a frames nulos y errores, y reconexión automática ante fallos de conexión.',
        "simbolos": {
            "FakeStreamer": (
                '💡 LA IDEA: Comprobar el escenario de FakeStreamer.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Streamer falso: mantiene is_running y entrega una cola de frames prearmados a get_frame().'
            ),
            "FakeStreamer.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeStreamer.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Streamer falso con is_running True y una lista de frames a devolver en orden.'
            ),
            "FakeStreamer.get_frame": (
                '💡 LA IDEA: Comprobar el escenario de FakeStreamer.get frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el siguiente frame de la cola o, si se agota, un frame negro de 180x320.'
            ),
            "FakeEngine": (
                '💡 LA IDEA: Comprobar el escenario de FakeEngine.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Motor OCR simulado para verificar el dibujado de overlay sobre los frames transmitidos por WebSocket.'
            ),
            "FakeEngine.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeEngine.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Motor de overlay falso que solo cuenta cuántas veces se lo invocó.'
            ),
            "FakeEngine.get_frame_with_overlay": (
                '💡 LA IDEA: Comprobar el escenario de FakeEngine.get frame with overlay.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el mismo frame y suma overlay_calls.'
            ),
            "FakeSocket": (
                '💡 LA IDEA: Comprobar el escenario de FakeSocket.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Socket WebSocket falso que captura mensajes enviados y dispara eventos para pruebas.'
            ),
            "FakeSocket.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeSocket.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Socket falso que acumula en sent todo lo enviado y dispara el callback on_send después de cada envío.'
            ),
            "FakeSocket.send": (
                '💡 LA IDEA: Comprobar el escenario de FakeSocket.send.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el dato y llama al on_send asíncrono (permite cortar el bucle del worker desde el envío).'
            ),
            "FakeSocket.__aenter__": (
                '💡 LA IDEA: Comprobar el escenario de FakeSocket.  aenter  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Context manager async: devuelve a sí mismo (el worker usa 'async with')."
            ),
            "FakeSocket.__aexit__": (
                '💡 LA IDEA: Comprobar el escenario de FakeSocket.  aexit  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra el context manager sin propagar excepciones.'
            ),
            "FakeBackendFactory": (
                '💡 LA IDEA: Comprobar el escenario de FakeBackendFactory.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Fábrica de conexiones WebSocket falsas para simular reconexiones y cortes de red.'
            ),
            "FakeBackendFactory.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeBackendFactory.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Fábrica de sockets parametrizable: 'raise_first' lanza ConnectionRefusedError en las primeras N conexiones, 'stop_on_connect'/'stop_at' deciden en qué conexión se apaga el streamer."
            ),
            "FakeBackendFactory.__call__": (
                '💡 LA IDEA: Comprobar el escenario de FakeBackendFactory.  call  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuenta conexiones, lanza el error si corresponde o devuelve un FakeSocket nuevo (y opcionalmente detiene el streamer).'
            ),
            "FakeBackendFactory._on_send": (
                '💡 LA IDEA: Comprobar el escenario de FakeBackendFactory. on send.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Callback por defecto sin acción, reemplazable por los tests.'
            ),
            "_frame": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Numpy array uint8 de h x w x 3 con el relleno indicado, para simular frames.'
            ),
            "_run": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _run.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta una corrutina con asyncio.run.'
            ),
            "no_sleep_cnt": (
                '💡 LA IDEA: Comprobar el escenario de no sleep cnt.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplaza asyncio.sleep por un no-op que cuenta llamadas, para que los bucles de reintento terminen al instante.'
            ),
            "test_envia_frames_sin_engine": (
                '💡 LA IDEA: Comprobar el escenario de envia frames sin engine.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin engine, el worker envía un único mensaje cuyo base64 decodifica a un JPEG válido (magic bytes FF D8).'
            ),
            "test_envia_frames_con_engine": (
                '💡 LA IDEA: Comprobar el escenario de envia frames con engine.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con engine, el worker invoca get_frame_with_overlay una vez y envía un solo frame.'
            ),
            "test_frame_none_no_envia": (
                '💡 LA IDEA: Comprobar el escenario de frame none no envia.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si get_frame() devuelve None no se envía nada y el bucle interno termina (is_running en False).'
            ),
            "test_error_al_procesar_frame_breakea_bucle_interno": (
                '💡 LA IDEA: Comprobar el escenario de error al procesar frame breakea bucle interno.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Cv2.resize falla la primera vez: se imprime '[!] Error al procesar/enviar frame', el worker NO propaga la excepción y el bucle interno continúa hasta la conexión donde se lo detiene."
            ),
            "test_reconexion_tras_error_de_conexion": (
                '💡 LA IDEA: Comprobar el escenario de reconexion tras error de conexion.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con dos ConnectionRefusedError seguidos, el worker reintenta hasta 3 conexiones, registrando '[!] WS Streaming Error' y 'ConnectionRefusedError' en salida."
            ),
        },
    },
}
