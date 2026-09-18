# Auditoría de Modularización — AUTOPASS

> **Fecha:** 2026-09-16 (revisión contra código v9.20.0)
> **Commit auditado original:** `3b59d78` (post v9.18.4) — **revisado contra** `22f9397` (v9.20.0)
> **Alcance:** SOLO modularización (estructura de capas, acoplamiento, patrones frontend/backend, reglas de extensión). No se audita funcionalidad, seguridad ni rendimiento.
> **Metodología:** análisis estático de imports, conteo de consultas directas a BD, tamaño de módulos, asignaciones al scope global (`window.*`), carga en templates y cumplimiento de los mandatos de `Info proyecto/GUIA_DESARROLLO.md`.

---

## 1. Resumen Ejecutivo

| Dimensión | Estado | Hallazgos |
|---|---|---|
| Separación de capas backend | Aceptable | Sin acoplamiento circular, pero rutas con mucha lógica y consultas directas |
| Frontend Bridge Pattern | Cumplido | 0 asignaciones `window.*` en módulos (76 migradas a puentes en v9.21.0); doble instancia de `notifications.js` [resuelta en v9.21.0] |
| Repositorios | Parcial | Solo 2 repos, usados por 2 servicios; el acceso a datos sigue descentralizado |
| Enums / Tipado | Parcial | Enums implementados, con strings mágicos residuales en 3 puntos |
| Tamaño de clases/módulos | God modules | Backend saneado: `access_service.py` (607→499) + `access_occupancy.py` (80), `report_service.py` (581→639 tras helpers) evaluado y no descompuesto; pendientes megamódulos JS `tour.js` (1730), `dashboard-reservations.js` (1294), `reservas-form.js` (1262). `reservation_service.py` descompuesto [v9.21.0] |
| Lógica inline en templates | Cumplido | Lógica de `reset_password.html` y `estadisticas_ocr.html` extraída a módulos [v9.22.0] |
| Config / Hardcoding | Correcto | Configuración centralizada en `core/config.py` |

**Puntaje de salud de modularización: 8.0 / 10** (era 6.5 / 10; +1.0 por restaurar el Bridge Pattern al mover las 76 asignaciones `window.*` a los puentes, +0.5 por extraer la lógica inline de `reset_password.html` y `estadisticas_ocr.html` a módulos en v9.22.0).

---

## 2. Backend — Cumplimiento por Capa

### 2.1 Diagrama de dependencias real

```
main.py
 └─ routes/* (APIRouter por dominio)
     ├─ core/          -> config, security, database, mqtt, seed, limiter, logger, time, normalize, cache   [OK]
     ├─ services/*     -> lógica de negocio (15 servicios)                                                    [OK]
     ├─ repositories/  -> 2 repos usados SOLO por reservation_service y user_service                         [PARCIAL]
     ├─ models/        -> 8 modelos + enums                                                                  [OK]
     └─ schemas/       -> validación Pydantic por dominio                                                    [OK]
```

- **[OK]** **No existe acoplamiento circular**: ningún `services/*.py` importa `routes` (verificado). La regla "los servicios importan modelos/schemas, pero no routers" se cumple.
- **[OK]** **`main.py` es un orquestador delgado** y el registro de routers está limpio (aliasing en `routes/__init__.py` + agregación por submódulo en `routes/admin|user|parking|system/__init__.py`).
- **[OK]** **`core/`** concentra la infraestructura (11 archivos).
- **[OK]** **`schemas/`** separada por dominio (auth, user, reservation, parking, support, notification, mercadopago) con `validators.py` compartido.

### 2.2 VIOLACIÓN ALTA: Rutas gordas (mandato "rutas delgadas")

**~77 consultas directas `db.query(...)` + 4 `SessionLocal()`** repartidas en 17 archivos de `routes/` (revisión v9.21.0; Fases 1-4 aplicadas: brancheos, vehículos, ocupación y reservas delegados a servicios). La capa de transporte está hablando con la BD y ejecutando lógica de negocio en lugar de delegar a servicios.

