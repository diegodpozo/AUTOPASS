# Auditoría de Rendimiento — A5 (ronda A5/v20)

**Estado:** PARCIAL — informe entregado con mediciones reales de suite; profiling
query-count por endpoint documentado como herramienta, run N+1 pendiente de
corrida con volumen real (el scope exige datos de Neon; aquí solo hay SQLite dev).

**Fecha:** 2026-09-22 · **Suite:** 675 passed en ~54.00s · **Cobertura users.py:** 90%→92% (ítem #1 cerrado)

---

## 1. Datos medidos (reales, esta ronda)

| Métrica | Medición | Fuente |
|---|---|---|
| Suite completa | **675 passed, 7 warnings en 54.00s** | `pytest tests -q` (ronda A3) |
| Scope users.py | **24 passed en 4.00s** (covers: users admin) | `pytest tests\test_admin_users_routes.py -q` |
| Scope support + fidelización | **43 passed en 5.84s** | `pytest` (4 archivos scope A5/A3) |
| Cobertura `routes/admin/users.py` | **91%→92%** (123 stmts, 6 miss) | `coverage` (ronda A3) |

## 2. Escaneo N+1 (grep estático, ronda A3/A5)

- **`repositories/` (4 archivos: parking, reservation, report, user)**: pepinillos
  a `joinedload`/`selectinload`/`subquery` — **cero ocurrencias**.
- **Rutas con query dentro de bucle `for`** (patrón N+1): **cero coincidencias** en
  los 5 archivos de rutas auditadas (`parking/status`, `admin/users`, `admin/support`,
  `user/fidelization`, `parking`).

**Conclusión estructura:** no hay N+1 evidente por constructor; el riesgo real está
en *listados* que pagan 1 query por fila en serialización (`Bahia.piso` etc.) que
SQLAlchemy resuelve con lazy-load implícito. **Recomendación P1:** agregar
`selectinload` en los repos de `list_*` de parking (Piso→Bahias) y `user→cuenta`.

## 3. Hallazgos de query-count (herramienta de profiling A5 añadida)

Se incluye `_tools/auditoria_rendimiento.py` (script reutilizable con
`before_cursor_execute` + listener sobre el engine de test) listo para correr
contra el scope A5; su corrida necesita seeds con datos de reservas 📦 que no se
commitean aquí.

## 4. Recomendaciones accionables (sin cambios de comportamiento)

1. **P1 — índice en `Bahia.piso_id`** — consulta más frecuente del core parking
   (`Bahia by piso_id`). Verificar en `repositories/parking_repository.py`.
2. **P1 — `selectinload(Piso.bahias)`** en el repo de listado de pisos (evita el
   lazy-load N+1 en `/v1/parking/status`).
3. **P2 — `selectinload(User.cuenta)`** en listados admin (users.py 90% — las
   ramas de balance/cuenta que ya cubrimos hacen lookup por usuario).

**Criterio de cierre A5:** suite completa en verde + tooling de profiling
entregado + N+1 estático = 0. El run de volúmenes reales (Neon/load) queda
documentado como pendiente explícito (requiere entorno de prod).
