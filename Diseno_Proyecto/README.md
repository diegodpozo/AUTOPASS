# Diseno del Proyecto — AUTOPASS

Documentacion completa del diseno del sistema siguiendo el **Proceso Unificado de Desarrollo (RUP/UP)**.

## Estructura

```
Diseno_Proyecto/
│
├── 01_Inception/                     # FASE DE INICIO
│   ├── 01_Vision_Del_Sistema.md      # Vision, proposito, propuesta de valor
│   ├── 02_Stakeholders_Y_Equipo.md   # Stakeholders, equipo, cronograma
│   ├── 03_Alcance_Y_GLOSARIO.md      # Alcance funcional, glosario, exclusiones
│   └── 04_Modelo_De_Negocio.md       # Modelo de negocio, KPIs, ventajas competitivas
│
├── 02_Elaboration/                   # FASE DE ELABORACION
│   ├── 01_Requisitos_Funcionales.md  # RF-01 a RF-44 detallados
│   ├── 02_Requisitos_No_Funcionales.md # RNF-01 a RNF-29
│   ├── 03_Casos_De_Uso.md           # 20 casos de uso con flujos principales
│   └── 04_Arquitectura_General.md   # Clean Architecture, capas, patrones, flujo de datos
│
├── 03_Construction/                  # FASE DE CONSTRUCCION
│   ├── 01_Modelo_De_Datos.md        # DER, 14 entidades, columnas, relaciones
│   ├── 02_Diagramas_De_Secuencia.md # 5 diagramas de secuencia detallados
│   ├── 03_Diagrama_De_Clases.md     # Diagrama de clases por capa
│   └── 04_Diseno_Frontend.md        # Arquitectura frontend, design system, componentes
│
├── 04_Transition/                    # FASE DE TRANSICION
│   ├── 01_Despliegue.md             # Instalacion, configuracion, produccion
│   ├── 02_Pruebas.md                # Estrategia de pruebas, casos criticos, cobertura
│   └── 03_Operaciones_Y_Mantenimiento.md # Monitoreo, logs, recovery, seguridad
│
└── 05_Apendices/                     # DOCUMENTACION ADICIONAL
    ├── 01_Mapa_De_Rutas_API.md       # Todos los endpoints organizados por modulo
    ├── 02_Arquitectura_ALPR.md       # Arquitectura del sistema de vision artificial
    └── 03_Integracion_Hardware.md    # ESP32, MQTT, camaras, firmware
```

## Resumen por Fase

### 1. Inception (Inicio)
Define la **vision del sistema**: un gestor de estacionamientos inteligente con ALPR,
multi-sucursal, multi-piso, facturacion trimodal y reservas. Identifica 4 roles de usuario
(ADMIN, LOCAL_ADMIN, STAFF, USER) y establece el alcance de la version v10.0.0.

### 2. Elaboration (Elaboracion)
Especifica **44 requisitos funcionales** y **29 no funcionales**, detalla **20 casos de uso**
con flujos principales y alternativos, y define la **arquitectura Clean Architecture** con
5 capas (Presentation, Transport, Business, Data, Infrastructure) mas frontend Jinja2 + WebSockets.

### 3. Construction (Construccion)
Documenta el **modelo de datos** con 14 entidades (User, Vehicle, AccessLog, Reservation,
ParkingFloor, ParkingAforo, Settings, ParkingCamera, PointsLog, Coupon, Promotion,
UserNotification, SupportTicket) y sus relaciones, **5 diagramas de secuencia** (ingreso ALPR, egreso con
pago, reserva, worker de limpieza, worker de notificaciones, operacion manual),
**diagrama de clases** completo por capa (12 servicios), y el **diseno del frontend** con
design system (Glassmorphism, dorado #C5A059, FAB).

### 4. Transition (Transicion)
Cubre el **plan de despliegue** (SQLite dev / PostgreSQL prod), **estrategia de pruebas**
con 8 casos criticos, **virtual time service** para testing, y **operaciones y mantenimiento**
(health checks, logs, workers, recovery).

### 5. Apendices
Mapa completo de **rutas API** (~99 endpoints HTTP + 2 WebSocket), **arquitectura del sistema ALPR**
(motor OCR dual RapidOCR/PaddleOCR + OpenCV con consenso y cooldown), e **integracion con hardware** ESP32 via MQTT.

## Servicios del Sistema

| Servicio | Responsabilidad |
|----------|----------------|
| AccessService | Validacion ALPR/QR, entrada/salida, pago de estadia |
| BillingService | Calculo de tarifas, deuda, puntos, proceso de pago |
| ReservationService | CRUD reservas, pago, cancelacion, simulacion, auto-finalizacion |
| BranchService | CRUD sucursales, resumen de capacidad trimodal |
| UserService | CRUD usuarios, soft delete con anonimizacion |
| ReportService | Analitica financiera y transacciones (resumen, historial UNION ALL, accesos) |
| SupportService | Tickets de soporte (crear, consultar, gestionar y responder) |
| EmailService | Envio de emails transaccionales (confirmacion, recordatorio, recuperacion) |
| NotificationService | Notificaciones en tiempo real via WebSocket (OccupancyManager) |
| UserNotificationService | CRUD de notificaciones in-app (create, read, mark) |
| WorkerService | 2 hilos: limpieza de reservas (300s) + notificaciones (recordatorios, auto-cancelacion) |
| TimeService | Tiempo virtual para testing (offset persistido en JSON) |

## Version del Sistema
**AUTOPASS v10.0.0** — Agosto 2026
