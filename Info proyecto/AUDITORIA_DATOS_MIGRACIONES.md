# Auditoría de Datos y Migraciones — AUTOPASS

> **Fecha:** 2026-09-19 (revisión contra código v9.23.0, rama `main`)
> **Alcance:** `alembic/` (14 migraciones), `core/database.py`, `core/seed.py`, `init_db.py`, `scripts/setup.ps1`, Neon (prod) vs SQLite (dev).
> **Metodología:** sandbox sobre BD SQLite vacía ejecutando los flujos reales de arranque (`setup.ps1` y `main.py`), comparación de `alembic history/current/heads`, revisión manual de cada migración (grep de `op.execute`/data/DDL), verificación de consistencia modelos ↔ migraciones y de seeds.
> **Referencia:** `Info proyecto/PLAN_AUDITORIAS.md` § A4.

---

## 1. Resumen Ejecutivo

| Dimensión | Estado | Hallazgo |
|---|---|---|
| `alembic upgrade head` desde BD vacía | **ROTO** | La migración inicial `c833a3129266` es un `pass` (no crea tablas) → el `ALTER TABLE user_notifications` de `d4f7c8e2a190` falla con `no such table`. El esquema base NO lo construyen las migraciones. |
| Reproducibilidad en Neon | En riesgo | El único flujo que funciona es `create_all` (modelos) + `stamp head`, que esconde el bug. Un `upgrade head` real en Neon desde vacío fallaría igual si se corre sin `create_all` previo. |
| Ramas / heads | **OK** | Cadena lineal de 14 migraciones, single head `ce7d1e2f3a5b` (termina en `ce7d1e2f3a5b`). `alembic current` sobre Neon reporta head: sin pendientes ni divergencias. |
| Migraciones con data de usuario | **OK** | 0 `op.execute` / inserts / updates en todo `alembic/`. Las 3 señaladas en el plan (`49a240f0fc25`, `c9d8e7f6a5b4`, `b7e3a1d2c4f5`) son DDL puro; no tocan filas sensibles. |
| Updates legacy sin migración | **OK** | El prefijo "AUTOPASS " se normaliza en tiempo de lectura (`core/normalize.py:7`, `report_repository.py:59`, `reservation_repository.py:183`), no con operaciones manuales de datos. Los `scripts/_*.py` son tooling de refactor (A2/A3), no migraciones. |
| `DATABASE_URL` dev vs prod | **OK** | Default en `core/config.py:26` = `sqlite:///./parking.db`. `.env` real apunta a Neon (PostgreSQL). No se detecta SQLite en prod. |
| Duplicado de init/seed | **OK** | `scripts/init_db.py` no existe (plan desactualizado). Existe `init_db.py` (raíz) que delega el seeding en `core/seed.py`. Un solo orquestador de seed. |
| **Consistencia models ↔ migraciones** | **DEFECTUOSO → RESUELTO (P1)** | `init_db.py:migrate_db()` hacía `ALTER TABLE` manuales (columnas `is_blocked`, `capacidad_motos`, etc.) sin equivalente Alembic — dos fuentes de verdad del esquema. **Eliminado:** el esquema lo define solo `create_all` de modelos dentro de `sync_schema()`. |

**Nivel de riesgo general: MEDIO-ALTO por operación** — no hay pérdida de datos hoy (las migraciones son DDL puro) y el arranque en prod funciona, pero la verdad del esquema está dividida entre 3 mecanismos (modelos via `create_all`, migraciones Alembic parciales, y ALTERs manuales en `init_db.py`). El `upgrade head` no es reproducible desde cero, que es el criterio de aceptación del plan.

---

## 2. Hallazgos por paso

### A4.1 — `alembic upgrade head` desde BD vacía — **[ROTO]**

**Reproducción (sandbox, SQLite en memoria/disc, sin `create_all` previo):**

```
$ DATABASE_URL=sqlite:///sandbox.db  alembic upgrade head
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) no such table: user_notifications
[SQL: ALTER TABLE user_notifications ADD COLUMN ticket_id INTEGER]   # d4f7c8e2a190
```

