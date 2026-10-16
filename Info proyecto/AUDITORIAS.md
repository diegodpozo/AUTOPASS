# Auditorías de AUTOPASS — Documento Consolidado

> **Estado global: A1–A9 CERRADAS** con remediación aplicada y verificada (última ronda 2026-09-30, suite **756 passed**, cobertura **93%**). Auditorías transversales resueltas (modularización, colores/fuentes, tamaños/proporciones, nomenclatura, componentes, UX/UI). Propuestas CSS: AC-1, AC-2 y AC-4 cerradas; **AC-5 CERRADA (Lotes 1, 2, 7 y 9: 0 clases huérfanas, 0 keyframes duplicados, −15 tokens, −1247 líneas netas)**; **AC-3 CERRADA (2026-09-29: `viewport-fit=cover` + 4 tokens `--safe-area-*` en 11 superficies, `overscroll-behavior-y: contain` en 3 contenedores; touch targets ≥44px descartado por no aplicar)**. **No queda ninguna auditoría CSS abierta de esta tanda.** Pendiente explícito único backend: mediciones con volumen real de Neon (no disponible).

Este documento reemplaza a los informes individuales `AUDITORIA_*.md`, `PLAN_AUDITORIAS.md` y `PROPUESTA_AUDITORIAS_CSS.md` (eliminados 2026-09-27, v9.34.50). Reúne lo más importante de cada auditoría: hallazgos, remediación, verificación y herramientas reutilizables.

---

## Resumen de Auditorías

| # | Auditoría | Prioridad | Esfuerzo | Riesgo que mitiga | Estado |
|---|-----------|-----------|----------|-------------------|--------|
| A1 | Seguridad de la API | Alta | 1–2 días | Exposición, abuso de endpoints, headers ausentes | ✅ CERRADA (riesgo ALTO → **BAJO**) |
| A2 | Dependencias y Supply Chain | Alta | 0.5–1 día | CVEs en OCR y librerías | ✅ CERRADA (8 CVEs → **1 sin fix no explotable**) |
| A3 | Cobertura de Tests | Alta | 1 día | Gaps en ALPR, workers, views | ✅ CERRADA (**82%**, CI sugerido `--cov-fail-under=82`) |
| A4 | Datos / Migraciones (SQL) | Alta | 1 día | Alembic roto entre Neon y SQLite | ✅ CERRADA (upgrade reproducible, 0 migraciones con data) |
| A5 | Rendimiento (profiling) | Media | 1–2 días | N+1 en dashboard, tickets, resevas | ✅ CERRADA (hot spot O(N²) 217s→1.86s; P1+P2 medidos) |
| A6 | Consistencia Frontend/Backend | Media | 1 día | JS llama rutas inexistentes | ✅ CERRADA (11 rutas front, **0 faltantes**) |
| A7 | Errores y Manejo de Excepciones | Media | 0.5 día | Excepciones cegadas, internals filtradas | ✅ CERRADA (0 `except:` desnudos; 17 bloques instrumentados) |
| A8 | Accesibilidad / UX | Baja | 1 día | Contraste, foco, labels | ✅ CERRADA (contraste `#F2E3BF`, foco global, autofocus) |
| A9 | Seguridad Frontend (XSS) | Baja | 0.5 día | innerHTML sin sanear | ✅ CERRADA (177 innerHTML / **0 XSS explotable**) |
| AN | Nomenclatura de Archivos | Media | 1 día | Espacios y casing rotos | ✅ CERRADA (8.2→**9.0/10**, P0/P1 aplicadas) |
| T | Transversales (UI/CSS/JS) | — | — | Deuda de estilo y código | ✅ Resueltas (ver sección Transversales) |

---

## A1 — Seguridad de la API

**Cierre:** 2026-09-20 (P0/P1) + 2026-09-24 (P2/P3) + deuda de auth de nodo ALPR. **Riesgo general: ALTO → MEDIO → BAJO.** Suite 694 passed al cierre.

**Hallazgos críticos originales (2026-09-19):**
- `POST /access/pay-stay` **público**: un tercero podía marcar pagada una estadía ajena.
- Video WS `/ws/video/{id}` + `POST /update-frame/{camera_id}` **anónimos**: suplantación de video (spoofing) y saturación del feed.
- `get_current_user` no rechazaba `is_blocked` → el toggle-block no invalidaba tokens vigentes (24 h).
- **0 headers de seguridad** (sin CSP, HSTS, XFO, nosniff, Referrer-Policy).
- CORS `*`, WS de ocupación con token en query sin rol operativo.

**Remediación aplicada (checklist cerrado):**
1. `pay-stay` → `Depends(get_operational_user)` + `@limiter.limit("10/minute")` (`routes/parking/access.py`).
2. Nodos ALPR (`validate-plate`/`exit-plate`/`validate-qr`) → `Depends(require_alpr_node)` (`core/alpr_security.py`): header `X-Node-Secret` en tiempo constante o red local/privada; el nodo lo envía desde `alpr/ocr_engine.py:_dispatch_request`. Test: `test_alpr_node_auth.py`.
3. `get_current_user` → 403 si `is_blocked` (`core/security.py:71,107`); login bloqueado; mercadopago/reservas validan también.
4. `security_headers_middleware` en `main.py:72-101`: CSP (con CDNs/fuentes/mapas), HSTS, `X-Frame-Options: DENY`, `nosniff`, Referrer-Policy. Test: `test_security_headers.py`.
5. JWT con `iat`/`jti`/`token_type` + blacklist en memoria (`revoke_token`); guard de arranque que falla si `SECRET_KEY` es el demo en producción.
6. `POST /v1/auth/logout` revoca jti + borra `UserSession` del device; `ui.logout` lo invoca.
7. CORS con lista explícita por entorno (default localhost, sin `*`) (`core/config.py`).
8. Rate limits finos: `pay-stay` 10/min, webhook MP 60/min, mutadores admin 30/min (`admin_rate_limit` en `core/limiter.py`).
9. Sin PII en logs INFO: `mask_email()` en WS/workers/email; MP ya no loguea `resp.text[:500]`.

**Buenas bases ya presentes:** JWT HS256 forzado, BCrypt, **0 inyección SQL** (0 `text()/exec_driver_sql/raw`, todo por repositorios con binds SQLAlchemy).

**Herramienta:** OWASP API Top 10 checklist.

---

## A2 — Dependencias y Supply Chain

**Cierre:** 2026-09-19 (bumps P1) + P2 coordenado (starlette major). **pip-audit final: 1 vuln (ecdsa, sin fix, no explotable).** 8 paquetes con CVEs detectados (3 directos + 5 transitivos).

| Paquete | De → A | CVEs | Nota |
|---|---|---|---|
| starlette | 0.52.1 → **1.6.0** | 5 → 0 | P2: salto mayor requerido por todos los fixes (BadHost/DoS); fastapi 0.141.1 + slowapi 0.1.10 acompañan (no pinnean tope) |
| python-multipart | 0.0.22 → **0.0.31** | 5 → 0 | DoS de parsing multipart |
| cryptography | 46.0.5 → **50.0.1** | 6 → 0 | El crítico 9.8 (RCE) se cubrió con 46.0.7; 50.0.1 suma PKCS#7/wildcard/OpenSSL |
| ecdsa | 0.19.2 | 1 (Minerva) | **SIN FIX**; transitoria de `python-jose` y el proyecto **solo usa HS256** → no explotable. A futuro: evaluar PyJWT |
| idna / requests / click | bumps patch | 1 c/u | Bajo; sin superficie de red |

**También:** `pip check` limpio (0 deps rotas); inconsistencia numpy requirements↔venv resuelta reinstalando a 2.4.6; coexistencia `opencv-python` + `headless` OK.

