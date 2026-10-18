"""Explicaciones analizadas de la sección de tests (parte 5 de 6, análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "tests/test_reservation_availability_logic.py": {
        "proposito": 'Valida la lógica de disponibilidad de reservas de plaza: cálculo de ocupación máxima simultánea con sweep-line, reglas de bloqueo por capacidad, generación de fechas/horas deshabilitadas y el caso de capacidad de reservas igual a cero.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea todas las tablas sobre un motor SQLite en memoria, entrega una sesión y al terminar la cierra y elimina el esquema, aislándose por test.'
            ),
            "test_sweep_line_algorithm": (
                '💡 LA IDEA: Comprobar el escenario de sweep line algorithm.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que `_calcular_ocupacion_maxima_simultanea` cuenta el pico de solapamientos: con tres reservas devuelve 2 en la ventana completa (14-15:30) y 1 al evaluar solo de 16:00 a 17:00.'
            ),
            "test_capacity_blocking_rules": (
                '💡 LA IDEA: Comprobar el escenario de capacity blocking rules.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con capacidad de 2 autos y dos reservas activas/pagadas que la llenan de 14 a 15, verifica que `verificar_disponibilidad` rechace el día completo (ocupada=2), rechace esa misma hora y acepte otra hora libre (disponible, ocupada=0, restan=2).'
            ),
            "test_disabled_dates_calculation": (
                '💡 LA IDEA: Comprobar el escenario de disabled dates calculation.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con capacidad de 1 auto y una reserva que la llena de 10 a 11 el 15/09, comprueba que `obtener_fechas_deshabilitadas` marque ese día para estadía por día y que `obtener_horas_deshabilitadas` liste la hora 10:00 pero no la 11:00.'
            ),
            "test_capacidad_reservas_cero_no_muestra_disponibilidad": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                "⚙️ FUNCIONAMIENTO: Regresión: con `capacidad_reservas_autos=0` explícita el sistema no debe usar fallback de 5; `verificar_disponibilidad` devuelve disponible=False con capacidad 0 y mensaje de 'no cuenta con plazas', las horas deshabilitadas cubren >=24 y las fechas evaluadas quedan deshabilitadas. Al subir la capacidad a 2 vuelve a haber lugar."
            ),
        },
    },
    "tests/test_reservation_price_snapshot.py": {
        "proposito": "Verifica la 'foto de tarifas' (price snapshot): que al crear/editar reservas se persistan las tarifas y el cálculo, que una cotización discrepante del front se rechace con 409, y que al pagar con descuento se registren el total base y el %.",
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma un motor SQLite con StaticPool, crea el esquema, siembra una sucursal con precios de hora/fracción/día (1500/750/15000) y entrega la sesión.'
            ),
            "_seed_branch": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_branch.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta una `ParkingBranch` y sus `Settings` de tarifas por sucursal (precio_hora, precio_30min, precio_dia) para que el cotizador tenga datos.'
            ),
            "_usuario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea y persiste un `User` de prueba (rol user, sin bloqueo) con DNI aleatorio y lo refresca para devolverlo con id asignado.'
            ),
            "_vehiculo": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _vehiculo.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra un `Vehicle` asociado al usuario con patente y tipo (por defecto Auto) y lo devuelve tras refrescar.'
            ),
            "_ticket": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un `RedemptionTicket` de descuento de reserva vigente con el porcentaje indicado y la sucursal opcional, devolviéndolo tras persistir.'
            ),
            "test_admin_create_persiste_foto_tarifas": (
                '💡 LA IDEA: Comprobar el escenario de admin create persiste foto tarifas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Al crear por admin una reserva de 2h con cotización válida (3750), comprueba que se guardan tarifa_hora=1500, tarifa_fraccion=750, tarifa_aplicada=1500, horas_calculadas=2, monto_calculado=3750 y la marca tarifa_fijada_en.'
            ),
            "test_admin_create_sin_cotizacion_no_valida": (
                '💡 LA IDEA: Comprobar el escenario de admin create sin cotizacion no valida.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin cotización del front, `create_reservation` no valida contra nada y calcula el total por el servidor: monto_total y monto_calculado quedan en 3750.'
            ),
            "test_admin_create_monto_discrepante_409": (
                '💡 LA IDEA: Comprobar el escenario de admin create monto discrepante 409.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el monto cotizado (9999) no coincide con el calculado, la creación lanza una excepción con status_code 409.'
            ),
            "test_admin_create_horas_discrepantes_409": (
                '💡 LA IDEA: Comprobar el escenario de admin create horas discrepantes 409.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Si las horas cotizadas (5.0) no coinciden con las calculadas, la creación se rechaza con status_code 409.'
            ),
            "test_user_create_persiste_foto_tarifas": (
                '💡 LA IDEA: Comprobar el escenario de user create persiste foto tarifas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Al crear por usuario una reserva de día con cotización correcta (15000), verifica status ok y que persisten tarifa_hora=1500, tarifa_fraccion=750, tarifa_aplicada=15000 y monto_calculado=15000.'
            ),
            "test_user_create_monto_discrepante_409": (
                '💡 LA IDEA: Comprobar el escenario de user create monto discrepante 409.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el usuario cotiza un monto incorrecto (1.0), `create_user_reservation` lanza una excepción con status_code 409.'
            ),
            "_reserva": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea y persiste una `Reservation` de prueba asociada al usuario con monto y sucursal dados, en estado Pendiente, y la devuelve refrescada.'
            ),
            "test_manual_pago_guarda_descuento_y_base": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Al pagar manualmente una reserva de 1000 con un ticket de 10%, comprueba que el monto_total baja a 900, que monto_calculado conserva el base 1000 y que descuento_pct queda en 10.'
            ),
            "test_pago_saldo_guarda_descuento_y_base": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Igual que el pago manual pero por saldo (el usuario tiene 2000): al pagar con el ticket del 10% el total queda 900, el base 1000 y descuento_pct 10 (con el email de confirmación monkeypatched a no-op).'
            ),
            "test_pago_sin_descuento_no_toca_foto": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Al pagar manualmente sin ticket, verifica que descuento_pct permanece None: la foto no se altera cuando no hay descuento.'
            ),
        },
    },
    "tests/test_reservation_service.py": {
        "proposito": 'Pruebas básicas del servicio de reservas: creación exitosa de una reserva por admin y resolución del texto descriptivo de una sucursal.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea el esquema sobre SQLite en memoria, entrega una sesión y la cierra/elimina al final para aislar cada test.'
            ),
            "test_create_reservation_success": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Con una sucursal y sus tarifas cargadas, crea una reserva por admin y comprueba que nace en estado_reserva PENDIENTE y estado_pago PENDIENTE.'
            ),
            "test_branch_info_str_resolution": (
                '💡 LA IDEA: Comprobar el escenario de branch info str resolution.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que `BranchService.get_branch_info_str` incluya la dirección y el texto 'Abierto 24hs' al buscar por nombre exacto, y que también resuelva por coincidencia parcial ('Castelar')."
            ),
        },
    },
    "tests/test_reservation_spots.py": {
        "proposito": 'Valida la separación entre plazas rotativas y plazas de reserva, discriminando por tipo de vehículo (auto/moto/camioneta) en ingresos, egresos y disponibilidad.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea el esquema sobre SQLite en memoria, entrega una sesión y la cierra/elimina al cerrar, aislando cada test.'
            ),
            "test_exclusive_reservation_spots_logic": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un aforo trimodal y capacidades de reserva por tipo, recorre el ciclo completo: un ingreso rotativo incrementa `ocupacion_actual` pero no las de reserva; las reservas vigentes y pagadas de Auto y Moto aparecen en `verificar_disponibilidad` (capacidad 2, ocupada 1); el ingreso con reserva incrementa `ocupacion_reservas` y su contador por tipo sin tocar las plazas rotativas; y los egresos vuelven los contadores a cero.'
            ),
        },
    },
    "tests/test_routes_auth.py": {
        "proposito": 'Cubre el router de autenticación: registro, recuperación de contraseña, login con sesiones multi-dispositivo, flujo OAuth (authorize/callback/complete), logout con revocación y el rechazo de tokens de recuperación como tokens de acceso; usa TestClient con base SQLite aislada y resetea el rate limiter.',
        "simbolos": {
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma un motor SQLite con StaticPool, crea el esquema, sobreescribe la dependencia get_db de la app, resetea el limiter y entrega el TestClient junto a la factoría de sesiones; al terminar restaura los overrides y el limiter.'
            ),
            "_usuario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea y persiste un `User` de prueba con contraseña hasheada, rol user y DNI fijo, permitiendo marcarlo como bloqueado; devuelve el usuario.'
            ),
            "_login_body": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _login_body.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma el diccionario de credenciales para login, agregando `device_id` solo si se proporciona.'
            ),
            "test_register_user_success": (
                '💡 LA IDEA: Comprobar el escenario de register user success.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra un usuario nuevo por POST /v1/auth/register y comprueba que responde 200/201 con status ok.'
            ),
            "test_register_duplicado_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                "⚙️ FUNCIONAMIENTO: Registra el mismo email dos veces: el segundo intento devuelve 400 y el detalle contiene 'ya está registrado'."
            ),
            "test_register_dni_duplicado_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                "⚙️ FUNCIONAMIENTO: Registra dos usuarios con el mismo DNI: el segundo devuelve 400 y el detalle menciona 'DNI'."
            ),
            "test_register_error_interno_500": (
                '💡 LA IDEA: Comprobar el escenario de register error interno 500.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Fuerza un ValueError en `UserService.create_user`; el registro responde 500 con el detalle fijo 'Error interno al guardar el usuario.'."
            ),
            "test_forgot_password_usuario_conocido_envia_mail": (
                '💡 LA IDEA: Comprobar el escenario de forgot password usuario conocido envia mail.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un usuario existente, forgot-password responde 200 y el `send_recovery_email` monkeypatched recibe un único correo cuyo enlace empieza con BASE_URL/reset-password?token=.'
            ),
            "test_forgot_password_usuario_desconocido_no_revela": (
                '💡 LA IDEA: Comprobar el escenario de forgot password usuario desconocido no revela.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un email inexistente igual responde 200 con status ok pero no se envía ningún correo, evitando revelar si la cuenta existe.'
            ),
            "test_reset_password_purpose_invalido_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un token con purpose 'login' en reset-password devuelve 400 con 'inválido'."
            ),
            "test_reset_password_token_expirado_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un token de recuperación con exp en el pasado devuelve 400 con 'expirado'."
            ),
            "test_reset_password_usuario_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un token de recuperación válido para un email sin usuario devuelve 404 con 'Usuario no encontrado.'."
            ),
            "test_reset_password_exitoso": (
                '💡 LA IDEA: Comprobar el escenario de reset password exitoso.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un token de recuperación válido cambia la contraseña (200 status ok) y el login posterior con la nueva clave devuelve 200.'
            ),
            "test_login_user_invalid_credentials": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Login con credenciales inexistentes devuelve 401 e incluye la cabecera WWW-Authenticate.'
            ),
            "test_login_ok_sin_device": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Login correcto sin device_id devuelve 200 con token_type bearer, rol user, nuevo_dispositivo False y access_token presente.'
            ),
            "test_login_nueva_device_con_otra_activa_avisa": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con una sesión activa de otro device, un login desde un device nuevo marca nuevo_dispositivo True y genera una notificación tipo NEW_DEVICE_LOGIN.'
            ),
            "test_login_misma_device_sin_aviso": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Login con el mismo device_id/user_agent existente marca nuevo_dispositivo False, no genera notificaciones y conserva la UserSession.'
            ),
            "test_login_absorbe_sesion_por_user_agent": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuando el User-Agent coincide con una sesión de otro device_id, el login absorbe esa sesión (nuevo_dispositivo False) y actualiza su device_id al nuevo.'
            ),
            "test_oauth_providers_lista": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/auth/oauth/providers devuelve 200 con la lista provista por el `enabled_providers` monkeypatched.'
            ),
            "test_oauth_authorize_no_configurado_503": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Si el proveedor no está configurado, authorize responde 503 con 'no está configurado'."
            ),
            "test_oauth_authorize_ok_302": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con proveedor configurado, authorize redirige (302) a la URL de Google y captura un state no vacío.'
            ),
            "test_oauth_callback_error_denegado": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: El callback con error=access_denied redirige (303) con 'oauth_error=denegado'."
            ),
            "test_oauth_callback_state_invalido": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un callback con state inválido redirige (303) con 'oauth_error=state_invalido'."
            ),
            "test_oauth_callback_sin_codigo": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un callback con state válido pero sin code redirige (303) con 'oauth_error=sin_codigo'."
            ),
            "test_oauth_callback_intercambio_falla": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Si `exchange_code` lanza HTTPException 502, el callback redirige (303) llevando el mensaje de error en el fragmento de la URL.'
            ),
            "test_oauth_callback_usuario_existente": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Con un usuario ya existente, el callback redirige (303) a '/#' incluyendo oauth_token y sin oauth_error."
            ),
            "test_oauth_callback_usuario_bloqueado": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Si el usuario que devuelve el proveedor está bloqueado, el callback redirige (303) con 'oauth_error=bloqueado'."
            ),
            "test_oauth_callback_nuevo_usuario_signup": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Para un email nuevo, el callback redirige (303) incluyendo el signup token, el email y el proveedor (oauth_signup, oauth_email, oauth_provider=google).'
            ),
            "test_oauth_complete_crea_usuario": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/auth/oauth/complete con un token de signup válido crea el usuario (200, token bearer, rol user) verificando que se guardó con el nombre provisto.'
            ),
            "test_logout_revoca_token_y_borra_sesion": (
                '💡 LA IDEA: Comprobar el escenario de logout revoca token y borra sesion.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Tras login, logout revoca el jti del token (el mismo token ya no autentica en /v1/user/me) y elimina la UserSession del device.'
            ),
            "test_logout_requiere_auth": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Logout sin cabecera de autorización devuelve 401.'
            ),
            "test_token_recuperacion_no_es_accesso": (
                '💡 LA IDEA: Comprobar el escenario de token recuperacion no es accesso.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un token con purpose 'recovery' no se decodifica como access token (`decode_access_token` devuelve None) y usarlo en /v1/user/me da 401."
            ),
        },
    },
    "tests/test_schema_parity_p2.py": {
        "proposito": 'Previene el desfase de índices entre los modelos (create_all) y la cadena Alembic, y evita índices redundantes sobre claves primarias.',
        "simbolos": {
            "_run_alembic_head": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _run_alembic_head.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Apunta la DATABASE_URL (settings y alembic.ini) a un archivo SQLite temporal, desactiva fileConfig y ejecuta `command.upgrade` hasta head para construir el esquema tal como lo dejaría Alembic.'
            ),
            "_index_names_from_models": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _index_names_from_models.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Recorre las tablas ordenadas de `Base.metadata` y devuelve el conjunto de índices declarados por los modelos con el formato 'tabla.indice'."
            ),
            "_index_names_from_db": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _index_names_from_db.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Abre el SQLite dado y consulta sqlite_master para devolver los índices reales ('tabla.indice'), excluyendo los autoindex del motor."
            ),
            "test_paridad_indices_modelo_vs_alembic": (
                '💡 LA IDEA: Comprobar el escenario de paridad indices modelo vs alembic.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la estructura de tablas y columnas en la base de datos coincida perfectamente con los modelos del código.\n\n'
                '⚙️ FUNCIONAMIENTO: Construye el esquema con Alembic y compara los índices: no debe faltar ninguno del modelo en la base ni sobrar índices que el modelo no declare (missing y extra vacíos).'
            ),
            "test_no_hay_indices_redundantes_sobre_pk": (
                '💡 LA IDEA: Comprobar el escenario de no hay indices redundantes sobre pk.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la estructura de tablas y columnas en la base de datos coincida perfectamente con los modelos del código.\n\n'
                '⚙️ FUNCIONAMIENTO: Recorre todas las tablas y afirmas que ninguna columna de la PK tiene index=True, ya que la PK ya está indexada y eso se alinea con Alembic.'
            ),
        },
    },
    "tests/test_security_headers.py": {
        "proposito": 'Regresión de las cabeceras de seguridad (CSP y básicas) emitidas por main.py, comprobando que la política permita los orígenes externos de fuentes y APIs de mapas.',
        "simbolos": {
            "test_csp_permite_fuentes_de_cdnjs_y_apis_de_mapas": (
                '💡 LA IDEA: Comprobar el escenario de csp permite fuentes de cdnjs y apis de mapas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Pide /static/manifest.json y, parseando la cabecera Content-Security-Policy, verifica que font-src incluya cdnjs y que connect-src incluya overpass-api.de, nominatim.openstreetmap.org, cdn.jsdelivr.net y unpkg.com.'
            ),
            "test_headers_de_seguridad_basicos_presentes": (
                '💡 LA IDEA: Comprobar el escenario de headers de seguridad basicos presentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que la respuesta traiga X-Content-Type-Options: nosniff y X-Frame-Options: DENY.'
            ),
        },
    },
    "tests/test_status_ws.py": {
        "proposito": 'Cubre el estado de aforo y su WebSocket: OccupancyManager (connect/disconnect/broadcast por sucursal y GLOBAL), el endpoint /v1/parking/ws con validación de token y rol, y los endpoints HTTP de sucursales, estado de estacionamiento y ocupación actual.',
        "simbolos": {
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma el motor SQLite con StaticPool, crea el esquema, sobreescribe get_db, limpia las conexiones activas del manager y la caché de ocupación, y resetea el limiter; entrega TestClient y la factoría de sesiones, restaurando todo al final.'
            ),
            "FakeUser": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase simple que representa un usuario en sesión, con rol, email y sucursal, usada para simular la resolución de identidad en los tests de WS.'
            ),
            "FakeUser.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Inicializa el usuario falso con rol 'user', email y sucursal por defecto ('Centro')."
            ),
            "_fake_user_repo": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _fake_user_repo.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplazo de `UserRepository.get_active_by_email` que ignora la base y devuelve el usuario global `CURRENT_USER` fijado por `_mock_ws`.'
            ),
            "_seed": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta una `ParkingBranch` activa y su `ParkingAforo` (capacidad total 50, ocupación 3, motos y camionetas) y devuelve la sucursal creada.'
            ),
            "_mock_ws": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _mock_ws.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Configura el módulo de status monkeypatchando get_db, decode_access_token (que devuelve el email del usuario) y UserRepository para que el WS resuelva al usuario falso dado.'
            ),
            "FakeWS": (
                '💡 LA IDEA: Comprobar el escenario de FakeWS.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: WebSocket falso que registra si fue aceptado y guarda los mensajes JSON enviados, para testear el manager sin red real.'
            ),
            "FakeWS.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeWS.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa el socket falso con accepted=False y la lista vacía de mensajes.'
            ),
            "accept": (
                '💡 LA IDEA: Comprobar el escenario de accept.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca el socket falso como aceptado, emulando el handshake del WebSocket.'
            ),
            "send_json": (
                '💡 LA IDEA: Comprobar el escenario de send json.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrega el dato JSON recibido a la lista de mensajes enviados del socket falso.'
            ),
            "test_manager_connect_admin_usa_global": (
                '💡 LA IDEA: Comprobar el escenario de manager connect admin usa global.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin (sin sucursal) se conecta y el manager lo ubica en la clave GLOBAL, aceptando el socket.'
            ),
            "test_manager_connect_user_normaliza_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de manager connect user normaliza sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un usuario con sucursal 'Centro' se conecta y el manager lo registra bajo la clave normalizada 'CENTRO'."
            ),
            "test_manager_disconnect_elimina": (
                '💡 LA IDEA: Comprobar el escenario de manager disconnect elimina.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Tras conectar, `disconnect` quita el socket de su grupo y no falla al desconectar una clave inexistente.'
            ),
            "test_broadcast_branch_envia_a_sockets": (
                '💡 LA IDEA: Comprobar el escenario de broadcast branch envia a sockets.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Con una sucursal sembrada y un socket en CENTRO, `broadcast_update(db,'CENTRO')` envía un mensaje BRANCH_UPDATE con ocupacion_actual=3."
            ),
            "test_broadcast_global_envia_todas_sucursales": (
                '💡 LA IDEA: Comprobar el escenario de broadcast global envia todas sucursales.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con un socket en GLOBAL, `broadcast_update(db, None)` envía GLOBAL_UPDATE con la lista de sucursales (la primera 'Centro')."
            ),
            "test_broadcast_event_envia_a_sucursal_y_global": (
                '💡 LA IDEA: Comprobar el escenario de broadcast event envia a sucursal y global.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Un evento PENDING_EXIT para CENTRO llega tanto al socket de la sucursal como al socket global.'
            ),
            "test_broadcast_event_global_no_duplica": (
                '💡 LA IDEA: Comprobar el escenario de broadcast event global no duplica.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Al emitir hacia GLOBAL, el socket global recibe el evento una sola vez.'
            ),
            "test_broadcast_event_sin_sockets_no_falla": (
                '💡 LA IDEA: Comprobar el escenario de broadcast event sin sockets no falla.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Emitir hacia una sucursal sin sockets conectados no lanza error.'
            ),
            "test_ws_sin_token_cierra_4008": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Conectar al WS sin token cierra la conexión con código 4008.'
            ),
            "test_ws_token_invalido_cierra_4008": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un token que falla al decodificarse o un usuario no encontrado cierra con 4008.'
            ),
            "test_ws_admin_recibe_global_update": (
                '💡 LA IDEA: Comprobar el escenario de ws admin recibe global update.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin conectado por WS recibe al instante un mensaje GLOBAL_UPDATE.'
            ),
            "test_ws_staff_recibe_branch_update": (
                '💡 LA IDEA: Comprobar el escenario de ws staff recibe branch update.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un staff de la sucursal 'Centro' recibe al conectar un BRANCH_UPDATE con ocupacion_actual=3."
            ),
            "test_ws_cliente_no_operativo_cierra_4003": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Un usuario común (no operativo) es rechazado con cierre 4003 y no queda registrado en el grupo de su sucursal.'
            ),
            "test_ws_dos_clientes_reciben_broadcast": (
                '💡 LA IDEA: Comprobar el escenario de ws dos clientes reciben broadcast.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Al conectar un segundo admin, ambos sockets reciben el GLOBAL_UPDATE del broadcast.'
            ),
            "test_list_public_branches": (
                '💡 LA IDEA: Comprobar el escenario de list public branches.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/parking/branches (con caché desactivada) devuelve una sucursal con nombre, capacidad_total 50 y ocupacion_actual 3.'
            ),
            "test_get_parking_status_usuario_por_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de get parking status usuario por sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con get_operational_user sobreescrito a un user de 'Centro', /v1/parking/status devuelve capacidad_total 50 y ocupacion_actual 3 de esa sede."
            ),
            "test_get_parking_status_admin_fallback_primera_activa": (
                '💡 LA IDEA: Comprobar el escenario de get parking status admin fallback primera activa.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin sin sucursal obtiene el estado de la primera sucursal activa (capacidad_total 50).'
            ),
            "test_get_parking_status_sin_sucursales_default": (
                '💡 LA IDEA: Comprobar el escenario de get parking status sin sucursales default.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin sucursales, /v1/parking/status devuelve los valores por defecto (capacidad_total y disponibilidad 20).'
            ),
            "test_current_occupancy_sin_vehiculos": (
                '💡 LA IDEA: Comprobar el escenario de current occupancy sin vehiculos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin accesos registrados, /v1/parking/current-occupancy devuelve una lista vacía.'
            ),
            "test_current_occupancy_con_ingreso": (
                '💡 LA IDEA: Comprobar el escenario de current occupancy con ingreso.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un AccessLog de entrada reciente, la ocupación actual lista la patente AA123BB.'
            ),
        },
    },
    "tests/test_sucursal_id_sync.py": {
        "proposito": 'Prueba el traductor central de sede: el nombre vive solo en parking_branches y las tablas dependientes guardan únicamente `sucursal_id`, derivado del nombre al insertar/actualizar y sin cambiar al renombrar la sede.',
        "simbolos": {
            "session": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para session.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea el esquema sobre SQLite en memoria con StaticPool y entrega la sesión junto a su factoría; al final cierra la sesión y libera el motor.'
            ),
            "_seed": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea una `ParkingBranch` activa con el nombre dado y devuelve su id.'
            ),
            "test_reservacion_insert_deriva_sucursal_id": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Al insertar una `Reservation` con sucursal_nombre existente, el listener deriva automáticamente su `sucursal_id` al id de la sede.'
            ),
            "test_insert_en_todas_las_tablas_deriva_id": (
                '💡 LA IDEA: Comprobar el escenario de insert en todas las tablas deriva id.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Parametrizado sobre Reservation, AccessLog, User, SupportTicket y RedemptionTicket: en cada tabla el alta deriva `sucursal_id` desde el nombre de sede dado.'
            ),
            "test_nombre_inexistente_deja_sucursal_id_none": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Insertar con un nombre de sucursal que no existe deja `sucursal_id` en None.'
            ),
            "test_update_repunta_id_al_cambiar_nombre": (
                '💡 LA IDEA: Comprobar el escenario de update repunta id al cambiar nombre.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Al cambiar `sucursal_nombre` de una reserva a otra sede existente, el `sucursal_id` se re-apunta al id de la nueva.'
            ),
            "test_renombrar_sede_no_cambia_ids_y_actualiza_display": (
                '💡 LA IDEA: Comprobar el escenario de renombrar sede no cambia ids y actualiza display.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Renombrar la `ParkingBranch` no cambia el `sucursal_id` de la reserva y, al reconsultar, su `sucursal_nombre` muestra el nombre actualizado de la sede.'
            ),
        },
    },
    "tests/test_support_service.py": {
        "proposito": 'Prueba el servicio de soporte: creación y consulta de tickets, transición de estados al responder, mensajes de staff tratados como admin y el filtrado de tickets por rol y sucursal.',
        "simbolos": {
            "db_session": (
                '💡 LA IDEA: Comprobar el escenario de db session.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea el esquema en memoria y siembra dos sucursales, un usuario común y un admin local de Belgrano, entregando la sesión.'
            ),
            "test_create_and_get_support_ticket": (
                '💡 LA IDEA: Comprobar el escenario de create and get support ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea un ticket (estado Pendiente, sucursal correcta); comprueba que el usuario ve 1 ticket y el admin también, y que al actualizar el estado a 'Resuelto' con respuesta, el mensaje del admin queda en el hilo del ticket."
            ),
            "test_reply_sets_en_revision_y_bloquea_terminales": (
                '💡 LA IDEA: Comprobar el escenario de reply sets en revision y bloquea terminales.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Responder un ticket lo pasa a 'En Revisión'; luego, tras resolverlo, un nuevo intento de respuesta falla con 400/'bloqueado' por estado terminal."
            ),
            "test_staff_messages_render_as_is_admin": (
                '💡 LA IDEA: Comprobar el escenario de staff messages render as is admin.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un mensaje de staff se registra con autor 'Staff Operador' y todos sus mensajes quedan marcados con is_admin=True."
            ),
            "test_ticket_filtering_by_role_and_branch": (
                '💡 LA IDEA: Comprobar el escenario de ticket filtering by role and branch.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Con tres tickets (General, Belgrano, Castelar): el super admin por defecto ve solo los Generales, filtrando por sucursal ve el de esa sede y con 'TODAS' ve los tres; cada admin local solo ve los de su propia sucursal."
            ),
        },
    },
}
