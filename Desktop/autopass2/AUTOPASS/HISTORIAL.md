# HISTORIAL DEL PROYECTO: AUTOPASS

## 📅 18 DE MAYO, 2026 - SOPORTE MULTI-SEDE & RBAC DESCENTRALIZADO (V6.4.0)
- **INFRAESTRUCTURA MULTI-SUCURSAL**:
    - SE AÑADIÓ EL CAMPO `sucursal` A LOS MODELOS DE USUARIOS, LOGS DE ACCESO, CONFIGURACIONES Y AFORO.
    - SE IMPLEMENTÓ LA CAPACIDAD DE TENER PRECIOS INDEPENDIENTES POR PUNTO AUTOPASS.
- **SEGURIDAD Y ROLES**:
    - NUEVOS ROLES: `local_admin` (ADMINISTRADOR DE SEDE) Y `staff` (EMPLEADO OPERATIVO).
    - AISLAMIENTO TOTAL: LOS ROLES LOCALES SÓLO TIENEN ACCESO A LA DATA DE SU SEDE ASIGNADA.
    - EL ROL `admin` EVOLUCIONÓ A **SUPER-ADMINISTRADOR GLOBAL** CON CONTROL TOTAL.
- **INTERFAZ DE ADMINISTRACIÓN**:
    - SE ACTUALIZÓ EL MODAL DE CREACIÓN DE USUARIOS PARA PERMITIR LA VINCULACIÓN A SUCURSALES.
    - LOS DASHBOARDS SE FILTRAN AUTOMÁTICAMENTE SEGÚN LA PERTENENCIA DEL USUARIO.

## 📅 18 DE MAYO, 2026 - REFACTORIZACIÓN OPERATIVA, SEGURIDAD & BUGFIXES (V6.3.4)
- **POLÍTICAS DE RESERVA**:
    - **ANTICIPACIÓN MÍNIMA**: SE ESTABLECIÓ UNA REGLA DE 2 HORAS DE ANTELACIÓN PARA CREAR RESERVAS (EVITA SATURACIÓN DE ÚLTIMO MOMENTO).
    - **FIX CANCELACIÓN AGRESIVA**: SE AMPLIÓ EL MARGEN DE GRACIA A 2 HORAS PARA EVITAR QUE EL SISTEMA CANCELE RESERVAS RECIÉN CREADAS.
- **GESTIÓN DE ROLES (RBAC)**:
    - **PERMISOS STAFF**: EL ROL EMPLEADO AHORA TIENE ACCESO COMPLETO AL MONITOREO (ÚLTIMOS MOVIMIENTOS Y CAPTURAS).
    - **ROBUSTEZ DASHBOARD**: SE IMPLEMENTARON CHEQUEOS DE DOM Y PERMISOS PARA EVITAR CRASHES DE JS EN EL ADMIN.
- **COMMAND CENTER 2.5 (UX FINAL)**:
    - **MODAL DE EVENTO**: REFACTORIZACIÓN TOTAL CON TÍTULO DORADO, PLACEHOLDERS PARA IMÁGENES FALTANTES Y ETIQUETAS MINIMALISTAS.
    - **LOCALIZACIÓN**: CAMBIO DE "VEHÍCULOS EN PLAYA" A "VEHÍCULOS ESTACIONADOS" PARA MEJOR SEMÁNTICA.
    - **SIDEBAR**: REORDENAMIENTO FINAL PRIORIZANDO CAPACIDAD > OPERACIÓN > SALUD.

## 📅 17 DE MAYO, 2026 - EVOLUCIÓN COMMAND CENTER & LÓGICA DE NEGOCIO (V6.2)
- **MODELO DE PAGO MANUAL**: SE DESACTIVÓ EL COBRO AUTOMÁTICO DE RESERVAS. AHORA TODAS INICIAN COMO "PENDIENTE", DANDO CONTROL TOTAL AL USUARIO SOBRE SU SALDO.
- **REDISEÑO MONITORÉO DASHBOARD**: 
    - SE ELIMINÓ EL TEXTO "EN VIVO" REEMPLAZÁNDOLO POR UN CÍRCULO TITILANTE MINIMALISTA.
    - SE RENOMBRARON LAS CÁMARAS A "ENTRADA" Y "SALIDA" CON ALINEACIÓN HORIZONTAL.
    - SE AGREGÓ UN FILTRO DE BÚSQUEDA POR PATENTE EN TIEMPO REAL EN LA TABLA DE MOVIMIENTOS.
    - ACTUALIZACIÓN DE ICONOGRAFÍA: CAMBIO DE CANDADO POR BARRERA (`FA-ROAD-BARRIER`).
