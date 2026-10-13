# PENDIENTES_PROXIMA_SESION.md

Recordatorio de trabajo pendiente para continuar en una próxima sesión.
Última actualización: 13/10/2026

## Configuración de Monitoreo (cards + modales de cámara/nivel) — APLICADO 13/10/2026 (LOCAL, SIN COMMITEAR)

- Cards de cámaras (`static/js/modules/dashboard-cameras.js` + `dashboard-settings.css`): se quitó el
  handle de arrastre (`.camera-drag-handle`, los "6 puntitos" `fa-grip-vertical`). El reordenar sigue
  andando porque `enableDragSort` no usa `handleSelector`: la card entera es `draggable`.
- Modales de cámara (`#modal-camera-config`; sirve alta y edición) y nivel (`#modal-add-floor`), cambios scopeados en CSS:
  - Inputs 25% más angostos y centrados: `#form-camera-config .input-with-icon { width: 75%; margin: 0 auto; }`.
  - Select TIPO/Sucursal sin el fondo azul: se eliminó la regla `#camera-tipo, #camera-sucursal { background:#111424; color:#fff; }`; ahora usan el `.select-premium` estándar (igual que los otros inputs).
  - Barra de acciones sin fondo gris: `#modal-camera-config .modal-actions-sticky { background: transparent; border-color: transparent; box-shadow: none; backdrop-filter: none; -webkit-backdrop-filter: none; }`.
  - Botón submit: **GUARDAR** en alta y **ACTUALIZAR** en edición (default del HTML = GUARDAR; el label lo setean `showCreateCameraModal`/`showEditCameraModal`).
  - Shell de los modales de Cámara **y** Nivel igualado al modal `#modal-new-reservation` (crear nueva reserva del dashboard): `.modal-content` sin padding/fondo + `.modern-reservation-card` + header `.card-header-premium` full-width con `header-icon` + `header-text` + `modal-close-top modal-close-top--inline`, y cuerpo `.reservation-form-body-premium`. CSS en `dashboard-settings.css`: `#modal-add-floor .modal-content, #modal-camera-config .modal-content { max-width: 700px; padding: 0; background: transparent; border: none; }`. Nota: `.modern-reservation-card` / `.card-header-premium` (gradiente oscuro) y `.reservation-form-body-premium` se resuelven desde `profile-reservations.css`, que el dashboard carga vía `components/css_profile.html`.
- Manual `manual/admin-sucursal.html` actualizado ("GUARDAR" / "ACTUALIZAR").
- Verificación: suite **845 passed**, `node --check` OK, guards 7/8 verdes. `check_color_equivalence.py`
  marca `dashboard-settings.css` como cambio de color **INTENCIONAL** (pasa con `--allow`).
- **PENDIENTE**: `git commit` + `git push`; **subir `static/sw.js` a `v5`** (cambiaron JS/CSS/template);
  al commitear, registrar `static/css/pages/dashboard/dashboard-settings.css` en
  `_tools/color_equivalence_allowlist.json` (commit + motivo) para la validación `--against HEAD~1`.
  Falta verificación **runtime** del modal y las cards en navegador.

## Facturación escalonada 30 min / hora — APLICADO 13/10/2026 (LOCAL, SIN COMMITEAR)

- Pedido del usuario: unificar el cobro de **estadías sin reserva y reservas por hora** (incluido
  el **tiempo extra** al vencer una reserva) con una regla que **alterne tarifa hora y fracción de
  30 min**. Fórmula: `n = ceil(minutos / 30)` (mínimo 1); `n == 1` → **fracción**; `n >= 2` →
  `(n // 2) * hora + ((n - 1) // 2) * fraccion`. Aplica a **todas las sucursales**, con las tarifas
  que cada sede tenga configuradas (`precio_hora`/`precio_30min` + `_moto`/`_camioneta`); criterio
  estricto por sede (sin tarifa propia no hay precio; no hereda la global).
- Backend (helper único, DRY):
  - `services/billing_service.py`: `hourly_amount_from_rates(duration_hours, hora, fraccion)` (pura)
    y `calculate_hourly_amount(db, duration_hours, sucursal, tipo_vehiculo)`; fallbacks
    `fracción = hora/2` / `hora = fracción*2`; sin ninguna → `None`. `calculate_debt` y
    `calculate_total_amount` (término `hora`) usan el helper.
  - `services/reservation_service.py`: alta y edición de usuario usan `calculate_hourly_amount`
    (se quitaron las 2 fórmulas inline de bloques).
  - `services/report_service.py` (deuda proyectada) y `services/occupancy_service.py` (mapa en vivo)
    usan el helper; se eliminaron sus cálculos locales y `import math`.
- Frontend: `static/js/modules/utils.js` → `computeHourlyAmount(durationHours, hora, fraccion)`;
  consumido por `reservas-form-price.js` (portal) y `reservations-admin-form.js` (admin).
- Verificación: suite **845 passed** (antes 837), guards de `_tools/` **8/8**, `py_compile` OK.
- **PENDIENTE**:
  1. `git commit` + `git push` (aún local, no commiteado; el usuario no lo pidió todavía).
  2. **`static/sw.js`: subir `CACHE_NAME`/`SHELL_CACHE` de `v4` a `v5`** al commitear (cambiaron
     `utils.js`, `reservas-form-price.js` y `reservations-admin-form.js`, los tres en el precache).
  3. Verificación en runtime (navegador) del precio mostrado en el form de reserva (portal y admin).
- Documentación actualizada (13/10/2026): `Info proyecto/HISTORIAL.md`, `Info proyecto/FUNCIONALIDADES.html`,
  `Info proyecto/CONTEXTO_SISTEMA.md`, `Info proyecto/ESTADO_PROYECTO.md`,
  `Diseno_Proyecto/02_Elaboration/01_Requisitos_Funcionales.md` y `manual/admin-sucursal.html`.

