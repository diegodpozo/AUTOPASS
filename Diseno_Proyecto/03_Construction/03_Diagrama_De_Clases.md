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
│  │  TimeService                                                       │
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
│ - RESERVA_HORA_MIN_SEGUNDOS: int (default 1800)                │
│ - MAINTENANCE_INTERVAL_SECONDS: int                            │
│ - HEARTBEAT_TIMEOUT_SECONDS: int                               │
│ - IMAGE_DIR: str                                               │
│ - ALLOWED_ORIGINS: list[str]                                   │
│ - CONTACT_SUPPORT: str                                         │
│ - DEFAULT_HOURLY_RATE: float                                   │
│ - DEFAULT_BASE_RATE: float                                     │
│ - RECOVERY_TOKEN_EXPIRE_MINUTES: int                           │
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
│ + validate_plate(db, data, request) -> dict                   │
│ + exit_plate(db, data, request) -> dict                       │
│ + validate_qr(db, data, request) -> dict                      │
│ # _save_image(plate, image_base64) -> str                     │
│ # _publish_mqtt(request, topic, payload)                      │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│              services.reservation_service.ReservationService   │
├───────────────────────────────────────────────────────────────┤
│ + create_reservation(db, data) -> Reservation                 │
│ + update_reservation(db, res_id, data) -> Reservation         │
│ + cleanup_overdue_reservations(db)                            │
│ + auto_finalize_reservations(db, user_id)                     │
│ + auto_finalize_all_reservations(db)                          │
│ + pay_reservation(db, user, res_id)                           │
│ + simulate_refund(db, res) -> dict                            │
│ + cancel_reservation(db, user, res_id)                        │
│ # normalize_name(name) -> str                                 │
│ # verificar_disponibilidad(db, ...) -> bool                   │
│ # _reservar_plaza_en_aforo(db, ...)  [NO-OP v9.5]             │
│ # _liberar_plaza_en_aforo(db, ...)   [NO-OP v9.5]             │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│               services.billing_service.BillingService          │
├───────────────────────────────────────────────────────────────┤
│ + get_rate(db, tipo, sucursal, tipo_vehiculo) -> float        │
│ + get_hourly_rate(db, sucursal, tipo_vehiculo) -> float       │
│ + calculate_debt(entry_time_str, db, sucursal, tipo_vehiculo) │
│ + calculate_total_amount(db, tipo_estadia, fecha_inicio, ...) │
│ + calculate_points(amount) -> int                             │
│ + process_payment(db, plate) -> dict                          │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│            services.notification_service.NotificationService   │
├───────────────────────────────────────────────────────────────┤
│ - _occupancy_manager: OccupancyManager                        │
│ - _event_loop: asyncio.AbstractEventLoop                       │
│ + set_occupancy_manager(manager)                              │
│ + set_event_loop(loop)                                        │
│ + notify_occupancy_change(db, sucursal_norm)                  │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│               services.worker_service.WorkerService            │
├───────────────────────────────────────────────────────────────┤
│ - _cleanup_thread: threading.Thread                            │
│ - _notification_thread: threading.Thread                       │
│ + start_reservation_cleanup()                                 │
│ + start_notification_worker()                                 │
│ # _reservation_cleanup_worker()                               │
│ # _notification_worker()                                      │
│ # _process_reminders(db)                                      │
│ # _process_started_reservations(db)                           │
│ # _process_auto_cancellations(db)                             │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                 services.email_service.EmailService            │
├───────────────────────────────────────────────────────────────┤
│ + send_async_email(to_email, subject, html_content)           │
│ + send_recovery_email(to_email, user_name, recovery_url)      │
│ + send_reservation_confirmation(to_email, user_name, res_data)│
│ + send_reservation_reminder(to_email, user_name, res_data)    │
│ + send_auto_cancelled_notification(to_email, user_name, res)  │
│ # _render_template(template_name, **context) -> str            │
│ # _get_logo_base64() -> str                                   │
│ # _send_email(to_email, subject, html_content)                │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│           services.user_notification_service                   │
│                  .UserNotificationService                      │
├───────────────────────────────────────────────────────────────┤
│ + create_notification(db, user_id, tipo, titulo, mensaje,     │
│                       reserva_id) -> UserNotification          │
│ + get_user_notifications(db, user_id, limit, offset) -> list  │
│ + get_unread_count(db, user_id) -> int                        │
│ + mark_as_read(db, notif_id, user_id) -> bool                 │
│ + mark_all_as_read(db, user_id) -> int                        │
│ + mark_reservation_notifications_as_read(db, user_id,         │
│                                          reserva_id, tipo)    │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│                 services.time_service.TimeService              │
├───────────────────────────────────────────────────────────────┤
│ (clase estatica/classmethod)                                   │
│ + now() -> datetime                                           │
│ + now_str() -> str                                            │
│ + set_offset(seconds: int)                                    │
│ + advance(**kwargs)                                           │
│ + reset()                                                     │
│ + get_offset() -> int                                         │
│ + get_virtual_now() -> str                                    │
│ + is_active() -> bool                                         │
│ + get_info() -> dict                                          │
│ # _load_offset()                                              │
│ # _save_offset()                                              │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│              services.branch_service.BranchService             │
├───────────────────────────────────────────────────────────────┤
│ + get_branch_capacity_summary(db, branch) -> dict             │
│ + list_branches_with_summary(db) -> list                      │
└───────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────┐
│               services.user_service.UserService                │
├───────────────────────────────────────────────────────────────┤
│ + create_user(db, user_data, rol, sucursal) -> User           │
│ + update_user(db, user_id, user_data) -> User                 │
│ + delete_user(db, user_id)                                    │
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
│  (Delgadas)  │     │  (Logica Negocio)│     │  (ORM Entities)  │
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
│  - Validation│     │  - DB Sessions   │     │  - Indices       │
└──────────────┘     │  - MQTT Client   │     └──────────────────┘
                     └──────────────────┘
```
