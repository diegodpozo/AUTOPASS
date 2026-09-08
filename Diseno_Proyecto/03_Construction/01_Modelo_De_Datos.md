# Modelo de Datos — AUTOPASS

## Diagrama Entidad-Relación (Texto)

```
┌────────────────┐       ┌──────────────────┐       ┌─────────────────────┐
│      User      │       │     Vehicle      │       │    AccessLog         │
├────────────────┤       ├──────────────────┤       ├─────────────────────┤
│ PK id          │◄──────│ PK id            │       │ PK id               │
│ nombre         │       │ FK user_id       │       │ patente_detectada   │
│ apellido       │       │ patente          │       │ normalized_patente  │
│ dni (unique)   │       │ marca_modelo     │       │ tipo_evento         │
│ email (unique) │       │ tipo (VehicleType)│      │ tipo_vehiculo       │
│ telefono       │       │ is_favorite      │       │ fecha_hora          │
│ patente        │       └──────────────────┘       │ imagen_path         │
│ direccion      │                                  │ costo_estadia       │
│ password_hash  │       ┌──────────────────┐       │ metodo_pago         │
│ rol (UserRole) │       │   Reservation    │       │ fecha_pago          │
│ sucursal       │       ├──────────────────┤       │ pago_confirmado     │
│ saldo          │       │ PK id            │       │ FK reserva_id       │
│ puntos_acum    │       │ FK user_id       │       │ FK floor_id         │
│ is_blocked     │       │ patente          │       │ sucursal            │
│ is_deleted     │       │ fecha_inicio     │       └─────────────────────┘
└────────────────┘       │ fecha_fin        │
        │                │ dias_semana      │
        │                │ tipo_estadia     │
        │                │ monto_total      │
        │                │ monto_reembolsado│
        │                │ fecha_pago       │
        │                │ mp_preference_id │
        │                │ estado_pago      │
        │                │ estado_reserva   │
        │                │ sucursal_nombre  │
        │                │ sucursal_info    │
        │                │ cliente_nombre   │
        │                │ recordatorio_confirmado
        │                └──────────────────┘
        │
        ▼
┌────────────────┐       ┌──────────────────┐       ┌─────────────────────┐
│   PointsLog    │       │     Coupon       │       │   ParkingBranch     │
├────────────────┤       ├──────────────────┤       ├─────────────────────┤
│ PK id          │       │ PK id            │       │ PK id               │
│ FK user_id     │       │ codigo (unique)  │       │ nombre (unique)    │
│ cantidad       │       │ descuento_porcentaje     │ telefono            │
│ motivo         │       │ fecha_expiracion │       │ horario             │
│ fecha          │       │ activo           │       │ is_24h              │
└────────────────┘       └──────────────────┘       │ logo_url            │
                                                    │ activa              │
┌──────────────────────┐                            │ latitude            │
│     Promotion        │                            │ longitude           │
├──────────────────────┤                            └────────┬────────────┘
│ PK id                │                                     │
│ titulo               │                                     │ 1
│ descripcion          │                                     │
│ costo_puntos         │                                     │ *
│ icono                │                                     ▼
│ categoria            │                            ┌─────────────────────┐
│ activa               │                            │   ParkingFloor      │
│ sucursal             │                            ├─────────────────────┤
└──────────────────────┘                            │ PK id               │
                                                    │ FK branch_id        │
┌──────────────────────┐                            │ nombre              │
│   ParkingAforo       │                            │ capacidad_total     │
├──────────────────────┤                            │ ocupacion_actual    │
│ PK id                │                            │ capacidad_motos     │
│ sucursal (unique)    │                            │ ocupacion_motos     │
│ capacidad_total      │                            │ capacidad_camionetas│
│ ocupacion_actual     │                            │ ocupacion_camionetas│
│ capacidad_motos      │                            └─────────────────────┘
│ ocupacion_motos      │
│ capacidad_camionetas │      ┌────────────────────────────────┐
│ ocupacion_camionetas │      │          Settings              │
│ ultima_actualizacion │      ├────────────────────────────────┤
└──────────────────────┘      │ PK id                          │
                              │ clave                          │
┌──────────────────────┐      │ valor (Float)                  │
│  ParkingCamera       │      │ valor_str                      │
├──────────────────────┤      │ sucursal                       │
│ PK id                │      └────────────────────────────────┘
│ nombre               │
│ tipo                 │      ┌────────────────────────────────┐
│ source               │      │     UserNotification           │
│ sucursal             │      ├────────────────────────────────┤
│ activa               │      │ PK id                          │
└──────────────────────┘      │ FK user_id                     │
                              │ tipo                           │
                              │ titulo                         │
                              │ mensaje                        │
                              │ leido                          │
│ FK reserva_id (nullable)       │
│ created_at (DateTime)          │
└────────────────────────────────┘

┌────────────────────────────────┐     ┌────────────────────────────────┐
│       SupportTicket            │     │   MercadoPagoPayment (v9.14.0) │
├────────────────────────────────┤     ├────────────────────────────────┤
│ PK id                          │     │ PK id                          │
│ FK user_id (not null)          │     │ tipo (reserva|estadia)         │
│ categoria                      │     │ FK reserva_id (nullable)       │
│ sucursal (default "General")   │     │ FK access_log_id (nullable)    │
│ asunto                         │     │ FK redemption_ticket_id (null) │
│ mensaje (Text)                 │     │ patente                        │
│ estado (default "Pendiente")   │     │ monto                          │
│ respuesta (nullable)           │     │ moneda (default "ARS")         │
│ created_at (DateTime)          │     │ external_reference (unique)    │
│ updated_at (DateTime)          │     │ preference_id                  │
└────────────────────────────────┘     │ payment_id                     │
                                       │ estado (PENDIENTE/APROBADO...)  │
                                       │ mp_status                      │
                                       │ created_at (DateTime)          │
                                       │ updated_at (DateTime)          │
                                       └────────────────────────────────┘
                                       
┌────────────────────────────────┐     ┌────────────────────────────────┐
│   RedemptionTicket (v9.13.0)   │     │       UserSession (v9.11.0)    │
├────────────────────────────────┤     ├────────────────────────────────┤
│ PK id                          │     │ PK id                          │
│ codigo (16 chars, unique)      │     │ FK user_id (indexed)           │
│ qr_data                        │     │ device_id (indexed)            │
│ tipo_canje (default "desc_res")│     │ user_agent                     │
│ valor_descuento                │     │ ip_address                     │
│ fecha_expiracion (default +30d)│     │ created_at (DateTime)          │
│ usado                          │     │ last_login_at (indexed)        │
│ created_at (DateTime)          │     └────────────────────────────────┘
└────────────────────────────────┘
```