## Integración de `origin/main` (refactor sucursal_id) — HECHO 13/10/2026

- Merge de `origin/main` (`df7003c`, `cebae20`) sobre `v9.34.89` (`f4c44ce`) → merge commit
  `54765f5`. Único conflicto real: este doc (resuelto conservando ambas secciones). Los otros 4
  archivos auto-mergearon; ajuste manual en `routes/system/cameras.py` (el reorden de cámaras
  pasó a usar `misma_sucursal`, alineado con el refactor por id).
- **Alembic**: el merge dejó 2 heads (`b8f1c2d3e4a5` orden + `e1f2a3b4c5d6` sucursal_id). Se
  agregó la migración de merge `c4d5e6f7a8b9` (`5f728f7`) → head único.
- **Neon**: sellada con `alembic stamp c4d5e6f7a8b9` (la columna `parking_cameras.orden` ya
  existía; no se corrió B8 para no duplicarla). `alembic current` = head.
- `static/sw.js`: `CACHE_NAME`/`SHELL_CACHE` subidos a `v4` (se agregaron `action-menu.css`,
  `drag-sort.js`, `action-menu.js`, `operator-alerts.js` al precache).
- Verificación: guards 8/8 verdes; suite **837 passed**.
- **Pendiente**: verificación en runtime (navegador) del popup ALPR; `git push`.

## Popup de salida impaga (ALPR) — APLICADO 12/10/2026 (COMMITEADO v9.34.89)

- Pedido del usuario: cuando un vehículo intente salir **sin pago** por el **lector de
  patente (ALPR)**, mostrar en el dashboard un popup con: nombre del usuario (o
  "INVITADO" si no está registrado), **foto de la patente**, **monto a pagar** y
  **método de pago**; al cobrar en caja, **abrir la barrera** automáticamente.
  Aclaración del usuario: **solo para ALPR** (el sistema manual de salida ya existe y es
  aparte).
- Decisiones confirmadas por el usuario: disparo **automático** al denegar el ALPR,
  **abrir la barrera** al cobrar, usar la **foto de la ENTRADA** (el sistema no guarda
  foto de salida).
- Backend:
  - `services/notification_service.py`: store de salidas impagas
    (`set/get/clear_pending_exit`, TTL 120 s) + `notify_pending_exit` que emite el evento
    WS `PENDING_EXIT`. Refactor DRY: se extrajo `_dispatch(coro_builder)` reutilizado por
    `notify_occupancy_change` y `notify_pending_exit` (mismo scheduling por
    `run_coroutine_threadsafe` sobre el loop de Uvicorn).
  - `routes/parking/status.py`: `OccupancyManager.broadcast_event(sucursal_norm, event)`
    (manda un evento puntual a la sede + GLOBAL, sin recalcular aforo).
  - `services/access_service.py`: al denegar la salida por deuda (>10 min) se llama
    `_emit_pending_exit(...)` con `{patente, log_id (entrada), deuda, usuario,
    es_registrado, tipo_vehiculo, sucursal, gate_id}`.
  - `services/billing_service.py`: `preview_pending_amount(db, log)` (read-only, espeja
    el monto de `process_payment`: `calculate_debt` o `monto_total` de reserva + extra).
- Frontend:
  - `templates/dashboard.html`: modal `#modal-pending-exit` (reusa `capture-audit-grid`,
    `glass-premium`, `select-premium`), botones "COBRAR Y ABRIR BARRERA" y cerrar.
  - `static/js/modules/dashboard-operations.js`: `openPendingExitPopup(data)`,
    `confirmPendingExit()` (POST `/access/pay-stay` → POST `/admin/manual-exit` que
    registra la salida y dispara la barrera), `closePendingExitPopup()`.
  - `static/js/modules/dashboard-stats.js`: en `initOccupancyWS`, si llega
    `data.type === 'PENDING_EXIT'` llama `window.openPendingExitPopup(data.data)`.
  - `static/js/dashboard.js`: bindings `window.openPendingExitPopup/confirmPendingExit/
    closePendingExitPopup`.
- Verificación: `node --check` OK (3 módulos), 8 guards en verde, suite **822 passed**
  (813 + 9 tests nuevos en `test_access_flow.py`, `test_notifications.py`,
  `test_status_ws.py`).
- **PENDIENTE**: verificación en runtime real (navegador) del popup end-to-end con el
  nodo ALPR. Commit local hecho en `f4c44ce` (`v9.34.89`, integrado con el refactor de
  `origin/main`).

## Refactor "sucursal por id" — APLICADO, PUSHEADO (`df7003c`) y Neon ALINEADA (12/10/2026)

- **Objetivo cumplido**: TODA referencia a sede en las tablas dependientes se guarda por
  `sucursal_id`; el nombre vive SOLO en `parking_branches`. Se eliminó `propagate_rename`
  (`repositories/branch_repository.py`, `services/branch_service.py`): renombrar una sede ya
  no toca ninguna otra tabla.
- **Traductor central** (`models/branch_ref.py`, nuevo): hybrid `branch_ref_property(default)`
  expone el nombre para display y permite seguir haciendo `Modelo.sucursal == x` (se traduce a
  un subselect sobre `parking_branches`); el setter posterga la traducción y un `before_flush`
  resuelve nombre→id una sola vez por flush, **por nombre normalizado** (ignora prefijo
  `AUTOPASS `, mayúsculas y acentos → "AUTOPASS Centro" y "Centro" apuntan a la misma sede).
  Nombre inexistente → `sucursal_id = NULL`; queda un fallback en memoria
  (`_sucursal_fallback`) para display/comparación dentro de la misma sesión.
