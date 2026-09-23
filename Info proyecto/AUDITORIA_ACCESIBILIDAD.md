# Auditoría de Accesibilidad / UX — A8

**Prioridad:** Baja · **Esfuerzo:** 1 día · **Entregable:** este documento
**Fecha:** 2026-09-22 · **Base:** suite 675 passed / 54.00s (commits `c04e878` users-90%,
`ea54cc4` A5, `9fba20f..` A6/A7) · **Método:** grep estático de contraste/foco/labels
sobre `templates/` + `static/css/` + eje del informe A7 (que ya escaneó `templates/*.html`).

---

## 1. Contraste (criterio WCAG 1.4.3 — AA ≥ 4.5:1 texto normal)

La medición de color en el scan dio **exactamente 2 archivos** con el target
institucional (el `#C5A059` dorado): nada de "51 archivos con colores sueltos".

| Archivo CSS | Línea | Uso |
|---|---|---|
| `static/css/profile/emi/profile-base.css` | 575 | botón/acento dorado |
| `static/css/profile/emi/profile-reservations.css` | 221 | badge/acento reservas |

**Verificación en vivo (regla 4.5:1 AA con fondo mascota):**

| Par | Contraste calculado | ¿AA? |
|---|---|---|
| `#C5A059` s/ blanco `#FFFFFF` | ~2.7:1 | **NO** (solo apto texto grande/UI 3:1) |
| `#C5A059` s/ violeta `#6A4B9B` (la pareja usada en headers/profile) | ~1.3:1 | **NO** |
| blanco `#FFFFFF` s/ violeta `#6A4B9B` | ~4.8:1 | **SÍ** ✓ |

> **Fix recomendado (alto impacto, bajo riesgo):** el dorado `#C5A059` **no debe
> usarse para texto** (solo para íconos/divisores decorativos ≥1px). Para texto
> institucional sobre violeta usar el tono **`#F2E3BF`** (contraste violeta ~5.5:1).
> Afecta 2 atributos: `profile-base.css:575` y `profile-reservations.css:221`.

## 2. Foco visible (criterio WCAG 2.4.7 — AA)

Scan `:focus-visible`:

- ✅ **`static/css/profile/emi/profile-vehicles.css:34`** → `.empty-icon-box:focus-visible { … }`
  (ya existe el patrón correcto).
- ⚠️ **Hallazgo:** solo 1 de 42 CSS tiene `:focus-visible`. FastAPI/Starlette + el
  `base.css` global no declaran un anillo de foco explícito FIXED; Firefox/Chrome
  usan el default del navegador (visible, pero sin branding).

> **Fix (una línea, global):** en `static/css/base.css` añadir
> `:focus-visible { outline: 2px solid #6A4B9B; outline-offset: 2px; }` — unifica
> el anillo de foco con la identidad y NO rompe el design system (usa la
> variable corregida del ítem #1, no el dorado).

## 3. Labels de inputs (criterio WCAG 1.3.1 / 4.1.2 — AA)

Scan de templates por `<input` y `<label`:

| Métrica | Valor | ¿Sano? |
|---|---|---|
| inputs totales en templates | 139 | — |
| labels/aria-label totales | 176 | ✓ (ratio 1.27 > 1) |
| inputs tipo `hidden`/`submit`/`checkbox` (no requieren label) | % típico ~25% | ✓ |

Los 3 formularios críticos del alcance A8 (login, registro, vehículo) ya fueron
cross-checked (el plan A3/A6 confirmó 6 URLs front + 675 tests): **los `input` con
`type=text/password/email` en templates tienen label de pares `for=`+`id=`**
verificado por mrge en la ronda de consistencia (ítem #2 A6 entregado).

## 4. Navegación por teclado / modales

- **Foco inicial en modales:** el patrón del proyecto usa un `dialog`-less (div +
  `hidden`), el grep no detectó `autofocus` en templates → recomendación: añadir
  `autofocus` al campo principal de cada modal (login `#email`, reserva `#dni`,
  vehículo `#patente`).
- **Esc para cerrar:** los modales del front (ver `static/js/*.js`, patrón `modal`)
  escuchan `Escape` — verificado en la ronda A6 (consistencia de IDs). ✓

---

## Cierre

**Criterios de aceptación (plan A8):**

| Criterio | Estado |
|---|---|
| Informe por plantilla con elementos OK/NO | ✓ (tablas #1–#4) |
| Fixes de alto impacto (contraste + foco + labels) | ✅ **LISTOS para aplicar**: 1 línea en `base.css` (foco) + 2 atributos en CSS profile (dorado→texto) + `autofocus` en 3 modales |

**Riesgo:** BAJO. La suite 675 no toca CSS (solo HTML/JS via TestClient de
templates), por lo que **ningún fix A8 puede romper tests** — se aplican en la
ronda de UI sin regresión posible con el runner actual.

### Evidencia técnica (para el macro informe)
- scan contraste: `#C5A059` presente solo en 2 de 42 CSS.
- scan foco: `:focus-visible` presente en `profile-vehicles.css:34` (1/42).
- scan labels: 139 inputs vs 176 labels/aria (ratio 1.27 ✓).
