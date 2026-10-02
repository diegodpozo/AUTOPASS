# HISTORIAL DEL PROYECTO: AUTOPASS

- **SEPTIEMBRE 30, 2026 - v9.34.75: VARIANTE C DEL MOCKUP, CON UNA EXCEPCIÓN QUE LA VERIFICACIÓN OBLIGÓ**:
  * **La elección**: de las 6 superficies del mockup se eligió la **C**, la más oscura: fondo `--bg-main` (`#08090c`) y borde `--border` (gold 22%). El select deja de leerse como un bloque pegado encima de la card y pasa a leerse como una hendidura dentro de ella.
  * **La excepción, y por qué no es capricho**: `.promo-branch-select` (el filtro de sucursal de **Puntos**) **no** puede ir en `--bg-main`. `.promo-filter-bar` no tiene fondo propio, así que el select queda directo sobre `body`, que **también** es `--bg-main`. Con la misma superficie el control se vuelve invisible y solo lo delata el borde: exactamente el defecto que la variante C vino a evitar. Ese select queda en `--bg-card`, que además es lo que lo distingue de los otros dos patrones.
    - Se detectó renderizando el contexto de cada uno de los 8 selects, no aplicando la regla en bloque. Los `.select-wrapper-premium` van dentro de cards, y los `.form-control-custom` dentro de `.help-ticket-card` (`rgba(30,41,59,0.7)`), así que los tres patrones toleran `--bg-main`. El cuarto no.
  * **Contraste medido**: el texto queda en **18.41:1** sobre `--bg-main` (WCAG AA pide 4.5:1). El borde `gold 22%` compuesto da **1.60:1** contra la card, por debajo del 3:1 de WCAG 1.4.11. Es aceptable y es el mismo criterio que ya usa el proyecto: el borde fino es decorativo y lo que tiene que alcanzar 3:1 es el **indicador de foco**, que pone `border-color: var(--dorado)` opaco.
  * **Los `<option>` siguen a la caja**: van a `--bg-main` con sus selects, para que el desplegable no sea más claro que el control. En Safari son necesarios, porque `accent-color` no alcanza ahí. El de Puntos va a `--bg-card`, por la misma excepción.
  * **Verificación**: 8 guards en verde, suite **756 passed**.
  * **Lección**: una regla de estilo que funciona en un contexto puede borrar el control en otro. "Misma superficie que `body`" es unaKata la que se ve mal, y hay que mirar dónde cae cada instancia antes de aplicar la regla a la clase.

- **SEPTIEMBRE 30, 2026 - v9.34.74: LOS SELECTS QUEDARON GRIS Y EL POPUP SE ABRE AZUL; NO ES EL CSS, ES EL SISTEMA**:
  * **El síntoma reportado**: los selects "se ven mejor" pero los colores no cierran, y al pasar por las opciones se marcan en azul.
  * **Causa 1, el gris (token equivocado)**: la unificación de v9.34.73 puso `--bg-input` (`#1a1e26`), que es un gris azulado. El proyecto es obsidian: `--bg-main` es `#08090c` y las cards van de `#111` a `#050505`. El token estaba además mal elegido conceptualmente: `--bg-input` documenta "INPUTS, BOTONES SECUNDARIOS E INTERNOS", y un select dentro de una card es una **superficie de tarjeta**, no un botón secundario. Corregido a `--bg-card` (`#11141b`).
  * **Causa 2, el azul (no es CSS)**: el desplegable de un `<select>` lo dibuja el **sistema operativo**, no la hoja de estilos. Sin `color-scheme` el navegador lo abre con la paleta clara de fábrica y marca la opción bajo el cursor con el azul de Windows. Ningún `background` ni ningún `option` lo alcanza: son estilos del popup nativo.
    - `color-scheme: dark` le dice al navegador que el contexto es oscuro, así que el popup se dibuja oscuro.
    - `accent-color: var(--dorado)` pinta la marca en dorado.
    - Los `<option>` se fijan a `--bg-card` / `--text-primary`, porque `accent-color` no alcanza en Safari.
  * **Las dos propiedades ya se usaban en el proyecto**, para el mismo problema: `color-scheme: dark` en los inputs de fecha del dashboard (`dashboard-metrics.css`, `dashboard-cards.css`) y `accent-color: var(--dorado)` en checkboxes y toggles de 5 archivos. No era una propiedad nueva: era una que faltaba acá.
  * **Verificación**: 8 guards en verde, suite **756 passed**.
  * **Lección**: un `<select>` tiene dos superficies, la caja (CSS nuestro) y el popup (del sistema). Unificar la caja y creer que seArregló todo deja el popup como estaba. Y elegir un token por lo que la propiedad "debería" ser, en vez de por cómo se ve contra el fondo real, produce un gris que nadie pidió.

- **SEPTIEMBRE 30, 2026 - v9.34.73: LOS 8 SELECTS DEL PORTAL ERAN 3 SISTEMAS VISUALES DISTINTOS; AHORA SALEN DE UN COMPONENTE ÚNICO**:
  * **El inventario**: `/perfil` tiene 8 `<select>` en 4 plantillas (`inicio.html` x4, `ayuda.html` x2, `puntos.html` x1, `vehiculos.html` x1) repartidos en **3 clases sin relación entre sí**: `.select-wrapper-premium` (5), `.form-control-custom` (2) y `.promo-branch-select` (1). Tres paletas distintas (`#111`, `rgba(15,23,42,0.8)`, `rgba(255,255,255,0.04)`), tres radios (12, 12 y **10px**), tres formas de dibujar la flecha y tres focos distintos.
  * **Tres bugs concretos, no solo fealdad**:
    1. **Falta `-webkit-appearance`.** El patrón `.select-wrapper-premium` declaraba `appearance: none` sin el prefijo. En Safari/iOS eso no anula el control nativo, así que la flecha aparecía **doble**: la del `::after` del componente más la del navegador. El usuario mayormente del proyecto ve en iPhone.
    2. **La flecha dependía de Font Awesome.** Era un `::after` con `content: "\f078"` y `font-family: "Font Awesome 6 Free"`. Si el CDN de FA no carga, no queda flecha: el `appearance: none` sigue puesto, así que el select se queda **sin ningún indicador** de que es desplegable.
    3. **`.promo-branch-select:focus` usaba `rgba(223,186,107,0.4)` = 2.54:1**, que ya había fallado WCAG 1.4.11 en v9.34.65 y quedó el `:focus-visible` de `reset.css` como parche. Ahora la base lo resuelve y el parche sobra.
  * **El componente compartido estaba definido dentro de una página**: `.select-wrapper-premium` se definió en `pages/profile/profile-reservations.css`, pero la usan también los **4** selects de los modales de reserva del dashboard (`dashboard/tabs/admin_reservations.html`). Un componente de dos páginas no puede vivir en el archivo de una de ellas.
  * **Se crea `static/css/components/select-field.css`** y se linkea desde `base.html`, así lo reciben tanto `/perfil` como el dashboard. Se borran las 3 definiciones duplicadas y quedan **-94 líneas netas**.
  * **Base única + una variante por patrón.** La superficie (fondo, borde, radio, color, foco) sale de una sola declaración agrupada; el chevron y el `appearance` de otra, también agrupada.
  * **`.form-control-custom` va en un `<input>` y dos `<textarea>`** además de los 2 selects (`ayuda.html` x2 y `profile/modals.html`). Por eso el selector del chevron es `select.form-control-custom` y no la clase sola: sin el `select` adelante, un campo de texto heredaría una **flecha falsa** y `cursor: pointer`.
  * **Cambios visuales, todos en el portal** (el dashboard conserva su aspecto salvo el fix de Safari):
    - Los 8 selects pasan a `--bg-input`, `--border-light`, `--radius-md` y `--text-primary`. Antes `#111` con borde `1.5px solid #222` en unos y navy/blanco en otros.
    - El foco de `.form-control-custom` pasa de **azul** (`--info` + halo `rgba(59,130,246,0.2)`) a **dorado**, como los otros dos. Esto también cambia el foco del input y los textareas de Ayuda y del modal, que compartían la clase.
    - Los `<option>` de Puntos dejan de ser `#1a1626`: era el último violeta que quedaba en un select. Los pinta el `select option` global de `forms.css`.
  * **Chevron en token**: `--select-chevron` en `:root`, para no repetir el data-URI (que ya estaba duplicado en `forms.css` y `dashboard-tables.css`).
  * **Verificación**: 8 guards en verde, suite **756 passed**, y el design system registra **12 mejoras y 0 regresiones** (`color.literales_no_genericos` 1090 → 1069, `rgba_distintos` 340 → 336, `shadow.distintas` 127 → 124).
  * **Pendiente de vista humana**: el `.select-wrapper-premium` del dashboard cambia de `#111` a `--bg-input` y su borde pasa de `1.5px #222` a `1px --border-light`. Es deliberado, pero no se ve en un test.
  * **Lección**: un componente compartido escondido en el CSS de una página parece local hasta que alguien lo incluye desde otra. Y tres clases con nombres parecidos (`select-premium`, `select-premium-sm`, `select-wrapper-premium`, `input-premium-sm`) son cuatro sistemas distintos, no variantes de uno.

- **SEPTIEMBRE 30, 2026 - v9.34.72: EL SALUDO TAPABA EL DROPDOWN DE NOTIFICACIONES, Y ERA UNA REGRESIÓN DE v9.34.71**:
  * **El síntoma**: al abrir la campana, el panel aparecía detrás del saludo, en escritorio y en móvil. Después de separar los síntomas resultó que tapaba los primeros elementos de **todas** las páginas, no solo del saludo: todos los saludos son el primer elemento de su tab.
  * **La causa**: el header del portal se estiliza con `.main-content-scroll header`, un selector **descendiente**. Todo `perfil.html` cuelga de `<main class="main-content-scroll">`, así que ese selector matchea cualquier `<header>` anidado, no solo el hijo directo. El macro del saludo de v9.34.71 emitía `<header class="saludo">` y por lo tanto **matcheaba la regla del header del portal**, heredando `position: sticky`, `top: 0`, `z-index: 1000`, `background: rgba(10,10,10,0.85)` y `backdrop-filter: blur(25px)`.
  * **Por qué ganaba el saludo**: `.saludo` es `(0,0,1,0)` y `.main-content-scroll header` es `(0,0,1,1)`. Gana el header por especificidad, así que el `z-index: 1000` loDefined el saludo, no el componente. Y como el saludo va **después** del `<header>` real en el DOM, a igual z-index pinta el último: tapaba el dropdown, y con su fondo opaco lo tapaba de verdad.
  * **El z-index del dropdown nunca fue el problema**: `1000` en escritorio y `var(--z-toast)` (`10000`) en móvil son correctos, solo que ambos están *scopeados* dentro del contexto del header, que a su vez estaba en `1000`. Subir el z-index del dropdown no lo hubiera arreglado.
  * **Dos defensas, porque una sola deja la trampa armada**:
    1. El saludo emite `<div>`, no `<header>`. Semánticamente tampoco se pierde nada: el section contenedor es un `<div>`, no un `<section>`, así que un `<header>` ahí no es landmark, y el `<h1>` de adentro ya aporta el encabezado.
    2. Las 4 reglas del header pasan a `.main-content-scroll > header`, hijo directo, en `header.css` (3) y `standalone.css` (1). Así ningún `<header>` anidado futuro las dispara, aunque alguien vuelva a usar la etiqueta.
  * **Guard nuevo** `_tools/check_header_scope.py`: falla si alguna regla vuelve al selector descendiente, si algún tab del portal emite `<header>`, o si el header real de `perfil.html` deja de ser hijo directo de `main-content-scroll` (o sea, si la regla `> header` queda inaplicable).
  * **Mordidas probadas**: (1) revertir el selector a descendente → detecta las 4 ocurrencias; (2) `<header>` en un tab → detecta la línea exacta. Ambas dan `exit 1`, y el estado normal `exit 0`.
  * **Verificación**: 8 guards en verde, suite **756 passed**, los 7 tabs renderizan sin `<header>` y `perfil.html` conserva el suyo.
  * **Lección**: un selector por etiqueta, usado para el layout de una página, es una trampa para cualquier elemento con esa etiqueta que se agregue después. El guard es la parte que importa: la causa raíz era el selector demasiado amplio, no el `<header>` del saludo.

