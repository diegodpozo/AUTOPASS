# AUTOPASS

**Sistema inteligente de gestión de estacionamientos** con Visión Artificial (ALPR), Arquitectura Limpia y Frontend Premium.

Multi-sucursal · Multi-piso · Trimodal (Auto/Moto/Camioneta) · Reservaciones · Fidelización por puntos

---

## Características Principales

- **Visión Artificial (ALPR)** — Reconocimiento de patentes y códigos QR en tiempo real con PaddleOCR + OpenCV, sistema de consenso de votos y detección de movimiento
- **Multi-Sucursal** — Gestión independiente de tarifas, aforo, pisos y personal por sucursal
- **Multi-Piso** — Soporte para N niveles por sucursal con capacidad trimodal configurable (Autos/Motos/Camionetas)
- **Facturación Trimodal** — Motor de precios diferenciados por tipo de vehículo y período (Hora/Día/Semana/Quincena/Mes)
- **Reservaciones** — Creación, pago, cancelación con reembolso, anticipación configurable y auto-cancelación
- **Fidelización** — Sistema de puntos (10 pts/$1000), catálogo de promociones canjeables y cupones
- **Mapas Interactivos & Filtro de Localidades** — Mosaico de Google Maps con buscador autocompletado en tiempo real, desglose de direcciones exactas, aviso de disponibilidad por zona y navegación animada `flyTo`
- **Dashboard Admin Premium** — 8 pestañas modulares: Monitoreo, Reservas, Usuarios, Reportes, Promociones, Soporte, Sucursales, Configuración
- **Portal de Usuario** — Perfil, reservas, vehículos, billetera virtual, pase digital QR, notificaciones
- **Real-time** — WebSocket (aforo), MQTT (barreras), polling de notificaciones
- **Monitoreo CCTV** — Grilla dinámica de cámaras con streaming MJPEG y controles DVR
- **Soporte** — Sistema de tickets con aislamiento por sucursal y respuesta en tiempo real
- **Tiempo Virtual** — Servicio de testing que permite simular el paso del tiempo sin afectar el reloj real
- **RBAC** — Control de acceso por roles: Admin Global, Local Admin, Staff, User
- **Base de Datos Online** — Neon/Postgres (sa-east-1) compartido entre múltiples PC, con fallback a SQLite local
- **Migraciones** — Alembic para control de versiones del esquema

## Arquitectura

```
AUTOPASS/
├── core/               # Infraestructura (Config, Seguridad JWT/RBAC, DB, MQTT, Seed)
├── models/             # Entidades SQLAlchemy + Enums (Domain Layer)
├── schemas/            # Validación Pydantic
├── routes/             # Endpoints FastAPI (Transport Layer - delgados)
│   ├── admin/          # CRUD admin (users, branches, reservations, promotions, operations, settings, virtual_time, support)
│   ├── user/           # Portal usuario (profile, vehicles, reservations, balance, fidelization, notifications, support)
│   ├── parking/        # Control de acceso (ALPR/QR, status, utils)
│   └── system/         # Sistema (health, cameras, video, common)
├── services/           # Lógica de negocio (13 servicios)
├── repositories/       # Data Access Layer
├── alpr/               # Paquete modular de visión artificial
├── static/
│   ├── js/modules/     # 36 módulos ES6
│   └── css/            # 39 archivos CSS (Glassmorphism Premium)
├── templates/          # Jinja2 (dashboard 9 tabs, profile 7 tabs, emails, modales)
├── tests/              # Suite de pruebas automatizadas (pytest)
├── alembic/            # Migraciones de BD
└── scripts/            # Utilidades y migraciones
```

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI (Python 3.14) |
| Base de Datos | SQLAlchemy — Neon/Postgres (sa-east-1) o SQLite local |
| Frontend | Vanilla JS (ES6 Modules), CSS Moderno, Jinja2 |
| Visión Artificial | PaddleOCR + OpenCV |
| IoT | ESP32 + Paho-MQTT |
| Real-time | WebSockets, MQTT |
| Migraciones | Alembic |
| Testing | Pytest |

