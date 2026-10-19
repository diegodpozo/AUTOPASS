"""Explicaciones analizadas de herramientas de verificación y linters (_tools/check_*.py)."""

ANALISIS: dict[str, dict] = {
    "_tools/check_a11y_forms.py": {
        "proposito": 'Herramienta de auditoría que verifica la accesibilidad en todos los formularios HTML de la aplicación, asegurando que cada etiqueta <label> esté conectada a su campo de entrada, que los botones de alternar contraseña sean accesibles para lectores de pantalla y que las alertas visuales (toasts) se anuncien por voz.',
        "simbolos": {
            "rel": (
                '💡 LA IDEA: Convertir una ruta absoluta de disco en una ruta relativa legible desde la raíz del proyecto.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra reportes limpios y fáciles de leer en consola sin exponer directorios absolutos del entorno local.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte una ruta absoluta del disco en una ruta relativa al directorio raíz del proyecto con barras inclinadas para mostrarla en reportes legibles.'
            ),
            "control_after": (
                '💡 LA IDEA: Localizar el campo interactivo que se encuentra inmediatamente después de una etiqueta de texto en el formulario.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite comprobar la asociación de etiquetas y controles incluso cuando no se especifica el atributo for de manera explícita.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca y devuelve la etiqueta de campo interactivo (<input>, <select> o <textarea>) que le sigue inmediatamente a un <label> dentro del formulario.'
            ),
            "check_template": (
                '💡 LA IDEA: Auditar una plantilla HTML para verificar que cada campo posea una etiqueta legible para lectores de pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita formularios inaccesibles donde personas con discapacidad visual no puedan saber qué dato deben ingresar.\n\n'
                '⚙️ FUNCIONAMIENTO: Inspecciona el código HTML de una plantilla para confirmar que los <label> tengan el atributo for= correcto apuntando al identificador del campo, o bien que lo envuelvan físicamente, y que los botones de revelar contraseña tengan sus etiquetas de accesibilidad.'
            ),
            "check_toast": (
                '💡 LA IDEA: Confirmar que el contenedor de notificaciones flotantes incluya atributos de anuncio auditivo en tiempo real.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que los mensajes emergentes de éxito o advertencia sean leídos en voz alta por las tecnologías asistivas.\n\n'
                "⚙️ FUNCIONAMIENTO: Verifica que el contenedor global de notificaciones emergentes incluya los atributos role='alert' y aria-live para que las personas con disminución visual escuchen los mensajes que aparecen en pantalla."
            ),
            "main": (
                '💡 LA IDEA: Coordinar la auditoría de accesibilidad sobre todas las plantillas y formularios del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Actúa como barrera de control de calidad para bloquear cambios que introduzcan barreras de accesibilidad.\n\n'
                '⚙️ FUNCIONAMIENTO: Punto de entrada del script que recorre todas las plantillas HTML del sistema, evalúa los formularios y notificaciones, y finaliza con código de error si encuentra alguna falla de accesibilidad.'
            ),
        },
    },
    "_tools/check_a11y_modals.py": {
        "proposito": 'Guard que comprueba que todas las ventanas modales y diálogos superpuestos de la aplicación cumplan con los estándares internacionales de accesibilidad: posean rol de diálogo, nombre audible para lectores de pantalla y un botón de cierre operable mediante el teclado o la tecla Escape.',
        "simbolos": {
            "rel": (
                '💡 LA IDEA: Estandarizar la ruta de un archivo para expresarla de forma relativa a la raíz del repositorio.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita la interpretación de las alertas y errores en la terminal acortando las ubicaciones de archivo.\n\n'
                '⚙️ FUNCIONAMIENTO: Transforma la ruta física de un archivo en una ruta relativa normalizada respecto a la raíz del sistema.'
            ),
            "bloque": (
                '💡 LA IDEA: Extraer el contenido textual completo de un contenedor HTML respetando sus niveles de apertura y cierre.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite evaluar integralmente la estructura de una ventana modal sin omitir sus botones ni etiquetas hijas.\n\n'
                '⚙️ FUNCIONAMIENTO: Extrae el fragmento completo de texto HTML correspondiente a un elemento <div> contabilizando sus etiquetas de apertura y cierre para analizar su contenido interno.'
            ),
            "macro_emite_cierre": (
                '💡 LA IDEA: Verificar que las macros de cabecera modal generen un botón de cierre accesible con teclado y mouse.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que todas las ventanas emergentes del sistema provean siempre un mecanismo claro y estandarizado para cerrarse.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que la macro reutilizable de cabeceras modales genere un botón accesible con el atributo data-modal-close y una etiqueta explicativa.'
            ),
            "check_template": (
                '💡 LA IDEA: Inspeccionar una plantilla para comprobar que sus modales tengan atributos de diálogo y títulos identificables.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita ventanas emergentes que desorienten a usuarios que emplean lectores de pantalla o navegación por teclado.\n\n'
                "⚙️ FUNCIONAMIENTO: Analiza una plantilla HTML en busca de ventanas modales y valida que posean role='dialog', aria-modal='true', un título o etiqueta legible, y un botón de cierre apto para ser enfocado con el teclado."
            ),
            "main": (
                '💡 LA IDEA: Ejecutar el análisis de accesibilidad en todas las ventanas modales y emitir el balance general.\n\n'
                '🎯 POR QUE FUE GENERADA: Detiene el flujo de integración continua si se detecta alguna ventana modal que incumpla las normas de accesibilidad.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta la revisión sobre todas las pantallas del sistema, contabiliza cuántos modales cumplen las pautas y emite un informe detallando cualquier diálogo mal configurado.'
            ),
        },
    },
    "_tools/check_color_equivalence.py": {
        "proposito": 'Herramienta que garantiza que al reemplazar colores en hojas de estilo CSS por variables globales del sistema de diseño, la apariencia visual de la pantalla no cambie ni un solo píxel en comparación con la versión guardada en Git.',
        "simbolos": {
            "_alpha": (
                '💡 LA IDEA: Estandarizar cualquier valor de transparencia a una escala entera uniforme de 0 a 255.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite comparar matemáticamente transparencias expresadas en decimales, porcentajes o enteros sin discrepancias.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte cualquier valor de transparencia alfa (sea decimal de 0 a 1, porcentaje o entero) a un número estándar entre 0 y 255.'
            ),
            "hex_to_rgba": (
                '💡 LA IDEA: Convertir un código de color hexadecimal en una tupla de cuatro canales numéricos (rojo, verde, azul y opacidad).\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica la representación cromática para permitir comparaciones exactas entre colores de distinta notación.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte un código de color en formato hexadecimal (#RGB, #RRGGBB o #RRGGBBAA) a una tupla de cuatro números enteros Rojo, Verde, Azul y Alfa.'
            ),
            "rgb_to_rgba": (
                '💡 LA IDEA: Transformar cadenas en formato rgb() o rgba() a una tupla estándar de cuatro números.\n\n'
                '🎯 POR QUE FUE GENERADA: Homogeneíza diversas sintaxis CSS en un formato matemático homogéneo para su cotejo.\n\n'
                '⚙️ FUNCIONAMIENTO: Transforma valores de color expresados en formato rgb() o rgba() a una tupla estandarizada de cuatro valores numéricos.'
            ),
            "token_values": (
                '💡 LA IDEA: Extraer el diccionario de colores reales asociados a cada variable de diseño en una hoja de estilos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite conocer el tono visual exacto que respalda a cada token del sistema de diseño.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee un archivo CSS y extrae un diccionario con los colores reales asociados a cada variable de diseño personalizada declarada (custom property).'
            ),
            "resolve_tokens": (
                '💡 LA IDEA: Sustituir recursivamente las referencias var() por sus colores numéricos reales.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve tokens anidados para determinar el color final visible que renderiza el navegador.\n\n'
                '⚙️ FUNCIONAMIENTO: Reemplaza de forma recursiva todas las funciones var(--nombre) presentes en un texto CSS por sus colores numéricos reales o valores predeterminados.'
            ),
            "color_multiset": (
                '💡 LA IDEA: Contabilizar la frecuencia de aparición de cada color en un archivo de estilos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite comparar la distribución de color de un archivo antes y después de una refactorización de estilos.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera una lista con el recuento exacto de todos los colores resueltos que se usan en un archivo CSS para poder compararlo matemáticamente.'
            ),
            "_rgb_multiset": (
                '💡 LA IDEA: Filtrar exclusivamente los colores numéricos válidos ignorando marcas especiales o errores.\n\n'
                '🎯 POR QUE FUE GENERADA: Limpia el conjunto de datos para enfocar la auditoría únicamente en píxeles coloreables reales.\n\n'
                '⚙️ FUNCIONAMIENTO: Filtra únicamente los colores representados como tuplas numéricas válidas, descartando marcadores especiales o identificadores de error.'
            ),
            "multiset_delta": (
                '💡 LA IDEA: Calcular la desviación máxima entre dos conjuntos de colores.\n\n'
                '🎯 POR QUE FUE GENERADA: Detecta si un cambio en el código alteró accidentalmente la tonalidad visual respecto a la versión previa en Git.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula la diferencia máxima canal por canal entre dos grupos de colores, permitiendo saber si hubo alguna variación visible entre la versión actual y la anterior.'
            ),
            "_no_new_unresolved": (
                '💡 LA IDEA: Comprobar que ninguna variable CSS quede sin resolver tras actualizar los estilos.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que variables inexistentes dejen botones o textos con colores transparentes o caídos.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que tras una modificación de estilos no hayan aparecido variables o nombres de color inexistentes que dejen elementos sin pintar.'
            ),
            "_parents_of": (
                '💡 LA IDEA: Obtener los identificadores de los commits anteriores directos en el historial de Git.\n\n'
                '🎯 POR QUE FUE GENERADA: Identifica el punto de referencia histórico exacto contra el cual debe compararse el código actual.\n\n'
                '⚙️ FUNCIONAMIENTO: Obtiene los identificadores de los commits antecesores inmediatos en el historial de Git para realizar comparaciones de versiones.'
            ),
            "_git_show": (
                '💡 LA IDEA: Leer el contenido histórico de un archivo en Git sin modificar el espacio de trabajo local.\n\n'
                '🎯 POR QUE FUE GENERADA: Posibilita cotejar versiones anteriores contra el código actual de manera no destructiva.\n\n'
                '⚙️ FUNCIONAMIENTO: Obtiene el contenido que tenía un archivo en una versión histórica de Git específica sin alterar el archivo del disco de trabajo.'
            ),
            "committed_allowlist": (
                '💡 LA IDEA: Cargar la lista de archivos que tienen autorización explícita para alterar sus colores.\n\n'
                '🎯 POR QUE FUE GENERADA: Distingue cambios intencionales de diseño aprobados de modificaciones accidentales o regresiones.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga la lista de archivos que tienen autorización explícita para modificar sus colores intencionalmente sin que el guard lance una advertencia.'
            ),
            "main": (
                '💡 LA IDEA: Orquestar la verificación de equivalencia visual comparando el código contra la rama de Git.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que la migración a variables globales conserve la identidad visual del sistema sin variar ni un tono.\n\n'
                '⚙️ FUNCIONAMIENTO: Orquesta la verificación de equivalencia visual de estilos comparando el código de trabajo contra la rama principal de Git y advierte si algún color cambió indebidamente.'
            ),
        },
    },
    "_tools/check_consistencia_frontend.py": {
        "proposito": 'Auditor que escanea todas las llamadas a URLs y WebSockets en los archivos JavaScript y plantillas HTML, comparándolas contra las rutas oficiales registradas en el servidor FastAPI para detectar enlaces rotos o métodos HTTP no permitidos.',
        "simbolos": {
            "scan_urls": (
                '💡 LA IDEA: Recorrer scripts y plantillas para registrar todas las peticiones a endpoints del servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Construye el catálogo de URLs consumidas por la interfaz para validarlas contra el backend.\n\n'
                '⚙️ FUNCIONAMIENTO: Recorre el código frontend y las plantillas para recolectar todas las cadenas de texto que apuntan a endpoints del backend bajo los prefijos /v1/ y /ws/.'
            ),
            "front_path_to_api": (
                '💡 LA IDEA: Homogeneizar rutas dinámicas del frontend para hacerlas coincidir con el formato de rutas de FastAPI.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite equiparar parámetros como ${id} en JavaScript con rutas {id} en Python sin fallos de concordancia.\n\n'
                '⚙️ FUNCIONAMIENTO: Normaliza una dirección web reemplazando parámetros variables (como {id} o ${reserva}) por un comodín estándar para poder contrastarla con el esquema del servidor.'
            ),
            "load_openapi_paths": (
                '💡 LA IDEA: Extraer el catálogo oficial de rutas y métodos soportados a partir del esquema OpenAPI de FastAPI.\n\n'
                '🎯 POR QUE FUE GENERADA: Dispone de la lista fidedigna de rutas públicas que el servidor realmente reconoce.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga la instancia de la aplicación FastAPI y obtiene el catálogo completo de rutas públicas documentadas en la especificación OpenAPI.'
            ),
            "_is_websocket": (
                '💡 LA IDEA: Identificar si una ruta corresponde a una conexión bidireccional en tiempo real tipo WebSocket.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite verificar protocolos WebSocket de manera diferenciada respecto a peticiones HTTP comunes.\n\n'
                '⚙️ FUNCIONAMIENTO: Determina si una ruta registrada en el servidor corresponde a una conexión de comunicación en tiempo real tipo WebSocket.'
            ),
            "_walk_routes": (
                '💡 LA IDEA: Recorrer recursivamente todos los routers y subrutas registradas en la aplicación.\n\n'
                '🎯 POR QUE FUE GENERADA: Descubre endpoints anidados bajo prefijos o módulos para que ninguno quede fuera de la verificación.\n\n'
                '⚙️ FUNCIONAMIENTO: Recorre en forma recursiva los enrutadores de FastAPI acumulando prefijos de URL para listar todas las rutas secundarias y sus controladores.'
            ),
            "load_app": (
                '💡 LA IDEA: Importar e instanciar en memoria la aplicación principal de FastAPI.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite inspeccionar directamente la configuración y las rutas activas del sistema sin necesidad de levantar el servidor web.\n\n'
                '⚙️ FUNCIONAMIENTO: Importa la aplicación central de FastAPI desde el archivo principal del proyecto para examinar su configuración en memoria.'
            ),
            "method_supported": (
                '💡 LA IDEA: Validar si el verbo HTTP (GET, POST, PUT, DELETE) utilizado por la llamada web está soportado por el endpoint.\n\n'
                "🎯 POR QUE FUE GENERADA: Previene errores de tipo '405 Method Not Allowed' antes de que el código llegue a los usuarios.\n\n"
                '⚙️ FUNCIONAMIENTO: Verifica si el método HTTP utilizado por una llamada del frontend (GET, POST, PUT, DELETE) está habilitado en el endpoint correspondiente del servidor.'
            ),
            "main": (
                '💡 LA IDEA: Comparar exhaustivamente las peticiones del frontend contra las rutas reales de la API.\n\n'
                '🎯 POR QUE FUE GENERADA: Detecta enlaces rotos, URLs obsoletas o parámetros mal nombrados entre la interfaz y el servidor.\n\n'
                '⚙️ FUNCIONAMIENTO: Compara las rutas usadas por la interfaz de usuario contra las ofrecidas por la API e informa si alguna llamada apunta a una dirección inexistente.'
            ),
        },
    },
    "_tools/check_css_balance.py": {
        "proposito": "Verificador de sintaxis CSS que asegura que todas las llaves de apertura '{' tengan su correspondiente llave de cierre '}', evitando que reglas de pantallas móviles (@media) atrapen y rompan el diseño en pantallas de computadora.",
        "simbolos": {
            "_strip_noise": (
                '💡 LA IDEA: Quitar comentarios y cadenas entre comillas en código CSS para contabilizar solo llaves estructurales.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita falsos positivos producidos por llaves escritas en comentarios o textos decorativos.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina comentarios y cadenas de texto entre comillas en el código CSS para contabilizar únicamente las llaves que delimitan bloques de reglas.'
            ),
            "analyze": (
                '💡 LA IDEA: Rastrear línea por línea que cada apertura de llave cuente con su debido cierre.\n\n'
                '🎯 POR QUE FUE GENERADA: Señala con exactitud la línea donde se desbalanceó el código y desarmó la cascada de estilos.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee un archivo CSS línea por línea, lleva un registro de las llaves abiertas en una pila y señala la primera línea donde se produjo un desajuste.'
            ),
            "_strip_comments_lines": (
                '💡 LA IDEA: Filtrar comentarios multilínea de los estilos preservando los números de línea reales.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita el análisis sintáctico sin desfasar la numeración de los avisos de error.\n\n'
                '⚙️ FUNCIONAMIENTO: Generador que entrega las líneas de un archivo de estilos tras limpiar comentarios multilínea y caracteres de escape.'
            ),
            "find_unbalanced": (
                '💡 LA IDEA: Analizar todas las hojas de estilo del proyecto en busca de llaves abiertas o sobrantes.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene que bloques incompletos atrapen reglas posteriores y arruinen la visualización en distintos dispositivos.\n\n'
                '⚙️ FUNCIONAMIENTO: Escanea todas las hojas de estilo del proyecto y compila un reporte de aquellos archivos que tienen llaves sin cerrar o llaves sobrantes.'
            ),
            "main": (
                '💡 LA IDEA: Ejecutar el control de balance de llaves en todo el repositorio de estilos.\n\n'
                '🎯 POR QUE FUE GENERADA: Detiene el proceso de prueba si existe algún archivo CSS con llaves mal cerradas.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta el chequeo sobre todo el catálogo de estilos CSS e interrumpe el proceso si detecta alguna anomalía que pueda alterar la visualización de la plataforma.'
            ),
        },
    },
    "_tools/check_css_design_system.py": {
        "proposito": 'Guard del sistema de diseño que audita las hojas de estilo midiendo la consistencia de colores, espacios, sombras, transiciones y el cumplimiento de las normas de reducción de movimiento y visibilidad del foco.',
        "simbolos": {
            "hex_to_rgba": (
                '💡 LA IDEA: Convertir códigos de color hexadecimal a tuplas numéricas estandarizadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite evaluar matemáticamente la consistencia de la paleta cromática.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte un código de color hexadecimal en una tupla normalizada de cuatro números con sus componentes rojo, verde, azul y transparencia.'
            ),
            "rgb_to_rgba": (
                '💡 LA IDEA: Transformar expresiones rgb/rgba a estructuras numéricas uniformes.\n\n'
                '🎯 POR QUE FUE GENERADA: Normaliza la representación de colores sin importar cómo fueron declarados en el archivo.\n\n'
                '⚙️ FUNCIONAMIENTO: Interpreta una coincidencia de expresión regular de rgb() o rgba() y la devuelve como una tupla numérica estándar.'
            ),
            "iter_css": (
                '💡 LA IDEA: Recorrer todas las hojas de estilo del proyecto entregando su contenido limpio de comentarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Automatiza la lectura y análisis masivo de estilos para la auditoría de diseño.\n\n'
                '⚙️ FUNCIONAMIENTO: Recorre todos los archivos CSS del proyecto y produce pares con la ruta del archivo y su contenido desprovisto de comentarios.'
            ),
            "declarations_only": (
                '💡 LA IDEA: Extraer solo los bloques de propiedades descartando los selectores de las reglas.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que nombres de clases como btn-blue se confundan erróneamente con colores reales.\n\n'
                '⚙️ FUNCIONAMIENTO: Descarta los selectores de las reglas CSS y conserva solo el bloque de propiedades para evitar confundir identificadores con valores de color.'
            ),
            "token_rgba_map": (
                '💡 LA IDEA: Asociar cada tono numérico de color con el nombre de su variable de diseño correspondiente.\n\n'
                '🎯 POR QUE FUE GENERADA: Sugiere automáticamente qué token utilizar cuando se detecta un color hardcodeado.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee el archivo variables.css y construye un mapa inverso que asocia cada valor de color exacto con el nombre de su variable correspondiente.'
            ),
            "_alpha": (
                '💡 LA IDEA: Escalar cualquier porcentaje o decimal de opacidad a un número entero de 0 a 255.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite comparar y agrupar transparencias de forma precisa.\n\n'
                '⚙️ FUNCIONAMIENTO: Normaliza el componente de opacidad a una escala numérica entre 0 y 255 admitiendo porcentajes o decimales.'
            ),
            "alpha_scale": (
                '💡 LA IDEA: Medir los niveles de transparencia utilizados en cada familia cromática.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene una graduación armónica y predecible de sombras y capas transparentes en la UI.\n\n'
                '⚙️ FUNCIONAMIENTO: Analiza qué niveles de transparencia se emplean en cada familia de color (blancos, negros, dorados, grises) para asegurar una paleta armónica.'
            ),
            "measure": (
                '💡 LA IDEA: Calcular estadísticas generales sobre el uso de variables, sombras y animaciones.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee una calificación cuantitativa de la consistencia visual y salud del diseño.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula métricas estadísticas globales del CSS: cantidad de colores únicos, porcentajes de reutilización de espaciados, variedad de sombras y animaciones.'
            ),
            "check_reduced_motion": (
                '💡 LA IDEA: Validar que las animaciones contemplen la preferencia de reducir el movimiento en pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege a usuarios sensibles a mareos o problemas vestibulares respetando sus ajustes de accesibilidad.\n\n'
                '⚙️ FUNCIONAMIENTO: Verifica que el sistema respete la configuración de usuarios que prefieren reducir animaciones bruscas mediante la regla prefers-reduced-motion de WCAG.'
            ),
            "check_focus_ring": (
                '💡 LA IDEA: Verificar que el resalte visual al navegar con teclado no sea tapado por reglas específicas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que los usuarios que navegan sin mouse siempre puedan ver con claridad qué elemento está seleccionado.\n\n'
                '⚙️ FUNCIONAMIENTO: Valida que el contorno visual que resalta los elementos enfocados con el teclado esté configurado con una especificidad suficiente para que ninguna regla particular lo anule.'
            ),
            "iter_js": (
                '💡 LA IDEA: Recorrer todos los scripts JavaScript del cliente para auditar su código fuente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite inspeccionar comportamientos dinámicos que inciden en el diseño y accesibilidad.\n\n'
                '⚙️ FUNCIONAMIENTO: Itera por todos los archivos JavaScript del frontend para inspeccionar su código fuente.'
            ),
            "check_js_scroll_motion": (
                '💡 LA IDEA: Detectar si algún script realiza desplazamientos automáticos suaves sin chequear la preferencia de accesibilidad.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita animaciones de scroll forzadas en personas que configuraron el sistema para no ver movimientos bruscos.\n\n'
                '⚙️ FUNCIONAMIENTO: Detecta si algún script realiza desplazamientos de pantalla suaves de forma fija en lugar de consultar la preferencia de reducción de movimiento del usuario.'
            ),
            "main": (
                '💡 LA IDEA: Comparar los indicadores de diseño actuales contra la línea de base histórica del proyecto.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene la degradación progresiva de la accesibilidad y coherencia visual ante nuevos cambios de código.\n\n'
                '⚙️ FUNCIONAMIENTO: Compara las métricas de diseño actuales contra una línea base guardada y falla si se introducen regresiones en la accesibilidad o en la coherencia visual.'
            ),
        },
    },
    "_tools/check_css_huerfano.py": {
        "proposito": "Auditor que detecta clases CSS 'huérfanas' o en desuso: clases que fueron definidas en las hojas de estilo pero que ya no son utilizadas por ninguna plantilla HTML, archivo JavaScript o código Python del sistema.",
        "simbolos": {
            "_strip_comments": (
                '💡 LA IDEA: Eliminar comentarios en hojas de estilo para analizar únicamente código operativo.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita contabilizar selectores comentados que ya no forman parte activa del diseño.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina los comentarios dentro del código CSS para evitar extraer selectores o nombres de clase que estén comentados.'
            ),
            "defined_classes": (
                '💡 LA IDEA: Confeccionar el inventario de todas las clases CSS definidas en el proyecto.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber con certeza qué estilos existen y en qué archivos fueron declarados.\n\n'
                '⚙️ FUNCIONAMIENTO: Examina todas las hojas de estilo y devuelve un diccionario con cada nombre de clase y la lista de archivos donde está declarada.'
            ),
            "_read": (
                '💡 LA IDEA: Leer archivos de texto controlando posibles excepciones de codificación.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza una lectura robusta de archivos sin interrumpir el análisis por caracteres especiales.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee el contenido de un archivo de texto de forma segura ignorando posibles errores de codificación o de permisos.'
            ),
            "_usage_blob": (
                '💡 LA IDEA: Unificar el código fuente de templates, scripts y backend en un único bloque de texto.\n\n'
                '🎯 POR QUE FUE GENERADA: Agiliza exponencialmente la búsqueda de clases mediante consultas de contención en memoria.\n\n'
                '⚙️ FUNCIONAMIENTO: Concatena en un único bloque de texto todo el contenido de plantillas HTML, scripts JS y código Python del proyecto para realizar búsquedas rápidas.'
            ),
            "find_orphans": (
                '💡 LA IDEA: Contrastar las clases definidas contra el código de la aplicación para hallar estilos abandonados.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a reducir el peso de las hojas de estilo eliminando reglas que ya no se usan.\n\n'
                '⚙️ FUNCIONAMIENTO: Compara las clases CSS declaradas contra el bloque de código de la app, excluyendo librerías externas y nombres dinámicos, para encontrar clases abandonadas.'
            ),
            "load_baseline": (
                '💡 LA IDEA: Cargar la lista histórica de clases huérfanas preexistentes permitidas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite vigilar que no surjan nuevas clases huérfanas sin bloquear el desarrollo por deuda técnica anterior.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga la lista de referencia de clases huérfanas históricas permitidas desde su archivo JSON.'
            ),
            "main": (
                '💡 LA IDEA: Contabilizar las clases en desuso y alertar si la cifra supera la línea base registrada.\n\n'
                '🎯 POR QUE FUE GENERADA: Preserva la higiene del código CSS impidiendo la acumulación descontrolada de reglas muertas.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula el número de clases huérfanas existentes y alerta si la cantidad creció respecto a la línea base registrada.'
            ),
        },
    },
    "_tools/check_css_tokens.py": {
        "proposito": 'Guard que verifica la integridad de los tokens CSS (Custom Properties): detecta si alguna regla intenta usar una variable que no fue declarada o si existen variables definidas que nunca se utilizan en ningún lugar.',
        "simbolos": {
            "_orphaned_decls": (
                '💡 LA IDEA: Detectar variables CSS escritas fuera de bloques selectores válidos.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene tokens colocados por error fuera de :root que los navegadores ignoran silenciosamente.\n\n'
                '⚙️ FUNCIONAMIENTO: Identifica declaraciones de variables que quedaron escritas fuera de cualquier bloque selector (por ejemplo, después del cierre de :root), lo que provoca que los navegadores las ignoren por completo.'
            ),
            "_collect": (
                '💡 LA IDEA: Construir el catálogo completo de variables CSS declaradas y consumidas en la aplicación.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite contrastar oferta y demanda de variables de diseño para hallar inconsistencias.\n\n'
                '⚙️ FUNCIONAMIENTO: Escanea todos los archivos CSS para armar el inventario de variables declaradas, variables consumidas mediante var() y en qué archivos se utilizan.'
            ),
            "main": (
                '💡 LA IDEA: Evaluar el balance de variables en todo el frontend y emitir alertas si hay errores.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que nombres mal escritos o variables inexistentes dejen partes de la interfaz sin pintar.\n\n'
                '⚙️ FUNCIONAMIENTO: Evalúa el balance de variables en todo el frontend y reporta con código de error si hay variables no resueltas o tokens huérfanos.'
            ),
        },
    },
    "_tools/check_header_scope.py": {
        "proposito": 'Verificador que garantiza que la barra de navegación superior (header) de los portales de usuario y panel de control no herede estilos de elementos secundarios o componentes internos de las pestañas.',
        "simbolos": {
            "main": (
                '💡 LA IDEA: Asegurar que los estilos del encabezado principal se apliquen exclusivamente a la barra superior sin afectar tarjetas internas.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene que etiquetas header internas dentro de paneles o tarjetas hereden accidentalmente el diseño de la barra de navegación.\n\n'
                "⚙️ FUNCIONAMIENTO: Comprueba que las reglas de estilo apunten estrictamente al encabezado principal directo mediante el selector '>' y que ninguna subpestaña o tarjeta interna declare etiquetas <header> indebidas."
            ),
        },
    },
}
