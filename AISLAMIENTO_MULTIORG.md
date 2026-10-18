# AISLAMIENTO_MULTIORG.md

Arquitectura de aislamiento multiempresa (multi-tenant) de AUTOPASS: que un operador
nunca vea ni opere datos de otra organización, y cómo quedó implementado capa por capa.

Última actualización: 18/10/2026.

---

## 1. Modelo de datos

- `Organization` (`models/organization.py`): empresas de la plataforma; una sola es
  `es_principal=True` (super-admin).
- `organization_id` (FK nullable a `organizations.id`) en: `User`, `ParkingBranch`,
  `Promotion`, `Settings`, `SupportTicket`, `ParkingCamera` (vía su sede), etc.
- `Reservation` y `AccessLog` **no** llevan `organization_id` directo: se atribuyen a
  través de su sede (`sucursal_id`, FK a `parking_branches`; el nombre vive únicamente
  en esa tabla y se expone con el hybrid `branch_ref_property()`).
- Traducción nombre → id en un solo lugar: `models/branch_ref.py::before_flush`
  (`_elegir_sede` nunca cruza de organización: si no puede atribuir, deja `NULL`).

## 2. Núcleo compartido (reutilizar, no reimplementar)

### `repositories/scoping.py`

| Función | Qué hace |
| --- | --- |
| `scope_by_organization(query, model, organization_id)` | Filtro de lista genérico por org (compartido por repositorios de usuarios, sucursales, promos, settings, reservas, etc.). |
| `multi_organization_active(db)` | `COUNT(organizations) > 1` → **True = modo estricto**; ≤1 org (BDs locales/demo) = modo tolerante actual. `try/except → False`. |
| `organization_of_sede(db, branch_id=None, branch_name=None)` | **Atribución sede → empresa**. Por id; por nombre solo si todos los candidatos coinciden en la misma org; ambiguo o inexistente → `None`. |
| `sede_ids_and_names(db, organization_id)` | `(ids, nombres)` de las sedes de una org; los nombres solo si no se repiten en otra empresa. |

### `core/security.py`

| Función | Qué hace |
| --- | --- |
| `resolve_actor_organization_id(db, actor)` | Org del actor: `actor.organization_id` → si no, la de su sede (`sucursal_id` o nombre). Sin atribución → `None`. |
| `require_tenant_scope(db, organization_id, detail=...)` | **Fail-closed**: 403 si `organization_id is None` y multi-org activo. Single-tenant → no hace nada. |
| `enforce_organization_scope(actor, resource_org, ..., db=None, organization_id=None)` | Guard único de IDOR por recurso recibido por id (usuarios, sucursales, pisos, promos, cámaras, reservas). Exención primero para `is_principal_org_admin`; con `db` resuelve la org del actor y en multi-org activo rechaza 403 si **el actor o el recurso** no tienen org atribuible; sin `db` conserva el comportamiento tolerante original. |
| `is_principal_org_admin(user)` | Exención del super-admin (tolerante: sin datos devuelve `False`). |

Regla transversal: **`services/` no puede improvisar scoping propio**; delega en estas
funciones (verificado que solo `user_service.py`/`oauth_service.py` importan
`core.security` adentro de servicios, sin ciclos).

## 3. Regla de filas legacy (sin `sucursal_id`)

Una fila con solo `sucursal = "Nombre"` se acepta dentro del alcance de una org **solo
si ese nombre es atribuible** (`organization_of_sede(...) == organization_id`). Si el
nombre es homónimo entre dos empresas, **no es atribuible a nadie** → no se incluye
(fail-closed, nunca se elige una al azar). Implementado en:

- `repositories/reservation_repository.py::_sucursal_id_predicate` (con `include_global`
  para las filas globales: `sucursal_id IS NULL AND nombre IS NULL`, que siguen
  incluidas cuando corresponde).
- `repositories/access_log_repository.py::_sucursal_id_filter` / `_scope_filter` /
  `log_in_scope`.
- `BranchRepository.get_id_by_name` devuelve `None` ante nombre ambiguo (nunca `.one()`
  que rompía con sedes homónimas).

## 4. Reservas (IDOR cross-org)

- **Listado / conteo** (`ReservationService.list_admin_reservations`,
  `get_new_reservations_count`): `resolve_actor_organization_id` para **todos** los roles
  + `require_tenant_scope` + `ReservationRepository.list_filtered(..., organization_id=org)`.
- **Operar una reserva por id** (`get_permissioned_reservation`, `confirm_reservation_payment`,
  `update_admin_reservation`): `check_reserva_scope(db, staff, reserva)` =
  `enforce_organization_scope` con la org de la reserva (vía `organization_of_sede`) y
  recién después la regla histórica de sede para staff/local admin.
- **Crear / editar sede de una reserva manual** (`_sucursal_admin`): con multi-org activo,
  el nombre de la sede debe ser atribuible a la empresa del operador → 404 si no existe
  / no es atribuible, 403 si pertenece a otra empresa. El staff no-admin siempre opera
  sobre su propia sucursal.

