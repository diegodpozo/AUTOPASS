@echo off
chcp 65001 >nul
title AUTOPASS - Detener Acceso Remoto
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\stop_remote.ps1"
echo.
pause
