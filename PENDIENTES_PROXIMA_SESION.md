# PENDIENTES_PROXIMA_SESION.md

Recordatorio de trabajo pendiente para continuar en una proxima sesion.
Ultima actualizacion: 16/11/2026

## Sin commitear en este momento

- Ninguno (árbol de trabajo limpio).

## Cerrado recientemente

### 16/11/2026 - Rediseño de Mapa de Calor de Tráfico y Descarga Directa de PDF
- **Rediseño del Mapa de Calor de Tráfico (Métricas)**:
  - Cuadrícula mensual interactiva y focalizada mes a mes (28-31 columnas según el mes), con navegación fluida entre meses (`< Anterior` / `Siguiente >`), títulos en dorado suave y resaltado de fines de semana.
  - Tarjetas de KPIs calculadas en el frontend específicas para el mes visualizado (hora pico del mes, día de la semana con mayor flujo acumulado, promedio diario y total de entradas).
  - Remoción de la cabecera duplicada de la grilla (`[ SUCURSAL ] [ MES ] [ TOT ]`), de los filtros obsoletos de fecha (`DESDE`, `HASTA`, `APLICAR`, `LIMPIAR`) y de textos explicativos y notas al pie redundantes.
- **Optimización de Exportación a PDF**:
  - Eliminación definitiva del botón y exportación a HTML.
  - Descarga directa de PDF: apertura inmediata del cuadro de diálogo nativo de guardado/impresión del navegador mediante un iframe invisible en la misma pestaña, sin abrir pestañas ni ventanas en blanco.
  - Supresión de la caja de parámetros y filtros activos (`PARAMETROS Y FILTROS ACTIVOS EN EL DASHBOARD`) en el informe exportado.
- **Cache Busting**:
  - Actualización del Service Worker a `autopass-shell-v17` en `static/sw.js` y query string `?v=17` en `static/js/dashboard.js`.

### 10/11/2026 - Limpieza de Documentación Redundante
- **Limpieza de documentación no operativa**:
  - Eliminación de la carpeta `Info proyecto/` y archivos sueltos de auditoría/prueba (`AISLAMIENTO_MULTIORG.md`, `AUDITORIA_DB.md`, `AUDITORIA_DB_NEON.md`, `BUGS_A_RESOLVER.md`, `USUARIOS_PRUEBA.xlsx`, `qr-code.png`).
  - Preservación íntegra de `Diseno_Proyecto/` como documentación formal RUP del sistema.
  - Actualización de `INDICE_DOCUMENTACION.md` apuntando a `Diseno_Proyecto/` y archivos normativos raíz (`AGENTS.md`, `README.md`, `PENDIENTES_PROXIMA_SESION.md`).

### 10/11/2026 - Aislamiento Multiempresa P1 + Informe de Testing y Validaciones
- **Implementación de los 5 P1 de aislamiento multiempresa (`test_multiorg_p1_scope.py` 13/13 passed)**:
  - **P1.1 (`lookup_patente`)**: acepta `staff`, acotando búsqueda por patente a la organización del operador; fail-closed si no tiene org o pertenece a otra empresa.
  - **P1.2 (`get_admin_available_redemptions`)**: valida que el usuario y el operador pertenezcan a la misma empresa (`HTTP 403` si difieren o si el staff carece de empresa).
  - **P1.3 (`validate_manual_vinculacion`)**: valida alcance multi-tenant al asociar un usuario por patente en caja.
  - **P1.4 (Reportes y `_branch_filter`)**: `_branch_filter` devuelve `false()` en multi-org si no hay sede/empresa; `get_financial_summary` y `get_access_logs` aplican `require_tenant_scope` y resuelven la empresa para evitar sumar sedes homónimas de otras organizaciones ($100 en lugar de $1099).
  - **P1.5 (`redeem_points`)**: rechaza con `HTTP 404` el canje de promociones pertenecientes a otra organización.
- **Informe de Testing y Validaciones**:
  - `Info proyecto/INFORME_TESTING_Y_VALIDACIONES.md` (matriz de pruebas, validaciones en 4 capas, guards y métricas) y versión para impresión `Info proyecto/INFORME_TESTING_Y_VALIDACIONES.pdf` (5 páginas, generada con `_tools/export_pdf.py`).
  - Catálogo en `INDICE_DOCUMENTACION.md` actualizado.

