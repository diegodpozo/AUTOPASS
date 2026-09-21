# Auditoría de Cobertura de Tests — AUTOPASS

> **Fecha:** 2026-09-20 (revisión contra código v9.23.0, rama `main`, Python 3.14.7)
> **Alcance:** `tests/` (34 archivos, 330 tests) vs `services/`, `routes/`, `repositories/`, `alpr/`, `core/`.
> **Metodología:** `pytest tests --cov=services --cov=routes --cov=repositories --cov=alpr --cov=core --cov-report=term-missing --cov-report=html` (HTML en `coverage_html/`).
> **Herramientas:** `pytest-cov`, `coverage`, `pytest`.

---

## 1. Resumen Ejecutivo

**Cobertura total: 69%** (7044 stmts / 2194 sin cubrir). La suite pasa completa (**330 passed**). Ronda #1–#6 (38 tests: 55%→60%), ítems #7–#10 (79 tests: 60%→66%), regresión CSP (`test_security_headers.py`, 2), y ronda #11 — **pagos y auth a 100%** (61 tests: 66%→69%):

| Capa | Cobertura (antes) | Cobertura (ahora) | Nota |
|---|---|---|---|
| `alpr/` | 21% (738 stmts) | **49%** (813 stmts) | runner 64%, ocr_engine 56%, config 95% |
| `routes/` | 35% (2565 stmts) | **57%** (2010 stmts) | auth 100%, webhook MP 90%, branches 76%, status 84%, access 89% |
| `services/` | 63% (2392 stmts) | **78%** (3109 stmts) | payments 100%, access_service 89%, occupancy 91%, worker 66%, billing 73% |
| `repositories/` | 77% (816 stmts) | **78%** (777 stmts) | branch 98%, access_log 85% |
| `core/` | 68% (345 stmts) | **75%** (335 stmts) | security 85%, database 81% |
| `routes/views.py` | 74% | 74% | Renderizados base cubiertos |

Zonas por encima del 85%: `access_service` (89), `branch_repository` (98), `oauth_service` (89), `branch_service` (89), `access.py` route (89), `occupancy_service` (91), `time_service` (90), `user_notification_service` (91), `mercadopago.py` route (90), `vehicles.py` (89), `config` ALPR (95), `limiter/mqtt/logger/time` (100), `access_log_repository` (85), **`routes/auth.py` (100)**, **`services/payments.py` (100)**, `session_repository` (100).

**Nivel de riesgo: MEDIO.** Los flujos de seguridad cobrados en A1 tienen red de protección (webhook MP 90%, pay-stay 89%, toggle-block/users 65%, security 85%, workers 66%, access_service 89%, branches/status 76/84%) y el pipeline ALPR salió de 0%. El grueso que queda sin cubrir es negocio de management y streaming: **admin cameras/settings (17–21%), video WS (`routes/system/video.py` 24%), `alpr/preprocessor` (25%), `video_streamer` (18%), `ws_client` (24%)**.

---

## 2. Ranking de cobertura por módulo (< 60%)

