# PENDIENTES_PROXIMA_SESION.md

Recordatorio de trabajo pendiente para continuar en una proxima sesion.
Ultima actualizacion: 15/10/2026

## Sin commitear en este momento

- Solo los cambios de v9.34.97 (FAB del reloj virtual, color del marcador del mapa y docs), listos para commitear cuando el usuario lo pida.

## Cerrado recientemente

### 15/10/2026 - v9.34.97: menores de UX/a11y (LOCAL, sin commitear)
- #vt-fab: era un `<div onclick>`, ahora es `<button type="button">` con `aria-label="Control de tiempo virtual"` (icono y badge ON quedan `aria-hidden`). Tabulable, se activa con Enter/Espacio y la puerta unica le devuelve el foco al cerrar el reloj.
- Borde del marcador de sucursal: pasa del verde suelto `#22c55e` a `THEME.gold` (`#dfba6b`) de theme.js, alineado con el borde dorado de style.css. El `.branch-status-dot` (verde activo / rojo inactivo) se mantiene porque es semantico.
- Docs: HISTORIAL recibe las entradas de v9.34.91 y v9.34.92 (se habian commiteado sin registro) mas la de v9.34.97; se repara la corrupcion de bytes de control (BEL/TAB/BS/VT/FF) que una escritura previa habia dejado en HISTORIAL.md y en este archivo.

### 15/10/2026 - v9.34.96: performance CDN por pagina (commit local c60e087, SIN PUSHEAR)
- Leaflet, Chart.js, Flatpickr (CSS + dark + JS + l10n), qrcodejs y html2canvas salen de base.html hacia las vistas que los usan, via macro DRY `templates/components/cdn_libs.html` (cdn_head / cdn_scripts). Font Awesome queda global.
- Las paginas sin mapa/graficos/fechas/QR ya no bajan esas librerias. Guard `_tools/check_cdn_per_page.py`.

### 15/10/2026 - v9.34.95: menores de accesibilidad
- 3 `<img>` sin alt, `aria-hidden` a 574 iconos decorativos, loading/decoding en `<img>`, `aria-describedby` en los errores de auth.

### 14/10/2026 - v9.34.94: modales accesibles
- Puerta unica openModal/closeModal para todos los dialogos; focus trap y Escape DOM-driven; autofocus al primer campo visible; devolucion del foco al disparador. Macro `components/modal_header.html`.
- Excepcion documentada: apertura directa de modal-pase-digital en `static/js/modules/profile-help.js:391` (mantiene el scroll del ticket de soporte).
- vt-modal (reloj virtual) enrutado a la puerta unica; el intervalo corre solo mientras el dialogo esta abierto.

### SUPER-ADMIN (commit 701c49f)
- El Admin General de la organizacion principal gestiona todas las organizaciones (bypass de enforce_organization_scope + listado global de usuarios). Ya esta commiteado y pusheado.

## Pendientes abiertos

- **git push**: c60e087 (v9.34.96) y el commit de v9.34.97 estan sin pushear. Requieren pedido explicito del usuario.
- **Performance parte 2 (CSS/JS local por pagina)**: mover `landing-map.css` (12 KB), `chart-window.css`, `sidebar.css`, `tables.css`, `badges.css` y `action-menu.css` fuera de base.html hacia las paginas que las usan, mas el `style.css` legacy (3.8 KB). Ganancia modesta: ya estan en el precache del service worker, asi que no elimina descargas de red. Exige verificar los estilos computados antes/despues en navegador real: el analisis estatico por clases es ruidoso porque hay nombres genericos (`active`, `badge`, `danger`) en varios archivos y en el JS.
- **Menores no urgentes**: `prefers-reduced-motion` (respetar la reduccion de movimiento del sistema) y revision de contraste en puntos sueltos.
- **Deuda de docs**: v9.34.90 y v9.34.93 quedaron sin entrada en HISTORIAL (se documentaron en el mensaje del commit, no en el historial).

## Verificacion usada en esta tanda

- Guards: 11/11 en verde (`Get-ChildItem _tools -Filter "check_*.py"` corridos con `.\venv\Scripts\python.exe`).
- Suite: 891 passed, 9 warnings (siempre con el python del venv; el python global del sistema no tiene alembic).
- Runtime: Edge headless + CDP (puerto 9371, perfil en el temp de opencode) para el FAB (tag, tamano, teclado, arbol AX) y el color del marcador.