- **Modelos** (9) sin columnas de nombre, con `branch = relationship("ParkingBranch", lazy="joined")`:
  `parking_aforo`, `settings`, `parking_cameras`, `promotions`, `reservations`, `access_logs`,
  `support_tickets`, `support_ticket_messages`, `users`. Eliminado `models/branch_id_sync.py`.
  `_sucursal_predicate` estricto (`false()` si la sede no existe) en `settings_repository` y
  `promotion_repository`; serialización API por `response_model` (`routes/admin/users.py`).
- **Migraciones nuevas** (aplicadas a Neon el 12/10/2026):
  `d1e2f3a4b5c6_add_sucursal_id_dependencias`, `f5a6b7c8d9e0_add_sucursal_id_tablas_config`,
  `c3d4e5f6a7b8_drop_sucursal_nombre_columns` (dropea las 9 columnas de nombre + índices/FKs por
  nombre; recrea `ix_access_logs_pat_tipo_suc_fecha` y `uq_settings_clave_sucursal` sobre
  `sucursal_id`) y `e1f2a3b4c5d6_merge_sucursal_id_chain_y_drop_legacy_` (merge de la cadena con la
  de MarianoJAC). Backfill 100% verificado; head único; `test_schema_parity_p2` verde.
- **Merge de `origin/main`** (12 commits, `8253ddc` → `8230f4c`): conflictos resueltos en
  `services/support_service.py` (`_can_access_ticket` id-first + se conservó
  `mark_ticket_notifications_read` de Mariano) y en este doc; revisados los archivos
  auto-mergeados (reservation/promotion repositories, users, tests).
- **Suite completa: 822 passed, 0 fallos** (los 5 archivos que antes colgaban por serial ya no
  se excluyen; `tests/conftest.py` setea `SERIAL_ENABLED=False`). Fixtures sembradas con
  `ParkingBranch` donde faltaba (reservas, ocupación, pagos, bugfixes, notificaciones,
  promociones, settings, users, cámaras, health, soporte). Nota operación: `git stash@{0}`
  (refactor WIP pre-merge) quedó retenido tras el `pop`; se puede dropear.

### Estado (cerrado 12/10/2026)
1. **Neon ALINEADA 12/10/2026** (autorizado por el usuario):
   - **Backups ELIMINADOS 12/10/2026**: las 11 tablas `backup_refactor_id_*` (9 tablas + `branches`
     + `alembic`, ~13210 filas) fueron **dropeadas** en Neon tras verificar el refactor (backfill
     100%, head único, suite 822 passed y pruebas de movimientos OK). Ningún código las referenciaba.
   - **Backfill**: 34 filas insertadas tras F1/F4 quedaron sin `sucursal_id` (14 `access_logs`
     'Castelar', 20 `redemption_tickets` 'Morón') → se completaron con el id derivado del nombre
     normalizado. Los 66 `support_tickets` 'General' quedan `sucursal_id NULL` (tickets globales,
     centinela del hybrid `default="General"`), igual que users/settings/promotions/aforo globales.
   - `alembic_version` pasó de `b8f1c2d3e4a5` (fantasma) a marcado doble `{f5a6b7c8d9e0,
     f9a8b7c6d5e4}` (ambas ramas aplicadas) y `upgrade head` corrió `c3d4e5f6a7b8` + `e1f2a3b4c5d6`.
   - Resultado: head único `e1f2a3b4c5d6`; las 9 columnas de NOMBRE eliminadas; `sucursal_id`
     presente con FK por id en las 9 tablas; 0 huérfanos (`NOT EXISTS` a `parking_branches`);
     `ix_access_logs_pat_tipo_suc_fecha` recreado sobre `sucursal_id` y `uq_settings_clave_sucursal`
     sobre `COALESCE(sucursal_id,-1)`; conteos intactos (12298 logs, 175 reservas, etc.).
     Así el `alembic upgrade head` ya NO falla (antes: `Can't locate revision 'b8f1c2d3e4a5'`).
   - Nota: `parking_cameras.orden` sigue en Neon pero no está en el modelo (columna legacy previa;
     SQLAlchemy la ignora — no es parte del refactor).
2. **Commit/push** del refactor: **HECHO** en `df7003c` ("NORMALIZACION DE BASE CON ID PARA NOMBRES DE SUCURSALES").
3. **Todos los backups `backup*` de Neon ELIMINADOS 12/10/2026** (15 tablas: `backup_refactor_id_*`
   ×11, `backup_users`, `backup_vehicles`, `backup_reservations`, `backup_access_logs`,
   `backup_parking_cameras`, `backup_support_tickets`, `backup_fechas_pre_ts`,
   `backup_f9_support_reply`, `backup_h6_*` ×5, `backup_sucursal_id_legacy`). Verificado: ningún
   código/dato las referenciaba (solo este doc) y el refactor quedó verificado (backfill 100% +
   suite 822 passed + pruebas de movimientos OK).

## Paginador de reservas admin — APLICADO Y PUSHEADO en v9.34.87 (`28b5045`, 11/10/2026)

- Pedido del usuario: en "REGISTRO DE RESERVAS" (dashboard admin) reemplazar el toggle
  "Ver todas las reservas (N)" por una **barra navegadora de 10 por página**.
- Helper DRY nuevo `renderPaginatedList(container, itemsHtml, cfg)` + `resetPaginatedState` en
  `static/js/modules/list-pagination.js` (convive con `renderCappedList`): estado por `container.id`,
  `window.__pageGoto(id,page)`, `onPage` para re-render sin resetear, y `fillRow` (opcional) para
  rellenar la última página con filas vacías y mantener la altura. **Reutiliza el componente de
  paginación del proyecto** (`.pagination-premium` + botones `btn--icon sm` con chevrons + etiqueta
  `text-small text-muted font-bold` "Página X de Y", igual que users.html/finance.html/live).
