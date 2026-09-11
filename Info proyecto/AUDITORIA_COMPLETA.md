# Auditoría Técnica Integral — AUTOPASS Professional

**Plataforma:** Sistema de gestión de estacionamientos (parking)
**Stack:** Python 3.13 / FastAPI 0.135 / SQLAlchemy 2.0 / PostgreSQL (Neon) / HTMX+JS SPA
**Métricas globales:** 243 archivos, ~39.000 líneas de código (9.045 Python, 10.798 JS, 9.227 HTML, 9.828 CSS), 48 dependencias, 101 endpoints, 17 tablas, 14 módulos de servicio, 15 archivos de test.
**Fecha de auditoría:** Septiembre 2026

> **Actualización (2026-09-11):** Auditoría histórica (snapshot). Varios hallazgos fueron abordados desde entonces: caché TTL en memoria (`core/cache.py`, `SimpleTTLCache`, v9.14.0), índices de performance en `access_logs`/`reservations`/`support_ticket_messages`/`vehicles`/`redemption_tickets` (migración `49a240f0fc25`), nuevas migraciones Alembic `a4c8d2e3f5b6` (`tipo_vehiculo` en `Reservation`) y `d3b7e1a9c2f0` (`metodo_pago` en `Reservation`), purga automática de imágenes ALPR (`ALPR_IMAGE_RETENTION_DAYS`, default 30 días), suite de tests ampliada a **82 pruebas passing en 21 archivos** (incl. `test_oauth.py`, `test_admin_reservations.py`, `test_mercadopago.py`), rate limiting SlowAPI (v9.12.0+) y limpieza de dependencias muertas en `requirements.txt`. Los hallazgos de seguridad críticos pendientes deben tratarse según el plan original.

---

## Tabla de contenidos

