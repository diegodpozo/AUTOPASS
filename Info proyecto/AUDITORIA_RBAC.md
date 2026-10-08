# AUDITORÍA DE AUTORIZACIÓN (RBAC e IDOR) — AUTOPASS

**Fecha:** 2026-10-08
**Alcance:** Matriz ruta × rol (auth, admin, user, system, parking, reports), scoping por sucursal, ownership de objetos (IDOR), escalada de privilegios.
**Método:** Revisión estática de `routes/`, `services/`, `core/security.py`, `core/alpr_security.py` contra modelos de rol (`UserRole`: `admin`, `local_admin`, `staff`, `user`).
**Estado:** Auditoría completada. Se detectaron **10 hallazgos** (2 altos, 3 medio-altos, 3 medios, 2 bajos).

---

## 1. Dependencias de Autorización (primitivas)

| Primitiva | Roles admitidos | Ubicación |
|---|---|---|
| `get_current_user` | cualquier rol autenticado, no bloqueado, no `is_deleted` | `core/security.py:78` |
| `get_super_admin` | `admin` (global) | `core/security.py:111` |
| `get_local_manager` | `admin`, `local_admin` | `core/security.py:117` |
| `get_operational_user` | `admin`, `local_admin`, `staff` | `core/security.py:124` |
| `get_operational_user` + rate limit | idem + `admin_rate_limit` / `limiter.limit` | `core/limiter.py` |
| `require_alpr_node` | nodos ALPR (secret en tiempo constante o red local/privada) | `core/alpr_security.py:23` |

Helpers de jurisdicción:
- `validate_local_admin_branch(admin, branch_nombre)` — local_admin solo sobre SU sucursal (normalizada) (`core/security.py:131`).
- `validate_local_admin_user_permission(admin, target_user)` — local_admin NO puede operar sobre `admin`; sobre staff/local_admin de OTRA sucursal; SÍ puede operar sobre cualquier `USER` (`routes/admin/users.py:16`).
- `get_permissioned_reservation(db, staff, res_id)` — staff/local solo sobre reservas de su sede (`services/reservation_service.py:156`).
- Scoping de reportes: `sucursal = user.sucursal if rol != admin` en la mayoría de `ReportService` (líneas 78, 235, 249, 287, 320, 346, 467, 546).

---

## 2. Matriz de Endpoints por Router

Leyenda: **A**=get_super_admin · **M**=get_local_manager · **O**=get_operational_user · **U**=get_current_user · **N**=require_alpr_node · **P**=público · 🔒=scoping sucursal presente.

### auth (`routes/auth.py`) — montado sin prefijo
- POST `/register`, `/login`, `/forgot-password`, `/reset-password`, GET `/oauth/{provider}/authorize|callback`, POST `/oauth/complete` → **P** (flujo de auth, correcto).
- POST `/logout` → **U**.

### views (`routes/views.py`) — **P** (serving de HTML; los datos salen por API con su propia auth). OK.

### admin (`routes/admin/`) — router con prefijo `/v1/admin`