**Herramientas:** `pip-audit`, `pip check`, OSV API (`api.osv.dev/v1/vulns/{id}`), PyPI JSON.

---

## A3 — Cobertura de Tests

**Cierre:** rondas #1–#22 (2026-09-21). **82% total** (7.044 stmts / 1.261 sin cubrir); de 55% inicial. Suite 609+ passed. Umbral CI sugerido: `--cov-fail-under=82`.

**Revisión 2026-09-30 (v9.34.60):** los dos gaps que quedaban declarados como "pendientes/depriorizados" están **cerrados**. Cobertura real medida: **93%** (16.318 stmts / 1.201 sin cubrir), suite **733 passed**.

**Ronda de coherencia visual (v9.34.61):** al medir el CSS en lugar de suponerlo apareció un **token inexistente**: `.barrier-text` en `dashboard-live.css:357` usaba `var(--text)`, que no existe. Los tokens ausentes no dan error — la propiedad cae en silencio a su valor heredado y el texto se ve despintado. Corregido a `var(--text-secondary)`, con dos guards nuevos que evitan la recaída: `_tools/check_css_tokens.py` (token usado sin declarar / declarado sin usar) y `_tools/check_css_design_system.py` (baseline de las 4 métricas visuales). La migración de color de equivalencias exactas (195 literales, 31 archivos) se verificó **neutral a nivel de píxel** con `_tools/check_color_equivalence.py`, que compara el multiset de RGBA resueltos contra HEAD.

**Por capa (antes → ahora):** `alpr/` 64→**95%** · `routes/` 57→**83%** · `services/` **78%** · `repositories/` **78%** · `core/` 75→**77%**.

**100% alcanzado:** `auth.py`, `payments.py`, `preprocessor.py`, `video_streamer.py`, `ws_client.py`, `video.py`, `cameras.py`, `common.py`, `settings.py`, `balance.py`, `promotions.py`, `health.py`, `session_repository`.

**Rondas destacadas:** #12 preprocessor ALPR a 100% (36 tests) · #14 `ocr_engine.py` 56→98% (55 tests) · #15 cameras/common a 100% (74 tests) · #20 `fidelization.py` →88% · #21 support user 41→100% · #22 support admin 57→100% (estos dos últimos no contabilizados en el resumen; ver `tests/test_user_support_routes.py` / `test_admin_support_routes.py`).

**Gaps cerrados (2026-09-30, v9.34.60) — los 2 pendientes declarados, resueltos:**
- `core/seed.py` **0% → 100%** con `tests/test_core_seed.py` (8 tests). Se cubrieron las 5 ramas del orquestador y, sobre todo, la **idempotencia** (que `init_db.py` puede correr más de una vez: no duplica usuarios, aforo, tarifas, promos ni sucursales), la normalización de DNI con puntos en usuarios preexistentes, y que el seed **no pisa** tarifas/aforo/promos/sucursales que el operador ya haya cargado.
- `routes/admin/virtual_time.py` **sin cobertura → 100%** con `tests/test_admin_virtual_time_routes.py` (18 tests). `test_virtual_time.py` cubría solo `services/time_service.py`; las 6 rutas de admin estaban sin test. Ahora se cubren: avance/retroceso/`set`/`reset`/`set-target`, el alias de ruta `""` vs `/status`, el **400** de fecha ISO inválida (que no debe mover el reloj), el **422** de campo faltante, el gate `get_local_manager` (**403 para staff**, admin global y local admin sí pasan) y `_run_all_checks` (tolerancia a fallos: un worker caído se loguea y la ruta sigue respondiendo; más una guarda de que los 5 workers se siguen invocando).
- El fixture de esos tests restaura `data/virtual_time_offset.json` porque `TimeService` persiste el offset en disco: sin eso, los tests dejaban el repo sucio y el estado se filtraba entre corridas.

**Sin gap:** pipeline ALPR, pagos/webhook MP, OAuth, socket de aforo, workers, streaming.

**CI — CORREGIDO (2026-09-30).** La nota anterior decía "NO reactivar tal cual" y hablaba de `ci.yml.disabled`. Hoy la realidad es otra: el workflow está **activo y en verde**, con los 3 cambios que se recomendaban ya aplicados en `.github/workflows/ci.yml`: `ubuntu-latest`, Python **3.14**, `init_db.py` en vez de `patch_bidi.py`, y `--cov-fail-under=82`. Últimas corridas verificadas en GitHub Actions: `success` en `v9.34.59` (2m8s), `v9.34.58` y `v9.34.54`. La nota era una instrucción de trabajo previa, ya ejecutada.

---

## A4 — Datos / Migraciones (SQL)

**Cierre:** P1 2026-09-19 + P2 2026-09-27. **`alembic upgrade head` REPRODUCIBLE desde BD vacía.**

**P1 aplicada:** flujo único `sync_schema()` en `core/database.py` (`create_all` de modelos + Alembic al head, con warning si la cadena no es reproducible); eliminado `init_db.py:migrate_db()` que hacía `ALTER TABLE` manuales (`is_blocked`, `capacidad_motos`, etc.) = **segunda fuente de verdad del esquema eliminada**.

**P2 aplicada (2026-09-27):**
- Baseline real en `alembic/versions/c833a3129266_initial_schema.py`: era `upgrade() -> pass`, ahora materializa 16 tablas base + índices.
- `d4f7c8e2a190` convertida a batch-mode con FK nombrada (SQLite) y `e6f7a8b9c0d1` con columnas `nullable` alineadas al modelo.
- Deuda A4.6 liquidada: eliminados los 2 "parches" de datos de `core/seed.py` (aforo `getattr` legacy y `update()` masivo de sucursales).
- **Verificado en sandbox SQLite:** BD vacía → `upgrade head` EXIT 0, 18 tablas, schema **idéntico** a `create_all` (**0 diffs** orden-insensible), `current == head`.

**Reproducibilidad:** cadena lineal de 17 migraciones, single head `9c4f2a7b1e83`; `alembic current` en Neon = head (sin pendientes; solo lectura, no se tocó prod). La última (`9c4f2a7b1e83`) **dropea la tabla `coupons`** y su índice `ix_coupons_codigo`: el modelo `Coupon` ya no existe (0 referencias en el repo) y sin ese drop la paridad modelo↔alembic que exige `tests/test_schema_parity_p2.py` quedaba rota. Su `downgrade` los recrea. **0 migraciones con data de usuario** (DDL puro; grep `op.execute|insert|update|delete|bulk` = 0). Updates legacy ("AUTOPASS " prefix) resueltos en lectura (`core/normalize.py`), no en BD.

**Nota compatibilidad:** una BD ya creada por `create_all` y sellada en head no re-ejecuta migraciones; el baseline no altera prod.

**Herramientas:** `alembic current/history/heads`; comparador de schema orden-insensible (usado también por `tests/test_schema_parity_p2.py`).

---

## A5 — Rendimiento (profiling con volumen sintético)

**Cierre:** 2026-09-27 (CERRADA ✓). **Suite 702 passed.** Metodología: sandbox SQLite aislado (`%TEMP%\a5_profiler_volume.db`, 6 sucursales, ~413 usuarios, 1.200 vehículos, 20.000 reservas, 60.600 access_logs) + hook `before_cursor_execute` para query-count. Limitación anotada: tiempos SQLite dev en-disk; el query-count sí representa el patrón N+1 real.

### Hot spot principal — CORREGIDO
`GET /v1/reports/financial-summary`: **217.3 s → 1.86 s (117×)**. Causa: `NOT EXISTS` correlacionado por entrada impaga sin índice → O(N²) (`report_repository.py:192`). Fix: índice compuesto `ix_access_logs_pat_tipo_suc_fecha` (migración `cdb7d130c856`).

