# Mapa Completo de Rutas API — AUTOPASS

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
| GET | `/branches` | Listar sucursales | Público |
| POST | `/branches` | Crear sucursal | ADMIN |
| PATCH | `/branches/{id}` | Editar sucursal | ADMIN |
| DELETE | `/branches/{id}` | Eliminar sucursal | ADMIN |
| POST | `/branches/{id}/toggle` | Activar/suspender | ADMIN |
| POST | `/{id}/floors` | Agregar piso | LOCAL_ADMIN+ |
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
| GET | `/virtual-time` | Ver tiempo virtual | USER+ |
| GET | `/virtual-time/status` | Estado del tiempo virtual | USER+ |
| POST | `/virtual-time/advance` | Adelantar tiempo (testing, minutos/horas/días) | USER+ |
| POST | `/virtual-time/set` | Establecer offset de tiempo (offset_seconds) | USER+ |
| POST | `/virtual-time/reset` | Resetear tiempo virtual | USER+ |
| GET | `/support-tickets` | Listar tickets de soporte (filtro sucursal/estado) | STAFF+ |
| PATCH | `/support-tickets/{ticket_id}` | Actualizar estado/responder ticket | STAFF+ |

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
| GET | `/points-history` | Historial puntos | USER+ |
| GET | `/profile/notifications` | Notificaciones | USER+ |
| GET | `/profile/notifications/unread` | No leídas | USER+ |
| PATCH | `/profile/notifications/{id}/read` | Marcar leída | USER+ |
| POST | `/profile/notifications/read-all` | Leer todas | USER+ |
| DELETE | `/profile/notifications/{id}` | Eliminar notificación | USER+ |
| DELETE | `/profile/notifications/clear-read` | Eliminar notificaciones leídas | USER+ |
| POST | `/support-tickets` | Crear ticket de soporte | USER+ |
| GET | `/support-tickets` | Ver mis tickets de soporte | USER+ |

## Prefijo: `/v1/user/mercadopago` (pagos Checkout Pro)
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| POST | `/mercadopago/checkout` | Crear preferencia Checkout Pro (pagar reserva/estadía) | USER+ |
| GET | `/mercadopago/success` | Retorno: pago aprobado | Público (MP) |
| GET | `/mercadopago/pending` | Retorno: pago pendiente | Público (MP) |
| GET | `/mercadopago/failure` | Retorno: pago fallido | Público (MP) |
| POST | `/mercadopago/webhook` | Webhook de confirmación de pago | Público (MP) |

## Prefijo: `/v1/parking`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| POST | `/access/validate-plate` | Validar patente ALPR | Público (ALPR) |
| POST | `/access/exit-plate` | Validar salida ALPR | Público (ALPR) |
| POST | `/access/validate-qr` | Validar QR | Público (ALPR) |
| POST | `/access/pay-stay` | Pagar estadía | Público |
| GET | `/parking/status` | Estado aforo | STAFF+ |
| GET | `/parking/current-occupancy` | Ocupación actual | STAFF+ |
| GET | `/parking/branches` | Sucursales activas | Público |
| WS | `/parking/ws` | WebSocket ocupación | USER+ |

## Prefijo: `/v1/reports`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| GET | `/financial-summary` | Resumen financiero | STAFF+ |
| GET | `/payment-history` | Historial transacciones | LOCAL_ADMIN+ |
| GET | `/access` | Historial accesos | STAFF+ |

## Prefijo: `/v1/system`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| GET | `/health` | Health check | STAFF+ |
| POST | `/heartbeat` | Heartbeat ALPR | Público (ALPR) |
| POST | `/reset` | Reset sistema | ADMIN |
| GET | `/cameras` | Listar cámaras | STAFF+ |
| POST | `/cameras` | Crear cámara | STAFF+ |
| PUT | `/cameras/{id}` | Editar cámara | STAFF+ |
| DELETE | `/cameras/{id}` | Eliminar cámara | STAFF+ |
| POST | `/cameras/{id}/control/{action}` | Start/stop cámara | STAFF+ |
| GET | `/camera-config/{gate}` | Ver config cámara | STAFF+ |
| POST | `/camera-config` | Configurar cámara | STAFF+ |
| POST | `/camera-service/{gate}/{action}` | Start/stop servicio | STAFF+ |
| POST | `/update-frame/{camera_id}` | Actualizar frame | Público (ALPR) |
| GET | `/video-feed/{camera_id}` | Feed MJPEG | STAFF+ |
| WS | `/ws/video/{camera_id}` | WebSocket video | STAFF+ |
| GET | `/capture/{log_id}` | Ver imagen capturada | STAFF+ |

## Vistas (Frontend)
| Método | Ruta | Template | Rol Requerido |
|--------|------|----------|---------------|
| GET | `/` | index.html | Público |
| GET | `/dashboard` | dashboard.html | Público |
| GET | `/perfil` | perfil.html | Público |
| GET | `/nuestra-red` | nuestra-red.html | Público |
| GET | `/contacto` | contacto.html | Público |
| GET | `/terminos` | terminos.html | Público |
| GET | `/privacidad` | privacidad.html | Público |
| GET | `/reset-password` | reset_password.html | Público |
| GET | `/monitoreo` | monitoreo_live.html | Público |
