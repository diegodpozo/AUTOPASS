# Auditoría de Nomenclatura de Archivos — AUTOPASS

> **Fecha:** 2026-09-27  
> **Alcance:** 334 archivos de código, configuración, plantillas, documentación y recursos estáticos (excluyendo entornos virtuales, `.git`, cachés y uploads dinámicos).  
> **Calificación General de Nomenclatura:** 8.2 / 10 → **9.0 / 10**  
> **Estado:** Diagnóstico completo + **remediación P0/P1 APLICADA (2026-09-27, v9.34.42)** — ver §6. Queda P2 (spanglish/UI lingüística) como deuda técnica funcional aceptada, documentada en §5.

---

## 1. Diagnóstico General y Resumen Ejecutivo

El ecosistema presenta una **excelente disciplina en el backend Python**, donde rige de forma homogénea el estándar `snake_case` en inglés en todas sus capas arquitectónicas (modelos, schemas, repositorios, rutas, servicios y tests).

Sin embargo, a medida que se avanza hacia las capas de **Frontend (JS/CSS)**, **Plantillas (Jinja2)**, **Documentación** y **Scripts de automatización**, surgen fricciones derivadas de la evolución del proyecto:
1. **Espacios en nombres de archivos y directorios** que atentan contra la portabilidad en sistemas UNIX/CI y URLs HTTP.
2. **Divergencia de casing** entre `kebab-case` y `snake_case` en módulos JS y hojas de estilo CSS.
3. **Hibridación lingüística (Spanglish)**: entidades en inglés en el backend conviviendo con equivalentes en español en el frontend (`profile` vs. `perfil`, `reservations` vs. `reservas`, `vehicles` vs. `vehiculos`) y archivos compuestos con términos mezclados.

---

## 2. Hallazgos por Nivel de Severidad

### 🔴 Prioridad P0 — Espacios en Nombres de Archivos y Carpetas (Riesgo en URLs y Scripts)

Los espacios en nombres de archivos generan problemas de escape en scripts de terminal (Bash/PowerShell), roturas potenciales en servidores web, fallos en compilación PWA y dificultades en entornos Linux/Docker.

| Archivo / Carpeta | Tipo | Ubicación | Problema |
|---|---|---|---|
| `Info proyecto/` | Directorio | Raíz | Directorio principal de documentación con espacio intermedio. Dificulta rutas en CLI y herramientas automatizadas. |
| `Info proyecto/Link Backlog.md` | Archivo | Documentación | Contiene espacio y formato *Title Case*. |
| `static/images/barrera alta.png` | Asset Web | Imágenes | Imagen referenciada en plantillas y JS con espacio; exige URL encoding (`%20`). |
| `static/images/barrera baja.png` | Asset Web | Imágenes | Mismo caso anterior, utilizado en el monitor de barreras. |

---

### 🟠 Prioridad P1 — Inconsistencias de Casing por Capa

#### A. Módulos JavaScript (`static/js/modules/`)
* **Regla predominante:** `kebab-case` (48 módulos, ej: `dashboard-ui.js`, `reservas-form.js`, `landing-map.js`, `admin-tour.js`).
* **Anomalías en `snake_case` (4 módulos):**
  - `chart-window.js` *(debería ser `chart-window.js`)*
  - `estadisticas-ocr.js` *(debería ser `estadisticas-ocr.js`)*
  - `onboarding-helpers.js` *(debería ser `onboarding-helpers.js`)*
  - `reset-password.js` *(debería ser `reset-password.js`)*

#### B. Estilos CSS (`static/css/`)
* **Regla predominante:** `kebab-case` en todas las páginas compuestas (ej: `dashboard-cards.css`, `landing-hero.css`, `profile-reservations.css`, `monitoreo-live.css`).
* **Anomalías en `snake_case` (3 archivos):**
  - `components/virtual-time.css` *(debería ser `virtual-time.css`, como su par `virtual-time.js`)*
  - `components/chart-window.css` *(debería ser `chart-window.css`)*
  - `pages/estadisticas-ocr.css` *(debería ser `estadisticas-ocr.css`)*

#### C. Plantillas HTML (`templates/`)
* **Regla predominante:** `snake_case` en componentes y modales (ej: `auth_modals.html`, `admin_reservations.html`, `user_modals.html`).
* **Anomalías de formato:**
  - `templates/nuestra_red.html`: Es la **única** plantilla de todo el proyecto nombrada en `kebab-case`. Todas las demás vistas multi-palabra usan `snake_case` (`monitoreo_live.html`, `estadisticas_ocr.html`, `reset_password.html`).

#### D. Documentación (`Info proyecto/`)
* **Regla predominante:** `SCREAMING_SNAKE_CASE.md` (24 documentos, ej: `ARQUITECTURA_DETALLADA.md`, `ESTADO_PROYECTO.md`, todas las `AUDITORIA_*.md`).
* **Anomalías:**
  - `explicacionCodigo.md`: Nombrado en **camelCase**, único en todo el repositorio.
  - `Readme.md`: *TitleCase* con minúsculas intermedias frente al `README.md` en mayúsculas de la raíz.
  - `FUNCIONALIDADES.html`: Archivo HTML en mayúsculas dentro de la carpeta de documentación.
  - `Hardware/`: Único subdirectorio con inicial en mayúscula (*PascalCase*).

