# Guía de Desarrollo: Arquitectura Modular

Este documento sirve como mapa técnico tras la gran refactorización. Explica la ubicación de los recursos y las reglas de extensión del sistema.

---

## Organización de Capas

### 1. `core/` (Infraestructura)
Cualquier configuración que afecte a todo el sistema debe ir aquí.
- **Seguridad**: Si añadís un nuevo rol, registralo en `core/security.py`. Las dependencias disponibles son: `get_current_user` (todos autenticados), `get_super_admin` (solo ADMIN), `get_local_manager` (ADMIN/LOCAL_ADMIN), `get_operational_user` (ADMIN/LOCAL_ADMIN/STAFF).
- **Config**: Si añadís una API Key o variable al `.env`, definila en `core/config.py`. Variables existentes: `RESERVA_HORA_MIN_SEGUNDOS`, `MAINTENANCE_INTERVAL_SECONDS`, `SMTP_*` (server, port, user, password), `MQTT_*` (broker, topics), `DATABASE_URL`, `MP_*` (access_token, public_key, webhook_url, preference_expire_minutes). **MP Checkout Pro exige `BASE_URL` con `https://`** (rechaza `http://` en `back_urls`); para pruebas locales usá un túnel (cloudflared vía `acceso_remoto.bat`) y probá logueado en el dominio del túnel (la sesión de AUTOPASS es por origen).
- **MQTT**: Usa `CallbackAPIVersion.VERSION2` de Paho. El cliente se crea sin callbacks globales en `core/mqtt.py`.
- **Seed**: `core/seed.py` incluye `INITIAL_USERS` (admin con DNI, admins de sucursal), `DEFAULT_PRICES` (tarifas trimodales incluyendo `camioneta`), `INITIAL_PROMOS` (3 promos iniciales con icono y categoría). La función `seed()` parchea datos existentes sin duplicar.
- **Caché**: `core/cache.py` provee `SimpleTTLCache` (TTL 5s). `BillingService.get_rate` ya usa `ttl_cache` para no recalcular tarifas en picos de carga.

### 2. `models/` y `schemas/` (Datos)
- **Regla**: Siempre que crees una tabla nueva, hacelo en un archivo dentro de `models/` y exportalo en `models/__init__.py`.
- **Validación**: Toda entrada de datos a la API debe tener un esquema en `schemas/`. Usá `@field_validator` para lógica de validación.

### 3. `services/` (Cerebro)
- **IMPORTANTE**: No pongas lógica de cálculo de precios o validación de stock en los routers. Creá un método estático en un servicio dentro de `services/`.
- **Aforo Solo Físico (v9.5+)**: Las reservas no horarias (Día/Semana/Quincena/Mes) **no** descuentan plaza del aforo ni al pagar ni al iniciar el período. El conteo de ocupación lo maneja exclusivamente el ALPR/ingreso manual (incrementa en ENTRADA, decrementa en SALIDA) reflejando solo vehículos físicamente presentes. No modificar este comportamiento sin revisar el refactor v9.5.0.
- **Disponibilidad de Reserva (v9.14.1+)**: La disponibilidad del selector de reservas se valida contra los **cupos exclusivos de reserva** (`capacidad_reservas_*`/`ocupacion_reservas_*` en `ParkingAforo` y `ParkingFloor`, migración `e6f7a8b9c0d1`), NO contra el aforo físico. Usá `verificar_disponibilidad`, `obtener_fechas_deshabilitadas` y `obtener_horas_deshabilitadas` de `services/reservation_service.py` (sweep-line + cache TTL) y los endpoints `/reservations/check-availability`, `/reservations/disabled-dates` y `/reservations/disabled-hours`. Todos comparten la lógica por tipo de vehículo y solapamiento en el rango.

---

## Mapa de Rutas (Endpoints Modularizados)

