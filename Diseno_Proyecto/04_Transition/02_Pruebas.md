# Estrategia de Pruebas — AUTOPASS

## Niveles de Prueba

### 1. Pruebas Unitarias (pytest)

Ubicación: `tests/`

| Archivo | Servicio Bajo Prueba | Casos Clave |
|---------|---------------------|-------------|
| `test_access_service.py` | AccessService | validate_plate, exit_plate, manual_entry, cortesía 10 min |
| `test_billing_service.py` | BillingService | Cálculo de tarifas trimodal, puntos, descuentos |
| `test_reservation_service.py` | ReservationService | Creación, pago, cancelación, reembolso, simulación |
| `test_user_service.py` | UserService | Creación con normalización de DNI y patente |
| `test_branch_service.py` | BranchService | CRUD sucursales, pisos, capacity summary |

**Ejecución:**
```powershell
.\venv\Scripts\python.exe -m pytest tests/ -v
```

### 2. Pruebas de Integración (Flujo Completo)

| Script | Propósito |
|--------|-----------|
| `test_user_flow.py` | Flujo completo de usuario: registro → login → crear reserva → pagar → cancelar |
| `test_multi_branch_rbac.py` | Verificación de aislamiento por sucursal y permisos RBAC |

**Ejecución:**
```powershell
.\venv\Scripts\python.exe test_user_flow.py
.\venv\Scripts\python.exe test_multi_branch_rbac.py
```

### 3. Pruebas de ALPR (Visión Artificial)

| Script | Propósito |
|--------|-----------|
| `test_video.py` | Prueba de fuente de video (cámara o archivo) |
| `alpr_service.py` (modo SCREEN_TO_SCREEN) | Simulación con video de archivo para validar detección |

**Ejecución:**
```powershell
.\venv\Scripts\python.exe scripts/test_video.py
```

### 4. Pruebas de Base de Datos

| Script | Propósito |
|--------|-----------|
| `migrate_add_normalized_patente.py` | Verificar migración de columna |
| `backfill_normalize_all_access_logs.py` | Verificar normalización masiva |
| `backfill_attach_reservations.py` | Verificar vinculación accesos ↔ reservas |
| `query_access_logs.py` | Consultar y verificar datos |
| `query_res.py` | Consultar reservas |

## Casos de Prueba Críticos

### TC-01: Ingreso ALPR exitoso
1. Enviar patente válida a `POST /v1/access/validate-plate`
2. Verificar: status 200, tipo_evento=ENTRADA, ocupacion_incrementada

### TC-02: Ingreso ALPR con reserva no horaria (v9.5)
1. Crear reserva de DÍA pagada
2. Enviar patente a validate-plate
3. Verificar: entrada permitida, ocupación NO incrementada

### TC-03: Salida con cortesía 10 min
1. Registrar entrada manual
2. Esperar 5 minutos (o usar virtual time)
3. Enviar salida
4. Verificar: costo_estadia=0, salida permitida

### TC-04: Salida sin pago (deuda)
1. Registrar entrada
2. Enviar salida inmediatamente (después de 10 min de cortesía)
3. Verificar: rechazo con monto de deuda

### TC-05: Cancelación de reserva con reembolso
1. Crear y pagar reserva de SEMANA
2. Cancelar a los 2 días
3. Verificar: reembolso proporcional, liberación de aforo

### TC-06: RBAC - Admin Local no puede crear Admin Global
1. Autenticar como LOCAL_ADMIN
2. Intentar cambiar rol de usuario a ADMIN
3. Verificar: 403 Forbidden

### TC-07: Worker - Liberación automática al vencer
1. Crear reserva que vence en 1 minuto (usar virtual time)
2. Avanzar tiempo + ejecutar worker manualmente
3. Verificar: reserva COMPLETADA, aforo liberado

### TC-08: Monitoreo - Grilla dinámica
1. Configurar 1 cámara → verificar grilla 1x1
2. Configurar 3 cámaras → verificar grilla 3x1
3. Configurar 5 cámaras → verificar grilla 3x2

## Cobertura de Pruebas por Módulo

| Módulo | Cobertura Objetivo | Estado |
|--------|-------------------|--------|
| Autenticación | 90% | ⚠ Parcial |
| Acceso (ALPR) | 85% | ✅ Alta |
| Reservas | 80% | ✅ Alta |
| Facturación | 90% | ✅ Alta |
| Aforo | 85% | ⚠ Parcial |
| Usuarios | 80% | ✅ Alta |
| Sucursales/Pisos | 75% | ⚠ Parcial |
| Admin operations | 70% | ⚠ Parcial |
| Fidelización | 60% | 🔄 En desarrollo |
| Monitoreo | 50% | 🔄 En desarrollo |
| Workers | 70% | ⚠ Parcial |

## Pruebas de Virtual Time

El sistema incluye un **Virtual Time Service** (`services/time_service.py`) que permite adelantar el reloj del sistema para pruebas sin alterar el reloj real.

```powershell
# Consultar estado
GET /v1/virtual-time/status

# Avanzar tiempo (ej: 2 horas)
POST /v1/virtual-time/advance
Body: { "seconds": 7200 }

# Resetear
POST /v1/virtual-time/reset
```

## Estrategia de Datos de Prueba

- **Patentes de prueba**: `ABC 123`, `ABC 1D23`, `A123ABC` (moto)
- **Usuarios de prueba**: admin@autopass.com / admin123 (ADMIN), local@test.com / test123 (LOCAL_ADMIN)
- **Sucursal de prueba**: "Sucursal Principal" creada por seed.py
