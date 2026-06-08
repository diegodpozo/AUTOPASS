# Arquitectura del Sistema: AUTOPASS

Este documento detalla la estructura técnica y el flujo de datos del ecosistema de estacionamiento inteligente tras la refactorización a **Arquitectura Limpia**.

---

## Estructura de Directorios

El proyecto sigue una organización basada en la separación de responsabilidades para maximizar la mantenibilidad y escalabilidad.

```text
AUTOPASS/
├── core/ # El "corazón" del sistema (Infraestructura)
│ ├── config.py # Configuración centralizada (.env, constantes)
│ ├── database.py # Motor de DB, Sesiones y Base ORM
│ ├── security.py # Autenticación JWT, Hashing y RBAC (Roles)
│ └── mqtt.py # Cliente de comunicación IoT (Barreras)
├── models/ # Entidades de Base de Datos (SQLAlchemy)
│ ├── user.py # Usuarios, Vehículos, Puntos
│ ├── parking.py # Aforo, Logs de Acceso, Settings
│ └── reservation.py # Reservas, Cupones
├── schemas/ # Contratos de la API y Validación (Pydantic)
│ ├── user.py # Validaciones de perfil y cuenta
│ ├── parking.py # Validaciones ALPR y QR
│ ├── reservation.py # Validaciones de estadías
│ └── auth.py # Esquemas de tokens
├── routes/ # Capa de Entrega (Endpoints Modularizados)
│ ├── admin/ # Gestión administrativa (Sub-módulos: users, reservations, settings, etc.)
│ ├── user/ # Acciones del cliente (Sub-módulos: profile, vehicles, balance, etc.)
│ ├── parking/ # Control de accesos e IA (Sub-módulos: access, status, utils)
│ ├── auth.py # Login y Registro
│ ├── reports.py # Analítica y finanzas
│ ├── system.py # Salud del sistema y video streaming
│ └── views.py # Servido de páginas HTML con inyección global de settings
├── services/ # Lógica de Negocio (Service Pattern)
│ ├── billing_service.py # Cálculos financieros y deudas
│ ├── reservation_service.py # Lógica compleja de reservas
│ ├── email_service.py # Comunicaciones SMTP vía plantillas Jinja2
│ └── worker_service.py # Tareas en segundo plano (Background)
├── templates/ # Vistas HTML (Jinja2)
│ ├── emails/ # Plantillas de correo electrónico desacopladas (NUEVO)
│ ├── components/ # Fragmentos reutilizables (Navbar, Footer, Modales)

│ └── reservation_repository.py
├── static/ # Recursos estáticos (CSS, JS, Imágenes)
│ ├── js/ # Lógica de Frontend
│ │ ├── modules/ # Módulos ES6 (Lógica encapsulada)
│ │ │ ├── api.js # Cliente de red centralizado
│ │ │ ├── utils.js # Helpers y utilidades
│ │ │ └── ui.js # Componentes de interfaz
│ │ └── *.js # Scripts de página (Bridges)
├── templates/ # Vistas HTML (Jinja2)
│ ├── components/ # Fragmentos reutilizables (Navbar, Footer, Modales)
│ ├── profile/ # Módulos del Panel de Cliente (Tabs)
│ ├── dashboard/ # Módulos del Panel Administrativo (Tabs)
│ └── *.html # Páginas completas (index, contacto, etc.)
└── main.py # Punto de entrada (Orquestador)
```

---

## Capas y Responsabilidades

### 1. Capa Core (`core/`)
Centraliza las dependencias críticas que atraviesan todo el proyecto.
* **Configuración:** No se usan `os.getenv` dispersos; todo se lee desde `settings` en `core/config.py`.
* **Seguridad:** Implementa **RBAC (Role-Based Access Control)** con 4 niveles: `admin`, `local_admin`, `staff`, `user`.

### 2. Capa de Datos (`models/` y `schemas/`)
* **Models:** Representan las tablas físicas. La base es el aislamiento por `sucursal` para permitir el modelo multi-sucursal. Se incluye la entidad `ParkingBranch` (con soporte para `latitude` y `longitude`) para la gestión de la red.
* **Schemas:** Actúan como "filtros". Validan que los datos que entran y salen de la API cumplan con las reglas de negocio (ej: coordenadas geográficas, formato de patente, carga de logos).

### 🖼️ Gestión de Assets y Archivos
* **Estructura Estática:** Organización centralizada en `static/images/inicio/` para recursos visuales del carrusel y UI.
* **Uploads Locales:** El sistema almacena logos de sucursales en `static/uploads/branches/` con nombres normalizados vía UUID.
* **Integración ALPR:** Almacenamiento cronológico de capturas reales en `captured_images/`.
* **Fallback Inteligente:** El backend implementa una lógica de fallback que sirve imágenes aleatorias desde la carpeta estática si un registro de acceso no posee una captura real, optimizando el espacio en disco al no duplicar archivos para demostraciones.

### 3. Capa de Lógica (`services/`)
Aquí reside la **Inteligencia de Negocio**. Los servicios son agnósticos a la HTTP; se encargan de:
* Calcular deudas basadas en el tiempo de estadía.
* Procesar canjes de puntos.
* Gestionar el ciclo de vida de una reserva (Pendiente -> Activa -> Completada).

### 4. Capa de Rutas (`routes/`)
Es la puerta de entrada. Su única responsabilidad es recibir la petición, llamar al servicio correspondiente y devolver una respuesta.
* **API:** Retorna JSON para el frontend o servicios ALPR.
* **Views:** Renderiza plantillas Jinja2 para el navegador.

