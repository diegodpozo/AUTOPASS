# HISTORIAL DEL PROYECTO: AUTOPASS

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
