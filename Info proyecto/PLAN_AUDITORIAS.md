# Plan de Auditorías — AUTOPASS

> Documento de planificación. Estado: **A1–A4 HECHO** (informes en `Info proyecto/`), **A5 pendiente** (requiere Neon/profiling en vivo), **A6–A9 HECHO** con verificaciones formales del 2026-09-27. Auditorías transversales resueltas: `AUDITORIA_MODULARIZACION.md` (10/10), `AUDITORIA_COLORES_FUENTES.md` (P0/P1/P2/P3 cerrados), `AUDITORIA_TAMANOS_PROPORCIONES.md` (fases 1–4 + bloque de cierre aplicado), `AUDITORIA_NOMENCLATURA_ARCHIVOS.md` (8.2→9.0/10, remediación P0/P1 aplicada, ver §AN), `AUDITORIA_COMPONENTES.md` (DRY) y `AUDITORIA_UX_UI.md`. Propuesta de extensión para la capa CSS detallada en `Info proyecto/PROPUESTA_AUDITORIAS_CSS.md`.

## Resumen

| # | Auditoría | Prioridad | Esfuerzo | Riesgo que mitiga |
|---|-----------|-----------|----------|-------------------|
| A1 | Seguridad de la API | Alta | 1–2 días | Exposición de datos, abuso de endpoints, headers ausentes |
| A2 | Dependencias y Supply Chain | Alta | 0.5–1 día | CVEs conocidos en paddleocr/rapidocr/opencv |
| A3 | Cobertura de Tests | Alta | 1 día | Gaps de cobertura en ALPR, workers, views |
| A4 | Datos / Migraciones (SQL) | Alta | 1 día | Alembic roto entre Neon y SQLite, datos en logs |
| A5 | Rendimiento (profiling) | Media | 1–2 días | N+1 en dashboard admin, tickets, reservas |
| A6 | Consistencia Frontend/Backend | Media | 1 día | JS llama rutas inexistentes o campos faltantes |
| A7 | Errores y Manejo de Excepciones | Media | 0.5 día | Excepciones cegadas, info interna filtrada |
| A8 | Accesibilidad / UX | Baja | 1 día | Contraste, foco, labels en formularios |
| A9 | Seguridad Frontend (XSS) | Baja | 0.5 día | innerHTML con datos del backend sin sanear |

---

## A1 — Auditoría de Seguridad de la API

**Prioridad:** Alta · **Esfuerzo:** 1–2 días · **Entregable:** `Info proyecto/AUDITORIA_SEGURIDAD_API.md`

> **Estado: HECHO** (informe 2026-09-19) + **remediación P0/P1 aplicada el 2026-09-20** (pay-stay autenticado, video WS protegido, bloqueo efectivo en `get_current_user`, headers de seguridad, rate-limit de webhook MP). Riesgo recalculado: **MEDIO**. Checklist cerrado en el informe (§3).

### Objetivo
Detectar vectores de exposición en autenticación, autorización, transporte y data-at-rest.

### Alcance
- `core/security.py`, `core/config.py`, `core/limiter.py`, `main.py`
- `routes/auth.py`, `routes/parking/access.py`, `routes/user/*`, `routes/admin/*`
- WebSockets: `routes/parking/status.py` (WS `/v1/parking/ws`), `routes/system/video.py` (WS `/ws/video/{id}`)

### Pasos
1. **Headers de seguridad**: ~~confirmar la ausencia (grep dio 0) y redactar middleware~~ — **HECHO**: `security_headers_middleware` en `main.py:72-101` (CSP con CDNs, fuentes de Google y APIs de mapas, HSTS tras TLS, XFO, nosniff, Referrer-Policy) + test de regresión `tests/test_security_headers.py`.
2. **JWT**: revisar claim `sub` (email vs id), expiración, `iat`/`jti` para revocación, algoritmo forzado `HS256` y riesgo del default `SECRET_KEY="tu_super_secreto_para_produccion"` (config.py:17) — exigir error de arranque si es el valor demo.
3. **Refresh/cierre de sesión**: verificar que UserSession se invalide en logout y si un token sigue siendo válido tras el bloqueo de cuenta (toggle-block).
4. **CORS**: validar `ALLOWED_ORIGINS` en config; sugerir lista explícita por entorno.
5. **WebSockets**: auditar cómo se autentica el WS (¿token en query? ¿se valida en `accept`?) y si el video WS exige rol STAFF+.
6. **Inyección SQL**: muestreo de filtros en `services/report_service.py` y `routes/admin/*` — confirmar que usan binds de SQLAlchemy (los repos centralizaron, esto es verificación).
7. **Rate limiting**: verificar cobertura en endpoints sensibles (admin, mercadopago webhook, oauth callback) más allá de `/auth` y `/access`.
8. **Datos sensibles en logs**: patentes, emails, tokens MP en `logger`/toasts.

