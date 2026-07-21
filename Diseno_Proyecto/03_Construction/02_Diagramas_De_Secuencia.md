# Diagramas de Secuencia — AUTOPASS

## 1. Flujo de Ingreso por ALPR

```
Sistema ALPR          Backend API           AccessService       ReservationService    ParkingAforo    MQTT        DB
    │                      │                      │                     │                  │            │         │
    │  1. Patente/QR      │                      │                     │                  │            │         │
    │────────────────────►│                      │                     │                  │            │         │
    │                      │                      │                     │                  │            │         │
    │                      │  2. validate_plate() │                     │                  │            │         │
    │                      │─────────────────────►│                     │                  │            │         │
    │                      │                      │                     │                  │            │         │
    │                      │                      │  3. Buscar reserva  │                  │            │         │
    │                      │                      │────────────────────►│                  │            │         │
    │                      │                      │                     │                  │            │         │
    │                      │                      │  4. Reserva (o null)│                  │            │         │
    │                      │                      │◄────────────────────│                  │            │         │
    │                      │                      │                     │                  │            │         │
    │                      │                      │  5. Verificar ya    │                  │            │         │
    │                      │                      │     dentro (último  │                  │            │         │
    │                      │                      │     registro ENTRADA│                  │            │         │
    │                      │                      │     sin SALIDA)     │                  │            │         │
    │                      │                      │───────────────────────────────────────────────►         │
    │                      │                      │◄───────────────────────────────────────────────         │
    │                      │                      │                     │                  │            │         │
    │                      │                      │  6. Verificar       │                  │            │         │
    │                      │                      │     capacidad       │                  │            │         │
    │                      │                      │─────────────────────────────────►                      │
    │                      │                      │◄─────────────────────────────────                      │
    │                      │                      │                     │                  │            │         │
    │                      │                      │  7. [Si hay lugar]  │                  │            │         │
    │                      │                      │     Registrar       │                  │            │         │
    │                      │                      │     AccessLog       │                  │            │         │
    │                      │                      │     ENTRADA        │                  │            │         │
    │                      │                      │───────────────────────────────────────────────►         │
    │                      │                      │                     │                  │            │         │
    │                      │                      │  8. Incrementar     │                  │            │         │
    │                      │                      │     ocupacion       │                  │            │         │
    │                      │                      │─────────────────────────────────►                      │
    │                      │                      │                     │                  │            │         │
    │                      │                      │  9. MQTT: OPEN     │                  │            │         │
    │                      │                      │───────────────────────────────────────────────►         │
    │                      │                      │                     │                  │            │         │
    │                      │                      │ 10. Notificar WS   │                  │            │         │
    │                      │                      │    (NotificationService)                               │
    │                      │                      │                     │                  │            │         │
    │  11. Respuesta OK   │                      │                     │                  │            │         │
    │◄────────────────────│                      │                     │                  │            │         │
```

## 2. Flujo de Egreso con Pago

```
Sistema ALPR        Backend API         AccessService       BillingService      ParkingAforo      MQTT        DB
    │                    │                    │                   │                  │            │         │
    │  1. Patente       │                    │                   │                  │            │         │
    │──────────────────►│                    │                   │                  │            │         │
    │                    │                    │                   │                  │            │         │
    │                    │ 2. exit_plate()   │                   │                  │            │         │
    │                    │──────────────────►│                   │                  │            │         │
    │                    │                    │                   │                  │            │         │
    │                    │                    │ 3. Buscar último  │                  │            │         │
    │                    │                    │    registro      │                  │            │         │
    │                    │                    │──────────────────────────────────────────────►            │
    │                    │                    │◄──────────────────────────────────────────────            │
    │                    │                    │                   │                  │            │         │
    │                    │                    │ 4. Calcular       │                  │            │         │
    │                    │                    │    tiempo         │                  │            │         │
    │                    │                    │                   │                  │            │         │
    │                    │                    │ ┌─ ¿≤ 10 min? ────┤                  │            │         │
    │                    │                    │ │                 │                  │            │         │
    │                    │                    │ │ [SÍ] cortesía:  │                  │            │         │
    │                    │                    │ │ costo = 0       │                  │            │         │
    │                    │                    │ │                 │                  │            │         │
    │                    │                    │ │ [NO] calcular   │                  │            │         │
    │                    │                    │ │       deuda     │                  │            │         │
    │                    │                    │ │────────────────►│                  │            │         │
    │                    │                    │ │◄────────────────│                  │            │         │
    │                    │                    │ │                 │                  │            │         │
    │                    │                    │ └─ ¿pagó o       │                  │            │         │
    │                    │                    │    tiene reserva?│                  │            │         │
    │                    │                    │                   │                  │            │         │
    │                    │                    │ 5. [Si OK]       │                  │            │         │
    │                    │                    │    Registrar     │                  │            │         │
    │                    │                    │    AccessLog     │                  │            │         │
    │                    │                    │    SALIDA        │                  │            │         │
    │                    │                    │──────────────────────────────────────────────►            │
    │                    │                    │                   │                  │            │         │
    │                    │                    │ 6. Decrementar    │                  │            │         │
    │                    │                    │    ocupacion      │                  │            │         │
    │                    │                    │──────────────────────────────►                      │
    │                    │                    │                   │                  │            │         │
    │                    │                    │ 7. MQTT: OPEN    │                  │            │         │
    │                    │                    │──────────────────────────────────────────────►         │
    │                    │                    │                   │                  │            │         │
    │                    │                    │ 8. Notificar WS  │                  │            │         │
    │                    │                    │                   │                  │            │         │
    │  9. Respuesta OK  │                    │                   │                  │            │         │
    │◄──────────────────│                    │                   │                  │            │         │
```

