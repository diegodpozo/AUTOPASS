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

### 2. Capa de Datos (Modelos y Enums)
- **Seguridad de Tipos:** Se han implementado Enums en `models/enums.py` para eliminar "strings mágicos" (ej: `UserRole`, `VehicleType`, `ReservationStatus`).
- **Gestión Vertical:** Soporte para sucursales con múltiples pisos (`ParkingFloor`).

---

## Reglas de Arquitectura
1. **Rutas Delgadas:** Los controladores en `routes/` no deben contener lógica de negocio. Solo delegan a los servicios correspondientes.
2. **Independencia:** Los servicios deben importar modelos y esquemas, pero no routers.
3. **Tipo Seguro:** Usar siempre los Enums definidos en `models/enums.py` para cualquier estado o rol del sistema.
4. **Configuración Centralizada:** Cualquier parámetro, constante o URL externa debe ser configurada en `core/config.py` y, si es necesario, provista vía `.env`.
5. **Aforo por Reserva:** Las reservas no horarias (Día/Semana/Quincena/Mes) descuentan la plaza al pagar y la liberan solo al vencer o cancelar. Las reservas por hora descuentan al entrar físicamente.
6. **Liberación Diferida:** La salida física nunca libera plazas de reservas no horarias — la liberación la gestiona exclusivamente `auto_finalize_all_reservations` al vencer el período.
