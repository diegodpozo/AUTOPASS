# Estado del Proyecto: AUTOPASS (Actualizado 2026-06-12)

### 🚀 Hitos Recientes (Junio 2026) - Versión 8.5.0 (UI/UX Refinement & System Diagnostics)
- [x] **Simplificación de la UI de Configuración**: Eliminación de cabeceras redundantes e iconos de sección.
- [x] **Mejoras Portal Cliente (v8.5.1)**: Formulario de vinculación colapsable, validación de patentes Mercosur y rediseño de formularios de reserva.
- [x] **Nuevo Centro de Control y Diagnóstico**: Grilla premium para monitoreo en tiempo real de servicios core (Servidor, BD) y hardware (Barreras, Lectores de patente).
- [x] **Consistencia en Gestión de Niveles**: Edición habilitada para Planta Baja y sincronización de iconos (Layer Group, Pen/Gear) en todo el módulo.

### 🚀 Hitos Previos (Junio 2026) - Versión 8.3.3 (Configuration UI Overhaul)
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
