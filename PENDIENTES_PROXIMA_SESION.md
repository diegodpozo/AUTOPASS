# PENDIENTES_PROXIMA_SESION.md

Recordatorio de trabajo pendiente para continuar en una proxima sesion.
Ultima actualizacion: 16/10/2026

## Sin commitear en este momento

- Nada: v9.34.98 y v9.34.99 quedaron commiteados en local en esta sesion (los 3 commits `c60e087`, `b1288be` y los dos nuevos siguen SIN PUSHEAR, a la espera de un pedido explicito del usuario).
- Archivos de v9.34.99: `static/js/modules/landing-map-pois.js`, `static/sw.js` y los 4 documentos.

## Cerrado recientemente

### 16/10/2026 - v9.34.99: fix del reintento de Overpass en los POIs (commit local)
- Sintoma: los POIs del mapa no cargaban; consola con `[OVERPASS] Error: TypeError: Failed to fetch` en `landing-map-pois.js` (doFetch -> loadTheaters).
- Causa raiz: cuando Overpass esta saturado/rate-limited responde 429/5xx desde nginx SIN cabeceras CORS; el navegador lo convierte en bloqueo CORS y el `fetch` rechaza con `TypeError`, asi que nunca hay `res.status` y el reintento original (solo 429/504) no se disparaba nunca. No es CSP ni red.
- Fix: `doFetch` async/await + helper `esReintentable()` que reintenta ante `TypeError` (red/CORS) y 429/5xx, con el mismo backoff (3 s x2 hasta 60 s; 6 reintentos). Los 4xx no reintentables y el `AbortError` siguen propagandose.
- Verificacion: FASE A 2 fallos CORS simulados -> 2 warns -> HTTP 200 -> 100 POIs y cache; FASE B saturacion real de Overpass -> 1 fallo real 502-sin-CORS -> reintento -> 100 POIs, 0 errores OVERPASS. `sw.js` a v13.
- Nota (no tocado): la consulta a Overpass tarda ~30-45 s (bbox CABA/GBA, `[timeout:60]`, `out center 100`).

### 16/10/2026 - v9.34.98: movimiento accesible en JS (LOCAL, sin commitear)
- El bloque CSS de `prefers-reduced-motion` frena transiciones, animaciones y `scroll-behavior`, pero no alcanza a lo que se dibuja fuera del DOM: Chart.js anima dentro de un `<canvas>` y Leaflet mueve la camara por `requestAnimationFrame`. Era el ultimo tramo del criterio WCAG 2.3.3.
- Helper unico `mapMotionOptions(extra)` en `static/js/modules/utils.js`: con la preferencia activa devuelve `{animate:false, duration:0}`; sin ella devuelve solo `extra` (identico a no pasar opciones, asi que para el resto de usuarios no cambia nada). Aplicado a los 16 llamados de camara (flyTo/flyToBounds/setView/fitBounds) de landing-map, landing-map-locality, landing-map-geo, dashboard-admin-branches-crud y dashboard-promotions.
- `applyReducedMotionToCharts()` fija `Chart.defaults.animation = false` desde `main.js` una sola vez (cubre los 8 `new window.Chart(...)` sin tocar ningun call site) y guarda el default para restaurarlo. La preferencia es viva: el listener del MediaQueryList re-sincroniza los graficos ya creados sin recargar.
- Guard nuevo `check_js_motion_gaps()` dentro de `_tools/check_css_design_system.py` (hermano de `check_js_scroll_motion`), con mordida probada 4/4. `sw.js` a v12.
- Docs: se repara la corrupcion de bytes de control preexistente en `Info proyecto/AUDITORIAS.md` (7 BEL, 4 TAB, 2 CR sueltos) y `AUDITORIA_DB.md` (1 BEL).

### 15/10/2026 - v9.34.97: menores de UX/a11y (commit local `b1288be`, SIN PUSHEAR)
- #vt-fab: era un `<div onclick>`, ahora es `<button type="button">` con `aria-label="Control de tiempo virtual"` (icono y badge ON quedan `aria-hidden`). Tabulable, se activa con Enter/Espacio y la puerta unica le devuelve el foco al cerrar el reloj.
- Borde del marcador de sucursal: pasa del verde suelto `#22c55e` a `THEME.gold` (`#dfba6b`) de theme.js, alineado con el borde dorado de style.css. El `.branch-status-dot` (verde activo / rojo inactivo) se mantiene porque es semantico.
- Docs: HISTORIAL recibe las entradas de v9.34.91 y v9.34.92 (se habian commiteado sin registro) mas la de v9.34.97; se repara la corrupcion de bytes de control (BEL/TAB/BS/VT/FF) que una escritura previa habia dejado en HISTORIAL.md y en este archivo.