- `reservations-admin-list.js`: render extraído a `renderAdminReservationRows()` (cap 10, navContainer
  `#admin-res-pager`, `fillRow: '<tr class="row-filler" ...>'`); **búsqueda re-integrada**
  (`onAdminResSearch`) para que filtre el dataset completo y re-pagine (antes `filterTable` solo veía
  las filas en DOM → con paginado habría buscado solo la página).
  Nuevo contenedor `#admin-res-pager` (`class="pagination-premium flex-row items-center justify-center
  gap-20 py-20"`) en `admin_reservations.html`; input onkeyup → `onAdminResSearch`.
  Facade `dashboard-reservations.js` y binding en `dashboard.js` (`window.onAdminResSearch`).
- **Fix "la card se agranda al paginar"** (lo reportó el usuario): la card cambiaba de alto porque
  (a) las filas variaban 73/86px según contenido condicional (línea de reembolso o "EN PREDIO"),
  (b) el `thead` pasaba de 1 a 2 líneas (40/55px) porque `table-layout:auto` redistribuye columnas
  según el contenido de cada página y "ESTADO PAGO"/"ESTADO RESERVA" se partían, y (c) algunas filas
  con nota de reembolso larga llegaban a 101px (wrap en la celda "Monto"). Solución en
  `static/css/pages/dashboard/dashboard-tables.css` (solo `@media (min-width: 1025px)`; en ≤1024px la
  tabla es card-layout y no aplica): altura de fila uniforme `td { height: 106px; vertical-align: middle }`
  (cubre el peor caso de 2 líneas), `thead th { white-space: nowrap }`, y filas de relleno
  `tr.row-filler td { height: 106px; border-bottom: none; pointer-events: none }` para la última página.
  Además `renderPaginatedList` soporta `fillRow` (solo con >1 página).
- Verificación runtime (Edge headless CDP, 175 reservas): **pager top = 1479 px en las 18 páginas**
  (antes variaba hasta ~80px), card idéntica (1329px) en todas; filas 106px uniformes; última página 5
  reales + 5 relleno (border suprimido, `borderBottomStyle: none`); búsqueda "AE114RA" → 4 páginas,
  "Teresa" → 2 páginas (sin relleno en página full), sin resultados → estado vacío sin pager.
  Guards 8/8 sin `--update`/`--allow` (color_equivalence exacto 0/255), suite **813 passed**.
- **COMMITEADO y PUSHEADO en v9.34.87 (`28b5045`, 11/10/2026)**: mensaje `v9.34.87: paginador de 10
  por pagina en registro de reservas admin (estilo del proyecto) y altura de card estable`.

## Follow-ups post v9.34.85 — APLICADO y PUSHEADO 11/10/2026 (v9.34.86, `8b04563`)

- **Fix tests serial-colgados**: nuevo `tests/conftest.py` setea `settings.SERIAL_ENABLED = False`
  a nivel import (evita `serial.Serial.write()` bloqueante si hay un COM sin dispositivo). No había
  conftest antes. Suite completa **813 passed** sin `--ignore` (antes había que excluir 5 archivos).
- **B7**: removidas llamadas espurias `NotificationService.notify_occupancy_change(db)` en
  `routes/user/support.py` y `routes/admin/support.py` (+ imports sin uso).
- **B8**: eliminadas columnas legacy `respuesta`/`user_response` de `models/support.py`; helper
  `SupportService._build_message(...)` reemplaza el doble-escritura/lectura; campos removidos de las
  respuestas de API (user/admin); `schemas/support.py` mantiene `respuesta` como input.
  Migración nueva `alembic/versions/f9a8b7c6d5e4_drop_legacy_support_reply_fields.py` (down_revision
  `b2f4e8c1a9d7`) — **APLICADA a Neon el 11/10/2026**: se dropearon `support_tickets.respuesta` y
  `support_tickets.user_response` (backup `backup_f9_support_reply`, 86 filas) y se selló
  `alembic_version` en `f9a8b7c6d5e4` (head) con `alembic stamp --purge head` (el stamp viejo
  `f5a6b7c8d9e0` no existía en la cadena, por eso el purge). Verificado: `alembic current` = head,
  ORM `SupportTicket` sin las columnas, `support_ticket_messages` intacta (138 filas).
- **Escalabilidad → notificaciones y promociones** (ver sección v9.34.85 abajo): helper extendido con
  `wrapperClass`; `notifications-render.js` cap 8; `dashboard-promotions.js` cap 8 con
  `renderPromotionsTable()` para el `onToggle`. Bug detectado y corregido en runtime: sin `onToggle`
  el botón cambiaba el estado pero no re-renderizaba (no expandía).
- Verificación runtime (Edge headless CDP, server :8000): notificaciones 8 → "Ver todas las
  notificaciones (10)" → 10 → 8 (filtro reagrupa); promociones admin 8 → "Ver todas las promociones
  (12)" → 12 → 8. Guards 8/8 verdes (sin CSS nuevo). Suite completa **813 passed**.
- **COMMITEADO y PUSHEADO en v9.34.86 (`8b04563`, 11/10/2026)** (13 archivos, +173/−82).

## Comunicación de Soporte (usuario ↔ soporte) — APLICADO y PUSHEADO en v9.34.85 (`acafbd2`, 10/10/2026)

Auditoría de la cadena ticket/notificación + frontend de Ayuda. Hallazgos A1–A10
reportados; el usuario eligió **A1–A6** (B7/B8/B9/B10 NO se tocaron).

- **A1**: listado "MIS CONSULTAS / TICKETS" para el cliente (`loadMyTickets` en
  `profile-help.js`, `GET /user/support-tickets`, carga on-demand vía `showSection('ayuda')`,
  refresh tras crear/responder).
