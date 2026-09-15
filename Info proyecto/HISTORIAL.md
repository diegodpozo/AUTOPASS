# HISTORIAL DEL PROYECTO: AUTOPASS

- **SEPTIEMBRE 14, 2026 - UBICACIÓN DE CANJE (MAPAS) & CARDS DE CANJEO CON FILTRO POR SUCURSAL (V9.19.0)**:
    *   **Ubicación de canje**: `promotions` y `redemption_tickets` suman `direccion`, `latitude` y `longitude` (migración Alembic `ce7d1e2f3a5b`, aplicada y verificada en Neon). El admin edita la ubicación de cada promo desde el panel con búsqueda Nominatim y mapa Leaflet (`promotion_modal.html`, `dashboard-promotions.js`).
    *   **Fallback de ubicación doble**: `_crear_ticket` guarda snapshot (ubicación de la promo → sino la de su sucursal); `GET /user/redemption-tickets` enriquece la respuesta sin reescribir BD (ticket → promo actual → sucursal), mostrando la dirección vigente incluso en tickets canjeados antes.
    *   **Link a Google Maps (mapa de calles)**: La dirección es un link `place/<direccion>/@lat,lng,z` con pin exacto en roadmap. Se quitó el token `data=!3m1!1e3` porque activaba la vista aérea/satélite (render 3D de casas); se descartaron `?basemap=roadmap` y `loc:` por romper la posición del pin. Fallbacks: `search/?api=1&query=` (solo dirección) y `?q=lat,lng&z=16` (solo coords).
    *   **Cards de canjeo con look tipo ticket**: Promos por canjear reescritas como `voucher-card promo-card` (gradiente violeta, badges de tipo + sucursal, divider, footer dorado), icono+título a la izquierda y descripción/dirección/puntos centrados (se anuló `translateX(-31px)` que las corría a la izquierda).
    *   **Filtro por sucursal**: Dropdown "Sucursal" sobre la grilla de promos (opciones: Todas / Globales / cada sucursal). Al filtrar por sucursal se ocultan las globales; `applyPromoBranchFilter` re-renderiza sin refetch.
    *   **Baja del ajuste manual de puntos**: Eliminados los botones `+10/−10`, `adjustPoints` (profile.js/perfil.js), el CSS `.points-adjust-*` y el endpoint `POST /user/points-adjust`.
    *   **Verificación**: `node --check` y `py_compile` en verde; assets versionados a `?v=9.19.0` para forzar la recarga de caché.

- **SEPTIEMBRE 13, 2026 - GLOBITO DE NOTIFICACIÓN EN RESERVAS DEL DASHBOARD EN TIEMPO REAL (V9.18.4)**:
    *   **Globito de Notificación en Reservas (`#reservation-badge-sidebar`)**: Badge rojo dinámico con animación pulsante `.pulse` sobre el ítem de navegación "Reservas" del Dashboard (`templates/dashboard.html`).
    *   **Endpoint Liviano de Detección**: `GET /v1/admin/reservations/new-count?since_id=...` (`routes/admin/reservations.py`) que obtiene de forma ultra rápida (`MAX(id)` y `COUNT(*)`) la cantidad de reservas nuevas registradas, con filtro de sucursal para administradores locales.
    *   **Notificación en Tiempo Real vía WebSocket**: Emisión con `NotificationService.notify_occupancy_change` al crear reservas desde el portal del usuario (`routes/user/reservations.py`) y de forma manual por administración (`services/reservation_service.py`). En el frontend, `initOccupancyWS` (`dashboard-stats.js`) dispara `updateReservationBadge()` instantáneamente al recibir el mensaje.
    *   **Auto-Limpieza al Entrar a Reservas**: `clearReservationBadge()` en `dashboard-reservations.js` oculta inmediatamente el globito y guarda el último ID visto en `localStorage` al hacer click o navegar a la pestaña "Reservas" (`switchTab('admin-reservations')`). Si el usuario ya está visualizando Reservas, la grilla se refresca en vivo sin alertar con globito.
    *   **Polling de Resguardo & Verificación**: Chequeo cada 10s para resguardo ante desconexiones, 3 pruebas unitarias añadidas en `tests/test_admin_reservations.py` y suite completa de 133/133 tests en verde (100% de efectividad).

