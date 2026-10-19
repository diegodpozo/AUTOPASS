"""Explicaciones analizadas de migraciones Alembic, parte 1 (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "alembic/versions/49a240f0fc25_add_performance_indexes.py": {
        "proposito": 'Agrega índices sobre las columnas que más se filtran o buscan para acelerar consultas: access_logs por sucursal y tipo de evento, reservations por patente, sucursal y usuario, y vehicles por usuario. Además quita la columna access_logs.backend_time (que ya no se usaba) y ajusta redemption_tickets: hace opcional el código, reemplaza el índice por user_id por uno sobre id. El downgrade revierte exactamente estos cambios (vuelve a crear backend_time y los índices viejos).',
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Crear índices rápidos sobre accesos, reservas y vehículos, y limpiar campos en desuso.\n\n'
                '🎯 POR QUE FUE GENERADA: Acelera drásticamente las consultas más frecuentes del sistema y evita demoras al filtrar historiales masivos.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade crea los índices de rendimiento, elimina backend_time y reordena los índices de redemption_tickets; downgrade los deshace en sentido inverso.'
            ),
        },
    },
    "alembic/versions/8b3e9e815c78_drop_redundant_pk_id_indexes.py": {
        "proposito": 'Elimina dos índices redundantes sobre la clave primaria id de las tablas redemption_tickets y support_ticket_messages. La propia PK ya crea un índice en SQLite/Postgres, así que los índices ix_*_id no aportan nada y solo ocupan espacio y ralentizan escrituras; los modelos no los declaran y esta migración alinea la cadena Alembic con eso. El downgrade los vuelve a crear.',
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Quitar índices redundantes que duplicaban la indexación natural de la clave primaria.\n\n'
                '🎯 POR QUE FUE GENERADA: Porque la clave primaria ya indexa la columna por defecto; un índice extra duplicado solo desperdicia almacenamiento y hace más lentas las inserciones.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade dropea ix_redemption_tickets_id e ix_support_ticket_messages_id; downgrade los recrea como índices simples sobre id.'
            ),
        },
    },
    "alembic/versions/9c4f2a7b1e83_drop_coupons_table.py": {
        "proposito": 'Elimina por completo la tabla coupons (y su índice único ix_coupons_codigo). El concepto de cupones quedó cubierto por redemption_tickets y la tabla se quedó sin modelo ORM, por lo que se elimina para restaurar la paridad modelo↔Alembic que exige tests/test_schema_parity_p2.py. El downgrade recrea la tabla con sus columnas (id, código, descuento_porcentaje, fecha_expiracion, activo) y su índice único de código.',
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Dar de baja y remover la tabla antigua de cupones que ya no se utiliza en el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: La lógica de promociones migró a tickets de canje; quitar la tabla obsoleta evita confusiones y asegura que el esquema coincida con los modelos ORM actuales.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade dropea ix_coupons_codigo y la tabla coupons; downgrade la recrea con su índice único por código.'
            ),
        },
    },
    "alembic/versions/a1b2c3d4e5f6_redemption_tickets.py": {
        "proposito": "Crea la tabla redemption_tickets, que representa los tickets de canje (vouchers, descuentos, etc.) que un usuario obtiene por canjear puntos o promociones: guarda código único, título, descripción, tipo de canje, valor de descuento, ícono, sucursal, estado (VIGENTE por defecto), datos del QR, observación, fecha de creación/uso y la reserva asociada, con claves foráneas a users y promotions. También agrega a promotions las columnas tipo_canje (default 'voucher') y valor_descuento para definir qué tipo de canje ofrece cada promoción. El downgrade elimina la tabla y esas dos columnas.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Crear la tabla de tickets de canje para emitir vouchers y descuentos canjeables con puntos o promociones.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que los beneficios obtenidos por el cliente tengan ciclo de vida propio, código único, QR y trazabilidad al aplicarse a una estadía.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade agrega tipo_canje y valor_descuento a promotions, crea redemption_tickets con sus índices por código (único) y user_id; downgrade elimina todo en sentido inverso.'
            ),
        },
    },
    "alembic/versions/a1c2e3f4b5d6_organizations_multi_tenant.py": {
        "proposito": "Introduce el multi-tenant por organizaciones: crea la tabla organizations (nombre único, flags es_principal/activa, created_at) y agrega la columna organization_id con su índice y FK a organizations en las cinco tablas raíz (users, parking_branches, settings, parking_aforo y promotions); el resto de las tablas se aislan por su sucursal o usuario. Hace un backfill que crea la organización principal 'AUTOPASS' y la asigna a todas las filas existentes. Es idempotente (usa el inspector de SQLAlchemy para chequear tablas, columnas e índices antes de crear nada) porque sync_schema ejecuta create_all antes que Alembic y en una base nueva las tablas ya pueden existir. El downgrade elimina las FKs (solo Postgres), índices, columnas organization_id y la tabla organizations.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Incorporar la entidad de organizaciones para permitir la coexistencia de múltiples empresas en la misma base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Habilita el esquema multi-inquilino (multi-tenant) aislando usuarios, sedes, tarifas y promociones según la empresa correspondiente.\n\n'
                "⚙️ FUNCIONAMIENTO: upgrade crea organizations, agrega organization_id + índice + FK en las tablas raíz (idempotente) y backfillea la organización 'AUTOPASS'; downgrade revierte todo."
            ),
        },
    },
    "alembic/versions/a3b4c5d6e7f8_add_adjunto_support_messages.py": {
        "proposito": 'Agrega a la tabla support_ticket_messages dos columnas para adjuntos de archivos en los mensajes del sistema de soporte: adjunto_url (dirección del archivo) y adjunto_nombre (nombre original para mostrar). Ambas son opcionables; el downgrade las elimina.',
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Añadir soporte para adjuntar archivos e imágenes en los mensajes del centro de ayuda.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que usuarios y operadores adjunten capturas de pantalla o comprobantes para resolver incidencias con mayor claridad.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade agrega adjunto_url y adjunto_nombre; downgrade las quita.'
            ),
        },
    },
    "alembic/versions/a4c8d2e3f5b6_add_tipo_vehiculo_to_reservations.py": {
        "proposito": "Agrega a la tabla reservations la columna tipo_vehiculo (texto con default 'Auto') para registrar el tipo de vehículo de cada reserva (auto, moto, camioneta, etc.). El downgrade la elimina.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Incorporar la categoría o tipo de vehículo (auto, moto, camioneta) en cada registro de reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite tarifar y controlar el aforo disponible de manera diferenciada según el tamaño del rodado reservado.\n\n'
                "⚙️ FUNCIONAMIENTO: upgrade agrega tipo_vehiculo con default 'Auto'; downgrade la dropea."
            ),
        },
    },
    "alembic/versions/a7f3d9c2e1b8_timestamps_checks_settings_unique.py": {
        "proposito": "Moderniza tipos y agrega validaciones a nivel de base de datos. Solo en Postgres: convierte las columnas de fecha que estaban guardadas como texto (fecha_hora y fecha_pago en access_logs; fecha_inicio, fecha_fin y fecha_pago en reservations; fecha_creacion y fecha_confirmacion en mercadopago_payments; fecha en points_log) a timestamp real con CAST usando NULLIF para tolerar strings vacíos; y crea once check constraints que impiden saldos/puntos/montos/capacidades negativos, descuentos fuera de 1–100 y reservas cuya fecha_fin sea anterior a la fecha_inicio. En ambas bases crea el índice único uq_settings_clave_sucursal sobre (clave, COALESCE(sucursal,'')) para que cada configuración exista una sola vez por sede (los globales con sucursal NULL cuentan como su propio valor). El downgrade revierte el índice y, en Postgres, los checks y los tipos de fecha.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Convertir fechas de texto a marcas de tiempo formales e imponer restricciones de integridad en la base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que entren datos corruptos (como importes negativos o fechas invertidas) asegurando coherencia directamente en el motor relacional.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade pasa fechas a timestamp y crea checks (solo Postgres) y el índice único de settings (ambas bases); downgrade elimina el índice y revierte checks y tipos en Postgres.'
            ),
        },
    },
    "alembic/versions/a9b8c7d6e5f4_reservation_price_snapshot.py": {
        "proposito": "Agrega a reservations columnas que guardan una 'foto' del cálculo de precio al momento de cotizar, para dejar trazabilidad aunque después cambie el tarifario: tarifa_hora y tarifa_fraccion (tarifas unitarias de la sede), tarifa_aplicada (tarifa de la modalidad usada), horas_calculadas (duración cotizada), monto_calculado (total base antes de descuentos), descuento_pct (% de descuento por canje aplicado al pagar) y tarifa_fijada_en (momento en que se fijó la foto). El downgrade elimina las siete columnas.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Guardar una captura inmutable de las tarifas y fórmulas aplicadas al momento de confirmar una reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita discrepancias o recálculos inesperados si la administración actualiza el cuadro tarifario mientras la reserva sigue vigente.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade agrega las siete columnas de la foto de tarifas a reservations; downgrade las elimina.'
            ),
        },
    },
    "alembic/versions/b2c3d4e5f6a7_settings_unique_per_org.py": {
        "proposito": 'Ajusta la unicidad de settings al esquema multi-tenant: el índice único anterior uq_settings_clave_sucursal (clave + COALESCE(sucursal_id,-1)) hacía que dos organizaciones no pudieran tener su propia fila global para la misma clave, porque colisionaban. Lo reemplaza por uq_settings_clave_sucursal_org, que también incluye COALESCE(organization_id,-1) para que cada empresa tenga su tarifario global aislado. Usa DROP/CREATE INDEX IF (NOT) EXISTS para ser idempotente ante sync_schema. El downgrade vuelve al índice por clave+sede.',
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Ajustar la regla de unicidad de configuraciones para incluir la organización a la que pertenecen.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve el conflicto que impedía que dos organizaciones distintas tuvieran sus propias configuraciones globales con el mismo nombre de clave.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade cambia uq_settings_clave_sucursal por uq_settings_clave_sucursal_org; downgrade lo reemplaza al revés.'
            ),
        },
    },
    "alembic/versions/b2f4e8c1a9d7_fk_sucursal_parking_branches.py": {
        "proposito": 'En Postgres, crea claves foráneas que vinculan la columna sucursal (que guarda el nombre de la sede) de las cuatro tablas de configuración —parking_aforo, settings, parking_cameras y promotions— con parking_branches.nombre, que es único y funciona como clave natural de sede. Usa ON UPDATE CASCADE para que renombrar una sede propague el cambio y ON DELETE CASCADE para que eliminar una sede (ya validado en la aplicación) borre su configuración huérfana automáticamente. En SQLite no hace nada (no soporta ALTER ADD CONSTRAINT; ahí el FK se crea vía create_all). El downgrade elimina las cuatro FKs.',
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Enlazar con claves foráneas las tablas operativas a la tabla de sedes.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide registros huérfanos asociados a sedes inexistentes y propaga automáticamente cualquier renombrado de sede.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade crea las cuatro FKs sucursal→parking_branches.nombre solo en Postgres; downgrade las elimina.'
            ),
        },
    },
    "alembic/versions/b5c9d1e2f3a4_add_origen_to_reservations.py": {
        "proposito": "Agrega a la tabla reservations la columna origen (texto con default 'cliente') para registrar de dónde vino la reserva (cliente, admin, sistema, etc.). El downgrade la elimina.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Añadir un campo que indique el canal u origen desde donde se generó una reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite distinguir reservas originadas por la app del cliente de aquellas creadas manualmente por recepcionistas o procesos automáticos.\n\n'
                "⚙️ FUNCIONAMIENTO: upgrade agrega origen con default 'cliente'; downgrade la dropea."
            ),
        },
    },
    "alembic/versions/b7e3a1d2c4f5_add_user_sessions.py": {
        "proposito": 'Crea la tabla user_sessions para controlar las sesiones de cada usuario por dispositivo: guarda user_id (FK obligatoria a users), device_id, user_agent, ip_address, created_at y last_login_at. Crea tres índices (por user_id, device_id y last_login_at) para buscar rápido la sesión de un usuario en un dispositivo y poder limpiar o expirar sesiones antiguas. El downgrade elimina los índices y la tabla.',
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Crear una tabla dedicada para registrar y auditar las sesiones activas de cada usuario por dispositivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita el control de accesos concurrentes, el cierre remoto de sesiones y la caducidad por inactividad.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade crea user_sessions con sus tres índices; downgrade los elimina y borra la tabla.'
            ),
        },
    },
    "alembic/versions/b8f1c2d3e4a5_add_orden_to_parking_cameras.py": {
        "proposito": "Agrega la columna orden a parking_cameras para poder ordenar manualmente las cámaras en la grilla de monitoreo. Después de crearla, hace un UPDATE que copia el id de cada cámara existente en su orden, de modo que la vista previa sea el orden actual (por id); un valor NULL significa 'sin ordenar' y queda al final. El downgrade elimina la columna.",
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Añadir una columna de orden numérico a las cámaras de estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los operadores organizar el panel de monitoreo visual en la secuencia deseada en lugar de depender del orden de creación.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade agrega orden, la backfillea con el id de cada fila existente y downgrade la elimina.'
            ),
        },
    },
    "alembic/versions/c3d4e5f6a7b8_drop_sucursal_nombre_columns.py": {
        "proposito": 'Fase final de la migración a referencias de sede por id: elimina las columnas de NOMBRE legacy de sucursal en nueve tablas (reservations.sucursal_nombre, users.sucursal, access_logs.sucursal, support_tickets.sucursal, redemption_tickets.sucursal, parking_aforo.sucursal, settings.sucursal, parking_cameras.sucursal y promotions.sucursal), junto con sus índices por nombre y, en Postgres, sus FKs por nombre. La única fuente de verdad pasa a ser sucursal_id (FK → parking_branches.id), lo que hace que renombrar una sede ya no requiera propagar cambios. Recrea los índices que estaban sobre la columna de nombre: el compuesto ix_access_logs_pat_tipo_suc_fecha sobre sucursal_id y el único uq_settings_clave_sucursal sobre (clave, COALESCE(sucursal_id,-1)). El downgrade vuelve a agregar las columnas de nombre y sus índices/FKs.',
        "simbolos": {
            "upgrade / downgrade": (
                '💡 LA IDEA: Eliminar definitivamente los campos de nombre de sede en texto plano para usar exclusivamente el identificador numérico (sucursal_id).\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina redundancias frágiles y desacopla la integridad de los datos de cualquier modificación comercial en el nombre de una sede.\n\n'
                '⚙️ FUNCIONAMIENTO: upgrade elimina las columnas de nombre de sucursal, sus índices y FKs (solo Postgres las FKs), y recrea los índices sobre sucursal_id; downgrade agrega de vuelta las columnas y sus índices/FKs.'
            ),
        },
    },
}
