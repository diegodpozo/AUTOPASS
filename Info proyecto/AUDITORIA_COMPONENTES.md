# Auditoría de Componentes y Reutilización — AUTOPASS

> **Fecha:** 2026-09-24
> **Versión auditada:** v9.34.0 (rama `main`, incluye remediación UX/UI P1–P3)
> **Alcance:** Inventario y grado de reutilización de componentes en `templates/`, `static/css/components/` y módulos JS con rol de componente (`ui.js`, `api.js`, `utils.js`, `chart_window.js`, skeleton). Foco: **DRY de marcado y estilos** (mandato de `AGENTS.md`). No audita funcionalidad ni seguridad.
> **Metodología:** conteo estático de `{% include %}`, inventario de partials/CSS, medición de estilos inline por template (`style="…"`), detección de bloques duplicados y verificación de extracciones recientes (skeleton, BEM, `section-title-premium--center`).

---

## 1. Resumen Ejecutivo

| Dimensión | Estado | Evidencia |
|---|---|---|
| Componentes de página (`templates/components/`) | 🟢 Sólido | 8 partials: `navbar`, `footer`, `auth_modals`, `sidebar_user`, `modals_global`, `virtual_time_banner`, `monitoreo_controls`, `chart_window_controls` |
| Modales compartidos | 🟢 Sólido | 6 packs reutilizados por tab/área (`onboarding_modal`, `profile/modals`, `branch_modals`, `promotion_modal`, `user_modals`, `admin_help_modal`) |
| CSS componentizado (`static/css/components/`) | 🟢 Sólido | 10 archivos (buttons, cards, forms, tables, badges, modals, chart_window, footer, virtual_time, skeleton) |
| JS como componente reutilizable | 🟢 Sólido | `ui.js` (modales únicos), `api.js` (único cliente HTTP), `utils.js` (formateadores/toasts), `chart_window.js` (`WindowedChart`), virtual-time |
| Reutilización real de partials | 🟢 Alto | 46 `{% include %}`. `navbar`+`footer`+`auth_modals` usados en 5 páginas públicas; `sidebar_user` en portal; 9 tabs en dashboard; 7 tabs en perfil |
| Estilos inline por template | 🟡 Deuda | `inicio.html` 83, `admin_reservations.html` 59, `metricas.html` 48, `live.html` 46, `estadisticas_ocr.html` 43 |
| Botones (BEM vs legacy) | 🟡 En transición | BEM `.btn--*` agrupado con legacy (v9.34.0); faltan migrar usos en templates |

**Puntaje de salud: 8.5 / 10** — La arquitectura de partials y la componente CSS está muy por encima de la media, pero queda deuda de estilos inline (hasta 83 por archivo) y la migración BEM está a mitad de camino.

---

## 2. Inventario de Componentes

### 2.1 Partial de templates (`templates/components/`)

| Componente | Consumidores |
|---|---|
| `navbar.html` | index, contacto, nuestra-red, privacidad, terminos → **5** |
| `footer.html` | index, contacto, nuestra-red, privacidad, terminos → **5** |
| `auth_modals.html` | index, contacto, nuestra-red, privacidad, terminos → **5** |
| `sidebar_user.html` | perfil → **1** (7 tabs internos) |
| `modals_global.html` | base.html → global |
| `virtual_time_banner.html` | base.html → global |
| `monitoreo_controls.html` | monitoreo_live → **1** |
| `chart_window_controls.html` | estadisticas_ocr → **1** |

### 2.2 Modales (`templates/profile/modals/`, `templates/dashboard/modals/`)

| Partial | Consumidor |
|---|---|
| `profile/modals/onboarding_modal.html` | `profile/tabs/inicio.html` |
| `profile/modals.html` | `perfil.html` (global del portal) |
| `dashboard/modals/admin_help_modal.html` | `dashboard.html` |
| `dashboard/modals/branch_modals.html` | tab branches |
| `dashboard/modals/promotion_modal.html` | tab promotions |
| `dashboard/modals/user_modals.html` | tab users |

### 2.3 CSS (`static/css/components/`)

`buttons.css`, `cards.css`, `forms.css`, `tables.css`, `badges.css`, `modals.css`, `chart_window.css`, `footer.css`, `virtual_time.css`, `skeleton.css` (v9.34.0), `premium.css` (v9.34.0).

`skeleton.css` es el caso modelo de reutilización reciente: **1 definición, 9 consumidores** (6 tablas admin + cards/historial del cliente + grid de reservas). `premium.css` consolida las primitivas del portal (acciones rápidas, estado vacío) que estaban dispersas en CSS de página.

