<#
.SYNOPSIS
    Provisiona e testa o pipeline Medidata no Overseer (máquina WS1207).

.DESCRIPTION
    Executa por ordem: verificar túnel, provision-runners -Register, teste manual
    do manifest. Depois indica como migrar o Task Scheduler.

.EXAMPLE
    .\setup-medidata-overseer.ps1 -SshTarget eferreira@195.23.9.32
#>
param(
    [string]$RepoPath = "C:\MAIATRON\Overseer",
    [string]$SshTarget = "eferreira@195.23.9.32",
    [string]$VenvPath = (Join-Path $env:LOCALAPPDATA "overseer-venv"),
    [switch]$SkipTest
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")

$listening = netstat -an | Select-String "127\.0\.0\.1:18090.*LISTENING"
if (-not $listening) {
    Write-Warning "Túnel SSH não detectado em 127.0.0.1:18090."
    Write-Host "Arranca noutra janela:"
    Write-Host "  powershell -ExecutionPolicy Bypass -File `"$OverseerScriptDir\ssh-tunnel.ps1`" -SshTarget $SshTarget"
    throw "Túnel em falta."
}

Write-Host "== Provisionar Medidata =="
& (Join-Path $OverseerScriptDir "provision-runners.ps1") -Register -VenvPath $VenvPath

$runDir = Join-Path $env:USERPROFILE "overseer-runners\medidata_pipeline"
$manifest = Join-Path $runDir "manifest.yaml"
if (-not (Test-Path -LiteralPath $manifest)) {
    throw "Manifest não encontrado: $manifest"
}

if (-not $SkipTest) {
    Write-Host "== Teste manual do manifest =="
    Import-OverseerEnvFile (Join-Path $env:USERPROFILE "overseer-runners\.env.overseer")
    $env:NO_PROXY = "127.0.0.1,localhost"
    $env:HTTP_PROXY = ""
    $env:HTTPS_PROXY = ""
    $env:ALL_PROXY = ""
    $py = Join-Path $VenvPath "Scripts\python.exe"
    & $py -m overseer_agent manifest $manifest --by taskscheduler
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host ""
Write-Host "Setup concluído."
Write-Host "Migrar Task Scheduler (GUI se GPO bloquear):"
Write-Host "  Programa: powershell.exe"
Write-Host "  Argumentos: -ExecutionPolicy Bypass -File `"$runDir\run.ps1`""
Write-Host "  Iniciar em: $runDir"
Write-Host ""
Write-Host "Dashboard (no teu PC): ssh -L 8080:127.0.0.1:8090 $SshTarget"
Write-Host "  http://127.0.0.1:8080/ui/dashboard.html -> medidata_pipeline (host WS1207)"
