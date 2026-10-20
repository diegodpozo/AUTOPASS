# AUDITORIA DE BASE DE DATOS (SQLite seed actual)

> **Documento histórico (ronda SQLite, 2026-08-27).** En ese momento la base de uso era el
> SQLite *seed*; hoy el sistema corre sobre **Neon/Postgres**. La auditoría vigente es
> `AUDITORIA_DB_NEON.md`. Se conserva este archivo como registro de la ronda original.

## Resumen
- Duplicados usuarios (email/dni): 0
- Duplicados vehículos (user+patente normalizada): 0
- Settings con (clave,sucursal) duplicados: 0
- Sucursales con nombre duplicado (normalizado): 0
- Access logs: patente con espacios 0, normalized_patente NULL con patente 0, fechas NULL 0, duplicados por clave (patente,fecha,tipo,sucursal) 0
- Reservations: fechas NULL 0, patentes con espacios 0
- Vehicles: huérfanos (sin user_id) 0

## Incongruencias encontradas
- **Aforo huérfano**: 1 registro parking_aforo.sucursal = NULL (sin branch). Potencial dato inconsistente.
- **Sucursales sin aforo**: 4 branches creados en seed (AUTOPASS Castelar, Central, Ituzaingó, Morón) no tienen registro en parking_aforo. Pueden faltar filas esperadas o seed incompleto para aforo por sucursal.

## Notas de normalización
- Patentes limpias (sin espacios) y access_logs.normalized_patente poblado. OK.
- settings.sucursal NULL = global (uso correcto según modelo). OK.
- No hay claves compuestas duplicadas críticas.

## Recomendaciones (no invasivas)
1. Limpiar/explicar parking_aforo con sucursal IS NULL (o asignarlo a sucursal correcta).
2. Completar aforo por sucursal (o eliminar branches huérfanos si no aplican).
3. Validar unicidad (clave, COALESCE(sucursal,'')) a nivel modelo/migración si no existe.