### Módulo de Reportes e Interfaz (Financial Dashboard 2.0)
- **Motor Financiero Unificado (SQL Pro)**: El sistema utiliza consultas `UNION ALL` con paginación a nivel de base de datos (`OFFSET/LIMIT`) para consolidar ingresos de `AccessLog`, `Reservation` y transacciones de `Reembolso`.
- **Lógica Contable Neta**: Cálculo automático de **Recaudación Neta** (`Bruto - Reembolsos`) utilizando la columna `monto_reembolsado` para mantener precisión absoluta en devoluciones parciales.
- **Analítica de Eficiencia**: Implementación de KPIs avanzados como **Tasa de Cancelación** e **Incumplimiento de Reservas** (No-Shows).
- **Trazabilidad de Reembolsos**: Visualización detallada en el historial con montos negativos e identificadores específicos (`REF#`).
- **Ingresos Proyectados**: Algoritmo que escanea vehículos actualmente en el predio para calcular deudas en tiempo real.

### 🧠 Inteligencia de Negocio y Reembolsos
El sistema implementa una política de cancelación flexible y automatizada:
1. **Validación de Presencia Física**: Bloqueo absoluto de cancelación si el vehículo está dentro del predio (`ENTRADA` activa).
2. **Reembolsos Proporcionales**: 
   - **Pre-inicio**: 100% de devolución.
   - **En curso (Activa)**: Devolución proporcional al tiempo/días restantes para todos los tipos de abono.
   - **Reserva por Hora Usada**: 0% de devolución si se detecta que el vehículo ya ingresó al menos una vez.
3. **Ajuste de Fidelización**: Deducción automática y prorrateada de puntos AutoPass acumulados al ejecutar el reembolso.
4. **Endpoint de Simulación**: Permite previsualizar el monto exacto del reembolso en la UI sin afectar la base de datos.

---

## Flujo de una Petición (Request Flow)

Para una operación estándar como "Crear Reserva":

1. **Browser/App:** Envía un POST a `/v1/user/reservations`.
2. **Routes (`user.py`)**: Recibe el JSON, lo valida con `ReservationCreate` (Schema).
3. **Dependency Injection**: Inyecta la sesión de DB (`get_db`) y el usuario actual (`get_current_user`).
4. **Services (`reservation_service.py`)**: Ejecuta la lógica: verifica si el vehículo es del usuario, calcula el costo con `billing_service` y guarda en DB.
5. **Models (`reservation.py`)**: Realiza el commit final en SQLite/PostgreSQL.
6. **Response**: El router devuelve el objeto creado al cliente.

## Seguridad y Control de Acceso (RBAC)

El sistema utiliza un motor de seguridad basado en JWT y roles jerárquicos:

1.  **Admin Global**: Acceso total a todas las sucursales, gestión de roles de administradores, y configuraciones base del sistema. Se enfoca en la gestión de alto nivel.
2.  **Admin de Sucursal (local_admin)**: Gestión total de una sucursal específica (Tarifas, Personal, Reportes).
3.  **Staff (Operativo)**: Acceso operativo (Monitoreo, Barreras, Ingresos).
4.  **User (Cliente)**: Gestiona sus vehículos, reservas y puntos.

### Hardening de Sesión e Interfaz
Para garantizar la integridad visual y funcional, el sistema implementa:
*   **Anti-Flicker Protection**: Inyección de clase de rol inmediata vía script inline al inicio del `<body>` en `dashboard.html`.
*   **Sincronización de Contexto**: El backend inyecta la `sucursal` en el payload de login, que se persiste en `localStorage`.
*   **Inicialización Resiliente**: El script de Dashboard prioriza la carga de identidad (cargo y sucursal) mediante un flujo defensivo.
*   **Etiquetado Dinámico**: La cabecera se construye en tiempo real (ej: `Administrador` + `Morón`).

---

## Flujos de Datos Clave

### 1. Motor de Reconocimiento ALPR (v8.1.0)
El sistema de visión artificial ha sido evolucionado a una arquitectura de grado industrial:
1.  **Captura Asíncrona**: Utiliza colas de prioridad para no bloquear el streaming de video.
2.  **Pre-procesamiento OpenCV**: Aplica una cadena de filtros (CLAHE, Gaussian Blur, Adaptive Threshold).
3.  **Algoritmo de Consenso**: Implementa una ventana de votación temporal para validación de patentes.
4.  **ROI (Region of Interest)**: Recorta dinámicamente el área de la patente.

### 2. Cálculo de Tarifas Dinámicas
Al realizar una reserva, el cliente selecciona un "Punto AutoPass". El sistema:
1. Consulta las tarifas de esa sucursal específica.
2. Si no existen, aplica los precios base globales.
3. Actualiza el presupuesto en tiempo real.

---

## Tecnologías Clave

* **FastAPI:** Framework asíncrono de alto rendimiento.
* **SQLAlchemy:** ORM para abstracción de base de datos.
* **EasyOCR + OpenCV:** Motor híbrido de visión artificial para patentes y QR.
* **Paho MQTT:** Protocolo ligero para control de hardware (barreras).
* **Jinja2:** Motor de plantillas premium.
* **Chart.js:** Visualización de analítica avanzada.

---

## Reglas de Oro para Desarrolladores

1. **No queries en Rutas:** No hagas consultas complejas en `routes/`. Mové esa lógica a un `Service` o `Repository`.
2. **Validación en Schemas:** Si un campo es obligatorio, validalo en el `Schema` usando `@field_validator`.
3. **Configuración Única:** Si añadís una variable al `.env`, registrala en `core/config.py`.
4. **Voseo Argentino:** Todo texto que vea el usuario final debe usar voseo (Ej: "Cargá tu saldo").
5. **Mayúsculas en DB:** Las patentes siempre se normalizan a mayúsculas.