| Archivo (ruta) | `db.query` | Lógica de negocio inline |
|---|---|---|
| `routes/admin/branches.py` | 9 | CRUD + logo inline (rename ya delegado a `BranchService.rename_branch`) |
| `routes/parking/status.py` | 6 | Ocupación/capacidades/deuda delegadas a `OccupancyService` (el WSS sí usa `OccupancyManager`) |
| `routes/admin/reservations.py` | 1 | Confirmar pago, crear/editar/cancelar, lookup y redemptions delegados a `ReservationService` (solo queda el query de ticket aplicado en `reservation_redemption_info`) |
| `routes/user/fidelization.py` | 12 | Canjes, descuentos, puntos inline |
| `routes/user/reservations.py` | 0 | CRUD completo, disponibilidad, pagos, reembolsos y notificaciones delegados a `ReservationService` |
| `routes/user/vehicles.py` | 0 | CRUD delegado a `UserService` (ver §5) |
| `routes/system/cameras.py` | 8 | Control ALPR mezclado con CRUD de cámaras |
| `routes/admin/users.py` | 7 | Roles, balance, bloqueo inline |
| `routes/admin/promotions.py` | 5 | CRUD + toggle inline |
| `routes/auth.py` | 6 | Sesiones multi-dispositivo, device_id inline |
| `routes/user/balance.py` | 6 | Resumen de saldo y estadías inline |
| `routes/system/health.py` | 6 | Reset destructivo de tablas inline |
| `routes/admin/settings.py` | 4 | Tarifas/capacidad inline |
| `routes/system/video.py` | 3 | WebSockets de video |
| `routes/admin/support.py` | 2 | Notificaciones de tickets |
| `routes/views.py` | 1 | Inyección de sucursales en templates |
| `routes/user/mercadopago.py` | 1 | Confirmación de pago MP |
| **Total** | **77** | |

**Consecuencias:** duplicación de consultas (repos no se usan), riesgo de inconsistencia, tests difíciles de aislar y desvío del mandato arquitectónico V9.6.0.

### 2.3 God services (servicios excesivamente grandes)

| Servicio | Líneas | Riesgo |
|---|---|---|
| `services/reservation_service.py` | 687 (fachada; era 1451) | Disponibilidad extraída a `availability.py` (382) y pagos a `payments.py` (422) — ver §2.3
| `services/access_service.py` | 499 (era 607) | Entrada/salida ALPR/QR/manuales; ocupación extraída a `access_occupancy.py` (80) — ver §2.3 |
| `services/report_service.py` | 639 (era 581) | Evaluado: cohesivo (una query analítica por método), no se descompone en módulos — ver §2.3 |

**Sugerencia:** en `reservation_service.py` extraer `availability.py` (sweep-line y fechas/horas deshabilitadas) y `payments.py` (pago manual/MP/reembolsos), manteniendo el resto como fachada.

**Resolución (v9.21.0, working tree):** aplicado. `reservation_service.py` quedó como **fachada de 687 líneas** (`class ReservationService(ReservationPaymentsMixin)`): extraídos `services/availability.py` (382 líneas: capacidad por tipo, `verificar_disponibilidad`, fechas/horas deshabilitadas, sweep-line, aforo no-op) y `services/payments.py` (422 líneas: `ReservationPaymentsMixin` con `get_available_redemption_discounts`, `pay_reservation_manual`, `redemption_sucursal_clause`, `validate_redemption_ticket`, `pay_reservation`, `pay_reservation_mp`, `simulate_refund`, `cancel_reservation`). La fachada re-exporta `verificar_disponibilidad`/`obtener_fechas_deshabilitadas`/`obtener_horas_deshabilitadas_con_reservas` etc. (los tests y `routes/user/reservations.py` siguen importando desde `services.reservation_service`). Todos los `onclick` de llamadas externas resuelven por herencia MRO (`ReservationService.pay_reservation_manual`, `.simulate_refund`, `.validate_redemption_ticket`, `.redemption_sucursal_clause`). **152 tests en verde y `py_compile` OK.** El dominio "ciclo de vida" (cleanups, finalización, `get_en_predio_ids`, listados y CRUD user/admin) quedó como núcleo del facade hasta una descomposición futura si hace falta.

