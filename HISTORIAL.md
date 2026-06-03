# HISTORIAL DEL PROYECTO: AUTOPASS

- **JUNIO 03, 2026 - GESTIÓN AVANZADA & MAPA INTERACTIVO (V7.8.0)**:
  - **GESTIÓN DE USUARIOS**:
    - IMPLEMENTACIÓN DE EDICIÓN DE PERFILES DESDE EL PANEL DE ADMINISTRACIÓN.
    - SOPORTE PARA CAMBIO DE ROLES Y SUCURSALES CON RESTRICCIONES DE SEGURIDAD RBAC.
    - NORMALIZACIÓN AUTOMÁTICA DE DNI (ELIMINACIÓN DE PUNTOS/ESPACIOS).
  - **INTERACTIVIDAD DEL MAPA**:
    - IMPLEMENTACIÓN DE "HEAT MAP" DE DISPONIBILIDAD (COLORES DORADO/NARANJA/ROJO).
    - BOTÓN DE GEOLOCALIZACIÓN PARA BUSCAR SUCURSAL MÁS CERCANA (ALGORITMO HAVERSINE).
    - FLUJO DE "RESERVA ONE-CLICK" DESDE EL MARCADOR DEL MAPA AL PERFIL DEL USUARIO.
  - **CORRECCIONES TÉCNICAS**:
    - FIX: BUG DE DNI DUPLICADO EN `init_db.py` QUE BLOQUEABA INSTALACIONES NUEVAS.
    - FIX: NORMALIZACIÓN DE EMAIL EN LOGIN PARA EVITAR SENSIBILIDAD A MAYÚSCULAS.
    - FIX: ERROR DE SELECTORES EN FORMULARIO DE RESERVAS (TYPEERROR VALUE).

- **JUNIO 02, 2026 - TERMINOLOGY UNIFICATION & PREMIUM UX (V7.7.0)**:
  - **MIGRACIÓN DE LENGUAJE**:
    - SE REEMPLAZÓ EL TÉRMINO "SEDE" POR **"SUCURSAL"** EN TODO EL PROYECTO (UI, DOCUMENTACIÓN, MENSAJES).
  - **GEOLOCALIZACIÓN Y MAPAS**:
    - IMPLEMENTACIÓN DE COORDENADAS (LAT/LNG) PARA SUCURSALES.
    - CREACIÓN DE SELECTOR DE MAPA INTERACTIVO (LEAFLET PICKER) EN EL PANEL ADMIN.
    - INTEGRACIÓN DE BUSCADOR DE DIRECCIONES (GEOCALIZACIÓN) VÍA API NOMINATIM.
    - MAPA DE LANDING DINÁMICO: AHORA CONSUME LA API PÚBLICA DE SUCURSALES EN TIEMPO REAL.
  - **NOTIFICACIONES (TOASTS)**:
    - REFACTORIZACIÓN COMPLETA A ESTILO **GLASSMORPHISM**.
    - CAMBIO DE UBICACIÓN A TOP-RIGHT Y ADICIÓN DE ICONOGRAFÍA DINÁMICA.
  - **UI/UX HARDENING**:
    - IMPLEMENTACIÓN DE SCRIPT INLINE PARA ELIMINAR EL "FLICKER" DE CONTENIDO NO AUTORIZADO AL CARGAR EL DASHBOARD.
    - REDISEÑO DE FORMULARIOS DE SUCURSAL CON LOGOS CIRCULARES Y SELECTORES DE HORARIO SIMPLIFICADOS.
    - ELIMINACIÓN DE ELEMENTOS COLAPSABLES EN GESTIÓN DE USUARIOS PARA MEJORAR LA VELOCIDAD DE OPERACIÓN.
  - **LÓGICA DE NEGOCIO**:
    - LAS PROMOCIONES AHORA CARGAN SUCURSALES DINÁMICAMENTE DESDE LA DB (ELIMINANDO HARDCODING).
    - RESTRICCIÓN DE CREACIÓN DE PROMOCIONES PARA ADMINS LOCALES BLOQUEADA A SU PROPIA SUCURSAL.