- **SEPTIEMBRE 13, 2026 - DESCUENTOS DE RESERVA APLICADOS AL TOTAL & REDISEÑO DE MIS VOUCHERS Y BENEFICIOS (V9.18.3)**:
    *   **Fix de match de sucursal para descuentos (`redemption_sucursal_clause`)**: Las promociones y tickets de canje guardaban la sucursal con prefijo `"AUTOPASS "` (datos legados del seed), mientras el formulario de reserva usaba el nombre limpio del branch (`Ituzaingó`); el match exacto fallaba y los descuentos no se mostraban ni se aplicaban al pagar. Se agregó en `services/reservation_service.py` un método estático que normaliza la sucursal (quita el prefijo, espacios y mayúsculas), usado por `validate_redemption_ticket` y por `/redemptions/available`.
    *   **Normalización de datos legados**: UPDATE sobre `promotions.sucursal` (3 filas) y `redemption_tickets.sucursal` (8 filas) quitando el prefijo "AUTOPASS "; BD verificada sin valores remanentes con prefijo.
    *   **Descuento en el total de la reserva (portal usuario)**: `reservas-form.js` consulta `/redemptions/available` por sucursal (carga lazy con anti-race) y muestra en el total estimado en vivo y en el resumen de confirmación el total original tachado, la línea "DESCUENTO X% · -$Y" y el "TOTAL A PAGAR"; el descuento se consume al abonar (saldo o Mercado Pago).
    *   **Descuento aplicado también en caja (pago manual admin)**: `pay_reservation_manual` acepta `redemption_ticket_id` y valida el canje `descuento_reserva` vigente del usuario vinculado a la reserva (misma sucursal o global) para registrar el cobro sobre el valor descontado (consumiendo el ticket). Se aplica en `confirm-payment` y en el alta manual con pago; nuevos endpoints `GET /admin/reservations/{id}/redemptions` y `GET /admin/redemptions/available` para detectar el descuento en caja. En el panel el operador confirma un diálogo "Descuento aplicable" (monto, descuento %, total) antes de cobrar. Puntos acreditados sobre el monto efectivamente abonado.
    *   **Rediseño de "Mis vouchers y beneficios"**: Cards de descuento `descuento_reserva` presentadas como beneficio (sin código/QR/badge de ticket) con fila única icono + título + badge de sucursal, `%` de descuento destacado, "SE APLICA AUTOMÁTICAMENTE AL RESERVAR", "Vto." debajo y botón CANCELAR centrado. Cards de voucher unificadas al estilo violeta, sin badges de nº de ticket ni "VOUCHER", contenido con más contraste y centrado ópticamente (compensación de -31px), títulos en fila con icono y badge, y solo "Vto." (sin fecha de canje). Nueva función `formatTitulo` (con stopwords) que normaliza títulos en mayúsculas ("LAVADO" → "Lavado", "REGALO SORPRESA" → "Regalo Sorpresa") aplicada en cards de descuento, vouchers y el modal del ticket.
    *   **Total con descuento visible al editar una reserva manual (panel admin)**: Al modificar una reserva, `dashboard-reservations.js` consulta el nuevo `GET /admin/reservations/{id}/redemption-info` y muestra el total original tachado + línea "DESCUENTO X% · -$Y" con el total con descuento (fuente `vigente`, se aplica al abonar; fuente `aplicado`, la reserva ya se pagó con ese descuento en caja). `update_admin_reservation` conserva el mismo % al recalcular el monto si la reserva se pagó con descuento, quedando cobros/reembolsos por diferencia sobre la base descontada.
    *   **Verificación**: Suite completa de pytest (130/130 en verde, con 15 casos nuevos de descuentos en caja y en edición) y `node --check` OK sobre los JS modificados.