### 10/11/2026 - Soporte WebSocket y Web Serial para Arduino Hardware Bridge + Hardening Concurrencia
- **Soporte de WebSocket para Arduino Hardware Bridge (Cloudflare / Tailscale)**:
  - **Endpoint WebSocket**: `routes/system/hardware.py` implementa `@router.websocket("/ws/hardware")` con autenticación por `node_secret` (`ALPR_NODE_SECRET` o `SECRET_KEY`), IP de red privada (Tailscale) o token JWT operativo.
  - **HardwareService**: `services/hardware_service.py` añade `register_ws`, `unregister_ws` y `broadcast_ws(payload)`, y en `trigger_barrier` emite el evento por WebSocket hacia todos los puentes conectados (además de MQTT y Serial local).
  - **Arduino Bridge**: `scripts/arduino_bridge.py` actualizado con soporte dual: modo WebSocket (`--url https://tu-dominio.trycloudflare.com` o IP de Tailscale, reconexión automática y auto-detección de puerto COM) y modo MQTT retrocompatible.
  - **Web Serial en Dashboard (100% Web sin consola)**: Módulo `static/js/modules/dashboard-web-serial.js` integrado en `dashboard.js` y `templates/dashboard/tabs/live.html`. Permite que desde Chrome/Edge en la laptop el usuario presione "Conectar Maqueta USB", autorice el puerto serie y el propio navegador accione el Arduino por USB en tiempo real ante detecciones ALPR, QR o clics en el panel.
  - **Tests y Guards**: `tests/test_hardware_routes.py` (7 tests nuevos: autenticación por secret, SECRET_KEY y JWT operativo, rechazo sin auth, broadcast de eventos de barrera, helper `build_ws_url` y procesamiento de payloads). Suite completa en verde.
- **Fix del control flaky `sin_lock` (R1/R2)**:
  - `tests/test_concurrencia_reservas.py` suma `_correr_dos_carrera` + `_sincronizar_tras_leer`, que sincronizan los hilos entre la lectura de decisión y la escritura para garantizar la ventana de carrera determinista sin depender de la velocidad del runner de CI. Documentado en `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md`.
- **Docs de responsables y catálogo de documentación**:
  - `Info proyecto/RESPONSABLES_BACKLOG.md` y catálogo en `INDICE_DOCUMENTACION.md`.
  - Helper portable `run_pytest.bat`.