### Criterios de aceptación
- Checklist abierto/cerrado por ítem con evidencia (línea:archivo).
- Sin hallazgo crítico sin recomendación explícita.

### Herramientas
`curl`, revisión manual de código, lista OWASP API Top 10.

---

## A2 — Auditoría de Dependencias y Supply Chain

**Prioridad:** Alta · **Esfuerzo:** 0.5–1 día · **Entregable:** `Info proyecto/AUDITORIA_DEPENDENCIAS.md`

> **Estado: HECHO** (informe 2026-09-19) — P1+P2 aplicadas: bump starlette 0.52.1→1.6.0 y cryptography →50.0.1; queda 1 sola vuln (`ecdsa`, sin fix, no explotable). `pip check` limpio.

### Objetivo
Identificar CVEs, paquetes obsoletos o de doble versión en el entorno (Python 3.14.7).

### Alcance
- `requirements.txt` (55 líneas), venv instalado, `alpr/ocr_engine.py` (RapidOCR/PaddleOCR)

### Pasos
1. `python -m pip install pip-audit` → `python -m pip-audit -r requirements.txt` y sobre el venv (`--disable-pip`).
2. `pip check` para dependencias rotas (doble versión de numpy, etc.).
3. Revisar manualmente las fijaciones problemáticas: `numpy` (marker por versión de Python), `passlib 1.7.4` + `bcrypt 5.0.0` (compatibilidad conocida), `paddleocr==3.7.0` (solo < 3.14), `opencv-python`.
4. Evaluar separar `paddleocr`/`rapidocr` a extras opcionales (`requirements-ocr.txt`) para que la base sea menos frágil.
5. Documentar decisión de marcadores Python version.

### Criterios de aceptación
- Tabla paquete/versión/CVE/severidad/remedio.
- Nada de severidad crítica/alta sin plan de remediación.

### Herramientas
`pip-audit`, `pip check`, `pipdeptree`.

---

## A3 — Auditoría de Cobertura de Tests

**Prioridad:** Alta · **Esfuerzo:** 1 día · **Entregable:** `Info proyecto/AUDITORIA_COBERTURA.md`

> **Estado: HECHO (2026-09-20)** — suite a **66% de cobertura** (7044/2424), **271 tests / 33 archivos en verde**. Se escribieron los ítems #1–#10 (117 tests) + test de regresión de CSP. Umbral sugerido para CI: `--cov-fail-under=65`. Pendiente: A5 y ronda payments/auth.

### Objetivo
Medir % de cobertura por capa y detectar las zonas sin tests.

### Alcance
- `tests/` (33 archivos, 271 tests) vs `services/`, `routes/`, `repositories/`, `alpr/`, `core/`

### Pasos
1. Instalar `pytest-cov` y `coverage`; ejecutar `pytest --cov=services --cov=routes --cov=repositories --cov=alpr --cov=core --cov-report=html:coverage_html`.
2. Ranking por módulo: identificar los que están < 60%.
3. Cruzar contra los flujos críticos: ALPR (reconocimiento, consenso, cooldown, hallucination), workers (limpieza, notificaciones), views (renderizados), mercadopago webhook, oauth callback.
4. Producir lista priorizada de "primeros 10 tests a escribir".
5. Considerar umbral mínimo en CI si se reactiva el workflow (`ci.yml.disabled`, GHA).

### Criterios de aceptación
- Reporte HTML navegable + resumen numérico por módulo.
- Lista de gaps con prioridad.

### Herramientas
`pytest-cov`, `coverage`.

---

## A4 — Auditoría de Datos y Migraciones (SQL)

**Prioridad:** Alta · **Esfuerzo:** 1 día · **Entregable:** `Info proyecto/AUDITORIA_DATOS_MIGRACIONES.md`

> **Estado: HECHO (2026-09-19, P1; 2026-09-27, P2)** — P1 aplicada: flujo único `sync_schema()` (`create_all` de modelos + Alembic al head) en `core/database.py`; eliminados los `ALTER TABLE` manuales de `init_db.py:migrate_db()`. **P2 aplicada (2026-09-27):** baseline auténtico en `alembic/versions/c833a3129266_initial_schema.py` (16 tablas base + índices), `d4f7c8e2a190` y `e6f7a8b9c0d1` ajustadas a batch-mode/`nullable` para que `alembic upgrade head` sea reproducible desde BD vacía; deuda A4.6 liquidada (2 parches de datos removidos de `core/seed.py`). Verificado: BD vacía → `upgrade head` EXIT 0, 18 tablas, schema **idéntico** a `create_all` (0 diffs), `alembic current == head`. Detalle en `AUDITORIA_DATOS_MIGRACIONES.md`.

