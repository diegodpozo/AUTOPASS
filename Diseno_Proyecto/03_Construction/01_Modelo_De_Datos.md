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

┌────────────────────────────────┐
│       SupportTicket            │
├────────────────────────────────┤
│ PK id                          │
│ FK user_id (not null)          │
│ categoria                      │
│ sucursal (default "General")   │
│ asunto                         │
│ mensaje (Text)                 │
│ estado (default "Pendiente")   │
│ respuesta (nullable)           │
│ created_at (DateTime)          │
│ updated_at (DateTime)          │
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
| capacidad_total | Integer (default 20) | Cupo para autos |
| ocupacion_actual | Integer (default 0) | Autos estacionados actualmente |
| capacidad_motos | Integer (default 10) | Cupo para motos |
| ocupacion_motos | Integer (default 0) | Motos estacionadas actualmente |
| capacidad_camionetas | Integer (default 5) | Cupo para camionetas |
| ocupacion_camionetas | Integer (default 0) | Camionetas estacionadas actualmente |

### ParkingAforo (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| sucursal | String (unique, nullable) | Sucursal |
| capacidad_total | Integer (default 20) | Cupo total de autos |
| ocupacion_actual | Integer (default 0) | Autos presentes |
| capacidad_motos | Integer (default 10) | Cupo total de motos |
| ocupacion_motos | Integer (default 0) | Motos presentes |
| capacidad_camionetas | Integer (default 5) | Cupo total de camionetas |
| ocupacion_camionetas | Integer (default 0) | Camionetas presentes |
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
ParkingBranch 1──* ParkingFloor (sucursal tiene múltiples pisos)
```