## Descripción de Entidades

### User (models/user.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| nombre | String | Nombre del usuario |
| apellido | String | Apellido del usuario |
| dni | String (unique, indexed) | Documento nacional de identidad |
| email | String (unique, indexed) | Email de login |
| telefono | String | Teléfono de contacto |
| patente | String (nullable) | Patente de referencia del usuario |
| direccion | String (nullable) | Dirección física |
| password_hash | String | Hash bcrypt de la contraseña |
| rol | String (default "user") | admin, local_admin, staff, user |
| sucursal | String (nullable) | Sucursal asignada (null para admin global) |
| saldo | Float (default 0.0) | Saldo digital para pagos |
| puntos_acumulados | Integer (default 0) | Puntos de fidelización acumulados |
| is_blocked | Boolean (default False) | Bloqueo administrativo |
| is_deleted | Boolean (default False) | Soft delete |

### Vehicle (models/user.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| user_id | Integer FK→users.id | Dueño del vehículo |
| patente | String (unique, indexed) | Patente del vehículo |
| marca_modelo | String | Marca y modelo |
| tipo | String (default "Auto") | Auto, Moto o Camioneta |
| is_favorite | Boolean (default False) | Vehículo favorito del usuario |

### UserSession (models/user_session.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| user_id | Integer FK→users.id (indexed) | Usuario de la sesión |
| device_id | String (indexed) | Identificador del dispositivo/navegador |
| user_agent | String (nullable) | User-Agent del navegador |
| ip_address | String (nullable) | IP de origen |
| created_at | DateTime (default utcnow) | Fecha de creación |
| last_login_at | DateTime (default utcnow, indexed) | Último login |

