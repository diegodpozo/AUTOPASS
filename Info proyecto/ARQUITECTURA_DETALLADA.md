# Arquitectura del Sistema: AUTOPASS

Este documento detalla la estructura técnica y el flujo de datos del ecosistema de estacionamiento inteligente con **Arquitectura Limpia** (v9.2.0).

---

## Estructura de Directorios

El proyecto sigue una organización basada en la separación de responsabilidades:

```text
AUTOPASS/
├── core/ # Infraestructura (Configuración, Seguridad, DB, MQTT)
├── models/ # Entidades SQLAlchemy + Enums (Domain Layer)
├── schemas/ # Validación Pydantic
├── routes/ # Endpoints (Transport Layer - Delgados)
├── services/ # Inteligencia de Negocio (Service Layer - Gruesos)
├── tests/ # Pruebas unitarias (pytest)
└── main.py # Orquestador
```

---

## Capas y Responsabilidades (v9.2.0)

### 1. Capa de Servicios (Service Layer)
Toda la lógica de negocio se ha centralizado en archivos bajo `services/`:
- **`AccessService`**: Gestiona toda la lógica de validación de patentes, salidas y QR. Integra con el aforo: no incrementa ocupación si el vehículo tiene reserva no horaria pagada (ya se reservó en el pago); no libera en salida si la reserva sigue vigente.
- **`ReservationService`**: Gestiona el ciclo de vida de las reservas (creación, edición, cancelación con reembolsos proporcionales). Al pagar una reserva no horaria, reserva la plaza en el aforo. Al cancelar o vencer, la libera.
- **`BillingService`**: Motor de tarifas y cálculo de puntos por fidelización.
- **`UserService`**: Gestión administrativa de usuarios y validaciones de seguridad.
- **`BranchService`**: Lógica de gestión de sucursales y aforos.
- **`EmailService`**: Envío de emails transaccionales con templates Jinja2 (confirmación de reserva con QR embebido, recuperación de contraseña, logo en base64).
- **`NotificationService`**: Sistema de notificaciones asíncronas vía WebSockets con aislamiento por sucursal para actualización en tiempo real del aforo. Usa un `asyncio.Queue` por sala.
- **`WorkerService`**: Hilo de fondo que ejecuta `auto_finalize_all_reservations` cada `MAINTENANCE_INTERVAL_SECONDS` (default 300s). Libera plazas de aforo de reservas vencidas y limpia reservas expiradas no pagadas.

### 2. Capa de Datos (Modelos y Enums)
- **Seguridad de Tipos:** Se han implementado Enums en `models/enums.py` para eliminar "strings mágicos" (ej: `UserRole`, `VehicleType`, `ReservationStatus`).
- **Gestión Vertical:** Soporte para sucursales con múltiples pisos (`ParkingFloor`), cada uno con capacidad independiente para autos y motos (`capacidad`, `capacidad_motos`, `ocupacion`, `ocupacion_motos`).
- **Fidelización:** Modelos `Promotion` (catálogo de beneficios con icono, categoría, sucursal, activa) y `Coupon` (cupones generados por canje de puntos).
- **Configuración Dinámica:** Modelo `Settings` (key-value store con `valor_str` para configuraciones de texto como IPs de cámaras, y aislamiento por sucursal).
- **Normalización de Patentes:** Campo `normalized_patente` en `AccessLog` para búsquedas eficientes, con funciones `normalize_plate`/`format_plate` en `routes/parking/utils.py` que soportan formatos MERCOSUR (Argentina, Brasil, Uruguay, Paraguay).
- **Soporte Trimodal:** `VehicleType` incluye `CAMIONETA` además de `AUTO` y `MOTO`. `ParkingAforo` y `ParkingFloor` tienen `capacidad_motos` y `ocupacion_motos`.
- **Pago y Liquidación:** `AccessLog` incluye `costo_estadia`, `metodo_pago` ('DIGITAL'/'CAJA'), `fecha_pago`, `pago_confirmado`, `status`, `floor_id`.
- **Sucursales Geo-localizadas:** `ParkingBranch` incluye `logo_url`, `activa`, `latitude`, `longitude` para mapa interactivo y toggle de activación.
- **Reservas:** `Reservation` incluye `monto_reembolsado`, `sucursal_info` (JSON), `cliente_nombre`, `tipo_estadia`.
- **Usuarios:** `User` incluye `apellido`, `dni`, `telefono`, `direccion`, `saldo`, `is_blocked` para bloqueo administrativo.

---

### 3. Capa de Servicio ALPR (`alpr_service.py`)
Servicio independiente de visión artificial que corre como proceso hijo:
- **Sistema de Consenso:** Buffer de votos (múltiples lecturas de la misma patente) antes de enviar al backend para evitar falsos positivos.
- **Detección de QR:** Escaneo directo de QR en cada frame (Quick QR), alternativa a patente.
- **Heartbeat:** Envía pulsos periódicos (`/v1/system/heartbeat`) para monitoreo de salud de cámaras.
- **Video WebSocket:** Envía frames en tiempo real al backend (`/v1/system/ws/video/{gate_id}`) para visualización en dashboard.
- **Cola de Frames:** Política drop-oldest para no acumular frames sin procesar.
- **Detección de Movimiento:** Ignora frames estáticos para optimizar procesamiento.
- **Recorte MERCOSUR:** Detecta y recorta la banda azul de patentes MERCOSUR para mejorar OCR.
- **ROI (Region of Interest):** Múltiples estrategias de detección de región de placa.
- **Imágenes de Debug:** Guarda imágenes de patentes aceptadas (solo Argentina).
- **Des-duplicación:** Cooldown por patente para no re-enviar la misma.
- **Modos de Operación:** `SCREEN_TO_SCREEN` (simulación con video de archivo) y `SCREEN_TO_CAMERA` (cámaras IP reales).

### 4. Capa de Hardware (ESP32)
- **Firmware:** `firmware_esp32/firmware_esp32.ino`
- **Comunicación:** MQTT con CallbackAPIVersion.VERSION2.
- **Tópicos configurables vía .env:** `MQTT_TOPIC_ENTRADA`, `MQTT_TOPIC_SALIDA`.
- **Componentes:** Servomotor (barrera), sensor ultrasónico (detección de paso), pantalla LCD (mensajes al conductor).

---
1. **Rutas Delgadas:** Los controladores en `routes/` no deben contener lógica de negocio. Solo delegan a los servicios correspondientes.
2. **Independencia:** Los servicios deben importar modelos y esquemas, pero no routers.
3. **Tipo Seguro:** Usar siempre los Enums definidos en `models/enums.py` para cualquier estado o rol del sistema.
4. **Configuración Centralizada:** Cualquier parámetro, constante o URL externa debe ser configurada en `core/config.py` y, si es necesario, provista vía `.env`.
5. **Aforo por Reserva:** Las reservas no horarias (Día/Semana/Quincena/Mes) descuentan la plaza al iniciar el período (fecha_inicio) y la liberan solo al vencer o cancelar. Las reservas por hora descuentan al entrar físicamente.
6. **Liberación Diferida:** La salida física nunca libera plazas de reservas no horarias — la liberación la gestiona exclusivamente `auto_finalize_all_reservations` al vencer el período.