### Objetivo
Garantizar que Alembic `upgrade head` sea reproducible de cero en Neon y SQLite, y que no se registren datos sensibles.

### Alcance
- `alembic/` (~40 migraciones), `core/database.py`, `core/seed.py`, Neon (prod) vs SQLite (dev)

### Pasos
1. En sandbox: BD SQLite vacía → `init_db.py` (flujo único `create_all` + Alembic al head) → seed; verificar sin errores.
2. Comparar `alembic history` entre local y Neon (`alembic current` en cada una); detectar heads duplicados o ramas.
3. Revisar migraciones con data de usuario: `49a240f0fc25` (dropea `backend_time`), `c9d8e7f6a5b4` (mercadopago), `b7e3a1d2c4f5` (user_sessions) — verificar idempotencia y que no toquen filas sensibles.
4. Auditar que ningún update legado (ej. limpieza de prefijo `"AUTOPASS "` en promotions) quede como operación manual sin migración.
5. Confirmar que el código con `backend` DATABASE_URL en `core/config.py` sea solo `sqlite:///./parking.db` para dev y que en prod no se use SQLite.
6. Duplicados de seed: `core/seed.py` vs `scripts/init_db.py` — unificar (el inicializador real es `init_db.py` en la raíz).

### Criterios de aceptación
- `upgrade head` verde desde BD vacía en ambos motores **(resuelto P2: baseline real en `c833a3129266`; verificado `upgrade head` desde SQLite vacía = schema de `create_all`, 0 diffs; ver `AUDITORIA_DATOS_MIGRACIONES.md`, §4.2)**.
- Lista de migraciones pendientes de aplicar en Neon, si las hay.

### Herramientas
`alembic current/history/heads`, SQLite local, Neon sandbox.

---

## A5 — Auditoría de Rendimiento (profiling)

**Prioridad:** Media · **Esfuerzo:** 1–2 días · **Entregable:** `Info proyecto/AUDITORIA_RENDIMIENTO.md`

> **Estado: HECHO (2026-09-27, CERRADA ✓)** — profiling con volumen sintético
> (SQLite sandbox + hook `before_cursor_execute`). Hot spot O(N²) de
> `financial-summary` corregido vía índice compuesto (`cdb7d130c856`): 217.3s → 1.86s.
> **Pendientes P1 remediados (2026-09-27):** historial de accesos con límite
> server-side + dedupe (crash de IN 60k → 200 OK/104ms) y cleanup de vencidas
> en batch (`get_reserva_ids_with_entry`, 2.003 queries → 4). Restan P2 anotados
> en §6 del informe.

### Objetivo
Detectar N+1 y latencias en los agregados más usados del dashboard admin y portal.

### Alcance
- `routes/parking/status.py`, `routes/admin/reservations.py`, `routes/admin/users.py`, `services/report_service.py`, `routes/user/fidelization.py`

### Pasos
1. Con datos de prueba cargados, medir con `py-spy` o logs de timing (ya existe `ocr_time`/timing en access_logs) los endpoints: `/v1/parking/status`, `/v1/admin/reservations`, `/v1/reports/financial-summary`, `/v1/admin/users`, `/v1/user/redemption-tickets`.
2. Contar queries por request (hook SQLAlchemy `before_cursor_execute` o SQLAlchemy `echo`) y detectar N+1 en listados paginados.
3. Verificar uso de `selectinload`/`joinedload` en repositorios y del `SimpleTTLCache` (5s) en tarifas.
4. Revisar índices existentes vs queries más frecuentes (`access_logs`, `reservations`, `support_ticket_messages`, `vehicles`, `redemption_tickets`).
5. Probar WS `/v1/parking/ws` bajo +50 clientes (broadcast de ocupación) para detectar bloqueo del event loop.

### Criterios de aceptación
- Reporte con tiempos antes/después y query-count por endpoint.
- Ningún endpoint de listado con N+1 sin anotar.

### Herramientas
`py-spy`, SQLAlchemy echo, `locust` (opcional), `chrome devtools` network.

---

## A6 — Auditoría de Consistencia Frontend/Backend

**Prioridad:** Media · **Esfuerzo:** 1 día · **Entregable:** `Info proyecto/AUDITORIA_CONSISTENCIA_FRONT.md`

