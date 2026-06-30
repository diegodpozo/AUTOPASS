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

## Cambios aplicados (parche ALPR — 2026-06-23, ajustes en runtime)

Se aplicaron múltiples correcciones y mejoras al servicio `alpr_service.py` para robustecer la lectura de patentes en condiciones reales (cámaras móviles, celulares, reflejos y placas de moto). Resumen técnico:

- Parámetros por defecto ajustados (configurables vía .env):
  - `ALPR_OCR_INTERVAL` = 0.35s (reduce carga y aumenta probabilidad de frames nítidos)
  - `ALPR_FRAMEQ_MAXSIZE` = 12 (cola de frames más grande, prioriza frames recientes)
  - `ALPR_CONFIDENCE_THRESHOLD` = 0.45 (umbral mínimo para aceptar lecturas directas)
  - `ALPR_CONSENSUS_REQUIRED` = 2 (cantidad de lecturas iguales en ventana para aceptar lecturas de baja confianza)

- Lógica de consenso y filtrado:
  - Buffer temporal (`vote_buffer`) y ventana de consenso que permite aceptar lecturas fiables por repetición cuando la confianza es baja.
  - Rechazo temprano de candidatos que no cumplen heurísticas básicas (longitud, presencia de letra y dígito).
  - Debounce/COOLDOWN preservado para evitar reenvíos rápidos del mismo registro.

- Mejora en detección y recorte de ROI (region of interest):
  - Nueva función `find_plate_roi` con estrategia mixta: cascade detector, franjas inferior/central y detección por contornos (filtrado por aspect ratio y área). Soporta placas anchas y compactas (motos).
  - `crop_below_blue` recorta la franja inferior cuando se detecta la banda azul Mercosur, evitando que EasyOCR lea la leyenda superior ("REPUBLICA ARGENTINA").

- Soporte para placas de motos y formatos en dos filas:
  - Regex ampliado para cubrir variantes compactas y combinaciones top-bottom.
  - Construcción de texto combinando left->right y top->bottom (se elige la forma más informativa).
  - Ajustes en padding y aspecto para capturar placas casi cuadradas.

- Robustez y logging:
  - Manejo defensivo de la salida de EasyOCR (evita IndexError/TypeError al parsear resultados), orden seguro y cálculo de confianza.
  - Reducción del ruido en disco: ahora solo se guardan imágenes de evidencia cuando se acepta una placa y corresponde a ARGENTINA (ej. `accepted_plate_<GATE>_<PLATE>_<ts>.jpg`).
  - Se suprimen guardados masivos de ROIs no-matched o de baja confianza para evitar llenar disco.

- Corrección de comportamiento del worker:
  - El hilo OCR ya no finaliza tras aceptar una lectura; continúa procesando frames inmediatamente después de enviar el evento al backend.

- Variables de entorno relevantes para tuning:
  - `ALPR_OCR_INTERVAL`, `ALPR_FRAMEQ_MAXSIZE`, `ALPR_CONFIDENCE_THRESHOLD`, `ALPR_CONSENSUS_REQUIRED`, `ALPR_FORCE_OCR` (forzar OCR aun sin motion).

Recomendaciones operativas:
1. Reiniciar `alpr_service.py` tras desplegar estos cambios.
2. Si la cámara es un celular, fijar enfoque/exposure y bajar FPS (ej. 15 FPS) mejora notablemente la detección.
3. Para entornos muy ruidosos aumentar `ALPR_CONSENSUS_REQUIRED` a 3 o subir `ALPR_CONFIDENCE_THRESHOLD` a 0.6.

---

Mantener este changelog junto a la documentación principal para referencia rápida durante despliegues y debugging.
