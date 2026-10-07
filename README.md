# AUTOPASS

**Sistema inteligente de gestión de estacionamientos** con Visión Artificial (ALPR), Arquitectura Limpia y Frontend Premium.

Multi-sucursal · Multi-piso · Trimodal (Auto/Moto/Camioneta) · Reservaciones · Fidelización por puntos · PWA instalable

---

## Características Principales

- **Visión Artificial (ALPR)** — Reconocimiento de patentes y códigos QR en tiempo real con RapidOCR (motor ONNX, rápido y liviano) con fallback automático a PaddleOCR + OpenCV, sistema de consenso de votos y detección de movimiento
- **Multi-Sucursal** — Gestión independiente de tarifas, aforo, pisos y personal por sucursal
- **Multi-Piso** — Soporte para N niveles por sucursal con capacidad trimodal configurable (Autos/Motos/Camionetas)
- **Facturación Trimodal** — Motor de precios diferenciados por tipo de vehículo y período (Hora/Día/Semana/Quincena/Mes)
- **Reservaciones** — Creación, pago, cancelación con reembolso, anticipación configurable y auto-cancelación; cupos **exclusivos de reserva** por sucursal/tipo de vehículo con disponibilidad en tiempo real (sweep-line) y fechas/horas deshabilitadas en el selector; edición admin de reservas pagadas con **ajuste financiero automático** (cobra o reembolsa la diferencia al saldo según el método elegido, con monto neto `total − reembolsado` reflejado en reportes y en el portal)
- **Pagos con Mercado Pago (v9.14.0)** — Checkout Pro por redirección para abonar reservas y estadías en curso de forma **directa** (no toca el saldo de la billetera); confirmación por retorno (`/success|pending|failure`) y webhook
- **Pagos en efectivo y digital** — El pago de estadías soporta método `DIGITAL` (billetera/MP) o `CAJA` (efectivo, registrado por el operador desde monitoreo); los reportes financieros desglosan la recaudación por método (`recaudado_efectivo` / `recaudado_digital`)
- **Fidelización** — Sistema de puntos (10 pts/$1000), catálogo de promociones canjeables, cupones y descuentos con voucher
- **Mapas Interactivos & Filtro de Localidades** — Mosaico de Google Maps con buscador autocompletado en tiempo real, desglose de direcciones exactas, aviso de disponibilidad por zona y navegación animada `flyTo`
- **Dashboard Admin Premium** — 9 pestañas modulares (Monitoreo, Ocupación, Reservas, Usuarios, Reportes, Promociones, Soporte, Sucursales, Configuración) + página de Estadísticas OCR
- **Portal de Usuario** — Perfil, reservas, vehículos, billetera virtual, pase digital QR, notificaciones
- **Real-time** — WebSocket (aforo), MQTT (barreras), polling de notificaciones
- **Monitoreo CCTV** — Grilla dinámica de cámaras con streaming MJPEG y controles DVR
- **Soporte** — Sistema de tickets con aislamiento por sucursal, adjuntos y respuesta en tiempo real
- **Tiempo Virtual** — Servicio de testing que permite simular el paso del tiempo sin afectar el reloj real
- **PWA instalable** — Manifest + Service Worker en scope raíz con cache offline de assets
- **RBAC** — Control de acceso por roles: Admin Global, Local Admin, Staff, User
- **Base de Datos Online** — Neon/Postgres (sa-east-1) **compartido** por todas las PC (no hay fallback automático; SQLite local queda solo como opción aislada para desarrollo/tests)
- **Migraciones** — Alembic para control de versiones del esquema

## Arquitectura

```
AUTOPASS/
├── core/               # Infraestructura (Config, Seguridad JWT/RBAC, DB, MQTT, Seed)
├── models/             # Entidades SQLAlchemy + Enums (Domain Layer)
├── schemas/            # Validación Pydantic
├── routes/             # Endpoints FastAPI (Transport Layer - delgados)
│   ├── admin/          # CRUD admin (users, branches, reservations, promotions, operations, settings, virtual_time, support)
│   ├── user/           # Portal usuario (profile, vehicles, reservations, balance, fidelization, notifications, support, mercadopago)
│   ├── parking/        # Control de acceso (ALPR/QR, status, utils)
│   └── system/         # Sistema (health, cameras, video, common)
├── services/           # Lógica de negocio (14 servicios)
├── repositories/       # Data Access Layer
├── alpr/               # Paquete modular de visión artificial
├── static/
│   ├── js/modules/     # 36 módulos ES6
│   └── css/            # 40 archivos CSS (Glassmorphism Premium)
├── templates/          # Jinja2 (dashboard 9 tabs + página OCR, profile 7 tabs, emails, modales)
├── tests/              # Suite de pruebas automatizadas (pytest)
├── alembic/            # Migraciones de BD
└── scripts/            # Utilidades y migraciones
```

## Stack Tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | FastAPI (Python 3.14) |
| Base de Datos | SQLAlchemy — Neon/Postgres (sa-east-1) compartido por defecto · SQLite local (opcional, aislado) |
| Frontend | Vanilla JS (ES6 Modules), CSS Moderno, Jinja2 |
| Visión Artificial | PaddleOCR + OpenCV |
| IoT | ESP32 + Arduino Uno (MQTT + Serie USB) |
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
# Base de datos compartida (por defecto): Neon/Postgres, la cadena completa está en .env.example
DATABASE_URL=postgresql://usuario:clave@ep-xxxx.sa-east-1.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=tu_secreto_aqui
MQTT_BROKER=broker.hivemq.com
MQTT_TOPIC_ENTRADA=parking/barrera/entrada/control
MQTT_TOPIC_SALIDA=parking/barrera/salida/control
IMAGE_DIR=captured_images
RESERVA_HORA_MIN_SEGUNDOS=1800
MAINTENANCE_INTERVAL_SECONDS=300