> **Estado: HECHO (2026-09-27, CERRADA ✓)** — entregable `_tools/check_consistencia_frontend.py` (extractor ejecutable) + `_tools/_a6_openapi.json` (dump OpenAPI, 128 paths). Resultado: 13 ocurrencias / 11 rutas únicas, **0 faltantes**, 128 rutas backend registradas. Verificaciones formales en el informe.

### Objetivo
Que todo endpoint que llama el JS exista con ese método/path, y que los campos leídos estén en los response models.

### Alcance
- `static/js/**` (9 bridges + 62 módulos) vs `routes/**` (31 archivos) y `schemas/**`

### Pasos
1. Extraer con grep todas las urls `/v1/...` (y `/ws/...`) de `static/js` y `templates`.
2. Cruzar contra la tabla de rutas real (método + path) generada desde FastAPI (`app.openapi()['paths']` en un script).
3. Listar: rutas llamadas que no existen, métodos mal usados, y variantes (`{id}` vs `{patente}` vs `{user_id}`).
4. Para los endpoints OK, verificar que los campos que consume el JS (`.data.xxx`) estén en el schema de respuesta (grep de `response_model`).
5. Revisar versionado de assets `?v=` consistente (v9.23.0) contra la precache de `sw.js`.

### Criterios de aceptación
- Tabla ruta-JS / ruta-backend / estado (OK, faltante, mismatch).
- Cero llamadas a rutas inexistentes.

### Herramientas
Script de extracción de rutas, `app.openapi()`, grep.

---

## A7 — Auditoría de Errores y Manejo de Excepciones

**Prioridad:** Media · **Esfuerzo:** 0.5 día · **Entregable:** `Info proyecto/AUDITORIA_ERRORES.md`

> **Estado: HECHO (2026-09-22)** + **verificación formal 2026-09-27**: grep `^\s*except\s*:` en `*.py` (excl. venv/.git) → **0 ocurrencias**. Checklist y verificación en el informe (§Verificación formal).

### Objetivo
Eliminar excepciones cegadas, logs sin contexto y mensajes que filtren internals.

### Alcance
- `services/*.py` (19), `routes/*.py`, `core/logger.py`

### Pasos
1. Grep de `except:` desnudos y `except Exception` sin `logger.exception`/`logger.error` con contexto.
2. Revisar mensajes de error devueltos al cliente: que no incluyan stack traces, SQL ni rutas del servidor.
3. Consistencia de códigos: 400/404/409/422/503 según dominio (uso de `HTTPException` vs `JSONResponse`).
4. Verificar que los toasts del front no muestren el mensaje crudo del backend en inglés (si aplica, mapear a mensajes amigables).

### Criterios de aceptación
- Cero `except:` sin log con contexto en services/routes.
- Checklist de códigos por endpoint crítico.

### Herramientas
grep + revisión manual.

---

## A8 — Auditoría de Accesibilidad / UX

**Prioridad:** Baja · **Esfuerzo:** 1 día · **Entregable:** `Info proyecto/AUDITORIA_ACCESIBILIDAD.md`

> **Estado: HECHO (2026-09-22)** — informe con checklist OK/NO por plantilla y fixes de alto impacto; evidencia en `AUDITORIA_ACCESIBILIDAD.md`.

### Objetivo
Cumplir un nivel WCAG 2.1 AA razonable sin romper el design system.

### Alcance
- `templates/*` (51), `static/css/**` (42)

### Pasos
1. Contrastes: texto sobre fondo oscuro (dorado `#C5A059`, violeta, grises) — probar con herramienta de contraste.
2. Foco visible: revisar `:focus`/`:focus-visible` en botones, FAB, modales.
3. Labels: inputs de formularios (login, registro, vehículos, reservas) con `label`/`aria-label`.
4. Navegación por teclado en modales (Esc, foco inicial, trap en dropdown de notificaciones).
5. Roles ARIA en componentes: toasts, tabs del dashboard, tooltips de tour.

### Criterios de aceptación
- Informe por plantilla con elementos OK/NO.
- Fixes de alto impacto (contraste + foco + labels).

### Herramientas
Lighthouse (Chrome), axe-core, contraste manual.

---

## A9 — Auditoría de Seguridad Frontend (XSS)

**Prioridad:** Baja · **Esfuerzo:** 0.5 día · **Entregable:** `Info proyecto/AUDITORIA_XSS.md`

> **Estado: HECHO (2026-09-22)** + **verificación formal 2026-09-27**: `_tools/check_xss_innerhtml.ps1` (scan automatizado): 177 innerHTML/insertAdjacentHTML, 25 interpoladas, 23 sin escape en la misma línea → todas datos server-side (BAJO). Evidencia en el informe (§Verificación).