### 20/10/2026 - Fase 6 del plan de concurrencia: hardening y cierre (PLAN COMPLETO)
- **Que se hizo**: los 4 puntos de cierre del informe. (1) El CI ahora corre el grupo `postgres` contra un servicio Postgres 16. (2) Suite sin regresiones. (3) Guards 11/11. (4) El contrato de `bloqueo_transaccional` quedo documentado en la guia de desarrollo.
- **CI**: `.github/workflows/ci.yml` suma `services.postgres` (imagen `postgres:16`, con healthcheck `pg_isready`) y un paso final `python -m pytest -m postgres tests/` con `DATABASE_URL=postgresql://autopass:autopass@localhost:5432/autopass_test`. El `DATABASE_URL` se define **solo en ese paso** (no a nivel de job) para que la suite normal siga igual: sin la variable, el grupo `postgres` se salta solo, no falla.
- **Guard `REQUIRE_POSTGRES`**: el paso de CI lo setea en `1`, asi un Postgres ausente o inalcanzable **falla** en vez de saltear. Sin esto, un servicio caido (o una `DATABASE_URL` mal puesta) daba 15 skips y CI en VERDE: los tests de concurrencia no habrian corrido y nadie se habria enterado (era el problema de fondo del punto 1). En `tests/postgres_helpers.py` el skip (`pg_only` y `solo_si_postgres_esta_vivo`) respeta el flag; localmente sin el flag sigue siendo un skip amable. Se verificaron los 5 caminos: flag+DB muerta -> falla; flag+URL sqlite -> falla; sin flag+DB muerta -> skip; sin flag+URL sqlite -> skip; flag+DB viva -> 15 passed.
- **Por que**: el informe pedia que los tests de concurrencia "queden en CI", pero el CI corria pytest sin Postgres y el `addopts = -m "not postgres"` los deseleccionaba: los tests del plan NUNCA corrian solos en un push. Era verificacion manual disfrazada de automatizada.
- **Docs**: `Info proyecto/GUIA_DESARROLLO.md` suma la seccion **"Convenciones de Concurrencia (Secciones Críticas)"**: la regla de oro (toda escritura que dependa de un `SELECT` previo abre seccion critica), el contrato del helper (claves ordenadas anti-deadlock, el lock vive hasta commit/rollback, re-ejecutar las validaciones DENTRO del `with`, `refrescar` si el objeto ya estaba cargado, no-op en SQLite, `LockTimeoutError -> 409`), las claves canonicas (`clave_aforo`/`clave_patente`/`clave_usuario`/`clave_reserva`) y las redes de seguridad de las Fases 1/4/5. Ademas se agrego el **mandato arquitectonico 8** ("Concurrencia") a la lista de MANDATOS, para que la regla rija en sesiones futuras.
- **Correccion de docs**: el conteo de tests de la guia decia "756 pruebas en 56 archivos" (obsoleto); se midio y se corrigio a **956 pruebas en 72 archivos** (941 por defecto + 15 del grupo `postgres`).
- **Verificacion**: suite por defecto `941 passed, 15 deselected, 9 warnings`; grupo `postgres` `15 passed` (con `REQUIRE_POSTGRES=1` tambien); guards `11/11` (incluidos `check_consistencia_frontend`, 132 rutas, y `check_css_huerfano`, 0 huerfanas, los 2 que nombraba el informe); YAML del workflow validado con `yaml.safe_load` (servicio `postgres` presente, 7 pasos, `DATABASE_URL` y `REQUIRE_POSTGRES` solo en el paso del grupo); los 5 caminos del guard `REQUIRE_POSTGRES` probados. Actualizado `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md` (Fase 6 IMPLEMENTADA, encabezado "plan COMPLETO", orden de ejecucion).

### 20/10/2026 - Fase 4 del plan de concurrencia: constraint de no-solape de patente por sede (Postgres)
- **Que se hizo**: migracion Alembic `b1c2d3e4f5a6_reservations_exclude_solape_patente.py` con un `EXCLUDE USING gist` que impide que existan dos reservas VIGENTES de la misma patente (normalizada) solapadas en la misma sede. Es la red de seguridad de ULTIMO nivel contra R2: el lock `patente:` de la Fase 2 ya lo evita a nivel de aplicacion, pero el constraint lo evita a nivel de MOTOR, asi que tambien cubre cualquier alta que esquive el servicio (scripts, seeds, SQL a mano).
- **Por que**: si un bug, un script o una migracion futura escriben una reserva sin pasar por el servicio, el lock no la ve. El constraint es la unica defensa que no depende del codigo de aplicacion.
- **Desvios respecto del borrador del informe** (los tres verificados contra Postgres real antes de decidir; el borrador no era aplicable tal cual):
  1. **Sin columna `patente_norm`**: se usa directo la EXPRESION `upper(replace(patente,' ',''))`, que es exactamente lo que evalua `get_overlap_by_patente`. Evita columna nueva, backfill de las 560 reservas y un write-path que mantener sincronizado (si alguien insertaba sin setearla, el constraint no protegia).
  2. **Sobre `sucursal_id`, no `sucursal_nombre`**: el nombre de la sede no es una columna (vive en `parking_branches`, resuelta por un hybrid); la columna real es `sucursal_id`.
  3. **Estados con los valores REALES del enum** (`'Pendiente'`, `'Activa'`, `'Pagado'`, capitalizados). El borrador usaba mayusculas, que no matchean ninguna fila y habrian creado un constraint INUTIL (peor que nada: daba falsa sensacion de proteccion).
  4. Ademas, **el modelo NO declara el constraint**: `create_all` en SQLite falla al intentar emitir un `EXCLUDE` (`UnsupportedCompilationError`), lo que romperia la suite entera. Por eso vive solo en la migracion.