### Query-count por endpoint (ronda 2026-09-27)
| Endpoint | q | tiempo |
|---|---|---|
| `/v1/parking/status` | 5 | 47 ms |
| `/v1/parking/branches` | 13 | 68 ms |
| `/v1/parking/current-occupancy` | 6 | 1.1 s |
| `/v1/admin/reservations` + cleanup | 9 + N_vencidas | 1.06 s (post-fix) |
| `/v1/reports/financial-summary` | 18 | **1.86 s** (era 217 s) |
| `/v1/user/redemption-tickets` | 452 | 347 ms (N+1 anotado, aceptable hoy) |
| WS broadcast GLOBAL/FILIAL (50 clientes) | 19/21 | ~70 ms |

### P1 remediados (v9.34.48)
| Fix | Antes | Después |
|---|---|---|
| `GET /v1/reports/access` (historial sin paginar) | **CRASH** (`too many SQL variables`, IN 60k) | **200, 104ms, 4q** — límite server-side (default 300) + dedupe de patentes (`dict.fromkeys`) |
| `cleanup_overdue_reservations` (2.500 vencidas) | 2.003 q / 1.314 ms | **4 q / 179 ms** — batch `get_reserva_ids_with_entry` (1 query) |
| `_process_auto_cancellations` (worker) | N+1 por reserva | 1 query batch `IN` |

### P2 remediados (v9.34.49)
| Fix | Antes | Después |
|---|---|---|
| Broadcast WS GLOBAL sin caché | ~950 q por 50 pushes | **19 q** (1 compute + 49 cache hits), 71 ms — caché TTL 3s `occupancy_ws_global`/`occupancy_ws_branch_{norm}` en `core/cache.py`; `force_refresh=True` solo ante cambios reales |
| `ix_{tabla}_id` redundantes sobre el PK | 18 PK con `index=True` + 2 índices reales creados por alembic | `index=True` quitado; migración `8b3e9e815c78` DROP `ix_redemption_tickets_id`/`ix_support_ticket_messages_id`; `ix_mercadopago_payments_user_id` declarado en el modelo. **Paridad índice modelo↔alembic = 0 diffs** (`tests/test_schema_parity_p2.py`) |

**N+1 anotados no remediados (aceptables):** `list_public_branches`/WS (crece lineal con sucursales, ≤6-8 OK), `redemption-tickets` (1 usuario, hotel 1-1).

**Pendiente explícito único:** mediciones con volumen real de Neon (plan gratuito sin datos).

---

## A6 — Consistencia Frontend/Backend

**Cierre:** 2026-09-27 (CERRADA ✓). **11 rutas únicas `/v1` llamadas por el front (13 ocurrencias) = 0 faltantes y 0 verbos mal usados** contra las 128 rutas backend de `app.openapi()`.

**Metodología automatizada** en `_tools/check_consistencia_frontend.py`:
```
venv\Scripts\python.exe _tools\check_consistencia_frontend.py [--json | --dump-openapi _tools\_a6_openapi.json]
```
1. Regex normalizado de `/v1/...` y `/ws/...` en `static/js/**` + `templates/**` (soporta template literals `${provider}`).
2. Normalización `{var}`→`{_}` (comparación posicional).
3. Cruce contra OpenAPI del mismo `main.app`.
4. WebSockets aparte (no figuran en OpenAPI): contra `app.routes` (autorouter custom).
5. Tabla de `response_model` por ruta.

**Rutas front:** `POST /auth/logout` · `GET /auth/oauth/{provider}/authorize` · `GET /parking/branches` · WS `/parking/ws` · `GET/SET` tiempo virtual | `/system/capture/{log_id}` · WS `/system/ws/video/{proc_id}` · `POST /admin/virtual-time/advance|rewind|set-target|reset`. Solo `BranchPublicResponse` tiene schema explícito (el resto responde JSON de acción, correcto).

---

## A7 — Errores y Manejo de Excepciones

**Cierre:** 2026-09-22 (fixes) + verificación formal 2026-09-27. **0 ocurrencias de `except:` desnudo en todo `*.py`** (grep formal, excl. venv/.git). Suite 695 passed al cierre.

**Informe base (2026-09-22):** 11 bloques `except Exception:` en services (access ×5, availability ×2, billing ×2, branch, mercadopago), 10 sin logger → **indebuggeable en prod**.

**Aplicado (v9.34.14):** los 10 bloques quedaron instrumentados con `logger.X(msj, exc_info=True)`; el scan completo de `services/` detectó además **7 `except Exception: pass` realmente ciegos** fuera del alcance original (payments, reservation, user, worker) → `logger.warning(..., exc_info=True)` y se agregó `core/logger.py` a `payments.py`/`user_service.py`. Los `except HTTPException|ValueError|JWTError|RuntimeError|ImportError` restantes son control de flujo intencional (no ciegos).

**Sin fuga de internals:** cero `detail=` con stack/SQL/paths en rutas (auth 401/403; webhook MP 200 echo/400 firma; reservas 400/404/409; admin 403 local vs global; fidelización 400/404). Sin 500 sin mapear.

---

## A8 — Accesibilidad / UX

**Cierre:** 2026-09-22 (v9.34.15). **Riesgo BAJO.** Los fixes ya estaban aplicados en versiones previas (P0.1/P0.2/P2.6 de UX/UI).

**Contraste (WCAG 1.4.3 AA ≥ 4.5:1):** el dorado institucional `#C5A059` s/ blanco = ~2.7:1 y s/ violeta `#6A4B9B` = ~1.3:1 → **NO</bendre**. Solo estaba en 2 archivos: `profile-base.css:575` y `profile-reservations.css:221`. **Fix:** texto institucional → `#F2E3BF` (violeta ~5.5:1); `#C5A059` queda solo en bordes/íconos decorativos. Verificado: **0 `#C5A059` en CSS**.

**Foco visible (2.4.7):** solo 1 de 42 CSS tenía `:focus-visible`. **Fix:** `:focus-visible { outline: 2px solid #6A4B9B; outline-offset: 2px; }` global (`profile-base.css:526`, branding violeta).

**Labels (1.3.1):** 176 labels/aria-labels vs 139 inputs (ratio 1.27 > 1) ✓; inputs clave con `for=id`.

**Autofocus (2.1.1):** `ui.js:27-31` enfoca el primer campo editable al abrir cualquier modal + `autofocus` HTML en login (`auth_modals.html:23`) y recarga saldo (`modals.html:146`).

**Touch target (2.5.5):** botones principales ≥44px ✓; `.btn-icon-premium.sm` en mobile con padding ≥40px a verificar en audit CSS (AC-4/AC-3).

---

## A9 — Seguridad Frontend (XSS)

**Cierre:** 2026-09-22 + verificación automatizada 2026-09-27 (`_tools/check_xss_innerhtml.ps1`). **Cero XSS explotable.**

**Métrica bruta:** 177 `innerHTML=`/`insertAdjacentHTML(` en `static/js/**` → ~155 estáticos sin riesgo · 22 interpolaban variables (informe base) · **3 con origen usuario/server review**.

**Veredicto de las 3:** ninguna ejecuta `javascript:` (sin `onerror`/`onload`/`onclick` en el mismo tag; los mensajes de soporte se renderizan por `textContent`).

**Fixes aplicados (v9.34.16):**
- `escapeHtml` centralizado y exportado en `static/js/modules/utils.js` (guarda `'`), reemplaza 3 usos locales/inseguros.
- `dashboard-tickets.js:179` — `href` de `adjunto_url` → `escapeHtml(encodeURI(...))` (único con `href` interpolado; MEDIO). También `m.mensaje`, `label` y `adjunto_nombre` escapados.
- `landing-map.js:203` — `p.nombre` en overlay → `escapeHtml`.
- `monitoreo-live.js:44` — `b.nombre` en `<option>` → `escapeHtml` (se eliminó el `escapeHtml` local duplicado, DRY).

