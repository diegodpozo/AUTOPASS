# Guía de Desarrollo: Arquitectura Modular

Este documento sirve como mapa técnico tras la gran refactorización. Explica la ubicación de los recursos y las reglas de extensión del sistema.

---

## Organización de Capas

### 1. `core/` (Infraestructura)
Cualquier configuración que afecte a todo el sistema debe ir aquí.
- **Seguridad**: Si añadís un nuevo rol, registralo en `core/security.py`. Las dependencias disponibles son: `get_current_user` (todos autenticados), `get_local_manager` (ADMIN/LOCAL_ADMIN), `get_operational_user` (ADMIN/LOCAL_ADMIN/STAFF).
- **Config**: Si añadís una API Key o variable al `.env`, definila en `core/config.py`. Variables existentes: `RESERVA_HORA_MIN_SEGUNDOS`, `MAINTENANCE_INTERVAL_SECONDS`, `SMTP_*` (server, port, user, password), `MQTT_*` (broker, topics), `DATABASE_URL`.
- **MQTT**: Usa `CallbackAPIVersion.VERSION2` de Paho. El cliente se crea sin callbacks globales en `core/mqtt.py`.
- **Seed**: `core/seed.py` incluye `INITIAL_USERS` (admin con DNI, admins de sucursal), `DEFAULT_PRICES` (tarifas trimodales incluyendo `camioneta`), `INITIAL_PROMOS` (3 promos iniciales con icono y categoría). La función `seed()` parchea datos existentes sin duplicar.

### 2. `models/` y `schemas/` (Datos)
- **Regla**: Siempre que crees una tabla nueva, hacelo en un archivo dentro de `models/` y exportalo en `models/__init__.py`.
- **Validación**: Toda entrada de datos a la API debe tener un esquema en `schemas/`. Usá `@field_validator` para lógica de validación.

### 3. `services/` (Cerebro)
- **IMPORTANTE**: No pongas lógica de cálculo de precios o validación de stock en los routers. Creá un método estático en un servicio dentro de `services/`.
- **Aforo por Reserva**: Las reservas no horarias (Día/Semana/Quincena/Mes) descuentan la plaza del aforo al iniciar el período (`fecha_inicio`), no al pagar. Si la reserva es futura, el worker (`_process_started_reservations`) descuenta la plaza cuando arranca. La salida física NO libera la plaza — la liberación ocurre al vencer (`auto_finalize_all_reservations`) o al cancelar. Para reservas por hora, la plaza se descuenta al entrar y se libera al salir.

---

## Mapa de Rutas (Endpoints Modularizados)

| Prefijo | Paquete/Archivo | Responsabilidad |
| :--- | :--- | :--- |
| `/v1/auth` | `routes/auth.py` | Login, Register, Forgot/Reset Password, Refresh Token. |
| `/v1/admin` | `routes/admin/` | **Modular:** Users CRUD (toggle-block, balance, password, role, delete), Branches CRUD (logo, toggle, floors), Reservations CRUD (confirm-payment, cancel, update), Promotions CRUD (toggle), Operations (manual entry/exit, open-barrier, cancel-stay, manual-entry), Settings (prices, capacity). |
| `/v1/user` | `routes/user/` | **Modular:** Profile (get/update, change-password), Vehicles CRUD, Balance (recharge, payment-history, active-stays, rates), Reservations (modify, pay, cancel-simulation, cancel), Fidelization (promotions, redeem, points-history). |
| `/v1/parking`| `routes/parking/`| **Modular:** Access (validate-plate, pay-stay, exit-plate, validate-qr), Status (current-occupancy, branches, ws), Utils (normalize_plate, format_plate). |
| `/v1/reports`| `routes/reports.py` | Resúmenes financieros y logs de acceso. Filtros: `vehicle_type`, `payment_method`, `date_range`. |
| `/v1/system` | `routes/system.py` | Health, Heartbeat ALPR, Camera config/service/start/stop, Video feeds, WebSocket video, Capture, System Reset. |
| `/` (Vistas) | `routes/views.py` | Renderizado Jinja2 con **Inyección Global de Settings**. |

---

## Desarrollo de Frontend

Para modificar la UI, seguí la nueva estructura de componentes y módulos:
- **Plantillas Email**: `templates/emails/`. Usar Jinja2 para variables dinámicas con QR embebido en base64.
- **Componentes HTML**: `templates/components/` (Navbar, Footers, Modales base).
- **Lógica JS (Módulos)**: `static/js/modules/`. Toda nueva función lógica debe ir aquí y exportarse.
- **Scripts de Página**: `static/js/*.js`. Actúan como puentes, importando módulos y exponiendo funciones al ámbito global si es necesario.
- **Mapa Interactivo**: Usa Leaflet.js (CDN) para selector de coordenadas en creación de sucursales.
- **Tour de Usuario**: Archivos `tour.js` y `onboarding_helpers.js` para guía interactiva.
- **Sidebar**: Colapsable con persistencia en localStorage (`sidebar-collapsed`).
- **Pase Digital**: Vista de pase con QR en `digital_pass.html`.
- **Puntos**: Barra de progreso con metas escalonadas (500/1000/2500/5000/10000).

