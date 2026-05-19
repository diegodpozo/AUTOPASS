# 🎙️ Presentación Técnica: AutoPass v6.2

Este documento contiene la estructura, el speech y los puntos clave para la presentación del proyecto **AutoPass (ParkingTech)**.

---

## 🏗️ 1. Arquitectura General del Sistema
**Concepto Clave:** Robustez, modularidad y separación de responsabilidades.

*   **Arquitectura de Capas:** Implementación de patrones **Service Pattern** y **Repository Pattern** para aislar la lógica de negocio de la persistencia de datos.
*   **Backend Modular:** Uso de **FastAPI Routers** para segmentar el sistema en dominios:
    *   `auth`: Seguridad y sesiones.
    *   `parking`: Control de acceso y lógica ALPR.
    *   `user`: Portal del cliente y gestión de flota.
    *   `admin`: Centro de comando y métricas.
*   **Comunicación Asíncrona:** El backend está diseñado para manejar procesos concurrentes (sensores, cámaras, pagos) sin bloqueos.

---

## 🛠️ 2. Stack Tecnológico
**Concepto Clave:** Integración de tecnologías de vanguardia para una solución 360°.

| Tecnología | Rol en el Proyecto |
| :--- | :--- |
| **FastAPI** | Framework de alto rendimiento para la API y lógica central. |
| **Python 3.9+** | Lenguaje núcleo del backend y servicios de IA. |
| **MQTT** | Protocolo de mensajería ligero para comunicación IoT en tiempo real. |
| **ESP32 / Arduino** | Hardware para control de barreras y sensores físicos. |
| **SQLite / SQLAlchemy** | Base de datos relacional con ORM para gestión ágil de datos. |
| **OpenCV** | Pre-procesamiento de imágenes y visión artificial. |
| **EasyOCR** | Motor de reconocimiento de caracteres para patentes y QR. |

---

## ⚙️ 3. Backend y Comunicación en Tiempo Real
**Concepto Clave:** Latencia mínima entre el sensor y la interfaz.

*   **Motor ALPR Híbrido:** El servicio `alpr_service.py` procesa streams de video, detectando simultáneamente patentes y códigos QR.
*   **Flujo de Datos IoT:**
    1.  Detección de vehículo (Cámara/Sensor).
    2.  Validación en Backend (FastAPI).
    3.  Publicación de mensaje vía **MQTT**.
    4.  Acción física (Apertura de barrera por ESP32).
*   **WebSockets:** Actualización instantánea del Dashboard administrativo ante cada evento de entrada o salida.

---

## 🔐 4. Seguridad y Escalabilidad
**Concepto Clave:** Protección de datos y crecimiento sin fricciones.

*   **Seguridad:**
    *   Autenticación mediante **JWT (JSON Web Tokens)**.
    *   Control de acceso basado en roles (**RBAC**): Admin, Empleado, Cliente.
    *   Protección de endpoints y validación de esquemas con **Pydantic**.
*   **Escalabilidad:**
    *   Configuración centralizada mediante archivos `.env`.
    *   Diseño preparado para migración transparente a bases de datos empresariales (PostgreSQL).
    *   Capacidad de desplegar múltiples nodos de visión (cámaras) conectados al mismo backend.

---

## 🚀 5. Funcionalidades Principales
**Concepto Clave:** Experiencia de usuario premium y control total centralizado.

1.  **Command Center (Dashboard v6.2):**
    *   **Monitoreo Unificado:** Visualización de cámaras, estado de servicios (Database, API, OCR), listado de ocupación y logs en una sola pantalla.
    *   **Panel de 'Operación Manual' Colapsable:** Acceso rápido a registro de ingresos/salidas manuales y control físico de barreras (con iconos de estado dinámicos).
    *   **Monitoreo de Salud:** Indicadores visuales de servicios en tiempo real con detección automática de fallos.
2.  **Portal del Cliente:**
    *   Gestión de flota vehicular y registro de patentes.
    *   Cálculo de deuda en tiempo real y sistema de puntos AutoPass.
    *   **Pase Digital QR** para accesos rápidos.
3.  **Lógica de Negocio Avanzada:**
    *   Modelo de **Pago Manual** (Control total del usuario sobre su saldo).
    *   Validación de aforo y prevención de duplicados de patente.

---

## 🇦🇷 Nota de Estilo: Experiencia Local
El sistema está diseñado con una identidad fuerte:
*   **Voseo:** Trato cercano con el usuario ("Cargá", "Tenés").
*   **Estética Gold & Black:** Interfaz premium tipo "Glassmorphism".
*   **Fuente:** Montserrat (Tipografía corporativa obligatoria).