| Ruta | Dep | Scoping | Observación |
|---|---|---|---|
| GET `/branches` | **O** (fix R1) | — | ✅ Corregido: antes sin auth |
| POST `/{branch_id}/floors` · PATCH/DELETE `/floors/{id}` | **M** + rate | `validate_local_admin_branch` 🔒 | OK |
| POST/DELETE/PATCH `/branches*` · POST `/branches/{id}/toggle` | **A** + rate | — | OK |
| POST `/open-barrier` · `/manual-entry` · `/manual-exit` · `/cancel-stay` | **O** + `30/min` | por `staff.sucursal` 🔒 | OK (hardware envía sucursal en details) |
| Promotion CRUD | **M** + rate | local: `sucursal == admin.sucursal` 🔒 | OK |
| GET `/reservations/patente-lookup` | **O** | **sin scope** | [**R5**] expone PII de cualquier usuario |
| GET `/reservations` · POST/PUT/reservas admin, confirm-payment, cancel | **O** + rate | `get_permissioned_reservation` 🔒 | OK |
| GET `/reservations/{id}/redemptions` · `/redemption-info` | **O** | `get_permissioned_reservation` 🔒 | OK |
| GET `/redemptions/available?user_id=` | **O** | **sin scope** | [**R5**] IDOR a canjes de otro user |
| GET `/settings` · POST `/settings/prices` | **M** + rate | por `admin.sucursal` 🔒 | OK (validación de valores pendiente: AUDITORIA_VALIDACIONES V4) |
| Soporte GET/PATCH (list y detail) | **O** | listar sí 🔒, **detail NO** | [**R2**] |
| USERS: list · create · update · role · toggle-block · balance · password · delete | **M** | `validate_local_admin_user_permission` (USER global) | [**R4**] escalada cross-sucursal |
| Virtual time (advance/rewind/set/target/reset) | **O** (operativo) + rate | **GLOBAL** (feature de test) | ✅ Uso de test: admin/local/staff |

### user (`routes/user/`) — prefijo `/v1/user`
- Balance, fidelización, MP, notifications, profile, reservations, support, vehicles → **U** con ownership por `current_user.id` / `get_by_user_and_id` / `get_by_id_and_user`. **OK** (verificado en servicios: `payments.py:112`, `user_notification_service.py:45`, `support_service.py:224`).
- GET `/rates`, MP `/success|pending|failure|webhook` → **P** intencionales.

### system (`routes/system/`) — prefijo `/v1/system`
- Cámaras (CRUD/control/config) → **O** con scoping por sucursal y prefijo de gate 🔒 | OK.
- POST `/camera-reading/{gate_id}` → **NINGUNA** | [**R6**]
- Video WS/frames → token/rol o nodo ALPR 🔒 | OK.
- GET `/capture/{log_id}` → token/bearer + rol staff+, scoping `log.sucursal == staff.sucursal` (comparación exacta) | [**R10**] inconsistencia de comparación.
- GET `/health` **O** · POST `/heartbeat` **N** · POST `/reset` **A** · GET `/virtual-time` **P**. OK.

### parking (`routes/parking/`)
- POST `/access/validate-plate` · `/exit-plate` · `/validate-qr` → **N** | OK.
- POST `/access/pay-stay` → **O** + `10/min` | OK.
- GET `/parking/branches` → **P** | OK (endpoint público con `BranchPublicResponse`).
- GET `/parking/status` · `/current-occupancy` → **O** | OK.
- WS `/parking/ws` → token JWT, **sin validación de rol** | [**R7**] cualquier USER puede recibir el feed de ocupación.

### reports (`routes/reports.py`) — prefijo `/v1/reports`
| Ruta | Dep | Scoping |
|---|---|---|
| `/financial-summary` | **O** | 🔒 |
| `/payment-history` | **M** | 🔒 |
| `/access` | **O** | 🔒 |
| `/ocr-stats` · `/ocr-activity` | **O** | 🔒 |
| `/metrics/*` | **M** | 🔒 |

Todos con scoping por `staff.sucursal`/`admin.sucursal` salvo el caso [**R10**] de databases con nombres «AUTOPASS X».

---

## 3. Hallazgos y Severidad