- **Semantica verificada** (identica a la del repositorio): misma patente normalizada (mayusculas sin espacios) + misma sede + rango solapado con semantica `[)` (dos reservas contiguas NO chocan) + solo entre reservas vigentes (Cancelada/Completada/Fallida/Reembolsado no bloquean; fechas NULL tampoco).
- **Tests**: `tests/test_concurrencia_constraints_postgres.py` (11 casos, grupo `postgres`), que **importa el DDL real de la migracion** (`cargar_migracion` en `tests/postgres_helpers.py`) para que el test verifique lo que hay, no una copia. RED confirmado: con el DDL neutralizado fallan exactamente los 3 tests de enforcement (los otros 8 documentan "no bloquea", que trivialmente pasan sin constraint). Se creo `tests/postgres_helpers.py` (andamiaje compartido: resolver URL, probe, skip, schema efimero, carga de migracion) y se refactorizo `tests/test_concurrencia_reservas.py` (R1/R2) para usarlo, sin duplicar.
- **Colision de revision ID**: al escribir la migracion use `f7a8b9c0d1e2`, que YA existia (`f7a8b9c0d1e2_parking_branch_name_per_org.py`, en medio de la cadena). Alembic detecto el ciclo y la corrija: la migracion paso a `b1c2d3e4f5a6` (unico, cadena con un solo head: `b1c2d3e4f5a6`).
- **Aplicada en Neon**: `alembic upgrade head` (version paso de `e5f6a7b8c9d0` a `b1c2d3e4f5a6`). Antes se verifico que las 560 reservas existentes NO tenian ningun solapamiento, asi que aplico limpia (sin ventana de mantenimiento). Verificado contra Postgres real: `btree_gist` instalada (1.8), constraint registrado como tipo `x`, un `INSERT` manual solapado falla con `IntegrityError`, un rango contiguo entra, y no quedo ninguna fila de prueba (560 total, sin cambios).
- **Verificacion**: suite por defecto `941 passed, 15 deselected` (los 11 nuevos son del grupo `postgres`); grupo `postgres` `15 passed` (4 de R1/R2 + 11 de Fase 4), 3 corridas seguidas en verde; guards 11/11; `git diff --check` en 0; sin schemas `rk_*` remanentes en Neon. Reversibilidad verificada en schema aislado: upgrade crea, downgrade borra, re-upgrade recrea. Actualizado `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md` (estado y criterio de salida de Fase 4, los desvios, baseline de Fase 6, orden de ejecucion y el encabezado del informe).
- **Flake detectado y corregido**: el test que verifica que el constraint existe contaba por NOMBRE en `pg_constraint` sin acotar al schema. Al aplicar la migracion en Neon, el mismo nombre existe en `public` Y en el schema efimero del test -> el `COUNT` daba 2 y fallaba. Se acoto con `conrelid = to_regclass('reservations')` (respeta el `search_path`). Solo aparecio DESPUES de aplicar en Neon: es la clase de bug que un test con datos reales descubre y uno aislado no.