**Entrega de CSS (v9.34.x):** los 3 orquestadores con `@import` (`landing.css`, `dashboard.css`, `profile.css`) fueron reemplazados por partials Jinja (`components/css_landing|css_dashboard|css_profile.html`) cuyos `<link>` llevan `?v={{ cache_buster }}` (timestamp por restart del server) → busteo automático sin versionar a mano cada hoja + descarga en paralelo.

### 2.4 Módulos JS con rol de componente

| Módulo | Rol | Reutilizado por |
|---|---|---|
| `ui.js` | openModal/closeModal/switchModal/toasts | puentes perfil, dashboard, main, auth |
| `api.js` | único cliente HTTP | todos los módulos |
| `utils.js` | formateadores + showToast | todos los módulos |
| `chart_window.js` | `WindowedChart` (gráfico) | dashboards de métricas |
| `virtual-time.js` | hora virtual | dashboard y monitoreo |

Jaula: **0 asignaciones `window.*` en módulos** (mandato Bridge, A2) — los componentes se consumen por import y se exponen solo en puentes.

---

## 3. Índice de Reutilización

Regla empírica aplicada: un componente de página debe tener **≥ 2 consumidores** para justificar ser partial. Estado:

- **5 partials con 5 consumidores** (navbar, footer, auth_modals) → excelente.
- **6 tablas admin** renderizadas por los mismos patrones (`.btn-action-mini`, `.badge-status`, `skeleton-cells`) → consistente.
- **`tabs/` y `tabs/settings/`** como composición: `dashboard.html` ensambla 9 tabs + `settings.html` ensambla 4 sub-tabs; `perfil.html` ensambla 7 tabs. Patrón compuesto → correcto.

---

## 4. Hallazgos

### 4.1 Estilos inline residuales (deuda principal)

Conteo de `style="…"` por template (top 12):

| Template | Inline |
|---|:---:|
| `profile/tabs/inicio.html` | 83 |
| `dashboard/tabs/admin_reservations.html` | 59 |
| `dashboard/tabs/metricas.html` | 48 |
| `dashboard/tabs/live.html` | 46 |
| `estadisticas_ocr.html` | 43 |
| `dashboard/modals/user_modals.html` | 33 |
| `emails/reservation_confirmation.html` | 30 (aceptable: emails inline obligatorio) |
| `dashboard/modals/branch_modals.html` | 29 |
| `profile/modals.html` | 27 |
| `profile/tabs/vehiculos.html` | 23 |
| `dashboard/tabs/finance.html` | ~15 |
| `dashboard.html` | 11 |

Los bloques repetidos con mayor costo de extracción:

- **Título de panel/modal en dorado** (`<h3 style="color: var(--dorado);">`): duplicado en **9 sitios** (dashboard `DETALLE DE RESERVA`, tabs SUCURSALES/PROMOCIONES/NUEVA RESERVA MANUAL, modales de sucursal x2/promoción/cámara y banner RELOJ VIRTUAL). **Extraído a la utilidad `.text-dorado` (v9.34.0)**.
- **Título de sección premium** (h3 + línea dorada + centrado): solo existe en `inicio.html` (2 usos, ya componente `.section-title-premium--center` en v9.34.0). No está duplicado en otras tabs — estas usan patrones propios (`welcome-card h1`, `help-hero-title`, `hub-section-title`).
- **`empty-state-premium`** y **`action-btn-premium`**: cada uno con 1–2 usos en `inicio.html`, pero sus estilos vivían en `profile-vehicles.css` / `profile-base.css` (páginas de perfil) creando una **dependencia cruzada de archivo** (un partial consumido fuera de su css de origen). **Consolidados en `components/premium.css` (v9.34.0)** para reutilización app-wide.

### 4.2 Migración BEM de botones (en transición)

`buttons.css` agrupa `.btn--primary/--outline/--premium/--sm/--full/--icon/--mini` con los selectores legacy (v9.34.0). Usos migrados: auth_modals (login, register, recovery, OAuth complete) e onboarding. **Pendiente:** usos restantes en templates (grep `class="btn btn-primary` etc.).

### 4.3 Coincidencias positivas (no romper)

- `ui.js` es el único dueño de la apertura/cierre de modales; ningún template redefine lógica de modal.
- `showToast`/formatadores centralizados en `utils.js`; sin duplicación de toasts/formatos.
- `skeleton.css` (v9.34.0) cumple el mandato DRY con 9 consumidores.
- Modales de admin por dominio (branch/promotion/user) evitan un "mega-modal" monolítico.

---

## 5. Recomendaciones Priorizadas

