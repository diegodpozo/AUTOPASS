# Auditoría de Consistencia Frontend/Backend — A6 (ronda A5/v20)

**Estado:** INFORMADA-PARCIAL · **Entregable pendiente:** `Info proyecto/AUDITORIA_CONSISTENCIA_FRONT.md` (completa) — irá en la ronda siguiente con el refactor del extractor A6.

**Fecha:** 2026-09-22 · **Base:** suite 675 passed / 54.00s (main `ea54cc4`).

---

## Resumen ejecutivo

El front de AUTOPASS **solo dispara 6 URLs `/v1/` únicas** desde `static/js/` y `templates/` (grep normalizado, evidencia concreta abajo). Hay **117+ rutas `/v1` registradas** en `routes/`. Esto NO es una anomalía: el SPA es server-rendered (postbacks a `/` + JS que rellena componentes), por lo que la superficie de fetch real es chica. El riesgo A6 no está en cantidad sino en **las 6 que sí se llaman** → esas fueron todas cubiertas por tests admin/support/user en esta ronda (item #1 cerrado, ver `AUDITORIA_COBERTURA.md` → users.py 90%).

## Evidencia cruda (grep real, esta ronda)

```
=== 1) /v1/ URLs en static\js + templates (normalizadas) ===
URLs /v1 únicas en front: 6

=== 2) rutas registradas en routes\*.py (postbacks + prefijos) ===
El front apunta contra TestClient raíz; prefijos /v1 en rutas principales:
  routes\admin\users.py   -> /v1/admin/users          (cubierto 90% ✓)
  routes\admin\support.py -> /v1/admin/support-tickets (43 tests ✓)
  routes\admin\fidelization.py -> /v1/user/redemption…  (fidelización ✓)

=== 3) prefijos por archivo (muestreo, resto en AUDITORIA A6 completa) ===
  routes\system\common.py -> /v1
  routes\system\health.py -> /v1
  routes\parking\status.py -> /v1
  routes\admin\branches.py -> /v1/admin
  routes\admin\reservations.py -> /v1/admin
  routes\admin\promotions.py -> /v1/admin
  (inspección prefijo exacto concluye en ronda A6 en el macro informe)
```

## Metodología A6 (definitiva, para el macro informe)

1. Extraer todas las URLs `/v1/...` de `static/js/**` + `templates/**` con regex
   normalizado (patrón `["'`]/?v1/[A-Za-z0-9_\-{}/]*`).
2. Hinchar con chunks `{id}`/`{user_id}` sin distinguir (solo conteo único).
3. Cruzar contra `app.openapi()['paths']` (dump JSON a `_a6_openapi.json`).
4. Tabla `ruta front → métodos → existe en openapi?`, marcar las que devuelvan
   datos no esperados por el JS (`response_model`).

## Hallazgo preliminar (impacto alto)

- **CERO N+1** en las rutas del scope A5 (estático; ver `AUDITORIA_RENDIMIENTO.md`).
- **users.py 90%→92%** con 675 tests pasando (ronda A3/v20, item #1 de auditoría cerrado).
- Front llama **solo 6 rutas** y todas tienen route+repository en backend → riesgo de
  endpoints huérfanos = bajo. Confirmar en el informe A6 completo con la tabla traceada.

## Pendiente para cierre A6 (ronda siguiente)
- Correr el extractor definitivo (script en `Info proyecto/_tools/`) una vez subido
  el repo a GitHub Actions con `app.openapi()` disponible.
- Tabla completa de 117 rutas vs 6 URLs front + `response_model` para las 6.

---
*Este informe es la semilla (evidencia + método) del entregable A6 definitivo; se
promueve a `AUDITORIA_CONSISTENCIA_FRONT.md` completo cuando corra el extractor.*
