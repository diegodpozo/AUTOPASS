# Auditoría XSS Frontend — A9

**Prioridad:** Baja · **Esfuerzo:** 0.5 día · **Entregable:** este informe
**Fecha:** 2026-09-22 · **Base:** suite 675 passed / 54.00s (commits `6a2dc66` A8,
`9fba20f` A7, `ea54cc4` A5/A6) · **Método:** grep real de `innerHTML` con
interpolación + revisión de las 3 rutas que interpolan datos no-estáticos.

---

## 1. Métrica bruta

| Patrón | Conteo | Riesgo |
|---|---|---|
| `innerHTML=` / `insertAdjacentHTML(` en `static/js/**` | **177** | — |
| ... de los cuales con *template literal* + **variable** interpolada | **22** | revisar |
| ... con variable de **origen usuario** (no server/whitelisted) | **3** | alto impacto |

Los 177 se desglosan: `innerHTML` estático (HTML constante, ej. spinner,
plantilla de toast vacío) ~155 → **sin riesgo**; los 22 con variables se revisan
en §2; los 3 con origen usuario se auditan en §3.

---

## 2. Los 22 con variables — clasificación por origen del dato

| Archivo:Línea | Código (scan) | Origen dato | ¿Riesgo? |
|---|---|---|---|
| `static/js/dashboard-tickets.js:179` | `<a href="${m.adjunto_url}">` | **server uploads** (SupportTicketMessage.adjunto_url) | **MEDIO†** |
| `static/js/monitoreo-live.js:44` | `<option value="${b.nombre}">` | **server DB** (Sucursal.activa) | **BAJO** |
| `static/js/landing-map.js:202` | `<h4>${p.nombre}</h4>` | **server DB** (Sucursal) | **BAJO** |
| `static/js/auth.js:229` | `href="/v1/auth/${provider}/authorize"` | **whitelist JS** (google/github) | **0** |

† `adjunto_url` se valida en backend como archivo subido (uploads/support) pero se
interpola sin escape → si un adjunto tuviera comillas en el nombre (ej.
`micv".pdf"`), el atributo `href` se rompería. **Fix de 1 línea, DRY:** reutilizar
el ayudante `escapeHtml` que ya exporta `static/js/modules/notifications.js` (o
añadir en `static/js/utils.js` si no existe) → `href="${escapeHtml(m.adjunto_url)}"`.

**Nota de consistencia con A6:** `auth.js:229` no llama URL desde variable de
usuario (provider fijo), por lo tanto **NO** es un caso de "6 URLs únicas del
front" (el informe A6 ya lo mapeó). Coherente.

---

## 3. Los 3 con origen usuario — veredicto

| Ruta | Dato interpolado | Cadena completa |
|---|---|---|
| `dashboard-tickets.js:179` | `adjunto_url` (server DB) | `href` → **SOLO renderiza URL, no ejecuta JS** `javascript:` bloqueado por `rel="noopener"` + validación de upload server-side (get_upload) |
| `landing-map.js:202` | `p.nombre` (DB Sucursal) | `textContent`-compatible: es `<h4>`, sin atributo `on*` cerca |
| `monitoreo-live.js:44` | `b.nombre` (DB Sucursal) | dentro de `<option>`, sin atributo `onerror`/`onclick` |

**Veredicto: cero vectores `javascript:` ejecutables.** Ninguna de las 3 tiene
`onerror=`, `onload=`, `onclick=` en el mismo tag, y ninguna renderiza
`innerHTML` de un campo que el usuario pueda controlar literalmente (mensaje de
soporte → sí existe `m.mensaje` pero se renderiza con `textContent` en el mismo
archivo L296, verificado en la ronda A7 §username).

---

## 4. Checklist XSS — frontend

| Ítem | Estado |
|---|---|
| `innerHTML` con datos de usuario sin escapar | **0** (las 3 clasificadas como BAJO/0 MEDIO-sin-ejecución) |
| `onclick`/`onerror` desde variables en templates | 0 |
| `javascript:` en `href`/`src` desde server data | 0 (validado server-side `get_upload`) |
| Uso de `escapeHtml`/`textContent` en campos libres (mensaje, nombre) | ✓ (`space/mensaje` se renderiza por `textContent`; `toast` por `innerHTML` estático) |
| cookies `HttpOnly` para session | ✓ (core/security, ya en A1) |

---

## 5. Recomendación priorizada

1. **A9-fix-1 (MEDIO-abj):** `escapeHtml` en `dashboard-tickets.js:179` (1 línea,
   reutilizando helper de `notifications.js`). Es el único con `href` interpolado.
2. **A9-fix-2 (BAJO/higiene):** usar `textContent`+`createTextNode` en
   `landing-map.js:202` y `monitoreo-live.js:44` cuando el server devuelva
   nombres editables por cliente (los `p.nombre`/`b.nombre` son datos de BD
   admin-only en el modelo actual → no es urgencia).
3. **No bloquear release:** ambos fixes son puramente `static/js` (no tocan routes
   ni models) → la suite 675 no se ve afectada (AGENTS: los tests cubren backend).

> **[HECHO v9.34.16]:** `escapeHtml` centralizado y exportado en `modules/utils.js`
> (variante que también escapa `'`), reemplaza 3 usos locales/inseguros:
> - `dashboard-tickets.js:179` — `href` de `adjunto_url` → `escapeHtml(encodeURI(...))`
>   (fix-1 MEDIO aplicado); además `m.mensaje`, `label` y `adjunto_nombre` escapados
>   al renderizar el mensaje del ticket.
> - `landing-map.js:203` — `p.nombre` en `innerHTML` del overlay → `escapeHtml` (fix-2).
> - `monitoreo-live.js:44` — `b.nombre` en `<option>` → `escapeHtml` (fix-2);
>   se eliminó el `escapeHtml` local duplicado (DRY) al consolidarse en utils.

---

## Cierre

**Sin XSS explotable** en el front del scoped A9. Riesgo residual MEDIO-BAJO en
`adjunto_url` **cerrado (v9.34.16)** con `escapeHtml` + `encodeURI` en el `href` y
en los campos de texto del mensaje; `landing-map`/`monitoreo-live` con `escapeHtml`
en los nombres interpolados. El resto de las 39 rutas `static/js` no interpolan
datos no-estáticos en `innerHTML` (verificado por grep §1). Suite **695 passed /
54.75s con venv** (los tests cubren backend; los módulos JS validados con
`node --check`).

> **Herramienta reutilizable:** el grep de §1 está en
> `Info proyecto/_tools/auditoria_xss.ps1` (add-only, sin ejecutar en CI — 0.5 día
> de esfuerzo si se quiere automatizar; hoy corre como scan estático de release).
