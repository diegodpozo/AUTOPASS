# Auditoría de Cobertura de Tests — AUTOPASS

> **Fecha:** 2026-09-21 (revisión contra código v9.23.1, rama `main`, Python 3.14.7)
> **Alcance:** `tests/` (41 archivos, 557 tests) vs `services/`, `routes/`, `repositories/`, `alpr/`, `core/`.
> **Metodología:** `pytest tests --cov=services --cov=routes --cov=repositories --cov=alpr --cov=core --cov-report=term-missing --cov-report=html` (HTML en `coverage_html/`).
> **Herramientas:** `pytest-cov`, `coverage`, `pytest`.

---

## 1. Resumen Ejecutivo

**Cobertura total: 80%** (7044 stmts / 1410 sin cubrir). La suite pasa completa (**557 passed**). Ronda #1–#6 (38 tests: 55%→60%), ítems #7–#10 (79 tests: 60%→66%), regresión CSP (`test_security_headers.py`, 2), ronda #11 (**pagos y auth a 100%**, 61 tests: 66%→69%), ronda #12 (**preprocessor ALPR a 100%**, 36 tests: 69%→71%), ronda #13 (**streaming y video a 100%**, 47 tests: 71%→73%), ronda #14 (**ocr_engine ALPR a 98%**, 55 tests: 73%→76%), ronda #15 (**gestión de cámaras y common a 100%**, 74 tests: 76%→79%) y ronda #16 (**settings admin a 100%**, 15 tests: 79%→80%):

| Capa | Cobertura (antes) | Cobertura (ahora) | Nota |
|---|---|---|---|
| `alpr/` | 64% (813 stmts) | **95%** (813 stmts) | preprocessor 100%, runner 64%, **ocr_engine 98%**, **video_streamer 100%**, **ws_client 100%** |
| `routes/` | 57% (2010 stmts) | **77%** (2010 stmts) | auth 100%, **video.py 100%**, **cameras.py 100%**, **common.py 100%**, **settings.py 100%**, webhook MP 90%, branches 76%, status 84% |
| `services/` | 78% (3109 stmts) | **78%** (3109 stmts) | payments 100%, access_service 89%, occupancy 91%, worker 66%, billing 73% |
| `repositories/` | 78% (777 stmts) | **78%** (777 stmts) | branch 98%, access_log 85% |
| `core/` | 75% (335 stmts) | **77%** (335 stmts) | security 85%, database 87% |
| `routes/views.py` | 74% | 74% | Renderizados base cubiertos |

Zonas por encima del 85%: `access_service` (89), `branch_repository` (98), `oauth_service` (89), `branch_service` (89), `access.py` route (89), `occupancy_service` (91), `time_service` (90), `user_notification_service` (91), `mercadopago.py` route (90), `vehicles.py` (89), `config` ALPR (95), `limiter/mqtt/logger/time` (100), `access_log_repository` (85), **`routes/auth.py` (100)**, **`services/payments.py` (100)**, **`alpr/preprocessor.py` (100)**, **`alpr/video_streamer.py` (100)**, **`alpr/ws_client.py` (100)**, **`alpr/ocr_engine.py` (98)**, **`routes/system/video.py` (100)**, **`routes/system/cameras.py` (100)**, **`routes/system/common.py` (100)**, **`routes/admin/settings.py` (100)**, `session_repository` (100).

**Nivel de riesgo: MEDIO→BAJO.** Los flujos de seguridad cobrados en A1 tienen red de protección (webhook MP 90%, pay-stay 89%, toggle-block/users 65%, security 85%, workers 66%, access_service 89%, branches/status 76/84%) y el pipeline ALPR completo quedó cubierto (preprocessor/OCR/streaming/video/cámaras todos ≥95%). El grueso que queda sin cubrir es negocio de management y reconocimiento: **balance (32%), promotions (31%), health (37%), support admin (57%), fidelization (47%)**.

---

