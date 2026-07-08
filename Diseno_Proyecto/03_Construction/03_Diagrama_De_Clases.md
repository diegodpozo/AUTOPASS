# Diagrama de Clases — AUTOPASS

## Diagrama de Paquetes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        AUTOPASS                                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐│
│  │    core/    │  │   models/   │  │  schemas/   │  │  routes/    ││
│  │ config.py   │  │ enums.py    │  │ auth.py     │  │ auth.py     ││
│  │ security.py │  │ user.py     │  │ user.py     │  │ views.py    ││
│  │ database.py │  │ parking.py  │  │ parking.py  │  │ system.py   ││
│  │ mqtt.py     │  │ reservation │  │ reservation │  │ reports.py  ││
│  │ seed.py     │  │ notification│  │ notification│  │ admin/      ││
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │ user/       ││
│         │                │                │          │ parking/    ││
│         ▼                ▼                ▼          └──────┬──────┘│
│  ┌──────────────────────────────────────────────────────────┘      │
│  │                      services/                                   │
│  │  AccessService  BillingService  ReservationService                │
│  │  UserService    BranchService   EmailService                      │
│  │  NotificationService  WorkerService  UserNotificationService      │
│  └──────────────────────────────────────────────────────────────────┘
│                                                                      │
│  ┌─────────────┐  ┌─────────────────┐  ┌──────────────────────────┐ │
│  │repositories/│  │   templates/    │  │       static/            │ │
│  │ user_repo   │  │   (Jinja2)      │  │  js/  css/  images/     │ │
│  │ reserv_repo │  │                 │  │                          │ │
│  └─────────────┘  └─────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

## Clases del Core

```
┌───────────────────────────────────────────────────────────────┐
│                      core.config.Settings                      │
├───────────────────────────────────────────────────────────────┤
│ - PROJECT_NAME: str                                            │
│ - VERSION: str                                                 │
│ - SECRET_KEY: str                                              │
│ - ALGORITHM: str                                               │
│ - ACCESS_TOKEN_EXPIRE_MINUTES: int                             │
│ - DATABASE_URL: str                                            │
│ - SMTP_SERVER: str                                             │
│ - SMTP_PORT: int                                               │
│ - SMTP_USER: str                                               │
│ - SMTP_PASSWORD: str                                           │
│ - SMTP_FROM: str                                               │
│ - MQTT_BROKER: str                                             │
│ - MQTT_PORT: int                                               │
│ - MQTT_TOPIC_ENTRADA: str                                      │
│ - MQTT_TOPIC_SALIDA: str                                       │
│ - RESERVA_HORA_MIN_SEGUNDOS: int                               │
│ - MAINTENANCE_INTERVAL_SECONDS: int                            │
│ - HEARTBEAT_TIMEOUT_SECONDS: int                               │
│ - IMAGE_DIR: str                                               │
├───────────────────────────────────────────────────────────────┤
│ (carga desde .env)                                             │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                    core.security (Functions)                   │
├───────────────────────────────────────────────────────────────┤
│ + verify_password(plain, hashed) -> bool                      │
│ + get_password_hash(password) -> str                          │
│ + create_access_token(data, expires_delta) -> str             │
│ + decode_access_token(token) -> dict | None                   │
│ + get_current_user(token, db) -> User                         │
│ + get_super_admin(current_user) -> User                       │
│ + get_local_manager(current_user) -> User                     │
│ + get_operational_user(current_user) -> User                  │
│ + authenticate_user(db, email, password) -> User | None       │
└───────────────────────────────────────────────────────────────┘
```

## Clases de Servicios