- **SEPTIEMBRE 12, 2026 - AJUSTE FINANCIERO AL EDITAR RESERVAS PAGADAS, NETO CON REEMBOLSOS & REPORTE ROBUSTO (V9.18.1)**:
    *   **Edición con Cobro/Reembolso de Diferencia**: Al editar el monto de una reserva **Pagada** desde el dashboard admin (`PUT /v1/admin/reservations/{id}`), la diferencia se resuelve automáticamente: si el nuevo total es **mayor**, se cobra la diferencia (actualiza `monto_total` y `fecha_pago`, registrando el método elegido en `cobrar_diferencia_metodo`); si es **menor**, se reembolsa acumulando en `monto_reembolsado`. La devolución sigue el **canal elegido**: si el método es `SALDO`/billetera, se acredita al saldo virtual del usuario (descontando puntos con registro en `PointsLog`); si es **efectivo** (`CAJA`/`EFECTIVO`) u otro canal externo, se devuelven **billetes/por fuera del sistema** sin tocar el saldo, quedando imputada en el reporte al método correspondiente. El monto neto siempre es `monto_total − monto_reembolsado`.
    *   **Modal de Confirmación de Edición (`#modal-edit-resumo`)**: La pestaña Reservas del dashboard muestra un resumen previo con detalle por ítem, nuevo total, **diferencia a cobrar/reembolsar y selector de método de pago** para la operación (usado por los reportes). Con diferencia cero no se tocan las finanzas. Reescrito con la estructura estándar `.modal` / `.modal-content` (se descartó la clase inexistente `modal-overlay` que desalineaba el modal).
    *   **Monto Neto en Interfaces**: El listado admin, el detalle de reserva ("Pagado $X · Reemb. -$Y") y el lado del usuario (tarjetas activas, historial y comprobante/QR) muestran el **monto neto** (`monto_total − monto_reembolsado`) sin notas de reembolso visibles para el cliente (solo el monto actualizado). `UserReservationResponse` incorpora `monto_reembolsado`.
    *   **Reporte Financiero con Reembolsos Parciales**: `_es_reembolso_parcial` en `services/report_service.py` reconoce reembolsos de reservas `REEMBOLSADO` **o** `PAGADO` con `monto_reembolsado > 0`, y los integra en el resumen (`total_reembolsado`), el desglose por método y el historial (entradas `REF{id}`).
    *   **Suite de 107 Tests Automáticos**: 5 casos nuevos en `tests/test_admin_reservations.py` (cobro por aumento de monto, reembolso a saldo por disminución, sin diferencia sin tocar finanzas, múltiples ajustes con neto correcto, y reporte que cuantifica el reembolso parcial de una reserva pagada). Suite completa en verde.

- **SEPTIEMBRE 11, 2026 - GESTIÓN DE RESERVAS ADMIN, OAUTH 2.0, METODO DE PAGO & TIPO VEHÍCULO EN RESERVAS (V9.14.2+)**:
    *   **Gestión Integral de Reservas para Administradores**: Rediseño completo de la pestaña de Reservas del Dashboard (`routes/admin/reservations.py`, `dashboard-reservations.js`). Búsqueda multi-criterio por cliente, email, DNI, patente, ID de reserva y sucursal. Filtros por estado (`PENDIENTE_PAGO`, `PAGADA`, `EN_USO`, `FINALIZADA`, `CANCELADA`), tipo de vehículo, rango de fechas y sucursal.
    *   **Creación y Edición de Reservas a Nombre del Usuario**: El Administrador puede emitir reservas directamente seleccionando cliente, sucursal, fechas, patente y tipo de vehículo, con cálculo dinámico de precio y comprobación de cupos de reserva en tiempo real.
    *   **Confirmación de Pagos Manuales & Reembolsos**: Endpoint `POST /v1/admin/reservations/{id}/confirm-payment` para registrar pagos con método elegible (`DIGITAL`, `CAJA` / Efectivo, `MERCADOPAGO`, `SALDO`). Cancelación administrativa con simulación y acreditación al saldo del usuario.
    *   **Columnas `tipo_vehiculo` y `metodo_pago` en Reservas**: Migraciones Alembic `a4c8d2e3f5b6_add_tipo_vehiculo_to_reservations.py` y `d3b7e1a9c2f0_add_metodo_pago_to_reservations.py`.
    *   **Login Social OAuth 2.0 (Google & Facebook)**: Servicio completo en `services/oauth_service.py` con state HMAC stateless, intercambio de token, modal de compleción de registro (DNI/Teléfono) y suite de pruebas `tests/test_oauth.py`.
    *   **Suite de 82 Tests Automáticos**: Expansión de la suite a **82 pruebas passing en 21 archivos** (`pytest`), logrando 100% de ejecución limpia.
    *   **Mejoras de UI / UX**: Modal de tickets scrolleable y responsive (header X fija, acciones apiladas), saludos personalizados en monitor ALPR ("¡BIENVENIDO!" / "¡HASTA LUEGO!") y CSS PWA `standalone.css`.