## 3. Flujo de Reserva y Pago

```
Usuario (Browser)     User Routes         ReservationService    BillingService      ParkingAforo        DB
    │                      │                     │                   │                  │              │
    │  1. POST /reservas   │                     │                   │                  │              │
    │─────────────────────►│                     │                   │                  │              │
    │                      │                     │                   │                  │              │
    │                      │ 2. create_reserva() │                   │                  │              │
    │                      │────────────────────►│                   │                  │              │
    │                      │                     │                   │                  │              │
    │                      │                     │ 3. Validar:       │                  │              │
    │                      │                     │    - anticipación │                  │              │
    │                      │                     │      (solo hora)  │                  │              │
    │                      │                     │    - capacidad    │                  │              │
    │                      │                     │────────────────────────────────────►                │
    │                      │                     │◄────────────────────────────────────                │
    │                      │                     │                   │                  │              │
    │                      │                     │ 4. Calcular costo │                  │              │
    │                      │                     │──────────────────►│                  │              │
    │                      │                     │◄──────────────────│                  │              │
    │                      │                     │                   │                  │              │
    │                      │                     │ 5. Crear          │                  │              │
    │                      │                     │    Reservation    │                  │              │
    │                      │                     │    (PENDIENTE)   │                  │              │
    │                      │                     │──────────────────────────────────────►              │
    │                      │                     │                   │                  │              │
    │                      │                     │ 6. Enviar email   │                  │              │
    │                      │                     │    confirmación   │                  │              │
    │                      │                     │    con QR         │                  │              │
    │                      │                     │                   │                  │              │
    │  7. Reserva creada  │                     │                   │                  │              │
    │◄────────────────────│                     │                   │                  │              │
    │                      │                     │                   │                  │              │
    │  8. POST /pagar      │                     │                   │                  │              │
    │─────────────────────►│                     │                   │                  │              │
    │                      │ 9. pay_reserva()   │                   │                  │              │
    │                      │────────────────────►│                   │                  │              │
    │                      │                     │                   │                  │              │
    │                      │                     │ 10. Verificar     │                  │              │
    │                      │                     │     saldo         │                  │              │
    │                      │                     │──────────────────────────────────────►              │
    │                      │                     │◄──────────────────────────────────────              │
    │                      │                     │                   │                  │              │
    │                      │                     │ 11. Restar saldo  │                  │              │
    │                      │                     │     Actualizar    │                  │              │
    │                      │                     │     estado=PAGADO │                  │              │
    │                      │                     │──────────────────────────────────────►              │
    │                      │                     │                   │                  │              │
    │                      │                     │ 12. [Solo si no   │                  │              │
    │                      │                     │     horaria]:     │                  │              │
    │                      │                     │     NO pre-ocupa  │                  │              │
    │                      │                     │     plaza (v9.5) │                  │              │
    │                      │                     │                   │                  │              │
    │ 13. Pago confirmado  │                     │                   │                  │              │
    │◄────────────────────│                     │                   │                  │              │
```

## 4. Flujo de Worker de Mantenimiento

WorkerService ejecuta **3 hilos** en background:

### 4a. Limpieza de Reservas (cada 300 segundos)