- **A2**: XSS cerrado en el chat del usuario (`escapeHtml` en `renderTicketMessages`).
- **A3**: `is_admin` incluye `staff` (`support_service.py`).
- **A4**: estado "En Revisión" integrado (filtro/admin select/KPIs; `reply_to_ticket` lo setea).
- **A5**: tickets terminales (resuelto/resuelta/cerrado/cancelado) bloqueados para responder
  (backend `TERMINAL_STATES` + frontend en dashboard y perfil).
- **A6**: `get_admin_pending_count` excluye los terminales.
- **Rediseño de la pantalla Ayuda y Soporte** (pedido por el usuario al ver el listado
  desacomodado): "MIS CONSULTAS" salió del grid 2 col de contacto y quedó full-width debajo;
  `.my-ticket-subject` con `-webkit-line-clamp:2`; modal con pill de estado
  (`#modal-ticket-state`), asunto con `overflow-wrap`, burbujas con `overflow-wrap:anywhere`.
- Verificación runtime en Edge headless (CDP): grid 2 col con alturas iguales (h=134),
  subjects clamp 2 líneas sin overflow horizontal, gap wrapper→MIS CONSULTAS 40px, pill
  "En Revisión" visible en modal, palabra larga (360 chars AEIOU) sin overflow en la burbuja,
  asunto largo envuelto dentro del card. Suite soporte **47 passed**; **8/8 guards** OK
  (design system re-baselineado `--update` + `check_color_equivalence --allow profile-help.css`,
  mecanismo documentado de aceptación).
- **Escalabilidad de listados (volumen)** — patron DRY reutilizable: helper
  `static/js/modules/list-pagination.js` (`renderCappedList(container, itemsHtml, cfg)` con
  `pageSize/tag/colspan/toggleClass/toggleAll/toggleLess/emptyHtml/onToggle`, estado por
  `container.id`, `window.__capToggleList(id)` para el onclick inline + `resetCappedState(container)`);
  CSS global `.cap-toggle-grid`/`.cap-toggle-btn` en `utilities.css`. Aplicado a:
  - **MIS CONSULTAS (usuario)**: cap 6 + "Ver todas las consultas (N)"/"Ver menos" + pills de
    estado (Todas/Pendientes/En revisión/En proceso/Resueltas/Cerradas) + chip `(N)`.
  - **Soporte admin** (`dashboard-tickets.js`): cap 8 (`drag` tabla).
  - **Reservas admin** (`reservations-admin-list.js`): cap 8.
   - **Vouchers usuario** (`profile.js`, tab Mis Puntos): cap 6 + "Ver todos (N)" (`.voucher-toggle`).
   - **Notificaciones** (`notifications-render.js`): cap 8 + "Ver todas las notificaciones (N)"
     (`.notif-list`, vía la opción nueva `wrapperClass` del helper); reset al recargar y al cambiar filtro.
   - **Promociones admin** (`dashboard-promotions.js`): cap 8 + "Ver todas las promociones (N)"
     (`renderPromotionsTable()` extraído para el `onToggle`).
   - `profile.js` historial de pagos solo alimenta un contador (`acc-stat-stays`), no es lista → descartado.
  Verificación runtime (Edge headless CDP, usuario + 12 tickets + 10 vouchers canjeados por API):
  my-tickets 6 → 12 → 6, filtro en_revision 2; vouchers 6 → 10 → 6; admin tickets 8(+header) →
  67/66; reservas admin 8(+header) de 175. Suite soporte 47 passed; guards 8/8 (design system
  re-baselineado `--update` + `check_color_equivalence --allow profile-help.css --allow utilities.css
  --allow profile-points.css`).
- **APLICADO y PUSHEADO en v9.34.85 (`acafbd2`, 10/10/2026)**: 19 archivos (+605/−39) incluyendo
  el nuevo `static/js/modules/list-pagination.js`. La extensión a notificaciones/promociones y la
  limpieza B7/B8 se hicieron en la tanda siguiente (v9.34.86, ver sección superior).

## F1 de AUDITORIA_VALIDACIONES — APLICADO y PUSHEADO en v9.34.82 (`0f35417`, 10/10/2026)

- **V1**: `UserService.create_user` valida `get_active_by_dni` antes de insertar → 400
  "El DNI ya está registrado por otro usuario."; `routes/auth.py` captura `IntegrityError`
  como red (rollback + 400). Test `test_register_dni_duplicado_400`.
- **V2**: helper DRY `_save_branch_logo` en `routes/admin/branches.py` (extensión
  whitelist png/jpg/jpeg/webp, máx 2 MB leído en chunks de 64KB, aborta sin escribir más;
  makedirs del dir; en update, el logo nuevo se guarda antes de borrar el viejo).
  Se quitó `import shutil` (quedó huérfano). Test `test_create_branch_logo_extension_invalida_400`.
- **V5**: `PromotionCreate` en `schemas/user.py`: `costo_puntos = Field(..., gt=0)` y
  `valor_descuento = Field(default=None, ge=1, le=100)`. Tests de 422 en
  `test_admin_promotions.py`.

## F2 de AUDITORIA_VALIDACIONES — APLICADO Y PUSHEADO en `16ef01e` (10/10/2026)

- **V4-whitelist**: `ALLOWED_SETTINGS_KEYS` en `routes/admin/settings.py` (18 tarifas
  `precio_*` × Auto/Moto/Camioneta + 7 claves `capacidad_*`); `update_price` rechaza claves
  fuera de la lista con 400 "Clave de configuración no permitida". Tests de
  `test_admin_settings.py` migrados a claves canónicas + `test_update_price_clave_no_permitida_400`.
- **V6**: `UserService.add_vehicle` acepta patentes Mercosur BR/UY/PY (BR viejo `ABC1234`,
  BR Mercosur `ABC1D23`, UY `AB123CD`, PY `1234ABC`) además de AR (viejo, Mercosur y moto).
  Tests parametrizados en `test_user_service.py`. **Decisión del usuario**: alinear backend
  al frontend (aceptar), sin tocar front.