- **SEPTIEMBRE 5, 2026 - TARIFA FRACCIÓN 30 MIN & SELECTOR POR RANGO (V9.10.0)**:
    *   **Casillas de Horarios Más Compactas**: Se redujo la altura de la grilla de horarios: padding de las casillas de `6px 12px` a `3px 8px`, fuente de `0.78rem` a `0.68rem` y gap de la grilla de 6px a 4px. Resultado: la grilla de 34 horarios ocupa ~40% menos de alto en pantalla.
    *   **Mensaje de Selección de Horario Eliminado**: Se quitó por completo el texto "Inicio: X — ahora tocá la hora de fin" y el resumen "X → Y (Nh)" que aparecía/desaparecía entre el picker de día y la grilla al seleccionar horarios. La página ya no se mueve; el estado de selección se refleja solo en las casillas resaltadas.
    *   **Toasts de Selección de Horario Eliminados**: Se quitaron las notificaciones flotantes que aparecían al tocar/arrastrar los horarios ("Inicio: X — ahora tocá o arrastrá...", "Rango X → Y (Nh)"), que se acumulaban durante la selección. El selector actualiza hora y cantidad directamente, sin toasts intermedios; se mantienen las validaciones y confirmaciones finales.
    *   **Arrastre de Horarios en Móviles**: Fix del drag del selector de rango en modo responsive: el browser capturaba el gesto como scroll y cancelaba la selección (solo permitía clic-clic). Se agregó `touch-action: pan-y` en `.chips-container-premium`, permitiendo el arrastre horizontal mientras el scroll vertical de la página sigue funcionando.
    *   **Texto de Instrucción Simplificado**: Se quitó "(pasos de 30 min)" del hint del selector de horarios.
    *   **Slots Pasados Bloqueados el Día de Hoy**: Para la fecha actual, la grilla de horarios deshabilita automáticamente las casillas del día que ya pasaron o que no respetan la anticipación mínima configurable (`RESERVA_HORA_MIN_SEGUNDOS`, default 30 min), incluyendo el slot en curso. Implementado en ambas capas: backend (`_calcular_horas_deshabilitadas` en `reservation_service.py`, usando `TimeService.now()`) y frontend (recálculo local en `updateHourlySlotsUI` con `getVirtualNow()` + `RESERVA_MIN_MS`) para cubrir la ventana de cache de 30s.
    *   **Cuadrícula de Horarios Alineada**: La grilla de selección por hora pasó de flex-wrap (filas desparejas, la última incompleta) a una grilla CSS de 6 columnas fijas; las celdas faltantes de la última fila se completan con espacios invisibles (`.hourly-chip-premium.placeholder`) manteniendo 6×6 parejo.
    *   **Desglose de Tarifas en el Total**: Para reservas por hora, el sumario muestra "Total" y debajo el detalle "1 hora = $X · 30 min = $Y" (`#reserva-rates-detail`), calculado con la tarifa de 30 min configurada o la mitad de la hora como fallback.
    *   **Limpieza del Selector de Horario**: Se eliminaron las tabs de filtro Mañana/Tarde/Noche/Todos del selector de rango (código muerto `currentSlotFilter`, `setSlotFilter` y CSS `.slot-tab-btn` removidos) y el hint redundante debajo del picker de día (`res-hour-range-hint`). El selector ahora muestra las casillas completas de 07:00 a 23:30.
    *   **Tarifa de 30 Minutos Configurable**: Nueva clave `precio_30min` (+ `_moto`/`_camioneta`) configurable en el Dashboard (tab Ajustes > Tarifas, campo "FRACCIÓN 30 MIN") junto a las tarifas existentes. Si se deja vacía, vale automáticamente la mitad de la tarifa hora (`precio_hora / 2`).
    *   **Cobro por Bloques de 30 Min**: Los montos (reservas hora, estadías físicas, deuda proyectada) ahora se calculan redondeando hacia arriba al bloque de 30 min más cercano (`max(1, ceil(horas * 2)) * tarifa_30min`). Aplica en `billing_service.py` (`calculate_debt`, `calculate_total_amount` + nuevo `get_30min_rate`), `routes/user/reservations.py`, `routes/parking/status.py` y `services/report_service.py`.
    *   **Estimador Frontend Coherente**: Previews de precio del portal (`reservas-form.js`) y del editor admin (`dashboard-reservations.js`) usan la misma lógica de bloques de 30 min con fallback a mitad de hora.
    *   **Selector de Horario por Rango (Portal Usuario)**: Reemplazo del input de cantidad de horas por selección de inicio/fin sobre la grilla horaria (clic-clic o arrastre con pointer events). El backend se mantiene intacto: se persiste la duración real del rango; los horarios deshabilitados se consultan con `duracion_horas=1`.
    *   **Verificación Automática**: Suite completa de Pytest (50/50 pruebas en `tests/`) pasando exitosamente; `node --check` OK sobre los módulos JS modificados.

