# Changelog: ALPR, QR & Normalización (2026-06-23)

Resumen de los cambios introducidos el 2026-06-23 relacionados con ALPR/QR, normalización de patentes y notificaciones en tiempo real.

- **ALPR — Quick QR & Debounce:** Se incorporó detección rápida de QR en el bucle principal (Quick QR) y un mecanismo de supresión/debounce de eventos duplicados. El cooldown por defecto está en **10 segundos**.
- **ALPR — Cola y política de drop:** La cola de frames del ALPR usa `maxsize=4` y política "drop-oldest" cuando está llena, evitando bloqueo por FPS altos.
- **Normalización de patentes:** Nueva columna `normalized_patente` en `AccessLog` con índice (`idx_access_logs_normalized_patente`). Se añadieron scripts de migración y backfill:
  - `scripts/migrate_add_normalized_patente.py`
  - `scripts/backfill_normalize_all_access_logs.py`
  - `scripts/backfill_attach_reservations.py` (vincula accesos a reservas pagas vigentes)

- **Manual entry/exit:** Los flujos manuales (admin) reusan registros `ENTRADA` existentes cuando corresponde e intentan asociar la `reserva_id` y marcar `pago_confirmado` si aplica, evitando duplicados y cargos erróneos.

- **NotificationService / WebSockets:** `NotificationService` ahora permite registrar el loop de asyncio del servidor Web (uvicorn) y usa `asyncio.run_coroutine_threadsafe` para programar broadcast desde hilos sin bloqueo. Se añadieron logs de conexión: `"[WS] Conexión establecida: user=... sucursal=..."`.

- **Frontend:** El endpoint `current_occupancy` ahora devuelve info de `reserva` (id, tipo_estadia, estado_pago). El dashboard oculta el botón "Cancelar estadía" para reservas no horarias pagas y depende de una conexión WebSocket activa (`/v1/parking/ws`) para actualizar la lista de vehículos automáticamente.

- **Recomendaciones operativas:**
  1. Reiniciar el backend (uvicorn) y el proceso ALPR para cargar los cambios.
  2. Verificar que el dashboard cliente tenga abierta la conexión WS (`/v1/parking/ws`) — en logs backend se verá `"[WS] Conexión establecida: ..."` al recargar la UI.
  3. Si la cola de frames sigue saturándose con cámaras de alto FPS, considerar aumentar `ALPR` queue `maxsize` a 8.

- **Archivos clave tocados:**
  - `alpr_service.py` (Quick QR, queue drop-oldest, cooldown 10s)
  - `services/access_service.py` (normalized_patente, attach reserva, notify)
  - `services/notification_service.py` (set_event_loop + run_coroutine_threadsafe)
  - `routes/parking/status.py` (registro WS connect)
  - `routes/admin/operations.py` (manual-entry/manual-exit reuse)
  - `static/js/modules/dashboard-stats.js` (oculta botón cancelar para reservas pagas)

- **Pruebas realizadas in-situ:** Detección de QR y placas (ej: FG 112 LO). Backfill y asociación de reservas verificadas contra `reservation_id=707` en entorno local.

---

Mantener este changelog junto a la documentación principal para referencia rápida durante despliegues y debugging.
