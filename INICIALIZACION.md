#  Guía de Inicialización: AUTOPASS

Sigue estos pasos para poner en marcha el sistema bajo la nueva arquitectura modular.

## 1. Requisitos Previos
- Python 3.9+ e instalar dependencias:
```bash
.\venv\Scripts\python.exe -m pip install -r requirements.txt
# O el comando rápido:
.\venv\Scripts\python.exe -m pip install fastapi uvicorn sqlalchemy python-dotenv jinja2 passlib[bcrypt] python-jose[cryptography] paho-mqtt requests opencv-python easyocr httpx pytest
```

## 2. Configuración de Entorno
Crea o edita el archivo `.env` en la raíz:
```env
DATABASE_URL=sqlite:///./parking.db
SECRET_KEY=tu_secreto_aqui
MQTT_BROKER=broker.hivemq.com
IMAGE_DIR=captured_images
```

## 3. Preparación de Base de Datos
Este paso crea las tablas y los roles iniciales (Admin Global).
```bash
python init_db.py
```

## 4. Ejecución del Servidor y Cámaras

### Iniciar Servidor Principal
```bash
# Opción 1: Batch (Recomendado)
.\run_server.bat

# Opción 2: Manual
.\venv\Scripts\python.exe -m uvicorn main:app --reload
```

### Iniciar Cámaras (ALPR)
Abre terminales separadas para cada cámara:

**Cámara de Entrada:**
```bash
.\run_camera_entry.bat
```

**Cámara de Salida:**
```bash
.\run_camera_exit.bat
```

> **Configuración de IPWebcam (Celular):**
> 1. Abre los archivos `.bat` con un editor de texto (Bloc de notas).
> 2. Busca la línea `set VIDEO_SOURCE=http://TU_IP_CELULAR:8080/video`.
> 3. Reemplaza `TU_IP_CELULAR` con la dirección IP que te muestra la aplicación IPWebcam en tu celular (ej: `192.168.1.50`).
> 4. Guarda los cambios y ejecuta el script.

## 5. Verificación de Integridad
Ejecuta los tests automáticos para asegurar que la modularización está operativa:
```bash
.\venv\Scripts\python.exe test_user_flow.py
```

---
### 🚦 Flujo de Prueba Rápido (ALPR)
1. Inicia el servidor.
2. Abre una terminal nueva y corre `python alpr_service.py` (simulará una cámara).
3. Entra a `http://localhost:8000/dashboard` como admin (admin@autopass.com / admin123).
4. En la pestaña **Live**, deberías ver el stream simulado y las detecciones ingresando a la base de datos modular.
