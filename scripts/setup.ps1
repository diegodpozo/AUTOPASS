# AUTOPASS - Modern Setup Engine (PowerShell Engine)
$ErrorActionPreference = "Continue"
$Host.UI.RawUI.WindowTitle = "AUTOPASS - Modern Setup Engine v10.0"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Clear-Host

Write-Host ""
Write-Host " =========================================================================" -ForegroundColor Yellow
Write-Host "        █████╗ ██╗  ██╗████████╗██████╗ ██████╗  █████╗ ███████╗███████╗" -ForegroundColor Yellow
Write-Host "       ██╔══██╗██║  ██║╚══██╔══╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝" -ForegroundColor Yellow
Write-Host "       ███████║██║  ██║   ██║   ██║  ██║██████╔╝███████║███████╗███████╗" -ForegroundColor Yellow
Write-Host "       ██╔══██║██║  ██║   ██║   ██║  ██║██╔═══╝ ██╔══██║╚════██║╚════██║" -ForegroundColor Yellow
Write-Host "       ██║  ██║╚█████╔╝   ██║   ██████╔╝██║     ██║  ██║███████║███████║" -ForegroundColor Yellow
Write-Host "       ╚═╝  ╚═╝ ╚════╝    ╚═╝   ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝" -ForegroundColor Yellow
Write-Host " =========================================================================" -ForegroundColor Yellow
Write-Host "               Sistema Inteligente de Estacionamientos v10.0" -ForegroundColor Cyan
Write-Host ""

$isUpdate = (Test-Path "venv\Scripts\python.exe") -and (Test-Path "main.py")

function Show-ProgressBar {
    param(
        [int]$Percent,
        [string]$StepText,
        [string]$StepName
    )
    $width = 25
    $filled = [math]::Round(($Percent / 100) * $width)
    $empty = $width - $filled
    $bar = ("█" * $filled) + ("░" * $empty)
    
    Write-Host " [$bar] " -NoNewline -ForegroundColor Cyan
    Write-Host ("{0,3}%" -f $Percent) -NoNewline -ForegroundColor Yellow
    Write-Host " [$StepText]" -NoNewline -ForegroundColor White
    Write-Host " $StepName" -ForegroundColor Gray
}

# -----------------------------------------------------------------------------
# PASO 1: PYTHON (16%)
# -----------------------------------------------------------------------------
Show-ProgressBar -Percent 16 -StepText "1/6" -StepName "Verificando entorno Python..."
$pyCheck = & python --version 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "        [✔] $pyCheck detectado y compatible." -ForegroundColor Green
} else {
    Write-Host "        [✖] Python no encontrado en el PATH de Windows." -ForegroundColor Red
    Write-Host "        Instalá Python 3.10+ desde https://www.python.org" -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# -----------------------------------------------------------------------------
# PASO 2: VENV (33%)
# -----------------------------------------------------------------------------
$stepLabel = if ($isUpdate) { "Verificando entorno virtual (venv)..." } else { "Creando entorno virtual aislado (venv)..." }
Show-ProgressBar -Percent 33 -StepText "2/6" -StepName $stepLabel
if (-not (Test-Path "venv")) {
    & python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Host "        [✔] Entorno virtual venv creado exitosamente." -ForegroundColor Green
    } else {
        Write-Host "        [✖] No se pudo crear el entorno virtual." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "        [✔] Reutilizando entorno virtual existente." -ForegroundColor Green
}
Write-Host ""

# -----------------------------------------------------------------------------
# PASO 3: DEPENDENCIAS & IA (50%)
# -----------------------------------------------------------------------------
$depLabel = if ($isUpdate) { "Actualizando paquetes y motor ALPR / OCR..." } else { "Instalando dependencias backend e IA..." }
Show-ProgressBar -Percent 50 -StepText "3/6" -StepName $depLabel
Write-Host "        Procesando paquetes desde requirements.txt..." -ForegroundColor DarkYellow
$pipOut = & venv\Scripts\python.exe -m pip install -r requirements.txt 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "        [✔] Dependencias y motor de visión instalados correctamente." -ForegroundColor Green
} else {
    Write-Host "        [✖] Falló la instalación de dependencias core." -ForegroundColor Red
    Write-Host ($pipOut | Select-Object -Last 25)
    exit 1
}
Write-Host ""