### 15/10/2026 - v9.34.96: performance CDN por pagina (commit local c60e087, SIN PUSHEAR)
- Leaflet, Chart.js, Flatpickr (CSS + dark + JS + l10n), qrcodejs y html2canvas salen de base.html hacia las vistas que los usan, via macro DRY `templates/components/cdn_libs.html` (cdn_head / cdn_scripts). Font Awesome queda global.
- Las paginas sin mapa/graficos/fechas/QR ya no bajan esas librerias. Guard `_tools/check_cdn_per_page.py`.

### 14/10/2026 - v9.34.95: menores de accesibilidad
- 3 `<img>` sin alt, `aria-hidden` a 574 iconos decorativos, loading/decoding en `<img>`, `aria-describedby` en los errores de auth.

### 14/10/2026 - v9.34.94: modales accesibles
- Puerta unica openModal/closeModal para todos los dialogos; focus trap y Escape DOM-driven; autofocus al primer campo visible; devolucion del foco al disparador. Macro `components/modal_header.html`.
- Excepcion documentada: apertura directa de modal-pase-digital en `static/js/modules/profile-help.js:391` (mantiene el scroll del ticket de soporte).
- vt-modal (reloj virtual) enrutado a la puerta unica; el intervalo corre solo mientras el dialogo esta abierto.

### SUPER-ADMIN (commit 701c49f)
- El Admin General de la organizacion principal gestiona todas las organizaciones (bypass de enforce_organization_scope + listado global de usuarios). Ya esta commiteado y pusheado.

## Pendientes abiertos

- **git push**: `c60e087` (v9.34.96) y `b1288be` (v9.34.97) estan sin pushear (el remoto no se movio: 0 detras, sin riesgo de divergencia por ahora). Requieren pedido explicito del usuario.
- **Performance parte 2 (CSS/JS local por pagina)**: mover `landing-map.css` (12 KB), `chart-window.css`, `sidebar.css`, `tables.css`, `badges.css` y `action-menu.css` fuera de base.html hacia las paginas que las usan, mas el `style.css` legacy (3.8 KB). Ganancia modesta: ya estan en el precache del service worker, asi que no elimina descargas de red. Exige verificar los estilos computados antes/despues en navegador real.
- **Nominatim (revision, no tocado)**: `dashboard-admin-branches-crud.js` y `dashboard-promotions.js` hacen fetch cross-origin a nominatim SIN reintento; mismo patron de riesgo (un error sin CORS llega como TypeError). Se puede reutilizar el patron de `esReintentable()`.
- **POIs/Overpass (opcional, no tocado)**: la consulta tarda ~30-45 s (bbox CABA/GBA, `[timeout:60]`, `out center 100`). Se podria acotar el bbox o bajar el tope; alternativa: espejo `overpass.kumi.systems` (requiere sumarlo a `connect-src` en main.py y al test `tests/test_security_headers.py`).
- **Menores no urgentes**: revision de contraste en puntos sueltos.
- **Deuda de docs**: v9.34.90 y v9.34.93 quedaron sin entrada en HISTORIAL (se documentaron en el mensaje del commit, no en el historial).

## Verificacion usada en esta tanda

- Guards: 11/11 en verde (`Get-ChildItem _tools -Filter "check_*.py"` corridos con `.\venv\Scripts\python.exe`).
- Suite: 891 passed, 9 warnings (siempre con el python del venv; el python global del sistema no tiene alembic).
- `node --check` en `static/js/modules/landing-map-pois.js` y `static/sw.js`.
- Runtime: Edge headless + CDP contra el server local (puerto 8013). FASE A: 2 fallos CORS simulados -> 2 warns de reintento -> HTTP 200 -> 100 POIs y cache creada. FASE B: saturacion real de Overpass -> 1 fallo real 502-sin-CORS -> reintento -> 100 POIs, 0 errores OVERPASS. La senal de exito es la cache POI (los 5 `poi-marker` fijos son estadios).
- Script: `C:\Users\usuario.DESKTOP-P7MEQGK\AppData\Local\Temp\opencode\verify_poi_retry.py` (diagnostico previo: `diag_poi_cdp.py` y `diag_overpass_429.py`).