- **JUNIO 01, 2026 - ALPR ENGINE UPGRADE & UI HARDENING (V7.6.0)**:
  - **MOTOR ALPR (IA)**:
    - INTEGRACIÓN DE PROCESAMIENTO ASINCRÓNICO MEDIANTE COLAS DE PRIORIDAD (QUEUE).
    - IMPLEMENTACIÓN DE PRE-PROCESAMIENTO CON OPENCV (GRAYSCALE, GAUSSIAN BLUR, CLAHE, ADAPTIVE THRESHOLD).
    - DESARROLLO DE ALGORITMO DE CONSENSO POR VOTACIÓN PARA ELIMINAR FALSOS POSITIVOS.
    - OPTIMIZACIÓN POR REGIÓN DE INTERÉS (ROI) PARA REDUCIR CARGA DE CPU.
  - **HARDENING DE INTERFAZ**:
    - REFACTORIZACIÓN DE INICIALIZACIÓN DE DASHBOARD PARA CARGA RESILIENTE DE CARGOS Y SUCURSALES.
    - ETIQUETAS DINÁMICAS EN CABECERA: "ADMINISTRADOR [SUCURSAL]" O "EMPLEADO [SUCURSAL]".
    - CORRECCIÓN DE BUG DE PERSISTENCIA DE SUCURSAL EN LOGIN Y STORAGE.
  - **GESTIÓN DE USUARIOS**:
    - RESTRICCIÓN DE ALTA DE USUARIOS PARA ADMINS LOCALES (SOLO STAFF/ADMIN DE SU PROPIA SUCURSAL).
    - FILTRADO DE CLIENTES EN LA LISTA PARA ADMINISTRADORES DE PUNTO.

- **JUNIO 2026 - MULTI-SUCURSAL ISOLATION & RBAC HARDENING (V7.5.0)**:
  - **AISLAMIENTO DE SUCURSALES**:
    - IMPLEMENTACIÓN DE FILTRADO ESTRICTO POR `sucursal` EN DASHBOARD PARA `local_admin` Y `staff`.
    - REFACTORIZACIÓN DE ENDPOINTS DE ESTADO, OCUPACIÓN Y REPORTES PARA SER "BRANCH-AWARE".
    - VALIDACIÓN DE ACCESO ALPR Y QR AHORA VERIFICA LA SUCURSAL CORRESPONDIENTE, EVITANDO CRUCE DE DATOS.
  - **SEGURIDAD Y RBAC**:
    - RESTRICCIÓN TOTAL DE MÓDULOS SENSIBLES (USUARIOS, FINANZAS, SETTINGS) PARA EL ROL `staff`.
    - OCULTAMIENTO DE FUNCIONES CRÍTICAS (RESET SISTEMA, AUDITORÍA GLOBAL) PARA `local_admin`.
    - ACTUALIZACIÓN DINÁMICA DE INTERFAZ SEGÚN EL ROL AUTENTICADO.
  - **SISTEMA DE TARIFAS DINÁMICAS**:
    - LAS RESERVAS DE CLIENTES AHORA CARGAN TARIFAS EN TIEMPO REAL SEGÚN EL PUNTO AUTOPASS ELEGIDO.
    - CORRECCIÓN DE BUG EN MATCHING DE SUCURSALES (USO DE NOMBRES COMPLETOS EN LUGAR DE TRUNCADOS).
    - LÓGICA DE FALLBACK A TARIFAS GLOBALES SOLO CUANDO NO EXISTEN PRECIOS ESPECÍFICOS DE SUCURSAL.

- **MAYO 2026 - AUTOMATION & ROBUSTNESS (V7.4.1)**:
  - **SCRIPTS DE AUTOMATIZACIÓN**:
  - CREACIÓN DE `run_alpr_entrada.bat` Y `run_alpr_salida.bat` PARA FACILITAR EL TESTEO CON IP WEBCAM.
  - OPTIMIZACIÓN DE `run_server.bat` USANDO EL MÓDULO `python -m uvicorn` PARA EVITAR CONFLICTOS DE PATH.
  - **DOCUMENTACIÓN CORE**:
  - GENERACIÓN DE `FUNCIONALIDADES_CORE.md` CON EL DETALLE TÉCNICO DE LOS 4 PILARES DEL SISTEMA.