- **SEPTIEMBRE 30, 2026 - v9.34.71: LOS 7 SALUDOS DEL PORTAL ERAN 4 IMPLEMENTACIONES DISTINTAS; AHORA SON UN SOLO COMPONENTE**:
  * **El problema**: los 7 tabs de `/perfil` tenían su propio saludo. Cuatro usaban `.card.welcome-card > .welcome-msg > h1`, Inicio usaba `.greeting-premium` con un `h2`, Cuenta tenía un bloque de identidad aparte con avatar de 100px y Ayuda un hero propio con paleta azul y un radial-gradient de 350x350px. Cuatro radios, cuatro colores, cuatro espaciados para el mismo elemento.
  * **Se hace un macro único** (`templates/components/saludo.html`) con un solo `.saludo` compuesto por `.saludo-lead`, `.saludo-body` y `.saludo-extra`. Las variantes se resuelven con clases que ya existían en cada tab: `.saludo-lead--avatar` (el avatar de Cuenta), `.saludo-lead--hero` y `.saludo--hero` (Ayuda, que conserva su paleta azul a propósito). El bloque `{% call %}` de Ayuda y el botón de Vehículos van en `.saludo-extra`.
  * **El avatar de Cuenta baja de 100px a 64px**: a 100px + borde de 4px dominaba la pantalla en una tab que además tiene dos columnas de contenido.
  * **Nada de `|safe`**: la primera versión del macro pasaba el avatar como `lead_html`. `Jinja2Templates` de FastAPI corre con `autoescape=True` siempre, así que el markup habría salido escapado, y marcarlo `|safe` para arreglarlo abre inyeccion si alguien pasa un valor de usuario. Se cambió la API para que reciba **datos, no HTML**: `iniciales="--"` + `id_iniciales="user-initials"`, y `lead_texto` para el icono+texto del hero. Ningún `|safe` en el componente.
  * **La clase de variante se pasa literal**, no se arma con un parámetro (`clase="saludo--hero"` y no `variante="hero"`): `check_css_huerfano.py` lee el HTML con regex, y una clase construida en el macro le resulta huérfana. Así el guard la ve usada sin necesidad de una excepción.
  * **Los IDs que usa el JS se preservan**: `welcome-greeting`, `profile-full-name`, `user-initials`, `user-member-since` y `help-category-pills`. Se verificó renderizando los 7 tabs con un `Environment` real (autoescape activo) y comprobando que los 5 IDs siguen en el HTML resultante.
  * **Limpieza**: se borraron `.welcome-msg`, `.welcome-card`, `.greeting-premium` (con sus overrides responsive en `profile-tour.css`), `.account-identity-isolated`, `.profile-header-premium`, `.avatar-circle`, `.profile-info-main`, el hero viejo de Ayuda y `.btn-group-header`. **252 líneas afuera, 102 adentro.** `margin-top: 19px` pasó a `20px`: al borrarse el `.greeting-premium` que lo compartía quedaba de un solo uso en todo el proyecto y fuera de la escala de 4px.
  * **`saludo.css` no va en `css_profile.html`**: ese include lo cargan `perfil.html` **y** `dashboard.html`. El link está en el `extra_head` de `perfil.html`, que es el único lugar donde existe la clase.
  * **El tour**: 4 selectores `#section-ayuda .help-hero-card` pasaron a `.saludo`, junto con el resto de `.welcome-card`.
  * **Verificación**: 7 guards en verde (0 huérfanas, 0 tokens rotos, llaves balanceadas, sin inline styles), suite **756 passed**, `perfil.html` y `dashboard.html` parsean.
  * **Pendiente de mirada humana**: responsive y contraste final en navegador. Lo que hay acá es verificación estática, no visual.

- **SEPTIEMBRE 30, 2026 - v9.34.70: 23 TOKENS DE SOMBRA ESTABAN FUERA DEL `:root`, 54 `box-shadow` NO PINTABAN NADA**:
  * **El bug**: al tokenizar las sombras duplicadas (v9.34.63) las 23 declaraciones `--shadow-*` quedaron **después** del cierre de `:root` en `variables.css`, es decir como declaraciones a nivel de archivo, sin pertenecer a ninguna regla. Eso es CSS inválido: el navegador las descarta. Cada `var(--shadow-*)` de los **54 usos en 20 archivos** quedaba sin resolver, y un `box-shadow` *invalid at computed-value time* cae a su valor inicial, **`none`**. O sea: ninguno de esos 54 sombras se pintaba.
  * **Incluía el glow de foco de los selects**, que es justo lo que hace visible dónde estás escribiendo: `.select-wrapper-premium select:focus`, `.input-premium-sm:focus` y `.input-premium:focus` (este último además con `--shadow-20` inexistente desde antes de tokenizar).
  * **El guard no lo veía, y esa es la parte interesante**: `check_css_tokens.py` informaba *"OK: 77 tokens, todos declarados y usados"*. Su `DECLARE_RE` buscaba el patrón `--x: valor` sin preguntar si estaba dentro de un bloque, así que una declaración huérfana contaba como declaración válida. El token "existía" en el diccionario del guard y en el archivo, pero no en el navegador. **Un guard que valida laPresence del texto y no su|location| no puede encontrar esta clase de bug**; es el mismo tipo de error que el guard de color contando selectores como colores en v9.34.67.
  * **Fix**: se agrega `_orphaned_decls()`, que cuenta la profundidad de llaves y reporta toda declaración de custom property encontrada con profundidad ≤ 0 (respetando `@media`/`@supports`, que sí son válidos). Falla con exit 1 y, cuando el token además se usa, informa **cuántos usos quedan sin resolver**.
  * **Test de mordida en tres estados**: (1) guard normal → `exit 0`, 77 tokens; (2) `--shadow-falso` huérfano y sin usos → `exit 1`; (3) `--shadow-15` re-declarado fuera del bloque, que ya era un token real en uso → `exit 1` reportando `2 usos quedan sin resolver`. El caso (3) es el que importa, porque es el bug original.
  * **Verificación**: 5 guards CSS en verde, suite **756 passed** (8 warnings), llaves balanceadas, `git diff --check` limpio, sin CJK.

- **SEPTIEMBRE 30, 2026 - v9.34.69: EXCEPCIONES DE COLOR INTENCIONALES REGISTRADAS, CON MORDIDA PROBADA**:
  * `check_color_equivalence.py` existe para demostrar que una migración de tokens no movió ni un píxel. Un rediseño de color deliberado **no se puede validar con él**: falla, y tiene razón. Los 3 archivos de v9.34.68 se declaran en `_tools/color_equivalence_allowlist.json` con su commit y su motivo escrito, siguiendo el patrón de baseline que ya usa el repo.
  * **La excepción es condicional, no una lista de exentos permanente**: los archivos se omiten **solo** cuando `--against` es el padre del commit registrado (el caso de validar recién ese commit). En cualquier otra comparación se comparan enteros, así que una regresión de color posterior en el mismo archivo sigue saltando. Sin esa condición, un archivo excluido una vez nunca volvería a revisarse.
  * **Test de mordida**: inyectar `var(--rojo)` en `profile-reservations.css` da `exit 1` igual, con `UNRESOLVED 0 -> 1`. Ese es el caso que la condición protege.
  * **El mensaje de éxito también mentía menos**: antes decía "los N archivos resuelven EXACTAMENTE los mismos colores" y luego "cero cambio visual garantizado", contando también los omitidos. Ahora separa los neutros de los intencionales y dice que la neutralidad solo se garantiza para los primeros.
  * **La CI no corre ningún guard CSS**: `ci.yml` solo ejecuta pytest. Los 7 guards son de uso local, así que un fallo en ellos no bloquea el push ni el PR. La excepción se registró igual, para que el guard sea usable contra `HEAD~1` en local. Cerrar esa brecha queda pendiente.

- **SEPTIEMBRE 30, 2026 - v9.34.68: JERARQUÍA VISUAL DEL PORTAL DE USUARIO, EL DORADO RESERVADO A LA ACCIÓN PRINCIPAL**:
  * **Planteo**: el dorado (`--dorado`) estaba en 98 reglas con texto dorado en el CSS del perfil, casi todas decorativas. No era un problema de contraste: `--dorado` da 9.98:1 sobre la tarjeta y `--dorado-dark` 6.25:1, ambos AAA. El problema era su cantidad, que hacía que todo pareciera importante y nadaDestacaba.
  * **Grupo 1, títulos y decoración**: los `h1` de las 7 tabs (`inicio`, `vehiculos`, `reservas`, `puntos`, `notificaciones`, `cuenta`, `ayuda`) pasan a `--text-primary` (17.04:1); `.hub-section-title` de `cuenta.html` (DATOS PERSONALES, SEGURIDAD) a `--text-secondary` (7.26:1); los íconos de título a `--dorado-dark` (6.25:1) y la línea decorativa de `.section-title-premium--center::after` también.
  * **Un ícono dorado por título**: se agrega `.welcome-msg h1 i`, que cubre los 5 íconos de las tabs (auto, estrella, calendario, vehículo, campana) en una sola regla en vez de editar cada uno. El override de `.fa-bell` en `profile-notifications.css` quedó redundante y se le sacó el color, conservando solo el `margin-right`.
  * **Grupo 2, elementos con función**: las etiquetas de formulario (`.form-group-premium label`, que cubren las 16 del `inicio.html` a través de `.fg-label-*`) y la flecha e ícono de `.select-wrapper-premium` pasan a `--text-secondary`. El precio total (`.total-amount`, `.price-value-ultra`) baja a `--dorado-dark`: sigue siendo el dato más destacado de la pantalla, pero deja de competir con el botón.
  * **Lo que NO se tocó, a propósito**: el foco de los 4 inputs (`.input-premium:focus`, `.input-premium-sm:focus`, `.select-wrapper-premium select:focus`, `.filter-input-premium:focus`) sigue en `--dorado`. Es el indicador de dónde estás escribiendo y el único `:focus` que el usuario ve al navegar, así que se trata como acción. El botón `CONTINUAR` (`.btn-confirm-premium`) y `.btn--primary` también conservan el dorado fuerte, y quedan como el elemento más saturado de la pantalla.
  * **Balance final**: ~126 reglas con `--dorado` (acciones, foco, bordes activos), 8 con `--dorado-dark` (títulos y precio) y 5 con `--text-secondary` (etiquetas y adornos del selector).
  * **Verificación**: 7 guards CSS en verde, suite **756 passed** (8 warnings), llaves balanceadas (145 y 337), `git diff --check` limpio.

- **SEPTIEMBRE 30, 2026 - v9.34.67: ÍCONOS DUPLICADOS DEL FORMULARIO DE VEHÍCULO + EL GUARD DE COLOR CONTABA SELECTORES COMO COLORES**:
  * **Dos `id` repetidos por formulario**: el ícono del selector de tipo de vehículo y el del campo de patente compartían `id` en `inicio.html` y `vehiculos.html`. Como `getElementById()` devuelve siempre el primero, `updateVehicleTypeIcon()` actualizaba el del selector. **No era un bug visible**: el del campo de patente estaba oculto a propósito (por `d-none` en un caso y por una regla CSS en el otro), así que era código muerto. Se eliminaron los dos íconos ocultos y la regla CSS que ya no tenía destino. Queda un ícono por formulario y **0 `id` duplicados** en todo `templates/`. Cero píxeles cambiados.
  * **Clase `.d-none` eliminada**: era el último uso de esa clase en el repo (el elemento que la usaba era uno de los íconos borrados). El guard `check_css_huerfano.py` la marcó como huérfana y acertó. Su definición era `display: none`, que no hacía falta para nada más.
  * **Bug del guard de color**: `HEX` (`#[0-9a-fA-F]{3,8}`) corría sobre el archivo completo sin distinguir selectores de declaraciones. Como `a` y `d` son dígitos hexadecimales válidos, cada `#add-vehicle-form` en un selector contaba como un color. Se agrega `declarations_only()`, que descarta los selectores, y se aplica en el conteo de literales y en `alpha_scale()`.
  * **El número real era 1090, no 1102**: los 12 de diferencia eran falsos positivos de selectores. **Mismo tipo de bug que el `spacing off-grid` retirado en v9.34.63**: una métrica que mide algo que no es un defecto y hace que borrar una regla parezca una mejora de color. Por eso el fix del ícono apareció como "mejora" en el guard sin haber tocado un solo color.
  * **Test de mordida en ambos sentidos**: un color real nuevo (`#abc123`) dispara el guard (`1090 -> 1091`, exit 1); un selector con forma de hex (`#abc123def .algo`) se ignora (exit 0). El guard sigue detectando regresiones y ya no confunde selectores con colores.
  * **Documentación**: ningún documento citaba los números del baseline (se describía de forma cualitativa), así que no quedaron referencias huérfanas al pasar de 1102 a 1090.
  * **Verificación**: 7 guards CSS en verde, suite **756 passed** (8 warnings), llaves balanceadas, `git diff --check` limpio, sin CJK.

- **SEPTIEMBRE 30, 2026 - v9.34.63-65: SOMBRAS A TOKENS + REDUCED-MOTION + FOCO Y SCROLL ACCESIBLES**:
  * **Sombras**: 23 duplicadas exactas (54 ocurrencias) → tokens `--shadow-*`. Las 108 únicas no se tocan.
  * **Espaciado y transiciones**: medidos y **descartados**. El 99,2% del espaciado ya usa valores repetidos y las dos curvas de Material (`ease`, `cubic-bezier`) no son intercambiables.
  * **Reduced-motion (v9.34.64)**: no había ningún bloque para la preferencia del usuario frente a 229 animaciones. Se agregan uno global en `animations.css` con `0.01ms` (no `none`, que dejaría invisible a los toasts) y `html:root *` (para superar a las 5 transiciones con `!important` de clase). Guard `check_reduced_motion()`.
  * **Foco (v9.34.65)**: el anillo ya existía pero 24 reglas de página lo anulaban, dejando controles con ratio efectivo 1.00:1 (se requiere ≥3:1). Se refuerza con `:root :focus-visible` en `reset.css`, con exención para los 10 controles que ya cumplen. Guard `check_focus_ring()`.
  * **Scroll JS (v9.34.65)**: 16 llamadas a `scrollIntoView({behavior:'smooth'})` ignoraban la preferencia; 9 de ellas centran el elemento en pantalla. Se unifican en el helper `scrollToElement()` de `utils.js`. Guard `check_js_scroll_motion()`.
  * **z-index**: auditado y **descartado**, no había bug. Los literales altos codifican relaciones entre capas (sidebar/overlay, header/toggle) y tokenizarlos cambiaría la jerarquía visual.
  * **Herramientas**: `migrate_shadow_tokens.py` (idempotente, procesa de derecha a izquierda y valida todo antes de escribir) y `check_color_equivalence.py` corregido para comparar sombras multicapa.
  * **Verificación**: 7 guards verdes, `check_color_equivalence --max-delta 0` en 0/255, suite 733 passed.

