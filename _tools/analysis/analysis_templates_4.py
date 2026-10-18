"""Explicaciones analizadas de templates/profile (análisis del código real).

Cubre los 9 parciales de la vista de perfil: las pestañas (inicio, cuenta,
notificaciones, puntos, reservas, vehículos, ayuda) y los contenedores de
modales (modals.html y el modal de onboarding). Ninguno define bloques
`{% block %}` de nivel superior, por eso `simbolos` está vacío en todos.
"""

ANALISIS: dict[str, dict] = {
    "templates/profile/modals.html": {
        "proposito": 'Recolecta los modales reutilizados por toda la vista de perfil (se inyecta una sola vez desde perfil.html): el detalle de un ticket de soporte con su hilo de mensajes, respuestas y adjuntos; el pase digital de reserva (ticket tipo boarding-pass con QR, datos de la estadía, total y acciones de pago con saldo o Mercado Pago); el ticket de canje de un beneficio por puntos (QR canjeable); el modal de carga de saldo (formulario con montos rápidos $1000/$5000/$10000); y el modal legal que carga dinámicamente términos o privacidad. Todos los IDs tienen prefijo propio y las acciones delegan en funciones JS del perfil (closeSupportTicketModal, payReservationFromPass, processRecharge, openLegalModal, etc.).',
        "simbolos": {
        },
    },
    "templates/profile/modals/onboarding_modal.html": {
        "proposito": 'Modal de bienvenida dirigido a usuarios sin vehículos registrados: muestra una guía en tres pasos (vincular patente, elegir sucursal y estadía, obtener el pase QR) con enlaces para omitir la guía (skipReservationOnboarding) o iniciar el alta de vehículo (startReservationOnboarding), más notas legales que abren el modal de privacidad/términos. Se incluye desde la pestaña inicio.html y su apertura la controla el JS del perfil.',
        "simbolos": {
        },
    },
    "templates/profile/tabs/ayuda.html": {
        "proposito": "Pestaña 'Centro de Ayuda y Soporte': combina autoayuda y contacto directo. Arriba, píldoras de categorías que filtran el contenido (filterHelpCategory) y seis tarjetas de guías interactivas que disparan tours guiados (tour general, alta de vehículo, crear reserva, cargar saldo, canjear puntos, pase QR). En el medio, un FAQ acordeón agrupado por categoría (reservas/aforo, ALPR/QR, vehículos/tarifas, saldo/puntos) con búsqueda que puede quedar vacía (#help-empty-search). Abajo, canales de contacto (WhatsApp, correo, presencial) y el formulario de ticket de soporte (submitSupportTicket) con categoría, sucursal, asunto y detalle, seguido de la lista 'Mis Consultas' filtrable por estado (filterMyTickets) y abrible en el modal de detalle.",
        "simbolos": {
        },
    },
    "templates/profile/tabs/cuenta.html": {
        "proposito": "Pestaña 'Mi Cuenta': encabezado con saludo/.avatar (iniciales, nombre y fecha de alta cargados por JS), tarjeta de estadías en curso (donde se abona en salida) y un hub de gestión en dos paneles: datos personales (nombre, apellido, DNI, email, teléfono) en modo consulta/edición por campo (enterEditMode/exitEditMode/saveField) y seguridad con formulario de cambio de contraseña (changePassword) que incluye mostrar/ocultar, requisitos en vivo (8+ caracteres, mayúscula, símbolo, coincidencia) y medidor de fortaleza.",
        "simbolos": {
        },
    },
    "templates/profile/tabs/inicio.html": {
        "proposito": 'Pestaña de inicio del perfil y pantalla principal de reserva del usuario. Presenta el saludo, incluye el modal de onboarding y un stepper de cuatro pasos (Vehículo → Sucursal → Horario → Confirmación). Si el usuario no tiene vehículos muestra un estado vacío con alta rápida de Auto/Moto/Camioneta (quick-add); si tiene, el formulario de reserva moderno: selects de vehículo/sucursal/tipo de estadía, campos dinámicos por tipo (hora, día, semana, quincena, mes), contenedor de disponibilidad y slots horarios, y resumen de total con descuentos antes de continuar (createReservation). A la derecha, mapa Leaflet de sucursales; abajo, accesos a cargar saldo y beneficios.',
        "simbolos": {
        },
    },
    "templates/profile/tabs/notificaciones.html": {
        "proposito": "Pestaña 'Centro de Notificaciones': barra de filtros por categoría/estado (todas, no leídas, reservas, pagos y saldo, soporte, seguridad) que delegan en filterNotifs, más acciones masivas de marcar como leídas (markAllNotifRead) y borrar leídas (clearReadNotifs), ambas deshabilitadas hasta que haya datos. El listado real se puebla por JS en #notifications-container.",
        "simbolos": {
        },
    },
    "templates/profile/tabs/puntos.html": {
        "proposito": "Pestaña 'Mis Puntos': resumen del saldo de puntos disponibles y estadísticas de acumulado/canjeado, sección de vouchers y beneficios con pestañas Vigentes/Finalizados (switchVoucherTab) y contenedor de tarjetas, catálogo de promociones filtrable por sucursal (applyPromoBranchFilter), y el historial paginado de movimientos de puntos (changePtsPage). Todos los datos numéricos y listados los llena el JS del perfil; el HTML solo aporta estructura, contenedores y botones.",
        "simbolos": {
        },
    },
    "templates/profile/tabs/reservas.html": {
        "proposito": "Pestaña 'Mis Reservas': tarjetas de estadística (en curso y próximas), la estadía actual destacada (#reservation-featured-list), la grilla de reservas próximas con skeleton de carga, y el historial de estadías paginado (historialPage) con filtros por rango de fechas (applyHistoryFilters/resetHistoryFilters). Las tarjetas reales (pase QR, cancelación, pago) se generan por JS al llenar los contenedores.",
        "simbolos": {
        },
    },
    "templates/profile/tabs/vehiculos.html": {
        "proposito": "Pestaña 'Mis Vehículos': permite dar de alta patentes (Auto, Moto o Camioneta) mediante un formulario compacto que se muestra/oculta con toggleVehicleForm y se envía con addVehicle; el ícono del selector cambia según el tipo elegido (updateVehicleTypeIcon). La flota del usuario se lista por JS dentro de #vehicle-list (tarjetas con favorito, edición y borrado).",
        "simbolos": {
        },
    },
}