| ID | Ruta / Lugar | Hallazgo | Sev. | Impacto |
|---|---|---|---|---|
| **R1** | `routes/admin/branches.py:18` | `GET /v1/admin/branches` sin ninguna dependencia de auth; expone `BranchResponse` (capacidades, ocupación, pisos, `admin_name`). | **Alta** | Info interna de todas las sedes accesible anónimamente (el público tiene su propio `BranchPublicResponse`). |
| **R2** | `routes/admin/support.py:42,73` + `services/support_service.py:166` | Detail y PATCH de ticket usan `get_by_id`/`get_by_id_with_user` **sin filtro de sucursal** (el listado sí filtra). Un staff/local puede leer y responder tickets de CUALQUIER sede. | **Alta** | IDOR por sucursal: PII de clientes de otras sedes + mutación de tickets ajenos. |
| **R3** | `routes/admin/virtual_time.py:46-83` | Virtual time (adelantar/rebobinar/fijar reloj) es **global** y acepta `local_manager`. | ~~Media-Alta~~ **DESCARTADO** | Herramienta de TEST (temporal, se descartará en producción): uso permitido a roles operativos. |
| **R4** | `routes/admin/users.py:83-93` (`change_user_role`), `:43` (`create_user_admin`), `:53-66` (`update_user_admin`) | `validate_local_admin_user_permission` permite operar sobre cualquier `USER` y el chequeo de rol solo bloquea `ADMIN`. Un local_admin puede **promover un USER de otra sucursal a STAFF/LOCAL_ADMIN** y crear/promover más local_admin. | **Media-Alta** | Escalada de privilegios cross-sucursal y multiplicación de administradores. |
| **R5** | `routes/admin/reservations.py:14` (`patente_lookup`) y `:98` (`admin_available_redemptions`) | `lookup_patente` devuelve `email/nombre/apellido/user_id` de cualquier usuario por patente, sin scope; `admin_available_redemptions(user_id)` lista descuentos de cualquier user_id. | **Media** | IDOR / fuga de PII y datos de fidelización de otros clientes por parte de cualquier staff. |
| **R6** | `routes/system/cameras.py:326` | `POST /v1/system/camera-reading/{gate_id}` sin auth: un tercero puede forjar el estado «LEYENDO PATENTE…» en los dashboards. | **Baja** | Spoofing de estado operativo / notificaciones falsas. |
| **R7** | `routes/parking/status.py:151` | WS `/parking/ws` valida token pero **no rol**: cualquier `USER` recibe el feed real-time de ocupación (el REST `/current-occupancy` exige operativo). | **Baja** | Inconsistencia de acceso a datos operativos. |
| **R8** | `routes/admin/support.py:25` (`mark_ticket_notifications_read`) | Sin scope de sucursal (marca notif de ticket de otra sede). | **Baja** | Limpieza de notificaciones ajenas (impacto menor). |
| **R9** | `routes/system/video.py:134` (`get_capture`) | Scoping por comparación **exacta** `log.sucursal != staff.sucursal` (sin normalizar); con nombres tipo «AUTOPASS Castelar» el staff local pierde acceso a sus propias capturas. | **Baja** | Disponibilidad (falso 403) ante datos inconsistentes; no es fuga. |
| **R10** | Scoping de reportes/cámaras/reservas | Comparaciones de sucursal usando `!=`/`==` literal en varios puntos (`payment_history`, `camera.sucursal`, `get_capture`, `get_permissioned_reservation` cuando sucursal no normalizada) | **Baja** | Con la data real de Neon (H2: prefijos «AUTOPASS ») hay falso 403 o exclusión de datos. |

**Estado de remediación:** **R1, R2 y R4 CORREGIDOS** el 2026-10-08 (Fase 1, sección 5).
**R3 DESCARTADO** (feature de test, se descartará en producción).
Pendientes: **R5–R10** (Fases 2 y 3).

---

## 4. Fortalezas Confirmadas

1. **Endpoints ALPR** (`validate-plate`, `exit-plate`, `validate-qr`, `heartbeat`, WS video, `update-frame`): todos protegidos por `require_alpr_node` / token + rol / red local. Sin acceso anónimo. ✅
2. **Ownership en el 100% de las rutas user** (reservas, notificaciones, tickets, vehículos, canjes): verificadas por `get_by_user_and_id`/`get_by_id_and_user` en los servicios. ✅
3. **Scoping por sucursal en reportes** implementado de forma consistente en `ReportService` (9/9 endpoints). ✅
4. **Requisito de rol en todos los mutadores admin** salvo R1/R6; rate limits en la mayoría (creación/edición/borrado, pagos, balance, cajas, promociones). ✅
5. **Barreras de jurisdicción** (`validate_local_admin_branch`, `validate_local_admin_user_permission`, `get_permissioned_reservation`, `normalize_system_name` en cámaras) cubren el caso de pisos, cámaras, reservas y operación. ✅
6. **Doble refuerzo de la data de Neon**: los hallazgos no son «acceso total», sino faltas de scoping puntuales; ningún rol puede leer saldos, claves ni tokens ajenos vía API. ✅

