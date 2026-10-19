"""Explicaciones analizadas del lote tests_2 (reloj virtual, ALPR, saldo, facturación y sucursales)."""

ANALISIS: dict[str, dict] = {
    "tests/test_admin_virtual_time_routes.py": {
        "proposito": 'Pruebas automatizadas de los endpoints del reloj virtual (/virtual-time), verificando que los administradores y operarios puedan avanzar, retroceder o fijar la hora del sistema para probar tarifas y reservas sin alterar el reloj real de la máquina.',
        "simbolos": {
            "FakeUser": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuario simulado con rol y sucursal configurables para probar los permisos de acceso a las rutas del reloj virtual.'
            ),
            "FakeUser.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Constructor del usuario simulado que asigna el rol administrativo o de cliente según el caso de prueba.'
            ),
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona un cliente HTTP preconfigurado con las credenciales necesarias para consultar los endpoints del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: De pytest que inicializa un cliente HTTP de pruebas conectado a las rutas del reloj virtual con usuario inyectado.'
            ),
            "_reset_clock": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reset_clock.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el estado previo del reloj virtual en disco y lo restaura a cero al terminar cada prueba para no afectar a los demás tests.'
            ),
            "_leer_offset_de_disco": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _leer_offset_de_disco.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee el archivo temporal donde se almacena el desplazamiento horario en segundos para recordar el valor original.'
            ),
            "_restaurar_offset_en_disco": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _restaurar_offset_en_disco.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Reescribe o elimina el archivo de desplazamiento en disco para devolver el reloj a su estado inicial.'
            ),
            "_no_side_effects": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _no_side_effects.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplaza la ejecución de tareas de fondo por una función vacía para que las pruebas de tiempo no ejecuten procesos secundarios pesados.'
            ),
            "_set_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _set_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Configura el usuario actual de la prueba cambiando su rol a administrador, personal de sede o cliente común.'
            ),
            "test_get_status_devuelve_el_estado_del_reloj": (
                '💡 LA IDEA: Comprobar el escenario de get status devuelve el estado del reloj.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que la consulta del estado del reloj devuelva correctamente si está activo y cuántos segundos de diferencia tiene.'
            ),
            "test_alias_raiz_sin_status": (
                '💡 LA IDEA: Comprobar el escenario de alias raiz sin status.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que la ruta base /virtual-time responda igual que /virtual-time/status.'
            ),
            "test_advance_horas": (
                '💡 LA IDEA: Comprobar el escenario de advance horas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que la acción de adelantar el reloj incremente el desplazamiento en la cantidad exacta de segundos correspondiente a las horas pedidas.'
            ),
            "test_advance_todo_ceros_no_mueve_el_reloj": (
                '💡 LA IDEA: Comprobar el escenario de advance todo ceros no mueve el reloj.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba que enviar un avance sin valores mantenga el reloj en su posición actual.'
            ),
            "test_advance_combinado_dias_horas_minutos": (
                '💡 LA IDEA: Comprobar el escenario de advance combinado dias horas minutos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba el cálculo matemático correcto cuando se combinan días, horas y minutos en una sola petición.'
            ),
            "test_rewind_resta_offset": (
                '💡 LA IDEA: Comprobar el escenario de rewind resta offset.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que retroceder el reloj disminuya los segundos de desplazamiento acumulados.'
            ),
            "test_rewind_puede_dejar_offset_negativo": (
                '💡 LA IDEA: Comprobar el escenario de rewind puede dejar offset negativo.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que sea válido retroceder a un momento previo al tiempo real resultando en un valor negativo.'
            ),
            "test_set_target_con_iso_valido": (
                '💡 LA IDEA: Comprobar el escenario de set target con iso valido.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba fijar el reloj en una fecha y hora futura específica usando el formato estándar ISO.'
            ),
            "test_set_target_con_fecha_invalida_devuelve_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que el sistema rechace con código 400 los textos que no representen una fecha y hora válida.'
            ),
            "test_set_target_sin_campo_requerido_devuelve_422": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que la validación de esquemas devuelva código 422 si falta el cuerpo del mensaje requerido.'
            ),
            "test_set_offset_absoluto": (
                '💡 LA IDEA: Comprobar el escenario de set offset absoluto.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica la asignación directa de un desplazamiento fijo en segundos.'
            ),
            "test_reset_deja_el_reloj_en_cero": (
                '💡 LA IDEA: Comprobar el escenario de reset deja el reloj en cero.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba que reiniciar el reloj virtual desactive la simulación y restaure el desplazamiento a cero.'
            ),
            "test_staff_si_puede_manipular_el_reloj": (
                '💡 LA IDEA: Comprobar el escenario de staff si puede manipular el reloj.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Confirma que el personal operativo de playa tenga autorización para manipular el reloj en el entorno de pruebas.'
            ),
            "test_admin_global_si_puede": (
                '💡 LA IDEA: Comprobar el escenario de admin global si puede.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que el administrador general de la plataforma pueda ajustar el tiempo virtual.'
            ),
            "test_local_admin_si_puede": (
                '💡 LA IDEA: Comprobar el escenario de local admin si puede.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que el administrador de una sucursal local pueda ajustar el tiempo virtual.'
            ),
            "test_cliente_no_puede_manipular_el_reloj": (
                '💡 LA IDEA: Comprobar el escenario de cliente no puede manipular el reloj.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que a los clientes comunes se les niegue el acceso (error 403) si intentan mover el reloj.'
            ),
            "test_status_tambien_exige_rol_operativo": (
                '💡 LA IDEA: Comprobar el escenario de status tambien exige rol operativo.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que los clientes comunes no puedan consultar el estado del reloj de pruebas.'
            ),
            "_DB": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _DB.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase simulada que emula una sesión de base de datos para pruebas unitarias.'
            ),
            "_DB.close": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _DB.close.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Método de cierre simulado que no realiza ninguna operación real.'
            ),
            "test_run_all_checks_no_tumba_la_ruta_si_un_worker_falla": (
                '💡 LA IDEA: Comprobar el escenario de run all checks no tumba la ruta si un worker falla.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba que si uno de los procesos de control automático arroja un error, la petición HTTP igual responda con éxito.'
            ),
            "test_run_all_checks_invoca_los_cinco_pasos": (
                '💡 LA IDEA: Comprobar el escenario de run all checks invoca los cinco pasos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Asegura que el ajuste de tiempo dispare los cinco chequeos automáticos de recordatorios y vencimientos de reservas.'
            ),
        },
    },
    "tests/test_alpr_aspect_ratio_filter.py": {
        "proposito": 'Prueba del filtro de relación de aspecto de patentes, asegurando que un recorte incompleto de la chapa de un automóvil no sea clasificado erróneamente como una patente de motocicleta.',
        "simbolos": {
            "test_incomplete_auto_crop_detected_as_moto_aspect_ratio_check": (
                '💡 LA IDEA: Comprobar el escenario de incomplete auto crop detected as moto aspect ratio check.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que si una patente de auto se recorta por la mitad aparentando el formato de moto, su proporción ancho/alto delate que es un auto y se descarte.'
            ),
        },
    },
    "tests/test_alpr_hallucination_prevention.py": {
        "proposito": 'Pruebas para prevenir lecturas fantasmas o alucinaciones del motor OCR provocadas por leyendas institucionales o números compartidos entre lecturas sucesivas.',
        "simbolos": {
            "test_plate_close_shared_digits_debounce": (
                '💡 LA IDEA: Comprobar el escenario de plate close shared digits debounce.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que la función de comparación detecte lecturas parecidas que comparten el bloque numérico para no generar entradas duplicadas.'
            ),
            "test_header_noise_filtering": (
                '💡 LA IDEA: Comprobar el escenario de header noise filtering.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que palabras como 'REPUBLICA', 'ARGENTINA' o 'MERCOSUR' grabadas en la placa sean filtradas y no se confundan con la matrícula."
            ),
        },
    },
    "tests/test_alpr_node_auth.py": {
        "proposito": 'Pruebas de seguridad para la comunicación entre las cámaras de lectura de patentes (nodos ALPR) y el servidor central, comprobando el uso de contraseñas compartidas (tokens secretos) y direcciones IP confiables.',
        "simbolos": {
            "node_secret": (
                '💡 LA IDEA: Comprobar el escenario de node secret.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Configura temporalmente un secreto compartido de prueba para la autenticación de cámaras.'
            ),
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona un cliente HTTP preconfigurado con las credenciales necesarias para consultar los endpoints del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Cliente de pruebas HTTP configurado con base de datos en memoria para probar las rutas de validación de acceso.'
            ),
            "_ok_access": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _ok_access.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera una respuesta simulada de éxito para emular la apertura de la barrera.'
            ),
            "test_is_local_or_private_variantes": (
                '💡 LA IDEA: Comprobar el escenario de is local or private variantes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que la función reconozca correctamente direcciones IP locales (127.0.0.1, 192.168.x.x, 10.x.x.x) y rechace IPs públicas.'
            ),
            "test_is_trusted_alpr_node_con_secreto": (
                '💡 LA IDEA: Comprobar el escenario de is trusted alpr node con secreto.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba que un nodo con la clave secreta correcta sea admitido sin importar su dirección IP.'
            ),
            "test_is_trusted_alpr_node_sin_secreto_usa_red": (
                '💡 LA IDEA: Comprobar el escenario de is trusted alpr node sin secreto usa red.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que en caso de no configurarse clave secreta, solo se admitan cámaras conectadas a la red local.'
            ),
            "_fake_request": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _fake_request.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Construye una petición HTTP ficticia con encabezados y dirección IP personalizados para evaluar dependencias de seguridad.'
            ),
            "test_require_alpr_node_sin_secret_ok_node_secret": (
                '💡 LA IDEA: Comprobar el escenario de require alpr node sin secret ok node secret.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que una petición con la clave en el encabezado sea aceptada.'
            ),
            "test_require_alpr_node_403_sin_header": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que una petición remota sin encabezado de seguridad sea rechazada con código de prohibido 403.'
            ),
            "test_require_alpr_node_403_secret_malo": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba que si se envía una contraseña incorrecta se bloquee el acceso con error 403.'
            ),
            "test_require_alpr_node_acepta_red_local_sin_secreto": (
                '💡 LA IDEA: Comprobar el escenario de require alpr node acepta red local sin secreto.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Valida que un equipo de la red local pueda operar si no se exigió secreto explícito.'
            ),
            "test_validate_plate_403_sin_header": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Asegura que el endpoint de validar patente de entrada exija autenticación.'
            ),
            "test_validate_plate_403_secret_malo": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica el rechazo de la validación de patente con clave inválida.'
            ),
            "test_validate_plate_ok_con_secret": (
                '💡 LA IDEA: Comprobar el escenario de validate plate ok con secret.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba la validación exitosa de una patente cuando se incluye la clave correcta.'
            ),
            "test_exit_plate_ok_con_secret": (
                '💡 LA IDEA: Comprobar el escenario de exit plate ok con secret.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que el endpoint de registrar salida admita la cámara autenticada.'
            ),
            "test_exit_plate_403_sin_secret": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que no se permita registrar salidas sin la debida autenticación.'
            ),
            "test_validate_qr_403_sin_secret": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Asegura que la lectura de código QR de acceso rechace conexiones no autorizadas.'
            ),
            "test_validate_qr_ok_con_secret": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba la autorización de lectura de código QR con el secreto configurado.'
            ),
            "FakeResp": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Respuesta HTTP simulada para pruebas del despachador de eventos del motor OCR.'
            ),
            "FakeResp.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa la respuesta simulada con código de estado y datos en formato JSON.'
            ),
            "FakeResp.ok": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Indica si la respuesta HTTP simulada corresponde a un estado exitoso (200-299).'
            ),
            "FakeResp.status_code": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.status code.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el código numérico de estado HTTP de la respuesta simulada.'
            ),
            "FakeResp.json": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.json.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el cuerpo de la respuesta simulada decodificado como diccionario de datos.'
            ),
            "_EmptyError": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _EmptyError.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Excepción ficticia para simular caídas de red durante las pruebas de envío de eventos.'
            ),
            "test_dispatch_envia_header_secret": (
                '💡 LA IDEA: Comprobar el escenario de dispatch envia header secret.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que el motor ALPR adjunte el encabezado X-Node-Secret al enviar detecciones al backend.'
            ),
            "test_dispatch_sin_secret_no_envia_header": (
                '💡 LA IDEA: Comprobar el escenario de dispatch sin secret no envia header.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que si no se configuró clave secreta, el motor no envíe el encabezado innecesariamente.'
            ),
        },
    },
    "tests/test_alpr_overlay.py": {
        "proposito": 'Pruebas de la superposición visual (overlay) que dibuja sobre el video los recuadros verdes, el texto de la patente y el nivel de confianza de la lectura.',
        "simbolos": {
            "test_draw_overlay_rendering": (
                '💡 LA IDEA: Comprobar el escenario de draw overlay rendering.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que la función dibuje correctamente los recuadros delimitadores y carteles sobre la imagen sin corromper el formato de video.'
            ),
            "test_get_frame_with_overlay_clears_expired": (
                '💡 LA IDEA: Comprobar el escenario de get frame with overlay clears expired.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que las cajas de patentes detectadas desaparezcan del video una vez transcurrido el tiempo límite de visualización.'
            ),
        },
    },
    "tests/test_alpr_pipeline.py": {
        "proposito": 'Pruebas del flujo completo de reconocimiento de patentes: lectura óptica de caracteres, consenso de votos para evitar errores, descarte de cuadros oscuros y corrección de caracteres confusos (como ceros y letras O).',
        "simbolos": {
            "FakeQRDetector": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Detector simulado de códigos QR para aislar la prueba del reconocimiento de placas de matrícula.'
            ),
            "FakeQRDetector.detectAndDecode": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Método simulado que devuelve que no se encontró ningún código QR en la imagen.'
            ),
            "FakeReader": (
                '💡 LA IDEA: Comprobar el escenario de FakeReader.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Lector OCR simulado que devuelve lecturas de texto predeterminadas con alta confianza para pruebas repetibles.'
            ),
            "FakeReader.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeReader.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa el lector simulado con una lista de textos que irá entregando en orden.'
            ),
            "FakeReader.__call__": (
                '💡 LA IDEA: Comprobar el escenario de FakeReader.  call  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el siguiente resultado OCR simulado simulando el comportamiento de la librería RapidOCR.'
            ),
            "_make_engine": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _make_engine.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Instancia un motor ALPR ligero sin cargar modelos pesados en memoria para que los tests se ejecuten velozmente.'
            ),
            "_frame": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera una imagen digital uniforme en memoria simulando un cuadro de video capturado por una cámara.'
            ),
            "_wait_for": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _wait_for.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Bucle de espera activo que aguarda hasta que una condición asíncrona se cumpla o venza el tiempo límite.'
            ),
            "_stop_worker": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _stop_worker.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Detiene el hilo secundario de procesamiento OCR y libera los recursos del grupo de ejecución.'
            ),
            "test_ocr_consenso_dos_votos_emite_evento": (
                '💡 LA IDEA: Comprobar el escenario de ocr consenso dos votos emite evento.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que el motor requiera dos lecturas idénticas consecutivas antes de confirmar y enviar la patente al servidor.'
            ),
            "test_ocr_sin_consenso_patentes_distintas_no_emite": (
                '💡 LA IDEA: Comprobar el escenario de ocr sin consenso patentes distintas no emite.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que si la cámara lee valores diferentes y no hay mayoría de votos, la lectura se ignore para no levantar la barrera por error.'
            ),
            "test_ocr_frame_negro_descarta_votos": (
                '💡 LA IDEA: Comprobar el escenario de ocr frame negro descarta votos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba que los cuadros de video completamente oscuros o tapados se ignoren y reseteen los votos acumulados.'
            ),
            "test_send_event_debounce_suprime_duplicado_por_cooldown": (
                '💡 LA IDEA: Evitar ingresos duplicados cuando el vehículo ya figura dentro del establecimiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que si un vehículo permanece frente a la cámara, no se reenvíe el mismo evento múltiples veces dentro del tiempo de espera.'
            ),
            "test_send_event_patente_distinta_en_cooldown_si_envia": (
                '💡 LA IDEA: Comprobar el escenario de send event patente distinta en cooldown si envia.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que si ingresa un segundo vehículo con otra patente durante el tiempo de espera del primero, el nuevo vehículo sí se registre de inmediato.'
            ),
            "test_corregir_patente_mercosur_auto_con_digitos_ambiguos": (
                '💡 LA IDEA: Comprobar el escenario de corregir patente mercosur auto con digitos ambiguos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que si en una patente nueva Mercosur un número parece una letra (o viceversa), la regla posicional lo corrija según el estándar.'
            ),
            "test_corregir_patente_antigua_llllll_a_nnn": (
                '💡 LA IDEA: Comprobar el escenario de corregir patente antigua llllll a nnn.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba la corrección de caracteres ambiguos en patentes del modelo tradicional de tres letras y tres números.'
            ),
            "test_corregir_patente_limpia_ruido_header": (
                '💡 LA IDEA: Comprobar el escenario de corregir patente limpia ruido header.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Asegura que se eliminen fragmentos de palabras institucionales leídas en los bordes de la chapa.'
            ),
            "test_corregir_patente_larga_sin_formato_queda_limpia_solo": (
                '💡 LA IDEA: Comprobar el escenario de corregir patente larga sin formato queda limpia solo.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que textos extensos sin formato reconocido se limpien descartando símbolos no alfanuméricos.'
            ),
            "test_runner_videostreamer_fatal_no_crashea": (
                '💡 LA IDEA: Comprobar el escenario de runner videostreamer fatal no crashea.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que si la cámara de video no está disponible o falla su arranque, el servicio lo informe ordenadamente sin caerse de golpe.'
            ),
            "test_runner_bucle_principal_modo_entrada": (
                '💡 LA IDEA: Comprobar el escenario de runner bucle principal modo entrada.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica el ciclo principal de captura y procesamiento en modo de barrera de entrada.'
            ),
        },
    },
    "tests/test_alpr_queue_flush.py": {
        "proposito": 'Prueba de vaciado inmediato de la cola de imágenes del motor OCR para evitar acumulación de retraso en el procesamiento de video en vivo.',
        "simbolos": {
            "test_flush_queue_clears_all_stale_frames": (
                '💡 LA IDEA: Comprobar el escenario de flush queue clears all stale frames.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que al vaciar la cola de cuadros de video pendientes, la cola quede completamente limpia y en tamaño cero.'
            ),
        },
    },
    "tests/test_alpr_utils.py": {
        "proposito": 'Pruebas de utilidades de formato y normalización de patentes vehiculares y documentos de identidad.',
        "simbolos": {
            "test_normalize_plate": (
                '💡 LA IDEA: Comprobar el escenario de normalize plate.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que se quiten guiones, espacios y se pase a mayúsculas cualquier patente ingresada.'
            ),
            "test_format_plate_mercosur_arg": (
                '💡 LA IDEA: Comprobar el escenario de format plate mercosur arg.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba el formateo visual de una patente argentina nueva agregando los espacios correspondientes (ej: AB 123 CD).'
            ),
            "test_format_plate_old_arg": (
                '💡 LA IDEA: Comprobar el escenario de format plate old arg.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba el formateo visual de patentes argentinas tradicionales (ej: AAA 111).'
            ),
            "test_format_plate_mercosur_brasil": (
                '💡 LA IDEA: Comprobar el escenario de format plate mercosur brasil.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba el formateo de patentes Mercosur de Brasil (ej: ABC 1D23).'
            ),
            "test_normalize_dni": (
                '💡 LA IDEA: Comprobar el escenario de normalize dni.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica la limpieza de puntos y espacios en los números de documento de los usuarios.'
            ),
            "test_identify_country_bw_paper_printed_plate": (
                '💡 LA IDEA: Comprobar el escenario de identify country bw paper printed plate.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba la identificación del país y tipo de vehículo a partir de la estructura del texto cuando la chapa está impresa en papel blanco y negro.'
            ),
            "test_paraguay_auto_format": (
                '💡 LA IDEA: Comprobar el escenario de paraguay auto format.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica el formateo estandarizado de patentes de Paraguay.'
            ),
        },
    },
    "tests/test_balance_routes.py": {
        "proposito": 'Pruebas del módulo de saldo, estadías activas y tarifas para clientes, verificando el cálculo exacto de deudas por estacionamiento y la recarga de dinero virtual en la cuenta del usuario.',
        "simbolos": {
            "SimpleVehicle": (
                '💡 LA IDEA: Comprobar el escenario de SimpleVehicle.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Objeto simple que representa un vehículo registrado con su patente para su uso en tests.'
            ),
            "SimpleVehicle.__init__": (
                '💡 LA IDEA: Comprobar el escenario de SimpleVehicle.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Asigna la patente especificada a la instancia de vehículo de prueba.'
            ),
            "FakeUser": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Usuario cliente simulado con lista de vehículos y saldo para las pruebas del portal.'
            ),
            "FakeUser.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa el usuario simulado con un saldo y sus vehículos asociados.'
            ),
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Entrega el cliente de pruebas conectado a una base de datos SQLite en memoria.'
            ),
            "_reset_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reset_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Restablece el usuario simulado a sus valores iniciales al finalizar cada test.'
            ),
            "_set_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _set_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Configura el usuario actual de la prueba indicando su patente y su saldo disponible.'
            ),
            "_seed_log": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_log.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra en la base de datos un evento simulado de entrada o salida de un vehículo con fecha y costo.'
            ),
            "test_active_stays_usuario_sin_vehiculos": (
                '💡 LA IDEA: Comprobar el escenario de active stays usuario sin vehiculos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que si el cliente no tiene vehículos cargados, la lista de estadías activas devuelva vacío.'
            ),
            "test_active_stays_sin_ingresos_devuelve_lista_vacia": (
                '💡 LA IDEA: Comprobar el escenario de active stays sin ingresos devuelve lista vacia.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que si no hay registros de ingreso para los autos del usuario no se muestre ninguna estadía.'
            ),
            "test_active_stays_ingreso_no_pagado_con_deuda": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba que un auto actualmente adentro del estacionamiento sin pagar figure con su deuda calculada.'
            ),
            "test_active_stays_ingreso_pagado_deuda_cero": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que si el cliente ya abonó su estadía antes de salir, la deuda figure en cero.'
            ),
            "test_active_stays_salida_posterior_excluye_el_ingreso": (
                '💡 LA IDEA: Comprobar el escenario de active stays salida posterior excluye el ingreso.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Asegura que si el vehículo ya egresó del estacionamiento, no aparezca listado como estadía en curso.'
            ),
            "test_active_stays_multiples_salidas_mantiene_la_ultima": (
                '💡 LA IDEA: Comprobar el escenario de active stays multiples salidas mantiene la ultima.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que al existir múltiples ingresos y egresos históricos, el sistema reconozca el estado más reciente.'
            ),
            "test_active_stays_salida_anterior_al_ingreso_no_excluye": (
                '💡 LA IDEA: Comprobar el escenario de active stays salida anterior al ingreso no excluye.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que una salida de ayer no anule el ingreso registrado hoy por la mañana.'
            ),
            "test_active_stays_varias_patentes_solo_las_propias": (
                '💡 LA IDEA: Comprobar el escenario de active stays varias patentes solo las propias.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que un usuario únicamente vea los ingresos de sus propios vehículos y no los de terceros.'
            ),
            "test_payment_history_con_y_sin_logs": (
                '💡 LA IDEA: Comprobar el escenario de payment history con y sin logs.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba la consulta del historial de pagos realizados por el cliente.'
            ),
            "test_payment_history_sin_logs_pagados": (
                '💡 LA IDEA: Comprobar el escenario de payment history sin logs pagados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que la lista de pagos aparezca vacía si el usuario todavía no realizó ningún pago.'
            ),
            "test_rates_sin_configuracion_no_inventa_precios": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que el sistema devuelva valores vacíos y no invente tarifas si una sede no tiene precios configurados.'
            ),
            "test_rates_globales_deriva_30min_de_hora": (
                '💡 LA IDEA: Comprobar el escenario de rates globales deriva 30min de hora.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que si se define precio por hora pero no de media hora, el sistema deduzca la fracción dividiendo la hora por dos.'
            ),
            "test_rates_sucursal_no_hereda_globales": (
                '💡 LA IDEA: Comprobar el escenario de rates sucursal no hereda globales.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Asegura que una sucursal con tarifas específicas aplique sus propios valores sin mezclarlos con precios generales.'
            ),
            "test_rates_sucursal_sin_tarifario_devuelve_vacio": (
                '💡 LA IDEA: Comprobar el escenario de rates sucursal sin tarifario devuelve vacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que consultar tarifas de una sucursal sin precios asignados retorne vacío.'
            ),
            "test_recharge_balance_monto_invalido": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que se rechacen montos negativos o en cero al intentar recargar saldo.'
            ),
            "test_recharge_balance_ok_con_notificacion": (
                '💡 LA IDEA: Comprobar el escenario de recharge balance ok con notificacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba la acreditación exitosa de saldo en la cuenta del cliente junto con el envío de una notificación de confirmación.'
            ),
            "test_recharge_balance_notificacion_que_falla_devuelve_ok": (
                '💡 LA IDEA: Comprobar el escenario de recharge balance notificacion que falla devuelve ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que si el servicio de notificaciones falla, la recarga de dinero igual se acredite correctamente.'
            ),
        },
    },
    "tests/test_billing_service.py": {
        "proposito": 'Pruebas unitarias de las reglas de cálculo de cobro por estacionamiento: tarifas escalonadas por horas y fracciones de media hora, deducción de valores faltantes y separación de tarifas entre sucursales.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Prepara una base de datos en memoria limpia e invalida la memoria caché para cada prueba de facturación.'
            ),
            "test_calculate_total_amount_hora": (
                '💡 LA IDEA: Comprobar el escenario de calculate total amount hora.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica el cálculo del monto total correspondiente a dos horas de estadía aplicando el precio de hora y su fracción adicional.'
            ),
            "test_calculate_hourly_amount_escalonado": (
                '💡 LA IDEA: Comprobar el escenario de calculate hourly amount escalonado.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Prueba la tabla completa de tiempos escalonados (desde 30 minutos hasta varias horas) validando que el costo coincida exactamente con la política comercial.'
            ),
            "test_hourly_amount_from_rates_fallbacks": (
                '💡 LA IDEA: Comprobar el escenario de hourly amount from rates fallbacks.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba los cálculos auxiliares cuando falta el precio de la hora o de la media hora, derivando uno a partir del otro.'
            ),
            "test_calculate_total_amount_sin_tarifario_devuelve_none": (
                '💡 LA IDEA: Comprobar el escenario de calculate total amount sin tarifario devuelve none.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Asegura que si no hay ningún precio cargado en la base de datos, el cálculo retorne None en vez de un valor falso.'
            ),
            "test_get_rate_estricta_por_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de get rate estricta por sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que la consulta de tarifas respete estrictamente los precios de la sede indicada y no devuelva datos de otra sucursal.'
            ),
        },
    },
    "tests/test_branch_service.py": {
        "proposito": 'Pruebas del servicio de administración de sucursales: cálculo de capacidad total sumando planta baja y pisos superiores, propagación de cambios de nombre y verificación de ocupación física real.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea la estructura de tablas de prueba y la destruye ordenadamente al finalizar.'
            ),
            "test_get_branch_capacity_summary": (
                '💡 LA IDEA: Comprobar el escenario de get branch capacity summary.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que la capacidad total de una sede se calcule sumando los cupos de planta baja más cada uno de los pisos configurados para autos, motos y camionetas.'
            ),
            "test_rename_branch_propagates": (
                '💡 LA IDEA: Comprobar el escenario de rename branch propagates.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que al cambiar el nombre de una sucursal, el nuevo nombre se actualice automáticamente en los registros de aforo vinculados.'
            ),
            "test_rename_branch_same_name_is_noop": (
                '💡 LA IDEA: Comprobar el escenario de rename branch same name is noop.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que intentar renombrar una sucursal con el mismo nombre que ya tiene no realice operaciones innecesarias en la base de datos.'
            ),
            "test_has_physical_occupancy": (
                '💡 LA IDEA: Comprobar el escenario de has physical occupancy.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica si una sucursal tiene vehículos estacionados en su interior en este momento para evitar eliminar o modificar sedes ocupadas.'
            ),
        },
    },
}
