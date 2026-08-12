@echo off
title Server - AUTOPASS Professional
echo ======================================================
echo   EJECUTANDO SERVIDOR AUTOPASS (FASTAPI)
echo ======================================================
echo.

:: Verificar si el entorno virtual existe
if not exist venv (
    echo [ERROR] No se encontro el entorno virtual 'venv'.
    echo Por favor, ejecuta primero setup_backend.bat
    pause
    exit /b
)

:: Activar el entorno virtual
echo [+] Activando entorno virtual...
call venv\Scripts\activate

:: Abrir navegador automaticamente SOLO cuando el servidor responda
:: (waiter TCP en segundo plano; usa TcpClient para bypasear el proxy de sistema,
::  que hace que Invoke-WebRequest a localhost de timeout)
echo [+] Abriendo navegador cuando el servidor este listo...
start "" /b powershell -WindowStyle Hidden -command "for($i=0;$i -lt 90;$i++){ $c=New-Object Net.Sockets.TcpClient; try{ $c.Connect('127.0.0.1',8000); Start-Process 'http://localhost:8000'; break }catch{} finally{ $c.Dispose() }; Start-Sleep -Seconds 1 }"

:: Ejecutar el servidor (sin --reload para arranque rapido; Ctrl+C para detener)
echo [+] Iniciando Uvicorn en http://localhost:8000
echo [+] (Presiona Ctrl+C para detener el servidor)
echo.

python -m uvicorn main:app --host 127.0.0.1 --port 8000

pause