**Verificación 2026-09-27 (automatizada):** 177 total · 25 interpoladas (3 rutas nuevas de Reservas/Looper/tour, todas server-side o derivadas) · 23 candidatas sin escape en la misma línea → revisadas manualmente, todas de origen no-usuario (estados de servidor, nombres de BD admin-only, números) → **0 vectores `javascript:` nuevos**.

**Herramientas:** `_tools/check_xss_innerhtml.ps1` (scan estático, add-only, sin ejecutar en CI).

---

## AN — Nomenclatura de Archivos

**Cierre:** 2026-09-27, remediación P0/P1 (v9.34.42). **Calificación 8.2 → 9.0/10.** Alcance: 334 archivos. Suite **695 passed** post-remediación.

**P0 (espacios) renombrados con `git mv` + referencias actualizadas:**
- `static/images/barrera alta.png` → `barrera-alta.png` / `barrera baja.png` → `barrera-baja.png` (refs en `dashboard-admin-settings.js` ×2, `live.html` ×2, `settings_system.html`).
- Documentación: `Link Backlog.md` → `LINK_BACKLOG.md` · `explicacionCodigo.md` → `EXPLICACION_CODIGO.md` · `Readme.md` → `README.md` · `Hardware/` → `hardware/`.

**P1 (casing) unificados:**
- JS a kebab-case: `chart_window.js`→`chart-window.js` · `estadisticas_ocr.js`→`estadisticas-ocr.js` · `onboarding_helpers.js`→`onboarding-helpers.js` · `reset_password.js`→`reset-password.js`.
- CSS a kebab-case: `virtual_time.css`→`virtual-time.css` · `chart_window.css`→`chart-window.css` · `estadisticas_ocr.css`→`estadisticas-ocr.css`.
- Template `nuestra-red.html` → `nuestra_red.html` (la ruta `/nuestra-red` no cambia).

**P2 (spanglish lingüístico) = deuda técnica aceptada:** `perfil.html`, `reservas*.js`, `vehiculos.html`, `monitoreo_live*` son módulos vivos con imports internos; renombrarlos implica refactor de todos los enlaces con riesgo alto de regresión (criterio funcional sobre cosmético). Regla de nomenclatura ya incorporada a `AGENTS.md`.

---

## Transversales

### T1 — Modularización
**Cierre:** 6.5 → **10/10** (resueltos por capas). Puntaje desglosado: +1.0 Bridge Pattern (76 asignaciones `window.*` migradas a puentes, grep `^\s*window\.\w+\s*=` = 0 en módulos), +0.5 lógica inline de templates extraída, +0.5 megamódulos JS partidos, +1.0 los 77 `db.query` de rutas a repositorios (0 directos en services/routes; 16 repositorios = única puerta de acceso a datos), +0.5 últimos 3 megamódulos partidos.

- **Capa backend:** sin acoplamiento circular; `core/` infra (11 archivos); schemas por dominio; enums implementados (`UserRole`, `VehicleType`, `AccessEventType`, `ReservationStatus`, `PaymentStatus`, `NotificationType`).
- **God services descompuestos:** `reservation_service.py` 1451→fachada 687 (extraídos `availability.py` 382 + `payments.py` 422 via mixin) · `access_service.py` 607→fachada 499 (extraído `access_occupancy.py` 80, dedupe de 7 bloques + 3) · `report_service.py` evaluado cohesivo, solo helper `_branch_filter` (13 usos).
- **6 megamódulos JS partidos en submódulos temáticos** (tour, dashboard-reservations, reservas-form, landing-map, admin-tour, notifications) manteniendo la superficie exportada 100% compatible; `sw.js` con precache ampliada; `node --check` OK.
- **Estados reales de UI documentados:** el backend usa `Pendiente/Activa/Completada/Cancelada/Fallido/Pagado` (la UI comparativa los maneja); los estados de la doc (`PENDIENTE_PAGO`, etc.) no existen como constantes.

### T2 — Colores y Fuentes (Design System & Tokens)
**Cierre:** P0, P1, P2, P3 CERRados 2026-09-27. Alcance: 41 CSS / 54 templates / 62 JS.

**Diagnóstico (2026-09-24):** 306 ocurrencias de dorado viejo `#C5A059`/`rgba(197,160,89,...)` (264 CSS + 29 JS + 13 HTML), 121 HEX únicos, 271 estilos inline, 35+ `font-size` distintos, 6 familias tipográficas.