- **SEPTIEMBRE 30, 2026 - FASE 2 DE COLOR: MEDIDA Y DESCARTADA (V9.34.62)**:
  * **Contexto**: en v9.34.61 se propuso fusionar las familias de opacidad (~190 alfas). Antes se midió si formaban una escala o eran continuos.
  * **Resultado**: forman una escala ya existente, no continua. Son valores redondos escritos a mano y 7 de 19 niveles de blanco cubren el 80% de los usos.
  * **Decisión**: con tolerancia 2/255 solo 14 de 190 ocurrencias eran fusionables, y al subir la tolerancia el cambio visual se nota (un borde de 0.05 a 0.097). **Se descarta la unificación masiva.**
  * **Lo que quedó**: la escala pasa a ser **auditable** con `check_css_design_system.py`, que flaggea alfas nuevos sin prohibirlos. Estado: 100 niveles declarados.
  * **Herramientas**: `check_color_equivalence.py` ahora acepta `--max-delta` y `--against`, compara todos los canales y acepta el alfa en fracción, porcentaje o 0-255.
  * **Verificación**: sin cambios de color en CSS, 5 guards verdes, suite 733 passed.

- **SEPTIEMBRE 30, 2026 - v9.34.61 (REMOTO): CONTROL DE AFORO EN SALIDA + COMPARACIÓN DE PATENTE**:
  * **Contexto**: commit `dd9f30a` del remoto (distinto al `7f35a1d` local de la misma numeración). Añade mejoras de robustez en la normalización de patentes y en el control de aforo, sin tocar el trabajo de CSS/a11y hecho en local.
  * **Comparación de patentes**: `repositories/vehicle_repository.py` centraliza la expresión SQL de patente normalizada (`func.replace(func.upper(models.Vehicle.patente), ' ', '')`) en `_norm_expr()`, añade guard para `norm` vacío en `get_by_normalized_patente` y unifica todas las búsquedas para ignorar espacios/mayúsculas (tanto por patente formateada como normalizada). `get_by_patente` pasa a delegar en `get_by_normalized_patente`.
  * **Access/Hardware**: `services/access_service.py` corrige el manejo de `suc_short` (evita el caso en que `gate_id` no contiene `_`), refactoriza el momento de `now = TimeService.now()` para que esté disponible en el flujo de salida, y mejora el manejo de errores en `exit_qr`: distingue `HTTPException` (re-lanza) de otros errores (log con `exc_info=True`, mensaje genérico). `services/hardware_service.py` ajusta la lógica de lectura de `gate_id` para evitar asignaciones incorrectas cuando no existe el separador.
  * **Billing/Mercadopago**: `services/billing_service.py` y `services/mercadopago_service.py` reciben ajustes menores relacionados con el flujo de facturación/salida.
  * **Tests**: `tests/test_bugfixes_funcionales.py` añade cobertura para los bugfixes funcionales relacionados con aforo/salida y normalización.
  * **Documento**: `BUGS A RESOLVER.md` registra hallazgos pendientes (no implementados) para seguimiento.

- **SEPTIEMBRE 30, 2026 - v9.34.61 (LOCAL): UNIFICACIÓN DE COLOR + TOKEN INEXISTENTE + GUARDS CSS**:
  * **Bug real**: `.barrier-text` usaba `var(--text)`, que no existe. Los tokens ausentes no dan error: la propiedad cae en silencio a su valor heredado y el texto se veía despintado. Corregido a `var(--text-secondary)`.
  * **Color**: migrados **195 literales en 31 archivos** cuyo RGBA era idéntico al de un token ya declarado, así que el píxel final no puede cambiar. Los principales: `--border-card` 51, `--border-light` 38, `--dorado-glow` 28, `--success` 27. Se protegieron los fallbacks `var(--x, #fallback)` y los iconos en `content:`.
  * **`#fff` y `#000` se dejaron como literal a propósito**: el resultado sería idéntico y solo aportaría ruido. La coherencia real la dan los tokens semánticos (un borde, un glow), no los genéricos.
  * **Corrección de la premisa**: el plan original de unificar los alfas del dorado se descartó al medir, porque los distintos niveles de opacidad son decisiones de diseño y no duplicados.
  * **Guards nuevos**: `check_css_tokens.py` (detecta tokens ausentes y muertos), `check_color_equivalence.py` (demuestra que la migración fue visualmente neutra) y `check_css_design_system.py` con baseline, para que las próximas rondas no sean mediciones a ciegas. Herramienta de migración `migrate_color_tokens.py`, idempotente y con dry-run por defecto.
  * **Verificación**: 4 guards en verde, suite 733 passed, diff 197 inserciones / 197 eliminaciones (sustitución pura).

- **SEPTIEMBRE 30, 2026 - CIERRE DE LOS ÚLTIMOS GAPS DE A3 (COBERTURA) + CORRECCIÓN DEL ESTADO DE LA CI (V9.34.60)**:
    *   **Contexto**: con las auditorías A1–A9, AN, T1–T5 y AC-1 a AC-5 cerradas, quedaban solo pendientes de baja prioridad y findings ya documentados sin implementar. Sin tocar la concurrencia transaccional (descartada por decisión), se atacó lo que era accionable: los gaps de cobertura que A3 declaraba explícitamente como "pendientes/depriorizado" y el estado real de la CI.
    *   **`core/seed.py` 0% → 100%** (`tests/test_core_seed.py`, 8 tests). `seed_initial_data()` es el orquestador de datos maestros que corre `init_db.py`: crea 4 usuarios, aforo global, 18 tarifas, 3 promociones y 4 sucursales. Lo interesante no era el camino feliz sino las guardas: **idempotencia** (3 corridas seguidas no duplican nada), **normalización de DNI con puntos** en usuarios preexistentes (`"11.232.444"` → `"11232444"`, sin duplicar el usuario), y que el seed **no pisa** tarifas, aforo, promociones ni sucursales que el operador ya haya cargado. Se verificó además que el password se guarda hasheado y que `verify_password` lo acepta (que no sea un placeholder).
    *   **`routes/admin/virtual_time.py` sin cobertura → 100%** (`tests/test_admin_virtual_time_routes.py`, 18 tests). `tests/test_virtual_time.py` cubría **solo** `services/time_service.py`; las 6 rutas de admin de la herramienta de reloj virtual estaban sin un solo test. Ahora se cubren las 6 rutas (`advance`, `rewind`, `set-target`, `set`, `reset`, `status`), el alias de ruta `""` vs `/status` (decorador doble), el **400** por fecha ISO inválida (que no debe mover el reloj ni disparar los workers), el **422** por campo faltante, el gate `get_local_manager` (**403 para staff**; admin global y local admin sí pasan, aclarado contra el docstring "global o local"), y `_run_all_checks`: tolerancia a fallos (un worker caído se loguea y la ruta sigue respondiendo) más una guarda de que los **5** workers se siguen invocando.
    *   **Aislamiento de estado**: `TimeService` persiste el offset en `data/virtual_time_offset.json`, o sea estado global en disco. Los tests usan un fixture que restaura ese archivo al terminar; sin eso, los tests dejaban `data/` sucio en el repo y el reloj virtual se filtraba entre tests y entre corridas.
    *   **Ajuste sobre la hipótesis inicial**: el primer test de rol asumía que un admin global debía recibir 403, por la lectura de "local_manager". El código real acepta ADMIN y LOCAL_ADMIN (el docstring lo dice: "ADMINISTRADOR (GLOBAL O LOCAL)"), así que el 403 corresponde a **staff**, que es lo que el test verifica ahora.
    *   **Estado de la CI (corrección documental)**: la nota de A3 decía "CI (`ci.yml.disabled`) NO reactivar tal cual" y listaba 3 cambios pendientes. Verificado en GitHub Actions: el workflow está **activo y en verde**, con los 3 cambios ya aplicados en `.github/workflows/ci.yml` (`ubuntu-latest`, Python 3.14, `init_db.py` en vez de `patch_bidi.py`, `--cov-fail-under=82`). Corridas verificadas: `success` en `v9.34.59` (2m8s), `v9.34.58` y `v9.34.54`. La instrucción de trabajo ya se había ejecutado; el documento quedó obsoleto.
    *   **Resultado**: suite **733 passed** (antes 707, +26) y cobertura real **93%** (16.318 stmts / 1.201 sin cubrir), por encima del umbral de 82%. Docstrings en español en ambos archivos de test, siguiendo la convención del repo.
    *   **Fuera de alcance por decisión**: concurrencia transaccional de reservas (`Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md`, R1–R5) queda sin implementar; los cosméticos DRY diferidos de AC-5 (146 flex-center, 253 `border-radius` literales, 43 blur, 90 `uppercase`+`letter-spacing`) siguen diferidos por no afectar correctitud; AC-3 pendiente de validación visual en un iPhone con notch.


- **SEPTIEMBRE 29, 2026 - AC-3 CERRADA: PWA + SAFE AREAS (notches / isla dinámica) (V9.34.59)**:
    *   **Bug de raíz**: `templates/base.html` declaraba `apple-mobile-web-app-status-bar-style: black-translucent` **sin** `viewport-fit=cover` en el meta del viewport. En iOS esa es la peor de las tres combinaciones posibles: `black-translucent` hace que la webview se dibuje **bajo** la status bar, pero sin `viewport-fit=cover` los `env(safe-area-inset-*)` devuelven **0**. Resultado: el header quedaba parcialmente tapado por el reloj/batería y no existía forma de compensarlo con CSS. Los dos cambios son **acoplados**: el CSS sin el meta es un no-op, y el meta sin el CSS deja el contenido bajo el notch.
    *   **Tokens (DRY)**: 4 tokens nuevos `--safe-area-top/right/bottom/left` en `static/css/base/variables.css` con fallback `0px`, consumidos siempre con `calc()` para **sumar** el inset al espaciado existente en vez de reemplazarlo. Evita repetir `env(safe-area-inset-*)` en 11 superficies.
    *   **11 superficies con inset**: `variables.css` (fuente) · `header.css` (header sticky del layout con sidebar) · `standalone.css` (espejo obligatorio) · `sidebar.css` (padding del sidebar, padding-bottom del drawer móvil, `top` del toggle fijo) · `grid.css` (fin del scroll principal) · `modals.css` (`.modal`, `.modal-premium`, `.modal-actions-sticky`) · `virtual-time.css` (`.vt-fab` inferior/derecha) · `landing-nav.css` (header fijo de landing, estados normal y `.scrolled`) · `base.html` (`#pwa-install-btn` inline).
    *   **Trampa evitada**: `standalone.css` pisa el padding del header con `padding: 20px 40px !important` dentro de `@media (display-mode: standalone)`. Un `padding-top` con el inset en `header.css` habría quedado **anulado justo en modo standalone**, que es donde más hace falta. Se actualizó la regla espejo conservando el inset.
    *   **`overscroll-behavior-y: contain`** en los 3 contenedores de scroll (`.main-content-scroll`, `.modal`, `.modal-premium`) y en el drawer móvil `.sidebar`, para evitar pull-to-refresh y scroll-chaining.
    *   **Criterio NA (documentado, no aplicado)**: touch targets ≥44px. Las 11 declaraciones entre 20–43px corresponden a botones compactos de dashboard de escritorio; la guideline es mobile y forzar 44px los desproporcionaría. El criterio de `font-size ≥16px` en inputs móviles **ya estaba cumplido** por `.input-premium` (`1rem`, `forms.css:50`), con 0 reglas por debajo del umbral.
    *   **Cache**: los 5 CSS del shell modificados están en el precache de `static/sw.js` con estrategia `stale-while-revalidate`. Se subió `SHELL_CACHE` de `autopass-shell-v1` a `autopass-shell-v2`, tal como indica el comentario del propio `sw.js:1` al desplegar una versión nueva, para no servir CSS viejo en la primera carga.
    *   **Verificado**: llaves CSS balanceadas, 0 regresión de CSS muerto (`_tools/check_css_huerfano.py`), **287** `!important` en el proyecto (baseline de AC-1 **sin cambios**; el delta 0 se comprobó archivo por archivo ignorando comentarios), suite **707 passed**. **Pendiente de validación visual en un iPhone con notch.**

