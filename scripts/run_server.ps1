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

# 2. LIMPIAR PROCESOS PREVIOS (evita doble bind en el puerto 8000 que reparte el trafico
# entre instancias viejas y nuevas, dejando codigo obsoleto sirviendo requests)
$autopassPy = Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object {
    $_.CommandLine -match 'AUTOPASS' -and ($_.CommandLine -match 'uvicorn main:app' -or $_.CommandLine -match 'alpr_service\.py')
}
foreach ($ap in $autopassPy) {
    Write-Host "        [LIMPIEZA] Deteniendo proceso previo PID $($ap.ProcessId)..." -ForegroundColor Yellow
    Stop-Process -Id $ap.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2
Write-Host "        [OK] Servidores previos detenidos." -ForegroundColor Green

# 3. VERIFICAR .ENV
if (Test-Path ".env") {
    $envContent = Get-Content ".env" -Raw
    if ($envContent -notmatch "ALPR_FORCE_OCR=true") {
        Add-Content -Path ".env" -Value "`nALPR_FORCE_OCR=true"
    }
    Write-Host "        [OK] Archivo de configuración .env verificado." -ForegroundColor Green
}

# 4. LANZAR APERTURA AUTOMATICA DE NAVEGADOR
Write-Host "        [OK] Lanzador de navegador automático listo (http://localhost:8000)." -ForegroundColor Green
$browserCmd = @'
$client = New-Object Net.Sockets.TcpClient
for ($i = 0; $i -lt 90; $i++) {
    try {
        $c = New-Object Net.Sockets.TcpClient
        $c.Connect('127.0.0.1', 8000)
        Start-Process 'http://localhost:8000'
        break
    } catch {
        Start-Sleep -Seconds 1
    } finally {
        try { $c.Dispose() } catch {}
    }
}
'@
Start-Process -WindowStyle Hidden -FilePath "powershell.exe" -ArgumentList "-NoProfile -WindowStyle Hidden -Command", $browserCmd

Write-Host ""
# Recuadro con ancho fijo: el borde derecho cierra siempre en la misma columna
# y el frame se pinta con un unico color (solo el texto interior conserva su color).
$boxBorderColor = "Cyan"
$boxWidth = 70

function Write-ServerBoxBorder {
    param([string]$CornerL, [string]$CornerR)
    Write-Host (" " + $CornerL + ("─" * $boxWidth) + $CornerR) -ForegroundColor $boxBorderColor
}

function Write-ServerBoxLine {
    param([string]$Text, [string]$Color)
    $pad = $boxWidth - 2 - $Text.Length
    if ($pad -lt 0) { $pad = 0 }
    Write-Host " │ " -ForegroundColor $boxBorderColor -NoNewline
    Write-Host $Text -ForegroundColor $Color -NoNewline
    Write-Host (" " * $pad) -NoNewline
    Write-Host " │" -ForegroundColor $boxBorderColor
}

Write-ServerBoxBorder "┌" "┐"
Write-ServerBoxLine "SERVIDOR FASTAPI EN EJECUCIÓN" "Yellow"
Write-ServerBoxLine "URL Local:    http://localhost:8000" "White"
Write-ServerBoxLine "Servicios:    WebSockets (Aforo), MQTT (Barreras), ALPR (IA)" "Gray"
Write-ServerBoxLine "Para detener: Presioná [Ctrl + C] en esta consola" "DarkYellow"
Write-ServerBoxBorder "└" "┘"
Write-Host ""

$env:PYTHONWARNINGS = "ignore"
& "venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --no-access-log
