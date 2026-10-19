"""Explicaciones analizadas de scripts (lote 2: guards, migradores y manuales)."""

ANALISIS: dict[str, dict] = {
    "manual/tools/capturar.py": {
        "proposito": 'Motor de capturas de pantalla del manual de usuario: lee manual/capturas/manifiesto.json, abre la app con Playwright, inicia sesión por rol, ejecuta los pasos declarados (clics, esperas, scroll, JS) y guarda cada captura en manual/assets/img/. Soporta filtro por ids o por manual, y un modo --vigilar que recaptura sola cada vez que cambian templates, CSS o JS.',
        "simbolos": {
            "log": (
                '💡 LA IDEA: Imprimir un mensaje en consola con vaciado inmediato de búfer.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el usuario vea el avance en tiempo real sin retrasos producidos por operaciones bloqueantes de Playwright.\n\n'
                '⚙️ FUNCIONAMIENTO: Imprime un mensaje por stdout con flush=True para que aparezca inmediatamente en la consola, incluso cuando el proceso está bloqueado esperando acciones largas de Playwright.'
            ),
            "login": (
                '💡 LA IDEA: Iniciar sesión automáticamente en la API según el rol del usuario (cliente, admin, staff).\n\n'
                '🎯 POR QUE FUE GENERADA: Obtiene los tokens y credenciales necesarios para navegar por páginas privadas sin interacción manual.\n\n'
                '⚙️ FUNCIONAMIENTO: POSTea /v1/auth/login con las credenciales del rol elegido (mapa CUENTAS) y devuelve el payload de sesión (access_token, rol, nombre, apellido). Si el rol no tiene cuenta (staff/anonimo) devuelve None; si el login falla, aborta el proceso con SystemExit mostrando el código y detalle del error HTTP.'
            ),
            "inyectar_sesion": (
                '💡 LA IDEA: Pre-cargar el token y los datos de usuario directamente en el almacenamiento local del navegador.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el navegador abra directamente la pantalla que se quiere fotografiar sin tener que pasar primero por el formulario de login.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve un script JS (init script del contexto de Playwright) que escribe token, rol, nombre y apellido en localStorage antes de cada carga de página, así la app cree que hay sesión sin pasar por la pantalla de login.'
            ),
            "cerrar_overlays": (
                '💡 LA IDEA: Cerrar modales, tours guiados o carteles emergentes que tapen la vista.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que las capturas de pantalla queden arruinadas por ventanas superpuestas que no forman parte de la explicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra lo que tape la captura: recorre hasta 4 veces una lista de selectores de tours/modales, hace clic en el primero visible y termina con una pulsación de Escape. Ignora silenciosamente cualquier error de cada intento.'
            ),
            "aplicar_pasos": (
                '💡 LA IDEA: Ejecutar la secuencia de acciones declarada (clics, esperas, scroll) sobre la interfaz.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite posicionar la página en el estado exacto (formulario abierto, menú desplegado) antes de sacar la foto.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta en orden los pasos declarados en el manifiesto sobre la página: clic por selector, clic por texto, espera en ms, scroll vía evaluate o ejecución de JS, con espera extra tras scroll/JS y una pausa final (400 ms por defecto) entre pasos.'
            ),
            "capturar": (
                '💡 LA IDEA: Orquestar la toma de capturas de pantalla de la aplicación según el manifiesto.\n\n'
                '🎯 POR QUE FUE GENERADA: Automatiza la generación completa de las imágenes del manual con dimensiones y resoluciones homogéneas.\n\n'
                '⚙️ FUNCIONAMIENTO: Función principal: filtra las capturas del manifiesto por manual/ids, hace login una sola vez por rol distinto, crea un contexto de Playwright por rol (1600x1000, device_scale_factor 2, es-AR, sin animaciones) y, por cada captura, navega, cierra overlays, aplica pasos y guarda screenshot de un elemento o de la página completa. Devuelve 0 si no falló ninguna y 1 si hubo fallas.'
            ),
            "firma_de_archivos": (
                '💡 LA IDEA: Calcular una huella temporal de los archivos de plantillas, estilos y scripts.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber si el código de la interfaz cambió para disparar automáticamente nuevas capturas en modo vigilar.\n\n'
                '⚙️ FUNCIONAMIENTO: Huella (ruta + mtime) de todos los archivos de templates/, static/css/, static/js/ y del manifiesto: es lo que compara el modo vigilar para detectar que la interfaz cambió.'
            ),
            "vigilar": (
                '💡 LA IDEA: Supervisar el proyecto en segundo plano y recapturar automáticamente las pantallas cuando haya cambios de diseño.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene los manuales siempre actualizados con el diseño vigente sin que el desarrollador deba acordarse de volver a capturar a mano.\n\n'
                '⚙️ FUNCIONAMIENTO: Bucle infinito de vigilancia: cada N segundos (3 por defecto) compara la firma de archivos; si cambió, lista los archivos modificados y vuelve a ejecutar capturar(). Atrapa SystemExit de cada ciclo para no morir, y sale con Ctrl+C.'
            ),
            "main": (
                '💡 LA IDEA: Procesar las opciones de terminal y disparar la captura única o el modo de vigilancia continua.\n\n'
                '🎯 POR QUE FUE GENERADA: Sirve como punto de entrada por línea de comandos para generar las imágenes del manual de usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Parsea los argumentos (ids posicionales, --base, --manual, --vigilar, --intervalo) y deriva a vigilar() o a capturar(), saliendo con el código devuelto por esta última.'
            ),
        },
    },
    "manual/tools/generar-pdf.py": {
        "proposito": 'Genera el PDF de los manuales AUTOPASS con el Chromium de Playwright (misma estética que el HTML en pantalla). Agrega portada, índice con número de página real (dos pasadas), índice con links y bookmarks, PDF etiquetado, y paginado sin cortes: secciones en página nueva y temas (<h3> + contenido) nunca partidos.',
        "simbolos": {
            "normalizar": (
                '💡 LA IDEA: Limpiar y unificar títulos quitando acentos, puntuación y mayúsculas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite comparar y relacionar con precisión los títulos del HTML con el texto extraído del documento PDF.\n\n'
                '⚙️ FUNCIONAMIENTO: Deja un texto solo con letras/números en minúscula (quita acentos con NFD y todo lo no alfanumérico) para poder comparar los títulos del HTML —que se arman como «1. Antes de empezar» sin espacio— con el texto extraído del PDF, donde sí hay espacio.'
            ),
            "esperar_carga": (
                '💡 LA IDEA: Pausar la ejecución hasta que la página haya cargado fuentes, imágenes y terminado sus tareas de red.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita imprimir PDFs con imágenes rotas, fuentes sustitutas o elementos descolocados por renderizado incompleto.\n\n'
                '⚙️ FUNCIONAMIENTO: Bloquea hasta que la página esté quieta: espera networkidle (60 s), la carga de fuentes, la carga de todas las imágenes pendientes y hace una pausa extra de 1200 ms, evitando PDFs con fuentes o imágenes a medio renderizar.'
            ),
            "aplicar_paginas": (
                '💡 LA IDEA: Inyectar en el índice del manual los números de página reales medidos en la primera pasada.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve el problema clásico de la maquetación web donde no se sabe en qué página caerá un tema hasta después de imprimirlo.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve la función 'poner', que escribe en cada elemento [data-pagina] del índice el número de página real medido en la pasada 1 (mapa id -> número)."
            ),
            "mover_si_puede": (
                '💡 LA IDEA: Mover el archivo PDF generado a su ubicación final contemplando posibles bloqueos de lectura de Windows.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el script falle si el desarrollador tiene el PDF abierto en un visor, guardándolo temporalmente con un sufijo alternativo.\n\n'
                '⚙️ FUNCIONAMIENTO: Mueve el PDF temporal al destino con os.replace; si el archivo destino está abierto en Acrobat/visor de Windows (PermissionError), lo escribe al lado con sufijo «-nuevo» y devuelve esa ruta en vez de romper.'
            ),
            "imprimir_pdf": (
                '💡 LA IDEA: Renderizar la página actual en un archivo PDF con formato A4, encabezados y números de página.\n\n'
                '🎯 POR QUE FUE GENERADA: Produce el documento final imprimible con calidad profesional y enlaces accesibles.\n\n'
                '⚙️ FUNCIONAMIENTO: Imprime la página actual como PDF A4 con cabecera (título del manual + AUTOPASS) y pie («Página X de Y») inyectados, print_background, outline (bookmarks) y tagged=True (accesibilidad). Escribe primero a un .tmp y luego lo mueve con mover_si_puede().'
            ),
            "paginas_de_titulos": (
                '💡 LA IDEA: Escanear el borrador preliminar en PDF para mapear en qué página quedó cada encabezado del documento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite alimentar la tabla de contenidos con los números de página exactos de cada sección.\n\n'
                '⚙️ FUNCIONAMIENTO: Pasada 1: lee el borrador de PDF con pypdf, detecta las páginas de índice (las que concentran >60% de los títulos) y asigna a cada entrada su número de página buscándolas en orden a partir del último hallazgo (fallback: barrido completo). Devuelve el mapa id->página, el total de páginas y las páginas de índice.'
            ),
            "titulos_huerfanos": (
                '💡 LA IDEA: Detectar títulos que quedaron aislados al final de una página sin su contenido correspondiente.\n\n'
                '🎯 POR QUE FUE GENERADA: Corrige un defecto tipográfico común en navegadores forzando el salto del título a la página siguiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve los ids de los títulos que quedaron solos al pie de una página (defecto de paginación que CSS no puede resolver: Chromium a veces ignora break-after: avoid). Descarta índice, última página, encabezado/pie del visor y solo cuenta si la última línea normalizada ES un título del manual.'
            ),
            "forzar_saltos": (
                '💡 LA IDEA: Añadir saltos de página obligatorios antes de los temas que quedaron cortados.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que ningún título empiece huérfano en el pie de página, garantizando una lectura limpia y ordenada.\n\n'
                "⚙️ FUNCIONAMIENTO: Agrega la clase 'salto' al título huérfano y a su contenedor .tema para que el tema arranque en página nueva en la pasada 2."
            ),
            "generar": (
                '💡 LA IDEA: Coordinar la compilación completa de un manual desde su origen HTML hasta el PDF final de dos pasadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Encapsula la lógica de diagramación, numeración y paginado automático de manuales de usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Orquesta la generación de un manual: abre el HTML, agrupa los temas, arma el índice, imprime una pasada en una carpeta temporal para medir paginación y huérfanos, fuerza los saltos, aplica los números definitivos e imprime el PDF final. Devuelve (ruta, detalle) o (None, motivo) si el manual no existe; avisa si el destino estaba abierto.'
            ),
            "main": (
                '💡 LA IDEA: Interpretar los parámetros de consola y disparar la generación individual o masiva de manuales en PDF.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee la interfaz de línea de comandos para automatizar la publicación de la documentación formal del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Parsea argumentos (manual opcional o --todos), elige los manuales objetivo —los que existan en manual/—, levanta Chromium y llama a generar() por cada uno. Devuelve 0, o 1 si no hay manuales.'
            ),
        },
    },
    "_tools/check_inline_styles.py": {
        "proposito": 'Guard de CI (P3 Componentes/DRY) que cuenta los estilos inline style=" en templates/ y falla si un template supera su conteo baseline (regresión) o si uno nuevo supera 25. Los emails se excluyen por diseño; con --update se regenera el baseline tras una limpieza.',
        "simbolos": {
            "count_styles": (
                '💡 LA IDEA: Contar cuántas veces aparece el atributo style= dentro de un archivo de plantilla.\n\n'
                '🎯 POR QUE FUE GENERADA: Mide el uso de estilos CSS incrustados directamente en el marcado HTML.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee el archivo y devuelve cuántas veces aparece el patrón style= seguido de comillas (simple conteo por regex, sin parsear HTML).'
            ),
            "scan": (
                '💡 LA IDEA: Escanear todas las plantillas del proyecto contabilizando estilos inline y descartando excepciones como correos.\n\n'
                '🎯 POR QUE FUE GENERADA: Recopila la métrica de estilos directos en todas las pantallas para su control.\n\n'
                '⚙️ FUNCIONAMIENTO: Recorre templates/**/*.html en orden, salta cualquier ruta con un directorio excluido (emails) y devuelve {ruta relativa: cantidad de estilos inline}.'
            ),
            "load_baseline": (
                '💡 LA IDEA: Leer el archivo de referencia que registra la cantidad máxima tolerada de estilos inline.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite controlar que nadie agregue nuevos estilos inline respecto a la meta establecida.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee y parsea el JSON del baseline (inline_styles_baseline.json) con los conteos aceptados.'
            ),
            "main": (
                '💡 LA IDEA: Verificar que ninguna pantalla haya introducido estilos inline no autorizados o actualizar la referencia.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la arquitectura CSS obligando a usar clases reutilizables en lugar de estilos directos en el HTML.\n\n'
                '⚙️ FUNCIONAMIENTO: Interpreta --update (reescribe el baseline con los conteos actuales y sale) o modo CI: compara contra el baseline, clasifica cada template como DEL/NUEVO/REGRESIÓN/ok/mejorado, imprime la tabla ordenada por conteo y devuelve 1 si hubo regresiones o archivos nuevos fuera de umbral, 0 si todo está bajo control.'
            ),
        },
    },
    "_tools/generate_code_docs.py": {
        "proposito": "Genera el visor de documentación 'EXPLICACION DE CODIGO/data.js' recorriendo el código real del proyecto: extrae símbolos (clases/funciones/métodos con firma y docstring), imports y relaciones (importado por), asigna cada archivo a una sección y fusiona la capa de análisis (_tools/analysis/analysis_*.py), que tiene prioridad sobre el docstring original. Expone modos --inventario y --cobertura que no escriben nada.",
        "simbolos": {
            "is_skipped": (
                '💡 LA IDEA: Determinar si un archivo debe omitirse del análisis y catálogo de documentación.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita indexar dependencias externas, carpetas temporales o el propio código de análisis.\n\n'
                '⚙️ FUNCIONAMIENTO: Decide si un archivo entra al visor: excluye la propia carpeta _tools/analysis (para no documentar el análisis sobre sí mismo) y cualquier directorio de SKIP_PARTS (venv, .git, node_modules, capturas, documentación generada, etc.).'
            ),
            "rel": (
                '💡 LA IDEA: Convertir cualquier ruta física en una clave relativa normalizada con barras estándar.\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica la identificación de archivos para que los enlaces funcionen igual en Windows y Linux.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte una ruta absoluta en ruta relativa a la raíz del repo en formato POSIX (con /), que es la clave con la que se indexa todo.'
            ),
            "load_analysis": (
                '💡 LA IDEA: Importar dinámicamente y fusionar todos los módulos de explicaciones pedagógicas de _tools/analysis/.\n\n'
                '🎯 POR QUE FUE GENERADA: Carga las explicaciones detalladas escritas para cada símbolo y las superpone a los comentarios básicos del código.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga y fusiona todos los ANALISIS declarados en _tools/analysis/analysis_*.py importando cada archivo como módulo dinámico con importlib; si alguno falla al importar lo informa y sigue con el resto. Devuelve {ruta: {proposito, simbolos}}.'
            ),
            "apply_analysis": (
                '💡 LA IDEA: Sobrescribir los docstrings técnicos originales con las explicaciones pedagógicas enriquecidas.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el visor de código presente la idea y el propósito humano de cada función en lugar de solo su firma.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica el análisis a una entrada del visor: marca analizado=True, pisa el propósito con el del análisis (guardando el viejo en purpose_doc si era distinto) y, por cada símbolo, busca primero la clave calificada (Clase.metodo) y si no existe cae al nombre simple, pisando doc y conservando el docstring original en doc_orig.'
            ),
            "py_signature": (
                '💡 LA IDEA: Reconstruir la firma legible de una función a partir de su árbol sintáctico (AST).\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra claramente los parámetros obligatorios y opcionales sin necesidad de ejecutar el archivo.\n\n'
                "⚙️ FUNCIONAMIENTO: Arma la firma textual de una función a partir del AST: argumentos posicionales (con / si hay pos-only), *args, *, kwargs con default, **kwargs, marcando '=...' en los que tienen valor por defecto."
            ),
            "py_symbol": (
                '💡 LA IDEA: Convertir un elemento sintáctico (clase, función, método) en un objeto estructurado de documentación.\n\n'
                '🎯 POR QUE FUE GENERADA: Estandariza la metadata de cada símbolo (línea, firma, tipo) para ser consumida por el visor web.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte un nodo AST (clase o función) en el dict de símbolo del visor: nombre, calificación, kind (class/function/private si empieza con _), firma (bases de la clase o firma de la función con prefijo async), docstring, línea y sangría.'
            ),
            "py_module_doc": (
                '💡 LA IDEA: Extraer el comentario general o docstring ubicado al inicio de un módulo Python.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee una descripción introductoria por defecto cuando el archivo no cuenta con análisis específico.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el docstring de módulo (o vacío) de un AST; se usa como propósito de fallback cuando no hay FILE_NOTES ni análisis.'
            ),
            "py_symbols": (
                '💡 LA IDEA: Extraer todas las clases, funciones y métodos declarados en un archivo de Python.\n\n'
                '🎯 POR QUE FUE GENERADA: Construye el índice de componentes inspeccionables de cada módulo del backend.\n\n'
                "⚙️ FUNCIONAMIENTO: Recorre el body del módulo y lista clases y funciones de nivel superior; los métodos de cada clase se agregan con sangría 1 y calificación 'Clase.metodo' para poder resolver nombres repetidos."
            ),
            "py_imports": (
                '💡 LA IDEA: Extraer los módulos importados resolviendo referencias relativas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite armar el mapa de dependencias y saber qué módulos son requeridos por cada archivo.\n\n'
                '⚙️ FUNCIONAMIENTO: Extrae los módulos importados (toma los dos primeros segmentos del path) resolviendo imports relativos (from .x) contra el paquete del archivo; sirve para armar la relación importado-por.'
            ),
            "js_symbols": (
                '💡 LA IDEA: Detectar funciones, clases y constantes exportadas en archivos JavaScript.\n\n'
                '🎯 POR QUE FUE GENERADA: Genera el catálogo de símbolos inspeccionables del frontend de la aplicación.\n\n'
                '⚙️ FUNCIONAMIENTO: Detecta por regex funciones/clases y declaraciones export const/let/var de nivel superior en JS; a las funciones/const con arrow o function les asigna kind function, si no value, y les adjunta el doc comentario previo.'
            ),
            "_js_doc": (
                '💡 LA IDEA: Extraer el bloque de comentarios explicativos ubicado inmediatamente antes de una función JavaScript.\n\n'
                '🎯 POR QUE FUE GENERADA: Recupera la documentación escrita por el desarrollador para presentarla en la ficha del símbolo.\n\n'
                '⚙️ FUNCIONAMIENTO: Recoge el comentario JSDoc (/** ... */) o la tira de // inmediatamente anterior a un símbolo JS y lo devuelve como texto plano.'
            ),
            "js_header": (
                '💡 LA IDEA: Obtener el encabezado de documentación general al comienzo de un archivo JavaScript.\n\n'
                '🎯 POR QUE FUE GENERADA: Establece el propósito global del módulo de frontend.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la cabecera JSDoc /** ... */ al inicio del archivo JS, limpiando asteriscos, para usarla como propósito del archivo.'
            ),
            "js_imports": (
                '💡 LA IDEA: Registrar las dependencias e imports relativos entre módulos de JavaScript.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite conocer las conexiones internas entre componentes del cliente web.\n\n'
                "⚙️ FUNCIONAMIENTO: Lista los imports relativos (from './x') de un archivo JS, sin duplicados y ordenados."
            ),
            "section_for": (
                '💡 LA IDEA: Asignar un archivo a su categoría temática en la navegación de la documentación.\n\n'
                '🎯 POR QUE FUE GENERADA: Agrupa los cientos de archivos del proyecto en secciones intuitivas y fáciles de explorar.\n\n'
                '⚙️ FUNCIONAMIENTO: Mapea la ruta de un archivo al id de sección del visor (arranque, core, models, services, routes, css, templates, tests, migraciones, scripts, frontend-*); para JS decide por palabras clave del nombre del archivo y por defecto cae en arranque.'
            ),
            "collect": (
                '💡 LA IDEA: Recorrer todo el proyecto para extraer y enriquecer la documentación de cada archivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la recolección integral de backend, frontend, estilos y plantillas en un solo paso.\n\n'
                '⚙️ FUNCIONAMIENTO: Barrido central: recorre todos los archivos del repo, aplica is_skipped, delega en _collect_py/_collect_js/_collect_css/_collect_html según extensión y ubicación, aplica el análisis y rellena el propósito de fallback si quedó vacío. Devuelve la lista de entradas del visor.'
            ),
            "_base_entry": (
                '💡 LA IDEA: Crear la plantilla de datos inicial para un archivo documentado.\n\n'
                '🎯 POR QUE FUE GENERADA: Inicializa los campos indispensables de cada entrada antes de procesar sus símbolos específicos.\n\n'
                '⚙️ FUNCIONAMIENTO: Fabrica el esqueleto de una entrada: ruta, lenguaje, sección (de FILE_NOTES o de section_for), propósito/relaciones de FILE_NOTES y listas vacías de imports y symbols.'
            ),
            "pretty": (
                '💡 LA IDEA: Generar un nombre amigable y limpio para mostrar un archivo en la interfaz.\n\n'
                '🎯 POR QUE FUE GENERADA: Mejora la legibilidad visual en los encabezados y menús del visor.\n\n'
                '⚙️ FUNCIONAMIENTO: Nombre legible de un archivo: le quita la extensión y reemplaza guiones bajos/por guiones, para títulos y mensajes.'
            ),
            "fallback_purpose": (
                '💡 LA IDEA: Generar una descripción explicativa genérica cuando un archivo no posea análisis explícito.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que queden archivos con descripciones vacías en la documentación pública.\n\n'
                '⚙️ FUNCIONAMIENTO: Redacta un propósito genérico cuando no hay análisis, docstring ni FILE_NOTES: según lenguaje y carpeta (CSS base/components/pages, emails, partials, tests, scripts, etc.).'
            ),
            "_collect_py": (
                '💡 LA IDEA: Analizar un archivo Python mediante su árbol AST extrayendo símbolos, imports y docstrings.\n\n'
                '🎯 POR QUE FUE GENERADA: Descompone el código fuente de backend en sus componentes funcionales de forma estática y segura.\n\n'
                "⚙️ FUNCIONAMIENTO: Analiza un .py con ast: propósito = docstring de módulo, imports e imports. Las migraciones de Alembic se tratan aparte: propósito desde su docstring y un símbolo sintético 'upgrade / downgrade'. Si el AST falla, devuelve la entrada vacía."
            ),
            "_collect_js": (
                '💡 LA IDEA: Procesar un archivo JavaScript extrayendo cabeceras, dependencias y funciones declaradas.\n\n'
                '🎯 POR QUE FUE GENERADA: Integra el código de cliente en la base documental del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Entrada de un .js: propósito desde la cabecera JSDoc, imports relativos y símbolos vía js_symbols.'
            ),
            "_collect_css": (
                '💡 LA IDEA: Analizar una hoja de estilos CSS extrayendo sus selectores principales.\n\n'
                '🎯 POR QUE FUE GENERADA: Documenta los estilos visuales del proyecto y las clases que definen cada componente.\n\n'
                '⚙️ FUNCIONAMIENTO: Entrada de un .css: toma hasta 60 selectores como símbolos (sin doc); el propósito lo ponen FILE_NOTES, el análisis o el fallback.'
            ),
            "_css_selectors": (
                '💡 LA IDEA: Extraer selectores CSS limpios descartando reglas complejas o ilegibles.\n\n'
                '🎯 POR QUE FUE GENERADA: Identifica las reglas de estilo que dan forma a la interfaz.\n\n'
                "⚙️ FUNCIONAMIENTO: Extrae selectores por regex cortando en llaves: todo lo que precede a un '{' que no sea bloque @ o regla, descartando los que miden 120+ caracteres (reglas con datos URI, etc.)."
            ),
            "_collect_html": (
                '💡 LA IDEA: Procesar una plantilla Jinja2 extrayendo bloques, inclusiones y herencias.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra la arquitectura de vistas y qué plantillas heredan o reutilizan a otras.\n\n'
                '⚙️ FUNCIONAMIENTO: Entrada de un template: propósito desde el comentario inicial {# ... #} o <!-- ... --> o desde el extends, imports = extends/include/import de Jinja (resueltos contra templates/) y símbolos = los bloques {% block %} sin repetir.'
            ),
            "resolve_import": (
                '💡 LA IDEA: Traducir una instrucción de import en la ruta física real del archivo correspondiente.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace posible hacer clic sobre un módulo importado para navegar directamente hacia su definición.\n\n'
                "⚙️ FUNCIONAMIENTO: Resuelve un import a una ruta real del proyecto: si ya es un path conocido lo devuelve; si es un import relativo de JS navega con '../' contra la ruta del archivo; si no, busca el módulo en el índice invertido de .py (path -> módulo punto)."
            ),
            "main": (
                '💡 LA IDEA: Compilar toda la documentación y volcarla en el archivo data.js y las páginas estáticas.\n\n'
                '🎯 POR QUE FUE GENERADA: Construye el visor completo interactivo para que cualquier persona pueda estudiar y consultar el código.\n\n'
                '⚙️ FUNCIONAMIENTO: Modo de escritura: recolecta archivos, construye la relación inversa (importado por) resolviendo cada import, agrega symbolNames, y vuelca todo a EXPLICACION DE CODIGO/data.js como window.CODE_DOCS. Imprime totales: archivos, símbolos, cuántos con análisis, pendientes y sin propósito.'
            ),
            "inventario": (
                '💡 LA IDEA: Listar los símbolos y funciones pendientes de documentar según la sección o ruta.\n\n'
                '🎯 POR QUE FUE GENERADA: Sirve como guía de trabajo para saber con precisión qué explicaciones faltan redactar.\n\n'
                '⚙️ FUNCIONAMIENTO: Modo --inventario <seccion|ruta|all>: lista los archivos y símbolos (con su kind) que un lote de análisis debe cubrir, filtrando por sección o por ruta exacta; es la fuente de verdad de los nombres de clave del diccionario ANALISIS.'
            ),
            "cobertura": (
                '💡 LA IDEA: Medir el porcentaje de funciones y clases que ya cuentan con explicación pedagógica.\n\n'
                '🎯 POR QUE FUE GENERADA: Monitorea el avance de la documentación pedagógica y señala qué áreas requieren atención.\n\n'
                '⚙️ FUNCIONAMIENTO: Modo --cobertura [lista]: sin escribir nada, cruza el ANALISIS cargado con el inventario (acepta rutas o secciones separadas por coma), imprime solo los archivos con símbolos faltantes o sin entrada y resume cuántos símbolos están cubiertos y cuántos quedan pendientes.'
            ),
        },
    },
    "_tools/migrate_color_tokens.py": {
        "proposito": 'Migra literales de color (#hex / rgb) a var(--token) solo cuando el RGBA normalizado es EXACTAMENTE igual al de un token ya declarado en variables.css: cero cambio visual garantizado. Excluye el propio variables.css, los fallbacks de var(--x, #literal) y los content: (iconos); los genéricos --blanco/--negro se dejan fuera salvo --include-generic. Dry-run por defecto, --apply escribe.',
        "simbolos": {
            "hex_to_rgba": (
                '💡 LA IDEA: Convertir códigos hexadecimales en tuplas numéricas de color.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite evaluar equivalencias exactas de color con los tokens del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte #rgb/#rrggbb/#rrggbbaa a tupla RGBA (0-255); devuelve None si la longitud no es válida.'
            ),
            "rgb_to_rgba": (
                '💡 LA IDEA: Normalizar valores rgb a una tupla de cuatro canales con opacidad.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita la comparación de formatos de color disímiles.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte los componentes de rgb()/rgba() a tupla RGBA con alfa 0-255 (255 si no viene alfa).'
            ),
            "build_token_map": (
                '💡 LA IDEA: Leer variables.css y crear un catálogo de colores asociados a sus tokens.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber al instante qué nombre de variable CSS corresponde exactamente a un color hardcodeado.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee solo variables.css, extrae cada --token: valor y arma {tupla RGBA: [tokens]} con los que tengan color hex o rgb legible; es el índice que decide qué literal se puede reemplazar.'
            ),
            "pick_token": (
                '💡 LA IDEA: Seleccionar el token más representativo y semántico ante múltiples variables con el mismo color.\n\n'
                '🎯 POR QUE FUE GENERADA: Prefiere nombres como --text-primary antes que identificadores genéricos para mayor claridad.\n\n'
                '⚙️ FUNCIONAMIENTO: Ante varios tokens con el mismo RGBA, elige el primero de la lista PREFERRED (semánticos: --text-primary, --border, --dorado…) y si ninguno está, el alfabéticamente menor.'
            ),
            "protected_spans": (
                '💡 LA IDEA: Delimitar zonas del código de estilos que no deben ser modificadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege reglas críticas que requieren colores directos obligatorios por compatibilidad.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve los rangos (inicio, fin) de todo lo que no se debe tocar: fallbacks de var(--x, ...) y declaraciones content:.'
            ),
            "in_spans": (
                '💡 LA IDEA: Determinar si una posición de texto se encuentra dentro de un área protegida.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita sobreescribir colores en lugares intocables.\n\n'
                '⚙️ FUNCIONAMIENTO: Indica si una posición cae dentro de alguno de esos rangos (recorrido anticipado: los spans están ordenados, corta al pasar de uno).'
            ),
            "plan": (
                '💡 LA IDEA: Planificar todos los reemplazos de colores hardcodeados por variables sin tocar el disco.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite previsualizar las ediciones y verificar que no haya solapamientos antes de escribir.\n\n'
                '⚙️ FUNCIONAMIENTO: Corazón del codemod: recorre todos los hex y rgb del texto, salta los protegidos, resuelve a token (descartando genéricos si corresponde) y devuelve (texto nuevo, Counter por token) aplicando las ediciones en orden sin solaparse. No escribe nada.'
            ),
            "main": (
                '💡 LA IDEA: Ejecutar la migración masiva de colores directos a tokens semánticos de diseño.\n\n'
                '🎯 POR QUE FUE GENERADA: Estandariza todo el CSS del sistema bajo la paleta central de diseño sin alterar ningún píxel visible.\n\n'
                '⚙️ FUNCIONAMIENTO: CLI: construye el mapa de tokens, corre plan() sobre cada .css excepto variables.css, imprime el dry-run (archivos y tokens más usados) y, con --apply, escribe los archivos modificados.'
            ),
        },
    },
    "_tools/migrate_form_attributes.py": {
        "proposito": 'Completa en templates/ los atributos de usabilidad móvil y gestores de contrasena que faltaban: autocomplete= para login/registro/recuperación/perfil, inputmode= para DNI y teléfono, autocapitalize/spellcheck para patentes, y autocomplete=off a nivel de <form> en los modales del dashboard (cargan datos de otra persona). Idempotente y dry-run por defecto.',
        "simbolos": {
            "add_attr": (
                '💡 LA IDEA: Insertar atributos en una etiqueta HTML antes de su cierre.\n\n'
                '🎯 POR QUE FUE GENERADA: Modifica el marcado agregando propiedades sin alterar el resto de la etiqueta.\n\n'
                "⚙️ FUNCIONAMIENTO: Inserta los atributos dados antes del cierre de la etiqueta de apertura, soportando tanto '>' como '/>'."
            ),
            "apply_attrs": (
                '💡 LA IDEA: Agregar atributos de usabilidad solo si no existían previamente.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace la migración completamente idempotente para que pueda ejecutarse múltiples veces sin duplicar atributos.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrega attrs a tag solo si faltan (chequea nombre por nombre con \\b nombre= sobre la etiqueta); si el tag no se encuentra en el archivo imprime un AVISO. La edición se acumula en la lista edits como (inicio, fin, reemplazo) sin escribir.'
            ),
            "main": (
                '💡 LA IDEA: Añadir masivamente atributos de autocompletado y teclado móvil en formularios.\n\n'
                '🎯 POR QUE FUE GENERADA: Mejora la experiencia en celulares y con gestores de contraseñas completando atributos clave en todos los campos.\n\n'
                '⚙️ FUNCIONAMIENTO: CLI dry-run/--apply: por cada template agrupa las ediciones de todos los FIELD_ATTRS (busca cada input/select/textarea por id con TAG_RE) y de FORM_ATTRS (etiquetas <form> exactas que reciben autocomplete=off), imprime archivo y cantidad de campos, y con --apply reescribe aplicando las ediciones de atrás hacia adelante para no desplazar los offsets. Devuelve 0.'
            ),
        },
    },
    "_tools/migrate_label_association.py": {
        "proposito": 'Asocia cada <label> suelto con el control que rotula: le agrega for= al lado del control y, si el control no tiene id, se lo inventa según el mapa explícito MISSING_ID (clave: ruta + texto exacto del control). No toca labels que envuelven al control (asociación implícita), labels de grupo ni labels sobre valores de display, y nunca cruza el </form>. Idempotente y dry-run por defecto.',
        "simbolos": {
            "add_attr": (
                '💡 LA IDEA: Insertar atributos for o id en una etiqueta HTML.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite asociar campos con sus títulos descriptivos en el código.\n\n'
                "⚙️ FUNCIONAMIENTO: Inserta un atributo (for= o id=) antes del cierre de la etiqueta de apertura, soportando '>' y '/>'."
            ),
            "plan_for": (
                '💡 LA IDEA: Identificar etiquetas <label> huérfanas y asociarlas a su control interactivo más cercano.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve el enlace de etiquetas sin modificar la estructura visual de la pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Para un template, recorre los <label> sin for= y para cada uno busca el primer control (input/select/textarea) antes del </form>, descartando si hay otro label antes (grupo) o si el label lo envuelve. Si el control no tiene id lo agrega desde MISSING_ID; si no está en el mapa genera un aviso. Devuelve (ediciones, avisos).'
            ),
            "main": (
                '💡 LA IDEA: Recorrer todas las plantillas y aplicar las asociaciones entre etiquetas y campos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza la accesibilidad de formularios en todo el sistema de manera automatizada.\n\n'
                '⚙️ FUNCIONAMIENTO: CLI dry-run/--apply: corre plan_for sobre templates/**/*.html, imprime por archivo cuántos labels y cuántos id nuevos se agregarían, escribe con --apply (ediciones de atrás hacia adelante) y devuelve 1 si hubo avisos de controles sin id, 0 si no.'
            ),
        },
    },
    "_tools/migrate_modal_a11y.py": {
        "proposito": 'Convierte los contenedores de diálogo de templates/ en diálogos accesibles: agrega role=dialog + aria-modal + nombre accesible (aria-labelledby al título visible o aria-label donde no hay título), title_id a las llamadas del macro modal_header, id a los títulos sin él, convierte los <span class="close-btn"> en <button type=button> tabulables con aria-label y marca con data-modal-close los cierres que Escape debe activar. Idempotente y dry-run.',
        "simbolos": {
            "add_attr": (
                '💡 LA IDEA: Incorporar atributos de accesibilidad en la etiqueta de apertura de una ventana modal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite añadir roles y descripciones audibles a los diálogos existentes.\n\n'
                "⚙️ FUNCIONAMIENTO: Inserta el atributo antes del cierre de la etiqueta de apertura, soportando '>' y '/>'."
            ),
            "fin_de_llamada": (
                '💡 LA IDEA: Encontrar el paréntesis de cierre de una macro Jinja respetando comillas y anidamientos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite modificar llamadas a componentes sin romper los argumentos que contienen comas o paréntesis.\n\n'
                "⚙️ FUNCIONAMIENTO: Parser chico de paréntesis: desde la apertura de la llamada al macro, devuelve el índice exclusivo del ')' que la cierra, contando profundidad y respetando comillas simples/dobles (necesario porque los argumentos traen cadenas con paréntesis)."
            ),
            "plan_for": (
                '💡 LA IDEA: Detectar y planificar las correcciones de accesibilidad necesarias en las ventanas modales de una plantilla.\n\n'
                '🎯 POR QUE FUE GENERADA: Transforma diálogos visuales simples en componentes completamente accesibles para lectores de pantalla y teclado.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera las ediciones de un template en 5 pasadas: (1) contenedores DIALOGOS → role/aria-modal/aria-labelledby o aria-label (sumando clase modal--centered a modal-confirm/modal-choice), (2) title_id en llamadas al macro modal_header, (3) id en títulos visibles sin id, (4) span.close-btn → button con aria-label y data-modal-close, (5) data-modal-close/aria-label en controles puntuales. Devuelve (ediciones, avisos).'
            ),
            "archivo_no_aplica": (
                '💡 LA IDEA: Confirmar si una modificación específica corresponde verdaderamente al archivo analizado.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita ediciones erróneas o aplicaciones accidentales en plantillas no designadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Evita ediciones por accidente: dado el texto viejo de un control a marcar, dice si el archivo actual NO es el que le corresponde según ARCHIVO_MARCA (cada control vive en un template puntual); si el texto no está en el mapa, siempre aplica que no.'
            ),
            "main": (
                '💡 LA IDEA: Automatizar la adecuación de todas las ventanas modales a los estándares WCAG.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que todos los diálogos emergentes del sistema sean utilizables por personas con tecnologías asistivas.\n\n'
                '⚙️ FUNCIONAMIENTO: CLI dry-run/--apply: recorre templates/**/*.html con plan_for, imprime cada archivo con sus ediciones y el reemplazo (truncado), escribe con --apply aplicando de atrás hacia adelante, y devuelve 1 si hubo avisos (contenedores o títulos que ya no se encuentran).'
            ),
        },
    },
    "_tools/migrate_shadow_tokens.py": {
        "proposito": 'Tokeniza box-shadow duplicados EXACTOS: solo crea un var(--shadow-…) cuando el mismo valor (normalizando espacios y !important) aparece en >= 2 lugares; las sombras de un solo uso son decisiones de diseño y no se tocan. Los nombres se derivan de la geometría (--shadow-0-10-30-b50) y todo se valida antes de escribir nada (código atómico). Dry-run por defecto.',
        "simbolos": {
            "split_important": (
                '💡 LA IDEA: Separar el modificador !important del valor de sombra de una regla CSS.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite reemplazar la sombra por una variable conservando la prioridad de la cascada intacta.\n\n'
                "⚙️ FUNCIONAMIENTO: Separa 'sombra !important' en (sombra, ' !important') para que el sufijo se conserve DESPUÉS del var() en el reemplazo: var(--x) !important gana la cascada igual que el literal original, mientras que 'var(--x !important)' sería un token inexistente."
            ),
            "norm": (
                '💡 LA IDEA: Normalizar la sintaxis de una sombra colapsando espacios y formatos de color.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite agrupar sombras que son visualmente idénticas aunque difieran en espacios o comas.\n\n'
                '⚙️ FUNCIONAMIENTO: Normaliza una sombra para comparar: quita !important, colapsa espacios y compacta paréntesis/commas de rgba, de modo que rgba(0, 0, 0, 0.5) == rgba(0,0,0,0.5).'
            ),
            "token_name": (
                '💡 LA IDEA: Crear un nombre representativo para una variable de sombra según sus coordenadas y opacidad.\n\n'
                '🎯 POR QUE FUE GENERADA: Asigna identificadores claros y autodescriptivos a las nuevas variables de sombra generadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Deriva un nombre legible de la sombra: números en px (desplazamiento/blur/spread) con signos codificados, sufijo -inset si lo tiene (una sombra inset pinta distinto) y sufijo -bNN con la opacidad alpha; sin números usa --shadow-flat.'
            ),
            "verify": (
                '💡 LA IDEA: Validar estrictamente que los reemplazos de sombra no hayan alterado la estructura sintáctica del CSS.\n\n'
                '🎯 POR QUE FUE GENERADA: Actúa como red de seguridad abortando la operación si detecta cualquier desbalance en llaves o puntos y comas.\n\n'
                "⚙️ FUNCIONAMIENTO: Post-condición fuerte del codemod: comprueba que tras el reemplazo no cambió el balance de '{}' y ';', ni el número de declaraciones box-shadow, que cada sombra resultante está bien formada (regex WELL_FORMED o var/none), que los cortes no se solapan y que la cantidad de ediciones coincide con las declaraciones candidatas. Cualquier desvío aborta."
            ),
            "main": (
                '💡 LA IDEA: Detectar sombras repetidas en todo el proyecto y reemplazarlas por variables globales compartidas.\n\n'
                '🎯 POR QUE FUE GENERADA: Elimina duplicaciones en hojas de estilo unificando el aspecto visual de paneles y tarjetas.\n\n'
                '⚙️ FUNCIONAMIENTO: CLI en 5 fases: (1) cuenta frecuencia de sombras normalizadas fuera de variables.css y filtra por --min (default 2), (2) asigna nombres únicos resolviendo colisiones con sufijo, (3) con --apply agrega los tokens nuevos a variables.css, (4) calcula TODOS los reemplazos y los valida con verify() —si algo falla aborta sin escribir— y (5) escribe los archivos. Sin --apply solo imprime el plan.'
            ),
        },
    },
}