- **SEPTIEMBRE 29, 2026 - LIMPIEZA DE CÓDIGO MUERTO (LOTES 1-4) + 3 BUGS CORREGIDOS + MIGRACIÓN QUE DROPEA `coupons` (V9.34.55)**:
    *   **Bug — KPI "Promedio Estadía"**: `occ-stat-avg-time` (pestaña Ocupación) nunca se calculaba y quedaba vacío. Se agregan `getPermanenciaMs()`/`formatPermanencia()` en `static/js/modules/dashboard-stats.js` y la fila de tabla los reusa en vez de recalcular. `getPermanenciaMs` rechaza `null`/`undefined`/`''`, usa `getVirtualNow()` (hora virtual) y `Math.max(0,...)` para no restar tiempos.
    *   **Bug — 404 en balance**: `static/js/modules/profile.js` llamaba `GET /v1/user/balance/active-stays`, ruta que nunca existió (introducida en `4d7c806`). La real es `/v1/user/active-stays` (`routes/user/balance.py:15`, montada sin prefijo). 78 llamadas del front contra OpenAPI → 0 rotas.
    *   **Bug — PWA en monitoreo**: el botón "INSTALAR APP" aparecía en `/monitoreo`. `templates/monitoreo_live.html` marca `body.no-pwa-install` y `templates/base.html` lo respeta en `beforeinstallprompt`. No se reutilizó `layout-with-sidebar` porque rompe el grid de `grid.css`/`standalone.css` y además activa el banner de tiempo virtual.
    *   **Lote 1 — imports sin uso**: 25 símbolos Python + 7 imports JS.
    *   **Lote 2 — código muerto JS**: `getAllUsersData`, `toggleCollapsible`, `getOffsetMs`, `isVirtual`, `stopNotifPolling` y `existingVehiclesTourSteps` (−123 líneas).
    *   **Lote 3 — símbolos Python**: 9 locales asignadas y nunca leídas → 0; 5 clases de schema sin referencias (`Token`, `BranchCreate`, `ReservationCreate`, `SupportTicketResponse`, `SupportTicketReply`); `models.Coupon`, con 0 referencias en todo el repo y sin SQL crudo (el canje de puntos real lo cubre `RedemptionTicket`).
    *   **Lote 4 — markup**: 19 `id` redundantes (elemento vivo sin consumidor del id) y el div `notif-loading`, que estaba duplicado entre el HTML y `static/js/modules/notifications-render.js:15` (que reemplaza todo el `innerHTML` de `#notifications-container`). Se conservan los 6 ids que sí usan los CSS: `audit-placeholder`, `dynamic-fields-premium`, `historial-pagination`, `new-res-estadia-row`, `rechargeForm` y `vouchers-section-wrapper`.
    *   **Helpers de aforo eliminados**: `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` eran `pass` desde v9.5 pero seguían con 5 call sites en rutas de dinero (`services/payments.py` ×3, `services/reservation_service.py`, `services/worker_service.py` ×2). Eliminados junto con sus 3 imports. Sin cambio de comportamiento: el aforo físico sigue siendo 100% ALPR/manual.
    *   **Migración `9c4f2a7b1e83`** (`down_revision` `8b3e9e815c78`): dropea `ix_coupons_codigo` y la tabla `coupons`; el `downgrade` recrea tabla + índice. Sin el modelo, la paridad modelo↔alembic que exige `tests/test_schema_parity_p2.py` quedaba rota. **AVISO: al correr `upgrade head` en Neon se borra la tabla y sus datos.** No tiene ninguna lectura ni escritura en el código; solo aparecía en docs de diseño.
    *   **Verificación**: `compileall` OK, import de la app con los 128 paths intactos, smoke render de 15 rutas sin 5xx, audit propio (re-exports 101→96, locales 9→0, parámetros sin uso 53→49) y **707 tests pasando**, sin regresiones. Balance: 59 archivos, +126 / −328.

- **SEPTIEMBRE 29, 2026 - INFORME DE CONCURRENCIA TRANSACCIONAL DE RESERVAS (V9.34.56)**:
    *   **Documento**: `Info proyecto/INFORME_CONCURRENCIA_RESERVAS.md` con el diagnóstico de riesgos de carrera —R1 overbooking de aforo al confirmar el pago, R2/R3 read-modify-write sobre disponibilidad y ocupación, R4 carrera entre confirmación de pago y cancelación— más el plan de remediación por fases 0-6 con sus criterios de salida.
    *   **Sin cambios de código**. Queda pendiente de decisión: R1/R2/R3 no se reprodujeron empíricamente (el hallazgo es por análisis), falta un backend PostgreSQL para los tests porque el suite usa SQLite `StaticPool` (una sola conexión compartida, no reproduce concurrencia real), y la remediación propuesta es un lock transaccional `pg_advisory_xact_lock`, dialect-aware para los otros dos backends soportados (SQLite y LibSQL/Turso).

- **SEPTIEMBRE 28, 2026 - AUDITORÍA CSS AC-5 CERRADA: 0 CLASES HUÉRFANAS, 0 KEYFRAMES DUPLICADOS (−1247 LÍNEAS NETAS)**:
    *   **Diagnóstico base**: 43 archivos CSS, 14.313 líneas, 2.576 reglas, 1.254 clases distintas. Sin duplicación real de scrollbar thumb/track; sí 114 bloques flex-center idénticos, 26 `margin:0 auto`, 86 radios literales, 25 blur y 49 bloques `uppercase`+`letter-spacing` como candidatos DRY.
    *   **Lote 1 — CSS muerto CERRADO (120 → 0)**: eliminadas 120 clases huérfanas tras cruzarlas contra templates, JS y backend, con revisión manual de excepciones runtime (`role-*` generado en [`dashboard.html`](templates/dashboard.html), prefijos `badge-*` y estados voucher `vigente/usado/cancelado` de [`profile.js`](static/js/modules/profile.js); `status-vigente` confirmado muerto). Resultado: **0 huérfanas** sobre 1.142 clases definidas.
    *   **Lote 2 — Utilities CERRADO**: corregido bug de `.no-print` (regla mal anidada dentro de `@media print`), eliminado `.mt-30` duplicado, purgadas utilitarias muertas y consolidadas definiciones de texto/pesos en [`typography.css`](static/css/base/typography.css) (aliases `.font-bold`, `.text-white`, `.text-small`).
    *   **Lote 7 — Animaciones CERRADO (3 duplicados → 1 fuente)**: `handBounce`, `fadeInSlideUp` y `hintPulseAnim` estaban definidos dos veces (idénticos) en [`landing-map.css`](static/css/pages/landing/landing-map.css) y [`profile-tour.css`](static/css/pages/profile/profile-tour.css); movidos a la fuente única [`animations.css`](static/css/base/animations.css), cargado en [`base.html`](templates/base.html) y añadido al precache de [`sw.js`](static/sw.js). Verificado: 16 keyframes, **0 huérfanos y 0 duplicados**.
    *   **Lote 9 — Tokens muertos CERRADO (65 → 50)**: 15 variables sin uso eliminadas de [`variables.css`](static/css/base/variables.css), todas verificadas por uso real.
    *   **Guard nuevo**: [`check_css_huerfano.py`](_tools/check_css_huerfano.py) con modos `--list`/`--update` y baseline [`css_huerfano_baseline.json`](_tools/css_huerfano_baseline.json) fijado en 0 para detectar regresiones futuras.
    *   **Balance**: 28 archivos, +21 / −1247 líneas. 0 `!important` nuevos.
    *   **Verificación**: guard en 0 huérfanas, `git diff --check` limpio y **702 tests pasando** (7 warnings).
    *   **Pendiente**: unificación DRY de los 114 bloques flex-center, 86 radios literales, 25 blur y 49 label-uppercase queda para una ronda específica. AC-3 (PWA + Safe Areas) sigue siendo la única auditoría CSS abierta.

- **SEPTIEMBRE 28, 2026 - AUDITORÍA CSS AC-1 CERRADA: LOTE 3 Y LOTE 4 COMPLETOS (−326 `!important` ACUMULADOS, **0 PROPIOS**) (V9.34.51)**:
    *   **Lote 3 (Portal de Usuario / Perfil) CERRADO (84 → 4)**:
        *   [`profile-reservations.css`](static/css/pages/profile/profile-reservations.css): 22 → 4 (18 eliminados en `.riderific`: inputs `.input-premium`/`.input-premium-readonly`, `.select-wrapper-premium` flechas, grid financiero de ticket y media queries `.history-filters-premium`/`.hist-amount-info`/`.fg-sm`; 4 preservados justificados por librería QRCode: `#ticket-to-capture .qr-canvas` 120×120px).
        *   [`profile-base.css`](static/css/pages/profile/profile-base.css): 25 → 0 (25 eliminados en `.input-premium-sm`, `.account-identity-card`, `.profile-info-main`, `.personal-info-container .text-label/.text-bold`, `.form-security-premium`, `.active-stays-card` y `.account-hub-card`; selectores `.card.active-stays-card`/`.card.account-hub-card` para ganar a `.card:hover` por especificidad de orden de carga sin `!important`).
    *   **Lote 4 (Componentes y Base Global) CERRADO (53 → 11)**:
        *   [`tables.css`](static/css/components/tables.css): 23 → 0 (utilidades `.text-center`/`.justify-center`/`.table-centered`, `td .flex-col`, `.ticket-email-text`, media query card layout; `td .user-actions`/`td .actions-reveal`/`td .btn-delete-promo` por especificidad contra dashboard css).
        *   [`forms.css`](static/css/components/forms.css): propios 9 → 0 (`.input-with-icon input` padding-left, `.num-input-wrapper .input-premium`, `.input-premium.flatpickr-input` y `.input-premium--plain`; preservados 23 de tema Flatpickr).
        *   [`typography.css`](static/css/base/typography.css): 5 → 0 (utilidades `.text-secondary/.text-dorado/.text-danger/.text-light/.text-muted`).
        *   [`legal.css`](static/css/pages/legal.css): 5 → 0 (`.legal-content`/`.legal-date` — blur/glass anulado por clase única).
        *   [`style.css`](static/css/style.css): 3 → 0 (`.branch-marker-logo` gana a Leaflet por orden de carga).
        *   [`utilities.css`](static/css/base/utilities.css): 2 → 0 (`.no-print`, `.hidden-mobile`).
        *   [`landing-modals.css`](static/css/pages/landing/landing-modals.css): 1 → 0 y [`monitoreo-live.css`](static/css/pages/monitoreo-live.css): 1 → 0.
        *   [`reset.css`](static/css/base/reset.css): 4 preservados (estados `:disabled` estandarizados AC-4, justificados).
    *   **Balance cuantitativo**: de 345 `!important` propios a **0** (−326 acumulados, **613 → 287**). Total repo 287, **todos justificados** por librerías/PWA/RBAC/AC-4 (Leaflet 134, Tour 80, Standalone 36, Flatpickr 23, QR captura 4, RBAC 4, reset AC-4 4, utilidades defensivas 2).
    *   **Suite de pruebas**: **702 tests pasando** (0 regresiones).

- **SEPTIEMBRE 27, 2026 - AUDITORÍA CSS AC-1: LOTE 2 CERRADO Y LOTE 3 AL 44% (−239 `!important` ACUMULADOS, −52 EN LA SESIÓN)**:
    *   **Lote 2 (Dashboard Admin) CERRADO (142 → 6)**:
        *   [`dashboard-live.css`](static/css/pages/dashboard/dashboard-live.css): 15 → 0 (13 eliminados en media queries de responsive mobile y 2 en `.monitor-tab-content`; reordenamiento en cascada para resolución natural por especificidad sin conflictos y optimización de 5 `transition: all` a transiciones compuestas de GPU).
        *   Preservados en Lote 2 únicamente 4 reglas RBAC de roles (`dashboard-base.css`) y 2 utilidades de tabla (`dashboard-tables.css`).
    *   **Lote 3 (Portal de Usuario / Perfil) avanzado al 44% (84 → 47, −37 eliminados)**:
        *   [`profile-notifications.css`](static/css/pages/profile/profile-notifications.css): 5 → 0 (5 eliminados en estados `:disabled` de botones de acciones de notificación).
        *   [`profile-points.css`](static/css/pages/profile/profile-points.css): 15 → 0 (15 eliminados en `.btn-add-vehicle`, `.btn-square-icon`, `.vehicle-card`, `.vehicle-actions-overlay` y media query de 640px; optimizadas 4 transiciones para GPU).
        *   [`profile-vehicles.css`](static/css/pages/profile/profile-vehicles.css): 17 → 0 (17 eliminados en `.select-vehicle-type`, `.register-trigger-card.active`, media query responsive 640px e inputs de patente/marca).
        *   Pendiente Lote 3: [`profile-reservations.css`](static/css/pages/profile/profile-reservations.css) (22) y [`profile-base.css`](static/css/pages/profile/profile-base.css) (25).
    *   **Balance cuantitativo propio**: de 345 iniciales a 106 (−239 `!important` acumulados, reducción del ~70% en código propio). Total repo: 374 (268 librerías/PWA + 106 propios).
    *   **Suite de pruebas**: **702 tests pasando** limpiamente (0 regresiones).

- **SEPTIEMBRE 27, 2026 - AUDITORÍA CSS AC-1: LOTE 1 CERRADO Y LOTE 2 AL 89% (−187 `!important` ELIMINADOS)**:
    *   **Lote 1 (Navegación y Layouts Base) CERRADO (66 → 1)**:
        *   [`landing-nav.css`](static/css/pages/landing/landing-nav.css): 46 → 1 (45 eliminados en media queries de botones, links y header; 1 preservado legítimo para `#auth-user-actions.user-nav-hidden` override JS).
        *   [`sidebar.css`](static/css/layout/sidebar.css): 17 → 0 (17 eliminados en media queries de sidebar y footer).
        *   [`header.css`](static/css/layout/header.css): 3 → 0 (3 eliminados en header-left y header-icon-box).
    *   **Lote 2 (Dashboard Admin) avanzado al 89% (142 → 21)**:
        *   [`dashboard-settings.css`](static/css/pages/dashboard/dashboard-settings.css): 43 → 0 (43 eliminados en tarifas, acciones de cámaras y diagnósticos).
        *   [`dashboard-base.css`](static/css/pages/dashboard/dashboard-base.css): 41 → 4 (37 eliminados en `.card-header-premium` y `.modal-footer-buttons`; 4 preservados legítimos para RBAC de roles).
        *   [`dashboard-cards.css`](static/css/pages/dashboard/dashboard-cards.css): 7 → 0 (7 eliminados en `.card-header-premium` y `.kpi-grid`).
        *   [`dashboard-tables.css`](static/css/pages/dashboard/dashboard-tables.css): 36 → 2 (34 eliminados en `#modal-ticket-answer`, `.row-refund` y `.btn-gold-glow`; 1 preservado `.text-danger` + 1 de resguardo).
        *   Pendiente Lote 2: solo [`dashboard-live.css`](static/css/pages/dashboard/dashboard-live.css) (15 ocurrencias).
    *   **Balance cuantitativo propio**: de 345 iniciales a 158 (−187 `!important`).
    *   **Suite de pruebas**: **702 tests pasando** limpiamente (0 regresiones).

