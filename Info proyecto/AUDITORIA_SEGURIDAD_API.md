# Auditoría de Seguridad de la API — AUTOPASS

> **Fecha:** 2026-09-19 (revisión contra código v9.23.0, rama `main`)
> **Alcance:** autenticación (JWT/refresh/logout/bloqueo), autorización (roles, RBAC), transporte (headers, CORS, WebSockets), rate limiting e inyección SQL. No se audita XSS frontend (es A9) ni dependencias (es A2).
> **Metodología:** análisis estático de código, greps de patrones (headers, SQL crudo, rate limits, logs con PII), revisión manual de `core/security.py`, `core/config.py`, `core/limiter.py`, `main.py`, `routes/auth.py`, `routes/parking/*`, `routes/system/video.py`, `routes/system/common.py`, `routes/admin/users.py`, `routes/user/mercadopago.py`, `repositories/user_repository.py`.
> **Checklist OWASP API Top 10** aplicado a los vectores del alcance.
> **Actualización 2026-09-20:** los ítems P0/P1 del plan (§4) quedaron aplicados y verificados: `pay-stay` protegido, video WS autenticado, bloqueo efectivo en `get_current_user`, headers de seguridad y rate-limit del webhook MP. Estado real por ítem en §1.5; checklist cerrado en §3. Riesgo general recalculado: **MEDIO** (era ALTO).

---

## 1. Resumen Ejecutivo

| Dimensión | Estado | Hallazgos |
|---|---|---|
| Headers de seguridad | ~~**OMISO**~~ → **RESUELTO (2026-09-20)** | 0 headers de seguridad al auditarlo (sin CSP, HSTS, X-Frame-Options, X-Content-Type-Options). Solo CORS + GZip (`main.py:57-63`). **Hoy:** `security_headers_middleware` en `main.py:72-101` (CSP/HSTS/XFO/nosniff/Referrer-Policy) |
| JWT | Aceptable c/ deudas | `sub`=email (PII en claims), sin `iat`/`jti`, TTL 24h sin revocación, SECRET_KEY demo sin guard de arranque |
| Recuperación (reset) | Correcto | Token con `purpose="recovery"` validado (`auth.py:85-93`); TTL 30 min |
| Cierre de sesión / bloqueo | **Defectuoso** | No hay endpoint de logout en backend (solo front). `toggle-block` NO invalida tokens activos; `get_current_user` no chequea `is_blocked` |
| CORS | Débil | `ALLOWED_ORIGINS="*"` por defecto con `allow_methods/headers=["*"]` (`config.py:20`) |
| WebSockets | **Defectuoso** | `/ws/video/{id}` acepta nodos anónimos que pueden difundir frames; `POST /update-frame/{id}` público; WS no exige rol STAFF+ (inconsistente con `/video-feed`) |
| Autorización de acceso ALPR | **Expuesto** | `/access/validate-plate`, `/access/exit-plate`, `/access/pay-stay` **sin autenticación** (pay-stay muta deuda sin validar identidad) |
| Inyección SQL | **OK** | 0 usos de `text()/exec_driver_sql/raw` en services/routes; todo vía repositorios con binds de SQLAlchemy |
| Rate limiting | Parcial | Default 300/min global; cobertura fina solo en `/auth` y `/access`; faltan `pay-stay`, webhook MP, admin |
| PII en logs | Débil | Emails de usuarios en logs INFO (WS, workers, email); sin enmascarado |

**Nivel de riesgo general: ALTO** — 2 hallazgos críticos (`pay-stay` sin auth y broadcast de video anónimo), 2 altos (bloqueo no efectivo y nodo WS anónimo) y varios medios. La base JWT/BCrypt/parametrización está bien puesta; las mutaciones críticas de negocio (pagos, video, barreras) carecen de autenticación.

> *Estado original detectado el 2026-09-19. Ver §1.5 para el estado post-remediación.*

---

## 1.5 Estado de remediación (2026-09-20)