- **V7**: `VehicleCreate(BaseModel)` en `schemas/parking.py` con `tipo: Literal["Auto",
  "Moto", "Camioneta"] = "Auto"` (exportado en `schemas/__init__.py`); `POST /v1/user/vehicles`
  recibe body JSON (`data: VehicleCreate` por import directo para que openapi resuelva);
  `vehicles.js:181` envía `{ patente, marca_modelo, tipo }`. Tests de firma actualizados
  (`test_new_validations.py`, `test_notifications.py`).
- **V8**: `reply_to_support_ticket` lee el adjunto en chunks de 64 KB y aborta a 1 MB sin
  escribir a disco; el borrado del parcial se hace fuera del `with open()` (evita
  `PermissionError` WinError 32 en Windows). Se quitó `import shutil`.
- **V9**: `disabled-dates`: `dias = Query(90, ge=1, le=365)`; `disabled-hours`:
  `duracion_horas = Query(1.0, gt=0, le=24)`, `paso_minutos = Query(30, ge=5, le=120)`,
  `exclude_id = Query(None, ge=1)`.
- **V11**: `create_admin_reservation` valida `fecha_inicio < fecha_fin` (400) y solapamiento
  de la misma patente en la sede (`get_overlap_by_patente` → 400). `update_admin_reservation`
  replica el chequeo excluyendo la propia reserva (`exclude_id` agregado al repositorio).
  Setup del test `test_edit_excluye_propia_reserva_de_disponibilidad` ajustado a patentes
  distintas (r1 `ABC123`, r2 `ZZZ999`) porque ahora el doble-book de una misma patente se rechaza.
- Verificado: suite completa **732 passed** (excluidos los 5 serial-hanging) + **8/8 guards** OK.
- **AUDITORIA_VALIDACIONES F1/F2/F3 CERRADA al 100% (10/10/2026):** F2.5 (V10) y F3.1 (V12)
  verificados como ya cubiertos (validators DNI 7-8 + formato email vía `@field_validator`, y
  CheckConstraints en modelos + Neon). Sin trabajo pendiente de esta auditoría.

## UX del portal — APLICADO y COMMITEADO/PUSHEADO en v9.34.81 (`09955fe`, 10/10/2026)

- Stepper sticky (header sticky ≥769, rail vertical ≥1281 con sync de altura vía
  ResizeObserver en `reservas-form.js`, `scroll-padding-top` en `.main-content-scroll`).
- Hamburguesa móvil anclada al header (`position:absolute` ≤1024) en vez de flotar.
- Nav inferior `.user-footer-nav` solo en responsive (≤1024, coincidente con drawer).
- Reloj virtual (`.vt-fab` + controles) oculto para clientes (`rol:user` en localStorage);
  se muestra solo a admin/local_admin/staff.

## Puntos 1-4 de mejoras BD — RESUELTOS 08/10/2026 (migraciones `a7f3d9c2e1b8` y `b2f4e8c1a9d7`)

- **1. Fechas varchar → timestamp**: 8 columnas convertidas en Neon
  (`access_logs.fecha_hora/fecha_pago`, `reservations.fecha_inicio/fecha_fin/fecha_pago`,
  `mercadopago_payments.fecha_creacion/fecha_confirmacion`, `points_log.fecha`) con
  `USING NULLIF(col,'')::timestamp`. Backup previo en `backup_fechas_pre_ts` (25.477 filas).
- **2. CheckConstraints**: 11 constraints aplicados (no negatividad de saldo/puntos/montos/aforo/
  costo/settings/costo_puntos; % de descuento 1-100; orden `fecha_fin >= fecha_inicio`). Los
  guards 400 acompañan: `adjust_user_balance` (monto<0), `update_price` (valor<0) y ajuste
  negativo de puntos al editar reserva.
- **3. UNIQUE de settings**: índice `uq_settings_clave_sucursal (clave, COALESCE(sucursal,''))`
  (0 duplicados en 112 filas).
- **4. FKs de sucursal**: 4 constraints aplicadas en Neon (migración `b2f4e8c1a9d7`):
  `fk_parking_aforo_sucursal_branch`, `fk_settings_sucursal_branch`,
  `fk_parking_cameras_sucursal_branch`, `fk_promotions_sucursal_branch` →
  `parking_branches.nombre`, todas con `ON UPDATE CASCADE ON DELETE CASCADE`
  (0 huérfanos verificado antes de aplicar). Modelos actualizados con las mismas FKs.
- **Compatibilidad back/front**: `models/types.py` `DateTimeAsStr` (timestamp en BD, `str`
  `'YYYY-MM-DD HH:MM:SS'` en Python). Helper front `parseFecha` en `utils.js` + `_coerceDate`
  unificado; `TimeService.now_str()` alineado a `%Y-%m-%d %H:%M:%S`. Tests: **718 passed**
  (los 5 archivos que cuelgan por puerto serial siguen excluidos).
- **Puntos 5 y 6 DESCARTADOS por decisión del usuario** (no reabrir salvo pedido):
  5 (`parking_floors` vacía con FK viva) y 6 (94% de `access_logs` son demo). Todos los datos
  son de PRUEBA, proyecto escolar que nunca irá a producción (ver AGENTS.md).

## Completado (no reabrir salvo regresión)

### Unificación de criterios de PATENTES y DNI (commit "UNIFICACION DE CRITERIOS DE PATENTES Y DNI")

- **Patentes**: se guardan SIEMPRE canónicas (mayúsculas, sin espacios, ej. `AE114RA`) en
  `vehicles`, `reservations`, `access_logs.patente_detectada`, `access_logs.normalized_patente`.
  El front muestra con espacios vía `formatPlate`/`format_plate`; el ingreso tolera ambos formatos
  (`normalize_plate` al escribir y al matchear).
