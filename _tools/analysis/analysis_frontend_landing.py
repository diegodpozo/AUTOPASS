"""Explicaciones analizadas de frontend-landing (análisis del código real)."""

ANALISIS: dict[str, dict] = {
    "static/js/contacto.js": {
        "proposito": (
            "💡 LA IDEA: Es el buzón de consultas de la página de contacto. Atiende a quien completa el formulario de preguntas o sugerencias y le confirma de inmediato que su mensaje fue recibido.\n\n"
            "🎯 POR QUE FUE GENERADA: Los formularios web tradicionales, al apretar enviar, suelen recargar toda la página o dejar la pantalla en blanco. Este archivo intercepta el envío para que la página permanezca intacta, muestra una notificación visual de agradecimiento y resetea los campos de texto.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Importa la utilidad de avisos visuales `showToast` desde `./modules/utils.js`. 2. Al cargarse el contenido del navegador (`DOMContentLoaded`), localiza el formulario identificado como `contactForm`. 3. Si existe, captura su evento de envío (`onsubmit`) y cancela la recarga de página por defecto (`e.preventDefault()`). 4. Despliega un mensaje flotante de éxito avisando que un asesor se pondrá en contacto a la brevedad. 5. Limpia los campos del formulario (`e.target.reset()`) dejándolo disponible para una nueva consulta."
        ),
        "simbolos": {
        },
    },
    "static/js/landing.js": {
        "proposito": (
            "💡 LA IDEA: Es el anfitrión y presentador de la portada pública de AUTOPASS. Guía al visitante por el carrusel de bienvenida, enciende el mapa interactivo de sucursales, adapta el menú para celulares y le abre la puerta al formulario de reservas sin rodeos.\n\n"
            "🎯 POR QUE FUE GENERADA: La página principal combina muchas funciones dinámicas: navegación fluida, popups en el mapa con botones de 'Cómo llegar' o 'Reservar acá', menú hamburguesa para teléfonos móviles y redirección inteligente (si el usuario ya inició sesión y toca una sucursal en el mapa, lo lleva directamente a reservar en esa cochera sin obligarlo a empezar de cero).\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Expone en `window` las funciones `getDirectionsTo` (abre Google Maps con la ruta hasta la sucursal) e `irAReserva` (comprueba si hay sesión: si no hay abre el modal de login, si ya está en `/perfil` autocompleta el formulario, y si está afuera redirige a `/perfil?reserva_sucursal=...`). 2. Implementa `fillReservationForm`, una rutina inteligente que abre el panel de reserva y mediante reintentos periódicos (`setTimeout`) aguarda a que carguen las sucursales del servidor para seleccionar la cochera deseada y enfocar el formulario con scroll suave. 3. Define `toggleMobileMenu` y listeners de clic exterior para desplegar o colapsar el menú hamburguesa en smartphones bloqueando el scroll del fondo mientras está abierto. 4. En `DOMContentLoaded`, verifica el estado de autenticación (`checkAuthState`), activa la barra de navegación pegajosa al hacer scroll (`handleHeaderScroll`), dibuja el mapa interactivo Leaflet (`initMap`) y pone en movimiento el carrusel fotográfico de la portada (`InicializarCarrusel`)."
        ),
        "simbolos": {
        },
    },
    "static/js/modules/estadisticas-ocr.js": {
        "proposito": 'Módulo de dashboard de estadísticas OCR (ALPR): obtiene serie completa y logs vía API, construye datasets móviles con ventana deslizante (usando WindowedChart), calcula KPIs (promedio/mínimo/máximo/P90/cantidad), filtra tabla y gráfico por texto (patente/sucursal) y evento, formatea fechas/tiempos, asigna badges de rendimiento, mantiene reloj en vivo y gestiona auto-refresh configurable.',
        "simbolos": {
            "buildOCRDatasets": (
                '💡 LA IDEA: Es el dibujante de gráficos que traza cuatro líneas en la pantalla: los tiempos de cada lectura y tres líneas guía con el promedio, el récord más rápido y el más lento.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ver de un golpe de vista si el reconocimiento de patentes está funcionando rápido o si se produjeron demoras inusuales.\n\n'
                "⚙️ FUNCIONAMIENTO: Construye los cuatro datasets del gráfico móvil a partir de puntos (x,y): serie principal 'Tiempo OCR', línea de 'Promedio', línea de 'Máximo' y línea de 'Mínimo' (aplanadas a valor constante). Calcula avg/min/max sobre values, configura colores/estilo (trazos punteados para referencias, puntos visibles solo en serie principal), fill para la serie principal y hitRadius para interacción."
            ),
            "pushSerieOcr": (
                '💡 LA IDEA: Es el alimentador continuo que empuja los nuevos puntos de lectura al gráfico animado para que avance en el tiempo.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene el gráfico sincronizado en tiempo real a medida que ingresan vehículos por las barreras.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualiza el gráfico móvil con la serie filtrada (serieFiltrada) mapeada a {x:tMs, y} y delega en chartOcr.setSeries.'
            ),
            "formatearFecha": (
                '💡 LA IDEA: Es el traductor de marcas temporales que convierte fechas técnicas en un formato amigable de hora y día.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita mostrar fechas crudas incomprensibles en la tabla de auditoría de cámaras.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea una cadena ISO (o valor recibido) a representación legible: usa parseFecha + formatDateTime; si la fecha es inválida, intenta recortar 'T' a ' ' (primeros 19 caracteres) o devuelve el valor original."
            ),
            "obtenerBadgeRendimiento": (
                '💡 LA IDEA: Es la cucarda de velocidad: pega un rayito verde si leyó en menos de medio segundo, o una alerta amarilla/roja si tardó demasiado.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita detectar a simple vista qué lecturas fueron instantáneas y cuáles sufrieron demoras técnicas.\n\n'
                "⚙️ FUNCIONAMIENTO: Devuelve HTML de badge según ocr_time (parseFloat). Clasificación: >1.5 s -> perf-slow (triángulo-exclamación), >0.6 s -> perf-medium (indicador), else -> perf-fast (rayo). Si es null/undefined muestra '--' con estilo atenuado."
            ),
            "actualizarEstadisticasOcr": (
                '💡 LA IDEA: Es el recolector general que viaja al servidor a buscar las últimas lecturas de patentes y recalcula los promedios del día.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene actualizado todo el panel de control técnico con los últimos datos registrados por las cámaras.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga datos del dashboard OCR (en paralelo): /reports/ocr-stats?limit=N y /reports/ocr-activity. Actualiza serieOcr mapeando points (fecha_hora, y=ocr_time, patente, sucursal, tipo_evento) con parseFecha/tMs, filtrando NaN. Si stats OK, guarda logs en todosLosLogs, actualiza KPIs (avg/min/max/p90/count) y llama a filtrarTablaOcr. Muestra spinner en botón mientras dura la petición y maneja errores con mensaje en tabla. Usa limit desde #ocr-limit-select (default 100).'
            ),
            "serieFiltrada": (
                '💡 LA IDEA: Es el colador de datos que descarta las lecturas que no coinciden con la patente, sucursal o tipo de evento buscado.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite aislar el comportamiento de una cámara o patente puntual en el gráfico sin ruido de otros accesos.\n\n'
                '⚙️ FUNCIONAMIENTO: Filtra la serie completa serieOcr según inputs de la tabla: texto libre (uppercase) que coincida con patente o sucursal (substring); y filtro por tipo_evento. Devuelve array filtrado con tMs preservado.'
            ),
            "filtrarTablaOcr": (
                '💡 LA IDEA: Es la limpiadora de la tabla que muestra únicamente las filas que coinciden con los filtros aplicados y actualiza el gráfico.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga una búsqueda ágil e interactiva en la lista histórica de reconocimientos vehiculares.\n\n'
                "⚙️ FUNCIONAMIENTO: Filtra todosLosLogs con misma lógica que serieFiltrada (texto + tipo_evento). Llama a pushSerieOcr para sincronizar gráfico. Actualiza contador 'Mostrando X de Y registros'. Renderiza tbody: si vacío, muestra mensaje de sin resultados; si hay datos, genera filas con ID, fecha formateada, patente, badge de evento (ENTRADA/OTRO), sucursal (o 'Global') y badge de rendimiento (obtenerBadgeRendimiento)."
            ),
            "actualizarReloj": (
                '💡 LA IDEA: Es el segundero digital en vivo que late en la esquina del panel para confirmar que el sistema sigue funcionando.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda tranquilidad al operador de que la pantalla no se congeló y está conectada en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualiza #ocr-live-clock con formatTimeSeconds(now).'
            ),
            "configurarAutoRefresh": (
                '💡 LA IDEA: Es el piloto automático que actualiza las métricas cada 5 segundos si el operador dejó marcada la casilla de actualización continua.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita tener que apretar F5 o el botón de recargar para supervisar el movimiento en horas pico.\n\n'
                '⚙️ FUNCIONAMIENTO: Si existe intervaloAutoRefresh, lo limpia. Si #ocr-autorefresh está marcado, configura setInterval(actualizarEstadisticasOcr, 5000).'
            ),
            "initEstadisticasOcr": (
                '💡 LA IDEA: Es el botón de arranque que enciende el reloj, conecta los filtros y pide los primeros datos al cargar la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Deja el tablero de métricas de cámaras 100% operativo desde el primer instante en que se abre la página.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa listeners y timers del módulo OCR: escucha cambio de #ocr-autorefresh (configurarAutoRefresh), lanza actualizarReloj cada 1s e inicial (llamado inmediato), ejecuta actualizarEstadisticasOcr inicial y configura auto-refresh.'
            ),
        },
    },
    "static/js/modules/landing-carousel.js": {
        "proposito": 'Controla el carrusel principal de la landing (diapositivas e leyenda animada). Genera dinámicamente items a partir de DatosCarrusel, gestiona índice activo, navegación con flechas (RotarCarrusel con reinicio de temporizador), sincroniza leyenda con #frase-animada y mantiene intervalo automático (5s).',
        "simbolos": {
            "InicializarCarrusel": (
                '💡 LA IDEA: Es el armador del proyector de fotos de la portada, cargando las imágenes destacadas y preparando las flechas de navegación.\n\n'
                '🎯 POR QUE FUE GENERADA: Construye la galería visual de bienvenida de forma dinámica y liviana apenas carga el sitio web.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa el carrusel: valida contenedor #contenedorCarrusel (si no existe o ya tiene hijos, retorna). Para cada elemento de DatosCarrusel crea .item-carrusel con backgroundImage y marca activo el primero. Adjunta listeners a #carrusel-prev y #carrusel-next (RotarCarrusel con reiniciarTimer=true). Llama a IniciarTemporizadores.'
            ),
            "RotarCarrusel": (
                '💡 LA IDEA: Es el cambio de diapositiva que avanza o retrocede a la siguiente foto y actualiza la frase explicativa que la acompaña.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace dinámico el paseo visual por las comodidades del estacionamiento, reiniciando el temporizador si el usuario tocó una flecha.\n\n'
                '⚙️ FUNCIONAMIENTO: Rota diapositivas en dirección Direccion (±1). Si no hay items, retorna. Quita activo del actual, calcula IndiceCarruselActual con módulo (wrap-around). Agrega activo al nuevo. Sincroniza IndiceFraseActual con el mismo índice y actualiza #frase-animada con DatosCarrusel[IndiceFraseActual].leyenda. Si reiniciarTimer es true, limpia IntervaloCarrusel y reinicia intervalo de 5s.'
            ),
            "IniciarTemporizadores": (
                '💡 LA IDEA: Es el relojito automático que pasa las fotos cada 5 segundos si nadie toca nada.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene la portada viva y atractiva para los visitantes que entran a conocer el servicio.\n\n'
                '⚙️ FUNCIONAMIENTO: Limpia IntervaloCarrusel si existe. Inicia intervalo setInterval(() => RotarCarrusel(1), 5000). Inicializa leyenda en #frase-animada con DatosCarrusel[0].leyenda (si existe).'
            ),
        },
    },
    "static/js/modules/landing-data.js": {
        "proposito": 'Fuentes de datos estáticas de la landing: claves/TTL de cache de POIs, listado fijo de estadios (ESTADIOS_FIJOS con lat/lng/nombre/dirección) y DatosCarrusel con rutas de imagen + leyenda para diapositivas/frases.',
        "simbolos": {
            "POI_CACHE_KEY": (
                '💡 LA IDEA: Es la etiqueta del cajón del navegador donde se guardan los puntos de interés (estadios, cines) para no tener que bajarlos dos veces.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita hacer pedidos repetidos a internet, haciendo que el mapa cargue al instante.\n\n'
                "⚙️ FUNCIONAMIENTO: Clave localStorage para cache de POIs ('autopass_poi_cache')."
            ),
            "POI_CACHE_TTL": (
                '💡 LA IDEA: Es el tiempo de vida (24 horas) de los datos del mapa guardados en el navegador antes de renovarlos.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que la información de cines y estadios no quede obsoleta para siempre pero sin saturar la red.\n\n'
                '⚙️ FUNCIONAMIENTO: TTL del cache de POIs en milisegundos (86400000 = 1 día).'
            ),
            "ESTADIOS_FIJOS": (
                '💡 LA IDEA: Es la lista fija de estadios de fútbol populares (River, Boca, Racing, San Lorenzo, Morón) con sus coordenadas exactas.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que los estadios más concurridos aparezcan siempre en el mapa incluso si falla la conexión con servicios externos de mapas.\n\n'
                '⚙️ FUNCIONAMIENTO: Listado estático de estadios con coordenadas y dirección (Mâs Monumental, La Bombonera, El Cilindro, Pedro Bidegain, Carlos Sacaan).'
            ),
            "DatosCarrusel": (
                '💡 LA IDEA: Es el álbum oficial con las fotos y lemas publicitarios de la portada.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza las imágenes y frases promocionales en un solo lugar para cambiarlas fácilmente sin tocar el código visual.\n\n'
                '⚙️ FUNCIONAMIENTO: Array de objetos {imagen, leyenda} usados por carrusel y frase animada (contenido promocional/explicativo de AUTOPASS).'
            ),
        },
    },
    "static/js/modules/landing-map-data.js": {
        "proposito": 'Utilidades de datos/mapa para la landing: normalización de direcciones (sucursales/POIs), extracción de localidad desde branch, formateo de direcciones y cache de POIs (get/set con TTL desde landing-data). También expone getDirectionsTo para abrir rutas en Google Maps/Waze usando geolocalización (con fallback).',
        "simbolos": {
            "extractLocality": (
                '💡 LA IDEA: Es el detective geográfico que deduce a qué barrio o partido corresponde una sucursal leyendo su nombre o dirección.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite agrupar los estacionamientos por zona (como Morón, Castelar o Capital) en los menús de búsqueda.\n\n'
                "⚙️ FUNCIONAMIENTO: Extrae localidad desde branch: prioriza branch.localidad.trim(); si vacío, intenta limpiar nombre (elimina 'autopass' case-insensitive, recorta guiones/espacios iniciales); si aún vacío, toma última parte tras coma en direccion; fallback 'General'."
            ),
            "formatAddress": (
                '💡 LA IDEA: Es el corrector de direcciones que asegura que la altura de la calle esté bien separada con comas.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita direcciones mal tipeadas para que las aplicaciones de GPS puedan ubicarlas sin perderse.\n\n'
                '⚙️ FUNCIONAMIENTO: Normaliza dirección: si no contiene coma, intenta insertar coma tras número de calle (regex /(\\d+)\\s+([a-zA-ZáéíóúÁÉÍÓÚñÑ\\s]+)$/); si ya tiene coma, devuelve tal cual.'
            ),
            "formatPoiAddress": (
                '💡 LA IDEA: Es el armador de domicilios para cines y teatros a partir de los datos crudos del mapa mundial (OpenStreetMap).\n\n'
                '🎯 POR QUE FUE GENERADA: Transforma etiquetas dispersas en una dirección postal limpia y comprensible para el conductor.\n\n'
                '⚙️ FUNCIONAMIENTO: Construye dirección legible para POI desde tags OSM: street + housenumber (si street existe), añade suburb/district/city si no está ya incluido case-insensitive en street. Fallback a address o addr:full.'
            ),
            "getDirectionsTo": (
                "💡 LA IDEA: Es el botón de 'Cómo llegar' que abre la ruta en Google Maps o Waze desde la ubicación del celular hasta el estacionamiento.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite al conductor iniciar la navegación guiada por voz hacia la sucursal elegida con un solo toque.\n\n'
                "⚙️ FUNCIONAMIENTO: Abre navegación a (branchLat,branchLng) según mode ('google'|'waze'). Define URLs para Google/Waze. Si no hay geolocalización, abre fallback directo. Si hay geolocalización, obtiene posición (timeout 5000, enableHighAccuracy false), abre URL con origen+destino; en error usa fallback."
            ),
            "getPoiCache": (
                '💡 LA IDEA: Es el lector de la memoria local del navegador que busca si los cines y estadios ya estaban descargados de antes.\n\n'
                '🎯 POR QUE FUE GENERADA: Acelera drásticamente la carga del mapa al saltarse la consulta a servidores externos si los datos aún son frescos.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee cache POI desde localStorage (POI_CACHE_KEY). Si no existe, retorna null. Parsea JSON; si (Date.now()-ts > POI_CACHE_TTL) elimina clave y retorna null. Retorna data.items. Captura excepciones retornando null.'
            ),
            "setPoiCache": (
                '💡 LA IDEA: Es el guardián de la memoria que almacena los cines y estadios descargados junto con la hora actual.\n\n'
                '🎯 POR QUE FUE GENERADA: Guarda los puntos de interés para que las próximas visitas al sitio web no gasten datos móviles del cliente.\n\n'
                '⚙️ FUNCIONAMIENTO: Guarda en localStorage {ts: Date.now(), items} bajo POI_CACHE_KEY. Captura excepciones silenciosamente.'
            ),
        },
    },
    "static/js/modules/landing-map-geo.js": {
        "proposito": "Geolocalización y lógica de 'sucursal más cercana' para el mapa de landing: calcula distancia Haversine, localiza usuario, dibuja marcador + círculo de precisión, encuentra nearest branch en lmState.allBranchesMap y ajusta vista/popup/overlay con distancia. Usa toast si disponible.",
        "simbolos": {
            "calculateDistance": (
                '💡 LA IDEA: Es la regla de navegación que calcula la distancia en kilómetros en línea recta entre dos puntos de la Tierra.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ordenar las sucursales desde la más cercana a la más lejana respecto de la ubicación actual del conductor.\n\n'
                '⚙️ FUNCIONAMIENTO: Distancia Haversine entre (lat1,lon1)-(lat2,lon2) en km (R=6371). Convierte grados a radianes, aplica fórmula y retorna R*c.'
            ),
            "findNearestBranch": (
                "💡 LA IDEA: Es el radar 'Encontrar la más cercana' que ubica al cliente en el mapa, dibuja su posición y enfoca el estacionamiento más próximo.\n\n"
                '🎯 POR QUE FUE GENERADA: Resuelve la urgencia cotidiana del conductor que necesita saber de inmediato cuál es el estacionamiento más accesible desde donde está parado.\n\n'
                "⚙️ FUNCIONAMIENTO: Solicita geolocalización del usuario. Muestra toast 'Buscando tu ubicación...'. En éxito: obtiene myLat/myLng; si no hay branches retorna. Limpia _userMarker/_userCircle previos (si existen en activeMap). Dibuja marcador con ícono personalizado (punto azul con halo) y popup 'Tu ubicación', más círculo L.circle con radio=accuracy||50. Recorre lmState.allBranchesMap buscando la con menor distancia (calculateDistance). Si existe nearest: ajusta bounds (my+nearest) con padding [60,60] maxZoom 16; abre popup de sus marcadores asociados en ese mapa; actualiza overlay activo con texto 'nearest.nombre — distKm' (m si <1km); muestra toast con distancia. En error de geolocalización, loggea y muestra toast 'No se pudo obtener tu ubicación.'. Usa activeMap = targetMap || lmState.mapInstance; retorna alert si navegador no soporta geolocalización."
            ),
        },
    },
    "static/js/modules/landing-map-locality.js": {
        "proposito": 'Filtrado del mapa por localidad: a partir de lmState y extractLocality, muestra solo sucursales cuya localidad coincide con selectLocalidad.value. Para cada branch activa marcadores, actualiza panel/overlay (si corresponde) y refresca bounds del mapa con marcadores visibles.',
        "simbolos": {
            "filterMapByLocality": (
                '💡 LA IDEA: Es el filtro por barrio o ciudad del mapa, mostrando únicamente los estacionamientos de la zona seleccionada.\n\n'
                '🎯 POR QUE FUE GENERADA: Limpia la pantalla para que el cliente que viaja a un partido o centro comercial vea solo las opciones relevantes para su viaje.\n\n'
                "⚙️ FUNCIONAMIENTO: Filtra sucursales mostradas por localidad seleccionada. Obtiene select #selectLocalidad. Recorre lmState.allBranchesMap: determina loc = extractLocality(branch); visible = (selected==='Todas' || loc.toLowerCase()===selected.toLowerCase()). Para cada una: toggle de marcadores, actualiza branch.visible, oculta/expone .branch-item si existe. Actualiza overlay activo con mensaje 'Filtrado: X sucursal(es) en [localidad]' (o genérico si 'Todas'). Ajusta bounds: si hay marcadores visibles, fitBounds con padding [40,40] y maxZoom 14; si no hay visibles, centra según mapa activo."
            ),
        },
    },
    "static/js/modules/landing-map-pois.js": {
        "proposito": 'Carga y renderizado de POIs (cines/teatros y estadios) sobre el mapa de landing: usa cache (getPoiCache/setPoiCache), fetch a Overpass API con timeout, normaliza direcciones (formatPoiAddress), crea íconos personalizados, añade leyenda (#poi-legend), gestiona estados de carga (show/hidePoiLoading) y cachea resultados.',
        "simbolos": {
            "loadTheaters": (
                '💡 LA IDEA: Es el explorador cultural que busca cines y teatros cercanos en el mapa y les coloca un pin con forma de cámara de cine.\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a los conductores que van a ver una película o una obra de teatro a encontrar estacionamiento a pocas cuadras de la sala.\n\n'
                "⚙️ FUNCIONAMIENTO: Carga cines/teatros desde Overpass usando doFetch. Normaliza cada elemento (name, lat/lon, address=formatPoiAddress). Filtra válidos. Crea marcadores con ícono cinema y popup (nombre+dirección+'Cómo llegar'). Añade a lmState.poiLayers.theaters y muestra leyenda. En error, loguea advertencia."
            ),
            "createCfg": (
                '💡 LA IDEA: Es el taller de pines del mapa que define los colores, íconos y tamaños para cada categoría de lugar de interés.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga una apariencia visual distintiva y prolija a estadios y cines sin duplicar código de configuración de Leaflet.\n\n'
                "⚙️ FUNCIONAMIENTO: Factory de configuración/ícono para POI según type ('stadium'|'cinema'): define html, iconSize, iconAnchor, popupAnchor."
            ),
            "loadCachedPoi": (
                '💡 LA IDEA: Es la carga exprés de lugares guardados en el navegador para dibujarlos en el mapa sin esperar a internet.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace que los estadios y cines aparezcan al instante en pantalla mejorando la velocidad percibida por el usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga POIs cacheados via getPoiCache(). Para items stadium/cinema añade marcadores correspondientes a sus grupos. Muestra leyenda si hay items. Retorna true si cargó desde cache.'
            ),
            "doFetch": (
                '💡 LA IDEA: Es la llamada con límite de espera a la base cartográfica mundial de OpenStreetMap.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el mapa se quede colgado indefinidamente si el servicio de mapas externo responde con lentitud.\n\n'
                '⚙️ FUNCIONAMIENTO: Ejecuta fetch a Overpass con AbortController (timeout 15000ms). Retorna response.json().'
            ),
            "loadStadiums": (
                '💡 LA IDEA: Es el especialista en eventos deportivos que ubica las canchas de fútbol en el mapa con pines de pelota.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita a los hinchas reservar estacionamiento seguro antes de ir a la cancha en días de partido.\n\n'
                '⚙️ FUNCIONAMIENTO: Añade ESTADIOS_FIJOS con ícono stadium. Luego intenta enriquecer con Overpass (leisure=stadium), fusiona resultados, actualiza cache con setPoiCache. Muestra leyenda. En error, loguea advertencia.'
            ),
            "showPoiLoading": (
                "💡 LA IDEA: Es el cartelito de 'Cargando cines y estadios...' que avisa que se están buscando puntos de interés en la zona.\n\n"
                '🎯 POR QUE FUE GENERADA: Informa al visitante que el mapa está trabajando y evita que piense que no hay resultados disponibles.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra indicador de carga #poi-loading (flex/block).'
            ),
            "hidePoiLoading": (
                '💡 LA IDEA: Es el repliegue del indicador de carga cuando los puntos de interés terminaron de dibujarse.\n\n'
                '🎯 POR QUE FUE GENERADA: Deja el mapa despejado y listo para la interacción del usuario.\n\n'
                '⚙️ FUNCIONAMIENTO: Oculta indicador de carga #poi-loading (none).'
            ),
            "addPoiLegend": (
                '💡 LA IDEA: Es el cuadrito de referencias en la esquina del mapa que explica qué significa cada ícono (cines, teatros, canchas).\n\n'
                '🎯 POR QUE FUE GENERADA: Ayuda a los usuarios a interpretar el mapa sin confusiones de simbología.\n\n'
                "⚙️ FUNCIONAMIENTO: Añade leyenda #poi-legend al DOM si no existe con íconos 'Cines/Teatros' y 'Estadios'."
            ),
        },
    },
    "static/js/modules/landing-map-state.js": {
        "proposito": 'Estado compartido del módulo de mapa landing: almacena instancias/grupos Leaflet y datos derivados (mapInstance, allBranchesMap, poiLayers, etc.) para coordinación entre submódulos.',
        "simbolos": {
            "lmState": (
                '💡 LA IDEA: Es la mesa de trabajo compartida donde todos los módulos del mapa guardan la instancia del mapa, los marcadores y las capas activas.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el buscador, los filtros de barrio y el radar de cercanía interactúen con el mismo mapa sin pisarse los datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Objeto de estado compartido usado por submódulos para lectura/escritura coordinada.'
            ),
        },
    },
    "static/js/modules/landing-map.js": {
        "proposito": 'Orquestador principal del mapa de sucursales en landing: inicializa Leaflet, carga sucursales vía API, construye marcadores con popups ricos, maneja fullscreen, filtros por localidad, integración geo/POIs y expone helpers globales.',
        "simbolos": {
            "initMap": (
                '💡 LA IDEA: Es el director de escena del mapa interactivo: monta Leaflet, descarga las sucursales, coloca los pines y activa los botones.\n\n'
                '🎯 POR QUE FUE GENERADA: Da vida al mapa principal de la portada, permitiendo a los clientes explorar toda la red de estacionamientos.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa mapa Leaflet, carga /api/branches/map-data, crea marcadores por branch (con extractLocality, popup con datos+botones), configura UI (cercanía, toggles POI, selector localidad, fullscreen), expone window.getDirectionsTo/closeFullMap/openFullMap, carga POIs (theaters/stadiums) tras obtener sucursales.'
            ),
        },
    },
    "static/js/modules/landing.js": {
        "proposito": 'Módulo de utilidades/UI específicas de la landing: gestiona estado de autenticación (checkAuthState) y comportamiento del header al hacer scroll (handleHeaderScroll).',
        "simbolos": {
            "handleHeaderScroll": (
                '💡 LA IDEA: Es el camaleón de la barra de navegación superior: se vuelve oscura y compacta cuando el usuario baja por la página.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene los botones de menú y reservas siempre legibles y a mano sin importar en qué parte de la página te encuentres.\n\n'
                "⚙️ FUNCIONAMIENTO: Añade/remueve clase 'scrolled' al header según window.scrollY > 50."
            ),
            "checkAuthState": (
                "💡 LA IDEA: Es el detector de sesión de la portada que cambia los botones de 'Iniciar Sesión' por 'Mi Perfil' si el conductor ya está logueado.\n\n"
                '🎯 POR QUE FUE GENERADA: Ahorra clics innecesarios a usuarios habituales dirigiéndolos directamente a sus reservas y autos.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra/oculta nav-login/register vs nav-profile/logout según presencia de token localStorage. Asigna logout para limpiar token y redirigir.'
            ),
        },
    },
    "static/js/modules/monitoreo-live.js": {
        "proposito": 'Dashboard de monitoreo en vivo (CCTV + eventos): carga sucursales/cámaras, renderiza grid de slots, gestiona WebSocket por cámara y WS general, acciones (toggleCamera, openGate), grid responsive, consola de eventos y feedback visual.',
        "simbolos": {
            "initMonitoreoLive": (
                '💡 LA IDEA: Es el botón maestro de la sala de monitoreo: carga las sucursales, conecta los canales de video y prepara la cuadrícula de cámaras.\n\n'
                '🎯 POR QUE FUE GENERADA: Arranca todo el sistema de televigilancia en un solo paso dejando las pantallas listas para la guardia operativa.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa módulo: carga sucursales, listener branchSelect, conecta WS general, resize listener, arranque con sucursal guardada o primera.'
            ),
            "loadBranchesSelect": (
                '💡 LA IDEA: Es el desplegable de estacionamientos que le permite al guardia elegir qué sede quiere vigilar.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita alternar entre diferentes playas de estacionamiento de la empresa sin cambiar de pantalla.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga sucursales para #branchSelect vía API y guarda en estado.'
            ),
            "changeBranch": (
                '💡 LA IDEA: Es el cambio de sede: apaga los videos de la sede anterior, limpia la memoria y sintoniza las cámaras del nuevo estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita mezclar transmisiones de sucursales distintas y no satura la conexión a internet con videos en segundo plano.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia sucursal seleccionada: guarda en localStorage, limpia sockets, resetea estado, carga cámaras.'
            ),
            "clearVideoWebSockets": (
                '💡 LA IDEA: Es el corte general de transmisión que apaga todos los canales de video abiertos.\n\n'
                '🎯 POR QUE FUE GENERADA: Libera la memoria del navegador y la carga del servidor cada vez que el usuario cambia de vista o de sede.\n\n'
                '⚙️ FUNCIONAMIENTO: Cierra y limpia todos los WS de cámaras.'
            ),
            "loadCameras": (
                '💡 LA IDEA: Es la sintonizadora que pide las cámaras de la sucursal, arma los mosaicos en pantalla y empieza a recibir las imágenes en vivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Dibuja automáticamente una pantalla de vigilancia profesional adaptada a la cantidad de cámaras del predio.\n\n'
                '⚙️ FUNCIONAMIENTO: Obtiene cámaras por branchId, renderiza grid (computeCctvGrid+applyCctvGridSize), crea slots, adjunta eventos, muestra saludo, conecta cada cámara.'
            ),
            "computeCctvGrid": (
                '💡 LA IDEA: Es el arquitecto de pantalla que calcula cuántas columnas y filas hacen falta para que todas las cámaras se vean lo más grandes y cómodas posible.\n\n'
                '🎯 POR QUE FUE GENERADA: Optimiza el espacio disponible evitando barras de desplazamiento molestas tanto en monitores gigantes como en pantallas chicas.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula cols/rows óptimas según cantidad de cámaras.'
            ),
            "applyCctvGridSize": (
                '💡 LA IDEA: Es el pintor que ajusta el tamaño de cada visor de video según la distribución calculada.\n\n'
                '🎯 POR QUE FUE GENERADA: Aplica los estilos visuales necesarios para que el mosaico de cámaras luzca ordenado y simétrico.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica layout al #cctvGrid según config.'
            ),
            "arrangeCctvGrid": (
                '💡 LA IDEA: Es el adaptador de pantalla que reorganiza las cámaras si el operador agranda o achica la ventana del navegador.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene el mosaico prolijo y adaptable a cualquier resolución de pantalla en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Recalcula y reaplica layout (resize).'
            ),
            "renderActiveSlot": (
                '💡 LA IDEA: Es el proyector del visor principal que muestra el video de la cámara seleccionada con sus botones de control de barrera.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda al operador una vista ampliada de la cámara donde está ocurriendo una maniobra para inspeccionarla en detalle.\n\n'
                '⚙️ FUNCIONAMIENTO: Renderiza contenido del slot activo (video/overlay/controles/timestamp).'
            ),
            "connectCameraWebSocket": (
                '💡 LA IDEA: Es el cable digital directo hacia una cámara específica para recibir sus fotos cuadro por cuadro sin demora.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee streaming en vivo ultrarrápido y se encarga de reconectar automáticamente si hay un microcorte de red.\n\n'
                '⚙️ FUNCIONAMIENTO: Conecta WS por cámara, gestiona eventos, estado y reconexión con backoff.'
            ),
            "toggleCamera": (
                '💡 LA IDEA: Es el clic para seleccionar una cámara del mosaico y enfocarla en el visor de control principal.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al guardia saltar rápidamente a la cámara de la entrada o salida cuando un auto se aproxima a la barrera.\n\n'
                '⚙️ FUNCIONAMIENTO: Activa/desactiva slot de cámara, asegura conexión WS, oculta saludo.'
            ),
            "openGate": (
                "💡 LA IDEA: Es el botón de emergencia de 'Levantar Barrera' desde la pantalla de monitoreo.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite al operador habilitar el paso manualmente en milisegundos si un auto tiene dificultades con la lectura automática.\n\n'
                '⚙️ FUNCIONAMIENTO: Envía comando para abrir compuerta (API/WS), feedback y debounce temporal.'
            ),
            "connectGeneralWS": (
                '💡 LA IDEA: Es la radio de guardia general que escucha alertas de todo el predio (como ingresos o estadías pendientes).\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene informado al personal sobre sucesos de toda la sucursal sin depender de qué cámara esté mirando en ese momento.\n\n'
                '⚙️ FUNCIONAMIENTO: Conecta WS general para eventos globales, actualiza consola y último evento.'
            ),
            "showLastEventOnCameras": (
                '💡 LA IDEA: Es el cartel sobreimpreso en el video que muestra la patente y el estado del último auto que pasó por esa cámara.\n\n'
                '🎯 POR QUE FUE GENERADA: Ofrece información contextual instantánea al operador mientras vigila la imagen del vehículo.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra resumen del último evento en slots/cámaras.'
            ),
            "showCameraGreeting": (
                '💡 LA IDEA: Es la pantalla de espera elegante con instrucciones que se muestra antes de elegir una cámara para monitorear.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita mostrar pantallas vacías o rotas, guiando al guardia sobre cómo comenzar a operar.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra saludo cuando no hay slot activo.'
            ),
            "hideCameraGreeting": (
                '💡 LA IDEA: Es el retiro del cartel de bienvenida cuando el operador ya eligió una cámara para ver su transmisión.\n\n'
                '🎯 POR QUE FUE GENERADA: Despeja el visor central para dedicar todo el espacio a la imagen en vivo del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Oculta saludo.'
            ),
            "appendCameraConsoleLine": (
                "💡 LA IDEA: Es la línea de bitácora técnica que anota lo que la cámara va reconociendo (ej: 'Patente detectada: AB 123 CD').\n\n"
                '🎯 POR QUE FUE GENERADA: Permite al técnico auditar en directo los mensajes del motor de visión artificial para verificar su correcto funcionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrega línea formateada a consola de eventos de cámara.'
            ),
        },
    },
}
