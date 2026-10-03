# BUGS A RESOLVER

Registro de problemas detectados pero **NO corregidos**, pendientes de implementación.

Este documento no aplica cambios en el código: solo describe el problema, su impacto, dónde está y cómo corregirlo.

---

## 1. Bug funcional

### 1.1 `updateFloorCapacity` no está expuesto en `window`

| | |
|---|---|
| **Severidad** | Media (funcional, solo bloquea una acción del panel) |
| **Estado** | Pendiente |
| **Componente** | Frontend / panel de administración |

**Descripción**

Al editar la capacidad de un piso desde el panel de sucursales, el botón "Guardar" no hace nada y la consola del navegador muestra:

```
Uncaught ReferenceError: updateFloorCapacity is not defined
```

**Causa raíz**

`updateFloorCapacity` se exporta desde `static/js/modules/dashboard-admin-branches.js:28` y se invoca desde un atributo `onclick` inline en `static/js/modules/dashboard-admin-branches-floors.js:262`:

```html
<button ... onclick="updateFloorCapacity(${f.id})" ...>
```

Los atributos `onclick` inline se resuelven contra el objeto global `window`, no contra el scope del módulo ES. En `static/js/dashboard.js` la sección "9. PISOS DE SUCURSAL" (líneas 166-173) expone todos los handlers vecinos (`openAddFloorModal`, `deleteFloor`, `updatePBCapacity`, `savePBCapacity`, `toggleLevelEdit`), pero **`updateFloorCapacity` quedó fuera de la lista**.

**Corrección sugerida**

Agregar la asignación en `static/js/dashboard.js`, junto al resto de los handlers de pisos:

```js
window.updateFloorCapacity = admin.updateFloorCapacity;
```

**Idea de fondo (DRY)**

Los `onclick` inline dependen de que cada handler se registre a mano en `window`, y eso ya falló una vez. Conviene evitar el `onclick` inline y usar delegación de eventos con `data-action` + `data-id`, de modo que agregar un handler nuevo no requiera tocar dos archivos.

---

## 2. Seguridad

### 2.1 Credenciales reales versionadas en `.env`

| | |
|---|---|
| **Severidad** | Crítica |
| **Estado** | Pendiente |
| **Componente** | Git / infraestructura |

**Descripción**

`.env` está trackeado por Git pese a estar en `.gitignore:7`. El historial contiene credenciales reales:

- `MP_ACCESS_TOKEN` — token de producción de Mercado Pago (75 caracteres)
- `SMTP_PASSWORD` — contraseña real del servidor de correo (20 caracteres)
- `SECRET_KEY` — clave de firma de JWT, usada para emitir sesiones
- `DATABASE_URL` — credenciales de la base de datos (Neon/PostgreSQL; antes Turso/libSQL)
- `MP_WEBHOOK_URL`, `MP_PUBLIC_KEY`, `SMTP_USER`

**Commits donde entraron**

```
0b1bf19  chore: subir .env con credenciales de Turso (repo privado)
e8d331b  Integración completa de AUTOPASS (...)
```

**Impacto**

Cualquiera con acceso de lectura al repositorio (o cualquier clon suyo) obtiene el token de Mercado Pago y la clave de firma de JWT. Con `SECRET_KEY` se pueden **forjar tokens de administrador válidos** durante toda la ventana de `ACCESS_TOKEN_EXPIRE_MINUTES`, sin necesidad de credenciales. Con `MP_ACCESS_TOKEN` se pueden operar cobros reales.

**Corrección sugerida**

1. **Rotar ya mismo** `SECRET_KEY`, `MP_ACCESS_TOKEN` y `SMTP_PASSWORD` en los respectivos servicios. Rotar `SECRET_KEY` invalida todas las sesiones activas.
2. Eliminar `.env` del índice de Git (`git rm --cached .env`) y mantener solo `.env.example` con valores de ejemplo.
3. Reescribir el historial (`git filter-repo` / BFG) para sacar los secretos de todos los commits.
4. Si el repositorio fue compartido o el sitio estuvo expuesto, auditar en MercadoPago y en el servidor SMTP.
5. Rotar también las credenciales de la base de datos.

**Nota**: si el repositorio nunca salió de la máquina del equipo y el token sigue sin usarse fuera de producción, el paso 3 es opcional, pero los pasos 1, 2 y 5 no lo son.

---

### 2.2 Broker MQTT sin autenticación ni TLS

| | |
|---|---|
| **Severidad** | Alta |
| **Estado** | Pendiente |
| **Componente** | `core/mqtt.py` |

**Descripción**

`core/mqtt.py:4-11` crea el cliente sin credenciales:

```python
def get_mqtt_client():
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    return client
```

