# AUTOPASS - Modern Server Runner (PowerShell Engine)
$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "AUTOPASS - Servidor de Produccion v10.0"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Clear-Host

Write-Host ""
Write-Host " =========================================================================" -ForegroundColor Yellow
Write-Host "        █████╗ ██╗  ██╗████████╗██████╗ ██████╗  █████╗ ███████╗███████╗" -ForegroundColor Yellow
Write-Host "       ██╔══██╗██║  ██║╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝" -ForegroundColor Yellow
Write-Host "       ███████║██║  ██║   ██║   ██║  ██║██████╔╝███████║███████╗███████╗" -ForegroundColor Yellow
Write-Host "       ██╔══██║██║  ██║   ██║   ██║  ██║██╔═══╝ ██╔══██║╚════██║╚════██║" -ForegroundColor Yellow
Write-Host "       ██║  ██║╚█████╔╝   ██║   ██████╔╝██║     ██║  ██║███████║███████╗" -ForegroundColor Yellow
Write-Host "       ╚═╝  ╚═╝ ╚════╝    ╚═╝   ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝" -ForegroundColor Yellow
Write-Host " =========================================================================" -ForegroundColor Yellow
Write-Host "               Sistema Inteligente de Estacionamientos v10.0" -ForegroundColor Cyan
Write-Host ""

# 1. VERIFICAR ENTORNO VIRTUAL
if (-not (Test-Path "venv\Scripts\python.exe")) {
    Write-Host "        [ERROR] No se encontró el entorno virtual 'venv'." -ForegroundColor Red
    Write-Host "        Ejecutá primero setup_backend.bat para instalar el sistema." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Presioná Enter para salir..."
    exit 1
}
Write-Host "        [OK] Entorno virtual 'venv' detectado." -ForegroundColor Green

# 2. VERIFICAR .ENV
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -notmatch "ALPR_FORCE_OCR=true") {
        Add-Content -Path ".env" -Value "`nALPR_FORCE_OCR=true"
    }
    Write-Host "        [OK] Archivo de configuración .env verificado." -ForegroundColor Green
}

# 3. LANZAR APERTURA AUTOMATICA DE NAVEGADOR
Write-Host "        [OK] Lanzador de navegador automático listo (http://localhost:8000)." -ForegroundColor Green
Start-Process -WindowStyle Hidden -FilePath "powershell.exe" -ArgumentList "-WindowStyle Hidden -Command `"`$c=New-Object Net.Sockets.TcpClient; for(`$i=0;`$i -lt 90;`$i++){ try{ `$c.Connect('127.0.0.1',8000); Start-Process 'http://localhost:8000'; break }catch{} finally{ `$c.Dispose() }; Start-Sleep -Seconds 1 }`""

Write-Host ""
Write-Host " ┌─────────────────────────────────────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host " │  SERVIDOR FASTAPI EN EJECUCIÓN                                          │" -ForegroundColor Yellow
Write-Host " │  URL Local:    http://localhost:8000                                  │" -ForegroundColor White
Write-Host " │  Servicios:    WebSockets (Aforo), MQTT (Barreras), ALPR (IA)         │" -ForegroundColor Gray
Write-Host " │  Para detener: Presioná [Ctrl + C] en esta consola                     │" -ForegroundColor DarkYellow
Write-Host " └─────────────────────────────────────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""

$env:PYTHONWARNINGS = "ignore"
& "venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --no-access-log
