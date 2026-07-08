# Alcance y Glosario del Sistema

## Alcance Funcional (Incluido en v9.5.0)

### Módulo de Autenticación y Seguridad
- [x] Registro de usuarios con validación de email
- [x] Login con JWT + bcrypt
- [x] Recuperación de contraseña por email
- [x] RBAC con 4 roles: ADMIN, LOCAL_ADMIN, STAFF, USER
- [x] Bloqueo administrativo de usuarios
- [x] Refresh de token

### Módulo de Acceso (ALPR + QR)
- [x] Reconocimiento automático de patentes (EasyOCR + OpenCV)
- [x] Detección de códigos QR en tiempo real
- [x] Validación de entrada con reserva o "al paso"
- [x] Validación de salida con verificación de pago
- [x] Cortesía de 10 minutos sin cargo
- [x] Cancelación de estadía
- [x] Pago en salida (pay_stay)
- [x] Operaciones manuales (entry/exit/barrier)

### Módulo de Reservas
- [x] Reservas por hora, día, semana, quincena, mes
- [x] Pago de reservas con confirmación
- [x] Cancelación con reembolso proporcional
- [x] Simulación de cancelación
- [x] Restricción de anticipación (solo por hora)
- [x] Liberación automática al vencer (worker)

### Módulo de Aforo
- [x] Control de capacidad por sucursal y piso
- [x] Ocupación solo física (reservas no horarias ya no pre-ocupan)
- [x] WebSockets en tiempo real para dashboard
- [x] Soporte trimodal (Auto/Moto/Camioneta)
- [x] Barras de progreso con colores dinámicos

### Módulo de Facturación
- [x] Tarifas configurables por sucursal
- [x] Precios diferenciados por tipo de vehículo
- [x] Reportes financieros con filtros (fecha, tipo, método de pago)
- [x] Exportación CSV
- [x] Puntos de fidelización

### Módulo de Usuario/Perfil
- [x] Gestión de perfil (datos personales)
- [x] Gestión de vehículos (CRUD + favorito)
- [x] Historial de pagos y estadías activas
- [x] Recarga de saldo
- [x] Visualización de tarifas
- [x] Sistema de notificaciones in-app
- [x] FAB "Nueva Reserva" con animación expansiva

### Módulo de Administración
- [x] CRUD de usuarios con cambio de rol/balance/password
- [x] CRUD de sucursales con logo, toggle activo, coordenadas
- [x] Gestión de pisos por sucursal
- [x] CRUD de promociones y catálogo de beneficios
- [x] Configuración de tarifas y capacidades
- [x] Gestión de cámaras (IP, start/stop)

### Módulo de Monitoreo
- [x] Dashboard con ocupación en tiempo real
- [x] Video streaming por WebSocket
- [x] Grilla DVR dinámica auto-ajustable
- [x] HUD con identificadores de función de cámara
- [x] Panel flotante de controles
- [x] Heartbeat de salud del sistema
- [x] Mapa interactivo Leaflet.js

### Infraestructura
- [x] Comunicación MQTT con hardware ESP32
- [x] Servicio worker de limpieza de reservas
- [x] Virtual Time para testing/simulación
- [x] EmailService con templates Jinja2 + QR embebido
- [x] Sistema de notificaciones asíncronas

## Glosario de Términos

| Término | Definición |
|---------|------------|
| **ALPR** | Automatic License Plate Recognition - Reconocimiento automático de patentes |
| **OCR** | Optical Character Recognition - EasyOCR para lectura de texto en imágenes |
| **ROI** | Region of Interest - Región de la imagen donde se busca la patente |
| **MQTT** | Protocolo de mensajería IoT para comunicación con barreras físicas |
| **RBAC** | Role-Based Access Control - Control de acceso basado en roles |
| **JWT** | JSON Web Token - Token de autenticación |
| **Aforo** | Capacidad máxima de vehículos que puede albergar el estacionamiento |
| **MERCOSUR** | Formato de patente con banda azul (ABC 1D23) usado en Argentina, Brasil, Uruguay, Paraguay |
| **FAB** | Floating Action Button - Botón de acción flotante en la UI |
| **HUD** | Heads-Up Display - Superposición de información técnica en video |
| **DVR CCTV** | Digital Video Recorder para circuito cerrado de televisión |
| **Glassmorphism** | Estilo visual con fondo desenfocado y bordes semi-transparentes |
| **Clean Architecture** | Arquitectura limpia con separación de capas (routes/services/models/schemas) |
| **Pase Digital** | QR generado para acceso sin patente |
| **Trimodal** | Soporte para tres tipos de vehículo: Auto, Moto, Camioneta |
| **Virtual Time** | Sistema que permite adelantar el reloj del servidor para pruebas |
| **Heartbeat** | Pulso periódico que indica que un servicio/cámara está activo |

## Exclusiones (Fuera de Alcance v9.5.0)
- Aplicación móvil nativa (iOS/Android) — solo web responsive
- Integración con sistemas de pago externos reales (Mercado Pago, etc.) — simulación
- Reconocimiento facial de conductores
- Machine Learning para predicción de ocupación
- Módulo de facturación electrónica (AFIP/ARBA)
- App de cobro para personal (POS móvil)
- Integración con sistemas de gestión empresarial (ERP)