- **OPTIMIZACIÓN ALPR HÍBRIDO**: 
    - EL SERVICIO AHORA DETECTA CÓDIGOS QR ADEMÁS DE PATENTES.
    - REDUCCIÓN DE CARGA DE CPU MEDIANTE STREAMING A 10 FPS Y CONTROL DE FLUJO EN EL MOTOR OCR.
    - SILENCIADO DE LOGS TÉCNICOS DE FFMPEG PARA UNA CONSOLA MÁS LIMPIA.
- **REGLAS DE NEGOCIO Y SEGURIDAD**:
    - RESTRICCIÓN DE CANCELACIÓN: LOS USUARIOS NO PUEDEN CANCELAR RESERVAS "EN CURSO" (ACTIVA).
    - AJUSTE DE CLEANUP: SE EVITA LA CANCELACIÓN PREVENTIVA DE RESERVAS IMPAGAS HASTA QUE HAYA PASADO SU HORA DE INICIO.
- **UX & BUG FIXES**:
    - SE CORRIGIÓ EL CÁLCULO DE FECHAS PARA ESTADÍAS SEMANALES/MENSUALES (COINCIDENCIA EXACTA DE PRECIOS).
    - SOLUCIÓN AL ERROR DE JAVASCRIPT POR ELEMENTOS NULOS DURANTE LA CARGA DEL PERFIL.

## 📅 16 DE MAYO, 2026 - REVOLUCIÓN DASHBOARD (COMMAND CENTER V5.9)
- **REDISÉÑO INTEGRAL (ADMIN)**: SE TRANSFORMÓ EL DASHBOARD EN UN "CENTRO DE COMANDO" PROFESIONAL USANDO LA ESTÉTICA GOLD & BLACK.
- **GESTIÓN DE RESERVAS PRO**: REFACTORIZACIÓN TOTAL DE LA TABLA DE RESERVAS CON KPIS DE RECAUDACIÓN, FILTRADO POR SEDE Y ACCIONES ADMINISTRATIVAS (COBRO MANUAL/CANCELACIÓN).
- **CONTROL DE ACCESO HÍBRIDO**: IMPLEMENTACIÓN DE VALIDACIÓN DE PASES DIGITALES (QR) PARA APERTURA DE BARRERAS EN TÓTEMS DE ENTRADA Y SALIDA.
- **AUTOMATIZACIÓN**: SISTEMA DE CANCELACIÓN AUTOMÁTICA PARA RESERVAS IMPAGAS 1 HORA ANTES DE SU INICIO (WORKER DE FONDO).
- **OPTIMIZACIÓN VISUAL**: UNIFICACIÓN DE ICONOGRAFÍA DORADA, ALINEACIÓN DE FILTROS Y ENSANCHAMIENTO DE COLUMNAS PARA PATENTES LARGAS.
- **FIX RESPONSIVE**: CORRECCIÓN DE EVENTOS EN EL MENÚ MÓVIL QUE IMPEDÍAN LA APERTURA DE MODALES DE LOGIN/REGISTRO.
- **ARQUITECTURA MODULAR**: SE DIVIDIÓ EL HTML DEL DASHBOARD EN FRAGMENTOS (`/tabs/`) PARA FACILITAR EL MANTENIMIENTO.

## 📅 17 DE MAYO, 2026 - REVOLUCIÓN GESTIÓN & UX (V6.1)
- **GESTIÓN DE USUARIOS 2.0**: 
    - Rediseño de la tabla de usuarios con comportamiento colapsable y animación fluida.
    - Implementación de paginación (10 usuarios por página) y ordenamiento jerárquico (Admin > Empleado > Cliente).
    - Desglose de KPIs en el header (Totales, Admins, Empleados, Clientes).
    - Eliminación de columnas redundantes y protección de cuentas administrativas (botones de acción ocultos para admins).
