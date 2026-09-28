# Auditoría de Rendimiento — A5 (profiling con volumen sintético)

**Estado:** HECHO (2026-09-27, CERRADA ✓) — profiling con volumen sintético
corregido y medido. Hot spot O(N²) resuelto (217s → 1.86s) vía índice compuesto;
**pendientes P1 remediados** (historial de accesos con límite+dedupe, cleanup con
batch) y anotados en §6.

**Fecha:** 2026-09-24 (remediación base) + 2026-09-27 (profiling + P1 con volumen) ·
**Suite:** 700 passed · **Migración:** `cdb7d130c856` (2 índices sobre `access_logs`)

---

## 1. Metodología de medición

Imposible medir con volumen real: Neon plan gratuito sin datos y `parking.db` dev
vacía (0 MB). En su lugar, **sandbox SQLite aislado** (`%TEMP%\a5_profiler_volume.db`)
con volumen sintético realista y **hook `before_cursor_execute`** para contar y
normalizar cada consulta por request:

- 6 sucursales (cada una con 2 pisos, aforo y tarifas en settings)
- ~413 usuarios (1 admin, 6 staff, 6 local, 400 user)
- 1.200 vehículos · 20.000 reservas · 60.600 access_logs
- 450 redemption_tickets (la mayoría **sin coords** → expone N+1 de fidelización)
- 12 promociones

> Limitación anotada: tiempos son de SQLite dev (en-disk), no de Postgres/Neon.
> Los **query-count por endpoint** sí son representativos del patrón N+1 real.

## 2. Query-count y tiempos por endpoint (ronda 2026-09-27)

| Endpoint | queries | tiempo | Hallazgo |
|---|---|---|---|
| `GET /v1/parking/status` | 5 | 47 ms | OK |
| `GET /v1/parking/branches` | 13 (x6 aforo + x6 reservas) | 68 ms | N+1 acotado por sucursal (1/sucursal) |
| `GET /v1/parking/current-occupancy` | 6 | 1.114 ms | OK (1 query para ~3.000 entradas vivas) |
| `GET /v1/admin/reservations` | 9 + N_vencidas | 41.9s → 1.06s ✱ | **N+1 en cleanup** (sección 4) |
| `GET /v1/admin/users` | 2 | 39 ms | OK |
| `GET /v1/reports/financial-summary` | 18 | **217.3s → 1.86s ✱** | **O(N²) resuelto** (sección 3) |
| `GET /v1/reports/payment-history` | 2 | 104 ms | OK |
| `GET /v1/reports/access` | — | **EXPLOTA** | **Historial sin paginar** (sección 6) |
| `GET /v1/reports/metrics/access-activity` | 2 | 1.000 ms | Full-scan 60k filas (aceptable) |
| `GET /v1/reports/ocr-activity` | 2 | 824 ms | Full-scan con ocr_time (aceptable) |
| `GET /v1/user/redemption-tickets` | **452** | 347 ms | **N+1** (x375 promotions + x75 branches) |
| WS `/v1/parking/ws` broadcast GLOBAL (50 clientes) | 19 (x6 aforo, x6 floors, x6 reservas) | 73 ms | N+1 por sucursal, sin caché en global — **no bloquea** el event loop |
| WS broadcast SUCURSAL (50 clientes) | 21 | 62 ms | idem |
| `cleanup_overdue_reservations` (2.000 vencidas) | 2.003 | 1.31 s ✱ | N+1 por reserva (sección 4) |
| `cleanup_overdue_reservations` (1.000 vencidas) | 1.003 | 0.73 s ✱ | idem |

✱ post-índices de `access_logs` (sección 5).

## 3. Hot spot principal: O(N²) en financial-summary — CORREGIDO

**Síntoma:** `GET /v1/reports/financial-summary` tardaba **217 segundos** con
60.6k logs / 20k reservas (medición HTTP del 2026-09-27).

**Causa raíz** (`repositories/report_repository.py:192` — `unpaid_entries_without_exit`):
por cada ENTRADA impaga (~30k) una **subconsulta correlacionada `NOT EXISTS`** sobre
`access_logs` filtrando `patente_detectada` (sin índice), `tipo_evento`, `sucursal`
y `fecha_hora`. Sin índice de cobertura = **full-scan por fila → O(N²)**.

**Fix (migración `cdb7d130c856`, modelo AccessLog):**
`ix_access_logs_pat_tipo_suc_fecha (patente_detectada, tipo_evento, sucursal, fecha_hora)`.

**Medición: 217.3s → 1.86s (117× más rápido).** El 99% del tiempo estaba en esa
única subquery; con el índice pasa de full-scan a un lookup indexado.

## 4. N+1 en cleanup de reservas vencidas — ANOTADO (P1)

**Síntoma:** `GET /v1/admin/reservations` ejecuta `ReservationService.cleanup_overdue_reservations`
dentro del GET. Por cada reserva impaga vencida llama `AccessRepository.get_entry_for_reserva`
(`reservation_service.py:95`) → **1 query por reserva** (medido: 2.003 queries
para 2.000 vencidas).

**Mitigación aplicada:** `ix_access_logs_reserva_id (reserva_id, tipo_evento)`
deja cada lookup en ~0.6 ms (full-scan eliminado). Con 2.000 vencidas el cleanup
pasa de minutos a 1.3s.

**Pendiente de código (P1, sección 6):** el patrón N+1 persiste — conviene
resolver los IDs «en predio» en un solo batch (`get_en_predio_ids` ya existe y
hace exactamente eso) y sólo consultar el primer acceso por reserva saliente.