- **DNI**: solo dígitos, sin puntos (`normalize_dni`). Registro web (`schemas/user.py`) y OAuth
  (`schemas/auth.py`) aceptan DNI con puntos y lo normalizan. El front muestra sin puntos.
- **Sucursales**: `parking_cameras.sucursal` y `support_tickets.sucursal` quedaron con los nombres
  de branch canónicos (sin prefijo `AUTOPASS `, tildes correctas). Las comparaciones usan
  `normalize_system_name` (quita prefijo, pasa a mayúsculas y quita acentos).
- **tipo_vehiculo**: unificado a `Auto`/`Moto`/`Camioneta` en `access_logs`, `vehicles`,
  `reservations`. `billing_service._tipo_key` y `report_repository` normalizan en comparaciones.
- **Migración Neon aplicada** con backups por tabla (`backup_users`, `backup_vehicles`,
  `backup_reservations`, `backup_access_logs`, `backup_parking_cameras`, `backup_support_tickets`).
  **Backups ELIMINADOS 12/10/2026**: reportes y suite OK → se dropearon estas 6 junto al resto de
  las tablas `backup*` de Neon (ver sección del refactor `sucursal por id`).
- Archivos backend/front/scripts/tests tocados (ver git log del commit). NADA de Arduino,
  firmware (`.ino`), `hardware_service`, MQTT, ALPR pipeline o config de cámaras fue modificado.

## H6 (datos Neon) — RESUELTO 08/10/2026 (los 7 ítems aplicados/decididos)

Backups en Neon `backup_h6_*` (ELIMINADOS 12/10/2026):

1. **RESUELTO**: reservas huérfanas 79 y 84 eliminadas (0 referencias) → `backup_h6_reservaciones`.
2. **RESUELTO**: 62 pagadas sin `fecha_pago` → completadas con `fecha_pago = fecha_inicio`
   → `backup_h6_reservas_sinfp`. NO se borraron porque 90 `access_logs.reserva_id` las referencian.
3. **RESUELTO**: 211 `access_logs` con `pago_confirmado=TRUE` y `costo_estadia` 0/NULL
   **ELIMINADOS** (decisión del usuario) → `backup_h6_logs_costo0`. Verificado antes de borrar:
   única FK hacia `access_logs` = `mercadopago_payments.access_log_id` con 0 referencias a esos 211.
4. **RESUELTO**: 25 MP `PENDIENTE` eliminados (quedan 3 FALLIDO + 9 APROBADO) → `backup_h6_mp_pendientes`.
5. **DESCARTADO POR DISEÑO** (decisión del usuario): las IPs/cámaras "duplicadas" son configuración
   de **PRUEBA** — misma LAN y misma cámara usada cambiando de sede; el sistema está en prueba.
   **No es un problema ni debe tratarse como bug.** Las 7 filas que se habían borrado fueron
   **RESTAURADAS** (5 desde `backup_parking_cameras`, 2 desde `backup_h6_camaras`):
   `parking_cameras` quedó con sus **22 filas originales**.

## Pendiente config / tarifas — RESUELTO 08/10/2026

- **Central**: 15 tarifas `precio_*` copiadas de Castelar (antes 0 → ahora 18 settings con quincena).
- **Quincena por sede**: `precio_quincena` 120000 / `precio_quincena_moto` 60000 /
  `precio_quincena_camioneta` 150000 creadas en las 5 sedes (antes solo globales; `get_rate` es
  estricto por sede → la modalidad quincena daba 409). Verificado: 15 filas quincena por sede.
- La caché de tarifas (`ttl_cache`, 300 s) no cachea misses → los rates nuevos aplican ya.

## Tests / CI (entorno) — RESUELTO 11/10/2026

- **2 tests SI fallaban (pre-existentes, de commits remotos) — YA CORREGIDOS y pusheados en
  `f07494a`**:
  - `tests/test_admin_branches.py::test_list_branches_con_resumen` → `BranchResponse.tarifa_*`
    ahora `Optional[float] = None` (tarifario no configurado = null, no 500).
  - `tests/test_inline_styles_guard.py::test_guard_inline_styles_no_regresiones` → opacidad del
    heatmap vacío movida de `style=inline` a `.heatmap-vacio i` en dashboard-metrics.css.
  - En el mismo commit se dejaron verdes 3 guards CSS que 16d6d3c (MAPA DE CALOR) había roto sin
    actualizar: se borró `.metrica-card-badge.proximamente` (huérfana), se declaró `--hm-cols`
    en variables.css (token sin declarar) y se registró el baseline del design system.
  - Verificado: suite completa `782 passed` (con y sin `--cov`), 8/8 guards en verde.

- **RESUELTO — test flake de Mercado Pago que dependía del entorno**:
  `tests/test_bugfixes_funcionales.py::test_checkout_mercadopago_de_estadia_acepta_patente_en_distinto_formato`
  usaba el `MP_ACCESS_TOKEN` real del `.env` (`settings.MP_ENABLED` = bool(token)), por eso pasaba
  local y daba `503` en un entorno sin ese secreto (git/CI). Fix aplicado (patrón de
  `test_mercadopago.py:71`): `monkeypatch` de `MP_ACCESS_TOKEN`/`BASE_URL` + fake `_mp_request`.
  Verificado pasando con `MP_ACCESS_TOKEN=""` y suite completa `782 passed`.
  **Commiteado y pusheado en `2185ffe`.**

## Auditorías — remediación RESUELTA (VALIDACIONES F1–F3 y RBAC R1–R10)

- **AUDITORIA_VALIDACIONES.md** (commit `e637bd4`): 12 hallazgos V1–V12 aún vigentes en el código.
  Plan F1 (críticos), F2 (simetría), F3 (defensa en profundidad) documentado. **No se tocó código
  todavía** — decidir qué hallazgos corregir.