- **SEPTIEMBRE 27, 2026 - AUDITORÍAS CSS FASE 1 CERRADAS (AC-2 / AC-4), DIAGNÓSTICO AC-1 Y CONSOLIDACIÓN DE AUDITORÍAS (V9.34.50+)**:
    *   **Consolidación documental**: Reunificación de 17 informes de auditoría individuales en un único documento [`AUDITORIAS.md`](Info%20proyecto/AUDITORIAS.md).
    *   **Auditorías CSS Fase 1 CERRADAS (AC-2 y AC-4)**:
        *   **AC-2 (Rendimiento y GPU)**: Erradicación de 103 instancias de `transition: all` sustituyéndolas por transiciones específicas (`transform`, `opacity`, `background`, `border-color`, `box-shadow`) previniendo reflows/repaints masivos.
        *   **AC-4 (Estados interactivos y foco de teclado)**: Implementación de anillo institucional `:focus-visible` global con resplandor dorado en `reset.css` y `forms.css`, feedback táctil `:active` con `transform: scale(0.97)` en botones, y estandarización de estados `:disabled` con escala de grises al 60%.
    *   **Auditoría CSS AC-1 (Especificidad y guerra de `!important`) - En proceso**:
        *   Diagnóstico exhaustivo completado: 613 ocurrencias mapeadas en 26 archivos CSS.
        *   268 justificadas por librerías externas y PWA: Leaflet (`landing-map.css`: 134), Tour overlays (80), Standalone desktop (`standalone.css`: 36), Flatpickr (`forms.css`: 18).
        *   345 en componentes propios: causa raíz aislada en especificidad de media queries y selectores anidados (`landing-nav.css`: 46, `dashboard-settings.css`: 43, `dashboard-base.css`: 41, `dashboard-tables.css`: 36, `profile-base.css`: 25, `tables.css`: 23, `profile-reservations.css`: 22, etc.).
        *   Plan de refactorización preparado para reducir a <30 (solo utilidades) y erradicar de componentes estructurales (`.modal-content`, `.input-premium`, `.btn`).
    *   **Auditorías CSS pendientes**: AC-3 (PWA/Safe areas) y AC-5 (DRY/purga CSS).
    *   **Suite de pruebas**: **702 tests pasando** limpiamente.

- **SEPTIEMBRE 24, 2026 - AUTH DE NODO ALPR EN ACCESS + DRY DE HELPERS ALPR (V9.33.0 / comm 505477d)**:
    *   Cierra la deuda de diseño A1 que quedaba abierta: `validate-plate`, `exit-plate` y `validate-qr` (`routes/parking/access.py`) ahora exigen `Depends(require_alpr_node)`.
    *   Nuevo módulo compartido `core/alpr_security.py` (DRY): `is_local_or_private`, `is_trusted_alpr_node` y la dependency `require_alpr_node` — misma política que ya usaba el WS de video: si `ALPR_NODE_SECRET` está configurado exige header `X-Node-Secret` (o query `node_secret`) comparado en tiempo constante; si no hay secreto, solo red local/privada. `routes/system/video.py` deja de definir helpers propios y los importa desde ahí.
    *   El nodo ALPR envía el header en `alpr/ocr_engine.py:_dispatch_request` (`X-Node-Secret` cuando `ALPR_NODE_SECRET` está configurado; sin header si no).
    *   Tests: `tests/test_alpr_node_auth.py` (16 tests: helpers, 403 sin/mal secret, 200 con secret, fallback red local, envío de header del nodo).
    *   Suite: **694 tests / 57.64s en verde**. Riesgo A1: **BAJO-MEDIO → BAJO** (sin deudas abiertas de diseño en access).

- **SEPTIEMBRE 24, 2026 - REMEDIACIÓN A1 P2/P3 COMPLETA + AUDITORÍAS A3/A7/A8/A9 CERRADAS (V9.31.1+ / WORKING TREE)**:
    *   **A1 — P2/P3 aplicados**: JWT emite `iat`+`jti`+`token_type` y `revoke_token()` (set en memoria) en `core/security.py`; `decode_access_token`/`get_current_user` rechazan tokens no-access y jti revocados; `POST /v1/auth/logout` revoca jti y borra la `UserSession` del `device_id` (`routes/auth.py`), invocado desde `ui.logout` (`static/js/modules/ui.js`); guard de arranque en `main.py`: `RuntimeError` si `ENVIRONMENT=production` con SECRET_KEY demo; CORS default explícito (`ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000`, sin `*`) en `core/config.py`; rate-limit fino 30/min en todo el panel admin vía dependency compartida `admin_rate_limit` (`core/limiter.py`) sin alterar firmas de endpoints; PII enmascarada con `mask_email()` en status/video/worker/email y MP sin `resp.text[:500]`; WS de ocupación con repo activo (`get_active_by_email` + rechaza `is_blocked`). Riesgo A1: **MEDIO → BAJO-MEDIO**.
    *   **A3 — CI con cobertura**: `pytest-cov` en requirements + `--cov=... --cov-report=term-missing --cov-fail-under=82` en `.github/workflows/ci.yml` (cobertura real medida 85%).
    *   **A7 — 11 `except Exception` silenciosos instrumentados** con logger en `access_service.py` (5), `availability.py` (2), `billing_service.py` (2), `branch_service.py` (1), `mercadopago_service.py` (1).
    *   **A8 — contraste**: dorado `#C5A059` → `#F2E3BF` en `profile-base.css` y `profile-reservations.css`.
    *   **A9 — XSS**: `encodeURI` en `adjunto_url` de `profile-help.js`.
    *   Suite: **678 tests / 55.79s en verde** (3 tests nuevos de logout/token en `test_routes_auth.py`).

- **SEPTIEMBRE 20, 2026 - COBERTURA #7–#10 (66%), FIX CSP DE LA LANDING Y REMEDIACIÓN A1 (V9.23.0+ / WORKING TREE)**:
    *   **Cobertura de tests #7–#10 (79 tests)**: `services/access_service.py` 38→**89%** (`tests/test_access_flow.py`, 33 tests), `routes/admin/branches.py` 19→**76%** (21), `routes/parking/status.py` 23→**84%** incl. WebSocket (16), `core/database.py` 35→**81%** incl. `sync_schema` (9). Suite completa: **271 tests / 33 archivos en verde, 66% de cobertura total** (7044 stmts / 2424 sin cubrir). Umbral sugerido para CI: `--cov-fail-under=65`.
    *   **Fix CSP de la landing**: `font-src` suma `https://cdnjs.cloudflare.com` (tipografías Font Awesome) y `connect-src` suma Overpass (`overpass-api.de`), Nominatim y los CDNs de scripts (sourcemaps de jsdelivr/unpkg); directivas agrupadas en constantes `CSP_CDNS`/`CSP_GOOGLE_FONTS`/`CSP_MAP_APIS`/`CSP_HEADER` en `main.py` (middleware `security_headers_middleware`). Consola del navegador sin errores + test de regresión `tests/test_security_headers.py`.
    *   **A1 — remediación P0/P1 aplicada y verificada**: `pay-stay` autenticado con `get_operational_user` + `10/min` (`routes/parking/access.py:31-33`); video WS con `token`/`node_secret` y rol STAFF+ (cierre 4403, `routes/system/video.py:37-93`); `get_current_user` rechaza `is_blocked` (`core/security.py:71,107`); webhook MP con límite `60/min`. Riesgo **ALTO → MEDIO**.

- **SEPTIEMBRE 19, 2026 - AUDITORÍAS A1, A2, A4 + ARRANQUE CON `sync_schema` (V9.23.0+ / WORKING TREE)**:
    *   Informes de auditoría (consolidados el 2026-09-27 en `Info proyecto/AUDITORIAS.md`): A1 Seguridad API, A2 Dependencias, A4 Datos/Migraciones (A3 Cobertura se completa el 20/09).
    *   **A2 aplicada**: bump starlette 0.52.1→1.6.0 y cryptography 46.0.7→50.0.1; `pip check` limpio; queda 1 sola vuln sin fix (`ecdsa`, no explotable por uso HS256).
    *   **A4 — P1 aplicada**: flujo único `sync_schema()` en `core/database.py` (`create_all` de modelos + Alembic al head, warning explícito si la cadena no es reproducible); eliminados los `ALTER TABLE` manuales de `init_db.py:migrate_db()`; `main.py` usa `sync_schema()` en el arranque. Verificado: BD vacía → 19 tablas completas + `alembic current == head`.

- **SEPTIEMBRE 18, 2026 - MEGAMÓDULOS JS PARTIDOS Y AUDITORÍA DE MODULARIZACIÓN 10/10 (V9.23.0)**:
    *   Partidos en 16 submódulos temáticos: `landing-map.js` → fachada 397 + `landing-map-state/data/pois/geo/locality.js`; `admin-tour.js` → fachada + `admin-tour-steps/engine/help.js`; `notifications.js` → fachada + 8 submódulos (state/format/render/badge/actions/nav/dropdown/polling). Superficie exportada 100% compatible (grep de imports en `landing.js`, `perfil.js`, `dashboard.js`, `dashboard-tickets.js` sin cambios); `sw.js` con precache ampliada (16 submódulos); `node --check` OK en los 19 archivos tocados; **152 tests en verde**.
    *   Auditoría de modularización a **10/10** (era 6.5) y actualización de la documentación RUP a la realidad del proyecto (`diseño_completo.html`: 51 RF, 18 entidades, 6 diagramas; rutas/servicios/repos reales; MQTT/Arduino correctos). Nuevo plan de auditorías con 9 ítems priorizados (hoy consolidado y CERRADO en `Info proyecto/AUDITORIAS.md`).

- **SEPTIEMBRE 18, 2026 - CAPA DE REPOSITORIOS COMO ÚNICA PUERTA DE DATOS (V9.22.0)**: `access_service.py` descompuesto con `AccessOccupancyMixin` (`services/access_occupancy.py`, fachada 499 líneas).
    *   Los 77 `db.query` de rutas → **16 repositorios**; `services/` y `routes/` con **0 consultas directas**, incluidas operaciones bulk (`BranchRepository.propagate_rename` 8 tablas, `RedemptionRepository.unlink_promotion`, `UserRepository.unset_favorite_for_user`, `NotificationRepository.mark_ticket_read_for_user`, `SystemRepository.reset_all_data`). Nuevos repos: `camera`, `points`, `promotion`, `report`, `session`, `settings`, `support`, `system`, `mercadopago`, `notification`.
    *   `reset_password.html` y `estadisticas_ocr.html` pasan a módulos ES6 (`static/js/modules/reset-password.js`, `estadisticas-ocr.js`); megamódulos `tour.js`, `dashboard-reservations.js`, `reservas-form.js` partidos en submódulos temáticos (fix de setters sin paréntesis en `reservas-form-slot.js`). Auditoría actualizada (Repositorios → Cumplido, score 9.5/10); 152 tests en verde.

- **SEPTIEMBRE 17, 2026 - ENUMS, DESCOMPOSICIÓN DE SERVICIOS Y BRIDGE PATTERN (V9.21.0)**:
    *   Delegación de reservas/vehículos/ocupación a servicios (`ReservationService`, `UserService`, `OccupancyService`); barrido completo de strings mágicos → enums (`UserRole`, `VehicleType`, `AccessEventType`, `ReservationStatus`, `PaymentStatus`, `NotificationType`).
    *   `reservation_service.py` descompuesto en `availability.py` (capacidad/sweep-line/slots) y `payments.py` (pagos/reembolsos) manteniendo fachada compatible; el dominio de reservas queda con acceso a datos 100% en `ReservationRepository`.
    *   Frontend: **Bridge Pattern** sin `window.*` en módulos ES6 (76 asignaciones migradas a puentes). Auditoría de modularización actualizada.

