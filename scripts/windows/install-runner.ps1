<#
.SYNOPSIS
    Instala o agente Overseer num venv local no Windows.

.DESCRIPTION
    Verifica Python 3.11+, cria um venv em %LOCALAPPDATA%\overseer-venv (ou no
    caminho indicado), instala o pacote a partir do repositório em modo editable
    e faz um smoke test do CLI. Não altera o código dos pipelines.

.EXAMPLE
    .\install-runner.ps1 -RepoPath "C:\Dev\Repos\emanuwells\Overseer"
#>
param(
    [Parameter(Mandatory = $true)][string]$RepoPath,
    [string]$VenvPath = (Join-Path $env:LOCALAPPDATA "overseer-venv"),
    [string]$PythonPath = "",
    [string]$SshTarget = "",
    [int]$LocalPort = 18090,
    [string]$IdentityFile = ""
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")

if (-not (Test-Path -LiteralPath $RepoPath)) {
    throw "Repositório não encontrado: $RepoPath"
}

$pythonExe = Get-OverseerPython -VenvPath $VenvPath -PythonPath $PythonPath

$versionRaw = & $pythonExe -c "import sys; print('%d.%d' % sys.version_info[:2])"
$parts = $versionRaw.Split(".")
$major = [int]$parts[0]
$minor = [int]$parts[1]
if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 11)) {
    throw "Python 3.11+ é necessário (encontrado $versionRaw)."
}
Write-Host "Python $versionRaw OK."

if (-not (Test-Path -LiteralPath $VenvPath)) {
    Write-Host "A criar venv em $VenvPath ..."
    & $pythonExe -m venv $VenvPath
}

$venvPython = Join-Path $VenvPath "Scripts\python.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -e $RepoPath

$agent = Join-Path $VenvPath "Scripts\overseer-agent.exe"
if (-not (Test-Path -LiteralPath $agent)) {
    throw "overseer-agent não foi instalado em $agent"
}

if ($SshTarget) {
    Write-Host "A configurar .env.overseer automaticamente ..."
    $initArgs = @{ SshTarget = $SshTarget; LocalPort = $LocalPort }
    if ($IdentityFile) { $initArgs["IdentityFile"] = $IdentityFile }
    & (Join-Path $OverseerScriptDir "Initialize-OverseerEnv.ps1") @initArgs
    Write-Host "Instalado e configurado. Próximos passos:"
    Write-Host "  1. .\scripts\windows\register-infra-tasks.ps1 -SshTarget $SshTarget"
    Write-Host "  2. Smoke test (com túnel ativo): .\scripts\windows\heartbeat.ps1"
}
else {
    Write-Host "Instalado. Próximos passos:"
    Write-Host "  1. .\scripts\windows\Initialize-OverseerEnv.ps1 -SshTarget <user>@<servidor>"
    Write-Host "  2. .\scripts\windows\register-infra-tasks.ps1 -SshTarget <user>@<servidor>"
    Write-Host "  3. Smoke test (precisa do túnel SSH ativo): .\scripts\windows\heartbeat.ps1"
}
