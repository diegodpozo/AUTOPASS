"""Explicaciones analizadas de frontend-admin (parte 2): módulos JS del dashboard."""

ANALISIS: dict[str, dict] = {
    "static/js/modules/dashboard-finance.js": {
        "proposito": 'Pestaña de reporte financiero del panel admin: carga KPIs de recaudación, desglose por canal y método de pago, historial de transacciones paginado y gráfico de ingresos (Chart.js) filtrados por período, tipo de vehículo y método.',
        "simbolos": {
            "toggleFinanceStatsCollapsible": (
                '💡 LA IDEA: Es el fuelle para abrir o cerrar la caja de estadísticas avanzadas de recaudación.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ahorrar espacio en pantalla y enfocar la vista en los gráficos o en la tabla según lo que necesite el administrador.\n\n'
                "⚙️ FUNCIONAMIENTO: Alterna la clase 'open' en un botón desplegable y en su contenido ('finance-stats-collapsible-content') para abrir/cerrar la sección de estadísticas."
            ),
            "fitKpiValue": (
                '💡 LA IDEA: Es el encogedor de letras automático para números millonarios: reduce la fuente si el importe no entra en el cartel.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que cifras grandes de dinero queden cortadas o rompan el diseño del panel de control.\n\n'
                '⚙️ FUNCIONAMIENTO: Ajusta progresivamente el tamaño de fuente de un elemento KPI (de su tamaño base hasta 10px mínimo) hasta que el texto deje de desbordar su contenedor.'
            ),
            "setKpi": (
                '💡 LA IDEA: Es el pintor de carteles que estampa un número en su casillero asegurando que se lea completo.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la actualización de métricas contables aplicando el ajuste de tamaño correspondiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Escribe el texto en el elemento con el id dado (si existe) y le aplica fitKpiValue para que no se desborde.'
            ),
            "toggleFinanceDateFilter": (
                '💡 LA IDEA: Es el selector de fecha puntual que despliega el calendario solo cuando elegís filtrar por un día específico.\n\n'
                '🎯 POR QUE FUE GENERADA: Limpia el formulario ocultando el selector de días cuando se analizan períodos estándar como hoy, semana o mes.\n\n'
                "⚙️ FUNCIONAMIENTO: Si el período elegido es 'specific' muestra el input de fecha (prellenándolo con hoy según tiempo virtual si está vacío); si no, lo oculta. Recarga los datos al final."
            ),
            "switchMethodTab": (
                '💡 LA IDEA: Es la solapa de medios de pago para mirar la recaudación dividida por efectivo, Mercado Pago, tarjeta o billetera virtual.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita conciliar por separado los ingresos según el canal por donde entraron los fondos.\n\n'
                "⚙️ FUNCIONAMIENTO: Marca como activa la pestaña de método de pago elegida y muestra su panel, alternando las clases 'active' sobre .method-tab y .method-panel de 'metodos-breakdown'."
            ),
            "loadFinanceData": (
                '💡 LA IDEA: Es el balance general de caja: trae la recaudación total, desglose por métodos, tabla de pagos y dibuja la curva de ingresos.\n\n'
                '🎯 POR QUE FUE GENERADA: Consolida toda la información económica del estacionamiento para el control gerencial del negocio.\n\n'
                '⚙️ FUNCIONAMIENTO: Orquesta la pestaña financiera: arma la query con período/filtros del formulario (un día concreto se convierte en period=day con start/end), llama a /reports/financial-summary para llenar todos los KPIs y desgloses, luego a /reports/payment-history paginado (15 por página) para la tabla de transacciones (marcando reembolsos en rojo) y finalmente vuelve a pedir el historial completo (limit=0) para dibujar el gráfico. resetPage reinicia la paginación.'
            ),
            "nextFinancePage": (
                '💡 LA IDEA: Es el salto a la página siguiente del historial de transacciones de pago.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite auditar cobros antiguos sin sobrecargar la pantalla con miles de filas.\n\n'
                '⚙️ FUNCIONAMIENTO: Avanza a la siguiente página del historial de pagos y recarga sin resetear la página.'
            ),
            "prevFinancePage": (
                '💡 LA IDEA: Es el retroceso a la página anterior de transacciones cobradas.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita regresar a los cobros más recientes durante una revisión contable.\n\n'
                '⚙️ FUNCIONAMIENTO: Retrocede una página del historial (si no está en la primera) y recarga los datos.'
            ),
            "renderRevenueChart": (
                '💡 LA IDEA: Es el gráfico de montaña de ingresos que muestra en qué momentos del día o del mes entró más dinero.\n\n'
                '🎯 POR QUE FUE GENERADA: Ofrece a los administradores una visualización clara de las tendencias económicas y los picos de facturación.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja el gráfico de línea de ingresos con Chart.js: ordena los pagos por fecha, agrupa montos por etiqueta según el período (hora del día, día dd/mm o mes), destruye la instancia previa del gráfico y usa los colores del tema. Si Chart.js no está cargado no hace nada.'
            ),
        },
    },
    "static/js/modules/dashboard-informes.js": {
        "proposito": 'Informes analíticos del dashboard: mapa de calor de tráfico (grilla hora×día o gráfico por tramos), ocupación y reservas por hora, recaudación con ventas por sucursal, y tiempos de OCR/ALPR. Cada informe tiene filtros propios de sucursal y rango.',
        "simbolos": {
            "_hmLerp": (
                '💡 LA IDEA: Es la mezcla de acuarelas que calcula qué tan rojo debe ser un casillero según el nivel de ocupación (de blanco a rojo intenso).\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga una escala gradual de color para representar matemáticamente el tráfico vehicular.\n\n'
                '⚙️ FUNCIONAMIENTO: Interpola linealmente entre blanco y rojo según una razón 0..1 (recortada) y devuelve el color RGB [r,g,b]. Base de la rampa del mapa de calor.'
            ),
            "_hmCellColor": (
                '💡 LA IDEA: Es el formateador de color web para pintar el fondo de cada celda del mapa de calor.\n\n'
                '🎯 POR QUE FUE GENERADA: Aplica el tono exacto de saturación a cada casillero de la grilla horaria.\n\n'
                "⚙️ FUNCIONAMIENTO: Convierte el resultado de _hmLerp a string 'rgb(r,g,b)' para el fondo de una celda."
            ),
            "_hmCellText": (
                '💡 LA IDEA: Es el contraste automático de texto: pone letras negras sobre fondos claros y letras blancas sobre rojos intensos.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que los números de vehículos siempre se lean con total nitidez en el mapa de calor.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el color de texto (oscuro o blanco) según la luminancia del color calculado por _hmLerp, para que el número de la celda sea legible.'
            ),
            "cargarBranches": (
                '💡 LA IDEA: Es la carga única de sucursales en los filtros de todos los reportes analíticos.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita pedidos redundantes a la base de datos cada vez que cambiás de tipo de informe.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga una sola vez (flag branchesLoaded) la lista de sucursales desde /parking/branches y puebla los tres selects de filtros (hm/occ/fin-sucursal) con opción TODAS.'
            ),
            "cargarInforme": (
                '💡 LA IDEA: Es el distribuidor de tráfico analítico: dispara la carga del mapa de calor, ocupación, recaudación o tiempos de cámara según el informe elegido.\n\n'
                '🎯 POR QUE FUE GENERADA: Centraliza la llamada a los reportes avanzados asegurando que las dependencias estén listas.\n\n'
                "⚙️ FUNCIONAMIENTO: Despacha la carga del informe indicado: heatmap, ocupacion y recaudacion cargan antes las sucursales y luego su función propia; 'ocr' llama directo a cargarOcr."
            ),
            "aplicarInforme": (
                "💡 LA IDEA: Es el botón de 'Filtrar' que lee las fechas y sucursal elegidas y recalcula el reporte en pantalla.\n\n"
                '🎯 POR QUE FUE GENERADA: Permite acotar los informes a un período o sede específicos para auditorías puntuales.\n\n'
                "⚙️ FUNCIONAMIENTO: Lee los filtros del informe indicado desde el DOM (_leerFiltros), los guarda en el estado 'filtros' y recarga el informe."
            ),
            "limpiarInforme": (
                '💡 LA IDEA: Es la goma de borrar que vacía los filtros y devuelve el informe a su estado panorámico completo.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita reiniciar la consulta analítica con un solo clic.\n\n'
                '⚙️ FUNCIONAMIENTO: Vacía los inputs del informe indicado (_limpiar), limpia su estado de filtros y recarga con filtros vacíos.'
            ),
            "alternarHeatmapVista": (
                '💡 LA IDEA: Es el conmutador entre ver el mapa de calor como cuadrícula coloreada o como gráfico de barras apiladas por día.\n\n'
                '🎯 POR QUE FUE GENERADA: Ofrece al analista dos formas distintas y complementarias de interpretar el movimiento vehicular.\n\n'
                "⚙️ FUNCIONAMIENTO: Cambia entre vista 'calor' (grilla) y 'barras' del mapa de calor: actualiza el estado, refresca los botones [data-hm-view], repinta la leyenda y re-renderiza con los datos cacheados si hay."
            ),
            "_leerFiltros": (
                '💡 LA IDEA: Es el extractor de parámetros que lee los campos de fecha y sucursal del formulario correspondiente.\n\n'
                '🎯 POR QUE FUE GENERADA: Estandariza la recolección de filtros entre los distintos paneles analíticos.\n\n'
                "⚙️ FUNCIONAMIENTO: Lee los campos sucursal/desde/hasta del DOM usando un prefijo de ids ('hm', 'occ', 'fin') y devuelve el objeto de filtros."
            ),
            "_limpiar": (
                '💡 LA IDEA: Es el reseteador de campos que vacía los inputs del formulario analítico.\n\n'
                '🎯 POR QUE FUE GENERADA: Limpia las fechas y desplegables de manera uniforme.\n\n'
                '⚙️ FUNCIONAMIENTO: Vacía los inputs {prefijo}-sucursal/desde/hasta y devuelve un objeto de filtros en blanco.'
            ),
            "_params": (
                '💡 LA IDEA: Es el constructor de enlaces web que empaqueta los filtros de búsqueda para enviárselos al servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Transforma las opciones elegidas en la pantalla en una petición HTTP válida para el backend.\n\n'
                "⚙️ FUNCIONAMIENTO: Convierte un objeto de filtros en query string ('?sucursal=...&desde=...') omitindo los vacíos; devuelve cadena vacía si no hay filtros."
            ),
            "cargarHeatmap": (
                '💡 LA IDEA: Es el generador del mapa de calor de tráfico: pide los accesos hora por hora y dibuja la cuadrícula térmica.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite descubrir patrones de afluencia de clientes para optimizar turnos y horarios de atención.\n\n'
                '⚙️ FUNCIONAMIENTO: Pide /reports/metrics/traffic-heatmap con los filtros de heatmap, cachea la respuesta en heatmapCache, pinta la leyenda y renderiza la vista activa; muestra mensajes de carga/vacío/error en el contenedor.'
            ),
            "_renderHeatmap": (
                '💡 LA IDEA: Es el dibujante que elige si pintar la grilla de celdas o el gráfico de barras según la preferencia del operador.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene actualizada la visualización activa aprovechando los datos cacheados en memoria.\n\n'
                '⚙️ FUNCIONAMIENTO: Según la vista activa delega en _renderHeatmapBarras o _renderHeatmapGrid, usando los datos cacheados.'
            ),
            "_renderHeatmapGrid": (
                '💡 LA IDEA: Es la cuadrícula térmica con días en las columnas y horas en las filas, pintando de rojo las horas pico.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra de un solo vistazo el mapa completo de intensidad de tránsito de todo el mes.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja la grilla CSS del mapa de calor: cabecera de meses y días, filas por hora con celdas coloreadas según ratio máximo (tooltip con fecha/hora y cantidad), columna y fila de totales, y nota informativa debajo.'
            ),
            "_calcTramos": (
                '💡 LA IDEA: Es el divisor de la jornada en franjas horarias (mañana, mediodía, tarde, noche) para agrupar las estadísticas.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita comparar el volumen de ingresos entre diferentes momentos del día.\n\n'
                '⚙️ FUNCIONAMIENTO: Divide las horas de apertura en hasta 5 tramos iguales y, por cada día, suma las entradas de las horas de cada tramo; devuelve tramos con etiqueta, clase, color y valores.'
            ),
            "_renderHeatmapBarras": (
                '💡 LA IDEA: Es el gráfico de barras comparativo que apila las entradas de cada franja horaria día por día con barra de total general.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite evaluar qué días de la semana tuvieron mayor movimiento vehicular histórico.\n\n'
                '⚙️ FUNCIONAMIENTO: Renderiza el mapa de calor como gráfico de barras por día (Chart.js): un dataset por cada tramo calculado más uno TOTAL en dorado, en un viewport con scroll horizontal; destruye el gráfico previo del canvas y muestra error si Chart.js falta.'
            ),
            "_pintarLeyenda": (
                '💡 LA IDEA: Es el cuadro de referencias que explica qué significa cada color en el mapa de calor y en las barras.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita confusiones interpretativas indicando claramente los niveles bajo, medio y alto.\n\n'
                "⚙️ FUNCIONAMIENTO: Repinta la leyenda del heatmap: en vista 'barras' lista los tramos con sus colores más TOTAL DÍA; en vista 'calor' muestra Bajo/Medio/Alto."
            ),
            "_err": (
                '💡 LA IDEA: Es el cartelito de error con ícono de advertencia cuando un reporte no puede descargarse.\n\n'
                '🎯 POR QUE FUE GENERADA: Informa amablemente al usuario si hubo una falla de conexión en lugar de dejar la pantalla rota.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra un mensaje de error con icono dentro del elemento indicado (usado cuando falla la carga del heatmap).'
            ),
            "cargarOcupacion": (
                '💡 LA IDEA: Es el reporte de eficiencia de reservas: calcula el porcentaje de asistencia, cobros y dibuja la curva de capacidad horaria.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite medir el índice de conductores que reservaron pero no se presentaron (no-show) para ajustar el sobrecupo.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga /reports/metrics/occupancy-summary: arma la fila de KPIs (reservas, pagadas, pendientes, canceladas, no-show, ticket promedio, ingresos, días) y dibuja un gráfico de barras de ocupación promedio por hora y tipo de vehículo.'
            ),
            "_kpi": (
                '💡 LA IDEA: Es la fábrica de tarjetas de métricas destacadas con ícono, título y número formateado.\n\n'
                '🎯 POR QUE FUE GENERADA: Estandariza la presentación de cifras clave en todos los informes de la plataforma.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el HTML de una tarjeta KPI (icono + label + valor) usada por los informes de ocupación, recaudación y OCR.'
            ),
            "cargarRecaudacion": (
                '💡 LA IDEA: Es el informe de ingresos comerciales con desglose por sucursal y gráfico comparativo de billetera vs efectivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga al directorio una visión clara de la rentabilidad de cada sede del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga /reports/financial-summary traduciendo los filtros desde/hasta al formato period=day+start/end; pinta 8 KPIs, la tabla de ventas por sucursal y un gráfico de barras del monto por método de pago.'
            ),
            "_renderVentasPorSucursal": (
                '💡 LA IDEA: Es la tabla comparativa de facturación entre las distintas sucursales de la compañía.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite identificar qué sedes generan mayores ingresos y cuáles requieren incentivos comerciales.\n\n'
                "⚙️ FUNCIONAMIENTO: Renderiza la tabla 'ventas por sucursal' si el backend devolvió por_sucursal (solo llega al admin general sin filtro de sede); si no hay filas oculta la tarjeta."
            ),
            "cargarOcr": (
                '💡 LA IDEA: Es la auditoría técnica de cámaras ALPR: mide promedios de velocidad de lectura y grafica demoras en vivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al equipo de sistemas diagnosticar demoras en el reconocimiento de patentes antes de que afecten la operación.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga en paralelo /reports/ocr-stats y /reports/ocr-activity: pinta KPIs de tiempos OCR (promedio, min, max, p90, lentos >1s) y un gráfico de línea de los últimos 500 eventos de tiempo de lectura.'
            ),
        },
    },
    "static/js/modules/dashboard-metrics.js": {
        "proposito": 'Pestaña de métricas del dashboard: gráfico en vivo de accesos (entrada/salida por bucket de tiempo) con navegación por ventana, filtro de rango de fechas y auto-refresh; también orquesta el ingreso a los otros informes (heatmap, ocupación, recaudación, OCR) reutilizando dashboard-informes.',
        "simbolos": {
            "bucketToDate": (
                '💡 LA IDEA: Es el convertidor de etiquetas de tiempo de los gráficos en fechas reales comprensibles para el navegador.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita errores al posicionar los puntos de lectura en la línea temporal de Chart.js.\n\n'
                '⚙️ FUNCIONAMIENTO: Convierte el label de un bucket a Date con parseFecha; devuelve null si es inválido.'
            ),
            "cargarSerie": (
                '💡 LA IDEA: Es la descarga continua de entradas y salidas de autos divididas en intervalos de tiempo para dibujar el gráfico.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene alimentado el velocímetro de flujo vehicular en tiempo real.\n\n'
                '⚙️ FUNCIONAMIENTO: Pide /reports/metrics/access-activity (con desde/hasta del filtro si hay), actualiza KPIs, mantiene la vista al final si estaba en modo live, sincroniza el slider y re-renderiza el gráfico. Devuelve false si falla.'
            ),
            "maxStart": (
                '💡 LA IDEA: Es el tope de rebobinado: calcula hasta dónde podés deslizar la barra de tiempo hacia atrás sin salirte de los datos.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene la barra deslizadora calibrada dentro de los límites reales de la información disponible.\n\n'
                '⚙️ FUNCIONAMIENTO: Índice máximo de inicio de ventana: 0 si se muestra todo o no hay datos; si no, la cantidad de buckets menos el largo de la ventana visible.'
            ),
            "actualizarKPIs": (
                '💡 LA IDEA: Es el panel de cifras rápidas que muestra cuántos autos entraron y salieron en la ventana de tiempo visible.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee números totales inmediatos sin obligar al operador a sumar los puntos del gráfico a mano.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualiza los KPIs de la pestaña: primer dato, última hora, entradas, salidas y total (formateados en es-AR) a partir de serieData.'
            ),
            "ventanaVisible": (
                '💡 LA IDEA: Es la porción recortada de datos que entra en la ventana de tiempo elegida por el operador.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el gráfico dibuje únicamente las horas que el usuario desea analizar en ese momento.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve labels/entradas/salidas de la porción de buckets visible según el estado (showAll o recorte por viewStart/viewLen).'
            ),
            "renderGrafico": (
                '💡 LA IDEA: Es el electrocardiograma vehicular: traza dos líneas de colores (entradas en verde, salidas en azul) a lo largo del tiempo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ver con total claridad si en este momento está entrando más gente de la que sale en el predio.\n\n'
                "⚙️ FUNCIONAMIENTO: Dibuja el gráfico de línea de entradas y salidas con Chart.js sobre 'metricasChart'; destruye la instancia previa, usa los colores del tema y formatea fechas en los ejes/tooltips. Sin datos muestra un mensaje vacío."
            ),
            "fillEmpty": (
                "💡 LA IDEA: Es el cartelito amigable de 'Sin movimientos en este período' cuando no hubo tráfico en la playa.\n\n"
                '🎯 POR QUE FUE GENERADA: Evita mostrar gráficos vacíos o desfigurados cuando el local estuvo cerrado o sin actividad.\n\n'
                '⚙️ FUNCIONAMIENTO: Agrega al contenedor un mensaje centrado con icono (usado cuando no hay buckets de accesos).'
            ),
            "sincronizarSlider": (
                '💡 LA IDEA: Es la barra deslizadora que te permite viajar hacia atrás o adelante en el tiempo dentro del gráfico.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita rebobinar y revisar qué pasó horas atrás con un simple movimiento del cursor.\n\n'
                "⚙️ FUNCIONAMIENTO: Configura el input range 'metricas-range' con min=0, max=maxStart(), el valor actual de la vista y lo deshabilita en modo showAll o sin datos."
            ),
            "setVentana": (
                '💡 LA IDEA: Es el selector de zoom temporal para ver las últimas 2 horas, 6 horas, 24 horas o el historial completo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite pasar de una vista microscópica a una panorámica con un solo clic.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia el largo de la ventana visible (0 = mostrar todo), recorta viewStart al máximo posible, sincroniza el slider y re-renderiza.'
            ),
            "detenerRefresh": (
                '💡 LA IDEA: Es la pausa del cronómetro que apaga la actualización automática cuando abandonás la pestaña.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que el navegador gaste memoria y red actualizando gráficos que nadie está mirando.\n\n'
                '⚙️ FUNCIONAMIENTO: Limpia el intervalo de auto-refresh de la serie si existe.'
            ),
            "configurarRefresh": (
                '💡 LA IDEA: Es el piloto automático que refresca el gráfico de accesos cada 15 segundos mientras estés en la pantalla de métricas.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene la información al día sin que el operador tenga que apretar F5.\n\n'
                "⚙️ FUNCIONAMIENTO: Programa un refresco cada 15 s que solo recarga la serie si la pestaña activa es 'metricas' y el filtro no está bloqueado."
            ),
            "sincronizarEstadoFiltro": (
                '💡 LA IDEA: Es el candado de seguridad que apaga la actualización en vivo si estás analizando un período pasado que ya terminó.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que nuevos datos del presente se mezclen con auditorías de días anteriores.\n\n'
                "⚙️ FUNCIONAMIENTO: Marca el filtro como bloqueado si 'hasta' terminó hace más de una hora; en ese caso desactiva live y fuerza showAll, y habilita/deshabilita el checkbox live."
            ),
            "aplicarFiltroMetricas": (
                '💡 LA IDEA: Es el filtrado por rango de fechas y horas para auditar el tráfico vehicular de un turno específico.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite aislar incidentes o congestiones ocurridas en un horario determinado.\n\n'
                '⚙️ FUNCIONAMIENTO: Lee desde/hasta, intercambia si están invertidos, guarda el filtro en el estado, sincroniza el estado de bloqueo y recarga la serie.'
            ),
            "limpiarFiltroMetricas": (
                '💡 LA IDEA: Es la vuelta al presente que borra los filtros de fecha y regresa el gráfico a la transmisión en vivo de este momento.\n\n'
                '🎯 POR QUE FUE GENERADA: Restablece el monitoreo en tiempo real con un solo clic.\n\n'
                '⚙️ FUNCIONAMIENTO: Restablece el filtro vacío, reactiva live, vuelve al final de la serie, rehabilita el checkbox y recarga.'
            ),
            "setViewTitle": (
                '💡 LA IDEA: Es el cartel que escribe el nombre del informe que estás mirando arriba de la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Orienta al usuario sobre qué métrica o reporte tiene abierta en ese instante.\n\n'
                "⚙️ FUNCIONAMIENTO: Escribe el título de la vista actual ('view-title')."
            ),
            "abrirMetrica": (
                '💡 LA IDEA: Es la puerta de entrada a los reportes avanzados (tráfico, mapa de calor, recaudación u OCR) desde la solapa general.\n\n'
                '🎯 POR QUE FUE GENERADA: Conecta el menú de métricas con cada uno de los informes analíticos detallados.\n\n'
                "⚙️ FUNCIONAMIENTO: Muestra la vista de una métrica concreta (accesos, heatmap, ocupacion, recaudacion, ocr), oculta la lista, pone el título correspondiente y carga sus datos; para 'accesos' además activa el auto-refresh, para los demás lo detiene y delega en cargarInforme de dashboard-informes."
            ),
            "volverMetricas": (
                '💡 LA IDEA: Es el botón de regreso hacia el menú principal de métricas e informes.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite salir del detalle de un reporte y elegir otro tema de análisis.\n\n'
                '⚙️ FUNCIONAMIENTO: Vuelve a la lista de métricas, oculta todas las vistas de detalle, limpia el título y detiene el auto-refresh.'
            ),
            "verDetalleVisible": (
                '💡 LA IDEA: Es el sensor que averigua qué informe específico tenés abierto en la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite que el sistema recargue los datos correctos si la pantalla se actualiza en segundo plano.\n\n'
                "⚙️ FUNCIONAMIENTO: Detecta qué vista de detalle está visible (chequeando display==='block' de cada contenedor) y devuelve su clave, o null si está en la lista."
            ),
            "loadMetricas": (
                '💡 LA IDEA: Es la recarga inteligente que refresca el informe que tenés a la vista al volver a la pestaña de métricas.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que siempre encuentres los datos al día al retomar tu sesión de trabajo.\n\n'
                '⚙️ FUNCIONAMIENTO: Al re-entrar a la pestaña, recarga la vista de detalle visible (serie de accesos u otro informe) con su título.'
            ),
            "irAlInicio": (
                '💡 LA IDEA: Es el salto rápido al primer registro del historial vehicular.\n\n'
                '🎯 POR QUE FUE GENERADA: Lleva la línea de tiempo al comienzo del día o del período de análisis.\n\n'
                '⚙️ FUNCIONAMIENTO: Desactiva live y desplaza la ventana del gráfico al primer bucket.'
            ),
            "irAlFinal": (
                '💡 LA IDEA: Es el salto rápido al momento presente reconectando la transmisión en vivo.\n\n'
                '🎯 POR QUE FUE GENERADA: Devuelve el gráfico a los autos que están pasando por las barreras ahora mismo.\n\n'
                '⚙️ FUNCIONAMIENTO: Activa live y desplaza la ventana al último bucket disponible.'
            ),
            "initMetricas": (
                '💡 LA IDEA: Es el enganche de botones, controles deslizantes y selectores al cargar la pestaña de métricas.\n\n'
                '🎯 POR QUE FUE GENERADA: Deja el tablero interactivo de análisis listo para la navegación del operador.\n\n'
                '⚙️ FUNCIONAMIENTO: Engancha los listeners del checkbox live (sigue el final), del slider (navegación manual) y del selector de ventana de tiempo.'
            ),
        },
    },
    "static/js/modules/dashboard-operations.js": {
        "proposito": 'Operaciones manuales del panel de monitoreo: registro de ingresos/salidas a mano, cobro de estadías en caja, detalle de logs con captura y el popup de salida impaga que dispara el ALPR cuando un vehículo quiere salir con deuda.',
        "simbolos": {
            "manualEntry": (
                '💡 LA IDEA: Es la libreta de guardia digital para anotar la entrada de un auto cuando la cámara no leyó la patente.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita trabar la fila de ingreso cuando un coche tiene la patente tapada o deteriorada, iniciando el cobro de inmediato.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra un ingreso manual: normaliza la patente, detecta automáticamente Moto por formato (1 letra + 3 números + 3 letras), pide confirmación con modal premium y llama a /admin/manual-entry (con piso si hay); refresca ocupación y KPIs vivos.'
            ),
            "payOccupancy": (
                '💡 LA IDEA: Es la caja registradora de garita para cobrar la estadía en efectivo o billetera y levantar la barrera de salida.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al empleado cobrar en ventanilla y liberar la plaza en el sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Cobra una estadía desde el panel: elige el método de pago con showChoice, confirma el importe y POSTea a /access/pay-stay; al OK refresca ocupación/estadísticas y ejecuta el callback onPaidCallback si existe.'
            ),
            "manualExit": (
                '💡 LA IDEA: Es el registro de salida forzada para habilitar el egreso de un auto cuya patente no fue leída al salir.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite completar la estadía y levantar la barrera de salida manualmente.\n\n'
                '⚙️ FUNCIONAMIENTO: Registra una salida manual tras confirmación y llama a /admin/manual-exit; refresca ocupación y KPIs vivos al éxito.'
            ),
            "showLogDetail": (
                '💡 LA IDEA: Es la ficha probatoria del paso vehicular: muestra la foto captada por la cámara en la barrera junto con la fecha y hora exacta.\n\n'
                '🎯 POR QUE FUE GENERADA: Esencial para resolver disputas con clientes que reclaman por el horario registrado en su ticket.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca el log por id en /reports/access, llena el modal de detalle (patente, fecha, tipo, pago, reserva, usuario) y carga la imagen de captura del evento pasando el token por query string.'
            ),
            "openPendingExitPopup": (
                '💡 LA IDEA: Es la sirena visual de advertencia: salta en pantalla con la foto del auto cuando una cámara detecta un vehículo que quiere salir sin pagar.\n\n'
                '🎯 POR QUE FUE GENERADA: Alerta de inmediato al operador de garita para que cobre el importe adeudado antes de abrir la barrera.\n\n'
                "⚙️ FUNCIONAMIENTO: Abre el popup de salida impaga con los datos del evento PENDING_EXIT (patente, usuario, deuda —o 'SIN TARIFARIO'— y foto de la cámara con fallback a placeholder), reinicia el método de pago y habilita el botón de confirmar."
            ),
            "closePendingExitPopup": (
                '💡 LA IDEA: Es el cierre de la ventana de cobro de salida de emergencia.\n\n'
                '🎯 POR QUE FUE GENERADA: Despeja la pantalla cuando el vehículo fue atendido o se retiró de la barrera.\n\n'
                '⚙️ FUNCIONAMIENTO: Limpia los datos pendientes y cierra el modal de salida impaga.'
            ),
            "confirmPendingExit": (
                '💡 LA IDEA: Es el cobro y liberación en dos pasos: cobra la deuda acumulada y de inmediato habilita la salida del vehículo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que no se levante la barrera sin haber cobrado la estadía primero.\n\n'
                '⚙️ FUNCIONAMIENTO: Cobra la deuda con /access/pay-stay y luego registra la salida con /admin/manual-exit en secuencia; si el pago falla no hace la salida. Muestra toasts con el monto cobrado y refresca el tablero al terminar.'
            ),
        },
    },
    "static/js/modules/dashboard-promotions.js": {
        "proposito": 'CRUD administrativo de promociones del sistema de fidelización: tabla paginada, alta/edición con mapa Leaflet para la ubicación de canje (geocoding con Nominatim) y toggle de activación, con permisos por rol (staff solo lectura).',
        "simbolos": {
            "initPromoMap": (
                '💡 LA IDEA: Es el mapa interactivo para marcar la ubicación del comercio donde los clientes pueden canjear una promoción.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite ubicar físicamente el local asociado (como un lavadero o cafetería) para que aparezca en el mapa de los clientes.\n\n'
                "⚙️ FUNCIONAMIENTO: Crea el mapa Leaflet ('promo-map-picker') centrado en Buenos Aires con tiles de Google y un listener de click que ubica el marker; es idempotente."
            ),
            "updatePromoMarker": (
                '💡 LA IDEA: Es el pin del mapa que guarda las coordenadas y averigua automáticamente la calle y número por geocodificación inversa.\n\n'
                '🎯 POR QUE FUE GENERADA: Ahorra trabajo al operador completando la dirección postal con solo hacer clic en el mapa.\n\n'
                '⚙️ FUNCIONAMIENTO: Coloca o mueve el marker dorado en el mapa, escribe lat/lng en los inputs del formulario y, con debounce de 500 ms, hace reverse geocoding (Nominatim) para autocompletar el campo de dirección.'
            ),
            "_resetPromoMap": (
                '💡 LA IDEA: Es el centrado del mapa a su vista habitual de Buenos Aires quitando marcas viejas.\n\n'
                '🎯 POR QUE FUE GENERADA: Limpia el mapa para la creación de una nueva oferta.\n\n'
                '⚙️ FUNCIONAMIENTO: Quita el marker y devuelve el mapa a su vista por defecto.'
            ),
            "searchPromoAddress": (
                '💡 LA IDEA: Es el buscador de direcciones que ubica el mapa en la calle y altura ingresadas.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita posicionar el pin en el comercio sin tener que buscarlo visualmente entre las calles.\n\n'
                '⚙️ FUNCIONAMIENTO: Busca la dirección escrita con el geocoder de Nominatim, coloca el marker y centra el mapa en el primer resultado; avisa con toast si no encuentra nada.'
            ),
            "loadPromotionsAdmin": (
                '💡 LA IDEA: Es la cartelera de promociones activas e inactivas de la empresa para administrarlas desde el panel.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite consultar el catálogo completo de recompensas por puntos con sus costos y sedes asociadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Trae las promociones desde /admin/promotions, las cachea, resetea el estado de lista acotada y re-renderiza la tabla (o muestra error en línea).'
            ),
            "_promoColSpan": (
                '💡 LA IDEA: Es el calculador de columnas de la tabla para adaptar el diseño según si el usuario tiene permisos globales o locales.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene alineada la tabla para no dejar huecos visuales antiestéticos.\n\n'
                '⚙️ FUNCIONAMIENTO: Cantidad de columnas de la tabla según rol: 5 para admin global (incluye sucursal), 4 para el resto.'
            ),
            "renderPromotionsTable": (
                '💡 LA IDEA: Es el maquetador de filas de ofertas: muestra ícono, puntos requeridos, sucursal, switch de encendido y botones de edición.\n\n'
                '🎯 POR QUE FUE GENERADA: Presenta las promociones de forma ordenada y permite paginarlas en bloques de a 8 elementos.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja las filas de promociones (beneficio con icono y badge de tipo, puntos, sucursal solo para admin, switch de activación o badge de solo lectura para staff, acciones editar/eliminar) y las pagina con renderCappedList (8 por página).'
            ),
            "_cargarSucursalesPromo": (
                '💡 LA IDEA: Es el selector de sede para vincular la oferta a un estacionamiento puntual o dejarla disponible para toda la red.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los administradores definir promociones locales exclusivas o beneficios corporativos generales.\n\n'
                '⚙️ FUNCIONAMIENTO: Según rol: para admin global muestra el select de sucursal con /admin/branches (más opción Global); para admin local/staff lo oculta y fija la sucursal propia deshabilitada.'
            ),
            "showCreatePromotionModal": (
                '💡 LA IDEA: Es el formulario de alta de una nueva recompensa con su costo en puntos y mapa de ubicación.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite crear promociones atractivas para fidelizar a los clientes del estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Prepara el modal de nueva promoción (bloqueado para staff): limpia formulario, icono por defecto, tipo de canje voucher, ubicación vacía y mapa reseteado.'
            ),
            "editPromotion": (
                '💡 LA IDEA: Es el editor de términos de la oferta para corregir puntos necesarios o la dirección del local.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita mantener al día las promociones sin tener que crearlas desde cero.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el mismo modal cargando los datos de la promoción existente (título, puntos, icono, tipo de canje, sucursal, ubicación con marker en el mapa) y marca editingPromotionId para que el submit haga PUT.'
            ),
            "togglePromoTipoCanje": (
                "💡 LA IDEA: Es el selector que muestra el campo de '% de Descuento' solo si la promoción se aplica a reservas.\n\n"
                '🎯 POR QUE FUE GENERADA: Mantiene simple el formulario ocultando campos numéricos cuando el premio es un voucher físico (como un café de regalo).\n\n'
                "⚙️ FUNCIONAMIENTO: Muestra u oculta el campo de porcentaje de descuento según el tipo de canje seleccionado ('descuento_reserva' lo muestra)."
            ),
            "selectPromoIcon": (
                '💡 LA IDEA: Es el muestrario de íconos para elegir un dibujo representativo (un auto, un café, una llave o una estrella).\n\n'
                '🎯 POR QUE FUE GENERADA: Hace atractiva e identificable la recompensa en la aplicación móvil de los clientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Marca la opción de icono clickeada como activa y escribe su clase en el input oculto promo-icono.'
            ),
            "handleCreatePromotion": (
                '💡 LA IDEA: Es el guardado de la nueva promoción hacia la base de datos de la empresa.\n\n'
                '🎯 POR QUE FUE GENERADA: Valida los campos y publica la oferta para que los conductores empiecen a canjear sus puntos.\n\n'
                '⚙️ FUNCIONAMIENTO: Arma el payload del formulario (puntos, sucursal, tipo de canje, descuento, ubicación) y hace POST o PUT según editingPromotionId; recarga la lista al éxito. Bloqueado para staff.'
            ),
            "togglePromotion": (
                '💡 LA IDEA: Es el interruptor para pausar o reactivar una promoción con un solo clic.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite suspender ofertas temporalmente ante quiebres de stock sin borrarlas del sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Activa o desactiva una promoción vía POST /admin/promotions/{id}/toggle y recarga la tabla.'
            ),
            "deletePromotion": (
                '💡 LA IDEA: Es la eliminación definitiva de una promoción que ya no volverá a usarse.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene limpio el catálogo comercial retirando ofertas obsoletas.\n\n'
                '⚙️ FUNCIONAMIENTO: Elimina una promoción tras confirmación con DELETE /admin/promotions/{id} y recarga la lista.'
            ),
        },
    },
    "static/js/modules/dashboard-reservations.js": {
        "proposito": (
            "💡 LA IDEA: Es el mostrador de reservas del panel administrativo. Unifica la pantalla donde los supervisores consultan la lista de turnos de los clientes y el formulario donde cargan o modifican reservas manualmente cuando un conductor lo solicita por teléfono o en ventanilla.\n\n"
            "🎯 POR QUE FUE GENERADA: El ciclo de vida de una reserva administrativa requiere dos especialidades: buscar y filtrar en una grilla histórica (con paginado, cobro de señas y cancelaciones) y un formulario interactivo con calculadora de tarifas en tiempo real según el tipo de auto y horario. Este archivo aplica el patrón 'Fachada' para fusionar ambas mitades en un único punto de acceso.\n\n"
            "⚙️ FUNCIONAMIENTO: 1. Reexporta 8 funciones de consulta y auditoría desde `reservations-admin-list.js` (como `loadAdminReservations`, `onAdminResSearch`, `payReservationAdmin`, `cancelReservationAdmin`, `showReservationDetail`). 2. Reexporta 13 funciones de carga y cálculo desde `reservations-admin-form.js` (como `openNewReservationModal`, `openEditReservationModal`, `initNewResPatenteLookup`, `updateNewReservationPrice`, `handleAdminNewReservation`, `confirmEditResumoProceed`). 3. Garantiza que el tablero maestro `dashboard.js` acceda a todo el ecosistema de reservas administrativas a través de una interfaz limpia y coherente."
        ),
        "simbolos": {
        },
    },
    "static/js/modules/dashboard-stats.js": {
        "proposito": 'Panel de estadísticas en vivo: WebSocket de ocupación, KPIs de disponibilidad por tipo de vehículo, log de accesos recientes con paginación y tabla de ocupación actual con temporizador de cortesía y acciones de caja.',
        "simbolos": {
            "getPermanenciaMs": (
                '💡 LA IDEA: Es el cronómetro que calcula cuántos milisegundos lleva estacionado un auto adentro del predio según el reloj virtual.\n\n'
                '🎯 POR QUE FUE GENERADA: Base matemática para calcular el tiempo real de estadía y liquidar la deuda correspondiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Milisegundos transcurridos desde el ingreso usando tiempo virtual (getVirtualNow), o null si la fecha es inválida o vacía.'
            ),
            "formatPermanencia": (
                "💡 LA IDEA: Es el formateador de tiempo que convierte milisegundos en horas y minutos legibles (como '2h 15m').\n\n"
                '🎯 POR QUE FUE GENERADA: Facilita leer el tiempo transcurrido en la tabla de vehículos estacionados.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea milisegundos como 'Xh Ym' (horas y minutos)."
            ),
            "initOccupancyWS": (
                '💡 LA IDEA: Es el receptor de radio en vivo que escucha las alertas del servidor y actualiza la pantalla en milisegundos ante cada auto que entra o sale.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace que el panel de monitoreo sea un tablero en tiempo real sin requerir recargar la página web.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el WebSocket /v1/parking/ws con el token; ante cada mensaje refresca KPIs, logs, ocupación, tickets, badge de reservas (y el listado si esa pestaña está activa). Un evento PENDING_EXIT notifica al operador y abre el popup de cobro. Ante cierre reintenta en 5 s (salvo código 4003 = acceso restringido).'
            ),
            "loadLiveStats": (
                '💡 LA IDEA: Es la foto instantánea de plazas libres por categoría (autos, motos, camionetas) y la recaudación del día.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda al encargado de playa la situación actual del predio apenas ingresa al panel.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga en paralelo /parking/status y el resumen financiero del día; actualiza todas las cifras y barras de disponibilidad (autos, motos, camionetas, reservas por tipo) más los KPIs de pagos del día.'
            ),
            "setBarFill": (
                '💡 LA IDEA: Es el termómetro de colores que pinta las barras de aforo de verde, amarillo o rojo según qué tan lleno esté el estacionamiento.\n\n'
                '🎯 POR QUE FUE GENERADA: Alerta visualmente al operador cuando una categoría de vehículo está próxima a agotarse.\n\n'
                '⚙️ FUNCIONAMIENTO: Helper interno de loadLiveStats: ajusta el ancho de una barra de progreso y le agrega clase de color según la disponibilidad porcentual (danger ≤10%, orange ≤25%, warning ≤50%).'
            ),
            "loadRecentLogs": (
                '💡 LA IDEA: Es la bitácora de lecturas de cámaras ALPR con las últimas patentes reconocidas en las barreras.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite supervisar los accesos recientes y detectar problemas de reconocimiento de patentes.\n\n'
                '⚙️ FUNCIONAMIENTO: Pide /reports/access, actualiza las patentes mostradas en las cajas de cámara (footer + overlay con animación de detección si cambió) y aplica el filtro/paginación del log.'
            ),
            "applyLogsFilter": (
                '💡 LA IDEA: Es el buscador de la bitácora para encontrar el paso de una patente puntual o filtrar solo entradas o salidas.\n\n'
                '🎯 POR QUE FUE GENERADA: Agiliza la búsqueda de auditoría ante reclamos o dudas de clientes en la garita.\n\n'
                '⚙️ FUNCIONAMIENTO: Filtra los logs por patente o tipo de evento según la búsqueda, corrige la página si quedó fuera de rango y re-renderiza la tabla.'
            ),
            "renderLogsTable": (
                '💡 LA IDEA: Es la tabla de accesos recientes con horarios exactos, patentes y botones para ver la foto de la cámara.\n\n'
                '🎯 POR QUE FUE GENERADA: Presenta el flujo de accesos con sus comprobantes fotográficos de respaldo.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja la página actual del log de accesos (hora, patente, evento, badge PAGADO/CORTESÍA/PENDIENTE y botón de detalle con captura).'
            ),
            "renderLogsPagination": (
                '💡 LA IDEA: Es la botonera de Anterior y Siguiente de la bitácora de cámaras.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite recorrer cientos de lecturas de barrera sin lentitud en el navegador.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera los botones Anterior/Siguiente y el indicador de página del log; lo vacía si hay una sola página.'
            ),
            "changePageLogs": (
                '💡 LA IDEA: Es el cambio de página en la lista de lecturas de cámaras.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita navegar por el registro histórico de ingresos y salidas.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia la página del log de accesos y re-renderiza.'
            ),
            "filterLogs": (
                '💡 LA IDEA: Es el activador del filtro de patentes que reinicia la tabla en la primera página de resultados.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que la búsqueda comience siempre desde el primer resultado coincidente.\n\n'
                '⚙️ FUNCIONAMIENTO: Expone el filtro del log: guarda la consulta, vuelve a la página 1 y re-aplica.'
            ),
            "loadOccupancy": (
                '💡 LA IDEA: Es el censo de autos adentro: lista cada patente presente en la playa con su piso asignado, deuda y permanencia.\n\n'
                '🎯 POR QUE FUE GENERADA: Controla con exactitud qué vehículos están ocupando plazas y cuánto dinero deben abonar para salir.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga en paralelo la ocupación actual y las sucursales: puebla el select de pisos del ingreso manual si la sucursal tiene planta baja, aplica el filtro, y actualiza KPIs (cantidad, motos, deuda total y permanencia promedio).'
            ),
            "applyOccupancyFilter": (
                '💡 LA IDEA: Es la lupa rápida para saber si una patente determinada se encuentra adentro del estacionamiento y en qué piso.\n\n'
                '🎯 POR QUE FUE GENERADA: Resuelve en segundos la consulta de un cliente que pregunta por su vehículo o busca dónde lo dejó.\n\n'
                '⚙️ FUNCIONAMIENTO: Filtra la ocupación por patente o nombre de piso, corrige la página fuera de rango y re-renderiza la tabla.'
            ),
            "renderOccupancyTable": (
                '💡 LA IDEA: Es la planilla de autos adentro con botones para cobrar, forzar salida o cancelar estadías.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga al operador todas las herramientas de gestión sobre los vehículos presentes en el establecimiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Pinta la tabla de ocupación en ambos contenedores posibles (lista y pestaña), actualiza paginación y arranca el temporizador de cortesía si hay badges activos.'
            ),
            "getCortesiaRemainingMs": (
                '💡 LA IDEA: Es el cronómetro regresivo de los 10 minutos de cortesía para autos que acaban de ingresar.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite saber si un auto todavía está a tiempo de salir sin pagar si dio la vuelta de inmediato.\n\n'
                '⚙️ FUNCIONAMIENTO: Milisegundos restantes de la cortesía de 10 minutos desde el ingreso (tiempo virtual); nunca negativo.'
            ),
            "formatCortesiaTimer": (
                "💡 LA IDEA: Es el reloj que muestra '08:45' en cuenta regresiva para la cortesía de ingreso.\n\n"
                '🎯 POR QUE FUE GENERADA: Advierte con precisión cuánto tiempo de gracia le queda al conductor antes de comenzar a cobrarle.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea los ms restantes como 'MM:SS'; devuelve null cuando se agotó."
            ),
            "startCortesiaTimer": (
                '💡 LA IDEA: Es el segundero que descuenta segundo a segundo el tiempo de gracia en las tarjetas de vehículos recién ingresados.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene viva la cuenta regresiva en pantalla y recalcula la deuda apenas se agota la cortesía.\n\n'
                '⚙️ FUNCIONAMIENTO: Intervalo de 1 s que descuenta el temporizador de cortesía en cada badge; al agotarse re-renderiza la tabla y se detiene solo.'
            ),
            "buildOccupancyRows": (
                '💡 LA IDEA: Es el maquetador de filas de autos estacionados con sus íconos de vehículo, badges de reserva y deuda calculada.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra la información contable y operativa de cada coche con un diseño claro y legible.\n\n'
                '⚙️ FUNCIONAMIENTO: Construye el HTML de la página actual de la tabla de ocupación: patente+piso, tipo con icono, badge de reserva, ingreso, permanencia, estado de deuda (PAGADO/cortesía en vivo/deuda) y acciones (cobrar, salida manual, cancelar).'
            ),
            "renderOccupancyPagination": (
                '💡 LA IDEA: Es la paginación de la lista de vehículos adentro de la playa.\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene ordenada la visualización en estacionamientos de gran capacidad con cientos de plazas ocupadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Genera la paginación de ocupación en los dos contenedores posibles (oculta si hay una sola página).'
            ),
            "changePageOcc": (
                '💡 LA IDEA: Es el avance o retroceso de página en la lista de ocupación actual.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite recorrer la lista completa de vehículos presentes de forma ágil.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia la página de ocupación y re-renderiza.'
            ),
            "filterOccupancy": (
                '💡 LA IDEA: Es el disparo del filtro de ocupación que resetea a la primera página de coincidencias.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura encontrar el vehículo buscado sin importar en qué página estaba.\n\n'
                '⚙️ FUNCIONAMIENTO: Expone el filtro de ocupación: guarda la búsqueda, vuelve a la página 1 y re-aplica.'
            ),
            "cancelStay": (
                '💡 LA IDEA: Es la anulación de una estadía errónea o de un vehículo que se retiró dentro de la tolerancia de cortesía sin costo.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita cobros indebidos y libera la plaza en el sistema de inmediato.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancela una estadía desde la tabla: calcula si aún está en cortesía de 10 min (muestra deuda 0 si es así), pide confirmación y llama a /admin/cancel-stay; refresca ocupación y KPIs al éxito.'
            ),
        },
    },
    "static/js/modules/dashboard-tickets.js": {
        "proposito": 'Gestión de tickets de soporte desde el panel admin: listado filtrable con badge de pendientes, estadísticas, modal de atención con conversación, envío de respuesta y cambio de estado, con auto-refresh cada 10 s mientras la pestaña esté visible.',
        "simbolos": {
            "loadAdminTickets": (
                '💡 LA IDEA: Es la bandeja de entrada de soporte del personal: descarga los reclamos de los clientes con filtros por estado.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al equipo de atención al cliente organizar su trabajo y responder consultas pendientes.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga los tickets desde /admin/support-tickets (con filtro de estado si hay), los cachea, re-aplica la búsqueda activa, actualiza estadísticas y el badge de pendientes del sidebar.'
            ),
            "updateTicketBadge": (
                '💡 LA IDEA: Es la burbuja roja con número en el menú lateral que avisa cuántas consultas de usuarios quedan sin responder.\n\n'
                '🎯 POR QUE FUE GENERADA: Alerta al personal sobre reclamos entrantes para que no queden clientes esperando ayuda.\n\n'
                "⚙️ FUNCIONAMIENTO: Actualiza el badge de notificaciones del sidebar con /admin/support-tickets/pending-count (muestra '99+' y animación pulse si hay pendientes)."
            ),
            "filterTicketList": (
                '💡 LA IDEA: Es el buscador de reclamos por nombre de cliente, correo, asunto o sucursal.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita encontrar el historial de un conductor cuando llama por teléfono o se acerca a la ventanilla.\n\n'
                '⚙️ FUNCIONAMIENTO: Filtra los tickets cacheados por asunto, nombre/email del cliente, categoría o sucursal; sin consulta restaura la lista completa.'
            ),
            "updateTicketStats": (
                '💡 LA IDEA: Es el resumen numérico de atención: muestra cuántos tickets están pendientes, cuántos en proceso y cuántos resueltos.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite a los supervisores medir la eficiencia y velocidad de respuesta del equipo de soporte.\n\n'
                "⚙️ FUNCIONAMIENTO: Actualiza los contadores de la pestaña: total, pendientes (incluye 'en revisión'), en proceso y resueltos, más el texto del encabezado."
            ),
            "renderAdminTickets": (
                "💡 LA IDEA: Es la lista de mensajes de soporte con cartelitos de 'SIN LEER', datos del conductor y botón para abrir la charla.\n\n"
                '🎯 POR QUE FUE GENERADA: Organiza los reclamos de forma clara y prioriza los mensajes que todavía no fueron leídos por el staff.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja las filas de tickets (nro + tag SIN LEER, cliente, categoría, asunto, badge de estado con icono, fecha y botón de atención) con lista acotada a 8 por página.'
            ),
            "renderAdminTicketMessages": (
                '💡 LA IDEA: Es la ventana de chat con el cliente: muestra el historial cronológico de la conversación con fechas y adjuntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Provee todo el contexto del problema para que cualquier empleado pueda continuar la atención sin repetir preguntas.\n\n'
                '⚙️ FUNCIONAMIENTO: Renderiza la conversación del ticket en burbujas (autor, hora, píldora de fecha al cambiar de día, adjuntos con icono según imagen/PDF), con escape HTML y scroll automático al final.'
            ),
            "setTicketAnswerLocked": (
                '💡 LA IDEA: Es el cerrojo del formulario de respuesta que bloquea el envío si el reclamo ya fue cerrado o resuelto.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita continuar conversaciones en tickets archivados o finalizados.\n\n'
                '⚙️ FUNCIONAMIENTO: Bloquea o desbloquea el formulario de respuesta: si el ticket está cerrado oculta campos y botones, muestra el mensaje de bloqueo y cambia el placeholder.'
            ),
            "openTicketAnswerModal": (
                '💡 LA IDEA: Es la apertura del panel de respuesta al cliente, marcando además las notificaciones como leídas.\n\n'
                '🎯 POR QUE FUE GENERADA: Abre el canal de diálogo directo con el usuario y limpia la alerta de pendiente en el sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Abre el modal de atención: llena datos del ticket, precarga estado, bloquea si está resuelto/cerrado, carga la conversación desde /admin/support-tickets/{id} y marca las notificaciones como leídas (PATCH read-notifs).'
            ),
            "submitTicketAnswer": (
                "💡 LA IDEA: Es el envío de la solución o respuesta al cliente con actualización del estado del reclamo (ej: a 'Resuelto').\n\n"
                '🎯 POR QUE FUE GENERADA: Despacha la respuesta al celular del usuario y archiva el ticket resuelto.\n\n'
                '⚙️ FUNCIONAMIENTO: Envía la respuesta con PATCH (estado + texto); valida que haya texto, deshabilita el botón mientras procesa, re-renderiza la conversación, refresca la lista y los badges al éxito.'
            ),
        },
    },
    "static/js/modules/dashboard-ui.js": {
        "proposito": 'UI base del dashboard admin: reloj con tiempo virtual, indicadores de salud del sistema (BD, API, ALPR por sucursal), conmutación de pestañas con control de permisos por rol y colapso del sidebar; además re-exporta el módulo de cámaras.',
        "simbolos": {
            "initClock": (
                '💡 LA IDEA: Es el reloj maestro del panel que marca la hora y fecha del tiempo virtual de pruebas escolares en el encabezado.\n\n'
                '🎯 POR QUE FUE GENERADA: Informa constantemente al operador en qué momento temporal se encuentra operando la simulación.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra la hora (tiempo virtual) en #clock y la actualiza cada segundo.'
            ),
            "checkSystemHealth": (
                '💡 LA IDEA: Es el chequeo de conectividad que verifica que la base de datos y los servicios de lectura de patentes respondan.\n\n'
                '🎯 POR QUE FUE GENERADA: Alerta de inmediato si hay una caída de servicio antes de que los clientes lleguen a las barreras.\n\n'
                '⚙️ FUNCIONAMIENTO: Pide /system/health y actualiza los indicadores: punto principal de BD+API y nodos de OCR de entrada/salida de la sucursal actual (claves {SUCURSAL}_ENTRADA/_SALIDA o las principales si no hay sucursal).'
            ),
            "updateHealthNode": (
                '💡 LA IDEA: Es la luz indicadora verde o roja (ONLINE/OFFLINE) de cada componente del sistema.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda una señal visual instantánea sobre el estado técnico de cada nodo.\n\n'
                '⚙️ FUNCIONAMIENTO: Pinta un nodo de salud (punto + label ONLINE/OFFLINE) según el estado recibido, usando los colores del tema.'
            ),
            "initVideoStreams": (
                '💡 LA IDEA: Es el punto de enganche para encender las transmisiones de video al ingresar a la pantalla de monitoreo.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que los visores de cámaras se inicialicen ordenadamente al abrir la solapa de vigilancia.\n\n'
                "⚙️ FUNCIONAMIENTO: Función vacía: los streams de video se manejan por settings/cámaras; queda como hook al entrar a la pestaña 'live'."
            ),
            "switchTab": (
                '💡 LA IDEA: Es el cambiador de pestañas del panel de control respetando estrictamente los roles de acceso (admin, local o staff).\n\n'
                '🎯 POR QUE FUE GENERADA: Protege secciones restringidas redirigiendo a los empleados solo a las herramientas autorizadas para su cargo.\n\n'
                "⚙️ FUNCIONAMIENTO: Cambia la pestaña activa del dashboard: para staff redirige pestañas restringidas a 'live', actualiza nav, vistas y título, persiste la pestaña en localStorage, dispara loadTabData, limpia el badge de reservas, gestiona el intervalo de diagnósticos de la pestaña settings y cierra el menú móvil."
            ),
            "toggleSidebar": (
                '💡 LA IDEA: Es el botón para contraer o expandir el menú lateral del dashboard para ganar espacio de trabajo.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite dedicar toda la pantalla a las cámaras y tablas de vehículos cuando se necesita máxima visibilidad.\n\n'
                '⚙️ FUNCIONAMIENTO: Colapsa o expande el sidebar y el layout, alterna el icono de flecha y persiste la preferencia en localStorage.'
            ),
        },
    },
    "static/js/modules/reservations-admin-form.js": {
        "proposito": 'Formulario unificado de reserva manual del admin/staff: alta y edición en un mismo modal, con tarifas autoritativas por sucursal, descuentos por ticket de canje, selector horario con chips y arrastre, y confirmación de diferencia de importe al editar reservas ya pagadas.',
        "simbolos": {
            "_newBranchSlotRange": (
                '💡 LA IDEA: Es la consulta de horarios del estacionamiento para no permitir reservas manuales cuando el local está cerrado.\n\n'
                '🎯 POR QUE FUE GENERADA: Impide que los empleados tomen reservas fuera del horario de atención al público.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el rango de la grilla horaria según la sucursal seleccionada: 00:00–23:30 si es 24 h, el horario configurado parseado si existe (cierre 00:00 = fin del día), o el fallback 07:00–23:30.'
            ),
            "_newResYmd": (
                '💡 LA IDEA: Es el formateador de fechas de calendario en formato estándar año-mes-día.\n\n'
                '🎯 POR QUE FUE GENERADA: Estandariza las fechas para las consultas de disponibilidad en la base de datos.\n\n'
                "⚙️ FUNCIONAMIENTO: Formatea una Date como 'YYYY-MM-DD'."
            ),
            "updateNewVehicleTypeIcon": (
                '💡 LA IDEA: Es el cambio de ícono de auto, moto o camioneta en la reserva manual de mostrador.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga confirmación visual inmediata del rodado y recalcula el precio correspondiente.\n\n'
                '⚙️ FUNCIONAMIENTO: Cambia el icono del tipo de vehículo (moto/camioneta/auto), recalcula el precio y refresca la grilla horaria.'
            ),
            "resetNewResPatenteLookup": (
                '💡 LA IDEA: Es la limpieza de la búsqueda de clientes cuando se borra o cambia la patente en el formulario.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita asociar la reserva a un usuario equivocado si el operador tipea una patente distinta.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancela el debounce de búsqueda, limpia el usuario vinculado y su badge, restaura icono de auto y refresca el descuento en vivo.'
            ),
            "clearNewResPatenteLookup": (
                '💡 LA IDEA: Es el borrado total de la patente y usuario asociado, restableciendo el formulario a modo Auto.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita empezar una nueva carga manual desde cero.\n\n'
                '⚙️ FUNCIONAMIENTO: Resetea el lookup y además fuerza el tipo de vehículo a Auto.'
            ),
            "lookupNewResPatente": (
                '💡 LA IDEA: Es el identificador automático de conductores: al tipear la patente en caja, te dice al instante a qué cliente registrado pertenece.\n\n'
                '🎯 POR QUE FUE GENERADA: Vincula la reserva a la cuenta del usuario para que sume puntos y pueda ver su comprobante en su celular.\n\n'
                "⚙️ FUNCIONAMIENTO: Consulta /admin/reservations/patente-lookup con la patente (mínimo 4 caracteres): si el dueño está registrado vincula user_id, autocompleta tipo de vehículo y muestra el badge verde; si no, marca 'Patente no registrada'."
            ),
            "refreshNewResLiveDiscount": (
                '💡 LA IDEA: Es el asistente que busca si el cliente vinculado tiene algún descuento de puntos aplicable a esta reserva.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite al empleado ofrecer y aplicar el descuento de fidelización en el momento de tomar la reserva.\n\n'
                '⚙️ FUNCIONAMIENTO: Si hay usuario vinculado y no es edición, busca descuento vigente en /admin/redemptions/available para la sucursal y actualiza newResLiveDiscount con token anti-carrera; luego recalcula el precio.'
            ),
            "initNewResPatenteLookup": (
                '💡 LA IDEA: Es el sensor de tipeo que espera a que termines de escribir la patente para consultar al servidor sin demoras.\n\n'
                '🎯 POR QUE FUE GENERADA: Agiliza la búsqueda de clientes mientras se ingresa la patente en el mostrador.\n\n'
                '⚙️ FUNCIONAMIENTO: Engancha el evento input del campo patente con debounce de 450 ms para el lookup.'
            ),
            "openNewReservationModal": (
                '💡 LA IDEA: Es la apertura del formulario de reserva manual limpio y listo para cargar un nuevo turno por teléfono o en caja.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite asegurar una plaza a clientes presenciales precargando horarios y tarifas actualizadas.\n\n'
                '⚙️ FUNCIONAMIENTO: Prepara el modal para una reserva nueva: limpia estado, formulario y grilla, precarga fecha/hora actuales (tiempo virtual), carga sucursales desde /admin/branches, fija la sucursal propia del staff, inicializa tarifas, pickers y descuento, y abre el modal.'
            ),
            "setNewResModalMode": (
                '💡 LA IDEA: Es el camaleón que adapta títulos y botones según estés creando una reserva nueva o modificando una ya existente.\n\n'
                '🎯 POR QUE FUE GENERADA: Reutiliza el mismo formulario para altas y ediciones evitando duplicar código visual.\n\n'
                '⚙️ FUNCIONAMIENTO: Ajusta título, subtítulo y texto del botón según sea alta o edición.'
            ),
            "openEditReservationModal": (
                '💡 LA IDEA: Es la carga de una reserva existente en el formulario para cambiar fechas, horas o patente a pedido del cliente.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita corregir turnos calculando automáticamente si hay diferencias de dinero a favor o en contra.\n\n'
                '⚙️ FUNCIONAMIENTO: Reutiliza el modal de alta cargando una reserva existente: datos de patente y dueño, tipo de estadía y fechas según tipo, estado de pago (oculta método si ya pagó), descuento aplicado vía redemption-info y grilla horaria; recalcula precio.'
            ),
            "initNewReservationPickers": (
                '💡 LA IDEA: Es la puesta en marcha de los calendarios interactivos y selectores horarios del formulario de reservas manuales.\n\n'
                '🎯 POR QUE FUE GENERADA: Configura la selección de fechas en español con controles táctiles y botones de suma y resta de horas.\n\n'
                '⚙️ FUNCIONAMIENTO: Inicializa los flatpickr (fecha única, día, inicio de semana/quincena/mes con fin automático), listeners de cantidad de horas y grilla, botones +/- y el arrastre de chips; evita doble inicialización.'
            ),
            "updateNewFormGroups": (
                '💡 LA IDEA: Es el selector de campos que muestra horas para reservas cortas o calendarios de días para estadías largas.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra solo los campos relevantes para la modalidad que eligió el cliente en el mostrador.\n\n'
                '⚙️ FUNCIONAMIENTO: Muestra solo el bloque de campos del tipo de estadía elegido, muestra/oculta el grupo de fecha-hora, gestiona la grilla horaria y recalcula el precio.'
            ),
            "updateNewPeriodEnd": (
                '💡 LA IDEA: Es la calculadora de fecha final para reservas por semana o mes cerrando siempre a las 23:59.\n\n'
                '🎯 POR QUE FUE GENERADA: Calcula con exactitud el último día del turno sin que el cajero tenga que hacer cuentas a mano.\n\n'
                '⚙️ FUNCIONAMIENTO: Calcula y escribe la fecha de fin (23:59 del último día) a partir del inicio y la cantidad de días, y recalcula el precio.'
            ),
            "loadNewResRates": (
                '💡 LA IDEA: Es la descarga de las tarifas oficiales de la sucursal para calcular el costo de la reserva manual.\n\n'
                '🎯 POR QUE FUE GENERADA: Asegura que el personal de garita cobre exactamente las mismas tarifas autorizadas que figuran en la app.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga y cachea por sucursal las tarifas autoritativas desde /user/rates (misma fuente que el front de usuario); si ya están cacheadas solo recalcula.'
            ),
            "_newResRatesFor": (
                '💡 LA IDEA: Es el buscador de tarifas según el tamaño del vehículo (auto, moto o camioneta) y el tiempo contratado.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza que se aplique el valor correcto según el rodado que va a ingresar.\n\n'
                '⚙️ FUNCIONAMIENTO: Resuelve las tarifas por sucursal y tipo de vehículo: prioriza /user/rates (con sufijo _moto/_camioneta), cae a los tarifa_* del DTO de la sucursal y finalmente a valores por defecto; incluye horaBase y fracción de 30 min.'
            ),
            "updateNewReservationPrice": (
                '💡 LA IDEA: Es el cotizador en vivo del mostrador que calcula el total a cobrar aplicando posibles descuentos por puntos.\n\n'
                '🎯 POR QUE FUE GENERADA: Muestra el precio exacto en la pantalla de caja para informarle al conductor antes de cobrarle.\n\n'
                '⚙️ FUNCIONAMIENTO: Recalcula el total en vivo según tipo de estadía (hora con computeHourlyAmount, día/semana/quincena/mes por cantidad de períodos), aplica el descuento vigente si lo hay, guarda la foto de la cotización en newResQuote y muestra el monto con tachado del base cuando hay descuento.'
            ),
            "_newHourlySelectionSummary": (
                '💡 LA IDEA: Es el cartelito de confirmación horaria que indica la hora de inicio, fin y duración en la grilla de turnos.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda certeza visual al operador sobre el rango horario reservado.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el HTML del resumen de selección horaria: chips de INICIO y FIN con la duración entre ellos, o el hint inicial.'
            ),
            "updateNewHourlySlotsUI": (
                '💡 LA IDEA: Es la grilla de botoncitos de media hora que muestra qué franjas están libres u ocupadas para reservas por hora.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita el sobrecupo bloqueando los horarios en los que el estacionamiento ya no tiene plazas libres.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja la grilla de chips de 30 min para reservas por hora: consulta horarios deshabilitados (/user/reservations/disabled-hours, excluyendo la reserva en edición), bloquea horas pasadas o sin anticipación mínima de hoy, marca rango seleccionado y bordes de otras reservas, y avisa si no hay libres.'
            ),
            "selectNewHourRange": (
                '💡 LA IDEA: Es la selección de inicio y fin de reserva al cliquear los bloques de la grilla horaria.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite elegir el horario con un par de clics rápidos durante la atención en ventanilla.\n\n'
                '⚙️ FUNCIONAMIENTO: Selecciona inicio/fin al tocar un chip (sin drag): reinicia el rango si la hora es anterior al inicio o si ya había fin; luego confirma el rango.'
            ),
            "_newSlotCommitRange": (
                '💡 LA IDEA: Es el sincronizador que traslada las horas marcadas en la grilla a los campos de texto del formulario.\n\n'
                '🎯 POR QUE FUE GENERADA: Conecta la selección visual con los datos numéricos que se enviarán a la base de datos.\n\n'
                '⚙️ FUNCIONAMIENTO: Sincroniza el rango de chips con los inputs de hora de inicio y cantidad de horas, recalcula precio y re-renderiza la grilla.'
            ),
            "initNewHourSlotDrag": (
                '💡 LA IDEA: Es la selección por arrastre: hacés clic y deslizás el mouse para pintar todas las horas que el cliente desea reservar.\n\n'
                '🎯 POR QUE FUE GENERADA: Hace ultrarrápida la toma de turnos prolongados en garita.\n\n'
                '⚙️ FUNCIONAMIENTO: Implementa la selección por arrastre con pointer events sobre la grilla: pointerdown inicia (o reinicia) el rango, pointermove extiende el fin y pointerup/cancel confirma.'
            ),
            "handleAdminNewReservation": (
                '💡 LA IDEA: Es el cierre de la reserva manual: valida plazas disponibles, calcula el total final y envía el turno al servidor.\n\n'
                '🎯 POR QUE FUE GENERADA: Garantiza un registro ordenado del turno y habilita la patente en las barreras para cuando llegue el conductor.\n\n'
                '⚙️ FUNCIONAMIENTO: Submit del formulario: valida patente y sucursal, arma inicio/fin según tipo, verifica disponibilidad, arma el payload con la cotización (tarifas), gestiona alta con pago o edición; al editar una reserva pagada abre el modal de resumen de diferencia (cobro/reembolso), y al crear puede aplicar descuento de canje tras confirmación. Delega el envío en _submitReservationPayload.'
            ),
            "confirmEditResumoProceed": (
                '💡 LA IDEA: Es la confirmación de diferencias económicas al editar una reserva previa (liquidando cobros extra o reembolsos).\n\n'
                '🎯 POR QUE FUE GENERADA: Mantiene las cuentas claras cuando un cliente cambia de horario y se genera una diferencia de tarifa.\n\n'
                '⚙️ FUNCIONAMIENTO: Confirma el modal de diferencia: agrega al payload el método de cobro o reembolso según corresponda, cierra el modal y envía.'
            ),
            "cancelEditResumo": (
                '💡 LA IDEA: Es el descarte de las modificaciones pendientes, cerrando la ventana de diferencia de tarifa sin tocar la reserva original.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite arrepentirse de una edición si el cliente no está de acuerdo con la diferencia a pagar.\n\n'
                '⚙️ FUNCIONAMIENTO: Descarta la edición pendiente y cierra el modal de resumen de diferencia.'
            ),
            "_submitReservationPayload": (
                '💡 LA IDEA: Es el envío definitivo de la reserva manual hacia el backend con bloqueo momentáneo del botón para evitar dobles clics.\n\n'
                '🎯 POR QUE FUE GENERADA: Previene la duplicación de turnos y actualiza el listado de reservas inmediatamente tras la confirmación.\n\n'
                '⚙️ FUNCIONAMIENTO: Envía el payload (PUT en edición, POST en alta) con el botón en estado procesando; al éxito muestra toast según acción (cobro/reembolso), resetea el modal a modo alta, cierra y recarga la lista de reservas.'
            ),
        },
    },
    "static/js/modules/reservations-admin-list.js": {
        "proposito": 'Listado administrativo de reservas: tabla paginada con búsqueda y filtros de estado, pago manual con descuento de canje, cancelación, detalle, y badge de reservas nuevas en el sidebar basado en last-seen persistido por rol/sucursal.',
        "simbolos": {
            "getAllReservations": (
                '💡 LA IDEA: Es la memoria de reservas en el panel que entrega la lista de turnos cargados sin volver a pedirlos a la red.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite abrir la edición de cualquier reserva al instante con sus datos ya descargados.\n\n'
                '⚙️ FUNCIONAMIENTO: Devuelve el array cacheado de reservas (lo consume el formulario de edición).'
            ),
            "loadAdminReservations": (
                '💡 LA IDEA: Es el libro de reservas del estacionamiento: descarga todos los turnos, actualiza las alertas y calcula los totales del día.\n\n'
                '🎯 POR QUE FUE GENERADA: Otorga al personal de garita la nómina completa de vehículos esperados para organizar el espacio.\n\n'
                '⚙️ FUNCIONAMIENTO: Carga /admin/reservations con filtro de estado, cachea el resultado, actualiza el last-seen del badge si corresponde, renderiza filas y calcula los KPIs (total, pendientes y activas hoy con fechas solapadas usando tiempo virtual).'
            ),
            "renderAdminReservationRows": (
                '💡 LA IDEA: Es la planilla de turnos con nombres, patentes, horarios, badges de pago y botones de cobrar o cancelar.\n\n'
                '🎯 POR QUE FUE GENERADA: Presenta las reservas de forma clara y con paginación de a 10 elementos para un trabajo diario ágil.\n\n'
                '⚙️ FUNCIONAMIENTO: Dibuja las filas del listado (cliente, patente, fechas, tipo, monto neto de reembolsos, badges de pago/reserva con indicador EN PREDIO/FUERA y acciones editar/pago/cancelar según estado y origen manual), con búsqueda y paginación de 10 por página.'
            ),
            "onAdminResSearch": (
                '💡 LA IDEA: Es el buscador de reservas por patente del auto o nombre del conductor.\n\n'
                '🎯 POR QUE FUE GENERADA: Permite encontrar la reserva de una persona que llega a la garita en una fracción de segundo.\n\n'
                '⚙️ FUNCIONAMIENTO: Aplica la búsqueda por patente o nombre del cliente: resetea paginación y re-renderiza.'
            ),
            "payReservationAdmin": (
                '💡 LA IDEA: Es el cobro manual de una reserva en caja física: permite cobrar en efectivo, aplicar cupones de descuento y marcarla como pagada.\n\n'
                '🎯 POR QUE FUE GENERADA: Facilita cobrar a clientes que pagan en el mostrador dejando el turno confirmado en el sistema.\n\n'
                '⚙️ FUNCIONAMIENTO: Pago manual de una reserva: elige método, consulta descuentos aplicables (/admin/reservations/{id}/redemptions), pregunta si aplicar uno y confirma el pago con el ticket de canje elegido vía /confirm-payment.'
            ),
            "cancelReservationAdmin": (
                '💡 LA IDEA: Es la anulación administrativa de una reserva con confirmación previa.\n\n'
                '🎯 POR QUE FUE GENERADA: Libera la plaza reservada para que pueda ser aprovechada por otros conductores.\n\n'
                '⚙️ FUNCIONAMIENTO: Cancela una reserva tras confirmación vía /admin/reservations/{id}/cancel y recarga la lista.'
            ),
            "showReservationDetail": (
                '💡 LA IDEA: Es la ficha completa de la reserva con importes detallados, fecha de cobro y registro de si el auto ya ingresó al predio.\n\n'
                '🎯 POR QUE FUE GENERADA: Brinda total claridad para responder dudas de clientes o realizar auditorías operativas.\n\n'
                '⚙️ FUNCIONAMIENTO: Llena el modal de detalle con los datos de la reserva (importes netos, nota de reembolso, badges de estado y presencia en predio) y lo abre.'
            ),
            "getStorageKey": (
                '💡 LA IDEA: Es la etiqueta de memoria que aísla las alertas de reservas nuevas según la sucursal y el rol del operador.\n\n'
                '🎯 POR QUE FUE GENERADA: Evita que un empleado de una sede vea notificaciones de reservas que corresponden a otra playa de estacionamiento.\n\n'
                '⚙️ FUNCIONAMIENTO: Clave de localStorage para el last-seen del badge, compuesta por rol y sucursal para aislar cada vista.'
            ),
            "updateReservationBadge": (
                '💡 LA IDEA: Es el globo de alerta que avisa cuántas reservas nuevas ingresaron desde la última vez que miraste la pantalla.\n\n'
                '🎯 POR QUE FUE GENERADA: Informa de inmediato al cajero sobre nuevas contrataciones sin obligarlo a recargar la página.\n\n'
                '⚙️ FUNCIONAMIENTO: Actualiza el badge de reservas nuevas del sidebar cada 10 s: si el usuario está en la pestaña de reservas lo oculta y registra latest_id; si nunca vio reservas inicializa el last-seen; si no, consulta el count desde ese id y muestra/oculta el badge con pulse.'
            ),
            "clearReservationBadge": (
                '💡 LA IDEA: Es el apagado del globo de alertas apenas el operador entra a mirar la pestaña de reservas.\n\n'
                '🎯 POR QUE FUE GENERADA: Limpia las novedades pendientes reconociendo que el personal ya tomó nota de las nuevas reservas.\n\n'
                '⚙️ FUNCIONAMIENTO: Oculta el badge y sincroniza el last-seen con el latest_id del servidor (llamado al entrar a la pestaña de reservas).'
            ),
        },
    },
}
