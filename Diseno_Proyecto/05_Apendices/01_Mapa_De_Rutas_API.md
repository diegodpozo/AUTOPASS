# Mapa Completo de Rutas API — AUTOPASS

## Prefijo: `/v1/auth`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| POST | `/login` | Iniciar sesión | Público |
| POST | `/register` | Registrarse | Público |
| POST | `/forgot-password` | Solicitar recuperación | Público |
| POST | `/reset-password` | Resetear contraseña | Público |
| POST | `/refresh` | Renovar token | USER+ |

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
| GET | `/branches` | Listar sucursales | LOCAL_ADMIN+ |
| POST | `/branches` | Crear sucursal | ADMIN |
| PATCH | `/branches/{id}` | Editar sucursal | LOCAL_ADMIN+ |
| DELETE | `/branches/{id}` | Eliminar sucursal | ADMIN |
| POST | `/branches/{id}/toggle` | Activar/suspender | ADMIN |
| POST | `/{id}/floors` | Agregar piso | LOCAL_ADMIN+ |
| PATCH | `/floors/{id}` | Editar piso | LOCAL_ADMIN+ |
| DELETE | `/floors/{id}` | Eliminar piso | LOCAL_ADMIN+ |
| GET | `/reservations` | Listar reservas | LOCAL_ADMIN+ |
| POST | `/reservations` | Crear reserva admin | LOCAL_ADMIN+ |
| PATCH | `/reservations/{id}` | Editar reserva | LOCAL_ADMIN+ |
| POST | `/reservations/{id}/confirm-payment` | Confirmar pago | LOCAL_ADMIN+ |
| POST | `/reservations/{id}/cancel` | Cancelar reserva | LOCAL_ADMIN+ |
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
| GET | `/rates` | Ver tarifas | USER+ |
| POST | `/recharge-balance` | Recargar saldo | USER+ |
| GET | `/reservations` | Mis reservas | USER+ |
| GET | `/reservations/check-availability` | Disponibilidad | USER+ |
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

## Prefijo: `/v1/parking`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| POST | `/access/validate-plate` | Validar patente ALPR | Público (ALPR) |
| POST | `/access/exit-plate` | Validar salida ALPR | Público (ALPR) |
| POST | `/access/validate-qr` | Validar QR | Público (ALPR) |
| POST | `/access/pay-stay` | Pagar estadía | USER+ |
| GET | `/parking/status` | Estado aforo | USER+ |
| GET | `/parking/current-occupancy` | Ocupación actual | STAFF+ |
| GET | `/parking/branches` | Sucursales activas | Público |
| WS | `/parking/ws` | WebSocket ocupación | USER+ |

## Prefijo: `/v1/reports`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| GET | `/financial-summary` | Resumen financiero | LOCAL_ADMIN+ |
| GET | `/payment-history` | Historial transacciones | LOCAL_ADMIN+ |
| GET | `/access` | Historial accesos | LOCAL_ADMIN+ |

## Prefijo: `/v1/system`
| Método | Ruta | Función | Rol Requerido |
|--------|------|---------|---------------|
| GET | `/health` | Health check | STAFF+ |
| POST | `/heartbeat` | Heartbeat ALPR | Público (ALPR) |
| POST | `/reset` | Reset sistema | ADMIN |
| GET | `/cameras` | Listar cámaras | LOCAL_ADMIN+ |
| POST | `/cameras` | Crear cámara | LOCAL_ADMIN+ |
| PUT | `/cameras/{id}` | Editar cámara | LOCAL_ADMIN+ |
| DELETE | `/cameras/{id}` | Eliminar cámara | LOCAL_ADMIN+ |
| POST | `/cameras/{id}/control/{action}` | Start/stop cámara | LOCAL_ADMIN+ |
| GET | `/camera-config/{gate}` | Ver config cámara | LOCAL_ADMIN+ |
| POST | `/camera-config` | Configurar cámara | LOCAL_ADMIN+ |
| POST | `/camera-service/{gate}/{action}` | Start/stop servicio | LOCAL_ADMIN+ |
| POST | `/update-frame/{camera_id}` | Actualizar frame | Público (ALPR) |
| GET | `/video-feed/{camera_id}` | Feed MJPEG | STAFF+ |
| WS | `/ws/video/{camera_id}` | WebSocket video | STAFF+ |
| GET | `/capture/{log_id}` | Ver imagen capturada | STAFF+ |
| GET | `/virtual-time` | Tiempo virtual | Público |

## Vistas (Frontend)
| Método | Ruta | Template | Rol Requerido |
|--------|------|----------|---------------|
| GET | `/` | index.html | Público |
| GET | `/dashboard` | dashboard.html | STAFF+ |
| GET | `/perfil` | perfil.html | USER+ |
| GET | `/nuestra-red` | nuestra-red.html | Público |
| GET | `/contacto` | contacto.html | Público |
| GET | `/terminos` | terminos.html | Público |
| GET | `/privacidad` | privacidad.html | Público |
| GET | `/reset-password` | reset-password.html | Público |
| GET | `/monitoreo` | monitoreo_live.html | LOCAL_ADMIN+ |
