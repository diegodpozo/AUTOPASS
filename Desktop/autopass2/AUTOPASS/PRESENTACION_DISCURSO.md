# 🎙️ Speech de Presentación: AutoPass v6.3

Este documento contiene el discurso refinado para la presentación técnica, corregido según la arquitectura real del sistema y las últimas mejoras de UX.

---

## 🏗️ 1. Arquitectura General
"Lo que armamos es un sistema pensado para ser **modular, fácil de escalar y mantener**. La idea es que cada parte tenga su rol bien definido, y que todo junto funcione como una solución completa para manejar el acceso de vehículos.

En la arquitectura, lo separamos en **capas**, usando patrones que nos permiten dividir la lógica de negocio de la base de datos (Service & Repository Pattern). El backend está dividido en módulos: uno para seguridad, otro para el control de acceso y reconocimiento de patentes, otro para el portal del cliente y un potente **Command Center** para el administrador. Todo corre de forma **asíncrona**, permitiendo procesar múltiples eventos simultáneamente sin bloqueos."

## 🛠️ 2. Tecnologías Core
"Elegimos **Python y FastAPI** como base porque nos permiten construir APIs extremadamente rápidas, seguras y con validación automática.

Para la comunicación IoT usamos **MQTT**, un protocolo de mensajería ligero que permite que las cámaras y sensores hablen con el backend consumiendo el mínimo ancho de banda. Las barreras físicas son controladas mediante **Arduino/ESP32**.

En cuanto a los datos, utilizamos **SQLite** para una portabilidad total, combinado con **SQLAlchemy**. Al usar este ORM, el código es independiente del motor, lo que nos permitiría migrar a una base empresarial como **PostgreSQL** en minutos sin cambiar la lógica del programa."

## 👁️ 3. Visión Artificial y Tiempo Real
"El motor ALPR híbrido es el corazón operativo. Usamos **OpenCV** para el procesamiento de imagen y la detección nativa de códigos QR (Pases Digitales), trabajando en conjunto con **EasyOCR** para el reconocimiento de las patentes.

El flujo es instantáneo:
1. La cámara detecta el vehículo.
2. El backend valida la identidad o reserva.
3. Se envía la señal por **MQTT** y el Arduino abre la barrera.

Todo esto se refleja de forma **dinámica** en el dashboard, que se mantiene sincronizado constantemente con el estado de la playa para que el operador no pierda un segundo de información."

## 🔐 4. Seguridad y Roles
"La seguridad se basa en **JWT (JSON Web Tokens)**, donde codificamos la identidad y los permisos de cada usuario. Definimos tres roles jerárquicos: **Admin, Empleado (Staff) y Cliente**.

Además, implementamos **Pydantic** para la integridad de datos. Esta librería:
* **Valida automáticamente**: asegura que no entre basura al sistema.
* **Convierte tipos**: transforma datos de entrada al formato técnico necesario.
* **Refuerza la API**: cada petición que llega a FastAPI es filtrada por modelos estrictos, eliminando bugs comunes y ataques de inyección."

## 🎨 5. UX Operativa e Identidad Local
"Diseñamos un **Command Center 2.5** enfocado en la usabilidad profesional. Implementamos una **arquitectura colapsable**: el operador puede expandir o esconder secciones como las tarifas o las plazas para enfocarse 100% en el monitoreo de las cámaras.

Le dimos una identidad fuerte y local:
* **Lenguaje cercano**: uso de voseo argentino en toda la interfaz.
* **Estética Premium**: diseño 'Gold & Black' con efectos de Glassmorphism.
* **Marca unificada**: tipografía Montserrat y elementos visuales consistentes."

## 🏁 Cierre
"En resumen, **AutoPass** es un sistema robusto, seguro y altamente usable, que combina visión artificial avanzada con una experiencia de usuario premium, listo para transformar la gestión de cualquier estacionamiento moderno."