### 20/10/2026 - Fase 5 del plan de concurrencia: idempotencia de pagos y manejo de errores
- **Que se hizo**: `MercadoPagoPayment.payment_id` (el id del pago en MP) paso a ser `unique=True` en el modelo y con su migracion Alembic `e5f6a7b8c9d0` (que ademas normaliza a `NULL` los `''` que hubieran quedado y crea el indice unico `ix_mercadopago_payments_payment_id`, de forma idempotente porque `sync_schema` corre `create_all` antes que Alembic). En `services/mercadopago_service.py`, `_aplicar_pago` guarda `NULL` (no `''`) cuando MP no devuelve id: varios `NULL` no colisionan en un indice unico, asi que los pagos pendientes conviven. Se agrego un handler global `IntegrityError -> HTTP 409` en `main.py` (mismo patron que `LockTimeoutError`) y rollback explicito en `get_db` para que la sesion quede limpia.
- **Por que**: Mercado Pago REINTENTA los webhooks; sin clave de idempotencia a nivel de base, dos entregas del mismo pago pueden acreditar dos veces (doble cobro / doble acreditacion de puntos). El `unique` es la defensa especifica contra ese reintento.
- **Guarda bajo lock**: la `if pago.aplicado` de `confirm_payment` (que era un read-then-write) ya quedaba doble desde la Fase 2: `_aplicar_pago` re-lee la columna `estado` dentro de `bloqueo_transaccional` y sale sin acreditar si otro webhook ya lo aplico. La Fase 5 la refuerza a nivel de motor.
- **Tests**: `tests/test_concurrencia_idempotencia_pagos.py` (6 casos): `payment_id` unico choca con `IntegrityError`; varios `NULL` conviven; `_aplicar_pago` guarda `NULL` y no `''`; dos confirmaciones = un solo cobro y una sola acreditacion de puntos; dos POST del webhook por la ruta real no duplican; `IntegrityError` en un endpoint devuelve 409 (verificado ademas que el test FALLA si se quita el handler).
- **Migracion en Neon**: aplicada con `alembic upgrade head` (version paso de `d9e0f1a2b3c4` a `e5f6a7b8c9d0`). Verificado contra Postgres real: el indice unico rechaza duplicados con `IntegrityError` y varios `NULL` conviven; no habia `''` en la base (0 filas), asi que la normalizacion fue no-op; sin filas basura ni schemas temporales.
- **Verificacion**: suite por defecto `941 passed, 4 deselected, 9 warnings`; grupo `postgres` `4 passed`; guards 11/11. Actualizado `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md` (estado y criterio de salida de Fase 5, baseline de Fase 6).

### 20/10/2026 - Fase 3 del plan de concurrencia: invalidacion del cache de disponibilidad
- **Que se hizo**: helper `invalidar_cache_disponibilidad(sucursal=None)` en `services/availability.py`. TODAS las claves del cache guardan la sucursal en la posicion 1, asi que con `sucursal` se invalidan solo las entradas de esa sede y con `None` se vacia el cache completo (callers que no conocen la sede). Se invoca **despues del commit** en `create_user_reservation` y `modify_user_reservation` (`services/reservation_service.py`) y en `cancel_reservation` (`services/payments.py`): invalidar antes no sirve porque la transaccion podria hacer rollback y una consulta concurrente podria repoblar con el estado viejo.
- **Por que**: con el cache de 30 s, el selector de horarios seguia ofreciendo un rango recien ocupado (o marcando como ocupado uno recien liberado) hasta que expiraba el TTL. Es la parte de R1/R2 que cierra la Fase 3.
- **Limite documentado en el codigo**: el cache vive en memoria del proceso; con mas de un worker uvicorn la invalidacion deja de ser global (habria que ir a Redis o invalidar por version en BD).
- **Tests**: `tests/test_concurrencia_cache_disponibilidad.py` (RED->GREEN del helper: horas, fechas, invalidacion por sede, vaciado total, y un caso que documenta que sin invalidar el cache sirve el valor viejo), `tests/test_concurrencia_cache_flujos.py` (los 3 flujos reales de crear/modificar/cancelar invalidan la sede) y `tests/test_concurrencia_reservas.py` (R1/R2 con concurrencia real: schema efimero de Postgres + 2 hilos con barrera; cada carrera trae CONTROL sin lock y GREEN con lock; 5 corridas seguidas en verde). RED confirmado: la importacion fallaba al no existir la funcion.
- **Grupo `postgres`**: `tests/test_concurrencia_reservas.py` quedo marcado con `pytest.mark.postgres` (module-level) y `pytest.ini` lo deselecciona por defecto (`addopts = -m "not postgres"`), asi que la suite normal es rapida y offline. Para correrlo: `venv\Scripts\python.exe -m pytest -m postgres` (el `-m` de la linea de comandos pisa el addopts).
- **Verificacion**: suite por defecto `935 passed, 4 deselected, 9 warnings`; grupo `postgres` `4 passed` (y `4 skipped` si la base no responde); guards 11/11; imports OK; sin schemas de test remanentes en Neon. Actualizado `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md` (estado de Fase 0, Fase 2, Fase 3 y Fase 6).
- **Commiteado y pusheado** en `81c5833` ("feat(concurrencia): Fase 3 - invalidacion del cache de disponibilidad + tests R1/R2 en Postgres"), fast-forward a `origin/main`.

