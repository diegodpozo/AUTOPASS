# Operaciones y Mantenimiento — AUTOPASS

## Monitoreo de Salud del Sistema

### Endpoints de Health Check

| Endpoint | Propósito | Respuesta |
|----------|-----------|-----------|
| `GET /v1/system/health` | Estado general del sistema | JSON con DB, MQTT, ALPR heartbeat status |
| `GET /v1/system/heartbeat` | Heartbeat de nodos ALPR | Timestamp actualizado |
| `GET /v1/admin/virtual-time/status` | Estado del tiempo virtual | Offset aplicado, tiempo real vs virtual |

### Sistema de Heartbeat
- Cada cámara/nodo ALPR envía heartbeat a `POST /v1/system/heartbeat` cada N segundos
- El backend mantiene un diccionario `ALPR_HEARTBEATS` con timestamps
- Timeout configurable: `HEARTBEAT_TIMEOUT_SECONDS` (default 90s)
- El health check reporta cada cámara como:
  - 🟢 **OK**: Heartbeat recibido dentro del timeout
  - 🔴 **TIMEOUT**: No se recibió heartbeat en el período

### Workers de Background

| Worker | Intervalo | Función |
|--------|-----------|---------|
| **Reservation Cleanup** | 300s (configurable) | `auto_finalize_all_reservations()` - Libera plazas de reservas vencidas, limpia no pagadas |
| **Notification Worker** | Continuo | Procesa colas de WebSocket para broadcasts de ocupación |

## Logs y Debugging

### Fuentes de Log

| Componente | Ubicación | Nivel |
|------------|-----------|-------|
| Servidor FastAPI | stdout (consola) | INFO, WARNING, ERROR |
| ALPR Service | stdout (consola) | DEBUG en modo simulación |
| WebSocket | stdout con prefijo `[WS]` | INFO |
| MQTT | stdout con prefijo MQTT | INFO |

### Logs Importantes
```
[WS] Conexión establecida: user=admin sucursal=Sucursal Principal
[AccessService] validate_plate: patente=ABC123 entrada OK
[AccessService] exit_plate: patente=ABC123 salida OK cortesía=10min
[Worker] auto_finalize_all_reservations: 3 reservas finalizadas
[ReservationService] Cancelación: reserva #123 reembolso=$500.00
[System] Error en fase de inicio (MQTT/DB): ...
```

## Mantenimiento Preventivo

### Diario
- [ ] Verificar health check del sistema
- [ ] Monitorear heartbeats de cámaras
- [ ] Revisar logs por errores inusuales

### Semanal
- [ ] Verificar espacio en disco (especialmente `captured_images/`)
- [ ] Revisar pool de conexiones DB
- [ ] Verificar estado de reservas (ninguna colgada)

### Mensual
- [ ] Backup de base de datos
- [ ] Limpieza de imágenes de debug (`alpr_debug/`)
- [ ] Revisar y optimizar consultas lentas en DB
- [ ] Actualizar dependencias de seguridad

## Procedimientos de Recuperación

### Reinicio del Sistema
```powershell
# Detener Uvicorn (Ctrl+C)
# Verificar que no queden procesos colgados
.\venv\Scripts\python.exe main.py  # Reiniciar
```

### Recuperación ante Falla de DB
1. Detener el servidor
2. Restaurar backup de `parking.db` (SQLite) o restaurar dump de PostgreSQL
3. Iniciar servidor
4. Verificar consistencia de datos con scripts de consulta

### Recuperación ante Falla de Cámara ALPR
1. Verificar conectividad de red con la cámara (ping)
2. Desde Dashboard > Ajustes > Monitoreo: detener y reiniciar servicio
3. Si persiste: verificar IP en configuración, credenciales RTSP

### Rollback de Versión
1. `git checkout release/vX.X.X`
2. Restaurar backup de DB de la versión anterior
3. Reiniciar servidor

## Seguridad Operativa

### Recomendaciones
1. **HTTPS**: Usar reverse proxy (nginx/caddy) con SSL en producción
2. **SECRET_KEY**: Generar clave única para cada instancia:
   ```python
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
3. **Firewall**: Restringir puertos (solo 443/80 para web, 1883 para MQTT saliente)
4. **PostgreSQL**: Usar usuario dedicado con privilegios mínimos
5. **Logs**: No loguear contraseñas ni tokens JWT completos
6. **Actualizaciones**: Mantener EasyOCR, PyTorch y dependencias actualizadas

### Variables de Entorno Sensibles
| Variable | Protección |
|----------|------------|
| `SECRET_KEY` | No compartir, única por instancia |
| `SMTP_PASSWORD` | Almacenar en gestor de secrets |
| `DATABASE_URL` | No incluir en repositorios públicos |
| `MQTT_*` | Usar credenciales si el broker lo requiere |