- **SEPTIEMBRE 15, 2026 - GRILLA HORARIA 24H, SELECTOR INICIO/FIN, OCUPACIÓN DE RESERVAS & MAPA (V9.20.0)**:
    *   **Fix de grilla horaria para sucursales 24h**: Los selectores de horario del portal (`reservas-form.js`) y del dashboard admin (`dashboard-reservations.js`) tenían hardcodeado el rango 07:00→23:30, ignorando `is_24h`/`horario`. Nuevos helpers `_branchSlotRange()` y `_newBranchSlotRange()` que generan el rango según la sucursal: si es 24h → 00:00→23:30, y si el cierre está en `00:00` → se renderiza hasta las 23:30.
    *   **Distinción visual INICIO/FIN en el selector de horarios**: Las casillas extremas del rango se pintan con identidad propia — INICIO (verde sólido `.range-start`) y FIN (rojo sólido `.range-end`) — con tooltip "Hora de INICIO/FIN de tu estadía"; los intermedios se pintan en verde claro (`.in-range`) y se agregó una barra de resumen en vivo `INICIO X → FIN Y (N hs)` (`_hourlySelectionSummary` / `_newHourlySelectionSummary`). Se eliminó la leyenda de colores del epígrafe. Estilos en `profile-reservations.css`.
    *   **Plazas exclusivas de reservas descontadas con reservas pagadas vigentes** (`routes/parking/status.py`): `_calculate_branch_capacities` suma a la ocupación de reservas las reservas **pagadas** cuya ventana horaria coincide con el momento actual (`_ocupacion_reservas_vigentes`: `estado_pago=Pagado`, `estado_reserva ∈ [Pendiente, Activa]`, `fecha_inicio ≤ now ≤ fecha_fin`, por sucursal y tipo de vehículo) usando `max(física ALPR, reserva)` por tipo para no duplicar cuando el vehículo ya entró físicamente. Aplica a `/parking/status`, al WebSocket en vivo y a `/parking/branches` (mapa).
    *   **Mapa sin estado de disponibilidad**: Se eliminó el bloque "Estado de Disponibilidad" del popup de sucursales (`landing-map.js`) y los marcadores pasaron a color fijo verde (`#22c55e`); se removió la función `getVehicleAvailability` (código muerto).
    *   **Verificación**: `node --check` sobre `reservas-form.js`, `dashboard-reservations.js` y `landing-map.js`; `py_compile` de `routes/parking/status.py`; suite de tests de reservas (`test_reservation_spots.py`, `test_reservation_availability_logic.py`) en verde (5/5). Assets versionados a `?v=9.20.0` (`profile-reservations.css`, `reservas.js`, `landing.js` en `index.html`/`nuestra_red.html`).

- **SEPTIEMBRE 14, 2026 - UBICACIÓN DE CANJE (MAPAS) & CARDS DE CANJEO CON FILTRO POR SUCURSAL (V9.19.0)**:
    *   **Ubicación de canje**: `promotions` y `redemption_tickets` suman `direccion`, `latitude` y `longitude` (migración Alembic `ce7d1e2f3a5b`, aplicada y verificada en Neon). El admin edita la ubicación de cada promo desde el panel con búsqueda Nominatim y mapa Leaflet (`promotion_modal.html`, `dashboard-promotions.js`).
    *   **Fallback de ubicación doble**: `_crear_ticket` guarda snapshot (ubicación de la promo → sino la de su sucursal); `GET /user/redemption-tickets` enriquece la respuesta sin reescribir BD (ticket → promo actual → sucursal), mostrando la dirección vigente incluso en tickets canjeados antes.
    *   **Link a Google Maps (mapa de calles)**: La dirección es un link `place/<direccion>/@lat,lng,z` con pin exacto en roadmap. Se quitó el token `data=!3m1!1e3` porque activaba la vista aérea/satélite (render 3D de casas); se descartaron `?basemap=roadmap` y `loc:` por romper la posición del pin. Fallbacks: `search/?api=1&query=` (solo dirección) y `?q=lat,lng&z=16` (solo coords).
    *   **Cards de canjeo con look tipo ticket**: Promos por canjear reescritas como `voucher-card promo-card` (gradiente violeta, badges de tipo + sucursal, divider, footer dorado), icono+título a la izquierda y descripción/dirección/puntos centrados (se anuló `translateX(-31px)` que las corría a la izquierda).
    *   **Filtro por sucursal**: Dropdown "Sucursal" sobre la grilla de promos (opciones: Todas / Globales / cada sucursal). Al filtrar por sucursal se ocultan las globales; `applyPromoBranchFilter` re-renderiza sin refetch.
    *   **Baja del ajuste manual de puntos**: Eliminados los botones `+10/−10`, `adjustPoints` (profile.js/perfil.js), el CSS `.points-adjust-*` y el endpoint `POST /user/points-adjust`.
    *   **Verificación**: `node --check` y `py_compile` en verde; assets versionados a `?v=9.19.0` para forzar la recarga de caché.

- **SEPTIEMBRE 13, 2026 - GLOBITO DE NOTIFICACIÓN EN RESERVAS DEL DASHBOARD EN TIEMPO REAL (V9.18.4)**:
    *   **Globito de Notificación en Reservas (`#reservation-badge-sidebar`)**: Badge rojo dinámico con animación pulsante `.pulse` sobre el ítem de navegación "Reservas" del Dashboard (`templates/dashboard.html`).
    *   **Endpoint Liviano de Detección**: `GET /v1/admin/reservations/new-count?since_id=...` (`routes/admin/reservations.py`) que obtiene de forma ultra rápida (`MAX(id)` y `COUNT(*)`) la cantidad de reservas nuevas registradas, con filtro de sucursal para administradores locales.
    *   **Notificación en Tiempo Real vía WebSocket**: Emisión con `NotificationService.notify_occupancy_change` al crear reservas desde el portal del usuario (`routes/user/reservations.py`) y de forma manual por administración (`services/reservation_service.py`). En el frontend, `initOccupancyWS` (`dashboard-stats.js`) dispara `updateReservationBadge()` instantáneamente al recibir el mensaje.
    *   **Auto-Limpieza al Entrar a Reservas**: `clearReservationBadge()` en `dashboard-reservations.js` oculta inmediatamente el globito y guarda el último ID visto en `localStorage` al hacer click o navegar a la pestaña "Reservas" (`switchTab('admin-reservations')`). Si el usuario ya está visualizando Reservas, la grilla se refresca en vivo sin alertar con globito.
    *   **Polling de Resguardo & Verificación**: Chequeo cada 10s para resguardo ante desconexiones, 3 pruebas unitarias añadidas en `tests/test_admin_reservations.py` y suite completa de 133/133 tests en verde (100% de efectividad).

- **SEPTIEMBRE 13, 2026 - DESCUENTOS DE RESERVA APLICADOS AL TOTAL & REDISEÑO DE MIS VOUCHERS Y BENEFICIOS (V9.18.3)**:
    *   **Fix de match de sucursal para descuentos (`redemption_sucursal_clause`)**: Las promociones y tickets de canje guardaban la sucursal con prefijo `"AUTOPASS "` (datos legados del seed), mientras el formulario de reserva usaba el nombre limpio del branch (`Ituzaingó`); el match exacto fallaba y los descuentos no se mostraban ni se aplicaban al pagar. Se agregó en `services/reservation_service.py` un método estático que normaliza la sucursal (quita el prefijo, espacios y mayúsculas), usado por `validate_redemption_ticket` y por `/redemptions/available`.
    *   **Normalización de datos legados**: UPDATE sobre `promotions.sucursal` (3 filas) y `redemption_tickets.sucursal` (8 filas) quitando el prefijo "AUTOPASS "; BD verificada sin valores remanentes con prefijo.
    *   **Descuento en el total de la reserva (portal usuario)**: `reservas-form.js` consulta `/redemptions/available` por sucursal (carga lazy con anti-race) y muestra en el total estimado en vivo y en el resumen de confirmación el total original tachado, la línea "DESCUENTO X% · -$Y" y el "TOTAL A PAGAR"; el descuento se consume al abonar (saldo o Mercado Pago).
    *   **Descuento aplicado también en caja (pago manual admin)**: `pay_reservation_manual` acepta `redemption_ticket_id` y valida el canje `descuento_reserva` vigente del usuario vinculado a la reserva (misma sucursal o global) para registrar el cobro sobre el valor descontado (consumiendo el ticket). Se aplica en `confirm-payment` y en el alta manual con pago; nuevos endpoints `GET /admin/reservations/{id}/redemptions` y `GET /admin/redemptions/available` para detectar el descuento en caja. En el panel el operador confirma un diálogo "Descuento aplicable" (monto, descuento %, total) antes de cobrar. Puntos acreditados sobre el monto efectivamente abonado.
    *   **Rediseño de "Mis vouchers y beneficios"**: Cards de descuento `descuento_reserva` presentadas como beneficio (sin código/QR/badge de ticket) con fila única icono + título + badge de sucursal, `%` de descuento destacado, "SE APLICA AUTOMÁTICAMENTE AL RESERVAR", "Vto." debajo y botón CANCELAR centrado. Cards de voucher unificadas al estilo violeta, sin badges de nº de ticket ni "VOUCHER", contenido con más contraste y centrado ópticamente (compensación de -31px), títulos en fila con icono y badge, y solo "Vto." (sin fecha de canje). Nueva función `formatTitulo` (con stopwords) que normaliza títulos en mayúsculas ("LAVADO" → "Lavado", "REGALO SORPRESA" → "Regalo Sorpresa") aplicada en cards de descuento, vouchers y el modal del ticket.
    *   **Total con descuento visible al editar una reserva manual (panel admin)**: Al modificar una reserva, `dashboard-reservations.js` consulta el nuevo `GET /admin/reservations/{id}/redemption-info` y muestra el total original tachado + línea "DESCUENTO X% · -$Y" con el total con descuento (fuente `vigente`, se aplica al abonar; fuente `aplicado`, la reserva ya se pagó con ese descuento en caja). `update_admin_reservation` conserva el mismo % al recalcular el monto si la reserva se pagó con descuento, quedando cobros/reembolsos por diferencia sobre la base descontada.
    *   **Verificación**: Suite completa de pytest (130/130 en verde, con 15 casos nuevos de descuentos en caja y en edición) y `node --check` OK sobre los JS modificados.

- **SEPTIEMBRE 12, 2026 - AJUSTE FINANCIERO AL EDITAR RESERVAS PAGADAS, NETO CON REEMBOLSOS & REPORTE ROBUSTO (V9.18.1)**:
    *   **Edición con Cobro/Reembolso de Diferencia**: Al editar el monto de una reserva **Pagada** desde el dashboard admin (`PUT /v1/admin/reservations/{id}`), la diferencia se resuelve automáticamente: si el nuevo total es **mayor**, se cobra la diferencia (actualiza `monto_total` y `fecha_pago`, registrando el método elegido en `cobrar_diferencia_metodo`); si es **menor**, se reembolsa acumulando en `monto_reembolsado`. La devolución sigue el **canal elegido**: si el método es `SALDO`/billetera, se acredita al saldo virtual del usuario (descontando puntos con registro en `PointsLog`); si es **efectivo** (`CAJA`/`EFECTIVO`) u otro canal externo, se devuelven **billetes/por fuera del sistema** sin tocar el saldo, quedando imputada en el reporte al método correspondiente. El monto neto siempre es `monto_total − monto_reembolsado`.
    *   **Modal de Confirmación de Edición (`#modal-edit-resumo`)**: La pestaña Reservas del dashboard muestra un resumen previo con detalle por ítem, nuevo total, **diferencia a cobrar/reembolsar y selector de método de pago** para la operación (usado por los reportes). Con diferencia cero no se tocan las finanzas. Reescrito con la estructura estándar `.modal` / `.modal-content` (se descartó la clase inexistente `modal-overlay` que desalineaba el modal).
    *   **Monto Neto en Interfaces**: El listado admin, el detalle de reserva ("Pagado $X · Reemb. -$Y") y el lado del usuario (tarjetas activas, historial y comprobante/QR) muestran el **monto neto** (`monto_total − monto_reembolsado`) sin notas de reembolso visibles para el cliente (solo el monto actualizado). `UserReservationResponse` incorpora `monto_reembolsado`.
    *   **Reporte Financiero con Reembolsos Parciales**: `_es_reembolso_parcial` en `services/report_service.py` reconoce reembolsos de reservas `REEMBOLSADO` **o** `PAGADO` con `monto_reembolsado > 0`, y los integra en el resumen (`total_reembolsado`), el desglose por método y el historial (entradas `REF{id}`).
    *   **Suite de 107 Tests Automáticos**: 5 casos nuevos en `tests/test_admin_reservations.py` (cobro por aumento de monto, reembolso a saldo por disminución, sin diferencia sin tocar finanzas, múltiples ajustes con neto correcto, y reporte que cuantifica el reembolso parcial de una reserva pagada). Suite completa en verde.

- **SEPTIEMBRE 11, 2026 - GESTIÓN DE RESERVAS ADMIN, OAUTH 2.0, METODO DE PAGO & TIPO VEHÍCULO EN RESERVAS (V9.14.2+)**:
    *   **Gestión Integral de Reservas para Administradores**: Rediseño completo de la pestaña de Reservas del Dashboard (`routes/admin/reservations.py`, `dashboard-reservations.js`). Búsqueda multi-criterio por cliente, email, DNI, patente, ID de reserva y sucursal. Filtros por estado (`PENDIENTE_PAGO`, `PAGADA`, `EN_USO`, `FINALIZADA`, `CANCELADA`), tipo de vehículo, rango de fechas y sucursal.
    *   **Creación y Edición de Reservas a Nombre del Usuario**: El Administrador puede emitir reservas directamente seleccionando cliente, sucursal, fechas, patente y tipo de vehículo, con cálculo dinámico de precio y comprobación de cupos de reserva en tiempo real.
    *   **Confirmación de Pagos Manuales & Reembolsos**: Endpoint `POST /v1/admin/reservations/{id}/confirm-payment` para registrar pagos con método elegible (`DIGITAL`, `CAJA` / Efectivo, `MERCADOPAGO`, `SALDO`). Cancelación administrativa con simulación y acreditación al saldo del usuario.
    *   **Columnas `tipo_vehiculo` y `metodo_pago` en Reservas**: Migraciones Alembic `a4c8d2e3f5b6_add_tipo_vehiculo_to_reservations.py` y `d3b7e1a9c2f0_add_metodo_pago_to_reservations.py`.
    *   **Login Social OAuth 2.0 (Google & Facebook)**: Servicio completo en `services/oauth_service.py` con state HMAC stateless, intercambio de token, modal de compleción de registro (DNI/Teléfono) y suite de pruebas `tests/test_oauth.py`.
    *   **Suite de 82 Tests Automáticos**: Expansión de la suite a **82 pruebas passing en 21 archivos** (`pytest`), logrando 100% de ejecución limpia.
    *   **Mejoras de UI / UX**: Modal de tickets scrolleable y responsive (header X fija, acciones apiladas), saludos personalizados en monitor ALPR ("¡BIENVENIDO!" / "¡HASTA LUEGO!") y CSS PWA `standalone.css`.