- **MAYO 2026 - UI/UX PREMIUM REFACTOR (V7.4.0)**:
  - **REFACCIÓN DASHBOARD ADMINISTRATIVO**:
  - UNIFICACIÓN DE PESTAÑA CONFIGURACIÓN: TARIFAS Y CAPACIDAD EN UNA SOLA VISTA COMPACTA (800PX).
  - ELIMINACIÓN DE COMPONENTES COLAPSABLES EN FAVOR DE ACCESO DIRECTO.
  - INTEGRACIÓN BACKEND COMPLETA PARA PERSISTENCIA DE CAPACIDAD EN `ParkingAforo`.
  - SIMPLIFICACIÓN DE GESTIÓN DE PROMOCIONES CON NUEVA TABLA DE 4 COLUMNAS Y BOTONES DE ELIMINACIÓN INTELIGENTES (HOVER-ONLY).
  - **EVOLUCIÓN HUB DE CUENTA (USUARIO)**:
  - REDISEÑO DEL ÁREA DE SEGURIDAD CON GRILLA 2X2 PARA VALIDACIONES DE CONTRASEÑA.
  - ESTANDARIZACIÓN DE LÍNEAS DIVISORIAS CON GRADIENTE DORADO EN TODO EL PERFIL.
  - AJUSTE DE ESPACIADOS INTERNOS (GAP 30PX) Y ALINEACIÓN VERTICAL BALANCEADA.
  - **OPTIMIZACIÓN DE USABILIDAD Y BUGS**:
  - REPOSICIONAMIENTO DE BOTONES DE ACCIÓN EN TARJETAS VEHICULARES (ESQUINA SUPERIOR DERECHA).
  - REPARACIÓN DEL COLAPSO DEL SIDEBAR (SINCRONIZACIÓN JS/CSS).
  - RESTAURACIÓN DE FUNCIONALIDADES GLOBALES PARA REGISTRO RÁPIDO DE VEHÍCULOS.

- **MAYO 2026 - EMAIL SERVICE & SECURITY RECOVERY (V7.3.0)**:
  - **SISTEMA DE NOTIFICACIONES**:
  - IMPLEMENTACIÓN DE `EmailService` CON SOPORTE PARA ENVÍOS ASÍNCRONOS (MULTITHREADING).
  - INTEGRACIÓN DE GENERACIÓN DE CÓDIGOS QR EN EL SERVIDOR PARA PASES DIGITALES VÍA EMAIL.
  - DISEÑO DE PLANTILLAS PREMIUM HTML (RESPONSIVE) CON ESTÉTICA FIEL A LA WEB.
  - **RECUPERACIÓN DE CUENTAS**:
  - DESARROLLO DEL FLUJO "FORGOT PASSWORD" CON TOKENS JWT DE UN SOLO USO.
  - CREACIÓN DE LA PÁGINA `reset_password.html` CON VALIDACIONES DE SEGURIDAD EN TIEMPO REAL.
  - **INFRAESTRUCTURA**:
  - CONFIGURACIÓN CENTRALIZADA DE SMTP EN `core/config.py` Y VARIABLES DE ENTORNO.
  - ACTUALIZACIÓN DE `ReservationService` PARA DISPARAR MAILS DE CONFIRMACIÓN AL ABONAR.

- **SISTEMA DE INSTALACIÓN**:
  - **Refactor de `init_db.py`**: El script de inicialización ahora es un "Todo-en-Uno" que maneja la creación de tablas, migraciones automáticas y seeding de datos.
  - **Migraciones Automáticas**: Implementación de lógica de detección de columnas faltantes para SQLite; el sistema ahora se actualiza solo al correr `init_db.py`.
  - **Seeding de Datos Maestros**: Creación automática del usuario Administrador Global (`admin@autopass.com`), tarifas base, capacidad del predio y catálogo inicial de promociones.
  - **Robustez**: Se eliminó la dependencia de scripts de mantenimiento manuales dispersos.

## 22 DE MAYO, 2026 - UI REFINEMENTS: PROMOTIONS & SECURITY HUB (V7.2.5)
- **MIS PUNTOS**:
  - **Restauración UI de Promociones**: Implementación completa de CSS para la grilla de beneficios (`promotions-grid`).
  - **Tarjetas Premium**: Diseño de `promo-card` con Glassmorphism (desenfoque de fondo), bordes dorados y elevación dinámica (hover).
  - **Iconografía & Tipografía**: Integración de iconos en contenedores circulares y destaque de costos en Montserrat 900.