- **ADMINISTRACIÓN DE RESERVAS**:
    - Agregado filtro dinámico por estado (Pendiente, Activa, Completada, Cancelada).
    - Normalización de textos: Capitalización automática de tipos de estadía (Ej: "Mensual").
    - Optimización de layout: Ensanchamiento de columna de vehículos para patentes de formato nuevo/largo.
    - Limpieza de métricas: Eliminación del KPI de recaudación proyectada para foco operativo.
- **PORTAL DEL CLIENTE (UX/UI)**:
    - **Sincronización de Tarifas**: Creación de endpoint `/user/rates` para que los clientes vean precios actualizados en tiempo real sin errores de permisos.
    - **Cálculo Preciso**: Unificación de lógica de precios entre frontend y backend (redondeo por bloques y cálculo de duración exacta).
    - **Formulario Inteligente**: El formulario de reserva ahora inicia vacío (sin pre-selecciones) para evitar errores.
    - **Nomenclatura Profesional**: Cambio de etiquetas ("Tipo de Estadía", "Vehículo") y opciones simplificadas ("Hora", "Día", "Mes").
    - **Navegación Fluida**: Redirección automática a "Mis Reservas" tras confirmar una estadía con éxito.
- **BACKEND & SEGURIDAD**:
    - Implementación de endpoints administrativos para bloqueo, ajuste de saldo y eliminación de usuarios.
    - Sincronización de esquemas Pydantic con soporte para campo `is_blocked`.
    - Fix crítico en `reservas.js` que impedía crear estadías prolongadas (Semanales/Mensuales) por error de selectores.

## 📝 REGLAS DE LENGUAJE Y ESTILO (ACTUALIZADO 2026-05-17)

1.  **TRATO DE VOS (VOSEO ARGENTINO)**: TODO EL SITIO DEBE DIRIGIRSE AL USUARIO USANDO EL "VOS" (EJ: "INICIÁ", "REGISTRATE", "CONTACTANOS", "TENÉS").
2.  **ORTOGRAFÍA Y ACENTOS**: TODAS LAS PALABRAS DEBEN ESTAR ESCRITAS CORRECTAMENTE, INCLUYENDO ACENTOS EN MAYÚSCULAS.
3.  **FORMATO DE TEXTOS EN UI**: 
    - **NOMBRES DE USUARIO**: SIEMPRE EN MAYÚSCULAS EN TODA LA INTERFAZ.
    - **LOGO**: "AUTOPASS" siempre en **DORADO** (`var(--dorado)`) en el header público.
4.  **ESTÉTICA**: GOLD & BLACK (Premium). Uso intensivo de Glassmorphism en interfaces públicas.

## 🚀 VERSIONES RECIENTES

### VERSIÓN 5.8 (2026-05-16) — REFACTOR UI & NORMALIZACIÓN
- **NORMALIZACIÓN FUENTES**: Migración total a Montserrat como fuente base del sistema.
- **ESCALA TIPOGRÁFICA**: Implementación de variables CSS para tamaños de fuente estandarizados.
- **SIDEBAR MÓVIL V2**: Ancho reducido a 260px, alineación izquierda y cambio de Uppercase a Title Case para mejor legibilidad.
- **HEADER DESKTOP**: Restauración de proporciones premium y refactorización del botón de cierre de sesión (Outline Style).
- **JS CLEANUP**: Depuración de `landing.js`, eliminación de lógica duplicada y mejora del cierre por click exterior.

### VERSIÓN 5.1 (2026-05-16) — DASHBOARD & HEADER PRO
- **HEADER LANDING REFACTORED**: Implementación de sticky header con desenfoque de fondo y detección de estado de sesión (Login/Perfil dinámico).
- **DASHBOARD ENHANCEMENTS**: 
    - Agregado saludo personalizado dinámico.
    - Nueva sección "Mi Progreso" para visualización de beneficios acumulados.
    - Grilla de "Accesos Rápidos" para navegación ágil.
- **SECURITY UX**: Implementación de "ojitos" para ver/ocultar contraseña en el perfil.
- **LOGO UNIFICATION**: Unificación de marca en dorado para todos los headers públicos.
- **SIDEBAR REFACTOR**: Reducción de ancho a 240px y corrección de responsive en colapsado.