1. [Capacidad para soportar tráfico](#1-capacidad-para-soportar-tráfico)
2. [Coherencia entre módulos](#2-coherencia-entre-módulos)
3. [Preparación para una aplicación que vivirá varios años](#3-preparación-para-una-aplicación-que-vivirá-varios-años)
4. [Análisis de arquitectura](#4-análisis-de-arquitectura)
5. [Análisis del lenguaje utilizado](#5-análisis-del-lenguaje-utilizado)
6. [Análisis de costos y consumo de recursos](#6-análisis-de-costos-y-consumo-de-recursos)
7. [Revisión del código generado por IA](#7-revisión-del-código-generado-por-ia)
8. [Revisión de logs y manejo de información](#8-revisión-de-logs-y-manejo-de-información)
9. [Auditoría de seguridad](#9-auditoría-de-seguridad)
10. [¿Es necesario incorporar otro lenguaje?](#10-es-necesario-incorporar-otro-lenguaje)
11. [Conclusión general](#11-conclusión-general)

---

## 1. Capacidad para soportar tráfico

### 1.1 Funcionamiento con pocos usuarios simultáneos

Con 1–10 usuarios simultáneos, la aplicación funciona correctamente. Los endpoints principales (listado de vehículos, creación de reservas, dashboard de admin) responden en milisegundos. La base de datos Neon tiene un pool pequeño pero suficiente para este nivel. Los workers en background (limpieza de reservas, recordatorios) no impactan perceptiblemente.

### 1.2 Funcionamiento con muchos usuarios simultáneos

**Problemas identificados:**

- **Engine sincrónico en app async:** `core/database.py:31` crea un `create_engine` síncrono. Todos los endpoints de FastAPI son `def` (síncronos), lo que bloquea threads del pool de Uvicorn. Con múltiples usuarios concurrentes, los threads se agotan y las respuestas se encolan.
- **Pool de conexiones limitado:** `pool_size=10, max_overflow=20` (máximo 30 conexiones). Con 50+ usuarios concurrentes haciendo consultas a la BD, se alcanza el límite.
- **WebSocket broadcast serial:** `routes/parking/status.py:61-70` — cada evento de ocupación ejecuta una query SQL **por cada conexión WebSocket**, serialmente. Con 20 dashboards abiertos, un evento dispara 20 queries secuenciales.
- **Sin caché de ningún tipo:** No hay Redis, ni caché en memoria, ni response caching. Cada request recalcula todo desde cero.

### 1.3 Horarios de mayor utilización

Un parking típico tiene picos a la mañana (8-10hs) y noche (18-22hs). El endpoint `/v1/access/validate-plate` es el más crítico: cada entrada de vehículo ejecuta:
1. Query a `access_logs` (buscar estancia activa)
2. Query a `vehicles` (buscar propietario)
3. Query a `reservations` (verificar reserva)
4. Query a `settings` (obtener tarifa)
5. Query a `parking_aforo` (verificar capacidad)

Todas estas son **full table scans** (ver §1.6). Con 10 entradas simultáneas, 50+ queries secuenciales se ejecutan.

### 1.4 Días de alta demanda

Días festivos o eventos especiales podrían multiplicar el tráfico por 3-5x. Los problemas de fondo (queries sin índices, workers con full scans) se amplifican proporcionalmente. El endpoint de reservas ejecuta `verificar_disponibilidad` que hace un `full scan` de todas las reservas de la sucursal (`services/reservation_service.py:43`).

### 1.5 Fines de semana / concentración de tráfico

El worker de notificaciones (`services/worker_service.py`) ejecuta cada 30 segundos un ciclo completo que incluye 3 pasadas de full-scan sobre `reservations`:
- `_process_reminders` (línea 96): N+1 queries por reserva
- `_process_started_reservations`: full scan
- `_process_auto_cancellations`: full scan + N+1 queries por reserva

En fin de semana con muchas reservas activas, el worker consume CPU/IO significativa.

### 1.6 Operaciones que pueden convertirse en cuellos de botella

| Operación | Cuello de botella | Ubicación |
|---|---|---|
| **Lookup de placa (ALPR)** | `func.replace(func.upper(patente),' ','')` en cada query — deshabilita índices, full scan | `access_service.py:80,90`, `operations.py:41,126,196,264` |
| **Broadcast de ocupación** | 1 query SQL por conexión WebSocket, serial | `status.py:61-70` |
| **Reportes** | `LIKE '%...%'` + `union_all` con sort + offset | `report_service.py:58,87,110,135+` |
| **Workers background** | 3 full scans de `reservations` cada 30s + sync SMTP | `worker_service.py:96-232` |
| **Estancia activa del usuario** | 3N+1 queries para N vehículos | `balance.py:17-25` |
| **Tickets admin** | N+1 messages + M×N+1 user loads | `support_service.py:126-129` |

### 1.7 Consultas a la base de datos que pueden ser costosas

**Top 5 consultas más costosas (por frecuencia × complejidad):**

1. **`get_rate` / `get_hourly_rate`** — se ejecuta en CADA entrada, CADA salida, CADA cálculo de deuda. Hace scan sobre `settings` sin índice compuesto `(clave, sucursal)`. (`billing_service.py:33-43,56-66`)

2. **`verificar_disponibilidad`** — full scan de reservas por sucursal + rango de fechas, sin índices en `sucursal_nombre`, `fecha_inicio`, `fecha_fin`. (`reservation_service.py:43`)

3. **`_get_global_status`** — broadcast WebSocket que carga todas las sucursales + aforos + lazy-load de pisos. (`status.py:86-104`)

4. **Reportes financieros** — `LIKE '%sucursal%'` + `LIKE '%patente%'` + `union_all` de access_logs + reservations + sort in-memory. (`report_service.py:58-341`)

5. **Worker de notificaciones** — 3 full scans de reservations + N queries de notificaciones por reserva. (`worker_service.py:96-232`)

### 1.8 Procesos que consumen demasiada memoria o CPU

- **ALPR (reconocimiento de patentes):** Cada cámara ejecuta un subprocess con `rapidocr-onnxruntime` + `paddleocr`. Cada instancia carga modelos de ~200-500 MB en RAM. Con 4 cámaras = ~2 GB solo para OCR.
- **OpenCV (`cv2`):** Se carga `opencv-python` completo (no headless). Cada frame de video se procesa en memoria.
- **Workers con full scans:** `_notification_worker` carga todas las reservas pendientes en memoria, itera, y hace queries individuales.

### 1.9 Carga de imágenes, archivos u otros recursos pesados

- **Imágenes de cámaras (captura de patentes):** Se guardan en `captured_images/` sin rotación ni limpieza automática. Cada evento ALPR genera un JPG.
- **Archivos de soporte:** Se guardan en `static/uploads/support/` sin límite de cantidad (solo 1 MB por archivo). Sin rotación ni limpieza.
- **Logos de sucursales:** Se guardan en `static/uploads/branches/` sin compresión.
- **FastAPI sirve todo estático directamente** (`StaticFiles` en `main.py:38-39`) — sin CDN, sin compresión gzip, sin caching headers.

### 1.10 Cantidad de conexiones a la base de datos

- Pool máximo: 10 (base) + 20 (overflow) = **30 conexiones simultáneas**
- Workers en background: 2 threads que abren sesiones independientes
- WebSocket broadcast: cada conexión puede disparar queries
- MQTT: mantiene 1 conexión persistente (no usa el pool)
- ALPR subprocesses: cada uno tiene su propia conexión

**Total potencial:** 30 del pool + 2 workers + N subprocesses ALPR. Con 4 cámaras = 36 conexiones. Neon free tier: 1-20 conexiones según plan. **Riesgo de agotar conexiones.**

### 1.11 Posibilidad de utilizar caché cuando corresponda

**No existe ningún mecanismo de caché en toda la aplicación.** Oportunidades claras:

| Dato | Frecuencia de cambio | Candidato a caché |
|---|---|---|
| Tarifas (`settings`) | Casi estática | TTL 5 min |
| Sucursales (`parking_branches`) | Estática | TTL 30 min |
| Capacidad de sucursales (`parking_aforo`) | Cada entrada/salida | TTL 10s |
| Datos del usuario (`users`) | Estática por request | Request-scoped |
| Estado de ocupación (`access_logs`) | Cada evento | In-memory + WS push |

### 1.12 Cuello de botella principal

**El cuello de botella principal es la base de datos SQLite como default.** Aunque en producción usa Neon PostgreSQL, el `config.py:23` defaulta a `sqlite:///./parking.db`. SQLite tiene un solo writer, y bajo concurrencia real (múltiples entradas ALPR + dashboard + workers) produce `"database is locked"`.

El segundo cuello son las **queries sin índices** en las tablas de mayor tráfico (`access_logs`, `reservations`), que ejecutan full scans en cada operación de entrada/salida de vehículos.

### 1.13 ¿Qué sucedería si la cantidad de usuarios se multiplicara?

| Multiplicador | Impacto |
|---|---|
| **×10** (~50-100 usuarios simultáneos) | Pool de conexiones saturado. Workers con full scans compiten por IO. Latencia visible en dashboard. ALPR puede perder frames. |
| **×100** (~500-1000 usuarios) | Neon free tier colapsa. WebSocket broadcast serial bloquea eventos. Rate limiting in-memory (300/min por IP) insuficiente. N+1 queries multiplican carga exponencialmente. |
| **×1000** (~5000-10000 usuarios) | Necesita arquitectura completamente diferente: connection pooling externo (PgBouncer), Redis para caché/sesiones, Celery para workers, CDN para estáticos, separación de servicios ALPR. |

---

## 2. Coherencia entre módulos

### 2.1 Código repetido

**Lógica de normalización duplicada 4 veces:**
1. `core/normalize.py:4-7` — `normalize_name()` (central)
2. `routes/system/common.py:35-40` — `normalize_system_name()` (copia)
3. `services/reservation_service.py:18-22` — `_normalizar_sucursal()` (copia)
4. `alpr/config.py:22-25` — `normalize_id()` (copia)

Además, `core/normalize.py:10-11` tiene `normalize_branch_name()` que es un alias muerto de `normalize_name()` — nunca se invoca.

**Validación de contraseña duplicada 3 veces:**
1. `schemas/validators.py:4-11` — validador central
2. `schemas/auth.py:19-25` — reimplementa las mismas 3 regex inline
3. `static/js/modules/auth.js:149` — reimplementación client-side

### 2.2 Funcionalidades duplicadas

- **Dos sistemas de migración:** `init_db.py` ejecuta `ALTER TABLE` manual + `create_all` + Alembic en `main.py`. Tres fuentes de verdad diferentes.
- **Dos constructores de URL de BD:** `core/database.py:13-14` y `alembic/env.py:23-24` hacen la misma conversión `postgresql://` → `postgresql+psycopg://`.
- **Doble import de `TimeService`:** `services/billing_service.py:7` importa al top level y lo re-importa localmente en línea 116.

### 2.3 Diferentes formas de resolver el mismo problema

| Problema | Forma A | Forma B |
|---|---|---|
| **Normalización de texto** | `core/normalize.py` | 3 copias inline |
| **Consulta de usuario por email** | `db.query(models.User).filter_by(email=...)` (services) | `authenticate_user` con email normalizado (security) |
| **Manejo de errores HTTP** | `raise HTTPException(status_code=..., detail=...)` (la mayoría) | `return {"error": "..."}` (algunos endpoints admin) |
| **Timestamps** | `core.time.localnow()` (tickets) | `datetime.now()` (users, reservations) | `datetime.datetime.now().isoformat()` (aforo) |
| **Autorización** | `str(admin.rol) != UserRole.ADMIN.value` (`users.py:18`) | `admin.rol != "admin"` (`promotions.py:14`) | `staff.rol != "admin"` (`reservations.py:23`) |

### 2.4 Entidades que representan conceptos similares de distintas maneras

- **Fechas:** Soporte usa `DateTime` nativo de SQLAlchemy. Todo el dominio de parking (reservations, access_logs, points_log, coupons, redemption_tickets) almacena fechas como **`String`** (ISO format). Peor aún: se mezcla `T` separator (`2026-09-04T10:00`) con space separator (`2026-09-04 10:00`), lo cual produce errores silenciosos en comparaciones lexicales.

- **Enums:** `models/enums.py` define enums de Python (`UserRole`, `VehicleType`, etc.) pero **ninguna columna** los usa como `Enum` de SQLAlchemy. Los estados son strings libres (`"Pendiente"`, `"VIGENTE"`, etc.) con validación por convención.

### 2.5 Validaciones duplicadas

- Password: 3 implementaciones (ver §2.1)
- Email: validación en Pydantic schema + normalización en `authenticate_user` + normalización en register
- Patente: normalización en `core/normalize.py` + normalización inline en `access_service.py:80` + normalización en `reservation_service.py`

### 2.6 Diferentes criterios para manejar errores

- **Rutas de usuario:** `HTTPException(404, "Ticket no encontrado")`
- **Rutas de admin:** Algunas usan `HTTPException`, otras devuelven `{"error": "..."}` con status 200
- **Services:** Devuelven `None` en caso de no encontrar (caller debe chequear)
- **Workers:** `try/except Exception` que swallan errores silenciosamente (`worker_service.py:96`)
- **ALPR:** `print()` a stdout en subprocess, no llega al log central

### 2.7 Diferentes criterios de autenticación/autorización

- `get_current_user` — usuario autenticado (cualquier rol)
- `get_local_manager` — admin o local_admin
- `get_super_admin` — solo admin global
- `get_operational_user` — para endpoints de hardware
- **Problema:** `routes/admin/virtual_time.py:38` usa solo `get_current_user` (cualquier usuario puede manipular el reloj virtual global)

### 2.8 Nombres inconsistentes

- Mezcla español/inglés: `verificar_disponibilidad` vs `validate_plate` vs `get_user_active_stays`
- Prefijos inconsistentes: `parking_` en algunos modelos, `user_` en otros, sin prefijo en Reservation
- `sucursal` vs `branch` vs `parking_branch` — tres nombres para el mismo concepto
- `fecha_inicio` vs `created_at` vs `ultima_actualizacion` — timestamps con nombres diferentes

### 2.9 Módulos que no respetan las mismas reglas de negocio

- **Admin branch CRUD** (`routes/admin/branches.py:24`) tiene un bug: referencia `nombre` no definida → `NameError` al crear pisos.
- **Soporte** (`routes/user/support.py:28`) llama `NotificationService.notify_occupancy_change(db)` después de crear un ticket — semánticamente incorrecto (no es un cambio de ocupación).
- **Virtual time** (`routes/admin/virtual_time.py`) es accesible por cualquier usuario autenticado, no solo admin.

### 2.10 Respuesta a la pregunta principal

> *"Si un nuevo desarrollador ingresara al proyecto, ¿podría entender que todo fue construido como una única aplicación?"*

**Parcialmente.** La estructura de carpetas (`routes/`, `services/`, `models/`) es coherente y sigue un patrón MVC reconocible. Sin embargo, un desarrollador nuevo notaría:
1. Cuatro copias de la misma función de normalización
2. Dos sistemas de migración compitiendo
3. Fechas almacenadas como strings en un módulo y como DateTime en otro
4. Autorización verificada de 3 formas diferentes
5. `print()` en vez de logging en ALPR y workers
6. Un repositorio entero (`repositories/user_repository.py`) que nunca se importa

Parece una **aplicación construida como un todo** pero con deuda técnica acumulada por iteraciones rápidas (probablemente asistidas por IA) que introdujeron inconsistencias.

---

## 3. Preparación para una aplicación que vivirá varios años

### 3.1 Mantenibilidad

**Fortalezas:**
- Separación clara en capas (routes → services → models)
- Uso de dependencias de FastAPI para inyección de DB y auth
- Pydantic schemas para validación de entrada
- Test suite existente (15 archivos)

**Debilidades:**
- **3 fuentes de verdad para el esquema:** `create_all`, `init_db.py` ALTER TABLE, y Alembic. Cualquier cambio de esquema debe actualizarse en 3 lugares.
- **Sin refactorización centralizada:** Las 4 copias de normalización, las 3 validaciones de password, los múltiples patrones de error handling no se han consolidado.
- **Acoplamiento implícito:** Los workers acceden directamente a los modelos y ejecutan queries complejas sin pasar por services.
- **Sin typed returns:** Los services devuelven `dict` con claves string en vez de DTOs tipados.

### 3.2 Escalabilidad

**Límites claros:**
- **SQLite como default** no escala para múltiples writers
- **Pool de 30 conexiones** es insuficiente para >100 usuarios concurrentes
- **Workers síncronos** con full scans bloquean el event loop
- **Sin horizontal scaling:** No hay Redis para sesiones compartidas, no hay message queue para workers distribuidos
- **Archivos estáticos servidos por la app** no escalan horizontalmente

### 3.3 Organización del código

```
AUTOPASS/
├── core/           # Config, DB, security, logger, time, normalize
├── models/         # SQLAlchemy models (17 tablas, bien agrupadas)
├── schemas/        # Pydantic schemas (pero con duplicaciones)
├── routes/         # Endpoints (user/, admin/, parking/, system/)
├── services/       # Business logic (14 módulos)
├── repositories/   # Solo 1 usado (reservation_repository)
├── templates/      # Jinja2 + HTMX
├── static/         # JS modules, CSS, images, uploads
├── alembic/        # Migrations (pero el initial está vacío)
├── tests/          # 15 archivos de test
├── alpr/           # Módulo OCR separado (subprocess)
└── init_db.py      # Manual DB init (tercer sistema de migración)
```

La estructura es razonable pero inconsistente: `repositories/` existe pero solo se usa 1 de 2. `alpr/` está separado pero se ejecuta como subprocess. No hay `__init__.py` consistente.

### 3.4 Facilidad para agregar nuevas funcionalidades

**Moderada.** Agregar un nuevo endpoint es straightforward (crear route + schema + service). Pero:
- Agregar una columna a una tabla existente requiere modificar: model, `init_db.py`, migración alembic (3 lugares)
- Agregar una feature que toque múltiples módulos requiere entender 3 patrones diferentes de error handling
- No hay "feature flags" ni configuración por tenant/plan

### 3.5 Dependencias utilizadas

**48 dependencias en `requirements.txt`**, de las cuales **~17 nunca se importan:**
- `passlib` (bcrypt se usa directo)
- `scipy`, `scikit-image`, `shapely`, `pyclipper` (nunca importados)
- `google-generativeai` + 4 paquetes Google API (nunca importados)
- `htttptools`, `tqdm`, `pyyaml`, `annotated-doc`, `colorama`, `click` (nunca importados)
- Duplicidad: `opencv-python` Y `opencv-python-headless`
- Duplicidad: `psycopg[binary]` Y `psycopg-binary`

### 3.6 Versiones de frameworks y librerías

| Dependencia | Versión | Estado |
|---|---|---|
| FastAPI | 0.135.1 | Actual (2025) |
| SQLAlchemy | 2.0.48 | Actual |
| Pydantic | ≥2.10.0 | Actual |
| python-jose | 3.5.0 | **CVE conocido** (CVE-2024-33663) |
| bcrypt | 5.0.0 | Actual |
| alembic | 1.19.0 | Actual |
| uvicorn | 0.42.0 | Actual |

**Riesgo:** `python-jose` tiene CVEs conocidos. Se recomienda migrar a `PyJWT`.

### 3.7 Código obsoleto

- **`models/reservation.py:29-35`** — Tabla `coupons` completa: **0 queries** en todo el código. Nunca se usa.
- **`reservations.mp_preference_id`** — Campo MercadoPago: 0 referencias en el código. Vestigio.
- **`repositories/user_repository.py`** — Clase entera: nunca importada.
- **`schemas/auth.py:15`** — `new_password` en `ResetPasswordRequest` con `field_validator` duplicado.
- **`core/normalize.py:10-11`** — `normalize_branch_name` alias muerto.
- **`run_server.bat` / `setup_backend.bat`** — Scripts de desarrollo local, obsoletos si se usa Docker.

### 3.8 Acoplamiento entre componentes

- **Workers ↔ Services ↔ Models:** Los workers (`worker_service.py`) acceden directamente a modelos y ejecutan queries SQL sin pasar por la capa de services.
- **ALPR ↔ Access Service:** El ALPR se comunica vía WebSocket y HTTP, pero el endpoint de camera-reading (`cameras.py`) es completamente auto-contenido sin pasar por services.
- **Templates ↔ JS modules:** Los templates Jinja2 renderizan datos server-side, pero la mayoría de la lógica UI está en módulos JS que hacen fetch a la API. Hay superposición.

### 3.9 Documentación

- **No existe documentación de arquitectura** (no ARCHITECTURE.md, noADR)
- **No existe API docs** más allá de la generada automáticamente por FastAPI (Swagger)
- **No existe guía de setup** más allá de `setup_backend.bat`
- **No existe CONTRIBUTING.md**
- Los docstrings son All-Caps en español pero no explican "por qué", solo "qué"

### 3.10 Configuración de diferentes ambientes

- **No existe distinción de ambientes.** Un solo `.env` para todo.
- No hay `settings_dev.py`, `settings_prod.py`, ni environment detection
- El `DATABASE_URL` default es SQLite (desarrollo), pero no hay mecanismo automático de selección
- No hay Docker, no hay CI/CD, no hay GitHub Actions

### 3.11 Estrategia de actualización tecnológica

**Inexistente.** No hay:
- Dependabot o Renovate para updates automáticos
- CI que ejecute tests en PRs
- Pinning seguro de dependencias (usa `>=` sin upper bounds en muchos casos)
- Security scanning (no Snyk, no safety, no bandit)

### 3.12 ¿Qué partes podrían ser un problema en 5 años?

1. **Las 3 fuentes de verdad del esquema** — inevitablemente divergirán
2. **Las 48 dependencias sin actualización automática** — acumularán CVEs
3. **Las fechas como strings** — inevitablemente causarán bugs a medida que se agreguen features temporales
4. **Los workers síncronos** — no podrán escalar con el tráfico
5. **La falta de tests de integración** — los 15 test files son unitarios, no hay tests E2E
6. **La documentación ausente** — cada nuevo desarrollador tardará semanas en entender el sistema

---

## 4. Análisis de arquitectura

### 4.1 Arquitectura actual

**Monolito MVC síncrono** con:
- FastAPI como framework HTTP
- SQLAlchemy ORM síncrono
- Jinja2 + HTMX + JS vanilla para frontend
- PostgreSQL (Neon) como BD
- MQTT + Serial para hardware
- WebSockets para tiempo real
- Threads para workers background
- Subprocess para ALPR

### 4.2 Evaluación

**B. La arquitectura es adecuada pero necesita mejoras.**

**Por qué es adecuada:**
- Un monolito es correcto para una aplicación de este tamaño (~39K LOC, 17 tablas, 101 endpoints)
- FastAPI es ideal para APIs REST con WebSocket
- SQLAlchemy es el estándar de facto para Python + relational DB
- El patrón routes → services → models es claro y mantenible
- HTMX + vanilla JS evita la complejidad de un SPA framework

**Por qué necesita mejoras:**

1. **Async real:** Los endpoints son `def` (síncronos) pero FastAPI soporta `async def`. Con `databases` o `SQLAlchemy async`, se liberarían los threads del event loop.

2. **Task queue:** Los workers con `threading.Thread` no son robustos. Celery/RQ con Redis permitiría:
   - Reintentos automáticos
   - Monitoreo de tareas
   - Escalado horizontal
   - Colas prioritarias

3. **Caché:** Redis como capa de caché para tarifas, estados de ocupación, datos de usuario. Reduce carga de BD en 60-80%.

4. **Separación de servicios ALPR:** Los subprocess de ALPR deberían ser un servicio separado (mismo código, diferente proceso), comunicándose vía WebSocket o cola de mensajes, no vía HTTP directo a la app principal.

5. **CDN para estáticos:** Los archivos JS/CSS/imágenes deberían servirse desde un CDN o bucket S3, no desde FastAPI.

### 4.3 Diagrama de componentes actual

```
┌─────────────┐     ┌──────────────────────────────────┐
│   Browser    │────▶│        FastAPI (Monolith)         │
│  (HTMX+JS)  │◀────│                                    │
└─────────────┘     │  ┌────────┐  ┌────────┐  ┌──────┐│
                    │  │ Routes │→ │Services│→ │Models││
                    │  └────────┘  └────────┘  └──────┘│
                    │       │          │          │      │
                    │       └──────────┼──────────┘      │
                    │                  ▼                  │
                    │         ┌──────────────┐           │
                    │         │  SQLAlchemy  │           │
                    │         │   (sync)     │           │
                    │         └──────┬───────┘           │
                    │                │                    │
                    │  ┌─────────────┼─────────────┐    │
                    │  │             │             │     │
                    │  ▼             ▼             ▼     │
                    │ ┌───┐   ┌──────────┐   ┌───────┐ │
                    │ │MQTT│   │Neon (PG) │   │Files  │ │
                    │ └───┘   └──────────┘   └───────┘ │
                    │                                    │
                    │  ┌──────────────────┐             │
                    │  │  Worker Threads   │             │
                    │  │  (notifications,  │             │
                    │  │   cleanup)        │             │
                    │  └──────────────────┘             │
                    │                                    │
                    │  ┌──────────────────┐             │
                    │  │  ALPR Subprocess  │             │
                    │  │  (per camera)     │             │
                    │  └──────────────────┘             │
                    └──────────────────────────────────┘
```

---

## 5. Análisis del lenguaje utilizado

### 5.1 Python + FastAPI

| Criterio | Evaluación |
|---|---|
| **Rendimiento** | Adecuado para I/O-bound (API REST). Limitado para CPU-bound (ALPR). El GIL impide paralelismo real. |
| **Escalabilidad** | Horizontal: sí (múltiples workers Uvicorn). Vertical: limitado por GIL. |
| **Seguridad** | Buen ecosistema (bcrypt, python-jose, Pydantic). Requiere configuración correcta. |
| **Ecosistema** | Excelente para web (FastAPI, SQLAlchemy, Pydantic), ML (ONNX, PaddleOCR), IoT (paho-mqtt, pyserial). |
| **Disponibilidad de devs** | Alta. Python es el lenguaje #1 en uso. FastAPI creciendo rápidamente. |
| **Costos** | Bajo. Hosting en Render/Rail/Fly.io desde USD 0-7/mes. Neon free tier para BD. |
| **Mantenibilidad** | Alta. Tipado dinámico pero con Pydantic + type hints facilita refactoring. |
| **Integración BD** | Excelente (SQLAlchemy + psycopg para PostgreSQL). |
| **Proyección a futuro** | Python 3.13+ con nogil (PEP 703) mejorará rendimiento. FastAPI madurando. |

### 5.2 ¿Para ESTA aplicación concreta existe realmente una razón técnica para cambiar de lenguaje?

**No.** Razones:

1. **FastAPI + SQLAlchemy** es el stack ideal para una API REST con ORM. Node.js/Express o Go/Gin no ofrecen ventaja clara para este caso de uso.

2. **ALPR (OCR) funciona bien en Python** gracias a ONNX Runtime. En Go o Node sería más difícil (menos librerías de CV).

3. **MQTT + Serial** tienen bibliotecas maduras en Python (`paho-mqtt`, `pyserial`).

4. **El bottleneck no es el lenguaje** — es la arquitectura (queries sin índices, workers síncronos, sin caché). Resolver esto en Python es más rápido que reescribir en otro lenguaje.

5. **El equipo conoce Python.** Cambiar de lenguaje tendría un costo de aprendizaje enorme sin beneficio proporcional.

**Única excepción:** Si el ALPR fuera critical path de alta frecuencia (>30 FPS por cámara), un servicio dedicado en Rust/C++ para el procesamiento de video podría ser beneficioso. Pero para 1-4 cámaras de parking, Python con ONNX es suficiente.

---

## 6. Análisis de costos y consumo de recursos

### 6.1 Servidor

**Opción actual (inferida):** Servidor único corriendo la app + Uvicorn.

| Componente | Costo estimado | Notas |
|---|---|---|
| Render/Rail/Fly.io (Python) | USD 7-25/mes | Free tier limitado |
| VPS (DigitalOcean/Hetzner) | USD 5-20/mes | Más control |
| AWS EC2 t3.micro | USD 8-15/mes | Con reserved pricing |

**Conclusión:** El costo del servidor es bajo. Con Uvicorn + 2-4 workers, un VPS básico maneja 50-100 usuarios simultáneos.

### 6.2 Base de datos

| Tier Neon | Conexiones | Almacenamiento | Costo |
|---|---|---|---|
| Free | 1-20 | 512 MB | USD 0 |
| Launch | 100-500 | 10 GB | USD 19/mes |
| Scale | 1000+ | 100 GB | USD 69/mes |

**Riesgo de costos:** La BD Neon free tier es suficiente para desarrollo/primeros usuarios. A 100+ usuarios concurrentes, se necesita Launch tier. Las queries sin índices (§1.6) incrementan el uso de CPU de BD, lo que puede sobrepasar los límites del free tier.

**Optimizaciones disponibles:**
- **Índices en columnas calientes** reducirían el CPU de BD en ~60-80% (ver §1.6)
- **Caché Redis** para tarifas/estados reduciría queries en ~70%
- **Paginación server-side** en reports evitaría full scans

### 6.3 Almacenamiento

| Tipo | Crecimiento estimado | Costo |
|---|---|---|
| Imágenes ALPR (JPG) | ~50 KB × N eventos/día | Creciente sin limpieza |
| Archivos de soporte (PDF/img) | ~500 KB × N tickets/día | Creciente sin limpieza |
| Logs | Inexistente (stdout) | USD 0 |
| BD | ~1 KB × N registros | Variable |

**Riesgo:** Las imágenes ALPR se guardan sin rotación ni eliminación. Con 100 vehículos/día × 365 días = 36,500 archivos (~1.8 GB/año). Con 1000/día = 18 GB/año. Sin política de retención, esto crece indefinidamente.

### 6.4 Transferencia de datos

- **API responses:** JSON liviano (~1-10 KB por request). Bajo.
- **WebSocket occupancy:** ~500 bytes por update, cada pocos segundos. Bajo.
- **Imágenes ALPR:** No se transfieren al frontend (se guardan localmente). Bajo.
- **Estáticos (JS/CSS):** ~500 KB total. Bajo, pero servidos desde la app (no CDN).

### 6.5 APIs externas

| API | Uso | Costo |
|---|---|---|
| MQTT (HiveMQ public) | Conexión a broker | Gratis (limitado) |
| Mailtrap | Email de desarrollo | Gratis (100 emails/día) |
| Neon PostgreSQL | BD | Gratis (free tier) |
| Google APIs | Importadas pero **nunca usadas** | USD 0 (pero dependencia innecesaria) |

**Riesgo:** HiveMQ público tiene límites de conexiones y mensajes. Para producción se necesita un broker privado (Mosquitto self-hosted o AWS IoT).

### 6.6 Servicios de IA

- **RapidOCR + PaddleOCR:** Modelos locales, sin costo por uso. Pero consumen ~500 MB RAM por instancia de cámara.
- **Google Generative AI:** Importado (`google-generativeai`) pero **nunca usado** en el código. Dependencia muerta que puede eliminarse.

### 6.7 Envío de correos

El email service (`services/email_service.py`) envía emails en un **nuevo thread por cada email** (línea 61). Sin límite de concurrencia. Si se envían muchos emails simultáneamente (notificaciones masivas), se crean threads ilimitados.

**Optimización:** Usar una cola de emails (Celery + Redis) o al menos un pool de threads limitado.

### 6.8 Componentes que podrían aumentar su costo

| Componente | Trigger de escalada | Mitigación |
|---|---|---|
| **Neon DB** | Queries sin índices → alto CPU | Agregar índices (ver §1.6) |
| **Servidor** | >100 usuarios concurrentes | CDN para estáticos, caché Redis |
| **ALPR** | >4 cámaras | Servicio ALPR separado |
| **Email** | Notificaciones masivas | Cola con rate limiting |
| **Almacenamiento** | Sin retención de imágenes | Política de retención + compresión |

---

## 7. Revisión del código generado por IA

### 7.1 Código duplicado

| Patrón duplicado | Instancias | Ubicaciones |
|---|---|---|
| Normalización de texto | 4 copias | `core/normalize.py`, `common.py:35`, `reservation_service.py:18`, `alpr/config.py:22` |
| Validación de contraseña | 3 copias | `schemas/validators.py:4`, `schemas/auth.py:19`, `auth.js:149` |
| Consulta de rate/tarifa | ~10 instancias | `billing_service.py:33,56`, `balance.py:46`, `status.py:338`, todas con el mismo patrón |
| Normalización de patente | ~15 instancias | `access_service.py:80,90`, `operations.py:41,126`, `vehicles.py:37,60`, `reservations.py:103` |

### 7.2 Código que nunca se ejecuta

- **`repositories/user_repository.py`** — Clase `UserRepository` completa: nunca importada
- **`models/reservation.py:29-35`** — Tabla `Coupons`: 0 queries en todo el proyecto
- **`reservations.mp_preference_id`** — Columna MercadoPago: 0 referencias
- **`core/normalize.py:10-11`** — `normalize_branch_name()`: alias muerto

### 7.3 Funciones que ya no se utilizan

- `normalize_branch_name` (dead alias)
- `UserRepository` class (never imported)
- `Coupon` model (never queried)

### 7.4 Variables innecesarias / imports innecesarios

- `services/billing_service.py:7` importa `TimeService` al top + lo re-importa en línea 116
- `services/reservation_service.py:20` importa `unicodedata` localmente dentro de una función duplicada
- `requirements.txt` incluye 17+ paquetes nunca importados

### 7.5 Soluciones excesivamente complejas

- **`services/report_service.py`** — El módulo de reports usa `literal_column` + `union_all` + sort in-memory + offset pagination para unificar access_logs y reservations. Es extremadamente complejo para lo que hace: un listado combinado de pagos. Podría resolverse con una vista SQL o una tabla de eventos unificados.

- **`services/worker_service.py`** — El worker de notificaciones re-implementa un programador de tareas completo dentro de un `while True` + `time.sleep(30)`. Un CronJob o Celery beat sería más simple y robusto.

### 7.6 Código que funciona pero no respeta buenas prácticas

- **`print()` en vez de `logging`** — 62 llamadas a `print()` en producción
- **`except Exception: pass`** — Errores silenciados sin logging (`common.py:31`, `worker_service.py`)
- **Fechas como strings** — Almacena ISO strings en vez de DateTime nativo
- **Sin type hints en returns** — Services devuelven `dict`, `None`, o `Model` sin consistencia
- **Constantes mágicas** — `"Pendiente"`, `"VIGENTE"`, `"En revisión"` como strings hardcodeados en vez de usar los enums definidos

### 7.7 Dependencias que no son necesarias

**17 paquetes en `requirements.txt` que nunca se importan en el código:**
`htttptools`, `passlib`, `scipy`, `scikit-image`, `shapely`, `pyclipper`, `google-generativeai`, `google-api-python-client`, `google-auth`, `google-auth-httplib2`, `google-ai-generativelanguage`, `googleapis-common-protos`, `tqdm`, `pyyaml`, `annotated-doc`, `colorama`, `click`

**2 paquetes duplicados:**
- `opencv-python` + `opencv-python-headless` (conflicto potencial)
- `psycopg[binary]` + `psycopg-binary` (redundante)

---

## 8. Revisión de logs y manejo de información

### 8.1 Mecanismo actual de logging

**`core/logger.py:5-18`** — Configuración mínima:
- Framework: stdlib `logging`
- Nivel: INFO
- Handler: `StreamHandler(sys.stdout)` (un solo handler)
- Formato: `[timestamp] LEVEL logger: message` (texto plano)
- **Sin file handler** → logs se pierden al reiniciar
- **Sin rotación** → sin archivos de log persistentes
- **Sin formato JSON** → imposible indexar/agregar/buscar

### 8.2 Información que se guarda

Casi nada. La aplicación tiene un logging extremadamente mínimo:

- **No se loguea:** Login exitoso, login fallido, intentos de acceso bloqueado, creación/edición/eliminación de entidades, cambios de contraseña, reset de contraseña
- **No se loguea:** Requests HTTP entrantes (el handler de uvicorn.access está silenciado a WARNING)
- **No se loguea:** Queries SQL (silenciado a WARNING)
- **No se loguea:** Errores de autenticación/autorización
- **Sí se loguea:** Seed data al iniciar (`core/seed.py`), errores de notificación (`print()`, no logger)
- **62 `print()` bypass logging** — especialmente en ALPR (subprocess) y workers

### 8.3 Datos personales / información sensible

| Dato | ¿Se guarda en logs? | Riesgo |
|---|---|---|
| Contraseñas | No (solo hash en DB) | Bajo |
| Tokens JWT | No | Bajo |
| DNI / Teléfono | No explícitamente | Bajo |
| Email | No explícitamente | Bajo |
| Patentes | Sí, implícitamente en ALPR logs | Medio |
| SECRET_KEY | Sí, como fallback en `config.py:17` | **Alto** (si .env falta) |

### 8.4 Análisis del nivel de logs

- **ALPR:** `print()` a stdout en subprocess → solo visible en consola del proceso, no en log central
- **Workers:** `print()` para errores de notificación → se pierde
- **Services:** Algunos usan `logger` (via `get_logger()`), otros usan `print()`
- **Routes:** Casi ninguno loguea
- **Database:** Silenciada a WARNING

### 8.5 ¿Los logs actuales permitirían investigar un incidente?

**No.** Si mañana ocurre:
- **Un ataque de fuerza bruta:** No hay logs de intentos de login fallidos
- **Un acceso no autorizado:** No hay logs de autorización rechazada
- **Una corrupción de datos:** No hay audit trail de cambios
- **Un error en producción:** Los errores se swallean sin logging (`except: pass`)
- **Un problema de performance:** No hay logs de queries lentas ni métricas

Los logs actuales son insuficientes para cualquier tipo de investigación de incidentes.

### 8.6 Recomendaciones

1. **Archivo de log con rotación** — mínimo 30 días de retención
2. **JSON estructurado** — para indexación en ELK/Grafana
3. **Audit trail** — loguear TODAS las acciones de admin (CRUD users, branches, settings)
4. **Security events** — loguear login, logout, intentos fallidos, accesos bloqueados
5. **Request logging** — activar el handler de uvicorn.access
6. **SQL logging en debug** — para investigación de performance
7. **Reemplazar `print()` por `logger`** en todo el código

---

## 9. Auditoría de seguridad

### 9.1 CRÍTICO

#### C1. Credenciales de BD y secretos comprometidos en git

- **Riesgo:** Exposición de credenciales / breach completo de datos
- **Evidencia:** `.env` y `.env.example` están tracked en git. El `.gitignore:5` incluye `.env` pero fue agregado **después** de que el archivo ya estaba commiteado. El historial de git contiene:
  - Password de Neon: `npg_3sJtSwT9dbRK` (commit `24a0760`)
  - Token JWT de Turso: `eyJ...` (commit `0b1bf19`)
  - `.env.example` con la URL completa de producción
- **Impacto:** Cualquier persona con acceso al repo (o al historial si es público) puede conectarse a la BD de producción, leer/modificar todos los datos de usuarios.
- **Solución:** (1) Rotar el password de Neon y revocar el token de Turso **inmediatamente**. (2) `git rm --cached .env` y purgar del historial con `git filter-repo`. (3) Asegurar que `.env` esté gitignored antes de cualquier commit futuro.

#### C2. `SECRET_KEY` hardcodeado como fallback

- **Riesgo:** Forjado de tokens JWT / autenticación rota
- **Evidencia:** `core/config.py:17` — `SECRET_KEY: str = os.getenv("SECRET_KEY", "tu_super_secreto_para_produccion")`. El valor default es público y predecible.
- **Impacto:** Si `.env` no está presente (fresh clone, otro dev, deploy Dockerizado), el secret JWT es una cadena conocida. Cualquiera puede forjar tokens de admin.
- **Solución:** Eliminar el fallback. Fallar al startup si `SECRET_KEY` no está configurado o es débil.

#### C3. IDOR — cualquier usuario puede cancelar la reserva de otro y quedarse con el reembolso

- **Riesgo:** Fraude financiero directo
- **Evidencia:** `services/reservation_service.py:362` — `cancel_reservation` busca `Reservation` por `res_id` **sin filtrar por `user_id`**. El caller en `routes/user/reservations.py:283-286` pasa `current_user` pero no verifica propiedad. El reembolso se acredita al caller (`reservation_service.py:381`).
- **Impacto:** Un usuario puede enumerar IDs de reserva, cancelar reservas ajenas, y recibir el saldo reembolsado en su propia cuenta.
- **Solución:** En la ruta de usuario, filtrar por `user_id`. La ruta de admin puede mantener el `user_id=None` con autorización `get_super_admin`.

#### C4. Endpoints sin autenticación: "mark paid" e inyección de frames

- **Riesgo:** Manipulación de pagos / suplantación de video
- **Evidencia:**
  - `routes/parking/access.py:30-34` — `POST /v1/access/pay-stay` **sin dependencia de auth**. Marca `pago_confirmado = True` sin cobro real.
  - `routes/system/video.py:53-58` — `POST /update-frame/{camera_id}` inyecta frames arbitrarios al feed de video, sin auth.
  - `routes/system/health.py:52-56` — `POST /heartbeat` sin auth.
- **Impacto:** Cualquiera puede marcar una estancia como pagada sin pagar, inyectar frames falsos en cámaras de seguridad, o simular heartbeats de nodos ALPR muertos.
- **Solución:** Requerir autenticación (o shared-secret API key para hardware) en todos estos endpoints.

#### C5. Auto-servicio de saldo y puntos (farming)

- **Riesgo:** Integridad financiera
- **Evidencia:**
  - `routes/user/balance.py:68-86` — `POST /v1/user/recharge-balance` agrega `saldo += monto` **sin verificación de pago**. Sin límite superior.
  - `routes/user/fidelization.py:87-104` — `POST /v1/user/points-adjust?delta=...` permite a cualquier usuario agregar **puntos ilimitados** a su cuenta.
- **Impacto:** Los usuarios pueden crear saldo y puntos de la nada, canjearlos por estacionamiento gratis y vouchers.
- **Solución:** Eliminar estos endpoints o detrás de verificación de pago real + autorización admin.

#### C6. Cualquier usuario puede manipular el reloj virtual global

- **Riesgo:** Manipulación de facturación
- **Evidencia:** `routes/admin/virtual_time.py:38-59` usa solo `Depends(get_current_user)` — cualquier cliente autenticado. Expone `/advance`, `/set`, `/reset`.
- **Impacto:** Un usuario regular puede adelantar el tiempo para auto-cancelar reservas antes de que se cobren, o manipular cálculos de deuda/refund.
- **Solución:** Restringir a `Depends(get_super_admin)`.

### 9.2 ALTO

#### H1. XSS stored/reflected via innerHTML

- **Evidencia:** Múltiples módulos JS construyen DOM con template literals de datos de usuario y asignan a `.innerHTML`:
  - `static/js/modules/dashboard-tickets.js:113,180` — asunto, mensaje de tickets de soporte
  - `static/js/modules/notifications.js:59,403` — mensaje/título de notificaciones
  - `static/js/modules/profile.js:117` — descripciones de promociones
  - `static/js/modules/dashboard-reservations.js` — patentes, nombres de sucursal
- **Impacto:** Un usuario puede inyectar `<script>` o `<img onerror>` en un mensaje de soporte. Cuando un admin lo ve en el dashboard, el payload ejecuta en la sesión del admin → robo de token completo.
- **Solución:** Nunca usar `innerHTML` con datos de usuario. Usar `textContent` o una función `escapeHtml()`.

#### H2. File upload: solo valida extensión, no contenido

- **Evidencia:** `routes/user/support.py:98-118` — valida extensión contra allowlist, pero:
  1. Escribe el archivo **primero** (línea 109-110) y luego verifica tamaño (línea 112) → TOCTOU
  2. No verifica MIME/contenido real — un `.jpg` puede contener HTML/JS
  3. Los archivos se sirven desde el mismo origen vía `StaticFiles` → XSS served from same origin
- **Impacto:** Subir un HTML/JS con extensión `.jpg` permite XSS stored, sirviendo el payload desde el mismo dominio.
- **Solución:** Validar contenido real (python-magic), verificar tamaño ANTES de escribir, servir uploads con `Content-Disposition: attachment` y `X-Content-Type-Options: nosniff`.

#### H3. Sin protección CSRF

- **Evidencia:** No hay middleware CSRF ni tokens CSRF. Auth usa Bearer token en `localStorage` (no cookie). FastAPI no tiene CSRF built-in.
- **Impacto:** Combinado con XSS (H1), el atacante puede ejecutar requests cross-origin con el token de la víctima. El uso de `localStorage` en vez de cookies httpOnly agrava el riesgo.
- **Solución:** Migrar tokens a cookies httpOnly + SameSite=Strict. Agregar CSRF tokens para state-changing operations.

#### H4. Token de recuperación de contraseña: largo, en URL, no invalidado

- **Evidencia:** `routes/auth.py:40-46` — usa JWT con exp=60 min, colocado en la URL (`reset-password?token=...`). Sin nonce, sin uso único, sin invalidación post-uso.
- **Impacto:** El token queda en historial del browser, logs de referrer, y se puede reutilizar.
- **Solución:** Usar tokens opacos aleatorios (`secrets.token_urlsafe`), almacenar hasheados en DB con `used` flag y expiración.

#### H5. Bug en `branches.py:24` — variable no definida

- **Evidencia:** `routes/admin/branches.py:24` — `add_floor()` referencia `nombre` que no es parámetro. Cualquier llamada → `NameError` (500).
- **Impacto:** El endpoint de crear pisos está roto. Disponibilidad afectada.

#### H6. LIKE con wildcards de usuario

- **Evidencia:** `services/report_service.py:58,87,110,135+` — `.filter(X.sucursal.like(f"%{target_name}%"))` donde `target_name` puede contener `%`. Un admin con sucursal `%` puede ver datos de todas las sucursales.
- **Impacto:** Filtrado cross-branch: un local_admin puede leer la data financiera de otras sucursales.
- **Solución:** Escapar `%`/`_` en valores de filtro, o usar igualdad exacta.

### 9.3 MEDIO

| ID | Hallazgo | Evidencia |
|---|---|---|
| M1 | CORS totalmente permisivo (`*`) | `main.py:42-47`, `config.py:20` |
| M2 | `python-jose` con CVE conocido | `requirements.txt:22` |
| M3 | PII en texto plano en DB (dni, telefono, email) | `models/user.py:14-28` |
| M4 | Datos sensibles impresos (no logueados) | `print()` en services |
| M5 | Sin límites de longitud en inputs | Faltan `max_length` en schemas |
| M6 | JWT sin revocación server-side | Tokens de 24h no se pueden invalidar |
| M7 | Usuarios bloqueados mantienen token 24h | `get_current_user` no chequea `is_blocked` |

### 9.4 Buenas prácticas observadas

- Bcrypt con salt por usuario para contraseñas (`core/security.py:25-30`)
- Validación server-side de fuerza de contraseña
- SQLAlchemy ORM (no SQL raw con interpolación)
- Dependencies de autorización (`get_super_admin`, `get_local_manager`) en endpoints admin
- Tickets de soporte con ownership scoping para usuarios
- Rate limiting con slowapi en endpoints sensibles (auth, access)

---

## 10. ¿Es necesario incorporar otro lenguaje?

### **A. No es necesario incorporar otro lenguaje.**

**Justificación técnica:**

1. **Procesamiento intensivo (ALPR):** Ya funciona con Python via `rapidocr-onnxruntime` + `paddleocr`. ONNX Runtime ejecuta modelos optimizados en C++ por debajo. Para 1-4 cámaras de parking, el rendimiento es suficiente. Un servicio en Rust/C++ tendría beneficio marginal con costo de mantenimiento significativo.

2. **Inteligencia Artificial:** PaddleOCR + RapidOCR son las mejores opciones de open-source para OCR de patentes. Funcionan nativamente en Python. No hay razón para usar otro lenguaje.

3. **Procesamiento de imágenes:** OpenCV Python es la misma librería que la versión C++ (wraps el mismo código). No hay diferencia de rendimiento.

4. **Generación de archivos:** FastAPI con Jinja2 genera HTML. Para PDFs, `weasyprint` o `reportlab` son nativos de Python. No hay necesidad de otro lenguaje.

5. **Procesos en segundo plano:** Los workers actuales son el problema, no el lenguaje. Un task queue (Celery) en Python resuelve esto sin cambiar de lenguaje.

6. **Tiempo real:** WebSockets en FastAPI funcionan nativamente. No hay necesidad de Node.js u otro lenguaje.

**La aplicación completa es factible y eficiente en Python.** Los problemas de rendimiento identificados en esta auditoría son de **arquitectura** (queries sin índices, workers síncronos, sin caché), no de lenguaje. Resolverlos en Python es más rápido y barato que reescribir en otro lenguaje.

---

## 11. Conclusión general

### 11.1 ¿La aplicación está preparada para salir a producción?

**No.**

**Justificación:** Aunque la aplicación tiene todas las funcionalidades core funcionando (gestión de estacionamiento, reservas, ALPR, soporte, reportes), presenta **6 vulnerabilidades críticas de seguridad** que impiden un lanzamiento responsable:

1. Credenciales de BD comprometidas en git history
2. JWT secret hardcodeado como fallback
3. IDOR en cancelación de reservas (fraude financiero)
4. Endpoints de pago sin autenticación
5. Auto-servicio de saldo y puntos (farming)
6. Acceso al reloj virtual por usuarios no admin

Además, la **falta total de logging** hace imposible detectar o investigar incidentes, y la **ausencia de distinción entre ambientes** (dev/prod) incrementa el riesgo de errores en deployment.

### 11.2 ¿Cuál es actualmente el principal riesgo técnico?

**Las credenciales de la base de datos de producción están comprometidas en el historial de git.** Esto no es un riesgo potencial — es una brecha activa. Cualquiera que haya clonado el repo (o cualquier persona con acceso al historial de GitHub) tiene la contraseña de la BD Neon y el token de Turso. Estos deben rotarse **antes** de cualquier otro cambio.

### 11.3 ¿Cuál es actualmente el principal riesgo de seguridad?

**El IDOR en cancelación de reservas (C3) combinado con el auto-servicio de saldo (C5).** Un usuario malicioso puede:
1. Agregar saldo ilimitado a su cuenta (`/v1/user/recharge-balance`)
2. Cancelar reservas de otros usuarios para recibir sus reembolsos
3. Canjear puntos auto-generados por vouchers

Esto permite **robo directo de dinero** sin necesidad de skills técnicos avanzados.

### 11.4 ¿Cuál es el principal problema de escalabilidad?

**Las queries sin índices en las tablas de mayor tráfico.** `access_logs` y `reservations` se consultan en CADA operación de entrada/salida de vehículos, pero columnas como `tipo_evento`, `sucursal`, `patente_detectada`, `user_id`, `sucursal_nombre` **no tienen índice**. Esto produce full table scans en el hot path. Con 100+ vehículos/día, la BD se degrada rápidamente. Agregar 10-15 índices resolvería el 80% del problema de escalabilidad de BD.

### 11.5 ¿Cuál podría ser el principal problema de costos?

**Neon PostgreSQL free tier con queries sin índices.** Las full table scans consumen CPU de BD innecesariamente. En free tier (limitado), esto puede agotar la cuota y forzar un upgrade prematuro a Launch tier (USD 19/mes). Con índices correctos, el free tier podría soportar 10x más tráfico.

### 11.6 ¿Cuál es el principal problema encontrado en el código generado por IA?

**La duplicación de lógica fundamental.** La normalización de texto está implementada 4 veces, la validación de contraseña 3 veces, y el patrón de consulta de tarifas ~10 veces. Esto no es solo un problema de "código limpio" — es un problema de mantenibilidad y consistencia. Cuando se corrige un bug en una copia, las otras 3 siguen rotas. Un desarrollador nuevo no sabe cuál es la "canónica".

### 11.7 ¿Cambiarían alguna decisión tecnológica?

| Decisión actual | Cambio propuesto | Razón |
|---|---|---|
| SQLAlchemy síncrono | SQLAlchemy async + `databases` | Liberar threads del event loop |
| Workers con `threading.Thread` | Celery + Redis | Reintentos, monitoreo, escalado |
| Sin caché | Redis para tarifas/estados | Reducir carga de BD 60-80% |
| Fechas como `String` | `DateTime` nativo | Correctitud + performance de queries |
| `python-jose` | `PyJWT` | CVE conocidos |
| Sin logging persistente | FileHandler + JSON + rotación | Investigación de incidentes |
| 3 fuentes de verdad de esquema | Alembic como única fuente | Consistencia de BD |
| Archivos estáticos desde FastAPI | CDN / S3 | Escalabilidad horizontal |

### 11.8 ¿Qué deberían solucionar antes de lanzar la aplicación?

#### CRÍTICO (antes de cualquier deploy)

1. **Rotar credenciales comprometidas** — Neon password + Turso token + SECRET_KEY
2. **Purgar `.env` del historial de git** — `git filter-repo` o BFG
3. **Eliminar `recharge-balance` y `points-adjust`** — o detrás de auth real de pago
4. **Corregir IDOR en cancelación** — filtrar por `user_id` en ruta de usuario
5. **Bloquear `pay-stay`, `update-frame`, `heartbeat`** — requerir autenticación
6. **Restringir `virtual_time`** — a `get_super_admin`
7. **Eliminar fallback de `SECRET_KEY`** — fallar si no está configurado

#### ALTO (antes de tener usuarios reales)

8. **Eliminar `innerHTML` con datos de usuario** — reemplazar por `textContent` o escape
9. **Hardening de file uploads** — validar contenido real, tamaño antes de escribir, servir con `nosniff`
10. **Agregar índices a columnas calientes** — `reservations.user_id`, `access_logs.tipo_evento/sucursal/fecha_hora`, `vehicles.user_id`, `settings(clave,sucursal)`
11. **Implementar logging persistente** — file handler + rotación + audit trail de admin actions
12. **Unificar fuentes de verdad de esquema** — Alembic como único sistema de migración
13. **Eliminar dependencias muertas** — 17 paquetes sin import
14. **Corregir bug en `branches.py:24`** — variable `nombre` no definida

#### MEDIO (antes de escalar)

15. **Migrar fechas de String a DateTime** — en todas las tablas del dominio core
16. **Agregar caché Redis** — para tarifas, estados de ocupación, datos estáticos
17. **Implementar task queue** — Celery/RQ para workers en background
18. **Migrar tokens a cookies httpOnly** — + CSRF protection
19. **Implementar invalidación de JWT** — blacklist o tokens de corta vida
20. **Agregar tests de integración** — E2E con TestClient contra BD real
21. **Configurar CI/CD** — GitHub Actions para tests + lint + deploy

#### BAJO (mejoras continuas)

22. **Documentación de arquitectura** — ARCHITECTURE.md
23. **Dockerfile + docker-compose** — para deploy consistente
24. **CDN para estáticos** — o S3 + CloudFront
25. **Paginación server-side** en reports
26. **Rate limiting distribuido** — Redis-backed en vez de in-memory
27. **Cleanup automático** de imágenes ALPR antiguas
28. **Refactorización de duplicación** — normalización, validación, queries de tarifa

---

*Auditoría realizada sobre la revisión del código fuente completo del proyecto AUTOPASS (repositorio `MarianoJAC/AUTOPASS`, branch `main`, commit `842ab9f`).*
