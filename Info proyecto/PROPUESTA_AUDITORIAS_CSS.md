# Propuesta de Auditorías Técnicas para la Capa CSS — AUTOPASS

**Fecha:** 2026-09-24  
**Alcance:** Capa Frontend (`static/css/`, `templates/`, `static/js/`)  
**Contexto:** Complemento a las auditorías ya completadas (`AUDITORIA_COLORES_FUENTES.md` y `AUDITORIA_TAMANOS_PROPORCIONES.md`).

---

## Resumen de Auditorías CSS Propuestas

| # | Auditoría | Prioridad | Esfuerzo | Impacto / Riesgo Mitigado | Métrica Actual |
|---|---|:---:|:---:|---|:---:|
| **AC-1** | **Especificidad y Guerra de `!important`** | **Alta** | 1 día | Fragilidad de cascada, bugs de sobreescritura, deuda técnica acumulada | **606** usos de `!important` |
| **AC-2** | **Rendimiento de Renderizado, GPU y Animaciones** | **Alta** | 1–2 días | Caídas de frames (jank), consumo de batería y CPU en móviles | **103** `transition: all`, **44** `backdrop-filter` |
| **AC-3** | **Soporte PWA, Mobile & Safe Areas (Notches / Isla Dinámica)** | **Media/Alta** | 1 día | Elementos flotantes cortados por barras/notches en iOS y Android | Solo **1** uso de `safe-area-inset` |
| **AC-4** | **Estados Interactivos y Accesibilidad de Teclado** | **Media** | 1 día | Navegación ciega con teclado, falta de feedback en botones e inputs | Solo **2** reglas `:focus-visible`, **20** `:disabled` |
| **AC-5** | **CSS Muerto, Duplicación de Código y Principio DRY** | **Media** | 1 día | Peso excesivo del bundle CSS, estilos legacy huérfanos | ~41 archivos con patrones repetidos |

---

## AC-1 — Auditoría de Especificidad y Guerra de `!important`

**Prioridad:** Alta · **Esfuerzo:** 1 día · **Entregable:** `Info proyecto/AUDITORIA_ESPECIFICIDAD_CSS.md`

### 1.1 Objetivo
Identificar las causas estructurales por las cuales el proyecto acumuló **606 ocurrencias de `!important`** y establecer una arquitectura de cascada limpia donde la especificidad natural del selector baste para aplicar estilos sin forzar el motor CSS.

### 1.2 Alcance
- `static/css/base/` (reset, typography, utilities, variables)
- `static/css/components/` (modals, buttons, forms, tables, cards)
- `static/css/pages/` (dashboard, profile, landing)
- Scripts JS con manipulación directa de `style.setProperty(..., 'important')` o `!important` en template strings

### 1.3 Pasos y Diagnóstico
1. **Mapeo de Puntos Calientes:** Clasificar los 606 `!important` según su tipo:
   - *Utilidades forzadas:* `.text-center { text-align: center !important; }` (Uso aceptable según metodologías utility-first).
   - *Parches entre capas:* Reglas donde una página necesita pisar un componente base (ej. `profile-tour.css` forzando `.input-premium { height: 2.625rem !important; }`).
   - *Librerías externas:* Conflictos con Leaflet, Flatpickr o FontAwesome.
2. **Jerarquización del Orden de Carga:** Verificar cómo se importan los CSS en las vistas base Jinja2 (`base.html`, `dashboard.html`, `perfil.html`) para evitar que estilos base se carguen después de estilos de página.
3. **Plan de Reducción:** Sustituir `!important` innecesarios reestructurando la especificidad BEM o el orden de la cascada.

### 1.4 Criterio de Aceptación
- Reducir el uso de `!important` de 606 a menos de 30 (limitados estrictamente a clases utilitarias de override).
- Cero `!important` en selectores de componentes estructurales (`.modal-content`, `.input-premium`, `.btn`).

---

## AC-2 — Auditoría de Rendimiento de Renderizado, GPU y Animaciones

**Prioridad:** Alta · **Esfuerzo:** 1–2 días · **Entregable:** `Info proyecto/AUDITORIA_RENDIMIENTO_CSS.md`

### 2.1 Objetivo
Garantizar una tasa sostenida de 60 FPS en interfaces interactivas, reduciendo el consumo de GPU, ciclos de reflow/repaint innecesarios y drenaje de batería en dispositivos portátiles.

