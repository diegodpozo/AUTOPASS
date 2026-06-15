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
4. **Modo Edición (UI Pattern)**:
   - Los campos de configuración (ej: tarifas) deben estar deshabilitados por defecto (`disabled`).
   - Usar un botón único "EDITAR" que habilita los campos y cambia la etiqueta a "APLICAR".
   - Al aplicar, disparar `showConfirm` con resumen. El sistema guarda y vuelve a bloquear los campos automáticamente.
5. **Reportes Financieros**: Al agregar nuevos reportes o filtros, asegurar la integración de `vehicle_type` y `payment_method` ('all', 'DIGITAL', 'CAJA').

---

## Convenciones Multi-Sucursal (Aislamiento)
1. **Nombres Completos**: Al interactuar con la DB, usá siempre el nombre completo de la sucursal.
2. **Seguridad en Rutas**: Usá siempre las dependencias `get_local_manager` o `get_operational_user`.

---

## Pruebas (Tests)
Para correr las pruebas tras un cambio:
```bash
.\venv\Scripts\python.exe test_user_flow.py
.\venv\Scripts\python.exe test_multi_branch_rbac.py
```

---

## ⚠️ MANDATOS ARQUITECTÓNICOS (V8.7.0+)
Para mantener la integridad del sistema a futuro, todo nuevo desarrollo DEBE cumplir estrictamente con lo siguiente:

1. **Arquitectura Limpia (Clean Architecture):**
   - **Rutas (`routes/`):** "Delgadas". Validación vía `schemas/`, llamada al servicio.
   - **Servicios (`services/`):** Lógica de negocio pesada, orquestación.
   - **Modelos (`models/`):** Entidades de BD y Enums.

2. **Cero Hardcoding:**
   - Valores configurables deben ir en `core/config.py` cargados desde `.env`.

3. **Modularización:**
   - Evitá el acoplamiento circular.

4. **Tipado Seguro:**
   - Usar SIEMPRE Enums (`models/enums.py`). Prohibido usar strings literales para estados o tipos.

5. **Testing Obligatorio:**
   - Todo nuevo servicio debe incluir pruebas en `tests/`.