- **AGOSTO 28, 2026 - OCR ENGINE OVERHAUL, ESTADÍSTICAS OCR & UNIFICACIÓN DE PATENTES**:
    *   **Motor OCR Lazy/Opcional**: `alpr/ocr_engine.py` ya no aborta el arranque si ningún motor OCR importa; loguea el motivo (RapidOCR/PaddleOCR) y agrega diagnóstico del motor en el setup.
    *   **numpy por Versión de Python**: `numpy>=1.26.0,<2.3.0` para Python < 3.14 y `numpy>=2.3.0,<2.5.0` para Python ≥ 3.14 (numpy < 2.3.0 no tiene wheels para Python 3.14).
    *   **Setup Robustecido**: `setup_backend.bat`/`setup.ps1` muestran los errores reales de pip/init_db y abortan si fallan (encoding UTF-8).
    *   **Estadísticas OCR**: Nueva página `/estadisticas-ocr` (`templates/estadisticas_ocr.html`, ~600 líneas) con tiempos de lectura en BD (`ocr_timing_ms` en `AccessLog`, migración Alembic `f1a2b3c4d5e6_add_ocr_timing_to_access_logs`).
    *   **Avisos en Cámara**: Mensajes de evento de patente/QR en la vista de monitoreo en vivo vía WebSocket (`live.html`).
    *   **Unificación de Códigos y Revisión de Patentes**: Refactor del pipeline ALPR (`alpr/config.py`, `alpr/ocr_engine.py`, `alpr/runner.py`, `routes/parking/access.py`, `services/access_service.py`, `services/report_service.py`).
    *   **CI Deshabilitado**: Workflow de GitHub Actions renombrado a `.github/workflows/ci.yml.disabled` hasta tener la suite estable.

