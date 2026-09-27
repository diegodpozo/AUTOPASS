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
 * ============================================================================
 * AUTOPASS Professional v10.0.0 - Firmware Control de Barreras (Arduino Uno)
 * ============================================================================
 * Hardware: Arduino Uno + 2 Servomotores (SG90 / MG90S / MG995)
 * Conexión: USB Serial (9600 Baudios) o MQTT Bridge
 * 
 * Asignación de Pines:
 * - Servo Entrada (Ingreso): Pin 9 (PWM)
 * - Servo Salida (Egreso)  : Pin 10 (PWM)
 * ============================================================================
 */

#include <Servo.h>

// Definición de Servomotores
Servo servoEntrada;
Servo servoSalida;

// Pines PWM
const int PIN_SERVO_ENTRADA = 9;
const int PIN_SERVO_SALIDA  = 10;

// Ángulos de Servomotor Entrada (invertidos)
const int ANGLO_CERRADO_ENTRADA = 180;   // Posición barrera horizontal (Cerrada)
const int ANGLO_ABIERTO_ENTRADA = 90;    // Posición barrera vertical (Abierta)

// Ángulos de Servomotor Salida (invertidos)
const int ANGLO_CERRADO_SALIDA = 180;    // Posición barrera horizontal (Cerrada)
const int ANGLO_ABIERTO_SALIDA = 90;     // Posición barrera vertical (Abierta)

// Tiempo de Auto-Cierre tras apertura (en milisegundos)
const unsigned long TIEMPO_AUTOCIERRE = 5000; 

// Estado de Barreras
bool entradaAbierta = false;
bool salidaAbierta  = false;
unsigned long timerEntrada = 0;
unsigned long timerSalida  = 0;

void setup() {
  // Inicialización de la Comunicación Serie USB (9600 Baudios)
  Serial.begin(9600);
  
  // Asignar servos a los pines PWM
  servoEntrada.attach(PIN_SERVO_ENTRADA);
  servoSalida.attach(PIN_SERVO_SALIDA);
  
  // Posición inicial: Barreras cerradas
  servoEntrada.write(ANGLO_CERRADO_ENTRADA);
  servoSalida.write(ANGLO_CERRADO_SALIDA);
  
  Serial.println("==========================================");
  Serial.println("   AUTOPASS HARDWARE READY - ARDUINO UNO  ");
  Serial.println("==========================================");
  Serial.println("Esperando comandos Serie: OPEN_ENTRADA, CLOSE_ENTRADA, OPEN_SALIDA, CLOSE_SALIDA");
}

void abrirBarreraEntrada() {
  servoEntrada.write(ANGLO_ABIERTO_ENTRADA);
  entradaAbierta = true;
  timerEntrada = millis();
  Serial.println("OK: OPEN_ENTRADA");
}

void cerrarBarreraEntrada() {
  servoEntrada.write(ANGLO_CERRADO_ENTRADA);
  entradaAbierta = false;
  Serial.println("OK: CLOSE_ENTRADA");
}

void abrirBarreraSalida() {
  servoSalida.write(ANGLO_ABIERTO_SALIDA);
  salidaAbierta = true;
  timerSalida = millis();
  Serial.println("OK: OPEN_SALIDA");
}

void cerrarBarreraSalida() {
  servoSalida.write(ANGLO_CERRADO_SALIDA);
  salidaAbierta = false;
  Serial.println("OK: CLOSE_SALIDA");
}

void loop() {
  // 1. LECTURA DE COMANDOS ENVIADOS DESDE EL DASHBOARD / BACKEND (USB SERIAL)
  if (Serial.available() > 0) {
    String comando = Serial.readStringUntil('\n');
    comando.trim();
    comando.toUpperCase();
    
    if (comando == "OPEN_ENTRADA" || comando == "OPEN_ENTRY") {
      abrirBarreraEntrada();
    } 
    else if (comando == "CLOSE_ENTRADA" || comando == "CLOSE_ENTRY") {
      cerrarBarreraEntrada();
    } 
    else if (comando == "OPEN_SALIDA" || comando == "OPEN_EXIT") {
      abrirBarreraSalida();
    } 
    else if (comando == "CLOSE_SALIDA" || comando == "CLOSE_EXIT") {
      cerrarBarreraSalida();
    }
  }
  
  // 2. AUTO-CIERRE AUTOMÁTICO TRAS TIEMPO CONFIGURADO (5 SEGUNDOS)
  if (entradaAbierta && (millis() - timerEntrada >= TIEMPO_AUTOCIERRE)) {
    cerrarBarreraEntrada();
  }
  
  if (salidaAbierta && (millis() - timerSalida >= TIEMPO_AUTOCIERRE)) {
    cerrarBarreraSalida();
  }
}

## ⚡ Activación de Barreras desde el Dashboard

1. **Botones ABRIR y CERRAR en el Dashboard**:
   - Pestaña **MONITOREO** (`/dashboard`), panel *CONTROL DE BARRERAS FÍSICAS*. Puedes pulsar los botones **ABRIR** y **CERRAR** para la barrera de Entrada o Salida.
2. **Ingresos y Salidas Manuales**:
   - Al ejecutar un Ingreso o Salida Manual, la barrera correspondiente se abrirá automáticamente.
3. **Lectura por Cámara ALPR**:
   - Al detectar una patente autorizada en Entrada o Salida, la barrera correspondiente se abrirá automáticamente.
4. **Escaneo de Código QR**:
   - Al validar un pase digital QR en Entrada o Egreso, se accionará automáticamente el servo de la puerta correspondiente.
