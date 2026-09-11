# Especificación de la API: AUTOPASS

Esta API centraliza la lógica de negocio y permite la interacción entre el Portal de Usuario (Web/PWA), el Panel Administrativo (Dashboard), los Clientes Móviles, la Visión Artificial ALPR y el Hardware IoT (ESP32/Arduino).

**Base URL**: `/v1`
**Protocolo**: REST (JSON) + WebSockets (Aforo Real-time & Video Streaming)

---

## 1. Autenticación y OAuth (`/v1/auth`)
| Endpoint | Método | Descripción | Permisos |
| :--- | :--- | :--- | :--- |
| `/v1/auth/login` | `POST` | Autenticación con email/contraseña | Público (Rate limit 15/min) |
| `/v1/auth/register` | `POST` | Auto-registro de cliente | Público (Rate limit 10/min) |
| `/v1/auth/forgot-password` | `POST` | Solicita token de recuperación de contraseña | Público (Rate limit 5/min) |
| `/v1/auth/reset-password` | `POST` | Restablece contraseña con token de recuperación | Público (Rate limit 10/min) |
| `/v1/auth/oauth/providers` | `GET` | Lista proveedores social login configurados | Público |
| `/v1/auth/oauth/{provider}/authorize` | `GET` | Genera URI de autorización con state HMAC | Público |
| `/v1/auth/oauth/{provider}/callback` | `GET` | Callback OAuth: login directo o emite signup token | Público |
| `/v1/auth/oauth/complete` | `POST` | Finaliza alta social registrando DNI y teléfono | Público |

---

## 2. Administración (`/v1/admin`)
| Endpoint | Método | Descripción | Permisos |
| :--- | :--- | :--- | :--- |
| `/v1/admin/users/` | `GET / POST` | Listar y crear usuarios | `ADMIN` / `LOCAL_ADMIN` |
| `/v1/admin/users/{user_id}` | `PATCH / DELETE` | Editar, cambiar rol/password o soft-delete usuario | `ADMIN` / `LOCAL_ADMIN` |
| `/v1/admin/branches/` | `GET / POST` | Listar y crear sucursales | `ADMIN` |
| `/v1/admin/branches/{branch_id}` | `PATCH / DELETE` | Editar sucursal (renombre con propagación) o desactivar | `ADMIN` |
| `/v1/admin/reservations/` | `GET / POST` | Listar con filtros y crear reserva a nombre de usuario | `ADMIN` / `LOCAL_ADMIN` |
| `/v1/admin/reservations/{id}` | `PATCH / DELETE` | Editar fechas/patente/tipo_vehiculo o cancelar reserva | `ADMIN` / `LOCAL_ADMIN` |
| `/v1/admin/reservations/{id}/confirm-payment` | `POST` | Confirmar pago manual (`DIGITAL`, `CAJA`, `MERCADOPAGO`, `SALDO`) | `ADMIN` / `LOCAL_ADMIN` |
| `/v1/admin/promotions/` | `GET / POST / PATCH` | CRUD y toggle de promociones del catálogo | `ADMIN` / `LOCAL_ADMIN` |
| `/v1/admin/operations/manual-entry` | `POST` | Registro de ingreso manual de vehículo | `STAFF`+ |
| `/v1/admin/operations/manual-exit` | `POST` | Registro de egreso manual de vehículo | `STAFF`+ |
| `/v1/admin/operations/open-barrier` | `POST` | Apertura manual de barrera vía MQTT/Serial | `STAFF`+ |

---

## 3. Portal de Usuario (`/v1/user`)
| Endpoint | Método | Descripción | Permisos |
| :--- | :--- | :--- | :--- |
| `/v1/user/profile` | `GET / PATCH` | Consultar y actualizar perfil de usuario | Autenticado |
| `/v1/user/vehicles` | `GET / POST / DELETE` | CRUD de vehículos asociados | Autenticado |
| `/v1/user/reservations` | `GET / POST` | Listar e iniciar solicitud de reserva | Autenticado |
| `/v1/user/reservations/check-availability` | `GET` | Validar disponibilidad exclusiva (sweep-line) | Autenticado |
| `/v1/user/reservations/disabled-dates` | `GET` | Días sin cupos de reserva en 90 días | Autenticado |
| `/v1/user/reservations/disabled-hours` | `GET` | Horas deshabilitadas para una fecha dada | Autenticado |
| `/v1/user/reservations/{id}/pay` | `POST` | Pagar reserva con saldo virtual | Autenticado |
| `/v1/user/reservations/{id}/cancel` | `POST` | Cancelar reserva con cálculo de reembolso | Autenticado |
| `/v1/user/mercadopago/checkout` | `POST` | Crear preferencia Checkout Pro para reserva/estadía | Autenticado |
| `/v1/user/mercadopago/webhook` | `POST` | Callback/Webhook asíncrono de Mercado Pago | Público |
| `/v1/user/support-tickets` | `GET / POST` | Consultar y crear tickets de soporte con adjuntos | Autenticado |

---

## 4. Control de Acceso y Aforo (`/v1/parking`)
| Endpoint | Método | Descripción | Permisos |
| :--- | :--- | :--- | :--- |
| `/v1/parking/validate-plate` | `POST` | Valida patente leída por ALPR en ingreso | Sistema ALPR |
| `/v1/parking/pay-stay` | `POST` | Registra pago de estadía (`DIGITAL` o `CAJA`) | Staff / Sistema |
| `/v1/parking/exit-plate` | `POST` | Valida salida ALPR y abre barrera | Sistema ALPR |
| `/v1/parking/current-occupancy` | `GET` | Ocupación física + disponibilidad de reserva | Público |
| `/v1/parking/ws` | `WS` | WebSocket de aforo en tiempo real | Público |

---

## Ejemplos de Payload

### 1. Crear Reserva como Admin (`POST /v1/admin/reservations/`)
```json
{
  "user_id": 5,
  "sucursal_nombre": "AUTOPASS Morón",
  "patente": "AA123BB",
  "tipo_vehiculo": "auto",
  "fecha_inicio": "2026-09-12T10:00:00Z",
  "fecha_fin": "2026-09-12T12:00:00Z"
}
```

### 2. Confirmar Pago de Reserva (`POST /v1/admin/reservations/15/confirm-payment`)
```json
{
  "metodo_pago": "CAJA",
  "monto": 3000.0
}
```

### 3. Validar Patente ALPR (`POST /v1/parking/validate-plate`)
```json
{
  "plate": "AA123BB",
  "gate_id": "MORON_PATENTE_INGRESO_1"
}
```
**Respuesta (200 OK)**:
```json
{
  "status": "allowed",
  "action": "OPEN_GATE",
  "message": "¡BIENVENIDO JUAN PEREZ! Acceso por reserva autorizado.",
  "access_log_id": 142
}
```
