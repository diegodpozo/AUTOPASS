# 🗺️ Guía de Desarrollo: Arquitectura y Rutas

Este documento sirve como mapa técnico para desarrolladores. Explica dónde está cada recurso, cómo se relacionan los archivos y las reglas para editarlos.

---

## 🛤️ Mapa de Rutas (Endpoints)

### 📄 Páginas (Frontend - Jinja2)
Definidas en `main.py`:
- `/`: Landing Page (Inicio).
- `/perfil`: Portal del cliente (Gestión de vehículos y reservas).
- `/dashboard`: Panel administrativo (Control de cámaras y reportes).
- `/nuestra-red`: Mapa de sucursales.
- `/contacto`: Formulario corporativo.

### 🔌 API Endpoints (v1)
Los prefijos se definen en los routers dentro de `routes/`:
- `/v1/auth`: Login, Registro y validación de tokens.
- `/v1/user`: Datos del perfil, gestión de flota, reservas y consulta de tarifas públicas (`/rates`).
- `/v1/admin`: Gestión global, auditoría de usuarios (bloqueo/ajustes) y métricas.
- `/v1/parking`: Control de acceso (ALPR), apertura de barreras y sensores.
- `/v1/reports`: Generación de datos para gráficos y analítica financiera.
- `/v1/system`: Flujos de video y utilidades técnicas.

---

## 📂 Ubicación de Archivos Útiles

### 🖥️ Frontend (Interfaz)
- **Estructura HTML**: `templates/` (Usa herencia de `base.html`).
- **Dashboard Modular**: `templates/dashboard/tabs/` - Fragmentos por sección (`live.html`, `finance.html`, etc.).
- **Lógica de Negocio (JS)**: `static/js/`
    - `api_client.js`: **CRÍTICO** - Cliente centralizado para peticiones al backend.
    - `dashboard.js`: Lógica exclusiva del panel de administración (Charts, Monitoreo).
    - `perfil.js`: Hub de gestión del portal de usuario.
    - `reservas.js` y `vehicles.js`: Módulos de gestión de flota y estadías.
- **Estilos (CSS Modular)**: `static/css/`
    - `dashboard.css`: Estilos del "Command Center" (Grid de cámaras, KPIs, Charts).
    - `perfil-base.css`: Elementos comunes y layout de la zona privada.
    - `style.css`: Variables globales, fuentes y reset.

### ⚙️ Backend (Servidor)
- **Entrada**: `main.py` (Configuración de FastAPI y MQTT).
- **Controladores**: `routes/` (Segmentación por dominio).
- **Servicios**: `services/` (Lógica financiera en `billing_service.py`).
- **Validación/DLO**: `schemas.py` (Modelos Pydantic para la API).

---

## 🔗 Relaciones Críticas

```mermaid
graph TD
    Templates[.html] -->|Include Tabs| Fragments[.html]
    Fragments -->|Script Import| JS[.js]
    JS -->|Centralized Fetch| apiClient[api_client.js]
    apiClient -->|JWT Token Injection| Routers[.py]
    Routers -->|Validate| Schemas[.py]
    Routers -->|Business Logic| BillingService[.py]
```

---

## 🛠️ Reglas de Oro (Developer Guide)

### 🎨 Estilo y Visuales:
- **Montserrat**: Fuente principal obligatoria para toda la UI.
- **Glassmorphism**: Usar variables de `--border-light` y fondos `rgba(10, 10, 10, 0.8)`.
- **Dorado AutoPass**: `#C5A059` para iconos, botones primarios y resaltados.
- **Voseo**: Todo texto debe usar voseo argentino (Ej: "Cargá", "Tenés", "Registrate").
- **Secciones Colapsables**: Utilizar el patrón `toggleName()` con `max-height` animado para optimizar el espacio vertical en el Dashboard.

### 🧠 Lógica y Datos:
1.  **Centralización**: NUNCA hagas un `fetch` manual. Usá siempre `apiClient` para asegurar la inyección de tokens y manejo de errores.
2.  **Modularidad Dashboard**: Si añadís una sección al admin, creá un archivo en `templates/dashboard/tabs/` y vinculalo en `dashboard.html`.
3.  **Gráficos**: Siempre usá Chart.js siguiendo el estilo oscuro de `dashboard.js`. Destruí instancias previas antes de recrear gráficos.
4.  **Cálculos Financieros**: La única fuente de verdad es `services/billing_service.py`. No calcules deudas en el frontend.
5.  **Ordenamiento de Usuarios**: Toda lista de usuarios debe seguir la jerarquía: Admin > Staff (Empleado) > Cliente.
6.  **Nomenclatura Operativa**: Usar términos como "Playa" o "Vehículos en Playa" para referirse al predio activo. Las acciones directas de hardware deben llamarse "Apertura Manual".

### 👁️ Visión Artificial (ALPR & QR)
- **Motor Híbrido**: El servicio `alpr_service.py` utiliza un motor dual. Primero intenta detectar códigos QR (Pases Digitales) y, si no hay presencia de QR, activa el motor EasyOCR para patentes.
- **Optimización de Recursos**: Mantener el streaming a un máximo de 10 FPS para evitar saturación del backend. El motor OCR debe tener un cooldown de al menos 500ms entre frames procesados.
- **Validación Robusta**: El backend siempre prioriza los datos de la reserva en la DB sobre el texto extraído del QR para evitar errores de registro.

### 💰 Lógica de Pagos y Reservas
- **Estado Pendiente**: Toda reserva nueva o modificada debe iniciar en estado `Pendiente`. NO realizar cobros automáticos con el saldo del usuario para darle control total.
- **Cancelaciones**: Solo permitir la cancelación de reservas con estado `Pendiente` desde el cliente. Las reservas `Activa` (vehículo dentro) solo pueden ser gestionadas por administradores.
- **Limpieza de Reservas**: Las reservas impagas solo se cancelan automáticamente una vez que su hora de inicio ha pasado, permitiendo reservas de "último minuto" sin riesgo de borrado preventivo.

---
*Este documento es dinámico. Mantenelo actualizado tras cada refactorización importante.*
