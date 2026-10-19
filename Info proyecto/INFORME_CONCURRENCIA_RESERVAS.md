# INFORME DE CONCURRENCIA TRANSACCIONAL — RESERVAS, PAGOS Y SALDO

**Fecha:** 2026-09-29
**Alcance:** backend FastAPI + ALPR + worker de fondo
**Estado:** informe y plan propuesto. **NINGÚN cambio de código aplicado todavía.**
**Severidad global:** ALTA (afecta dinero y disponibilidad de plazas)

---

## 1. Resumen ejecutivo

El sistema **no implementa ningún mecanismo de bloqueo transaccional** en el flujo de
reservas, pagos ni saldo. Todas las decisiones críticas se toman con un patrón
**check-then-act** (leer estado → validar → escribir) sobre transacciones independientes,
sin `SELECT ... FOR UPDATE`, sin advisory locks, sin nivel de aislamiento reforzado y sin
constraints de base de datos que respalden las invariantes.

Bajo concurrencia, que es el estado normal de producción, esto produce:

| # | Defecto | Impacto |
|---|---------|---------|
| R1 | Sobreventa de aforo | Más reservas que plazas físicas |
| R2 | Doble reserva de la misma patente | Dos reservas para un mismo vehículo y rango |
| R3 | Doble pago / doble acreditación | Doble débito de saldo, doble acreditación de puntos, doble reembolso |
| R4 | Cache de disponibilidad desactualizada | El usuario ve horarios que ya se ocuparon |
| R5 | El worker compite con las requests | Transiciones de estado perdidas o inconsistentes |

**R3 es el más grave**: el movimiento de dinero no es idempotente y tampoco lo es el webhook
de Mercado Pago, que por diseño reintenta.

---

## 2. Diagnóstico: por qué no hay bloqueo

### 2.1 Ausencia de primitivas de bloqueo

Búsqueda exhaustiva sobre `core/`, `routes/`, `services/`, `repositories/`, `models/`, `alpr/`:

```
with_for_update | FOR UPDATE | pg_advisory_lock | advisory_lock |
LOCK TABLE | nowait | skip_locked | isolation_level | SERIALIZABLE | REPEATABLE
```

**Resultado: cero coincidencias.** Los dos únicos hits fueron `queue.get_nowait()` del
procesador de frames del ALPR, falso positivo por el sufijo `nowait`.

El nivel de aislamiento es, por tanto, el **default de PostgreSQL: READ COMMITTED**, que no
ofrece ninguna garantía frente a check-then-act.

### 2.2 La concurrencia es real, no teórica

- `scripts/run_server.ps1` lanza `uvicorn main:app` **con un solo worker**.
- Aun así, **140 de 165 endpoints son `def` (síncronos)** frente a solo 25 `async def`.
  FastAPI ejecuta los endpoints síncronos en el threadpool de **anyio (40 hilos por default)**.
- `core/database.py:31` configura el pool de Postgres con `pool_size=20, max_overflow=40`,
  es decir **hasta 60 conexiones concurrentes** a la base.
- `services/worker_service.py:25,32` levanta **2 hilos daemon** que escriben estado de
  reservas en background, sin lock.

Las transacciones de dos requests se entrelazan libremente **dentro del mismo proceso**, y
compiten con 2 hilos más de background.

### 2.3 Ninguna red de seguridad en la base

`models/reservation.py` solo declara índices **no únicos** (`user_id`, `patente`,
`sucursal_nombre`). El único `unique` es `codigo`, que es otro campo.

**No existe:**

- Constraint de exclusión por solapamiento de rangos temporales.
- Constraint de unicidad parcial sobre (patente, sucursal, rango) para reservas vigentes.
- Constraint que limite la cantidad de reservas al aforo disponible.

Además, **no hay manejo de `IntegrityError` en ningún punto del proyecto** (verificado sobre
`services/`, `routes/`, `repositories/`, `core/`). Aunque existiera un constraint, la
violación aflora como HTTP 500, sin rollback limpio ni mensaje útil.

