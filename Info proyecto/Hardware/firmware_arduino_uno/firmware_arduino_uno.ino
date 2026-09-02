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

