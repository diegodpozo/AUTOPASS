# Mapa Completo de Rutas API — AUTOPASS

> **Nota de roles:** `STAFF+` = ADMIN, LOCAL_ADMIN, STAFF (usa `get_operational_user`). `LOCAL_ADMIN+` = ADMIN, LOCAL_ADMIN (usa `get_local_manager`). `ADMIN` = solo Administrador Global (usa `get_super_admin`).
> `Público` = sin autenticación (endpoint accesible desde cualquier cliente). La mayoría de rutas `Público` de ALPR/MP están pensadas para ser llamadas por los sistemas externos de cámaras/Mercado Pago.

## Prefijo: `/v1/auth`
| Método | Ruta | Función | Rol Requerido | Rate Limit |
|--------|------|---------|---------------|------------|
| POST | `/login` | Iniciar sesión (registra `UserSession`, retorna `nuevo_dispositivo`) | Público | 15/min |
| POST | `/register` | Registrarse (rol `USER`) | Público | 10/min |
| POST | `/forgot-password` | Solicitar recuperación (token `purpose: recovery`, 30 min) | Público | 5/min |
| POST | `/reset-password` | Resetear contraseña | Público | 10/min |

## Prefijo: `/v1/admin`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| GET | `/users` | Listar usuarios | LOCAL_ADMIN+ |
| POST | `/users` | Crear usuario | LOCAL_ADMIN+ |
| PATCH | `/users/{id}` | Editar usuario | LOCAL_ADMIN+ |
| POST | `/users/{id}/role` | Cambiar rol | ADMIN |
| POST | `/users/{id}/toggle-block` | Bloquear/desbloquear | LOCAL_ADMIN+ |
| POST | `/users/{id}/balance` | Ajustar saldo | LOCAL_ADMIN+ |
| POST | `/users/{id}/password` | Cambiar contraseña | LOCAL_ADMIN+ |
| DELETE | `/users/{id}` | Eliminar usuario | ADMIN |
| POST | `/users/{id}/delete` | Eliminar usuario (alias POST) | ADMIN |
| GET | `/branches` | Listar sucursales (solo activas si es público) | Público |
| POST | `/branches` | Crear sucursal | ADMIN |
| PATCH | `/branches/{id}` | Editar sucursal | ADMIN |
| DELETE | `/branches/{id}` | Eliminar sucursal | ADMIN |
| POST | `/branches/{id}/toggle` | Activar/suspender | ADMIN |
| POST | `/{branch_id}/floors` | Agregar piso | LOCAL_ADMIN+ |
| PATCH | `/floors/{id}` | Editar piso | LOCAL_ADMIN+ |
| DELETE | `/floors/{id}` | Eliminar piso | LOCAL_ADMIN+ |
| GET | `/reservations` | Listar reservas | STAFF+ |
| POST | `/reservations` | Crear reserva admin | STAFF+ |
| PATCH | `/reservations/{id}` | Editar reserva | STAFF+ |
| POST | `/reservations/{id}/confirm-payment` | Confirmar pago | STAFF+ |
| POST | `/reservations/{id}/cancel` | Cancelar reserva | STAFF+ |
| GET | `/promotions` | Listar promos | LOCAL_ADMIN+ |
| POST | `/promotions` | Crear promo | LOCAL_ADMIN+ |
| POST | `/promotions/{id}/toggle` | Activar/desactivar | LOCAL_ADMIN+ |
| DELETE | `/promotions/{id}` | Eliminar promo | LOCAL_ADMIN+ |
| POST | `/open-barrier` | Abrir barrera | STAFF+ |
| POST | `/manual-entry` | Ingreso manual | STAFF+ |
| POST | `/manual-exit` | Egreso manual | STAFF+ |
| POST | `/cancel-stay` | Cancelar estadía | STAFF+ |
| GET | `/settings` | Ver config | LOCAL_ADMIN+ |
| POST | `/settings/prices` | Actualizar tarifas | LOCAL_ADMIN+ |
| GET | `/virtual-time` (y `/virtual-time/status`) | Ver tiempo virtual | LOCAL_ADMIN+ |
| POST | `/virtual-time/advance` | Adelantar tiempo (testing, minutos/horas/días) | LOCAL_ADMIN+ |
| POST | `/virtual-time/rewind` | Retroceder tiempo (testing) | LOCAL_ADMIN+ |
| POST | `/virtual-time/set-target` | Fijar fecha/hora exacta (ISO, ej: `2026-10-15T14:30:00`) | LOCAL_ADMIN+ |
| POST | `/virtual-time/set` | Establecer offset de tiempo (`offset_seconds`) | LOCAL_ADMIN+ |
| POST | `/virtual-time/reset` | Resetear tiempo virtual | LOCAL_ADMIN+ |
| GET | `/support-tickets` | Listar tickets de soporte (filtro sucursal/estado) | STAFF+ |
| GET | `/support-tickets/{ticket_id}` | Ver ticket con todos sus mensajes | STAFF+ |
| GET | `/support-tickets/pending-count` | Cantidad de tickets no leídos por el admin actual | STAFF+ |
| PATCH | `/support-tickets/{ticket_id}` | Actualizar estado/responder ticket | STAFF+ |
| PATCH | `/support-tickets/{ticket_id}/read-notifs` | Marcar notificaciones del ticket como leídas | STAFF+ |