### 19/10/2026 - Fase 1 del plan de concurrencia: aritmetica atomica de saldo y puntos
- **Que se hizo**: todos los ajustes de saldo/puntos pasan por 6 helpers de `repositories/user_repository.py` que ejecutan UN solo `UPDATE ... RETURNING` (`sumar_saldo`, `descontar_saldo`, `fijar_saldo`, `sumar_puntos`, `canjear_puntos`, `descontar_puntos_tope_cero`). Las condiciones (saldo/puntos suficientes, tope cero, `COALESCE` para columnas en NULL) viajan dentro de la sentencia: 0 filas = no alcanzaba (se lee como `None`), asi que desaparece la ventana entre el chequeo y el descuento. Ningun helper hace commit: lo decide el flujo, tipicamente dentro del lock de la Fase 2.
- **Sitios migrados**: 20 en 6 archivos - `services/payments.py` (6: descuento de saldo, acreditacion de puntos en los 3 caminos de pago, reembolso de saldo y de puntos con tope cero), `services/billing_service.py` (4: puntos por estadias), `services/reservation_service.py` (6: ajuste por edicion de reserva + reembolso admin), `routes/user/fidelization.py` (2: canje y anulacion), `routes/user/balance.py` (1: recarga) y `routes/admin/users.py` (1: set del admin). `update_balance`/`add_points` (que eran codigo muerto) ahora delegan en los helpers.
- **Tests**: `tests/test_concurrencia_saldo_puntos.py` (3 tests de carrera real: hilos + `threading.Barrier` sobre SQLite de archivo con WAL y `busy_timeout`) y `tests/test_user_repository_atomic.py` (10 unitarios del contrato: valor devuelto, no alcanza, tope cero, columnas NULL). `tests/test_balance_routes.py` suma `_seed_user_saldo(...)` en los 2 tests de recarga, porque el saldo dejo de actualizarse en memoria y el `UPDATE` necesita la fila (no se cambio ninguna asercion).
- **Verificacion**: RED reproducido contra `95aca58` en un worktree temporal (3 failed: doble gasto de saldo, 10 puntos en vez de 20, dos tickets con 80 puntos) -> GREEN con el fix (3 passed). Suite completa `927 passed, 9 warnings`; guards 11/11; `py_compile` y `git diff --check` en 0; grep sin `+=`/`-=` sobre saldo/puntos en codigo de negocio.
- **Material de defensa**: los paquetes `DEFENSA_FASE1/` y `DEFENSA_FASE2/` se sacaron de la carpeta del proyecto (20/10/2026). En su lugar, el material de defensa/comunicacion vive ahora en `Info proyecto/BLOQUEO_TRANSACCIONAL_PARA_DUMMIES.md` (explicacion llana de las 6 fases, sin codigo).

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

- **Plan de concurrencia (continuacion)**: hechas la Fase 1, la Fase 2, la Fase 3 (invalidacion del cache de disponibilidad post-commit) y la **Fase 5** (idempotencia de webhooks por `payment_id`). R1/R2 tienen su prueba real de concurrencia en Postgres (`tests/test_concurrencia_reservas.py`). Sigue la **Fase 4** (constraints en Postgres, requiere ventana de migracion) y la **Fase 6** (hardening y cierre). Referencia: `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md` (seccion 7).
- **git push**: AL DIA. `c60e087` (v9.34.96), `b1288be` (v9.34.97), `e0449b3` (v9.34.98), `f652832` (v9.34.99) y la Fase 1 + Fase 2 del plan de concurrencia pusheados; `origin/main` al dia (verificado con fetch: ahead 0 / behind 0, sin marcadores de conflicto).
- **Performance parte 2 (CSS/JS local por pagina)**: mover `landing-map.css` (12 KB), `chart-window.css`, `sidebar.css`, `tables.css`, `badges.css` y `action-menu.css` fuera de base.html hacia las paginas que las usan, mas el `style.css` legacy (3.8 KB). Ganancia modesta: ya estan en el precache del service worker, asi que no elimina descargas de red. Exige verificar los estilos computados antes/despues en navegador real.
- **Nominatim (revision, no tocado)**: `dashboard-admin-branches-crud.js` y `dashboard-promotions.js` hacen fetch cross-origin a nominatim SIN reintento; mismo patron de riesgo (un error sin CORS llega como TypeError). Se puede reutilizar el patron de `esReintentable()`.
- **POIs/Overpass (opcional, no tocado)**: la consulta tarda ~30-45 s (bbox CABA/GBA, `[timeout:60]`, `out center 100`). Se podria acotar el bbox o bajar el tope; alternativa: espejo `overpass.kumi.systems` (requiere sumarlo a `connect-src` en main.py y al test `tests/test_security_headers.py`).
- **Menores no urgentes**: revision de contraste en puntos sueltos.
- **Deuda de docs**: v9.34.90 y v9.34.93 quedaron sin entrada en HISTORIAL (se documentaron en el mensaje del commit, no en el historial).

