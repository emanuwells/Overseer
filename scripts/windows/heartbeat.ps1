<#
.SYNOPSIS
    Envia um heartbeat do agente Overseer, carregando o .env.overseer.

.DESCRIPTION
    Wrapper usado pela tarefa agendada "Overseer Heartbeat". Carrega a
    configuração partilhada (URL + token + host_id) antes de invocar o agente,
    para o heartbeat agendado ter as credenciais corretas.
#>
param(
    [string]$RunnersRoot = (Join-Path $env:USERPROFILE "overseer-runners"),
    [string]$VenvPath = (Join-Path $env:LOCALAPPDATA "overseer-venv")
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")

Import-OverseerEnvFile (Join-Path $RunnersRoot ".env.overseer")

$env:NO_PROXY = "127.0.0.1,localhost"
$env:HTTP_PROXY = ""
$env:HTTPS_PROXY = ""
$env:ALL_PROXY = ""

if (-not $env:OVERSEER_API_URL) {
    throw "OVERSEER_API_URL em falta. Corre Initialize-OverseerEnv.ps1 ou define $RunnersRoot\.env.overseer"
}

$Venv = $env:OVERSEER_VENV
if (-not $Venv) { $Venv = $VenvPath }
$Python = Join-Path $Venv "Scripts\python.exe"
if (-not (Test-Path -LiteralPath $Python)) {
    throw "Python do venv não encontrado em $Python. Corre install-runner.ps1 primeiro."
}

& $Python -m overseer_agent heartbeat
exit $LASTEXITCODE
