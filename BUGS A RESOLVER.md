# BUGS A RESOLVER

Registro de problemas detectados pero **NO corregidos**, pendientes de implementación.

Este documento no aplica cambios en el código: solo describe el problema, su impacto, dónde está y cómo corregirlo.

- **Última revisión**: 2026-10-05, contra `7536e12` (`fix(security): proteger heartbeat y aislar pisos por sede`), que está en `v9.34.80 + 2`.
- **Estado**: 1 bug funcional y 4 problemas de seguridad abiertos, 1 cerrado y 1 parcialmente cerrado.

---

## 1. Bug funcional

### 1.1 `updateFloorCapacity` no está expuesto en `window`

| | |
|---|---|
| **Severidad** | Media (funcional, solo bloquea una acción del panel) |
| **Estado** | Pendiente (sin cambios desde el reporte original) |
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

Los atributos `onclick` inline se resuelven contra el objeto global `window`, no contra el scope del módulo ES. En `static/js/dashboard.js` la sección "9. PISOS DE SUCURSAL" expone todos los handlers vecinos (`openAddFloorModal`, `deleteFloor`, `updatePBCapacity`, `savePBCapacity`, `toggleLevelEdit`), pero **`updateFloorCapacity` sigue fuera de la lista**. Verificado sobre el código actual: no aparece en `dashboard.js`.

**Corrección sugerida**

Agregar la asignación en `static/js/dashboard.js`, junto al resto de los handlers de pisos:

```js
window.updateFloorCapacity = admin.updateFloorCapacity;
```

**Idea de fondo (DRY)**

Los `onclick` inline dependen de que cada handler se registre a mano en `window`, y eso ya falló una vez. Conviene evitar el `onclick` inline y usar delegación de eventos con `data-action` + `data-id`, de modo que agregar un handler nuevo no requiera tocar dos archivos.

---

## 2. Seguridad

### 2.1 `.env.example` trackeado con las credenciales reales de producción

| | |
|---|---|
| **Severidad** | **Crítica** |
| **Estado** | Pendiente (el `.env` sepurgó, pero los secretos reaparecieron en `.env.example`) |
| **Componente** | Git / infraestructura |

**Descripción**

El reporte original señalaba que `.env` estaba trackeado con secretos reales. Eso **ya se corrigió**: `.env` ya no está en el índice (`git ls-files .env` vacío) y los commits que lo habían agregado ya no son alcanzables desde `origin/main`, o sea que el historial fue reescrito y quedó purgado.

**El problema es que los secretos no se eliminaron: se movieron de archivo.** `.env.example` **sí está trackeado** y contiene los mismos valores que el `.env` de producción, verificado carácter por carácter:

| Clave | Valor en `.env.example` | ¿Igual al de producción? |
|---|---|---|
| `SECRET_KEY` | clave de ejemplo hardcodeada (`.env.example:2`) | **Sí, idéntica a producción** |
| `DATABASE_URL` | `postgresql://neondb_owner:<password>@ep-silent-math-acirnekl.sa-east-1.aws.neon.tech/neondb` | **Sí, idéntica** |
| `MQTT_BROKER` | `broker.hivemq.com` (puerto 1883, sin credenciales) | Config por defecto |

**Agravantes**

1. `scripts/setup.ps1:94-96` copia `.env.example` sobre `.env` de forma automática:

   ```powershell
   if (Test-Path ".env.example") {
       Copy-Item ".env.example" ".env"
   ```

   Toda instalación nueva arranca con la base de datos real y la clave de firma real.

2. El guard que existe contra claves de ejemplo **no detecta este valor**. `main.py:35` y `main.py:39` solo comparan contra el default de `core/config.py:83`:

   ```python
   if settings.ENVIRONMENT == "production" and settings.SECRET_KEY == "tu_super_secreto_para_produccion":
   ```

   El valor que trae `.env.example` no es el default de `core/config.py`, así que pasa el guard sin problema.

**Impacto**

- Con `SECRET_KEY` conocida se pueden **firmar tokens JWT de administrador válidos** durante `ACCESS_TOKEN_EXPIRE_MINUTES` (1440 min = 24 h), sin credenciales y sin tocar la base de datos. El guard de `jti` revocados es en memoria y se limpia al reiniciar.
- Con el password de Neon se accede **directamente a la base de datos de producción** desde internet.
- `broker.hivemq.com:1883` es un broker público: los topics de barreras son legibles y publicables por cualquiera (ver 2.2).

**Corrección sugerida**

1. **Rotar ya mismo** la clave de firma de JWT y el password de Neon. Rotar `SECRET_KEY` invalida todas las sesiones activas.
2. Dejar `.env.example` solo con placeholders inequívocos:
   ```
   SECRET_KEY=cambiar_por_un_secreto_aleatorio_de_64_chars
   DATABASE_URL=postgresql://usuario:password@host:5432/dbname
   MQTT_BROKER=tu-broker-local
   ```