No se llama a `username_pw_set()`, ni a `tls_set()`, ni se fija `client_id`. Cualquiera que alcance el broker puede publicar en los topics de entrada/salida (`MQTT_TOPIC_ENTRADA` / `MQTT_TOPIC_SALIDA`) y **abrir la barrera o simular el paso de un vehículo**.

El puerto viene de `MQTT_PORT` (1883 por defecto), que es el puerto sin cifrar.

**Corrección sugerida**

```python
client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2,
    client_id=settings.MQTT_CLIENT_ID,
)
client.username_pw_set(settings.MQTT_USER, settings.MQTT_PASSWORD)
client.tls_set(ca_certs=settings.MQTT_CA_CERTS)
client.tls_insecure_set(False)
```

Además, restringir los ACL del broker para que el usuario de AUTOPASS solo pueda publicar en los topics de su propia sede.

---

### 2.3 `LOCAL_ADMIN` puede operar sobre cualquier sede

| | |
|---|---|
| **Severidad** | Alta |
| **Estado** | Parcial (`routes/admin/branches.py`: pisos protegidos por scope de sede. Resta revisar otros endpoints que usan get_local_manager) |
| **Componente** | `core/security.py`, `routes/admin/branches.py`, otros routers que usan `get_local_manager` |

**Descripción**

`get_local_manager` y `get_operational_user` solo validan el **rol**, nunca la **sede**. El filtrado por sede se hace de forma **puntual y manual** en algunos endpoints. Como `get_local_manager` es una dependencia que no conoce el recurso sobre el que opera (recibe solo al usuario), no es posible forzar el scope a nivel de dependencia para todos los casos sin cambiar la firma de rutas que pasan ids.

**Impacto**

Un `LOCAL_ADMIN` de la sede *Centro* podía operar pisos (`add_floor`, `delete_floor`, `update_floor_capacity`) de otra sede (caso concreto detectado).

**Corrección aplicada**

- En `core/security.py`: agregado `validate_local_admin_branch(admin, branch_nombre)` (usa `normalize_branch_name` para comparar de forma insensible a mayúsculas/espacios).
- En `routes/admin/branches.py`: se invoca el validador en los 3 endpoints de pisos (add/delete/update), recuperando la sucursal del piso/sucursal objetivo antes de aplicar cambios. Se mantuvieron `get_super_admin` para operaciones a nivel sucursal (crear/editar/eliminar sucursales, activar/desactivar) según criterio existente.

**Pruebas agregadas:** 6 tests en `tests/test_admin_branches.py` que verifican 403 ante otra sede, éxito en propia sede, ADMIN global sin restricciones y comparación normalizada.

**Pendiente**

Revisar sistemáticamente endpoints que usan `get_local_manager` sin validar sede (ej. `virtual_time` es global, revisar `promotions.py`, `settings.py`, `users.py`, `reports.py`) y aplicar validación explícita por recurso cuando corresponda.

---

### 2.4 Endpoints de sistema accesibles sin autenticación

| | |
|---|---|
| **Severidad** | Media |
| **Estado** | Parcial (`/heartbeat` corregido; `/camera-reading` sigue pendiente) |
| **Componente** | `routes/system/cameras.py`, `routes/system/health.py` |

**Descripción**

Dos endpoints mutan estado global sin ninguna dependencia de autenticación:

**`POST /camera-reading/{gate_id}`** — `routes/system/cameras.py` (PENDIENTE)

```python
@router.post("/camera-reading/{gate_id}")
def notify_camera_reading(gate_id: str, db: Session = Depends(get_db)):
```

Notifica al dashboard que una cámara está leyendo. **Todos** los demás endpoints del router (`/camera-config`, `/cameras`, `/camera-service/{gate_id}/{action}`) sí usan `Depends(get_operational_user)`; este quedó afuera. Verificado sobre el código actual: sigue sin dependencia de autenticación.

**`POST /heartbeat`** — `routes/system/health.py` (CORREGIDO)

Antes mutaba `ALPR_HEARTBEATS` sin ninguna comprobación:

```python
def alpr_heartbeat(gate_id: str):
    ALPR_HEARTBEATS[gate_id] = datetime.datetime.now()
```

Cualquiera podía marcar un portón como `ONLINE` en el panel de salud, falseando el monitoreo operativo, y spamming `gate_id` distintos hacía crecer el diccionario sin límite.

**Corrección aplicada**: se agregó la dependencia `require_alpr_node` que ya existía en `core/alpr_security.py:23` y que se usa igual en el resto de los endpoints de nodo ALPR:

```python
def alpr_heartbeat(gate_id: str, _: None = Depends(require_alpr_node)):
```