- **MI CUENTA**:
  - **Compactación de Seguridad**: Reducción del ancho máximo del formulario de cambio de contraseña (`max-width: 320px`) para un diseño más elegante y centrado.
  - **Refinamiento de Requerimientos**: Transición de la caja de validación a un flujo vertical más legible y estético.
  - **Limpieza de Código**: Eliminación de estilos inline en `cuenta.html` delegando toda la responsabilidad al sistema modular de CSS.

## 22 DE MAYO, 2026 - UI REFINEMENTS & LOCAL ADMIN ACCESS FIX (V7.2.4)
- **DASHBOARD ADMINISTRATIVO**:
  - **Ajuste de Columnas**: Ensanchamiento de la columna de "Patente" (`min-width: 110px`) en todas las tablas administrativas (Reservas, Monitoreo, Finanzas, Ocupación).
  - **Integridad de Patentes**: Aplicación de `white-space: nowrap` a la clase `.plate-style` para evitar rupturas de línea en identificadores de vehículos.
  - **Limpieza de Consola**: Eliminación de logs de depuración innecesarios (`console.log`) en la carga de usuarios para un entorno de producción más limpio.
- **PORTAL DE USUARIO (RESERVA)**:
  - **Alineación de Formulario**: Reajuste del layout de "Nueva Reserva" en el perfil; ahora los selectores (Vehículo, Punto, Estadía) se alinean a la izquierda y ocupan el ancho total de su columna.
  - **Refinamiento de Labels**: Etiquetas alineadas a la izquierda para una lectura más natural.
- **OPTIMIZACIÓN RESPONSIVA**:
  - **Corrección de Misalignment**: Implementación de media query a 992px para apilar los campos de reserva en una sola columna, evitando desajustes visuales en tablets y móviles.
  - **Estado Hover en Móvil**: Fix para el botón "Confirmar Reserva"; ahora mantiene su color dorado en touch-devices, evitando que se vuelva blanco por el hover persistente.
- **SEGURIDAD & ACCESO**:
  - **FIX: Redirección de Local Admin**: Se corrigió el error que enviaba a los Administradores de Sede al portal de cliente.
  - **Dashboard Gatekeeper**: Actualización del script de seguridad inline en `dashboard.html` para autorizar explícitamente al rol `local_admin`.
  - **Navegación Dinámica**: Sincronización de IDs en `navbar.html` para permitir que el JS actualice correctamente el enlace de perfil según el rol administrativo detectado.
  - **Dashboard Bridge**: Inclusión de `local_admin` en la lógica de inicialización de pestañas restringidas.

## 22 DE MAYO, 2026 - PROMOTIONS SYSTEM & TOTAL RESPONSIVE (V7.2.3)
- **SISTEMA DE PROMOCIONES**:
  - Implementación de **Promociones por Sede**: Los beneficios ahora están vinculados a sucursales específicas (Castelar, Morón, Ituzaingó) o nivel Global.
  - Backend: Actualización de modelos, esquemas y rutas administrativas para soportar aislamiento de beneficios por área.
  - **Selector Visual de Íconos**: Interfaz interactiva en el dashboard para elegir iconos premium mediante cuadrícula en lugar de texto manual.
  - Filtrado de Usuario: Los clientes solo visualizan beneficios de su sede asignada o promociones globales.
- **OPTIMIZACIÓN RESPONSIVA (MOBILE FIRST)**:
  - Implementación de **Responsive Card Layout**: Transformación automática de tablas (Reservas, Usuarios, Promociones) en tarjetas individuales en celulares y tablets (< 992px).
  - Navegación Móvil Refinada: Sidebar deslizable con botón de hamburguesa y overlay de desenfoque para una experiencia tipo App nativa.
  - Sincronización de Etiquetas: Uso de atributos `data-label` para mantener nombres de columnas visibles a la izquierda de los valores en modo tarjeta.
  - Ajuste de Grillas: Transición de monitoreo y finanzas de multi-columna a flujo vertical simple en dispositivos pequeños.
- **GESTIÓN DE USUARIOS REFINADA**:
  - **Aislamiento de Datos por Rol**: Se ocultan los campos de "Puntos" y "Saldo" (`---`) para roles internos (Admin, Local Admin, Staff) para limpiar la interfaz.
  - **Resaltado Financiero**: Aplicación de color verde esmeralda (`text-success`) exclusivo para el saldo de clientes, facilitando su identificación.
  - **Filtro Avanzado por Rol**: Adición de selector de roles (Clientes, Empleados, etc.) que trabaja en conjunto con la búsqueda por texto.
  - Reubicación del botón "NUEVO USUARIO" para equilibrio visual en escritorio y accesibilidad en móvil.