| Prefijo | Paquete/Archivo | Responsabilidad |
| :--- | :--- | :--- |
| `/v1/auth` | `routes/auth.py` | Login, Register, Forgot/Reset Password, **Login social OAuth** (providers/authorize/callback/complete vía `services/oauth_service.py`). |
| `/v1/admin` | `routes/admin/` | **Modular:** Users CRUD (toggle-block, balance, password, role, delete), Branches CRUD (logo, toggle, floors; **renombre con propagación** a Aforo/Settings/User/Reservations/AccessLog/SupportTickets/Cámaras/Promociones + remapeo `CAMERA_SOURCE_*` y detención de subprocesos ALPR si el prefijo cambia), Reservations CRUD (confirm-payment, cancel, update, validación de disponibilidad exclusiva), Promotions CRUD (toggle), Operations (manual entry/exit, open-barrier, cancel-stay), Settings (prices, capacity, cupos de reserva), Virtual Time (status, advance, rewind, set-target, set, reset — LOCAL_ADMIN+), Support (listar/detalle/pending-count/responder tickets, marcar notifs leídas). |
| `/v1/user` | `routes/user/` | **Modular:** Profile (get/update, change-password), Vehicles CRUD, Balance (recharge, payment-history, active-stays, rates), Reservations (modify, pay, cancel-simulation, cancel, confirm-reminder, **check-availability, disabled-dates, disabled-hours**), Fidelization (promotions, redeem, redemption-tickets, redemptions available/cancel, points-history), Notifications (CRUD in-app, unread count, mark read, read-all, clear-read), Support (crear/consultar/detalle propio/responder), Mercado Pago (checkout, callbacks success/pending/failure, webhook). |
| `/v1/parking`| `routes/parking/`| **Modular:** Access (validate-plate, pay-stay con `metodo=DIGITAL\|CAJA`, exit-plate, validate-qr), Status (current-occupancy con `capacidad_reservas_*`/`disponibilidad_reservas_*`, branches, ws), Utils (normalize_plate, format_plate). |
| `/v1/reports`| `routes/reports.py` | Resúmenes financieros, logs de acceso y estadísticas OCR. Controlador delgado delegando a `ReportService`. Filtros: `vehicle_type`, `payment_method`, `date_range`. |
| `/v1/system` | `routes/system/` | **Modular:** `common.py` (ConnectionManager, stop_all_cameras), `health.py` (/health, /heartbeat, /reset, /virtual-time), `cameras.py` (CRUD y control dinámico, camera-reading), `video.py` (WebSockets, streaming, capturas). |
| `/` (Vistas) | `routes/views.py` | Renderizado Jinja2 con **Inyección Global de Settings**. |

---

## Desarrollo de Frontend

Para modificar la UI, seguí la nueva estructura de componentes y módulos:
- **Plantillas Email**: `templates/emails/`. Usar Jinja2 para variables dinámicas con QR embebido en base64.
- **Componentes HTML**: `templates/components/` (Navbar, Footers, Modales base).
- **Módulos ES6**: `static/js/modules/`. Toda nueva función lógica debe ir aquí y exportarse como ES6 module.
- **Scripts Puente**: `static/js/*.js`. Actúan como puentes entre módulos y handlers inline, importando módulos y exponiendo funciones al ámbito global (`window.*`) si es necesario.
- **Mapa Interactivo**: Usa Leaflet.js (CDN) para selector de coordenadas en creación de sucursales.
- **Tour de Usuario**: Archivos `tour.js` y `onboarding-helpers.js` para guía interactiva.
- **Sidebar**: Colapsable con persistencia en localStorage (`sidebar-collapsed`).
- **Pase Digital**: Vista de pase con QR renderizada como sección/modal dentro de `perfil.html` (módulo `reservas-pass.js`), no como template separado.
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
5. **Reportes Financieros**: Al agregar nuevos reportes o filtros, asegurar la integración de `vehicle_type` y `payment_method` ('all', 'DIGITAL', 'CAJA'). El resumen financiero expone `recaudado_efectivo` y `recaudado_digital` (ver `_logs_agg` en `services/report_service.py`); el desglose respeta los filtros aplicados (si el filtro es solo `CAJA`, lo digital va en 0 y viceversa).
6. **Gestión de Cámaras**: UI con botones Play/Stop por cámara, input de IP, indicador de estado (conectado/desconectado).
7. **Centro de Monitoreo Dinámico**:
   - Fondo `#000000` y bordes finos `#ffffff` (cambian a `#00bcd4` al hacer hover).
   - Sin cabecera superior: barra de mandos flotante a la derecha con posición fija (`.cctv-floating-controls`).
   - Rejilla adaptativa: las cámaras ocupan el mismo tamaño y la grilla se ajusta según la cantidad (1x1, 2x1, 2x2, 3x2, 3x3).
   - Identificadores de función visibles en la cabecera de cada slot (ej: `[LECTURA PATENTE (ENTRADA)]`).
7. **Monitoreo de Salud**: Puntos de indicador (verde/rojo) para servicios del sistema en dashboard.

### Tarjetas de Monitoreo (Vehicle Stats Cards - v9.14.1)
Refactorización completa de las tarjetas de ocupación Autos/Motos/Camionetas. Ubicación: `templates/dashboard/tabs/live.html` (estructura) y `static/css/pages/dashboard/dashboard-live.css` (estilos).

