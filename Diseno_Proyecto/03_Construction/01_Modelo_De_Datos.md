# Modelo de Datos — AUTOPASS

## Diagrama Entidad-Relación (Texto)

```
┌────────────────┐       ┌──────────────────┐       ┌─────────────────────┐
│      User      │       │     Vehicle      │       │    AccessLog         │
├────────────────┤       ├──────────────────┤       ├─────────────────────┤
│ PK id          │◄──────│ PK id            │       │ PK id               │
│ nombre         │       │ FK user_id       │◄──────┤ FK user_id          │
│ apellido       │       │ patente          │       │ patente_detectada   │
│ dni (unique)   │       │ marca_modelo     │       │ normalized_patente  │
│ email (unique) │       │ tipo (VehicleType)│      │ tipo_evento         │
│ telefono       │       │ is_favorite      │       │ tipo_vehiculo       │
│ direccion      │       └──────────────────┘       │ fecha_hora          │
│ password_hash  │                                   │ imagen_path         │
│ rol (UserRole) │                                   │ costo_estadia       │
│ sucursal       │       ┌──────────────────┐       │ metodo_pago         │
│ saldo          │       │   Reservation    │       │ fecha_pago          │
│ puntos_acum    │       ├──────────────────┤       │ pago_confirmado     │
│ is_blocked     │       │ PK id            │       │ status              │
│ is_deleted     │       │ FK user_id       │       │ FK reserva_id       │
└────────────────┘       │ patente          │       │ FK floor_id         │
        │                 │ fecha_inicio     │       │ sucursal            │
        │                 │ fecha_fin        │       └─────────────────────┘
        │                 │ tipo_estadia     │               │
        │                 │ monto_total      │               │
        │                 │ monto_reembolsado│               │
        │                 │ mp_preference_id │               │
        │                 │ estado_pago      │               │
        │                 │ estado_reserva   │               │
        │                 │ sucursal_nombre  │               │
        │                 │ cliente_nombre   │               │
        │                 │ recordatorio_confirmado          │
        │                 └──────────────────┘               │
        │                         │                          │
        ▼                         ▼                          ▼
┌────────────────┐       ┌──────────────────┐       ┌─────────────────────┐
│   PointsLog    │       │     Coupon       │       │   ParkingBranch     │
├────────────────┤       ├──────────────────┤       ├─────────────────────┤
│ PK id          │       │ PK id            │       │ PK id               │
│ FK user_id     │       │ FK user_id       │       │ nombre (unique)    │
│ cantidad       │       │ codigo (unique)  │       │ direccion           │
│ motivo         │       │ descuento_porc   │       │ telefono            │
│ fecha          │       │ fecha_expiracion │       │ horario             │
└────────────────┘       │ activo           │       │ is_24h              │
                         └──────────────────┘       │ logo_url            │
┌──────────────────────┐                             │ activa              │
│     Promotion        │                             │ latitude            │
├──────────────────────┤                             │ longitude           │
│ PK id                │                             └────────┬────────────┘
│ titulo               │                                      │
│ descripcion          │                                      │ 1
│ costo_puntos         │                                      │
│ icono                │                                      │
│ categoria            │                                      │ *
│ activa               │                                      ▼
│ sucursal             │                             ┌─────────────────────┐
└──────────────────────┘                             │   ParkingFloor      │
                                                     ├─────────────────────┤
┌──────────────────────┐                             │ PK id               │
│   ParkingAforo       │                             │ FK branch_id        │
├──────────────────────┤                             │ nombre              │
│ PK id                │                             │ capacidad_total     │
│ sucursal (unique)    │                             │ ocupacion_actual    │
│ capacidad_total      │                             │ capacidad_motos     │
│ ocupacion_actual     │                             │ ocupacion_motos     │
│ capacidad_motos      │                             │ capacidad_camionetas│
│ ocupacion_motos      │                             │ ocupacion_camionetas│
│ capacidad_camionetas │                             └─────────────────────┘
│ ocupacion_camionetas │
└──────────────────────┘       ┌────────────────────────────────┐
                               │          Settings              │
┌──────────────────────┐       ├────────────────────────────────┤
│  ParkingCamera       │       │ PK id                          │
├──────────────────────┤       │ clave (unique con sucursal)   │
│ PK id                │       │ valor                          │
│ nombre               │       │ valor_str                     │
│ tipo                 │       │ sucursal                       │
│ source               │       └────────────────────────────────┘
│ sucursal             │
│ activa               │
└──────────────────────┘
```

## Descripción de Entidades

### User (models/user.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| nombre | String(100) | Nombre del usuario |
| apellido | String(100) | Apellido del usuario |
| dni | String(20) (unique) | Documento nacional de identidad |
| email | String(150) (unique) | Email de login |
| telefono | String(50) | Teléfono de contacto |
| direccion | String(255) | Dirección física |
| password_hash | String(255) | Hash bcrypt de la contraseña |
| rol | Enum(UserRole) | ADMIN, LOCAL_ADMIN, STAFF, USER |
| sucursal | String(100) | Sucursal asignada (null para ADMIN global) |
| saldo | Float | Saldo digital para pagos |
| puntos_acumulados | Integer | Puntos de fidelización acumulados |
| is_blocked | Boolean | Bloqueo administrativo |
| is_deleted | Boolean | Soft delete |