- **LIMPIEZA DE UI & UX**:
  - Ajuste de espaciado agresivo en el Registro de Reservas: Mayor separación vertical y líneas divisorias sutiles entre fechas.
  - Centrado absoluto de todas las tablas de monitoreo y gestión para eliminar desplazamientos laterales.
  - Fix de sintaxis CSS en `tables.css` para restaurar la integridad del diseño en pantallas retina y móviles.

## 21 DE MAYO, 2026 - UNIFIED ACCOUNT HUB & PAGINATED POINTS (V7.2.2)
- **MI CUENTA**:
  - Implementación del **Unified Account Surface**: Se unificaron los datos personales y el cambio de contraseña en una sola tarjeta premium de doble panel.
  - Se eliminaron los menús desplegables para una gestión más directa y fluida.
  - Alineación simétrica total: Columnas de iconos perfectamente alineadas y centrado de contenido en toda la pestaña.
  - Optimización de inputs: Ancho calibrado para contraseñas de 20+ caracteres y modo edición ultracompacto.
  - Se añadió una línea divisoria vertical para separar visualmente la información de la seguridad.
- **MIS PUNTOS**:
  - Implementación de **Paginación en Historial**: Navegación dinámica (10 por página) para mejorar el rendimiento y la legibilidad.
  - Backend: Actualización del endpoint de puntos para devolver totales históricos y datos paginados.
  - Centrado visual de las tarjetas de puntos acumulados, canjeados y disponibles.
  - Colores dinámicos para totales: Verde para acumulado, rojo para canjeado y dorado para disponible.
- **ESTABILIDAD JS**:
  - Se restauraron las referencias globales al objeto `window` para todas las funciones críticas de perfil y navegación.
  - Activación de validaciones de contraseña en tiempo real en la pestaña de cuenta.

## 21 DE MAYO, 2026 - PERFECCIONAMIENTO UI/UX PERFIL (V7.2.1)
- **MIS RESERVAS & PUNTOS**:
  - Rediseño de tarjetas de estadísticas: Iconos alineados horizontalmente con valores numéricos y leyendas centradas.
  - Eliminación de comportamiento colapsable en Historiales (Reservas y Puntos) para visibilidad directa.
  - Implementación de `.card-narrow` (600px) para compactar y centrar listados de historial, eliminando espacios muertos.
  - Restauración de colores dinámicos en Historial de Puntos (Verde para sumas, Rojo para canjes).
  - Centrado absoluto de encabezados, subtítulos y cuadrículas de contenido para mayor armonía visual.
- **PASE DIGITAL & MODALES**:
  - Fix estructural de `modal-premium`: Se corrigió posicionamiento (ahora flotante y centrado con desenfoque de fondo).
  - Restauración estética de Ticket Digital: Perforaciones, recortes circulares, tipografía monoespaciada y sección de QR.
  - Adición de botón de cierre (`fas fa-times`) integrado dentro del diseño del ticket para mejor accesibilidad.
- **INTEGRIDAD DE FORMULARIOS**:
  - Unificación de clases `.input-premium-sm` en edición de cuenta para consistencia estética total.
  - Exposición de funciones JS críticas a nivel global para asegurar interactividad en todas las pestañas.

## 21 DE MAYO, 2026 - MODULARIZACIÓN CSS & UI REFINED (V7.2.0)
- **ARQUITECTURA FRONTEND**:
  - Modularización completa del sistema de estilos: División en `base/`, `components/`, `layout/` y `pages/`.
  - Unificación del Header global y Sidebar responsiva con soporte para dashboard y portal.
  - Creación de `static/css/base/utilities.css` para centralizar clases de layout y espaciado.
- **OPTIMIZACIÓN DE PERFIL**:
  - Consolidación de 5 archivos de perfil en `pages/profile.css`.
  - Rediseño de la sección de **Vehículos**: Barra de herramientas estática y tarjetas con fondo difuminado.
  - Restauración de animaciones de reserva y medidores de seguridad de contraseña.
  - Ajuste de jerarquía visual: Eliminación de labels redundantes en tarjetas de flota.