**Evaluación/sección descompuesta posterior (working tree, item 8):** `access_service.py` quedó como **fachada de 499 líneas** (`class AccessService(AccessOccupancyMixin)`): extraído `services/access_occupancy.py` (80 líneas: normalización de tipo, `_inc/_dec_reserva_occ`, `_asignar_plaza`/`_liberar_plaza` y `_capacidad_por_tipo`, que reemplazan los bloques duplicados de incremento/decremento de ocupación que aparecían **7 veces** en los flujos ALPR/QR/manuales). Además se deduplicaron 3 bloques repetidos (resolución de sucursal por `gate_id`, detección de "ingreso sin salida posterior", get-or-create de aforo) y el acceso a datos pasó de 13 consultas directas en el dominio a **solo 2** (último registro de QR por `patente_detectada` y owner de `cancel_stay`; semántica distinta a los repos existentes), usando `AccessRepository`, `BranchRepository`, `ReservationRepository` y `VehicleRepository`. **`report_service.py` se evaluó y NO se descompone en módulos**: es dimensionalmente cohesivo (cada método es una query analítica read-only distinta; `get_financial_summary` es un único pipeline con estado local compartido). Se aplicó solo la extracción del helper de módulo `_branch_filter` (retira el filtro de aislamiento por sucursal duplicado en **13 sitios**). **152 tests en verde y `py_compile` OK.**

### 2.4 Repositorios subutilizados

- Existen 6 repositorios: `user_repository.py` (30 líneas), `reservation_repository.py` (~150 líneas), `vehicle_repository.py`, `access_log_repository.py`, `redemption_repository.py` y `branch_repository.py`.
- **6 servicios** los importan; ninguna ruta los usa; el acceso a datos sigue mayormente en las rutas (ver 2.2).
- La capa `repositories/` debería ser la única puerta de acceso a datos; hoy es un "casi esquema".
- **[PARCIAL v9.21.0]** El dominio de **reservas** quedó con acceso a datos 100% en repositorios: `ReservationRepository` (overlap, vencidas, expiradas, filtrado admin, stats), `VehicleRepository`, `UserRepository.get_active_by_id`, `AccessRepository`, `RedemptionRepository` y `BranchRepository`. `availability.py`, `payments.py` y el fachada tienen **0 `db.query(models.*)`**. Pendiente: otros servicios (`user_service`, `branch_service`, `access_service`, etc.) aún consultan datos directamente.
- **[working tree]** El dominio de **accesos** también quedó con acceso a datos en repositorios: `access_service.py` baja de 13 consultas directas a **2** (todas a `AccessRepository`/`BranchRepository`/`ReservationRepository`/`VehicleRepository`); solo quedan el último registro QR por `patente_detectada` y el owner de `cancel_stay`, por semántica distinta a los repos existentes.

### 2.5 Strings mágicos vs Enums — **[RESUELTO v9.21.0]**

Se implementaron `UserRole`, `VehicleType`, `AccessEventType`, `ReservationStatus`, `PaymentStatus` y `NotificationType` (68 líneas). Residuos encontrados (verificados en v9.20.0 y corregidos en v9.21.0):

| Ubicación | Línea | Problema |
|---|---|---|
| `services/access_service.py` | 252 | `('ENTRADA', 'SALIDA')` — notación de gate type en naming convention (ver nota) |
| `routes/system/health.py` | 66 | `rol == 'user'` debería ser `UserRole.USER` |
| `services/reservation_service.py` | 58-59, 149-150 | `["Pendiente", "Activa"]` y `["Pendiente", "Pagado"]` deberían usar `ReservationStatus` / `PaymentStatus` |
| `repositories/reservation_repository.py` | 25 | `["Pendiente", "Activa"]` idem |

**Corregido en v9.21.0:** todos los strings de la tabla fueron reemplazados por los Enums (`access_service.py:253`, `health.py:66`, `reservation_service.py` x4, `user_service.py:99`, `reservation_repository.py:25`, `branches.py` delete_branch).

