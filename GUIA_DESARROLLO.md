# 🗺️ Guía de Desarrollo: Arquitectura Modular

Este documento sirve como mapa técnico tras la gran refactorización. Explica la ubicación de los recursos y las reglas de extensión del sistema.

---

## 🏗️ Organización de Capas

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

## 🛤️ Mapa de Rutas (Endpoints)

| Prefijo | Archivo | Responsabilidad |
| :--- | :--- | :--- |
| `/v1/auth` | `routes/auth.py` | Registro, Login, Gestión de Tokens. |
| `/v1/admin` | `routes/admin.py` | Gestión RBAC, Usuarios de sede, Reservas manuales. |
| `/v1/user` | `routes/user.py` | Perfil, Vehículos, Carga de saldo, Reservas de cliente. |
| `/v1/reports`| `routes/reports.py` | Resúmenes financieros y logs de acceso. |
| `/v1/system` | `routes/system.py` | Salud del sistema, Video feeds, Reset. |
| `/` (Vistas) | `routes/views.py` | Renderizado de plantillas Jinja2 (HTML). |

---

## 🎨 Desarrollo de Frontend

Para modificar la UI, seguí la nueva estructura de componentes y módulos:
- **Componentes HTML**: `templates/components/` (Navbar, Footers, Modales base).
- **Lógica JS (Módulos)**: `static/js/modules/`. Toda nueva función lógica debe ir aquí y exportarse.
- **Scripts de Página**: `static/js/*.js`. Actúan como puentes, importando módulos y exponiendo funciones al ámbito global si es necesario.

### Reglas de JS:
1.  **Usar ES6 Modules**: Usá `import` / `export`. No crees funciones globales directamente en los módulos.
2.  **Modularización de API**: Toda petición a la red debe usar el módulo `api.js`.
3.  **Type Module**: Siempre que añadas un script a un template, usá `<script type="module" src="...">`.

### Reglas de Estilo:
1.  **Dorado AutoPass**: `#C5A059`.
2.  **Glassmorphism**: Fondo con desenfoque y bordes semi-transparentes.
3.  **Voseo**: "Registrate", "Cargá saldo", "Tus puntos".

---

## 🧪 Pruebas (Tests)
Para correr las pruebas tras un cambio:
```bash
.\venv\Scripts\python.exe test_user_flow.py
.\venv\Scripts\python.exe test_multi_branch_rbac.py
```
*Asegurate de que `init_db.py` se haya ejecutado al menos una vez.*
