"""Explicaciones analizadas del frontend-núcleo (análisis del código real).

Cubre los 9 archivos JavaScript del núcleo: puentes de compatibilidad global
(api_client.js, auth.js, main.js) y los módulos bajo static/js/modules/
(api, auth, reset-password, theme, ui, utils). Se redacta tras leer el código
completo de cada archivo y explica propósito de cada uno y qué hace cada
símbolo detectado (funciones, valor exportado). Algunos archivos no exponen
símbolos de nivel superior en el inventario: igual se documenta su propósito.
"""

ANALISIS: dict[str, dict] = {
    "static/js/api_client.js": {
        "proposito": (
            "💡 LA IDEA: Es el puente de compatibilidad o 'adaptador de enchufe' para scripts del navegador. Permite que el código que todavía no fue modernizado siga comunicándose con el servidor a través del cliente nuevo sin romperse.\n\n"
            "🎯 POR QUE FUE GENERADA: Durante la transición de la aplicación desde scripts JavaScript tradicionales hacia módulos modernos (ES Modules), existían pantallas y funciones antiguas que buscaban variables globales llamadas `window.apiClient` y `window.API_BASE`. En lugar de tener que reescribir cada página de golpe, este archivo conecta la arquitectura moderna con el código legado.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Importa el cliente HTTP moderno centralizado (`api`) desde el módulo `./modules/api.js`. 2. Lo expone en el ámbito global del navegador asignando `window.apiClient = api`. 3. Define la constante `window.API_BASE = '/v1'` como salvaguarda para cualquier script que construya rutas de red directamente. De esta manera, cualquier pantalla del sistema puede continuar realizando peticiones asíncronas con token y control de errores uniforme."
        ),
        "simbolos": {
        },
    },
    "static/js/auth.js": {
        "proposito": (
            "💡 LA IDEA: Es el recepcionista y coordinador de la pantalla de acceso. Se encarga de atender al usuario cuando interactúa con los botones de 'Iniciar Sesión', 'Registrarme', 'Olvidé mi contraseña' o 'Continuar con Google/Microsoft'.\n\n"
            "🎯 POR QUE FUE GENERADA: Los formularios web necesitan escuchar los eventos del usuario (como presionar Enter o hacer clic en enviar), validar datos antes de enviarlos a la red y responder prolijamente ante éxitos o rechazos sin recargar la página ni congelar la pantalla.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Importa la lógica de autenticación desde `./modules/auth.js`. 2. Expone en `window` las funciones `initPasswordValidation` (el medidor visual interactivo de fortaleza de clave) y `startOAuth` (el enlace para iniciar sesión con redes sociales). 3. Al cargarse el árbol de la página (`DOMContentLoaded`), enlaza los formularios de inicio de sesión (`loginForm`), registro de cuenta (`registerForm`), recuperación de contraseña (`recoveryForm`) y registro asistido por redes (`oauthSignupForm`) con sus respectivos controladores de envío. 4. Consulta al servidor qué redes sociales están habilitadas (`loadOAuthProviders`) y procesa el retorno de autorización de Google o Microsoft (`processOAuthCallback`). 5. En el evento `pageshow` (cuando el usuario vuelve atrás en el historial del navegador), reactiva los botones de envío y restaura sus leyendas originales para evitar bloqueos por la memoria caché (BFCache)."
        ),
        "simbolos": {
        },
    },
    "static/js/main.js": {
        "proposito": (
            "💡 LA IDEA: Es la caja de herramientas y el conserje global del sitio web. Provee todas las funciones comunes que necesita cualquier página: mostrar carteles flotantes de aviso (toasts), formatear monedas y fechas, abrir o cerrar ventanas modales y sincronizar los menús según si el usuario está conectado o no.\n\n"
            "🎯 POR QUE FUE GENERADA: En el diseño HTML tradicional muchas etiquetas usan eventos directos como `onclick=\"openModal('miModal')\"`. Para que esos botones respondan desde cualquier parte del sistema sin importar qué página se esté visitando, hace falta un archivo central que publique todas las utilidades esenciales en el objeto global `window`.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Importa funciones de formateo y mensajes desde `./modules/utils.js` (como `showToast`, `showConfirm`, `formatDate`, `formatNum`) y controladores visuales de `./modules/ui.js` (como `openModal`, `closeModal`, `toggleSidebar`, `logout`), registrándolos en `window`. 2. Define la función `window.updateAuthNav()` que inspecciona si hay un token de sesión en el almacenamiento local (`localStorage.token`); si el usuario inició sesión, oculta los botones de login/registro, muestra su botón de perfil (apuntando a `/dashboard` si es administrador o a `/perfil` si es conductor) y activa la opción de cerrar sesión. 3. Al completarse la carga de la página (`DOMContentLoaded`), sincroniza la botonera de navegación y restaura la barra lateral contraída si el usuario la había colapsado previamente. 4. En el evento `pageshow`, desbloquea botones de envío y cierra modales de ingreso pendientes si ya se detecta una sesión activa."
        ),
        "simbolos": {
        },
    },
    "static/js/modules/api.js": {
        "proposito": (
            "💡 LA IDEA: Es el mensajero oficial de AUTOPASS. Es el encargado exclusivo de viajar por Internet de ida y vuelta entre la pantalla que ve el usuario en su navegador y el servidor backend donde se procesan los datos y la base de datos.\n\n"
            "🎯 POR QUE FUE GENERADA: Si cada pantalla o botón hiciera sus propios pedidos a la red por separado, el código estaría lleno de repeticiones, sería muy fácil olvidar adjuntar el pase de seguridad (token JWT), no se sabría con exactitud cuándo caducó la sesión y cada error se mostraría de forma despareja. Este módulo concentra todas las comunicaciones en un único canal seguro, consistente y blindado.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Provee métodos directos para cada verbo de comunicación HTTP: `get()`, `post()`, `put()`, `patch()` y `delete()`, que delegan en una función maestra asíncrona `request()`. 2. En consultas `get`, convierte los filtros recibidos en parámetros de URL limpios (`?clave=valor`), omitiendo valores vacíos o nulos. 3. Antes de despachar cada paquete, busca el token de acceso en el almacenamiento local (`localStorage.getItem('token')`) y lo adjunta en la cabecera `Authorization: Bearer <token>`, agregando además `Content-Type: application/json` para envíos de datos que no sean archivos binarios (`FormData`). 4. Si el servidor responde con código 401 (sesión expirada), preserva únicamente la identidad del equipo y flags de tutoriales, borra la sesión vencida de la memoria y redirige automáticamente a la portada para solicitar un nuevo ingreso. 5. Si la respuesta es exitosa (código 204 sin contenido o código 200 con JSON), devuelve `{ ok: true, data }`. Si ocurre una falla (códigos 400, 422 o 500), desglosa el mensaje de error devuelto por FastAPI y retorna `{ ok: false, status, error }` para que la pantalla le informe con claridad al usuario."
        ),
        "simbolos": {
        },
    },
    "static/js/modules/auth.js": {
        "proposito": 'Módulo de autenticación: lógica de login, registro, recuperación y OAuth2. Reutiliza validación de contraseña (evaluatePassword), inicializa checklist de requisitos (initPasswordValidation), genera/recupera device_id (getDeviceId), gestiona tokens, rol, nombre/apellido, sucursal en localStorage, redirección por rol (staff/admin/local_admin -> /dashboard, resto -> /perfil) y flujo completo de OAuth (inicio, listado de providers, callback con hash #oauth, prefill y finalización de signup).',
        "simbolos": {
            "evaluatePassword": (
                '💡 LA IDEA: Es el examinador de seguridad de contraseñas: chequea si tiene 8 caracteres, mayúsculas, símbolos especiales y si coincide con la confirmación.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que los usuarios utilicen claves débiles o fáciles de adivinar, protegiendo sus cuentas y autos desde el primer instante.\n\n'
                '⚙️ FUNCIONAMIENTO: Evalúa requisitos de seguridad de una contraseña: longitud >= 8, presencia de mayúscula [A-Z], carácter especial [!@#$%^&*(),.?":{}|<>] y coincidencia con confirmValue. Devuelve {isLen,isUp,isSpec,isMatch,valid} donde valid = todos verdaderos.'
            ),
            "initPasswordValidation": (
                '💡 LA IDEA: Es el semáforo interactivo que pinta tildes verdes y cambia de color a medida que el usuario va escribiendo su clave.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda retroalimentación visual inmediata al usuario para que sepa con exactitud qué requisito le falta cumplir antes de apretar el botón de enviar.\n\n'
                "⚙️ FUNCIONAMIENTO: Inicializa validación en vivo sobre campos passId/confirmId. Actualiza íconos de requisitos (reqLen/reqUp/reqSpec/reqMatch) y medidor strengthMeter según evaluatePassword. Agrega listeners input a contraseña y confirmación; actualiza clases 'satisfied' y cambia íconos entre far fa-circle / fas fa-check-circle. El medidor aplica strength-weak/medium/strong según cantidad de requisitos cumplidos (1-3) cuando hay texto."
            ),
            "getDeviceId": (
                '💡 LA IDEA: Es la huella digital anónima de la computadora o teléfono desde donde se conecta el usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite reconocer si el conductor está iniciando sesión desde un equipo habitual o alertarlo si alguien entró desde un dispositivo desconocido.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve identificador de dispositivo persistido en localStorage 'autopass_device_id'. Si no existe, genera 'dev-' + string aleatorio + '-' + timestamp base36 y lo guarda. Usado en login para enviar device_id al backend."
            ),
            "handleLogin": (
                '💡 LA IDEA: Es el portero del formulario de inicio de sesión: toma las credenciales, consulta con el servidor y abre el panel que le corresponde según su rol.\n\n'
                '🎯 POR QUE FUE GENERADA: Controla todo el ciclo de ingreso, mostrando rueditas de carga, atrapando errores y guardando los pases de acceso en el navegador.\n\n'
                "⚙️ FUNCIONAMIENTO: Handler de submit del formulario de login. Previene envío, deshabilita botón con spinner 'Ingresando...', lee email/password, llama api.post('/auth/login',{email,password,device_id}). Si ok: guarda token, rol, nombre (toTitle), apellido (toTitle), sucursal en localStorage; restaura botón; cierra loginModal; si data.nuevo_dispositivo guarda flag sessionStorage 'autopass_device_alert'; redirige según rol (staff/admin/local_admin -> /dashboard, resto -> /perfil). Si error: muestra mensaje en #login-error y restaura botón."
            ),
            "handleRegister": (
                '💡 LA IDEA: Es la ficha de suscripción que valida DNI, teléfono, correo y contraseña antes de dar de alta a un nuevo cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene el envío de datos incompletos o mal formateados al servidor, guiando al usuario con mensajes claros.\n\n'
                "⚙️ FUNCIONAMIENTO: Handler de registro. Valida DNI 7-8 dígitos, email válido (regex), teléfono 10-13 dígitos, coincidencia de contraseñas y evaluatePassword().valid. Construye payload {nombre,apellido,dni,telefono,email,password}, deshabilita botón 'Procesando...', envía api.post('/auth/register', payload). Si ok: showToast de éxito y cambia modal a login tras 1500ms. Si falla: muestra error y restaura botón."
            ),
            "handleRecovery": (
                "💡 LA IDEA: Es el botón de auxilio del formulario de 'Olvidé mi contraseña', que solicita al servidor el envío del correo de rescate.\n\n"
                '🎯 POR QUE FUE GENERADA: Otorga una respuesta visual prolija al usuario para que sepa que el mensaje fue despachado y revise su bandeja de entrada.\n\n'
                "⚙️ FUNCIONAMIENTO: Handler de recuperación de contraseña (forgot-password). Deshabilita botón con spinner 'Enviando...', oculta mensajes previos, llama api.post('/auth/forgot-password',{email}). Si ok: muestra #recovery-success con mensaje del backend y resetea formulario. Si error o excepción: muestra mensaje en #recovery-error. Siempre restaura botón en finally."
            ),
            "startOAuth": (
                '💡 LA IDEA: Es la catapulta que envía al usuario directamente a la pantalla de login de Google o GitHub.\n\n'
                '🎯 POR QUE FUE GENERADA: Inicia la identificación social con un solo clic evitando pasos intermedios engorrosos.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicia flujo OAuth redirigiendo a `/v1/auth/oauth/${provider}/authorize` (navegación completa del navegador).'
            ),
            "loadOAuthProviders": (
                "💡 LA IDEA: Es el decorador que prende los botones de 'Continuar con Google' o 'GitHub' únicamente si la empresa los tiene habilitados.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita mostrar opciones de ingreso social que darían error si el administrador todavía no cargó las claves de esa plataforma.\n\n'
                "⚙️ FUNCIONAMIENTO: Carga providers habilitados vía api.get('/auth/oauth/providers'). Si ok, mapea data.providers a ids y muestra/oculta botones .oauth-btn por data-oauth-provider y bloques .oauth-block si alguno visible. No hace nada si falla la petición."
            ),
            "processOAuthCallback": (
                '💡 LA IDEA: Es el comité de bienvenida que recibe al usuario cuando vuelve de identificarse en Google o GitHub y decide qué pantalla mostrarle.\n\n'
                '🎯 POR QUE FUE GENERADA: Lee el resultado de la red social, guarda las credenciales en el navegador o abre la ventanita para completar el DNI y teléfono si es su primera vez.\n\n'
                '⚙️ FUNCIONAMIENTO: Procesa fragmento hash #oauth en URL. Lee params: si existe oauth_token -> limpia hash, guarda token, rol, nombre/apellido (toTitle) en localStorage y redirige por rol (staff/admin/local_admin -> /dashboard, resto -> /perfil). Si existe oauth_signup -> limpia hash, arma data {email,provider,nombre,apellido} y llama prefillOAuthSignup(signupCode,data). Si existe oauth_error -> limpia hash y muestra showToast con mensaje traducido según código (denegado/state_invalido/sin_codigo/bloqueado) o genérico.'
            ),
            "prefillOAuthSignup": (
                '💡 LA IDEA: Es el autocompletado del formulario para usuarios nuevos que vinieron de Google, rellenando su nombre y correo automáticamente.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra tiempo al conductor nuevo para que solo tenga que ingresar su documento y teléfono para empezar a usar el estacionamiento.\n\n'
                "⚙️ FUNCIONAMIENTO: Prepara formulario de registro OAuth intermedio: guarda pendingOAuthCode = code, setea etiquetas/valores (provider, email, nombre, apellido), limpia dni/teléfono y error, oculta error y abre 'oauthSignupModal'."
            ),
            "handleOAuthComplete": (
                '💡 LA IDEA: Es el apretón de manos final que guarda el DNI y teléfono del cliente social y lo deja listo para operar en su perfil.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que todas las cuentas sociales cuenten con los datos mínimos obligatorios para emitir comprobantes legales de estacionamiento.\n\n'
                "⚙️ FUNCIONAMIENTO: Completa registro OAuth: valida DNI 7-8 y teléfono 10-13, exige pendingOAuthCode. Deshabilita botón con spinner 'Finalizando...', llama api.post('/auth/oauth/complete',{code:pendingOAuthCode,dni,telefono}). Si ok: guarda token, rol, nombre, apellido, sucursal, limpia pendingOAuthCode, cierra modal y redirige a /perfil. Si falla: limpia pendingOAuthCode, muestra error y restaura botón."
            ),
        },
    },
    "static/js/modules/reset-password.js": {
        "proposito": "Módulo de formulario para restablecer contraseña (recuperación o activación/invitación por Admin General). Reutiliza evaluatePassword e initPasswordValidation desde auth.js para validación en vivo de requisitos. Lee token desde URL (search params), detecta propósito 'activation' decodificando JWT (payload.purpose) para adaptar subtítulo a bienvenida; si no hay token deshabilita formulario. Valida nueva contraseña antes de enviar y llama api.post('/auth/reset-password',{token,new_password}) mostrando panel de éxito o error según respuesta.",
        "simbolos": {
            "leerProposito": (
                '💡 LA IDEA: Es la lupa que examina el enlace recibido por correo para saber si la persona viene a recuperar una clave olvidada o a estrenar una cuenta invitada.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que la pantalla adapte su título y textos (dando la bienvenida a un nuevo empleado o asistiendo en el recupero de clave).\n\n'
                '⚙️ FUNCIONAMIENTO: Lee propósito del token JWT (recuperación vs activación/invitación). Intenta decodificar payload (base64url) y devuelve payload.purpose; en caso de error devuelve null.'
            ),
        },
    },
    "static/js/modules/theme.js": {
        "proposito": 'Paleta de tokens de diseño (export const THEME) usada por estilos/temas del frontend (colores dorados, fondos, textos, estados, tipografía mono, grid). Provee valores coherentes para reutilizar en JS/CSS dinámico.',
        "simbolos": {
            "THEME": (
                '💡 LA IDEA: Es la paleta de pinturas oficial del diseño de la aplicación, donde están definidos los tonos dorados, fondos oscuros y colores de alerta.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita escribir códigos de color de memoria por todo el código, asegurando que todos los gráficos y componentes luzcan idénticos y elegantes.\n\n'
                '⚙️ FUNCIONAMIENTO: Objeto con tokens de tema: gold, goldDark, goldHover, goldGlow, goldBorder, goldSoft, bgCard, bgInput, bgSoft, textPrimary, textSecondary, textMuted, success, danger, warning, info, accent, monoFont, grid, pointDark.'
            ),
        },
    },
    "static/js/modules/ui.js": {
        "proposito": 'Módulo de UI para gestión de diálogos/modales, foco accesible (trap focus), cierre con Escape, toggle de contraseña, sidebar (desktop/móvil) y toggles de secciones. Unifica apertura/cierre de contenedores con SELECTOR_DIALOGO (.modal, .modal-premium, .onboarding-overlay-premium), distingue display flex/block por CLASES_FLEX, mantiene mapa de disparadores para devolver foco, implementa encierro de foco (Tab/Shift+Tab) y delega cierre del diálogo de arriba al control interno (data-modal-close/.close-btn/.modal-close-top) para que showConfirm/showChoice/onboarding ejecuten su lógica propia.',
        "simbolos": {
            "visible": (
                '💡 LA IDEA: Es el sensor de visibilidad que chequea si un elemento está realmente a la vista en la pantalla o si está oculto.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita intentar interactuar o poner el foco del teclado en ventanas o botones que están escondidos.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve true si el elemento tiene getComputedStyle(el).display !== 'none'."
            ),
            "dialogoDeArriba": (
                '💡 LA IDEA: Es la vista telescópica que identifica cuál de todas las ventanas flotantes abiertas es la que está más al frente.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que al presionar la tecla Escape se cierre únicamente la ventana que el usuario está viendo arriba de todo, sin cerrar las de abajo.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el diálogo visible con mayor z-index entre SELECTOR_DIALOGO; en empate usa el último en DOM. Retorna null si no hay abiertos.'
            ),
            "focables": (
                '💡 LA IDEA: Es el rastreador de botones y campos interactivos dentro de una ventana para personas que navegan con teclado o lectores de pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Esencial para la accesibilidad web, permitiendo que la tecla Tabulador recorra solo los elementos que se pueden cliquear.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve lista de elementos focusables dentro de raiz (SELECTOR_FOCABLE) que son visibles (getClientRects().length>0).'
            ),
            "controlDeCierre": (
                "💡 LA IDEA: Es el localizador de la cruz o botón de 'Cancelar' dentro de cualquier ventana flotante.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite cerrar diálogos de forma limpia y consistente independientemente de cómo se llame el botón de salir en cada ventana.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca control interno para cerrar el diálogo: [data-modal-close] o .close-btn o .modal-close-top. Devuelve el elemento o null.'
            ),
            "devolverFoco": (
                '💡 LA IDEA: Es el marcador de memoria que recuerda qué botón habías tocado antes de que se abriera la ventana emergente y te devuelve allí al cerrarla.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el usuario con teclado o lector de pantalla quede desorientado y perdido en el inicio de la página al cerrar un modal.\n\n'
                '⚙️ FUNCIONAMIENTO: Recupera disparador guardado para id, lo elimina del mapa, y si existe, está en documento y visible, llama .focus() sobre él.'
            ),
            "openModal": (
                '💡 LA IDEA: Es la orden de apertura de cualquier ventana emergente, iluminando el contenido y posicionando el cursor en el primer campo a rellenar.\n\n'
                '🎯 POR QUE FUE GENERADA: Unifica la apertura de modales, restaura botones bloqueados y facilita que el usuario empiece a escribir sin tener que hacer clic en el formulario.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre modal por id: guarda disparador (elemento activo visible fuera del modal) en disparadores si corresponde; setea display flex o block según CLASES_FLEX; restaura botón submit (disabled false, recupera data.originalHtml o texto por defecto según id login/register); busca primer campo editable visible (input/select/textarea) para autofocus con timeout 100ms (si ninguno, enfoca propio modal con tabindex=-1).'
            ),
            "closeModal": (
                '💡 LA IDEA: Es el cierre ordenado de una ventana emergente, limpiando mensajes de error y devolviendo el foco donde estaba.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpia la pantalla y previene que errores viejos vuelvan a aparecer si el usuario reabre la misma ventana.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra modal id (display='none'), oculta todos .error-msg y llama devolverFoco(id)."
            ),
            "cerrarDialogoDeArriba": (
                '💡 LA IDEA: Es el reflejo de la tecla Escape: busca la ventana que está al frente y simula un clic en su botón de cancelar o cerrar.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee una experiencia de usuario natural donde presionar Escape siempre cancela y cierra lo que está enfrente.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra diálogo de arriba activando su controlDeCierre (dispara .click()) para que corra lógica propia; si sigue visible tras click, lo oculta forzadamente; luego devuelve foco.'
            ),
            "switchModal": (
                "💡 LA IDEA: Es el pase de magia que cierra una ventana y abre otra de inmediato (por ejemplo, pasar de 'Iniciar Sesión' a 'Registrarse').\n\n"
                '🎯 POR QUE FUE GENERADA: Hace las transiciones entre modales fluidas sin parpadeos molestos en la pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Intercambia modales: closeModal(oldId) y openModal(newId).'
            ),
            "togglePasswordVisibility": (
                '💡 LA IDEA: Es el ojito al lado del campo de contraseña para mostrar u ocultar los puntitos de la clave.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al usuario verificar si tipeó bien su contraseña antes de enviar el formulario, cuidando además la accesibilidad para no videntes.\n\n'
                "⚙️ FUNCIONAMIENTO: Alterna tipo password/text del inputId según estado actual. Actualiza ícono del trigger (button o i): pasa fa-eye <-> fa-eye-slash. Si trigger tiene aria-pressed, actualiza aria-pressed y aria-label ('Mostrar contraseña'/'Ocultar contraseña')."
            ),
            "toggleSidebar": (
                '💡 LA IDEA: Es la palanca para encoger o agrandar el menú lateral de la computadora para ganar más espacio en el tablero.\n\n'
                '🎯 POR QUE FUE GENERADA: Recuerda la preferencia del operador en su navegador para que no tenga que volver a achicar el menú cada vez que cambia de página.\n\n'
                "⚙️ FUNCIONAMIENTO: Colapsa/expande sidebar desktop: alterna clases 'collapsed' en .layout-with-sidebar y .sidebar, cambia ícono .sidebar-toggle i entre fa-chevron-left/right, guarda estado en localStorage('sidebarCollapsed')."
            ),
            "toggleMobileNav": (
                '💡 LA IDEA: Es el menú hamburguesa del celular que despliega las opciones de navegación sobre la pantalla táctil.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite navegar cómodamente en teléfonos bloqueando el desplazamiento del fondo mientras el menú está desplegado.\n\n'
                "⚙️ FUNCIONAMIENTO: Abre/cierra sidebar móvil: alterna clase 'mobile-open' en #main-sidebar o .sidebar, activa/desactiva overlay #sidebar-overlay, controla body.style.overflow (hidden cuando abierto)."
            ),
            "closeMobileNav": (
                '💡 LA IDEA: Es el repliegue del menú del celular al tocar fuera de él o al elegir una opción.\n\n'
                '🎯 POR QUE FUE GENERADA: Devuelve la pantalla del teléfono a su estado habitual permitiendo volver a desplazarse por el contenido.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra sidebar móvil: quita 'mobile-open', desactiva overlay, restaura overflow body."
            ),
            "toggleNuevoVinculo": (
                '💡 LA IDEA: Es el acordeón desplegable que muestra u oculta el formulario para asociar un nuevo vehículo en la cuenta.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene compacta la pantalla del perfil de usuario, mostrando el formulario de alta solo cuando se lo necesita.\n\n'
                '⚙️ FUNCIONAMIENTO: Alterna sección #vinculo-container (.open), trigger .register-trigger-card (.open) y rota flecha #vinculo-arrow según ancho (270°/90° móvil, 180°/0° desktop).'
            ),
            "toggleHistorial": (
                '💡 LA IDEA: Es el fuelle que abre o cierra la lista completa de estadías pasadas en el perfil.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita listas interminables en pantalla, permitiendo al conductor consultar su historial histórico solo cuando le interesa.\n\n'
                '⚙️ FUNCIONAMIENTO: Alterna #historial-container (.open) y rota #historial-arrow (180°/0°).'
            ),
            "logout": (
                '💡 LA IDEA: Es la salida de seguridad total: borra los tokens del navegador, avisa al servidor y te regresa a la portada principal.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la privacidad del usuario, asegurando que nadie pueda operar con su cuenta si usa una máquina compartida, pero conservando sus preferencias del dispositivo.\n\n'
                "⚙️ FUNCIONAMIENTO: Cierra sesión: lee token, preserva flags/tour y device_id (keepPrefixes ['autopass_tour_seen_'], keepExact ['autopass_device_id']) en savedKeys; hace best-effort POST /v1/auth/logout con Authorization Bearer y body {device_id} (ignora errores); limpia localStorage completo y restaura savedKeys; redirige a '/'."
            ),
        },
    },
    "static/js/modules/utils.js": {
        "proposito": "Módulo de utilidades transversales (formateo, fechas/horas, toasts, diálogos confirm/choice, validación de patentes/vehículos, helpers DOM/UX). Usa openModal/closeModal desde ui.js para diálogos modales unificados (foco/Escape). Incluye formateadores con Intl.DateTimeFormat forzando hour12:false para consistencia 24h, parseFecha que normaliza 'YYYY-MM-DD HH:MM:SS' a ISO (compatibilidad Safari), computeHourlyAmount (regla escalonada por bloques 30min alineada con backend), escapeHtml, prefersReducedMotion/scrollToElement respetando reduced-motion, auto-bind de inputs .digits-only y cierre global de toasts.",
        "simbolos": {
            "formatNum": (
                '💡 LA IDEA: Es el formateador de importes monetarios que coloca los puntos de miles en los números grandes (como transformar 1500 en 1.500).\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita la lectura rápida de tarifas y deudas en pantalla según las costumbres de puntuación locales.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea número a string con separadores de miles (puntos) y coma para decimales si existiera. Acepta number/string/undefined/null; redondea a entero para la parte entera. Ej.: 1500 -> '1.500'."
            ),
            "computeHourlyAmount": (
                '💡 LA IDEA: Es la calculadora de tarifas escalonadas que divide la estadía en bloques de 30 minutos y calcula el costo exacto.\n\n'
                '🎯 POR QUE FUE GENERADA: Reproduce en el navegador la misma regla matemática de facturación del servidor para presupuestar costos al instante sin llamar a la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula monto por estadía/reserva según bloques de 30 minutos (regla escalonada). n = max(1, ceil(durationHours*2)). Si n==1 -> devuelve fraccion. Si n>=2 -> Math.floor(n/2)*hora + Math.floor((n-1)/2)*fraccion (alternando hora, fracción...). Debe coincidir con BillingService.hourly_amount_from_rates.'
            ),
            "toTitle": (
                "💡 LA IDEA: Es el corrector de nombres que pasa a mayúscula la primera letra de cada palabra y el resto a minúsculas (como 'JUAN PÉREZ' a 'Juan Pérez').\n\n"
                '🎯 POR QUE FUE GENERADA: Prolija la visualización de nombres y apellidos de clientes y empleados para que se lean de forma elegante.\n\n'
                "⚙️ FUNCIONAMIENTO: Capitaliza cada palabra: pasa a minúsculas, separa por espacios, capitaliza primera letra de cada palabra no vacía, junta con espacios. Devuelve '---' si entrada inválida."
            ),
            "formatDate": (
                '💡 LA IDEA: Es el reloj que transforma fechas técnicas de computadora a un formato humano y legible de día, mes, año y hora.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita a los conductores comprender al instante la fecha y horario de sus tickets y reservas.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea fecha ISO/string (YYYY-MM-DD HH:MM o con T) a 'DD-MM-YY HH:MM'. Normaliza reemplazando 'T' por espacio y '-' por '/' antes de new Date. Si inválida devuelve isoStr original."
            ),
            "parseFecha": (
                '💡 LA IDEA: Es el traductor universal de fechas capaz de interpretar cualquier formato de texto y transformarlo en una fecha válida para navegadores exigentes.\n\n'
                "🎯 POR QUE FUE GENERADA: Evita el famoso error de 'Fecha Inválida' que suele ocurrir en teléfonos iPhone y navegadores Safari cuando el formato tiene espacios.\n\n"
                "⚙️ FUNCIONAMIENTO: Convierte string/Date/number a Date de forma segura. Si Date -> devuelve tal cual. Si number -> new Date(number). Si string con espacio entre fecha/hora (YYYY-MM-DD HH:MM:SS) lo convierte a ISO con 'T' para evitar Invalid Date en Safari/otros engines; caso contrario usa string tal cual."
            ),
            "_coerceDate": (
                '💡 LA IDEA: Es el verificador de fechas que revisa si un dato es una fecha de calendario real o si es un texto inválido.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene que funciones de formateo rompan la pantalla si reciben datos nulos o corruptos.\n\n'
                '⚙️ FUNCIONAMIENTO: Coacciona valor a Date válido o null (usa parseFecha + isNaN).'
            ),
            "formatTime": (
                '💡 LA IDEA: Es el reloj digital que muestra únicamente la hora y minutos (como 14:30) en formato de 24 horas.\n\n'
                '🎯 POR QUE FUE GENERADA: Ideal para indicar horarios de apertura, cierre y turnos de estacionamiento con total claridad y sin ambigüedades de AM/PM.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea d a HH:MM (24h) usando _TIME_FMT.time (Intl.DateTimeFormat es-AR hour12:false). Devuelve '' si inválido."
            ),
            "formatTimeSeconds": (
                '💡 LA IDEA: Es el cronómetro de precisión que muestra la hora, minutos y segundos exactos de un suceso.\n\n'
                '🎯 POR QUE FUE GENERADA: Se utiliza en auditorías de barreras y registros de cámaras ALPR donde cada segundo cuenta.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea d a HH:MM:SS (24h) con _TIME_FMT.timeSec. Devuelve '' si inválido."
            ),
            "formatDateTime": (
                '💡 LA IDEA: Es la estampa completa de calendario y reloj con día, mes, año, hora, minutos y segundos.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga certeza cronológica absoluta en los comprobantes de pago y auditorías de seguridad.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea d a DD/MM/YYYY HH:MM:SS (24h) con _TIME_FMT.dateTime. Devuelve '' si inválido."
            ),
            "formatDayTime": (
                '💡 LA IDEA: Es el formato abreviado que muestra solo el día/mes y la hora (ej: 15/10 18:30) para espacios reducidos.\n\n'
                '🎯 POR QUE FUE GENERADA: Perfecto para tablas compactas de teléfonos móviles donde el año es redundante.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea d a DD/MM HH:MM (24h) con _TIME_FMT.dayTime. Devuelve '' si inválido."
            ),
            "formatLocalDateTime": (
                '💡 LA IDEA: Es el conversor de horario local que ajusta la fecha y hora a la zona horaria del país del usuario.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita confusiones horarias mostrando la hora real de Argentina independientemente de la hora del servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea d a D/M/YYYY HH:MM:SS (24h) con _TIME_FMT.localDateTime. Devuelve '' si inválido."
            ),
            "showToast": (
                '💡 LA IDEA: Es la notificación flotante tipo cartelito que aparece en la esquina de la pantalla para avisar de un éxito o error.\n\n'
                '🎯 POR QUE FUE GENERADA: Informa al usuario de inmediato sin interrumpir su navegación con molestas alertas intrusivas.\n\n'
                "⚙️ FUNCIONAMIENTO: Muestra toast premium en #toast-container. Tipos: 'success','error','info','warning','default'. Evita duplicados idénticos no ocultándose. Asigna ícono según tipo y role='alert' para error/warning (live region inmediato). Si duration>0 y tipo no es error/warning, programa _dismissToast tras duration; error/warning quedan hasta descarte manual."
            ),
            "_dismissToast": (
                '💡 LA IDEA: Es la animación de despedida que desvanece suavemente un cartelito de aviso antes de quitarlo de la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga una transición visual agradable y limpia la memoria del navegador.\n\n'
                "⚙️ FUNCIONAMIENTO: Descarta toast con animación 'hiding' y lo remueve del DOM tras 400ms (si existe)."
            ),
            "_closeAllToasts": (
                '💡 LA IDEA: Es el barrido de notificaciones que descarta todos los avisos flotantes cuando el usuario hace clic en la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite despejar la vista rápidamente cuando se acumulan varios avisos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra todos los toasts no ocultándose llamando _dismissToast a cada uno. Se bindea una sola vez a document click (captura true).'
            ),
            "showConfirm": (
                "💡 LA IDEA: Es la pregunta de confirmación ('¿Estás seguro?') con botones elegantes de Aceptar y Cancelar.\n\n"
                '🎯 POR QUE FUE GENERADA: Reemplaza las ventanas feas de alert del navegador con un diálogo modal moderno y accesible.\n\n'
                "⚙️ FUNCIONAMIENTO: Abre modal #modal-confirm con título/msg y devuelve Promise<boolean>. Si title=='' oculta titleEl; permite msg con HTML. Maneja respuesta (true/false) limpiando handlers y cerrando modal; también cierra al click fuera del modal."
            ),
            "showChoice": (
                '💡 LA IDEA: Es el menú de múltiples opciones que le pide al usuario elegir una alternativa entre varias posibles.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite tomar decisiones guiadas (por ejemplo, elegir entre pagar en efectivo o digital) de manera sencilla y atractiva.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre modal #modal-choice con título/msg y opciones (array de strings u objetos {label,icon}). Renderiza botones .choice-option con data-value; devuelve Promise<string|null>. Limpia handlers al resolver (click opción/cancelar/click fuera).'
            ),
            "normalizeSystemName": (
                '💡 LA IDEA: Es la planchadora de nombres: quita tildes, mayúsculas raras y prefijos para generar identificadores limpios en el sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que diferencias de acentos o mayúsculas hagan que el sistema no encuentre una sucursal o vehículo.\n\n'
                "⚙️ FUNCIONAMIENTO: Normaliza texto para id de sistema: quita prefijo 'AUTOPASS ', trim, uppercase, elimina tildes/acentos (NFD + remove diacríticos). Devuelve '' si null/undefined/'null'/'undefined'."
            ),
            "formatPlate": (
                '💡 LA IDEA: Es el formateador de patentes que inserta los espacios correctos según sea formato nuevo Mercosur o tradicional argentino.\n\n'
                "🎯 POR QUE FUE GENERADA: Hace que patentes como 'AA123BB' se lean naturalmente como 'AA 123 BB' en todas las tablas y tarjetas.\n\n"
                "⚙️ FUNCIONAMIENTO: Formatea patente Mercosur/latam a presentación legible (espacios). Limpia no alfanuméricos y pasa a mayúsculas. Longitud 6: AAA111 -> 'AAA 111'. Longitud 7: detecta patrones (Argentina Mercosur AB123CD -> 'AB 123 CD', Brasil ABC1D23 -> 'ABC 1D23', Uruguay ABC1234 -> 'ABC 1234', Paraguay autos ABCD123 -> 'ABCD 123', Paraguay motos 123ABCD -> '123 ABCD'). Otros casos devuelve clean."
            ),
            "filterTable": (
                '💡 LA IDEA: Es la lupa de búsqueda rápida en tablas que esconde las filas que no coinciden con lo que se está tipeando.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite encontrar vehículos, clientes o pagos en listas extensas en milisegundos sin recargar la página.\n\n'
                '⚙️ FUNCIONAMIENTO: Filtra filas de tbodyId según query (case-insensitive): oculta filas cuyo innerText no incluye q, muestra las que sí.'
            ),
            "bindDigitsOnly": (
                '💡 LA IDEA: Es el filtro de teclado que impide escribir letras o símbolos en campos que solo aceptan números (como el DNI o teléfono).\n\n'
                '🎯 POR QUE FUE GENERADA: Evita errores de tipeo accidentales antes de que los datos se envíen al servidor.\n\n'
                "⚙️ FUNCIONAMIENTO: Bindea input para aceptar solo dígitos: bloquea teclas no dígito (excepto ctrl/meta/alt/teclas especiales length>1) en keydown; limpia todo no dígito en input. Ejecutado automáticamente sobre inputs con clase 'digits-only'."
            ),
            "validatePlate": (
                '💡 LA IDEA: Es el detector de autenticidad de patentes de Argentina y países vecinos para autos y motos.\n\n'
                '🎯 POR QUE FUE GENERADA: Verifica que la patente ingresada cumpla con las leyes de tránsito antes de dar de alta un rodado.\n\n'
                '⚙️ FUNCIONAMIENTO: Valida patente según tipo. Para Moto: patrón Argentina /^[A-Z]{1}[0-9]{3}[A-Z]{3}$/. Para Auto: acepta argOld /^[A-Z]{3}[0-9]{3}$/, argMercosur /^[A-Z]{2}[0-9]{3}[A-Z]{2}$/, braMercosur /^[A-Z]{3}[0-9]{1}[A-Z]{1}[0-9]{2}$/, par /^[A-Z]{4}[0-9]{3}$/, uru /^[A-Z]{3}[0-9]{4}$/.'
            ),
            "detectVehicleType": (
                '💡 LA IDEA: Es el adivinador inteligente que deduce si una patente es de auto o de moto mirando la combinación de letras y números.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra trabajo al usuario seleccionando automáticamente si su vehículo es auto o moto según la patente tipeada.\n\n'
                "⚙️ FUNCIONAMIENTO: Detecta tipo por patente: si cumple patrón moto argentino -> 'Moto'. Si cumple cualquier patrón de auto -> 'Auto'. Sino -> null (indeterminado)."
            ),
            "metodoPagoReport": (
                "💡 LA IDEA: Es el traductor de medios de pago que convierte códigos técnicos en nombres comerciales claros (como 'PAGO EN CAJA' o 'MERCADO PAGO').\n\n"
                '🎯 POR QUE FUE GENERADA: Presenta los reportes contables con descripciones profesionales y fáciles de interpretar por cualquier cajero.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve etiqueta legible para reporte financiero según metodo y tipo. Normaliza a mayúsculas sin espacios: CAJA/EFECTIVO -> 'PAGO EN CAJA', MERCADOPAGO -> 'MERCADO PAGO', SALDO/DIGITAL/BILLETERAAUTOPASS -> 'PAGO DIGITAL', TRANSFERENCIA -> 'TRANSFERENCIA', TARJETA -> 'TARJETA', OTRO -> 'OTRO'. Si tipo==='Reembolso' -> 'REEMBOLSO DIGITAL'. Resto -> 'PAGO DIGITAL'."
            ),
            "escapeHtml": (
                '💡 LA IDEA: Es el escudo de seguridad que neutraliza caracteres peligrosos en textos cargados por los usuarios.\n\n'
                '🎯 POR QUE FUE GENERADA: Protege la aplicación contra ataques de inyección de código malicioso (XSS) en la pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Escapa caracteres HTML (& < > " \') para interpolar datos en innerHTML (prevención XSS).'
            ),
            "prefersReducedMotion": (
                '💡 LA IDEA: Es el detector de sensibilidad visual que averigua si el usuario tiene activada la opción de reducir animaciones en su dispositivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Respeto y empatía con personas propensas a mareos o problemas visuales, apagando transiciones bruscas.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve true si media query (prefers-reduced-motion: reduce) coincide (usa matchMedia si disponible).'
            ),
            "scrollToElement": (
                '💡 LA IDEA: Es el ascensor suave que desplaza la página automáticamente hasta el elemento que se necesita ver en pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Guía la atención del usuario hacia mensajes de error o formularios abiertos, respetando además sus preferencias de animación.\n\n'
                "⚙️ FUNCIONAMIENTO: Hace scrollIntoView sobre el respetando prefersReducedMotion(): usa behavior 'auto' si reduce motion, sino 'smooth'. Permite options y fuerza behavior tras spread para que preferencia de usuario tenga prioridad."
            ),
        },
    },
}
