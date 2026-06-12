# HISTORIAL DEL PROYECTO: AUTOPASS

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
