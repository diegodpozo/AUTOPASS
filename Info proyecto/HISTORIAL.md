# HISTORIAL DEL PROYECTO: AUTOPASS

- **JUNIO 30, 2026 - UI/UX & FAB REFINEMENT (V9.3.0)**:
    *   **FAB en Perfil**: Nueva tarjeta flotante "Nueva Reserva" (FAB) con animación expansiva al hover, reemplazando los botones redundantes en cada tab del perfil.
    *   **FAB oculto en Inicio**: El FAB se oculta automáticamente en la tab "inicio" para no interferir con la vista principal del usuario.
    *   **Fix Animación FAB**: Corregido bug donde el icono desaparecía al replegarse; se reemplazó `width` fija por `min-width` y el label usa `max-width` animado.
    *   **Cards de Monitoreo Limpias**: Eliminado texto repetido "Tot. Disp." de las cards de aforo en `live.html` y `dashboard-stats.js`.
    *   **Barras de Progreso Dinámicas**: Colores variables según ocupación: verde (>50%), amarillo (26-50%), naranja (11-25%), rojo (≤10%).
    *   **Worker DB Robustez**: Wrapped DB sessions en `try/finally` para evitar agotamiento del pool de conexiones (`QueuePool limit`).
    *   **Pool de Conexiones**: Aumentado pool size a 10 con overflow 20 y timeout 60s para motores no-SQLite.
    *   **Títulos de Cards Actualizados**: "HACÉ TU RESERVA MANUAL" → "HACÉ TU RESERVA", "HACÉ TU RESERVA DESDE EL MAPA" → "SELECCIONÁ LA SUCURSAL DESDE EL MAPA".

- **JUNIO 23, 2026 - RESERVAS & AFORO INTELIGENTE (V9.2.0)**:
    *   **Aforo por Reserva No Horaria**: Las reservas de Día/Semana/Quincena/Mes descuentan la plaza del aforo al iniciar el período (vía worker `_process_started_reservations`). La plaza se libera solo al vencer el período o al cancelar, permitiendo al cliente entrar y salir libremente sin perder su lugar.
    *   **Restricción de Anticipación Selectiva**: Solo las reservas por hora requieren anticipación mínima (1 hora configurable). Las de período largo no tienen restricción.
    *   **Liberación Automática al Vencer**: El WorkerService libera la plaza automáticamente cuando la reserva expira, incluso si el vehículo nunca ingresó.
    *   **Salida Física sin Liberación**: La salida por ALPR/QR ya no libera la plaza de reservas no horarias — la gestión de aforo queda a cargo del ciclo de vida de la reserva.
    *   **Parametrización**: Nueva variable de entorno `RESERVA_HORA_MIN_SEGUNDOS` (default 3600) para configurar el tiempo mínimo de anticipación en reservas por hora.
    *   **Validación Sincronizada**: Frontend y backend validan consistentemente: solo reservas por hora con 1 hora de anticipación; el resto sin restricción.

- **JUNIO 17, 2026 - UX/UI REFINEMENT & RBAC (V9.1.5)**:
    *   **Rediseño Monitoreo**: Evolución de la pestaña de cámaras a un layout de grilla "Premium" con mejores indicadores de estado y visualización técnica mejorada.
    *   **Filtros Financieros**: Se añadió soporte para "Camionetas" en el reporte financiero del dashboard admin.
    *   **Seguridad UI (RBAC)**: Se eliminó la posibilidad de que un Administrador Local filtre o asigne el rol de Administrador General, endureciendo las reglas de visualización por jerarquía.
    *   **Fix de Estructura**: Corrección definitiva de solapamiento de pestañas en el panel de configuración.

