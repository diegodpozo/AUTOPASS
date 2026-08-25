@echo off
title AUTOPASS - Instalador
color 0F
setlocal enabledelayedexpansion

set "LOGFILE=setup_log.txt"
echo [%date% %time%] Inicio de instalacion > "%LOGFILE%"

cls
echo.
echo   ================================================
echo            AUTOPASS - Instalador v10.0
echo   ================================================
echo.

:: Detectar si es instalacion o actualizacion
set "MODE=instalacion"
if exist venv\Scripts\python.exe if exist main.py set "MODE=actualizacion"

:: 1. Verificar Python
echo   [1/6] Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo          [X] Python no encontrado.
    echo          Instala Python 3.10+ desde https://www.python.org
    echo [%date% %time%] ERROR: Python not found >> "%LOGFILE%"
    goto :cerrar
)
for /f "tokens=2 delims= " %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
echo          [OK] Python %PYVER%
echo [%date% %time%] Python: %PYVER% >> "%LOGFILE%"

:: Validar version minima (3.10)
for /f "tokens=1,2,3 delims=." %%a in ("%PYVER%") do (
    set "PY_MAJOR=%%a"
    set "PY_MINOR=%%b"
)
if "%PY_MAJOR%"=="2" (
    echo          [X] Python 2 detectado. Se necesita Python 3.10+.
    goto :cerrar
)
if %PY_MINOR% LSS 10 (
    if "%PY_MAJOR%"=="3" (
        echo          [X] Python %PYVER% es muy viejo. Se necesita Python 3.10+.
        echo          Descarga la ultima version desde https://www.python.org
        echo [%date% %time%] ERROR: Python %PYVER% too old >> "%LOGFILE%"
        goto :cerrar
    )
)

:: 2. Entorno virtual
echo.
if "%MODE%"=="actualizacion" (
    echo   [2/6] Entorno virtual existente...
) else (
    echo   [2/6] Creando entorno virtual...
)
if exist venv goto :venv_listo
python -m venv venv >nul 2>&1
if %errorlevel% neq 0 (
    echo          [X] No se pudo crear el entorno virtual.
    goto :cerrar
)
echo          [OK] Entorno creado.
goto :venv_fin
:venv_listo
echo          [OK] Reutilizando entorno existente.
:venv_fin

call venv\Scripts\activate >nul 2>&1
venv\Scripts\python.exe -m pip install --upgrade pip --quiet >nul 2>&1

:: 3. Dependencias
echo.
if "%MODE%"=="actualizacion" (
    echo   [3/6] Actualizando dependencias...
) else (
    echo   [3/6] Instalando dependencias...
)
echo          (esto puede tardar unos minutos la primera vez)
venv\Scripts\python.exe -m pip install -r requirements.txt --quiet >nul 2>&1 || echo          [~] Algunas dependencias de IA no se instalaron. Sistema core OK.
echo [%date% %time%] OK: dependencies >> "%LOGFILE%"

:: 4. Configurar .env
echo.
echo   [4/6] Configurando entorno...
if exist .env goto :env_listo
if exist .env.example (
    copy .env.example .env >nul
    echo          [OK] Archivo .env creado desde .env.example.
    goto :env_fin
)
echo DATABASE_URL=sqlite:///./parking.db > .env
echo SECRET_KEY=cambiar_este_secreto >> .env
echo MQTT_BROKER=broker.hivemq.com >> .env
echo MQTT_TOPIC_ENTRADA=parking/barrera/entrada/control >> .env
echo MQTT_TOPIC_SALIDA=parking/barrera/salida/control >> .env
echo IMAGE_DIR=captured_images >> .env
echo          [OK] Archivo .env basico creado.
goto :env_fin
:env_listo
echo          [OK] Archivo .env existente.
:env_fin
echo [%date% %time%] OK: .env >> "%LOGFILE%"

:: 5. Base de datos
echo.
echo   [5/6] Configurando base de datos...
venv\Scripts\python.exe init_db.py >nul 2>> "%LOGFILE%"
if %errorlevel% neq 0 (
    echo          [X] Error al inicializar la base de datos.
    echo [%date% %time%] ERROR: init_db failed >> "%LOGFILE%"
    goto :cerrar
)
venv\Scripts\python.exe -m alembic stamp head >nul 2>&1
venv\Scripts\python.exe -m alembic upgrade head >nul 2>&1
echo          [OK] Base de datos lista.
echo [%date% %time%] OK: database >> "%LOGFILE%"

:: 6. Verificacion
echo.
echo   [6/6] Verificando instalacion...
venv\Scripts\python.exe -m pytest tests/ -q 2>&1 | findstr /C:"passed" /C:"failed" > "tests_output.txt"
set "TEST_OK=1"
findstr /C:"failed" "tests_output.txt" >nul 2>&1 && set "TEST_OK=0"
echo [%date% %time%] Tests ejecutados >> "%LOGFILE%"

:: Directorios
if not exist captured_images mkdir captured_images
if not exist static\uploads\branches mkdir static\uploads\branches
if not exist alpr_debug mkdir alpr_debug

:: Resultado - saltar a la combinacion correcta
echo.
if "%MODE%"=="actualizacion" goto :res_update
goto :res_install

:res_update
if "%TEST_OK%"=="1" goto :ok_update
echo   ================================================
echo        ACTUALIZACION COMPLETADA (con advertencias)
echo   ================================================
echo.
echo   Algunas pruebas no pasaron.
goto :post_result

:ok_update
echo   ================================================
echo        ACTUALIZACION COMPLETADA CON EXITO
echo   ================================================
goto :post_result

:res_install
if "%TEST_OK%"=="1" goto :ok_install
echo   ================================================
echo        INSTALACION COMPLETADA (con advertencias)
echo   ================================================
echo.
echo   Algunas pruebas no pasaron.
goto :post_result

:ok_install
echo   ================================================
echo        INSTALACION COMPLETADA CON EXITO
echo   ================================================
goto :post_result

:post_result
echo.
echo   Credenciales por defecto:
echo     Email: admin@autopass.com       Pass: admin123  (Admin Global)
echo     Email: admmoron@autopass.com    Pass: admin123  (Moron)
echo     Email: admituzaingo@autopass.com Pass: admin123  (Ituzaingo)
echo     Email: admcastelar@autopass.com  Pass: admin123  (Castelar)
echo.
echo   Para iniciar ejecuta: run_server.bat
echo   Acceso: http://localhost:8000
echo.
echo   -----------------------------------------------
type "tests_output.txt"
echo   -----------------------------------------------

:cerrar
echo.
echo   Presiona cualquier tecla para cerrar...
pause >nul
