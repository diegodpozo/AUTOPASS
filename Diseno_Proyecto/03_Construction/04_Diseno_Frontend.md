# Diseno del Frontend — AUTOPASS

## Arquitectura del Frontend

```
templates/                     # 51 templates HTML
├── base.html                  # Layout base con navbar, footer, sidebar
├── index.html                 # Landing page (publico)
├── nuestra-red.html           # Mapa interactivo de sucursales
├── dashboard.html             # Dashboard principal (admin/staff)
├── perfil.html                # Perfil de usuario (cliente)
├── contacto.html              # Contacto
├── terminos.html              # Terminos y condiciones
├── privacidad.html            # Privacidad
├── reset_password.html        # Reset de contrasena
├── monitoreo_live.html        # Monitoreo DVR en vivo
├── instalar.html              # Guia de instalacion PWA
├── estadisticas_ocr.html      # Estadisticas del motor OCR
├── components/                # Componentes reutilizables
│   ├── navbar.html
│   ├── footer.html
│   ├── auth_modals.html       # Modales de login/registro
│   ├── modals_global.html     # Modales globales de confirmacion
│   ├── sidebar_user.html      # Sidebar de usuario
│   ├── virtual_time_banner.html # Banner de tiempo virtual (testing)
│   ├── monitoreo_controls.html # Controles del panel de monitoreo
│   └── chart_window_controls.html # Controles comunes de graficos (WindowedChart)
├── dashboard/
│   ├── modals/                # Modales del dashboard admin
│   │   ├── branch_modals.html
│   │   ├── promotion_modal.html
│   │   ├── user_modals.html
│   │   └── admin_help_modal.html # Centro de ayuda admin (modal FAQ)
│   └── tabs/                  # Tabs del dashboard admin
│       ├── users.html         # Gestion de usuarios
│       ├── branches.html      # Gestion de sucursales + pisos
│       ├── admin_reservations.html # Gestion de reservas
│       ├── promotions.html    # Gestion de promociones
│       ├── settings.html      # Configuracion (tarifas, capacidad)
│       │   └── settings/      # Sub-tabs de configuracion
│       │       ├── settings_rates.html
│       │       ├── settings_floors.html
│       │       ├── settings_monitoring.html
│       │       └── settings_system.html
│       ├── finance.html       # Reportes financieros
│       ├── occupancy.html     # Estadisticas de ocupacion
│       ├── live.html          # Monitoreo en vivo (camaras)
│       ├── metricas.html      # Grafico de accesos en vivo
│       └── tickets.html       # Soporte y tickets
├── profile/
│   ├── modals.html            # Modales del perfil
│   ├── modals/
│   │   └── onboarding_modal.html # Tour de onboarding
│   └── tabs/                  # Tabs del perfil de usuario
│       ├── inicio.html        # Dashboard personal
│       ├── reservas.html      # Mis reservas
│       ├── vehiculos.html     # Mis vehiculos
│       ├── puntos.html        # Puntos y fidelizacion
│       ├── notificaciones.html # Notificaciones in-app
│       ├── cuenta.html        # Configuracion de cuenta
│       └── ayuda.html         # Ayuda y soporte
└── emails/                    # Templates de email (autocontenidos)
    ├── reservation_confirmation.html
    ├── reservation_reminder.html
    ├── reservation_auto_cancelled.html
    └── recovery.html

static/
├── css/                       # 42 archivos CSS (41 en sub-carpetas + style.css legacy)
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
│   │   ├── virtual_time.css   # Banner de tiempo virtual
│   │   └── chart_window.css   # Controles de graficos (WindowedChart)
│   ├── layout/
│   │   ├── grid.css           # Sistema de grilla
│   │   ├── sidebar.css        # Sidebar colapsable
│   │   └── header.css         # Header
│   └── pages/
│       ├── landing.css        # Landing page
│       ├── dashboard.css      # Dashboard
│       ├── profile.css        # Perfil de usuario
│       ├── contacto.css       # Pagina de contacto
│       ├── legal.css          # Terminos y privacidad
│       ├── dashboard/         # Estilos del dashboard (7)
│       │   ├── dashboard-base.css
│       │   ├── dashboard-cards.css
│       │   ├── dashboard-live.css
│       │   ├── dashboard-settings.css
│       │   ├── dashboard-tables.css
│       │   ├── dashboard-admin-tour.css
│       │   └── dashboard-metrics.css
│       ├── landing/           # Estilos de la landing (5)
│       │   ├── landing-features.css
│       │   ├── landing-hero.css
│       │   ├── landing-map.css
│       │   ├── landing-modals.css
│       │   └── landing-nav.css
│       └── profile/           # Estilos del perfil (7)
│           ├── profile-base.css
│           ├── profile-help.css
│           ├── profile-notifications.css
│           ├── profile-points.css
│           ├── profile-reservations.css
│           ├── profile-tour.css
│           └── profile-vehicles.css
├── js/
│   ├── modules/               # Modulos ES6 (62)
│   │   ├── api.js             # Cliente HTTP centralizado (fetch wrapper)
│   │   ├── utils.js           # Utilidades (formatNum, toTitle, formatDate, showToast, showConfirm, validatePlate, detectVehicleType)
│   │   ├── ui.js              # Utilidades de UI general (modales, sidebar, logout)
│   │   ├── auth.js            # Logica de autenticacion (login, registro, validacion de forms)
│   │   ├── reset_password.js  # Reset de contrasena (validacion en vivo + token)
│   │   ├── profile.js         # Logica del perfil (puntos, promociones, historial)
│   │   ├── profile-help.js    # Ayuda y soporte
│   │   ├── vehicles.js        # Gestion de vehiculos
│   │   ├── reservas.js        # Fachada de reservas (re-exporta form/list/actions/pass)
│   │   ├── reservas-form.js   # Formulario de reservas (datepickers, tarifas, validaciones)
│   │   ├── reservas-form-state.js # Estado compartido del formulario (tarifas, vehiculos, slots)
│   │   ├── reservas-form-price.js  # Estimacion de precios y tarifas
│   │   ├── reservas-form-slot.js   # Selector de slots horarios (drag, horas deshabilitadas)
│   │   ├── reservas-list.js   # Lista de reservas (cards, timeline, historial, paginacion)
│   │   ├── reservas-actions.js # Acciones de reservas (pagar con saldo, cancelar con reembolso)
│   │   ├── reservas-pass.js   # Pase digital con QR (QRCode.js)
│   │   ├── landing.js         # Fachada de landing (re-exporta mapa + carrusel)
│   │   ├── landing-carousel.js # Carrusel de imagenes de la landing
│   │   ├── landing-data.js    # Cache de POIs y datos de estadios
│   │   ├── landing-map.js     # Fachada del mapa Leaflet (re-exporta getDirectionsTo, findNearestBranch, filterMapByLocality)
│   │   ├── landing-map-state.js # Estado global compartido del mapa (lmState)
│   │   ├── landing-map-data.js  # Datos del mapa (localidad, direcciones, getDirectionsTo, cache POIs)
│   │   ├── landing-map-pois.js  # POIs del mapa (cines, estadios)
│   │   ├── landing-map-geo.js   # Geocoding y sucursal mas cercana (findNearestBranch)
│   │   ├── landing-map-locality.js # Filtro y busqueda por localidad (filterMapByLocality)
│   │   ├── virtual-time.js    # Control de tiempo virtual
│   │   ├── notifications.js   # Fachada de notificaciones (re-exporta 24 funciones de 8 submódulos)
│   │   ├── notifications-state.js # Estado global compartido de notificaciones (notifState)
│   │   ├── notifications-format.js # Formateo (titulos, enlaces, tiempo relativo, iconos)
│   │   ├── notifications-render.js # Renderizado de listados, toasts y badges
│   │   ├── notifications-badge.js  # Badge de unread y contador en header/sidebar
│   │   ├── notifications-actions.js # Acciones (marcar leida, resolver, guardar dispositivo)
│   │   ├── notifications-nav.js    # Navegacion de pestanas del panel
│   │   ├── notifications-dropdown.js # Dropdown del panel (cierre al click fuera)
│   │   ├── notifications-polling.js # Polling de notificaciones (30s) y arranque
│   │   ├── tour.js            # Tour interactivo de onboarding (lanzadores)
│   │   ├── tour-steps.js      # Definicion de pasos de los tours del portal
│   │   ├── admin-tour.js      # Fachada del tour admin (re-exporta steps/engine/help; lanzadores)
│   │   ├── admin-tour-steps.js # Pasos de los tours admin
│   │   ├── admin-tour-engine.js # Motor del tour admin (showAdminTour, avance, highlight)
│   │   ├── admin-help.js      # Centro de ayuda admin (modal openAdminHelpModal, FAQ, filtros)
│   │   ├── onboarding_helpers.js # Helpers del tour
│   │   ├── dashboard-ui.js    # UI del dashboard (tabs, sidebar, reloj, camaras)
│   │   ├── dashboard-stats.js # Estadisticas de aforo en tiempo real + cortesia countdown
│   │   ├── dashboard-metrics.js # Grafico de accesos en vivo y filtros por rango
│   │   ├── dashboard-admin.js # Logica admin del dashboard (orquestador)
│   │   ├── dashboard-admin-branches.js # Fachada de sucursales
│   │   ├── dashboard-admin-branches-crud.js
│   │   ├── dashboard-admin-branches-floors.js
│   │   ├── dashboard-admin-settings.js
│   │   ├── dashboard-admin-users.js
│   │   ├── dashboard-reservations.js # Fachada de reservas admin (re-exporta list/form)
│   │   ├── reservations-admin-list.js # Listado de reservas admin (filtros, pago, cancelar, badge)
│   │   ├── reservations-admin-form.js # Formulario de reserva admin (alta/edicion, patente lookup)
│   │   ├── dashboard-finance.js
│   │   ├── dashboard-promotions.js
│   │   ├── dashboard-tickets.js # Soporte y tickets
│   │   ├── dashboard-operations.js
│   │   ├── dashboard-cameras.js # Configuracion y control de camaras del dashboard
│   │   ├── monitoreo-live.js  # Monitoreo de camaras en vivo
│   │   ├── chart_window.js    # Clase WindowedChart (graficos con ventana temporal)
│   │   └── estadisticas_ocr.js # Estadisticas del motor OCR
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
│                ├── Live (monitoreo camaras en vivo)
│                ├── Admin Reservations (gestion de reservas)
│                ├── Users (gestion de usuarios)
│                ├── Finance (reportes financieros)
│                ├── Promotions (gestion de promociones)
│                ├── Tickets (soporte y tickets)
│                ├── Branches (gestion sucursales + pisos)
│                ├── Settings (tarifas, capacidad; sub-tabs rates/floors/monitoring/system)
│                └── Occupancy (estadisticas de ocupacion)
├── Login (modales via auth_modals.html) ──► Perfil (cliente)
│                ├── Inicio (dashboard personal)
│                ├── Reservas (mis reservas + pase digital QR)
│                ├── Vehiculos (mi flota)
│                ├── Puntos (fidelizacion)
│                ├── Notificaciones (in-app)
│                ├── Cuenta (configuracion personal)
│                └── Ayuda (soporte y tickets)
├── Nuestra Red (mapa sucursales)
├── Contacto
└── Reset Password
```