# -----------------------------------------------------------------------------
# PASO 4: CONFIGURAR .ENV (66%)
# -----------------------------------------------------------------------------
Show-ProgressBar -Percent 66 -StepText "4/6" -StepName "Configurando archivo de entorno (.env)..."
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "        [✔] Archivo .env configurado desde .env.example." -ForegroundColor Green
    } else {
        Set-Content -Path ".env" -Value "DATABASE_URL=sqlite:///./parking.db`nSECRET_KEY=autopass_super_secreto_2026`nMQTT_BROKER=broker.hivemq.com`nMQTT_TOPIC_ENTRADA=parking/barrera/entrada/control`nMQTT_TOPIC_SALIDA=parking/barrera/salida/control`nIMAGE_DIR=captured_images"
        Write-Host "        [✔] Archivo .env básico generado automáticamente." -ForegroundColor Green
    }
} else {
    Write-Host "        [✔] Archivo .env existente verificado." -ForegroundColor Green
}
Write-Host ""

# -----------------------------------------------------------------------------
# PASO 5: BASE DE DATOS Y MIGRACIONES (83%)
# -----------------------------------------------------------------------------
Show-ProgressBar -Percent 83 -StepText "5/6" -StepName "Estructurando base de datos y aplicando migraciones..."
# Flujo único: init_db.py crea tablas (create_all) y sincroniza Alembic al head.
& venv\Scripts\python.exe init_db.py 2>&1
$initStatus = $LASTEXITCODE

if ($initStatus -eq 0) {
    Write-Host "        [✔] Base de datos y esquema de migraciones listos." -ForegroundColor Green
} else {
    Write-Host "        [✖] Error al inicializar la base de datos." -ForegroundColor Red
    Write-Host "        Revisá el mensaje de error de init_db.py arriba." -ForegroundColor Yellow
    exit 1
}
Write-Host ""

# -----------------------------------------------------------------------------
# PASO 6: PRUEBAS AUTOMATIZADAS (100%)
# -----------------------------------------------------------------------------
Show-ProgressBar -Percent 100 -StepText "6/6" -StepName "Verificando integridad del sistema con Pytest..."
$pytestRun = & venv\Scripts\python.exe -m pytest tests/ -q --timeout=60 2>&1
$testSummary = ($pytestRun | Select-String "passed|failed|error") -join "`n"
Write-Host "        [✔] Pruebas automatizadas ejecutadas." -ForegroundColor Green
$ocrCheck = & venv\Scripts\python.exe -c "from alpr.ocr_engine import OCR_ENGINE_NAME; print(OCR_ENGINE_NAME or 'NINGUNO')" 2>&1
Write-Host "        Motor OCR detectado: $(($ocrCheck | Select-Object -Last 1))" -ForegroundColor Cyan
Write-Host ""

# Crear carpetas requeridas
New-Item -ItemType Directory -Force -Path "captured_images", "static\uploads\branches", "alpr_debug" | Out-Null

Write-Host " =====================================================================" -ForegroundColor Green
Write-Host "             ✔ INSTALACIÓN COMPLETADA CON ÉXITO" -ForegroundColor Green
Write-Host " =====================================================================" -ForegroundColor Green
Write-Host ""
Write-Host " Credenciales por Defecto de Prueba:" -ForegroundColor White
Write-Host "   • Admin Global:   admin@autopass.com        / Pass: admin123" -ForegroundColor Cyan
Write-Host "   • Admin Morón:    admmoron@autopass.com     / Pass: admin123" -ForegroundColor Cyan
Write-Host "   • Admin Ituzaingó: admituzaingo@autopass.com / Pass: admin123" -ForegroundColor Cyan
Write-Host "   • Admin Castelar:  admcastelar@autopass.com  / Pass: admin123" -ForegroundColor Cyan
Write-Host ""
Write-Host " Para Iniciar el Servidor:  ejecutá run_server.bat" -ForegroundColor Yellow
Write-Host " Acceso Web Portal/Admin:    http://localhost:8000" -ForegroundColor Yellow
Write-Host ""
Write-Host " ---------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host " $testSummary" -ForegroundColor Gray
Write-Host " ---------------------------------------------------------------------" -ForegroundColor DarkGray
Write-Host ""