### Objetivo
Verificar que el uso de `innerHTML` con datos del backend esté sanitizado.

### Alcance
- `static/js/modules/**` (62), 9 bridges

### Pasos
1. Grep de `.innerHTML`/`insertAdjacentHTML` y clasificar por origen del dato (usuario vs server).
2. Para los que insertan datos de usuario (promos, tickets, notificaciones, mensajes de soporte, nombres de sucursal), exigir escape o uso de `textContent`/creación de nodos.
3. Revisar atributos href/onclick construidos con data (`voucher-address-link`, mapas).
4. Verificar `html2canvas useCORS` (ya en profile.js / reservas-pass.js) no exponga datos en canvas taint.

### Criterios de aceptación
- Tabla origen/sanitización/estado por ocurrencia.
- Cero innerHTML con datos de usuario sin escapar.

### Herramientas
grep + revisión manual.

---

## AN — Auditoría de Nomenclatura de Archivos

**Prioridad:** Media · **Esfuerzo:** 1 día · **Entregable:** `Info proyecto/AUDITORIA_NOMENCLATURA_ARCHIVOS.md`

> **Estado: HECHO (2026-09-27)** — calificación **8.2→9.0/10**. Remediación **P0/P1 APLICADA** (v9.34.42): renames de assets con espacios (barrera alta/baja), docs (`LINK_BACKLOG`, `EXPLICACION_CODIGO`, `README`, `hardware/`), 4 módulos JS a kebab-case, 3 CSS a kebab-case y `nuestra_red.html` (template) + todas las referencias funcionales y documentales actualizadas; baseline inline regenerado, `node --check` OK, suite 695 passed. Queda **P2 spanglish como deuda técnica aceptada** (ver §5/§6 del informe).

### Objetivo
Uniformar nombres de archivos, carpetas y assets para garantizar portabilidad (Linux/Docker/CI), URLs sin encoding y coherencia por capa.

### Alcance
- 334 archivos de código, configuración, plantillas, documentación y assets (excl: venv, `.git`, cachés, uploads)

### Pasos
1. Inventario de nombres por capa (Python, JS, CSS, templates, docs, scripts) y detección de espacios.
2. Detectar `snake_case`/`kebab-case` anomalos en JS/CSS/templates frente a la convención predominante de cada capa.
3. Detectar hibridación lingüística (backend inglés ↔ frontend español, Spanglish) y asimetrías semánticas.
4. Producir plan de normalización priorizado (P0 assets críticos → P1 unificación de convención → P2 regla de estilo en `AGENTS.md`).

### Criterios de aceptación
- Matriz de discordancias por nivel de severidad con ubicación exacta.
- Plan de remediación con renames concretos (origen → destino) y referencias a actualizar.

### Herramientas
grep/ls por capa, revisión manual del árbol.

---

## Orden de ejecución sugerido

1. ~~**A1** Seguridad API (mayor riesgo, base para A9).~~ — **HECHO** (remediación P0/P1 aplicada).
2. ~~**A4** Migraciones (puede romper prod sin aviso).~~ — **HECHO** (P1 y P2 aplicadas).
3. ~~**A2** Dependencias (CVEs en OCR).~~ — **HECHO** (P1+P2 aplicadas).
4. ~~**A3** Cobertura (define dónde escribir tests nuevos).~~ — **HECHO** (66%, 271 tests).
5. ~~**A6/A7** (consistencia y errores).~~ — **HECHO** (2026-09-27, verificaciones formales incluidas).
6. ~~**A8/A9** según disponibilidad.~~ — **HECHO** (A8 2026-09-22; A9 2026-09-22 + verificación automática 2026-09-27).
7. ~~**A5** Rendimiento (profiling).~~ — **HECHO (2026-09-27, CERRADA ✓)** — profiling con volumen sintético (SQLite sandbox + hook `before_cursor_execute`): O(N²) de `financial-summary` resuelto (217s→1.9s), cleanup de vencidas acelerado con índice, N+1 anotados y priorizados. Mediciones con volumen real de Neon quedan como pendiente explícito del informe.

> Cada auditoría se marca como **HECHO** al dejar su informe en `Info proyecto/` y actualizar este `PLAN_AUDITORIAS.md` (estado → "resuelta"). **A1–A9 cumplidas (todas CERRADAS).** Pendientes P1 de A5 remediados (2026-09-27); restan **A5-P2** (paginado server-side del historial si el front crece, caché broadcast WS) y **A5-P2** del desfase `ix_access_logs_id`, anotados en `AUDITORIA_RENDIMIENTO.md` §6.