> Nota: `UserSession` habilita la detección de inicios de sesión desde otros dispositivos (notificación `NEW_DEVICE_LOGIN`). Migración Alembic: `b7e3a1d2c4f5_add_user_sessions.py`.

### AccessLog (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| patente_detectada | String | Patente leída por ALPR o manual |
| normalized_patente | String (indexed, nullable) | Patente normalizada para búsqueda |
| tipo_evento | String | ENTRADA o SALIDA |
| tipo_vehiculo | String (default "Auto") | Auto, Moto o Camioneta |
| reserva_id | Integer FK→reservations.id (nullable) | Reserva asociada |
| floor_id | Integer FK→parking_floors.id (nullable) | Piso donde estacionó |
| fecha_hora | String | Timestamp del evento (formato ISO) |
| fecha_pago | String (nullable) | Cuándo pagó |
| imagen_path | String (nullable) | Ruta de imagen capturada |
| pago_confirmado | Boolean (default False) | Indica si pagó |
| metodo_pago | String (nullable) | DIGITAL o CAJA |
| costo_estadia | Float (default 0.0) | Monto calculado de la estadía |
| sucursal | String (nullable) | Sucursal del evento |

### Reservation (models/reservation.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| user_id | Integer FK→users.id | Usuario que reserva |
| patente | String | Patente del vehículo |
| fecha_inicio | String | Inicio del período de reserva (formato ISO) |
| fecha_fin | String | Fin del período de reserva (formato ISO) |
| dias_semana | String (nullable) | Días de la semana para reserva recurrente (ej: "0,1,2") |
| tipo_estadia | String (default "hora") | hora, dia, semana, quincena, mes |
| monto_total | Float | Monto total de la reserva |
| monto_reembolsado | Float (default 0.0) | Monto reembolsado si canceló |
| fecha_pago | String (nullable) | Fecha de pago |
| mp_preference_id | String (nullable) | ID de referencia de pago |
| estado_pago | String (default "Pendiente") | Pendiente, Pagado, Fallido, Reembolsado, Cancelado |
| estado_reserva | String (default "Pendiente") | Pendiente, Activa, Completada, Cancelada |
| sucursal_nombre | String (nullable) | Sucursal reservada |
| sucursal_info | String (nullable) | Información adicional de la sucursal |
| cliente_nombre | String (nullable) | Nombre del cliente al momento de reservar |
| recordatorio_confirmado | Boolean (default False) | Confirmación de recordatorio |

### ParkingFloor (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| branch_id | Integer FK→parking_branches.id | Sucursal a la que pertenece |
| nombre | String | Nombre del piso (PB, P1, etc.) |
| capacidad_total | Integer (default 20) | Cupo para autos (aforo físico) |
| ocupacion_actual | Integer (default 0) | Autos estacionados actualmente (físico) |
| capacidad_motos | Integer (default 10) | Cupo para motos (físico) |
| ocupacion_motos | Integer (default 0) | Motos estacionadas actualmente (físico) |
| capacidad_camionetas | Integer (default 5) | Cupo para camionetas (físico) |
| ocupacion_camionetas | Integer (default 0) | Camionetas estacionadas actualmente (físico) |
| capacidad_reservas_autos/motos/camionetas | Integer (defaults 5/3/2) | Cupos **exclusivos de reserva** por tipo (v9.14.1+) |
| ocupacion_reservas_autos/motos/camionetas | Integer (default 0) | Ocupación de cupos de reserva por tipo (v9.14.1+) |
| capacidad_reservas | Integer (default 10) | Cupo total de reservas del piso (v9.14.1+) |
| ocupacion_reservas | Integer (default 0) | Ocupación total de reservas del piso (v9.14.1+) |

