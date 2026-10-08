# AGENTS — Reglas para asistentes automatizados

## Continuidad entre sesiones

- Al iniciar una sesión, revisar `PENDIENTES_PROXIMA_SESION.md` (raíz del repo): contiene el
  estado de la última tanda y los puntos abiertos con las decisiones del usuario.

## Estilo de código

- Escribir código **escalable**, **minimalista** y **agrupado por funciones** (seguir el principio DRY): no duplicar lógica, CSS, marcado o componentes.
- Cuando una pieza de UI o lógica se repita en más de un lugar, extraerla a un componente/compartido único (partial de template, CSS global, módulo JS, helper de backend, etc.) y reutilizarlo configurando la parte específica de cada página o contexto.
- Aplicar el mismo criterio a cualquier lenguaje o tecnología del proyecto (Python, JS, HTML/CSS, SQL, etc.): lógica común → módulos/funciones reutilizables; estilos y marcado común → clases y partials globales.
- Preferir patrones reutilizables (prefijos de ids, clases/helpers) sobre copiar código.
- Antes de implementar algo nuevo, verificar si ya existe una función, módulo o componente que lo cubra y reutilizarlo en vez de reimplementarlo.

## Nomenclatura de archivos

- **Python / Backend:** siempre `snake_case` en inglés (`{dominio}_{subdominio}.py`).
- **Módulos CSS y JS:** siempre `kebab-case` (`{modulo}-{submodulo}.js` / `.css`).
- **Templates Jinja2:** siempre `snake_case` (`{vista}_{variante}.html`).
- **Documentación:** siempre `SCREAMING_SNAKE_CASE.md` en español.
- **Prohibido usar espacios o caracteres especiales** en nombres de archivos o carpetas (rompe URLs, precache de sw.js y scripts CLI).

## Control de versiones (git)

- **NUNCA hacer `git commit` ni `git push` (ni `--force`) salvo que el usuario lo pida expresamente**, indicando el mensaje de commit cuando corresponda. Esto incluye cambios en documentación, manuales, imágenes, `.env`, AGENTS.md y cualquier otro archivo: aunque el cambio parezca terminado o solicitado en conversación, hasta que no haya un pedido explícito de commitear/pushear, los cambios quedan locales.
- Antes de hacer `git push`, verificar que no haya conflictos de merge sin resolver (marcas `<<<<<<<`, `=======`, `>>>>>>>`) en ningún archivo del proyecto.
- Si durante un `git rebase`, `git merge` o `git pull` surge un conflicto, AVISAR AL USUARIO antes de resolverlo. No resolver conflictos automáticamente sin autorización.
- Si se detectan conflictos existentes en el código (dejados por operaciones anteriores), informar al usuario antes de modificarlos.

## Base de datos (archivos .db, .sqlite, etc.)

- Antes de hacer `git pull`, verificar si algún archivo de base de datos (*.db, *.sqlite, etc.) figura en los cambios del remoto (`git diff --name-only HEAD..origin/main`).
- Si aparece:
  1. Extraer schema de la versión local y remota para compararlos.
  2. Si el schema NO cambió (solo data), preservar la BD local y descartar la versión remota.
  3. Si el schema SÍ cambió (nuevas tablas/columnas), AVISAR AL USUARIO antes de resolver. No reemplazar la BD automáticamente.
- Para extraer schemas (ejemplo con SQLite):
  ```bash
  sqlite3 archivo.db ".schema"           # local
  git show :archivo.db | sqlite3 ".schema"  # remoto (versión del index)
  ```

## Backlog web (backlogAUTOPASS)

- El tablero vive en el repo `backlogAUTOPASS/` (sitio: `https://marianojac.github.io/backlogAUTOPASS/`). El `DATA` dentro de `index.html` es solo la semilla/fallback: si Firebase (`backlog/rows2`) tiene datos, la app los usa e IGNORA el `DATA` del HTML.
- Por lo tanto, para que filas/secciones nuevas (o ediciones hechas a mano en `index.html`) se vean en el tablero, hay que escribirlas también en Firebase:
  - `GET https://backlog-dd061-default-rtdb.firebaseio.com/backlog/rows2.json`
  - `PUT` (reemplazo completo del array) con la lista final; Firebase está en reglas de lectura/escritura pública.
- Las filas son objetos `{comp, desc, estado, ffin, finicio (dd/mm/yy), id, kind: "row", mvp, obs, responsable, tipo}` (claves en orden alfabético); las secciones son `{fecha:"", kind:"section", text}`. `estado` ∈ CERRADA/EN CURSO/PENDIENTE; `mvp` ∈ "MVP 1".."MVP 4".
- El historial "Revisiones" vive en `backlog/revisions` (array, máximo 40): se agrega al inicio `{ts, autor, count, data}` (`count` = cantidad de elementos `kind:"row"`). Un alta hecha por API no genera revisión automática: hay que agregarla manualmente si se quiere que figure en la pestaña "Revisiones".


# AGENTS — Normas de mantenimiento (Modularidad y CSS)

## Modularidad y DRY
- Respetar estrictamente la arquitectura modular existente (capas: routes → services → repositories → models/schemas). No introducir lógica de negocio en routes; mantener controllers delgados.
- No duplicar código. Si una función/lógica se repite, extraer a servicio/helper compartido.
- Antes de crear código nuevo, buscar en el repositorio si ya existe una utilidad/componente similar y reutilizarlo.
- No romper la factorización existente. Cualquier cambio debe preservar la organización por responsabilidades.

## Orden y jerarquía de CSS
- Mantener CSS organizado siguiendo la jerarquía y estructura actual de static/css/ (base, layout, components, pages). No mezclar estilos sin criterio.
- Respetar cascada, especificidad y evitar duplicados de reglas entre archivos.
- No introducir CSS inline innecesario; priorizar clases reutilizables.
- Al modificar estilos, verificar que no se rompa la consistencia entre módulos.

## Verificación obligatoria antes de modificar
- Revisar historial reciente (git blame, git log -p) para entender contexto y no revertir correcciones previas.
- Confirmar que el cambio no duplica lógica existente.
- Validar imports/capas: routes solo delegan, services contienen lógica, repositories acceso a datos.

## Documentación
- Registrar estas normas en AGENTS.md para cumplimiento permanente en futuras sesiones.