### 2.4 No hay tests de concurrencia

Toda la suite de reservas (`test_reservation_service.py`, `test_reservation_spots.py`,
`test_reservation_availability_logic.py`, `test_payments.py`) es **secuencial y mono-hilo**.
Además los tests usan `sqlite://` con `StaticPool` + `check_same_thread=False`, lo que impide
reproducir concurrencia real.

**Por eso pasan 707 tests y el defecto sigue ahí: nadie lo estaba midiendo.**

---

## 3. Las carreras, en detalle

### R1 — Sobreventa de aforo (CRÍTICO)

`services/reservation_service.py`, método `create_user_reservation`:

| Línea | Acción |
|-------|--------|
| 232 | `get_overlap_by_patente(...)` — lectura sin lock |
| 235 | `BillingService.get_rate(...)` — lectura |
| **246** | `disp = verificar_disponibilidad(...)` — **la decisión** |
| 247-248 | `if not disp["disponible"]: raise` |
| ... | ~40 líneas de cálculos de monto |
| 285 | `db.add(new_res)` |
| **286** | `db.commit()` — **la escritura** |

`services/availability.py:119-152` (`verificar_disponibilidad`) lee la capacidad, calcula la
ocupación con sweep-line y decide:

```python
# availability.py:144
disponible = ocupada < capacidad_reservas
```

**Escenario de fallo:** quedan 2 plazas. Dos usuarios presionan "Reservar" en el mismo
instante. Ambos leen `ocupada=4, capacidad=6` → `restan=2` → ambos pasan el check → ambos
insertan. Resultado: `ocupada=6` sobre una capacidad efectiva de 5.

**Agravante:** la lectura de la línea 246 ocurre ~40 líneas antes del commit. El thread queda
libre para el otro request durante todo ese intervalo.

### R2 — Doble reserva de la misma patente (CRÍTICO)

Mismo patrón entre la línea 232 y la 285. `get_overlap_by_patente` no bloquea; entre su
retorno y el `commit`, un segundo request con la misma patente y rango pasa el filtro y
también inserta.

Escenario de fallo trivial: doble clic en el botón, o dos pestañas abiertas.

### R3 — Doble pago y doble acreditación (CRÍTICO, dinero)

**Guarda no atómica.** `services/payments.py:42`:

```python
if res.estado_pago == PaymentStatus.PAGADO:
    return {"status": "ok", "message": "La reserva ya se encuentra pagada", ...}
```

Es un **read-then-write**: lee el estado, decide, y recién después escribe. Dos requests
concurrentes leen ambos `PENDIENTE` y ambos continúan.

**Consecuencias, todas por read-modify-write sobre el objeto ORM:**

| Ubicación | Operación | Daño con doble ejecución |
|-----------|-----------|--------------------------|
| `payments.py:68` | `res.user.puntos_acumulados += puntos_ganados` | Puntos acreditados dos veces |
| `payments.py:139` | `user.saldo -= monto_a_cobrar` | **Saldo debitado dos veces** |
| `payments.py:151` | `user.puntos_acumulados += puntos_ganados` | Doble acreditación |
| `payments.py:239` | `user.puntos_acumulados += puntos_ganados` | Doble acreditación |
| `payments.py:354` | `target_user.saldo += monto_a_reembolsar` | **Reembolso duplicado** |
| `user_repository.py:87` | `user.saldo += amount` | Saldo inflado |
| `user_repository.py:93` | `user.puntos_acumulados += points` | Puntos inflados |
| `billing_service.py:157,165,224,269` | `puntos_acumulados += puntos_ganados` | Doble acreditación |

**Mercado Pago agrava el caso:** el webhook reintenta por diseño.
`services/mercadopago_service.py:111` repite la misma guarda no atómica, y la línea 222
devuelve `"Pago ya confirmado"`, pero si el reintento de MP entra mientras la transacción
original sigue abierta (antes del commit), ambos pasan la guarda.
`routes/user/mercadopago.py:25` (`_procesar_retorno`) abre su propia `SessionLocal()`, o sea
una transacción independiente de la original.

