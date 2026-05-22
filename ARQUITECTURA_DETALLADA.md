# 🏗️ Arquitectura del Sistema: AUTOPASS

Este documento detalla la estructura técnica y el flujo de datos del ecosistema de estacionamiento inteligente tras la refactorización a **Arquitectura Limpia**.

---

## 📁 Estructura de Directorios

El proyecto sigue una organización basada en la separación de responsabilidades para maximizar la mantenibilidad y escalabilidad.

```text
AUTOPASS/
├── core/                # ⚙️ El "corazón" del sistema (Infraestructura)
│   ├── config.py        # Configuración centralizada (.env, constantes)
│   ├── database.py      # Motor de DB, Sesiones y Base ORM
│   ├── security.py      # Autenticación JWT, Hashing y RBAC (Roles)
│   └── mqtt.py          # Cliente de comunicación IoT (Barreras)
├── models/              # 🏛️ Entidades de Base de Datos (SQLAlchemy)
│   ├── user.py          # Usuarios, Vehículos, Puntos
│   ├── parking.py       # Aforo, Logs de Acceso, Settings
│   └── reservation.py   # Reservas, Cupones
├── schemas/             # 📝 Contratos de la API y Validación (Pydantic)
│   ├── user.py          # Validaciones de perfil y cuenta
│   ├── parking.py       # Validaciones ALPR y QR
│   ├── reservation.py   # Validaciones de estadías
│   └── auth.py          # Esquemas de tokens
├── routes/              # 🔌 Capa de Entrega (Endpoints)
│   ├── admin.py         # Gestión administrativa y sede
│   ├── auth.py          # Login y Registro
│   ├── parking.py       # Control de accesos y barreras
│   ├── reports.py       # Analítica y finanzas
│   ├── system.py        # Salud del sistema y video streaming
│   ├── user.py          # Acciones del cliente
│   └── views.py         # Servido de páginas HTML (Jinja2)
├── services/            # 🧠 Lógica de Negocio (Service Pattern)
│   ├── billing_service.py     # Cálculos financieros y deudas (Traza fecha_pago)
│   ├── reservation_service.py # Lógica compleja de reservas
│   └── worker_service.py      # Tareas en segundo plano (Background)
├── repositories/        # 💾 Capa de Acceso a Datos (Repository Pattern)
│   ├── user_repository.py
│   └── reservation_repository.py
├── static/              # 🎨 Recursos estáticos (CSS, JS, Imágenes)
│   ├── js/              # Lógica de Frontend
│   │   ├── modules/     # 📦 Módulos ES6 (Lógica encapsulada)
│   │   │   ├── api.js   # Cliente de red centralizado
│   │   │   ├── utils.js # Helpers y utilidades
│   │   │   └── ui.js    # Componentes de interfaz
│   │   └── *.js         # Scripts de página (Bridges)
├── templates/           # 🖼️ Vistas HTML (Jinja2)
│   ├── components/      # Fragmentos reutilizables (Navbar, Footer, Modales)
│   ├── profile/         # Módulos del Panel de Cliente (Tabs)
│   ├── dashboard/       # Módulos del Panel Administrativo (Tabs)
│   └── *.html           # Páginas completas (index, contacto, etc.)
└── main.py              # 🚀 Punto de entrada (Orquestador)
```

---

## 층 Capas y Responsabilidades

### 1. Capa Core (`core/`)
Centraliza las dependencias críticas que atraviesan todo el proyecto.
*   **Configuración:** No se usan `os.getenv` dispersos; todo se lee desde `settings` en `core/config.py`.
*   **Seguridad:** Implementa **RBAC (Role-Based Access Control)** con 4 niveles: `admin`, `local_admin`, `staff`, `user`.

### 2. Capa de Datos (`models/` y `schemas/`)
*   **Models:** Representan las tablas físicas. La base es el aislamiento por `sucursal` para permitir el modelo multi-sede.
*   **Schemas:** Actúan como "filtros". Validan que los datos que entran y salen de la API cumplan con las reglas de negocio (ej: longitud de DNI, formato de patente).

### 3. Capa de Lógica (`services/`)
Aquí reside la **Inteligencia de Negocio**. Los servicios son agnósticos a la HTTP; se encargan de:
*   Calcular deudas basadas en el tiempo de estadía.
*   Procesar canjes de puntos.
*   Gestionar el ciclo de vida de una reserva (Pendiente -> Activa -> Completada).

### 4. Capa de Rutas (`routes/`)
Es la puerta de entrada. Su única responsabilidad es recibir la petición, llamar al servicio correspondiente y devolver una respuesta.
*   **API:** Retorna JSON para el frontend o servicios ALPR.
*   **Views:** Renderiza plantillas Jinja2 para el navegador.

### 📊 Módulo de Reportes e Interfaz (Dashboard Refined)
- **Motor Financiero Unificado**: El sistema consolida ingresos de dos fuentes: `AccessLog` (cobros en sitio) y `Reservation` (abonos anticipados), proporcionando un flujo de caja real.
- **Lógica Cronológica**: Priorización de `fecha_pago` sobre `fecha_hora`.
- **Arquitectura de Modales**: Uso de visualizadores especializados (`modal-log-detail` para ALPR y `modal-res-detail` para Reservas) para evitar colisiones de contexto y mejorar la profundidad informativa.
- **Gráficos Dinámicos**: Integración con **Chart.js** para visualización de tendencias de ingresos en tiempo real.

---

## 🔄 Flujo de una Petición (Request Flow)

Para una operación estándar como "Crear Reserva":

1.  **Browser/App:** Envía un POST a `/v1/user/reservations`.
2.  **Routes (`user.py`)**: Recibe el JSON, lo valida con `ReservationCreate` (Schema).
3.  **Dependency Injection**: Inyecta la sesión de DB (`get_db`) y el usuario actual (`get_current_user`).
4.  **Services (`reservation_service.py`)**: Ejecuta la lógica: verifica si el vehículo es del usuario, calcula el costo con `billing_service` y guarda en DB.
5.  **Models (`reservation.py`)**: Realiza el commit final en SQLite/PostgreSQL.
6.  **Response**: El router devuelve el objeto creado al cliente.

---

## 🛠️ Tecnologías Clave

*   **FastAPI:** Framework asíncrono de alto rendimiento.
*   **SQLAlchemy:** ORM para abstracción de base de datos.
*   **EasyOCR + OpenCV:** Motor híbrido de visión artificial para patentes y QR.
*   **Paho MQTT:** Protocolo ligero para control de hardware (barreras).
*   **Jinja2:** Motor de plantillas con herencia para el frontend premium.
*   **Chart.js:** Visualización de analítica avanzada.

---

## 📝 Reglas de Oro para Desarrolladores

1.  **No queries en Rutas:** No hagas consultas complejas de SQLAlchemy en `routes/`. Mové esa lógica a un `Service` o `Repository`.
2.  **Validación en Schemas:** Si un campo es obligatorio o tiene un formato especial, validalo en el `Schema` usando `@field_validator`.
3.  **Configuración Única:** Si añadís una variable al `.env`, registrala en `core/config.py`.
4.  **Voseo Argentino:** Todo texto que vea el usuario final debe usar voseo (Ej: "Cargá tu saldo").
5.  **Mayúsculas en DB:** Las patentes siempre se normalizan a mayúsculas antes de guardarse.

---