**Barrido adicional (v9.21.0, item 7 del plan):** se reemplazaron además los `rol !=/== "admin"` restantes en `status.py`, `settings.py`, `promotions.py`, `cameras.py`, `health.py`, `video.py`, `common.py`, `support_service.py` (incl. `in_(["admin","local_admin"])`), `reservation_service.py` y `branch_service.py` (`local_admin`), los `tipo_evento == "ENTRADA"/"SALIDA"` de `balance.py`, `billing_service.py` y `occupancy_service.py`, el `ev in ("ENTRADA","SALIDA")` de `report_service.py`, los 8 strings de estado de `reservation_service.py` (`Completada/Cancelada/Pagado/Pendiente`) y la asignación `rol="user"` de `oauth_service.py`.

**Nota de consistencia:** los estados de la UI admin (`PENDIENTE_PAGO`, `PAGADA`, `EN_USO`, `FINALIZADA`, `CANCELADA`) referenciados en la documentación **NO existen como constantes**; el backend usa los valores `Pendiente/Activa/Completada/Cancelada/Fallido/Pagado`. No hay corte funcional (la UI compara los valores reales), pero la documentación y el frontend usan nomenclaturas distintas, lo que confunde a desarrolladores. Conviene alinear la documentación con los valores reales o mapearlos explícitamente.

**Nota sobre `('ENTRADA', 'SALIDA')` en `access_service.py`:** este string checkea el tipo de portón desde el `gate_id` (naming convention `SUCURSAL_PATENTE_ENTRADA`), no es un `AccessEventType`. Es menos crítico que los otros strings pero mantiene un acoplamiento al formato del gate_id.

---

## 3. Frontend — Cumplimiento del Bridge Pattern

### 3.1 Arquitectura actual

```
modules/*.js  (38 módulos ES6, lógica real; incluye `chart_window.js` — componente `WindowedChart` compartido)
      |
      v
*_bridge.js   (9 scripts puente: dashboard.js, perfil.js, main.js, auth.js, landing.js, reservas.js, vehicles.js, contacto.js, api_client.js)
      |
      v
window.*  ->  handlers inline (onclick en templates)
```

- **[OK]** Los puentes principales (`dashboard.js` 313 líneas, `perfil.js` 431 líneas) importan módulos y exponen `window.*` como pasamanos; son los únicos autorizados a asignar al scope global.
- **[OK]** Los módulos usan `import/export` y comparten dependencias limpias (`api.js`, `utils.js`, `ui.js`, `virtual-time.js`).
- **[OK]** `api.js` es el único cliente HTTP (mandato "toda petición a la red usa `api.js`") y se respeta en los módulos auditados.

### 3.2 ~~VIOLACIÓN ALTA: `window.*` asignado DENTRO de los módulos~~ **[RESUELTO v9.21.0 — working tree, sin commitear]**

El mandato V9.6.0 dice: "No modificar `window.*` desde módulos ES6. Solo los scripts puente asignan al scope global." En la revisión v9.20.0 se detectaban **~88 matches en 16 módulos** (2 lecturas `typeof window.Chart` en `chart_window.js` y `dashboard-metrics.js` no eran asignaciones); el conteo real de asignaciones a descontar quedó en **76** (excluye lecturas `typeof window.X ===` y grabados muertos):

| Módulo | Asignaciones `window.*` |
|---|---|
| `notifications.js` | 22 |
| `admin-tour.js` | 11 |
| `tour.js` | 11 |
| `utils.js` | 7 |
| `dashboard-stats.js` | 7 |
| `landing-map.js` | 5 |
| `dashboard-reservations.js` | 4 |
| `vehicles.js` | 4 |
| `profile-help.js` | 4 |
| `reservas-form.js` | 3 |
| `dashboard-ui.js` | 3 |
| `dashboard-tickets.js` | 3 |
| `onboarding_helpers.js` | 3 |
| `virtual-time.js` | 1 |
| `dashboard-metrics.js` | 0 (solo `typeof window.Chart` read) |
| `chart_window.js` | 0 (solo `typeof window.Chart` reads, nuevo módulo v9.20.0) |

