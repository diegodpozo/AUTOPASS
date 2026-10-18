"""Explicaciones analizadas de utilidades de desarrollo/demo y verificadores del manual
(análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "manual/tools/verificar-capturas.py": {
        "proposito": 'Control de calidad automático de las capturas del manual: recorre los PNG de manual/assets/img y mide peso, variedad de color y varianza para detectar imágenes vacías, planas o rotas antes de publicar, sin tener que mirarlas una por una.',
        "simbolos": {
            "analizar": (
                '💡 LA IDEA: Medir las propiedades visuales de una captura (dimensiones, peso, variedad cromática y contraste).\n\n'
                '🎯 POR QUE FUE GENERADA: Detecta automáticamente imágenes vacías, monocromáticas o renderizadas por la mitad sin tener que revisarlas manualmente una por una.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre una captura con PIL, la convierte a RGB y la reduce a 320 px de ancho para medirla: devuelve un dict con el nombre, las dimensiones, el peso en KB, la cantidad de colores únicos de la muestra y la varianza promedio de los canales respecto a 128 (indicador de contraste).'
            ),
            "main": (
                '💡 LA IDEA: Evaluar todas las capturas de pantalla del manual y listar aquellas que no alcancen los estándares de calidad.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene la publicación de manuales con capturas defectuosas o pantallas en blanco.\n\n'
                '⚙️ FUNCIONAMIENTO: Lista todos los PNG de manual/assets/img ordenados y emite una tabla por archivo marcando REVISAR cuando la imagen pesa menos de 20 KB, tiene menos de 25 colores únicos o una varianza menor a 120. Devuelve 1 si no hay capturas y 0 en caso contrario, e imprime el total a revisar.'
            ),
        },
    },
    "manual/tools/verificar-pdf.py": {
        "proposito": 'Verificación mecánica del PDF del manual: busca los defectos típicos de la paginación automática (páginas en blanco o casi vacías, títulos huérfanos al pie, índice sin links navegables y marcadores incompletos). No reemplaza revisarlo a ojo, pero avisa rápido de los problemas estructurales.',
        "simbolos": {
            "lineas_de_contenido": (
                '💡 LA IDEA: Extraer el texto significativo de una página descartando encabezados, pies de página y líneas vacías.\n\n'
                '🎯 POR QUE FUE GENERADA: Aísla el contenido real del documento para evaluar si una página tiene información sustantiva o quedó vacía.\n\n'
                '⚙️ FUNCIONAMIENTO: Extrae el texto de una página, descarta las líneas vacías y filtra las que son puro ruido de encabezado o pie ("Página N de M", "Documento de uso interno", "AUTOPASS"), dejando solo las líneas con contenido real.'
            ),
            "titulo_al_pie": (
                '💡 LA IDEA: Determinar si la última línea de una página es un título que quedó cortado de su contenido.\n\n'
                '🎯 POR QUE FUE GENERADA: Detecta títulos huérfanos que arruinan la lectura visual al quedar aislados al pie de página.\n\n'
                '⚙️ FUNCIONAMIENTO: Decide si la última línea de una página parece un título suelto: primero le quita el contador numerado pegado al final (p. ej. "Guardá.6"), descarta líneas de más de 90 caracteres o que terminan en puntuación, y acepta las que coinciden con PATRON_TITULO o son cortas (menos de 60), sin dígito inicial y sin punto final.'
            ),
            "imagenes_de": (
                '💡 LA IDEA: Contabilizar cuántas imágenes o figuras contiene una página del documento PDF.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber si una página con poco texto está justificada por la presencia de diagramas o capturas.\n\n'
                '⚙️ FUNCIONAMIENTO: Cuenta los objetos XObject declarados en /Resources de la página (es decir, las imágenes que contiene) y devuelve 0 si por cualquier motivo la estructura no se puede leer.'
            ),
            "texto_util": (
                '💡 LA IDEA: Limpiar el texto de una página quitando frases repetitivas y avisos institucionales.\n\n'
                '🎯 POR QUE FUE GENERADA: Mide con precisión la densidad informativa real de cada hoja del manual.\n\n'
                '⚙️ FUNCIONAMIENTO: Limpia el texto de una página eliminando encabezado, pie y numeración ("Página N de M", "AUTOPASS", "Documento de uso interno" y la primera ocurrencia de "Manual del ...") y colapsa los espacios, de modo que la cantidad de caracteres mida el contenido útil de verdad.'
            ),
            "normalizar": (
                '💡 LA IDEA: Convertir el texto a caracteres alfanuméricos en minúsculas sin acentos ni espacios.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita la búsqueda de palabras clave como índice o títulos sin importar su formato visual.\n\n'
                '⚙️ FUNCIONAMIENTO: Reduce el texto a minúsculas sin nada que no sea letra o número, para poder buscar palabras como "indice" ignorando acentos, mayúsculas y espacios.'
            ),
            "verificar_indice": (
                '💡 LA IDEA: Comprobar que la página de índice incluya enlaces navegables y números de página correctos.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el lector pueda hacer clic en el índice del PDF para saltar directamente a la sección deseada.\n\n'
                '⚙️ FUNCIONAMIENTO: Comprueba que la página 2 contenga el índice: que aparezca la palabra "indice" en su texto normalizado, que las anotaciones /Link (una por entrada) existan y que se vean números de página. Reporta cada hallazgo agregando mensajes a la lista de problemas y devuelve la cantidad de entradas con link.'
            ),
            "contar_nodos": (
                '💡 LA IDEA: Recorrer el árbol jerárquico de marcadores o bookmarks del PDF y contar sus elementos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que la barra lateral de navegación del PDF contenga todos los capítulos y subtemas.\n\n'
                '⚙️ FUNCIONAMIENTO: Recorre recursivamente el árbol de marcadores (outline) del PDF contando los hermanos de cada nivel (/Next) y bajando a los hijos (/First), de modo que devuelva el total de entradas incluidas las anidadas.'
            ),
            "verificar_marcadores": (
                '💡 LA IDEA: Validar que el PDF posea un menú de marcadores navegables completo y bien estructurado.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza la accesibilidad y fácil navegación del documento en cualquier lector de PDF.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee /Outlines del diccionario raíz del PDF: si no existe agrega el problema "sin marcadores", si existe cuenta sus nodos con contar_nodos e informa si hay menos de 10 entradas. Ante cualquier excepción la anota como problema y devuelve 0.'
            ),
            "empieza_seccion": (
                '💡 LA IDEA: Detectar si el texto de la página se inicia con un encabezado de sección numerado.\n\n'
                '🎯 POR QUE FUE GENERADA: Confirma que las secciones principales comiencen prolijamente al principio de una hoja nueva.\n\n'
                '⚙️ FUNCIONAMIENTO: Mira la primera línea no vacía del texto de una página y devuelve True si empieza con un título de sección numerado ("6. Tickets"), lo que indica que la página abre sección nueva.'
            ),
            "verificar": (
                '💡 LA IDEA: Auditar integralmente la calidad editorial del PDF página por página.\n\n'
                '🎯 POR QUE FUE GENERADA: Emite un diagnóstico detallado sobre hojas en blanco, títulos mal ubicados e índices descalibrados.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el PDF y analiza página por página: clasifica cada una como VACIA, casi vacia, cierre (cola de sección o última página) o escasa según los caracteres útiles y las imágenes, y marca las que terminan en un título huérfano al pie (excluyendo la última y la del índice). Al final valida índice y marcadores, imprime el reporte completo y devuelve la lista de problemas.'
            ),
            "main": (
                '💡 LA IDEA: Ejecutar el control de calidad automático sobre los manuales en PDF del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide dar por terminada la compilación de documentación si existen defectos de diagramación.\n\n'
                '⚙️ FUNCIONAMIENTO: Elige los PDF de manual/pdf (todos, o el nombrado como argumento de línea de comandos), ejecuta verificar en cada uno y devuelve 1 si no hay archivos generados.'
            ),
        },
    },
    "scripts/arduino_bridge.py": {
        "proposito": 'Puente entre el broker MQTT de AUTOPASS y el Arduino Uno que acciona las barreras: queda escuchando los tópicos de control de entrada/salida y traduce cada mensaje a un comando serie USB (OPEN_ENTRADA, CLOSE_SALIDA, etc.) para que la barrera se mueva sin que la aplicación toque el hardware directamente.',
        "simbolos": {
            "find_arduino_port": (
                '💡 LA IDEA: Localizar el puerto serie USB al que está conectado el microcontrolador Arduino.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite la conexión automática con el hardware de barrera sin necesidad de configurar manualmente el puerto COM en cada inicio.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el puerto serie a usar: si la variable de entorno SERIAL_PORT está definida y no es "AUTO" la devuelve tal cual; si no, recorre los puertos del sistema y devuelve el primero cuya descripción mencione Arduino, CH340, FT232 o USB Serial, o cuyo nombre sea ttyACM/COM. Devuelve None si no hay ninguno.'
            ),
            "main": (
                '💡 LA IDEA: Escuchar órdenes de apertura y cierre por MQTT y retransmitirlas por puerto serie al Arduino.\n\n'
                '🎯 POR QUE FUE GENERADA: Comunica el backend del sistema con la electrónica física que acciona los motores de la barrera de acceso.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el puerto serie (esperando 2 s por el auto-reset del Arduino), se conecta al broker MQTT configurado por entorno y se suscribe a los tópicos de control de entrada y salida. En cada mensaje interpreta el JSON (o el texto libre con "CLOSE") para armar el comando COMANDO_BARRERA y lo escribe por serial; si el puerto se cerró, reintenta detectar y abrir el Arduino. Termina en loop_forever atendiendo mensajes.'
            ),
        },
    },
    "scripts/cleanup_invalid_plates.py": {
        "proposito": 'Saneamiento de la base de prueba: elimina de todas las tablas los registros cuya patente no coincide con un formato LATAM válido, para que las métricas y búsquedas no se contaminen con patentes mal formadas. Es idempotente, admite --dry-run y guarda un respaldo JSON de lo borrado.',
        "simbolos": {
            "_bad": (
                '💡 LA IDEA: Validar si una patente almacenada incumple los formatos legales de patentes de la región.\n\n'
                '🎯 POR QUE FUE GENERADA: Filtra valores mal formateados o basura generada durante pruebas para su saneamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve True cuando la patente, una vez normalizada, no está vacía y no pasa la validación de formato: así se borran solo las inválidas con contenido y se respetan las vacías (que suelen ser registros sin cámara o manuales).'
            ),
            "_targets": (
                '💡 LA IDEA: Mapear todas las tablas y modelos de la base de datos que almacenan números de patente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite una limpieza integral y coordinada en todas las entidades donde impacta un vehículo.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la lista de tablas a recorrer con su modelo SQLAlchemy y el predicado que marca la fila como inválida: access_logs (por patente_detectada o normalized_patente), reservations, vehicles, users y mercadopago_payments (por patente).'
            ),
            "_row_snapshot": (
                '💡 LA IDEA: Generar una copia de respaldo en formato JSON de un registro antes de ser eliminado.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que cualquier depuración de datos sea reversible y auditable en caso de error.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte una fila de la base en un dict plano apto para el respaldo JSON: recorre las columnas de la tabla, conserva los tipos primitivos tal cual y serializa el resto con str(), agregando el nombre de la tabla en "_table".'
            ),
            "main": (
                '💡 LA IDEA: Orquestar el escaneo, respaldo y eliminación de patentes inválidas en la base de datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpia la base de pruebas para evitar que métricas y reportes se distorsionen con datos defectuosos.\n\n'
                '⚙️ FUNCIONAMIENTO: Parsea los argumentos (--dry-run y --backup), abre la sesión y recorre los targets de _targets acumulando las filas inválidas: las agrega al respaldo y, salvo en dry-run, las borra. Si no es simulación y hay bajas, escribe el respaldo JSON, hace commit y reporta el total; en dry-run solo informa qué se habría borrado. Cierra la sesión siempre.'
            ),
        },
    },
    "scripts/crear_usuarios_demo.py": {
        "proposito": 'Carga inicial de datos de demo: crea de una corrida 20 usuarios de prueba del dominio @pruebaoc.com con su vehículo, reservas ya pasadas y sus entradas/salidas, para tener con qué probar el panel, las métricas y los historiales sin depender de tráfico real.',
        "simbolos": {
            "main": (
                '💡 LA IDEA: Generar automáticamente 20 usuarios ficticios con vehículos, reservas y registros de acceso.\n\n'
                '🎯 POR QUE FUE GENERADA: Puebla la base de datos con escenarios realistas para poder probar y demostrar la plataforma sin requerir usuarios reales.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera 20 usuarios con Faker en español rioplatense (evitando repetir emails contra los existentes), los inserta con hash de la contraseña "Demo1234!" y datos aleatorios de DNI, teléfono y dirección. Luego le asigna a cada uno un vehículo con patente normalizada, 1 o 2 reservas pasadas en una sucursal al azar con su par de AccessLogs de entrada y salida, y acredita el monto de cada reserva en el saldo del usuario; imprime "OK" al terminar.'
            ),
        },
    },
    "scripts/generate_demo_traffic.py": {
        "proposito": 'Alimenta las métricas y el mapa de calor de horarios con movimientos ALPR ficticios: genera entradas y salidas por sucursal repartidas con una distribución realista de día de la semana y hora del día. Se puede reejecutar sin duplicar datos porque antes borra los movimientos que generó él mismo (marcados con imagen_path "demo:traffic").',
        "simbolos": {
            "_elegir_hora": (
                '💡 LA IDEA: Sortear un horario diurno priorizando las franjas horarias con picos de mayor concurrencia.\n\n'
                '🎯 POR QUE FUE GENERADA: Genera distribuciones de tránsito verosímiles que reflejan el comportamiento habitual de un estacionamiento comercial.\n\n'
                '⚙️ FUNCIONAMIENTO: Sortea una hora del día (0..23) ponderada por la lista HORAS_PESO, de modo que aparezcan con más frecuencia los picos laborales de 8 h, 13 h y 18-19 h y casi no haya tráfico de madrugada.'
            ),
            "generar": (
                '💡 LA IDEA: Limpiar el tráfico simulado anterior y generar nuevos accesos y cobros repartidos por sucursal y día.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite probar tableros de control y mapas de calor con datos estadísticos dinámicos y realistas.\n\n'
                '⚙️ FUNCIONAMIENTO: Con una semilla fija, borra los AccessLog previamente generados por este script (imagen_path igual a la marca) y luego recorre los últimos `dias` días hacia atrás y cada sucursal activa, generando un volumen de movimientos por día escalado por el peso del día de la semana, el de la sucursal y un jitter aleatorio. Cada movimiento crea el par ENTRADA/SALIDA con patente normalizada, hora sorteada dentro del día, duración de 0,5 a 7 h, costo, método de pago y tiempo de OCR; devuelve los contadores (y un aviso si no hay vehículos cargados).'
            ),
            "main": (
                '💡 LA IDEA: Interpretar parámetros de simulación y ejecutar la inyección de tráfico ficticio.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee una herramienta por consola para calibrar rápidamente el volumen de demostración del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Interpreta los argumentos --dias, --por-dia y --seed, abre la sesión de base de datos, llama a generar e imprime el resultado, cerrando la sesión siempre.'
            ),
        },
    },
    "scripts/generate_reservation_test.py": {
        "proposito": 'Herramienta del usuario (no se commitea) que arma tandas completas de pruebas de reservas: planifica movimientos en el pasado sin pisar cupos ni ventanas ya usadas, los crea y abona, simula los ingresos y egresos con tiempo virtual y los deja COMPLETADA; también ofrece el escenario de saturación por hora. Cada tanda queda registrada en un snapshot JSON de data/pruebas para poder limpiarla después.',
        "simbolos": {
            "_snapshot_path": (
                '💡 LA IDEA: Definir la ruta del archivo JSON donde se guardará el estado de una tanda de pruebas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite almacenar el registro exacto de reservas generadas para su posterior limpieza sin tocar datos ajenos.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la ruta del snapshot JSON de una tanda dentro de data/pruebas: <nombre>.json.'
            ),
            "_validar_nombre": (
                '💡 LA IDEA: Verificar que el identificador de la tanda use solo caracteres alfanuméricos y guiones.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita inyecciones o nombres inválidos al crear archivos en el disco.\n\n'
                '⚙️ FUNCIONAMIENTO: Valida que el nombre de la tanda sea [a-z0-9_-] de 1 a 40 caracteres; si no cumple, sale del script con mensaje de error (evita rutas raras en el snapshot).'
            ),
            "_branch_names": (
                '💡 LA IDEA: Consultar y listar los nombres de todas las sedes disponibles en el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que la simulación de pruebas distribuya reservas únicamente en sedes activas y reales.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve la lista de nombres de sucursal consultando BranchRepository.get_all sobre la sesión dada.'
            ),
            "_user_tipo": (
                '💡 LA IDEA: Obtener la categoría del vehículo principal registrado por un usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite cotizar y reservar la plaza adecuada según el tamaño del auto asignado al usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el tipo de vehículo del primer auto del usuario (normalizando el enum a string) o "Auto" si el usuario todavía no tiene vehículos.'
            ),
            "_seed_ocupacion": (
                '💡 LA IDEA: Calcular la ocupación real previa de las sucursales para no superponer turnos en el simulador.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que las reservas ficticias no violen los cupos de aforo existentes ni choquen con reservas reales.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula para la ventana [wstart, wend] dos cosas: la ocupación real por sucursal y tipo con las reservas ACTIVA/PENDIENTE pagadas de todos los usuarios (occ), y todas las ventanas ya ocupadas por los usuarios de prueba con cualquier estado (busy), para que los movimientos nuevos no repitan espacios usados. Devuelve (occ, busy) con los intervalos inicio/fin y el tipo real del vehículo.'
            ),
            "build_plan": (
                '💡 LA IDEA: Diseñar una agenda cronológica de reservas históricas distribuidas armónicamente por sucursal y modalidad.\n\n'
                '🎯 POR QUE FUE GENERADA: Estructura una batería compleja de pruebas sin sobrecargar la capacidad máxima de las sedes.\n\n'
                '⚙️ FUNCIONAMIENTO: Planifica N movimientos en el pasado [01-09-2026, ahora): cicla usuarios pruebaoc, sucursales y modos (sin "hora", que exige anticipación mínima) buscando para cada combinación el inicio más reciente válido que termine en el pasado, no supere la capacidad de la sucursal ni solape con reservas propias del usuario; actualiza la ocupación simulada en cada asignación. Devuelve el plan, la ocupación, los usuarios, las sucursales, las entradas que no entraron y las capacidades.'
            ),
            "_print_plan": (
                '💡 LA IDEA: Imprimir en consola el informe detallado del plan de reservas proyectado.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al operador verificar el cronograma y capacidad antes de efectuar escrituras en la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Imprime el reporte del plan: cantidad de usuarios, planeadas y sin lugar; cobertura por sucursal×modo; cantidades por sucursal×tipo contra la capacidad; y el máximo de simultáneos calculado por barrido de eventos de comienzo y fin, marcado OK o EXCEDE según la capacidad. Al final lista las entradas que quedaron sin lugar.'
            ),
            "_auto_users": (
                '💡 LA IDEA: Filtrar los usuarios de prueba cuyo vehículo principal sea un automóvil estándar.\n\n'
                '🎯 POR QUE FUE GENERADA: Selecciona candidatos homogéneos para ensayos de saturación de cupos por hora.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve los usuarios pruebaoc cuyo vehículo principal es Auto, ordenados por id, que son los elegibles para el escenario por hora.'
            ),
            "_hora_base_slot": (
                '💡 LA IDEA: Calcular el primer turno horario disponible respetando los tiempos mínimos de anticipación.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene que la prueba intente generar reservas en turnos que el sistema rechazaría por falta de anticipación.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula el primer turno válido del escenario por hora: ahora más la anticipación mínima de la reserva por hora y un margen de seguridad, redondeado hacia arriba al próximo múltiplo de 30 minutos.'
            ),
            "build_plan_hora": (
                '💡 LA IDEA: Estructurar un escenario intensivo de reservas por hora para llevar una sede al límite de su aforo.\n\n'
                '🎯 POR QUE FUE GENERADA: Pone a prueba los mecanismos de rechazo por cupo agotado y la resistencia del sistema ante alta demanda.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma el plan del escenario por hora de hoy: valida que exista la sucursal a saturar (Morón), que tenga plazas y que haya usuarios Auto suficientes; llena la saturada hasta su tope en el turno base, reparte turnos escalonados de 5 autos en las sucursales normales (nunca superan su tope), asigna cada reserva al usuario Auto menos cargado que no tenga solape (tope de 5 reservas por usuario) y suma los intentos fantasma que exceden el tope para provocar el error de capacidad. Aborta si algún turno cae después del cierre de sucursales y devuelve el plan completo.'
            ),
            "_print_plan_hora": (
                '💡 LA IDEA: Mostrar en pantalla el esquema del ensayo de saturación por turnos horarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda visibilidad de los intentos exitosos y fallidos planificados para la prueba de estrés.\n\n'
                '⚙️ FUNCIONAMIENTO: Imprime el reporte del escenario por hora: hora base, sucursal a saturar, reservas reales y fantasmas por sucursal, reparto de reservas por usuario, franja del turno a saturar y horarios de los turnos de cada sucursal normal.'
            ),
            "create_and_pay": (
                '💡 LA IDEA: Crear en la base de datos cada reserva del plan y procesar su pago simulado.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida el ciclo completo de contratación y cobro sin requerir intervención en la pasarela de pagos real.\n\n'
                '⚙️ FUNCIONAMIENTO: Deshabilita el envío de correos de confirmación y recorre el plan: para cada entrada consulta si ya existe una reserva idéntica (la reutiliza y la cuenta como skip) o la crea con ReservationService.create_user_reservation; luego abona con ReservationPaymentsMixin.pay_reservation, acreditando en el saldo del usuario el monto si le falta. Cada error se registra con rollback para no dejar la corrida a medias, y devuelve contadores, fallos y la lista de reservas.'
            ),
            "simulate": (
                '💡 LA IDEA: Simular las entradas y salidas de los vehículos manipulando el reloj interno del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Recrea la experiencia temporal completa de ingresos, estadías y egresos en pocos segundos.\n\n'
                '⚙️ FUNCIONAMIENTO: Deshabilita barrera física y notificaciones y, moviendo el tiempo virtual con TimeService a cada evento, ejecuta los ingresos (inicio + 61 s) y egresos (fin) de las reservas aún no procesadas mediante AccessService.manual_entry/manual_exit, verificando que el log de acceso quede vinculado a la reserva y que la salida quede registrada y pagada. Ordena los eventos respetando salidas antes que entradas en el mismo instante, lleva el máximo de simultáneos por sucursal y tipo contra la capacidad, revierte la ocupación ante cada fallo y devuelve todo el reporte (restaurando el offset de tiempo al terminar).'
            ),
            "finalize": (
                '💡 LA IDEA: Avanzar el reloj virtual para consolidar todas las reservas como completadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Cierra el ciclo de vida de las reservas de prueba y restaura el desfase horario a la hora real.\n\n'
                '⚙️ FUNCIONAMIENTO: Mueve el tiempo virtual un día después de la reserva que termina más tarde y marca todas las reservas de la prueba como COMPLETADA (comprometido o no), dejando el desfase de tiempo en 0. Devuelve cuántas reservas actualizó.'
            ),
            "_limpiar": (
                '💡 LA IDEA: Revertir todas las reservas, pagos y registros de acceso creados durante una tanda de pruebas.\n\n'
                '🎯 POR QUE FUE GENERADA: Deja la base de datos en su estado original sin dejar rastros de datos temporales.\n\n'
                '⚙️ FUNCIONAMIENTO: Borra la tanda indicada usando su snapshot: elimina los AccessLog por ids, por reserva_id o por patente normalizada, borra las notificaciones y reservas de la tanda, restaura los saldos iniciales de los usuarios, pone a cero la ocupación de reservas de todas las sucursales, hace commit y elimina el archivo de snapshot.'
            ),
            "run": (
                '💡 LA IDEA: Ejecutar el flujo integral de prueba: planificación, creación, pago, simulación y finalización.\n\n'
                '🎯 POR QUE FUE GENERADA: Automatiza la verificación de extremo a extremo del módulo de reservas en una sola instrucción.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta el flujo completo en cuatro etapas: plan (aborta si no pudo ubicar todos los movimientos, sin escribir en la BD), crear y abonar con el tiempo virtual congelado antes de la ventana para que los workers no auto-finalicen nada, simular ingresos/estadía/egresos y finalizar. Imprime los reportes de estado, cobertura por sucursal y máximo simultáneo contra capacidad, y guarda el snapshot con reservas, ids de logs, saldos y cobertura.'
            ),
            "run_hora": (
                '💡 LA IDEA: Disparar la variante de prueba orientada a la saturación de cupos por hora.\n\n'
                '🎯 POR QUE FUE GENERADA: Evalúa que el sistema bloquee correctamente las reservas cuando una sede agota su capacidad en un turno determinado.\n\n'
                '⚙️ FUNCIONAMIENTO: Variante del flujo para el escenario por hora con saturación: plan por hora, creación y abonado con tiempo real, simulación y finalización. Informa creadas contra intentos por sucursal, agrupa los errores de capacidad ("plazas exclusivas") y guarda el snapshot de la tanda.'
            ),
            "main": (
                '💡 LA IDEA: Procesar las opciones de la línea de comandos para planificar, ejecutar o limpiar tandas de prueba.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee una interfaz flexible para que los desarrolladores pongan a prueba las reservas con diversos escenarios.\n\n'
                '⚙️ FUNCIONAMIENTO: Interpreta los argumentos (nombre, -n/--movimientos, --solo-plan, --limpiar y --hora-saturacion), valida el nombre y que la cantidad sea al menos 1, y ejecuta la etapa elegida; siempre cierra la sesión y restaura el desfase de tiempo al terminar, incluso ante errores.'
            ),
        },
    },
    "scripts/generate_test_plates.py": {
        "proposito": 'Genera static/test_plates.html, una hoja A4 imprimible con patentes de prueba de los formatos que soporta el sistema (Mercosur Argentina, moto y Brasil), para ensayar la cámara ALPR mostrando la patente en pantalla o imprimiéndola en papel.',
        "simbolos": {
            "generate": (
                '💡 LA IDEA: Crear una página web imprimible con ejemplos de patentes reglamentarias de Argentina y Brasil.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los técnicos imprimir o mostrar patentes en pantalla para calibrar el lente y la lectura del OCR de las cámaras.\n\n'
                '⚙️ FUNCIONAMIENTO: Escribe el HTML con las cinco patentes de prueba (constante HTML_CONTENT) en static/test_plates.html, relativo al directorio desde el que se ejecuta el script, y avisa la ruta creada.'
            ),
        },
    },
    "scripts/test_video.py": {
        "proposito": (
            "💡 LA IDEA: Es el chequeo técnico rápido de la cámara. Como encender los faros de un auto en el taller para verificar que la óptica funciona y el foco está alineado antes de sacarlo a la ruta, este archivo permite comprobar si la lente y la captura de video responden bien.\n\n"
            "🎯 POR QUE FUE GENERADA: Para que un técnico, instalador o evaluador pueda probar si la cámara web, el video de simulación o la transmisión de red RTSP funciona correctamente de forma aislada, sin tener que encender todo el sistema pesado de barreras ni levantar el servidor web principal.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Lee la variable de entorno VIDEO_SOURCE (por defecto '0', correspondiente a la cámara web integrada) y la convierte a número entero si es un dígito. 2. Inicializa la captura de video con OpenCV (cv2.VideoCapture) y hace una pausa de 1 segundo para que el hardware y el sensor de imagen se estabilicen. 3. Comprueba si el dispositivo abrió; si no abrió emite un aviso por consola y sale con código 2. 4. Intenta leer el primer cuadro (frame) de video; si la lectura inicial falla, realiza hasta 5 reintentos sucesivos para dar tiempo al autoenfoque y exposición. 5. Si captura el cuadro con éxito, registra su resolución en pantalla (ancho y alto), guarda una foto testigo en 'static/uploads/camera_test.jpg', libera el dispositivo de video y finaliza con código 0 (éxito). 6. Si tras los 5 intentos no logra capturar imagen, avisa la falla, libera el dispositivo y finaliza con código 3."
        ),
        "simbolos": {
        },
    },
}
