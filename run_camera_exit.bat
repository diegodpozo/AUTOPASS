@echo off
title Camera Exit - AUTOPASS
echo ======================================================
echo   INICIANDO CAMARA DE SALIDA (ALPR)
echo ======================================================
echo.

:: Solicitar el nombre de la sede para aislamiento
set /p SEDE="Ingresa el nombre de la sede (ej: CASTELAR, MORON, CABALLITO): "
if "%SEDE%"=="" set SEDE=GLOBAL

:: Configurar variables para Salida
set GATE_TYPE=salida
set GATE_ID=%SEDE%_SALIDA
set BACKEND_URL=http://localhost:8000

echo.
echo [*] Configurado para Sede: %SEDE%
echo [*] ID de Puerta: %GATE_ID%
echo [*] Iniciando servicio...
echo.

:: Activar el entorno virtual
if exist venv (
    call venv\Scripts\activate
)

python alpr_service.py

pause