## 5. Cobro de estadías (`BillingService.process_payment`)

- Recibe `organization_id` (empresa del operador) y `sucursal_id` (sede si no es ADMIN
  global), calculados en la ruta `routes/parking/access.py::pay_stay` con
  `resolve_actor_organization_id` + `BranchRepository.get_id_by_name`.
- `require_tenant_scope` primero (sin alcance resoluble con multi-org → 403), luego
  `get_last_entry_by_patente(..., organization_id, sucursal_id)` y `log_in_scope` como
  defensa en profundidad: **nunca se cobra una estadía registrada por otra empresa**.

## 6. Acceso físico (ALPR / QR / manual): gate → sede → empresa

- `core/config.py::ALPR_NODE_ORG_ID` (env, `0` = sin binding) + 
  `core/alpr_security.py::require_alpr_node_org(request)`: dependencia de las rutas
  `/v1/access/validate-plate|exit-plate|validate-qr` que valida el nodo (igual que
  `require_alpr_node`, cuyo retorno no cambió) y devuelve la empresa a la que está
  ligado el nodo. Los flujos de acceso deciden con ese valor.
- `services/access_service.py`:
  - `_sede_desde_gate(db, gate_id, organization_id)`: prefijo antes del `_` →
    `ParkingBranch`. Con binding busca solo entre las sedes de esa empresa; sin binding,
    si el prefijo es homónimo entre empresas devuelve `None` (no atribuible).
  - `_alcance_gate(...) → (sede, org)`: prioriza el binding del nodo; si no lo hay,
    la org sale de la sede resuelta (gate → sede → empresa).
  - `_alcance_logs(sucursal, org)`: solo acota los logs cuando hubo sede resuelta
    (sin sede no hay atribución).
  - Gate ligado a una empresa sin sede propia → `{"status": "denied", "message":
    "Gate no habilitado para esta organización"}` (fail-closed, antes de tocar datos).
  - `validate_qr`: además exige que la reserva se atribuya a la org del gate
    (`Esta reserva no pertenece a esta organización`).
  - `manual_entry` / `manual_exit` / `cancel_stay` reciben `organization_id` (desde
    `routes/admin/operations.py`, con `resolve_actor_organization_id` del staff).

## 7. Rutas: delegar, no decidir

Las rutas siguen delgadas: resuelven el alcance (`Depends(require_alpr_node_org)` o
`resolve_actor_organization_id(db, staff)`) y lo pasan al servicio/repositorio; los
helpers de ruta (`_check_promo_org`, `_enforce_camera_org`,
`validate_local_admin_user_permission`) reciben `db` y lo reenvían a
`enforce_organization_scope` para que el guard sea estricto.

## 8. Dos modos según la base

| | Single-tenant (≤1 org) | Multi-tenant (>1 org) |
| --- | --- | --- |
| Listados y guards | Comportamiento actual, tolerante a datos incompletos | Acentado por `organization_id` |
| Actor/recurso sin org | Se deja pasar (legacy/demo) | 403 fail-closed |
| Nombres de sede homónimos | No aplica (nombres únicos) | Solo se atribuyen si son unívocos |

Eso mantiene intactas las BDs locales de prueba (`autopass.db`, `parking.db`, que no
tienen `organizations`) y solo activa el modo estricto cuando hay dos empresas cargadas.

## 9. Tests

`tests/test_multi_tenant_isolation.py` (fixtures reutilizables: `_crear_org`,
`_crear_usuario`, `_crear_branch`, `_branch_id`, `_crear_access_log`,
`_crear_reserva_rango`, `_headers`):

- Aislamiento de listados: usuarios, sucursales, promos, settings, reservas, cámaras,
  reportes financieros, ocupación y tickets.
- IDOR de reservas por id (editar, confirmar pago), creación en sede ajena y edición
  hacia sede ajena; fail-closed del admin sin organización.
- `pay-stay`: no cobra estadías de otra empresa (y sí las propias); staff sin org → 403.
- ALPR: gate de otra empresa con binding → denied; sede homónima no filtra la estadía
  ajena; QR de reserva ajena → denied y QR propio → allowed; `manual_entry` no reutiliza
  la estadía registrada por otra empresa; la ruta pasa el binding del nodo;
  `require_alpr_node_org` devuelve `None`/id y exige nodo autorizado.

Correr con el python del venv:

```bash
venv\Scripts\python.exe -m pytest -q tests/test_multi_tenant_isolation.py
venv\Scripts\python.exe -m pytest -q
```

## 10. Límites conocidos (aceptados en el entorno de prueba)

- El aforo (`ParkingAforo`) se resuelve por nombre de sede: con sedes homónimas queda
  global (`sucursal_id NULL`), no por empresa. Es capacidad, no acceso a datos.
- `AccessLog` no tiene `organization_id` propio: la atribución depende de la sede; una
  fila sin sede atribuible queda fuera de todo alcance (fail-closed).
- Todo el proyecto es un trabajo escolar con datos de prueba: no hay despliegue real.