## 2. Ranking de cobertura por módulo (< 60%)

Peor → mejor (post ítems #1–#10):

| Módulo | Stmts | Miss | Cobert. | Crítico |
|---|---:|---:|---:|---|
| `core/seed.py` | 51 | 51 | **0%** | No (utilidades) |
| `routes/admin/promotions.py` | 64 | 44 | **31%** | Media |
| `routes/user/balance.py` | 62 | 42 | **32%** | **SÍ** — dinero |
| `routes/system/health.py` | 67 | 42 | **37%** | Media |
| `routes/user/support.py` | 56 | 33 | **41%** | Media |
| `routes/user/fidelization.py` | 118 | 62 | **47%** | Media |
| `routes/admin/virtual_time.py` | 64 | 32 | **50%** | Media |
| `repositories/points_repository.py` | 12 | 6 | **50%** | Media |
| `repositories/system_repository.py` | 12 | 6 | **50%** | Media |
| `routes/admin/support.py` | 37 | 16 | **57%** | Media |
| `repositories/promotion_repository.py` | 22 | 9 | **59%** | Media |

Módulos que **superaron** el umbral del 60% en la ronda #16: `routes/admin/settings.py` (21→**100%**).

Módulos que **superaron** el umbral del 60% en la ronda #15: `routes/system/cameras.py` (17→**100%**), `routes/system/common.py` (59→**100%**).

Módulos que **superaron** el umbral del 60% en la ronda #14: `alpr/ocr_engine.py` (56→**98%**).

Módulos que **superaron** el umbral del 60% en la ronda #13: `routes/system/video.py` (24→**100%**), `alpr/video_streamer.py` (18→**100%**), `alpr/ws_client.py` (24→**100%**).

Módulos que **superaron** el umbral del 60% en la ronda #12: `alpr/preprocessor.py` (25→**100%**).

Módulos que **superaron** el umbral del 60% en la ronda #11: `routes/auth.py` (37→**100%**), `services/payments.py` (43→**100%**).

Módulos que **superaron** el umbral del 60% en la ronda #7–#10: `services/access_service.py` (38→**89%**), `routes/admin/branches.py` (19→**76%**), `routes/parking/status.py` (23→**84%**), `core/database.py` (35→**81%**), `services/occupancy_service.py` (90→**91%**), `services/branch_service.py` (→**88%**), `repositories/branch_repository.py` (→**98%**). En la ronda #1–#6: `alpr/runner.py` (0→**64%**), `services/worker_service.py` (44→**66%**), `routes/admin/users.py` (54→**65%**), `routes/user/mercadopago.py` (34→**90%**), `routes/parking/access.py` (→**89%**), `core/security.py` (54→**81%**).

El HTML navegable completo quedó en `coverage_html/` (índice por archivo, incluye los módulos con saltos por línea).

---

## 3. Cruce con flujos críticos

### 3.1 ALPR (reconocimiento, consenso, cooldown, hallucination) — **[MEDIO→BAJO, 95%]**
`test_alpr_pipeline.py` cubre por primera vez el pipeline real: **runner→consenso→cooldown→event_out** (runner 64%, ocr_engine 56%, config 95%): arranque fatal de VideoStreamer, bucle principal en modo ENTRADA, consenso de `CONSENSUS_REQUIRED` votos, descarte de frames en negro, debounce de `send_event`, y corrección posicional `CorregirPatente`. En la ronda #12, **`tests/test_preprocessor.py` (36 tests) lleva `alpr/preprocessor.py` a 100%**: `identify_country` (patentes MERCOSUR por país, DESCONOCIDO), `detect_motion` (FORCE_OCR, frames iguales/diferentes), `preprocess_for_screen`, `_iou`/`_is_valid_plate_roi` (área/aspect/ancho), `find_plate_roi` (múltiples ROI fijos, filtros de contorno por área/aspect/ancho, dedupe por IoU, tope de 10 candidatos, fallback al ROI principal, bloque `except` de findContours), `is_mercosur_candidate` (franja azul HSV, ROI vacía/grayscale) y `crop_below_blue` (recorte real, franja en la mitad inferior, resto pequeño, `np.where` vacío, grayscale). En la ronda #13, **`test_video_streamer.py` (12 tests) y `test_ws_client.py` (5 tests) llevan la captura y el envío de video a 100%**. En la ronda #14, **`tests/test_ocr_engine_detallado.py` (55 tests) lleva `alpr/ocr_engine.py` de 56% a 98%**: import de motores con fallbacks (RapidOCR/PaddleOCR/QR monotizados vía recarga de módulo), sensores de frames vacíos/None, `CorregirPatente`, `flush_queue`, `detect_motion`, `_ocr_single_roi` (redimensionado, ROI nula), controlador de lecturas (textos vacíos, rotación, Mercosur, formato de 6 caracteres, combinación de dos fragmentos), prioridades por confianza con votos, fallback a `find_plate_roi` (éxito y error), reconocimiento de motos (descartada/aceptada/confianza baja/aspecto ancho), overlay y `send_event`. Solo quedan 8 líneas muertas (rama de prioridad sin doble check y su `except`, ambos irreproducibles).

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

### 3.7 Streaming de video (WS de nodos y espectadores) — **[ALTO→BUENO, 100%]**
`tests/test_video_routes.py` (30 tests) lleva `routes/system/video.py` a 100%: el WebSocket `/ws/video/{camera_id}` con nodos ALPR (secreto en tiempo constante o red local/privada, cierre 4403 no autorizado) y espectadores (rol STAFF+ sin token → 4403; staff de otra sucursal → 4003; admin con `last_frames` recibido), `_is_local_or_private`/`_is_trusted_alpr_node`, `/update-frame` (nodo autorizado, sin imagen, 403), `/video-feed` MJPEG (frame real, sin frame, 403 por sucursal) y `/capture/{log_id}` (token por query o Bearer, 401/403/404, imagen y fallback a logo), incluido el `except` de resolución de usuario y el `except` del bucle del nodo. `alpr/video_streamer.py` (12 tests, 100%): `__init__` con source HTTP (CAP_FFMPEG + timeouts) o local, `start()` en hilo daemon, `_update` con reescalado/reintentos/excepción, `get_frame` (copia) y `stop`. `alpr/ws_client.py` (5 tests, 100%): envío de frames JPEG en base64 con/sin overlay, frames vacíos, error de procesamiento (corta el bucle interno) y reconexión tras error de conexión.

### 3.8 Gestión de cámaras ALPR y servicios de video — **[ALTO→BUENO, 100%]**
`tests/test_cameras_routes.py` (74 tests) lleva `routes/system/cameras.py` de 17% a 100% y `routes/system/common.py` de 59% a 100%: configuración de fuente por gate (`GET/POST /camera-config`, permisos por sucursal para staff, creación/actualización de `Settings` `CAMERA_SOURCE_*`), control del servicio ALPR por gate y por cámara dinámica (start con `GATE_TYPE` qr/entrada/salida por prefijos, `subprocess.Popen` + hilo de consola, error de fork; stop con taskkill en Windows o terminate en POSIX, proceso ya terminado, excepción, acción inválida), CRUD de cámaras (admin ve todas/staff filtra por sucursal, create con sucursal forzada para staff, update con `is_running`, delete que mata el proceso), `_schedule_async` (loop corriendo/no corriendo/sin loop/excepción), `_stream_console_output` (líneas reenviadas al WS de video, líneas vacías, decode con reemplazo, error de lectura, `finally` con stdout no asignable) y `notify_camera_reading` (sucursal matcheada vía BranchRepository, sin match → GLOBAL, excepción del repo, gate sin guion bajo). De bonus, `stop_all_cameras` y los `broadcast_console`/`broadcast_frame`/`disconnect` de `ConnectionManager` quedaron a 100%.

### 3.9 Settings admin (parametrización y aforo) — **[ALTO→BUENO, 100%]**
`tests/test_admin_settings.py` (15 tests) lleva `routes/admin/settings.py` de 21% a 100%: `GET /settings` (admin global ve settings globales y el aforo global; local_admin ve solo los de su sede con `sucursal_nombre`; sin aforo no hay claves de capacidad; `getattr` fallbacks de un aforo incompleto) y `POST /settings/prices` (claves de capacidad crean `ParkingAforo` con defaults si no existe, actualizan el existente sin duplicar, re-suma `capacidad_reservas` desde autos/motos/camionetas, notificación de ocupación con y sin excepción, settings por sede/global con `ttl_cache.invalidate("rate_")`). El rol se valida con el `get_local_manager` real vía `DependencyOverride` sobre `get_current_user` (staff → 403 "gestión administrativa").

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
| 13 | Alta | Preprocesamiento ALPR: recognizer de país MERCOSUR, motion, find_plate_roi, mercosur, crop_below_blue | `alpr/preprocessor.py` | 25% | **100%** ✅ |
| 14 | Alta | Streaming ALPR: captura con reintentos/reescalado y envío WS con overlay y reconexión | `alpr/video_streamer.py` + `alpr/ws_client.py` | 18%/24% | **100%/100%** ✅ |
| 15 | Alta | WS de video (fix A1 P0-2): nodos ALPR por secreto/red, espectadores por sucursal, update-frame, video-feed y capture | `routes/system/video.py` | 24% | **100%** ✅ |
| 16 | Alta | OCR en profundidad: import de motores, lectura de frames (PaddleOCR/RapidOCR/QR), consenso por prioridad, combinación de fragmentos, motos y dispatch al backend | `alpr/ocr_engine.py` | 56% | **98%** ✅ |
| 17 | Alta | Gestión de cámaras ALPR: config de fuente por gate, start/stop del servicio, CRUD con aislamiento por sucursal y aviso de lectura al dashboard | `routes/system/cameras.py` + `routes/system/common.py` | 17%/59% | **100%/100%** ✅ |
| 18 | Alta | Settings admin: parametrización por sede/global, capacidades de aforo con creación automática y re-suma de reservas | `routes/admin/settings.py` | 21% | **100%** ✅ |

Los ítems 5 y 6 eran los más urgentes (regresiones directas sobre fixes de seguridad de A1) y quedaron cerrados. Los ítems #7–#10 ya están escritos y en verde (79 tests nuevos). En la ronda #11 se cerraron los ítems #11–#12 (61 tests nuevos: `test_payments.py` 37 + `test_routes_auth.py` 24), en la #12 el ítem #13 (`test_preprocessor.py`, 36 tests), en la #13 los ítems #14–#15 (47 tests nuevos: `test_video_streamer.py` 12 + `test_ws_client.py` 5 + `test_video_routes.py` 30), en la #14 el ítem #16 (`test_ocr_engine_detallado.py`, 55 tests), en la #15 el ítem #17 (`test_cameras_routes.py`, 74 tests) y en la #16 el ítem #18 (`test_admin_settings.py`, 15 tests). Próximos candidatos por impacto: **balance (32%), promotions (31%), health (37%), support admin (57%), fidelization (47%)**.

---

## 5. Umbral mínimo en CI

`ci.yml.disabled` (v11): corre en ubuntu `python 3.11`, ejecuta `python scripts/patch_bidi.py` (script **eliminado**) y `alembic upgrade head` (falla en BD vacía, ver A4.1). **No reactivar tal cual.**

Opciones para reactivar CI:
- Correr en `ubuntu-latest` con `python 3.14` (venv local es 3.14.7).
- Reemplazar `patch_bidi.py` por el flujo de inicialización único `init_db.py` (o `sync_schema()`).
- Agregar `--cov-fail-under=80` (cobertura actual 80%). El umbral puede subir por PR a 85.
- No correr `alembic upgrade head` desde cero: usar `python init_db.py`.

Recomiendo reactivar CI con `--cov-fail-under=80` al mergear esta ronda.

---

## 6. Checklist de Cierre

| Ítem | Estado |
|---|---|
| `pytest-cov` + `coverage` instalados | ✔ |
| `pytest --cov=... --cov-report=html` ejecutado (**80% total, 557 passed**) | ✔ |
| Reporte HTML navegable generado (`coverage_html/`) | ✔ |
| Ranking por módulo (< 60%) documentado | ✔ |
| Cruce con flujos críticos (ALPR, workers, payments, oauth, WS, admin) | ✔ |
| Lista priorizada "primeros 10 tests" elaborada | ✔ |
| Umbral mínimo en CI evaluado (`ci.yml.disabled` desactualizado, no reactivar tal cual) | ✔ |
| Tests de la lista #1–#6 escritos y en verde | ✔ |
| Tests de la lista #7–#10 escritos y en verde | ✔ |
| Tests de la lista #11–#12 escritos y en verde (payments y auth a 100%) | ✔ |
| Tests de la lista #13 en verde (preprocessor ALPR a 100%) | ✔ |
| Tests de la lista #14–#15 en verde (streaming y WS de video a 100%) | ✔ |
| Tests de la lista #16 en verde (ocr_engine a 98%) | ✔ |
| Tests de la lista #17 en verde (cameras y common a 100%) | ✔ |
| Tests de la lista #18 en verde (settings admin a 100%) | ✔ |

---

## 7. Notas de ejecución

- La suite usa la BD SQLite temporal por test (patrón habitual del repo), 557 passed en 45–55s.
- Tests nuevos ronda #1–#6: `test_alpr_pipeline.py` (14), `test_worker_cleanup.py` (7), `test_mercadopago_webhook.py` (10), `test_toggle_block.py` (6), `test_pay_stay.py` (5) → 38 tests.
- Tests nuevos ronda #7–#10: `test_access_flow.py` (33), `test_admin_branches.py` (21), `test_status_ws.py` (16), `test_core_database.py` (9) → 79 tests.
- Tests nuevos ronda #11: `test_payments.py` (37) + `test_routes_auth.py` (crecido a 24, antes 2) → 61 tests. `test_payments.py` usa el patrón StaticPool + `sessionmaker` del repo; `test_routes_auth.py` reutiliza el fixture de `test_pay_stay.py` (engine SQLite en memoria por test, `dependency_overrides` guardado/restaurado y `limiter.reset()`).
- Tests nuevos ronda #12: `test_preprocessor.py` (36) → 36 tests. `identify_country` cubre patentes MERCOSUR de Argentina/Brasil/Uruguay/Paraguay/Otros + DESCONOCIDO; `detect_motion` exige parchear `preproc.FORCE_OCR=False` (el `from alpr.config import FORCE_OCR` enlaza el valor a `alpr.config` en el import del módulo, hay que patchear el atributo del módulo); los asserts de `detect_motion`/`is_mercosur_candidate` devuelven `np.True_`/`np.False_` (usar truethiness, no `is True`); `_iou` de contención es `área_interna/área_externa` (0.64), no 1.0; `find_plate_roi` llega al tope `len(merged) >= 10` con un frame de 2200 px (6 segmentos de cinta × 2), y las ramas defensivas (`except` de findContours/cvtColor y `np.where` vacío) se disparan con `monkeypatch` sobre `preproc.cv2.findContours`, `preproc.np.where` y ROIs en escala de grises 2D.
- Tests nuevos ronda #13: `test_video_streamer.py` (12) + `test_ws_client.py` (5) + `test_video_routes.py` (30) → 47 tests. `VideoStreamer` se prueba sin hilos: se monkeypatchea `threading.Thread` para `start()` y se llama `_update()` directo con un `VideoCapture` falso (las respuestas de `read()` deben ser tuplas `(ret, frame)`). `ws_monitoring_worker` se testea con `asyncio.run`, un `websockets.connect` falso (soporta lanzar en las primeras conexiones) y `asyncio.sleep` no-op. **Importante:** `import routes.system.video` falla como statement (`routes/__init__.py` reasigna `system` al APIRouter); hay que usar `importlib.import_module("routes.system.video")` (mismo patrón que `test_status_ws.py`). El WebSocket de video se testea con `TestClient.websocket_connect` + `dependency_overrides`/monkeypatch del token; el MJPEG `/video-feed` devuelve un `body_iterator` **async** (consumir en un único `asyncio.run`); `manager.disconnect` deja la clave con lista vacía (no borra el dict).
- Tests nuevos ronda #14: `test_ocr_engine_detallado.py` (55) → 55 tests, `ocr_engine.py` 56→98%. Sin `conftest.py`/`tests/__init__.py`: cada test file duplica sus helpers (`FakeReader`, `FakePaddleReader`, `FakeQRDetector`, `_make_engine`, `_run_worker` con `time.sleep` parcheado y frames encolados, `_wait_for`, `_stop_worker`). **Lectores:** `reader.result()` debe devolver tuplas `(texts, scores, polys)` y `get_boxes`/`det` formas numpy consistentes. **Import con fallbacks:** para cubrir los fallos de import (rapidocr→paddle→QR→detección de pdm) se usan módulos falsos en `sys.modules` (nombre a `None` para "no instalado", objeto con atributos para instalado) y `importlib.reload(ocr_engine)` dentro de un context manager `_scenario`. **Globales de módulo:** los flags de `config` se monkeypatchean como atributos de `ocr_engine` (`ocr_engine.ENABLE_MOTO_RECOGNITION`, `ocr_engine.LATAM_PLATE_PATTERN`, etc. — el import `from alpr.config import X` enlaza el valor al módulo destino). **Consenso por prioridad:** hay que entregar textos concretos para que cada prioridad tome la rama (p. ej. 6 caracteres `ABC123` → prioridad 1 por `match_6`, Mercosur con X → prioridad 4, dos fragmentos → combinación prioridad 4). **`_ocr_single_roi` override:** debe devolver tupla de 3 (`texts, scores, polys`). **Worker:** `dispatch` en `send_event` recibe `*args` (envolver en `lambda *a, **k: dispatched.append(a)`); para cubrir el flujo vice-versa se parchea `ocr_engine.REQ_VOTES=1`. `CorregirPatente` normaliza previo a los matches: un texto bruto 6-char que coincida con `LATAM_PLATE_PATTERN` custom puede ser reescrito como patente clásica válida antes de llegar a `is_valid_format` (p. ej. `AB1234`→`ABI234`); usar textos que sobrevivan intactos (`A1B2C3` para el corte de `is_valid_format`, `AB123456` para el de longitud).
- Tests nuevos ronda #15: `test_cameras_routes.py` (74) → 74 tests, `routes/system/cameras.py` 17→100% y `routes/system/common.py` 59→100% (bonus). Patrón de fixture: app FastAPI standalone con `cam.router`, override de `cam.get_db` (SQLite `StaticPool` + `create_all`) y `cam.get_operational_user` (lambda que devuelve el usuario global `CURRENT["user"]`, cambiada por helper `_set_staff`); `CAMERA_PROCESSES` se limpia en setup/teardown del fixture. Para arrancar/detener servicios se monkeypatchea `cam.subprocess.Popen` → `FakeProc` (captura `env`, `poll()` configurable con None/exit/exception), `cam.threading.Thread` → `FakeThread` (sin hilos reales: `start()` no-op) y `cam.subprocess.call` + `cam.os.name='nt'/'posix'` para las ramas taskkill/terminate. La consola del subproceso se testea llamando `_stream_console_output` directo con un `FakeStream` cuyo `readline` devuelve líneas hasta `b""` (o lanza). `_schedule_async` se fuerza con `NotificationService._loop` = `FakeLoop` (`is_running` True/False/excepción) y `asyncio.run_coroutine_threadsafe` parcheado. **Importante:** no usar `--cov=routes.system.cameras` (pytest-cov importa el paquete `--cov` dos veces y bcrypt/PyO3 revienta "may only be initialized once"); medir con `--cov=routes` y filtrar la fila. `_stream_console_output` setea `proc.stdout=None` en `finally`, así que `FakeStream.close()` debe ser inofensivo y el `except` defensivo (56-57) se cubre con una property `stdout` no asignable. El `proc_id` se arma `{sucursal_norm}_{TIPO}_{id}.upper()`: al renombrar vía PUT el id cambia, por lo que el proceso "corriendo" debe registrarse bajo el proc_id posterior al update.
- Tests nuevos ronda #16: `test_admin_settings.py` (15) → 15 tests, `routes/admin/settings.py` 21→100%. Se valida el rol con el `get_local_manager` real (core/security) vía `dependency_overrides` sobre `get_current_user` (lambda que devuelve el usuario global `CURRENT["user"]`), así el 403 "Requiere permisos de gestión administrativa" sale de la lógica productiva. **Ojo con `str` en enums:** `UserRole` es `str, Enum`, así que `isinstance(rol, str)` es True y hay que convertir a `.value` usando `isinstance(rol, UserRole)`; además `str(UserRole.ADMIN)` en Python 3.11+ da `"UserRole.ADMIN"`, no `"admin"` (el FakeUser debe guardar el `.value`). Como `CURRENT["user"]` persiste entre tests, `_reset_user` autouse restaura el admin por defecto (misma causa raíz que la contaminación vista en cameras). Las claves de capacidad (`capacidad_*`) crean/actualizan `ParkingAforo` (con defaults vía `getattr`), re-suman `capacidad_reservas` y disparan `notify_occupancy_change` (classmethod; se monkeypatchea con `classmethod(lambda cls, db, s: ...)` y se cubre la rama que lanza). Los settings por sede se guardan con `sucursal_norm` real (ej. "Centro") y el `ttl_cache.invalidate("rate_")` se ejecuta en cada update.
- El flujo login multi-dispositivo exige UserSession con `last_login_at` dentro de la ventana (`ACCESS_TOKEN_EXPIRE_MINUTES`, 1440) para que `count_other_devices`/`get_recent_by_user_agent` matcheen; y los redirects OAuth (`303` a `/#fragment`) se prueban con `follow_redirects=False`, decodificando el fragmento con `urllib.parse.unquote`.
- Detalle importante: en endpoints con `TestClient` hay que usar `create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)` — `sqlite:///:memory:` crea BD por conexión y los requests corren en otro thread (aparece "no such table"). Ya aplicado en los archivos HTTP nuevos.
- El WebSocket de aforo **sí es testeable** con `TestClient.websocket_connect` en este stack (starlette/CPython 3.14): se parchean `status.decode_access_token`, `status.UserRepository.get_by_email` y `status.get_db` (el endpoint usa `next(get_db())`, no `Depends`, por lo que `dependency_overrides` no aplica).
- En tests del ALPR, `FORCE_OCR=True` hace short-circuit y **no** llama a `detect_motion`; y con `monkeypatch time.sleep` a no-op los sincronismos deben esperar estado final (`_wait_for`) y no dormir.
- En tests de `access_service` el tiempo se fija monkeypatcheando `TimeService.now` (classmethod); la barrera se verifica monkeypatcheando `services.hardware_service.HardwareService.trigger_barrier`.
- Los `ResourceWarning: unclosed database` (report_service, sqlalchemy internals) son avisos de sesiones sin cerrar — no afectan resultados, pendientes de limpieza futura.
- El HTML de cobertura fue generado con `--cov-report=html:coverage_html` (directorio `coverage_html/` en la raíz), no commiteado.