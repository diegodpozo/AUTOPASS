# AUTOPASS - Detener Acceso Remoto (server uvicorn + túnel ngrok)
# Uso:  .\scripts\stop_remote.ps1
$ErrorActionPreference = "Continue"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host ""
Write-Host " ============================================================" -ForegroundColor Yellow
Write-Host "   AUTOPASS - DETENER ACCESO REMOTO" -ForegroundColor Cyan
Write-Host " ============================================================" -ForegroundColor Yellow
Write-Host ""

# Detener túneles ngrok
$ngrokList = Get-CimInstance Win32_Process -Filter "Name like 'ngrok%'"
foreach ($n in $ngrokList) {
    Write-Host "   [STOP] Deteniendo túnel ngrok (PID $($n.ProcessId))..." -ForegroundColor Yellow
    Stop-Process -Id $n.ProcessId -Force -ErrorAction SilentlyContinue
}

# Detener servidor uvicorn AUTOPASS
$uvList = Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object {
    $_.CommandLine -match 'AUTOPASS' -and $_.CommandLine -match 'uvicorn main:app'
}
foreach ($p in $uvList) {
    Write-Host "   [STOP] Deteniendo servidor uvicorn (PID $($p.ProcessId))..." -ForegroundColor Yellow
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}

Start-Sleep -Seconds 1
Write-Host ""
Write-Host "   [OK] Acceso remoto detenido." -ForegroundColor Green
Write-Host "   La app sigue disponible localmente con: .\run_server.bat (http://localhost:8000)" -ForegroundColor Gray
Write-Host ""