**Nota sobre `+=` en SQLAlchemy:** el ORM calcula el delta desde el valor cargado en memoria.
Con dos sesiones cargando el mismo `User`, la segunda escritura **pisa** a la primera
(lost update) o duplica el incremento según el orden de flush. Ninguna de las dos variantes
es la correcta.

### R4 — Cache de disponibilidad (MEDIO)

`services/availability.py:16-17`:

```python
_CACHE_AVAILABILITY = {}
_CACHE_AVAILABILITY_TTL_SECONDS = 30
```

El cache se usa en `obtener_fechas_deshabilitadas` (línea 178) y
`obtener_horas_deshabilitadas` (línea 249). **Correctamente NO se usa en
`verificar_disponibilidad`**, lo que evita el peor caso.

Pero el selector de horario que ve el usuario se alimenta del cache: puede ofrecer durante
30s un horario que acaba de llenarse. No hay invalidación al crear o cancelar una reserva.

**Advertencia:** el cache es **por proceso**. Con más de un worker de uvicorn dejaría de ser
consistente.

### R5 — Carrera entre worker y requests (MEDIO)

`services/worker_service.py` mueve `estado_reserva` a `ACTIVA` (línea 175) y a `CANCELADA`
(226) + `estado_pago = FALLIDO` (226) desde hilos daemon, sin lock.

Escenario: el worker decide auto-cancelar una reserva por falta de pago mientras el usuario
cierra el pago. Sin serialización, gana el último en escribir, y puede dejar la reserva
`PAGADA` con notificaciones ya disparadas para un estado que ya no existe, o viceversa.

---

## 4. Lo que NO es un problema (verificado)

- Las reservas no horarias nunca pre-ocupaban plaza física: los helpers
  `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` eran `pass` y se
  eliminaron en v9.34.55 (con sus 5 call sites). La ocupación física la maneja
  exclusivamente el ALPR. No hay doble reserva de plaza física por esta vía.
- `alpr/alpr_service.py` **ya no existe**; el proceso ALPR fue absorbido. El filtro de limpieza
  de `run_server.ps1:33` que lo menciona está obsoleto, pero no afecta a este análisis.

---

## 5. Restricción de diseño que condiciona la solución

`core/database.py:19-22` soporta **tres backends**:

| Backend | Dónde se usa | `pg_advisory_xact_lock` | `SELECT FOR UPDATE` | `EXCLUDE USING gist` |
|---------|--------------|-------------------------|--------------------|----------------------|
| **PostgreSQL** (Neon) | **Producción** (`.env`) | Sí | Sí | Sí (requiere `btree_gist`) |
| SQLite | Dev y tests | No | No | No |
| SQLite | Fallback configurado | No | No | No |

**Implicación:** la solución **no puede ser un único `pg_advisory_lock` a secas**. Debe ser un
helper con bifurcación por dialecto, y el tier de constraints solo aplica a Postgres.

**Salvedad específica de Neon serverless:** con pooler de conexiones en modo *transaction
pooling* los locks **a nivel de sesión** (`pg_advisory_lock`) se filtran, porque la sesión
física se reutiliza. Solo es seguro el variante **a nivel de transacción**
(`pg_advisory_xact_lock`), que se libera automáticamente en el commit o rollback. El plan usa
exclusivamente el variante transaccional.

---

## 6. Plan de solución

### Principio de diseño (AGENTS.md: DRY y escalable)

**Un único helper de bloqueo en `core/`, reutilizado por todos los puntos de entrada.**
Ninguna ruta, servicio o repositorio implementa su propio lock. El helper encapsula la
bifurcación por dialecto y expone claves canónicas, de modo que agregar un nuevo punto de
escritura sea agregar una línea, no repetir lógica.

### Fase 0 — Test de reproducción (RED)

