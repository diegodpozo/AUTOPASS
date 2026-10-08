# AUDITORIA DE BASE DE DATOS — NEON (POSTGRES)

Fecha: 2026-10-07 — Auditoría read-only contra Neon (`.env.DATABASE_URL`).

## Alcance

17 tablas auditadas (conteos reales):

| tabla | filas |
|---|---|
| access_logs | 12.495 |
| users | 416 |
| reservations | 176 |
| settings | 77 |
| vehicles | 63 |
| mercadopago_payments | 37 |
| redemption_tickets | 30 |
| parking_cameras | 22 |
| support_tickets | 20 |
| support_ticket_messages | 59 |
| user_notifications | 174 |
| user_sessions | 79 |
| points_log | 363 |
| promotions | 5 |
| parking_branches | 5 |
| parking_aforo | 5 |
| parking_floors | 0 |

## RESULTADO GLOBAL

- **Duplicados críticos (usuarios/emails/DNI/patentes/sucursales/settings): 0.**
- **Datos semilla/demo son la mayoría del tráfico**: 11.730 de 12.495 access_logs tienen `imagen_path = 'demo:traffic'` (94%). Solo 765 logs son reales.
- Se encontraron **6 hallazgos funcionales reales** y varias inconsistencias menores.

---

## HALLAZGOS (ordenados por impacto)

### H1 — `tipo_vehiculo` mezclado: `'MOTO'/'CAMIONETA'/'AUTO'` (MAYÚSCULAS) vs `'Moto'/'Camioneta'/'Auto'`  ⚠️ CRÍTICO

Valores en producción mezclados según tabla:

| tabla | mayúsculas (no canónico) | canónico |
|---|---|---|
| access_logs | AUTO 2.956 / MOTO 1.854 / CAMIONETA 3.430 | Auto 4.239 / Moto 16 |
| reservations | AUTO 24 / MOTO 12 / CAMIONETA 26 | Auto 114 |
| vehicles | AUTO 16 / MOTO 10 / CAMIONETA 18 | Auto 19 |

**Impacto**:
- `BillingService.get_rate` (billing_service.py:41-44), `get_hourly_rate` (:66-69) y `get_30min_rate` (:89-92) comparan `tipo_vehiculo == VehicleType.MOTO` / `== "Moto"` (case-sensitive). Una moto con log `'MOTO'` termina calculándose con **clave de AUTO** (`precio_hora`, no `precio_hora_moto`).
- Facturación real en curso: `access_service.py:472` y `mercadopago_service.py:130-131` pasan `ultimo.tipo_vehiculo / log.tipo_vehiculo` directamente → las motos/camionetas con tipo en mayúsculas se cobran con tarifa de auto. Hay **12 logs reales MOTO, 44 CAMIONETA y 34 AUTO (no demo) sin pagar expuestos** a este bug.
- Reportes financieros filtran `AccessLog.tipo_vehiculo == vehicle_type` (report_repository.py:78 y 103) con valores de UI `'Auto'/'Moto'/'Camioneta'` → las filas en mayúsculas **quedan excluidas** → métricas de motos/camionetas dan 0/parciales.
- `report_service.py:158-160` usa `e.tipo_vehiculo` como clave de cache → mezclas claves.

**Origen**: script `scripts/crear_usuarios_demo.py` crea vehículos/logs con `['AUTO','MOTO','CAMIONETA']`. `user_service.add_vehicle` valida y normaliza a `Auto/Moto/Camioneta`.

**Recomendación**: normalizar en producción (UPDATE con `tipo = INITCAP(LOWER(tipo))`) o normalizar en el modelo/service al leer/escribir.

### H2 — `parking_cameras.sucursal` con prefijo `'AUTOPASS '` (12 de 22)  ⚠️ ALTO

`parking_branches.nombre` = `'Castelar'` (sin prefijo) pero 12 cámaras tienen `sucursal = 'AUTOPASS Castelar'`, `'AUTOPASS Morón'`, `'AUTOPASS Ituzaingó'` (y 1 con `'AUTOPASS Ituzaingo'` sin tilde).

**Impacto**: el código filtra con igualdad exacta:
- `routes/system/cameras.py:160-161` (`c.sucursal == staff.sucursal`) → staff local no ve sus cámaras (solo el admin global ve todas).
- `routes/system/health.py:35` (misma comparación) → health check cae al fallback por nombre.
- `routes/system/cameras.py:207` (`camera.sucursal != staff.sucursal` → 403) → staff local **no puede editar** sus propias cámaras.
- `branch_repository.propagate_rename` renombra solo coincidencia exacta → el prefijo queda huérfano al renombrar.

`support_tickets.sucursal` tiene el mismo prefijo (3 tickets) pero **no es bug**: `support_service` filtra con `normalize_branch_name` (quita prefijo/tildes).

**Recomendación**: `UPDATE parking_cameras SET sucursal = btrim(regexp_replace(sucursal, '^AUTOPASS ', '', 'i'))` y corregir la tilde de Ituzaingó.

### H3 — Santos Dumont 686 incompleta  ⚠️ ALTO

- **Sin fila en `parking_aforo`** → al primer ingreso `access_service._get_or_create_aforo` la crea con defaults 20 auto / 10 moto / 5 camioneta (ignora cualquier aforo configurado desde el panel antes de existir).
- **Faltan las 5 tarifas de camioneta** (`precio_hora_camioneta`, `precio_30min_camioneta`, `precio_dia_camioneta`, `precio_semana_camioneta`, `precio_mes_camioneta`) → con el fix de tarifas estricto, **una camioneta en Santos Dumont arroja 409** (no puede pagar). Las de auto y moto sí están.
- Es la única sucursal del seed de producción que sí figura en `scripts/generate_demo_traffic.py` con peso 0.9.

