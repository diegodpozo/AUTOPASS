# F04II - GUÍA DETALLADA: TELEMETRÍA, COMANDOS REMOTOS Y AUDITORÍA DE HARDWARE (MVP 2)

Este documento detalla el diseño, la arquitectura y los pasos para implementar las tareas pendientes del hito **F04 (Comunicación y Control de Hardware)** en su versión **MVP 2**, completamente adaptado a la arquitectura modular y las novedades en tiempo real de la versión **v9.1.5**.

El objetivo es lograr un control bidireccional completo y seguro entre el backend de AUTOPASS y las placas controladoras IoT (ESP32) de las barreras físicas.

---

## 1. HITOS DE HARDWARE MVP 2 (CONTEXTO)
En el MVP 1 se implementó un flujo unidireccional básico:
1. El ALPR detecta patente o QR y envía la petición a [AccessService](file:///C:/xampp/htdocs/AUTOPASS/services/access_service.py#L12).
2. Si el acceso es autorizado, el backend publica el comando `OPEN` en el tópico de control.
3. El microcontrolador ESP32 recibe el comando por suscripción y acciona el servomotor para abrir la barrera, cerrándola automáticamente después de una espera temporizada.

El **MVP 2** requiere robustecer este sistema en tres aspectos críticos:
* **T175b (Telemetría):** El hardware debe reportar periódicamente su estado físico, conectividad y lecturas de sensores al servidor.
* **T175c (Comandos Remotos Bidireccionales):** Además de abrir la barrera (`OPEN`), el backend debe ser capaz de forzar el cierre inmediato (`CLOSE`) por razones operativas o de seguridad.
* **T175d (Auditoría de Eventos):** Registro permanente en base de datos de cada acción del hardware para contrastarla con las autorizaciones de la API (detección de fraudes/evasiones).

---

## 2. T175b - PROTOCOLO DE COMUNICACIÓN MQTT PARA TELEMETRÍA

La telemetría permite que el backend conozca el estado real de cada dispositivo físico sin necesidad de realizar peticiones activas (polling).

### A. Tópicos de Telemetría
Cada sede publica su telemetría en un tópico estructurado:
`parking/barrera/<nombre_sede>_<tipo_barrera>/status`

*   **Entrada:** `parking/barrera/ituzaingo_entrada/status`
*   **Salida:** `parking/barrera/ituzaingo_salida/status`

### B. Formato de Mensaje (JSON Payload)
El ESP32 debe publicar a intervalos regulares (ej. cada 10 segundos) o inmediatamente ante un cambio de estado:

```json
{
  "device_id": "ESP32_ITUZAINGO_ENTRADA",
  "sucursal": "ITUZAINGO",
  "tipo": "ENTRADA",
  "status_barrera": "CLOSED",      // "OPEN", "CLOSED", "OPENING", "CLOSING"
  "sensor_distancia_cm": 145.2,    // Distancia medida por el sensor ultrasónico HC-SR04
  "wifi_rssi": -68,                // Nivel de señal WiFi en dBm (diagnóstico de red)
  "uptime_segundos": 1420,
  "timestamp": "2026-06-19T12:30:00"
}
```

### C. Implementación en el Backend y Sincronización WebSockets (v9.1.5)
Para capturar estos eventos, el cliente MQTT en [core/mqtt.py](file:///C:/xampp/htdocs/AUTOPASS/core/mqtt.py) debe configurarse para suscribirse a los tópicos de estado al arrancar en [main.py](file:///C:/xampp/htdocs/AUTOPASS/main.py#L50-L51).

Además, en la versión **v9.1.5**, la comunicación física se vincula con la interfaz web en tiempo real: al procesar un evento de acceso, [AccessService](file:///C:/xampp/htdocs/AUTOPASS/services/access_service.py) utiliza [NotificationService](file:///C:/xampp/htdocs/AUTOPASS/services/notification_service.py) para enviar actualizaciones de aforo mediante WebSockets (`/parking/ws`) a todos los clientes web en tiempo real.

#### Integración en el arranque (Suscripción):
```python
# EN main.py DENTRO DE startup_event()
mqtt_client.subscribe("parking/barrera/+/status")
mqtt_client.on_message = procesar_mensaje_telemetria
```

#### Callback de Procesamiento de Telemetría:
El callback interpreta el mensaje y notifica de forma reactiva al frontend si hay cambios en el aforo físico o alertas del hardware:
```python
# EN core/mqtt.py O EN EL SERVICIO DE NOTIFICACIONES
def procesar_mensaje_telemetria(client, userdata, msg):
    import json
    from core.database import SessionLocal
    from services.notification_service import NotificationService
    # LOG EN MAYUSCULAS Y SIN ACENTOS SEGUN REGLAS GLOBALES
    print(f"[MQTT TELEMETRIA] MENSAJE RECIBIDO EN TO PICO: {msg.topic}")
    
    try:
        data = json.loads(msg.payload.decode('utf-8'))
        sucursal_norm = data.get("sucursal")
        
        # Opcional: Si se detecta cambio de estado físico en la barrera
        # se notifica a los dashboards vía WebSockets
        db = SessionLocal()
        try:
            NotificationService.notify_occupancy_change(db, sucursal_norm)
        finally:
            db.close()
            
    except Exception as e:
        print(f"[MQTT ERROR] ERROR AL PROCESAR TELEMETRIA: {e}")
```

---

## 3. T175c - IMPLEMENTACIÓN DE COMANDOS REMOTOS (`OPEN` / `CLOSE`)

El control remoto permite forzar acciones inmediatas en la barrera desde la interfaz web o por automatismos del backend.

### A. Payload de Comando Remoto (Backend -> ESP32)
Publicado en `parking/barrera/<sede>_<tipo>/control`:

```json
{
  "command": "CLOSE",        // "OPEN" o "CLOSE"
  "method": "MANUAL_OP",     // "ALPR", "QR", o "MANUAL_OP" (Operador)
  "staff_id": 1,             // ID del usuario de cabina que ejecutó la acción
  "sucursal": "ITUZAINGO",
  "timestamp": "2026-06-19T12:30:05"
}
```

### B. Implementación en el Firmware (ESP32 / Arduino C++)
El firmware en el ESP32 debe expandir su lógica para procesar de forma diferenciada el comando `CLOSE`, cancelando cualquier bucle activo de paso de vehículo.

#### Ejemplo de Estructura de Callback C++ para el ESP32:
```cpp
void callback(char* topic, byte* payload, unsigned int length) {
  // Convertir el payload en un JSON legible
  StaticJsonDocument<256> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  
  if (error) {
    Serial.println("ERR: ERROR AL PARSEAR JSON DE COMANDO");
    return;
  }
  
  const char* command = doc["command"];
  const char* plate = doc["plate"] | "MANUAL";
  
  if (String(command) == "OPEN") {
    Serial.println("CMD: ABRIENDO BARRERA DESDE BACKEND");
    openBarrier(plate);
  } 
  else if (String(command) == "CLOSE") {
    Serial.println("CMD: FORZANDO CIERRE DE BARRERA");
    closeBarrier();
  }
}

void openBarrier(String info) {
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("BIENVENIDO!");
  lcd.setCursor(0, 1);
  lcd.print(info);
  
  barrierServo.write(90); // Abre la barrera física (90 grados)
  barrierOpen = true;
  
  // Enviar confirmacion de estado por el canal de telemetría
  publicarEstado("OPEN");
}

void closeBarrier() {
  barrierServo.write(0); // Cierra la barrera física (0 grados)
  barrierOpen = false;
  mostrarAforoBase();
  
  // Enviar confirmacion de estado por el canal de telemetría
  publicarEstado("CLOSED");
}
```

*Nota: La lógica del sensor de ultrasonido para el auto-cierre debe estar programada de tal forma que un comando remoto `CLOSE` tenga mayor prioridad y pueda interrumpir cualquier espera de `checkVehiclePassed()` mediante banderas de estado (`barrierOpen = false`).*

---

## 4. T175d - SISTEMA DE LOGS DE EVENTOS DE HARDWARE PARA AUDITORÍA

Para garantizar la seguridad de la sede, evitar la evasión de pagos y auditar el comportamiento del personal, se deben registrar de forma independiente los eventos del hardware.

### A. Modelo de Base de Datos para Auditoría de Hardware
Se propone agregar la siguiente estructura en [models/parking.py](file:///C:/xampp/htdocs/AUTOPASS/models/parking.py) o crear un archivo modelo separado para registrar telemetría y diagnósticos físicos:

```python
from sqlalchemy import Column, Integer, String
from core.database import Base

class HardwareAuditLog(Base):
    """Logs de auditoría específicos de hardware y telemetría."""
    __tablename__ = "hardware_audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    sucursal = Column(String, nullable=False)
    device_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)   # 'OPEN_REQUEST', 'PHYSICAL_OPEN', 'PHYSICAL_CLOSE', 'SENSOR_OBSTACLE', 'WIFI_DISCONNECT'
    detalles = Column(String, nullable=True)       # Mensaje JSON o descripción
    fecha_hora = Column(String, nullable=False)    # Formato DD/MM/YYYY HH:MM
```

### B. Algoritmo de Detección de Fraude (Conciliación de Datos)
El sistema backend puede cruzar los datos de [AccessLog](file:///C:/xampp/htdocs/AUTOPASS/models/parking.py#L24) con los logs de hardware para detectar anomalías operativas:

1.  **Apertura Física sin Autorización API (Evasión):**
    *   *Escenario:* El sensor de telemetría detecta que la barrera cambió de estado a `OPEN` y luego a `CLOSED` midiendo la obstrucción del sensor ultrasónico, pero **no** se registra una petición autorizada por ALPR o QR en los últimos 30 segundos.
    *   *Resultado:* Se genera una alerta crítica de "APERTURA FÍSICA NO AUTORIZADA" en el historial de logs, y se notifica al instante al navegador del operador mediante WebSockets.
2.  **Atascamiento / Obstrucción de Barrera:**
    *   *Escenario:* La API envía comando `OPEN`. Pasan 60 segundos y la telemetría reporta que el sensor de distancia sigue marcando un objeto cercano (< 20 cm) o que la barrera no ha vuelto a su estado `CLOSED`.
    *   *Resultado:* Alerta visual de "BARRERA OBSTRUIDA" enviada al dashboard en tiempo real.
3.  **Pérdida de Conexión en Vivo:**
    *   *Escenario:* El backend no recibe mensajes de telemetría (Heartbeat) de `device_id` en un intervalo mayor a 30 segundos.
    *   *Resultado:* Marca el dispositivo como `OFFLINE` en el dashboard e inhabilita las alertas automáticas para esa barrera.

---

## 5. RECOMENDACIONES DE SEGURIDAD (IoT)

1.  **Autenticación en MQTT:** Aunque para desarrollo local se utiliza `broker.hivemq.com` en el puerto `1883` sin credenciales, para producción se debe configurar un broker local seguro (ej. Mosquitto) que requiera usuario y contraseña cifrados para el ESP32.
2.  **Mensaje de Última Voluntad (Last Will and Testament - LWT):** Configurar el cliente MQTT del ESP32 para registrar un mensaje LWT en el broker. Si el dispositivo pierde la conexión eléctrica o de red repentinamente, el broker publicará automáticamente un payload indicando `"status_barrera": "DISCONNECTED"` en el tópico de telemetría, permitiendo al backend alertar de inmediato.
