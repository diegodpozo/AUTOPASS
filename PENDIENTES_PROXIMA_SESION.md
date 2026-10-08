# PENDIENTES_PROXIMA_SESION.md

Recordatorio de trabajo pendiente para continuar en una próxima sesión.
Última actualización: 08/10/2026

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

## Pendiente H6 (datos Neon) — requiere decisión del usuario

1. **Reservas huérfanas** `id` 79 y 84 (sin usuario/vehículo): decidir si vincular o eliminar.
2. **62 reservas pagadas sin `fecha_pago`**: completar `fecha_pago` (usar `fecha_inicio`/`updated_at`?)
   en `reservations`.
3. **211 access_logs pagados (`pago_confirmado`) con `costo_estadia = 0`**: son de "pago interno"
   (metodo `SALDO`?) y rompen métricas. Decidir si dejar 0 o recalcular con tarifario.
4. **25 pagos MercadoPago PENDIENTE viejos**: decidir si cancelar/limpiar.
5. **IPs duplicadas** en 4 de las cámaras (misma IP en varias cámaras): corregir IPs en `parking_cameras`.

## Pendiente config / tarifas

- **Central no tiene tarifario** (0 settings de precio) → no puede cobrar (409). Decidir si cargar
  tarifas de Central (seguía bloqueada a propósito).
- **`precio_quincena_camioneta` no existe en ninguna sede** (solo global): cobrar "quincena" a una
  camioneta en sede da error. Se agregaron las 5 tarifas de camioneta a Santos Dumont copiadas de
  Castelar (30min/hora/dia/semana/mes). Falta decidir quincena si la modalidad es usable.

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
  **Fases 2–3 (R5–R10) pendientes:** scoping de `patente_lookup`/`redemptions`, auth en
  `camera-reading`, rol en WS occupancy, `mark_ticket_notifications_read`, normalización de
  comparaciones de sucursal (`get_capture`, cámaras, payment_history).
- **5 archivos de test cuelgan por puerto serial real (Arduino)** en esta máquina:
  `test_access_service.py`, `test_access_flow.py`, `test_reservation_spots.py`,
  `test_alpr_node_auth.py`, `test_bugfixes_funcionales.py`. `HardwareService.send_serial_command`
  hace `conn.write()` bloqueante si hay un COM presente pero sin dispositivo respondiendo.
  Correr el resto del suite con:
  `pytest --ignore=tests/test_access_service.py --ignore=tests/test_access_flow.py --ignore=tests/test_reservation_spots.py --ignore=tests/test_alpr_node_auth.py --ignore=tests/test_bugfixes_funcionales.py`
  Fix candidato: mockear/desactivar serial en tests (o guardar `SERIAL_ENABLED=False` solo en tests).

## Notas operación

- Última versión local = remoto = `e637bd4` (128 docs: auditorías validaciones + RBAC).
  Working tree limpio.
- Auditorías en `Info proyecto/`: `AUDITORIAS.md` (A1–A9), `AUDITORIA_DB.md`,
  `AUDITORIA_DB_NEON.md`, `AUDITORIA_VALIDACIONES.md` (V1–V12), `AUDITORIA_RBAC.md` (R1–R10).
- Los scripts de migración de Neon se dejaron en `%TEMP%\opencode\*` (migrate_normalize.py,
  migrate2.py, copy_tarifas.py, collision_check.py). Recrearlos si se necesitan.
- Regla AGENTS: no commitear/pushear sin pedido expreso. Antes de `git pull`, revisar si hay
  cambios de BD (`*.db`) en el remoto; si el schema NO cambió, preservar BD local.