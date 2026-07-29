# Guía de Desarrollo: Arquitectura Modular

Este documento sirve como mapa técnico tras la gran refactorización. Explica la ubicación de los recursos y las reglas de extensión del sistema.

---

## Organización de Capas

### 1. `core/` (Infraestructura)
Cualquier configuración que afecte a todo el sistema debe ir aquí.
- **Seguridad**: Si añadís un nuevo rol, registralo en `core/security.py`. Las dependencias disponibles son: `get_current_user` (todos autenticados), `get_super_admin` (solo ADMIN), `get_local_manager` (ADMIN/LOCAL_ADMIN), `get_operational_user` (ADMIN/LOCAL_ADMIN/STAFF).
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
| `/v1/auth` | `routes/auth.py` | Login, Register, Forgot/Reset Password. |
| `/v1/admin` | `routes/admin/` | **Modular:** Users CRUD (toggle-block, balance, password, role, delete), Branches CRUD (logo, toggle, floors), Reservations CRUD (confirm-payment, cancel, update), Promotions CRUD (toggle), Operations (manual entry/exit, open-barrier, cancel-stay, manual-entry), Settings (prices, capacity), Virtual Time (status, advance, set, reset). |
| `/v1/user` | `routes/user/` | **Modular:** Profile (get/update, change-password), Vehicles CRUD, Balance (recharge, payment-history, active-stays, rates), Reservations (modify, pay, cancel-simulation, cancel), Fidelization (promotions, redeem, points-history), Notifications (CRUD in-app, unread count, mark read). |
| `/v1/parking`| `routes/parking/`| **Modular:** Access (validate-plate, pay-stay, exit-plate, validate-qr), Status (current-occupancy, branches, ws), Utils (normalize_plate, format_plate). |
| `/v1/reports`| `routes/reports.py` | Resúmenes financieros y logs de acceso. Controlador delgado delegando a `ReportService`. Filtros: `vehicle_type`, `payment_method`, `date_range`. |
| `/v1/system` | `routes/system/` | **Modular:** `common.py` (ConnectionManager, stop_all_cameras), `health.py` (/health, /heartbeat, /reset, /virtual-time), `cameras.py` (CRUD y control dinámico), `video.py` (WebSockets, streaming, capturas). |
| `/` (Vistas) | `routes/views.py` | Renderizado Jinja2 con **Inyección Global de Settings**. |

---

## Desarrollo de Frontend

Para modificar la UI, seguí la nueva estructura de componentes y módulos:
- **Plantillas Email**: `templates/emails/`. Usar Jinja2 para variables dinámicas con QR embebido en base64.
- **Componentes HTML**: `templates/components/` (Navbar, Footers, Modales base).
- **Módulos ES6**: `static/js/modules/`. Toda nueva función lógica debe ir aquí y exportarse como ES6 module.
- **Scripts Puente**: `static/js/*.js`. Actúan como puentes entre módulos y handlers inline, importando módulos y exponiendo funciones al ámbito global (`window.*`) si es necesario.
- **Mapa Interactivo**: Usa Leaflet.js (CDN) para selector de coordenadas en creación de sucursales.
- **Tour de Usuario**: Archivos `tour.js` y `onboarding_helpers.js` para guía interactiva.
- **Sidebar**: Colapsable con persistencia en localStorage (`sidebar-collapsed`).
- **Pase Digital**: Vista de pase con QR en `digital_pass.html`.
- **Puntos**: Barra de progreso con metas escalonadas (500/1000/2500/5000/10000).

### Reglas de JS:
1. **Usar ES6 Modules**: Usá `import` / `export`. No crees funciones globales directamente en los módulos.
2. **Separación Módulo/Puente**: La lógica de negocio va en `modules/`. El script puente solo expone `window.*` y conecta event handlers. Ejemplo:
   ```js
   // modules/dashboard-admin.js (lógica)
   export async function loadUsers() { ... }
   
   // dashboard.js (puente)
   import * as admin from './modules/dashboard-admin.js';
   window.loadUsers = admin.loadUsers;
   ```
3. **Nomenclatura de Módulos**: Usar prefijo `dashboard-` para módulos exclusivos del dashboard admin. Para módulos compartidos (api, utils, ui) no usar prefijo.
4. **Validación de Datos**: Usá la función `validatePlate` de `static/js/modules/utils.js` para cualquier registro de patentes nuevo. Usá `detectVehicleType` para auto-detectar Moto/Auto/Camioneta desde el formato de patente.
5. **Modularización de API**: Toda petición a la red debe usar el módulo `api.js`.
6. **Type Module**: Siempre que añadas un script a un template, usá `<script type="module" src="...">`.
7. **Confirmaciones**: Usá `showConfirm` de `utils.js` para acciones destructivas.
8. **Carga de Pestañas**: Usá `switchTab(tabId, element)` para navegar entre pestañas del dashboard. La función gestiona explícitamente `style.display` y clases CSS para evitar problemas de rendering.

