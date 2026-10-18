"""Explicaciones analizadas de tests (parte 4: multi-tenant, validaciones, notificaciones,
OAuth, ocupación, OCR, pay-stay, pagos, preprocesador, rate limiting y reportes de acceso)."""

ANALISIS: dict[str, dict] = {
    "tests/test_multi_tenant_isolation.py": {
        "proposito": 'Verifica el aislamiento multiempresa (multi-tenant) por organization_id: que un Admin General de una organización no vea ni opere datos (usuarios, sucursales, promociones, configuraciones, reservas, cámaras) de otra organización, y que el super admin (org principal) sí pueda operar a través de todas.',
        "simbolos": {
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: crea una base SQLite en memoria con todo el esquema, sobrescribe get_db de la app FastAPI, reinicia el limitador de rate limiting y devuelve (TestClient, sessionmaker); al terminar restaura las dependencias y el limiter.'
            ),
            "_crear_org": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_org.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta una Organization con nombre, flag es_principal y activa=True, y devuelve su id.'
            ),
            "_crear_usuario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un User con rol, email, organización, sucursal opcional y contraseña hasheada (DNI aleatorio para evitar duplicados); lo usa cada test como admin, staff o cliente.'
            ),
            "_crear_branch": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_branch.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta una ParkingBranch activa con dirección/horario de prueba y la asigna a la organización dada.'
            ),
            "_crear_promo": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_promo.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta una Promotion activa de 10 puntos en la organización dada.'
            ),
            "_branch_id": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _branch_id.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca el id de una sucursal por nombre Y organización; devuelve None si no existe.'
            ),
            "_crear_access_log": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_access_log.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un AccessLog de ENTRADA (con pago opcional por monto y salida opcional) para simular estadías en curso en una sucursal.'
            ),
            "_crear_reserva": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea una Reservation pagada y activa (tipo hora, una hora en el futuro) sobre la sucursal dada, para probar el listado de reservas admin.'
            ),
            "_crear_ticket": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un SupportTicket pendiente de un usuario en una sucursal, para el contador de pendientes.'
            ),
            "_crear_setting": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_setting.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta una fila Settings (clave/valor) en la organización dada.'
            ),
            "_login": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _login.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Autentica contra POST /v1/auth/login con email/contraseña y devuelve el access_token; falla el test si el login no es 200.'
            ),
            "_headers": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _headers.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el header Authorization Bearer con el token obtenido por _login.'
            ),
            "test_admin_solo_ve_sus_usuarios": (
                '💡 LA IDEA: Comprobar el escenario de admin solo ve sus usuarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/admin/users como admin de Org A: el listado incluye al cliente de su org y excluye al cliente de Org B.'
            ),
            "test_admin_solo_ve_sus_sucursales": (
                '💡 LA IDEA: Comprobar el escenario de admin solo ve sus sucursales.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/admin/branches: el admin de Org A ve solo su sucursal; la sucursal homónima de Org B no aparece.'
            ),
            "test_admin_solo_ve_sus_promociones": (
                '💡 LA IDEA: Comprobar el escenario de admin solo ve sus promociones.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/admin/promotions: solo se listan las promociones de la organización del admin.'
            ),
            "test_org_nueva_puede_crear_sucursal_con_nombre_ya_usado": (
                '💡 LA IDEA: Comprobar el escenario de org nueva puede crear sucursal con nombre ya usado.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: POST /v1/admin/branches con nombre 'CENTRO' que ya existe en otra organización devuelve 200: los nombres de sucursal no son globales, son únicos por organización."
            ),
            "test_sedes_con_mismo_nombre_no_se_cruzan_entre_orgs": (
                '💡 LA IDEA: Comprobar el escenario de sedes con mismo nombre no se cruzan entre orgs.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea staff por nombre de sucursal 'CENTRO' en Org B y verifica en BD que su sucursal_id apunta a la sucursal de Org B, no a la homónima de Org A (resolución de sucursal desambiguada por organización)."
            ),
            "test_configuraciones_aisladas_por_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de configuraciones aisladas por organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/admin/settings devuelve el precio_hora de la org del admin (111.0), no el de la otra org (999.0).'
            ),
            "test_financial_summary_aislado_por_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de financial summary aislado por organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/reports/financial-summary: el admin de Org A ve 1000 de recaudado; el de Org B ve 0 aunque haya pagos en la sucursal de Org A.'
            ),
            "test_current_occupancy_aislado_por_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de current occupancy aislado por organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/parking/current-occupancy: el admin de Org A ve el vehículo estacionado en su sucursal; el de Org B recibe lista vacía.'
            ),
            "test_support_pending_count_aislado_por_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de support pending count aislado por organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/admin/support-tickets/pending-count: cuenta 1 el admin de la org del ticket y 0 el de la otra.'
            ),
            "test_reservas_admin_aisladas_por_organizacion": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/admin/reservations: solo devuelve las reservas de sucursales de la organización del admin.'
            ),
            "test_camaras_admin_aisladas_por_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de camaras admin aisladas por organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: GET /v1/system/cameras: el admin de Org A ve su cámara; el de Org B ve lista vacía.'
            ),
            "_user_id": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _user_id.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el id de un usuario por email (o None si no existe).'
            ),
            "test_admin_no_puede_editar_usuario_de_otra_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de admin no puede editar usuario de otra organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: PATCH /v1/admin/users/{id} sobre un usuario de otra organización devuelve 403.'
            ),
            "test_admin_no_puede_operar_sucursal_de_otra_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de admin no puede operar sucursal de otra organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: POST /v1/admin/branches/{id}/toggle sobre una sucursal ajena devuelve 403.'
            ),
            "test_admin_no_puede_operar_camara_de_otra_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de admin no puede operar camara de otra organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: PUT /v1/system/cameras/{id} sobre una cámara de sucursal ajena devuelve 403.'
            ),
            "test_super_admin_ve_usuarios_de_otra_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de super admin ve usuarios de otra organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Un admin en la organización principal (es_principal=True) ve en /v1/admin/users a usuarios de cualquier otra organización.'
            ),
            "test_super_admin_puede_editar_usuario_de_otra_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de super admin puede editar usuario de otra organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: PATCH sobre un usuario de otra org con super admin devuelve 200.'
            ),
            "test_super_admin_puede_borrar_admin_de_otra_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de super admin puede borrar admin de otra organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: DELETE /v1/admin/users/{id} de un admin ajeno con super admin devuelve 200 y hace borrado lógico (is_deleted=True y email renombrado a 'eliminado-...')."
            ),
            "test_admin_no_principal_no_puede_borrar_admin_de_otra_organizacion": (
                '💡 LA IDEA: Comprobar el escenario de admin no principal no puede borrar admin de otra organizacion.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: DELETE de un admin de otra org con un admin NO principal devuelve 403: solo el super admin puede borrar admins de otras organizaciones.'
            ),
        },
    },
    "tests/test_new_validations.py": {
        "proposito": 'Agrupa validaciones de negocio agregadas tras auditorías: borrar vehículos con reservas activas o con el auto dentro del predio, bloqueo de usuarios, email duplicado, pisos ocupados, y la validación de formato de patente LATAM en alta de vehículos, validación de placas, entrada manual y cobro.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: crea y destruye todas las tablas sobre una SQLite en memoria y cede una sesión para testear servicios y rutas directamente.'
            ),
            "test_delete_vehicle_with_active_reservation_fails": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Delete_user_vehicle lanza HTTP 400 si el vehículo tiene una reserva Activa/Pagada en curso (menciona 'reservas activas')."
            ),
            "test_delete_vehicle_parked_inside_fails": (
                '💡 LA IDEA: Comprobar el escenario de delete vehicle parked inside fails.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Delete_user_vehicle lanza 400 si existe un AccessLog de ENTRADA sin salida para esa patente (el vehículo está 'ingresado' en el predio)."
            ),
            "test_add_vehicle_camioneta_and_blocked_check": (
                '💡 LA IDEA: Comprobar el escenario de add vehicle camioneta and blocked check.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Add_user_vehicle: un usuario bloqueado recibe 403; al desbloquearlo, alta de Camioneta exitosa con patente normalizada sin espacios (AB123CD).'
            ),
            "test_update_user_duplicate_email_fails": (
                '💡 LA IDEA: Comprobar el escenario de update user duplicate email fails.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: UserService.update_user con un email ya registrado por otro usuario lanza 400 ('correo ya está registrado')."
            ),
            "test_delete_floor_with_occupancy_fails": (
                '💡 LA IDEA: Comprobar el escenario de delete floor with occupancy fails.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Delete_floor de la ruta admin rechaza (400) borrar un piso con ocupación actual distinta de cero.'
            ),
            "test_is_valid_plate_formatos_latam_reconocidos": (
                '💡 LA IDEA: Comprobar el escenario de is valid plate formatos latam reconocidos.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Is_valid_plate acepta formatos LATAM (Mercosur, clásicos, moto) y rechaza placas cortas, vacías o con espacios.'
            ),
            "test_add_vehicle_rechaza_formato_invalido": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Add_user_vehicle lanza 400 con 'Formato de patente inválido' y no persiste el vehículo si la patente no valida."
            ),
            "test_validate_plate_rechaza_formato_y_no_registra": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: AccessService.validate_plate con placa inválida devuelve status 'denied' y no crea ningún AccessLog."
            ),
            "test_manual_entry_rechaza_formato_invalido": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: AccessService.manual_entry lanza 400 si la patente no tiene formato válido.'
            ),
            "test_process_payment_rechaza_formato_invalido": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: BillingService.process_payment devuelve status 'error' con mensaje de formato inválido para patente no válida."
            ),
        },
    },
    "tests/test_notifications.py": {
        "proposito": 'Cubre el sistema de notificaciones a usuarios: CRUD de notificaciones, avisos que se emiten al responder tickets, pagar reservas/estadías, cambiar contraseña, modificar reservas, canjear puntos y registrar/borrar vehículos; además el store en memoria de salidas impagas (popup PENDING_EXIT) con TTL.',
        "simbolos": {
            "db_session": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db_session.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: SQLite en memoria con el esquema completo; cede una sesión de SQLAlchemy para los tests de servicio/rutas.'
            ),
            "test_user_notification_crud": (
                '💡 LA IDEA: Comprobar el escenario de user notification crud.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Ciclo completo de UserNotificationService: crear (no leída), contar no leídas, marcar leída, borrar leídas y verificar el total final.'
            ),
            "test_support_ticket_response_notification": (
                '💡 LA IDEA: Comprobar el escenario de support ticket response notification.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuando el admin resuelve un ticket con respuesta, el usuario recibe una notificación tipo SUPPORT_RESPONSE con el estado y el texto de la respuesta.'
            ),
            "test_delete_read_notifications_route": (
                '💡 LA IDEA: Comprobar el escenario de delete read notifications route.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Los endpoints clear_read_notifications y delete_notification de la ruta de usuario borran solo las leídas y la individual indicada, dejando el resto.'
            ),
            "test_worker_reminders_no_duplicate_on_delete": (
                '💡 LA IDEA: Comprobar el escenario de worker reminders no duplicate on delete.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el usuario borra el recordatorio de reserva próxima, el siguiente loop de _process_reminders no lo re-emite porque recordatorio_confirmado quedó en True.'
            ),
            "test_worker_started_reservations_no_duplicate_on_delete": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: _process_started_reservations activa la reserva vencida, notifica una vez, y al borrarse la notificación no se duplica en el siguiente loop (la reserva ya es Activa).'
            ),
            "test_support_status_changed_without_reply": (
                '💡 LA IDEA: Comprobar el escenario de support status changed without reply.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambiar solo el estado del ticket (sin texto de respuesta) genera una notificación SUPPORT_STATUS_CHANGED con el nuevo estado.'
            ),
            "test_manual_reservation_payment_emits_points_notification": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Pay_reservation_manual emite una notificación POINTS_EARNED al usuario que abonó.'
            ),
            "test_onsite_stay_payment_emits_notifications": (
                '💡 LA IDEA: Comprobar el escenario de onsite stay payment emits notifications.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: BillingService.process_payment de una estadía en curso emite STAY_PAID y POINTS_EARNED al dueño del vehículo.'
            ),
            "test_user_change_password_notification": (
                '💡 LA IDEA: Comprobar el escenario de user change password notification.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Change_password emite SECURITY_PASSWORD_CHANGED al usuario tras el cambio exitoso.'
            ),
            "test_user_modify_reservation_notification": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Modify_reservation (extender fecha_fin) emite RESERVATION_MODIFIED.'
            ),
            "test_points_redemption_notification_format": (
                '💡 LA IDEA: Comprobar el escenario de points redemption notification format.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                "⚙️ FUNCIONAMIENTO: El canje de puntos por voucher emite PROMO_REDEEMED con '(Voucher #id)' en el mensaje y verifica que el ticket venza 30 días después de creado."
            ),
            "test_vehicle_registration_and_removal_notifications": (
                '💡 LA IDEA: Comprobar el escenario de vehicle registration and removal notifications.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Add_user_vehicle y delete_user_vehicle emiten VEHICLE_REGISTERED y VEHICLE_REMOVED con la patente normalizada en el mensaje.'
            ),
            "test_pending_exit_set_get_clear": (
                '💡 LA IDEA: Comprobar el escenario de pending exit set get clear.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: El store estático de NotificationService guarda, recupera y limpia el payload de salida impaga por sucursal.'
            ),
            "test_pending_exit_expira_por_ttl": (
                '💡 LA IDEA: Comprobar el escenario de pending exit expira por ttl.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Get_pending_exit devuelve None si el timestamp del payload superó el TTL _PENDING_EXIT_TTL (simulado con monkeypatch del reloj).'
            ),
            "test_notify_pending_exit_guarda_aunque_no_haya_manager": (
                '💡 LA IDEA: Comprobar el escenario de notify pending exit guarda aunque no haya manager.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Notify_pending_exit no truena si _occupancy_manager es None; igualmente deja el payload disponible para consulta posterior.'
            ),
        },
    },
    "tests/test_oauth.py": {
        "proposito": 'Tests unitarios del servicio de login social (oauth_service): firma/verificación del state con TTL, proveedores habilitados según credenciales, URL de autorización, intercambio de código por token, userinfo de Google normalizado y registro de usuarios nuevos vía código de signup.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: SQLite en memoria con esquema completo; cede una sesión para los tests de signup.'
            ),
            "FakeResp": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de respuesta HTTP: guarda payload y status; raise_for_status lanza HTTPException con el status si es >= 400.'
            ),
            "FakeResp.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el payload JSON y el código de estado (por defecto 200).'
            ),
            "FakeResp.raise_for_status": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.raise for status.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Simula requests: lanza HTTPException si status_code >= 400; si no, no hace nada.'
            ),
            "FakeResp.json": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.json.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el payload simulado.'
            ),
            "test_state_sign_and_verify_roundtrip": (
                '💡 LA IDEA: Comprobar el escenario de state sign and verify roundtrip.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Sign_state('google') genera un state que verify_state valida correctamente con el mismo proveedor."
            ),
            "test_state_rejects_tampered_signature": (
                '💡 LA IDEA: Comprobar el escenario de state rejects tampered signature.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Un state con la firma alterada (últimos caracteres cambiados) es rechazado.'
            ),
            "test_state_rejects_wrong_provider": (
                '💡 LA IDEA: Comprobar el escenario de state rejects wrong provider.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Un state firmado para google no verifica como facebook.'
            ),
            "test_state_rejects_expired": (
                '💡 LA IDEA: Comprobar el escenario de state rejects expired.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un state cuyo timestamp supera OAUTH_STATE_TTL_SECONDS (simulado) es rechazado.'
            ),
            "test_state_rejects_short_input": (
                '💡 LA IDEA: Comprobar el escenario de state rejects short input.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Entradas demasiado cortas ('abc') se rechazan sin error."
            ),
            "test_enabled_providers_empty_when_no_credentials": (
                '💡 LA IDEA: Comprobar el escenario de enabled providers empty when no credentials.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin client_id/secret de Google ni Facebook, enabled_providers devuelve lista vacía.'
            ),
            "test_enabled_providers_with_google_credentials": (
                '💡 LA IDEA: Comprobar el escenario de enabled providers with google credentials.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Con credenciales solo de Google, el listado contiene el proveedor 'google' con label 'Google'."
            ),
            "test_get_authorize_url_unconfigured_raises_503": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Get_authorize_url de un proveedor sin credenciales lanza HTTP 503.'
            ),
            "test_get_authorize_url_google_build": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: La URL de Google incluye accounts.google.com, client_id, redirect_uri codificado al callback, state y prompt=select_account.'
            ),
            "test_unknown_provider_raises_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un proveedor desconocido ('github') lanza HTTP 404."
            ),
            "test_exchange_code_returns_token": (
                '💡 LA IDEA: Comprobar el escenario de exchange code returns token.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Exchange_code devuelve el access_token del proveedor cuando el POST del token devuelve 200 (requests.post parcheado).'
            ),
            "test_exchange_code_failure_raises_502": (
                '💡 LA IDEA: Comprobar el escenario de exchange code failure raises 502.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el intercambio del código falla por red, se lanza HTTP 502.'
            ),
            "test_fetch_google_userinfo_normalizes": (
                '💡 LA IDEA: Comprobar el escenario de fetch google userinfo normalizes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Fetch_user_info normaliza el email de Google (minúsculas y sin espacios) y separa nombre y apellido.'
            ),
            "test_fetch_userinfo_without_email_raises_502": (
                '💡 LA IDEA: Comprobar el escenario de fetch userinfo without email raises 502.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el userinfo no trae email, se lanza HTTP 502.'
            ),
            "test_signup_code_roundtrip": (
                '💡 LA IDEA: Comprobar el escenario de signup code roundtrip.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Issue_oauth_signup_code + decode_oauth_signup_code devuelven el payload con sub normalizado, purpose oauth_signup, provider y nombre.'
            ),
            "test_signup_code_rejects_other_purpose": (
                '💡 LA IDEA: Comprobar el escenario de signup code rejects other purpose.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Un JWT de propósito 'recovery' (reset de contraseña) no se acepta como código de signup OAuth."
            ),
            "test_complete_oauth_signup_creates_user": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Complete_oauth_signup crea el usuario con email, DNI, teléfono, nombre/apellido, rol 'user' y password_hash generado."
            ),
            "test_complete_oauth_signup_rejects_invalid_code": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un código que no es JWT válido lanza HTTP 400.'
            ),
            "test_complete_oauth_signup_rejects_duplicate_email": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: El signup OAuth rechaza (400) si el email ya existe en la BD.'
            ),
            "test_complete_oauth_signup_rejects_duplicate_dni": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: El signup OAuth rechaza (400) si el DNI ya existe en la BD.'
            ),
        },
    },
    "tests/test_occupancy_service.py": {
        "proposito": 'Tests del OccupancyService: capacidades por defecto y desde aforo, cálculo de capacidades por sucursal (planta baja + pisos + reservas vigentes), ocupación actual (excluye salidas, cortesía de 10 minutos, deuda acumulada y reservas pagadas).',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Fixture: SQLite en memoria con dos sucursales ('Centro' y 'Sede') y precios por hora/30min en Centro; destruye las tablas al terminar."
            ),
            "_reserva": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea una Reservation con sucursal, tipo de vehículo, estados y ventana de fechas configurables (pagada y pendiente por defecto).'
            ),
            "_log": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _log.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Inserta un AccessLog con id fijo, patente, tipo ENTRADA/SALIDA, sucursal, fecha, reserva opcional y flag de pago.'
            ),
            "test_default_capacities": (
                '💡 LA IDEA: Comprobar el escenario de default capacities.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Default_capacities devuelve los valores por defecto del sistema: 20 autos, 10 motos, 5 camionetas y disponibilidad 20.'
            ),
            "test_capacities_from_aforo": (
                '💡 LA IDEA: Comprobar el escenario de capacities from aforo.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Capacities_from_aforo traduce un ParkingAforo a capacidades/disponibilidades por tipo y completa con defaults las capacidades de reservas no seteadas.'
            ),
            "test_calculate_branch_capacities_suma_pb_y_pisos": (
                '💡 LA IDEA: Comprobar el escenario de calculate branch capacities suma pb y pisos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que el sistema respete los límites de aforo y no admita vehículos cuando la capacidad está agotada.\n\n'
                '⚙️ FUNCIONAMIENTO: Calculate_branch_capacities suma las capacidades de la planta baja (aforo) más las de cada piso, incluyendo defaults de reservas.'
            ),
            "test_ocupacion_reservas_vigentes_cuenta_por_tipo": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Ocupacion_reservas_vigentes cuenta reservas pagadas por tipo de vehículo y excluye las no pagadas.'
            ),
            "test_calculate_branch_capacities_incluye_reservas_vigentes": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Las capacidades de la sucursal descuentan la ocupación de reservas vigentes del tipo correspondiente.'
            ),
            "test_current_occupancy_excluye_salidas": (
                '💡 LA IDEA: Comprobar el escenario de current occupancy excluye salidas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Current_occupancy lista solo los vehículos sin salida registrada (los que tienen SALIDA quedan excluidos).'
            ),
            "test_current_occupancy_cortesia_dentro_de_10min": (
                '💡 LA IDEA: Comprobar que las estadías dentro del tiempo de cortesía salgan sin cargo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que las estadías breves dentro del tiempo de cortesía puedan salir sin costo ni retención innecesaria.\n\n'
                '⚙️ FUNCIONAMIENTO: Un ingreso reciente (ahora mismo) aparece con en_cortesia=True y deuda 0.'
            ),
            "test_current_occupancy_fuera_de_cortesia_acumula_deuda": (
                '💡 LA IDEA: Comprobar que las estadías dentro del tiempo de cortesía salgan sin cargo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que las estadías breves dentro del tiempo de cortesía puedan salir sin costo ni retención innecesaria.\n\n'
                '⚙️ FUNCIONAMIENTO: Un ingreso viejo sale de cortesía y acumula deuda > 0.'
            ),
            "test_current_occupancy_reserva_pagada_vigente": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Un ingreso ligado a una reserva pagada se lista con es_reserva=True, ya_pago=True, deuda 0 y el objeto reserva embebido.'
            ),
        },
    },
    "tests/test_ocr_engine_detallado.py": {
        "proposito": 'Cobertura profunda de alpr/ocr_engine.py: selección del motor OCR (import con fallo/éxito de RapidOCR y PaddleOCR), ReadingStatusNotifier con debounce, corrección de patentes, vaciado de cola, detección de movimiento, OCR por ROI con ambos motores, bucle del worker (QR, consenso, combinación de fragmentos, fallback ROI, motos), overlay y despacho de eventos al backend.',
        "simbolos": {
            "FakeQRDetector": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble del detector de QR que devuelve un resultado fijo configurado.'
            ),
            "FakeQRDetector.__init__": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda el resultado a devolver en detectAndDecode.'
            ),
            "FakeQRDetector.detectAndDecode": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve (resultado, None, None) sin tocar el frame.'
            ),
            "FakeReader": (
                '💡 LA IDEA: Comprobar el escenario de FakeReader.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble estilo rapidocr: es invocable como __call__(roi) y devuelve (resultado, None); el spec puede ser fijo, None o un callable por número de llamada.'
            ),
            "FakeReader.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeReader.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Recibe el spec de resultado y inicializa el contador de llamadas.'
            ),
            "FakeReader.__call__": (
                '💡 LA IDEA: Comprobar el escenario de FakeReader.  call  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Incrementa el contador y devuelve el resultado del spec (si es callable, lo invoca con el número de llamada).'
            ),
            "FakePaddleReader": (
                '💡 LA IDEA: Comprobar el escenario de FakePaddleReader.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble estilo paddleocr con método .ocr(img, cls=False); puede lanzar excepción o devolver el resultado configurado.'
            ),
            "FakePaddleReader.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakePaddleReader.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda resultado, flag raise_on_call y contador de llamadas.'
            ),
            "FakePaddleReader.ocr": (
                '💡 LA IDEA: Comprobar el escenario de FakePaddleReader.ocr.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuenta la llamada; si raise_on_call lanza RuntimeError, si no devuelve el resultado.'
            ),
            "_result": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _result.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Construye un resultado estilo rapidocr [[poly, texto, conf], ...] a partir de una lista de textos, confianza y polígonos opcionales.'
            ),
            "_frame": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera un frame numpy BGR sólido de 480x640 con el valor de relleno dado.'
            ),
            "_make_engine": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _make_engine.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Fabrica un ALPREngine sin pasar por __init__: inyecta reader, cola, buffers, executor y un _dispatch_request falso o el provisto.'
            ),
            "_wait_for": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _wait_for.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Espera (polling con sleep real) a que una condición sea verdadera; devuelve False si expira.'
            ),
            "_stop_worker": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _stop_worker.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Detena el worker (is_running=False), une el hilo y apaga el executor.'
            ),
            "_run_worker": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _run_worker.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Parcha time.sleep, encola frames (o usa la cola dada) y arranca ocr_worker en un hilo daemon.'
            ),
            "_encerar_frames": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _encerar_frames.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Encola n frames limpios en la cola del motor.'
            ),
            "_scenario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _scenario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Context manager que recarga el módulo ocr_engine con rapidocr/paddleocr forzados a ausentes (None) o a módulos fake, y restaura el entorno real al salir.'
            ),
            "_fake_module": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _fake_module.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un types.ModuleType con la clase del motor OCR fake bajo el nombre de atributo indicado.'
            ),
            "FakeResp": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Doble de requests.Response para _dispatch_request con ok/status/text/json.'
            ),
            "FakeResp.__init__": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.  init  .\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Configura ok, status_code, text y mensaje JSON.'
            ),
            "FakeResp.json": (
                '💡 LA IDEA: Comprobar el escenario de FakeResp.json.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve {'message': mensaje} simulado."
            ),
            "test_import_rapid_falla_paddle_ok": (
                '💡 LA IDEA: Comprobar el escenario de import rapid falla paddle ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin rapidocr y con paddleocr disponible, el motor seleccionado es PaddleOCR y ALPREngine instancia el reader de Paddle.'
            ),
            "test_import_ambos_motores_fallan": (
                '💡 LA IDEA: Comprobar el escenario de import ambos motores fallan.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si ambos motores fallan al importar, OCR_ENGINE_NAME queda None, se imprime warning y ALPREngine queda sin reader.'
            ),
            "test_init_rapid_constructor_falla": (
                '💡 LA IDEA: Comprobar el escenario de init rapid constructor falla.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Si RapidOCR importa pero su constructor lanza, el engine queda sin reader y con ocr_error detallando 'RapidOCR'."
            ),
            "test_init_paddle_constructor_falla": (
                '💡 LA IDEA: Comprobar el escenario de init paddle constructor falla.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Caso análogo para PaddleOCR: constructor que falla deja ocr_error con 'PaddleOCR'."
            ),
            "test_notifier_debounce_y_fire": (
                '💡 LA IDEA: Comprobar el escenario de notifier debounce y fire.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: ReadingStatusNotifier: la segunda notify_reading dentro del intervalo se silencia (debounce) y el error de conexión en _fire no propaga.'
            ),
            "test_notifier_segundo_aviso_fuera_de_intervalo": (
                '💡 LA IDEA: Comprobar el escenario de notifier segundo aviso fuera de intervalo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Pasado el intervalo, notify_reading vuelve a lanzar el hilo de notificación.'
            ),
            "test_corregir_patente_vacia": (
                '💡 LA IDEA: Comprobar el escenario de corregir patente vacia.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: CorregirPatente con cadena vacía o None devuelve cadena vacía.'
            ),
            "test_corregir_patente_moto_mercosur_con_digito_ambiguo": (
                '💡 LA IDEA: Comprobar el escenario de corregir patente moto mercosur con digito ambiguo.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Corrige dígitos confundibles en motos Mercosur argentinas: A0ABCDE→A048CDE y AO1BCDE→A018CDE.'
            ),
            "test_corregir_patente_moto_general": (
                '💡 LA IDEA: Comprobar el escenario de corregir patente moto general.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Una moto que no empieza con 'A' pasa por la corrección general de moto sin cambios."
            ),
            "test_corregir_patente_brasil_mercosur": (
                '💡 LA IDEA: Comprobar el escenario de corregir patente brasil mercosur.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Corrige 'I' confundida con '1' en formato Brasil (ABCID23→ABC1D23)."
            ),
            "test_corregir_patente_clasica_auto": (
                '💡 LA IDEA: Comprobar el escenario de corregir patente clasica auto.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Formato antiguo de auto LLLNNN: la última letra se reemplaza por dígito (ABC12D→ABC120).'
            ),
            "test_corregir_patente_moto_clasica": (
                '💡 LA IDEA: Comprobar el escenario de corregir patente moto clasica.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Formato antiguo de moto NNNLLL pasa sin corrección.'
            ),
            "_FlakyGetQueue": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _FlakyGetQueue.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Cola falsa cuyo get_nowait siempre lanza, para ejercitar los except de flush_queue.'
            ),
            "_FlakyGetQueue.empty": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _FlakyGetQueue.empty.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve False (siempre hay 'items')."
            ),
            "_FlakyGetQueue.get_nowait": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _FlakyGetQueue.get_nowait.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Lanza ValueError simulando un burst roto.'
            ),
            "test_flush_queue_descarta_item_que_falla_en_get": (
                '💡 LA IDEA: Comprobar el escenario de flush queue descarta item que falla en get.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Flush_queue corta el vaciado ante un error en get_nowait sin propagar (except interno).'
            ),
            "test_flush_queue_empty_que_levanta_error": (
                '💡 LA IDEA: Comprobar el escenario de flush queue empty que levanta error.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si empty() lanza, flush_queue lo silencia con su except externo.'
            ),
            "test_detect_motion_primera_vez_y_cambios": (
                '💡 LA IDEA: Comprobar el escenario de detect motion primera vez y cambios.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Detect_motion: primer frame True, frame idéntico False, frame con cambio fuerte True.'
            ),
            "test_detect_motion_error_cv2_devuelve_true": (
                '💡 LA IDEA: Comprobar el escenario de detect motion error cv2 devuelve true.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si cvtColor falla, detect_motion degrada a True (asume movimiento por seguridad).'
            ),
            "test_ocr_single_roi_guardas": (
                '💡 LA IDEA: Comprobar el escenario de ocr single roi guardas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: _ocr_single_roi devuelve ([], [], []) con ROI None/vacío o reader ausente.'
            ),
            "test_ocr_single_roi_resize_y_rapid_ok": (
                '💡 LA IDEA: Comprobar el escenario de ocr single roi resize y rapid ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: ROI pequeña se amplía antes de pasársela a RapidOCR (el original no se modifica) y devuelve textos, scores y polys.'
            ),
            "test_ocr_single_roi_resultado_vacio": (
                '💡 LA IDEA: Comprobar el escenario de ocr single roi resultado vacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Reader rapidocr que devuelve None resulta en listas vacías.'
            ),
            "test_ocr_single_roi_paddle_ok": (
                '💡 LA IDEA: Comprobar el escenario de ocr single roi paddle ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Rama PaddleOCR: extrae textos, confianzas y polys del formato anidado de paddle.'
            ),
            "test_ocr_single_roi_paddle_sin_resultado": (
                '💡 LA IDEA: Comprobar el escenario de ocr single roi paddle sin resultado.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: PaddleOCR sin líneas de resultado devuelve vacío.'
            ),
            "test_ocr_single_roi_paddle_falla": (
                '💡 LA IDEA: Comprobar el escenario de ocr single roi paddle falla.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Excepción dentro de PaddleOCR se traga y devuelve vacío.'
            ),
            "test_ocr_worker_sin_motor_retorna": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker sin motor retorna.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Ocr_worker sin reader imprime y retorna sin entrar al loop.'
            ),
            "test_ocr_worker_codigo_qr_string": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                "⚙️ FUNCIONAMIENTO: Un QR detectado como string genera un evento despachado tipo 'qr' con el contenido."
            ),
            "test_ocr_worker_codigo_qr_lista": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Un QR devuelto como lista se toma por su primer elemento.'
            ),
            "test_ocr_worker_is_mercosur_recorta_y_consenso": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker is mercosur recorta y consenso.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Un ROI detectado como Mercosur se recorta bajo la franja azul y la patente se acepta con país ARGENTINA.'
            ),
            "test_ocr_worker_resultado_vacio_continua": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker resultado vacio continua.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Reader sin resultados: el loop continúa sin emitir evento.'
            ),
            "test_ocr_worker_texto_muy_corto_descarta": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker texto muy corto descarta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Textos de un solo carácter no forman detecciones.'
            ),
            "test_ocr_worker_noise_header_descarta": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker noise header descarta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Textos de encabezado (REPUBLICA/ARGENTINA) se descartan como ruido.'
            ),
            "test_ocr_worker_polys_menos_que_textos": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker polys menos que textos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si hay menos polígonos que textos, el bbox del faltante cae al valor por defecto.'
            ),
            "test_ocr_worker_consenso_6_caracteres": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker consenso 6 caracteres.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Patente clásica de 6 caracteres (ABC123) se acepta por consenso y marca país 'ARGENTINA (Antigua)'."
            ),
            "test_ocr_worker_combina_fragmentos_by_x": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker combina fragmentos by x.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Fragmentos 'AB' + 'C123' ordenados por coordenada X se concatenan en ABC123."
            ),
            "test_ocr_worker_al_sin_formato_cae_fallback_vacio": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker al sin formato cae fallback vacio.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Texto sin formato no matchea y el fallback find_plate_roi vacío no aporta patente.'
            ),
            "test_ocr_worker_priority4_combina_por_y": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker priority4 combina por y.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si el orden por X no matchea, el orden por Y (prioridad 4) combina los fragmentos correctamente.'
            ),
            "test_ocr_worker_fallback_roi_detecta": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker fallback roi detecta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El fallback por ROIs candidatas prueba cada una y acepta la que confirma la patente con confianza mínima 0.65.'
            ),
            "test_ocr_worker_fallback_roi_error_ignorado": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker fallback roi error ignorado.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si find_plate_roi lanza excepción, se ignora y el frame no emite evento.'
            ),
            "test_ocr_worker_moto_descartada_sin_motos": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker moto descartada sin motos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con ENABLE_MOTO_RECOGNITION desactivado, una patente de moto se descarta pese al consenso.'
            ),
            "test_ocr_worker_moto_con_motos_habilitadas": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker moto con motos habilitadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con motos habilitadas: aspecto de bbox < 2.2 y confianza alta (0.95) aceptan; confianza 0.50 se descarta.'
            ),
            "test_ocr_worker_moto_aspecto_ancho_descarta": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker moto aspecto ancho descarta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Una caja muy ancha (>2.2) atribuida a moto se filtra como recorte de auto.'
            ),
            "test_ocr_worker_latam_personalizado_cae_en_validaciones": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker latam personalizado cae en validaciones.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Con LATAM_PLATE_PATTERN acotado, el texto cae en las validaciones de formato o longitud y no genera evento.'
            ),
            "test_ocr_worker_excepcion_interna_continua": (
                '💡 LA IDEA: Comprobar el escenario de ocr worker excepcion interna continua.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Una excepción dentro del loop del worker (por ejemplo en queue.get) se loguea y el loop continúa vivo.'
            ),
            "test_get_frame_with_overlay_none": (
                '💡 LA IDEA: Comprobar el escenario de get frame with overlay none.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Get_frame_with_overlay con frame None devuelve None.'
            ),
            "test_get_frame_with_overlay_dibuja_deteccion": (
                '💡 LA IDEA: Comprobar el escenario de get frame with overlay dibuja deteccion.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Una detección dentro de la ventana de tiempo dibuja el overlay sobre el frame.'
            ),
            "test_draw_overlay_none": (
                '💡 LA IDEA: Comprobar el escenario de draw overlay none.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Draw_overlay con frame None devuelve None.'
            ),
            "test_draw_overlay_bbox_corto_omite": (
                '💡 LA IDEA: Comprobar el escenario de draw overlay bbox corto omite.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Un bbox con menos de 4 puntos se salta; los demás sí se dibujan.'
            ),
            "_BoomStr": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _BoomStr.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Objeto cuyo __str__ lanza, para probar el manejo de errores de serialización.'
            ),
            "_BoomStr.__str__": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _BoomStr.__str__.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                "⚙️ FUNCIONAMIENTO: Lanza ValueError('no serializable')."
            ),
            "test_send_event_error_str_ignorado": (
                '💡 LA IDEA: Comprobar el escenario de send event error str ignorado.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si str(data) falla, send_event no despacha el evento y no rompe.'
            ),
            "_make_dispatch_engine": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _make_dispatch_engine.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Motor con el _dispatch_request real de la clase y requests.post/GATE_TYPE/GATE_ID/BACKEND_URL parcheados; devuelve el motor y la lista de llamadas.'
            ),
            "test_dispatch_entrada_bienvenido": (
                '💡 LA IDEA: Comprobar el escenario de dispatch entrada bienvenido.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Con GATE_TYPE entrada, send_event postea a /v1/access/validate-plate con gate_id, plate, ocr_time e image_base64.'
            ),
            "test_dispatch_salida_hasta_luego": (
                '💡 LA IDEA: Comprobar el escenario de dispatch salida hasta luego.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el mecanismo de apertura física de barreras se dispare solo ante accesos debidamente autorizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Con GATE_TYPE salida usa /v1/access/exit-plate.'
            ),
            "test_dispatch_mensaje_otro": (
                '💡 LA IDEA: Comprobar el escenario de dispatch mensaje otro.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Una respuesta ok con mensaje genérico no altera el flujo del dispatch.'
            ),
            "test_dispatch_respuesta_error": (
                '💡 LA IDEA: Comprobar el escenario de dispatch respuesta error.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Una respuesta !ok (ej. 404) se informa pero el evento ya fue enviado.'
            ),
            "test_dispatch_error_post": (
                '💡 LA IDEA: Comprobar el escenario de dispatch error post.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si requests.post lanza, el error se loguea sin romper el hilo.'
            ),
            "test_dispatch_qr_endpoint": (
                '💡 LA IDEA: Validar la lectura, vigencia y validación del pase QR de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica la autenticidad y vigencia de los códigos QR para evitar ingresos con pases inválidos, vencidos o de otra sucursal.\n\n'
                '⚙️ FUNCIONAMIENTO: Los eventos QR usan /v1/access/validate-qr con clave qr_data (sin plate).'
            ),
            "test_dispatch_error_al_codificar_frame": (
                '💡 LA IDEA: Comprobar el escenario de dispatch error al codificar frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si cv2.imencode falla, el dispatch se aborta sin propagar el error.'
            ),
        },
    },
    "tests/test_pay_stay.py": {
        "proposito": 'Tests del endpoint autenticado POST /v1/access/pay-stay: protección por token y rol operativo (staff/admin), y el flujo de cobro de estadía en curso con método de pago DIGITAL o CAJA.',
        "simbolos": {
            "client": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para client.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: SQLite en memoria con todo el esquema, override de get_db y reset del limiter; devuelve (TestClient, sessionmaker).'
            ),
            "_crear_usuario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un User de prueba (rol staff o user) con email único y password_hash dummy.'
            ),
            "_token": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _token.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Emite un JWT de acceso con sub=email y rol del usuario, sin pasar por login.'
            ),
            "_crear_entrada": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _crear_entrada.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea Settings de precio por hora/30min y un AccessLog de ENTRADA sin pagar de hace dos horas para la sucursal Central.'
            ),
            "test_pay_stay_sin_token_es_401": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: POST sin Authorization devuelve 401.'
            ),
            "test_pay_stay_rol_usuario_es_403": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Un cliente ('user') autenticado recibe 403: el rol no es operativo."
            ),
            "test_pay_stay_staff_cobra_estadia_pendiente": (
                '💡 LA IDEA: Comprobar el escenario de pay stay staff cobra estadia pendiente.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: Staff cobra la estadía pendiente: 200, status ok, monto > 0 y el AccessLog queda pago_confirmado con metodo_pago DIGITAL.'
            ),
            "test_pay_stay_staff_metodo_caja_aplica": (
                '💡 LA IDEA: Comprobar el escenario de pay stay staff metodo caja aplica.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                '⚙️ FUNCIONAMIENTO: El parámetro metodo=CAJA se refleja en el AccessLog como metodo_pago CAJA.'
            ),
            "test_pay_stay_staff_sin_estadia_devuelve_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las acciones administrativas estén rigurosamente blindadas frente a usuarios comunes o roles sin privilegios.\n\n'
                "⚙️ FUNCIONAMIENTO: Cobrar una patente sin estadías pendientes devuelve 400 con detalle que menciona 'pendientes'."
            ),
        },
    },
    "tests/test_payments.py": {
        "proposito": 'Cobertura del ReservationPaymentsMixin (services/payments.py): descuentos por ticket de canje, abono manual con puntos, pago con saldo y Mercado Pago, simulación y ejecución de reembolsos y cancelación de reservas.',
        "simbolos": {
            "session_factory": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para session_factory.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Fixture: SQLite en memoria con esquema completo y una sucursal 'AUTOPASS Central' sembrada; devuelve el sessionmaker para que cada test abra su sesión."
            ),
            "_usuario": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un User de prueba con saldo y puntos configurables.'
            ),
            "_reserva": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea una Reservation con monto, estados, sucursal, ventana de fechas y tipo de estadía variables.'
            ),
            "_ticket": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _ticket.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Crea un RedemptionTicket de descuento (porcentaje, estado y sucursal opcionales) para el usuario.'
            ),
            "_entrada": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _entrada.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra un AccessLog de ENTRADA sin pagar (con patente normalizada opcional).'
            ),
            "_salida": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _salida.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra un AccessLog de SALIDA para la misma patente/sucursal.'
            ),
            "test_lista_descuentos_sin_usuario_es_vacia": (
                '💡 LA IDEA: Comprobar el escenario de lista descuentos sin usuario es vacia.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Get_available_redemption_discounts con usuario None devuelve lista vacía.'
            ),
            "test_lista_descuentos_devuelve_tickets_vigentes": (
                '💡 LA IDEA: Comprobar el escenario de lista descuentos devuelve tickets vigentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista los tickets vigentes de descuento del usuario en la sucursal indicada.'
            ),
            "test_clausula_sucursal_delegada_al_repo": (
                '💡 LA IDEA: Comprobar el escenario de clausula sucursal delegada al repo.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Redemption_sucursal_clause construye la cláusula SQL de sucursal delegando al repositorio.'
            ),
            "test_validate_sin_id_devuelve_none": (
                '💡 LA IDEA: Comprobar el escenario de validate sin id devuelve none.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Validate_redemption_ticket sin ticket_id devuelve None (sin descuento).'
            ),
            "test_validate_ticket_invalido_lanza_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que el sistema informe claramente cuando se intenta operar sobre entidades o registros que no existen en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Un ticket_id inexistente lanza HTTP 400.'
            ),
            "test_manual_reserva_ya_pagada": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Pay_reservation_manual sobre reserva ya pagada devuelve ok con mensaje 'ya se encuentra pagada' y el monto original."
            ),
            "test_manual_sin_usuario_con_descuento_lanza_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplicar ticket de descuento a una reserva sin usuario (admin sin user_id) lanza 400.'
            ),
            "test_manual_aplica_descuento_y_acredita_puntos": (
                '💡 LA IDEA: Comprobar el escenario de manual aplica descuento y acredita puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: El abono manual aplica el 10% de descuento (1000→900), marca el ticket USADO ligado a la reserva, acredita 9 puntos (10% de 900) y registra el PointsLog.'
            ),
            "test_manual_notificacion_falla_no_bloquea": (
                '💡 LA IDEA: Comprobar el escenario de manual notificacion falla no bloquea.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Si create_notification lanza, el pago manual igual devuelve ok y acredita los puntos.'
            ),
            "test_manual_sin_descuento_acredita_puntos": (
                '💡 LA IDEA: Comprobar el escenario de manual sin descuento acredita puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin ticket, descuento 0 y se acreditan los puntos del monto total (10 de 1000).'
            ),
            "test_pay_reserva_no_pertenece_al_usuario_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Pay_reservation de una reserva de otro usuario lanza 404.'
            ),
            "test_pay_reserva_cancelada_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Reserva cancelada no se puede pagar (400).'
            ),
            "test_pay_reserva_completada_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Reserva completada no se puede pagar (400).'
            ),
            "test_pay_reserva_ya_abonada": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Reserva ya pagada devuelve ok con mensaje 'La reserva ya ha sido abonada'."
            ),
            "test_pay_reserva_saldo_insuficiente_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                "⚙️ FUNCIONAMIENTO: Saldo insuficiente lanza 400 con detalle 'Saldo insuficiente'."
            ),
            "test_pay_reserva_success_con_descuento": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Pago con saldo y ticket: descuenta saldo (2000→1100), activa la reserva, marca SALDO, guarda monto 900, usa el ticket, gana 9 puntos y envía mail de confirmación con costo y dirección de la sucursal.'
            ),
            "test_pay_reserva_no_horaria_iniciada_reserva_plaza": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Reserva de plaza (tipo 'dia') sin inicio se puede pagar igual (no exige horario iniciado)."
            ),
            "test_pay_reserva_notificacion_falla_ok": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Falla de notificación durante el pago con saldo no invalida el resultado ok.'
            ),
            "test_mp_reserva_cancelada_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Pay_reservation_mp sobre reserva cancelada lanza 400.'
            ),
            "test_mp_reserva_ya_abonada_applied_false": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Reserva ya pagada por MP devuelve ok con aplicado=False (idempotencia).'
            ),
            "test_mp_success_con_descuento": (
                '💡 LA IDEA: Comprobar el escenario de mp success con descuento.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del módulo de atención de reclamos y consultas de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: El pago Mercado Pago con ticket aplica descuento, marca MERCADOPAGO, usa el ticket, acredita 9 puntos y envía la confirmación.'
            ),
            "test_mp_no_horaria_iniciada_reserva_plaza": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Reserva de plaza (tipo 'semana') se puede pagar por MP sin ventana horaria."
            ),
            "test_mp_notificacion_falla_ok": (
                '💡 LA IDEA: Comprobar el escenario de mp notificacion falla ok.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los avisos e incidencias relevantes sean generados y despachados oportunamente a los destinatarios correctos.\n\n'
                '⚙️ FUNCIONAMIENTO: Falla de notificación en pago MP no rompe el resultado.'
            ),
            "test_simulate_vehiculo_en_predio": (
                '💡 LA IDEA: Comprobar el escenario de simulate vehiculo en predio.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Simulate_refund con el vehículo dentro del predio (entrada sin salida) devuelve reembolso 0 y error 'Vehículo en el predio'."
            ),
            "test_simulate_no_pagado_reembolso_cero": (
                '💡 LA IDEA: Comprobar el escenario de simulate no pagado reembolso cero.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Reserva no pagada: reembolso 0 sin error.'
            ),
            "test_simulate_antes_de_inicio_reembolso_total": (
                '💡 LA IDEA: Comprobar el escenario de simulate antes de inicio reembolso total.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Antes del inicio de la reserva, el reembolso simulado es el monto total.'
            ),
            "test_simulate_despues_de_fin_cero": (
                '💡 LA IDEA: Comprobar el escenario de simulate despues de fin cero.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Terminada la ventana de la reserva, el reembolso es 0.'
            ),
            "test_simulate_ventana_hora_con_ingreso_cero": (
                '💡 LA IDEA: Comprobar el escenario de simulate ventana hora con ingreso cero.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Estadía por hora ya usada (entrada y salida registradas) simula reembolso 0.'
            ),
            "test_simulate_ventana_no_hora_proporcional": (
                '💡 LA IDEA: Comprobar el escenario de simulate ventana no hora proporcional.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Estadía por día usada la mitad de la ventana simula reembolso proporcional (~50%).'
            ),
            "test_cancel_reserva_inexistente_404": (
                '💡 LA IDEA: Comprobar que el sistema responda con 404 (No Encontrado) ante recursos inexistentes.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancel_reservation de id inexistente lanza 404.'
            ),
            "test_cancel_reserva_ya_cancelada": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Reserva ya cancelada devuelve ok con mensaje 'ya se encuentra cancelada'."
            ),
            "test_cancel_reserva_completada_error": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Reserva completada devuelve status 'error' con 'no puede cancelarse'."
            ),
            "test_cancel_reserva_vehiculo_en_predio_400": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                "⚙️ FUNCIONAMIENTO: Cancelar con el vehículo en el predio lanza 400 'Vehículo en el predio'."
            ),
            "test_cancel_reserva_con_reembolso_total": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancelación con reembolso total: devuelve saldo, reversa 10 puntos, marca Cancelada/Reembolsado, registra monto_reembolsado y PointsLog negativo.'
            ),
            "test_cancel_reserva_sin_reembolso": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                "⚙️ FUNCIONAMIENTO: Reserva impaga se cancela sin reembolso y estado de pago 'Cancelado'."
            ),
            "test_cancel_reserva_notificacion_falla_ok": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Falla de notificación al cancelar no impide la cancelación.'
            ),
        },
    },
    "tests/test_preprocessor.py": {
        "proposito": 'Tests del ImagePreprocessor de alpr: identificación de país por formato de patente, detección de movimiento, preprocesado para pantalla, IoU, validación de ROIs, búsqueda de patentes por contornos y detección/recorte de la franja azul MERCOSUR.',
        "simbolos": {
            "_frame": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _frame.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera un frame numpy BGR sólido del tamaño y relleno dados.'
            ),
            "_blue_strip": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _blue_strip.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Imagen negra con una franja azul (BGR 255,0,0) en las primeras filas, para simular la banda MERCOSUR.'
            ),
            "test_identify_country_folios_argentinos": (
                '💡 LA IDEA: Comprobar el escenario de identify country folios argentinos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Identify_country clasifica folios Mercosur argentinos (AA123BB, AF456GH).'
            ),
            "test_identify_country_motos_argentinas": (
                '💡 LA IDEA: Comprobar el escenario de identify country motos argentinas.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Clasifica motos Mercosur (A012BCD), motos generales (AB123A) y motos antiguas (AB123).'
            ),
            "test_identify_country_antigua": (
                '💡 LA IDEA: Comprobar el escenario de identify country antigua.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Patente clásica AAA111 → ARGENTINA (Antigua).'
            ),
            "test_identify_country_brasil_uruguay_paraguay": (
                '💡 LA IDEA: Comprobar el escenario de identify country brasil uruguay paraguay.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Reconoce formatos de Brasil (ABC1D23), Uruguay (ABC1234) y Paraguay (WXYZ789).'
            ),
            "test_identify_country_fallbacks": (
                '💡 LA IDEA: Comprobar el escenario de identify country fallbacks.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                "⚙️ FUNCIONAMIENTO: Con is_mercosur=True cae en 'MERCOSUR (Otro)'; sin él, 'DESCONOCIDO'."
            ),
            "test_detect_motion_force_ocr_short_circuit": (
                '💡 LA IDEA: Comprobar el escenario de detect motion force ocr short circuit.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: FORCE_OCR activo fuerza motion=True y devuelve el frame anterior sin procesar.'
            ),
            "test_detect_motion_primer_frame_siempre_movimiento": (
                '💡 LA IDEA: Comprobar el escenario de detect motion primer frame siempre movimiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin frame anterior siempre hay movimiento y el gray devuelto está en escala de grises reducida (240x320).'
            ),
            "test_detect_motion_frames_iguales_no_movimiento": (
                '💡 LA IDEA: Comprobar el escenario de detect motion frames iguales no movimiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Dos frames idénticos no producen movimiento.'
            ),
            "test_detect_motion_frames_distintos_si_movimiento": (
                '💡 LA IDEA: Comprobar el escenario de detect motion frames distintos si movimiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Frames con contenido distinto producen movimiento.'
            ),
            "test_preprocess_for_screen_devuelve_tres_variantes": (
                '💡 LA IDEA: Comprobar el escenario de preprocess for screen devuelve tres variantes.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Preprocess_for_screen devuelve (nitidez, binarizada, invertida) ampliadas y con valores 0/255 en la binaria.'
            ),
            "test_iou_solapamiento_parcial": (
                '💡 LA IDEA: Comprobar el escenario de iou solapamiento parcial.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: IoU de rectángulos que se solapan parcialmente da el valor esperado (2500/17500).'
            ),
            "test_iou_sin_solapamiento_cero": (
                '💡 LA IDEA: Comprobar el escenario de iou sin solapamiento cero.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Rectángulos separados → IoU 0.'
            ),
            "test_iou_contencion_total": (
                '💡 LA IDEA: Comprobar el escenario de iou contencion total.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Rectángulo contenido: IoU = área interna / área externa (0.64).'
            ),
            "test_iou_area_nula_cero": (
                '💡 LA IDEA: Comprobar el escenario de iou area nula cero.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Área nula evita división por cero y devuelve 0.'
            ),
            "test_roi_valida": (
                '💡 LA IDEA: Comprobar el escenario de roi valida.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: ROI de proporción placa (40x120 en 640x480) es válida.'
            ),
            "test_roi_angosta_rechazada": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: ROI demasiado angosta se rechaza.'
            ),
            "test_roi_baja_rechazada": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: ROI demasiado baja se rechaza.'
            ),
            "test_roi_muy_ancha_rechazada": (
                '💡 LA IDEA: Validar que se bloquee el acceso y se devuelva error ante intentos no autorizados.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: ROI más ancha que el frame se rechaza.'
            ),
            "test_roi_aspect_ratio_invalido_rechazado": (
                '💡 LA IDEA: Verificar el rechazo con código de error ante parámetros inválidos o mal formados.\n\n'
                '🎯 POR QUE FUE GENERADA: Comprueba que las validaciones de entrada rechacen peticiones mal formadas antes de que causen errores en el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: ROI con aspect ratio fuera del rango de placa se rechaza.'
            ),
            "test_find_plate_roi_frame_liso_devuelve_roi_principal": (
                '💡 LA IDEA: Comprobar el escenario de find plate roi frame liso devuelve roi principal.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin contornos útiles, find_plate_roi devuelve al menos la ROI principal (recorte central del frame).'
            ),
            "test_find_plate_roi_con_contorno_placa": (
                '💡 LA IDEA: Comprobar el escenario de find plate roi con contorno placa.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Con contornos, filtra por tamaño/aspecto y devuelve al menos la ROI de la placa válida.'
            ),
            "test_find_plate_roi_error_contorno_no_crashea": (
                '💡 LA IDEA: Comprobar el escenario de find plate roi error contorno no crashea.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si cv2.findContours falla, se degrada a la ROI principal sin crashear.'
            ),
            "test_find_plate_roi_cinta_pequena_sin_contornos_devuelve_roi_principal": (
                '💡 LA IDEA: Comprobar el escenario de find plate roi cinta pequena sin contornos devuelve roi principal.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: En frames chicos sin contornos devuelve exactamente la ROI principal (77% de la altura).'
            ),
            "test_find_plate_roi_dedupe_por_iou": (
                '💡 LA IDEA: Comprobar el escenario de find plate roi dedupe por iou.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Candidatos casi idénticos (IoU alto) se deduplican, quedando uno solo.'
            ),
            "test_find_plate_roi_limite_10_candidatos": (
                '💡 LA IDEA: Comprobar el escenario de find plate roi limite 10 candidatos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: El listado de candidatos se limita a 10 elementos.'
            ),
            "test_mercosur_con_franja_azul": (
                '💡 LA IDEA: Comprobar el escenario de mercosur con franja azul.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Is_mercosur_candidate detecta la franja azul superior.'
            ),
            "test_mercosur_sin_franja_azul": (
                '💡 LA IDEA: Comprobar el escenario de mercosur sin franja azul.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin franja azul no es candidato Mercosur.'
            ),
            "test_mercosur_roi_vacia_no_crashea": (
                '💡 LA IDEA: Comprobar el escenario de mercosur roi vacia no crashea.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: ROI vacía devuelve False sin excepción.'
            ),
            "test_mercosur_roi_escala_de_grises_retorna_false": (
                '💡 LA IDEA: Comprobar el escenario de mercosur roi escala de grises retorna false.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: ROI en escala de grises (sin canal BGR) devuelve False.'
            ),
            "test_crop_baja_franja_azul_recorta": (
                '💡 LA IDEA: Comprobar el escenario de crop baja franja azul recorta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Crop_below_blue recorta la imagen dejando solo lo debajo de la franja.'
            ),
            "test_crop_sin_franja_azul_no_modifica": (
                '💡 LA IDEA: Comprobar el escenario de crop sin franja azul no modifica.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sin franja azul devuelve la ROI original (misma referencia).'
            ),
            "test_crop_franja_muy_baja_no_recorta": (
                '💡 LA IDEA: Comprobar el escenario de crop franja muy baja no recorta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Franja ubicada al 30-50% de la altura no se considera franja y no recorta.'
            ),
            "test_crop_resto_muy_pequeno_devuelve_roi": (
                '💡 LA IDEA: Comprobar el escenario de crop resto muy pequeno devuelve roi.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si lo que quedaría debajo de la franja es minúsculo, se devuelve la ROI completa.'
            ),
            "test_crop_franja_en_mitad_inferior_no_recorta": (
                '💡 LA IDEA: Comprobar el escenario de crop franja en mitad inferior no recorta.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Franja en la mitad inferior no recorta (no es la banda MERCOSUR).'
            ),
            "test_crop_roi_escala_de_grises_devuelve_roi": (
                '💡 LA IDEA: Comprobar el escenario de crop roi escala de grises devuelve roi.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: ROI en grises se devuelve sin modificar.'
            ),
            "test_crop_where_vacio_devuelve_roi": (
                '💡 LA IDEA: Comprobar el escenario de crop where vacio devuelve roi.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Si np.where no encuentra píxeles azules, se devuelve la ROI original.'
            ),
        },
    },
    "tests/test_rate_limiting.py": {
        "proposito": 'Verifica que el limitador de rate limiting del endpoint de login esté activo en la app real: tras superar el límite de intentos, el servidor responde HTTP 429.',
        "simbolos": {
            "override_get_db": (
                '💡 LA IDEA: Comprobar el escenario de override get db.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Sobrescribe get_db a nivel de módulo apuntando al engine de prueba; se registra una sola vez al importar el archivo.'
            ),
            "setup_test_db": (
                '💡 LA IDEA: Comprobar el escenario de setup db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Autouse: inicializa la BD de prueba y reinicia el limitador antes y después de cada test.'
            ),
            "test_login_rate_limiting": (
                '💡 LA IDEA: Validar el proceso de autenticación, emisión de credenciales y control de contraseñas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege el sistema de autenticación asegurando que solo usuarios válidos reciban tokens de acceso y se rechacen accesos indebidos.\n\n'
                '⚙️ FUNCIONAMIENTO: Envía 16 logins inválidos a /v1/auth/login y comprueba que al menos una respuesta sea 429 (límite de 15 peticiones).'
            ),
        },
    },
    "tests/test_report_access_p1.py": {
        "proposito": 'Regresión P1/A5: el batch get_reserva_ids_with_entry (reemplazo del N+1 de get_entry_for_reserva) devuelve solo reservas con entrada, el listado /reports/access respeta el límite server-side y la resolución de usuarios por patente deduplica el IN.',
        "simbolos": {
            "db": (
                '💡 LA IDEA: Proveer el entorno o recurso de prueba para db.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura un esquema de base de datos limpio y aislado en memoria para que las pruebas sean rápidas e independientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Fixture: SQLite en memoria con esquema completo y un admin global sembrado; destruye las tablas al final.'
            ),
            "_admin": (
                '💡 LA IDEA: Función auxiliar para preparar datos de prueba en _admin.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina la duplicación de código en la preparación de datos y agiliza la escritura de los tests.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el primer usuario con rol admin de la sesión.'
            ),
            "test_get_reserva_ids_with_entry_devuelve_solo_con_entrada": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: El batch devuelve únicamente el id de reserva que tiene al menos un AccessLog ENTRADA (ignora salidas y logs sin reserva).'
            ),
            "test_get_reserva_ids_with_entry_vacio_sin_queries": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas cumplan con los horarios contratados y reserven correctamente las plazas sin solapamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Con lista vacía devuelve set() sin ejecutar queries (protección del IN gigante).'
            ),
            "test_access_logs_history_limite_devuelve_solo_limit": (
                '💡 LA IDEA: Comprobar el escenario de access logs history limite devuelve solo limit.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Access_logs_history respeta el límite server-side y ordena por id descendente (más recientes primero).'
            ),
            "test_get_access_logs_deduplica_patentes_en_IN": (
                '💡 LA IDEA: Comprobar el escenario de get access logs deduplica patentes en IN.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica el correcto funcionamiento del flujo y previene regresiones ante futuras modificaciones de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Get_access_logs con patentes repetidas deduplica el IN a vehicles y entrega los logs completos sin error.'
            ),
            "test_get_reserva_ids_with_entry_equivale_a_entrada_por_reserva": (
                '💡 LA IDEA: Verificar la creación, asignación de cupos y ciclo de vida de las reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida la exactitud en la liquidación de la estadía y asegura que no se autorice la salida sin abonar la deuda pendiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Semántica del cleanup: la reserva impaga con ingreso registrado queda protegida (sigue Pendiente) y la impaga sin ingreso se cancela.'
            ),
        },
    },
}