> Nota virtual-time: además de `/virtual-time`, hay un endpoint de solo lectura bajo `/v1/system/virtual-time`.

## Prefijo: `/v1/user`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| GET | `/me` | Ver perfil | USER+ |
| PUT | `/me` | Editar perfil | USER+ |
| POST | `/change-password` | Cambiar contraseña | USER+ |
| GET | `/vehicles` | Listar vehículos | USER+ |
| POST | `/vehicles` | Agregar vehículo | USER+ |
| POST | `/vehicles/{patente}/favorite` | Favorito | USER+ |
| DELETE | `/vehicles/{patente}` | Eliminar vehículo | USER+ |
| GET | `/active-stays` | Estadías activas | USER+ |
| GET | `/payment-history` | Historial pagos | USER+ |
| GET | `/rates` | Ver tarifas | Público |
| POST | `/recharge-balance` | Recargar saldo | USER+ |
| GET | `/reservations` | Mis reservas | USER+ |
| GET | `/reservations/check-availability` | Disponibilidad | USER+ |
| GET | `/reservations/disabled-dates` | Fechas sin disponibilidad | USER+ |
| GET | `/reservations/disabled-hours` | Slots horarios sin disponibilidad | USER+ |
| POST | `/reservations` | Crear reserva | USER+ |
| PATCH | `/reservations/{id}` | Modificar reserva | USER+ |
| POST | `/reservations/{id}/pay` | Pagar reserva | USER+ |
| POST | `/reservations/{id}/confirm-reminder` | Confirmar recordatorio | USER+ |
| GET | `/reservations/{id}/cancel-simulation` | Simular cancelación | USER+ |
| POST | `/reservations/{id}/cancel` | Cancelar reserva | USER+ |
| GET | `/promotions` | Ver promos | USER+ |
| POST | `/redeem/{promo_id}` | Canjear puntos | USER+ |
| POST | `/points-adjust` | Ajustar puntos (admin) | USER+ (validado por rol) |
| GET | `/redemption-tickets` | Tickets de canje | USER+ |
| GET | `/redemptions/available` | Canjes disponibles | USER+ |
| POST | `/redemptions/{ticket_id}/cancel` | Cancelar canje | USER+ |
| GET | `/points-history` | Historial puntos | USER+ |
| GET | `/profile/notifications` | Notificaciones | USER+ |
| GET | `/profile/notifications/unread` | No leídas | USER+ |
| PATCH | `/profile/notifications/{id}/read` | Marcar leída | USER+ |
| POST | `/profile/notifications/read-all` | Leer todas | USER+ |
| DELETE | `/profile/notifications/{id}` | Eliminar notificación | USER+ |
| DELETE | `/profile/notifications/clear-read` | Eliminar notificaciones leídas | USER+ |
| POST | `/support-tickets` | Crear ticket de soporte | USER+ |
| GET | `/support-tickets` | Ver mis tickets de soporte | USER+ |
| GET | `/support-tickets/{ticket_id}` | Ver detalle de ticket propio | USER+ |
| PATCH | `/support-tickets/{ticket_id}/reply` | Responder en ticket propio | USER+ |