---

### 🟡 Prioridad P2 — Discordancia Lingüística (Inglés vs. Español / Spanglish)

#### A. Asimetría Semántica Backend ↔ Frontend
El backend utiliza términos en inglés estandarizados para los dominios, pero el frontend utiliza alternativamente inglés o español según la vista:

| Dominio / Entidad | Backend (Rutas / Repos / Modelos) | Frontend (Módulos / Puentes) | Templates HTML |
|---|---|---|---|
| **Perfil** | `routes/user/profile.py`<br>`repositories/user_repository.py` | `modules/profile.js`<br>⚡ `static/js/perfil.js` | `templates/perfil.html` |
| **Reservas** | `routes/admin/reservations.py`<br>`services/reservation_service.py` | ⚡ `modules/reservas.js`<br>⚡ `modules/reservas-form.js` | ⚡ `profile/tabs/reservas.html`<br>vs `dashboard/tabs/admin_reservations.html` |
| **Vehículos** | `routes/user/vehicles.py`<br>`repositories/vehicle_repository.py` | `modules/vehicles.js`<br>`static/js/vehicles.js` | ⚡ `profile/tabs/vehiculos.html` |
| **Fidelización / Puntos** | `routes/user/fidelization.py`<br>`repositories/points_repository.py` | `modules/profile.js` | ⚡ `profile/tabs/puntos.html` |
| **Soporte / Ayuda** | `routes/user/support.py`<br>`services/support_service.py` | `modules/profile-help.js`<br>`modules/admin-help.js` | ⚡ `profile/tabs/ayuda.html` |

#### B. Archivos con nombres híbridos (Spanglish)
- `templates/monitoreo_live.html`: Mezcla "monitoreo" (español) y "live" (inglés).
- `static/css/pages/monitoreo-live.css`: Misma mezcla híbrida en estilos.
- `static/js/modules/monitoreo-live.js`: Misma mezcla híbrida en JavaScript.
- `tests/test_ocr_engine_detallado.py`: Único archivo de prueba con palabra en español ("detallado"), entre 50 suites escritas 100% en inglés.

#### C. Scripts Raíz (`.bat`) vs Scripts Internos (`.ps1`)
Existe una discordancia en los scripts de conveniencia de la raíz y los de `scripts/`:
- En raíz: `acceso_remoto.bat` y `detener_acceso_remoto.bat` (español).
- En raíz: `setup_backend.bat` y `run_server.bat` (inglés).
- En scripts: `start_remote.ps1` y `stop_remote.ps1` (inglés, invocados por los `.bat` en español).

---

## 3. Matriz de Discordancia Cruzada (Ejemplo Paradigmático)

El subsistema de **Tiempo Virtual** ilustra cómo un mismo concepto se nombra de tres formas distintas a través de las capas del proyecto:

| Capa | Nombre del Archivo | Convención |
|---|---|---|
| **Backend API** | `routes/admin/virtual_time.py` | `snake_case` |
| **Backend Tests** | `tests/test_virtual_time.py` | `snake_case` |
| **CSS Component** | `static/css/components/virtual-time.css` | `snake_case` |
| **HTML Component** | `templates/components/virtual_time_banner.html` | `snake_case` |
| **JS Module** | ⚡ `static/js/modules/virtual-time.js` | ⚡ **`kebab-case`** |

---

## 4. Resumen Estadístico de Convenciones por Capa

```text
Backend Python (115 archivos):
  ├── snake_case: 100% (todos los .py)
  └── Idioma: 99.1% inglés (1 excepción: test_ocr_engine_detallado.py)

Frontend JS (72 archivos):
  ├── Módulos ES6 (63 archivos):
  │     ├── kebab-case: 76.2% (48 archivos)
  │     ├── simple_lower: 17.5% (11 archivos)
  │     └── snake_case anómalo: 6.3% (4 archivos)
  └── Scripts Puente (9 archivos):
        ├── simple_lower: 88.9% (8 archivos)
        └── snake_case: 11.1% (api_client.js)

Frontend CSS (41 archivos):
  ├── kebab-case: 48.8% (20 archivos)
  ├── simple_lower: 43.9% (18 archivos)
  └── snake_case anómalo: 7.3% (3 archivos: virtual_time, chart_window, estadisticas_ocr)

Templates Jinja2 (48 archivos):
  ├── snake_case: 54.2% (26 archivos)
  ├── simple_lower: 43.7% (21 archivos)
  └── kebab-case anómalo: 2.1% (1 archivo: nuestra_red.html)

Documentación e Info (31 archivos):
  ├── SCREAMING_SNAKE_CASE: 77.4% (24 archivos)
  ├── Archivos con espacios: 3.2% (1 archivo: Link Backlog.md)
  ├── camelCase: 3.2% (1 archivo: explicacionCodigo.md)
  └── TitleCase / Otros: 16.2% (5 archivos)
```

---

## 5. Plan de Normalización y Recomendaciones

