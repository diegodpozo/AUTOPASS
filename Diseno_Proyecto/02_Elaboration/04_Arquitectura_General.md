# Arquitectura General del Sistema — AUTOPASS

## Estilo Arquitectónico
**Clean Architecture (Arquitectura Limpia)** con organización por capas de responsabilidad:

```
┌─────────────────────────────────────────────────────────┐
│                    CAPA DE PRESENTACIÓN                  │
│              (Templates Jinja2 + JS + CSS)               │
├─────────────────────────────────────────────────────────┤
│                    CAPA DE TRANSPORTE                    │
│              (Routes/Endpoints FastAPI)                   │
├─────────────────────────────────────────────────────────┤
│                    CAPA DE NEGOCIO                        │
│              (Services + Workers)                         │
├─────────────────────────────────────────────────────────┤
│                    CAPA DE DATOS                          │
│              (Models/Schemas/Repositories)                │
├─────────────────────────────────────────────────────────┤
│                    CAPA DE INFRAESTRUCTURA                │
│         (Core: Config, Security, DB, MQTT)               │
└─────────────────────────────────────────────────────────┘
```

## Diagrama de Capas

```
┌──────────────────────────────────────────────────────────────┐
│  CLIENTE (Browser) ──── WebSockets ──── ALPR Service         │
│       │                       │              │                │
│       ▼                       ▼              ▼                │
│  ┌───────────────────────────────────────────────────┐       │
│  │              FASTAPI (main.py)                     │       │
│  │  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌────────┐  │       │
│  │  │  Auth   │ │  Admin   │ │  User  │ │Parking │  │       │
│  │  │ Routes  │ │  Routes  │ │ Routes │ │ Routes │  │       │
│  │  └────┬────┘ └────┬─────┘ └───┬────┘ └───┬────┘  │       │
│  │       │           │           │          │        │       │
│  │  ┌────▼───────────▼───────────▼──────────▼────┐   │       │
│  │  │           SERVICES LAYER                    │   │       │
│  │  │  Access  Billing  Reservation  Branch      │   │       │
│  │  │  User    Email   Notification  Worker      │   │       │
│  │  │  UserNotification  Time                   │   │       │
│  │  └────┬───────────────────────────────────────┘   │       │
│  │       │                                            │       │
│  │  ┌────▼───────────────────────────────────────┐   │       │
│  │  │       DATA LAYER                            │   │       │
│  │  │  Models (ORM)  Schemas (Pydantic)  Repos    │   │       │
│  │  └────┬───────────────────────────────────────┘   │       │
│  │       │                                            │       │
│  │  ┌────▼───────────────────────────────────────┐   │       │
│  │  │       CORE INFRASTRUCTURE                   │   │       │
│  │  │  Config  Security  Database  MQTT  Seed     │   │       │
│  │  └─────────────────────────────────────────────┘   │       │
│  └───────────────────────────────────────────────────┘       │
│       │                                                       │
│       ▼                                                       │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐          │
│  │ SQLite / │  │  MQTT    │  │   ESP32 Hardware   │          │
│  │PostgreSQL│  │  Broker  │  │  (Barrera/Sensor)  │          │
│  └──────────┘  └──────────┘  └────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

## Tecnologías por Capa

| Capa | Tecnología | Propósito |
|------|------------|-----------|
| **Presentación** | Jinja2, Vanilla JS (ES6 Modules), CSS3 | Templates HTML, lógica de UI, estilos Glassmorphism |
| **Frontend Libraries** | Chart.js, Leaflet.js, Font Awesome | Gráficos, mapas, iconos |
| **Transporte** | FastAPI, Uvicorn | API REST, WebSockets, servidor ASGI |
| **Validación** | Pydantic v2 | Schemas de entrada/salida con validación |
| **Negocio** | Python 3.9+, Services Layer | Lógica de acceso, facturación, reservas, workers |
| **Datos** | SQLAlchemy 2.0 ORM | Modelos de BD, consultas, migraciones |
| **Infraestructura** | core/config.py, core/security.py, core/database.py | Config, JWT+bcrypt, sesiones DB |
| **Visión Artificial** | OpenCV, EasyOCR, PyTorch | ALPR, detección de QR, procesamiento de imágenes |
| **IoT** | Paho-MQTT | Comunicación con barreras ESP32 |
| **Email** | smtplib, Jinja2 | Notificaciones transaccionales |
| **Base de datos** | SQLite (dev) / PostgreSQL (prod) | Persistencia |

## Patrones de Diseño Utilizados

| Patrón | Uso | Ubicación |
|--------|-----|-----------|
| **Repository** | Abstracción de acceso a datos | repositories/ |
| **Service Layer** | Lógica de negocio centralizada | services/ |
| **Dependency Injection** | Inyección de dependencias vía FastAPI Depends | routes/, core/security.py |
| **Observer (via WS)** | Notificaciones en tiempo real (OccupancyManager) | services/notification_service.py |
| **Singleton** | Configuración global, MQTT client | core/config.py, core/mqtt.py |
| **Strategy** | Cálculo de tarifas por tipo de vehículo/reserva | services/billing_service.py |
| **Worker Thread** | Procesos de fondo periódicos (3 hilos: limpieza, recordatorios, auto-cancelación) | services/worker_service.py |
| **Vote Buffer (Consensus)** | Sistema de consenso para ALPR | alpr_service.py |
| **Virtual Time** | Sistema de tiempo offset para testing sin alterar reloj real | services/time_service.py |

## Flujo de Datos Transversal

```
CÁMARA ALPR
    │
    ▼
alpr_service.py (OCR + QR + Consensus)
    │
    ├── POST /v1/access/validate-plate ──► AccessService
    │                                           │
    │              ┌────────────────────────────┤
    │              ▼                            ▼
    │     ReservationService          ParkingAforo (DB)
    │     (busca reserva)           (control capacidad)
    │              │                            │
    │              ▼                            ▼
    │     BillingService            AccessLog (DB)
    │     (calcula si aplica)      (registra evento)
    │              │                            │
    │              └──────────┬─────────────────┘
    │                         ▼
    │                 MQTT Broker
    │                         │
    │                         ▼
    │                 ESP32 (abre/cierra barrera)
    │
    └── WebSocket /v1/parking/ws ──► NotificationService
                                        │
                                        ▼
                                Dashboard (tiempo real)
```