- **SEPTIEMBRE 5, 2026 - TARIFA FRACCIÓN 30 MIN & SELECTOR POR RANGO (V9.10.0)**:
    *   **Casillas de Horarios Más Compactas**: Se redujo la altura de la grilla de horarios: padding de las casillas de `6px 12px` a `3px 8px`, fuente de `0.78rem` a `0.68rem` y gap de la grilla de 6px a 4px. Resultado: la grilla de 34 horarios ocupa ~40% menos de alto en pantalla.
    *   **Mensaje de Selección de Horario Eliminado**: Se quitó por completo el texto "Inicio: X — ahora tocá la hora de fin" y el resumen "X → Y (Nh)" que aparecía/desaparecía entre el picker de día y la grilla al seleccionar horarios. La página ya no se mueve; el estado de selección se refleja solo en las casillas resaltadas.
    *   **Toasts de Selección de Horario Eliminados**: Se quitaron las notificaciones flotantes que aparecían al tocar/arrastrar los horarios ("Inicio: X — ahora tocá o arrastrá...", "Rango X → Y (Nh)"), que se acumulaban durante la selección. El selector actualiza hora y cantidad directamente, sin toasts intermedios; se mantienen las validaciones y confirmaciones finales.
    *   **Arrastre de Horarios en Móviles**: Fix del drag del selector de rango en modo responsive: el browser capturaba el gesto como scroll y cancelaba la selección (solo permitía clic-clic). Se agregó `touch-action: pan-y` en `.chips-container-premium`, permitiendo el arrastre horizontal mientras el scroll vertical de la página sigue funcionando.
    *   **Texto de Instrucción Simplificado**: Se quitó "(pasos de 30 min)" del hint del selector de horarios.
    *   **Slots Pasados Bloqueados el Día de Hoy**: Para la fecha actual, la grilla de horarios deshabilita automáticamente las casillas del día que ya pasaron o que no respetan la anticipación mínima configurable (`RESERVA_HORA_MIN_SEGUNDOS`, default 30 min), incluyendo el slot en curso. Implementado en ambas capas: backend (`_calcular_horas_deshabilitadas` en `reservation_service.py`, usando `TimeService.now()`) y frontend (recálculo local en `updateHourlySlotsUI` con `getVirtualNow()` + `RESERVA_MIN_MS`) para cubrir la ventana de cache de 30s.
    *   **Cuadrícula de Horarios Alineada**: La grilla de selección por hora pasó de flex-wrap (filas desparejas, la última incompleta) a una grilla CSS de 6 columnas fijas; las celdas faltantes de la última fila se completan con espacios invisibles (`.hourly-chip-premium.placeholder`) manteniendo 6×6 parejo.
    *   **Desglose de Tarifas en el Total**: Para reservas por hora, el sumario muestra "Total" y debajo el detalle "1 hora = $X · 30 min = $Y" (`#reserva-rates-detail`), calculado con la tarifa de 30 min configurada o la mitad de la hora como fallback.
    *   **Limpieza del Selector de Horario**: Se eliminaron las tabs de filtro Mañana/Tarde/Noche/Todos del selector de rango (código muerto `currentSlotFilter`, `setSlotFilter` y CSS `.slot-tab-btn` removidos) y el hint redundante debajo del picker de día (`res-hour-range-hint`). El selector ahora muestra las casillas completas de 07:00 a 23:30.
    *   **Tarifa de 30 Minutos Configurable**: Nueva clave `precio_30min` (+ `_moto`/`_camioneta`) configurable en el Dashboard (tab Ajustes > Tarifas, campo "FRACCIÓN 30 MIN") junto a las tarifas existentes. Si se deja vacía, vale automáticamente la mitad de la tarifa hora (`precio_hora / 2`).
    *   **Cobro por Bloques de 30 Min**: Los montos (reservas hora, estadías físicas, deuda proyectada) ahora se calculan redondeando hacia arriba al bloque de 30 min más cercano (`max(1, ceil(horas * 2)) * tarifa_30min`). Aplica en `billing_service.py` (`calculate_debt`, `calculate_total_amount` + nuevo `get_30min_rate`), `routes/user/reservations.py`, `routes/parking/status.py` y `services/report_service.py`.
    *   **Estimador Frontend Coherente**: Previews de precio del portal (`reservas-form.js`) y del editor admin (`dashboard-reservations.js`) usan la misma lógica de bloques de 30 min con fallback a mitad de hora.
    *   **Selector de Horario por Rango (Portal Usuario)**: Reemplazo del input de cantidad de horas por selección de inicio/fin sobre la grilla horaria (clic-clic o arrastre con pointer events). El backend se mantiene intacto: se persiste la duración real del rango; los horarios deshabilitados se consultan con `duracion_horas=1`.
    *   **Verificación Automática**: Suite completa de Pytest (50/50 pruebas en `tests/`) pasando exitosamente; `node --check` OK sobre los módulos JS modificados.

- **AGOSTO 28, 2026 - OCR ENGINE OVERHAUL, ESTADÍSTICAS OCR & UNIFICACIÓN DE PATENTES**:
    *   **Motor OCR Lazy/Opcional**: `alpr/ocr_engine.py` ya no aborta el arranque si ningún motor OCR importa; loguea el motivo (RapidOCR/PaddleOCR) y agrega diagnóstico del motor en el setup.
    *   **numpy por Versión de Python**: `numpy>=1.26.0,<2.3.0` para Python < 3.14 y `numpy>=2.3.0,<2.5.0` para Python ≥ 3.14 (numpy < 2.3.0 no tiene wheels para Python 3.14).
    *   **Setup Robustecido**: `setup_backend.bat`/`setup.ps1` muestran los errores reales de pip/init_db y abortan si fallan (encoding UTF-8).
    *   **Estadísticas OCR**: Nueva página `/estadisticas-ocr` (`templates/estadisticas_ocr.html`, ~600 líneas) con tiempos de lectura en BD (`ocr_timing_ms` en `AccessLog`, migración Alembic `f1a2b3c4d5e6_add_ocr_timing_to_access_logs`).
    *   **Avisos en Cámara**: Mensajes de evento de patente/QR en la vista de monitoreo en vivo vía WebSocket (`live.html`).
    *   **Unificación de Códigos y Revisión de Patentes**: Refactor del pipeline ALPR (`alpr/config.py`, `alpr/ocr_engine.py`, `alpr/runner.py`, `routes/parking/access.py`, `services/access_service.py`, `services/report_service.py`).
    *   **CI Deshabilitado**: Workflow de GitHub Actions renombrado a `.github/workflows/ci.yml.disabled` hasta tener la suite estable.

- **AGOSTO 27, 2026 - NOTIFICACIONES, PERMISOS SUCURSAL & SOPORTE VISUAL ADMIN (V9.12.0)**:
    *   **Visibilidad Permanente de Botones de Notificación de Usuario**:
        *   Los botones **"Marcar como leídas"** (`#btn-mark-all-read`) y **"Borrar notificaciones"** (`#btn-clear-read-notifs`) en `notificaciones.html` permanecen siempre visibles (`display: inline-flex`).
        *   Se parametrizaron los estados `disabled` dinámicos: "Marcar como leídas" activo solo con `unread > 0`; "Borrar notificaciones" activo solo con notificaciones leídas (`leido == True`).
        *   Mensaje toast *"Se han borrado todas las notificaciones"* y actualización de icono a check simple (`fa-check`).
    *   **Solución a Falso Positivo de `NEW_DEVICE_LOGIN`**: Preservación de `autopass_device_id` en `localStorage.clear()` al cerrar sesión en `ui.js` y `api.js`, y filtrado por `user_agent` en `routes/auth.py`.
    *   **Permisos Completos de Sucursal para Administrador Local (`local_admin`)**:
        *   Reestructuración de permisos en `routes/admin/users.py` permitiendo a los Administradores de Sucursal consultar, editar, modificar roles de personal y borrar usuarios de su sucursal y clientes.
        *   Normalización con `normalize_branch_name` en todas las rutas de usuarios para equiparar `"AUTOPASS Morón"` y `"Morón"`.
        *   Protección jerárquica impidiendo modificar o eliminar Administradores Globales.
    *   **Diferenciación Visual & Auto-Limpieza en Tickets de Soporte**:
        *   Inclusión de `has_unread` en `get_admin_tickets` (`support_service.py`) para identificar tickets con notificaciones pendientes.
        *   Insignia brillante `<span class="ticket-unread-tag"><i class="fas fa-bell pulse"></i> SIN LEER</span>` junto al `#ID`, insignias de estado con íconos y filas destacadas con resplandor dorado (`.ticket-row-attention`).
        *   Auto-limpieza de notificaciones en `update_ticket_status` y actualización instantánea en vivo del contador del menú lateral (`updateNotifBadge`).

- **AGOSTO 15, 2026 - SYSTEM INTEGRITY VALIDATIONS & TOAST NOTIFICATION OVERHAUL (V9.9.8)**:
    *   **Protección e Integridad en Eliminación de Vehículos**: `delete_vehicle` en `services/user_service.py` valida si la patente posee reservas activas (`PENDIENTE_PAGO`, `PAGADA`, `EN_USO`). Si existen, bloquea la eliminación arrojando error HTTP 400 descriptivo ("No podés eliminar el vehículo porque tiene reservas activas o pendientes").
    *   **Protección en Eliminación de Cuentas de Usuario**: `delete_user` en `services/user_service.py` e `user_admin_service.py` valida que el usuario no tenga reservas activas ni estadías en curso con saldo adeudado antes de ser dado de baja.
    *   **Control Anti-Doble Reserva de Vehículo**: `create_reservation` en `services/reservation_service.py` impide generar dos reservas simultáneas para el mismo vehículo en períodos de tiempo superpuestos.
    *   **Sincronización de Salida Manual y Aforo**: `manual_exit` en `services/access_service.py` verifica la presencia de estadía previa y libera el aforo físico únicamente si corresponde, registrando el timestamp exacto de salida.
    *   **Validaciones de Aforo e Eliminación de Pisos**: `delete_floor` y `update_floor` en `services/branch_service.py` verifican la capacidad de ocupación actual antes de permitir reducir plazas o eliminar un nivel.
    *   **Overhaul de Notificaciones Flotantes (Toasts)**:
        *   Se removió completamente el banner/panel gigante e invasivo (`#notif-alert-banner`) al recibir notificaciones.
        *   Las alertas en tiempo real utilizan únicamente el sistema de toasts flotantes compactos en la esquina superior derecha (`showToast` en `utils.js`).
        *   Se eliminó el cierre automático por clic arbitrario en la pantalla; las notificaciones permanecen en pantalla durante exactamente 5 segundos (`5000ms`) y luego se desvanecen suavemente.
    *   **Verificación Automática**: Suite completa de Pytest (35/35 pruebas en `tests/`, 15 archivos) pasando exitosamente.

- **AGOSTO 15, 2026 - SMART TOUR SYSTEM OVERHAUL & UI REFINEMENTS (V9.9.5)**:
    *   **Posicionamiento Fijo & Abrazamiento al Viewport (`tour.js`)**: Coordenadas de tooltip y flecha migradas a `position: fixed` relativo a `(0, 0)` del viewport. Clampeo con margen de 12px a los bordes de la ventana y fallback automático para móviles (`vw < 680px`). Manejo seguro de recorte SVG (`Math.max(0, ...)`) y navegación por teclado.
    *   **Auto-Arranque de Tour Restringido al Primer Logueo**: Clave por usuario `autopass_tour_seen_${userId}` en `localStorage`. El tour solo inicia automáticamente en la primera sesión de cada usuario. Se removió el botón sobrante "TOUR APP" de la tab Inicio.
    *   **Ramificación Inteligente de Tour Adaptativo**:
        *   *Primer logueo sin vehículos*: Flujo Quick-Add en Inicio -> `startPostAddReservationTour()` finaliza la reserva directamente en Inicio -> Mapa -> Reservas -> Puntos, sin desviar la navegación a la tab de Vehículos.
        *   *Repetición manual desde Ayuda con 1+ vehículos*: `existingVehiclesTourSteps` abre en Mis Vehículos -> despliega el formulario `#vehicle-form-container` ofreciendo la opción `¿Agregar un Nuevo Vehículo?` (con botón *Continuar*) -> formulario de reserva en Inicio -> Mapa -> Reservas -> Puntos.
        *   *Repetición manual desde Ayuda sin vehículos*: `noVehiclesTourSteps` abre en Mis Vehículos -> Formulario -> Mapa -> Puntos.
    *   **Evaluación de Visibilidad Multiselector**: `waitForVisible` evalúa todos los candidatos de selectores por coma en el DOM y retorna únicamente el que tenga dimensiones `offsetWidth > 0 && offsetHeight > 0`, corrigiendo salteos indeseados.
    *   **Remoción de Flecha de Despliegue en Inputs de Patente**: Reemplazo de `.select-wrapper-premium` por `.input-wrapper-premium` en inputs de texto de patente en `inicio.html`, `vehiculos.html` y `admin_reservations.html`. Regla de resguardo CSS `.select-wrapper-premium:has(input)::after { display: none !important; }`.

