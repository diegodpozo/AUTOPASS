# Arquitectura del Sistema: AUTOPASS

Este documento detalla la estructura técnica y el flujo de datos del ecosistema de estacionamiento inteligente tras la refactorización a **Arquitectura Limpia** (v8.5.0).

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

## Capas y Responsabilidades (v8.5.0)

### 1. Capa de Servicios (Service Layer)
Toda la lógica de negocio se ha centralizado en archivos bajo `services/`:
- **`AccessService`**: Gestiona toda la lógica de validación de patentes, salidas y QR.
- **`ReservationService`**: Gestiona el ciclo de vida de las reservas (creación, edición, cancelación con reembolsos proporcionales).
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
