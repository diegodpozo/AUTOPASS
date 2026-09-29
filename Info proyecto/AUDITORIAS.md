# Auditorías de AUTOPASS — Documento Consolidado

> **Estado global: A1–A9 CERRADAS** con remediación aplicada y verificada (última ronda 2026-09-27, suite **702 passed**). Auditorías transversales resueltas (modularización, colores/fuentes, tamaños/proporciones, nomenclatura, componentes, UX/UI). Propuestas CSS: AC-2 y AC-4 cerradas; **AC-1 CERRADA (Lotes 1–4 completos, 0 `!important` propios, −345, quedan solo justificados por librerías/PWA/RBAC)**; AC-3 y AC-5 pendientes de ejecutar. Pendiente explícito único backend: mediciones con volumen real de Neon (no disponible).

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

**Por capa (antes → ahora):** `alpr/` 64→**95%** · `routes/` 57→**83%** · `services/` **78%** · `repositories/` **78%** · `core/` 75→**77%**.

**100% alcanzado:** `auth.py`, `payments.py`, `preprocessor.py`, `video_streamer.py`, `ws_client.py`, `video.py`, `cameras.py`, `common.py`, `settings.py`, `balance.py`, `promotions.py`, `health.py`, `session_repository`.

**Rondas destacadas:** #12 preprocessor ALPR a 100% (36 tests) · #14 `ocr_engine.py` 56→98% (55 tests) · #15 cameras/common a 100% (74 tests) · #20 `fidelization.py` →88% · #21 support user 41→100% · #22 support admin 57→100% (estos dos últimos no contabilizados en el resumen; ver `tests/test_user_support_routes.py` / `test_admin_support_routes.py`).

**Pendientes/depriorizado:** `core/seed.py` 0% (utilities) y `virtual_time` (herramienta de demo, a propósito). Flujos críticos sin gap: pipeline ALPR, pagos/webhook MP, OAuth, socket de aforo, workers, streaming.

**CI (`ci.yml.disabled`) NO reactivar tal cual:** correr en ubuntu-latest + Python 3.14, reemplazar `patch_bidi.py` por `init_db.py`, agregar `--cov-fail-under=82`, no correr `alembic upgrade head` desde cero.

---

## A4 — Datos / Migraciones (SQL)

**Cierre:** P1 2026-09-19 + P2 2026-09-27. **`alembic upgrade head` REPRODUCIBLE desde BD vacía.**

**P1 aplicada:** flujo único `sync_schema()` en `core/database.py` (`create_all` de modelos + Alembic al head, con warning si la cadena no es reproducible); eliminado `init_db.py:migrate_db()` que hacía `ALTER TABLE` manuales (`is_blocked`, `capacidad_motos`, etc.) = **segunda fuente de verdad del esquema eliminada**.

**P2 aplicada (2026-09-27):**
- Baseline real en `alembic/versions/c833a3129266_initial_schema.py`: era `upgrade() -> pass`, ahora materializa 16 tablas base + índices.
- `d4f7c8e2a190` convertida a batch-mode con FK nombrada (SQLite) y `e6f7a8b9c0d1` con columnas `nullable` alineadas al modelo.
- Deuda A4.6 liquidada: eliminados los 2 "parches" de datos de `core/seed.py` (aforo `getattr` legacy y `update()` masivo de sucursales).
- **Verificado en sandbox SQLite:** BD vacía → `upgrade head` EXIT 0, 18 tablas, schema **idéntico** a `create_all` (**0 diffs** orden-insensible), `current == head`.

**Reproducibilidad:** cadena lineal de 14 migraciones, single head `ce7d1e2f3a5b`; `alembic current` en Neon = head (sin pendientes; solo lectura, no se tocó prod). **0 migraciones con data de usuario** (DDL puro; grep `op.execute|insert|update|delete|bulk` = 0). Updates legacy ("AUTOPASS " prefix) resueltos en lectura (`core/normalize.py`), no en BD.

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

Complemento de la propuesta original (2026-09-24) para la capa CSS. Ejecución de Fase 1 (AC-2 y AC-4) completada el 2026-09-27. Fase 2 (AC-1 en diagnóstico y preparación de refactor):

