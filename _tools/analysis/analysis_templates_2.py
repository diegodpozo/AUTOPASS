"""Explicaciones analizadas de templates del dashboard (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "templates/dashboard.html": {
        "proposito": "Esqueleto del panel administrativo: hereda de base.html, valida en el cliente que haya token y rol admin/local_admin/staff (sino redirige a '/') y arma la interfaz con barra lateral de pestañas, cabecera con reloj/estado del sistema y el contenedor que incluye las nueve pestañas del dashboard. Además define tres modales propios (detalle de captura de auditoría, salida con deuda pendiente del lector ALPR y detalle de reserva) e incluye el centro de ayuda operativa; al final carga dashboard.js como módulo.",
        "simbolos": {
            "title": (
                '💡 LA IDEA: Definir el título identificador en la pestaña del navegador para el panel de administración.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite reconocer rápidamente que se está operando dentro del centro de control administrativo de AUTOPASS.\n\n'
                "⚙️ FUNCIONAMIENTO: Título de la pestaña del navegador del panel admin: 'AUTOPASS Admin - Control Inteligente'."
            ),
            "body_class": (
                '💡 LA IDEA: Asignar la clase CSS que reserva el espacio lateral para el menú de navegación del administrador.\n\n'
                '🎯 POR QUE FUE GENERADA: Adapta el lienzo general para desplegar la barra lateral fija con accesos directos a todas las pestañas de gestión.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica la clase layout-with-sidebar al body para que base.html reserve el ancho de la barra lateral del admin.'
            ),
            "extra_head": (
                '💡 LA IDEA: Cargar las hojas de estilo del dashboard, perfil e insignias de notificación en la cabecera HTML.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el panel cuente con el diseño visual de tablas, métricas, tarjetas y animaciones de alerta.\n\n'
                '⚙️ FUNCIONAMIENTO: Inyecta los CSS compartidos del dashboard y del perfil más un bloque de estilos propio con la insignia roja de notificaciones (.notif-badge) y su animación de pulso usada en el sidebar y en los contadores de reservas/tickets.'
            ),
            "content": (
                '💡 LA IDEA: Renderizar el cuerpo completo del panel de control con sus módulos, cabecera de estado y ventanas modales de operación.\n\n'
                '🎯 POR QUE FUE GENERADA: Concentra en una sola vista toda la botonera y las pestañas operativas (monitoreo, reservas, finanzas, usuarios y soporte).\n\n'
                '⚙️ FUNCIONAMIENTO: Cuerpo del panel: script de guardia de rol (localStorage token/rol + clase role-<rol> para evitar parpadeo), el aside con el menú de pestañas (Monitoreo, Reservas, Usuarios, Finanzas, Métricas, Promociones, Tickets, Sucursales, Configuración y Ayuda) filtrado por clases de visibilidad por rol, la cabecera con título dinámico e indicador de salud, el contenedor que hace include de las nueve pestañas, los modales de captura de auditoría, salida con deuda (con método de pago y botón de cobrar y abrir barrera) y detalle de reserva, y el include del centro de ayuda.'
            ),
            "extra_scripts": (
                '💡 LA IDEA: Importar el script principal de JavaScript que da vida interactiva al panel administrativo.\n\n'
                '🎯 POR QUE FUE GENERADA: Conecta la interfaz con el backend para actualizar en tiempo real ingresos, gráficos, cámaras y aforos.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga /static/js/dashboard.js como módulo ES con sufijo ?v={{ cache_buster }} para evitar caché stale entre despliegues.'
            ),
        },
    },
    "templates/dashboard/modals/admin_help_modal.html": {
        "proposito": 'Centro de Ayuda Operativa para staff y administradores: modal con buscador de texto y pills de categoría que filtran tanto las tarjetas de tours guiados (uno por módulo, con botones que disparan startAdmin*Tour) como los grupos de FAQ operativa en acordeón (contingencias ALPR/barreras, reservas y cobros, usuarios y saldo). Sirve como capacitación y soporte rápido sin salir del panel.',
        "simbolos": {
        },
    },
    "templates/dashboard/modals/branch_modals.html": {
        "proposito": 'Modales de sucursales: uno muestra los niveles/pisos de una sucursal en tabla con la ocupación frente a la capacidad por tipo de vehículo y de reservas (cuerpo cargado por JS), y el otro es el formulario de alta/edición de sucursal con datos de contacto, dirección geolocalizable (botón de búsqueda, coordenadas ocultas y selector de punto en mapa), carga/limpieza de logo y horario operativo con interruptor de 24 horas.',
        "simbolos": {
        },
    },
    "templates/dashboard/modals/promotion_modal.html": {
        "proposito": 'Modal de alta de promociones canjeables por puntos: recoge título, costo en puntos, descripción, selector visual de ícono, tipo de canje (voucher con QR o descuento por porcentaje en la reserva, con campo condicional), sucursal asignada (solo admin) y la ubicación de canje con dirección buscable y mapa. Al enviar llama a handleCreatePromotion.',
        "simbolos": {
        },
    },
    "templates/dashboard/modals/user_modals.html": {
        "proposito": 'Tres modales de gestión de usuarios desde el panel: alta (nombre, apellido, email, DNI, rol con selección condicional de sucursal, contraseña temporal o invitación por mail con campo de organización), edición (mismos datos más teléfono y oculto con el id) y cambio de contraseña forzado por administración. Cada formulario delega su envío en handleAdminCreateUser, handleAdminEditUser y handleAdminChangePassword.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/admin_reservations.html": {
        "proposito": 'Pestaña Reservas del admin: tres KPIs (total, pendientes hoy y reservas de hoy) y el registro de reservas con alta manual, filtro por estado, búsqueda por patente, tabla paginada con skeleton. Incluye además el modal de reserva manual (patente con identificación del dueño, tipo de vehículo y de estadía con campos dinámicos por período, grilla de disponibilidad horaria, método de pago y total calculado) y el modal de confirmación de edición que resume la diferencia financiera antes de guardar.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/branches.html": {
        "proposito": 'Pestaña Sucursales (visible solo para super-admin): tarjeta con botón de alta y tabla con dirección, administrador, plazas de autos/motos, teléfono, horario, estado y acciones, cargada por JS con skeleton. Al final incluye los modales de sucursal (ver niveles y alta/edición).',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/finance.html": {
        "proposito": 'Pestaña Reporte Financiero: resumen colapsible con seis KPIs de recaudación (neto, efectivo, digital, reembolsado, tickets y ticket promedio), tres de eficiencia (proyectado, tasa de cancelación y no-show), desglose por canal (estadías/reservas) y por método de pago en pestañas; gráfico de tendencia de ingresos con filtros de método, vehículo, fecha y período; e historial de pagos exportable a CSV con paginación.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/live.html": {
        "proposito": 'Pestaña Monitoreo: accesos a estadísticas OCR y monitor multi-cámara, grilla de disponibilidad por tipo de vehículo (general y reservas, autos/motos/camionetas con spans ocultos que alimentan los totales), tarjeta de ingreso manual por patente con selección de piso y comandos de apertura/cierre de barreras de entrada y salida, y listados con sub-pestañas (vehículos estacionados y últimos movimientos) con buscadores y paginación propios.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/metricas.html": {
        "proposito": 'Pestaña Métricas con dos vistas: la lista de cinco informes (actividad de accesos, mapa de calor de tráfico, ocupación y reservas, recaudación y tiempos OCR/ALPR) y las vistas de detalle, cada una con botón volver, filtros de fecha/sucursal, KPIs dinámicos y su gráfico. El detalle de accesos agrega seguimiento en vivo, ventana temporal, deslizador de recorrido histórico y navegación a inicio/final; el de recaudación muestra además la tabla de ventas por sucursal solo para administrador general.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/promotions.html": {
        "proposito": 'Pestaña Promociones: tarjeta con botón de alta (oculto para staff) y tabla de beneficios con puntos, sucursal, estado y acciones, cargada por JS con skeleton. Incluye al final el modal de creación de promoción.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/settings.html": {
        "proposito": 'Pestaña Configuración (para local_admin): tarjeta con barra de sub-pestañas TARIFARIO, PLAZAS, MONITOREO y SISTEMA que alternan secciones con switchSettingsTab, y un cuerpo que hace include de las cuatro secciones settings_* anidadas. No trae contenido propio más allá de la navegación y el contenedor.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/tickets.html": {
        "proposito": 'Pestaña Soporte & Tickets: cuatro KPIs (total, pendientes, en proceso, resueltos) y la tabla de tickets con filtro por estado y búsqueda por asunto/cliente/categoría. Incluye el modal de atención con ficha del cliente, hilo de conversación, textarea de respuesta, selector de estado y aviso de bloqueo cuando el ticket está cerrado; envía por submitTicketAnswer.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/users.html": {
        "proposito": 'Pestaña Gestión de Usuarios: resumen colapsible con cuatro KPIs por rol (totales, administradores, empleados y clientes), y la lista de usuarios con búsqueda por nombre/DNI/email, filtro por rol, botón de alta y tabla paginada con puntos y saldo por cliente. Incluye al final los tres modales de usuario (alta, edición y cambio de contraseña).',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/settings/settings_floors.html": {
        "proposito": 'Sección PLAZAS de Configuración: contenedor del grid de arquitectura de edificios (pisos/niveles con sus plazas) que el JS renderiza dinámicamente; solo deja un estado de carga inicial con spinner mientras sincroniza la estructura.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/settings/settings_monitoring.html": {
        "proposito": 'Sección MONITOREO de Configuración: barra con el botón AGREGAR CÁMARA (showCreateCameraModal) y la grilla de dispositivos camera-settings-list donde el JS dibuja las cámaras IP con su estado, mostrando mientras tanto un spinner de carga.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/settings/settings_rates.html": {
        "proposito": 'Sección TARIFARIO de Configuración: sub-pestañas AUTOS/MOTOS/CAMIONETAS que alternan tres grupos de tarifas, cada uno con cinco importes (fracción de 30 min, hora, día, semana y mes) cargados por JS en inputs deshabilitados que se habilitan recién al pulsar EDITAR (toggleRateEdit), evitando ediciones accidentales.',
        "simbolos": {
        },
    },
    "templates/dashboard/tabs/settings/settings_system.html": {
        "proposito": 'Sección SISTEMA de Configuración: grid de diagnóstico con cuatro tarjetas de estado (base de datos, servidor, barreras de entrada/salida y lectores de patente) con puntos online/offline que actualiza el JS. Cierra los divs abiertos por settings.html y agrega dos modales compartidos de la configuración: alta/edición de nivel con seis capacidades (general y de reservas por tipo de vehículo) y alta/edición de cámara (tipo ALPR/QR/vigilancia, IP, sucursal y flag de activa).',
        "simbolos": {
        },
    },
}