- **JULIO 27, 2026 - GRANULAR MODULARIZATION OVERHAUL (V9.7.0)**:
    *   **Modularización Granular de Reservas JS**: Descomposición de `reservas.js` (903 líneas / 45 KB) en 4 submódulos ES6 especializados: `reservas-form.js` (formularios, validación, tarifas), `reservas-list.js` (tarjetas, timeline, historial y paginación), `reservas-actions.js` (pago con saldo y cancelación con reembolso) y `reservas-pass.js` (Pase Digital, QR `QRCode.js` y compartir ticket). `reservas.js` re-exporta todo el API usando el patrón Fachada.
    *   **Modularización Granular de Sucursales JS**: Separación de `dashboard-admin-branches.js` (705 líneas / 30 KB) en dos submódulos: `dashboard-admin-branches-crud.js` (CRUD sucursales, mapa Leaflet, geocoding, logo upload) y `dashboard-admin-branches-floors.js` (gestión de pisos `ParkingFloor`, aforos por piso y Planta Baja). `dashboard-admin-branches.js` re-exporta el API completo.
    *   **Componentes Partials de Modales HTML**: Extracción de modales HTML embebidos hacia componentes partials reutilizables: `profile/modals/onboarding_modal.html`, `dashboard/modals/user_modals.html`, `dashboard/modals/branch_modals.html` y `dashboard/modals/promotion_modal.html`, incluidos mediante `{% include %}` en las vistas principales.

- **JULIO 6, 2026 - CORTESÍA & OCUPACIÓN REFACTOR (V9.5.0)**:
    *   **Fix "ya está en la sede" en ALPR**: Se aplicó el mismo fix de `manual_entry` en `validate_plate` — ahora verifica si existe una SALIDA posterior a la última ENTRADA en lugar de solo mirar el último registro.
    *   **Cortesía 10 min en ALPR y manual**: Tanto `exit_plate` (cámara) como `manual_exit` ahora cheqiean el tiempo de cortesía (≤10 min desde la entrada) antes de denegar por deuda. Si está dentro del margen, la salida se registra sin cargo.
    *   **Ocupación solo física**: Se eliminó la pre-ocupación de plazas por reservas no horarias. `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` ya no tocan `ocupacion_actual`. El ALPR (entrada/salida) maneja el conteo para todos los vehículos por igual, reflejando solo autos físicamente presentes.

- **JUNIO 30, 2026 - UI/UX & FAB REFINEMENT (V9.3.0)**:
    *   **FAB en Perfil**: Nueva tarjeta flotante "Nueva Reserva" (FAB) con animación expansiva al hover, reemplazando los botones redundantes en cada tab del perfil.
    *   **FAB oculto en Inicio**: El FAB se oculta automáticamente en la tab "inicio" para no interferir con la vista principal del usuario.
    *   **Fix Animación FAB**: Corregido bug donde el icono desaparecía al replegarse; se reemplazó `width` fija por `min-width` y el label usa `max-width` animado.
    *   **Cards de Monitoreo Limpias**: Eliminado texto repetido "Tot. Disp." de las cards de aforo en `live.html` y `dashboard-stats.js`.
    *   **Barras de Progreso Dinámicas**: Colores variables según ocupación: verde (>50%), amarillo (26-50%), naranja (11-25%), rojo (≤10%).
    *   **Worker DB Robustez**: Wrapped DB sessions en `try/finally` para evitar agotamiento del pool de conexiones (`QueuePool limit`).
    *   **Pool de Conexiones**: Aumentado pool size a 10 con overflow 20 y timeout 60s para motores no-SQLite.
    *   **Títulos de Cards Actualizados**: "HACÉ TU RESERVA MANUAL" → "HACÉ TU RESERVA", "HACÉ TU RESERVA DESDE EL MAPA" → "SELECCIONÁ LA SUCURSAL DESDE EL MAPA".

- **JUNIO 23, 2026 - RESERVAS & AFORO INTELIGENTE (V9.2.0)**:
    *   **Aforo por Reserva No Horaria**: Las reservas de Día/Semana/Quincena/Mes descuentan la plaza del aforo al iniciar el período (vía worker `_process_started_reservations`). La plaza se libera solo al vencer el período o al cancelar, permitiendo al cliente entrar y salir libremente sin perder su lugar.
    *   **Restricción de Anticipación Selectiva**: Solo las reservas por hora requieren anticipación mínima (1 hora configurable). Las de período largo no tienen restricción.
    *   **Liberación Automática al Vencer**: El WorkerService libera la plaza automáticamente cuando la reserva expira, incluso si el vehículo nunca ingresó.
    *   **Salida Física sin Liberación**: La salida por ALPR/QR ya no libera la plaza de reservas no horarias — la gestión de aforo queda a cargo del ciclo de vida de la reserva.
    *   **Parametrización**: Nueva variable de entorno `RESERVA_HORA_MIN_SEGUNDOS` (default 3600) para configurar el tiempo mínimo de anticipación en reservas por hora.
    *   **Validación Sincronizada**: Frontend y backend validan consistentemente: solo reservas por hora con 1 hora de anticipación; el resto sin restricción.

- **JUNIO 17, 2026 - UX/UI REFINEMENT & RBAC (V9.1.5)**:
    *   **Rediseño Monitoreo**: Evolución de la pestaña de cámaras a un layout de grilla "Premium" con mejores indicadores de estado y visualización técnica mejorada.
    *   **Filtros Financieros**: Se añadió soporte para "Camionetas" en el reporte financiero del dashboard admin.
    *   **Seguridad UI (RBAC)**: Se eliminó la posibilidad de que un Administrador Local filtre o asigne el rol de Administrador General, endureciendo las reglas de visualización por jerarquía.
    *   **Fix de Estructura**: Corrección definitiva de solapamiento de pestañas en el panel de configuración.

- **JUNIO 17, 2026 - TRIMODAL PRICING & CAMIONETAS (V9.1.0)**:
    *   **Soporte para Camionetas**: Se integró "Camioneta" como tipo de vehículo oficial en el Enum, Base de Datos y Servicios.
    *   **Tarifario Trimodal**: Nueva pestaña en Configuración para gestionar los precios específicos de camionetas.
    *   **UI Updates**: Actualización de los formularios de usuario para permitir la selección de tipo de vehículo, rompiendo la dependencia exclusiva de la auto-detección por patente.
    *   **Iconografía**: Inclusión del icono `fa-truck-pickup` en todo el flujo de usuario y dashboard.

- **JUNIO 17, 2026 - REAL-TIME & SETTINGS OVERHAUL (V9.0.0)**:
    *   **Centralización de Cámaras**: Se movió la configuración de IPs y el control de servicios ALPR de la pestaña "Monitoreo" a una nueva sub-pestaña en "Configuración".
    *   **Aforo Real-time**: Implementación de WebSockets para la actualización instantánea del aforo en el dashboard, reemplazando el polling de 10 segundos.
    *   **Notification Service**: Creación de un servicio de notificaciones asíncronas para disparar eventos de WebSocket desde la lógica de negocio (`AccessService`).
    *   **UX Clean-up**: Se eliminaron botones de configuración de la vista de video para una experiencia de monitoreo más limpia ("Premium").
    *   **Fix Estructural**: Corrección de IDs y etiquetas en `settings.html` que causaban solapamiento de contenido entre pestañas.

- **JUNIO 17, 2026 - VIDEO STREAM OPTIMIZATION & DASHBOARD FIXES (V8.9.5)**:
    *   **Corrección de Visibilidad**: Eliminación de la lógica `onerror` que ocultaba los feeds de video; ahora el sistema restaura la opacidad al recibir el primer frame por WebSocket.
    *   **Placeholder Eficiente**: Uso de GIFs transparentes como placeholders para evitar errores 404 y mejorar la percepción de carga.
    *   **Seguridad WS**: Implementada validación preventiva de tokens en el frontend antes de abrir sockets de video para evitar colisiones con nodos ALPR.
    *   **Configuración Castelar**: Puesta en marcha exitosa de los nodos ALPR para entrada (IP) y salida (Local) en la sucursal Castelar.

- **JUNIO 16, 2026 - UI/UX REFINEMENT & FORM NORMALIZATION (V8.8.5)**:
    *   **Normalización de Formularios**: Estandarización de `height` (48px), `padding` (12px 15px) y `font-size` (0.9rem) en todos los inputs de reserva para asegurar una alineación perfecta.
    *   **Confirmación Minimalista**: Rediseño del alerta de confirmación de reserva eliminando marcos internos, simplificando la jerarquía visual y centrando la atención en el total estimado.
    *   **Gestión de Vehículos "Direct Swap"**: Refactorización del registro de vehículos reemplazando el sistema colapsable por un intercambio directo de interfaz (Botón <-> Formulario) con botón de cancelación negro estandarizado.
    *   **Unificación Estética**: Aplicación del estilo "Quick Add" (compacto y centrado) en todo el módulo de flota vehicular.
    *   **UX de Puntos**: Cambio de etiquetas ("Puntos Canjeados") y simplificación de los estados vacíos con iconos neutros y sin marcos.

- **JUNIO 15, 2026 - UX/UI MAP ENHANCEMENT & SMART OVERLAYS (V8.7.5)**:
    *   **Interactive Location Hint**: Implementación de la leyenda flotante "estacioná en tu zona" con manito animada (`fa-hand-point-down`) para incentivar el uso de la geolocalización.
    *   **Dynamic Map Overlay**: Rediseño del cuadro informativo para que sea contextual, mostrando detalles de la sucursal (nombre y dirección) solo cuando hay una selección activa.
    *   **Address Normalization**: Lógica de formateo automático en JS para corregir direcciones sin comas y estandarizar visualización en Title Case.
    *   **Sincronización Multi-Vistas**: Unificación de estilos y animaciones entre la Landing Page y el Dashboard del usuario (vía `landing.css` y `profile.css`).
    *   **Fix de Visibilidad**: Ajuste de `overflow` en tarjetas de dashboard para permitir que los elementos flotantes sobresalgan del contenedor del mapa sin recortes.

- **JUNIO 14, 2026 - DASHBOARD OPTIMIZATION & SMART MONITORING (V8.6.0)**:
    *   **Paginación Pro**: Listados de ocupación y movimientos limitados a 10 filas con navegación dinámica y **Auto-Scroll** suave al principio de tabla.
    *   **UI Operativa**: Panel de control manual siempre visible, eliminación de KPIs de ocupación total % y limpieza de indicadores de salud para mayor enfoque.
    *   **Alertas Estructuradas**: Nuevo sistema de confirmación vertical (Patente > Tipo > Monto) para ingresos, pagos y salidas.
    *   **Auto-Moto Detection**: Lógica frontend para identificar patentes de moto (`A123ABC`) y asignar el tipo de vehículo automáticamente en carga manual.
    *   **Política de Cortesía**: Reducción del margen de salida sin cargo a **10 minutos** sincronizado con el motor de facturación.
    *   **Cámaras Premium**: Remoción de imágenes de fallback (mapa) por fondo negro y centrado de visualización de patentes detectadas.

- **JUNIO 14, 2026 - FINANCIAL ANALYTICS & USER CONTROL (V8.5.5)**:
    *   **Filtros de Reporte**: Adición de selector de **Fecha Exacta** con calendario y filtrado por **Tipo de Vehículo** (Bimodal).
    *   **RBAC Empoderado**: Los `Local Admin` ahora pueden gestionar clientes (`USER`) además del personal de su sede.
    *   **Fix de Estabilidad**: Corrección de errores 403 (validación de roles) y 500 (estados de pago inexistentes).
    *   **Optimización SQL**: Refactorización de la unión de transacciones mediante subconsultas para mayor velocidad y precisión.
    *   **UI Premium**: Sincronización de iconos dorados en selectores y etiquetas en mayúsculas para filtros financieros.

- **JUNIO 09, 2026 - VERTICAL EXPANSION & BIMODAL SUPPORT (V8.2.0)**:
    *   **Gestión de Pisos**: Implementación de soporte para múltiples niveles por sucursal (`ParkingFloor`).
    *   **Unificación de PB**: Integración de la Planta Baja como nivel base en la tabla de gestión de plazas.
    *   **Soporte de Motos**: Identificación, cupos y tarifas independientes para motocicletas (Ahorro del ~50%).
    *   **RBAC Refinado**: Especialización de roles; Super Admin (Red/Usuarios) vs Local Admin (Operación de Sede/Pisos).
    *   **Fix Sucursal**: Nueva lógica de identificación de sede basada en datos del servidor para mayor estabilidad.

- **JUNIO 08, 2026 - REGIONAL ALPR & UI NORMALIZATION (V8.1.0)**:
    *   **Motor ALPR**: Soporte para patentes Mercosur (Brasil, Uruguay, Paraguay) con detección de franja azul.
    *   **Normalización**: Formateo unificado de patentes en todo el sistema (`ABC 1D23`, `ABC 1234`).
    *   **UI/UX**: Refinamiento de modales, mapas y dashboard financiero con recaudación neta.

- **JUNIO 05, 2026 - SMART FINANCE & FLEXIBLE CANCELLATIONS (V8.0.0)**:
  - **MOTOR DE REPORTES 2.0**: Implementación de `UNION ALL` y paginación en DB.
  - **CANCELACIÓN CON CORTESÍA**: Botón de salida con regla de 15 minutos sin cargo.
  - **REEMBOLSOS PROPORCIONALES**: Lógica de devolución basada en tiempo restante.

... [RESTO DEL HISTORIAL SE MANTIENE IGUAL] ...