> **Estado (19/10/2026): R3 IMPLEMENTADA; R1/R2 pendientes.** Los tests de R3
> (`tests/test_concurrencia_saldo_puntos.py`, SQLite de archivo con WAL y `busy_timeout`)
> están escritos y verificados en **RED** contra `95aca58` (3 fallos deterministas); quedan
> en verde con la Fase 1. Los de R1/R2 se escriben junto con la Fase 3: hasta que la cache
> de disponibilidad no se invalide, fallan (y son la prueba de ese arreglo).

Antes de tocar producción, tests que **demuestren** que las carreras existen. Sin esto, el fix
no es verificable y puede revertirse en silencio.

- `tests/test_concurrencia_reservas.py`
  - R1: N hilos con barrera de sincronización invocando `create_user_reservation` sobre la
    última plaza → debe fallar hoy.
  - R2: dos hilos con la misma patente y rango.
  - R3: dos hilos invocando el mismo `pay` → debe acreditar puntos dos veces hoy.
- Requiere SQLite sobre **archivo** (no `:memory:` con `StaticPool`, que no permite
  concurrencia real) o un Postgres de test. **Verificar factibilidad antes de escribir.**

**Criterio de salida:** los tests fallan de forma determinista contra el código actual.

### Fase 1 — Aritmética atómica de saldo y puntos (dinero, riesgo bajo)

> **Estado (19/10/2026): IMPLEMENTADA** en `960e3a9` (código) y `a9f3a5e` (tests). Los
> helpers viven en `repositories/user_repository.py` (6 sentencias `UPDATE ... RETURNING` +
> 6 métodos) y los 20 puntos de escritura de 6 archivos ya los usan: no quedan `+=`/`-=`
> sobre saldo/puntos en procesos de negocio.

Elimina los read-modify-write con una operación atómica de SQL, sin depender de locks. Es la
capa con mejor relación esfuerzo/beneficio y ataca el daño monetario directo.

- `repositories/user_repository.py:87,93`: reemplazar `user.saldo += amount` por
  `UPDATE users SET saldo = saldo + :amount WHERE id = :id` con `RETURNING`. Idem para
  `puntos_acumulados`.
- `services/payments.py:139`: `user.saldo -= monto_a_cobrar` → operación atómica con
  validación de saldo suficiente en la misma sentencia:
  `UPDATE users SET saldo = saldo - :monto WHERE id = :id AND saldo >= :monto RETURNING saldo`.
  Cero filas afectadas = saldo insuficiente.
- `services/payments.py:354`: reembolso con la misma operación atómica.
- `billing_service.py:157,165,224,269`: ídem para `puntos_acumulados`.

**Criterio de salida:** los `+=`/`-=` sobre saldo y puntos desaparecen del código de los
procesos de negocio. Los tests de Fase 0 de R3 pasan.

### Fase 2 — Helper único de bloqueo transaccional (núcleo de la solución)

> **Estado (19/10/2026): IMPLEMENTADA** en `c408507` (código). `core/db_lock.py` con
> `bloqueo_transaccional` y `refrescar`, timeout
> configurable (`LOCK_TIMEOUT_SECONDS`) y handler HTTP 409; aplicado en los 6 puntos de
> entrada críticos.

Nuevo módulo `core/db_lock.py`:

```python
@contextmanager
def bloqueo_transaccional(db: Session, *claves: str) -> Iterator[None]:
    """Serializa secciones críticas que abarcan varias lecturas y escrituras.

    Postgres: pg_advisory_xact_lock, liberado en commit/rollback (seguro con
    transaction pooling de Neon). SQLite: no-op, ver nota de limitaciones.
    """
```

Contrato:

- Las claves se derivan con `hashtextextended` en Postgres para obtener un `bigint` estable.
- El lock es **a nivel de transacción**: no hace falta liberarlo a mano, se libera solo.
- Se aplica sobre la sesión que el request ya tiene abierta, por lo que **no altera los
  límites de transacción existentes** ni requiere refactor de commits.
