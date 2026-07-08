# Diseño del Frontend — AUTOPASS

## Arquitectura del Frontend

```
templates/
├── base.html                  # Layout base con navbar, footer, sidebar
├── index.html                 # Landing page (público)
├── login.html                 # Login
├── register.html              # Registro
├── dashboard.html             # Dashboard principal (admin/staff)
├── perfil.html                # Perfil de usuario (cliente)
├── nuestra-red.html           # Mapa interactivo de sucursales
├── contacto.html              # Contacto
├── terminos.html              # Términos y condiciones
├── privacidad.html            # Privacidad
├── reset-password.html        # Reset de contraseña
├── monitoreo.html             # Monitoreo DVR en vivo
├── components/                # Componentes reutilizables
│   ├── navbar.html
│   ├── footer.html
│   ├── modals.html
│   └── sidebar.html
├── dashboard/
│   └── tabs/                  # Tabs del dashboard admin
│       ├── inicio.html
│       ├── operaciones.html
│       ├── usuarios.html
│       ├── sucursales.html
│       ├── monitoreo.html
│       ├── reservas_admin.html
│       ├── promociones.html
│       ├── configuracion.html
│       ├── reportes.html
│       └── fidelizacion.html
├── profile/
│   └── tabs/                  # Tabs del perfil de usuario
│       ├── inicio.html
│       ├── reservas.html
│       ├── vehiculos.html
│       ├── saldo.html
│       └── fidelizacion.html
└── emails/                    # Templates de email
    ├── base_email.html
    ├── reservation_confirmation.html
    └── password_reset.html

static/
├── css/
│   ├── base/
│   │   ├── reset.css          # Normalize / reset
│   │   ├── variables.css      # Variables CSS (colores, fuentes)
│   │   └── typography.css     # Tipografía global
│   ├── components/
│   │   ├── buttons.css        # Botones y FAB
│   │   ├── cards.css          # Cards Glassmorphism
│   │   ├── forms.css          # Formularios
│   │   ├── modals.css         # Modales y alerts
│   │   ├── navbar.css         # Barra de navegación
│   │   ├── progress.css       # Barras de progreso
│   │   └── tables.css         # Tablas
│   ├── layout/
│   │   ├── grid.css           # Sistema de grilla
│   │   ├── sidebar.css        # Sidebar colapsable
│   │   └── header.css         # Header
│   └── pages/
│       ├── landing.css        # Landing page
│       ├── dashboard.css      # Dashboard
│       ├── perfil.css         # Perfil de usuario
│       └── monitoreo.css      # Monitoreo DVR
├── js/
│   ├── modules/               # Módulos ES6
│   │   ├── api.js             # Cliente HTTP centralizado (fetch wrapper)
│   │   ├── utils.js           # Utilidades (validatePlate, detectVehicleType, showConfirm)
│   │   ├── dashboard-stats.js # Estadísticas de aforo en tiempo real
│   │   ├── notifications.js   # Gestión de notificaciones
│   │   ├── websocket.js       # Cliente WebSocket
│   │   ├── tour.js            # Tour interactivo de onboarding
│   │   ├── onboarding_helpers.js # Helpers del tour
│   │   └── map.js             # Integración Leaflet.js
│   ├── auth.js                # Lógica de autenticación
│   ├── dashboard.js           # Lógica del dashboard
│   ├── perfil.js              # Lógica del perfil de usuario
│   ├── monitoreo.js           # Lógica del monitoreo DVR
│   └── landing.js             # Lógica de la landing page
├── images/
│   ├── logo.png
│   └── INICIO/                # Imágenes de la landing
└── uploads/
    └── branches/              # Logos subidos de sucursales
```

## Diseño Visual (Design System)

### Paleta de Colores
| Elemento | Color | Código | Uso |
|----------|-------|--------|-----|
| Dorado AUTOPASS | Dorado | `#C5A059` | Botones principales, acentos, íconos |
| Fondo oscuro | Negro | `#0A0A0A` | Fondos de dashboard, monitoreo |
| Fondo claro | Blanco humo | `#F5F5F5` | Landing, formularios |
| Superficie | Gris oscuro | `#1A1A1A` | Cards, contenedores |
| Texto principal | Blanco | `#FFFFFF` | Texto sobre fondo oscuro |
| Texto secundario | Gris claro | `#888888` | Subtítulos, metadata |
| Éxito | Verde | `#4CAF50` | Confirmaciones, disponible |
| Alerta | Amarillo | `#FFC107` | Ocupación media |
| Peligro | Naranja | `#FF9800` | Ocupación alta |
| Error | Rojo | `#F44336` | Ocupación crítica, errores |
| Info | Cian | `#00bcd4` | Hover en monitoreo |

### Glassmorphism
```css
.glass-card {
    background: rgba(26, 26, 26, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
}
```

### Tipografía
- Sistema: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- Monitoreo: `monospace` para datos técnicos (duración, HUD)
- Tamaños: 0.75rem a 2rem según jerarquía

### Componentes Clave

**FAB (Floating Action Button)**
```css
.fab {
    position: fixed; bottom: 30px; right: 30px;
    background: #C5A059; color: #000;
    border-radius: 60px; padding: 0;
    min-width: 60px; height: 60px;
    display: flex; align-items: center;
    justify-content: center; gap: 0;
    transition: all 0.3s ease; z-index: 1000;
    border: none; cursor: pointer;
}
.fab .label {
    max-width: 0; overflow: hidden;
    transition: max-width 0.3s ease;
    font-size: 0.9rem; font-weight: 600;
}
.fab:hover .label { max-width: 150px; margin-right: 8px; }
```

**Barras de Progreso**
- `> 50%`: Verde `#4CAF50`
- `26-50%`: Amarillo `#FFC107`
- `11-25%`: Naranja `#FF9800`
- `≤ 10%`: Rojo `#F44336`

### Responsive Design
- CSS Grid para layouts adaptativos
- Sidebar colapsable con persistencia en localStorage
- Monitoreo: grilla dinámica (1x1, 2x1, 2x2, 3x2, 3x3) según cantidad de cámaras

### Convenciones de Código JS
1. **ES6 Modules**: `import/export` en todos los archivos de `modules/`
2. **API Centralizada**: Toda petición HTTP usa `modules/api.js`
3. **Validación de Patentes**: Usar `validatePlate` de `modules/utils.js`
4. **Detección de Tipo**: Usar `detectVehicleType` para auto-detectar Moto/Auto/Camioneta
5. **Confirmaciones**: Usar `showConfirm` para acciones destructivas
6. **WebSockets**: Usar `modules/websocket.js` para conexiones WS
7. **Type Module**: `<script type="module" src="...">` en templates

### Flujo de Navegación
```
Landing (público)
├── Login ──► Dashboard (admin/staff)
│                ├── Inicio (ocupación en tiempo real)
│                ├── Operaciones (manual entry/exit)
│                ├── Usuarios (gestión)
│                ├── Sucursales (gestión + pisos)
│                ├── Monitoreo (cámaras DVR)
│                ├── Reservas (admin)
│                ├── Promociones
│                ├── Configuración (tarifas, capacidad)
│                ├── Reportes (financieros)
│                └── Fidelización
├── Login ──► Perfil (cliente)
│                ├── Inicio (dashboard personal)
│                ├── Reservas (mis reservas)
│                ├── Vehículos (mi flota)
│                ├── Saldo (recarga, historial)
│                └── Fidelización (puntos)
├── Registro
├── Nuestra Red (mapa sucursales)
├── Contacto
└── Reset Password
```