**Caso peor (revisión v9.20.0):** `notifications.js` — además de 22 asignaciones, registra listeners globales al importar (clic del dropdown en línea 709, `DOMContentLoaded` en línea 735), generando efectos colaterales por el simple hecho de importarlo. Ese efecto colateral se mantiene por diseño (se importa como side-effect desde `dashboard.js:14`, que se carga solo en el dashboard), pero ya no escribe `window.*`.

**Resolución (v9.21.0):** se eliminaron las **76 asignaciones reales** de los 14 módulos y la exposición global quedó solo en los puentes:

- **Módulos limpiados:** `notifications.js` (22 → 19 exports), `admin-tour.js` (11), `tour.js` (9; quedan 10 exports), `utils.js` (7; quedan los formatadores exportados), `dashboard-stats.js` (4), `dashboard-reservations.js` (4), `profile-help.js` (4), `landing-map.js` (5), `dashboard-tickets.js` (3), `dashboard-ui.js` (2), `onboarding_helpers.js` (2), `reservas-form.js` (1), `virtual-time.js` (1), `vehicles.js` (1). El grep `^\s*window\.\w+\s*=` (sin ampliar) sobre `static/js/modules/*.js` devuelve **0 asignaciones**; solo quedan lecturas `typeof window.X === 'function'` y llamadas `window.x(...)`, permitidas porque los puentes proveen esos globals.
- **Estado interno a variables de módulo** (deja de usar `window` como estado): `pollInterval` (notifications), `_toastsClickBound` (utils), `allReservations` (dashboard-reservations, interno; también se quitó `window.allReservations`), `_resBadgeInterval → resBadgeInterval`, `_diagInterval → diagInterval` (dashboard-ui), `allBranchesMap`/`_userMarker`/`_userCircle` (landing-map).
- **Globals eliminados por duplicación o por estar muertos:** `window.selectHourRange` (muerto, solo definición), `window.filterMapByLocality` (QUEDA como export y se usa intra-módulo en 323/416, sin refs en templates), `window.getVirtualNow` (lo define la plantilla `virtual_time_banner.html` inline), `window.updateTicketBadge` (se usa `tickets.updateTicketBadge()` desde `dashboard.js`, single point of truth), `window.userVehicles` (lo escribe `perfil.js` tras `loadVehicles()`; lector único `tour.js`).
- **Asignaciones añadidas a los puentes:** `perfil.js` (+17 notif, +3 tours con alias `window.endReservationTour = endTour`, +4 support-help, +2 legal, +6 formatadores, `getDirectionsTo`, `userVehicles`); `dashboard.js` (+`filterAdminHelpCategory/Search`, `changePageLogs/filterLogs/changePageOcc/filterOccupancy`, +6 formatadores); `main.js` (+6 formatadores, cubre toda página vía `base.html`); `landing.js` (+`getDirectionsTo`).
- **Verificación:** `node --check` en verde para los 23 scripts tocados; los `onclick` de templates (perfil, dashboard, admin_help_modal, inicio, popups del mapa) quedan cubiertos por los puentes.

**Impacto (revisión v9.20.0):** los puentes re-asignaban lo mismo que ya asignó el módulo (ej. `updateReservationBadge` estaba en `dashboard-reservations.js:1230` y en `dashboard.js`); había doble punto de verdad, acoplamiento al DOM global y dificultad de testeo. Eliminado.

### 3.3 ~~VIOLACIÓN MEDIA~~ **[RESUELTO v9.21.0]**: Doble instancia de `notifications.js` en `perfil.html`

- ~~`templates/perfil.html:123` carga directo `<script type="module" src="/static/js/modules/notifications.js?v=9.10.1">`.~~
- ~~`static/js/perfil.js:8` además importa `./modules/notifications.js?v=9.8.6`.~~

