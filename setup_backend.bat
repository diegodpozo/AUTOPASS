@echo off
chcp 65001 >nul
title AUTOPASS - Instalador de Backend
powershell -ExecutionPolicy Bypass -NoProfile -File "%~dp0scripts\setup.ps1"
echo.
echo Presiona cualquier tecla para salir del instalador...
pause >nul