---

## 5. Plan de Remediación Propuesto

### Fase 1: Cierres de exposición inmediata (P0/P1) — ✅ APLICADA (2026-10-08)
- [x] **F1.1 (R1):** `GET /v1/admin/branches` → `Depends(get_operational_user)`.
- [x] **F1.2 (R2):** `SupportService._can_access_ticket` (helper reutiliza la regla del listado);
  usado por `get_admin_support_ticket_detail` (detail) y `update_ticket_status` (PATCH) → 403
  cross-sucursal.
- [~] **F1.3 (R3): DESCARTADO por decisión del usuario (2026-10-08).** El reloj virtual es una
  herramienta de TEST que se descartará en producción. Dependencia: `get_operational_user`
  (admin/local/staff; los clientes quedan excluidos con 403). El escalamiento por sucursal no
  aplica mientras la feature sea de test.
- [x] **F1.4 (R4):** helper `validate_staff_role_assignment` aplicado en `create_user_admin`,
  `update_user_admin` y `change_user_role`: solo el Admin Global asigna roles no-USER
  (STAFF/LOCAL_ADMIN); un local solo gestiona clientes (USER). Front
  `dashboard-admin-users.js` sincronizado (alta/edición para local: rol solo-lecturo / solo
  Cliente; el PATCH de edición no envía `rol` si el editor es local).

**Verificación:** suite completa `789 passed` (+7 tests nuevos: auth en branches, scoping de
tickets, gate de virtual time, promoción de personal), guards de frontend en verde.

> **Nota R3:** al ser de test, evaluar si al descartarla conviene mover las rutas bajo
> `require_alpr_node`/entorno solo-dev, o eliminarla del todo.

### Fase 2: Endurecimiento de scoping (P2)
- [ ] **F2.1 (R5):** `patente_lookup`: acotar a patentes de la sede del staff (o exigir `A` para buscada global); `admin_available_redemptions`: validar que `user_id` pertenezca a clientes de la sede del operador o restringir a `M`.
- [ ] **F2.2 (R6):** `POST /camera-reading/{gate_id}` → `Depends(require_alpr_node)` o `get_operational_user` (los nodos ya envían `X-Node-Secret`).
- [ ] **F2.3 (R7):** En `occupancy_websocket_endpoint`, exigir rol operativo (misma regla que `/parking/status`).

### Fase 3: Normalización y consistencia (P3)
- [ ] **F3.1 (R9/R10):** Reemplazar comparaciones literales de sucursal por `normalize_branch_name()` en `get_capture`, scoping de cámaras/video e historial de pagos; documentar que la comparación canónica es la normalizada.
- [ ] **F3.2 (R8):** `mark_ticket_notifications_read` con scope de sucursal por coherencia con el listado.

---

## 6. Para el futuro / observaciones

- El modelo de roles es plano (4 roles, sin permisos por recurso). Si crece el personal, evaluar una matriz `rol × permiso` (ej. `can_manage_tickets`, `can_create_staff`) en lugar de más `if rol ==` dispersos.
- `get_current_user` re-sincroniza rol/bloqueo desde BD en cada request: al bloquear o degradar a alguien, el efecto es inmediato. Buen diseño. ✅
- Los endpoints HTTP del sistema (`/v1/system/*`) comparten prefijo: conviene auditar con un test de integración que **los enumere y exija auth** (patrón similar a `check_consistencia_frontend.py`) para que R1/R6 no recaigan.