- Timeout configurable vía `settings` (por defecto 10s). Al expirar lanza `LockTimeoutError`,
  que la capa de rutas traduce a HTTP 409 con mensaje "la operación se completó en otro
  proceso, reintentá".
- En dialectos sin soporte hace `yield` sin nada, dejando un `logger.debug` una sola vez por
  proceso para que la limitación sea visible sin spamear el log.

Claves canónicas (helpers delgados sobre `bloqueo_transaccional`):

| Clave | Protege |
|-------|---------|
| `aforo:{sucursal}:{tipo_vehiculo}` | R1 — capacidad de reservas del tipo en la sede |
| `patente:{patente}:{sucursal}` | R2 — solapamiento de una misma patente en una sede |
| `usuario:{user_id}` | R3 — saldo y puntos |
| `reserva:{res_id}` | R3, R5 — transiciones de estado de una reserva |

Puntos de entrada a modificar (todos usan el mismo helper, ninguno implementa lógica propia):

1. `services/reservation_service.py` → `create_user_reservation` (~línea 232)
2. `services/reservation_service.py` → `modify_user_reservation` (~línea 303)
3. `services/reservation_service.py` → cancelación
4. `services/payments.py` → los 3 caminos de pago (manual admin, saldo, Mercado Pago)
5. `services/mercadopago_service.py` → `confirm_payment`
6. `services/worker_service.py` → `_reservation_cleanup_worker`

**Regla crítica:** dentro de la sección crítica hay que **re-ejecutar la validación**, no
reusar el valor leído antes del lock. En `create_user_reservation` hoy se lee en 232 y 246 y
se decide en 247; con el lock adquirido en 232 esas lecturas ya son consistentes, pero si el
lock se adquiriera más tarde habría que repetir `verificar_disponibilidad` dentro.

**Criterio de salida:** los tests de Fase 0 de R1 y R2 pasan de forma determinista.

### Fase 3 — Invalidación del cache de disponibilidad

- `services/availability.py`: helper `invalidar_cache_disponibilidad(sucursal=None)`.
- Invocar desde `create_user_reservation`, `modify_user_reservation` y la cancelación,
  **después** del `commit`. Invalidar antes no sirve: la transacción podría hacer rollback.
- Nota explícita en el código de que el cache es por proceso, y de que con más de un worker
  habría que moverlo a Redis o a invalidación por versión en BD.

**Criterio de salida:** tras una reserva, el selector de horas ya no ofrece el rango ocupado.

### Fase 4 — Constraints de BD (red de seguridad, Postgres)

Última línea de defensa. No reemplaza el lock: lo hace redundante en los casos que cubre.

- Migración Alembic nueva, **solo Postgres**:
  - Extensión `btree_gist`.
  - Columna `patente_norm` mantenida para poder indexar por patente normalizada, que es como
    hoy filtra `get_overlap_by_patente`.
  - `EXCLUDE USING gist (patente_norm WITH =, sucursal_nombre WITH =, tsrange(fecha_inicio, fecha_fin) WITH &&) WHERE (estado_reserva IN ('PENDIENTE','ACTIVA') AND estado_pago IN ('PENDIENTE','PAGADO'))`
  - Esto cierra **R2 por completo a nivel de motor**, sin depender de la lógica de aplicación.
- **R1 no se puede expresar como constraint**: "no más de N reservas solapadas" no es
  declarable en SQL estándar. Sigue dependiendo del lock `aforo:`.
- `models/reservation.py`: declarar el constraint en el modelo para que `create_all` lo vea.
- En SQLite el constraint no se crea y el guard de aplicación queda como única defensa.
  Documentarlo explícitamente.

**Criterio de salida:** un `INSERT` manual que solape una patente vigente falla con
`IntegrityError` aunque se esquive el servicio.

### Fase 5 — Idempotencia de pagos y manejo de errores