### Reglas de JS:
1. **Usar ES6 Modules**: Usá `import` / `export`. No crees funciones globales directamente en los módulos.
2. **Validación de Datos**: Usá la función `validatePlate` de `static/js/modules/utils.js` para cualquier registro de patentes nuevo. Usá `detectVehicleType` para auto-detectar Moto/Auto/Camioneta desde el formato de patente.
3. **Modularización de API**: Toda petición a la red debe usar el módulo `api.js`.
4. **Type Module**: Siempre que añadas un script a un template, usá `<script type="module" src="...">`.
5. **Confirmaciones**: Usá `showConfirm` de `utils.js` para acciones destructivas.

### Reglas de Estilo:
1. **Dorado AutoPass**: `#C5A059`.
2. **Glassmorphism**: Fondo con desenfoque y bordes semi-transparentes.
3. **Voseo**: "Registrate", "Cargá saldo", "Tus puntos".
4. **Modo Edición (UI Pattern)**:
   - Los campos de configuración (ej: tarifas) deben estar deshabilitados por defecto (`disabled`).
   - Usar un botón único "EDITAR" que habilita los campos y cambia la etiqueta a "APLICAR".
   - Al aplicar, disparar `showConfirm` con resumen. El sistema guarda y vuelve a bloquear los campos automáticamente.
5. **Reportes Financieros**: Al agregar nuevos reportes o filtros, asegurar la integración de `vehicle_type` y `payment_method` ('all', 'DIGITAL', 'CAJA').
6. **Gestión de Cámaras**: UI con botones Play/Stop por cámara, input de IP, indicador de estado (conectado/desconectado).
7. **Monitoreo de Salud**: Puntos de indicador (verde/rojo) para servicios del sistema en dashboard.

---

## Convenciones Multi-Sucursal (Aislamiento)
1. **Nombres Completos**: Al interactuar con la DB, usá siempre el nombre completo de la sucursal.
2. **Seguridad en Rutas**: Usá siempre las dependencias `get_local_manager` o `get_operational_user`.
3. **Settings por Sucursal**: El modelo `Settings` tiene campo `sucursal` para aislar configuraciones por sucursal. Usar `valor_str` para valores de texto (ej: IP de cámara).
4. **Aforo por Sucursal**: `ParkingAforo` y `ParkingFloor` tienen campo `sucursal` para aislamiento de capacidad.

## Convenciones de Email
1. **Templates**: Ubicados en `templates/emails/`, usar Jinja2 con herencia de `templates/emails/base_email.html`.
2. **QR en Base64**: Para emails de confirmación, generar QR como imagen base64 embebida.
3. **Logo**: El logo de la sucursal se incluye como `cid:logo` en el email.
4. **Servicio**: Usar `services/email_service.py` con `send_email` que soporta HTML y attachments.

## Convenciones ALPR
1. **No ejecutar `alpr_service.py` directamente en producción**: El backend lo inicia como proceso hijo al presionar Play en el dashboard.
2. **Heartbeat**: Toda instancia ALPR debe enviar heartbeat a `/v1/system/heartbeat` cada N segundos. El backend monitorea en `/v1/system/health`.
3. **Modo Simulación**: Usar `SCREEN_TO_SCREEN` para desarrollo (reproduce un video de archivo).
4. **Configuración de Cámara**: La IP se guarda en `Settings` con clave `camara_ip_<entrada|salida>`.
5. **Video WebSocket**: Los frames se envían a `/v1/system/ws/video/{gate_id}` con token JWT como query param.

---

## Pruebas (Tests)
Para correr las pruebas tras un cambio:
```bash
.\venv\Scripts\python.exe test_user_flow.py
.\venv\Scripts\python.exe test_multi_branch_rbac.py
```

---

## ⚠️ MANDATOS ARQUITECTÓNICOS (V9.2.0+)
Para mantener la integridad del sistema a futuro, todo nuevo desarrollo DEBE cumplir estrictamente con lo siguiente:

1. **Arquitectura Limpia (Clean Architecture):**
   - **Rutas (`routes/`):** "Delgadas". Validación vía `schemas/`, llamada al servicio.
   - **Servicios (`services/`):** Lógica de negocio pesada, orquestación.
   - **Modelos (`models/`):** Entidades de BD y Enums.

2. **Cero Hardcoding:**
   - Valores configurables deben ir en `core/config.py` cargados desde `.env`.

3. **Modularización:**
   - Evitá el acoplamiento circular.

4. **Tipado Seguro:**
   - Usar SIEMPRE Enums (`models/enums.py`). Prohibido usar strings literales para estados o tipos.

5. **Testing Obligatorio:**
   - Todo nuevo servicio debe incluir pruebas en `tests/`.

6. **Aforo Diferenciado por Tipo de Reserva:**
   - **Reservas por hora**: La plaza se descuenta al entrar (en `AccessService`) y se libera al salir.
   - **Reservas no horarias (Día/Semana/Quincena/Mes)**: La plaza se descuenta al pagar (en `pay_reservation`) y se libera solo al vencer (`auto_finalize_all_reservations`) o cancelar. La salida física nunca debe modificar el aforo para estas reservas.
   - Usar siempre los helpers `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` en `reservation_service.py` para gestionar estas operaciones.
