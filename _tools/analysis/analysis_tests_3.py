"""Explicaciones analizadas de tests (parte 3 de 6, análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "tests/test_bugfixes_funcionales.py": {
        "proposito": 'Regresión de bugs funcionales ya corregidos en AUTOPASS: salida en sedes sin aforo configurado, robustez del QR ante gate_id mal formado, validación de patentes con formato distinto entre checkout y cobro, cobro único del extra por reserva vencida, acreditación de puntos con patente normalizada y resolución de alias de portón. Monta una sesión SQLite en memoria con una sucursal, precios y helpers para crear usuarios, vehículos, logs y reservas.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Parchea HardwareService.trigger_barrier para que no dispare barreras reales y crea una base SQLite en memoria (StaticPool) con las tablas, una sucursal 'AUTOPASS Test' y los settings precio_hora/precio_30min. Devuelve la sesión; al terminar la cierra y borra las tablas."
            ),
            "_sucursal": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea la sucursal de prueba si todavía no existe en la sesión y hace commit; se usa para asegurar el parking sin duplicarlo.'
            ),
            "_usuario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Inserta y devuelve un usuario de rol USER con email 'test@autopass.com' y los puntos acumulados que se le pasen."
            ),
            "_vehiculo": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _vehiculo.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un vehículo AUTO con la patente de prueba formateada, ligado al usuario y marcado como favorito; devuelve el vehículo.'
            ),
            "_log": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _log.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un AccessLog de ENTRADA con la patente normalizada, fecha de ingreso tres horas atrás y los flags de pago/costo/fecha de pago recibidos; devuelve el log. Es el insumo de los tests de cobro.'
            ),
            "_reserva_vencida": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reserva_vencida.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta una reserva ACTIVA ya pagada (PaymentStatus.PAGADO) cuyo horario terminó dos horas atrás, con la patente de prueba; sirve para verificar el extra por reserva vencida.'
            ),
            "test_exit_plate_registra_salida_en_sede_sin_aforo_configurado": (
                '💡 LA IDEA: Comprobar el escenario de exit plate registra salida en sede sin aforo configurado.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                "⚙️ FUNCIONAMIENTO: Comprueba que la salida de un vehículo que ya pagó se registra aunque la sede no tenga fila en ParkingAforo: verifica que no existe aforo y que exit_plate devuelve 'allowed' y crea exactamente un AccessLog de SALIDA sin fallar."
            ),
            "test_validate_qr_sin_guion_bajo_en_gate_id_no_falla_con_error_interno": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que validate_qr con un gate_id sin guion bajo (p. ej. 'QR') y una reserva inexistente devuelve status 'error' con mensaje 'Reserva no encontrada', en vez de romper con un error interno."
            ),
            "test_validate_qr_no_expone_mensajes_de_error_interno": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Confirma que ante un QR mal formado la respuesta es 'Formato de QR inválido' y no filtra detalles internos de Python (no contiene 'local variable')."
            ),
            "test_checkout_mercadopago_de_estadia_acepta_patente_en_distinto_formato": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Con token y BASE_URL https falsos y _mp_request mockeado, verifica que crear el checkout de una estadía acepta la patente aunque el log la guarde normalizada: devuelve external_reference que empieza con 'AP-ESTADIA-', init_point y registra un MercadoPagoPayment."
            ),
            "test_extra_por_reserva_vencida_se_cobra_una_sola_vez": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Simula tres cobros en caja seguidos sobre un log asociado a una reserva vencida: el primero cobra un extra mayor a cero y los otros dos cobran cero, y el costo final del log queda intacto (solo se sumó el primer extra). Demuestra la idempotencia del recargo.'
            ),
            "test_cobro_en_caja_acredita_puntos_con_patente_normalizada": (
                '💡 LA IDEA: Comprobar el escenario de cobro en caja acredita puntos con patente normalizada.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que un cobro en caja busca al usuario por la patente normalizada y le acredita puntos: verifica que puntos_ganados es mayor a cero, que el saldo del usuario coincide y que se creó un único PointsLog.'
            ),
            "test_resolve_gate_reconoce_alias_de_porton": (
                '💡 LA IDEA: Comprobar el escenario de resolve gate reconoce alias de porton.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Parametrizado: verifica que resolve_gate traduce alias como 'ENTRADA'/'entrada'/'INGRESO'/'ENTRY' y 'SALIDA'/'EGRESO'/'EXIT' (y con prefijo de sucursal) a ENTRADA o SALIDA."
            ),
            "test_resolve_gate_rechaza_porton_desconocido_sin_asumir_salida": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Parametrizado: confirma que un gate_id vacío, nulo, 'QR', un typo ('EGRES0','TYP0') o ambiguo ('ENTRADA_SALIDA') lanza HTTPException 400 en vez de asumir una salida."
            ),
            "hardware_mocks": (
                '💡 LA IDEA: Simular el componente hardware_mocks para aislar la prueba de dependencias externas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite inspeccionar qué comandos físicos se habrían enviado sin necesitar una barrera de estacionamiento conectada.\n\n'
                '⚙️ FUNCIONAMIENTO: Parchea publish_mqtt y send_serial_command de HardwareService para que no hagan efectos reales durante los tests de barrera.'
            ),
            "test_trigger_barrier_rechaza_gate_id_desconocido": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Con los mocks de hardware, verifica que trigger_barrier('TYP0', ...) lanza HTTPException 400 al no reconocer el portón."
            ),
            "test_trigger_barrier_sigue_funcionando_con_gate_id_valido": (
                '💡 LA IDEA: Comprobar el escenario de trigger barrier sigue funcionando con gate id valido.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Con los mocks de hardware, verifica que trigger_barrier('EGRESO', 'OPEN') resuelve el portón a SALIDA y devuelve el comando OPEN."
            ),
        },
    },
    "tests/test_cameras_routes.py": {
        "proposito": 'Suite grande de routes/system/cameras.py y de los helpers de routes/system/common.py: configuración de fuente por gate, control del servicio ALPR (start/stop por gate y por cámara dinámica), CRUD y reordenamiento de cámaras, streaming de consola del subproceso por WebSocket, el aviso de lectura al dashboard y el broadcast de consola/frames. Usa dobles de subproceso, hilo, loop y WebSocket, monta una app FastAPI mínima con el router de cámaras y una base SQLite en memoria con dos sedes.',
        "simbolos": {
            "FakeUser": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de usuario autenticado que solo guarda rol y sucursal; los tests lo inyectan como usuario operativo para probar permisos por sede.'
            ),
            "FakeUser.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el rol (por defecto ADMIN) y la sucursal (por defecto None) del usuario simulado.'
            ),
            "FakeStream": (
                '💡 LA IDEA: Comprobar el escenario de FakeStream.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Doble del stdout de un subproceso: entrega líneas con readline hasta devolver b'' (centinela de fin) o lanzar la excepción configurada, y registra si se cerró."
            ),
            "FakeStream.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeStream.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Copia la lista de líneas, guarda la excepción opcional a lanzar y marca closed en False.'
            ),
            "FakeStream.readline": (
                '💡 LA IDEA: Comprobar el escenario de FakeStream.readline.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve la siguiente línea pendiente; si hay excepción configurada la lanza, y si no quedan líneas devuelve b'' indicando fin de stream."
            ),
            "FakeStream.close": (
                '💡 LA IDEA: Comprobar el escenario de FakeStream.close.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca el stream como cerrado (closed = True).'
            ),
            "FakeProc": (
                '💡 LA IDEA: Comprobar el escenario de FakeProc.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de subprocess.Popen que acumula todas las instancias creadas y expone poll/terminate para simular el ciclo de vida del proceso ALPR.'
            ),
            "FakeProc.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeProc.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda cmd, env, stdout (FakeStream si no se pasa), stderr y flags; inicializa poll_ret, exc_poll, un pid fijo, terminated en 0 y se agrega a la lista de instancias.'
            ),
            "FakeProc.poll": (
                '💡 LA IDEA: Comprobar el escenario de FakeProc.poll.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve poll_ret (normalmente None mientras corre) o lanza RuntimeError('poll boom') si exc_poll está activado; simula que un proceso sigue vivo o ya terminó."
            ),
            "FakeProc.terminate": (
                '💡 LA IDEA: Comprobar el escenario de FakeProc.terminate.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Incrementa el contador terminated, simulando el cierre del proceso en sistemas POSIX.'
            ),
            "FakeThread": (
                '💡 LA IDEA: Comprobar el escenario de FakeThread.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de threading.Thread que registra las instancias y si fueron arrancadas, para inspeccionar el hilo que lee la consola del subproceso.'
            ),
            "FakeThread.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeThread.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda target, args y kwargs, marca started en False y se registra en la lista de instancias.'
            ),
            "FakeThread.start": (
                '💡 LA IDEA: Comprobar el escenario de FakeThread.start.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca started en True sin ejecutar el target (no lanza hilos reales).'
            ),
            "FakeLoop": (
                '💡 LA IDEA: Comprobar el escenario de FakeLoop.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble del event loop de NotificationService que permite simular un loop corriendo, detenido o que falla al consultar is_running.'
            ),
            "FakeLoop.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeLoop.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda si el loop está corriendo y si debe lanzar excepción al consultarlo.'
            ),
            "FakeLoop.is_running": (
                '💡 LA IDEA: Comprobar el escenario de FakeLoop.is running.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve el estado configurado o lanza RuntimeError('loop caido') si exc está activo."
            ),
            "node_secret": (
                '💡 LA IDEA: Comprobar el escenario de node secret.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                "⚙️ FUNCIONAMIENTO: Fija settings.ALPR_NODE_SECRET en 's3cret' y lo devuelve, para probar el aviso de lectura autenticado por nodo."
            ),
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Principal: crea un engine SQLite en memoria con las tablas y dos sucursales ('Centro','Sur'), arma una app FastAPI con el router de cámaras, sobrescribe get_db y get_operational_user (usa CURRENT), limpia CAMERA_PROCESSES y entrega un TestClient junto al sessionmaker; al salir limpia overrides y procesos."
            ),
            "_set_staff": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _set_staff.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia el usuario operativo actual a un FakeUser de rol STAFF (por defecto) con la sucursal indicada, para probar restricciones por sede.'
            ),
            "_reset_staff": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reset_staff.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Tras cada test restablece el usuario actual a un FakeUser admin por defecto.'
            ),
            "_seed_camera": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_camera.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta una ParkingCamera con los campos indicados (nombre, tipo, source, sucursal, activa, orden y, opcionalmente, un id forzado); devuelve la cámara con el id ya cargado.'
            ),
            "_seed_setting": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_setting.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un Settings con clave, valor_str y sucursal opcionales; devuelve el setting ya refrescado. Se usa para sembrar la fuente de cámara (CAMERA_SOURCE_...).'
            ),
            "_get_setting": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _get_setting.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca y devuelve el primer Settings con la clave indicada, cerrando la sesión; permite verificar lo que persistió set_camera_config.'
            ),
            "_proc_id_of": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _proc_id_of.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Calcula el identificador de proceso de una cámara como '{SUCURSAL_NORMALIZADA}_{TIPO}_{ID}' en mayúsculas (GLOBAL si no tiene sucursal); es la clave con que CAMERA_PROCESSES indexa los subprocesos."
            ),
            "_set_running": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _set_running.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra en CAMERA_PROCESSES un FakeProc bajo el proc_id de la cámara para simular que su servicio ALPR está corriendo; permite además marcar exc_poll.'
            ),
            "_dummy_coro": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _dummy_coro.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Coroutine trivial de prueba que devuelve None, usada para verificar _schedule_async sin ejecutar trabajo real.'
            ),
            "test_schedule_async_loop_corriendo_programa_coro": (
                '💡 LA IDEA: Comprobar el escenario de schedule async loop corriendo programa coro.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un loop corriendo y run_coroutine_threadsafe parcheado, verifica que _schedule_async devuelve True y deja la coroutine programada en el loop.'
            ),
            "test_schedule_async_loop_no_corriendo_devuelve_false": (
                '💡 LA IDEA: Comprobar el escenario de schedule async loop no corriendo devuelve false.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con el loop detenido, verifica que _schedule_async devuelve False.'
            ),
            "test_schedule_async_sin_loop_devuelve_false": (
                '💡 LA IDEA: Comprobar el escenario de schedule async sin loop devuelve false.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin loop (None), verifica que _schedule_async devuelve False.'
            ),
            "test_schedule_async_excepcion_devuelve_false": (
                '💡 LA IDEA: Comprobar el escenario de schedule async excepcion devuelve false.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si consultar is_running lanza excepción, verifica que _schedule_async la captura y devuelve False.'
            ),
            "test_stream_console_envia_linea_por_websocket": (
                '💡 LA IDEA: Comprobar el escenario de stream console envia linea por websocket.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con un proceso cuyo stdout entrega una línea y luego b'', verifica que _stream_console_output programa exactamente una coroutine de envío y deja stdout en None al cerrar."
            ),
            "test_stream_console_lineas_vacias_no_reenvian": (
                '💡 LA IDEA: Comprobar el escenario de stream console lineas vacias no reenvian.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con líneas vacías, verifica que no se programa ningún envío y que igualmente se limpia stdout.'
            ),
            "test_stream_console_decode_con_errores_replace": (
                '💡 LA IDEA: Comprobar el escenario de stream console decode con errores replace.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con bytes inválidos (ÿþ), verifica que el decode con errors='replace' no rompe y se programa el envío de la línea saneada."
            ),
            "test_stream_console_error_de_lectura_no_propaga": (
                '💡 LA IDEA: Comprobar el escenario de stream console error de lectura no propaga.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si readline lanza excepción, verifica que _stream_console_output la absorbe y limpia stdout.'
            ),
            "ProcStdoutNoAsignable": (
                '💡 LA IDEA: Comprobar el escenario de ProcStdoutNoAsignable.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de proceso cuyo atributo stdout es de solo lectura: el setter lanza AttributeError, para forzar el camino del finally que intenta reasignar stdout.'
            ),
            "ProcStdoutNoAsignable.__init__": (
                '💡 LA IDEA: Comprobar el escenario de ProcStdoutNoAsignable.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el stream interno en _s.'
            ),
            "ProcStdoutNoAsignable.stdout": (
                '💡 LA IDEA: Comprobar el escenario de ProcStdoutNoAsignable.stdout.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Property de lectura que devuelve el stream interno y setter que lanza AttributeError('readonly') al intentar reasignarlo; así el test cubre el except del finally."
            ),
            "test_stream_console_finally_no_asignable_no_propaga": (
                '💡 LA IDEA: Comprobar el escenario de stream console finally no asignable no propaga.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un proceso cuyo stdout no se puede reasignar y cuya lectura falla, verifica que _stream_console_output no propaga el AttributeError y el stdout sigue presente.'
            ),
            "test_get_camera_config_admin_sin_setting": (
                '💡 LA IDEA: Comprobar el escenario de get camera config admin sin setting.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Sin setting guardado, verifica que GET /camera-config/centro_1 devuelve 200 con gate_id en mayúsculas, source '0' por defecto e is_running False."
            ),
            "test_get_camera_config_con_setting": (
                '💡 LA IDEA: Comprobar el escenario de get camera config con setting.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un setting CAMERA_SOURCE_CENTRO_1 sembrado, verifica que la config devuelve ese source, no corre y normaliza el gate_id.'
            ),
            "test_get_camera_config_proceso_corriendo": (
                '💡 LA IDEA: Comprobar el escenario de get camera config proceso corriendo.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un proceso registrado bajo CENTRO_1, verifica que is_running es True.'
            ),
            "test_get_camera_config_staff_misma_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de get camera config staff misma sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Centro', verifica que puede leer la config de CENTRO_1 (200)."
            ),
            "test_get_camera_config_staff_otra_sucursal_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Centro', verifica que leer la config de OTRA_1 devuelve 403."
            ),
            "test_get_camera_config_staff_sin_sucursal_pasa": (
                '💡 LA IDEA: Comprobar el escenario de get camera config staff sin sucursal pasa.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Con staff sin sucursal, verifica que puede leer cualquier config (200).'
            ),
            "test_set_camera_config_admin_crea_setting": (
                '💡 LA IDEA: Comprobar el escenario de set camera config admin crea setting.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que POST /camera-config crea el setting CAMERA_SOURCE_CENTRO_1 con el source pedido y responde el mensaje de guardado.'
            ),
            "test_set_camera_config_admin_actualiza_existente": (
                '💡 LA IDEA: Comprobar el escenario de set camera config admin actualiza existente.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con un setting previo en '0', verifica que actualizar el source a '2' modifica el valor existente en vez de duplicar."
            ),
            "test_set_camera_config_staff_mismo_prefijo_ok": (
                '💡 LA IDEA: Comprobar el escenario de set camera config staff mismo prefijo ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Centro', verifica que puede guardar la config de CENTRO_2 (mismo prefijo de sede) con 200."
            ),
            "test_set_camera_config_staff_otro_prefijo_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Centro', verifica que guardar la config de OTRA_2 devuelve 403."
            ),
            "test_control_start_ya_en_ejecucion_error": (
                '💡 LA IDEA: Comprobar el escenario de control start ya en ejecucion error.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con un proceso ya registrado para CENTRO_1, verifica que /camera-service/CENTRO_1/start responde error 'Ya está en ejecución'."
            ),
            "test_control_start_qr_configura_gate_type_qr": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Con Popen y Thread parcheados y un setting de fuente para la cámara QR, verifica que al arrancar el servicio se arma el entorno del subproceso (GATE_ID, VIDEO_SOURCE, GATE_TYPE 'qr', BACKEND_URL, PYTHONUNBUFFERED), se registra el proceso, se lanza el hilo lector y el cmd incluye alpr_service.py."
            ),
            "test_control_start_entrada_y_salida_determinan_gate_type": (
                '💡 LA IDEA: Comprobar el escenario de control start entrada y salida determinan gate type.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que el GATE_TYPE del subproceso se deriva del nombre del gate: 'entrada' para CENTRO_ENTRADA_1 y 'salida' para CENTRO_SALIDA_1."
            ),
            "test_control_start_error_de_popen": (
                '💡 LA IDEA: Comprobar el escenario de control start error de popen.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Si Popen lanza excepción, verifica que el endpoint responde error con el mensaje y no deja el proceso registrado.'
            ),
            "test_control_stop_no_en_ejecucion_error": (
                '💡 LA IDEA: Comprobar el escenario de control stop no en ejecucion error.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Sin proceso corriendo, verifica que /camera-service/CENTRO_1/stop responde error 'No está en ejecución'."
            ),
            "test_control_stop_nt_taskkill": (
                '💡 LA IDEA: Comprobar el escenario de control stop nt taskkill.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: En Windows (os.name 'nt'), verifica que detener el servicio mata el proceso con taskkill y lo saca de CAMERA_PROCESSES."
            ),
            "test_control_stop_posix_terminate": (
                '💡 LA IDEA: Comprobar el escenario de control stop posix terminate.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: En POSIX, verifica que detener el servicio llama terminate() una vez y quita el proceso del registro.'
            ),
            "test_control_stop_fin_proceso_sin_detener": (
                '💡 LA IDEA: Comprobar el escenario de control stop fin proceso sin detener.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un proceso cuyo poll ya devuelve 0 (terminado), verifica que el stop no intenta matarlo y responde ok.'
            ),
            "test_control_stop_excepcion_error": (
                '💡 LA IDEA: Comprobar el escenario de control stop excepcion error.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Si poll lanza excepción al detener, verifica que el endpoint responde error con el mensaje de la excepción.'
            ),
            "test_control_accion_invalida": (
                '💡 LA IDEA: Comprobar el escenario de control accion invalida.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que una acción no soportada ('reboot') responde error 'Acción no válida'."
            ),
            "test_control_staff_otra_sucursal_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Centro', verifica que operar el gate OTRA_1 devuelve 403."
            ),
            "test_get_cameras_admin_ve_todas_y_proceso_corriendo": (
                '💡 LA IDEA: Comprobar el escenario de get cameras admin ve todas y proceso corriendo.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin lista todas las cámaras sin importar sede y se marca is_running según CAMERA_PROCESSES (True solo para la que tiene proceso).'
            ),
            "test_get_cameras_staff_solo_su_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de get cameras staff solo su sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Centro', verifica que solo lista las cámaras de su sede."
            ),
            "test_get_cameras_staff_sin_sucursal_todas": (
                '💡 LA IDEA: Comprobar el escenario de get cameras staff sin sucursal todas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Con staff sin sucursal, verifica que ve todas las cámaras.'
            ),
            "test_get_cameras_vacio": (
                '💡 LA IDEA: Comprobar el escenario de get cameras vacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin cámaras, verifica que GET /cameras devuelve una lista vacía.'
            ),
            "test_get_cameras_respeta_orden_manual": (
                '💡 LA IDEA: Comprobar el escenario de get cameras respeta orden manual.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con órdenes 3,1,2, verifica que el listado se ordena por el campo orden (ids 2,3,1) y respeta ese orden.'
            ),
            "test_get_cameras_orden_null_va_al_final": (
                '💡 LA IDEA: Comprobar el escenario de get cameras orden null va al final.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que las cámaras con orden nulo quedan al final del listado.'
            ),
            "test_reorder_cameras_admin_asigna_orden_secuencial": (
                '💡 LA IDEA: Comprobar el escenario de reorder cameras admin asigna orden secuencial.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que PUT /cameras/order reasigna el campo orden de forma secuencial según la lista de ids enviada (3,1,2 -> orden 1,2,3) y el listado refleja ese orden.'
            ),
            "test_reorder_cameras_id_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Si la lista incluye un id inexistente, verifica que el reordenamiento devuelve 404.'
            ),
            "test_reorder_cameras_staff_misma_sucursal_ok": (
                '💡 LA IDEA: Comprobar el escenario de reorder cameras staff misma sucursal ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Centro', verifica que puede reordenar cámaras de su sede (200) y el orden se aplica."
            ),
            "test_reorder_cameras_staff_otra_sucursal_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Centro', verifica que reordenar una cámara de 'Sur' devuelve 403."
            ),
            "test_create_camera_admin_usa_sucursal_del_payload": (
                '💡 LA IDEA: Comprobar el escenario de create camera admin usa sucursal del payload.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin crea una cámara: verifica que se guarda con el tipo en mayúsculas, la sucursal indicada en el payload, is_running False y un id asignado.'
            ),
            "test_create_camera_staff_fuerza_su_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de create camera staff fuerza su sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Centro', verifica que al crear una cámara se fuerza su propia sede ignorando la sucursal enviada en el payload."
            ),
            "test_update_camera_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar una cámara inexistente devuelve 404.'
            ),
            "test_update_camera_staff_otra_sucursal_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Sur', verifica que actualizar una cámara de 'Centro' devuelve 403."
            ),
            "test_update_camera_admin_ok_con_is_running": (
                '💡 LA IDEA: Comprobar el escenario de update camera admin ok con is running.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin actualiza nombre, tipo, source y activa de una cámara: verifica que persisten los cambios (tipo en mayúsculas) y que is_running refleja el proceso registrado con el nuevo tipo.'
            ),
            "test_update_camera_staff_no_permite_cambiar_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de update camera staff no permite cambiar sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Centro', verifica que aunque envíe sucursal 'Sur', la cámara conserva 'Centro'."
            ),
            "test_delete_camera_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Eliminar una cámara inexistente devuelve 404.'
            ),
            "test_delete_camera_staff_otra_sucursal_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Sur', verifica que borrar una cámara de 'Centro' devuelve 403."
            ),
            "test_delete_camera_sin_proceso": (
                '💡 LA IDEA: Comprobar el escenario de delete camera sin proceso.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina una cámara sin proceso corriendo: verifica el mensaje de éxito y que la fila desapareció de la base.'
            ),
            "test_delete_camera_con_proceso_nt_taskkill": (
                '💡 LA IDEA: Comprobar el escenario de delete camera con proceso nt taskkill.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: En Windows, verifica que al borrar una cámara con servicio corriendo se mata el proceso con taskkill y se quita del registro.'
            ),
            "test_delete_camera_con_proceso_posix_terminate": (
                '💡 LA IDEA: Comprobar el escenario de delete camera con proceso posix terminate.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: En POSIX, verifica que al borrar la cámara se llama terminate() y se quita el proceso del registro.'
            ),
            "test_delete_camera_proceso_con_error_en_poll": (
                '💡 LA IDEA: Comprobar el escenario de delete camera proceso con error en poll.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si poll lanza excepción al borrar, verifica que la cámara igual se elimina sin romper y el proceso se quita del registro.'
            ),
            "test_dynamic_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Controlar una cámara dinámica inexistente devuelve 404.'
            ),
            "test_dynamic_staff_otra_sucursal_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con staff de 'Sur', verifica que controlar una cámara de 'Centro' devuelve 403."
            ),
            "test_dynamic_start_ya_en_ejecucion_error": (
                '💡 LA IDEA: Comprobar el escenario de dynamic start ya en ejecucion error.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con el proceso de la cámara ya corriendo, verifica que el start de la cámara dinámica responde 'Ya está en ejecución'."
            ),
            "test_dynamic_start_qr": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Arranca el servicio de una cámara tipo QR: verifica el mensaje de éxito y que el entorno del subproceso lleva GATE_ID (proc_id), VIDEO_SOURCE y GATE_TYPE 'qr'."
            ),
            "test_dynamic_start_egreso_gate_type_salida": (
                '💡 LA IDEA: Comprobar el escenario de dynamic start egreso gate type salida.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Una cámara tipo EGRESO genera GATE_TYPE 'salida' al arrancar su servicio."
            ),
            "test_dynamic_start_patente_gate_type_entrada": (
                '💡 LA IDEA: Comprobar el escenario de dynamic start patente gate type entrada.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Una cámara tipo PATENTE genera GATE_TYPE 'entrada'."
            ),
            "test_dynamic_start_tipo_default": (
                '💡 LA IDEA: Comprobar el escenario de dynamic start tipo default.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Un tipo desconocido ('OTRO') genera GATE_TYPE 'otro' (fallback en minúsculas)."
            ),
            "test_dynamic_start_error_de_popen": (
                '💡 LA IDEA: Comprobar el escenario de dynamic start error de popen.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Si Popen falla al arrancar la cámara dinámica, verifica que responde error con el mensaje y no registra el proceso.'
            ),
            "test_dynamic_stop_no_en_ejecucion_error": (
                '💡 LA IDEA: Comprobar el escenario de dynamic stop no en ejecucion error.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Detener una cámara dinámica sin proceso corriendo responde 'No está en ejecución'."
            ),
            "test_dynamic_stop_nt": (
                '💡 LA IDEA: Comprobar el escenario de dynamic stop nt.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: En Windows, detener la cámara dinámica mata el proceso con taskkill y lo quita del registro.'
            ),
            "test_dynamic_stop_posix": (
                '💡 LA IDEA: Comprobar el escenario de dynamic stop posix.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: En POSIX, detener la cámara dinámica llama terminate() y responde ok.'
            ),
            "test_dynamic_stop_proceso_ya_fin": (
                '💡 LA IDEA: Comprobar el escenario de dynamic stop proceso ya fin.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con el proceso ya terminado (poll 0), el stop responde ok sin llamar terminate().'
            ),
            "test_dynamic_stop_excepcion": (
                '💡 LA IDEA: Comprobar el escenario de dynamic stop excepcion.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Si poll lanza excepción al detener, responde error con el mensaje.'
            ),
            "test_dynamic_accion_invalida": (
                '💡 LA IDEA: Comprobar el escenario de dynamic accion invalida.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Una acción no soportada ('pause') responde error 'Acción no válida'."
            ),
            "_capture_set_last_event": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _capture_set_last_event.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Parchea NotificationService.set_last_event para capturar en una lista las tuplas (sucursal, tipo, patente, mensaje, estado) que emite el aviso de lectura.'
            ),
            "FakeBranch": (
                '💡 LA IDEA: Comprobar el escenario de FakeBranch.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble mínimo de sucursal que solo expone el atributo nombre, usado para simular BranchRepository.get_all.'
            ),
            "FakeBranch.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeBranch.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el nombre de la sucursal simulada.'
            ),
            "test_reading_403_sin_secret": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin header de secreto, verifica que POST /camera-reading/CENTRO_1 devuelve 403.'
            ),
            "test_reading_403_secret_invalido": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un secreto inválido, verifica que el aviso de lectura devuelve 403.'
            ),
            "test_reading_con_sucursal_matcheada": (
                '💡 LA IDEA: Comprobar el escenario de reading con sucursal matcheada.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Con secreto válido y una sucursal que coincide con el prefijo del gate, verifica que el aviso de lectura responde ok y emite un set_last_event con la sucursal 'Centro' y estado 'reading'."
            ),
            "test_reading_sin_match_de_sucursal_global": (
                '💡 LA IDEA: Comprobar el escenario de reading sin match de sucursal global.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                "⚙️ FUNCIONAMIENTO: Si ninguna sucursal coincide con el prefijo, verifica que el aviso se registra bajo 'GLOBAL'."
            ),
            "test_reading_excepcion_de_repositorio_global": (
                '💡 LA IDEA: Comprobar el escenario de reading excepcion de repositorio global.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                "⚙️ FUNCIONAMIENTO: Si BranchRepository.get_all lanza excepción, verifica que el aviso cae a 'GLOBAL' sin romper."
            ),
            "test_reading_gate_sin_guion_bajo_global": (
                '💡 LA IDEA: Comprobar el escenario de reading gate sin guion bajo global.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Con un gate sin guion bajo (p. ej. 'GLOBALCAM'), verifica que el aviso se registra bajo 'GLOBAL' sin fallar."
            ),
            "test_stop_all_cameras_nt_taskkill": (
                '💡 LA IDEA: Comprobar el escenario de stop all cameras nt taskkill.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: En Windows, stop_all_cameras mata todos los procesos con taskkill y deja CAMERA_PROCESSES vacío.'
            ),
            "test_stop_all_cameras_posix_terminate": (
                '💡 LA IDEA: Comprobar el escenario de stop all cameras posix terminate.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: En POSIX, stop_all_cameras llama terminate() en cada proceso y vacía el registro.'
            ),
            "test_stop_all_cameras_ignora_error_por_camara": (
                '💡 LA IDEA: Comprobar el escenario de stop all cameras ignora error por camara.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Aunque una cámara falle al matarse (poll o kill), verifica que stop_all_cameras sigue con las demás y deja el registro vacío.'
            ),
            "FakeWS": (
                '💡 LA IDEA: Comprobar el escenario de FakeWS.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de WebSocket que acumula los textos enviados y puede lanzar una excepción configurada para simular un socket caído.'
            ),
            "FakeWS.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeWS.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa la lista de mensajes enviados y la excepción opcional.'
            ),
            "FakeWS.send_text": (
                '💡 LA IDEA: Comprobar el escenario de FakeWS.send text.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrega el texto a los enviados o lanza la excepción configurada.'
            ),
            "test_broadcast_console_sin_conexiones_no_envia": (
                '💡 LA IDEA: Comprobar el escenario de broadcast console sin conexiones no envia.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin conexiones suscritas, verifica que broadcast_console no falla ni envía nada.'
            ),
            "test_broadcast_console_envia_payload_json": (
                '💡 LA IDEA: Comprobar el escenario de broadcast console envia payload json.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un WebSocket suscrito, verifica que broadcast_console envía el payload JSON con la marca __console__, el gate y la línea.'
            ),
            "test_broadcast_console_error_desconecta": (
                '💡 LA IDEA: Comprobar el escenario de broadcast console error desconecta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el envío falla, verifica que el WebSocket se elimina de las conexiones activas.'
            ),
            "test_broadcast_frame_actualiza_ultimo_y_envia": (
                '💡 LA IDEA: Comprobar el escenario de broadcast frame actualiza ultimo y envia.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que broadcast_frame guarda el frame como último del gate y lo envía al WebSocket suscrito.'
            ),
            "test_broadcast_frame_error_desconecta_y_sigue": (
                '💡 LA IDEA: Comprobar el escenario de broadcast frame error desconecta y sigue.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un socket caído y otro sano, verifica que el caído se elimina y el sano sigue recibiendo.'
            ),
            "test_disconnect_sin_conexion_no_rompe": (
                '💡 LA IDEA: Comprobar el escenario de disconnect sin conexion no rompe.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que disconnect es tolerante a gates sin conexiones o inexistentes, sin lanzar excepción.'
            ),
            "test_console_encoding_fallback_utf8": (
                '💡 LA IDEA: Comprobar el escenario de console encoding fallback utf8.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Si locale.getpreferredencoding lanza excepción al recargar el módulo, verifica que _console_encoding cae al fallback 'utf-8'."
            ),
        },
    },
    "tests/test_config_version.py": {
        "proposito": "Cobertura de _version() en core/config.py, que deriva la versión de la app del historial de git en vez de un valor fijo. Prueba los dos estilos de subject usados en el repo (canónico 'v9.34.79: ...' e incidental 'refactor(v9.34.17): ...'), el retroceso en el historial cuando HEAD no trae versión, la prioridad del canónico, las degradaciones a la versión de fallback y el cacheo.",
        "simbolos": {
            "_Result": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _Result.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de subprocess.CompletedProcess cuyo atributo stdout puede lanzar CalledProcessError, para simular que git falla justo al leerse la salida.'
            ),
            "_Result.__init__": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _Result.__init__.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda la salida simulada y si debe lanzar excepción al acceder a stdout.'
            ),
            "_Result.stdout": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _Result.stdout.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Property que lanza CalledProcessError si raise_exc está activo o devuelve la salida configurada.'
            ),
            "_clear_cache": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _clear_cache.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Limpia el cache de _version antes y después de cada test para que no se filtre entre casos.'
            ),
            "_fake_history": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _fake_history.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Parchea config.subprocess.run para devolver la lista de subjects recibida (como salida de git log) y registra los comandos invocados; puede forzar la excepción.'
            ),
            "test_lee_version_canonica_de_head": (
                '💡 LA IDEA: Comprobar el escenario de lee version canonica de head.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con un subject canónico en HEAD, verifica que _version extrae '9.34.79'."
            ),
            "test_acepta_subject_sin_espacio_tras_los_dos_puntos": (
                '💡 LA IDEA: Comprobar el escenario de acepta subject sin espacio tras los dos puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que el parser acepta 'v9.34.80:algo' sin espacio tras los dos puntos."
            ),
            "test_retrocede_cuando_head_no_lleva_version": (
                '💡 LA IDEA: Comprobar el escenario de retrocede cuando head no lleva version.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con HEAD sin versión (fix/wip), verifica que _version retrocede hasta encontrar '9.34.77' en vez de quedar en 0.0.0."
            ),
            "test_retrocede_por_varios_commits_sin_version": (
                '💡 LA IDEA: Comprobar el escenario de retrocede por varios commits sin version.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con varios commits sin versión (merge, fix, docs), verifica que retrocede hasta el '9.34.74' canónico."
            ),
            "test_acepta_version_incidental_en_parentesis": (
                '💡 LA IDEA: Comprobar el escenario de acepta version incidental en parentesis.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que reconoce la versión incidental de un subject tipo 'refactor(v9.34.17): ...' extrayendo '9.34.17'."
            ),
            "test_acepta_fix_con_version_incidental": (
                '💡 LA IDEA: Comprobar el escenario de acepta fix con version incidental.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que un subject 'fix(v9.21.0): ...' también expone la versión incidental '9.21.0'."
            ),
            "test_canonico_gana_sobre_mencion_incidental_mas_antigua": (
                '💡 LA IDEA: Comprobar el escenario de canonico gana sobre mencion incidental mas antigua.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con una mención incidental más antigua (revert(v9.30.0)) y un canónico vigente, verifica que gana el canónico '9.34.79'."
            ),
            "test_devuelve_fallback_si_git_falla": (
                '💡 LA IDEA: Comprobar el escenario de devuelve fallback si git falla.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si git falla (stdout lanza), verifica que _version devuelve _FALLBACK_VERSION.'
            ),
            "test_devuelve_fallback_si_historial_vacio": (
                '💡 LA IDEA: Comprobar el escenario de devuelve fallback si historial vacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con historial vacío, verifica que _version devuelve el fallback.'
            ),
            "test_devuelve_fallback_si_ningun_commit_menciona_version": (
                '💡 LA IDEA: Comprobar el escenario de devuelve fallback si ningun commit menciona version.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si ningún commit menciona una versión, verifica que devuelve el fallback.'
            ),
            "test_ignora_lines_vacias": (
                '💡 LA IDEA: Comprobar el escenario de ignora lines vacias.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con líneas vacías o en blanco alrededor, verifica que el parser las ignora y encuentra '9.34.70'."
            ),
            "test_pide_una_ventana_de_commits_limitada": (
                '💡 LA IDEA: Comprobar el escenario de pide una ventana de commits limitada.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que el comando de git log pide una ventana limitada (-50) y no el historial completo (-1 ausente).'
            ),
            "test_settings_expone_la_forma_del_dato": (
                '💡 LA IDEA: Comprobar el escenario de settings expone la forma del dato.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que config.Settings.VERSION tiene formato de dos puntos (dos separadores '.'), es decir X.Y.Z."
            ),
            "test_cache_evita_reinvocar_git": (
                '💡 LA IDEA: Comprobar el escenario de cache evita reinvocar git.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Llama _version tres veces y verifica que git solo se invocó una vez, confirmando el cache.'
            ),
        },
    },
    "tests/test_core_database.py": {
        "proposito": 'Cobertura de core/database.py: normalización de URLs de base de datos, creación de tablas con init_db y las ramas de sync_schema (alembic no disponible, ya en head, upgrade exitoso, upgrade fallido rescatado con stamp y fallo total con re-raise). Parchea las piezas de alembic para no tocar una base real.',
        "simbolos": {
            "mem_engine": (
                '💡 LA IDEA: Comprobar el escenario de mem engine.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un engine SQLite en memoria (StaticPool) y lo inyecta como core_db.engine mediante monkeypatch; al salir lo libera.'
            ),
            "_patch_alembic": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _patch_alembic.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Parchea Config, ScriptDirectory.from_config, MigrationContext.configure y las funciones upgrade/stamp de alembic con dobles, registrando las revisiones migradas/fijadas; permite simular cada rama de sync_schema (heads, revisión actual y fallos opcionales).'
            ),
            "test_normalize_url_vacia_devuelve_sqlite": (
                '💡 LA IDEA: Comprobar el escenario de normalize url vacia devuelve sqlite.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que una URL vacía o None se normaliza a sqlite:///./parking.db.'
            ),
            "test_normalize_postgres_a_psycopg": (
                '💡 LA IDEA: Comprobar el escenario de normalize postgres a psycopg.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que una URL postgresql:// se reescribe a postgresql+psycopg:// para usar el driver correcto.'
            ),
            "test_normalize_respeta_urls_ya_normalizadas": (
                '💡 LA IDEA: Comprobar el escenario de normalize respeta urls ya normalizadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que las URLs ya normalizadas (postgresql+psycopg, sqlite, sqlite+pysqlite) se devuelven sin cambios.'
            ),
            "test_init_db_crea_tablas": (
                '💡 LA IDEA: Comprobar el escenario de init db crea tablas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Tras init_db(), verifica que la base contiene las tablas users, parking_branches y access_logs.'
            ),
            "test_sync_schema_sin_alembic_devuelve_false": (
                '💡 LA IDEA: Comprobar el escenario de sync schema sin alembic devuelve false.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la estructura de tablas y columnas en la base de datos coincida perfectamente con los modelos del código.\n\n'
                '⚙️ FUNCIONAMIENTO: Si construir el Config de alembic falla (sin alembic.ini), verifica que sync_schema devuelve False sin migrar.'
            ),
            "test_sync_schema_ya_en_head_no_migra": (
                '💡 LA IDEA: Comprobar el escenario de sync schema ya en head no migra.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la estructura de tablas y columnas en la base de datos coincida perfectamente con los modelos del código.\n\n'
                '⚙️ FUNCIONAMIENTO: Si la revisión actual coincide con el head, verifica que sync_schema devuelve True y no llama a upgrade ni stamp.'
            ),
            "test_sync_schema_upgrade_exitoso": (
                '💡 LA IDEA: Comprobar el escenario de sync schema upgrade exitoso.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la estructura de tablas y columnas en la base de datos coincida perfectamente con los modelos del código.\n\n'
                "⚙️ FUNCIONAMIENTO: Si la revisión actual es None, verifica que sync_schema hace upgrade a 'head', no hace stamp y devuelve True."
            ),
            "test_sync_schema_upgrade_falla_stamp_rescata": (
                '💡 LA IDEA: Comprobar el escenario de sync schema upgrade falla stamp rescata.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la estructura de tablas y columnas en la base de datos coincida perfectamente con los modelos del código.\n\n'
                "⚙️ FUNCIONAMIENTO: Si el upgrade lanza 'no reproducible', verifica que sync_schema hace stamp a 'head' de rescate y devuelve True igualmente."
            ),
            "test_sync_schema_upgrade_y_stamp_fallan_re_raise": (
                '💡 LA IDEA: Comprobar el escenario de sync schema upgrade y stamp fallan re raise.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la estructura de tablas y columnas en la base de datos coincida perfectamente con los modelos del código.\n\n'
                "⚙️ FUNCIONAMIENTO: Si tanto upgrade como stamp fallan, verifica que sync_schema propaga la excepción del stamp ('stamp imposible')."
            ),
        },
    },
    "tests/test_core_seed.py": {
        "proposito": 'Cobertura de core/seed.py, el orquestador de datos maestros que corre init_db.py: crea usuarios, aforo global, tarifas, promociones y la red de sucursales, y debe ser idempotente. Verifica la creación de los cuatro usuarios con password hasheado, que no se duplica nada al re-correr, la normalización del DNI de un usuario preexistente y que no pisa aforo/tarifas/promos/sucursales ya cargados.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea las tablas sobre un engine SQLite en memoria compartido, abre una sesión, la entrega y al salir la cierra y borra las tablas.'
            ),
            "test_crea_los_cuatro_usuarios_iniciales": (
                '💡 LA IDEA: Comprobar el escenario de crea los cuatro usuarios iniciales.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Tras el seed, verifica que existen exactamente los emails de INITIAL_USERS, que el admin tiene rol 'admin' y sucursal None, que su password_hash está hasheado (no es 'admin123' ni lo contiene) y que su DNI se guarda sin puntos ('00000001')."
            ),
            "test_password_hash_es_verificable_por_el_mismo_sistema": (
                '💡 LA IDEA: Comprobar el escenario de password hash es verificable por el mismo sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que el hash generado por el seed sirve para el login real: verify_password acepta 'admin123' y rechaza una clave incorrecta."
            ),
            "test_crea_aforo_global_y_tarifas": (
                '💡 LA IDEA: Comprobar el escenario de crea aforo global y tarifas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que se crea un ParkingAforo global (sucursal None) con capacidad_total 20, ocupación 0, motos 10, camionetas 5 y reservas 5, y que existen los Settings globales de DEFAULT_PRICES con sus valores.'
            ),
            "test_carga_promociones_y_red_de_sucursales": (
                '💡 LA IDEA: Comprobar el escenario de carga promociones y red de sucursales.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que se cargan las promociones de INITIAL_PROMOS (Día Libre, Lavado Premium, Café Express) y las 4 sucursales con sus nombres y logo_url por defecto.'
            ),
            "test_es_idempotente_no_duplica_nada": (
                '💡 LA IDEA: Comprobar el escenario de es idempotente no duplica nada.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Corre el seed tres veces y verifica que usuarios, aforo global, settings, promos y sucursales mantienen sus cantidades (no se duplica nada).'
            ),
            "test_normaliza_dni_con_puntos_de_usuario_preexistente": (
                '💡 LA IDEA: Comprobar el escenario de normaliza dni con puntos de usuario preexistente.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                "⚙️ FUNCIONAMIENTO: Con un local_admin preexistente cuyo DNI tiene puntos, verifica que el seed lo normaliza a '11232444' sin crear un usuario duplicado."
            ),
            "test_no_pisa_tarifas_ni_aforo_preexistentes": (
                '💡 LA IDEA: Comprobar el escenario de no pisa tarifas ni aforo preexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un precio_hora y un aforo ya cargados por el operador, verifica que el seed respeta esos valores (9999.0 y capacidad 777 con ocupación 42) y no los sobreescribe.'
            ),
            "test_no_toca_promos_ni_sucursales_ya_cargadas": (
                '💡 LA IDEA: Comprobar el escenario de no toca promos ni sucursales ya cargadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con una promo y una sucursal ya cargadas, verifica que el seed no agrega las suyas: quedan exactamente esos registros del operador.'
            ),
        },
    },
    "tests/test_email_service.py": {
        "proposito": 'Tests del envío SMTP de EmailService mediante un SMTP falso que registra la secuencia de llamadas. Verifican que SMTP_TLS dispare STARTTLS antes del login (necesario para Gmail/Outlook en 587) y que sin credenciales no se intente autenticar, sin abrir conexiones de red reales.',
        "simbolos": {
            "FakeSMTP": (
                '💡 LA IDEA: Comprobar el escenario de FakeSMTP.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que las pruebas fallen por falta de internet o envíen spam a direcciones de ejemplo.\n\n'
                '⚙️ FUNCIONAMIENTO: Neutralizar las conexiones salientes de correo electrónico reemplazando la librería estándar por una simulación.'
            ),
            "FakeSMTP.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeSMTP.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda server y port, inicializa la lista de llamadas y se registra como la última instancia creada.'
            ),
            "FakeSMTP.__enter__": (
                '💡 LA IDEA: Comprobar el escenario de FakeSMTP.  enter  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el propio objeto para usarse como context manager.'
            ),
            "FakeSMTP.__exit__": (
                '💡 LA IDEA: Comprobar el escenario de FakeSMTP.  exit  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: No suprime excepciones (devuelve False).'
            ),
            "FakeSMTP.starttls": (
                '💡 LA IDEA: Comprobar el escenario de FakeSMTP.starttls.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Registra la llamada 'starttls' en la lista de llamadas."
            ),
            "FakeSMTP.login": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Registra la llamada 'login' (autenticación)."
            ),
            "FakeSMTP.sendmail": (
                '💡 LA IDEA: Comprobar el escenario de FakeSMTP.sendmail.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Registra la llamada 'sendmail' (envío efectivo)."
            ),
            "_configurar": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _configurar.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Parchea smtplib.SMTP por FakeSMTP y los settings SMTP_TLS/SMTP_USER/SMTP_PASSWORD/SMTP_FROM según si hay credenciales.'
            ),
            "test_starttls_antes_del_login_cuando_tls_activo": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con TLS activo y credenciales, verifica que la secuencia de llamadas es exactamente starttls, login y sendmail (STARTTLS antes de autenticar).'
            ),
            "test_sin_tls_no_llama_starttls": (
                '💡 LA IDEA: Comprobar el escenario de sin tls no llama starttls.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con TLS desactivado, verifica que no se llama starttls y la secuencia es login y sendmail.'
            ),
            "test_sin_credenciales_no_autentica": (
                '💡 LA IDEA: Comprobar el escenario de sin credenciales no autentica.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con TLS activo pero sin usuario ni password, verifica que no se llama login y la secuencia es starttls y sendmail.'
            ),
        },
    },
    "tests/test_financial_summary_branch.py": {
        "proposito": 'Verifica ReportService.get_financial_summary en sus variantes por sede: un admin general ve el desglose por sucursal activa (excluyendo las inactivas), puede filtrar por una sucursal puntual sin desglose, y un local_admin queda acotado a su propia sede ignorando el branch pedido. Siembra pagos confirmados por sede.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea las tablas, siembra tres sucursales ('Centro','Sede' activas y 'Cerrada' inactiva) con su precio_hora, entrega la sesión y limpia al salir."
            ),
            "_pago": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _pago.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un AccessLog confirmado de ENTRADA con id fijo, patente, sucursal, monto, método, tipo de vehículo y fecha de pago indicados; representa un pago cobrado.'
            ),
            "_admin": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _admin.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve un User admin global (rol 'admin', sucursal None) sin persistirlo, para pasar como usuario en el servicio."
            ),
            "_local": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _local.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve un User local_admin de la sucursal indicada, para probar el acotamiento por sede.'
            ),
            "test_admin_general_desglosa_por_sucursal_activa": (
                '💡 LA IDEA: Comprobar el escenario de admin general desglosa por sucursal activa.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Con tres pagos en dos sedes activas, verifica el total recaudado (7500), el orden del desglose por monto, que la sede inactiva no aparece, y los totales/conteos/efectivo/digital por sede.'
            ),
            "test_admin_general_filtra_por_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de admin general filtra por sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con filtro por 'Sede', verifica que el total corresponde solo a esa sede y que no se incluye el desglose 'por_sucursal'."
            ),
            "test_local_admin_ignora_branch_y_queda_acotado_a_su_sede": (
                '💡 LA IDEA: Comprobar el escenario de local admin ignora branch y queda acotado a su sede.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un local_admin de 'Centro' pide la sucursal 'Sede': verifica que el servicio ignora ese filtro, devuelve solo lo de 'Centro' y sin desglose."
            ),
        },
    },
    "tests/test_inline_styles_guard.py": {
        "proposito": 'Test de regresión del guard de estilos inline: ejecuta _tools/check_inline_styles.py en modo CI y exige código de salida 0. El guard solo falla si un template supera su conteo de estilos inline registrado en el baseline o si uno nuevo trae más de 25.',
        "simbolos": {
            "test_guard_inline_styles_no_regresiones": (
                '💡 LA IDEA: Comprobar el escenario de guard inline styles no regresiones.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Corre el script check_inline_styles.py con el intérprete actual y verifica que su código de retorno sea 0; si falla, muestra stdout+stderr como mensaje de aserción.'
            ),
        },
    },
    "tests/test_mercadopago.py": {
        "proposito": 'Tests del servicio de MercadoPago (services/mercadopago_service.py) sobre una base SQLite en memoria: creación de preferencias de checkout (requisitos de https y credenciales, y creación de intención para estadía) y confirmación de pagos (reserva aprobada sin descuento de saldo, idempotencia, estadía aprobada y pago rechazado). Mockea las llamadas a MP.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea las tablas sobre un engine SQLite en memoria, entrega la sesión y al salir la cierra y borra las tablas.'
            ),
            "_crear_usuario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea y persiste un usuario de rol user con email único (uuid), saldo y puntos indicados; devuelve el usuario refrescado.'
            ),
            "CheckoutSchema": (
                '💡 LA IDEA: Comprobar el escenario de CheckoutSchema.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Stub de schemas.MercadoPagoCheckout que expone tipo, reserva_id, access_log_id y redemption_ticket_id, para aislar el servicio del schema real.'
            ),
            "CheckoutSchema.__init__": (
                '💡 LA IDEA: Comprobar el escenario de CheckoutSchema.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Guarda los cuatro campos del checkout (tipo por defecto 'reserva') en el objeto."
            ),
            "test_create_payment_require_https_base_url": (
                '💡 LA IDEA: Comprobar el escenario de create payment require https base url.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Con BASE_URL http, verifica que create_payment para una reserva lanza HTTPException 400 cuyo detalle menciona 'https' (MP exige back_urls https)."
            ),
            "test_create_payment_require_credentials": (
                '💡 LA IDEA: Comprobar el escenario de create payment require credentials.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin MP_ACCESS_TOKEN, verifica que create_payment lanza HTTPException 503.'
            ),
            "test_create_payment_estadia_creates_intent": (
                '💡 LA IDEA: Comprobar el escenario de create payment estadia creates intent.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Con credenciales y BASE_URL https, verifica que el checkout de una estadía llama a /checkout/preferences, devuelve init_point y monto positivo, y persiste un MercadoPagoPayment PENDIENTE de tipo estadía con payment_id None y external_reference 'AP-ESTADIA-...'."
            ),
            "test_confirm_reserva_approved_no_saldo_deduction": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un pago de reserva y un MP aprobado, verifica que confirm_payment devuelve aplicado True, marca la reserva PAGADA, NO descuenta saldo (sigue 5000), acredita 30 puntos (10 por cada 1000) y actualiza el pago con aplicado True y payment_id.'
            ),
            "test_confirm_payment_idempotent": (
                '💡 LA IDEA: Comprobar el escenario de confirm payment idempotent.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Confirma dos veces el mismo pago: verifica que la segunda confirmación sigue devolviendo aplicado True pero no duplica puntos (quedan 10).'
            ),
            "test_confirm_estadia_approved": (
                '💡 LA IDEA: Comprobar el escenario de confirm estadia approved.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un pago de estadía aprobado, verifica que la confirmación aplica y marca el AccessLog como pagado con método MERCADOPAGO y costo 1500.'
            ),
            "test_confirm_payment_rejected_not_applied": (
                '💡 LA IDEA: Comprobar el escenario de confirm payment rejected not applied.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un pago rechazado por MP, verifica que confirm_payment devuelve aplicado False y deja el MercadoPagoPayment en estado FALLIDO.'
            ),
        },
    },
    "tests/test_mercadopago_webhook.py": {
        "proposito": 'Cobertura del webhook de notificaciones de MercadoPago (POST /v1/user/mercadopago/webhook) y de los redirects de retorno. Verifica el procesamiento de un payment_id válido, la tolerancia a bodies sin id/external_reference, JSON inválido y errores de MP o del confirm, y los redirects success/pending/failure con el mp_status correspondiente.',
        "simbolos": {
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Monta la app real con una base SQLite en memoria (StaticPool), sobrescribe get_db, resetea el limiter y entrega un TestClient junto al sessionmaker; al salir restaura overrides y limiter.'
            ),
            "test_webhook_procesa_pago_confirmado": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con un body type=payment y data.id, verifica que el webhook consulta /v1/payments/PAY-1, llama a confirm_payment con el external_reference devuelto por MP y responde {'status':'ok'}."
            ),
            "test_webhook_soporta_data_id_en_raiz": (
                '💡 LA IDEA: Comprobar el escenario de webhook soporta data id en raiz.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que el body alternativo con data_id en la raíz también se procesa y confirma con ese payment_id.'
            ),
            "test_webhook_sin_payment_id_no_confirma": (
                '💡 LA IDEA: Comprobar el escenario de webhook sin payment id no confirma.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Un evento sin id de pago se acepta con ok sin llamar a MP ni a confirm_payment.'
            ),
            "test_webhook_sin_external_reference_no_confirma": (
                '💡 LA IDEA: Comprobar el escenario de webhook sin external reference no confirma.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si MP no devuelve external_reference, el webhook responde ok sin confirmar (idempotente).'
            ),
            "test_webhook_hay_exception_de_mp_no_rompe": (
                '💡 LA IDEA: Comprobar el escenario de webhook hay exception de mp no rompe.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Si la consulta a MP lanza ConnectionError, verifica que el endpoint responde 200 {'status':'ok'} sin caer en 500."
            ),
            "test_webhook_confirm_rechazado_con_http_exception_no_rompe": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si confirm_payment lanza HTTPException (pago rechazado), el webhook igual responde 200 ok.'
            ),
            "test_webhook_json_invalido_es_ok": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Un body con JSON corrupto se descarta: responde 200 ok y no llama a MP.'
            ),
            "test_retorno_success_approved_redirige": (
                '💡 LA IDEA: Comprobar el escenario de retorno success approved redirige.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: El retorno /success con MP aprobado redirige (307) al portal con mp_status=approved y mp_tipo=reserva en la location.'
            ),
            "test_retorno_pending_redirige_en_pendiente": (
                '💡 LA IDEA: Comprobar el escenario de retorno pending redirige en pendiente.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El retorno /pending que no aplica redirige (307) con mp_status=pending.'
            ),
            "test_retorno_failure_redirige_a_failed": (
                '💡 LA IDEA: Comprobar el escenario de retorno failure redirige a failed.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El retorno /failure cuyo confirm lanza HTTPException redirige (307) con mp_status=failed.'
            ),
        },
    },
    "tests/test_metrics_activity.py": {
        "proposito": 'Cobertura de ReportService.get_access_activity: el panel de actividad de accesos con filtro opcional por rango de fechas. Verifica los totales entrada/salida, la exclusión por bordes desde/hasta, el contenido de los buckets horarios y el caso de rango inválido.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea las tablas, siembra un usuario admin global, entrega la sesión y la limpia al salir.'
            ),
            "_seed": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta AccessLogs con id incremental, una patente simple y la fecha/tipo/sucursal recibidos; representa los eventos de acceso del rango.'
            ),
            "_admin": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _admin.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el primer usuario admin de la base para pasar como usuario al servicio.'
            ),
            "test_access_activity_sin_filtro_incluye_todas": (
                '💡 LA IDEA: Comprobar el escenario de access activity sin filtro incluye todas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin filtro, verifica que los totales cuentan las 3 entradas y 2 salidas (total 5) y que first_datetime arranca el 2025-01-05.'
            ),
            "test_access_activity_desde_excluye_anteriores": (
                '💡 LA IDEA: Comprobar el escenario de access activity desde excluye anteriores.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con desde=2025-01-06, verifica que se excluyen los eventos anteriores y los totales son 1 entrada y 1 salida.'
            ),
            "test_access_activity_rango_completo": (
                '💡 LA IDEA: Comprobar el escenario de access activity rango completo.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con rango de un solo día, verifica que solo cuentan los eventos de ese día, que los buckets incluyen el label del día y excluyen los días vecinos.'
            ),
            "test_access_activity_rango_invalido_devuelve_vacio": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Con desde posterior a hasta, verifica que no hay buckets y los totales quedan en cero.'
            ),
            "test_access_activity_hasta_excluye_posteriores": (
                '💡 LA IDEA: Comprobar el escenario de access activity hasta excluye posteriores.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con hasta=2025-01-06, verifica que se excluyen los eventos posteriores y los totales son 1 entrada y 1 salida.'
            ),
        },
    },
}
