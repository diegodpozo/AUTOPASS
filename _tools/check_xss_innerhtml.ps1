# A9 AUDITORIA_XSS - Scan estatico de innerHTML/insertAdjacentHTML en static/js.
#
# Reproduce la metrica del informe A9 §1 de forma automatizada:
#   1. Total de ocurrencias innerHTML=/insertAdjacentHTML(
#   2. De las cuales las que interpolar template literals con variable (${...})
#   3. De esas, las que NO escapan con escapeHtml( en la misma linea (candidatas a revisar)
#
# Uso:
#   powershell -ExecutionPolicy Bypass -File _tools/check_xss_innerhtml.ps1
#   powershell ... -File _tools/check_xss_innerhtml.ps1 -NoList   # solo conteos
param(
    [switch]$NoList
)

$root = Split-Path -Parent $PSScriptRoot
$pattern = 'innerHTML\s*(\+=)?\s*=|insertAdjacentHTML\('
$varInterp = '\$\{'
$escaped = 'escapeHtml\('

$files = Get-ChildItem -Path (Join-Path $root 'static\js') -Recurse -Filter *.js

$total = 0
$interp = @()
$unEscaped = @()

foreach ($f in $files) {
    $rel = $f.FullName.Substring($root.Length + 1)
    $lines = Get-Content -LiteralPath $f.FullName -Encoding UTF8
    for ($i = 0; $i -lt $lines.Count; $i++) {
        $line = $lines[$i]
        if ($line -match $pattern) {
            $total++
            if ($line -match $varInterp) {
                $rec = [PSCustomObject]@{ File = $rel; Line = ($i + 1); Escaped = ($line -match $escaped) }
                $interp += $rec
                if (-not $rec.Escaped) { $unEscaped += $rec }
            }
        }
    }
}

Write-Host "=== A9 XSS: innerHTML/insertAdjacentHTML en static/js ==="
Write-Host ("Total ocurrencias: {0}" -f $total)
Write-Host ("Con interpolacion de variable ({0}): {1}" -f '${{...}}', $interp.Count)
Write-Host ("Sin escapeHtml() en la misma linea (revisar a mano): {0}" -f $unEscaped.Count)

if (-not $NoList) {
    if ($unEscaped.Count -gt 0) {
        Write-Host "`n-- No escapadas --"
        $unEscaped | ForEach-Object { Write-Host ("  {0}:{1}" -f $_.File, $_.Line) }
    }
    if ($interp.Count -gt 0) {
        Write-Host "`n-- Todas las interpoladas --"
        $interp | ForEach-Object { Write-Host ("  [{0}] {1}:{2}" -f $(if ($_.Escaped) { 'esc' } else { 'VER' }), $_.File, $_.Line) }
    }
}

# Exit 0 siempre: scan informativo personal; las lineas 'VER' se revisan segun origen
# del dato (server DB vs usuario). No bloquear CI (AGENTS: tests cubren backend).
exit 0