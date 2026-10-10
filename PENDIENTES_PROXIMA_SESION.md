# PENDIENTES_PROXIMA_SESION.md

Recordatorio de trabajo pendiente para continuar en una próxima sesión.
Última actualización: 10/10/2026

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

## F2 de AUDITORIA_VALIDACIONES — APLICADO 10/10/2026 (pendiente de commit/push)

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
- **Restan de la auditoría**: F2.5 (V10) migrar emails a `EmailStr` (los validators DNI 7-8 y
  formato email ya existen), y F3.1 (V12) CheckConstraints — verificar si se considera cerrado
  (ya hay constraints en modelos + Neon según tandas previas). Plan F2/F3 en
  `Info proyecto/AUDITORIA_VALIDACIONES.md`.

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
  Antes de descartar los backups, confirmar que los reportes corren bien.
- Archivos backend/front/scripts/tests tocados (ver git log del commit). NADA de Arduino,
  firmware (`.ino`), `hardware_service`, MQTT, ALPR pipeline o config de cámaras fue modificado.

## H6 (datos Neon) — RESUELTO 08/10/2026 (los 7 ítems aplicados/decididos)

Backups en Neon `backup_h6_*`:

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

## Pendiente tests / CI (entorno)

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

## Pendiente auditorías: implementar remediación

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
- **5 archivos de test cuelgan por puerto serial real (Arduino)** en esta máquina:
  `test_access_service.py`, `test_access_flow.py`, `test_reservation_spots.py`,
  `test_alpr_node_auth.py`, `test_bugfixes_funcionales.py`. `HardwareService.send_serial_command`
  hace `conn.write()` bloqueante si hay un COM presente pero sin dispositivo respondiendo.
  Correr el resto del suite con:
  `pytest --ignore=tests/test_access_service.py --ignore=tests/test_access_flow.py --ignore=tests/test_reservation_spots.py --ignore=tests/test_alpr_node_auth.py --ignore=tests/test_bugfixes_funcionales.py`
  Fix candidato: mockear/desactivar serial en tests (o guardar `SERIAL_ENABLED=False` solo en tests).

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
- Regla AGENTS: no commitear/pushear sin pedido expreso. Antes de `git pull`, revisar si hay
  cambios de BD (`*.db`) en el remoto; si el schema NO cambió, preservar BD local.