**Causa raíz:**
- `c833a3129266_initial_schema.py` tiene `upgrade() -> pass` (línea 24). NO crea tablas.
- De las 19 tablas reales del modelo, las migraciones solo crean 5 (`user_sessions`, `support_ticket_messages`, `redemption_tickets`, `mercadopago_payments` + ajustes). Tablas base (`users`, `user_notifications`, `access_logs`, `support_tickets`, `reservations`, …) las materializa **solo** `Base.metadata.create_all` (`core/database.py:54`).
- `d4f7c8e2a190` (ALTER `user_notifications.ticket_id`, `support_tickets.user_response`) se ejecuta ANTES de que exista cualquiera de esas tablas → fallo seguro en el orden lineal histórico real.

**Flujo que hoy SÍ funciona (y por qué se enmascara el bug) — estado previo a la remediación P1:**
- `scripts/setup.ps1:110-117`: `init_db.py` (create_all) → `alembic stamp head` → `alembic upgrade head`. Como `stamp` ya fijó el head, el `upgrade` posterior es no-op y termina bien.
- `main.py:108-122`: intenta `upgrade head`; ante cualquier excepción hace `stamp head` y sigue con `init_db()`. El fallo queda silenciado en `logger.debug/warning`.

> **Actualización (P1 aplicada):** ambos flujos se reemplazaron por `sync_schema()` (`core/database.py`) — flujo único `create_all` + Alembic al head con warning explícito si la cadena no es reproducible. Ver §4.1.

**Riesgo:** cualquier entorno nuevo que ejecute `alembic upgrade head` sin `create_all` previo (CI/CD, instancia adicional, sandbox) falla; peor, si se intentara remover el fallback, el arranque se rompería. Un `upgrade head` correcto desde vacío es imposible hoy.

**Recomendación (para el fix):**
1. Materializar un **baseline real** en Alembic: o bien generar `c833a3129266` con el schema completo del punto de partida (historizado), o —más simple y seguro para este repo— usar el patrón `init_db` actual + `alembic stamp` como único flujo documentado, y bloquear el `upgrade` salvo migraciones incrementales.
2. Si se quiere reproducibilidad real, configurar Alembic para comparar contra `Base.metadata` (`CHECK_TYPE/autogenerate` en CI) en vez de depender de `create_all` silencioso.

### A4.2 — `alembic history/current`: local vs Neon — **[OK]**

- Cadena **lineal, single head**: `c833a3129266 → b7e3a1d2c4f5 → d4f7c8e2a190 → e5a2b8c1d937 → f1a2b3c4d5e6 → a1b2c3d4e5f6 → a3b4c5d6e7f8 → c9d8e7f6a5b4 → 49a240f0fc25 → e6f7a8b9c0d1 → d3b7e1a9c2f0 → a4c8d2e3f5b6 → b5c9d1e2f3a4 → ce7d1e2f3a5b (head)`.
- `alembic heads` → `ce7d1e2f3a5b (head)` (único).
- `alembic current` contra la URL de `.env` (Neon) → `ce7d1e2f3a5b` = head. **Sin migraciones pendientes en prod.**
- No hay ramas, múltiples heads ni revisiones huérfanas.

**Nota:** no se ejecutó `upgrade`/`downgrade` contra Neon (requiere autorización explícita; solo se leyó `current`). El riesgo de reproducibilidad (A4.1) aplica por igual a Neon si el proveedor parte de BD vacía.

### A4.3 — Migraciones con data de usuario — **[OK]**

Grep sobre `alembic/versions/*.py` de `op.execute|sa.table|insert|update|delete|bulk` → **0 matches**. Todas las migraciones son DDL puro:

| Migración | Acción | Toca filas |
|---|---|---|
| `49a240f0fc25` | índices, `dropdown backend_time`, alter `codigo` | No |
| `c9d8e7f6a5b4` | crea `mercadopago_payments` + 2 índices | No |
| `b7e3a1d2c4f5` | crea `user_sessions` + 3 índices | No |
| resto (11) | create_table / add_column / índices | No |

**Idempotencia:** correcta por construcción (una sola aplicación por revisión; no hay retries parciales). Ninguna migración lee/borra/transforma filas de `users`, pagos ni logs. No hay riesgo de pérdida de datos por migración.

### A4.4 — Updates legacy sin migración — **[OK]**