```
WorkerService (Thread)     ReservationService        ParkingAforo          DB          NotificationService
    │                            │                       │                  │                 │
    │ 1. Cada 300 segundos      │                       │                  │                 │
    │───────────────────────────►│                       │                  │                 │
    │                            │                       │                  │                 │
    │                            │ 2. auto_finalize_     │                  │                 │
    │                            │    all_reservations() │                  │                 │
    │                            │                       │                  │                 │
    │                            │ 2a. Marcar COMPLETADA │                  │                 │
    │                            │     reservas vencidas │                  │                 │
    │                            │     (fecha_fin < ahora│                  │                 │
    │                            │     y estado=Activa)  │                  │                 │
    │                            │─────────────────────────────────────────►                 │
    │                            │◄─────────────────────────────────────────                 │
    │                            │                       │                  │                 │
    │  3. OK                   │                       │                  │                 │
    │◄───────────────────────────│                       │                  │                 │
```

### 4b. Worker de Notificaciones (continuo)

```
WorkerService (Thread)     UserNotificationService       EmailService         DB
    │                            │                          │                  │
    │ 1. Loop continuo          │                          │                  │
    │    _notification_worker() │                          │                  │
    │                           │                          │                  │
    │ 2. _process_reminders()   │                          │                  │
    │    Buscar reservas con    │                          │                  │
    │    inicio en 31 min       │                          │                  │
    │──────────────────────────────────────────────────────────────────────►   │
    │◄──────────────────────────────────────────────────────────────────────   │
    │                           │                          │                  │
    │    Enviar email recordatorio y                      │                  │
    │    crear notificacion in-app│                         │                  │
    │                           │─────────────────────────►│                  │
    │                           │◄─────────────────────────│                  │
    │                           │                          │                  │
    │ 3. _process_started_      │                          │                  │
    │    reservations()         │                          │                  │
    │    Auto-activar reservas  │                          │                  │
    │    cuando fecha_inicio    │                          │                  │
    │    <= ahora               │                          │                  │
    │──────────────────────────────────────────────────────────────────────►   │
    │◄──────────────────────────────────────────────────────────────────────   │
    │                           │                          │                  │
    │ 4. _process_auto_         │                          │                  │
    │    cancellations()        │                          │                  │
    │    Auto-cancelar reservas │                          │                  │
    │    PENDIENTES no pagadas  │                          │                  │
    │    30 min despues de      │                          │                  │
    │    fecha_inicio           │                          │                  │
    │──────────────────────────────────────────────────────────────────────►   │
    │                           │                          │                  │
    │    Enviar email de        │                          │                  │
    │    auto-cancelacion       │                          │                  │
    │                           │─────────────────────────►│                  │
    │                           │◄─────────────────────────│                  │
```

## 5. Flujo de Operación Manual (STAFF)

```
STAFF (Browser)       Admin Routes        AccessService        ParkingAforo     MQTT         DB
    │                      │                   │                    │            │          │
    │ 1. POST manual-entry │                   │                    │            │          │
    │─────────────────────►│                   │                    │            │          │
    │                      │                   │                    │            │          │
    │                      │ 2. manual_entry() │                    │            │          │
    │                      │──────────────────►│                    │            │          │
    │                      │                   │                    │            │          │
    │                      │                   │ 3. Verificar si    │            │          │
    │                      │                   │    ya está dentro  │            │          │
    │                      │                   │──────────────────────────────────►          │
    │                      │                   │◄──────────────────────────────────          │
    │                      │                   │                    │            │          │
    │                      │                   │ 4. Verificar       │            │          │
    │                      │                   │    capacidad       │            │          │
    │                      │                   │────────────────────────►                  │
    │                      │                   │◄────────────────────────                  │
    │                      │                   │                    │            │          │
    │                      │                   │ 5. Buscar reserva  │            │          │
    │                      │                   │    pagada para     │            │          │
    │                      │                   │    asociar         │            │          │
    │                      │                   │──────────────────────────────────►          │
    │                      │                   │◄──────────────────────────────────          │
    │                      │                   │                    │            │          │
    │                      │                   │ 6. Registrar       │            │          │
    │                      │                   │    ENTRADA         │            │          │
    │                      │                   │──────────────────────────────────►          │
    │                      │                   │                    │            │          │
    │                      │                   │ 7. Incrementar     │            │          │
    │                      │                   │    ocupacion       │            │          │
    │                      │                   │────────────────────────►                  │
    │                      │                   │                    │            │          │
    │  8. Entrada OK      │                   │                    │            │          │
    │◄────────────────────│                   │                    │            │          │
```