- **REFACTORIZACIÓN DE LAYOUT**:
  - Extracción de lógica estructural a `layout/grid.css` y `layout/sidebar.css`.
  - Implementación de contenedor dinámico para la lista de vehículos (crecimiento horizontal).

## 21 DE MAYO, 2026 - OPTIMIZACIÓN DASHBOARD & REPORTES (V7.1.0)
- **GESTIÓN DE USUARIOS**:
  - Implementación de cambio de contraseña administrado con validación de seguridad.
  - Ordenamiento jerárquico de lista (Admin > Staff > User) con orden alfabético interno.
  - Refactor visual: Eliminación de iniciales innecesarias y agregado de colores dinámicos por rol.
  - Acción de hover para botones de gestión (limpieza visual).
- **ANALÍTICA FINANCIERA**:
  - Motor de recaudación unificado: Integración de ingresos por Reservas Anticipadas y Estadías ALPR.
  - Reparación del motor de reportes: Sincronización de `fecha_pago` para precisión cronológica.
  - Implementación de Gráfico de Tendencia con **Chart.js** (estética Gold AutoPass).
- **GESTIÓN DE RESERVAS**:
  - Corrección de mapeo de nombres de clientes (eliminación de 'undefined').
  - Normalización de textos (Capitalización de tipos de estadía).
  - Refactor de esquemas Pydantic para soporte de datos de usuario extendidos.
- **EXPERIENCIA DE USUARIO (UX)**:
  - Agregado de etiquetas informativas (`title`) en todos los elementos interactivos del dashboard.
  - Implementación de cuadros de confirmación con resúmenes detallados para acciones críticas (Pagos, Tarifas, Reseteos).
  - Mejora en la visualización de detalles: Separación de modales para Eventos ALPR y Reservas.
- **SEGURIDAD & PERSISTENCIA**:
  - Corrección de redirección automática en errores de login (permite ver mensajes de error).
  - Validación de persistencia de sesión en navegación por historial (flechas del navegador).
  - Migración de base de datos para soporte de trazabilidad de pagos (`fecha_pago`).

## 19 DE MAYO, 2026 - ARQUITECTURA MODULAR V7.0 (LA GRAN REFACTORIZACIÓN)
- **INFRAESTRUCTURA CORE**:
  - Creación del paquete `core/` centralizando Configuración, Seguridad (JWT/RBAC), Base de Datos y MQTT.
  - Eliminación de archivos `auth.py` y `database.py` de la raíz para evitar dispersión de lógica.
- **MODULARIZACIÓN DE DATOS**:
  - División de `models.py` en `models/user.py`, `models/parking.py` y `models/reservation.py`.
  - División de `schemas.py` siguiendo el mismo patrón de dominios.
- **LIMPIEZA DE ENTRY POINT**:
  - `main.py` refactorizado para ser solo un orquestador de arranque.
  - Extracción de todas las rutas de vistas HTML a `routes/views.py`.
  - Creación de `services/worker_service.py` para manejar tareas de fondo de forma ordenada.
- **FRONTEND MODULAR (JS, TABS & COMPONENTS)**:
  - Modularización completa del JavaScript utilizando **ES6 Modules**.
  - Creación de `static/js/modules/` (api.js, utils.js, ui.js, auth.js, etc.) para eliminar la dependencia del ámbito global.
  - El archivo `perfil.html` (~1200 líneas) fue descuartizado en componentes manejables bajo `templates/profile/tabs/`.
  - Unificación del Header global en `templates/components/navbar.html`.
  - Extracción de sistemas de Toasts y Modales globales a `templates/components/modals_global.html`.
- **ALINEACIÓN DE TESTS**:
  - Actualización de toda la suite de pruebas (`test_*.py`) para ser compatible con la nueva estructura modular.
  - Incorporación de `httpx` y `pytest` como dependencias de validación.

## 18 DE MAYO, 2026 - SOPORTE MULTI-SEDE & RBAC (V6.4.0)
- **INFRAESTRUCTURA MULTI-SUCURSAL**:
  - SE AÑADIÓ EL CAMPO `sucursal` A LOS MODELOS DE USUARIOS, LOGS DE ACCESO, CONFIGURACIONES Y RESERVAS.
... [RESTO DEL HISTORIAL PREVIO SE MANTIENE IGUAL] ...