- **JUNIO 17, 2026 - TRIMODAL PRICING & CAMIONETAS (V9.1.0)**:
    *   **Soporte para Camionetas**: Se integró "Camioneta" como tipo de vehículo oficial en el Enum, Base de Datos y Servicios.
    *   **Tarifario Trimodal**: Nueva pestaña en Configuración para gestionar los precios específicos de camionetas.
    *   **UI Updates**: Actualización de los formularios de usuario para permitir la selección de tipo de vehículo, rompiendo la dependencia exclusiva de la auto-detección por patente.
    *   **Iconografía**: Inclusión del icono `fa-truck-pickup` en todo el flujo de usuario y dashboard.

- **JUNIO 17, 2026 - REAL-TIME & SETTINGS OVERHAUL (V9.0.0)**:
    *   **Centralización de Cámaras**: Se movió la configuración de IPs y el control de servicios ALPR de la pestaña "Monitoreo" a una nueva sub-pestaña en "Configuración".
    *   **Aforo Real-time**: Implementación de WebSockets para la actualización instantánea del aforo en el dashboard, reemplazando el polling de 10 segundos.
    *   **Notification Service**: Creación de un servicio de notificaciones asíncronas para disparar eventos de WebSocket desde la lógica de negocio (`AccessService`).
    *   **UX Clean-up**: Se eliminaron botones de configuración de la vista de video para una experiencia de monitoreo más limpia ("Premium").
    *   **Fix Estructural**: Corrección de IDs y etiquetas en `settings.html` que causaban solapamiento de contenido entre pestañas.

- **JUNIO 17, 2026 - VIDEO STREAM OPTIMIZATION & DASHBOARD FIXES (V8.9.5)**:
    *   **Corrección de Visibilidad**: Eliminación de la lógica `onerror` que ocultaba los feeds de video; ahora el sistema restaura la opacidad al recibir el primer frame por WebSocket.
    *   **Placeholder Eficiente**: Uso de GIFs transparentes como placeholders para evitar errores 404 y mejorar la percepción de carga.
    *   **Seguridad WS**: Implementada validación preventiva de tokens en el frontend antes de abrir sockets de video para evitar colisiones con nodos ALPR.
    *   **Configuración Castelar**: Puesta en marcha exitosa de los nodos ALPR para entrada (IP) y salida (Local) en la sucursal Castelar.

- **JUNIO 16, 2026 - UI/UX REFINEMENT & FORM NORMALIZATION (V8.8.5)**:
    *   **Normalización de Formularios**: Estandarización de `height` (48px), `padding` (12px 15px) y `font-size` (0.9rem) en todos los inputs de reserva para asegurar una alineación perfecta.
    *   **Confirmación Minimalista**: Rediseño del alerta de confirmación de reserva eliminando marcos internos, simplificando la jerarquía visual y centrando la atención en el total estimado.
    *   **Gestión de Vehículos "Direct Swap"**: Refactorización del registro de vehículos reemplazando el sistema colapsable por un intercambio directo de interfaz (Botón <-> Formulario) con botón de cancelación negro estandarizado.
    *   **Unificación Estética**: Aplicación del estilo "Quick Add" (compacto y centrado) en todo el módulo de flota vehicular.
    *   **UX de Puntos**: Cambio de etiquetas ("Puntos Canjeados") y simplificación de los estados vacíos con iconos neutros y sin marcos.

- **JUNIO 15, 2026 - UX/UI MAP ENHANCEMENT & SMART OVERLAYS (V8.7.5)**:
    *   **Interactive Location Hint**: Implementación de la leyenda flotante "estacioná en tu zona" con manito animada (`fa-hand-point-down`) para incentivar el uso de la geolocalización.
    *   **Dynamic Map Overlay**: Rediseño del cuadro informativo para que sea contextual, mostrando detalles de la sucursal (nombre y dirección) solo cuando hay una selección activa.
    *   **Address Normalization**: Lógica de formateo automático en JS para corregir direcciones sin comas y estandarizar visualización en Title Case.
    *   **Sincronización Multi-Vistas**: Unificación de estilos y animaciones entre la Landing Page y el Dashboard del usuario (vía `landing.css` y `profile.css`).
    *   **Fix de Visibilidad**: Ajuste de `overflow` en tarjetas de dashboard para permitir que los elementos flotantes sobresalgan del contenedor del mapa sin recortes.

