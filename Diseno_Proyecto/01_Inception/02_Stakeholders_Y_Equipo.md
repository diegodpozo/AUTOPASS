# Stakeholders y Equipo de Desarrollo

## Stakeholders Identificados

| Stakeholder | Rol | Intereses | Expectativas |
|-------------|-----|-----------|--------------|
| **Dirección / Dueño** | Sponsor del proyecto | ROI, expansión, imagen de marca | Sistema robusto que permita escalar el negocio |
| **Gerente de Operaciones** | Usuario clave (ADMIN) | Control de sucursales, reportes financieros | Dashboard ejecutivo con métricas en tiempo real |
| **Encargados de Sucursal** | LOCAL_ADMIN | Gestión diaria de tarifas, personal y aforo | Panel intuitivo para operación local |
| **Personal de Turno** | STAFF | Operaciones manuales, atención al cliente | Interfaz rápida y sin complicaciones |
| **Clientes** | USER | Reservar, pagar, entrar/salir sin demoras | App/web fácil de usar, respuesta inmediata |
| **Soporte Técnico** | Mantenimiento | Monitoreo de salud del sistema, debugging | Logs claros, heartbeats, diagnósticos remotos |

## Equipo de Desarrollo

| Rol | Responsabilidades |
|-----|-------------------|
| **Arquitecto de Software** | Define la estructura Clean Architecture, capas, patrones y estándares |
| **Backend Developer** | Implementa APIs FastAPI, lógica de negocio (services), modelos ORM, integración MQTT |
| **Frontend Developer** | Desarrolla templates Jinja2, CSS Glassmorphism, JS modular, WebSockets cliente |
| **DevOps** | Configura entorno de producción, despliegue, monitoreo, scripts de inicialización |
| **QA / Tester** | Pruebas unitarias (pytest), pruebas de integración, validación de flujos críticos |
| **Especialista en Visión Artificial** | Configura y optimiza EasyOCR + OpenCV para ALPR, tuning de parámetros |

## Cronograma de Alto Nivel

| Hito | Versión | Fecha | Entregable Principal |
|------|---------|-------|---------------------|
| Base operativa | v8.0.0 | Jun 2026 | ALPR funcional, acceso, facturación básica |
| Multi-sucursal + Pisos | v8.2.0 | Jun 2026 | Gestión vertical y bimodal (Auto/Moto) |
| Reportes financieros | v8.5.5 | Jun 2026 | Analytics con filtros, RBAC empoderado |
| Monitoreo premium | v8.6.0 | Jun 2026 | Dashboard en tiempo real, paginación |
| UX/UI avanzado | v8.8.5 | Jun 2026 | Formularios normalizados, FAB, animaciones |
| Video streaming | v8.9.5 | Jun 2026 | Cámaras en vivo, WebSockets de video |
| Tiempo real + Settings | v9.0.0 | Jun 2026 | WebSockets de aforo, configuración dinámica |
| Camionetas (trimodal) | v9.1.0 | Jun 2026 | Tercer tipo vehicular con tarifas propias |
| Refinamiento UX/RBAC | v9.1.5 | Jun 2026 | UI hardening, filtros financieros expandidos |
| Reservas + Aforo Inteligente | v9.2.0 | Jun 2026 | Reservas no horarias, liberación automática |
| FAB + Monitoreo limpio | v9.3.0 | Jun 2026 | Worker robusto, barras de progreso dinámicas |
| DVR CCTV Dinámico | v9.4.0 | Jul 2026 | Grilla auto-ajustable, HUD, panel flotante |
| Cortesía + Ocupación física | v9.5.0 | Jul 2026 | Fix ALPR, cortesía 10 min, ocupación solo física |
