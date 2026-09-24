# Auditoría de Rendimiento — A5 (ronda A5/v20)

**Estado:** PARCIAL — remediación aplicada y medida el 2026-09-24 (N+1 en
listados de reservas corregido); pendiente el run de profiling con volumen real
(exige datos de Neon, aquí solo hay SQLite dev).

**Fecha:** 2026-09-24 · **Suite:** 694 passed en ~57.64s · **Cobertura users.py:** 90%→92% (ítem #1 cerrado)

---

## 1. Datos medidos (reales, esta ronda)

| Métrica | Medición | Fuente |
|---|---|---|
| Suite completa | **694 passed, 7 warnings en 57.64s** | `pytest -q` (ronda 2026-09-24) |
| Worker (cleanup + notificaciones) | **19 passed en 3.77s** | `pytest tests\test_worker_cleanup.py tests\test_notifications.py -q` |
| Query-count `list_filtered` + serialización (3 reservas) | **2 queries totales** (SELECT reservas + SELECT IN users) | profiler `before_cursor_execute` (ronda remediación) |
| Cobertura `routes/admin/users.py` | **91%→92%** (123 stmts, 6 miss) | coverage (ronda A3) |

## 2. Escaneo N+1 (grep estático, ronda base A5)

**Hallazgo clave de la remediación:** el informe base referenciaba modelos que
**no existen** en el schema vigente (`Bahia.piso`, `Piso.bahias`,
`User.cuenta`) — esas recomendaciones quedaron **obsoletas** y NO se aplicaron.

Escaneo real sobre el schema actual (2026-09-24):
- `ParkingBranch→floors`: ya eager-cargado con `joinedload` en `branch_repository.py:29,54`.
- `SupportTicket.user` / `SupportTicketMessage.user`: ya eager-cargados con `joinedload` en `support_repository.py:52,73,93`.
- `AccessLog.floor`: ya eager-cargado con `selectinload` en `access_log_repository.py:174`.
- `Reservation.user` (listados): **N+1 detectado y corregido** (sección 3).

## 3. N+1 real detectado y corregido (ronda 2026-09-24)

**Síntoma:** los listados de reservas accedían `r.user` por fila con lazy-load
implícito (1 query extra por reserva). Afectaba:
- `ReservationRepository.list_filtered` → `ReservationService.list_admin_reservations`
  (listado admin `/v1/admin/reservations`).
- `get_pending_reminders` / `get_pending_started` / `get_unpaid_overdue` → workers
  de recordatorios, inicio y auto-cancelación.

**Fix aplicado** (`repositories/reservation_repository.py`):
- `selectinload(models.Reservation.user)` en los 4 métodos de listado/batches.
- `_process_auto_cancellations` (`services/worker_service.py`) pasa a usar
  `res.user` (eager) en vez de `UserRepository.get_by_id(...)` por fila; se
  eliminó el import de `UserRepository` del módulo.

**Medición de la ronda:** con 3 reservas, `list_filtered` + serialización
(acceso a `r.user`) = **2 queries totales** (SELECT reservas + SELECT IN users),
constante con N. Pre-fix crecía 1 query por fila.

**Limpieza colateral (DRY):** se eliminó un `ReservationRepository.get_unpaid_overdue`
duplicado que quedaba **sombreado** por la definición activa (filtro de reservas
"por hora" inalcanzable).

## 4. Estado de las recomendaciones del informe base

| Recomendación base | Estado |
|---|---|
| P1 índice en `Bahia.piso_id` | **Obsolleta** — el modelo `Bahia` no existe. `user_id`, `sucursal_nombre` y `patente` de `Reservation` ya tienen índice. |
| P1 `selectinload(Piso.bahias)` | **Obsolleta** — `ParkingFloor.bahias` no existe; `ParkingBranch.floors` ya va con `joinedload`. |
| P2 `selectinload(User.cuenta)` | **Obsolleta** — `User.cuenta` no existe. |
| (nueva) `selectinload(Reservation.user)` | **Aplicado y medido** (sección 3). |

## 5. Pendientes explícitos

- **Run de volúmenes reales (Neon/load):** requiere entorno de prod
  (`DATABASE_URL` Postgres/Neon y/o `TURSO_AUTH_TOKEN`) para medir tiempos de
  query reales; el SQLite dev no tiene volumen.
- **Tooling de profiling A5:** `_tools/auditoria_rendimiento.py` fue removido en
  `265c609` (limpieza de scripts temporales). Para esta medición se usó un
  profiler ad-hoc con `before_cursor_execute`. Recrear la herramienta estable se
  pospone hasta tener acceso al entorno real.

**Criterio de cierre A5:** suite completa en verde (694) + N+1 real corregido y
medido (query-count constante con N en listados) + N+1 estático = 0. El run de
volúmenes reales (Neon) queda documentado como pendiente explícito (requiere
entorno de prod).