# Mercado Pago (Checkout Pro) - ver "Pagos con Mercado Pago" más abajo
BASE_URL=https://tu-dominio.trycloudflare.com  # OBLIGATORIO con https (MP lo exige en back_urls)
MP_ACCESS_TOKEN=APP_USR-...   # Access Token de prueba (sandbox) desde el panel de desarrolladores
MP_PUBLIC_KEY=APP_USR-...     # Public Key de prueba
MP_WEBHOOK_URL=https://tu-dominio.trycloudflare.com/v1/user/mercadopago/webhook
MP_PREFERENCE_EXPIRE_MINUTES=45

# Email (opcional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu_email@gmail.com
SMTP_PASSWORD=tu_password
SMTP_FROM=noreply@autopass.com.ar

# Base local aislada (opcional, solo desarrollo/tests; reemplaza la DATABASE_URL de arriba)
# DATABASE_URL=sqlite:///./parking.db
```

> **Importante — base compartida:** por defecto todas las PC que arranquen el backend apuntan a la **misma** base Neon/Postgres: usuarios, reservas, saldos y sucursales se comparten. Si cargás datos de prueba, afectan a todos. Para trabajar aislado, usá la alternativa SQLite de arriba.

### 4. Inicializar Base de Datos (solo instalación manual)
```bash
# Flujo único: crea tablas desde los modelos (create_all) y sincroniza Alembic al head.
# Si la cadena de migraciones no es reproducible de cero, sella el head con warning explícito.
.\venv\Scripts\python.exe init_db.py
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
| ReportService | Analítica financiera y transacciones (UNION ALL), desglose de recaudación por método (efectivo/digital) |
| SupportService | Tickets de soporte con aislamiento por sucursal |
| EmailService | Emails transaccionales con templates Jinja2 (QR, recuperación) |
| NotificationService | Notificaciones en tiempo real via WebSocket |
| UserNotificationService | CRUD de notificaciones in-app |
| WorkerService | 2 hilos: limpieza/mantenimiento (300s) y notificaciones/recordatorios (30s) |
| TimeService | Tiempo virtual para testing |
| HardwareService | Control de barreras MQTT y comunicación Serie USB con Arduino Uno |
| MercadoPagoService | Preferencias Checkout Pro, confirmación (retorno/webhook) y aplicación de pagos MP en reservas y estadías |

## Pagos con Mercado Pago (v9.14.0)

Integración **Checkout Pro** (redirección) para pagar **reservas** y **estadías en curso** directamente desde el portal de usuario, **sin descontar el saldo** de la billetera.

### Cómo funciona
1. `POST /v1/user/mercadopago/checkout` crea la preferencia en MP (`MercadoPagoPayment`, tabla `mercadopago_payments`) y devuelve el `init_point` (sandbox en pruebas).
2. El usuario paga en el sitio de Mercado Pago.
3. Confirma por **retorno** (`GET /v1/user/mercadopago/success|pending|failure`) y/o **webhook** (`POST /v1/user/mercadopago/webhook`). `confirm_payment` consulta MP, valida estado `approved` + monto y aplica (idempotente).
4. Aplicar una **reserva**: marca `PAGADO`/`ACTIVA`, suma puntos y envía el pase digital; una **estadía**: marca `pago_confirmado` con `metodo_pago = MERCADOPAGO`. Ambos casos **no tocan `users.saldo`**.

### Credenciales y modo pruebas
- Credenciales **de prueba** desde https://www.mercadopago.com.ar/developers/panel (Desarrollo propio → Pagos online → API → Checkout Pro/Orders). Hoy el panel usa prefijo `APP_USR-` también en modo prueba.
- **Obligatorio**: `BASE_URL` con `https://` (MP rechaza `http://` en `back_urls`). Para pruebas locales usá un túnel: `.\acceso_remoto.bat` (cloudflared) y poné la URL pública en `BASE_URL` y `MP_WEBHOOK_URL`.
- Tarjeta test (aprobada): `5031 7557 3453 0604` (Mastercard), CVV y vencimiento cualquiera.
- Probá **dentro del mismo origen** del túnel (logueate en la URL del túnel) para no perder la sesión al volver de MP.

## Frontend

- **36 módulos ES6** con patrón Bridge (módulos → scripts puente → window.* → HTML onclick)
- **40 archivos CSS** organizados en base/layout/components/pages
- **Design System Premium**: Glassmorphism, dorado (#C5A059), animaciones fluidas
- **Dashboard**: 9 pestañas admin + portal de usuario con 7 tabs
- **Componentes**: Leaflet.js (mapas), Chart.js (reportes), Flatpickr (fechas), QRCode.js (pases)

## PWA

- Service Worker en scope raíz (`/sw.js`, `Service-Worker-Allowed: /`) con cache de assets por versionado (`autopass-v2`)
- Manifest en `/manifest.webmanifest`; página de guía de instalación en `/instalar`
- Botón de instalación visible solo donde corresponde (oculto en el monitor de cámaras multicámara, que además no forma parte de la app instalable)

## Licencia

Proyecto privado — Todos los derechos reservados.
