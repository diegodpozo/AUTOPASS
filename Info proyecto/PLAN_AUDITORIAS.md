# Plan de Auditorías — AUTOPASS

> Documento de planificación. Estado: **en ejecución** — **A1–A4 HECHO** (informes en `Info proyecto/`), pendientes **A5–A9**. Además se ejecutó `Info proyecto/AUDITORIA_MODULARIZACION.md` (resuelta, 10/10), fuera del plan.

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

> **Estado: HECHO (2026-09-19)** — P1 aplicada: flujo único `sync_schema()` (`create_all` de modelos + Alembic al head) en `core/database.py`; eliminados los `ALTER TABLE` manuales de `init_db.py:migrate_db()`. Verificado: BD vacía → 19 tablas + `alembic current == head`.

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
- `upgrade head` verde desde BD vacía en ambos motores **(resuelto: flujo único `create_all` + `alembic current == head`; ver `AUDITORIA_DATOS_MIGRACIONES.md`, remediación P1 aplicada)**.
- Lista de migraciones pendientes de aplicar en Neon, si las hay.

### Herramientas
`alembic current/history/heads`, SQLite local, Neon sandbox.

---

## A5 — Auditoría de Rendimiento (profiling)

**Prioridad:** Media · **Esfuerzo:** 1–2 días · **Entregable:** `Info proyecto/AUDITORIA_RENDIMIENTO.md`

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

## Orden de ejecución sugerido

1. ~~**A1** Seguridad API (mayor riesgo, base para A9).~~ — **HECHO** (remediación P0/P1 aplicada).
2. ~~**A4** Migraciones (puede romper prod sin aviso).~~ — **HECHO** (P1 aplicada).
3. ~~**A2** Dependencias (CVEs en OCR).~~ — **HECHO** (P1+P2 aplicadas).
4. ~~**A3** Cobertura (define dónde escribir tests nuevos).~~ — **HECHO** (66%, 271 tests).
5. **A5/A6/A7** en paralelo (sin dependencias entre sí). ← pendiente
6. **A8/A9** según disponibilidad.

> Cada auditoría se marca como **HECHO** al dejar su informe en `Info proyecto/` y actualizar este `PLAN_AUDITORIAS.md` (estado → "resuelta"). A1–A4 cumplido; sigue **A5 (rendimiento)**.