Los ítems P0/P1 del plan (§4) quedaron aplicados. Estado por ítem del checklist (§3):

| # | Ítem | Estado (2026-09-20) | Evidencia |
|---|---|---|---|
| 1 | Headers de seguridad | **RESUELTO** | `main.py:72-101` `security_headers_middleware`: `Content-Security-Policy` con `default-src 'self'`, `script/style/font-src` con CDNs (cdnjs, jsdelivr, unpkg, npmcdn) y fuentes de Google, `img-src` con tiles de Google, `connect-src` con `ws:/wss:`, Overpass, Nominatim y CDNs; HSTS (solo tras TLS), `X-Frame-Options: DENY`, `nosniff`, `Referrer-Policy`. Directivas agrupadas en constantes `CSP_CDNS`/`CSP_GOOGLE_FONTS`/`CSP_MAP_APIS`/`CSP_HEADER`. Test de regresión: `tests/test_security_headers.py` |
| 2 | JWT `iat`+`jti`, guard SECRET_KEY, `token_type` | PENDIENTE | `core/security.py:32-48` sin `iat`/`jti`; `core/config.py:17` mantiene el default demo `tu_super_secreto_para_produccion` sin guard de arranque |
| 3 | `get_current_user` rechaza `is_blocked` | **RESUELTO** | `core/security.py:71,107` (`hasattr(user,'is_blocked') and user.is_blocked` → 403); login bloqueado en `routes/auth.py:235`; mercadopago/reservas también validan (`routes/user/mercadopago.py:20`, `routes/user/reservations.py:89`) |
| 4 | `POST /v1/auth/logout` revoca sesión | PENDIENTE | grep `logout` en `routes/**` → 0 matches; el cierre de sesión sigue siendo solo frontend |
| 5 | CORS con lista explícita | PENDIENTE | `core/config.py:20` `os.getenv("ALLOWED_ORIGINS", "*")` — default abierto |
| 6 | Video WS: nodo autenticado + STAFF+ | **RESUELTO** | `routes/system/video.py:37-74`: WS acepta `token`/`node_secret`, decodifica el token y rechaza espectadores que no sean ADMIN/LOCAL_ADMIN/STAFF (cierre `4403`, `:69-71`); `POST /ws/video/{id}/update-frame` exige `node_secret` (`:84`); nodo ALPR verificado por `_is_trusted_alpr_node` (`:30`) |
| 7 | `pay-stay` (+ALPR) | **PARCIAL** | `pay-stay` protegido: `routes/parking/access.py:31-33` `Depends(get_operational_user)` + `@limiter.limit("10/minute")`. `validate-plate`/`exit-plate` siguen sin auth (nodo ALPR interno, mismo patrón que `notify_camera_reading` en `routes/system/cameras.py:326`) |
| 8 | Rate limits finos | **PARCIAL (mejorado)** | webhook MP `60/minute` (`routes/user/mercadopago.py:69-70`); `pay-stay` `10/minute`; falta el límite fino en endpoints admin |
| 9 | PII en logs INFO | PENDIENTE | sin enmascarado de emails/`payment_id`/`resp.text[:500]` de MP |

**Riesgo general recalculado: MEDIO** — los 2 hallazgos críticos (P0.1 `pay-stay`, P0.2 video) y los 2 altos (bloqueo no efectivo, nodo WS anónimo) quedaron resueltos. Deudas abiertas de severidad media/baja: JWT (2), logout (4), CORS (5), rate-limit admin (8 parcial) y PII en logs (9).

---

## 2. Hallazgos por dimensión

### A1.1 — Headers de seguridad — **[RESUELTO 2026-09-20]** (era OMISO)

**Evidencia:** `main.py:56-70` solo registra `GZipMiddleware` y `CORSMiddleware`, más el middleware de cache de JS. Grep de `Strict-Transport|X-Frame-Options|X-Content-Type|Content-Security|X-XSS|Cross-Origin|Referrer-Policy` → **0 matches** en código.

