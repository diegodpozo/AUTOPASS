# PENDIENTES_PROXIMA_SESION.md

Recordatorio de trabajo pendiente para continuar en una proxima sesion.
Ultima actualizacion: 19/10/2026

## Sin commitear en este momento

- Nada pendiente en el arbol de trabajo: la Fase 1 del plan de concurrencia (aritmetica atomica de saldo y puntos) quedo en `960e3a9` (codigo), `a9f3a5e` (tests) y un commit de docs con el informe y este archivo. La Fase 2 ya estaba en `c408507`, y la tanda multi-org del remoto (`2b7d0d6`, `51acaf1`, `ccc0328`, `d858a57`) quedo mergeada en el pull anterior.
- Falta pushear: nada; el push del 19/10/2026 dejo la rama local al dia con `origin/main` (0 adelante / 0 atras, verificado con `git fetch` + `git rev-list --left-right --count origin/main...HEAD`).
- Archivos de v9.34.99: `static/js/modules/landing-map-pois.js`, `static/sw.js` y los 4 documentos.

## Cerrado recientemente

### 19/10/2026 - Fase 1 del plan de concurrencia: aritmetica atomica de saldo y puntos
- **Que se hizo**: todos los ajustes de saldo/puntos pasan por 6 helpers de `repositories/user_repository.py` que ejecutan UN solo `UPDATE ... RETURNING` (`sumar_saldo`, `descontar_saldo`, `fijar_saldo`, `sumar_puntos`, `canjear_puntos`, `descontar_puntos_tope_cero`). Las condiciones (saldo/puntos suficientes, tope cero, `COALESCE` para columnas en NULL) viajan dentro de la sentencia: 0 filas = no alcanzaba (se lee como `None`), asi que desaparece la ventana entre el chequeo y el descuento. Ningun helper hace commit: lo decide el flujo, tipicamente dentro del lock de la Fase 2.
- **Sitios migrados**: 20 en 6 archivos - `services/payments.py` (6: descuento de saldo, acreditacion de puntos en los 3 caminos de pago, reembolso de saldo y de puntos con tope cero), `services/billing_service.py` (4: puntos por estadias), `services/reservation_service.py` (6: ajuste por edicion de reserva + reembolso admin), `routes/user/fidelization.py` (2: canje y anulacion), `routes/user/balance.py` (1: recarga) y `routes/admin/users.py` (1: set del admin). `update_balance`/`add_points` (que eran codigo muerto) ahora delegan en los helpers.
- **Tests**: `tests/test_concurrencia_saldo_puntos.py` (3 tests de carrera real: hilos + `threading.Barrier` sobre SQLite de archivo con WAL y `busy_timeout`) y `tests/test_user_repository_atomic.py` (10 unitarios del contrato: valor devuelto, no alcanza, tope cero, columnas NULL). `tests/test_balance_routes.py` suma `_seed_user_saldo(...)` en los 2 tests de recarga, porque el saldo dejo de actualizarse en memoria y el `UPDATE` necesita la fila (no se cambio ninguna asercion).
- **Verificacion**: RED reproducido contra `95aca58` en un worktree temporal (3 failed: doble gasto de saldo, 10 puntos en vez de 20, dos tickets con 80 puntos) -> GREEN con el fix (3 passed). Suite completa `927 passed, 9 warnings`; guards 11/11; `py_compile` y `git diff --check` en 0; grep sin `+=`/`-=` sobre saldo/puntos en codigo de negocio.
- **Material de defensa**: los paquetes de cada fase (codigo ANTES/DESPUES y explicaciones) quedan solo en local, fuera de git. Falta generar los PDFs del paquete de la Fase 1 (se arman con el mismo procedimiento que los de la Fase 2).

