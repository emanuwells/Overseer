<#
.SYNOPSIS
    Envia um heartbeat do agente Overseer, carregando o .env.overseer.

.DESCRIPTION
    Wrapper usado pela tarefa agendada "Overseer Heartbeat". Carrega a
    configuração partilhada (URL + token + host_id) antes de invocar o agente,
    para o heartbeat agendado ter as credenciais corretas.
#>
param(
    [string]$RunnersRoot = (Join-Path $env:USERPROFILE "overseer-runners")
)

$ErrorActionPreference = "Stop"

function Import-EnvFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    foreach ($raw in Get-Content -LiteralPath $Path) {
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith("#") -or ($line -notmatch "=")) { continue }
        $key, $value = $line.Split("=", 2)
        [Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
    }
}

Import-EnvFile (Join-Path $RunnersRoot ".env.overseer")

$Venv = $env:OVERSEER_VENV
if (-not $Venv) { $Venv = Join-Path $env:LOCALAPPDATA "overseer-venv" }
$Agent = Join-Path $Venv "Scripts\overseer-agent.exe"

& $Agent heartbeat
exit $LASTEXITCODE
