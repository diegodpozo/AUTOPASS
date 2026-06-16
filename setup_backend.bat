@echo off
title Setup Backend - AUTOPASS Modular Gold v8.7.0
echo ======================================================
echo   INSTALACION DEL ENTORNO MODULAR (AUTOPASS v8.7.0)
echo ======================================================
echo.
:: 1. Verificar si Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no se encuentra en el PATH.
    echo Por favor, instala Python 3.9 o superior.
    pause
    exit /b
)

:: 2. Crear entorno virtual
echo [+] Creando entorno virtual (venv)...
if not exist venv (
    python -m venv venv
) else (
    echo [!] El entorno venv ya existe, saltando creacion.
)

if %errorlevel% neq 0 (
    echo [ERROR] No se pudo crear el entorno virtual.
    pause
    exit /b
)

:: 3. Activar entorno e instalar dependencias
echo [+] Activando entorno virtual e instalando librerias...
call venv\Scripts\activate

echo [+] Actualizando PIP...
venv\Scripts\python.exe -m pip install --upgrade pip

echo [+] Instalando dependencias desde requirements.txt...
echo Nota: La instalacion de dependencias (OpenCV, EasyOCR, Torch, QRCode) puede tardar unos minutos segun tu conexion.
venv\Scripts\pip.exe install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo [!] La instalacion original fallo.
    echo [+] Intentando instalacion de contingencia con python-bidi puro...
    venv\Scripts\pip.exe install python-bidi==0.4.2
    echo [+] Reintentando instalacion de dependencias...
    venv\Scripts\pip.exe install -r requirements.txt
)

:: 4. Configurar Variables de Entorno (.env)
echo [+] Configurando archivo de variables de entorno (.env)...
if not exist .env (
    copy .env.example .env >nul
    echo [OK] Archivo .env creado desde .env.example.
) else (
    echo [!] El archivo .env ya existe, preservando configuracion actual.
)

:: 5. Inicializar Base de Datos
echo [+] Inicializando base de datos...
venv\Scripts\python.exe init_db.py

:: 6. Crear directorios necesarios
echo [+] Creando directorios de assets y uploads...
if not exist captured_images mkdir captured_images
if not exist static\uploads\branches mkdir static\uploads\branches

echo.
echo ======================================================
echo   INSTALACION COMPLETADA CON EXITO (v8.7.0 GOLD)
echo ======================================================
echo.
echo Arquitectura Limpia Modular (v8.7.0):
echo - Core: Configuracion y Seguridad Centralizada
echo - Domain Layers: Modelos y Esquemas divididos (User/Parking/Res)
echo - Business Logic: Capa de Servicios agnostica (services/)
echo - Modular Frontend: Plantillas Jinja2 por pestañas y componentes
echo - Multi-Sucursal: Soporte nativo para Puntos AutoPass geolocalizados
echo.
echo Credenciales de Admin por defecto:
echo Email: admin@autopass.com
echo Pass: admin123
echo.
echo Para iniciar el sistema:
echo 1. Ejecuta el script: run_server.bat
echo    (Este script abrira automaticamente tu navegador por defecto)
echo.
echo Acceso Web: http://localhost:8000
echo.
pause