### 18/10/2026 - tanda multi-org: 5 P1 de aislamiento (commiteada en el remoto, mergeada en este pull)
- **Nucleo** (`repositories/scoping.py` + `core/security.py`): `multi_organization_active`, `organization_of_sede` (sede -> empresa; homonimo = no atribuible), `sede_ids_and_names`; `resolve_actor_organization_id`, `require_tenant_scope` y `enforce_organization_scope(..., db=, organization_id=)` ahora FAIL-CLOSED en multi-org (actor o recurso sin org -> 403; exencion de super-admin primero; sin `db` conserva la tolerancia vieja). Dos modos: <=1 org = comportamiento actual intacto.
- **Reservas (IDOR)**: listado/conteo acotados por org para todos los roles; `check_reserva_scope` (org vía `organization_of_sede` + `same_branch` despues) en editar/confirmar/cancelar; `_sucursal_admin` valida la sede al crear/editar (404 no atribuible, 403 ajena).
- **Cobro**: `BillingService.process_payment(db, plate, metodo, organization_id, sucursal_id)` + `require_tenant_scope` + `get_last_entry_by_patente`/`log_in_scope`; `pay_stay` calcula org (y sede si no es ADMIN).
- **ALPR**: `ALPR_NODE_ORG_ID` (env) + `require_alpr_node_org` (binding nodo -> empresa) en validate-plate/exit-plate/validate-qr; `access_service` con `_sede_desde_gate`/`_alcance_gate`/`_alcance_logs` (gate ligado sin sede propia -> denied), QR exige reserva de la misma org, `manual_entry/exit/cancel_stay` reciben `organization_id`.
- **Rutas delgadas**: helpers `_check_promo_org`, `_enforce_camera_org`, `validate_local_admin_user_permission` ahora reciben `db` y lo pasan a `enforce_organization_scope` (16 call sites actualizados).
- **Fix colateral**: `BranchRepository.get_id_by_name` con nombre ambiguo devolvia `MultipleResultsFound` (500) con sedes homonimas; ahora devuelve `None` (no atribuible).
- **Docs**: `AISLAMIENTO_MULTIORG.md` (modelo de datos, nucleo, regla legacy, flujos, dos modos, tests, limites).
- **Verificacion**: suite `906 passed`; guards 11/11 OK; sin conflict markers. Ya commiteada en el remoto y mergeada en este pull.

### 16/10/2026 - v9.34.99: fix del reintento de Overpass en los POIs (commit `f652832`, pusheado)
- Sintoma: los POIs del mapa no cargaban; consola con `[OVERPASS] Error: TypeError: Failed to fetch` en `landing-map-pois.js` (doFetch -> loadTheaters).
- Causa raiz: cuando Overpass esta saturado/rate-limited responde 429/5xx desde nginx SIN cabeceras CORS; el navegador lo convierte en bloqueo CORS y el `fetch` rechaza con `TypeError`, asi que nunca hay `res.status` y el reintento original (solo 429/504) no se disparaba nunca. No es CSP ni red.
- Fix: `doFetch` async/await + helper `esReintentable()` que reintenta ante `TypeError` (red/CORS) y 429/5xx, con el mismo backoff (3 s x2 hasta 60 s; 6 reintentos). Los 4xx no reintentables y el `AbortError` siguen propagandose.
- Verificacion: FASE A 2 fallos CORS simulados -> 2 warns -> HTTP 200 -> 100 POIs y cache; FASE B saturacion real de Overpass -> 1 fallo real 502-sin-CORS -> reintento -> 100 POIs, 0 errores OVERPASS. `sw.js` a v13.
- Nota (no tocado): la consulta a Overpass tarda ~30-45 s (bbox CABA/GBA, `[timeout:60]`, `out center 100`).

### 16/10/2026 - v9.34.98: movimiento accesible en JS (commit `e0449b3`, pusheado)
- El bloque CSS de `prefers-reduced-motion` frena transiciones, animaciones y `scroll-behavior`, pero no alcanza a lo que se dibuja fuera del DOM: Chart.js anima dentro de un `<canvas>` y Leaflet mueve la camara por `requestAnimationFrame`. Era el ultimo tramo del criterio WCAG 2.3.3.
- Helper unico `mapMotionOptions(extra)` en `static/js/modules/utils.js`: con la preferencia activa devuelve `{animate:false, duration:0}`; sin ella devuelve solo `extra` (identico a no pasar opciones, asi que para el resto de usuarios no cambia nada). Aplicado a los 16 llamados de camara (flyTo/flyToBounds/setView/fitBounds) de landing-map, landing-map-locality, landing-map-geo, dashboard-admin-branches-crud y dashboard-promotions.
- `applyReducedMotionToCharts()` fija `Chart.defaults.animation = false` desde `main.js` una sola vez (cubre los 8 `new window.Chart(...)` sin tocar ningun call site) y guarda el default para restaurarlo. La preferencia es viva: el listener del MediaQueryList re-sincroniza los graficos ya creados sin recargar.
- Guard nuevo `check_js_motion_gaps()` dentro de `_tools/check_css_design_system.py` (hermano de `check_js_scroll_motion`), con mordida probada 4/4. `sw.js` a v12.
- Docs: se repara la corrupcion de bytes de control preexistente en `Info proyecto/AUDITORIAS.md` (7 BEL, 4 TAB, 2 CR sueltos) y `AUDITORIA_DB.md` (1 BEL).

