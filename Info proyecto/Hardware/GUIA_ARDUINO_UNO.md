# 🛠️ Guía Completa de Conexión: Arduino Uno con 2 Servomotores para AUTOPASS

Esta guía describe el esquema de conexión física, el código firmware simplificado para la placa **Arduino Uno**, y los flujos de integración para probar la apertura y cierre de las **Barreras de Entrada y Salida** desde el sistema **AUTOPASS (v10.0.0)**.

---

## 📐 Esquema de Conexión Física (Pinout)

### 🔌 Componentes Requeridos
- 1× Placa **Arduino Uno** (conectada a la PC por cable USB tipo A-B).
- 2× Servomotores **SG90**, **MG90S** o **MG995**.
- Cables Jumper macho-macho y macho-hembra.
- Fuente externa de 5V (recomendado si usas servos metálicos MG90S/MG995 para evitar sobrecargar el puerto USB de la PC).

---

### 📌 Tabla de Conexiones de Pines

| Componente | Pin del Componente | Conexión en Arduino Uno | Función |
| :--- | :--- | :--- | :--- |
| **Servo Entrada** | Naranja / Amarillo (Señal) | **Pin 9** (PWM) | Controla la barrera de Ingreso (0° - 90°) |
| **Servo Entrada** | Rojo (VCC) | **5V** (o Fuente +5V Externa) | Alimentación 5V |
| **Servo Entrada** | Marrón / Negro (GND) | **GND** | Tierra compartida |
| **Servo Salida** | Naranja / Amarillo (Señal) | **Pin 10** (PWM) | Controla la barrera de Egreso (0° - 90°) |
| **Servo Salida** | Rojo (VCC) | **5V** (o Fuente +5V Externa) | Alimentación 5V |
| **Servo Salida** | Marrón / Negro (GND) | **GND** | Tierra compartida |

> ⚠️ **RECOMENDACIÓN DE ALIMENTACIÓN**: Si utilizas servomotores metálicos (ej. MG90S o MG995), conecta los cables Rojos de los servos a una **fuente externa de 5V/2A** y une la tierra (GND) de la fuente al **GND del Arduino Uno** (tierra común).

---

## 💻 Código Firmware para Arduino Uno (`firmware_arduino_uno.ino`)

Copia y pega el siguiente código en el **Arduino IDE**, selecciona la placa `Arduino Uno` y sube el programa:

```cpp
/*
 * AUTOPASS v10.0.0 - Firmware Control de Barreras (Arduino Uno)
 * Hardware: Arduino Uno + 2 Servomotores (Entrada Pin 9, Salida Pin 10)
 * Controlado 100% por comandos USB Serial desde el Dashboard AUTOPASS
 */

#include <Servo.h>

Servo servoEntrada;
Servo servoSalida;

const int PIN_SERVO_ENTRADA = 9;
const int PIN_SERVO_SALIDA  = 10;

const int ANGLO_CERRADO = 0;   // Barrera horizontal (Cerrada)
const int ANGLO_ABIERTO = 90;  // Barrera vertical (Abierta)
const unsigned long TIEMPO_AUTOCIERRE = 5000; // 5 segundos

bool entradaAbierta = false;
bool salidaAbierta  = false;
unsigned long timerEntrada = 0;
unsigned long timerSalida  = 0;

void setup() {
  Serial.begin(9600); // Comunicación Serie USB a 9600 Baudios
  
  servoEntrada.attach(PIN_SERVO_ENTRADA);
  servoSalida.attach(PIN_SERVO_SALIDA);
  
  servoEntrada.write(ANGLO_CERRADO);
  servoSalida.write(ANGLO_CERRADO);
  
  Serial.println("AUTOPASS HARDWARE READY - ARDUINO UNO");
}

void abrirBarreraEntrada() {
  servoEntrada.write(ANGLO_ABIERTO);
  entradaAbierta = true;
  timerEntrada = millis();
  Serial.println("OK: OPEN_ENTRADA");
}

void cerrarBarreraEntrada() {
  servoEntrada.write(ANGLO_CERRADO);
  entradaAbierta = false;
  Serial.println("OK: CLOSE_ENTRADA");
}

void abrirBarreraSalida() {
  servoSalida.write(ANGLO_ABIERTO);
  salidaAbierta = true;
  timerSalida = millis();
  Serial.println("OK: OPEN_SALIDA");
}

void cerrarBarreraSalida() {
  servoSalida.write(ANGLO_CERRADO);
  salidaAbierta = false;
  Serial.println("OK: CLOSE_SALIDA");
}

void loop() {
  // 1. Recepción de comandos enviados por USB Serial desde AUTOPASS
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    comando.toUpperCase();
    
    if (comando == "OPEN_ENTRADA" || comando == "OPEN_ENTRY") {
      abrirBarreraEntrada();
    } else if (comando == "CLOSE_ENTRADA" || comando == "CLOSE_ENTRY") {
      cerrarBarreraEntrada();
    } else if (comando == "OPEN_SALIDA" || comando == "OPEN_EXIT") {
      abrirBarreraSalida();
    } else if (comando == "CLOSE_SALIDA" || comando == "CLOSE_EXIT") {
      cerrarBarreraSalida();
    }
  }
  
  // 2. Auto-cierre automático tras 5 segundos
  if (entradaAbierta && (millis() - timerEntrada >= TIEMPO_AUTOCIERRE)) {
    cerrarBarreraEntrada();
  }
  if (salidaAbierta && (millis() - timerSalida >= TIEMPO_AUTOCIERRE)) {
    cerrarBarreraSalida();
  }
}
```

---

## ⚙️ Configuración del Sistema AUTOPASS

### Conexión USB Serie Directa
El backend de AUTOPASS detecta automáticamente el puerto COM de tu Arduino cuando está conectado por USB.

En tu archivo `.env`:
```env
SERIAL_ENABLED=true
SERIAL_PORT=AUTO      # AUTO detecta automáticamente COM3, COM4, /dev/ttyACM0, etc.
SERIAL_BAUDRATE=9600
```

---

## ⚡ Activación de Barreras desde el Dashboard

1. **Botones ABRIR y CERRAR en el Dashboard**:
   - Pestaña **MONITOREO** (`/dashboard`), panel *CONTROL DE BARRERAS FÍSICAS*. Puedes pulsar los botones **ABRIR** y **CERRAR** para la barrera de Entrada o Salida.
2. **Ingresos y Salidas Manuales**:
   - Al ejecutar un Ingreso o Salida Manual, la barrera correspondiente se abrirá automáticamente.
3. **Lectura por Cámara ALPR**:
   - Al detectar una patente autorizada en Entrada o Salida, la barrera correspondiente se abrirá automáticamente.
4. **Escaneo de Código QR**:
   - Al validar un pase digital QR en Entrada o Egreso, se accionará automáticamente el servo de la puerta correspondiente.
