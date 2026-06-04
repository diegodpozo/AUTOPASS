# Guía de Desarrollo: Arquitectura Modular

Este documento sirve como mapa técnico tras la gran refactorización. Explica la ubicación de los recursos y las reglas de extensión del sistema.

---

## Organización de Capas

### 1. `core/` (Infraestructura)
Cualquier configuración que afecte a todo el sistema debe ir aquí.
- **Seguridad**: Si añadís un nuevo rol, registralo en `core/security.py`.
- **Config**: Si añadís una API Key o variable al `.env`, definila en `core/config.py`.

### 2. `models/` y `schemas/` (Datos)
- **Regla**: Siempre que crees una tabla nueva, hacelo en un archivo dentro de `models/` y exportalo en `models/__init__.py`.
- **Validación**: Toda entrada de datos a la API debe tener un esquema en `schemas/`. Usá `@field_validator` para lógica de validación.

### 3. `services/` (Cerebro)
- **IMPORTANTE**: No pongas lógica de cálculo de precios o validación de stock en los routers. Creá un método estático en un servicio dentro de `services/`.

---

## Mapa de Rutas (Endpoints Modularizados)

| Prefijo | Paquete/Archivo | Responsabilidad |
| :--- | :--- | :--- |
| `/v1/auth` | `routes/auth.py` | Registro, Login, Gestión de Tokens. |
| `/v1/admin` | `routes/admin/` | **Modular:** Users, Reservations, Settings, Branches, Promotions, Ops. |
| `/v1/user` | `routes/user/` | **Modular:** Profile, Vehicles, Balance, Reservations, Fidelization. |
| `/v1/parking`| `routes/parking/`| **Modular:** Access (IA/QR), Status (Aforo), Utils. |
| `/v1/reports`| `routes/reports.py` | Resúmenes financieros y logs de acceso. |
| `/v1/system` | `routes/system.py` | Salud del sistema, Video feeds, Reset. |
| `/` (Vistas) | `routes/views.py` | Renderizado Jinja2 con **Inyección Global de Settings**. |

---

## Desarrollo de Frontend

Para modificar la UI, seguí la nueva estructura de componentes y módulos:
- **Plantillas Email**: `templates/emails/`. Usar Jinja2 para variables dinámicas.
- **Componentes HTML**: `templates/components/` (Navbar, Footers, Modales base).
- **Lógica JS (Módulos)**: `static/js/modules/`. Toda nueva función lógica debe ir aquí y exportarse.
- **Scripts de Página**: `static/js/*.js`. Actúan como puentes, importando módulos y exponiendo funciones al ámbito global si es necesario.

### Reglas de JS:
1. **Usar ES6 Modules**: Usá `import` / `export`. No crees funciones globales directamente en los módulos.
2. **Modularización de API**: Toda petición a la red debe usar el módulo `api.js`.
3. **Type Module**: Siempre que añadas un script a un template, usá `<script type="module" src="...">`.

### Reglas de Estilo:
1. **Dorado AutoPass**: `#C5A059`.
2. **Glassmorphism**: Fondo con desenfoque y bordes semi-transparentes.
3. **Voseo**: "Registrate", "Cargá saldo", "Tus puntos".

---

## Convenciones Multi-Sucursal (Aislamiento)
1. **Nombres Completos**: Al interactuar con la DB, usá siempre el nombre completo de la sucursal (ej: "AUTOPASS Castelar") para asegurar coincidencias exactas.
2. **Geolocalización**: Toda nueva sucursal debe incluir coordenadas (Lat/Lng). Se recomienda usar el botón "BUSCAR" en el modal para autocompletar mediante Nominatim.
3. **Fallback de Configuración**: Al buscar una configuración, si no existe para la sucursal actual, buscá siempre el valor global (`sucursal == None`) antes de fallar.
3. **Seguridad en Rutas**: Usá siempre las dependencias `get_local_manager` o `get_operational_user` para asegurar que el usuario solo acceda a datos de su sucursal autorizada.
4. **Contexto UI**: No hardcodees cargos; usá la lógica de `dashboard.js` que construye el cargo + sucursal dinámicamente desde la sesión.

---

## Estándares del Motor ALPR
1. **Pre-procesamiento**: Toda imagen debe pasar por la cadena de filtros OpenCV antes del OCR.
2. **Consenso**: Nunca valides una patente con un solo frame; requiere votación mayoritaria en ventana.
3. **ROI**: Ajustá la región de interés si cambia la posición física de la cámara.

---

## Pruebas (Tests)
Para correr las pruebas tras un cambio:
```bash
.\venv\Scripts\python.exe test_user_flow.py
.\venv\Scripts\python.exe test_multi_branch_rbac.py
```
*Asegurate de que `init_db.py` se haya ejecutado al menos una vez.*

---

## Reglas de Oro para Desarrolladores
1. **No queries en Rutas:** No hagas consultas complejas de SQLAlchemy en `routes/`. Mové esa lógica a un `Service` o `Repository`.
2. **Validación en Schemas:** Si un campo es obligatorio o tiene un formato especial, validalo en el `Schema` usando `@field_validator`.
3. **Configuración Única:** Si añadís una variable al `.env`, registrala en `core/config.py`.
4. **Voseo Argentino:** Todo texto que vea el usuario final debe usar voseo (Ej: "Cargá tu saldo").
5. **Gestión de Assets:** Al implementar carga de archivos (logos, capturas), usar siempre `static/uploads/` con subcarpetas temáticas y nombres basados en UUID para evitar sobrescrituras.
6. **UI Premium Consistente:** Usar las clases `row-premium` para filas de tabla, `actions-reveal` para botones hover y `switch-premium` para estados binarios.
7. **Mayúsculas en DB:** Las patentes siempre se normalizan a mayúsculas antes de guardarse.