### 15/10/2026 - v9.34.97: menores de UX/a11y (commit `b1288be`, pusheado)
- #vt-fab: era un `<div onclick>`, ahora es `<button type="button">` con `aria-label="Control de tiempo virtual"` (icono y badge ON quedan `aria-hidden`). Tabulable, se activa con Enter/Espacio y la puerta unica le devuelve el foco al cerrar el reloj.
- Borde del marcador de sucursal: pasa del verde suelto `#22c55e` a `THEME.gold` (`#dfba6b`) de theme.js, alineado con el borde dorado de style.css. El `.branch-status-dot` (verde activo / rojo inactivo) se mantiene porque es semantico.
- Docs: HISTORIAL recibe las entradas de v9.34.91 y v9.34.92 (se habian commiteado sin registro) mas la de v9.34.97; se repara la corrupcion de bytes de control (BEL/TAB/BS/VT/FF) que una escritura previa habia dejado en HISTORIAL.md y en este archivo.

### 15/10/2026 - v9.34.96: performance CDN por pagina (commit `c60e087`, pusheado)
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

- **Plan de concurrencia (continuacion)**: hechas la Fase 1 y la Fase 2. Sigue la **Fase 3** (invalidar la cache de disponibilidad despues del commit en crear/modificar/cancelar reserva; es la que cierra R1/R2 y con la que se escriben sus tests RED), despues la **Fase 5** (idempotencia de webhooks por `payment_id`) y la **Fase 4** (constraints en Postgres, requiere ventana de migracion). Referencia: `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md` (seccion 7).
- **git push**: AL DIA. `c60e087` (v9.34.96), `b1288be` (v9.34.97), `e0449b3` (v9.34.98), `f652832` (v9.34.99) y la Fase 1 + Fase 2 del plan de concurrencia pusheados; `origin/main` al dia (verificado con fetch: ahead 0 / behind 0, sin marcadores de conflicto).
- **Performance parte 2 (CSS/JS local por pagina)**: mover `landing-map.css` (12 KB), `chart-window.css`, `sidebar.css`, `tables.css`, `badges.css` y `action-menu.css` fuera de base.html hacia las paginas que las usan, mas el `style.css` legacy (3.8 KB). Ganancia modesta: ya estan en el precache del service worker, asi que no elimina descargas de red. Exige verificar los estilos computados antes/despues en navegador real.
- **Nominatim (revision, no tocado)**: `dashboard-admin-branches-crud.js` y `dashboard-promotions.js` hacen fetch cross-origin a nominatim SIN reintento; mismo patron de riesgo (un error sin CORS llega como TypeError). Se puede reutilizar el patron de `esReintentable()`.
- **POIs/Overpass (opcional, no tocado)**: la consulta tarda ~30-45 s (bbox CABA/GBA, `[timeout:60]`, `out center 100`). Se podria acotar el bbox o bajar el tope; alternativa: espejo `overpass.kumi.systems` (requiere sumarlo a `connect-src` en main.py y al test `tests/test_security_headers.py`).
- **Menores no urgentes**: revision de contraste en puntos sueltos.
- **Deuda de docs**: v9.34.90 y v9.34.93 quedaron sin entrada en HISTORIAL (se documentaron en el mensaje del commit, no en el historial).

## Verificacion usada en esta tanda

- Guards: 11/11 en verde (`Get-ChildItem _tools -Filter "check_*.py"` corridos con `.\venv\Scripts\python.exe`).
- Suite: 927 passed, 9 warnings (ultima corrida, 19/10/2026, con la Fase 1 aplicada). Todos los tests y guards se corren con el python del venv; el python global del sistema no tiene alembic.
- Fase 1 (19/10/2026): RED reproducido en un worktree temporal sobre `95aca58` (3 failed) y GREEN con el fix (3 passed); `py_compile` y `git diff --check` en 0.
- `node --check` en `static/js/modules/landing-map-pois.js` y `static/sw.js`.
- Runtime: Edge headless + CDP contra el server local (puerto 8013). FASE A: 2 fallos CORS simulados -> 2 warns de reintento -> HTTP 200 -> 100 POIs y cache creada. FASE B: saturacion real de Overpass -> 1 fallo real 502-sin-CORS -> reintento -> 100 POIs, 0 errores OVERPASS. La senal de exito es la cache POI (los 5 `poi-marker` fijos son estadios).
- Script: `C:\Users\usuario.DESKTOP-P7MEQGK\AppData\Local\Temp\opencode\verify_poi_retry.py` (diagnostico previo: `diag_poi_cdp.py` y `diag_overpass_429.py`).
