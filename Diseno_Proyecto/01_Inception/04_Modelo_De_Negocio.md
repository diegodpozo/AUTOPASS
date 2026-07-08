# Modelo de Negocio — AUTOPASS

## Propuesta de Valor
AUTOPASS digitaliza por completo la operación de estacionamientos, eliminando la necesidad de personal en puerta y reduciendo los tiempos de espera. El sistema permite:

- **Operación 24/7 sin personal**: El ALPR + barrera automática gestiona entrada/salida
- **Maximización de ingresos**: Facturación precisa sin errores humanos
- **Fidelización de clientes**: Programa de puntos + reservas anticipadas
- **Expansión escalable**: Agregar sucursales sin esfuerzo adicional de infraestructura de software

## Flujo de Ingresos

| Fuente de Ingreso | Descripción |
|-------------------|-------------|
| **Estadía por hora** | Clientes sin reserva pagan al salir según tiempo estacionado |
| **Reservas** | Pago anticipado por día/semana/quincena/mes con precio preferencial |
| **Suscripción mensual** | Clientes frecuentes con reserva mensual y precio fijo |
| **Penalidades** | Cargos por cancelaciones tardías o no shows (según política) |

## Segmentos de Cliente

| Segmento | Comportamiento | Necesidad |
|----------|---------------|-----------|
| **Ocasional** | Estaciona 1-3 horas, pocas veces al mes | Rapidez de entrada/salida, pago fácil |
| **Frecuente diario** | Estaciona todos los días laborales | Reserva mensual con precio fijo, garantía de plaza |
| **Frecuente semanal** | Estaciona 2-3 veces por semana | Reserva semanal, puntos de fidelización |
| **Residente/Comercio** | Estaciona en el mismo lugar todo el mes | Reserva mensual, pase digital |

## KPIs del Negocio

| KPI | Descripción | Objetivo |
|-----|-------------|----------|
| **Ocupación promedio** | % de ocupación diario | > 75% en hora pico |
| **Tasa de conversión a reserva** | % de clientes que pasan de ocasional a recurrente | > 30% |
| **Tickets por día** | Cantidad de operaciones de entrada/salida | Variable por sucursal |
| **Ingreso por estadía** | Ticket promedio | Según tarifario |
| **Redención de puntos** | % de puntos acumulados que se canjean | > 40% |
| **Tasa de cancelación** | % de reservas canceladas | < 15% |
| **Tiempo de ciclo** | Tiempo desde que un auto llega hasta que estaciona | < 30 seg |

## Ventajas Competitivas

1. **Hardware mínimo**: Solo necesita cámara IP + ESP32 con servomotor — no requiere costosos equipos de portón
2. **Multi-sucursal nativo**: Una sola instancia de software gestiona N sucursales
3. **Sin dependencia de internet**: El ALPR corre localmente (no requiere API cloud de reconocimiento)
4. **Código abierto/modificable**: El cliente puede adaptar el sistema a sus necesidades
5. **Reservas cross-sucursal**: Un cliente con cuenta puede reservar en cualquier sucursal de la red
