# Captura ejecuciones reales de xterm en un servidor grafico virtual de WSL.
# No necesita abrir ventanas ni capturar otras aplicaciones del usuario.
param([int]$Corte = 5, [string]$Distribucion = 'Ubuntu')
$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
Push-Location -LiteralPath $raiz
try {
    # El namespace de montajes evita modificar el socket de WSLg del usuario.
    & wsl.exe -d $Distribucion -u root -- unshare --mount --propagation private python3 scripts/capturar_xvfb.py $Corte --wsl-namespace
    if ($LASTEXITCODE -ne 0) { throw "No se pudieron generar las capturas (codigo $LASTEXITCODE)." }
} finally {
    Pop-Location
}