## Prefijo: `/v1/user/mercadopago` (pagos Checkout Pro)
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| POST | `/mercadopago/checkout` | Crear preferencia Checkout Pro (pagar reserva/estadía) | USER+ |
| GET | `/mercadopago/success` | Retorno: pago aprobado | Público (MP) |
| GET | `/mercadopago/pending` | Retorno: pago pendiente | Público (MP) |
| GET | `/mercadopago/failure` | Retorno: pago fallido | Público (MP) |
| POST | `/mercadopago/webhook` | Webhook de confirmación de pago | Público (MP) |

## Prefijo: `/v1/parking`
| Método | Ruta | Función | Rol Requerido | Rate Limit |
|--------|------|---------|---------------|------------|
| POST | `/access/validate-plate` | Validar patente ALPR | Público (ALPR) | 120/min |
| POST | `/access/exit-plate` | Validar salida ALPR | Público (ALPR) | 120/min |
| POST | `/access/validate-qr` | Validar QR | Público (ALPR) | 60/min |
| POST | `/access/pay-stay` | Pagar estadía (`plate`, `metodo=DIGITAL\|CAJA`) | Público | — |
| GET | `/parking/status` | Estado aforo | STAFF+ |
| GET | `/parking/current-occupancy` | Ocupación actual | STAFF+ |
| GET | `/parking/branches` | Sucursales activas | Público |
| WS | `/parking/ws` | WebSocket ocupación | USER+ |

## Prefijo: `/v1/reports`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| GET | `/financial-summary` | Resumen financiero (incluye recaudado efectivo y digital) | STAFF+ |
| GET | `/payment-history` | Historial transacciones | LOCAL_ADMIN+ |
| GET | `/access` | Historial accesos | STAFF+ |
| GET | `/ocr-stats` | Estadísticas de OCR | STAFF+ |

## Prefijo: `/v1/system`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| GET | `/health` | Health check | STAFF+ |
| POST | `/heartbeat` | Heartbeat ALPR | Público (ALPR) |
| POST | `/reset` | Reset sistema | ADMIN |
| GET | `/virtual-time` | Ver tiempo virtual (solo lectura) | LOCAL_ADMIN+ |
| GET | `/cameras` | Listar cámaras | STAFF+ |
| POST | `/cameras` | Crear cámara | STAFF+ |
| PUT | `/cameras/{id}` | Editar cámara | STAFF+ |
| DELETE | `/cameras/{id}` | Eliminar cámara | STAFF+ |
| POST | `/cameras/{id}/control/{action}` | Start/stop cámara | STAFF+ |
| GET | `/camera-config/{gate}` | Ver config cámara | STAFF+ |
| POST | `/camera-config` | Configurar cámara | STAFF+ |
| POST | `/camera-service/{gate}/{action}` | Start/stop servicio | STAFF+ |
| POST | `/camera-reading/{gate_id}` | Leer patente del frame actual | Público (ALPR) |
| POST | `/update-frame/{camera_id}` | Actualizar frame | Público (ALPR) |
| GET | `/video-feed/{camera_id}` | Feed MJPEG | STAFF+ |
| WS | `/ws/video/{camera_id}` | WebSocket video | STAFF+ |
| GET | `/capture/{log_id}` | Ver imagen capturada | STAFF+ |

## Vistas (Frontend)
| Método | Ruta | Template | Rol Requerido |
|--------|------|----------|---------------|
| GET | `/` | index.html | Público |
| GET | `/instalar` | instalar.html (guía instalación PWA) | Público |
| GET | `/dashboard` | dashboard.html | Público |
| GET | `/perfil` | perfil.html | Público |
| GET | `/nuestra-red` | nuestra-red.html | Público |
| GET | `/contacto` | contacto.html | Público |
| GET | `/terminos` | terminos.html | Público |
| GET | `/privacidad` | privacidad.html | Público |
| GET | `/reset-password` | reset_password.html | Público |
| GET | `/monitoreo` | monitoreo_live.html | Público |
| GET | `/estadisticas-ocr` | estadisticas_ocr.html | Público |
| GET | `/sw.js` | Service worker PWA (scope raíz) | Público |
| GET | `/manifest.webmanifest` | Manifest PWA | Público |