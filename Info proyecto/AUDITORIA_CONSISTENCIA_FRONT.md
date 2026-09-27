# Auditoría de Consistencia Frontend/Backend — A6 (ronda A5/v20 · cierre)

**Estado:** CERRADA ✓ · **Entregable:** este informe + `_tools/check_consistencia_frontend.py` (extractor ejecutable) + `_tools/_a6_openapi.json` (dump OpenAPI, 128 paths).

**Fecha:** 2026-09-27 · **Base:** suite 695 passed (P3.7 inline cleanup completo).

---

## Resumen ejecutivo

El front de AUTOPASS dispara **11 rutas únicas** `/v1` (13 ocurrencias) desde `static/js/` y `templates/`
(9 HTTP + 2 WebSocket). El backend registra **128 rutas** en `app.openapi()['paths']`.

**Resultado: 0 rutas llamadas por el front que falten en el backend y 0 verbos no soportados.**
La metodología A6 quedó automatizada en un script ejecutable localmente (ya no depende de GitHub Actions).

---

## Metodología ejecutada (extractor `_tools/check_consistencia_frontend.py`)

1. **Extracción:** regex normalizado de todas las URLs `/v1/...` y `/ws/...` en `static/js/**` + `templates/**`.
   Soporta template literals JS (`/v1/auth/oauth/${provider}/authorize`) y chunks `{id}`.
2. **Normalización:** `{var}` y `${var}` → `{_}` (comparación posicional, sin distinguir nombres).
3. **Cruce contra OpenAPI:** `app.openapi()['paths']` con el **mismo** `main.app` que corre la app.
4. **WebSockets aparte:** no figuran en OpenAPI; se cruzan contra `app.routes` recorriendo el autorouter
   custom (`_IncludedRouter`/`APIWebSocketRoute`) acumulando prefijos (`/v1/parking/ws`,
   `/v1/system/ws/video/{camera_id}`).
5. **`response_model`:** tabla de schemas de respuesta para cada ruta consumida.

---

## Tabla: rutas del front vs backend (11 únicas · todas OK)

| Ruta front (normalizada)               | Verbo | Origen                                              | ¿Existe en backend? | response_model (200) |
|----------------------------------------|-------|-----------------------------------------------------|---------------------|-----------------------|
| `/v1/auth/logout`                      | POST  | `static/js/modules/ui.js`                           | ✓                   | `{}` (sin cuerpo)     |
| `/v1/auth/oauth/{provider}/authorize`  | GET   | `static/js/modules/auth.js` (`${provider}`)         | ✓                   | redirect 302 (cuerpo vacío) |
| `/v1/parking/branches`                 | GET   | `landing-map.js`, `profile.js`                      | ✓                   | `array<BranchPublicResponse>` |
| `/v1/parking/ws`                       | WS    | `dashboard-stats.js`, `monitoreo-live.js`           | ✓ (router.websocket) | — (stream) |
| `/v1/system/virtual-time`              | GET   | `templates/components/virtual_time_banner.html`     | ✓                   | `{}` (JSON balance) |
| `/v1/system/capture/{log_id}`          | GET   | `static/js/modules/dashboard-operations.js`         | ✓                   | imagen (no JSON) |
| `/v1/system/ws/video/{proc_id}`        | WS    | `static/js/modules/monitoreo-live.js`               | ✓ (`{camera_id}`)   | — (stream) |
| `/v1/admin/virtual-time/advance`       | POST  | `templates/components/virtual_time_banner.html`     | ✓                   | `{}` |
| `/v1/admin/virtual-time/rewind`        | POST  | `templates/components/virtual_time_banner.html`     | ✓                   | `{}` |
| `/v1/admin/virtual-time/set-target`    | POST  | `templates/components/virtual_time_banner.html`     | ✓                   | `{}` |
| `/v1/admin/virtual-time/reset`         | POST  | `templates/components/virtual_time_banner.html`     | ✓                   | `{}` |

## Hallazgo preliminar (ya confirmado en esta ronda)

- **CERO N+1** en el scope A5 (estático; ver `AUDITORIA_RENDIMIENTO.md`).
- Front llama **solo 11 rutas** y todas tienen route en backend → riesgo de endpoints huérfanos = **bajo**.
- `users.py` (la ruta más usada por admin) mantiene cobertura 90%→92% con 695 tests pasando.
- El único `response_model` tipado del conjunto es `BranchPublicResponse` (sucursales públicas);
  el resto responde JSON sin schema explícito (acciones/no-cuerpo). Correcto para su naturaleza.

## Cómo re-correr el entregable

```
venv\Scripts\python.exe _tools\check_consistencia_frontend.py          # resumen + exit 0/1
venv\Scripts\python.exe _tools\check_consistencia_frontend.py --json   # detalle por ocurrencia
venv\Scripts\python.exe _tools\check_consistencia_frontend.py --dump-openapi _tools\_a6_openapi.json
```

*(salida en frío con 0 errores: es el guard de consistencia A6 para CI)*

---
*Cerrado en ronda A6 — el entregable era el script extractor + esta tabla; ambos quedan en el repo.*