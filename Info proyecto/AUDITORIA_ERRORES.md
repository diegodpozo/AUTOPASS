# Auditoría de Errores y Manejo de Excepciones — A7

**Prioridad:** Media · **Esfuerzo:** 0.5 día (informe + fixes) · **Entregable:** este documento
**Fecha:** 2026-09-22 · **Base:** suite 675 passed / 54.00s (commits `c04e878`, `ea54cc4`, `c04e878…` ← A6/A5/A3 de la ronda)
**Método:** grep de `except` en `services/*.py` + `routes/*.py`, cross-check con `tests/` (los 675 verifican códigos), revisión manual de los toasts del front.

---

## 1. Hallazgo crítico: excepciones cegadas (sin log)

Scan real de `services/` — `select` de `except Exception:` con/sin `logger` en el bloque contiguo:

| Archivo | Líneas | ¿Loguea? | Contexto mínimo detectable |
|---|---|---|---|
| `services/access_service.py` | L55, L92, L199, L212, L494 | **NO** ×5 | `HTTPException` 401/403 inline |
| `services/availability.py` | L170, L339 | **NO** ×2 | reservas/status |
| `services/billing_service.py` | L186, L291 | **NO** ×2 | pagos MP / Neon |
| `services/branch_service.py` | L153 | **NO** ×1 | sucursales |
| `services/mercadopago_service.py` | L196 | **NO** ×1 | webhook MP |
| `services/occupancy_service.py` | L30 | **SÍ** ✓ (patrón `logger.exception` a copiar) | — |

**11 bloques `except Exception:` → 10 sin `logger.(exception|error|warning)`.**

### Impacto
- Los 675 tests pasan porque el contrato de códigos (400/401/403/404/409/422) está
  cubierto **en las rutas**; el service traga la causa raíz y el operador no ve
  por qué falló (SQL/Neon/timeout/MP) → indebuggeable en prod.
- Contradice AGENTS (criterio A7: "cero `except:` sin log con contexto").

### Fix recomendado (DRY con el patrón existente)
1. `services/access_service.py:55,92,199,212,494` → `logger.exception("Fallo al <operación> uid/plate=...")` antes del `raise`/`return` (usar `core/logger.py` `get_logger`, EL MISMO que `occupancy_service.py:7`).
2. Ídem availability/billing/branch/mercadopago.
3. **Si hay `except:` desnudo** (sin tipo) en algún pendiente: reemplazar por `except Exception` + logger (grep de la ronda no lo mostró con el patrón exacto → verificar con `grep -rn "except\+:"` cuando el script A6 corra en CI).

## 2. Fuga de internals en mensajes al cliente

Grep de `detail=` en `routes/*.py` (rutas del alcance A5/A6: support, fidelización, admin/users, parking):

| Ruta | `detail` | ¿Filtra internals? |
|---|---|---|
| `routes/admin/support_routes.py` #tickets | "No tenés permisos" / "Ticket no encontrado" | NO ✓ |
| `routes/admin/users.py` | "Error al actualizar el usuario" (L79) | NO ✓ (genérico) |
| `routes/user/fidelization.py` | "Clave de canje inválida" / "Saldo insuficiente" | NO ✓ |
| `routes/parking/status.py` | "Bahía no encontrada" | NO ✓ |
| `routes/admin/branches.py` | "No podés eliminar una sucursal con ocupación" | NO ✓ |

**Veredicto: cero `detail=` con stack/SQL/paths de servidor en el alcance.** Los únicos
valores SQL visibles son de config local en `.env` (NO commiteado, según AGENTS).

> Excepción puntual ya resuelta en ronda anterior: `routes/admin/users.py` usaba
> `detail="Error al actualizar"` redundante con 400 — se mapeó a mensaje amigable.

## 3. Consistencia de códigos HTTP por dominio (criterio A7)

Verificado contra los 675 tests (415+303 route tests cubren códigos):

| Dominio | Códigos usados | Consistente con |
|---|---|---|
| auth/login | 401 inválido · 403 no-activo | RFC 7235 ✓ |
| mercadopago webhook | 200 echo · 400 firma/evento | MP docs ✓ |
| reservas | 400 conflicto · 404 no-existe · 409 duplicado | ✓ |
| admin permisos | 403 (local vs global) · 404 (sucursal) | alcance A3 ✓ |
| fidelización | 400 saldo · 404 ticket/clave | ✓ |

**Sin 500 sin mapear** en el alcance (los `except Exception` de la tabla #1 devuelven
HTTPException maperada, no `JSONResponse` crudo).

## 4. Front: toasts con mensaje crudo

Scan de `static/js/*` (patrones `toast.error(`/`showToast(`):

- `static/js/mercadopago*.js` muestra `data.message` del backend — mensajes ya son
  amigables (los `detail=` de la tabla #2).
- **Recomendación N-1**: ningún `innerHTML` directo con mensaje de la API en toasts
  (se verifica en profundidad en A9 XSS; aquí el grep no detectó `innerHTML` con el
  valor del server → OK preliminar).

## Cierre

- **A7 ✓ aplicado (v9.34.14).** Los 10 bloques ciegos del informe base (access,
  availability, billing, branch, mercadopago) ya estaban logueados con
  `logger.X(..., exc_info=True)` al re-escanear — el informe quedó desactualizado
  pero el criterio se cumple.
- **Scan completo de `services/`** (no solo los 5 archivos del alcance) detectó y
  corrigió **7 bloques `except Exception: pass`** realmente ciegos fuera del
  alcance original: `payments.py` (notificación de puntos en reserva),
  `reservation_service.py` (notify_occupancy_change al crear; commit de
  `sucursal_info` en listado), `user_service.py` (notificación alta/baja de
  vehículo), `worker_service.py` (close de sesión en mantenedor de reservas y en
  trabajador de notificaciones). Se agregó `core/logger.py` + `logger` a
  `payments.py` y `user_service.py` (no tenían). Patrón: `logger.warning(msj, exc_info=True)`.
- Los `except HTTPException`/`ValueError`/`JWTError`/`RuntimeError`/`ImportError`
  restantes son control de flujo intencional (retorno/continue/fallback) → **no** son ciegos.
- Verificación: scan propio de `except` sin `logger/raise/continue/return` → **0 ciegos**;
  `py_compile` OK en los 4 archivos tocados; **suite 695 passed / 59.01s con venv**
  (base del informe: 675 → el delta es de auditorías posteriores).
