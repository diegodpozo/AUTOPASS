"""Explicaciones analizadas de las migraciones Alembic (parte 2 de 2)."""

ANALISIS: dict[str, dict] = {
    "alembic/versions/c4d5e6f7a8b9_merge_orden_y_sucursal_id_heads.py": {
        "proposito": "Migración de tipo 'merge' que une dos ramas de la historia: la cadena de orden de cámaras (b8f1c2d3e4a5) y la cadena de sucursal_id (e1f2a3b4c5d6). No cambia nada en el esquema: su upgrade/downgrade están vacíos (pass); solo sirve para que Alembic tenga un único head y las dos líneas de cambios queden integradas.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Fusionar dos ramas paralelas de la historia de migraciones sin alterar tablas ni datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica dos líneas de desarrollo independientes para que el motor de base de datos avance sobre un único historial lineal.\n\n'
                '⚙️ FUNCIONAMIENTO: Ambos son no-op (pass): esta revisión solo fusiona dos heads de Alembic, sin tocar tablas ni columnas.'
            ),
        },
    },
    "alembic/versions/c833a3129266_initial_schema.py": {
        "proposito": "Es la migración inicial de todo el proyecto y actúa como base: crea desde cero las tablas núcleo del sistema (users, vehicles, points_log, promotions, coupons, reservations, parking_aforo, settings, parking_branches, parking_cameras, parking_floors, access_logs, support_tickets y user_notifications) con sus columnas, claves primarias, claves foráneas e índices iniciales (dni/email únicos, patente única, normalized_patente, etc.). Las tablas creadas por migraciones posteriores y las columnas/índices agregados después se omiten a propósito, de modo que 'alembic upgrade head' reproduzca el esquema final desde una base vacía sin depender de Base.metadata.create_all; su downgrade elimina todo en orden inverso.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Construir desde cero los cimientos relacionales del sistema creando las 14 tablas fundacionales.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que cualquier entorno de desarrollo o prueba levante la estructura completa de base de datos de manera automatizada.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade crea las 14 tablas base del sistema con sus índices y FK; downgrade las revierte en orden inverso (primero índices y tablas dependientes, luego las referenciadas).'
            ),
        },
    },
    "alembic/versions/c9d8e7f6a5b4_add_mercadopago_payments.py": {
        "proposito": "Crea la tabla 'mercadopago_payments' para registrar los pagos realizados a través de MercadoPago: guarda el usuario, el tipo de pago, referencias opcionales a la reserva, log de acceso o ticket de canje, la patente, el monto y moneda, los identificadores de preferencia y de pago de MP, el estado interno y el de MP, y las fechas de creación/confirmación. Añade un índice único sobre external_reference (evita duplicar pagos) y un índice por user_id; el downgrade revierte borrando ambos índices y la tabla.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Crear la tabla de transacciones de pago para integraciones con la pasarela Mercado Pago.\n\n'
                '🎯 POR QUE FUE GENERADA: Registra comprobantes, referencias externas y confirmaciones de pago, evitando cobranzas duplicadas y manteniendo trazabilidad financiera.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade crea la tabla mercadopago_payments con sus FK, el índice único external_reference y el índice user_id; downgrade los elimina y borra la tabla.'
            ),
        },
    },
    "cdb7d130c856_add_access_logs_covering_indexes.py": {
        "proposito": "Agrega dos índices compuestos a 'access_logs' para acelerar consultas pesadas: ix_access_logs_pat_tipo_suc_fecha (patente_detectada, tipo_evento, sucursal, fecha_hora), que evita el escaneo completo por fila en las subconsultas correlacionadas del resumen financiero (entradas impagas sin salida), e ix_access_logs_reserva_id (reserva_id, tipo_evento), que sirve a la búsqueda de entrada por reserva en la limpieza de reservas vencidas. Usa batch_alter_table y su downgrade elimina ambos índices.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Añadir índices compuestos optimizados sobre la tabla de registros de acceso vehicular.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene escaneos completos de tabla en reportes financieros y agiliza la búsqueda de estadías activas pendientes de pago.\n\n'
                '⚙️ FUNCIONAMIENTO: Añadir índices compuestos optimizados sobre la tabla de registros de acceso vehicular.'
            ),
        },
    },
    "ce7d1e2f3a5b_add_promo_ubicacion.py": {
        "proposito": "Agrega la ubicación de canje a las promociones y a los tickets de canje: añade las columnas 'direccion' (texto), 'latitude' y 'longitude' (float), todas opcionales, a 'promotions' y a 'redemption_tickets'. Es la fase que agrega esas columnas que la migración inicial no declara; el downgrade las elimina en orden inverso de ambas tablas.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Incorporar dirección postal y coordenadas geográficas a los beneficios y tickets de canje.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite posicionar en mapas interactivos el punto exacto donde los clientes pueden retirar productos o validar sus vouchers.\n\n'
                '⚙️ FUNCIONAMIENTO: Incorporar dirección postal y coordenadas geográficas a los beneficios y tickets de canje.'
            ),
        },
    },
    "d1e2f3a4b5c6_add_sucursal_id_dependencias.py": {
        "proposito": "Fase 1 de la migración de sedes por id: agrega la columna 'sucursal_id' (con su índice) a las tablas que referenciaban la sede por nombre —reservations, users, access_logs, support_tickets y redemption_tickets—. En PostgreSQL rellena el id derivándolo del nombre actual y crea la clave foránea a parking_branches.id (ON UPDATE CASCADE, sin ON DELETE CASCADE para que borrar una sede no arrastre esas filas); en SQLite (tests de paridad) solo agrega columna e índice. La columna de nombre legacy se mantiene; el downgrade quita FK, índice y columna.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Añadir la clave foránea sucursal_id a las tablas operativas principales.\n\n'
                '🎯 POR QUE FUE GENERADA: Migra la relación de sedes desde nombres de texto a identidades numéricas indexadas, asegurando integridad referencial en cascada.\n\n'
                '⚙️ FUNCIONAMIENTO: Añadir la clave foránea sucursal_id a las tablas operativas principales.'
            ),
        },
    },
    "d3b7e1a9c2f0_add_metodo_pago_to_reservations.py": {
        "proposito": "Agrega la columna opcional 'metodo_pago' (texto) a la tabla 'reservations' para registrar cómo se pagó cada reserva; el downgrade la elimina mediante batch_alter_table.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Añadir el método de pago elegido a la ficha de cada reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a la administración saber si una reserva se canceló con Mercado Pago, tarjeta o efectivo para conciliaciones de caja.\n\n'
                '⚙️ FUNCIONAMIENTO: Añadir el método de pago elegido a la ficha de cada reserva.'
            ),
        },
    },
    "d4f7c8e2a190_add_ticket_id_and_user_response.py": {
        "proposito": "Conecta notificaciones con tickets de soporte y guarda la respuesta del usuario: agrega a 'user_notifications' la columna 'ticket_id' con clave foránea a support_tickets.id, y a 'support_tickets' la columna de texto 'user_response'. Ambas opcionales; el downgrade elimina user_response y ticket_id en ese orden.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Enlazar notificaciones del sistema con consultas de asistencia al cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el usuario responda directamente a avisos de soporte y mantenga el hilo de conversación unificado.\n\n'
                '⚙️ FUNCIONAMIENTO: Enlazar notificaciones del sistema con consultas de asistencia al cliente.'
            ),
        },
    },
    "e1f2a3b4c5d6_merge_sucursal_id_chain_y_drop_legacy_.py": {
        "proposito": "Migración de tipo 'merge' que une la cadena de sucursal_id (c3d4e5f6a7b8) con la de eliminación de campos legacy de soporte (f9a8b7c6d5e4). Su upgrade y downgrade están vacíos (pass): no toca el esquema, solo consolida ambos heads en uno para que la historia de migraciones quede lineal.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Consolidar dos cadenas de migraciones paralelas en una sola línea principal.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina cabezas de versión múltiples en Alembic asegurando que las actualizaciones automáticas no queden trabadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Consolidar dos cadenas de migraciones paralelas en una sola línea principal.'
            ),
        },
    },
    "e5a2b8c1d937_create_support_ticket_messages.py": {
        "proposito": "Crea la tabla 'support_ticket_messages' que guarda el hilo de mensajes de cada ticket de soporte: incluye clave primaria, ticket_id (FK a support_tickets.id, no nulo, indexado), user_id (FK a users.id, no nulo), el texto 'mensaje' y 'created_at'. Es la fuente de verdad de la conversación; el downgrade elimina la tabla.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Crear la tabla del historial de conversación para los tickets de soporte.\n\n'
                '🎯 POR QUE FUE GENERADA: Proporciona la estructura necesaria para un chat interactivo con fecha, autor y cuerpo de cada intercambio entre usuario y soporte.\n\n'
                '⚙️ FUNCIONAMIENTO: Crear la tabla del historial de conversación para los tickets de soporte.'
            ),
        },
    },
    "e6f7a8b9c0d1_add_reservation_spots_to_aforo_and_floors.py": {
        "proposito": "Separa la ocupación por reservas de la ocupación general del estacionamiento: agrega a 'parking_aforo' y a 'parking_floors' ocho columnas opcionales (capacidad/ocupación de reservas para autos, motos y camionetas, más un total de capacidad/ocupación de reservas). Permite calcular cupos de reserva sin mezclarlos con los ingresos por acceso; el downgrade elimina esas columnas de ambas tablas.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Desacoplar los cupos de reserva anticipada de la capacidad para vehículos espontáneos.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita el colapso del estacionamiento garantizando que siempre haya lugares libres para los usuarios que reservaron con anterioridad.\n\n'
                '⚙️ FUNCIONAMIENTO: Desacoplar los cupos de reserva anticipada de la capacidad para vehículos espontáneos.'
            ),
        },
    },
    "f1a2b3c4d5e6_add_ocr_timing_to_access_logs.py": {
        "proposito": "Agrega dos columnas opcionales de tipo float a 'access_logs' para medir rendimiento: 'ocr_time' (tiempo del reconocimiento de patente) y 'backend_time' (tiempo del backend). El downgrade las elimina en orden inverso.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Registrar métricas de latencia en milisegundos para el reconocimiento visual y el backend.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita la telemetría operativa para identificar y corregir cuellos de botella en la velocidad de apertura de barreras.\n\n'
                '⚙️ FUNCIONAMIENTO: Registrar métricas de latencia en milisegundos para el reconocimiento visual y el backend.'
            ),
        },
    },
    "f5a6b7c8d9e0_add_sucursal_id_tablas_config.py": {
        "proposito": "Fase 4 de la migración de sedes por id: agrega 'sucursal_id' (con índice) a las tablas de configuración que aún referenciaban la sede por nombre —parking_aforo, settings, parking_cameras y promotions—. En PostgreSQL rellena el id desde el nombre y crea la FK a parking_branches.id (ON UPDATE CASCADE); las filas globales con sucursal NULL quedan con sucursal_id NULL. El nombre legacy se conserva como cache de display; el downgrade quita FK, índice y columna.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Incorporar sucursal_id indexado a las tablas de aforo, parámetros, cámaras y promociones.\n\n'
                '🎯 POR QUE FUE GENERADA: Completa el enlace formal de la configuración física de cada sucursal a su identidad relacional única.\n\n'
                '⚙️ FUNCIONAMIENTO: Incorporar sucursal_id indexado a las tablas de aforo, parámetros, cámaras y promociones.'
            ),
        },
    },
    "f7a8b9c0d1e2_parking_branch_name_per_org.py": {
        "proposito": 'Cambia la unicidad del nombre de sucursal del ámbito global al ámbito por organización, para que varias empresas puedan tener una sede con el mismo nombre: deja ix_parking_branches_nombre como índice simple (no único) y crea el índice único uq_parking_branches_nombre_org sobre (nombre, COALESCE(organization_id,-1)). Usa IF (NOT) EXISTS para ser idempotente. El downgrade vuelve al nombre único global.',
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Restringir la unicidad del nombre de sucursal únicamente dentro del ámbito de cada empresa.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que organizaciones distintas puedan nombrar a sus sedes con apelativos comunes sin generar colisiones entre ellas.\n\n'
                '⚙️ FUNCIONAMIENTO: Restringir la unicidad del nombre de sucursal únicamente dentro del ámbito de cada empresa.'
            ),
        },
    },
    "f9a8b7c6d5e4_drop_legacy_support_reply_fields.py": {
        "proposito": "Elimina de 'support_tickets' las columnas legacy 'respuesta' y 'user_response', porque duplicaban el último mensaje del hilo y ahora la única fuente de verdad de la conversación es la tabla 'support_ticket_messages'. El downgrade las vuelve a crear (ambas de texto opcionales) como respaldo.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Eliminar los campos antiguos de respuesta única en los tickets de soporte.\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica el diálogo exclusivamente en la tabla de mensajes, evitando duplicaciones y desincronizaciones en las conversaciones.\n\n'
                '⚙️ FUNCIONAMIENTO: Eliminar los campos antiguos de respuesta única en los tickets de soporte.'
            ),
        },
    },
}