### VERSIÓN 5.0 (2026-05-14) — RESPONSIVE FULL 2.0 & ARQUITECTURA
- **UNIFICACIÓN LEGAL**: Aplicación del header premium a Términos, Privacidad y Nuestra Red.
- **GRID ADAPTATIVO**: Rediseño de formularios de reserva y tablas de historial para 1, 2 y 3 columnas según breakpoint.
- **FOOTER INTELIGENTE**: Apilado vertical automático de acciones de pago y botones en móviles.
- **CLEANUP CSS**: Eliminación masiva de estilos inline y centralización en hojas de estilo modulares.
- **ARQUITECTURA DE CAPAS (BACKEND)**: 
    - Implementación de Capa de Servicios (`ReservationService`) y Capa de Repositorios (`UserRepository`, `ReservationRepository`).
    - Modularización de base de datos en `database.py`.
- **SISTEMA DE PUNTOS**: Lógica integral de acumulación (10 pts x $1000) y descuentos por cancelación.

### 👤 MEJORAS EN PERFIL DE USUARIO
- **REEMPLAZO DE INLINE STYLES**: ~40 atributos `style` eliminados. Toda la UI ahora usa clases CSS reutilizables.
- **PANTALLA DE INICIO**: Banner de bienvenida, tarjetas de estadísticas y trigger de reserva renovado.
- **PASE DIGITAL**: Implementación de modal premium con QR dinámico y Web Share API.

### 🛠️ DASHBOARD ADMINISTRATIVO
- **REFACTORIZACIÓN DE UI**: Eliminación de estilos inline en favor de clases dedicadas (`.cam-box`, `.health-dot`, etc.).
- **MONITOREO EN VIVO**: Detección de patentes visual con fallback y pills de estado en logs.
- **GESTIÓN ADMIN**: Nuevos endpoints para creación de reservas manuales desde la administración.

### VERSIÓN 4.5 (2026-05-12) — MODULARIZACIÓN
- **REFACTORIZACIÓN JS**: Lógica de reservas extraída a `reservas.js`.
- **FORMULARIO DE RESERVAS PRO**: Automatización de fin de estadía por periodos.
- **SIDEBAR DINÁMICO**: Logo compacto (32px) y estados `collapsed` persistentes.
- **RESPONSIVE DESIGN**: Overhaul del menú hamburguesa y adaptabilidad total en móviles.

## 📌 PRÓXIMOS PASOS
- **REPORTES**: IMPLEMENTAR EXPORTACIÓN A CSV/PDF EN PESTAÑA FINANCIERA.
- **BLOQUEO UI**: AÑADIR BOTÓN DE SUSPENSIÓN DE USUARIOS EN EL FRONTEND.
- **MERCADO PAGO**: INTEGRAR EL SDK PARA PROCESAR PAGOS REALES.
- **NOTIFICACIONES**: SISTEMA DE ALERTAS POR EMAIL PARA INGRESOS Y EGRESOS.

## 📅 17 DE MAYO, 2026 - SEGURIDAD Y AUDITORÍA (COMMAND CENTER V6.0)
- **AUDITORÍA VISUAL**: IMPLEMENTACIÓN DE UN VISUALIZADOR DE CAPTURAS ALPR QUE PERMITE VER LA FOTO REAL DE CADA VEHÍCULO REGISTRADO EN LOS LOGS.
- **SISTEMA DE ROLES (STAFF)**: CREACIÓN DEL ROL "EMPLEADO" CON ACCESO LIMITADO SOLO A FUNCIONES OPERATIVAS (MONITOREO, BARRERAS, RESERVAS).
- **ALTA DE PERSONAL**: NUEVO MODAL PREMIUM PARA QUE EL ADMIN PUEDA DAR DE ALTA EMPLEADOS O CLIENTES DIRECTAMENTE DESDE EL DASHBOARD.
- **BLOQUEO DE ACCESO**: IMPLEMENTACIÓN DE LÓGICA DE SUSPENSIÓN DE CUENTAS EN EL BACKEND PARA IMPEDIR EL LOGIN DE USUARIOS BLOQUEADOS.
- **BI & ANALYTICS**: CONEXIÓN REAL DEL GRÁFICO FINANCIERO A LA BASE DE DATOS CON LÓGICA DE AGRUPAMIENTO POR DÍA, SEMANA Y MES.
- **ESTANDARIZACIÓN VISUAL**: REDONDEO TOTAL DE BOTONES (ESTILO PÍLDORA), SELECTORES CON MARCO INTEGRADO Y REAJUSTE DE JERARQUÍA DE COLORES EN ROLES (DORADO/VERDE/AZUL).