Con versionado distinto (`?v=9.10.1` vs `?v=9.8.6`) el navegador creaba **dos instancias del módulo** → doble `DOMContentLoaded` y doble listener de click; solo lo mitigaba el guard `window.__autopassNotifPollInterval`.

**Resolución:** se eliminó el script directo de `perfil.html` (el import de `perfil.js` ya cubría la funcionalidad) y se unificó el cache-busting en `?v={{ cache_buster }}`.

### 3.4 VIOLACIÓN MEDIA: Lógica de negocio en scripts puente y templates

- **`static/js/main.js`**: 84 líneas con lógica real (`updateAuthNav`, restauración de sidebar, manejo bfcache/pageshow y tecla Escape). El propio archivo lo admite con `// MANTENER AQUI POR AHORA O MOVER UN UI.JS`.
- **`static/js/dashboard.js`**: `switchMonitorTab` implementa lógica inline, y el bloque `DOMContentLoaded` decide tab inicial por rol (lógica de RBAC en el puente). Un dispatcher/puente no debería decidir permisos.
- ~~**`templates/reset_password.html`**: ~95 líneas de validación de contraseña en un `<script type="module">` (líneas 112-207, de 207 totales; deberían estar en un módulo reutilizando `auth.js`).~~
- ~~**`templates/estadisticas_ocr.html`**: ~269 líneas de script inline (líneas 527-796 de 797 totales) con lógica de la página — una reducción respecto a versiones previas pero sigue sin ser un módulo externo.~~
- **`templates/monitoreo_live.html`**: bridge inline de 16 líneas (aceptable, cumple el patrón de forma liviana).

**Resolución (v9.22.0):** `reset_password.html` pasó a cargar `static/js/modules/reset_password.js` (reutiliza `auth.evaluatePassword`/`initPasswordValidation` y `api.js`; se eliminó la reasignación redundante de `window.togglePasswordVisibility`, ya global vía `main.js`, y el `fetch` directo a `/v1`). `estadisticas_ocr.html` extrajo su lógica a `static/js/modules/estadisticas_ocr.js` (módulo sin `window.*`), con un bridge inline de 5 líneas en el template que expone `window.actualizarEstadisticasOcr`/`window.filtrarTablaOcr` (exigidos por los handlers inline) e inicia el dashboard vía `initEstadisticasOcr()`, siguiendo el precedente aceptado de `monitoreo_live.html`. `node --check` OK y **152 tests en verde**.

### 3.5 Megamódulos frontend

| Módulo | Líneas | Observación |
|---|---|---|
| `tour.js` | 1730 | Tours de cliente + helpers de onboarding mezclados |
| `dashboard-reservations.js` | 1294 | Listado + filtros + alta + edición + badge + descuentos |
| `reservas-form.js` | 1262 | Formulario + estimador + pickers + disponibilidad + descuentos |
| `landing-map.js` | 854 | Mapa + buscador + autocompletado + POIs |
| `admin-tour.js` | 895 | Tours admin + centro de ayuda (FAQ/buscador) |
| `notifications.js` | 745 | Centro de notificaciones + dropdown + badges + acciones |

Son mantenibles pero se acercan al límite de responsabilidad única; conviene partir en submódulos (acción recomendada, prioridad baja/media).

### 3.6 ~~Cache-busting manual inconsistente~~ **[RESUELTO v9.21.0]**

- ~~`perfil.html` usa `?v=9.18.3/9.10.1/9.10.1/9.10.1` hardcodeados por archivo.~~
- ~~`notifications.js` cargado directo con `?v=9.10.1` pero importado con `?v=9.8.6` en `perfil.js` (causa directa del bug 3.3).~~
- ~~`dashboard.html` usa `?v={{ cache_buster }}` (correcto) mientras otros templates no.~~

**Resolución:** todos los templates (`base.html`, `dashboard.html`, `index.html`, `nuestra-red.html`, `perfil.html`) usan `?v={{ cache_buster }}`; los imports intra-módulo se quitaron `?v=` (evita instancias duplicadas).

---

## 4. Tests y Reglas de Extensión

