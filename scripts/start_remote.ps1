# AUTOPASS - Acceso Remoto (ngrok + uvicorn + .env actualizado)
# Levanta el servidor en 0.0.0.0:8000, crea un túnel https de ngrok,
# actualiza BASE_URL / MP_WEBHOOK_URL en .env y muestra la URL pública.
# Uso:  .\scripts\start_remote.ps1
$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "AUTOPASS - Acceso Remoto"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = "C:\Users\usuario.DESKTOP-P7MEQGK\Desktop\AUTOPASS"
$venvPy = "$root\venv\Scripts\python.exe"
$uvicornPort = 8000
$ngrokBin = (Get-Command ngrok -ErrorAction SilentlyContinue).Source

Write-Host ""
Write-Host " ============================================================" -ForegroundColor Yellow
Write-Host "   AUTOPASS - ACCESO REMOTO DESDE INTERNET (ngrok)" -ForegroundColor Cyan
Write-Host " ============================================================" -ForegroundColor Yellow
Write-Host ""

# 1. REQUISITOS
if (-not (Test-Path $venvPy)) {
    Write-Host "   [ERROR] No se encontró el entorno virtual 'venv'." -ForegroundColor Red
    exit 1
}
Write-Host "   [OK] Entorno virtual detectado." -ForegroundColor Green

if (-not $ngrokBin) {
    Write-Host "   [ERROR] No se encontró 'ngrok' en el PATH." -ForegroundColor Red
    Write-Host "           Instalalo desde https://ngrok.com/download y agregalo al PATH." -ForegroundColor Yellow
    exit 1
}
Write-Host "   [OK] ngrok detectado: $ngrokBin" -ForegroundColor Green

# 2. DETENER SERVIDORES PREVIOS (evita doble bind en el puerto 8000)
$prev = Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object {
    $_.CommandLine -match 'AUTOPASS' -and $_.CommandLine -match 'uvicorn main:app'
}
foreach ($p in $prev) {
    Write-Host "   [LIMPIEZA] Deteniendo servidor previo PID $($p.ProcessId)..." -ForegroundColor Yellow
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
# Detener túnel ngrok previo
$prevNgrok = Get-CimInstance Win32_Process -Filter "Name like 'ngrok%'"
foreach ($n in $prevNgrok) {
    Write-Host "   [LIMPIEZA] Deteniendo túnel ngrok previo PID $($n.ProcessId)..." -ForegroundColor Yellow
    Stop-Process -Id $n.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2
Write-Host "   [OK] Procesos previos detenidos." -ForegroundColor Green

# 3. VERIFICAR AUTHTOCKEN DE NGROK
ngrok config check *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   [ERROR] ngrok no tiene authtoken configurado." -ForegroundColor Red
    Write-Host "           Ejecutá: ngrok config add-authtoken TU_TOKEN" -ForegroundColor Yellow
    exit 1
}
Write-Host "   [OK] ngrok authtoken configurado." -ForegroundColor Green

# 4. INICIAR SERVIDOR Uvicorn en 0.0.0.0
$uvLog = "$env:TEMP\opencode\uvicorn_remote.log"
$uvErr = "$env:TEMP\opencode\uvicorn_remote.err.log"
$uv = Start-Process -FilePath $venvPy `
    -ArgumentList "-m","uvicorn","main:app","--host","0.0.0.0","--port","$uvicornPort" `
    -WorkingDirectory $root -RedirectStandardOutput $uvLog -RedirectStandardError $uvErr `
    -PassThru -WindowStyle Hidden
Write-Host "   [OK] Servidor Uvicorn iniciado (PID $($uv.Id)) en 0.0.0.0:$uvicornPort" -ForegroundColor Green

# Esperar a que el servidor responda
$ready = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $c = New-Object Net.Sockets.TcpClient
        $c.Connect('127.0.0.1', $uvicornPort)
        $c.Dispose()
        $ready = $true
        break
    } catch {
        try { $c.Dispose() } catch {}
    }
}
if (-not $ready) {
    Write-Host "   [ERROR] El servidor no terminó de arrancar. Revisá:" -ForegroundColor Red
    Get-Content $uvLog -ErrorAction SilentlyContinue
    Get-Content $uvErr -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "   [OK] Servidor respondiendo en 127.0.0.1:$uvicornPort" -ForegroundColor Green

# 5. INICIAR TÚNEL NGROK
$ngLog = "$env:TEMP\opencode\ngrok_remote.log"
$ng = Start-Process -FilePath $ngrokBin -ArgumentList "http","$uvicornPort","--log=stdout" `
    -RedirectStandardOutput $ngLog -PassThru -WindowStyle Hidden
Write-Host "   [OK] Túnel ngrok iniciado (PID $($ng.Id))" -ForegroundColor Green

# Esperar a que ngrok genere un túnel
$publicUrl = $null
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $t = Invoke-RestMethod -Uri "http://127.0.0.1:4040/api/tunnels" -TimeoutSec 3
        if ($t.tunnels -and $t.tunnels.Count -gt 0) {
            $publicUrl = $t.tunnels[0].public_url
            break
        }
    } catch {}
}
if (-not $publicUrl) {
    Write-Host "   [ERROR] No se pudo obtener la URL del túnel ngrok." -ForegroundColor Red
    Get-Content $ngLog -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "   [OK] Túnel público: $publicUrl" -ForegroundColor Green

# 6. ACTUALIZAR .ENV (BASE_URL y MP_WEBHOOK_URL)
$envFile = "$root\.env"
if (Test-Path $envFile) {
    Copy-Item $envFile "$envFile.bak" -Force
    $lines = Get-Content $envFile
    $updated = @()
    foreach ($line in $lines) {
        if ($line -match '^BASE_URL=')       { $updated += "BASE_URL=$publicUrl" }
        elseif ($line -match '^MP_WEBHOOK_URL=') { $updated += "MP_WEBHOOK_URL=$publicUrl/v1/user/mercadopago/webhook" }
        else { $updated += $line }
    }
    Set-Content -Path $envFile -Value $updated -Encoding UTF8
    Write-Host "   [OK] .env actualizado con la nueva URL del túnel (backup en .env.bak)" -ForegroundColor Green
} else {
    Write-Host "   [AVISO] No se encontró .env; no se actualizó BASE_URL." -ForegroundColor Yellow
}

Write-Host ""
Write-Host " ============================================================" -ForegroundColor Green
Write-Host "   ✅ ACCESO REMOTO ACTIVO" -ForegroundColor Green
Write-Host ""
Write-Host "   URL pública (desde Internet):" -ForegroundColor White
Write-Host "     $publicUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Logs:" -ForegroundColor White
Write-Host "     uvicorn: $uvLog" -ForegroundColor Gray
Write-Host "     ngrok:   $ngLog" -ForegroundColor Gray
Write-Host " ============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "   NOTA: La URL cambia al reiniciar ngrok (plan gratuito)." -ForegroundColor DarkYellow
Write-Host "         Para la sesión de AUTOPASS logueate en la URL ngrok (es un origen distinto a localhost)." -ForegroundColor DarkYellow
Write-Host ""