```
┌───────────────────────────────────────────────────────────────┐
│                  services.access_service.AccessService         │
├───────────────────────────────────────────────────────────────┤
│ + validate_plate(db, data, settings) -> dict                  │
│ + validate_qr(db, data) -> dict                               │
│ + pay_stay(db, patente, metodo_pago, user_id) -> dict         │
│ + exit_plate(db, data, settings) -> dict                      │
│ + manual_entry(db, patente, tipo, user_id, ...) -> dict       │
│ + manual_exit(db, patente, settings) -> dict                  │
│ + cancel_stay(db, access_log_id) -> dict                      │
│ # _publish_mqtt(topic, payload)                               │
│ # _notify_occupancy(db, sucursal, event_type, ...)            │
│ # _check_courtesy_time(access_log) -> bool                    │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│              services.reservation_service.ReservationService   │
├───────────────────────────────────────────────────────────────┤
│ + create_reservation(db, user, data) -> Reservation           │
│ + get_availability(db, sucursal, fecha_inicio, ...) -> dict   │
│ + pay_reservation(db, user_id, res_id) -> dict                │
│ + cancel_reservation(db, user_id, res_id) -> dict             │
│ + simulate_cancel(db, user_id, res_id) -> dict                │
│ + update_reservation(db, user_id, res_id, data) -> dict      │
│ + auto_finalize_all_reservations(db) -> int                   │
│ - _calculate_refund(reservation, cancel_time) -> float        │
│ - _reservar_plaza_en_aforo(db, ...)  [NO-OP v9.5]             │
│ - _liberar_plaza_en_aforo(db, ...)   [NO-OP v9.5]             │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│               services.billing_service.BillingService          │
├───────────────────────────────────────────────────────────────┤
│ + calculate_stay_cost(db, patente, sucursal, ...) -> dict     │
│ + calculate_reservation_cost(db, sucursal, tipo, ...) -> float│
│ + calculate_points(amount) -> int                             │
│ + get_hourly_rate(db, sucursal, vehicle_type) -> float        │
│ + get_daily_rate(db, sucursal, vehicle_type) -> float         │
│ + get_weekly_rate(db, sucursal, vehicle_type) -> float        │
│ + get_monthly_rate(db, sucursal, vehicle_type) -> float       │
│ # _get_rates_dict(db, sucursal) -> dict                       │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│            services.notification_service.NotificationService   │
├───────────────────────────────────────────────────────────────┤
│ - _event_loop: asyncio.AbstractEventLoop                       │
│ - _queues: dict[str, asyncio.Queue]                           │
│ + set_event_loop(loop)                                        │
│ + broadcast(sucursal, message)                                │
│ + get_queue(sucursal) -> asyncio.Queue                        │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│               services.worker_service.WorkerService            │
├───────────────────────────────────────────────────────────────┤
│ - _cleanup_thread: threading.Thread                            │
│ - _notification_thread: threading.Thread                       │
│ + start_reservation_cleanup()                                 │
│ + start_notification_worker()                                 │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                 services.email_service.EmailService            │
├───────────────────────────────────────────────────────────────┤
│ + send_reservation_confirmation(db, reservation) -> bool      │
│ + send_password_reset(db, email, token) -> bool               │
│ - _send_email(to_email, subject, html_content)                │
│ - _render_template(template_name, context) -> str             │
└───────────────────────────────────────────────────────────────┘
```

## Clases de Rutas (Endpoints)

```
┌───────────────────────────────────────────────────────────────┐
│                    routes.auth (Router)                        │
├───────────────────────────────────────────────────────────────┤
│ POST /register       -> register_user()                       │
│ POST /login          -> login()                               │
│ POST /forgot-password -> forgot_password()                     │
│ POST /reset-password  -> reset_password()                      │
│ POST /refresh         -> refresh_token()                       │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│              routes.parking.access (Router)                    │
├───────────────────────────────────────────────────────────────┤
│ POST /access/validate-plate -> validate_plate()                │
│ POST /access/exit-plate     -> exit_plate()                    │
│ POST /access/validate-qr    -> validate_qr()                   │
│ POST /access/pay-stay       -> pay_stay()                      │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│              routes.parking.status (Router)                    │
├───────────────────────────────────────────────────────────────┤
│ GET  /parking/status           -> parking_status()             │
│ GET  /parking/current-occupancy-> current_occupancy()          │
│ GET  /parking/branches         -> branches_list()              │
│ WS   /parking/ws               -> parking_ws()                 │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│           routes.admin (Package with sub-routers)             │
├───────────────────────────────────────────────────────────────┤
│  /admin/users.py       -> CRUD users, roles, balance, block   │
│  /admin/branches.py    -> CRUD branches, floors, toggle       │
│  /admin/reservations.py-> CRUD reservations, confirm, cancel  │
│  /admin/promotions.py  -> CRUD promotions, toggle             │
│  /admin/operations.py  -> manual entry/exit, barrier, cancel  │
│  /admin/settings.py    -> prices, capacity settings           │
│  /admin/virtual_time.py-> virtual time control                │
└───────────────────────────────────────────────────────────────┘
```

## Relaciones entre Capas

```
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Routes/    │────►│    Services/     │────►│    Models/       │
│  (Delgadas)  │     │  (Lógica Negocio)│     │  (ORM Entities)  │
│              │     │                  │     │                  │
│  - Valida    │     │  - Orquesta      │     │  - Define tablas │
│  - Llama     │     │  - Calcula       │     │  - Enums         │
│  - Responde  │     │  - Persiste      │     │  - Relaciones    │
└──────────────┘     └──────────────────┘     └──────────────────┘
       │                      │                        │
       │                      ▼                        │
       │             ┌──────────────────┐              │
       │             │  Repositories/   │              │
       │             │  (Data Access)   │              │
       │             └──────────────────┘              │
       │                      │                        │
       ▼                      ▼                        ▼
┌──────────────┐     ┌──────────────────┐     ┌──────────────────┐
│  Schemas/    │     │    core/         │     │     Database     │
│  (Pydantic)  │     │ (Infrastructure) │     │  (SQLite/PG)     │
│              │     │                  │     │                  │
│  - Request   │     │  - Config        │     │  - Persistencia  │
│  - Response  │     │  - Security      │     │  - Consultas     │
│  - Validation│     │  - DB Sessions   │     │  - Índices       │
└──────────────┘     │  - MQTT Client   │     └──────────────────┘
                     └──────────────────┘
```