| Header | Ausente |
|---|---|
| `Content-Security-Policy` | Sí |
| `Strict-Transport-Security` (HSTS) | Sí |
| `X-Frame-Options` | Sí |
| `X-Content-Type-Options: nosniff` | Sí |
| `Referrer-Policy` | Sí |
| `Cross-Origin-Opener-Policy` / `Embedder` | Sí |

**Riesgo:** clickjacking, sniffing MIME (`nosniff`), exfiltración vía mixed content/iframe, y XSS amplificado sin CSP (mitiga en capa transporte lo que A9 detecte a nivel DOM).

**Recomendación:** agregar middleware `SecurityHeadersMiddleware` en `main.py` con:
- `Content-Security-Policy` (default-src 'self'; img-src 'self' data:; connect-src 'self' ws:, wss:; frame-ancestors 'self')
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (solo detrás de TLS)
- `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`
- Probar con `curl -I` tras aplicar.

---

### A1.2 — JWT — **[ACEPTABLE C/ DEUDAS]**

| Ítem | Estado | Evidencia |
|---|---|---|
| Claim `sub` | email | `routes/auth.py:31`, `:175` — expone PII en claims; un cambio de email invalida tokens |
| `exp` | Presente | `core/security.py:39` |
| `iat` | **Ausente** | no se emite; imposible medir vida real del token |
| `jti` | **Ausente** | sin ID de token, no hay blacklist/revocación individual |
| Algoritmo | HS256 forzado | `config.py:18`, `security.py:46,61` decodifica con `algorithms=[ALGORITHM]` (sin confusión de alg) |
| Default TTL | 1440 min (24 h) | `config.py:19` — largo sin capacidad de revocación (ver A1.3) |
| SECRET_KEY | Default demo | `config.py:17`: `"tu_super_secreto_para_produccion"` sin guard de arranque que falle si queda el valor por defecto |
| Recovery token ≠ access | Correcto | `auth.py:85-93` valida `purpose == "recovery"`; TTL 30 min (`config.py:34`) |

**Hallazgo menor:** `decode_access_token` (`security.py:43-48`) no valida `purpose`; los WS que autentican con él (`status.py:141`, `video.py:28`, `_user_from_token` en `video.py:86`) aceptarían un token de recuperación firmado con `sub` válido durante su ventana de 30 min. No se detectó en la práctica, pero conviene emitir `token_type` (`access|recovery`) y rechazar el recovery en dependencias de acceso.

**Recomendación:**
1. Exigir error de arranque en `main.py`/`config.py` si `SECRET_KEY` queda en el valor demo y no está en modo dev.
2. Emitir `iat` + `jti`; usar `jti` para revocación (logout/block) — habilita A1.3.
3. Considerar `sub` = id numérico y mover email a un claim `email` si se necesita (menos PII en el token; además `auth.py` ya firma `{"sub": email}`).

---

### A1.3 — Cierre de sesión / bloqueo — **[PARCIAL 2026-09-20]** (era DEFECTUOSO; bloqueo ✔, sigue sin logout)

**Hallazgo CRÍTICO (alto): el bloqueo de cuenta no revoca sesiones activas.**

- `get_current_user` (`security.py:50-71`) resuelve el usuario por email con `is_deleted == False`, pero **no verifica `is_blocked`** → un usuario bloqueado por `toggle-block` conserva su token vigente (24 h) y sigue accediendo a endpoints protegidos.
- `authenticate_user` (`security.py:101-106`) sí bloquea el *login* de usuarios bloqueados, y `mercadopago.py:19` lo chequea manualmente, pero es la inconsistencia: solo se valida al autenticar, no al usar el token.
- `toggle_user_block` (`routes/admin/users.py:106-130`) solo voltea la columna `is_blocked`; no invalida tokens ni sesiones.

**Hallazgo alto: no existe backend de logout.**

