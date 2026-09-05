@echo off
chcp 65001 >nul
title AUTOPASS - Acceso Remoto (Internet)
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\start_remote.ps1"
echo.
pause
