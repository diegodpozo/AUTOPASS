# Modelo de Casos de Uso — AUTOPASS

## Diagrama de Actores y Casos de Uso (Texto)

```
┌─────────────────────────────────────────────────────────────┐
│                    SISTEMA AUTOPASS                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ACTORES:                                                   │
│  ───────                                                    │
│  • Usuario No Autenticado (UU)                              │
│  • Cliente (USER)                                           │
│  • Personal STAFF                                           │
│  • Admin Local (LOCAL_ADMIN)                                │
│  • Admin Global (ADMIN)                                     │
│  • Sistema ALPR (actor secundario)                          │
│  • Hardware ESP32 (actor secundario)                        │
│                                                             │
│  CASOS DE USO PRINCIPALES:                                  │
│  ─────────────────────────                                   │
│  CU-01: Registrar usuario           [UU]                    │
│  CU-02: Iniciar sesión              [UU]                    │
│  CU-03: Recuperar contraseña        [UU]                    │
│  CU-04: Gestionar perfil            [USER]                  │
│  CU-05: Gestionar vehículos         [USER]                  │
│  CU-06: Hacer reserva               [USER]                  │
│  CU-07: Pagar reserva               [USER]                  │
│  CU-08: Cancelar reserva            [USER]                  │
│  CU-09: Ver ocupación               [USER, STAFF, ADMIN]    │
│  CU-10: Ingresar vehículo (ALPR)    [Sistema ALPR]          │
│  CU-11: Egresar vehículo (ALPR)     [Sistema ALPR]          │
│  CU-12: Pagar estadía               [USER]                  │
│  CU-13: Operación manual            [STAFF, LOCAL_ADMIN]    │
│  CU-14: Gestionar sucursales        [ADMIN]                 │
│  CU-15: Gestionar pisos             [LOCAL_ADMIN, ADMIN]     │
│  CU-16: Gestionar tarifas           [LOCAL_ADMIN]           │
│  CU-17: Gestionar usuarios          [ADMIN, LOCAL_ADMIN]    │
│  CU-18: Gestionar promociones       [ADMIN]                 │
│  CU-19: Ver reportes financieros    [ADMIN, LOCAL_ADMIN]    │
│  CU-20: Monitorear cámaras          [ADMIN, LOCAL_ADMIN]    │
└─────────────────────────────────────────────────────────────┘
```

## Especificación de Casos de Uso Críticos

---

### CU-10: Ingresar vehículo (ALPR)

**Actor:** Sistema ALPR  
**Disparador:** Cámara detecta patente o QR  
**Precondiciones:** El sistema ALPR está activo y conectado al backend

**Flujo Principal:**
1. El ALPR captura un frame con una patente o QR
2. El ALPR envía la patente a `POST /v1/access/validate-plate`
3. El backend verifica si el vehículo ya está dentro (`AccessService.validate_plate`)
4. El backend busca una reserva activa para la patente
5. Si hay reserva no horaria pagada: permite entrada SIN incrementar aforo
6. Si hay reserva por hora pagada: permite entrada e incrementa aforo
7. Si no hay reserva: verifica capacidad disponible
8. Si hay capacidad: registra entrada (ENTRADA), incrementa aforo, envía comando MQTT "OPEN" a la barrera
9. El backend notifica cambio de ocupación vía WebSocket
10. Retorna éxito con datos del vehículo

**Flujo Alternativo (ya está dentro):**
- Si el vehículo ya tiene una ENTRADA sin SALIDA posterior: rechaza con "Vehículo ya se encuentra en la sede"

**Flujo Alternativo (sin capacidad):**
- Si no hay lugar: rechaza con "Estacionamiento completo"

**Postcondiciones:** Vehículo registrado como ENTRADA, barrera abierta, aforo actualizado

---

### CU-11: Egresar vehículo (ALPR)

**Actor:** Sistema ALPR  
**Disparador:** Cámara de salida detecta patente  
**Precondiciones:** Vehículo está dentro (tiene ENTRADA registrada sin SALIDA)

**Flujo Principal:**
1. El ALPR envía patente a `POST /v1/access/exit-plate`
2. El backend verifica que el vehículo está dentro
3. El backend verifica el tiempo de estadía:
   - Si ≤ 10 minutos: permite salida sin cargo (cortesía)
   - Si > 10 minutos: verifica que haya pagado (`pago_confirmado` o reserva paga)
