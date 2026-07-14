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

function Write-Utf8JsonFile {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Json
    )
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $Json, $utf8NoBom)
}

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

function ConvertTo-ShortHeartbeatError {
    param([object]$ErrorValue)
    $message = [string]$ErrorValue
    $message = $message -replace '[\r\n]+', ' '
    if ($message.Length -gt 240) { return $message.Substring(0, 240) }
    return $message
}

$PayloadFile = Join-Path ([System.IO.Path]::GetTempPath()) ("overseer-heartbeat-payload-{0}.json" -f ([guid]::NewGuid().ToString("N")))
$Collector = Join-Path $PSScriptRoot "collect-taskscheduler-info.ps1"
$CatalogJson = Join-Path $RunnersRoot "catalog.json"

try {
    try {
        if (-not (Test-Path -LiteralPath $Collector)) {
            throw "Collector Task Scheduler não encontrado: $Collector"
        }
        $json = & $Collector -CatalogJson $CatalogJson
        if ($LASTEXITCODE -and $LASTEXITCODE -ne 0) {
            throw "Collector Task Scheduler terminou com código $LASTEXITCODE"
        }
        Write-Utf8JsonFile -Path $PayloadFile -Json $json
    }
    catch {
        $fallback = [ordered]@{
            task_scheduler = [ordered]@{
                ok = $false
                collected_at = (Get-Date).ToUniversalTime().ToString("o")
                host_id = $env:OVERSEER_HOST_ID
                error = ConvertTo-ShortHeartbeatError $_
                pipelines = @()
            }
        }
        Write-Utf8JsonFile -Path $PayloadFile -Json ($fallback | ConvertTo-Json -Depth 5 -Compress)
    }

    & $Python -m overseer_agent heartbeat --payload-file $PayloadFile
    exit $LASTEXITCODE
}
finally {
    if (Test-Path -LiteralPath $PayloadFile) {
        Remove-Item -LiteralPath $PayloadFile -Force
    }
}
