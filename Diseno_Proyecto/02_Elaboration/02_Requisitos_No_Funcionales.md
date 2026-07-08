# Requisitos No Funcionales — AUTOPASS

## Rendimiento

| ID | Nombre | Descripción | Especificación |
|----|--------|-------------|----------------|
| RNF-01 | Tiempo de respuesta API | Las respuestas de la API deben ser rápidas para mantener la UX fluida | < 500ms para 95% de las solicitudes |
| RNF-02 | Throughput de ALPR | El sistema debe procesar solicitudes ALPR sin acumulación | Mínimo 2 frames/segundo por cámara |
| RNF-03 | Latencia de WebSocket | Las actualizaciones de ocupación deben llegar al dashboard en tiempo real | < 1 segundo desde el evento |
| RNF-04 | Concurrencia | El sistema debe soportar múltiples usuarios y cámaras simultáneamente | Mínimo 50 usuarios concurrentes, 8 cámaras |
| RNF-05 | Pool de conexiones DB | Debe haber un pool suficiente para evitar cuellos de botella | pool_size=10, overflow=20, timeout=60s |

## Seguridad

| ID | Nombre | Descripción | Especificación |
|----|--------|-------------|----------------|
| RNF-06 | Hashing de contraseñas | Las contraseñas deben almacenarse con hash seguro | bcrypt con salt |
| RNF-07 | Autenticación JWT | Todas las rutas protegidas deben validar token JWT | HS256, expiración configurable (default 1440 min) |
| RNF-08 | RBAC | El acceso a funciones debe estar restringido por rol | Roles: ADMIN, LOCAL_ADMIN, STAFF, USER |
| RNF-09 | Bloqueo de cuenta | Usuarios bloqueados no deben poder autenticarse | Verificación en authenticate_user |
| RNF-10 | Protección de secrets | Las claves secretas deben cargarse desde .env, no hardcodearse | SECRET_KEY, SMTP_* en variables de entorno |

## Disponibilidad y Confiabilidad

| ID | Nombre | Descripción | Especificación |
|----|--------|-------------|----------------|
| RNF-11 | Disponibilidad del servidor | El backend debe mantener el servicio sin interrupciones planificadas | 99.9% uptime |
| RNF-12 | Worker de limpieza | El worker de mantenimiento debe ejecutarse periódicamente | Cada 300 segundos (configurable) |
| RNF-13 | Heartbeat de ALPR | Las cámaras deben reportar salud periódicamente | Cada N segundos, timeout de 90s |
| RNF-14 | Graceful shutdown | El sistema debe limpiar recursos al apagarse | Detener cámaras, cerrar conexiones MQTT |
| RNF-15 | Persistencia de DB | Los datos deben persistir en disco (SQLite/PostgreSQL) | Sin pérdida de datos ante reinicio |

## Mantenibilidad

| ID | Nombre | Descripción | Especificación |
|----|--------|-------------|----------------|
| RNF-16 | Arquitectura limpia | Separación estricta en capas (routes/services/models/schemas) | Las rutas no deben contener lógica de negocio |
| RNF-17 | Enums tipados | Prohibido usar strings literales para estados o roles | Usar siempre models/enums.py |
| RNF-18 | Configuración centralizada | Parámetros configurables en core/config.py desde .env | Sin hardcoding |
| RNF-19 | Modularidad | El código debe estar organizado en módulos con responsabilidad única | Cada módulo en su archivo/paquete |
| RNF-20 | Pruebas unitarias | Los servicios deben tener tests | pytest para services críticos |

## Usabilidad

| ID | Nombre | Descripción | Especificación |
|----|--------|-------------|----------------|
| RNF-21 | Diseño responsive | El frontend debe adaptarse a desktop y mobile | CSS Grid, Flexbox, media queries |
| RNF-22 | Estilo consistente | Paleta de colores, tipografía y componentes unificados | Dorado #C5A059, Glassmorphism |
| RNF-23 | Voseo argentino | Los textos deben usar "voseo" (registrate, cargá, etc.) | Consistente en toda la UI |
| RNF-24 | Feedback visual | Cada acción del usuario debe tener respuesta visual inmediata | Spinners, toasts, animaciones |
| RNF-25 | Tour de usuario | Nuevos usuarios deben tener guía interactiva | tour.js + onboarding_helpers.js |

## Compatibilidad

| ID | Nombre | Descripción | Especificación |
|----|--------|-------------|----------------|
| RNF-26 | Navegadores | El frontend debe funcionar en navegadores modernos | Chrome, Firefox, Edge, Safari (últimas 2 versiones) |
| RNF-27 | Python | El backend requiere Python moderno | Python 3.9+ |
| RNF-28 | Base de datos | Compatible con SQLite y PostgreSQL | SQLAlchemy ORM abstrae la DB |
| RNF-29 | Cámaras IP | El ALPR debe funcionar con cámaras IP estándar | RTSP, HTTP, MJPEG |
