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
2. **Validación de Datos**: Usá la función `validatePlate` de `static/js/modules/utils.js` para cualquier registro de patentes nuevo. No reescribas la lógica de validación.
3. **Modularización de API**: Toda petición a la red debe usar el módulo `api.js`.
4. **Type Module**: Siempre que añadas un script a un template, usá `<script type="module" src="...">`.

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

## ⚠️ MANDATOS ARQUITECTÓNICOS (V8.5.0+)
Para mantener la integridad del sistema a futuro, todo nuevo desarrollo DEBE cumplir estrictamente con lo siguiente:

1. **Arquitectura Limpia (Clean Architecture):**
   - **Rutas (`routes/`):** Deben ser "delgadas". Su única responsabilidad es recibir la solicitud HTTP, validar los parámetros (a través de `schemas/`), llamar al servicio correspondiente y retornar la respuesta.
   - **Servicios (`services/`):** Aquí reside toda la lógica de negocio, cálculos, acceso a repositorios y orquestación de servicios (ej: billing + email).
   - **Modelos (`models/`):** Solo entidades de base de datos y Enums. No deben contener lógica de API.

2. **Cero Hardcoding:**
   - Prohibido dejar valores configurables ("mágicos") dentro del código.
   - Si un valor puede cambiar según el entorno o la sucursal (tiempos, URLs, umbrales de IA, tarifas), debe ir en `core/config.py` y cargarse desde el archivo `.env`.

3. **Modularización:**
   - Antes de crear un archivo nuevo, evaluá si la funcionalidad pertenece a un servicio existente o si justifica uno nuevo.
   - Evitá el acoplamiento circular. Si un servicio necesita una función de utilidad de una ruta, mové esa función a `core/utils.py` o al directorio raíz de `routes/`.

4. **Tipado Seguro:**
   - Usar SIEMPRE los Enums definidos en `models/enums.py` para estados, roles y tipos de vehículos. No usar strings literales.

5. **Testing Obligatorio:**
   - Todo nuevo servicio o funcionalidad crítica debe incluir su prueba unitaria correspondiente en `tests/` utilizando la infraestructura de SQLite en memoria definida.

---