**Remediada:**
- **P0 marca:** 0 residuales de `#C5A059`/cian `#00bcd4` en producto (solo quedan 55 en documentación/maquetas `Diseno_Proyecto/diseno_completo.html`); monoespaciada unificada a `var(--font-mono)` (JetBrains Mono), eliminado Share Tech Mono.
- **P1 semántica/contraste:** paleta de estados normalizada a `--danger` (#f43f5e), `--success` (#10b981), `--warning` (#f59e0b), `--info` (#3b82f6) — 0 residuales de `#ef4444/#e74c3c/#2ecc71/#27ae60/#4caf50`; 21 sustituciones de gris `#444/#555` → `var(--text-muted)`.
- **P2 escala tipográfica:** escala oficial expandida en `variables.css` (`--text-2xs`…`--text-3xl`); redundancias de `font-family` retiradas (solo quedan las 4 declaraciones justificadas: reset, token, flatpickr ×2, select FA).
- **P3 inline/theme:** `estadisticas_ocr.html` y `monitoreo_live.html` con **0 `style=`** (todo delegado a su CSS de página; guard `_tools/check_inline_styles.py` en 50 templates / 0 inline); `static/js/modules/theme.js` con la paleta de tokens, importado por **11 módulos** (chart-window, dashboard-*, estadisticas-ocr, landing-map*, reservations-admin-form, admin-tour-engine, tour).

### T3 — Tamaños, Proporciones y Componentes Visuales
**Cierre:** fases 1–4 + bloque de cierre aplicado 2026-09-27 (gaps y tarjetas). Alcance: 41 CSS / 54 templates / 62 JS.

**Fase 1 — Tokens volumétricos en `variables.css`:** `--radius-*` (xs 4 / sm 8 / md 12 / lg 16 / xl 20 / full), `--control-height-*` (sm 36 / md 46 / lg 54), `--z-*` y `--modal-*` (sm 420 / md 520 / lg 680 / xl 900). El z-index se tokenizó con los valores **reales** del sistema (`.modal` = 3000; `#toast-container` = 10000; backdrop tour 10002 literal).

**Fase 2 — Modales e inputs:** modales tokenizados a `--modal-*` + `--radius-xl` + `max-height: calc(100vh - 80px); overflow-y: auto`; sobrescritura destructiva de `profile-base.css` (800px) eliminada; inputs unificados a `--control-height-md`/`--radius-md`; suprimido `height: 2.625rem !important`; `var(--azul)` y `var(--text)` rotos reemplazados (→ `--info`, `--text-secondary`).

**Fase 3 — Botones y badges (decisión: píldora):** botones → `--radius-full`; badges informativos/rol → `--radius-sm`; píldora solo para medidores numéricos (saldo/puntos/FAB). Touch target `.btn--mini` y `.btn--icon` elevado a 40/44px vía `::before { inset: -4px }` (WCAG 2.5.5).

**Fase 4 — Breakpoints (17 → 4):** `640/768/1024/1280px`; 38 media queries absorbidas en 17 archivos. Excepción única justificada: `min-width:769px` (par del stepper sticky) en `profile-base.css`. `standalone.css` conserva su media query PWA (contexto, no layout).

**Bloque de cierre (2026-09-27):** padding de modales 40→32px · `.close-btn` 35→44×44px · hovers de tarjeta unificados a `translateY(-2px)` · densidad de tabla ~65→~50px/fila · columnas Acciones con `min-width:140px; white-space:nowrap` · corregido selector muerto `#occupancy-content`→`#tab-occupancy` · **167 gaps disonantes normalizados a la escala 4/8/16/20/24/32/40px** (excepción documentada: `10px` ×72 se conserva, aire fino icono/texto). Verificado: `check_inline_styles.py` 50/50 en 0; cambios puramente CSS (backend intacto).

### T4 — Componentes y Reutilización (DRY)
**Cierre:** 2026-09-24. **Salud 8.5/10.** Mandato `AGENTS.md`: extraer lo repetido.

**Fuerte:** 8 partials de página (navbar+footer+auth_modals en 5 páginas públicas), 6 packs de modales por dominio, 10 CSS components, 46 `{% include %}`, `ui.js`/`api.js`/`utils.js` como único dueño de modal/HTTP/toasts, `chart-window.js` (`WindowedChart`).

**Aplicado:** título dorado duplicado (9 sitios) → utilidad `.text-dorado` · `skeleton.css` = **1 definición, 9 consumidores** (6 tablas admin + tarjetas/historial cliente) · `premium.css` consolida primitivas del portal · tablas admin adelgazadas (admin_reservations 59→44, metricas 46→32) · **BEM de botones completado**: `.btn--*` puro en producción, 0 selectores legacy residuales (paso 2 v9.34.6 + `btn-icon-premium`/`btn-action-mini` → `btn--icon`/`btn--mini` v9.34.17, 8 templates + 23 usos JS; grep 0 residuales, suite 695) · guard de CI contra inline: `_tools/check_inline_styles.py` + `tests/test_inline_styles_guard.py`.

**Deuda restante:** estilos inline en `inicio.html` (83), `live.html` (46) y resto de `dashboard.html` (los emails 30 son inline obligatorio).

### T5 — UX/UI Integral (Evaluación Heurística + Journeys)
**Cierre:** 2026-09-22 (v9.32.2 auditada; P0–P3 todos HECHO). Identidad **"Obsidian & Champagne Gold"** con acento Royal Velvet, arquitectura modularizada (62 JS + 22 CSS), tours interactivos, estados vacíos asistidos, toasts glassmorphism.

**Calificación por dimensión:** Identidad Visual 8.5 · Arquitectura de Información 9.0 · Flujos Críticos 8.8 · Retroalimentación 8.7 · Responsive 8.0 · Accesibilidad 7.5.

**10 heurísticas (Nielsen):** H1 9 · H2 9.5 · H3 8.5 · H4 8.0 · H5 9.0 · H6 9.0 · H7 8.5 · H8 8.5 · H9 8.5 · H10 9.5. Fortalezas: lenguaje contextual (patente, barrera, plaza), patentes con estética de placa real, modales con Esc/backdrop/×, validación de patentes en tiempo real, password meter, Pase Digital todo-en-uno, cascada de errores en español neutro, tickets + FAQ con buscador.

**Fricciones detectadas:** (1) pagar con saldo insuficiente → modal recarga abre MP y la reserva queda impaga al volver (reintentar débito automático sería más fluido); (2) navegación móvil dual (hamburguesa + bottom nav duplican Inicio/Reservas/Perfil).

**Implementado (todas las prioridades HECHOs):**
| Ítem | Fix |
|---|---|
| P0.1 Contraste tipografía dorada | Texto → `#F2E3BF`; `#C5A059` solo bordes/íconos (ver A8) |
| P0.2 `:focus-visible` global | `outline: 2px solid var(--violet-brand)` (`profile-base.css:574`) |
| P1.3 Skeleton loaders | `static/css/components/skeleton.css` (`.skeleton`, `.skeleton-cells`, `.skeleton-card`, `.skeleton-grid`, shimmer) en 6 tablas admin + tarjetas/historial cliente |
| P1.4 Navegación móvil jerárquica | `user-footer-nav` → 4 accesos primarios (Inicio, Reservas, Pase QR — `openCurrentPass` —, Notificaciones); hamburguesa para secundarias |
| P2.5 Stepper de reserva | 4 pasos (Vehículo → Sucursal → Horario → Confirmación) sincronizado con `reservas-form.js` |
| P2.6 Autofocus en modales | `openModal` enfoca el primer campo editable (`modules/ui.js`) |
| P3.7 Limpieza inline | Título centrado repetido → `.section-title-premium--center`; resto de `dashboard.html` a iteración futura |
| P3.8 Botones BEM | Selectores `.btn--primary/--outline/--premium/--sm/--full/--icon/--mini` agrupados con los legacy; usos de auth/onboarding migrados (luego 100% BEM en T4) |
| Sticky action-bar en modales largos | `.modal-actions-sticky` (sticky bottom glass) en DETALLE captura/reserva, tickets, sucursales, promociones, ayuda |

---

## Propuestas de Auditoría CSS (AC-1 a AC-5) — ESTADO DE EJECUCIÓN

Complemento de la propuesta original (2026-09-24) para la capa CSS. Ejecución de Fase 1 (AC-2 y AC-4) completada el 2026-09-27. Fase 2: AC-1 (2026-09-28), AC-5 (2026-09-28) y AC-3 (2026-09-29) cerradas:

| # | Auditoría | Prioridad | Esfuerzo | Estado | Métrica actual / Diagnóstico |
|---|---|:---:|:---:|:---:|:---|
| **AC-1** | Especificidad y guerra de `!important` | Alta | 1 día | ✅ **CERRADA** (Lotes 1–4 completos) | **287** `!important` totales restantes (de 613 iniciales, **−326 eliminados**); **0 propios** (reducidos de **345 a 0**). Todo lo restante está justificado por librerías/PWA/RBAC/AC-4: Leaflet (`landing-map.css` 134), Tour overlays (`profile-tour.css` 71 + `dashboard-admin-tour.css` 9), Standalone desktop (`standalone.css` 36), Flatpickr (`forms.css` 23), reset AC-4 (4), QR captura (`profile-reservations.css` 4), RBAC roles (`dashboard-base.css` 4), utilidades defensivas (`dashboard-tables.css` 1, `landing-nav.css` 1). |
| **AC-2** | Rendimiento de renderizado, GPU y animaciones | Alta | 1–2 días | ✅ **CERRADA** | **0** `transition: all` (todas migradas a `transform`/`opacity`/`background`/`border-color`/`box-shadow`) |
| **AC-3** | PWA + Safe Areas (notches / isla dinámica) | Media/Alta | 1 día | ✅ **CERRADA** (con 1 criterio descartado por no aplicar) | `viewport-fit=cover` en el meta + **4 tokens** `--safe-area-*` y **11 superficies** que los consumen (headers, sidebar, modales, FABs); `overscroll-behavior-y: contain` en los **3** contenedores de scroll; 0 → 11 usos de `env(safe-area-inset-*)` |
| **AC-4** | Estados interactivos y foco de teclado | Media | 1 día | ✅ **CERRADA** | Anillo institucional `:focus-visible` global en `reset.css` y `forms.css`, feedback `:active` (`scale(0.97)`), estados `:disabled` estandarizados |
| **AC-5** | CSS muerto, duplicación y DRY | Media | 1 día | ✅ **CERRADA** (Lotes 1, 2, 7 y 9) | **0** clases huérfanas (de 120 candidatas), **0** `@keyframes` duplicados (de 16 definidos), **−15 tokens** muertos en `variables.css` (65 → 50), 0 `!important` nuevos, **−1247 líneas** netas en el diff |

**Criterios de aceptación y avances:**
- **AC-1 (CERRADAS Lotes 1–4):** 
  - *Diagnóstico cuantitativo inicial:* 613 ocurrencias totales en 26 archivos (268 librerías/PWA + 345 propios).
  - *Avance acumulado (2026-09-27):* **−326 `!important` eliminados** sin romper especificidad ni diseño. **0 propios restantes** (de 345 iniciales).
    - **Lote 1 — Navegación y Layouts Base CERRADO (66 → 1):** `landing-nav.css` (46 → 1, preservada solo regla de ocultamiento de acciones auth por JS), `sidebar.css` (17 → 0), `header.css` (3 → 0).
    - **Lote 2 — Vistas del Dashboard Admin CERRADO (142 → 6):** `dashboard-settings.css` (43 → 0), `dashboard-base.css` (41 → 4, preservadas 4 reglas RBAC de roles), `dashboard-cards.css` (7 → 0), `dashboard-tables.css` (36 → 2, preservadas utilidades de texto), `dashboard-live.css` (15 → 0).
    - **Lote 3 — Portal de Usuario / Perfil avanzado CERRADO (84 → 4):** `profile-notifications.css` (5 → 0), `profile-points.css` (15 → 0), `profile-vehicles.css` (17 → 0), `profile-reservations.css` (22 → 4, preservadas 4 reglas de captura QR de ticket), `profile-base.css` (25 → 0).
    - **Lote 4 — Componentes y Base Global CERRADO (53 → 11):** `tables.css` (23 → 0), `forms.css` propios (9 → 0; preservados 23 de tema Flatpickr), `typography.css` (5 → 0), `legal.css` (5 → 0), `style.css` (3 → 0), `utilities.css` (2 → 0), `landing-modals.css` (1 → 0), `monitoreo-live.css` (1 → 0); `reset.css` (4, justificados por AC-4, no tocados).
  - *Meta final:* Reducir los propios a <30 (solo utilidades de override y RBAC). **CUMPLIDA: 0 propios.**
- **AC-2 (CERRADA ✓):** 0 `transition: all` en componentes de alta frecuencia; animaciones compuestas con aceleración GPU sin caídas de frames en modales/hover.
- **AC-3 (CERRADA ✓):** `env(safe-area-inset-*)` global en headers/barras/modales; `overscroll-behavior-y: contain`.
  - *Hallazgo previo (2026-09-29):* el proyecto declaraba `apple-mobile-web-app-status-bar-style: black-translucent` **sin** `viewport-fit=cover` en el meta. En iOS esa combinación es la peor de las tres: la webview se dibuja bajo la status bar (por `black-translucent`) pero `env()` devuelve **0** (sin `viewport-fit`), así que el header quedaba parcialmente tapado y no existía forma de compensarlo. Los dos cambios son **acoplados**: aplicar el CSS sin el meta es un no-op, y aplicar el meta sin el CSS deja el header bajo el notch.
  - *Tokens (DRY):* 4 tokens `--safe-area-top/right/bottom/left` en `variables.css` (con fallback `0px`), consumidos con `calc()` para **sumar** el inset al espaciado existente en lugar de reemplazarlo. Se evita repetir `env(safe-area-inset-*)` en 11 sitios.
  - *Superficies con inset (11):* `variables.css` (fuente) · `header.css` (header sticky del layout con sidebar) · `standalone.css` (espejo obligatorio: su `padding: ... !important` anulaba el inset del header en modo standalone, justo donde más hace falta) · `sidebar.css` (padding del sidebar, padding-bottom del drawer móvil, `top` del toggle fijo) · `grid.css` (fin del scroll principal) · `modals.css` (`.modal`, `.modal-premium`, `.modal-actions-sticky`) · `virtual-time.css` (`.vt-fab` inferior/derecha) · `landing-nav.css` (header fijo de landing, estados normal y `.scrolled`) · `base.html` (`#pwa-install-btn` inline).
  - *Overscroll (3 contenedores):* `.main-content-scroll`, `.modal`, `.modal-premium` y el drawer móvil `.sidebar` → `overscroll-behavior-y: contain` para evitar pull-to-refresh y scroll-chaining.
  - *Criterio NA (no aplicado):* touch targets ≥44px. Las 11 declaraciones entre 20–43px son botones compactos de dashboard de escritorio; la guideline es mobile y forzar 44px los desproporcionaría. El criterio de `font-size ≥16px` en inputs móviles **ya estaba cumplido** por `.input-premium` (`1rem` en `forms.css:50`), 0 reglas por debajo del umbral.
  - *Cache:* los 5 CSS del shell modificados están en el precache de `sw.js`; se subió `SHELL_CACHE` a `autopass-shell-v2` (el propio `sw.js:1` lo indica al desplegar) para que no sirvan CSS viejo con `stale-while-revalidate`.
  - *Verificado:* llaves balanceadas, 0 regresión de CSS muerto, **287** `!important` (baseline AC-1 sin cambios), suite **707 passed**. Pendiente de validación visual en un iPhone con notch.
- **AC-4 (CERRADA ✓):** navegación Tab/Shift+Tab 100% visible con `:focus-visible` dorado institucional; botones e inputs `:disabled` estandarizados con `filter: grayscale(0.6)`; feedback `:active` táctil unificado.
- **AC-5 (CERRADA ✓):** criterios cumplidos — **0** clases huérfanas de versiones v9.0–v9.23; **−1247 líneas** netas; unificación de scrollbar y keyframes duplicados.
  - *Diagnóstico:* 43 CSS, 14.313 líneas, 2.576 reglas, 1.254 clases distintas. Sin duplicación real de scrollbar thumb/track (solo 1 regla `display:none` en `monitoreo-live.css`); sí 114 bloques flex-center idénticos (32 archivos), 26 `margin:0 auto` (18 archivos), 86 radios literales, 25 blur y 49 bloques `uppercase`+`letter-spacing`.
  - *Lote 1 — CSS muerto CERRADO:* **120 clases huérfanas eliminadas**, verificadas contra templates + JS + backend y con revisión manual de excepciones runtime (`role-*` en `dashboard.html:28`, `badge-*`, estados voucher `vigente/usado/cancelado` en `profile.js`). Resultado: **0 huérfanas** sobre 1.142 clases definidas.
  - *Lote 2 — Utilities CERRADO:* corregido bug de `.no-print` (regla mal anidada dentro de `@media print`), eliminado `.mt-30` duplicado, purgadas clases utilitarias muertas y consolidadas las definiciones de texto/pesos en `typography.css` (`.font-bold`, `.text-white`, `.text-small` como aliases). Orden de carga preservado en `base.html` (`typography.css` antes de `utilities.css`).
  - *Lote 7 — Animaciones CERRADO:* los 3 `@keyframes` duplicados idénticos (`handBounce`, `fadeInSlideUp`, `hintPulseAnim`) se movieron a la fuente única `static/css/base/animations.css`, cargado en `base.html` y añadido al precache de `static/sw.js`. Verificado: 16 keyframes definidos, **0 huérfanos y 0 duplicados**.
  - *Lote 9 — Tokens muertos CERRADO:* 15 tokens sin uso eliminados de `variables.css` (65 → 50), todos verificados por uso real.
  - *Herramienta nueva:* `_tools/check_css_huerfano.py` (+ `_tools/css_huerfano_baseline.json`) con modos `--list`/`--update`, que escanea selectores `.clase` en `static/css` y los cruza contra templates, JS y backend, ignorando librerías de terceros y prefijos runtime. Baseline fijado en 0 para detectar regresiones futuras.
  - *Verificación:* guard en 0 huérfanas, `git diff --check` sin errores, **702 passed** (7 warnings). Diff: 28 archivos, +21 / −1247.
  - *No aplicado (fuera de alcance de esta ronda):* la unificación de los bloques flex-center, los radios literales, los blur y los label-uppercase queda para una ronda DRY específica posterior, ya que no afecta la correctitud ni el criterio de "cero clases huérfanas".
  - *Re-medido tras la purga (2026-09-30):* el diagnóstico original (114 flex-center, 86 radios, 25 blur, 49 label-uppercase) quedó desactualizado en cantidad y alcance. Con el CSS ya purgado, los valores reales son **146** flex-center idénticos (36 archivos), **253** `border-radius` literales (34 archivos), **43** blur sin token (17 archivos) y **90** `uppercase`+`letter-spacing` (29 archivos). Siguen diferidos: los 253 radios son valores **heterogéneos a propósito** (8px, 12px, 20px, 999px, 50%…) y mapearlos a tokens a ciegas rompería el diseño; solo el subconjunto de duplicados exactos sería seguro, y es chico para el ruido que genera. El subconjunto con gain real es el de los flex-center, que es también el más riesgoso.
  - *Color — Fase 1 CERRADA; Fase 2 MEDIDA y DESCARTADA con evidencia (v9.34.61–62):* de los 1.535 literales, solo **195** eran equivalencias exactas a tokens existentes (migrados, 31 archivos, verificado neutral a nivel de píxel). Los 1.132 restantes se agrupan en familias de opacidad. La pregunta que faltaba era **si esas familias forman una escala o son continuas**, y la medición respondió que **forman escala**: los alfas son decimales redondos que el autor escribió (`0.05`, `0.08`, `0.12`, `0.3`…), con **7 de 19** niveles de blanco, **8 de 20** de negro y **8 de 23** de dorado cubriendo el 80% de los usos. Fusionar con tolerancia de 2/255 mueve solo **14 de 190** ocurrencias; a 12/255 mueve 75 pero cambia un borde de 0.05 a 0.097 (casi el doble, visible). **Se descarta la unificación por escala gruesa**:se paga visual real por ~55 colores de coherencia. En su lugar la escala quedó **declarada y vigilada**: `check_css_design_system.py` mide los niveles de opacidad por familia contra el baseline (hoy 100: blanco 19, dorado 23, gris 9, negro 20, otros 29) y flaggea cualquier nivel nuevo para que sea una decisión registrada, no un descuido. No se prohíbe (sería una regla mortal para el diseño).

---

## Herramientas reutilizables (para re-correr cada guard)

| Guard | Ubicación | Qué verifica |
|---|---|---|
| Consistencia front↔back (A6) | `_tools/check_consistencia_frontend.py` | URLs `/v1`/`/ws` del front existen y con verbo correcto en backend |
| Scan XSS innerHTML (A9) | `_tools/check_xss_innerhtml.ps1` | Conteo de `innerHTML=`/`insertAdjacentHTML(` + interpoladas + no-escapadas |
| Guard estilos inline (A7/T4) | `_tools/check_inline_styles.py` (+ `tests/test_inline_styles_guard.py`) | Regresión de `style="…"` por template (baseline, umbral 25, emails exceptuados) |
| Paridad de índices (A5/T) | `tests/test_schema_parity_p2.py` | `create_all` ↔ `alembic head` = 0 diffs (usa comparador de schema orden-insensible) |
| Guard CSS muerto (AC-5) | `_tools/check_css_huerfano.py` (+ `_tools/css_huerfano_baseline.json`) | Clases `.clase` definidas en `static/css` sin uso en templates/JS/backend; baseline 0 |
| Integridad de tokens CSS (v9.34.61) | `_tools/check_css_tokens.py` | `var(--x)` sin `--x` declarado (bug silencioso) y `--x` declarado sin usar; distingue Custom Properties de clases BEM. **v9.34.70**: además exige que la declaración esté **dentro de un bloque**, porque los 23 tokens `--shadow-*` estaban fuera del `:root` y sus 54 usos no pintaban nada mientras el guard informaba "todos declarados" (solo buscaba el texto, sin preguntar su ubicación) |
| Equivalencia visual de color (v9.34.61) | `_tools/check_color_equivalence.py` | Compara el multiset de RGBA **resueltos** por archivo contra `--against` (default HEAD): si es idéntico, la migración no cambió ni un píxel. `--max-delta N` tolera desvío por canal; `--allow ARCHIVO` para diferencias deliberadas. **v9.34.68**: los cambios de color legítimos (mover un título de dorado a blanco para bajar la fatiga visual) se declaran en `_tools/color_equivalence_allowlist.json` con su commit y motivo. Se omiten **solo** cuando `--against` es el padre de ese commit; en cualquier otra comparación el archivo se compara entero, así una regresión posterior en el mismo archivo sigue saltando. Test de mordida: inyectar `var(--rojo)` en un archivo de la lista igual da exit 1 |
| Baseline de design system (v9.34.61) | `_tools/check_css_design_system.py` (+ `_tools/css_design_system_baseline.json`) | Fija y vigila 5 métricas: color (literales no genéricos / RGBA distintos), **adopción de la escala de espaciado** (v9.34.63 reemplazó la métrica `spacing off-grid`), `box-shadow` distintas, duraciones y curvas de transición, y **escala de opacidad por familia** (v9.34.62: 100 niveles; un alfa nuevo se flaggea, no se prohíbe) |
| Accesibilidad de formularios (2026-10-14) | `_tools/check_a11y_forms.py` | 4 reglas: cada `<label>` que **rotula un campo** lo asocia (`for=` o envolviéndolo); el `for=` no queda huérfano (debe apuntar al control que sigue); el toggle de contraseña es `<button type="button">` con `aria-label`+`aria-pressed` (un botón sin type dentro del form lo enviaría al clickearlo); `#toast-container` sigue siendo live region. Se ignoran **a propósito** los `<label>` que rotulan un valor (no hay campo que asociar) y los que envuelven su control |
| Migración de asociación label→campo (herramienta, no guard) | `_tools/migrate_label_association.py` | Agrega `for=` a los `<label>` que rotulan un campo y, si el control no tiene `id`, le genera uno **por formulario** (`quick-veh-*`, `add-veh-*`, `res-*`, `contact-*`) para que no colisionen en el mismo DOM: `perfil.html` incluye a la vez `inicio.html` y `vehiculos.html`. Dry-run por defecto, `--apply`, idempotente, preserva CRLF |
| Migración de atributos de formulario (herramienta, no guard) | `_tools/migrate_form_attributes.py` | Agrega `autocomplete` (username/current-password/new-password/given-name/family-name/email/tel), `inputmode` (`numeric`/`tel`), `autocapitalize="characters"`+`spellcheck="false"` en patentes, y `autocomplete="off"` a nivel `<form>` en los formularios de **datos de terceros** (panel de usuarios). Dry-run por defecto, `--apply`, idempotente |
| Migración de color (herramienta, no guard) | `_tools/migrate_color_tokens.py` | Convierte literales con RGBA idéntico a un token existente. Dry-run por defecto, `--apply`, `--include-generic`; idempotente |
| Migración de sombras (herramienta, no guard) | `_tools/migrate_shadow_tokens.py` | Convierte `box-shadow` duplicados **exactos** (≥2 usos) a tokens `--shadow-*`. No toca las de un solo uso. Idempotente, atómico y con post-condición estructural (`verify()`): balance de llaves/semicolon, número de declaraciones y forma de cada sombra deben quedar idénticos, y aborta entero si no |
| Movimiento accesible (v9.34.64) | `check_reduced_motion()` dentro de `_tools/check_css_design_system.py` | **Exige** un bloque `@media prefers-reduced-motion: reduce` que neutralice `animation-duration`, `animation-iteration-count` y `transition-duration` con `!important`, y rechaza los dos errores del patrón estándar (`animation: none` deja invisibles los elementos que la animación hacía aparecer; `transition-duration: 0s` deja de disparar `transitionend` y cuelga al JS). No se compara contra baseline: si se borra el bloque, el baseline no se entera |
| Anillo de foco (v9.34.65) | `check_focus_ring()` dentro de `_tools/check_css_design_system.py` | **Exige** que el anillo de AC-4 viva en `:root :focus-visible` (`0,2,0`) y no en `:focus-visible` pelado (`0,1,0`): `reset.css` se carga primero, así que cualquier `outline: none` de página con clase (misma especificidad, carga posterior) lo gana por cascada, y con ID gana sin discutir. No se compara contra baseline porque el fallo es de **especificidad**, no de conteo: degradar el selector a `:focus-visible` no cambia ningún número del baseline. También exige que exista la exención de los controles que ya cumplen 1.4.11 con su `:focus` propio, para que no queden con doble anillo |
| Movimiento accesible en JS (v9.34.65) | `check_js_scroll_motion()` dentro de `_tools/check_css_design_system.py` | **Exige** que ninguna llamada hardcodee `scrollIntoView({ behavior: 'smooth' })` (16 las tenía, en 6 módulos) y que `modules/utils.js` siga exportando `scrollToElement()`, que consulta `prefers-reduced-motion`. Complementa a `check_reduced_motion()`: el bloque CSS fija `scroll-behavior: auto !important`, pero eso **no** alcanza al scroll animado de JS, que se resuelve en cada llamada |
| Movimiento accesible en JS: gráficos y cámara (v9.34.98) | `check_js_motion_gaps()` dentro de `_tools/check_css_design_system.py` | Tercera mitad de la misma familia: `check_reduced_motion()` cubre el CSS y `check_js_scroll_motion()` el scroll, pero **Chart.js** anima dentro de un `<canvas>` y **Leaflet** mueve la cámara con `requestAnimationFrame`, fuera del alcance del CSS. **Exige** que `modules/utils.js` siga exportando `mapMotionOptions()` y `applyReducedMotionToCharts()` (ambos consultando `prefers-reduced-motion`), que **nadie fuera de `utils.js`** nombre `animate` (es el único lugar que decide), que **toda** llamada de cámara de Leaflet (`flyTo`/`flyToBounds`/`setView`/`fitBounds`/`panTo`/…) pase por `mapMotionOptions()` y que `main.js` llame a `applyReducedMotionToCharts()` exactamente una vez (corre en todas las páginas antes de que cada vista cree sus gráficos). Mordida probada con 4 mutaciones |
| Verificación de cierre A7 (grep) | terminal | `except\s*:` sin tipo = 0 en `*.py` |

---

## Estado de cierre (2026-09-28)

- **Suite backend: 756 passed**, 8 warnings. Cobertura **93%** (16.468 stmts / 1.160 sin cubrir). Reverificado tras AC-3, el cierre de gaps de A3, la migración de color de v9.34.61 y la documentación de v9.34.78.
- Todos los cambios CSS de T2/T3/T4 verificados sin regresión (los tests no tocan CSS).
- **5 guards CSS en verde**: llaves balanceadas, clases huérfanas, integridad de tokens, baseline de design system, y equivalencia de color con `--max-delta 0` (v9.34.63). Ninguno toca colores por su cuenta; la neutralidad visual de la migración de color se probó aparte con `check_color_equivalence.py` (31 de 32 archivos con multiset RGBA idéntico; el único diff es el fix intencional de `var(--text)`).
- **Pendiente único:** mediciones con volumen real de Neon.
- AC-3 (PWA + Safe Areas) cerrada el 2026-09-29: **no queda ninguna auditoría CSS abierta de esta tanda.**
- **Movimiento accesible (v9.34.64)**: cerrado. Faltaba por completo la vía de escape de `prefers-reduced-motion` para 229 transiciones y 18 `@keyframes`.
- **Scroll programático (v9.34.65)**: cerrado, y era el último pendiente de CSS/a11y. Eran **16 llamadas** (no 3) con `scrollIntoView({ behavior: 'smooth' })` en 6 módulos, que CSS no puede frenar; **9 usaban `block: 'center'`**, llevando el elemento al centro con animación durante la lectura. Ahora pasan por `scrollToElement()` de `static/js/modules/utils.js`. Guard `check_js_scroll_motion()` con mordida 6/6.
- **No queda ningún pendiente de CSS/a11y abierto.**
- **z-index: cerrado por medición, no había bug (v9.34.65)**. El pendiente de v9.34.64 suponía que 5 literales `1000`/`1100` conviviendo con 7 tokens `--z-*` producían un solapamiento. Al auditar cada uno con el DOM real, **ninguno lo produce**: `.sidebar-toggle` (1000) y `.notif-dropdown` (1000) son descendientes de elementos que ya crean stacking context (`.sidebar` y el header sticky), así que sus valores están encapsulados y nunca compiten globalmente. `.sidebar-overlay` (1999) está deliberadamente justo debajo de `--z-sidebar` (2000) para que el backdrop quede detrás del sidebar abierto. `.mobile-nav-toggle` (1100) debe ganarle al header (1000) para ser pulsable y perder contra el overlay (1999) para que el toque en el backdrop cierre el panel. Los literales altos **codifican relaciones, no valores absolutos**: tokenizarlos cambiaría la jerarquía. **No se unificó nada.**
- **Anillo de foco: cerrado, era un defecto real (v9.34.65)**. El anillo de AC-4 ya existía en `:focus-visible` (`0,1,0`) dentro de `reset.css`, pero `reset.css` se carga primero (`base.html:14`) y **24 reglas de página lo anulaban** con `outline: none`. Contraste medido del indicador (WCAG 1.4.11, exige ≥3:1): `.select-premium-sm` 1.09:1, `#promo-sucursal` 1.20:1, `.mobile-menu-btn` 1.13:1 (los tres sin cambio de píxel al enfocar) y `.promo-branch-select` 2.54:1. Resuelto con un bloque `:root :focus-visible` (`0,2,0`) indebatible frente a clases, más una exención acotada para los 10 controles que ya cumplen con su `:focus` propio (10.5:1–11.4:1). **0 controles sin indicador de foco.** Guard `check_focus_ring()`, mordida 5/5.
- **Cerrado el pendiente de decisión de diseño (v9.34.63):** las tres unificaciones pendientes —escala de espaciado, `box-shadow` y curvas de transición— se **midieron y se descartaron**, no se arrancaron. La conclusión es que **el design system ya está en uso y es consistente**, así que no quedaba unificación que valiera el riesgo visual.
- **Guard de accesibilidad de modales (v9.34.94):** _tools/check_a11y_modals.py valida role="dialog"+aria-modal="true", nombre accesible resoluble (aria-labelledby apunta a id real o aria-label), que el control de cierre es <button> o <a> con nombre accesible y type="button" cuando es <button>, y que dicho control es reconocible por ui.js (busca [data-modal-close] o .close-btn, .modal-close-top). Además, si el macro templates/components/modal_header.html se usa, exige que emita el cierre con data-modal-close y aria-label="Cerrar" (evita falsos positivos). Prueba negativa en Temp/opencode/test_guard_modales.py (esperados 8 problemas en 6 diálogos falsos → exit 1). Verificado **verde**.

- **Herramienta de migración de modales (v9.34.94):** _tools/migrate_modal_a11y.py agrega role="dialog" aria-modal="true", aria-labelledby/aria-label, data-modal-close cuando corresponde y normaliza cierres: convierte 5 <span class="close-btn"> a <button type="button" class="close-btn" data-modal-close aria-label="Cerrar">, agrega aria-label="Cerrar" a botones de cierre sin nombre (incluyendo los 2 de /perfil), usa title_id= del macro para enlazar el <h*>, añade tabindex="-1" al contenedor del onboarding cuando el h2 es el título y unifica los modales que deben centrarse vía .modal--centered. **45 líneas de marcado** en 14 templates. Idempotente (segunda corrida = 0 ediciones). No crea ids, ni cambia textos ni lógica JS.

