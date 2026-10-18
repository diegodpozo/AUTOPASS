"""Explicaciones analizadas de la sección arranque (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "main.py": {
        "proposito": 'Punto de entrada de la API: arma la aplicación FastAPI de AUTOPASS, monta los archivos estáticos y la PWA, aplica middlewares de compresión, CORS y seguridad, y engancha los eventos de arranque/apagado que levantan MQTT, el esquema de base de datos y los workers de fondo. Al final registra todos los routers de la API (`/v1/...`) y las vistas del frontend.',
        "simbolos": {
            "service_worker": (
                "💡 LA IDEA: Es el repartidor que le entrega al navegador el carnet del 'asistente offline' (el archivo `sw.js`). Se asegura de darle dos sellos indispensables: permiso para operar en todo el sitio web (`Service-Worker-Allowed: /`) y una orden para que el navegador nunca guarde una copia vieja vencida (`Cache-Control: no-cache`).\n\n"
                '🎯 POR QUE FUE GENERADA: Sin esta ruta configurada con esas cabeceras exactas, el navegador rechazaría registrar el Service Worker para todo el sistema AUTOPASS o se quedaría pegado ejecutando una versión vieja de la app sin actualizarse cuando cambiamos código.\n\n'
                '⚙️ FUNCIONAMIENTO: Ruta GET `/sw.js` que devuelve el archivo `static/sw.js` como JavaScript con dos cabeceras especiales: `Service-Worker-Allowed: /` (permite que el service worker controle todo el sitio, no solo su carpeta) y `Cache-Control: no-cache` (evita que el navegador retenga una versión vieja del worker). Sirve para habilitar el comportamiento offline de la PWA.'
            ),
            "manifest": (
                "💡 LA IDEA: Es como el documento de identidad de la aplicación en el celular o PC. Le entrega al navegador el archivo JSON que dice cómo se llama la app ('AUTOPASS'), qué colores usa y qué ícono poner en la pantalla de inicio al instalarla.\n\n"
                "🎯 POR QUE FUE GENERADA: Si no devolvemos este archivo con el tipo de contenido exacto (`application/manifest+json`), los celulares Android y navegadores de escritorio no muestran el botón 'Instalar aplicación' ni pueden funcionar como PWA.\n\n"
                '⚙️ FUNCIONAMIENTO: Ruta GET `/manifest.webmanifest` que devuelve el archivo `static/manifest.json` con el tipo MIME `application/manifest+json`, para que el navegador instale la PWA con nombre, íconos y colores definidos.'
            ),
            "no_cache_js": (
                "💡 LA IDEA: Es un guardia de aduana que le pega una etiqueta de 'vencimiento inmediato' a todos los archivos JavaScript del frontend (`Cache-Control: no-cache, must-revalidate`).\n\n"
                '🎯 POR QUE FUE GENERADA: Evita el clásico dolor de cabeza donde un programador sube una corrección al sistema pero los usuarios siguen viendo la pantalla rota porque su navegador guardó el JavaScript viejo en la memoria caché.\n\n'
                '⚙️ FUNCIONAMIENTO: Middleware HTTP que deja pasar la petición y luego, si la ruta empieza con `/static/js/`, agrega la cabecera `Cache-Control: no-cache, must-revalidate`. Así los scripts del frontend se revalidan siempre y los cambios de código se ven sin recargar caché.'
            ),
            "security_headers_middleware": (
                '💡 LA IDEA: Es el cinturón de seguridad y alarma antirrobo de cada respuesta HTTP. Le inyecta protecciones automáticas a cada página que sale del servidor para evitar que piratas informáticos nos metan trampas (bloquea que incrusten AUTOPASS en marcos invisibles con `X-Frame-Options: DENY`, prohíbe que el navegador adivine tipos de archivo y exige conexiones seguras HTTPS).\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la privacidad de los usuarios contra ataques de clickjacking, robo de credenciales y asegura que las conexiones viajen encriptadas en entornos de producción.\n\n'
                '⚙️ FUNCIONAMIENTO: Middleware HTTP que aplica cabeceras de seguridad a toda respuesta: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy` y una Content-Security-Policy construida a partir de las constantes CSP del archivo (permite CDNs, fuentes de Google y APIs de mapas concretas). Además, si la petición llegó por HTTPS (por `url.scheme` o por el header `x-forwarded-proto`), agrega HSTS con un año de vigencia y subdominios.'
            ),
            "startup_event": (
                '💡 LA IDEA: Es la lista de tareas del encargado que abre el negocio a la mañana: conecta la antena MQTT para escuchar a las barreras, verifica que todas las tablas de la base de datos existan y pone a rodar a los empleados en segundo plano (workers) que limpian reservas vencidas y mandan notificaciones.\n\n'
                '🎯 POR QUE FUE GENERADA: Si no existiera este evento central de arranque, el servidor web respondería páginas pero el sistema de barreras estaría sordo, la base de datos podría estar incompleta y nadie cancelaría las reservas abandonadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Se ejecuta al arrancar el servidor. Registra el event loop en NotificationService, conecta el cliente MQTT en modo asíncrono y arranca su loop, y luego sincroniza el esquema de base de datos con `sync_schema()` (con try/except propio para no frenar el arranque si falla). Por último lanza los workers de fondo: limpieza de reservas y envío de notificaciones. Cualquier fallo general se registra en el log sin abortar el proceso.'
            ),
            "shutdown_event": (
                '💡 LA IDEA: Es el encargado cerrando el local de noche: apaga las cámaras de seguridad ordenadamente, desconecta el cliente MQTT para no dejar canales colgados y le avisa al motor de base de datos que libere todas las conexiones abiertas.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita dejar procesos zombies comiendo memoria en el servidor, puertos de red trabados o conexiones fantasmas en la base de datos que bloqueen el próximo inicio.\n\n'
                '⚙️ FUNCIONAMIENTO: Se ejecuta al apagar el servidor. Registra el apagado en el log, detiene todas las cámaras con `stop_all_cameras()`, y en bloques try/except independientes detiene y desconecta el cliente MQTT y libera el engine de SQLAlchemy con `dispose()`. Los errores de limpieza solo se registran en nivel debug.'
            ),
        },
    },
    "init_db.py": {
        "proposito": 'Script de línea de comandos para preparar la base de datos desde cero: crea/sincroniza las tablas y luego carga los datos iniciales (seeds). Se usa al instalar el sistema o al recrear el entorno de pruebas.',
        "simbolos": {
            "create_tables": (
                '💡 LA IDEA: Es el maestro mayor de obras que revisa el terreno y levanta todas las paredes estructurales del edificio. Llama a `sync_schema()` para crear cualquier tabla faltante y dejar Alembic en la versión más reciente.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que con un solo comando de consola (`python init_db.py`) una computadora recién instalada cree todas las tablas vacías necesarias sin tener que ejecutar scripts SQL a mano.\n\n'
                '⚙️ FUNCIONAMIENTO: Importa los modelos y llama a `sync_schema()`, el flujo único de esquema que crea con SQLAlchemy las tablas faltantes y lleva Alembic al head. No devuelve nada; su efecto es dejar el esquema de la base de datos listo.'
            ),
            "seed_data": (
                '💡 LA IDEA: Es el decorador que amuebla la casa vacía. Abre la base de datos e inserta los datos esenciales para arrancar: el administrador por defecto, la sucursal de prueba y las tarifas iniciales.\n\n'
                '🎯 POR QUE FUE GENERADA: Sin datos semilla, un sistema recién instalado estaría completamente en blanco: nadie podría iniciar sesión (no habría usuario admin) ni registrar estadías (no habría playas ni tarifas configuradas).\n\n'
                '⚙️ FUNCIONAMIENTO: Abre una sesión con SessionLocal y llama a `seed_initial_data(db)` (el orquestador modular de seeds). Si ocurre cualquier excepción hace rollback y la registra por consola; pase lo que pase cierra la sesión en el `finally` para no dejar conexiones colgadas.'
            ),
        },
    },
    "alpr_service.py": {
        "proposito": (
            "💡 LA IDEA: Es la 'llave de contacto' del sistema de cámaras. Si imaginás a AUTOPASS como un camión con acoplado, el servidor web FastAPI es la cabina y el motor de cámaras ALPR es el acoplado. Este archivo es el botón de encendido que pone en marcha el motor de las cámaras en un proceso independiente sin frenar ni sobrecargar la página web.\n\n"
            "🎯 POR QUE FUE GENERADA: El reconocimiento óptico de patentes por redes neuronales (OCR) consume mucha memoria y procesador de la máquina. Si corriera adentro del mismo proceso del servidor web de FastAPI, cada vez que una cámara procesa una patente pesada, la página web de los clientes se pondría lenta o se congelaría. Al aislarlo en su propio ejecutable, el servicio de cámaras corre como un programa satélite independiente.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Verifica si fue ejecutado directamente desde la terminal (`if __name__ == '__main__'`). 2. Importa e invoca a `run_alpr_service()` desde `alpr.runner`, iniciando el bucle infinito de captura de cuadros, detección de movimiento y lectura OCR. 3. Atrapa la señal de interrupción del teclado (`KeyboardInterrupt` / Ctrl + C) con un bloque try/except, permitiendo que el operador cierre el programa de forma limpia y ordenada sin generar pantallas de error en la consola."
        ),
        "simbolos": {
        },
    },
    "locustfile.py": {
        "proposito": 'Archivo de pruebas de carga para Locust: simula usuarios concurrentes que inician sesión repetidamente contra la API para medir su comportamiento bajo estrés. Es una herramienta de test, no forma parte del sistema en ejecución.',
        "simbolos": {
            "AuthUser": (
                "💡 LA IDEA: Es un 'robot de pruebas' que imita el comportamiento de un cliente de carne y hueso: lee una lista de usuarios de prueba desde un archivo CSV y espera entre 2 y 3 segundos entre cada acción que realiza en la web.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite simular cientos de usuarios reales usando el sistema al mismo tiempo para medir cuánta carga soporta el servidor antes de saturarse.\n\n'
                "⚙️ FUNCIONAMIENTO: Clase de usuario Locust (hereda de HttpUser) con un tiempo de espera aleatorio de 2 a 3 segundos entre peticiones. Al importar el módulo, fuera de la clase, se lee `usuarios_demo.csv` y se arma la lista global `USERS` con email y la contraseña fija 'Demo1234!'; si el archivo no existe o falla la lectura, la lista queda vacía y el test no hace nada."
            ),
            "login": (
                '💡 LA IDEA: Es la acción concreta del robot: elige un usuario de la lista al azar y manda sus credenciales para iniciar sesión en la API, anotando en una planilla cuánto tardó el servidor en responder.\n\n'
                '🎯 POR QUE FUE GENERADA: Mide la velocidad y estabilidad del punto más crítico del sistema (el inicio de sesión) bajo estrés masivo.\n\n'
                "⚙️ FUNCIONAMIENTO: Tarea de Locust (peso 1) que representa al usuario: si la lista USERS está vacía retorna sin hacer nada; si no, elige un usuario al azar y hace un POST a `/v1/auth/login` con email y contraseña, agrupando todas las peticiones bajo el nombre 'login' en las métricas."
            ),
        },
    },
    "alembic/env.py": {
        "proposito": 'Entorno de ejecución de Alembic, la herramienta de migraciones de esquema. Agrega la raíz del proyecto al path, toma la URL de base de datos de la configuración (`settings.DATABASE_URL`, normalizada) y los metadatos de los modelos, y decide si corre las migraciones en modo offline o online. Es el puente entre los modelos SQLAlchemy y la base de datos al migrar.',
        "simbolos": {
            "run_migrations_offline": (
                "💡 LA IDEA: Es el 'modo plano de papel'. No se conecta a la base de datos real: calcula los cambios en el código de las tablas y redacta un script de texto con todas las órdenes SQL listas para auditoría o revisión manual.\n\n"
                "🎯 POR QUE FUE GENERADA: Resuelve el problema de bases de datos restringidas donde los administradores exigen ver primero el script SQL impreso antes de autorizar cambios, o para entornos sin acceso de red directo.\n\n"
                "⚙️ FUNCIONAMIENTO: Modo offline. La app NUNCA la ejecuta al abrirse (no existe como opción en la web). Solo se activa manualmente desde la terminal cuando el desarrollador escribe `alembic upgrade head --sql`. Configura el contexto sin abrir conexiones (`literal_binds=True`, `render_as_batch=True` para SQLite) y vuelca el código SQL por consola o archivo sin tocar la base viva."
            ),
            "run_migrations_online": (
                "💡 LA IDEA: Es el 'modo albañil en vivo'. Abre una conexión real contra la base de datos y ejecuta directamente una por una las reformas en las tablas hasta dejar el esquema al día.\n\n"
                "🎯 POR QUE FUE GENERADA: Automatiza la evolución de la base de datos en desarrollo y pruebas, evitando tener que correr scripts manuales cada vez que un modelo agrega o modifica un campo.\n\n"
                "⚙️ FUNCIONAMIENTO: Modo online. Es la función que SIEMPRE se usa al abrir la app: el backend la invoca automáticamente al iniciar (`core/database.py`) para asegurar que las tablas existan. También se ejecuta si corrés `alembic upgrade head` en la terminal sin banderas. Crea el motor, abre la conexión activa, aplica las reformas dentro de una transacción y actualiza la versión de la base."
            ),
        },
    },
    "static/offline.html": {
        "proposito": (
            "💡 LA IDEA: Es el 'letrero de cerrado por corte de luz'. Cuando el usuario entra a la app pero no tiene conexión a internet o el servidor de AUTOPASS está apagado, en vez de que el navegador muestre la pantalla en blanco con el tiranosaurio rex de Chrome, se muestra esta pantalla elegante con el logo de la empresa.\n\n"
            "🎯 POR QUE FUE GENERADA: Proporciona una experiencia de usuario profesional en Progressive Web Apps (PWA), informando con claridad qué ocurre y ofreciendo un botón para reintentar la conexión sin perder la estética del sistema.\n\n"
            "⚙️ FUNCIONAMIENTO: Documento HTML autocontenido con estilos CSS embebidos (no depende de ningún archivo externo). Muestra el logo dorado de AUTOPASS, el mensaje de advertencia indicando que el servidor de estacionamiento no está accesible en este momento, y un botón de reintento que ejecuta `window.location.reload()` para volver a cargar la aplicación cuando regrese la señal."
        ),
        "simbolos": {
        },
    },
    "static/test_plates.html": {
        "proposito": (
            "💡 LA IDEA: Es la 'hoja de tiro al blanco' para calibrar las cámaras. En lugar de tener que salir a la calle o manejar un auto real frente a la lente para ver si el sistema lee bien, este archivo genera en pantalla o imprime en papel 5 patentes de prueba realistas.\n\n"
            "🎯 POR QUE FUE GENERADA: Facilita las pruebas de laboratorio, desarrollo y demostraciones académicas sin depender de vehículos físicos reales, permitiendo validar si el reconocimiento óptico distingue correctamente formatos de Argentina, motos y países vecinos.\n\n"
            "⚙️ FUNCIONAMIENTO: Página web de prueba con estilos CSS específicos para pantalla e impresión A4 (`@media print`). Renderiza tipografías y proporciones oficiales de matrículas: Mercosur Argentina (`AB123CD`), clásica antigua (`ABC123`), moto Mercosur (`A123BCD`), moto clásica (`123ABC`) y patente de Brasil (`ABC1D23`). Cuenta con un botón para imprimir las placas en tamaño real para colocarlas frente a la cámara web."
        ),
        "simbolos": {
        },
    },
}
