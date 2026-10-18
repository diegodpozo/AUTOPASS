"""Explicaciones analizadas de la suite de tests (parte 1 de 6).

Cubre: conftest.py y los tests de acceso (flow, log-usuario, service) más los
tests de rutas admin (branches, invite, promotions, reservations, settings,
support, users). El texto sale de leer el cuerpo real de cada fixture, helper y
caso de prueba.
"""

ANALISIS: dict[str, dict] = {
    "tests/conftest.py": {
        "proposito": 'Configuración global de pytest para toda la suite: blinda el hardware serial (deja `settings.SERIAL_ENABLED = False` para que ningún test abra un puerto COM real) y evita el envío de correo SMTP real reemplazando `smtplib.SMTP`, de modo que las corridas no se cuelguen ni manden mails a las direcciones ficticias de los tests.',
        "simbolos": {
            "_SinRedSMTP": (
                '💡 LA IDEA: Simular el componente _SinRedSMTP para aislar la prueba de dependencias externas.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que las pruebas fallen por falta de internet o envíen spam a direcciones de ejemplo.\n\n'
                '⚙️ FUNCIONAMIENTO: Neutralizar las conexiones salientes de correo electrónico reemplazando la librería estándar por una simulación.'
            ),
            "_SinRedSMTP.__init__": (
                '💡 LA IDEA: Simular el componente _SinRedSMTP.__init__ para aislar la prueba de dependencias externas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite crear el objeto en memoria sin requerir parámetros de red válidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Instanciar el cliente SMTP simulado aceptando cualquier configuración de host o puerto.'
            ),
            "_SinRedSMTP.__enter__": (
                '💡 LA IDEA: Simular el componente _SinRedSMTP.__enter__ para aislar la prueba de dependencias externas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el bloque with de Python funcione de forma transparente sobre la clase sustituta.\n\n'
                '⚙️ FUNCIONAMIENTO: Proveer soporte de context manager (with) para el cliente de correo simulado.'
            ),
            "_SinRedSMTP.__exit__": (
                '💡 LA IDEA: Simular el componente _SinRedSMTP.__exit__ para aislar la prueba de dependencias externas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve `False` para no suprimir excepciones al salir del bloque `with`.'
            ),
            "_SinRedSMTP.starttls": (
                '💡 LA IDEA: Simular el componente _SinRedSMTP.starttls para aislar la prueba de dependencias externas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite satisfacer las dependencias de la interfaz probada sin ejecutar operaciones reales.\n\n'
                '⚙️ FUNCIONAMIENTO: Implementar una variante inocua del método _SinRedSMTP.starttls que no produzca efectos colaterales.'
            ),
            "_SinRedSMTP.login": (
                '💡 LA IDEA: Simular el componente _SinRedSMTP.login para aislar la prueba de dependencias externas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite satisfacer las dependencias de la interfaz probada sin ejecutar operaciones reales.\n\n'
                '⚙️ FUNCIONAMIENTO: Implementar una variante inocua del método _SinRedSMTP.login que no produzca efectos colaterales.'
            ),
            "_SinRedSMTP.sendmail": (
                '💡 LA IDEA: Simular el componente _SinRedSMTP.sendmail para aislar la prueba de dependencias externas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite satisfacer las dependencias de la interfaz probada sin ejecutar operaciones reales.\n\n'
                '⚙️ FUNCIONAMIENTO: Implementar una variante inocua del método _SinRedSMTP.sendmail que no produzca efectos colaterales.'
            ),
            "_SinRedSMTP.quit": (
                '💡 LA IDEA: Simular el componente _SinRedSMTP.quit para aislar la prueba de dependencias externas.\n\n'
                '🎯 POR QUE FUE GENERADA: Completa el ciclo de vida de la conexión simulada limpiamente.\n\n'
                '⚙️ FUNCIONAMIENTO: Simular el cierre ordenado de la conexión con el servidor SMTP.'
            ),
            "_sin_correo_real": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para _sin_correo_real.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que ningún caso de prueba envíe correos electrónicos a la red de forma accidental.\n\n'
                '⚙️ FUNCIONAMIENTO: Monkeypatchea `email_service.smtplib.SMTP` con `_SinRedSMTP` en cada test, garantizando que jamás se envíe correo real por defecto.'
            ),
        },
    },
    "tests/test_access_flow.py": {
        "proposito": 'Test de flujo completo de ingreso/egreso con barrera: valida `services/access_service.py` a través de las vías ALPR, QR y manual, comprobando aforo, cortesía de 10 minutos, deuda pendiente, cancelaciones y los helpers internos, con el hardware y el reloj mockeados.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea un engine SQLite en memoria (StaticPool) con todas las tablas y siembra la sucursal 'Centro' con un `ParkingAforo` (50 autos, 10 motos); entrega la sesión y al terminar cierra y borra el esquema."
            ),
            "env": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para env.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite inspeccionar qué comandos físicos se habrían enviado sin necesitar una barrera de estacionamiento conectada.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplaza `HardwareService.trigger_barrier` por un fake que registra cada disparo (gate, command, method, details) y fija `TimeService.now` al instante FIXED; devuelve un dict con la lista `calls` para inspeccionar los comandos disparados.'
            ),
            "_hace": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _hace.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve la fecha FIXED menos N minutos como string en formato 'YYYY-MM-DD HH:MM:SS'."
            ),
            "_futuro": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _futuro.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la fecha FIXED más N minutos como string con el mismo formato.'
            ),
            "_log_entrada": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _log_entrada.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un `AccessLog` (con patente normalizada, tipo, fecha, pago, sucursal y reserva opcional), lo confirma y lo devuelve.'
            ),
            "_reserva": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta una `Reservation` con patente, rango horario, estado de reserva/pago, sucursal y monto, y la devuelve confirmada.'
            ),
            "test_valida_plate_permite_y_dispara_barrera": (
                '💡 LA IDEA: Verificar el accionamiento físico de la barrera de acceso según la regla de negocio.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Una entrada ALPR nueva se permite, dispara la barrera con gate 'ENTRADA' y método 'ALPR', e incrementa `ocupacion_actual` a 1."
            ),
            "test_valida_plate_capacidad_maxima_no_dispara_barrera": (
                '💡 LA IDEA: Verificar el rechazo de ingreso cuando el estacionamiento alcanza su capacidad máxima.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                "⚙️ FUNCIONAMIENTO: Con la ocupación en el máximo (50) deniega el ingreso con mensaje 'Capacidad máxima' y no registra ningún disparo de barrera."
            ),
            "test_valida_plate_moto_usa_capacidad_motos": (
                '💡 LA IDEA: Comprobar el escenario de valida plate moto usa capacidad motos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si la patente corresponde a una Moto registrada, el ingreso descuenta de la capacidad de motos: sube `ocupacion_motos` a 1 y deja `ocupacion_actual` en 0.'
            ),
            "test_valida_plate_con_reserva_activa_libera_reserva": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con una reserva pendiente para la patente, permite el ingreso, incrementa `ocupacion_reservas` y deja el log ligado a `reserva_id` con `pago_confirmado` en False.'
            ),
            "test_valida_plate_ya_dentro_rechaza": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                "⚙️ FUNCIONAMIENTO: Si la patente ya tiene un ingreso reciente, deniega con 'ya figura dentro' y no dispara la barrera."
            ),
            "test_exit_plate_cortesia_ok_y_dispara_barrera": (
                '💡 LA IDEA: Comprobar que las estadías dentro del tiempo de cortesía salgan sin cargo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que las estadías breves dentro del tiempo de cortesía puedan salir sin costo ni retención innecesaria.\n\n'
                "⚙️ FUNCIONAMIENTO: Una salida ALPR dentro de la cortesía se autoriza, dispara la barrera ('SALIDA'/'ALPR') y baja `ocupacion_actual` a 0."
            ),
            "test_exit_plate_deuda_mayor_10min_rechaza_y_no_abre": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                "⚙️ FUNCIONAMIENTO: Con más de 10 minutos impagos deniega la salida ('Deuda pendiente'), no abre y emite el `pending_exit` para el popup de caja con los datos del invitado (sin usuario, deuda None, tipo Auto y el gate de salida)."
            ),
            "test_exit_plate_deuda_con_tarifario_previsualiza_monto": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un setting `precio_30min=100` y 30 minutos de estadía, el `pending_exit` previsualiza `deuda == 100.0` (un bloque).'
            ),
            "test_exit_plate_deuda_usuario_registrado_usa_nombre": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                "⚙️ FUNCIONAMIENTO: Si la patente pertenece a un usuario registrado, el `pending_exit` marca `es_registrado` True y arma el nombre completo 'Ana Gomez'."
            ),
            "test_exit_plate_cortesia_no_emite_pending_exit": (
                '💡 LA IDEA: Comprobar que las estadías dentro del tiempo de cortesía salgan sin cargo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que las estadías breves dentro del tiempo de cortesía puedan salir sin costo ni retención innecesaria.\n\n'
                '⚙️ FUNCIONAMIENTO: Una salida a los 5 minutos (dentro de cortesía) no deja ningún `pending_exit` registrado.'
            ),
            "test_exit_plate_sin_ingreso_error": (
                '💡 LA IDEA: Comprobar el escenario de exit plate sin ingreso error.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Una salida sin ingreso previo devuelve status 'error' con mensaje 'no tiene registro de ingreso'."
            ),
            "test_validate_qr_formato_invalido": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Un QR con formato inválido devuelve status 'error' con 'Formato de QR inválido'."
            ),
            "test_validate_qr_reserva_no_encontrada": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Un QR con id inexistente devuelve 'error' con 'Reserva no encontrada'."
            ),
            "test_validate_qr_patente_no_coincide": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Un QR cuya patente no coincide con la reserva devuelve 'error' con 'no coincide'."
            ),
            "test_validate_qr_sucursal_distinta_deniega": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Un QR de reserva cuya sede no es la del gate deniega con el mensaje 'únicamente para la sede Otra'."
            ),
            "test_validate_qr_ingreso_ok_y_dispara_barrera": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Un QR de reserva pendiente y pagada autoriza el ingreso, dispara la barrera ('ENTRADA'/'QR'), pasa la reserva a ACTIVA y sube `ocupacion_reservas` a 1."
            ),
            "test_validate_qr_ya_dentro_deniega": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                "⚙️ FUNCIONAMIENTO: Con la patente ya dentro, el QR deniega con 'ya se encuentra dentro'."
            ),
            "test_validate_qr_reserva_expirada_deniega": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Una reserva COMPLETADA deniega el QR con 'expiró o fue cancelada'."
            ),
            "test_validate_qr_fuera_de_horario_deniega": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Una reserva con rango horario ya pasada deniega el QR con 'no está vigente'."
            ),
            "test_validate_qr_salida_ok_y_dispara_barrera": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Un QR de salida sobre una reserva activa con log de entrada autoriza, disparando la barrera 'SALIDA'/'QR'."
            ),
            "test_validate_qr_salida_sin_ingreso_error": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Un QR de salida sin ingreso activo devuelve 'error' con 'ingreso activo'."
            ),
            "test_validate_qr_salida_deuda_mayor_10min_deniega": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                "⚙️ FUNCIONAMIENTO: Un QR de salida con estadía impaga de más de 10 minutos deniega con 'Deuda pendiente'."
            ),
            "test_manual_entry_nuevo_registra_y_dispara_barrera": (
                '💡 LA IDEA: Verificar el accionamiento físico de la barrera de acceso según la regla de negocio.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: El alta manual de una patente nueva devuelve 'ok', dispara la barrera con método 'MANUAL_ENTRY' y sube la ocupación a 1."
            ),
            "test_manual_entry_ya_ingresado_reutiliza": (
                '💡 LA IDEA: Comprobar el escenario de manual entry ya ingresado reutiliza.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Si la patente ya está dentro, el alta manual devuelve 'ok' con 'se reutilizó' y no dispara la barrera."
            ),
            "test_manual_entry_piso_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un alta manual con `floor_id` inexistente lanza una excepción con status 404.'
            ),
            "test_manual_exit_cortesia_ok": (
                '💡 LA IDEA: Comprobar que las estadías dentro del tiempo de cortesía salgan sin cargo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que las estadías breves dentro del tiempo de cortesía puedan salir sin costo ni retención innecesaria.\n\n'
                "⚙️ FUNCIONAMIENTO: La salida manual dentro de la cortesía devuelve 'ok', incluye '(Cortesía)' y dispara la barrera con método 'MANUAL_EXIT'."
            ),
            "test_manual_exit_sin_registro_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: La salida manual sin registro previo lanza una excepción con status 400.'
            ),
            "test_manual_exit_deuda_mayor_10min_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                "⚙️ FUNCIONAMIENTO: La salida manual con deuda lanza 403 cuyo detalle contiene 'DEUDA'."
            ),
            "test_cancel_stay_sin_ingreso_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancelar una estadía sin ingreso lanza una excepción con status 400.'
            ),
            "test_cancel_stay_cortesia_sin_cargo": (
                '💡 LA IDEA: Comprobar que las estadías dentro del tiempo de cortesía salgan sin cargo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que las estadías breves dentro del tiempo de cortesía puedan salir sin costo ni retención innecesaria.\n\n'
                "⚙️ FUNCIONAMIENTO: Cancelar dentro de la cortesía devuelve 'ok' con 'Sin cargo' y registra un `AccessLog` de SALIDA con `costo_estadia == 0.0`."
            ),
            "test_cancel_stay_mayor_10min_impago_402": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                "⚙️ FUNCIONAMIENTO: Con la deuda forzada a 500, cancelar una estadía impaga de más de 10 minutos lanza 402 con detalle 'abonar $500'."
            ),
            "test_cancel_stay_mayor_10min_pagada_ok": (
                '💡 LA IDEA: Comprobar el escenario de cancel stay mayor 10min pagada ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Cancelar una estadía de más de 10 minutos ya pagada devuelve 'ok' con 'Salida registrada'."
            ),
            "test_save_image_guarda_archivo": (
                '💡 LA IDEA: Comprobar el escenario de save image guarda archivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: `_save_image` decodifica base64 y escribe un '.jpg' en `IMAGE_DIR`, devolviendo el nombre del archivo y guardando exactamente los bytes."
            ),
            "test_save_image_sin_imagen_es_none": (
                '💡 LA IDEA: Comprobar el escenario de save image sin imagen es none.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: `_save_image` con imagen None devuelve None.'
            ),
            "test_branch_from_gate_id_resuelve_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de branch from gate id resuelve sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: `_branch_from_gate_id('Centro_ENTRADA')` resuelve la sucursal 'Centro'."
            ),
            "test_branch_from_gate_id_sin_prefijo_desconocido_es_none": (
                '💡 LA IDEA: Comprobar el escenario de branch from gate id sin prefijo desconocido es none.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: `_branch_from_gate_id` devuelve None tanto para un prefijo de gate inexistente como para un gate sin prefijo conocido.'
            ),
        },
    },
    "tests/test_access_log_usuario.py": {
        "proposito": "Test de regresión del monitoreo del dashboard: verificaba que las patentes de usuarios registrados aparecían como 'INVITADO'. Comprueba que `ReportService.get_access_logs` resuelve el dueño comparando la patente normalizada del log contra la patente (con formato visual) guardada en vehicles.",
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea las tablas sobre un engine SQLite en memoria global y siembra un usuario admin global; entrega la sesión y al final cierra y borra el esquema.'
            ),
            "_admin": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _admin.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve el primer usuario con rol 'admin' de la base."
            ),
            "_log": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _log.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un `AccessLog` con la patente detectada, el tipo de evento y la fecha actual, y confirma.'
            ),
            "test_log_normalizado_resuelve_usuario_con_patente_formateada": (
                '💡 LA IDEA: Comprobar el escenario de log normalizado resuelve usuario con patente formateada.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Log con patente normalizada 'AB123CD' frente al vehículo guardado como 'AB 123 CD': el reporte resuelve al dueño 'Juan Perez' con `es_registrado` True."
            ),
            "test_resuelve_usuario_ignoring_mayusculas_y_espacios": (
                '💡 LA IDEA: Comprobar el escenario de resuelve usuario ignoring mayusculas y espacios.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: La resolución es insensible a mayúsculas y espacios en ambos lados: una patente en minúsculas se resuelve a 'Ana Gomez'."
            ),
            "test_patente_sin_vehicle_sigue_siendo_invitado": (
                '💡 LA IDEA: Comprobar el escenario de patente sin vehicle sigue siendo invitado.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Una patente sin vehículo asociado no se resuelve a nadie: usuario None y `es_registrado` False.'
            ),
            "test_usa_normalized_patente_del_log_si_esta_disponible": (
                '💡 LA IDEA: Comprobar el escenario de usa normalized patente del log si esta disponible.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Si el log trae `normalized_patente`, se usa ese valor como fuente aunque `patente_detectada` tenga espacios, resolviendo 'Luis Soto'."
            ),
            "test_log_sin_patente_no_desalinea_el_resolucion_de_los_demas": (
                '💡 LA IDEA: Comprobar el escenario de log sin patente no desalinea el resolucion de los demas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Un log sin patente no desalinea la resolución de los siguientes: la fila sin patente queda sin usuario y la de 'GH234GH' resuelve 'Mia Rios'."
            ),
        },
    },
    "tests/test_access_service.py": {
        "proposito": 'Test básico de `AccessService` con un engine SQLite en memoria y una sucursal/aforo sembrados: cubre el alta por patente y la salida dentro de la cortesía.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea las tablas y siembra la sucursal 'Centro' con su `ParkingAforo` (id 1, capacidad 50); entrega la sesión y al terminar la cierra y borra el esquema."
            ),
            "test_validate_plate_new_entry": (
                '💡 LA IDEA: Comprobar el escenario de validate plate new entry.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Un alta ALPR nueva se autoriza ('Acceso permitido') e incrementa `ocupacion_actual` a 1."
            ),
            "test_validate_plate_duplicate_entry": (
                '💡 LA IDEA: Comprobar el escenario de validate plate duplicate entry.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                "⚙️ FUNCIONAMIENTO: El primer ingreso se autoriza; un segundo intento para la misma patente se deniega con 'ya figura dentro'."
            ),
            "test_exit_plate_courtesy_time": (
                '💡 LA IDEA: Comprobar el escenario de exit plate courtesy time.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Ingresar y salir de inmediato (dentro de los 10 minutos de cortesía) se autoriza con 'Salida autorizada' y devuelve `ocupacion_actual` a 0."
            ),
        },
    },
    "tests/test_admin_branches.py": {
        "proposito": 'Test de CRUD de sucursales y pisos de `routes/admin/branches.py`: listado, alta/baja/capacidad de pisos, alta/edición/borrado/toggle de sucursales con validaciones de ocupación y reservas activas, y el aislamiento por sede de los endpoints de pisos para el local_admin.',
        "simbolos": {
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea el engine SQLite en memoria (StaticPool), sobreescribe `get_db` y las dependencias de rol (`get_super_admin`, `get_local_manager`, `get_operational_user`) con usuarios fake, resetea el limiter y entrega un `TestClient` junto con la fábrica de sesiones.'
            ),
            "_seed_branch": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_branch.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea una `ParkingBranch` con su `ParkingAforo` asociado (capacidad 50 autos, 10 motos, 5 camionetas) y la devuelve tras confirmar.'
            ),
            "test_list_branches_con_resumen": (
                '💡 LA IDEA: Comprobar el escenario de list branches con resumen.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: El listado devuelve 200 con las dos sucursales sembradas ('Centro' y 'Norte')."
            ),
            "test_list_branches_requiere_auth": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Quitando el override de `get_operational_user`, el listado sin autenticación responde 401 o 403.'
            ),
            "test_add_floor": (
                '💡 LA IDEA: Comprobar el escenario de add floor.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Dar de alta un piso devuelve 200 con el nombre y persiste sus capacidades (total 20, reservas 4) en `ParkingFloor` para la sucursal.'
            ),
            "test_add_floor_sucursal_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Crear un piso en una sucursal inexistente responde 404.'
            ),
            "_seed_floor": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_floor.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un `ParkingFloor` con capacidades y ocupación inicial para una sucursal y lo devuelve.'
            ),
            "test_delete_floor_ok": (
                '💡 LA IDEA: Comprobar el escenario de delete floor ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Borrar un piso sin ocupación responde 200 y elimina la fila.'
            ),
            "test_delete_floor_con_vehiculos_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Borrar un piso con ocupación (3) responde 400.'
            ),
            "test_delete_floor_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Borrar un piso inexistente responde 404.'
            ),
            "test_update_floor_capacity": (
                '💡 LA IDEA: Comprobar el escenario de update floor capacity.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar capacidades del piso responde 200 y actualiza total, motos y el total de reservas (recalculado a partir de las capacidades de reserva).'
            ),
            "test_update_floor_capacidad_menor_a_ocupacion_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Bajar la capacidad por debajo de la ocupación actual responde 400 con el detalle 'ocupación actual'."
            ),
            "test_update_floor_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar un piso inexistente responde 404.'
            ),
            "test_create_branch_ok": (
                '💡 LA IDEA: Comprobar el escenario de create branch ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Crear una sucursal responde 200, la deja activa y le asigna el logo por defecto `/static/images/logo.png`.'
            ),
            "test_create_branch_logo_extension_invalida_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Subir un logo con extensión no permitida (.exe) responde 400 con detalle relacionado al logo.'
            ),
            "test_create_branch_duplicado_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                "⚙️ FUNCIONAMIENTO: Crear una sucursal con nombre ya existente responde 400 con 'ya existe'."
            ),
            "test_delete_branch_ok": (
                '💡 LA IDEA: Comprobar el escenario de delete branch ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Borrar una sucursal vacía responde 200 y elimina la fila.'
            ),
            "test_delete_branch_con_ocupacion_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Borrar una sucursal con vehículos responde 400 con 'vehículos'."
            ),
            "test_delete_branch_con_reservas_activas_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Borrar una sucursal con una reserva activa/pendiente en curso responde 400 con 'reservas activas'."
            ),
            "test_delete_branch_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Borrar una sucursal inexistente responde 404.'
            ),
            "test_update_branch_ok_renombra": (
                '💡 LA IDEA: Comprobar el escenario de update branch ok renombra.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Renombrar una sucursal responde 200, actualiza nombre/dirección y crea/mueve el `ParkingAforo` al nuevo nombre.'
            ),
            "test_update_branch_nombre_existente_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Renombrar a un nombre ya usado responde 400 con 'Ya existe'."
            ),
            "test_update_branch_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar una sucursal inexistente responde 404.'
            ),
            "test_toggle_branch_ok": (
                '💡 LA IDEA: Comprobar el escenario de toggle branch ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El toggle alterna `activa` de True a False y de vuelta a True.'
            ),
            "test_toggle_branch_con_vehiculos_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: El toggle con vehículos dentro responde 400 con 'vehículos'."
            ),
            "test_toggle_branch_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: El toggle de una sucursal inexistente responde 404.'
            ),
            "test_add_floor_de_otra_sede_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un LOCAL_ADMIN de 'Centro' no puede agregar pisos en otra sede: responde 403."
            ),
            "test_delete_floor_de_otra_sede_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un LOCAL_ADMIN de 'Centro' no puede borrar pisos de otra sede: responde 403."
            ),
            "test_update_floor_capacity_de_otra_sede_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un LOCAL_ADMIN de 'Centro' no puede cambiar la capacidad de un piso de otra sede: responde 403 y el piso queda sin cambios."
            ),
            "test_pisos_de_su_propia_sede_siguen_funcionando": (
                '💡 LA IDEA: Comprobar el escenario de pisos de su propia sede siguen funcionando.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El scope por sede no rompe al LOCAL_ADMIN legítimo de su propia sede: puede editar la capacidad y recibe 200.'
            ),
            "test_admin_global_pisos_de_cualquier_sede": (
                '💡 LA IDEA: Comprobar el escenario de admin global pisos de cualquier sede.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El ADMIN global (sin restricción de sede) puede editar pisos de otra sede: responde 200.'
            ),
            "test_scope_compara_normalizado_sin_distinguir_mayusculas": (
                '💡 LA IDEA: Comprobar el escenario de scope compara normalizado sin distinguir mayusculas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: El scope compara sedes normalizadas: 'Centro' y 'centro' se tratan como la misma sede y la edición responde 200."
            ),
        },
    },
    "tests/test_admin_invite.py": {
        "proposito": "Test del flujo de invitación/activación del Admin General: alta por invitación (solo admin general), imposibilidad de ingresar hasta fijar clave, activación vía reset-password con purpose 'activation' con envío de confirmación, y creación/derivación de la organización.",
        "simbolos": {
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea el engine SQLite en memoria, sobreescribe `get_db`, resetea el limiter y entrega un `TestClient` junto con la fábrica de sesiones (los roles se autentican por token real).'
            ),
            "_crear_usuario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un usuario con rol, email y contraseña dados (hash real) y campos por defecto, y devuelve el objeto recargado.'
            ),
            "_token": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _token.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Hace login con email/clave y devuelve el `access_token` JWT.'
            ),
            "_invite_body": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _invite_body.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma el cuerpo de invitación con nombre, apellido, DNI, teléfono y email (DNI autogenerado si no se pasa).'
            ),
            "test_admin_general_invita_y_envia_mail": (
                '💡 LA IDEA: Comprobar el escenario de admin general invita y envia mail.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin general invita: responde 200, se llama a `send_admin_invitation` con el email y una URL que incluye `token=`, y se crea el usuario con rol admin.'
            ),
            "test_invitado_no_puede_ingresar_antes_de_activar": (
                '💡 LA IDEA: Comprobar el escenario de invitado no puede ingresar antes de activar.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: El invitado no puede loguearse con la contraseña por defecto porque su clave es aleatoria: el login responde 401.'
            ),
            "test_invitacion_requiere_admin_general": (
                '💡 LA IDEA: Comprobar el escenario de invitacion requiere admin general.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un local_admin no puede invitar: responde 403.'
            ),
            "test_invitacion_email_duplicado_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide ingresos duplicados de una misma patente cuando el rodado ya se encuentra registrado dentro de la sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Invitar dos veces al mismo email: el primer intento da 200 y el segundo 400.'
            ),
            "test_activacion_fija_clave_y_confirma_registro": (
                '💡 LA IDEA: Comprobar el escenario de activacion fija clave y confirma registro.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un token de activación válido, reset-password responde 200, dispara `send_registration_confirmation` y luego el invitado puede ingresar con la nueva clave.'
            ),
            "test_reset_rechaza_purpose_desconocido": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un token con purpose distinto a 'activation'/'recovery' es rechazado con 400."
            ),
            "test_invitacion_crea_organizacion_con_nombre_del_formulario": (
                '💡 LA IDEA: Comprobar el escenario de invitacion crea organizacion con nombre del formulario.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Si el formulario trae 'organizacion', se crea una Organization no principal con ese nombre y el nuevo usuario queda asociado a ella."
            ),
            "test_invitacion_sin_organizacion_la_deriva_del_nombre": (
                '💡 LA IDEA: Comprobar el escenario de invitacion sin organizacion la deriva del nombre.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Sin organización en el formulario, se crea una con el nombre derivado del invitado ('Nuevo Admin')."
            ),
        },
    },
    "tests/test_admin_promotions.py": {
        "proposito": 'Test del CRUD de `routes/admin/promotions.py`: listado (admin global ve todas, local_admin solo su sede, activa None normalizada a True), alta con sucursal forzada y tipo de canje, toggle, actualización con reasignación de sucursal solo para admin global, y borrado con desasociación de tickets.',
        "simbolos": {
            "FakeUser": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase mínima que emula al usuario autenticado con `rol` y `sucursal`, inyectada vía override de `get_current_user`.'
            ),
            "FakeUser.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el rol (por defecto ADMIN) y la sucursal (por defecto None) del usuario simulado.'
            ),
            "CURRENT": (
                '💡 LA IDEA: Comprobar el escenario de CURRENT.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Dict global con el usuario actual fake que usa el override; se reemplaza por test y se resetea automáticamente.'
            ),
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Arma una `FastAPI` con el router de promotions, engine SQLite en memoria con las sedes 'Centro' y 'Norte', y overrides de `get_db` y `get_current_user`; entrega el `TestClient` y la fábrica de sesiones."
            ),
            "_reset_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reset_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Restaura el usuario actual a un FakeUser ADMIN tras cada test.'
            ),
            "_set_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _set_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Fija el usuario actual con el rol (acepta enum o string) y la sucursal indicados.'
            ),
            "_set_staff": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _set_staff.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Fija el usuario actual como STAFF con la sucursal dada.'
            ),
            "_seed_promo": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_promo.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea una `Promotion` con título, sucursal, activa, tipo de canje y valor, y devuelve su id.'
            ),
            "_get_promo": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _get_promo.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Recupera una `Promotion` por id y la devuelve.'
            ),
            "test_list_promotions_admin_global_ve_todas": (
                '💡 LA IDEA: Comprobar el escenario de list promotions admin global ve todas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El admin global ve las dos promociones (global y de sede).'
            ),
            "test_list_promotions_local_admin_solo_su_sede": (
                '💡 LA IDEA: Comprobar el escenario de list promotions local admin solo su sede.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin de 'Centro' solo ve la promoción de 'Centro', no la de 'Norte'."
            ),
            "test_list_promotions_activa_none_se_normaliza_a_true": (
                '💡 LA IDEA: Comprobar el escenario de list promotions activa none se normaliza a true.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Una promoción con `activa` en None se devuelve en el listado como True.'
            ),
            "test_list_promotions_staff_recibe_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El rol staff no puede listar promociones: responde 403.'
            ),
            "test_create_promotion_admin_global_con_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de create promotion admin global con sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El admin global crea una promoción para 'Centro': responde 200 con el mensaje que nombra la sede, y guarda tipo 'voucher' con valor None."
            ),
            "test_create_promotion_admin_global_global": (
                '💡 LA IDEA: Comprobar el escenario de create promotion admin global global.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El admin global puede crear una promoción global (sucursal None) y el mensaje dice 'para Global'."
            ),
            "test_create_promotion_descuento_reserva_guarda_valor": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Una promoción de tipo 'descuento_reserva' guarda su `valor_descuento` y los datos de ubicación (dirección, latitud, longitud)."
            ),
            "test_create_promotion_descuento_reserva_sin_valor": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Una promoción 'descuento_reserva' sin valor explícito responde 200 y guarda `valor_descuento` None."
            ),
            "test_create_promotion_local_admin_sucursal_forzada": (
                '💡 LA IDEA: Comprobar el escenario de create promotion local admin sucursal forzada.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin intenta crear en 'Norte' pero la sucursal se fuerza a la suya ('Centro')."
            ),
            "test_create_promotion_costo_puntos_invalido_422": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Un `costo_puntos` igual a 0 es rechazado por validación con 422.'
            ),
            "test_create_promotion_descuento_fuera_de_rango_422": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Un `valor_descuento` fuera de rango (150) es rechazado con 422.'
            ),
            "test_toggle_promotion_activa_a_desactiva": (
                '💡 LA IDEA: Comprobar el escenario de toggle promotion activa a desactiva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El toggle pasa una promoción activa a inactiva: responde True→False y persiste `activa` en False.'
            ),
            "test_toggle_promotion_desactiva_a_activa": (
                '💡 LA IDEA: Comprobar el escenario de toggle promotion desactiva a activa.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El toggle pasa una promoción inactiva a activa: `activa` True.'
            ),
            "test_toggle_promotion_no_encontrada_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                "⚙️ FUNCIONAMIENTO: El toggle de una promoción inexistente responde 404 con 'Promoción no encontrada'."
            ),
            "test_toggle_promotion_otra_sucursal_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un local_admin de 'Centro' no puede togglear una promoción de 'Norte': responde 403."
            ),
            "test_toggle_promotion_misma_sucursal_distinto_formato_ok": (
                '💡 LA IDEA: Comprobar el escenario de toggle promotion misma sucursal distinto formato ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: La comparación de sede es normalizada: 'AUTOPASS Centro' y 'Centro' son la misma sede y el toggle responde 200."
            ),
            "test_update_promotion_admin_global_reasigna_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de update promotion admin global reasigna sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El admin global actualiza una promoción y puede reasignar su sucursal de 'Centro' a 'Norte'."
            ),
            "test_update_promotion_local_admin_no_reasigna": (
                '💡 LA IDEA: Comprobar el escenario de update promotion local admin no reasigna.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin actualiza pero la sucursal se mantiene fija en 'Centro' aunque intente cambiarla."
            ),
            "test_update_promotion_descuento_reserva_actualiza_valor": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Al actualizar una promoción de descuento se guarda el nuevo `valor_descuento` (30).'
            ),
            "test_update_promotion_cambio_a_voucher_limpia_valor": (
                '💡 LA IDEA: Comprobar el escenario de update promotion cambio a voucher limpia valor.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Cambiar el tipo de canje a 'voucher' limpia el `valor_descuento` a None."
            ),
            "test_update_promotion_no_encontrada_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar una promoción inexistente responde 404.'
            ),
            "test_update_promotion_otra_sucursal_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un local_admin no puede actualizar promociones de otra sede: responde 403.'
            ),
            "test_delete_promotion_ok_desasocia_tickets": (
                '💡 LA IDEA: Comprobar el escenario de delete promotion ok desasocia tickets.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Borrar una promoción responde `{'status':'ok'}`, desasocia sus tickets (`promotion_id` a None) y elimina la promoción."
            ),
            "test_delete_promotion_no_encontrada_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Borrar una promoción inexistente responde 404.'
            ),
            "test_delete_promotion_otra_sucursal_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un local_admin no puede borrar promociones de otra sede: responde 403.'
            ),
        },
    },
    "tests/test_admin_reservations.py": {
        "proposito": 'Test integral de `routes/admin/reservations.py` y `ReservationService`: pago manual, creación/edición de reservas manuales (origen, vínculo con usuario, tipo de vehículo, recálculo de montos, cobros y reembolsos de diferencia), descuentos por canje, disponibilidad y contador de reservas nuevas con aislamiento por sucursal.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea el esquema en SQLite en memoria y siembra dos sucursales ('Sucursal Central' y 'Sucursal Dos'), un aforo de reservas de autos en la central y settings de tarifas (hora/30min para auto, moto y camioneta) en ambas; entrega la sesión y al final cierra y borra el esquema."
            ),
            "_cliente": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea un usuario 'user' de 'Sucursal Central' con saldo 5000 y devuelve el objeto."
            ),
            "_reserva_data": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reserva_data.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Construye un `AdminReservationCreate` con valores por defecto (patente, rango, tipo 'hora', sucursal) y permite sobrescribir campos."
            ),
            "test_pay_reservation_manual_marca_pagado_sin_tocar_saldo": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: El pago manual de una reserva la marca PAGADO/ACTIVA, setea método y fecha de pago, sin modificar el saldo del usuario (solo puede acreditar puntos).'
            ),
            "test_pay_reservation_manual_idempotente": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un segundo pago manual devuelve 'ok' pero conserva el método original ('Transferencia'), sin sobreescribirlo."
            ),
            "test_create_admin_reservation_con_pago_crea_y_registra_pago": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Crear una reserva con pago devuelve 'ok' y `pagado` True, y persiste la reserva PAGADO/ACTIVA con su método y sucursal."
            ),
            "test_create_admin_reservation_sin_pago_queda_pendiente": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Crear sin pago devuelve `pagado` False y deja la reserva PENDIENTE con método None.'
            ),
            "test_create_admin_reservation_staff_no_cambia_sucursal": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un staff que envía otra sucursal en el payload queda forzado a la suya ('Sucursal Central')."
            ),
            "test_create_admin_reservation_admin_si_cambia_sucursal": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un admin global sí puede crear la reserva en la sucursal elegida ('Sucursal Dos')."
            ),
            "test_create_admin_reservation_persiste_tipo_vehiculo": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: La reserva manual persiste el `tipo_vehiculo` indicado ('Camioneta')."
            ),
            "test_disponibilidad_considera_tipo_vehiculo_de_reserva_manual": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: La verificación de disponibilidad respeta el tipo de vehículo: una reserva de Moto ocupa el cupo de motos (1) y no el de autos (0).'
            ),
            "_cliente_con_vehiculo": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _cliente_con_vehiculo.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un usuario con un `Vehicle` de patente y tipo dados, y devuelve el usuario.'
            ),
            "_staff": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _staff.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea un usuario rol 'staff' en 'Sucursal Central' y lo devuelve."
            ),
            "test_patente_lookup_encuentra_dueno_registrado": (
                '💡 LA IDEA: Comprobar el escenario de patente lookup encuentra dueno registrado.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El lookup de patente normaliza y encuentra al dueño, devolviendo id, nombre, apellido y tipo de vehículo, sin exponer PII como el email.'
            ),
            "test_patente_lookup_no_encontrada": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El lookup de una patente desconocida devuelve `encontrado` False.'
            ),
            "test_patente_lookup_ignora_patentes_cortas": (
                '💡 LA IDEA: Comprobar el escenario de patente lookup ignora patentes cortas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: El lookup ignora patentes demasiado cortas ('ab') y devuelve `encontrado` False."
            ),
            "test_create_admin_reservation_vincula_usuario_por_patente": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Crear una reserva con user_id y patente vinculada marca PAGADO y acredita puntos al usuario.'
            ),
            "test_create_admin_reservation_marca_origen_manual": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Una reserva creada por admin/empleado queda con `origen == 'manual'`."
            ),
            "test_reserva_de_cliente_por_defecto_tiene_origen_cliente": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Una reserva creada directamente por el cliente (sin pasar por la ruta admin) queda con `origen == 'cliente'` por defecto."
            ),
            "test_edit_admin_reservation_actualiza_datos_y_recalcula_monto": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Editar una reserva manual actualiza patente, fechas y recalcula el monto total con `BillingService.calculate_total_amount`, conservando el origen manual.'
            ),
            "test_edit_admin_reservation_preserva_estados": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Editar una reserva ya pagada conserva los estados PAGADO/ACTIVA y el método de pago.'
            ),
            "test_edit_admin_reservation_vincula_usuario_por_patente": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Editar con una patente que pertenece a un usuario vincula la reserva a ese usuario y normaliza la patente.'
            ),
            "test_edit_reserva_de_cliente_rechazada": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Editar una reserva con origen 'cliente' es rechazado con 400."
            ),
            "test_edit_completada_rechazada": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Editar una reserva COMPLETADA es rechazado con 400.'
            ),
            "test_edit_staff_no_puede_editar_otra_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de edit staff no puede editar otra sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un staff no puede editar una reserva de otra sucursal: responde 403.'
            ),
            "test_get_permissioned_reservation_misma_sucursal_distinto_formato": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: `get_permissioned_reservation` acepta la reserva cuando la sede coincide pese al distinto formato ('AUTOPASS Sucursal Central' vs 'Sucursal Central')."
            ),
            "test_get_permissioned_reservation_otra_sucursal_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: `get_permissioned_reservation` lanza 403 al pedir una reserva de otra sede.'
            ),
            "test_edit_excluye_propia_reserva_de_disponibilidad": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Al editar se excluye la propia reserva del cálculo de disponibilidad, permitiendo editar aunque el slot esté lleno.'
            ),
            "test_edit_admin_reservation_valida_rango_invertido": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Editar con fecha de fin anterior al inicio es rechazado con 400.'
            ),
            "test_edit_sin_user_id_conserva_vinculo_si_la_patente_sigue_siendo_del_usuario": (
                '💡 LA IDEA: Comprobar el escenario de edit sin user id conserva vinculo si la patente sigue siendo del usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Editar sin user_id pero manteniendo una patente que pertenece al usuario conserva el vínculo.'
            ),
            "test_edit_sin_user_id_desvincula_si_la_patente_ya_no_es_del_usuario": (
                '💡 LA IDEA: Comprobar el escenario de edit sin user id desvincula si la patente ya no es del usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Editar sin user_id y cambiando a una patente ajena desvincula la reserva (user_id None).'
            ),
            "test_create_admin_reservation_almacena_patente_canonica_sin_espacios": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: La reserva manual guarda la patente canónica sin espacios en mayúsculas ('AS122TR')."
            ),
            "test_disabled_hours_excluye_propia_reserva_al_editar": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: `obtener_horas_deshabilitadas_con_reservas` incluye el rango reservado, y con `exclude_id` de la propia reserva el rango desaparece.'
            ),
            "_monto": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _monto.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Calcula el monto total de un rango en 'Sucursal Central' para autos vía `BillingService.calculate_total_amount`."
            ),
            "test_edit_cobra_diferencia_cuando_aumenta_el_monto": (
                '💡 LA IDEA: Comprobar el escenario de edit cobra diferencia cuando aumenta el monto.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Al extender una reserva pagada, la edición cobra la diferencia del monto con el método indicado y actualiza monto total, método y estado.'
            ),
            "test_edit_reembolsa_diferencia_al_saldo_cuando_disminuye": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                "⚙️ FUNCIONAMIENTO: Al acortar una reserva pagada y reembolsar por 'Saldo', se acredita la diferencia al saldo del usuario y se registra el `monto_reembolsado`."
            ),
            "test_edit_reembolso_en_efectivo_no_acredita_saldo": (
                '💡 LA IDEA: Comprobar el cálculo de tarifas, cobro de estadías y liquidación de saldos.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: El reembolso en efectivo NO acredita al saldo virtual; el reporte financiero imputa la reserva a CAJA en neto y muestra el reembolso en el historial.'
            ),
            "test_edit_sin_diferencia_no_toca_finanzas": (
                '💡 LA IDEA: Comprobar el escenario de edit sin diferencia no toca finanzas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Editar a un rango con el mismo monto deja `accion` 'sin_cambio' y no toca monto total ni reembolsos."
            ),
            "test_edit_pagada_con_multiples_ajustes_mantiene_neto_correcto": (
                '💡 LA IDEA: Comprobar el escenario de edit pagada con multiples ajustes mantiene neto correcto.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Tras un cobro y luego un reembolso sucesivos, el neto (`monto_total - monto_reembolsado`) coincide con el valor final de la reserva.'
            ),
            "test_reporte_cuenta_reembolso_parcial_de_reserva_pagada": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: El reporte financiero descuenta el reembolso parcial del desglose de reservas y por método (DIGITAL) y lo lista como 'Reembolso' en el historial."
            ),
            "_descuento_ticket": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _descuento_ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un `RedemptionTicket` de descuento (%) vigente para un usuario y sede, y lo devuelve.'
            ),
            "test_pay_reservation_manual_aplica_descuento_de_canje": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: El pago manual con un ticket de descuento aplica el porcentaje al monto, marca el ticket USADO y ligado a la reserva, y acredita puntos sobre la base ya descontada.'
            ),
            "test_pay_reservation_manual_idempotente_con_descuento": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un segundo pago manual de una reserva ya pagada no aplica descuento (0.0) ni cambia el método.'
            ),
            "test_pay_reservation_manual_rechaza_ticket_de_otra_sucursal": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Usar un ticket de otra sucursal en el pago manual es rechazado con 400 y la reserva queda PENDIENTE.'
            ),
            "test_pay_reservation_manual_sin_usuario_en_reserva_y_con_ticket_rechaza": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Si la reserva no tiene usuario, usar un ticket de canje es rechazado con 400.'
            ),
            "test_create_admin_reservation_con_descuento_crea_y_paga": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Crear una reserva pagada con ticket de descuento aplica el porcentaje al monto, marca el ticket USADO y deja la reserva PAGADO.'
            ),
            "test_confirm_reservation_payment_aplica_descuento": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Confirmar el pago de una reserva pendiente con ticket aplica el descuento, actualiza el monto final, marca PAGADO y consume el ticket.'
            ),
            "test_confirm_reservation_payment_con_ticket_invalido_rechaza": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Confirmar el pago con un ticket inválido (otra sucursal) es rechazado con 400 y deja la reserva PENDIENTE.'
            ),
            "test_reservation_available_redemptions_lista_descuentos": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista los descuentos disponibles para una reserva con usuario: incluye el ticket con su `descuento_peso` y `monto_final` calculados.'
            ),
            "test_reservation_available_redemptions_vacio_sin_usuario": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Una reserva sin usuario vinculado no tiene descuentos disponibles (lista vacía).'
            ),
            "test_admin_available_redemptions_por_usuario": (
                '💡 LA IDEA: Comprobar el escenario de admin available redemptions por usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista los canjes disponibles de un usuario por sede (un ticket) y devuelve vacío si el user_id es None.'
            ),
            "test_admin_available_redemptions_sin_tickets_vacia": (
                '💡 LA IDEA: Comprobar el escenario de admin available redemptions sin tickets vacia.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un usuario sin tickets de canje devuelve una lista vacía.'
            ),
            "test_admin_available_redemptions_user_id_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Consultar canjes de un user_id inexistente responde 404.'
            ),
            "test_redemption_info_edicion_reserva_pagada_con_descuento": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: La info de canje de una reserva pagada con descuento indica `aplica` True, fuente 'aplicado' y el ticket y porcentaje usados."
            ),
            "test_redemption_info_edicion_reserva_con_descuento_vigente": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: La info de canje de una reserva sin descuento aplicado pero con un ticket vigente indica `aplica` True y fuente 'vigente'."
            ),
            "test_redemption_info_edicion_reserva_sin_descuento": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: La info de canje de una reserva sin descuento indica `aplica` False y fuente None.'
            ),
            "test_editar_reserva_pagada_con_descuento_mantiene_descuento_al_recalcular": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Al recalcular por extensión de una reserva pagada con descuento porcentual, el nuevo monto y la diferencia se calculan sobre la base ya descontada, manteniendo el ticket USADO.'
            ),
            "test_get_new_reservations_count_sin_reservas": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin reservas, el contador devuelve count 0 y latest_id 0.'
            ),
            "test_get_new_reservations_count_incrementa_con_nuevas_reservas": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: El contador devuelve cuántas reservas se crearon después del `since_id` (2 nuevas) y cuál es el último id.'
            ),
            "test_get_new_reservations_count_aislamiento_sucursales": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: El local_admin solo cuenta las reservas de su sede (1) mientras el admin global cuenta las de ambas (2).'
            ),
        },
    },
    "tests/test_admin_settings.py": {
        "proposito": 'Test de `routes/admin/settings.py`: lectura de settings con visibilidad global/por sede y capacidades de aforo con fallbacks, y actualización de precios y capacidades (creación automática de aforo, re-suma de reservas, notificación de ocupación tolerante a fallos y rechazo de claves/roles no permitidos).',
        "simbolos": {
            "FakeUser": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Clase mínima que emula al usuario autenticado con `rol` y `sucursal`, inyectada vía override de `get_current_user`.'
            ),
            "FakeUser.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeUser.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el rol (por defecto ADMIN) y la sucursal (por defecto None) del usuario simulado.'
            ),
            "CURRENT": (
                '💡 LA IDEA: Comprobar el escenario de CURRENT.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Dict global con el usuario actual fake que usa el override; se reemplaza por test y se resetea automáticamente.'
            ),
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Arma una `FastAPI` con el router de settings, engine SQLite en memoria con la sede 'Centro', y overrides de `get_db` y `get_current_user`; entrega el `TestClient` y la fábrica de sesiones."
            ),
            "_set_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _set_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Fija el usuario actual con el rol (enum o string) y la sucursal indicados.'
            ),
            "_reset_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reset_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un estado inicial predecible y reproducible antes de ejecutar cada caso de prueba.\n\n'
                '⚙️ FUNCIONAMIENTO: Restaura el usuario actual a un FakeUser ADMIN tras cada test.'
            ),
            "_seed_setting": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_setting.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un `Settings` con clave, valor y sucursal, y lo devuelve.'
            ),
            "_seed_aforo": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_aforo.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un `ParkingAforo` con capacidades y ocupaciones por defecto (sobrescribibles) para una sucursal y lo devuelve.'
            ),
            "_get_aforo": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _get_aforo.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Recupera el `ParkingAforo` de una sucursal y lo devuelve.'
            ),
            "_get_setting": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _get_setting.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Recupera un `Settings` por clave y sucursal y lo devuelve.'
            ),
            "test_get_settings_admin_global_con_aforo": (
                '💡 LA IDEA: Comprobar el escenario de get settings admin global con aforo.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: El admin global recibe sus settings y las capacidades/ocupación del aforo global (total 50, motos 10, camionetas 5, reservas 0, ocupación 4).'
            ),
            "test_get_settings_local_admin_solo_su_sede": (
                '💡 LA IDEA: Comprobar el escenario de get settings local admin solo su sede.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin solo ve los settings de 'Centro' (no el global) y las capacidades de su aforo."
            ),
            "test_get_settings_admin_sin_aforo_no_incluye_capacidades": (
                '💡 LA IDEA: Comprobar el escenario de get settings admin sin aforo no incluye capacidades.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin aforo configurado, la respuesta no incluye claves de capacidad y `sucursal_nombre` es None.'
            ),
            "test_get_settings_aforo_basico_getattr_fallbacks": (
                '💡 LA IDEA: Comprobar el escenario de get settings aforo basico getattr fallbacks.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Con un aforo que solo tiene los campos básicos, los campos ausentes se rellenan con los defaults de `getattr` (0/5) sin romper.'
            ),
            "test_get_settings_staff_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El rol staff no puede leer settings: responde 403.'
            ),
            "test_update_price_capacidad_crea_aforo_y_notifica": (
                '💡 LA IDEA: Comprobar el escenario de update price capacidad crea aforo y notifica.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar `capacidad_total` crea el aforo con defaults, guarda la capacidad, notifica la ocupación y NO persiste un setting de esa clave.'
            ),
            "test_update_price_capacidad_existente_actualiza": (
                '💡 LA IDEA: Comprobar el escenario de update price capacidad existente actualiza.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar la capacidad de un aforo existente la modifica sin crear otro registro de aforo.'
            ),
            "test_update_price_reservas_autos_resuma_capacidad_reservas": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar `capacidad_reservas_autos` y `capacidad_reservas_motos` re-suma el total de `capacidad_reservas`.'
            ),
            "test_update_price_capacidad_camionetas": (
                '💡 LA IDEA: Comprobar el escenario de update price capacidad camionetas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar `capacidad_camionetas` guarda el nuevo valor en el aforo.'
            ),
            "test_update_price_notificacion_que_falla_devuelve_ok": (
                '💡 LA IDEA: Comprobar el escenario de update price notificacion que falla devuelve ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                "⚙️ FUNCIONAMIENTO: Si la notificación de ocupación lanza una excepción, el endpoint igual devuelve 'ok'."
            ),
            "test_update_price_existente_actualiza_setting": (
                '💡 LA IDEA: Comprobar el escenario de update price existente actualiza setting.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                "⚙️ FUNCIONAMIENTO: Actualizar un setting existente ('precio_hora') guarda el nuevo valor y devuelve el mensaje con la sede 'Global'."
            ),
            "test_update_price_nuevo_setting_global": (
                '💡 LA IDEA: Comprobar el escenario de update price nuevo setting global.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Crear un setting inexistente para el admin global lo guarda con sucursal None bajo la sede 'Global'."
            ),
            "test_update_price_local_admin_guarda_en_su_sede": (
                '💡 LA IDEA: Comprobar el escenario de update price local admin guarda en su sede.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin guarda el setting en su sede ('Centro') y no crea el global."
            ),
            "test_update_price_clave_no_permitida_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Una clave fuera del listado permitido responde 400 con 'Clave de configuración no permitida' y no persiste nada."
            ),
            "test_update_price_staff_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: El rol staff no puede actualizar precios: responde 403.'
            ),
            "test_update_price_capacidad_reservas_motos_y_camionetas": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar `capacidad_reservas_camionetas` se refleja en el total `capacidad_reservas`.'
            ),
        },
    },
    "tests/test_admin_support_routes.py": {
        "proposito": 'Test de `routes/admin/support.py` (soporte y tickets admin): contador de pendientes, marcado de notificaciones leídas, detalle de un ticket con sus mensajes, listado con filtro de estado y actualización de estado/respuesta, con aislamiento por sucursal del local_admin.',
        "simbolos": {
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea el engine SQLite en memoria, sobreescribe `get_db` y `get_operational_user` con un admin, resetea el limiter y entrega un `TestClient` junto con la fábrica de sesiones.'
            ),
            "_seed_ticket": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un usuario cliente y un `SupportTicket` con email, sucursal y estado dados, y devuelve el id del ticket.'
            ),
            "_seed_message": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_message.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrega un `SupportTicketMessage` a un ticket con autor y texto.'
            ),
            "test_pending_count_admin": (
                '💡 LA IDEA: Comprobar el escenario de pending count admin.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El contador de pendientes incluye al menos el ticket 'Pendiente' (excluye el 'Resuelto')."
            ),
            "test_pending_count_excluye_terminales": (
                '💡 LA IDEA: Comprobar el escenario de pending count excluye terminales.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: El contador excluye los estados terminales: con un 'Cancelado' y un 'En Revisión' devuelve count 1."
            ),
            "test_pending_count_zero": (
                '💡 LA IDEA: Comprobar el escenario de pending count zero.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin tickets, el contador devuelve 0.'
            ),
            "test_mark_ticket_notifs_read": (
                '💡 LA IDEA: Comprobar el escenario de mark ticket notifs read.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Marcar como leídas las notificaciones de un ticket responde 200 con `marked` booleano.'
            ),
            "test_mark_ticket_notifs_read_403_otra_sucursal": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un local_admin de 'Centro' no puede marcar notificaciones de un ticket de 'Norte': responde 403."
            ),
            "test_get_admin_ticket_detail": (
                '💡 LA IDEA: Comprobar el escenario de get admin ticket detail.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El detalle de un ticket devuelve su id, el email del cliente y el estado, con su lista de mensajes.'
            ),
            "test_get_admin_ticket_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Pedir un ticket inexistente responde 404.'
            ),
            "test_get_admin_ticket_403_otra_sucursal": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un local_admin no puede ver el detalle de un ticket de otra sucursal: responde 403.'
            ),
            "test_update_admin_ticket_403_otra_sucursal": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un local_admin no puede actualizar un ticket de otra sucursal: responde 403.'
            ),
            "test_list_admin_tickets": (
                '💡 LA IDEA: Comprobar el escenario de list admin tickets.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El listado de tickets devuelve 200 con una lista.'
            ),
            "test_list_admin_tickets_filtro_estado": (
                '💡 LA IDEA: Comprobar el escenario de list admin tickets filtro estado.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El listado con filtro `estado='Resuelto'` devuelve solo tickets con ese estado."
            ),
            "test_update_admin_ticket_estado": (
                '💡 LA IDEA: Comprobar el escenario de update admin ticket estado.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar el estado de un ticket responde 200 con el nuevo estado.'
            ),
            "test_update_admin_ticket_con_respuesta": (
                '💡 LA IDEA: Comprobar el escenario de update admin ticket con respuesta.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar un ticket con estado y respuesta responde 200 e incluye los mensajes en el cuerpo.'
            ),
            "test_update_admin_ticket_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar un ticket inexistente responde 404.'
            ),
        },
    },
    "tests/test_admin_users_routes.py": {
        "proposito": 'Test de `routes/admin/users.py`: CRUD de usuarios admin (listado con filtro por sede del local_admin, alta con restricción de rol, actualización, cambio de rol, toggle de bloqueo, ajuste de saldo, cambio de contraseña y borrado sin permitir la propia cuenta).',
        "simbolos": {
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea el engine SQLite en memoria con las sedes 'Quilmes' y 'Lanús', sobreescribe `get_db` y `get_local_manager` con un ADMIN global, resetea el limiter y entrega un `TestClient` junto con la fábrica de sesiones."
            ),
            "client_local": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client_local.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona un cliente HTTP preconfigurado con las credenciales necesarias para consultar los endpoints del sistema.\n\n'
                "⚙️ FUNCIONAMIENTO: Variante del fixture `client` que inyecta un LOCAL_MANAGER de 'Quilmes', para probar las restricciones del admin de sede."
            ),
            "_seed_user": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _seed_user.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un `User` con email, DNI, rol, sucursal, estado de bloqueo e id opcionales, y devuelve su id.'
            ),
            "_valid_create": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _valid_create.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma un payload de alta de usuario válido (nombre, apellido, DNI, teléfono, email y contraseña).'
            ),
            "test_list_users_admin": (
                '💡 LA IDEA: Comprobar el escenario de list users admin.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El admin global lista usuarios (200) e incluye el email sembrado.'
            ),
            "test_list_users_local_solo_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de list users local solo sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin de 'Quilmes' ve a los staff de su sede pero no a los de 'Lanús'."
            ),
            "test_list_users_local_ve_clientes_otra_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de list users local ve clientes otra sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin ve a los clientes de todas las sedes (incluye el de 'Lanús')."
            ),
            "test_create_user_global": (
                '💡 LA IDEA: Comprobar el escenario de create user global.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El admin global crea un usuario y recibe 200 con email y rol 'user' por defecto."
            ),
            "test_create_user_duplicate_email": (
                '💡 LA IDEA: Comprobar el escenario de create user duplicate email.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Crear un usuario con email ya existente responde 400.'
            ),
            "test_create_user_local_no_puede_admin": (
                '💡 LA IDEA: Comprobar el escenario de create user local no puede admin.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin no puede crear usuarios con rol 'admin' ni 'staff': responde 403 en ambos casos."
            ),
            "test_create_user_local_si_puede_cliente": (
                '💡 LA IDEA: Comprobar el escenario de create user local si puede cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin sí puede crear un usuario 'user', que queda en su sede ('Quilmes')."
            ),
            "test_update_user_admin_ok": (
                '💡 LA IDEA: Comprobar el escenario de update user admin ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El admin global actualiza un usuario (nombre y rol) y recibe 'ok'."
            ),
            "test_update_user_local_no_promueve_staff": (
                '💡 LA IDEA: Comprobar el escenario de update user local no promueve staff.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin no puede promover a un usuario a 'staff': responde 403."
            ),
            "test_update_user_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualizar un usuario inexistente responde 404.'
            ),
            "test_update_user_local_fuera_sucursal": (
                '💡 LA IDEA: Comprobar el escenario de update user local fuera sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El local_admin no puede actualizar a un usuario de otra sede: responde 403.'
            ),
            "test_update_user_local_asigna_admin_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin no puede asignar el rol 'admin' por la actualización: responde 403."
            ),
            "test_change_user_role_ok": (
                '💡 LA IDEA: Comprobar el escenario de change user role ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El admin global cambia el rol de un usuario a 'staff' con 'ok'."
            ),
            "test_change_user_role_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambiar el rol de un usuario inexistente responde 404.'
            ),
            "test_change_user_role_a_user_notifica": (
                '💡 LA IDEA: Comprobar el escenario de change user role a user notifica.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                "⚙️ FUNCIONAMIENTO: Cambiar el rol a 'user' responde 'ok' (dispara la notificación al usuario)."
            ),
            "test_change_user_role_local_asigna_admin": (
                '💡 LA IDEA: Comprobar el escenario de change user role local asigna admin.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin no puede asignar el rol 'admin' por este endpoint: responde 403."
            ),
            "test_change_user_role_local_no_promueve_staff": (
                '💡 LA IDEA: Comprobar el escenario de change user role local no promueve staff.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin no puede promover a 'staff': responde 403."
            ),
            "test_change_user_role_local_si_cambia_user_a_user": (
                '💡 LA IDEA: Comprobar el escenario de change user role local si cambia user a user.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: El local_admin sí puede mantener/cambiar de 'user' a 'user' dentro de su sede: responde 200."
            ),
            "test_toggle_user_block_ok": (
                '💡 LA IDEA: Comprobar el escenario de toggle user block ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El toggle de bloqueo alterna `is_blocked` de False a True y de vuelta.'
            ),
            "test_toggle_user_block_propia_cuenta": (
                '💡 LA IDEA: Comprobar el escenario de toggle user block propia cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El admin no puede bloquear su propia cuenta: responde 400.'
            ),
            "test_toggle_user_block_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: El toggle de un usuario inexistente responde 404.'
            ),
            "test_adjust_user_balance_ok": (
                '💡 LA IDEA: Comprobar el escenario de adjust user balance ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                "⚙️ FUNCIONAMIENTO: Ajustar el saldo de un usuario responde 'ok'."
            ),
            "test_adjust_user_balance_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Ajustar el saldo de un usuario inexistente responde 404.'
            ),
            "test_change_user_password_ok": (
                '💡 LA IDEA: Comprobar el escenario de change user password ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Cambiar la contraseña de un usuario responde 'ok'."
            ),
            "test_change_user_password_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambiar la contraseña de un usuario inexistente responde 404.'
            ),
            "test_delete_user_ok": (
                '💡 LA IDEA: Comprobar el escenario de delete user ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Eliminar un usuario responde 'ok'."
            ),
            "test_delete_user_propia_cuenta": (
                '💡 LA IDEA: Comprobar el escenario de delete user propia cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El admin no puede eliminar su propia cuenta: responde 400.'
            ),
            "test_delete_user_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Eliminar un usuario inexistente responde 404.'
            ),
        },
    },
}
