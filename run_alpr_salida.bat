@echo off
title ALPR SALIDA - AUTOPASS
echo ======================================================
echo   EJECUTANDO SERVICIO ALPR (SALIDA)
echo ======================================================
echo.

:: --- CONFIGURACION ---
:: Cambia esta IP por la que te muestra la App IP Webcam en tu celular
set IP_CELULAR=192.168.1.100
set VIDEO_SOURCE=http://%IP_CELULAR%:8080/video
set GATE_TYPE=salida
:: ---------------------

if not exist venv (
    echo [ERROR] No se encontro el entorno virtual 'venv'.
    pause
    exit /b
)

echo [+] Conectando a IP Webcam: %VIDEO_SOURCE%
echo [+] Modo: %GATE_TYPE%
echo.

call venv\Scripts\activate
python alpr_service.py

pause