Peor → mejor (post ítems #1–#10):

| Módulo | Stmts | Miss | Cobert. | Crítico |
|---|---:|---:|---:|---|
| `core/seed.py` | 51 | 51 | **0%** | No (utilidades) |
| `routes/system/cameras.py` | 247 | 204 | **17%** | **SÍ** — cámaras ALPR |
| `alpr/video_streamer.py` | 50 | 41 | **18%** | **SÍ** — streaming |
| `routes/admin/settings.py` | 67 | 53 | **21%** | **SÍ** — parametrización |
| `alpr/ws_client.py` | 25 | 19 | **24%** | Media |
| `routes/system/video.py` | 121 | 92 | **24%** | **SÍ** — WS video (fix A1 P0-2) |
| `alpr/preprocessor.py` | 163 | 122 | **25%** | **SÍ** — pipeline ALPR |
| `routes/admin/promotions.py` | 64 | 44 | **31%** | Media |
| `routes/user/balance.py` | 62 | 42 | **32%** | **SÍ** — dinero |
| `routes/system/common.py` | 75 | 50 | **33%** | Media |
| `routes/system/health.py` | 67 | 42 | **37%** | Media |
| `routes/user/support.py` | 56 | 33 | **41%** | Media |
| `routes/user/fidelization.py` | 118 | 62 | **47%** | Media |
| `routes/admin/virtual_time.py` | 64 | 32 | **50%** | Media |
| `repositories/points_repository.py` | 12 | 6 | **50%** | Media |
| `repositories/system_repository.py` | 12 | 6 | **50%** | Media |
| `alpr/ocr_engine.py` | 456 | 202 | **56%** | **SÍ** — reconocimiento OCR |
| `routes/admin/support.py` | 37 | 16 | **57%** | Media |
| `repositories/promotion_repository.py` | 22 | 9 | **59%** | Media |

Módulos que **superaron** el umbral del 60% en la ronda #11: `routes/auth.py` (37→**100%**), `services/payments.py` (43→**100%**).

Módulos que **superaron** el umbral del 60% en la ronda #7–#10: `services/access_service.py` (38→**89%**), `routes/admin/branches.py` (19→**76%**), `routes/parking/status.py` (23→**84%**), `core/database.py` (35→**81%**), `services/occupancy_service.py` (90→**91%**), `services/branch_service.py` (→**88%**), `repositories/branch_repository.py` (→**98%**). En la ronda #1–#6: `alpr/runner.py` (0→**64%**), `services/worker_service.py` (44→**66%**), `routes/admin/users.py` (54→**65%**), `routes/user/mercadopago.py` (34→**90%**), `routes/parking/access.py` (→**89%**), `core/security.py` (54→**81%**).

El HTML navegable completo quedó en `coverage_html/` (índice por archivo, incluye los módulos con saltos por línea).

---

## 3. Cruce con flujos críticos

### 3.1 ALPR (reconocimiento, consenso, cooldown, hallucination) — **[ALTO→MEDIO, 49%]**
`test_alpr_pipeline.py` cubre por primera vez el pipeline real: **runner→consenso→cooldown→event_out** (runner 64%, ocr_engine 56%, config 95%): arranque fatal de VideoStreamer, bucle principal en modo ENTRADA, consenso de `CONSENSUS_REQUIRED` votos, descarte de frames en negro, debounce de `send_event`, y corrección posicional `CorregirPatente`. Faltan: `preprocessor.py` (25%, recortes/mercosur), `video_streamer.py` (18%) y `ws_client.py` (24%).

### 3.2 Workers (limpieza, notificaciones) — **[ALTO→MEDIO, 66%]**
`test_worker_cleanup.py` agrega los flujos de limpieza: auto-cancelación de sesiones vencidas con notificación y liberación de plaza, cleanup de reservas por hora a las 2 h (con protección si hay AccessLog de ENTRADA), `auto_finalize_all_reservations` y purga de imágenes ALPR viejas (sobre settings). Queda el disparo periódico del tick (startup) y bloques menores.

### 3.3 Pagos / Webhook Mercado Pago — **[ALTO→BUENO, 90%/100%]**
`test_mercadopago_webhook.py` cubre la capa route **HTTP** (`/webhook` y redirects success/pending/failure) que era el gap de la auditoría original: 7 casos del webhook (confirmado, `data_id` raíz, sin id, sin ext_ref, Error MP, HTTPException, JSON inválido) + 3 redirects con `follow_redirects=False`. En la ronda #11, **`tests/test_payments.py` (37 tests) lleva `services/payments.py` a 100%**: abono manual (con/sin descuento por canje, sin usuario, ya pagada, notificación fallando), pago con saldo (404/400/ya pagada/insuficiente, descuento + acreditación de puntos + mail, reserva no-horaria iniciada), pago Mercado Pago (400, `aplicado:False`, descuento consumido, reserva de plaza no-horaria), simulación de reembolso (en predio, no pagado, antes de inicio, después de fin, ventana hora/día) y cancelación (404, ya cancelada, completada, en predio, con/sin reembolso, ajuste de puntos, notificación fallando).

### 3.4 OAuth callback — **[BIEN, 89%]**
Sin cambios: `test_oauth.py` (19 tests) cubre roundtrip de state, providers, exchange, userinfo, signup. En la ronda #11, **`tests/test_routes_auth.py` (24 tests) lleva `routes/auth.py` a 100%**: registro (éxito, duplicado 400, error interno 500), recuperación (mail a usuario conocido/inconocido, reset con purpose inválido/token vencido/404/éxito con relogin), login (401, sin device, device nuevo con otra sesión activa → aviso `NEW_DEVICE_LOGIN`, misma device, absorción por user-agent), OAuth (providers, authorize 503/302, callback con error/state inválido/sin código/intercambio fallido/usuario existente/bloqueado/signup, y complete que crea el usuario social).

### 3.5 Vista de WS status (aforo) — **[ALTO→BUENO, 84%]**
`test_status_ws.py` cubre por primera vez el WebSocket real de aforo: conexión con token válido (admin → `GLOBAL_UPDATE`; usuario de sede → `BRANCH_UPDATE`), broadcast concurrente a dos clientes, cierre 4008 sin token/token inválido, y `OccupancyManager` (connect/disconnect/broadcast por sucursal/GLOBAL). Además los endpoints HTTP `list_public_branches`, `get_parking_status` y `current_occupancy`.

### 3.6 Endpoints admin — **[ALTO→MEDIO, 17–76%]**
`test_admin_branches.py` cierra el CRUD de sucursales y pisos (`branches.py` 19→**76%**): listado con resumen, alta/baja/capacidad de pisos y validaciones de ocupación, crear/editar/renombrar (con propagación) /eliminar/toggle de sucursales, incluyendo los 400 por vehículos y reservas activas. Siguen sin cubrir: `settings.py` 21%, `cameras.py` 17%, `promotions.py` 31%.

---

## 4. Lista priorizada — primeros 10 tests

| # | Prioridad | Test | Módulo objetivo | Antes | Ahora |
|---|---|---|---|---|---|
| 1 | Alta | Pipeline ALPR completo: `runner → preprocessor→ocr (mock engines) → consenso → evento` | `alpr/runner.py` | 0% | **64%** ✅ |
| 2 | Alta | Consenso de votos + cooldown: mayoría, empate, rechazo | `alpr/ocr_engine.py` | 28% | **56%** ✅ |
| 3 | Alta | Webhook MP HTTP: firma válida/inválida, idempotencia, `rejected` | `routes/user/mercadopago.py` | 34% | **90%** ✅ |
| 4 | Alta | Limpieza de sessions expiradas + liberación de cupos por worker | `services/worker_service.py` | 44% | **66%** ✅ |
| 5 | Alta | `pay-stay` autenticado (fix A1 P0-1): 401/403 segun rol, 200 staff, 400 sin estadía | `services/payments.py` + `routes/parking/access.py` | 43%/79% | **43%/89%** ✅ |
| 6 | Alta | Bloqueo de cuenta (toggle-block) invalida tokens activos (fix A1 P0-3) | `core/security.py` + `routes/admin/users.py` | 54% | **81%/65%** ✅ |
| 7 | Media | Ingreso/egreso con barrera: flujo open-barrier → GPIO → estado | `services/access_service.py` | 38% | **89%** ✅ |
| 8 | Media | CRUD de sucursales admin (lista, crear, editar, eliminar, capacidad motos) | `routes/admin/branches.py` | 19% | **76%** ✅ |
| 9 | Media | WS de aforo: conexión, broadcast `GLOBAL_UPDATE`, desconexión | `routes/parking/status.py` | 23% | **84%** ✅ |
| 10 | Media | `sync_schema()` (fix A4 P1): BD vacía → tablas + alembic head; BD preexistente sin duplicar | `core/database.py` | 35% | **81%** ✅ |
| 11 | Alta | Pagos trimodales: abono manual/saldo/MP, descuentos por canje, simulación/ejecución de reembolso, cancelaciones | `services/payments.py` | 43% | **100%** ✅ |
| 12 | Alta | Auth: register/forgot/reset, login multi-dispositivo con sesiones, flujo OAuth completo | `routes/auth.py` | 37% | **100%** ✅ |

Los ítems 5 y 6 eran los más urgentes (regresiones directas sobre fixes de seguridad de A1) y quedaron cerrados. Los ítems #7–#10 ya están escritos y en verde (79 tests nuevos). En la ronda #11 se cerraron los ítems #11–#12 (61 tests nuevos: `test_payments.py` 37 + `test_routes_auth.py` 24). Próximos candidatos por impacto: **preprocessor ALPR (25%), video WS (`routes/system/video.py` 24%), `video_streamer` (18%), admin cameras/settings (17–21%)**.

---

## 5. Umbral mínimo en CI

`ci.yml.disabled` (v11): corre en ubuntu `python 3.11`, ejecuta `python scripts/patch_bidi.py` (script **eliminado**) y `alembic upgrade head` (falla en BD vacía, ver A4.1). **No reactivar tal cual.**

Opciones para reactivar CI:
- Correr en `ubuntu-latest` con `python 3.14` (venv local es 3.14.7).
- Reemplazar `patch_bidi.py` por el flujo de inicialización único `init_db.py` (o `sync_schema()`).
- Agregar `--cov-fail-under=65` (cobertura actual 69%). El umbral puede subir por PR a 70.
- No correr `alembic upgrade head` desde cero: usar `python init_db.py`.

Recomiendo reactivar CI con `--cov-fail-under=70` al mergear esta ronda.

---

## 6. Checklist de Cierre

| Ítem | Estado |
|---|---|
| `pytest-cov` + `coverage` instalados | ✔ |
| `pytest --cov=... --cov-report=html` ejecutado (**69% total, 330 passed**) | ✔ |
| Reporte HTML navegable generado (`coverage_html/`) | ✔ |
| Ranking por módulo (< 60%) documentado | ✔ |
| Cruce con flujos críticos (ALPR, workers, payments, oauth, WS, admin) | ✔ |
| Lista priorizada "primeros 10 tests" elaborada | ✔ |
| Umbral mínimo en CI evaluado (`ci.yml.disabled` desactualizado, no reactivar tal cual) | ✔ |
| Tests de la lista #1–#6 escritos y en verde | ✔ |
| Tests de la lista #7–#10 escritos y en verde | ✔ |
| Tests de la lista #11–#12 escritos y en verde (payments y auth a 100%) | ✔ |

---

## 7. Notas de ejecución

- La suite usa la BD SQLite temporal por test (patrón habitual del repo), 330 passed en 24–33s.
- Tests nuevos ronda #1–#6: `test_alpr_pipeline.py` (14), `test_worker_cleanup.py` (7), `test_mercadopago_webhook.py` (10), `test_toggle_block.py` (6), `test_pay_stay.py` (5) → 38 tests.
- Tests nuevos ronda #7–#10: `test_access_flow.py` (33), `test_admin_branches.py` (21), `test_status_ws.py` (16), `test_core_database.py` (9) → 79 tests.
- Tests nuevos ronda #11: `test_payments.py` (37) + `test_routes_auth.py` (crecido a 24, antes 2) → 61 tests. `test_payments.py` usa el patrón StaticPool + `sessionmaker` del repo; `test_routes_auth.py` reutiliza el fixture de `test_pay_stay.py` (engine SQLite en memoria por test, `dependency_overrides` guardado/restaurado y `limiter.reset()`).
- El flujo login multi-dispositivo exige UserSession con `last_login_at` dentro de la ventana (`ACCESS_TOKEN_EXPIRE_MINUTES`, 1440) para que `count_other_devices`/`get_recent_by_user_agent` matcheen; y los redirects OAuth (`303` a `/#fragment`) se prueban con `follow_redirects=False`, decodificando el fragmento con `urllib.parse.unquote`.
- Detalle importante: en endpoints con `TestClient` hay que usar `create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)` — `sqlite:///:memory:` crea BD por conexión y los requests corren en otro thread (aparece "no such table"). Ya aplicado en los archivos HTTP nuevos.
- El WebSocket de aforo **sí es testeable** con `TestClient.websocket_connect` en este stack (starlette/CPython 3.14): se parchean `status.decode_access_token`, `status.UserRepository.get_by_email` y `status.get_db` (el endpoint usa `next(get_db())`, no `Depends`, por lo que `dependency_overrides` no aplica).
- En tests del ALPR, `FORCE_OCR=True` hace short-circuit y **no** llama a `detect_motion`; y con `monkeypatch time.sleep` a no-op los sincronismos deben esperar estado final (`_wait_for`) y no dormir.
- En tests de `access_service` el tiempo se fija monkeypatcheando `TimeService.now` (classmethod); la barrera se verifica monkeypatcheando `services.hardware_service.HardwareService.trigger_barrier`.
- Los `ResourceWarning: unclosed database` (report_service, sqlalchemy internals) son avisos de sesiones sin cerrar — no afectan resultados, pendientes de limpieza futura.
- El HTML de cobertura fue generado con `--cov-report=html:coverage_html` (directorio `coverage_html/` en la raíz), no commiteado.