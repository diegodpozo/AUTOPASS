**Cerrado:**
- 3 <img> sin alt corregidos (live.html, branch_modals.html).
- aria-hidden='true' a 574 iconos decorativos <i>/<span> sin texto.
- loading='lazy' y decoding='async' en <img> donde faltaban.
- aria-describedby a errores en auth (login/recovery/register/oauth).
## 15/10/2026 — MENORES DE ACCESIBILIDAD (v9.34.95) — APLICADO, SIN COMMITEAR

# PENDIENTES_PROXIMA_SESION.md

Recordatorio de trabajo pendiente para continuar en una próxima sesión.
Última actualización: 14/10/2026

## 14/10/2026 — MODALES ACCESIBLES (v9.34.94) — APLICADO, SIN COMMITEAR

**Tanda cerrada (verificación CDP + 10 guards + 882 passed):**

- **Puerta única**: todos los diálogos se abren/cierran por openModal/closeModal. **Excepción documentada**: apertura directa de modal-pase-digital en static/js/modules/profile-help.js:391 (mantiene el scroll del ticket de soporte al abrir el pase digital desde el chat).
- **Focus trap y Escape**: DOM-driven sobre diálogos visibles (getComputedStyle !== 'none'). Escape activa el control de cierre de arriba ([data-modal-close] > .close-btn/.modal-close-top), topmost por z-index. Devolución de foco al disparador registrado.
- **Autofocus**: primer campo editable **visible** (filtra display:none, offsetParent nulo y elementos sin getClientRects().length > 0); si no hay campos, enfoca el contenedor con 	abindex="-1".
- **Marcado**: 
ole="dialog" aria-modal="true", nombre accesible resoluble (ria-labelledby o ria-label), cierres como <button type="button"> con nombre accesible y data-modal-close cuando corresponda. Macro modal_header.html emite cierre con data-modal-close aria-label="Cerrar".
- **vt-modal (reloj virtual)**: enrutado a la puerta única (	oggleVTModal usa openModal/closeModal); el intervalo se inicia solo con modal abierto y **se detiene** al cerrar (verificado en runtime). Ruta de cierre por Escape, X y click en fondo unificada.
- **CSS**: .modal--centered para diálogos centrados (sin pisar .modal { display: none }).

**Menores a11y (NO aprobados para esta tanda):**
- 3 lt faltantes en imágenes (solo texto decorativo no aplica; revisar los 3 puntos).
- ria-hidden="true" en iconos puramente decorativos (mejorar).
- prefers-reduced-motion: respetar reducción de movimiento.
- loading="lazy" / decoding="async" en imágenes no críticas.
- **FAV no keyboard-reachable**: #vt-fab es un <div> con onclick="toggleVTModal()" (div no enfocable). No corregido (admin/test; requiere 
ole="button" tabindex="0" + handlers de Enter/Espacio).
- **Performance**: mover CDN por página (más riesgoso, posponer para tanda final).

**Estado de verificación:** check_a11y_modals.py verde. Verificación CDP completa (landing, dashboard, /perfil, showConfirm/showChoice, vt-modal) con **0 excepciones JS de la app**.

---
## SUPER-ADMIN por organización principal — APLICADO 14/10/2026 (LOCAL, SIN COMMITEAR)

- Problema: el Admin General fundador (dmin@autopass.com, org principal) podía invitar nuevos Admin Generales pero no podía borrarlos/administrarlos (scope por org). No existía super-admin.