#### P1 — Unificar el título de panel/modal dorado
~~Reemplazar los `h3 style="color: var(--dorado);"` inline~~ — **[HECHO v9.34.0]:** 9 títulos migrados a la utilidad `.text-dorado` (dashboard, tabs, modales de sucursal/promoción/cámara y banner RELOJ VIRTUAL).

#### P1 — Consolidar las primitivas premium del portal
~~Mover `quick-actions-grid`/`action-btn-premium` y `empty-state-premium` a `components/`~~ — **[HECHO v9.34.0]:** creado `static/css/components/premium.css` (acciones rápidas + estado vacío) incluido en `base.html`; se eliminó la dependencia cruzada con `profile-vehicles.css`/`profile-base.css`.

#### P1 — Adelgazar los tablas del dashboard
~~`admin_reservations.html` (59) y `metricas.html` (48)~~ — **[HECHO v9.34.2]:** los patrones repetidos se extrajeron a componentes reutilizables: `.card--flush`/`.card-body` (cards.css), `.modal-close-top--inline` (modals.css), `.dynamic-row-premium--period`, `.input-premium--plain` y `.input-premium.flatpickr-input` (forms.css), `.metrica-card-icon--violet`, `.metrica-sub`, `.toolbar-label`, `.input-premium-sm` dentro de toolbar (dashboard-metrics.css). Resultado: admin 59→44, metricas 46→32 (29 estilos inline eliminados + 9 `max-width:180px` redundantes que eran el default de `.form-group-premium`).

#### P2 — Completar la migración BEM
~~Barrido `class="btn btn-primary…"` → `btn btn--primary…`~~ — **[HECHO v9.34.6]:** paso 1 (v9.34.5): 28 templates + 4 JS migrados con regex de límites de palabra (protege `vt-btn-full`). Paso 2 (v9.34.6): selectores legacy retirados de buttons.css (`.btn-primary/outline/premium/sm/full` y `.btn-outline.btn-danger` → `.btn--outline.btn--danger`), profile-base (`.btn--primary.btn--compact`), dashboard-base (`.header-actions .btn--premium`) y profile-tour. **[HECHO v9.34.17 — tokens residuales]:** `btn-icon-premium` (incl. variantes `sm`/`sm danger`/`sm warning`) migrado a `btn--icon`, y `btn-action-mini` (`success`/`danger`) a `btn--mini` en **8 usos de templates** (finance, users, live) + **23 usos en 6 módulos JS** (branches-crud, branches-floors, admin-users, promotions, dashboard-stats, reservations-admin-list). Selectores legacy retirados de buttons.css (`.btn-icon-premium`, `.btn-action-mini`, `.btn-warning`) y de tables.css/dashboard-tables.css (ajustado a `.btn--icon.sm(.danger)`); variantes `.btn--mini--success/--danger` (sin uso) eliminadas. **Solo BEM en producción; 0 residuales legacy** (grep templates/JS/CSS), `node --check` ×6, suite 695 passed / 52.38s.

#### P3 — Guard de CI contra inline
~~Script que falla si un template supera N `style="…"` (umbral sugerido 25, emails exceptuados)~~ — **[HECHO v9.34.4]:** `_tools/check_inline_styles.py` con baseline (`_tools/inline_styles_baseline.json`, 50 templates). Modo CI: falla si un template existente supera su conteo previo (regresión) o si un template nuevo supera el umbral 25; emails exceptuados. `--update` regenera el baseline tras limpiezas. Integrado a la suite como `tests/test_inline_styles_guard.py` (695 passed).

---

## 6. Conclusión

El proyecto ya tiene una **base de componentes sólida**: partials de página compartidos (5 consumidores), tabla de estilos componente (10 archivos), modales por dominio, patrones JS puente y una extracción reciente muy exitosa (`skeleton.css` con 9 reutilizaciones). La deuda se concentra en **estilos inline** de los templates más densos (inicio y tablas admin) y en terminar la **migración BEM**. Sin cambios estructurales; son extracciones locales de marcado con beneficio directo de consistencia.

---

## 7. Anexo — Evidencia

- Conteo de `{% include %}`: 46 resultados en `templates/` (grep `\{% include "`).
- Conteo de inline: `([regex]::Matches($c,'style="')).Count` por archivo .html (top 12 en §4.1).
- Inventario: `templates/components/` (8 archivos), `static/css/components/` (10 archivos).
- Validado contra `ARQUITECTURA_DETALLADA.md` (v9.14.1+): coincide el inventario de partials y CSS; este documento agrega el índice de reutilización cuantitativo.