- **[OK]** `tests/` organizados por dominio (`test_access_service.py`, `test_admin_reservations.py`, `test_notifications.py`, `test_oauth.py`, etc.). Nota: la suite corre **152 tests pasando en 23 archivos** (`pytest -q`); el conteo previo de 74 tests + 4 errores era un artefacto del entorno por faltar `slowapi==0.1.9` (instalada localmente).
- **[OK]** Todo valor configurable pasa por `core/config.py` desde `.env` (no se detectó hardcoding nuevo en el alcance auditado salvo los strings de la sección 2.5).
- **[PARCIAL]** Los tests de reservas (`test_admin_reservations.py`) y notificaciones crecieron rápido (+320 y +208 líneas en el último commit); se benefician de helpers/fixtures compartidos.

---

## 5. Plan de acción (orden de impacto)

### Prioridad 1 — Restaurar el Bridge Pattern (frontend)
1. ~~Sacar las ~89 asignaciones `window.*` de los 15 módulos y moverlas a los scripts puente (`dashboard.js`, `perfil.js`, `main.js`).~~ — **[HECHO]** en v9.21.0 (working tree, sin commitear): 76 asignaciones reales migradas desde 14 módulos (ver §3.2); puentes actualizados en `perfil.js`, `dashboard.js`, `main.js` y `landing.js`; estado interno pasado a variables de módulo; `node --check` en verde en los 23 scripts y grep de asignaciones `window.*` en módulos → 0 hits.
2. ~~Eliminar la doble carga de `notifications.js` en `perfil.html` y unificar cache-busting (`?v={{ cache_buster }}`); quitar `?v=` en imports intra-módulo.~~ — **[HECHO]** en v9.21.0.

### Prioridad 2 — Adelgazar rutas (backend)
3. ~~`routes/admin/branches.py` (20 queries): mover la propagación de rename a `BranchService.rename_branch(...)`~~ — **[HECHO]** en v9.21.0: `BranchService.rename_branch()` + `BranchService.has_physical_occupancy()`; además se eliminó un `@router.delete("/branches/{branch_id}")` duplicado (stub huérfano de `d8cbbf2`) que sombreaba la ruta real.
4. ~~`routes/parking/status.py` (15 queries): mover cálculo de ocupación/disponibilidad a `AccessService`/`ReportService` y usar `OccupancyManager` para los WSS.~~ — **[HECHO]** en v9.21.0: nuevo `services/occupancy_service.py` (`calculate_branch_capacities`, `ocupacion_reservas_vigentes`, `current_occupancy`, `capacities_from_aforo`, `default_capacities`, `branch_by_normalized_name`, `aforo_by_normalized_name`); se eliminó la clase `OccupancyManager` duplicada (residuo de merge), el import faltante `asyncio` (el registro del event loop del WS fallaba silenciosamente) y en `current_occupancy` la cortesía (≤10 min) ahora devuelve `deuda=0`.
5. ~~`routes/user/reservations.py` y `routes/admin/reservations.py`: usar `ReservationService.create_reservation/_create_admin_reservation` completo (hoy mezclan queries con el servicio).~~ — **[HECHO]** en v9.21.0: la lógica completa de reservas pasó a `ReservationService` (`create_user_reservation`, `modify_user_reservation`, `list_user_reservations`, `confirm_reminder`, `create_admin_reservation`, `update_admin_reservation`, `confirm_reservation_payment`, `list_admin_reservations`, `lookup_patente`, `get_new_reservations_count`, `get_reservation_or_404`/`get_permissioned_reservation`, `validate_manual_vinculacion`, `validar_horario_sucursal`). `routes/user/reservations.py` 10→**0** `db.query`; `routes/admin/reservations.py` 15→**1** (queda solo el query de ticket aplicado en `reservation_redemption_info`). Se eliminó `_validar_horario_sucursal` y la query muerta de `branches` de la ruta user, y el `import re` local de `simulate_refund`. Los 26 tests de `tests/test_admin_reservations.py` siguen verdes.
6. ~~`routes/user/vehicles.py`: consolidar en `UserService` (CRUD + validaciones ya existe parcialmente).~~ — **[HECHO]** en v9.21.0: `UserService.list_vehicles/add_vehicle/set_favorite_vehicle/delete_vehicle` + helper compartido `_last_entry_active` (reutilizado por `delete_user`).