## Verificacion usada en esta tanda

- Guards: 11/11 en verde (`Get-ChildItem _tools -Filter "check_*.py"` corridos con `.\venv\Scripts\python.exe`).
- Suite: `941 passed, 15 deselected, 9 warnings` por defecto (ultima corrida, 20/10/2026). Los 15 deselected son del grupo `postgres` (4 de R1/R2 en `tests/test_concurrencia_reservas.py` + 11 de constraints de Fase 4 en `tests/test_concurrencia_constraints_postgres.py`); se corren aparte con `venv\Scripts\python.exe -m pytest -m postgres`. Todos los tests y guards se corren con el python del venv; el python global del sistema no tiene alembic.
- Fase 3 + R1/R2 (20/10/2026): RED confirmado en el cache (import fallaba); `tests/test_concurrencia_reservas.py` corrido 5 veces seguidas en verde; camino de skip verificado (4 skipped con Postgres caido); sin schemas `rk_test_*` remanentes en Neon. Commit `81c5833` pusheado.
- Fase 5 (20/10/2026): RED confirmado (3 fallos: sin `unique`, `''` en vez de `NULL`, sin handler 409); el test de 409 FALLA si se quita el handler (verificado); migracion `e5f6a7b8c9d0` aplicada en Neon (`alembic upgrade head`); el indice unico rechaza duplicados con `IntegrityError` y varios `NULL` conviven; 0 filas `''` previas; sin filas basura ni schemas temporales.
- Fase 4 (20/10/2026): RED confirmado con el DDL neutralizado (fallan solo los 3 tests de enforcement); colision de revision ID detectada por Alembic y corregida (`f7a8b9c0d1e2` -> `b1c2d3e4f5a6`, un solo head); migracion `b1c2d3e4f5a6` aplicada en Neon; verificado en real: `btree_gist` 1.8, constraint tipo `x`, INSERT solapado rechazado con `IntegrityError`, contiguo aceptado, sin filas de prueba; 0 solapamientos preexistentes entre las 560 reservas; sin schemas `rk_*` remanentes. Reversibilidad probada (upgrade/downgrade/re-upgrade). Flake corregido: el test de existencia del constraint contaba global por nombre (daba 2 al existir tambien en `public`); acotado con `to_regclass`. 3 corridas seguidas del grupo `postgres` en verde.
- `node --check` en `static/js/modules/landing-map-pois.js` y `static/sw.js`.
- Runtime: Edge headless + CDP contra el server local (puerto 8013). FASE A: 2 fallos CORS simulados -> 2 warns de reintento -> HTTP 200 -> 100 POIs y cache creada. FASE B: saturacion real de Overpass -> 1 fallo real 502-sin-CORS -> reintento -> 100 POIs, 0 errores OVERPASS. La senal de exito es la cache POI (los 5 `poi-marker` fijos son estadios).
- Script: `C:\Users\usuario.DESKTOP-P7MEQGK\AppData\Local\Temp\opencode\verify_poi_retry.py` (diagnostico previo: `diag_poi_cdp.py` y `diag_overpass_429.py`).