3. Ampliar el guard de `main.py` para que rechace **cualquier** `SECRET_KEY` conocido como de ejemplo, no solo un literal. Lo más simple es exigir longitud mínima y entropía, en vez de comparar contra una blacklist.
4. Purgar los secretos del historial actual (`.env.example` entra en todo commit desde que se agregó).
5. Auditar en Neon y en MercadoPago si hubo accesos distintos al esperado.

---

### 2.2 Broker MQTT público, sin autenticación ni TLS

| | |
|---|---|
| **Severidad** | Alta |
| **Estado** | Pendiente (sin cambios: `core/mqtt.py` intacto) |
| **Componente** | `core/mqtt.py`, `.env.example` |

**Descripción**

`core/mqtt.py` sigue exactamente igual, sin credenciales:

```python
def get_mqtt_client():
    client = mqtt.Client(callback_api_version=CallbackAPIVersion.VERSION2)
    return client
```

No se llama a `username_pw_set()`, ni a `tls_set()`, ni se fija `client_id`. Y `.env.example` ahora shippea como configuración por defecto un broker público:

```
MQTT_BROKER=broker.hivemq.com
MQTT_PORT=1883
```

Cualquiera suscripto a ese broker puede publicar en `MQTT_TOPIC_ENTRADA` / `MQTT_TOPIC_SALIDA` y **abrir la barrera o simular el paso de un vehículo**, sin necesidad de tocar la aplicación.

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

Además, restringir los ACL del broker para que el usuario de AUTOPASS solo pueda publicar en los topics de su propia sede, y cambiar el default de `.env.example` a un broker local.

---

### 2.3 `LOCAL_ADMIN` sin scope de sede (resuelto solo para sucursales y pisos)

| | |
|---|---|
| **Severidad** | Alta |
| **Estado** | **Parcialmente corregido** |
| **Componente** | `core/security.py`, `routes/admin/*` |

**Corrección aplicada en el remoto**

Se agregó `validate_local_admin_branch(admin, branch_nombre)` en `core/security.py`, que compara `admin.sucursal` contra la del recurso usando normalización, con `ADMIN` global exento. Se aplica en `routes/admin/branches.py` (4 usos: sucursal y pisos).

**Lo que sigue abierto**

`validate_local_admin_branch` **solo se usa en `branches.py`**. Los demás routers admin dependen del rol y nada más:

| Router | Endpoints con dependencia de rol | Validación de sede |
|---|---|---|
| `branches.py` | 4 | **Sí** (4 usos) |
| `operations.py` | 5 | No |
| `promotions.py` | 6 | No |
| `reservations.py` | 11 | No |
| `settings.py` | 3 | No |
| `support.py` | 6 | No |
| `users.py` | 9 | No |
| `virtual_time.py` | 7 | No |

`get_local_manager` y `get_operational_user` en `core/security.py` siguen validando únicamente el rol. El filtrado por sede continúa siendo **puntual y manual** en algunos endpoints (por ejemplo `routes/system/video.py` y `routes/system/health.py`), que es exactamente el patrón que ya produjo un bug.

**Impacto**

Un `LOCAL_ADMIN` de la sede *Centro* puede operar sobre sucursales ajenas en promociones, reservas, usuarios, settings y tickets.

**Corrección sugerida**

1. Aplicar `validate_local_admin_branch` (o un `Depends` equivalente) en los routers que quedaron pendientes, empezando por `promotions.py`, `settings.py` y `reservations.py`, que son los de mayor impacto.
2. Agregar un test parametrizado que recorra los routers y falle si algún endpoint con `{gate_id}` / `{camera_id}` / sede en el path no llama a la validación.

---

### 2.4 `/camera-reading/{gate_id}` sigue sin autenticación

| | |
|---|---|
| **Severidad** | Media |
| **Estado** | **Mitad corregido** (`/heartbeat` arreglado, `/camera-reading` abierto) |
| **Componente** | `routes/system/health.py`, `routes/system/cameras.py` |

**Lo que ya se corrigió**

`POST /heartbeat` ahora está protegido con la dependencia de nodo ALPR:

```python
@router.post("/heartbeat")
def alpr_heartbeat(gate_id: str, _: None = Depends(require_alpr_node)):
```

Con eso se cierra el falseo del monitoreo y el crecimiento sin límite de `ALPR_HEARTBEATS`.

**Lo que sigue abierto**

`routes/system/cameras.py:325`:

```python
@router.post("/camera-reading/{gate_id}")
def notify_camera_reading(gate_id: str, db: Session = Depends(get_db)):
```

Notifica al dashboard que una cámara está leyendo. **Todos** los demás endpoints del router (`/camera-config`, `/cameras`, `/camera-service/{gate_id}/{action}`) usan `Depends(get_operational_user)`; este sigue afuera.

**Corrección sugerida**

- `notify_camera_reading`: agregar `Depends(require_alpr_node)`, por consistencia con `/heartbeat` — quien reporta la lectura es el nodo ALPR, no un operador.
- Si además debe poder dispararlo un operador manual, sumar `get_operational_user` y validar que el `gate_id` pertenezca a su sede.

