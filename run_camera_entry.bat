@echo off
title Camera Entry - AUTOPASS
echo ======================================================
echo   INICIANDO CAMARA DE ENTRADA (ALPR)
echo ======================================================
echo.

:: Activar el entorno virtual
if exist venv (
    call venv\Scripts\activate
)

:: Configurar variables para Entrada
:: Para usar IPWebcam del celular, cambia la IP por la que te de la app (ej: http://192.168.1.50:8080/video)
set GATE_TYPE=entrada
set VIDEO_SOURCE=http://TU_IP_CELULAR:8080/video
set BACKEND_URL=http://localhost:8000

python alpr_service.py

pause