- `IntegrityError` → HTTP 409 con mensaje de negocio, con `db.rollback()` limpio. Envolver las
  mutaciones de los puntos 1-6 de la Fase 2.
- **Clave de idempotencia del webhook:** `MercadoPagoPayment` ya persiste el `payment_id` de MP.
  Agregar `unique=True` sobre ese campo (o un `idempotency_key` dedicado). Un reintento de MP
  con el mismo `payment_id` debe detectar el conflicto y devolver el resultado ya aplicado en
  vez de reprocesar. Es la defensa específica contra el comportamiento de reintento de MP.
- Mover la guarda `if res.estado_pago == PAGADO` **dentro** de la sección crítica del lock,
  para que deje de ser un read-then-write.

**Criterio de salida:** dos entregas del mismo webhook producen un solo cobro y una sola
acreditación de puntos.

### Fase 6 — Hardening y cierre

- `tests/test_concurrencia_reservas.py` pasa de forma determinista y queda en CI.
- Suite completa sin regresiones (baseline actual: **707 passed**).
- `check_consistencia_frontend` y `check_css_huerfano` siguen en verde.
- Documentar en `Info proyecto/GUIA_DESARROLLO.md` el contrato de `bloqueo_transaccional` y la
  regla: **toda escritura que dependa de un `SELECT` anterior debe abrir sección crítica**.

---

## 7. Orden de ejecución y dependencias

```
Fase 0  tests de reproducción (RED)           <- sin cambios de producción
   |
Fase 1  aritmética atómica saldo/puntos       <- riesgo bajo, ataca el dinero
   |
Fase 2  helper de bloqueo + 6 puntos entrada <- núcleo, cierra R1 y R2
   |
Fase 3  invalidación de cache                 <- depende de 2
   |
Fase 4  constraints de BD (Alembic)           <- ventana de mantenimiento
   |
Fase 5  idempotencia de pagos + 409          <- depende de 1 y 2
   |
Fase 6  hardening, docs, cierre
```

La Fase 1 puede arrancar en paralelo con la Fase 0 porque no depende del lock.
Las Fases 2, 3 y 5 deben ir juntas: aplicar el lock sin idempotencia deja R3 a medias, y
aplicar idempotencia sin lock no serializa las transiciones de estado.

---

## 8. Esfuerzo estimado y riesgo

| Fase | Esfuerzo | Riesgo | Reversible |
|------|----------|--------|------------|
| 0 | Bajo | Nulo | Sí |
| 1 | Medio | Bajo | Sí |
| 2 | Medio | Medio | Sí |
| 3 | Bajo | Bajo | Sí |
| 4 | Alto | **Alto** (migración de esquema) | **No sin rollback** |
| 5 | Medio | Medio | Parcial |
| 6 | Bajo | Bajo | Sí |

**Recomendación:** ejecutar las Fases 0-3 y 5 de inmediato. La Fase 4 requiere ventana de
mantenimiento y validación previa contra una copia de la base, porque la migración es la
única parte del plan que no se revierte con un simple revert de git.

---

## 9. Preguntas abiertas antes de implementar

1. **Alcance de la Fase 4:** ¿el equipo acepta una migración de esquema con ventana de
   mantenimiento, o el constraint de exclusión queda para una iteración posterior?
2. **Timeout del lock:** 10s puede ser poco con 60 conexiones y picos de carga. Si un lock no
   se consigue a tiempo, ¿se responde 409 "reintentá" o se espera más?
3. **Cache con varios workers:** si se va a escalar `uvicorn` a más de un worker, el cache de
   disponibilidad en memoria deja de ser válido y hay que decidir entre Redis e invalidación
   por versión en BD. Hoy no es un problema porque hay 1 worker.
4. **Regla de solapamiento por patente:** el constraint propuesto permite varias reservas no
   solapadas para la misma patente, que es el comportamiento actual de
   `get_overlap_by_patente`. Confirmar que esa es la regla de negocio deseada, y no que la
   patente deba tener como máximo una reserva vigente en toda la sede.
