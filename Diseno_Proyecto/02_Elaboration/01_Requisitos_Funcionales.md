# Requisitos Funcionales — AUTOPASS

## Módulo de Autenticación

| ID | Nombre | Descripción | Prioridad |
|----|--------|-------------|-----------|
| RF-01 | Registro de usuario | El sistema debe permitir auto-registro con nombre, apellido, DNI, email, teléfono y contraseña | Alta |
| RF-02 | Inicio de sesión | El sistema debe autenticar usuarios por email/contraseña y emitir JWT | Alta |
| RF-03 | Recuperación de contraseña | El sistema debe enviar email con token de recuperación válido por 30 min | Alta |
| RF-04 | Cierre de sesión | El sistema debe invalidar el token JWT del lado del cliente | Media |
| RF-05 | Refresh de token | El sistema debe permitir renovar el token JWT antes de que expire | Media |
| RF-06 | Bloqueo de usuario | El ADMIN debe poder bloquear/desbloquear usuarios; el bloqueo impide el login | Alta |

## Módulo de Acceso (ALPR)

| ID | Nombre | Descripción | Prioridad |
|----|--------|-------------|-----------|
| RF-07 | Validación de patente (entrada) | El sistema debe recibir una patente del ALPR, verificar si ya está dentro, buscar reserva vigente, y registrar entrada si hay capacidad | Alta |
| RF-08 | Validación de QR (entrada) | El sistema debe decodificar un QR y verificar si corresponde a una reserva o pase digital válido | Alta |
| RF-09 | Pago en salida | El sistema debe calcular el costo de estadía y permitir pago desde el saldo del usuario o en caja | Alta |
| RF-10 | Validación de salida | El sistema debe verificar que el vehículo haya pagado o tenga reserva vigente antes de abrir barrera | Alta |
| RF-11 | Cortesía 10 min | El sistema debe permitir salida sin cargo si la estadía ≤ 10 minutos | Alta |
| RF-12 | Cancelación de estadía | El sistema debe cancelar una estadía activa sin costo (cortesía) | Media |

## Módulo de Reservas

| ID | Nombre | Descripción | Prioridad |
|----|--------|-------------|-----------|
| RF-13 | Crear reserva | El usuario debe poder reservar por hora, día, semana, quincena o mes | Alta |
| RF-14 | Verificar disponibilidad | El sistema debe chequear capacidad antes de confirmar reserva | Alta |
| RF-15 | Pagar reserva | El usuario debe pagar la reserva desde su saldo | Alta |
| RF-16 | Cancelar reserva | El usuario debe poder cancelar y recibir reembolso proporcional | Alta |
| RF-17 | Simular cancelación | El sistema debe mostrar el monto de reembolso estimado antes de cancelar | Media |
| RF-18 | Modificar reserva | El usuario debe poder modificar fechas/patente de una reserva pendiente | Media |
| RF-19 | Restricción de anticipación | Las reservas por hora requieren mínimo 1 hora de anticipación (configurable) | Alta |
| RF-20 | Liberación automática | El worker debe liberar plazas de reservas vencidas cada 5 min | Alta |

## Módulo de Aforo

| ID | Nombre | Descripción | Prioridad |
|----|--------|-------------|-----------|
| RF-21 | Control de capacidad | El sistema debe controlar que no se exceda la capacidad por piso y tipo de vehículo | Alta |
| RF-22 | Ocupación en tiempo real | El dashboard debe mostrar la ocupación actualizada vía WebSocket | Alta |
| RF-23 | Aforo multi-piso | Cada piso debe tener capacidad independiente para Autos, Motos y Camionetas | Alta |
| RF-24 | Colores dinámicos | Las barras de progreso deben cambiar de color según el nivel de ocupación | Media |

## Módulo de Facturación

| ID | Nombre | Descripción | Prioridad |
|----|--------|-------------|-----------|
| RF-25 | Tarifas configurables | El LOCAL_ADMIN debe poder configurar tarifas por hora/día/semana/mes por tipo de vehículo | Alta |
| RF-26 | Cálculo de estadía | El sistema debe calcular costo basado en tiempo real estacionado | Alta |
| RF-27 | Reportes financieros | El ADMIN debe ver ingresos filtrados por sucursal, fecha, tipo y método de pago | Alta |
| RF-28 | Exportación CSV | El sistema debe permitir descargar reportes en CSV | Media |

## Módulo de Perfil de Usuario

| ID | Nombre | Descripción | Prioridad |
|----|--------|-------------|-----------|
| RF-29 | Gestión de vehículos | El usuario debe poder registrar/editar/eliminar vehículos con patente y tipo | Alta |
| RF-30 | Historial de pagos | El usuario debe ver su historial de pagos y estadías activas | Media |
| RF-31 | Recarga de saldo | El usuario debe poder recargar saldo (simulación) | Media |
| RF-32 | Puntos de fidelización | El usuario debe ver su saldo de puntos y progreso hacia metas | Media |
| RF-33 | Notificaciones in-app | El usuario debe recibir notificaciones sobre reservas y promociones | Baja |

## Módulo de Administración

| ID | Nombre | Descripción | Prioridad |
|----|--------|-------------|-----------|
| RF-34 | CRUD de usuarios | El ADMIN debe gestionar usuarios (crear, editar, cambiar rol, eliminar) | Alta |
| RF-35 | CRUD de sucursales | El ADMIN debe gestionar sucursales con logo, coordenadas y toggle activo | Alta |
| RF-36 | Gestión de pisos | El LOCAL_ADMIN debe agregar/editar/eliminar pisos con capacidad independiente | Alta |
| RF-37 | Configuración de cámaras | El ADMIN debe configurar IPs de cámaras y iniciar/detener servicios ALPR | Alta |
| RF-38 | Operaciones manuales | El STAFF debe registrar entrada/salida manual, abrir barrera y cancelar estadía | Alta |
| RF-39 | Gestión de promociones | El ADMIN debe crear/editar/activar promociones del programa de fidelización | Media |

## Módulo de Monitoreo

| ID | Nombre | Descripción | Prioridad |
|----|--------|-------------|-----------|
| RF-40 | Dashboard de ocupación | El dashboard debe mostrar ocupación actual con barras de progreso | Alta |
| RF-41 | Video en vivo | El sistema debe transmitir video de cámaras por WebSocket | Alta |
| RF-42 | Grilla DVR dinámica | La vista de monitoreo debe ajustar grilla según cantidad de cámaras configuradas | Alta |
| RF-43 | HUD de cámara | Cada feed debe mostrar identificador de función (entrada/salida/vigilancia) y duración | Media |
| RF-44 | Heartbeat del sistema | El sistema debe monitorear salud de cámaras vía heartbeats | Alta |