- **AUDITORIA_RBAC.md**: auditoría de autorización completa, 10 hallazgos (R1–R10).
  **Fase 1 (R1–R4) APLICADA y verificada (2026-10-08):**
  - R1: `GET /v1/admin/branches` ahora exige `get_operational_user` (antes sin auth).
  - R2: detail/PATCH de tickets de soporte ahora con scoping por sucursal
    (`SupportService._can_access_ticket` → 403 cross-sucursal).
  - R3: **DESCARTADO por decisión del usuario** — el reloj virtual es feature de TEST que se
    descartará en producción. Queda en `get_operational_user` (admin/local/staff; clientes 403).
  - R4: `validate_staff_role_assignment` en create/update/role: solo Admin Global asigna
    STAFF/LOCAL_ADMIN; local solo gestiona clientes. Front `dashboard-admin-users.js`
    sincronizado (alta: local solo "Cliente"; edición: rol solo-lecturo).
  **Fase 2 (R5–R7) APLICADA y verificada (2026-10-08):**
  - R5: `patente_lookup` ya no devuelve `email` (el front no lo usa); `admin_rate_limit` en
    lookup + `/redemptions/available`; `get_admin_available_redemptions` valida usuario activo
    → 404. **Scoping por sede DESCARTADO** (vehicles sin sede y clientes no ligados a sede →
    rompería caja multi-sede), decisión documentada en AUDITORIA_RBAC.md F2.1.
  - R6: `POST /camera-reading/{gate_id}` con `require_alpr_node`; `ocr_engine._fire` ahora
    envía `X-Node-Secret`.
  - R7: WS `/parking/ws` exige rol operativo (helper DRY `is_operational_role` en
    `core/security.py`) → 4003 a clientes; fronts `dashboard-stats.js`/`monitoreo-live.js` no
    reintentan ante 4003. El feed incluye `last_event` con patentes en vivo.
  - Verificado: suite **794 passed** + guards en verde.
  **Fase 3 (R8–R10) APLICADA y verificada (2026-10-09):**
  - R8: `mark_ticket_notifications_read` valida jurisdicción reutilizando `_can_access_ticket`
    (403 cross-sucursal); la ruta delega en `SupportService.mark_ticket_notifications_read`.
  - R9/R10: helper DRY `same_branch(a, b)` en `core/normalize.py` (normaliza prefijo `AUTOPASS `,
    mayúsculas y acentos; deniega si la sede es vacía) reemplaza comparaciones literales en
    `get_capture` (`video.py`), promociones (toggle/update/delete) y reservas
    (`get_permissioned_reservation`, update y confirm-payment). `ReportService`/cámaras ya
    normalizaban (`_branch_filter`, `normalize_system_name`) → sin cambios.
  - Verificado: suite **799 passed** (+5 tests nuevos). **TODOS los hallazgos R1–R10 cerrados**
    (R3 descartado por decisión del usuario).
- **RESUELTO (11/10/2026)** — los 5 archivos de test que colgaban por puerto serial real (Arduino) ya
  no cuelgan: `tests/conftest.py` setea `settings.SERIAL_ENABLED = False` a nivel import (evita el
  `conn.write()` bloqueante de `HardwareService.send_serial_command` si hay un COM sin dispositivo).
  Ya no hace falta correr con `--ignore`; suite completa **813 passed** sin exclusiones.

## Notas operación

- Fase 3 RBAC (R8–R10) APLICADA y commiteada el 2026-10-09. Base previa: `cebf799` (Fase 2) +
  pull fast-forward a `8253ddc` (gráficos + validaciones Neon). **Todos los hallazgos R1–R10
  cerrados** (R3 descartado por decisión del usuario).
- **Guards CSS (regresión del pull resuelta, 2026-10-09):** el pull (`8253ddc`/`7c88eb5`)
  había roto `check_css_huerfano.py` (5 clases `hm-leg--t0..t4`, **falso positivo**: las genera
  `dashboard-informes.js` con `` `hm-leg--t${tramos.length}` `` → se agregó el prefijo `hm-leg--t`
  a `RUNTIME_BUILT_PREFIXES`) y `check_css_design_system.py` (literales/spacing nuevos del rediseño
  de gráficos). Fix DRY: `#dfba6b` → `var(--dorado)` en la leyenda; el resto son colores del
  rediseño sin token (`#dc2626`/`#ee9393` = rampa blanco→rojo de `HM_WHITE_TO_RED`, `#6fcf97`/
  `#062a1c` del stepper, `#888`, `#111`) + CSS nuevo legítimo → se aceptó el estado con
  `--update` del baseline. **8/8 guards en verde.**
- Auditorías en `Info proyecto/`: `AUDITORIAS.md` (A1–A9), `AUDITORIA_DB.md`,
  `AUDITORIA_DB_NEON.md`, `AUDITORIA_VALIDACIONES.md` (V1–V12), `AUDITORIA_RBAC.md` (R1–R10).
- Los scripts de migración de Neon se dejaron en `%TEMP%\opencode\*` (migrate_normalize.py,
  migrate2.py, copy_tarifas.py, collision_check.py, migrate_orden.py, migrate_orden2.py,
  cams_final.py, verify_final.py, borrar_logs3.py, find_lost_cams.py, restore_cams.py).
  Recrearlos si se necesitan.
- **Backups de Neon:** al 12/10/2026 **no queda ninguna tabla `backup*`** (todas dropeadas tras
  verificar el refactor y las migraciones; ningún código ni modelo las referenciaba).
- Regla AGENTS: no commitear/pushear sin pedido expreso. Antes de `git pull`, revisar si hay
  cambios de BD (`*.db`) en el remoto; si el schema NO cambió, preservar BD local.