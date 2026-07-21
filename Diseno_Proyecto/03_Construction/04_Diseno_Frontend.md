# Diseno del Frontend — AUTOPASS

## Arquitectura del Frontend

```
templates/
├── base.html                  # Layout base con navbar, footer, sidebar
├── index.html                 # Landing page (publico)
├── dashboard.html             # Dashboard principal (admin/staff)
├── perfil.html                # Perfil de usuario (cliente)
├── nuestra-red.html           # Mapa interactivo de sucursales
├── contacto.html              # Contacto
├── terminos.html              # Terminos y condiciones
├── privacidad.html            # Privacidad
├── reset_password.html        # Reset de contrasena
├── monitoreo_live.html        # Monitoreo DVR en vivo
├── components/                # Componentes reutilizables
│   ├── navbar.html
│   ├── footer.html
│   ├── auth_modals.html       # Modales de login/registro
│   ├── modals_global.html     # Modales globales de confirmacion
│   ├── sidebar_user.html      # Sidebar de usuario
│   └── virtual_time_banner.html # Banner de tiempo virtual (testing)
├── dashboard/
│   └── tabs/                  # Tabs del dashboard admin
│       ├── users.html         # Gestion de usuarios
│       ├── branches.html      # Gestion de sucursales + pisos
│       ├── admin_reservations.html # Gestion de reservas
│       ├── promotions.html    # Gestion de promociones
│       ├── settings.html      # Configuracion (tarifas, capacidad)
│       ├── finance.html       # Reportes financieros
│       ├── occupancy.html     # Estadisticas de ocupacion
│       └── live.html          # Monitoreo en vivo (camaras)
├── profile/
│   └── tabs/                  # Tabs del perfil de usuario
│       ├── inicio.html        # Dashboard personal
│       ├── reservas.html      # Mis reservas
│       ├── vehiculos.html     # Mis vehiculos
│       ├── puntos.html        # Puntos y fidelizacion
│       ├── notificaciones.html # Notificaciones in-app
│       └── cuenta.html        # Configuracion de cuenta
└── emails/                    # Templates de email
    ├── reservation_confirmation.html
    ├── reservation_reminder.html
    ├── reservation_auto_cancelled.html
    └── recovery.html

static/
├── css/
│   ├── style.css              # Estilos legacy (en proceso de vaciado)
│   ├── base/
│   │   ├── reset.css          # Normalize / reset
│   │   ├── variables.css      # Variables CSS (colores, fuentes)
│   │   ├── typography.css     # Tipografia global
│   │   └── utilities.css      # Utilidades (flex, spacing, etc.)
│   ├── components/
│   │   ├── badges.css         # Badges y etiquetas
│   │   ├── buttons.css        # Botones y FAB
│   │   ├── cards.css          # Cards Glassmorphism
│   │   ├── footer.css         # Footer
│   │   ├── forms.css          # Formularios
│   │   ├── modals.css         # Modales y alerts
│   │   ├── tables.css         # Tablas
│   │   └── virtual_time.css   # Banner de tiempo virtual
│   ├── layout/
│   │   ├── grid.css           # Sistema de grilla
│   │   ├── sidebar.css        # Sidebar colapsable
│   │   └── header.css         # Header
│   └── pages/
│       ├── landing.css        # Landing page
│       ├── dashboard.css      # Dashboard
│       ├── profile.css        # Perfil de usuario
│       ├── contacto.css       # Pagina de contacto
│       └── legal.css          # Terminos y privacidad
├── js/
│   ├── modules/               # Modulos ES6
│   │   ├── api.js             # Cliente HTTP centralizado (fetch wrapper)
│   │   ├── utils.js           # Utilidades (validatePlate, detectVehicleType, showConfirm)
│   │   ├── dashboard-stats.js # Estadisticas de aforo en tiempo real
│   │   ├── dashboard-ui.js    # UI del dashboard (tabs, sidebar)
│   │   ├── dashboard-admin.js # Logica admin del dashboard
│   │   ├── dashboard-promotions.js # Gestion de promociones
│   │   ├── notifications.js   # Gestion de notificaciones
│   │   ├── tour.js            # Tour interactivo de onboarding
│   │   ├── onboarding_helpers.js # Helpers del tour
│   │   ├── auth.js            # Logica de autenticacion
│   │   ├── profile.js         # Logica del perfil
│   │   ├── landing.js         # Logica de la landing
│   │   ├── reservas.js        # Gestion de reservas
│   │   ├── vehicles.js        # Gestion de vehiculos
│   │   ├── ui.js              # Utilidades de UI general
│   │   └── virtual-time.js    # Control de tiempo virtual
│   ├── auth.js                # Logica de autenticacion (root-level)
│   ├── dashboard.js           # Logica del dashboard (root-level)
│   ├── perfil.js              # Logica del perfil de usuario
│   ├── landing.js             # Logica de la landing page
│   ├── contacto.js            # Logica de contacto
│   ├── main.js                # Inicializacion principal
│   ├── api_client.js          # Cliente API alternativo
│   ├── vehicles.js            # Vehiculos (root-level)
│   └── reservas.js            # Reservas (root-level)
├── images/
│   ├── logo.png
│   └── INICIO/                # Imagenes de la landing
└── uploads/
    └── branches/              # Logos subidos de sucursales
```