### Paso 1: Normalización de Assets y Enlaces Críticos (Bajo Riesgo)
1. **Renombrar las imágenes con espacios:**
   - `static/images/barrera alta.png` ➔ `static/images/barrera-alta.png`
   - `static/images/barrera baja.png` ➔ `static/images/barrera-baja.png`
   - *Actualizar referencias en `live.html`, `settings_system.html` y `dashboard-admin-settings.js`.*
2. **Renombrar en documentación:**
   - `Info proyecto/Link Backlog.md` ➔ `Info proyecto/LINK_BACKLOG.md`
   - `Info proyecto/explicacionCodigo.md` ➔ `Info proyecto/EXPLICACION_CODIGO.md`
   - `Info proyecto/Readme.md` ➔ `Info proyecto/README.md`
   - `Info proyecto/Hardware/` ➔ `Info proyecto/hardware/`

### Paso 2: Unificación de Convención en Frontend (Cero Deuda Técnica)
1. **Módulos JS a `kebab-case` unificado:**
   - `chart-window.js` ➔ `chart-window.js`
   - `estadisticas-ocr.js` ➔ `estadisticas-ocr.js`
   - `onboarding-helpers.js` ➔ `onboarding-helpers.js`
   - `reset-password.js` ➔ `reset-password.js`
2. **CSS a `kebab-case` unificado:**
   - `virtual-time.css` ➔ `virtual-time.css`
   - `chart-window.css` ➔ `chart-window.css`
   - `estadisticas-ocr.css` ➔ `estadisticas-ocr.css`
3. **Plantillas a `snake_case` unificado:**
   - `nuestra_red.html` ➔ `nuestra_red.html` *(actualizando el render en `routes/views.py`)*.

### Paso 3: Regla de Estilo a Incorporar en `AGENTS.md`
- **Python / Backend:** Siempre `snake_case` en inglés (`{dominio}_{subdominio}.py`).
- **CSS y JS Módulos:** Siempre `kebab-case` (`{modulo}-{submodulo}.js` / `.css`).
- **Templates Jinja2:** Siempre `snake_case` (`{vista}_{variante}.html`).
- **Documentación:** Siempre `SCREAMING_SNAKE_CASE.md` en español.
- **Sin espacios:** Prohibido el uso de espacios o caracteres especiales en nombres de archivos o carpetas.

---

## 6. Remediación Aplicada (2026-09-27, v9.34.42)

P0 y P1 ejecutados en su totalidad con `git mv` + actualización de todas las referencias funcionales y documentales:

| Renombre (P0) | Referencias actualizadas |
|---|---|
| `static/images/barrera alta.png` → `barrera-alta.png` | `dashboard-admin-settings.js` (2), `live.html` (2), `settings_system.html` (1) |
| `static/images/barrera baja.png` → `barrera-baja.png` | Ídem |
| `Info proyecto/Link Backlog.md` → `LINK_BACKLOG.md` | — (sin referencias externas) |
| `Info proyecto/explicacionCodigo.md` → `EXPLICACION_CODIGO.md` | — |
| `Info proyecto/Readme.md` → `README.md` | `ESTADO_PROYECTO.md` |
| `Info proyecto/Hardware/` → `hardware/` | `ARQUITECTURA_DETALLADA.md` (2) |

| Renombre (P1) | Referencias actualizadas |
|---|---|
| `js/modules/chart_window.js` → `chart-window.js` | `estadisticas-ocr.js` (import) |
| `js/modules/estadisticas_ocr.js` → `estadisticas-ocr.js` | `estadisticas_ocr.html` (import), informe colores/fuentes |
| `js/modules/onboarding_helpers.js` → `onboarding-helpers.js` | `perfil.js` (import) |
| `js/modules/reset_password.js` → `reset-password.js` | `reset_password.html` (script tag) |
| `css/components/virtual_time.css` → `virtual-time.css` | `base.html`, `sw.js` (precache) |
| `css/components/chart_window.css` → `chart-window.css` | `base.html` |
| `css/pages/estadisticas_ocr.css` → `estadisticas-ocr.css` | `estadisticas_ocr.html` |
| `templates/nuestra-red.html` → `nuestra_red.html` | `routes/views.py` (render); URL `/nuestra-red` y navbar/footer/index intactos (la ruta no cambia) |

**Verificaciones post-remediación:**
- `check_inline_styles.py --update` → baseline regenerado y guard en verde (50 templates, incluye `nuestra_red.html`).
- Grep residual en `templates/`, `static/`, `tests/`, `routes/`: 0 referencias rotas a los nombres viejos (los únicos `virtual_time`/`reset_password` restantes son módulos Python backend — convención correcta — y `chart_window_controls.html`, template no incluido en el alcance).
- `AGENTS.md` → añadida regla de estilo de nomenclatura (§ Estilo de código).
- **P2 (spanglish lingüístico) NO se renombra**: `perfil.html`, `reservas*.js`, `vehiculos.html`, `monitoreo_live*` son módulos vivos con imports internos; su renombrado implica refactor de todos los enlaces import/URL y riesgo alto de regresión. Se documenta como deuda técnica aceptada (criterio funcional sobre cosmetico).