### Reglas de Estilo:
1. **Dorado AutoPass**: `#C5A059`.
2. **Glassmorphism**: Fondo con desenfoque y bordes semi-transparentes.
3. **Voseo**: "Registrate", "Cargá saldo", "Tus puntos".
4. **FAB (Floating Action Button)**: Botón dorado fijo en perfil de usuario. Usar `min-width` + `max-width` en label para animación sin pérdida del icono. Ocultar en "inicio" vía JS (`showSection`).
4. **Modo Edición (UI Pattern)**:
   - Los campos de configuración (ej: tarifas) deben estar deshabilitados por defecto (`disabled`).
   - Usar un botón único "EDITAR" que habilita los campos y cambia la etiqueta a "APLICAR".
   - Al aplicar, disparar `showConfirm` con resumen. El sistema guarda y vuelve a bloquear los campos automáticamente.
5. **Reportes Financieros**: Al agregar nuevos reportes o filtros, asegurar la integración de `vehicle_type` y `payment_method` ('all', 'DIGITAL', 'CAJA').
6. **Gestión de Cámaras**: UI con botones Play/Stop por cámara, input de IP, indicador de estado (conectado/desconectado).
7. **Centro de Monitoreo Dinámico**:
   - Fondo `#000000` y bordes finos `#ffffff` (cambian a `#00bcd4` al hacer hover).
   - Sin cabecera superior: barra de mandos flotante a la derecha con posición fija (`.cctv-floating-controls`).
   - Rejilla adaptativa: las cámaras ocupan el mismo tamaño y la grilla se ajusta según la cantidad (1x1, 2x1, 2x2, 3x2, 3x3).
   - Identificadores de función visibles en la cabecera de cada slot (ej: `[LECTURA PATENTE (ENTRADA)]`).
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
2. **Modo Simulación**: Configurar `VIDEO_SOURCE` con la ruta de un archivo de video para desarrollo.
3. **Configuración de Cámara**: La IP se guarda en `Settings` con clave `camara_ip_<entrada|salida>`.
4. **Video WebSocket**: Los frames se envían a `/v1/system/ws/video/{gate_id}` con token JWT como query param.
5. **Virtual Time**: Para testing, usar los endpoints de virtual time (`/v1/admin/virtual-time/*`) en lugar de alterar el reloj del sistema.

---

## Pruebas (Tests)
Para correr las pruebas tras un cambio:
```bash
.\venv\Scripts\python.exe -m pytest tests/ -v
```
Tests disponibles en `tests/`:
- `test_access_service.py`: Validación de placas, entrada/salida
- `test_billing_service.py`: Cálculo de tarifas/estadías
- `test_branch_service.py`: CRUD de sucursales, aforo, pisos
- `test_reservation_service.py`: Creación, estados de reservas
- `test_user_service.py`: CRUD de usuarios, roles

---

## ⚠️ MANDATOS ARQUITECTÓNICOS (V9.6.0+)
Para mantener la integridad del sistema a futuro, todo nuevo desarrollo DEBE cumplir estrictamente con lo siguiente:

1. **Arquitectura Limpia (Clean Architecture):**
   - **Rutas (`routes/`):** "Delgadas". Validación vía `schemas/`, llamada al servicio.
   - **Servicios (`services/`):** Lógica de negocio pesada, orquestación.
   - **Modelos (`models/`):** Entidades de BD y Enums.

2. **Cero Hardcoding:**
   - Valores configurables deben ir en `core/config.py` cargados desde `.env`.

3. **Modularización Backend y Frontend:**
   - Backend: Evitá acoplamiento circular. Cada servicio es independiente.
   - Frontend: Lógica de negocio en `modules/`, puente delgado en scripts raíz. No duplicar lógica entre módulos.

4. **Tipado Seguro:**
   - Usar SIEMPRE Enums (`models/enums.py`). Prohibido usar strings literales para estados o tipos.

5. **Testing Obligatorio:**
   - Todo nuevo servicio debe incluir pruebas en `tests/`.

6. **Aforo Diferenciado por Tipo de Reserva:**
   - **Reservas por hora**: La plaza se descuenta al entrar (en `AccessService`) y se libera al salir.
   - **Reservas no horarias (Día/Semana/Quincena/Mes)**: La plaza se descuenta al pagar (en `pay_reservation`) y se libera solo al vencer (`auto_finalize_all_reservations`) o cancelar. La salida física nunca debe modificar el aforo para estas reservas.
   - Usar siempre los helpers `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` en `reservation_service.py` para gestionar estas operaciones.

7. **Consistencia JS:**
   - No modificar `window.*` desde módulos ES6. Solo los scripts puente asignan al scope global.
   - Validar que los módulos pasen `node --check` antes de commitear.