### 2.2 Alcance
- Animaciones de modales, transiciones de botones y tarjetas (`transform` vs `all`).
- Componentes Glassmorphic con `backdrop-filter: blur(...)`.
- Listados y tablas con scroll infinito o gran volumen de filas (`access_logs`, historial financiero).

### 2.3 Pasos y Diagnóstico
1. **Revisión de `transition: all` (103 instancias):**
   - Rastrear cada `transition: all` y sustituirla por la lista explícita de propiedades a animar (ej. `transition: transform 0.2s ease, opacity 0.2s ease, border-color 0.2s ease`).
   - Prevenir que propiedades de layout (`width`, `height`, `margin`, `padding`, `top`, `left`) sean recalculadas en cascada durante transiciones de `:hover`.
2. **Impacto de `backdrop-filter` (44 instancias):**
   - Evaluar el costo computacional de apilar múltiples elementos con blur simultáneo (fondo del modal + tarjeta interior + botón + toast flotante).
   - Proponer fallbacks opacos (`background: rgba(17, 20, 27, 0.95);`) cuando no hay soporte o en navegadores de bajo consumo (`@media (prefers-reduced-motion)`).
3. **Aceleración por Hardware:**
   - Confirmar el uso correcto de `transform: translateZ(0)` o `will-change` en modales y paneles laterales para aislar capas de composición sin provocar consumo desmedido de memoria de video.

### 2.4 Criterio de Aceptación
- 0 ocurrencias de `transition: all` en componentes de alta frecuencia de interacción.
- Ausencia de caídas de frames perceptibles en animaciones de apertura de modales y hover de tarjetas.

---

## AC-3 — Auditoría de Soporte PWA, Mobile & Safe Areas (Notches / Isla Dinámica)

**Prioridad:** Media/Alta · **Esfuerzo:** 1 día · **Entregable:** `Info proyecto/AUDITORIA_PWA_MOBILE_CSS.md`

### 3.1 Objetivo
Asegurar que la experiencia de la PWA instalable (`standalone.css`, `manifest.json`, `sw.js`) se comporte con la fluidez y ergonomía de una aplicación móvil nativa en iOS y Android.

### 3.2 Alcance
- `static/css/layout/standalone.css`, `header.css`, `sidebar.css`
- Componentes flotantes: FAB de nueva reserva, toasts de notificación, indicador de tiempo virtual (`vt-fab-container`)
- Formularios en móvil (prevención de auto-zoom en iOS)

### 3.3 Pasos y Diagnóstico
1. **Safe Area Insets (Notches, Isla Dinámica y Barras de Gestos):**
   - El proyecto actualmente cuenta con **solo 1 mención** a `safe-area-inset`.
   - Implementar soporte global en headers, barras inferiores y modales:
     ```css
     padding-top: env(safe-area-inset-top, 0px);
     padding-bottom: env(safe-area-inset-bottom, 0px);
     padding-left: env(safe-area-inset-left, 0px);
     padding-right: env(safe-area-inset-right, 0px);
     ```
2. **Ergonomía Táctil (Touch Targets):**
   - Verificar que todos los controles clicables en dispositivos táctiles cumplan la norma WCAG 2.5.5 ($\ge 44 \times 44\text{ px}$).
   - Corregir botones `.btn--mini` (altura actual ~26px) y botones de cierre de modal (35px).
3. **Prevención de Zoom Accidental en iOS:**
   - Asegurar que ningún `input`, `select` o `textarea` tenga `font-size < 16px` en viewport móvil, ya que Safari en iOS fuerza un zoom automático destructivo que rompe el layout visual.
4. **Desplazamiento Elástico:**
   - Asegurar `-webkit-overflow-scrolling: touch;` y `overscroll-behavior-y: contain;` para evitar rebotes indeseados de toda la ventana al scrollear dentro de modales o tablas.

### 3.4 Criterio de Aceptación
- La PWA en modo standalone no tiene ningún control bloqueado o tapado por barras gestuales ni notches.
- Inputs móviles sin zoom indeseado en iOS.

---

## AC-4 — Auditoría de Estados Interactivos y Accesibilidad de Teclado

**Prioridad:** Media · **Esfuerzo:** 1 día · **Entregable:** `Info proyecto/AUDITORIA_ESTADOS_INTERACTIVOS.md`

### 4.1 Objetivo
Dotar a cada componente interactivo de la aplicación de una máquina de estados visual completa (`default`, `:hover`, `:active`, `:focus-visible`, `[disabled]`) garantizando accesibilidad y feedback táctil/visual inequívoco.