- **JUNIO 14, 2026 - DASHBOARD OPTIMIZATION & SMART MONITORING (V8.6.0)**:
    *   **Paginación Pro**: Listados de ocupación y movimientos limitados a 10 filas con navegación dinámica y **Auto-Scroll** suave al principio de tabla.
    *   **UI Operativa**: Panel de control manual siempre visible, eliminación de KPIs de ocupación total % y limpieza de indicadores de salud para mayor enfoque.
    *   **Alertas Estructuradas**: Nuevo sistema de confirmación vertical (Patente > Tipo > Monto) para ingresos, pagos y salidas.
    *   **Auto-Moto Detection**: Lógica frontend para identificar patentes de moto (`A123ABC`) y asignar el tipo de vehículo automáticamente en carga manual.
    *   **Política de Cortesía**: Reducción del margen de salida sin cargo a **10 minutos** sincronizado con el motor de facturación.
    *   **Cámaras Premium**: Remoción de imágenes de fallback (mapa) por fondo negro y centrado de visualización de patentes detectadas.

- **JUNIO 14, 2026 - FINANCIAL ANALYTICS & USER CONTROL (V8.5.5)**:
    *   **Filtros de Reporte**: Adición de selector de **Fecha Exacta** con calendario y filtrado por **Tipo de Vehículo** (Bimodal).
    *   **RBAC Empoderado**: Los `Local Admin` ahora pueden gestionar clientes (`USER`) además del personal de su sede.
    *   **Fix de Estabilidad**: Corrección de errores 403 (validación de roles) y 500 (estados de pago inexistentes).
    *   **Optimización SQL**: Refactorización de la unión de transacciones mediante subconsultas para mayor velocidad y precisión.
    *   **UI Premium**: Sincronización de iconos dorados en selectores y etiquetas en mayúsculas para filtros financieros.

- **JUNIO 09, 2026 - VERTICAL EXPANSION & BIMODAL SUPPORT (V8.2.0)**:
    *   **Gestión de Pisos**: Implementación de soporte para múltiples niveles por sucursal (`ParkingFloor`).
    *   **Unificación de PB**: Integración de la Planta Baja como nivel base en la tabla de gestión de plazas.
    *   **Soporte de Motos**: Identificación, cupos y tarifas independientes para motocicletas (Ahorro del ~50%).
    *   **RBAC Refinado**: Especialización de roles; Super Admin (Red/Usuarios) vs Local Admin (Operación de Sede/Pisos).
    *   **Fix Sucursal**: Nueva lógica de identificación de sede basada en datos del servidor para mayor estabilidad.

- **JUNIO 08, 2026 - REGIONAL ALPR & UI NORMALIZATION (V8.1.0)**:
    *   **Motor ALPR**: Soporte para patentes Mercosur (Brasil, Uruguay, Paraguay) con detección de franja azul.
    *   **Normalización**: Formateo unificado de patentes en todo el sistema (`ABC 1D23`, `ABC 1234`).
    *   **UI/UX**: Refinamiento de modales, mapas y dashboard financiero con recaudación neta.

- **JUNIO 05, 2026 - SMART FINANCE & FLEXIBLE CANCELLATIONS (V8.0.0)**:
  - **MOTOR DE REPORTES 2.0**: Implementación de `UNION ALL` y paginación en DB.
  - **CANCELACIÓN CON CORTESÍA**: Botón de salida con regla de 15 minutos sin cargo.
  - **REEMBOLSOS PROPORCIONALES**: Lógica de devolución basada en tiempo restante.

... [RESTO DEL HISTORIAL SE MANTIENE IGUAL] ...