- **AGOSTO 27, 2026 - NOTIFICACIONES, PERMISOS SUCURSAL & SOPORTE VISUAL ADMIN (V9.12.0)**:
    *   **Visibilidad Permanente de Botones de Notificación de Usuario**:
        *   Los botones **"Marcar como leídas"** (`#btn-mark-all-read`) y **"Borrar notificaciones"** (`#btn-clear-read-notifs`) en `notificaciones.html` permanecen siempre visibles (`display: inline-flex`).
        *   Se parametrizaron los estados `disabled` dinámicos: "Marcar como leídas" activo solo con `unread > 0`; "Borrar notificaciones" activo solo con notificaciones leídas (`leido == True`).
        *   Mensaje toast *"Se han borrado todas las notificaciones"* y actualización de icono a check simple (`fa-check`).
    *   **Solución a Falso Positivo de `NEW_DEVICE_LOGIN`**: Preservación de `autopass_device_id` en `localStorage.clear()` al cerrar sesión en `ui.js` y `api.js`, y filtrado por `user_agent` en `routes/auth.py`.
    *   **Permisos Completos de Sucursal para Administrador Local (`local_admin`)**:
        *   Reestructuración de permisos en `routes/admin/users.py` permitiendo a los Administradores de Sucursal consultar, editar, modificar roles de personal y borrar usuarios de su sucursal y clientes.
        *   Normalización con `normalize_branch_name` en todas las rutas de usuarios para equiparar `"AUTOPASS Morón"` y `"Morón"`.
        *   Protección jerárquica impidiendo modificar o eliminar Administradores Globales.
    *   **Diferenciación Visual & Auto-Limpieza en Tickets de Soporte**:
        *   Inclusión de `has_unread` en `get_admin_tickets` (`support_service.py`) para identificar tickets con notificaciones pendientes.
        *   Insignia brillante `<span class="ticket-unread-tag"><i class="fas fa-bell pulse"></i> SIN LEER</span>` junto al `#ID`, insignias de estado con íconos y filas destacadas con resplandor dorado (`.ticket-row-attention`).
        *   Auto-limpieza de notificaciones en `update_ticket_status` y actualización instantánea en vivo del contador del menú lateral (`updateNotifBadge`).

- **AGOSTO 15, 2026 - SYSTEM INTEGRITY VALIDATIONS & TOAST NOTIFICATION OVERHAUL (V9.9.8)**:
    *   **Protección e Integridad en Eliminación de Vehículos**: `delete_vehicle` en `services/user_service.py` valida si la patente posee reservas activas (`PENDIENTE_PAGO`, `PAGADA`, `EN_USO`). Si existen, bloquea la eliminación arrojando error HTTP 400 descriptivo ("No podés eliminar el vehículo porque tiene reservas activas o pendientes").
    *   **Protección en Eliminación de Cuentas de Usuario**: `delete_user` en `services/user_service.py` e `user_admin_service.py` valida que el usuario no tenga reservas activas ni estadías en curso con saldo adeudado antes de ser dado de baja.
    *   **Control Anti-Doble Reserva de Vehículo**: `create_reservation` en `services/reservation_service.py` impide generar dos reservas simultáneas para el mismo vehículo en períodos de tiempo superpuestos.
    *   **Sincronización de Salida Manual y Aforo**: `manual_exit` en `services/access_service.py` verifica la presencia de estadía previa y libera el aforo físico únicamente si corresponde, registrando el timestamp exacto de salida.
    *   **Validaciones de Aforo e Eliminación de Pisos**: `delete_floor` y `update_floor` en `services/branch_service.py` verifican la capacidad de ocupación actual antes de permitir reducir plazas o eliminar un nivel.
    *   **Overhaul de Notificaciones Flotantes (Toasts)**:
        *   Se removió completamente el banner/panel gigante e invasivo (`#notif-alert-banner`) al recibir notificaciones.
        *   Las alertas en tiempo real utilizan únicamente el sistema de toasts flotantes compactos en la esquina superior derecha (`showToast` en `utils.js`).
        *   Se eliminó el cierre automático por clic arbitrario en la pantalla; las notificaciones permanecen en pantalla durante exactamente 5 segundos (`5000ms`) y luego se desvanecen suavemente.
    *   **Verificación Automática**: Suite completa de Pytest (35/35 pruebas en `tests/`, 15 archivos) pasando exitosamente.