## 5. N+1 acotados (por sucursal) — anotados

- **`list_public_branches` / `_get_global_status` (WS):** por cada sucursal →
  `get_aforo_by_sucursal` + `floors` (lazy) + `get_paid_current_by_sucursal`.
  Con 6 sucursales = 19 queries/broadcast. Crece lineal con el nº de sucursales;
  con el catálogo actual (≤6-8) es aceptable. El broadcast GLOBAL **no** reusa
  la caché TTL 3s de las branches públicas.
- **`get_user_redemption_tickets`:** tickets sin coords → `PromotionRepository.get_by_id`
  (+ `BranchRepository.get_by_name` si tampoco tiene sucursal). Medido: **452 queries**
  para 450 tickets (375 promos + 75 branches) — 346 ms. Aceptable hoy, escala mal
  si crecen los tickets por usuario (es 1 usuario; hotel de 1-1).

## 6. Pendientes explícitos (fuera de alcance de esta ronda)

| # | Prioridad | Hallazgo | Código | Recomendación |
|---|---|---|---|---|
| P1 | — | ~~`GET /v1/reports/access` explota: `access_logs_history` no pagina y luego `get_by_patentes` arma `IN (60k patentes)`~~ | `report_repository.py:369` / `report_service.py:222` | **REMEDIADO (2026-09-27, v9.34.48):** límite server-side (`limit`, default 300) en `access_logs_history` + dedupe de patentes (`dict.fromkeys`) previo al `IN`. Mantiene el contrato array del front. Medido post-fix: 200 OK, **104ms, 4 queries (vs. crash SQLite / IN de 60k)**, sin límite el IN de Postgres bordea 65535 params. |
| P1 | — | ~~N+1 cleanup de vencidas persistente (1 query/reserva)~~ | `reservation_service.py:82` / `worker_service.py:207` | **REMEDIADO (2026-09-27, v9.34.48):** `AccessRepository.get_reserva_ids_with_entry` (batch, 1 query) reemplaza `get_entry_for_reserva` por fila en `cleanup_overdue_reservations` y `_process_auto_cancellations`; método por-fila eliminado (DRY). Medido con 2.500 vencidas: **4 queries / 179ms (vs. 2.003 queries / 1.314ms pre-fix)**. |
| P2 | Baja | ~~Broadcast WS GLOBAL sin caché (recomputaba branches + ocupación reservas por cada push)~~ | `status.py::_get_global_status` / `_get_branch_status` | **REMEDIADO (2026-09-27, v9.34.49):** caché TTL 3s del payload GLOBAL (`occupancy_ws_global`) y por sucursal (`occupancy_ws_branch_{norm}`) en `core/cache.py`; `broadcast_update(force_refresh=True)` desde `NotificationService.notify_occupancy_change` para invalidar solo ante cambios reales (`invalidate("occupancy_*")`); conexiones nuevas y pushes repetidos reusan el payload. Medido con 50 broadcasts GLOBAL: **19 queries / 50 pushes = 1 compute + 49 cache hits (antes ~950, 50× menos)**, 71ms total. |
| P2 | Baja | ~~`ix_access_logs_id` y demás `ix_{tabla}_id` redundantes sobre el PK~~ | modelos (18 tablas) vs alembic | **REMEDIADO (2026-09-27, v9.34.49):** se quita `index=True` del `id` PK en los 18 modelos (la PK ya indexa id) y migración `8b3e9e815c78` DROP de los 2 índices que sí había creado la cadena (`ix_redemption_tickets_id`, `ix_support_ticket_messages_id`). Bonus: `ix_mercadopago_payments_user_id` ahora declarado en el modelo (`index=True`) — era índice REAL (FK) creado por alembic pero ausente del modelo. Resultado: **paridad create_all ↔ alembic head = 0 diffs de índices**, verificado por `tests/test_schema_parity_p2.py`. |

## 7. Verificación de cierre

- Migración `cdb7d130c856` y `8b3e9e815c78` reproducibles desde BD vacía (`alembic upgrade head`).
- Paridad índice modelo↔alembic: **0 diffs** (verificado por
  `tests/test_schema_parity_p2.py`), tras quitar el `index=True` redundante de
  los 18 PK y declarar `ix_mercadopago_payments_user_id` en el modelo.
- Suite completa en verde: **702 passed** (695 base + 5 regresión P1 +
  2 paridad P2), 7 warnings.
- Cierre total de P1+P2, con mediciones:

| Fix | Antes | Después |
|---|---|---|
| `GET /v1/reports/access` | **CRASH** (SQLite `too many SQL variables`, IN 60k) | **200, 104ms, 4 queries**, 300 items + patentes deduped |
| `cleanup_overdue_reservations` (2.500 vencidas) | 2.003 queries / 1.314ms | **4 queries / 179ms** |
| `_process_auto_cancellations` (worker) | N+1 por reserva | 1 query batch `IN` |
| Broadcast WS GLOBAL (50 pushes) | ~950 queries (recompute por push) | **19 queries** (1 compute + 49 cache hits) |
| Paridad índices modelo↔alembic | 18 PK con `index=True` redundantes + 1 FK índice no declarado | **0 diffs** |

- Query-count por endpoint documentado en §2; N+1 detectados anotados (§§4-6) y
  los pendientes P2 cerrados en esta ronda.

**Criterio A5 cumplido:** reporte con tiempos y query-count por endpoint ✓ ·
sin N+1 de listado sin anotar ✓ (todos anotados y priorizados; P1 y P2
remediados y medidos) · hot spot de agregados corregido y medido ✓.