- Grep de `logout|/logout|close_session` en Python → **0 endpoints**. `ui.logout` (`static/js/modules/ui.js:132`) solo hace `localStorage.clear()` y redirige.
- La tabla `UserSession` registra dispositivos en login (`auth.py:119-157`), pero nunca se invalida al cerrar sesión ni se elimina por token.
- Un token robado (XSS, captura de query, log) no puede revocarse hasta su exp (≈24 h).

**Recomendación:**
1. `get_current_user`: rechazar usuarios con `is_blocked` (401/403) → vuelve efectivo el toggle-block de inmediato (bajo costo, alto impacto).
2. Implementar `POST /v1/auth/logout` que invalide la sesión (y guardar `jti` en blacklist/in-memory o borrar `UserSession` correspondiente) + llamarlo desde `ui.logout()`.
3. Como refuerzo: reducir `ACCESS_TOKEN_EXPIRE_MINUTES` en prod (ej. 60–120) mientras no exista revocación.

---

### A1.4 — CORS — **[DÉBIL]**

**Evidencia:** `core/config.py:20` → `ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")`; `main.py:58-63` con `allow_methods=["*"]`, `allow_headers=["*"]`, sin `allow_credentials`.

- Con `"*"` + métodos/headers `"*"`, cualquier sitio puede leer respuestas de la API desde el navegador (aunque el app es same-origin en operación normal, la API queda abierta a llamadas cross-origin).
- La app sirve frontend y API desde FastAPI; en prod debería fijarse lista explícita (dominio de la PWA) o reflejar `Origin`.

**Recomendación:** en `config.py`, default seguro: lista vacía o el origen de producción via .env; documentar que `"*"` solo para dev. Si se fija una lista, usar `allow_origins` explícitos y revisar `allow_credentials` sea coherente (hoy no se usan cookies — los tokens van por header).

---

### A1.5 — WebSockets — **[PARCIAL 2026-09-20]** (era DEFECTUOSO; video ✔, queda token-en-query en WS de ocupación)

**Hallazgo CRÍTICO: el video WS y el endpoint de frames son accesibles en modo anónimo y permiten difundir contenido.**

- `routes/system/video.py:34-44` — WS `/ws/video/{camera_id}`: si no hay `token` (o es inválido), **acepta la conexión como "Nodo ALPR"** y cualquier frame que reciba lo re-difunde por `manager.broadcast_frame` a los espectadores de esa cámara. Un atacante puede suplantar video (spoofing) o saturar.
- `routes/system/video.py:56-61` — `POST /update-frame/{camera_id}` es **100% público** (sin auth, sin rate limit propio): cualquiera puede inyectar frames en el feed en vivo.
- `manager` (`routes/system/common.py:42-90`) valida sucursal para espectadores no-admin (`:46`), pero **no valida rol**: un USER logueado (cliente) puede ver video de su sucursal, mientras `/video-feed` legacy exige `get_operational_user` (`video.py:64`). Inconsistencia de autorización.
- `GET /ws/video` usa `get_by_email` (`video.py:30`) sin filtrar `is_deleted` (vs `security.py:68`), e `/_user_from_token` (`video.py:89`) sí usa `get_active_by_email` — criterios divergentes en el mismo archivo.

**WS de ocupación (`routes/parking/status.py:134-166`):**
- Token en query `?token=` (queda en logs de proxy/acceso). Valida decode + `get_by_email` (`status.py:141-146`), pero **no exige rol operativo**: cualquier cliente con token recibe `BRANCH_UPDATE`/`GLOBAL_UPDATE` con ocupación y reservas (dato semi-público vía `/parking/branches`, pero el WS expone detalle de capacidades).
- Usa `get_by_email` (`status.py:143`) sin filtro `is_deleted` (un usuario borrado con token vigente re-conectaría).

**Recomendación:**
1. `POST /update-frame/{camera_id}` y el modo "Nodo ALPR": autenticar por token de nodo (device secret) o restringir por IP/localhost; nunca aceptar broadcast anónimo.
2. Exigir rol STAFF+ en el WS espectador (alinear con `/video-feed`); validar `is_deleted`/`is_blocked` con repositorio activo.
3. Para `/ws/video` aceptar token en header `Sec-WebSocket-Protocol`/`Authorization` además de query, y eliminar token de query.

