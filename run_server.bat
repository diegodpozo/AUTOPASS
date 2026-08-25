@echo off
title AUTOPASS - Servidor de Produccion
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\run_server.ps1"
echo.
pause