**Estructura HTML:**
```html
<div class="vehicle-stats-grid">
  <div class="vehicle-stat-card">
    <div class="vehicle-stat-header">
      <div class="vehicle-stat-icon"><i class="fas fa-car"></i></div>
      <span class="vehicle-stat-title">AUTOS</span>
    </div>
    <div class="vehicle-stat-metrics">
      <div class="metric-row metric-general">
        <span class="metric-label">General:</span>
        <span class="metric-value" id="stat-free-total">-- / --</span>
      </div>
      <div class="metric-row metric-reservas">
        <span class="metric-label"><i class="fas fa-bookmark"></i> Reservas:</span>
        <span class="metric-value" id="stat-res-autos-val">-- / --</span>
      </div>
    </div>
  </div>
</div>
```

**Características:**
- Grilla responsiva: 3 cols (desktop) → 2 cols (tablet 1200px) → 1 col (mobile 768px)
- Proporcionamiento uniforme con gap consistente (16px)
- Dos filas de métricas: "General" (gris) y "Reservas" (dorado)
- Hover effects suave con transiciones cubic-bezier
- Iconos dinámicos con fondo glassmorphic
- Valores en monospace (`var(--font-mono)`) para mejor legibilidad

**Clases CSS principales:**
- `.vehicle-stats-grid`: Contenedor grid responsivo
- `.vehicle-stat-card`: Tarjeta individual con gradiente 135deg
- `.vehicle-stat-header`: Header con icono + título centrado
- `.vehicle-stat-icon`: Icono 42x42 con fondo dorado suave
- `.metric-row`: Fila de métrica con padding 8px
- `.metric-general` / `.metric-reservas`: Variantes de color (gris/dorado)
- `.metric-label` / `.metric-value`: Etiqueta y valor

**Remoción de Progreso (v9.14.1):**
Las barras de progreso fueron removidas completamente (`progress-bar`, `progress-fill`) en favor de un diseño más limpio enfocado en métricas numéricas.

---

## Convenciones Multi-Sucursal (Aislamiento)
1. **Nombres Completos**: Al interactuar con la DB, usá siempre el nombre completo de la sucursal.
2. **Seguridad en Rutas**: Usá siempre las dependencias `get_local_manager` o `get_operational_user`.
3. **Settings por Sucursal**: El modelo `Settings` tiene campo `sucursal` para aislar configuraciones por sucursal. Usar `valor_str` para valores de texto (ej: IP de cámara).
4. **Aforo por Sucursal**: `ParkingAforo` y `ParkingFloor` tienen campo `sucursal` para aislamiento de capacidad.
5. **Renombre de Sucursal**: La edición del nombre (`PATCH /v1/admin/branches/{id}`) valida unicidad y **propaga** el cambio a `ParkingAforo`, `Settings`, `User`, `Reservation.sucursal_nombre`, `AccessLog.sucursal`, `SupportTicket.sucursal`, `ParkingCamera.sucursal` y `Promotion.sucursal`. El gate_id de cada cámara usa el prefijo normalizado del nombre de sucursal (`{normalize_name(sucursal)}_{TIPO}_{id}`): si ese prefijo cambia, el renovar remapea las claves legacy `Settings.CAMERA_SOURCE_*` y detiene los subprocesos ALPR con el prefijo viejo (los espectadores no recibirían frames). Si agregás una tabla nueva con referencia por nombre de sucursal, incluirla en esa propagación. Ya no se exige el prefijo "AUTOPASS" en el nombre.

## Convenciones OAuth (Login Social)
1. **Proveedores**: Registrar cada proveedor en `_PROVIDERS` (`services/oauth_service.py`). El estado (CSRF) se firma con HMAC sobre `SECRET_KEY` (stateless, sin cookies); no cambiar el formato `<provider>.<nonce>.<exp>.<sig>` sin actualizar `sign_state`/`verify_state`.
2. **Credenciales**: `GOOGLE_OAUTH_*` y `FACEBOOK_OAUTH_*` en `.env`. La `redirect_uri` debe ser exactamente `{BASE_URL}/v1/auth/oauth/{provider}/callback`. Con túnel cloudflared, `BASE_URL` debe ser el dominio público del túnel. Sin credenciales el proveedor queda oculto (el frontend consulta `/v1/auth/oauth/providers`).
3. **Usuarios nuevos**: No crear el usuario en el callback. Emitir `code` JWT con `purpose="oauth_signup"` y delegar el alta a `complete_oauth_signup` (valida DNI/teléfono y unicidad de email/dni). El password se genera aleatorio (acceso solo por red social; la recuperación queda disponible).
4. **Redirección al frontend**: Usar SIEMPRE el fragmento `#oauth_*` (nunca query string) para evitar exponer tokens en logs; limpiar el hash en el cliente tras procesarlo.