Con `ALPR_NODE_SECRET` configurado exige el secreto por header `x-node-secret` o query `node_secret` (comparación en tiempo constante); sin secreto configurado cae al criterio de red local/privada. Cubierto por 4 tests en `tests/test_system_health.py`, incluidos el rechazo con secreto ausente y con secreto incorrecto.

Nota: al verificar este bug se constató que ningún componente del repositorio envía heartbeats (ni el backend, ni `firmware_arduino_uno.ino`, ni `firmware_esp32.ino`, ni `scripts/arduino_bridge.py`, que es un bridge MQTT). El endpoint queda protegido sin riesgo de romper un cliente existente, pero mientras ningún nodo lo llame el indicador de liveness del panel de salud no puede marcar `ONLINE`.

**Corrección pendiente**

- `notify_camera_reading`: agregar `Depends(get_operational_user)` y validar que el `gate_id` pertenezca a la sede del usuario.

---

### 2.5 Webhook de Mercado Pago sin verificación de firma

| | |
|---|---|
| **Severidad** | Media (defensa en profundidad) |
| **Estado** | Pendiente |
| **Componente** | `routes/user/mercadopago.py` |

**Descripción**

`mp_webhook` (`routes/user/mercadopago.py:69-97`) procesa el cuerpo de la petición directamente, sin validar la firma que MercadoPago envía en los headers `x-signature` / `x-request-id` (HMAC SHA256 con `MP_WEBHOOK_SECRET`).

**Mitigación ya existente**

`confirm_payment` (`services/mercadopago_service.py`) **no se fía del cuerpo del webhook**: re-consulta `/v1/payments/{id}` contra la API de Mercado Pago, y de ahí toma el `external_reference` autoritativo, valida que el estado sea `approved` y que el monto coincida con lo esperado. Por eso **no hay riesgo de acreditar un pago falso** — el daño real se limita a poder disparar consultas a la API de MP (limitado a `60/minute` por el rate limit) y a generar ruido en los logs.

**Corrección sugerida**

Agregar la validación de firma antes de procesar, según la documentación de MercadoPago:

```python
ts = request.headers.get("x-request-id", "")
sign = request.headers.get("x-signature", "")
manifest = f"id:{data_id};request-id:{ts};ts:{ts};"
if not hmac.compare_digest(
    hmac.new(settings.MP_WEBHOOK_SECRET.encode(), manifest.encode(), hashlib.sha256).hexdigest(),
    sign.split("sha256=")[-1],
):
    raise HTTPException(status_code=403, detail="Firma inválida")
```

Agregar `MP_WEBHOOK_SECRET` a la configuración y al `.env.example`.

---

## Resumen

| # | Tipo | Severidad | Archivo principal |
|---|---|---|---|
| 1.1 | Funcional | Media | `static/js/dashboard.js` |
| 2.1 | Seguridad | **Crítica** | `.env` (historial de Git) |
| 2.2 | Seguridad | Alta | `core/mqtt.py` |
| 2.3 | Seguridad | Alta | `core/security.py` |
| 2.4 | Seguridad | Media | `routes/system/cameras.py` (`/heartbeat` ya corregido) |
| 2.5 | Seguridad | Media | `routes/user/mercadopago.py` |

**Orden de ataque sugerido**: 2.1 (rotar credenciales ya, es lo más urgente y no depende de código) → 2.2 → 2.3 → 2.4 → 2.5 → 1.1.

---

## Bugs ya corregidos

Los bugs funcionales 1 a 6 ya están resueltos y cubiertos por tests de regresión en `tests/test_bugfixes_funcionales.py`. Resumen:

1. `AccessService.exit_plate` fallaba con `UnboundLocalError` si la sede no tenía aforo configurado.
2. `AccessService.validate_qr` usaba `suc_short` sin inicializar cuando el `gate_id` no tenía `_`, y filtraba mensajes internos de error al cliente.
3. El checkout de Mercado Pago para estadías rechazaba pagos si la patente estaba en distinto formato (p. ej. `AB 123 CD` vs `AB123CD`).
4. `BillingService.process_payment` volvía a cobrar el extra por reserva vencida cada vez que se pasaba por caja.
5. Los puntos no se acreditaban al cobrar en caja si la patente venía normalizada (misma causa raíz que 3).
6. `HardwareService.trigger_barrier` asumía `SALIDA` ante un `gate_id` desconocido o ambiguo, pudiendo abrir la barrera incorrecta.

La causa raíz de 3 y 5 era la misma: la búsqueda de vehículos por patente no era tolerante a formato. Se resolvió en `repositories/vehicle_repository.py`, que ahora normaliza la patente en todas sus búsquedas.
