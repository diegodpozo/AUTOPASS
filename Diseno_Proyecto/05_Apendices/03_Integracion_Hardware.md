# Integración con Hardware — AUTOPASS

## Arquitectura IoT

```
┌──────────────────┐      MQTT       ┌──────────────────┐
│  Backend         │◄────────────────►│  Broker MQTT     │
│  (FastAPI)       │   publish/sub    │  (HiveMQ Cloud)  │
└──────────────────┘                  └────────┬─────────┘
                                                │
                                                │ MQTT
                                                │
                    ┌───────────────────────────────────────────┐
                    │           ESP32 (firmware_esp32.ino)      │
                    ├───────────────────────────────────────────┤
                    │  - WiFi STA mode                          │
                    │  - MQTT Client (CallbackAPIVersion.V2)    │
                    │  - Suscrito a: parking/barrera/+/control │
                    │  - Publica en: parking/barrera/+/status   │
                    └──────────┬────────────────────────────────┘
                               │
               ┌───────────────┼───────────────────┐
               ▼               ▼                   ▼
       ┌────────────┐ ┌────────────┐ ┌────────────────────┐
       │ Servomotor │ │ Sensor     │ │ LCD 16x2 I2C      │
       │ (Barrera)  │ │ Ultrasónico│ │ (Mensajes conductor)│
       └────────────┘ └────────────┘ └────────────────────┘
```

## Componentes Hardware

| Componente | Modelo Sugerido | Función |
|------------|-----------------|---------|
| Microcontrolador | ESP32 (NodeMCU-32S) | Conexión WiFi, MQTT, control de periféricos |
| Servomotor | MG996R o SG90 | Abrir/cerrar barrera física |
| Sensor ultrasónico | HC-SR04 | Detectar paso del vehículo |
| Pantalla LCD | LCD 16x2 I2C | Mostrar mensajes al conductor |
| Fuente de poder | 5V 2A | Alimentación del ESP32 y periféricos |

## Firmware ESP32

**Archivo:** `firmware_esp32/firmware_esp32.ino`

### Funcionamiento

1. **Conexión**: Se conecta a WiFi y al broker MQTT
2. **Suscripción**: Escucha en tópicos de control (entrada/salida)
3. **Comando "OPEN"**: 
   - Activa servomotor para levantar barrera
   - Muestra mensaje en LCD ("PASE", "BIENVENIDO")
4. **Sensor ultrasónico**: 
   - Monitorea continuamente distancia
   - Detecta cuando el vehículo pasó (distancia libre nuevamente)
5. **Cierre automático**: 
   - Cuando el vehículo termina de pasar, cierra la barrera
   - Por seguridad, cierre automático después de X segundos

### Tópicos MQTT

| Tópico | Dirección | Propósito |
|--------|-----------|-----------|
| `parking/barrera/entrada/control` | Backend → ESP32 | Comando: "OPEN" para entrada |
| `parking/barrera/salida/control` | Backend → ESP32 | Comando: "OPEN" para salida |
| `parking/barrera/+/status` | ESP32 → Backend | Estado: "OPENING", "OPEN", "CLOSING", "CLOSED" |

### Configuración en `.env`
```env
MQTT_TOPIC_ENTRADA=parking/barrera/entrada/control
MQTT_TOPIC_SALIDA=parking/barrera/salida/control
```

## Configuración de Cámaras IP

### Formato de Source
```
# RTSP (recomendado para transmisión continua)
rtsp://user:password@192.168.1.100:554/stream1

# HTTP MJPEG
http://192.168.1.100:8080/video

# Android/IP Webcam app
http://192.168.1.100:8080/video
```

### Configuración desde Dashboard
1. Ir a Ajustes > Monitoreo
2. Agregar cámara con:
   - Nombre descriptivo
   - Tipo: Entrada/Salida/Vigilancia
   - Source URL (RTSP/HTTP)
   - Sucursal
3. Presionar Play (▶) para iniciar el servicio ALPR

### Almacenamiento en DB
```python
class ParkingCamera(Base):
    __tablename__ = "parking_cameras"
    id = Column(Integer, primary_key=True)
    nombre = Column(String(100))       # "Cámara Entrada Principal"
    tipo = Column(String(50))          # "entrada", "salida", "vigilancia"
    source = Column(String(500))       # URL RTSP/HTTP
    sucursal = Column(String(100))     # Sucursal asignada
    activa = Column(Boolean, default=True)
```

## Flujo de Apertura de Barrera

```
1. ALPR detecta patente válida
2. Backend valida entrada/salida (AccessService)
3. Si OK → MQTT publish "OPEN" al tópico correspondiente
4. ESP32 recibe comando:
   a. Activa servomotor (ángulo 0° → 90°)
   b. Muestra "PASE" en LCD
   c. Inicia monitoreo ultrasónico
5. Vehículo pasa (sensor detecta distancia > umbral)
6. ESP32 cierra barrera (ángulo 90° → 0°)
7. Publica estado "CLOSED" en tópico status
8. Backend registra el evento (si aplica)
```

## Seguridad del Hardware

- **WiFi**: Usar WPA2-PSK en la red local
- **MQTT**: Si el broker lo soporta, usar autenticación TLS
- **Red Aislada**: Idealmente las cámaras y ESP32 en VLAN separada
- **Firmware**: Mantener actualizado el firmware del ESP32
- **Reset Físico**: El ESP32 debe tener botón de reset para recovery