### 4.2 Alcance
- Botones (`.btn`, `.btn--primary`, `.btn--outline`, botones de icono)
- Campos de formulario (`input`, `select`, `textarea`, switches toggle)
- Enlaces de navegación y pestañas (`.nav-item`, `.tab-btn`)

### 4.3 Pasos y Diagnóstico
1. **Anillo de Foco Accesible (`:focus-visible`):**
   - Actualmente solo existen **2 reglas** en todo el proyecto con `:focus-visible`.
   - Definir un anillo de foco institucional en `static/css/base/reset.css`:
     ```css
     :focus-visible {
         outline: 2px solid var(--dorado);
         outline-offset: 3px;
         box-shadow: 0 0 10px var(--dorado-glow);
     }
     ```
   - Eliminar `outline: none;` no compensado en inputs y botones.
2. **Estados `:disabled` y Feedback de Proceso:**
   - Actualmente solo existen **20 reglas** para estados deshabilitados.
   - Estandarizar el comportamiento de botones e inputs deshabilitados:
     ```css
     button:disabled, .btn[disabled], input:disabled, select:disabled {
         opacity: 0.45 !important;
         cursor: not-allowed !important;
         pointer-events: none;
         filter: grayscale(0.5);
     }
     ```
3. **Estado `:active` para Pantallas Táctiles:**
   - Añadir `transform: scale(0.97)` o feedback de pulsación para que el usuario perciba de inmediato que el toque fue registrado antes de que termine la petición asíncrona.

### 4.4 Criterio de Aceptación
- Navegación completa por teclado (Tab / Shift+Tab) 100% visible en todos los botones, inputs y modales.
- Ningún botón en proceso o deshabilitado permite clics ni confunde visualmente al usuario.

---

## AC-5 — Auditoría de CSS Muerto, Duplicación de Código y Principio DRY

**Prioridad:** Media · **Esfuerzo:** 1 día · **Entregable:** `Info proyecto/AUDITORIA_CSS_MUERTO_DRY.md`

### 5.1 Objetivo
Eliminar estilos no utilizados procedentes de versiones legadas (v9.0 a v9.23), consolidar reglas repetidas entre los 41 archivos CSS y reducir el peso del payload transferido al navegador.

### 5.2 Alcance
- Los 41 archivos en `static/css/` cruzados contra los 54 templates HTML en `templates/` y las inyecciones de clases dinámicas en `static/js/`.

### 5.3 Pasos y Diagnóstico
1. **Detección de Selectores Huérfanos:**
   - Escanear selectores de clases en CSS que no figuren en ningún archivo HTML ni sean construidos en JavaScript.
   - Purgar clases asociadas a componentes eliminados en refactorizaciones pasadas (ej. antiguas barras de progreso de ocupación, badges obsoletos, etc.).
2. **Consolidación DRY de Estilos Repetidos:**
   - *Barras de desplazamiento (`::-webkit-scrollbar`):* Se declaran de forma idéntica en múltiples archivos CSS; deben unificarse en una única regla global en `reset.css` o `utilities.css`.
   - *Patrón de centrado Flex/Grid:* Extraer utilidades como `.flex-center { display: flex; align-items: center; justify-content: center; }`.
   - *Efecto Glassmorphic:* Crear clase componente unificada `.glass-panel` en vez de reescribir `background: linear-gradient(...)`, `backdrop-filter` y `border: 1px solid ...` en cada tarjeta.

### 5.4 Criterio de Aceptación
- Reducción del tamaño total del paquete CSS en al menos un 15%–20%.
- Cero clases huérfanas de versiones anteriores sin justificación de uso dinámico.

---

## Cronograma de Ejecución Recomendado

```mermaid
gantt
    title Plan de Auditorías CSS Propuestas
    dateFormat  YYYY-MM-DD
    section Alta Prioridad
    AC-1: Especificidad y Guerra !important   :done, a1, 2026-09-25, 1d
    AC-2: Rendimiento, GPU y Transiciones      :active, a2, 2026-09-26, 2d
    section Media/Alta Prioridad
    AC-3: Soporte PWA, Mobile y Safe Areas     :a3, 2026-09-28, 1d
    section Estandarización
    AC-4: Estados Interactivos y Accesibilidad :a4, 2026-09-29, 1d
    AC-5: CSS Muerto, Duplicación y DRY        :a5, 2026-09-30, 1d
```