> Cupos de reserva (v9.14.1+): alimentan `verificar_disponibilidad`/fechas-horas deshabilitadas. Son **independientes** del aforo físico — NO se descuentan del estacionamiento en sí. Migración Alembic: `e6f7a8b9c0d1_add_reservation_spots_to_aforo_and_floors.py`.

### ParkingAforo (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| sucursal | String (unique, nullable) | Sucursal |
| capacidad_total | Integer (default 20) | Cupo total de autos (físico) |
| ocupacion_actual | Integer (default 0) | Autos presentes (físico) |
| capacidad_motos | Integer (default 10) | Cupo total de motos (físico) |
| ocupacion_motos | Integer (default 0) | Motos presentes (físico) |
| capacidad_camionetas | Integer (default 5) | Cupo total de camionetas (físico) |
| ocupacion_camionetas | Integer (default 0) | Camionetas presentes (físico) |
| capacidad_reservas_autos/motos/camionetas | Integer (defaults 5/3/2) | Cupos **exclusivos de reserva** por tipo (v9.14.1+) |
| ocupacion_reservas_autos/motos/camionetas | Integer (default 0) | Ocupación de cupos de reserva por tipo (v9.14.1+) |
| capacidad_reservas | Integer (default 10) | Cupo total de reservas planta baja (v9.14.1+) |
| ocupacion_reservas | Integer (default 0) | Ocupación total de reservas PB (v9.14.1+) |
| ultima_actualizacion | String | Timestamp de última actualización |

### Settings (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| clave | String | Nombre de la configuración |
| valor | Float (nullable) | Valor numérico (tarifas, capacidad) |
| valor_str | String (nullable) | Valor de texto largo (IPs, URLs) |
| sucursal | String (nullable) | Aislamiento por sucursal |

### ParkingCamera (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| nombre | String (not null) | Nombre de la cámara |
| tipo | String (not null) | entrada, salida o vigilancia |
| source | String (not null) | URL de la fuente (RTSP, HTTP MJPEG) |
| sucursal | String (nullable) | Sucursal a la que pertenece |
| activa | Boolean (default True) | Si la cámara está habilitada |

### PointsLog (models/user.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| user_id | Integer FK→users.id | Usuario propietario |
| cantidad | Integer | Cantidad de puntos (positivo=gana, negativo=canjea) |
| motivo | String | Descripción del movimiento |
| fecha | String | Fecha del movimiento |

### Coupon (models/reservation.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| codigo | String (unique, indexed) | Código del cupón |
| descuento_porcentaje | Integer | Porcentaje de descuento |
| fecha_expiracion | String | Fecha de expiración |
| activo | Boolean (default True) | Si el cupón está vigente |

### Promotion (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| titulo | String | Título de la promoción |
| descripcion | String | Descripción detallada |
| costo_puntos | Integer | Costo en puntos para canjear |
| icono | String (default "fas fa-gift") | Icono Font Awesome |
| categoria | String (default "Beneficio") | Categoría de la promoción |
| activa | Boolean (default True) | Si la promoción está activa |
| sucursal | String (nullable) | Sucursal (null = global) |

### UserNotification (models/notification.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| user_id | Integer FK→users.id (not null, indexed) | Usuario destinatario |
| tipo | String (not null) | Tipo de notificación (reserva, sistema, etc.) |
| titulo | String (not null) | Título de la notificación |
| mensaje | String (not null) | Cuerpo del mensaje |
| leido | Boolean (default False) | Si fue leída |
| reserva_id | Integer FK→reservations.id (nullable) | Reserva asociada (si aplica) |
| created_at | DateTime (default utcnow) | Fecha de creación |

### SupportTicket (models/support.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| user_id | Integer FK→users.id (not null, indexed) | Usuario que crea el ticket |
| categoria | String (not null) | Categoría de la consulta |
| sucursal | String (default "General", indexed) | Sucursal del ticket |
| asunto | String (not null) | Asunto de la consulta |
| mensaje | Text (not null) | Cuerpo del mensaje |
| estado | String (default "Pendiente", indexed) | Pendiente, Respondido, etc. |
| respuesta | Text (nullable) | Respuesta del administrador |
| created_at | DateTime (default utcnow) | Fecha de creación |
| updated_at | DateTime (default utcnow, onupdate) | Fecha de última actualización |