## Convenciones de Email
1. **Templates**: Ubicados en `templates/emails/`, templates Jinja2 autocontenidos (no existe `base_email.html`): `reservation_confirmation.html`, `reservation_reminder.html`, `reservation_auto_cancelled.html` y `recovery.html`.
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
Tests disponibles en `tests/` (**82 pruebas en 21 archivos**):
- `test_access_service.py`: Validación de placas, entrada/salida
- `test_admin_reservations.py`: CRUD de reservas admin (búsqueda, creación, edición, confirmación de pago con método, simulación y reembolso de cancelación)
- `test_alpr_aspect_ratio_filter.py`: Filtro de aspecto (área de placa)
- `test_alpr_hallucination_prevention.py`: Prevención de alucinaciones OCR
- `test_alpr_overlay.py`: Overlay de detecciones en frames
- `test_alpr_queue_flush.py`: Cola de frames / drop-oldest
- `test_alpr_utils.py`: Utilidades ALPR (normalización, formatos, país)
- `test_billing_service.py`: Cálculo de tarifas/estadías
- `test_branch_service.py`: CRUD de sucursales, aforo, pisos
- `test_mercadopago.py`: Checkout MP (estadía/reserva, BASE_URL https obligatorio, confirmación idempotente, 503 sin credenciales)
- `test_new_validations.py`: Validaciones de integridad (v9.9.8: vehículos, usuarios, pisos, doble reserva)
- `test_notifications.py`: CRUD de notificaciones, respuestas de soporte, borrado y filtros
- `test_oauth.py`: Ciclo de OAuth 2.0 social login (Google/Facebook, state HMAC, registro DNI/teléfono)
- `test_rate_limiting.py`: SlowAPI (login/register/recuperación)
- `test_reservation_availability_logic.py`: Lógica de disponibilidad de reservas
- `test_reservation_service.py`: Creación, estados de reservas
- `test_reservation_spots.py`: Cupos/ocupación de reservas
- `test_routes_auth.py`: Endpoints de auth con `TestClient` (login, registro, tokens)
- `test_support_service.py`: CRUD de tickets de soporte, permisos por rol, adjuntos
- `test_user_service.py`: CRUD de usuarios, roles, soft delete
- `test_virtual_time.py`: Tiempo virtual (avance/set/reset con offset)

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

6. **Aforo Solo Físico (v9.5+):**
   - La ocupación se gestiona **exclusivamente** con los eventos de acceso (ALPR/ingreso manual): ENTRADA incrementa `ocupacion_actual`, SALIDA la decrementa. Refleja solo vehículos físicamente presentes.
   - Las reservas no horarias (Día/Semana/Quincena/Mes) **no** pre-ocupan plaza. Desde v9.34.55 los helpers `_reservar_plaza_en_aforo` y `_liberar_plaza_en_aforo` se eliminaron por completo; no reintroducir la pre-ocupación sin autorización.

6b. **Cupos Exclusivos de Reserva (v9.14.1+):**
   - La **disponibilidad de reserva** se calcula contra los cupos dedicados `capacidad_reservas_*`/`ocupacion_reservas_*` (PB en `ParkingAforo` + pisos en `ParkingFloor`), no contra el aforo físico. Migración: `e6f7a8b9c0d1`.
   - Centralizar toda validación en `verificar_disponibilidad` (sweep-line, `exclude_id` para ediciones), `obtener_fechas_deshabilitadas` (ventana 90 días) y `obtener_horas_deshabilitadas` (paso 30 min, respeta `RESERVA_HORA_MIN_SEGUNDOS`).
   - No confundir `ocupacion_reservas_*` (cupos de reserva) con `ocupacion_actual` (aforo físico): son independientes.
   - **Reporte (v9.20.0):** `routes/parking/status.py` reporta los cupos de reserva como `max(física ALPR, reservas pagadas vigentes)` vía `_ocupacion_reservas_vigentes` (reservas `Pagado`, `Pendiente`/`Activa`, ventana actual). Aplica a `/parking/status`, WS en vivo y `/parking/branches`. El aforo físico no cambia.
   - Al validar en rutas admin/user, delegar siempre al servicio; nunca hardcodear los defaults 5/3/2/10.

7. **Consistencia JS:**
   - No modificar `window.*` desde módulos ES6. Solo los scripts puente asignan al scope global.
   - Validar que los módulos pasen `node --check` antes de commitear.
