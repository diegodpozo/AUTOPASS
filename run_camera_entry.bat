@echo off
title Camera Entry - AUTOPASS
echo ======================================================
echo   INICIANDO CAMARA DE ENTRADA (ALPR)
echo ======================================================
echo.

:: Solicitar el nombre de la sede para aislamiento
set /p SEDE="Ingresa el nombre de la sede (ej: CASTELAR, MORON, CABALLITO): "
if "%SEDE%"=="" set SEDE=GLOBAL

:: Configurar variables para Entrada
set GATE_TYPE=entrada
set GATE_ID=%SEDE%_ENTRADA
set BACKEND_URL=http://localhost:8000
:: Cambia '0' por la URL de IPWebcam si usas el celular (ej: http://192.168.1.50:8080/video)
set VIDEO_SOURCE=0

echo.
echo [*] Configurado para Sede: %SEDE%
echo [*] ID de Puerta: %GATE_ID%
echo [*] Fuente de Video: %VIDEO_SOURCE%
echo [*] Iniciando servicio...
echo.

:: Activar el entorno virtual
if exist venv (
    call venv\Scripts\activate
)

python alpr_service.py

pause