## Diseno Visual (Design System)

### Paleta de Colores
| Elemento | Color | Codigo | Uso |
|----------|-------|--------|-----|
| Dorado AUTOPASS | Dorado | `#C5A059` | Botones principales, acentos, iconos |
| Fondo oscuro | Negro | `#0A0A0A` | Fondos de dashboard, monitoreo |
| Fondo claro | Blanco humo | `#F5F5F5` | Landing, formularios |
| Superficie | Gris oscuro | `#1A1A1A` | Cards, contenedores |
| Texto principal | Blanco | `#FFFFFF` | Texto sobre fondo oscuro |
| Texto secundario | Gris claro | `#888888` | Subtitulos, metadata |
| Exito | Verde | `#4CAF50` | Confirmaciones, disponible |
| Alerta | Amarillo | `#FFC107` | Ocupacion media |
| Peligro | Naranja | `#FF9800` | Ocupacion alta |
| Error | Rojo | `#F44336` | Ocupacion critica, errores |
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

### Tipografia
- Sistema: `-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif`
- Monitoreo: `monospace` para datos tecnicos (duracion, HUD)
- Tamanos: 0.75rem a 2rem segun jerarquia

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
- `<= 10%`: Rojo `#F44336`

### Responsive Design
- CSS Grid para layouts adaptativos
- Sidebar colapsable con persistencia en localStorage
- Monitoreo: grilla dinamica (1x1, 2x1, 2x2, 3x2, 3x3) segun cantidad de camaras

### Convenciones de Codigo JS
1. **ES6 Modules**: `import/export` en todos los archivos de `modules/`
2. **API Centralizada**: Toda peticion HTTP usa `modules/api.js`
3. **Validacion de Patentes**: Usar `validatePlate` de `modules/utils.js`
4. **Deteccion de Tipo**: Usar `detectVehicleType` para auto-detectar Moto/Auto/Camioneta
5. **Confirmaciones**: Usar `showConfirm` para acciones destructivas
6. **Type Module**: `<script type="module" src="...">` en templates

### Flujo de Navegacion
```
Landing (publico)
├── Login (modales via auth_modals.html) ──► Dashboard (admin/staff)
│                ├── Occupancy (ocupacion en tiempo real)
│                ├── Live (monitoreo camaras en vivo)
│                ├── Users (gestion de usuarios)
│                ├── Branches (gestion sucursales + pisos)
│                ├── Admin Reservations (gestion de reservas)
│                ├── Promotions (gestion de promociones)
│                ├── Settings (tarifas, capacidad)
│                └── Finance (reportes financieros)
├── Login (modales via auth_modals.html) ──► Perfil (cliente)
│                ├── Inicio (dashboard personal)
│                ├── Reservas (mis reservas)
│                ├── Vehiculos (mi flota)
│                ├── Puntos (fidelizacion)
│                ├── Notificaciones (in-app)
│                └── Cuenta (configuracion personal)
├── Nuestra Red (mapa sucursales)
├── Contacto
└── Reset Password
```