**Recomendación**: cargar aforo propio + tarifas de camioneta (o copiarlas de otra sede).

### H4 — Central sin ningún setting (0 tarifas por sucursal)

`setting.sucursal IS NOT NULL`: Castelar 19, Ituzaingó 15, Morón 15, Santos Dumont 10, **Central 0**.

Con el fix de tarifas estricto, **Central no puede cobrar nada** (todos los cobros/reservas → 409). Es la situación ya conocida/aceptada, pero queda documentado como **dato faltante** en producción: si Central debe operar, hay que cargar su tarifario.

### H5 — `users.dni` con formato mixto  ⚠️ MEDIO

- 342 usuarios con formato con puntos (`23.456.778` — formato estándar vía `normalize_dni`).
- 44 usuarios con DNI sin puntos (solo dígitos) — ej.: admins `00000001`, users `11232444`.
- 30 usuarios eliminados con `dni = 'eliminado-N'` (placeholder de soft-delete).

**Impacto**: `UserRepository.get_active_by_dni` usa comparación exacta (`==`); `oauth_service` y `user_service` normalizan con `normalize_dni` (puntos) antes de buscar. Un usuario cuyo DNI se guardó sin puntos no matcheará con el formato con puntos → riesgo de **duplicados en alta social/edición** (hoy 0 duplicados, pero la colisión es posible). No hay duplicados actuales verificando sin puntos.

**Recomendación**: `UPDATE users SET dni = normalize_dni en SQL` (o normalizar en lectura) para unificar formato de los 44.

### H6 — Datos huérfanos / incompletos  ⚠️ MEDIO

| hallazgo | cantidad | detalle |
|---|---|---|
| reservations sin `user_id` | 2 | ids 79 (`Pagado`, 3.000) y 84 (`Reembolsado`, 6.000), `origen='manual'`, `cliente_nombre=''` → dinero sin dueño |
| reservations `'Pagado'` sin `fecha_pago` | 62 | repartidas en las 5 sedes |
| access_logs sin `sucursal` | 90 | ids 674-763, ENTRADA+SALIDA, sin branch → excluidos de reportes por sucursal |
| access_logs sin `normalized_patente` | 2 | ids 3 y 4 (primeros ALPR reales) |
| access_logs pagados con `costo_estadia` 0/NULL | 211 | Castelar 92, Ituzaingó 73, Morón 46 → recaudación en 0 |
| `mercadopago_payments` PENDIENTE sin `mp_status` | 25 | desde 2026-09-01 (5 x 30.000 del user 6, 3 del 305, 6 del 5) |

## MENORES / OK

- **Duplicados**: emails 0 • DNI (sin puntos) 0 • patentes vehicles 0 • patentes users 0 • `settings(clave,sucursal)` 0 • branches normalizados 0 • aforo 0 • tickets 0 • MP payment_id 0.
- **`user_sessions`**: 1 tupla repetida (user 1, device `'bench'`, ×7) — chatarra de login de benchmarking.
- **`parking_cameras.source` duplicada**: 4 URLs compartidas por varias cámaras (la IP `192.168.1.33` la usan 10) — posible configuración de prueba/duplicada sin limpiar.
- **Promotions tipo `voucher` sin `valor_descuento`**: 4 (Día Libre, Lavado Premium, LAVADO, Café Martínez) — no es bug: el código solo persiste `valor_descuento` cuando `tipo_canje == 'descuento_reserva'`.
- **`reservations.sucursal_info`**: es texto libre (dirección/descripción), no debe matchear contra `parking_branches`. OK.
- **Patentes con espacios** (`AA 110 RR`): formato de visualización estándar (`format_plate`); `normalized_patente` guarda sin espacios. Correcto.
- **`tipo_vehiculo` en reservations `'AUTO'`: en disponibilidad se normaliza con `.strip().title()` → no rompe reservas. El problema es solo facturación/reportes (H1).**
- **Aforo/ocupación**: sin sobre-límites. Solo Castelar tiene ocupación real (3 autos). Capacidades reservas por sucursal cargadas (Central/Ituzaingó/Morón 5-3-2, Castelar 10-5-5).
- **`parking_floors` vacía**: 0 pisos cargados; todas las capacidades vienen de `parking_aforo`. Consistente con el diseño (escritorio).

## RECOMENDACIONES PRIORIZADAS

1. **(H1) Normalizar tipos de vehículo** a mayúscula `'AUTO'/'MOTO'/'CAMIONETA'` o a `Title Case` en toda la BD y **endurecer el servicio**: `billing_service.get_rate/get_hourly_rate/get_30min_rate` deben normalizar el input (`tipo.title()` o `tipo.upper()` + match por set).
2. **(H2) `UPDATE parking_cameras`** quitando prefijo `AUTOPASS ` y corrigiendo tilde.
3. **(H3) Cargar aforo + tarifas de camioneta** de Santos Dumont.
4. **(H4) Cargar tarifario de Central** si debe operar.
5. **(H5) Unificar formato de DNI** de los 44 usuarios sin puntos.
6. **(H6)** revisar/liquidar: reservas huérfanas, 62 pagadas sin `fecha_pago`, 211 logs costo 0, 25 MP pendientes viejos.

## SCRIPTS USADOS

Auditoría read-only vía SQLAlchemy sobre `parking_aforo`/`parking_branches`/etc. No se modificó ningún dato.