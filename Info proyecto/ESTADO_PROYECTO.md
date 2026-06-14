# Estado del Proyecto: AUTOPASS (Actualizado 2026-06-14)

### 🚀 Hitos Recientes (Junio 2026) - Versión 8.6.0 (Dashboard Optimization & Smart Monitoring)
- [x] **Optimización de Monitoreo**: Eliminación de KPIs redundantes (Ocupación Total %) y sección de salud del sistema para una vista operativa más limpia.
- [x] **Paginación Inteligente**: Implementación de listados de 10 ítems para "Vehículos Estacionados" y "Últimos Movimientos" con navegación premium y **Auto-Scroll** suave.
- [x] **Operación Manual Refinada**: Panel siempre visible (sin colapsables), colores unificados (Verde para entrada/salida) e inputs centrados y compactos.
- [x] **Sistema de Alertas Unificado**: Reemplazo de notificaciones simples por cuadros de confirmación estructurados (Patente, Tipo, Monto) con diseño vertical premium.
- [x] **Detección Automática de Motos**: Lógica de reconocimiento de patrones para patentes de moto (`1 Letra + 3 Números + 3 Letras`) en carga manual.
- [x] **Ajuste de Política Operativa**: Reducción del tiempo de cortesía a **10 minutos** con reflejo dinámico de deuda $0 en alertas de cancelación.
- [x] **Mejoras Visuales de Cámaras**: Fondo negro sólido para feeds offline (eliminación del mapa) y centrado de etiquetas de patente detectada.

### 🚀 Hitos Previos (Junio 2026) - Versión 8.5.5 (Financial Analytics & User Control)
- [x] **Rediseño del Panel de Configuración**:
    *   **Layout Minimalista**: Interfaz centrada, 2x2 para tarifas, inputs compactos.
    *   **Navegación Intuitiva**: Sistema de pestañas y sub-pestañas (Autos/Motos).
    *   **Gestión Vertical Mejorada**: Botones directos de Editar/Borrar para niveles.
    *   **Refinamiento de Permisos**: Hiding de métricas operativas para Super Admin.

### 🚀 Hitos Previos (Junio 2026) - Versión 8.2.0 (Vertical Expansion & Bimodal Support)
... [ESTO SE MANTIENE] ...

### 🚀 Hitos Previos (Junio 2026) - Versión 8.1.0 (Regional ALPR & UI Normalization)
- [x] **Motor ALPR Regional Mercosur**: Soporte para patentes de Argentina, Brasil, Uruguay y Paraguay.
- [x] **Motor Financiero Pro 2.0**: Paginación SQL nativa y cálculo de Recaudación Neta.
- [x] **Política de Cancelación**: Reembolsos proporcionales y bloqueo por presencia física.

### 🛠️ Arquitectura Actual (v8.2.0)
- **Capas**: Clean Architecture con soporte nativo para jerarquías Sucursal -> Pisos.
- **Seguridad**: JWT + RBAC con 4 niveles de acceso blindados.
- **Frontend**: Dashboard Premium unificado (PB + Pisos + Tarifas).

### 📊 Cobertura de Funcionalidades
- **Gestión**: Multi-sucursal y Multi-piso.
- **Facturación**: Bimodal (Auto/Moto) con descuentos automáticos.
- **Monitoreo**: ALPR en vivo con desglose de ocupación por nivel.

### 📅 Próximos Pasos (Roadmap v8.x)
- [ ] Integración real con Mercado Pago (Webhooks).
- [ ] Mapas de calor de ocupación por piso en el dashboard.
- [ ] Implementación de WebSockets para actualizaciones de aforo instantáneas sin recarga.
- [ ] Exportación de reportes detallados por nivel/piso.