## Inicio Rápido

### 1. Requisitos
- Python 3.14

### 2. Instalación

#### Opción recomendada (automática)
```bash
# Clonar el repositorio
git clone https://github.com/MarianoJAC/AUTOPASS.git
cd AUTOPASS

# Ejecutar el instalador — crea venv, instala dependencias, configura .env,
# inicializa la base de datos, aplica migraciones Alembic y corre los tests
.\setup_backend.bat
```

#### Instalación manual
```bash
# Crear entorno virtual e instalar dependencias
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configuración
El instalador automático crea `.env` desde `.env.example`. Si instalás manualmente, creá o editá el archivo `.env` en la raíz:
```env
DATABASE_URL=sqlite:///./parking.db
SECRET_KEY=tu_secreto_aqui
MQTT_BROKER=broker.hivemq.com
MQTT_TOPIC_ENTRADA=parking/barrera/entrada/control
MQTT_TOPIC_SALIDA=parking/barrera/salida/control
IMAGE_DIR=captured_images
RESERVA_HORA_MIN_SEGUNDOS=1800
MAINTENANCE_INTERVAL_SECONDS=300

# Email (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_password
SMTP_FROM=noreply@autopass.com.ar

# Base online (opcional) - Neon/Postgres
# DATABASE_URL=postgresql://user:pass@ep-xxxx.sa-east-1.aws.neon.tech/neondb?sslmode=require
```

### 4. Inicializar Base de Datos (solo instalación manual)
```bash
.\venv\Scripts\python.exe init_db.py
.\venv\Scripts\python.exe -m alembic stamp head
.\venv\Scripts\python.exe -m alembic upgrade head
```

### 5. Ejecutar
```bash
# Opción recomendada (arranque rápido)
.\run_server.bat

# O manual
.\venv\Scripts\python.exe -m uvicorn main:app --port 8000
```

### 6. Verificar
```bash
.\venv\Scripts\python.exe -m pytest tests/ --verbose
```

## Credenciales por Defecto

| Rol | Email | Contraseña | Sucursal |
|-----|-------|-----------|----------|
| Admin Global | `admin@autopass.com` | `admin123` | Todas |
| Local Admin | `admmoron@autopass.com` | `admin123` | AUTOPASS Morón |
| Local Admin | `admituzaingo@autopass.com` | `admin123` | AUTOPASS Ituzaingó |
| Local Admin | `admcastelar@autopass.com` | `admin123` | AUTOPASS Castelar |

## Servicios del Sistema

| Servicio | Responsabilidad |
|----------|----------------|
| AccessService | Validación ALPR/QR, entrada/salida, pago de estadía |
| BillingService | Cálculo de tarifas, deuda, puntos, proceso de pago |
| ReservationService | CRUD reservas, pago, cancelación, simulación, auto-finalización |
| BranchService | CRUD sucursales, capacidad trimodal, gestión de pisos |
| UserService | CRUD usuarios, validaciones de seguridad |
| ReportService | Analítica financiera y transacciones (UNION ALL) |
| SupportService | Tickets de soporte con aislamiento por sucursal |
| EmailService | Emails transaccionales con templates Jinja2 (QR, recuperación) |
| NotificationService | Notificaciones en tiempo real via WebSocket |
| UserNotificationService | CRUD de notificaciones in-app |
| WorkerService | 3 hilos: limpieza (300s), recordatorios, auto-cancelación |
| TimeService | Tiempo virtual para testing |
| HardwareService | Control de barreras MQTT y comunicación con ESP32 |

## Frontend

- **32 módulos ES6** con patrón Bridge (módulos → scripts puente → window.* → HTML onclick)
- **39 archivos CSS** organizados en base/layout/components/pages
- **Design System Premium**: Glassmorphism, dorado (#C5A059), animaciones fluidas
- **Dashboard**: 8 pestañas admin + portal de usuario con 7 tabs
- **Componentes**: Leaflet.js (mapas), Chart.js (reportes), Flatpickr (fechas), QRCode.js (pases)

## Licencia

Proyecto privado — Todos los derechos reservados.