| # | Auditoría | Prioridad | Esfuerzo | Estado | Métrica actual / Diagnóstico |
|---|---|:---:|:---:|:---:|:---|
| **AC-1** | Especificidad y guerra de `!important` | Alta | 1 día | ✅ **CERRADA** (Lotes 1–4 completos) | **287** `!important` totales restantes (de 613 iniciales, **−326 eliminados**); **0 propios** (reducidos de **345 a 0**). Todo lo restante está justificado por librerías/PWA/RBAC/AC-4: Leaflet (`landing-map.css` 134), Tour overlays (`profile-tour.css` 71 + `dashboard-admin-tour.css` 9), Standalone desktop (`standalone.css` 36), Flatpickr (`forms.css` 23), reset AC-4 (4), QR captura (`profile-reservations.css` 4), RBAC roles (`dashboard-base.css` 4), utilidades defensivas (`dashboard-tables.css` 1, `landing-nav.css` 1). |
| **AC-2** | Rendimiento de renderizado, GPU y animaciones | Alta | 1–2 días | ✅ **CERRADA** | **0** `transition: all` (todas migradas a `transform`/`opacity`/`background`/`border-color`/`box-shadow`) |
| **AC-3** | PWA + Safe Areas (notches / isla dinámica) | Media/Alta | 1 día | ⏳ PENDIENTE | `env(safe-area-inset-*)` pendiente de aplicar |
| **AC-4** | Estados interactivos y foco de teclado | Media | 1 día | ✅ **CERRADA** | Anillo institucional `:focus-visible` global en `reset.css` y `forms.css`, feedback `:active` (`scale(0.97)`), estados `:disabled` estandarizados |
| **AC-5** | CSS muerto, duplicación y DRY | Media | 1 día | ⏳ PENDIENTE | ~41 archivos con patrones repetidos (`::-webkit-scrollbar`, flex-center, glass) |

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
- **AC-3 (Pendiente):** `env(safe-area-inset-*)` global en headers/barras/modales; touch targets ≥44px; `font-size ≥16px` en inputs móviles (evita zoom iOS); `overscroll-behavior-y: contain`.
- **AC-4 (CERRADA ✓):** navegación Tab/Shift+Tab 100% visible con `:focus-visible` dorado institucional; botones e inputs `:disabled` estandarizados con `filter: grayscale(0.6)`; feedback `:active` táctil unificado.
- **AC-5 (Pendiente):** −15–20% de peso del bundle CSS; cero clases huérfanas de versiones v9.0–v9.23; unificación de patrones scrollbar y glassmorphic.

---

## Herramientas reutilizables (para re-correr cada guard)

| Guard | Ubicación | Qué verifica |
|---|---|---|
| Consistencia front↔back (A6) | `_tools/check_consistencia_frontend.py` | URLs `/v1`/`/ws` del front existen y con verbo correcto en backend |
| Scan XSS innerHTML (A9) | `_tools/check_xss_innerhtml.ps1` | Conteo de `innerHTML=`/`insertAdjacentHTML(` + interpoladas + no-escapadas |
| Guard estilos inline (A7/T4) | `_tools/check_inline_styles.py` (+ `tests/test_inline_styles_guard.py`) | Regresión de `style="…"` por template (baseline, umbral 25, emails exceptuados) |
| Paridad de índices (A5/T) | `tests/test_schema_parity_p2.py` | `create_all` ↔ `alembic head` = 0 diffs (usa comparador de schema orden-insensible) |
| Verificación de cierre A7 (grep) | terminal | `except\s*:` sin tipo = 0 en `*.py` |

---

## Estado de cierre (2026-09-27)

- **Suite backend: 702 passed** (695 base + 5 regresión P1 A5 + 2 paridad P2 A5), 7 warnings.
- Todos los cambios CSS de T2/T3/T4 verificados sin regresión (los tests no tocan CSS).
- **Pendiente único:** mediciones con volumen real de Neon; cuando CI se reactive: Python 3.14 + `init_db.py` + `--cov-fail-under=82`.
- AC-1..AC-5 son candidatos naturales de la próxima ronda de auditorías.