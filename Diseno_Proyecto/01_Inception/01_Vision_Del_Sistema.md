# Visión del Sistema — AUTOPASS

## Propósito
AUTOPASS es una solución empresarial integral para la gestión inteligente de estacionamientos. Combina visión artificial (ALPR), arquitectura limpia (Clean Architecture) y un frontend premium para automatizar el control de acceso, facturación y monitoreo en tiempo real de estacionamientos multi-sucursal y multi-piso.

## Problema que Resuelve
- Control manual ineficiente de entrada/salida de vehículos
- Dificultad para gestionar múltiples sucursales y pisos con aforos independientes
- Falta de visibilidad en tiempo real de la ocupación
- Procesos de facturación lentos y propensos a errores
- Imposibilidad de hacer reservas anticipadas con garantía de plaza
- Falta de integración entre hardware (barreras, sensores) y software de gestión

## Usuarios Objetivo
| Perfil | Descripción |
|--------|-------------|
| **Administrador Global (ADMIN)** | Dueño del sistema, gestiona toda la red de sucursales, usuarios y configuración global |
| **Administrador Local (LOCAL_ADMIN)** | Encargado de una sucursal específica, gestiona tarifas, pisos, personal y operaciones |
| **Personal Operativo (STAFF)** | Operadores de turno que realizan ingresos/egresos manuales y atención al cliente |
| **Cliente (USER)** | Usuario final que estaciona, hace reservas, paga y acumula puntos de fidelización |

## Propuesta de Valor
1. **Automatización total**: Reconocimiento automático de patentes (ALPR) y códigos QR para entrada/salida sin intervención humana
2. **Gestión multi-sucursal**: Control unificado de N sucursales con tarifas, aforo y personal independientes
3. **Multi-piso nativo**: Capacidad para definir N niveles por sucursal con cupos de autos/motos/camionetas configurables
4. **Facturación trimodal**: Motor de precios diferenciado para Autos, Motos y Camionetas
5. **Reservas inteligentes**: Reservas por hora, día, semana, quincena o mes con garantía de plaza
6. **Fidelización**: Sistema de puntos canjeables por promociones
7. **Monitoreo en tiempo real**: Dashboard con WebSockets para ocupación en vivo y video streaming de cámaras DVR
8. **RBAC (Role-Based Access Control)**: Jerarquía de permisos con aislamiento por sucursal
9. **Arquitectura escalable**: Clean Architecture con separación clara de capas (Routes, Services, Models, Schemas)

## Métricas de Éxito
- Reducción del tiempo de entrada/salida a < 5 segundos por vehículo
- Eliminación de errores de facturación manual
- 100% de disponibilidad del dashboard en tiempo real
- Soporte para N sucursales sin degradación del rendimiento
- Tasa de reconocimiento ALPR > 95% en condiciones normales
