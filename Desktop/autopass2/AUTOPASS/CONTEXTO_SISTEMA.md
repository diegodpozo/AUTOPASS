# 🌐 Contexto del Sistema: ParkingTech

Este documento describe la arquitectura de comunicación y el flujo de datos del ecosistema de estacionamiento inteligente.

## 📐 Arquitectura del Ecosistema (v6.4+)

El sistema opera bajo un modelo de **Centro de Comando Descentralizado**:

1.  **Backend Multi-Sede (FastAPI)**: 
    - `routes/admin.py`: Gestión de usuarios y reservas con **aislamiento por sucursal**.
    - `routes/reports.py`: Analítica financiera segmentada por sede para administradores locales y consolidada para el Super-Admin.
    - `services/billing_service.py`: Lógica de cobro inteligente que aplica tarifas específicas según el Punto AutoPass.
2.  **Gestión de Accesos ALPR**:
    - Los eventos de entrada/salida se vinculan automáticamente a la `sucursal` del personal o del punto de acceso.
3.  **Frontend Administrativo**: 
    - Selección dinámica de sede durante la creación de personal operativo.
    - Tableros de control que filtran automáticamente la información según el alcance del usuario autenticado.
## 🔐 Configuración y Seguridad
- **Variables de Entorno**: Configuración centralizada en archivo `.env` (MQTT, Secret Keys, DB URLs).
- **Token JWT**: Protección robusta de endpoints y persistencia de sesión.

## 🛠️ Comandos de Inicio Rápido (v3.1)

### 1. Preparación del Entorno
```powershell
# Instalar dependencias
pip install -r DEPENDENCIAS.md (o el comando de instalación rápida)
# Configurar variables
cp .env.example .env  # Si existiera, o editar .env directamente
```

### 2. Inicialización de Base de Datos
```powershell
python init_db.py
```

### 3. Ejecución del Servidor
```powershell
uvicorn main:app --reload
```

---
*Nota: Es fundamental correr `init_db.py` antes del primer inicio para asegurar que los roles y configuraciones iniciales existan.*