---

### A1.6 — Inyección SQL — **[OK]**

**Evidencia:** grep de `\.text\(|exec_driver_sql|raw\(` → **0 matches** en todo el repo. `services/report_service.py`, `routes/admin/*` y repositorios usan `db.query` de SQLAlchemy con parámetros vinculados. No se construye SQL concatenado.

**Estado:** sin hallazgo.

---

### A1.7 — Rate limiting — **[PARCIAL — MEJORADO 2026-09-20]**

**Evidencia:** `core/limiter.py:7` → global `300/minute` por IP. Límites finos solo en:

| Grupo | Límites |
|---|---|
| `/v1/auth/*` | frozen: register 10/min, forgot 5/min, reset 10/min, login 15/min, oauth 10/min (`auth.py:45,58,79,106,196,257`) |
| `/v1/access/*` | validate/exit 120/min, validate-qr 60/min (`access.py:13,19,25`) |
| `pay-stay` | **sin límite propio** (usa default 300/min) |
| Webhook MP | **sin límite propio** |
| Admin/CRUD | **sin límites finos** (usa default) |

**Hallazgo:** `routes/parking/access.py:30-35` — `POST /access/pay-stay` no tiene `@limiter.limit` y además está sin autenticar (ver A1.8); combinado con el default 300/min da 300 intentos/min por IP.

**Recomendación:** aplicar límites finos a `pay-stay` (ej. 10/min), webhook MP (ej. 60/min) y endpoints sensibles de admin (ej. 30/min) para no depender solo del default.

---

### A1.8 — Autorización de acceso ALPR y pagos — **[PARCIAL 2026-09-20]** (era EXPUESTO; pay-stay ✔, ALPR sigue público por diseño de nodo)

**Hallazgo CRÍTICO: los endpoints de operación de garita/barrera y pago no requieren autenticación.**

- `routes/parking/access.py:12-22` — `validate-plate`, `exit-plate`, `validate-qr` son públicos (por diseño, los llama el nodo ALPR/garita), pero **cualquiera puede**: fabricar entradas/salidas, falsificar patentes, alterar ocupación y disparar barreras (el servicio publica por MQTT a `parking/barrera/entrada|salida/control`, `config.py:40-41`).
- `routes/parking/access.py:30-35` — `POST /access/pay-stay?plate=XX&metodo=DIGITAL` es **público y sin auth**: un tercero puede marcar como pagada una estadía ajena sin ningún pago real (`BillingService.process_payment` → `billing_service.py:192-295` genera `pago_confirmado`, asigna puntos de fidelidad y notifica). Impacto: fraude directo sobre deuda y acreditación de puntos.

> Nota: el flujo diseñado prevé que ALPR/garita corran en red local; si el servicio se expone a Internet (túnel MP, despliegue en la nube), estos endpoints quedan abiertos al público. Severidad depende del despliegue, pero el **riesgo de configuración es real** y `pay-stay` es abusable en cualquier red alcanzable.

**Recomendación:**
1. `pay-stay`: exigir autenticación operativa (`get_operational_user`) o un secreto de garita/nodo local; nunca exponerlo sin auth.
2. Para ALPR (validate/exit/QR): autenticar por token de nodo (device secret) o restricción de IP; idealmente firmar cada lectura.
3. Auditar `access_service.py` para confirmar que el disparo de barrera dependa de una validación autenticada (actualmente la puerta de entrada es este router público).

---

### A1.9 — PII en logs — **[DÉBIL]**

**Evidencia de logs con datos personales:**