### MercadoPagoPayment (models/mercadopago.py - v9.14.0)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único (autoincremental) |
| tipo | String (indexed) | Tipo de pago: 'reserva' o 'estadia' |
| reserva_id | Integer FK→reservations.id (nullable, indexed) | Reserva si tipo='reserva' |
| access_log_id | Integer FK→access_logs.id (nullable, indexed) | Estadía si tipo='estadia' |
| redemption_ticket_id | Integer FK→redemption_tickets.id (nullable) | Ticket de descuento aplicado |
| patente | String (nullable, indexed) | Patente del vehículo |
| monto | Float (not null) | Monto a pagar en MP |
| moneda | String (default "ARS") | Moneda ISO |
| external_reference | String (unique, indexed, nullable) | `AP-{TIPO}-{id}-{uuid8}` generada por MP |
| preference_id | String (nullable) | ID de preferencia devuelto por MP |
| payment_id | String (nullable, indexed) | ID de pago asignado por MP |
| estado | String (default "PENDIENTE") | PENDIENTE, APROBADO, FALLIDO, CANCELADO |
| mp_status | String (nullable) | Status HTTP devuelto por MP |
| created_at | DateTime (default utcnow, indexed) | Fecha de creación |
| updated_at | DateTime (default utcnow) | Fecha de última actualización |

> Nota: `external_reference` genera una referencia única para evitar duplicados. Migración Alembic: `c9d8e7f6a5b4_add_mercadopago_payments.py`.

### RedemptionTicket (models/reservation.py - v9.13.0)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| codigo | String (16 chars, unique, indexed, nullable) | Código QR legible por ALPR (ej: `APRD-XXXX-XXXX`) |
| qr_data | String (unique, indexed) | Datos QR codificados: `"AUTOPASS_REDEMPTION\|ID:{codigo}"` |
| tipo_canje | String (default "descuento_reserva") | Tipo de beneficio: descuento_reserva, etc. |
| valor_descuento | Float (not null) | Monto o porcentaje de descuento |
| fecha_expiracion | DateTime (indexed) | Fecha de expiración (default +30 días) |
| usado | Boolean (default False, indexed) | Si fue canjeado |
| created_at | DateTime (default utcnow) | Fecha de emisión |

> Nota: `RedemptionTicket` se genera al canjear puntos en una promoción de descuento. Puede ser leído por ALPR al ingreso o aplicado manualmente al pagar una reserva con MP.

## Enumeraciones (models/enums.py)

```python
class UserRole(str, Enum):        # admin, local_admin, staff, user
class VehicleType(str, Enum):     # Auto, Moto, Camioneta
class AccessEventType(str, Enum): # ENTRADA, SALIDA
class ReservationStatus(str, Enum): # Pendiente, Activa, Completada, Cancelada
class PaymentStatus(str, Enum):     # Pendiente, Pagado, Fallido, Reembolsado, Cancelado
```

> **Nota:** Los enums están definidos en `models/enums.py` pero las columnas en los modelos ORM usan `String` en lugar del tipo `Enum` de SQLAlchemy. Los valores válidos se mantienen por convención y se validan a nivel de servicio.

## Relaciones Clave

```
User 1──* Vehicle            (usuario tiene múltiples vehículos)
User 1──* Reservation        (usuario tiene múltiples reservas)
User 1──* PointsLog          (usuario tiene historial de puntos)
User 1──* UserNotification   (usuario tiene notificaciones in-app)
Reservation 1──* AccessLog   (reserva puede tener múltiples accesos)
Reservation 1──* UserNotification (reserva puede generar notificaciones)
Reservation 1──* MercadoPagoPayment (reserva puede tener pago MP)
AccessLog 1──* MercadoPagoPayment (estadía puede tener pago MP)
MercadoPagoPayment * ──0/1 RedemptionTicket (pago puede aplicar descuento)
ParkingBranch 1──* ParkingFloor (sucursal tiene múltiples pisos)
```