### Prioridad 3 — Enums y god services
7. ~~Reemplazar los strings mágicos de 2.5 por los `AccessEventType`, `UserRole` y `ReservationStatus`.~~ — **[HECHO]** en v9.21.0: los strings de la tabla 2.5 ya estaban corregidos; se completó el barrido de los restantes en 14 archivos (`routes/parking/status.py`, `routes/admin/settings.py` y `promotions.py`, `routes/system/cameras.py`, `health.py`, `video.py`, `common.py`, `routes/user/balance.py`, `services/reservation_service.py` (8 estados + 7 roles), `support_service.py` (incluye `in_([UserRole.ADMIN, UserRole.LOCAL_ADMIN])`), `branch_service.py` (`UserRole.LOCAL_ADMIN`), `billing_service.py`, `occupancy_service.py`, `report_service.py` y `oauth_service.py`). **152 tests en verde.** Quedan intencionalmente sin enum: naming de `gate_id`/`GATE_TYPE` de ALPR (cameras/access/hardware, acoplamiento documentado), claves de diccionario de `report_service` (pares almacenados) y el `estado` de `SupportTicket` (no existe enum de tickets).
8. ~~Descomponer `reservation_service.py` en `availability.py` + `payments.py` (fachada) y evaluar lo mismo para `access_service.py` y `report_service.py`.~~ — **[HECHO]** en v9.21.0 (working tree): fachada de 687 líneas + `availability.py` (382) + `payments.py` (422) vía mixin; 152 tests en verde. Incluye la evaluación pendiente: `access_service.py` (607) y `report_service.py` (581) resueltos en working tree — `access_service.py` descompuesto con `AccessOccupancyMixin` en `access_occupancy.py` (fachada 499 líneas, 2 queries directas), `report_service.py` evaluado como cohesivo (no se descompone; se extrajo el helper `_branch_filter`). Ver §2.3.

### Prioridad 4 — Templates y megamódulos
9. ~~Extraer la lógica de `reset_password.html` a un módulo (reutilizar validación de `auth.js`) y `estadisticas_ocr.html` a un módulo dedicado.~~ — **[HECHO]** en v9.22.0 (working tree): nuevos módulos `static/js/modules/reset_password.js` y `static/js/modules/estadisticas_ocr.js`; validación de clave reutilizada vía `evaluatePassword`/`initPasswordValidation` de `auth.js`; `estadisticas_ocr.html` con bridge inline de 5 líneas. `node --check` OK y 152 tests en verde. Ver §3.4.
10. Partir `tour.js`, `dashboard-reservations.js` y `reservas-form.js` en submódulos temáticos.

---

## 6. Anexos — Evidencia

- Conteo de `db.query` por ruta (sección 2.2) obtenido con búsqueda estática sobre `routes/**/*.py` (revisión v9.20.0: 132 hits en 17 archivos).
- Conteo de `window.*` por módulo (sección 3.2) obtenido con búsqueda `window\.\w+\s*=` sobre `static/js/modules/*.js` (revisión v9.20.0: 90 matches en 16 archivos, 88 asignaciones reales descartando reads typeof; post-migración v9.21.0: `^\s*window\.\w+\s*=` → 0 matches, subsisten solo lecturas `typeof window.X ===`).
- Carga de scripts verificada en `templates/base.html`, `dashboard.html`, `perfil.html`, `monitoreo_live.html`, `reset_password.html` y `estadisticas_ocr.html`.
- Tests corridos con `pytest -q` (152 passed; `slowapi` instalada destraba la colección completa).
- Tamaños de módulos verificados con `(Get-Content).Count` en PowerShell.
- Auditoría original sin modificar código; desde v9.21.0 este documento registra además el avance del plan (§5) con los cambios aplicados y sus tests.