| Ubicación | Dato |
|---|---|
| `routes/parking/status.py:34` | `user={email}` al conectar WS |
| `routes/system/video.py:46,53` | `user={email}` en espectador de video |
| `services/worker_service.py:159` | `user.email` en recordatorio de reserva |
| `services/email_service.py:54,56` | email destino de correos |
| `services/mercadopago_service.py:49` | `resp.text[:500]` de la API de MP (puede incluir datos del pago) |
| `routes/user/mercadopago.py:81` | `payment_id` |

**Estado:** no se loguean passwords ni tokens (bien); no hay enmascarado ni nivel dedicado de auditoría. `core/logger.py` imprime a stdout.

**Recomendación:** para clientes (rol USER) evitar loguear emails en INFO; usar ids/últimos 3 caracteres, o configurar un logger de auditoría separado. Enmascarar PII en `mercadopago_service.py:49`.

---

## 3. Checklist de cierre

| Ítem | Estado |
|---|---|
| 1 · Headers de seguridad CSP/HSTS/XFO/nosniff en `main.py` | ✔ [RESUELTO 2026-09-20] `main.py:72-101` + `tests/test_security_headers.py` |
| 2 · JWT `iat`+`jti`, guard de SECRET_KEY demo, validar `token_type` | [ ] pendiente |
| 3 · `get_current_user` rechaza `is_blocked` | ✔ [RESUELTO 2026-09-20] `core/security.py:71,107` |
| 4 · `POST /v1/auth/logout` revoca sesión + jti | [ ] pendiente |
| 5 · CORS con lista explícita por entorno | [ ] pendiente |
| 6 · Video WS: nodo ALPR autenticado, `update-frame` protegido, rol STAFF+ en espectador | ✔ [RESUELTO 2026-09-20] `routes/system/video.py:37-93` |
| 7 · `pay-stay` y endpoints ALPR con auth de nodo | ◐ [PARCIAL 2026-09-20] `pay-stay` ✔ (`access.py:31-33`); `validate/exit-plate` sin auth (nodo interno) |
| 8 · Rate limits finos en `pay-stay`, webhook MP, admin | ◐ [PARCIAL 2026-09-20] `pay-stay` 10/min ✔, webhook MP 60/min ✔; falta admin |
| 9 · Sin PII de clientes en logs INFO | [ ] pendiente |

---

## 4. Plan de remediación priorizado

1. **[P0]** Autenticar `POST /access/pay-stay` (+ límite 10/min) — evita fraude directo. — **APLICADO (2026-09-20):** `routes/parking/access.py:32-33` `Depends(get_operational_user)` + `@limiter.limit("10/minute")`.
2. **[P0]** Proteger `POST /update-frame/{camera_id}` y el modo "Nodo ALPR" del WS de video — evita spoofing del feed. — **APLICADO (2026-09-20):** `routes/system/video.py` — `node_secret` requerido en `update_frame_http` (`:84`) y verificación `_is_trusted_alpr_node` (`:30`).
3. **[P1]** `get_current_user`: rechazar `is_blocked` — hace efectivo el toggle-block de inmediato. — **APLICADO (2026-09-20):** `core/security.py:71,107`.
4. **[P1]** Header middleware de seguridad (`main.py`). — **APLICADO (2026-09-20):** `security_headers_middleware` con CSP/HSTS/XFO/nosniff/Referrer-Policy (`main.py:72-101`).
5. **[P1]** Rate limits finos en webhook MP y admin. — **APLICADO PARCIAL (2026-09-20):** webhook MP `60/min` (`routes/user/mercadopago.py:70`); falta el fino en admin.
6. **[P2]** Endpoint de logout + revocación (`UserSession`, `jti`/blacklist).
7. **[P2]** `iat`/`jti` en JWT y guard de arranque para SECRET_KEY demo.
8. **[P2]** CORS y WS: lista explícita, rol STAFF+ en espectador, repositorios activos (is_deleted/is_blocked) en WS.
9. **[P3]** Enmascarar PII en logs INFO.

> Los ítems P0–P1 son de bajo costo y alto impacto (cambios de 1–15 líneas c/u). Las auditorías A4 (migración) y A2 (deps) siguen al cierre de estos.