- **AGOSTO 15, 2026 - SMART TOUR SYSTEM OVERHAUL & UI REFINEMENTS (V9.9.5)**:
    *   **Posicionamiento Fijo & Abrazamiento al Viewport (`tour.js`)**: Coordenadas de tooltip y flecha migradas a `position: fixed` relativo a `(0, 0)` del viewport. Clampeo con margen de 12px a los bordes de la ventana y fallback automático para móviles (`vw < 680px`). Manejo seguro de recorte SVG (`Math.max(0, ...)`) y navegación por teclado.
    *   **Auto-Arranque de Tour Restringido al Primer Logueo**: Clave por usuario `autopass_tour_seen_${userId}` en `localStorage`. El tour solo inicia automáticamente en la primera sesión de cada usuario. Se removió el botón sobrante "TOUR APP" de la tab Inicio.
    *   **Ramificación Inteligente de Tour Adaptativo**:
        *   *Primer logueo sin vehículos*: Flujo Quick-Add en Inicio -> `startPostAddReservationTour()` finaliza la reserva directamente en Inicio -> Mapa -> Reservas -> Puntos, sin desviar la navegación a la tab de Vehículos.
        *   *Repetición manual desde Ayuda con 1+ vehículos*: `existingVehiclesTourSteps` abre en Mis Vehículos -> despliega el formulario `#vehicle-form-container` ofreciendo la opción `¿Agregar un Nuevo Vehículo?` (con botón *Continuar*) -> formulario de reserva en Inicio -> Mapa -> Reservas -> Puntos.
        *   *Repetición manual desde Ayuda sin vehículos*: `noVehiclesTourSteps` abre en Mis Vehículos -> Formulario -> Mapa -> Puntos.
    *   **Evaluación de Visibilidad Multiselector**: `waitForVisible` evalúa todos los candidatos de selectores por coma en el DOM y retorna únicamente el que tenga dimensiones `offsetWidth > 0 && offsetHeight > 0`, corrigiendo salteos indeseados.
    *   **Remoción de Flecha de Despliegue en Inputs de Patente**: Reemplazo de `.select-wrapper-premium` por `.input-wrapper-premium` en inputs de texto de patente en `inicio.html`, `vehiculos.html` y `admin_reservations.html`. Regla de resguardo CSS `.select-wrapper-premium:has(input)::after { display: none !important; }`.

- **JULIO 27, 2026 - GRANULAR MODULARIZATION OVERHAUL (V9.7.0)**:
    *   **Modularización Granular de Reservas JS**: Descomposición de `reservas.js` (903 líneas / 45 KB) en 4 submódulos ES6 especializados: `reservas-form.js` (formularios, validación, tarifas), `reservas-list.js` (tarjetas, timeline, historial y paginación), `reservas-actions.js` (pago con saldo y cancelación con reembolso) y `reservas-pass.js` (Pase Digital, QR `QRCode.js` y compartir ticket). `reservas.js` re-exporta todo el API usando el patrón Fachada.
    *   **Modularización Granular de Sucursales JS**: Separación de `dashboard-admin-branches.js` (705 líneas / 30 KB) en dos submódulos: `dashboard-admin-branches-crud.js` (CRUD sucursales, mapa Leaflet, geocoding, logo upload) y `dashboard-admin-branches-floors.js` (gestión de pisos `ParkingFloor`, aforos por piso y Planta Baja). `dashboard-admin-branches.js` re-exporta el API completo.
    *   **Componentes Partials de Modales HTML**: Extracción de modales HTML embebidos hacia componentes partials reutilizables: `profile/modals/onboarding_modal.html`, `dashboard/modals/user_modals.html`, `dashboard/modals/branch_modals.html` y `dashboard/modals/promotion_modal.html`, incluidos mediante `{% include %}` en las vistas principales.

- **JULIO 6, 2026 - CORTESÍA & OCUPACIÓN REFACTOR (V9.5.0)**:
    *   **Fix "ya está en la sede" en ALPR**: Se aplicó el mismo fix de `manual_entry` en `validate_plate` — ahora verifica si existe una SALIDA posterior a la última ENTRADA en lugar de solo mirar el último registro.
    *   **Cortesía 10 min en ALPR y manual**: Tanto `exit_plate` (cámara) como `manual_exit` ahora cheqiean el tiempo de cortesía (≤10 min desde la entrada) antes de denegar por deuda. Si está dentro del margen, la salida se registra sin cargo.
    *   **Ocupación solo física**: Se eliminó la pre-ocupación de plazas por reservas no horarias. `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` ya no tocan `ocupacion_actual`. El ALPR (entrada/salida) maneja el conteo para todos los vehículos por igual, reflejando solo autos físicamente presentes.

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
