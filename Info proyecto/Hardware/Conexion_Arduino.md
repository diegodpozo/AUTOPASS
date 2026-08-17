# Guía de Conexión: Hardware Real (Arduino Uno / ESP32)

Esta guía explica cómo conectar microcontroladores al sistema de AUTOPASS para controlar barreras físicas con servomotores mediante USB Serial o MQTT.

- 📄 **Guía Detallada Arduino Uno (2 Servos - Entrada/Salida USB Serial & MQTT)**: Ver [`GUIA_ARDUINO_UNO.md`](file:///C:/Users/usuario.DESKTOP-P7MEQGK/Desktop/AUTOPASS/Info%20proyecto/Hardware/GUIA_ARDUINO_UNO.md)
- 📄 **Firmware Arduino Uno**: Ver [`firmware_arduino_uno.ino`](file:///C:/Users/usuario.DESKTOP-P7MEQGK/Desktop/AUTOPASS/Info%20proyecto/Hardware/firmware_arduino_uno.ino)

## Requisitos
- **Microcontrolador**: ESP32 (Recomendado) o ESP8266.
- **Actuador**: Servomotor (ej. SG90 o MG90S).
- **Cables**: Jumpers macho-hembra.
- **Alimentación**: USB o fuente externa de 5V.

## Esquema de Conexión
1. **Servo Rojo (VCC)** -> Pin 5V del ESP32.
2. **Servo Marrón/Negro (GND)** -> Pin GND del ESP32.
3. **Servo Naranja/Amarillo (Señal)** -> Pin GPIO 18 (o el que definas en el código).

## Código del Firmware
Sube el siguiente código usando el IDE de Arduino. Asegúrate de instalar las librerías `PubSubClient` y `ESP32Servo`.

```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <ESP32Servo.h>

// --- CONFIGURACIÓN ---
const char* ssid = "TU_WIFI_NAME";
const char* password = "TU_PASSWORD";
const char* mqtt_broker = "broker.hivemq.com";
const char* topic_entrada = "parking/barrera/entrada/control";
const char* topic_salida = "parking/barrera/salida/control";

Servo barrierServo;
WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  barrierServo.attach(18); // Pin de señal
  barrierServo.write(0); // Cerrado

  setup_wifi();
  client.setServer(mqtt_broker, 1883);
  client.setCallback(callback);
}

void callback(char* topic, byte* payload, unsigned int length) {
  String msg = "";
  for (int i = 0; i < length; i++) msg += (char)payload[i];

  if (msg.indexOf("OPEN") != -1) {
  Serial.println(">>> ABRIENDO BARRERA");
  barrierServo.write(90);
  delay(5000);
  barrierServo.write(0);
  Serial.println(">>> BARRERA CERRADA");
  }
}

void loop() {
  if (!client.connected()) reconnect();
  client.loop();
}

void setup_wifi() {
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
}

void reconnect() {
  while (!client.connected()) {
  if (client.connect("ParkingNode_01")) {
  client.subscribe(topic_entrada);
  client.subscribe(topic_salida);
  } else delay(5000);
  }
}
```

## Funcionamiento
1. El **ALPR** detecta la patente desde el celular.
2. El **Backend** valida y publica un mensaje en el broker MQTT.
3. El **Arduino** recibe el mensaje por Wi-Fi y mueve el **Servo**.
4. La barrera permanece abierta 5 segundos y se cierra automáticamente.
