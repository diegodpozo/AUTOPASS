# AUTOPASS - Acceso Remoto (cloudflared + uvicorn + .env actualizado)
# Levanta el servidor en 0.0.0.0:8000, crea un túnel https de Cloudflare
# (trycloudflare.com, sin interstitial), actualiza BASE_URL / MP_WEBHOOK_URL
# en .env y muestra la URL pública.
# Uso:  .\scripts\start_remote.ps1
$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "AUTOPASS - Acceso Remoto"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$root = "C:\Users\usuario.DESKTOP-P7MEQGK\Desktop\AUTOPASS"
$venvPy = "$root\venv\Scripts\python.exe"
$uvicornPort = 8000

# Ruta de cloudflared (winget lo instala en Program Files (x86))
$cfBin = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $cfBin) {
    foreach ($candidate in @("$env:ProgramFiles(x86)\cloudflared\cloudflared.exe",
                             "$env:ProgramFiles\cloudflared\cloudflared.exe")) {
        if (Test-Path $candidate) { $cfBin = $candidate; break }
    }
}

Write-Host ""
Write-Host " ============================================================" -ForegroundColor Yellow
Write-Host "   AUTOPASS - ACCESO REMOTO DESDE INTERNET (Cloudflare)" -ForegroundColor Cyan
Write-Host " ============================================================" -ForegroundColor Yellow
Write-Host ""

# 1. REQUISITOS
if (-not (Test-Path $venvPy)) {
    Write-Host "   [ERROR] No se encontró el entorno virtual 'venv'." -ForegroundColor Red
    exit 1
}
Write-Host "   [OK] Entorno virtual detectado." -ForegroundColor Green

if (-not $cfBin) {
    Write-Host "   [ERROR] No se encontró 'cloudflared'." -ForegroundColor Red
    Write-Host "           Instalalo con: winget install --id Cloudflare.cloudflared" -ForegroundColor Yellow
    exit 1
}
Write-Host "   [OK] cloudflared detectado: $cfBin" -ForegroundColor Green

# 2. DETENER SERVIDORES PREVIOS (evita doble bind en el puerto 8000)
$prev = Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object {
    $_.CommandLine -match 'AUTOPASS' -and $_.CommandLine -match 'uvicorn main:app'
}
foreach ($p in $prev) {
    Write-Host "   [LIMPIEZA] Deteniendo servidor previo PID $($p.ProcessId)..." -ForegroundColor Yellow
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}
# Detener túnel cloudflared previo
$prevCf = Get-CimInstance Win32_Process -Filter "Name like 'cloudflared%'"
foreach ($c in $prevCf) {
    Write-Host "   [LIMPIEZA] Deteniendo túnel cloudflared previo PID $($c.ProcessId)..." -ForegroundColor Yellow
    Stop-Process -Id $c.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2
Write-Host "   [OK] Procesos previos detenidos." -ForegroundColor Green

# 3. INICIAR TÚNEL CLOUDFLARED (quick tunnel, sin cuenta)
# Se levanta ANTES que uvicorn porque el servidor debe arrancar con la URL
# del túnel en .env (settings.BASE_URL se lee una sola vez al importarse).
# cloudflared mantiene el túnel activo aunque el backend tarde unos segundos.
$cfLog = "$env:TEMP\opencode\cloudflared_remote.log"
$cfErr = "$env:TEMP\opencode\cloudflared_remote.err.log"
$cf = Start-Process -FilePath $cfBin -ArgumentList "tunnel","--url","http://localhost:$uvicornPort","--no-autoupdate" `
    -RedirectStandardOutput $cfLog -RedirectStandardError $cfErr -PassThru -WindowStyle Hidden
Write-Host "   [OK] Túnel Cloudflare iniciado (PID $($cf.Id))" -ForegroundColor Green

# Esperar a que cloudflared genere el túnel (parsear la URL del log)
$publicUrl = $null
for ($i = 0; $i -lt 60; $i++) {
    Start-Sleep -Milliseconds 500
    $logContent = (Get-Content $cfLog -ErrorAction SilentlyContinue | Out-String) + "`n" + (Get-Content $cfErr -ErrorAction SilentlyContinue | Out-String)
    $m = [regex]::Match($logContent, 'https://[a-z0-9\-]+\.trycloudflare\.com')
    if ($m.Success) { $publicUrl = $m.Value; break }
}
if (-not $publicUrl) {
    Write-Host "   [ERROR] No se pudo obtener la URL del túnel Cloudflare." -ForegroundColor Red
    Get-Content $cfLog -ErrorAction SilentlyContinue
    Get-Content $cfErr -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "   [OK] Túnel público: $publicUrl" -ForegroundColor Green

# 4. ACTUALIZAR .ENV (BASE_URL y MP_WEBHOOK_URL)
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

# 5. INICIAR SERVIDOR Uvicorn en 0.0.0.0 (ahora con el .env ya apuntando
# al túnel vigente: settings.BASE_URL se lee al importar core/config.py)
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

Write-Host ""
Write-Host " ============================================================" -ForegroundColor Green
Write-Host "   ✅ ACCESO REMOTO ACTIVO" -ForegroundColor Green
Write-Host ""
Write-Host "   URL pública (desde Internet):" -ForegroundColor White
Write-Host "     $publicUrl" -ForegroundColor Cyan
Write-Host ""
Write-Host "   Logs:" -ForegroundColor White
Write-Host "     uvicorn:    $uvLog" -ForegroundColor Gray
Write-Host "     cloudflared: $cfLog" -ForegroundColor Gray
Write-Host " ============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "   NOTA: La URL cambia al reiniciar el túnel (quick tunnel)." -ForegroundColor DarkYellow
Write-Host "         Cloudflare NO muestra interstitial: la PWA es instalable directamente." -ForegroundColor DarkYellow
Write-Host ""