- Limpieza de prefijo `"AUTOPASS "`: **no es una operación de datos** — se resuelve al leer (`core/normalize.py:7` quita `AUTOPASS `; `report_repository.py:59` y `reservation_repository.py:183` normalizan para comparar). No hay `UPDATE promotions/reports` manual pendiente.
- `core/seed.py` contiene 2 "parches" de datos (líneas 111-121 columnas viejas de aforo, 147-155 coords/logo de sucursales). Son migraciones de datos **disfrazadas de seed**: quedan como deuda → ver hallazgo A4.6.
- `scripts/_migrate_access.py`, `scripts/_acc_chk.py`: herramientas one-off del refactor de repositorios (A2/A3), fuera del runtime; no representan migraciones perdidas.

### A4.5 — `DATABASE_URL` dev/prod — **[OK]**

- Default en `core/config.py:26` = `sqlite:///./parking.db` (dev).
- `.env` real (productive) = `postgresql://…neon.tech/neondb…` (Neon con `sslmode=require&channel_binding=require`).
- `core/database.py:9-15` normaliza `postgresql://` → `postgresql+psycopg://`. No se detecta SQLite en prod.

### A4.6 — Duplicados de init/seed — **[OK + deuda]**

- `scripts/init_db.py`: **no existe** (el plan A4 quedó con la ruta vieja). El inicializador real es `init_db.py` (raíz), invocado por `setup.ps1:110` y `README`.
- Seeding: **un solo orquestador** — `core/seed.py:seed_initial_data()`, llamado por `init_db.py:seed_data()`. Sin duplicación.
- **Deuda RESUELTA en P1:** los `ALTER TABLE … ADD COLUMN` manuales de `init_db.py:migrate_db()` (que definían columnas sin equivalente Alembic como `is_blocked` en `users` o `capacidad_motos` en aforo) fueron **eliminados**. El esquema lo define una sola fuente: los modelos vía `create_all` dentro de `sync_schema()`.

---

## 3. Checklist de cierre (plan A4)

| Ítem del criterio | Estado |
|---|---|
| `upgrade head` verde desde BD vacía en ambos motores | **[x] CORREGIDO (P1)** — flujo único `create_all` + `alembic current == head`; verificado en sandbox SQLite (19 tablas + head) |
| Lista de migraciones pendientes en Neon | Encontrada: **ninguna** (current = head) |
| Migraciones con data de usuario idempotentes y seguras | [x] Sí — DDL puro |
| Updates legacy cubiertos por migración | [x] Sí — normalización en lectura / tooling fuera de runtime |
| `DATABASE_URL` dev=SQLite, prod≠SQLite | [x] Sí |
| Seeds unificados | [x] Sí (deuda de `init_db.py:migrate_db` + parches en seed eliminada en P1) |

---

## 4. Plan de remediación priorizado

1. **[P1] APLICADO — Eliminar la fuente paralela de esquema.**
   - `core/database.py`: nuevo `sync_schema()` = `init_db()` (create_all de modelos) + sincronización Alembic al head; si la cadena de migraciones no es reproducible desde cero, se sella en head con warning explícito (nada de fallback silencioso).
   - `main.py`: el arranque usa `sync_schema()` (antes: `upgrade` + fallback `stamp` + `init_db()` duplicado).
   - `init_db.py`: eliminado `migrate_db()` (los ALTERs manuales paralelos: `is_blocked`, `capacidad_motos`, etc.) y su llamada; ya no hay segunda fuente de definición de columnas.
   - **Verificado:** SQLite vacía → `init_db.py` → 19 tablas completas (incl. `is_blocked`, `ticket_id`) + `alembic current == head`. `pytest tests` → 152 passed.
2. **[P2]** Reproducibilidad **real** de Alembic desde cero: generar un baseline auténtico para `c833a3129266` (schema del punto de partida) si se quiere `upgrade head` sin `create_all` previo. Por ahora el flujo documentado y soportado es `create_all` + `stamp/current==head`.
3. **[P3]** Agregar a CI (cuando se habilite `ci.yml`) un paso de "BD vacía → `init_db` → `alembic current` == head → pytest" que atrape este tipo de regresión.

---

## 5. Notas de ejecución

- Sandbox usado: `%TEMP%\autopass_sandbox_a4.db` y `%TEMP%\autopass_setup_a4.db` (eliminables). Ningún archivo de BD del proyecto fue modificado.
- No se tocó Neon: solo lectura de `alembic current` (head). Cualquier `upgrade`/`downgrade` en prod requiere autorización explícita del responsable.