---

### 2.5 Webhook de Mercado Pago sin verificación de firma

| | |
|---|---|
| **Severidad** | Media (defensa en profundidad) |
| **Estado** | Pendiente (sin cambios) |
| **Componente** | `routes/user/mercadopago.py` |

**Descripción**

`mp_webhook` sigue procesando el cuerpo de la petición directamente, sin validar la firma que MercadoPago envía en los headers `x-signature` / `x-request-id` (HMAC SHA256 con `MP_WEBHOOK_SECRET`). No hay referencia a `x-signature` ni a `MP_WEBHOOK_SECRET` en el código.

**Mitigación ya existente**

`confirm_payment` **no se fía del cuerpo del webhook**: re-consulta `/v1/payments/{id}` contra la API de Mercado Pago y de ahí toma el `external_reference` autoritativo, valida que el estado sea `approved` y que el monto coincida. Por eso **no hay riesgo de acreditar un pago falso**; el daño real se limita a poder disparar consultas a la API de MP (limitado a `60/minute`) y a generar ruido en los logs.

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

Agregar `MP_WEBHOOK_SECRET` a la configuración y a `.env.example` como placeholder.

---

### 2.6 Secretos encore en un branch local

| | |
|---|---|
| **Severidad** | Baja mientras el branch sea local |
| **Estado** | Pendiente |
| **Componente** | Git local |

**Descripción**

Durante la sincronización con el remoto se creó el branch `backup/local-antes-de-pull`, que conserva la historia previa a la reescritura y por lo tanto **todavía contiene los commits con `.env` y los secretos originales**.

Un branch local no sale de la máquina, pero basta con un `git push --all` o un `git push --mirror` accidental para publicarlos.

**Corrección sugerida**

Rotar los secretos primero (ver 2.1) y después eliminar el branch:

```bash
git branch -D backup/local-antes-de-pull
git reflog expire --expire=now --all
git gc --prune=now
```

---

## Resumen

| # | Tipo | Severidad | Estado | Ubicación |
|---|---|---|---|---|
| 1.1 | Funcional | Media | Pendiente | `static/js/dashboard.js` |
| 2.1 | Seguridad | **Crítica** | Pendiente | `.env.example` (secretos de producción) |
| 2.2 | Seguridad | Alta | Pendiente | `core/mqtt.py`, `.env.example` |
| 2.3 | Seguridad | Alta | Parcial | `core/security.py`, 7 routers admin |
| 2.4 | Seguridad | Media | Parcial | `routes/system/cameras.py:325` |
| 2.5 | Seguridad | Media | Pendiente | `routes/user/mercadopago.py` |
| 2.6 | Higiene Git | Baja | Pendiente | branch `backup/local-antes-de-pull` |

**Orden de ataque sugerido**: 2.1 (rotar credenciales ya, no depende de código y es lo más urgente) → 2.2 → 2.3 (completar los routers que faltan) → 2.4 → 2.5 → 2.6 → 1.1.

---

## Cerrados desde el reporte original

| Ítem | Commit | Qué se hizo |
|---|---|---|
| `.env` trackeado | reescritura de historial | `.env` salió del índice y del historial; se agregó `.env.example` (ver nota) |
| `/heartbeat` sin auth | `7536e12` | `Depends(require_alpr_node)` en `routes/system/health.py` |
| Aforo de pisos por sede | `7536e12` | `validate_local_admin_branch` en `core/security.py`, aplicado en `routes/admin/branches.py` |
| Bugs funcionales 1-6 | `0772e36` | Ver abajo |

**Nota sobre 2.1**: el cierre de `.env` no es completo. Los secretos reaparecieron en `.env.example`, que sigue trackeado, así que el ítem se mantiene abierto y con severidad crítica.

## Bugs funcionales ya corregidos

Los bugs funcionales 1 a 6 están resueltos y cubiertos por tests de regresión en `tests/test_bugfixes_funcionales.py`. Resumen:

1. `AccessService.exit_plate` fallaba con `UnboundLocalError` si la sede no tenía aforo configurado.
2. `AccessService.validate_qr` usaba `suc_short` sin inicializar cuando el `gate_id` no tenía `_`, y filtraba mensajes internos de error al cliente.
3. El checkout de Mercado Pago para estadías rechazaba pagos si la patente estaba en distinto formato (p. ej. `AB 123 CD` vs `AB123CD`).
4. `BillingService.process_payment` volvía a cobrar el extra por reserva vencida cada vez que se pasaba por caja.
5. Los puntos no se acreditaban al cobrar en caja si la patente venía normalizada (misma causa raíz que 3).
6. `HardwareService.trigger_barrier` asumía `SALIDA` ante un `gate_id` desconocido o ambiguo, pudiendo abrir la barrera incorrecta.

La causa raíz de 3 y 5 era la misma: la búsqueda de vehículos por patente no era tolerante a formato. Se resolvió en `repositories/vehicle_repository.py`, que ahora normaliza la patente en todas sus búsquedas.

**Suite actual**: 779 tests en verde.