### Vehicle (models/user.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| user_id | Integer FK | Dueño del vehículo |
| patente | String(50) | Patente del vehículo |
| marca_modelo | String(100) | Marca y modelo |
| tipo | Enum(VehicleType) | Auto, Moto o Camioneta |
| is_favorite | Boolean | Vehículo favorito del usuario |

### AccessLog (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| patente_detectada | String(50) | Patente leída por ALPR o manual |
| normalized_patente | String(50) (indexed) | Patente normalizada para búsqueda |
| tipo_evento | Enum(AccessEventType) | ENTRADA o SALIDA |
| tipo_vehiculo | Enum(VehicleType) | Auto, Moto o Camioneta |
| reserva_id | Integer FK (nullable) | Reserva asociada |
| user_id | Integer FK (nullable) | Usuario asociado |
| floor_id | Integer FK (nullable) | Piso donde estacionó |
| fecha_hora | DateTime | Timestamp del evento |
| imagen_path | String(255) | Ruta de imagen capturada |
| pago_confirmado | Boolean | Indica si pagó |
| costo_estadia | Float | Monto calculado de la estadía |
| metodo_pago | String(20) | DIGITAL o CAJA |
| fecha_pago | DateTime | Cuándo pagó |
| status | String(20) | Estado del registro |
| sucursal | String(100) | Sucursal del evento |

### Reservation (models/reservation.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| user_id | Integer FK | Usuario que reserva |
| patente | String(50) | Patente del vehículo |
| fecha_inicio | DateTime | Inicio del período de reserva |
| fecha_fin | DateTime | Fin del período de reserva |
| tipo_estadia | String(20) | Hora, Día, Semana, Quincena, Mes |
| monto_total | Float | Monto total de la reserva |
| monto_reembolsado | Float | Monto reembolsado si canceló |
| mp_preference_id | String(100) | ID de referencia de pago |
| estado_pago | Enum(PaymentStatus) | Pendiente, Pagado, Fallido, Reembolsado |
| estado_reserva | Enum(ReservationStatus) | Pendiente, Activa, Completada, Cancelada |
| sucursal_nombre | String(100) | Sucursal reservada |
| cliente_nombre | String(200) | Nombre del cliente al momento de reservar |
| recordatorio_confirmado | Boolean | Confirmación de recordatorio |

### ParkingFloor (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| branch_id | Integer FK | Sucursal a la que pertenece |
| nombre | String(100) | Nombre del piso (PB, P1, etc.) |
| capacidad_total | Integer | Cupo para autos |
| ocupacion_actual | Integer | Autos estacionados actualmente |
| capacidad_motos | Integer | Cupo para motos |
| ocupacion_motos | Integer | Motos estacionadas actualmente |
| capacidad_camionetas | Integer | Cupo para camionetas |
| ocupacion_camionetas | Integer | Camionetas estacionadas actualmente |

### ParkingAforo (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| sucursal | String(100) (unique) | Sucursal |
| capacidad_total | Integer | Cupo total de autos |
| ocupacion_actual | Integer | Autos presentes |
| capacidad_motos | Integer | Cupo total de motos |
| ocupacion_motos | Integer | Motos presentes |
| capacidad_camionetas | Integer | Cupo total de camionetas |
| ocupacion_camionetas | Integer | Camionetas presentes |

### Settings (models/parking.py)
| Columna | Tipo | Descripción |
|---------|------|-------------|
| id | Integer PK | Identificador único |
| clave | String(100) | Nombre de la configuración |
| valor | String(255) | Valor numérico o corto |
| valor_str | Text | Valor de texto largo (IPs, URLs) |
| sucursal | String(100) | Aislamiento por sucursal |

## Enumeraciones (models/enums.py)

```python
class UserRole(str, Enum):        # ADMIN, LOCAL_ADMIN, STAFF, USER
class VehicleType(str, Enum):     # Auto, Moto, Camioneta
class AccessEventType(str, Enum): # ENTRADA, SALIDA
class ReservationStatus(str, Enum): # Pendiente, Activa, Completada, Cancelada
class PaymentStatus(str, Enum):     # Pendiente, Pagado, Fallido, Reembolsado, Cancelado
```

## Relaciones Clave

```
User 1──* Vehicle          (usuario tiene múltiples vehículos)
User 1──* Reservation       (usuario tiene múltiples reservas)
User 1──* PointsLog         (usuario tiene historial de puntos)
User 1──* AccessLog         (usuario tiene accesos registrados)
User 1──* Coupon            (usuario tiene cupones)
Reservation 1──* AccessLog  (reserva puede tener múltiples accesos)
ParkingBranch 1──* ParkingFloor (sucursal tiene múltiples pisos)
```