4. Si todo OK: registra SALIDA, actualiza aforo, envía "OPEN" por MQTT
5. Si no ha pagado: rechaza con monto de deuda

**Postcondiciones:** Vehículo registrado como SALIDA, barrera abierta, aforo actualizado

---

### CU-06: Hacer reserva

**Actor:** Cliente (USER)  
**Disparador:** Usuario selecciona "Nueva Reserva" desde el perfil

**Flujo Principal:**
1. El usuario selecciona tipo de estadía (hora/día/semana/quincena/mes)
2. El usuario ingresa patente, sucursal, piso y fecha/hora
3. El sistema verifica disponibilidad de capacidad
4. Para reservas por hora: valida anticipación mínima (1 hora configurable)
5. El sistema muestra el costo total estimado
6. El usuario confirma la reserva
7. El sistema crea la reserva con estado PENDIENTE
8. El sistema envía email de confirmación con QR embebido

**Flujo Alternativo (pago inmediato):**
- En paso 6, el usuario puede pagar directamente desde su saldo
- Si paga: reserva pasa a PAGADA, se descuenta del saldo

**Postcondiciones:** Reserva creada en estado PENDIENTE o PAGADA

---

### CU-14: Gestionar sucursales

**Actor:** Admin Global (ADMIN)  
**Disparador:** Admin selecciona "Sucursales" en el panel de administración

**Flujo Principal:**
1. El sistema lista todas las sucursales con su estado (activa/suspendida)
2. El admin puede:
   - Crear nueva sucursal: nombre, dirección, teléfono, horario, coordenadas (vía Leaflet.js), logo
   - Editar sucursal existente
   - Activar/suspender sucursal (toggle)
   - Eliminar sucursal

**Postcondiciones:** Sucursal creada/actualizada en base de datos

---

### CU-13: Operación manual (STAFF)

**Actor:** Personal STAFF, LOCAL_ADMIN  
**Disparador:** Situación excepcional (ALPR no detecta, cliente sin patente, etc.)

**Flujo Principal:**
1. El operador selecciona el tipo de operación:
   - **Ingreso manual**: Ingresa patente manualmente, selecciona tipo de vehículo, registra entrada
   - **Egreso manual**: Ingresa patente, registra salida (con verificación de pago)
   - **Abrir barrera**: Abre la barrera sin registro (para emergencias)
   - **Cancelar estadía**: Cancela estadía activa (cortesía 10 min)

**Postcondiciones:** Operación registrada en access_logs, aforo actualizado si corresponde

---

## Matriz Actor vs Caso de Uso

| Caso de Uso | UU | USER | STAFF | LOCAL_ADMIN | ADMIN | ALPR |
|-------------|:--:|:----:|:-----:|:-----------:|:-----:|:----:|
| CU-01 Registrar | ✓ | | | | | |
| CU-02 Login | ✓ | | | | | |
| CU-03 Recuperar pass | ✓ | | | | | |
| CU-04 Perfil | | ✓ | | | | |
| CU-05 Vehículos | | ✓ | | | | |
| CU-06 Reserva | | ✓ | | | | |
| CU-07 Pagar reserva | | ✓ | | | | |
| CU-08 Cancelar reserva | | ✓ | | | | |
| CU-09 Ver ocupación | | ✓ | ✓ | ✓ | ✓ | |
| CU-10 Ingreso ALPR | | | | | | ✓ |
| CU-11 Egreso ALPR | | | | | | ✓ |
| CU-12 Pagar estadía | | ✓ | | | | |
| CU-13 Operación manual | | | ✓ | ✓ | ✓ | |
| CU-14 Sucursales | | | | | ✓ | |
| CU-15 Pisos | | | | ✓ | ✓ | |
| CU-16 Tarifas | | | | ✓ | ✓ | |
| CU-17 Usuarios (admin) | | | | ✓ | ✓ | |
| CU-18 Promociones | | | | ✓ | ✓ | |
| CU-19 Reportes | | | | ✓ | ✓ | |
| CU-20 Monitoreo | | | | ✓ | ✓ | |
