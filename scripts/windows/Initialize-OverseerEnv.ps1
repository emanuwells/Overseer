<#
.SYNOPSIS
    Cria o .env.overseer da máquina automaticamente.

.DESCRIPTION
    Gera %USERPROFILE%\overseer-runners\.env.overseer com:
      - OVERSEER_API_URL: http://127.0.0.1:<LocalPort> (porta do túnel SSH)
      - OVERSEER_HOST_ID: hostname local normalizado (estável e legível)
      - OVERSEER_API_TOKEN: lido por SSH de ~/overseer-runners/.env.overseer no
        servidor de prod (ou passado em -ApiToken)

    O ficheiro fica com ACL restrita ao utilizador atual. Idempotente: não
    sobrescreve um .env.overseer existente sem -Force.

.EXAMPLE
    .\Initialize-OverseerEnv.ps1 -SshTarget eferreira@195.23.9.32

.EXAMPLE
    .\Initialize-OverseerEnv.ps1 -ApiToken "<token>" -Force
#>
param(
    [string]$SshTarget = "",
    [string]$ApiToken = "",
    [int]$LocalPort = 18090,
    [string]$HostId = "",
    [string]$RunnersRoot = (Join-Path $env:USERPROFILE "overseer-runners"),
    [switch]$Force
)

$ErrorActionPreference = "Stop"

function Get-NormalizedHostId {
    param([string]$Value)
    $normalized = ($Value -replace '[^A-Za-z0-9_-]+', '-').Trim('-')
    return $normalized
}

$envFile = Join-Path $RunnersRoot ".env.overseer"

if ((Test-Path -LiteralPath $envFile) -and -not $Force) {
    Write-Host ".env.overseer já existe em $envFile (usa -Force para regravar). Nada feito."
    return
}

if (-not (Test-Path -LiteralPath $RunnersRoot)) {
    New-Item -ItemType Directory -Path $RunnersRoot -Force | Out-Null
}

# host_id: argumento explícito, senão hostname normalizado.
if (-not $HostId) { $HostId = $env:COMPUTERNAME }
$HostId = Get-NormalizedHostId -Value $HostId

# token: argumento explícito tem prioridade; senão fetch via SSH.
$token = $ApiToken
if (-not $token) {
    if (-not $SshTarget) {
        throw "Sem -ApiToken nem -SshTarget: não há como obter o OVERSEER_API_TOKEN."
    }
    Write-Host "A obter o token via SSH de $SshTarget ..."
    $remoteCmd = "grep '^OVERSEER_API_TOKEN=' ~/overseer-runners/.env.overseer | cut -d= -f2-"
    $token = (& ssh -o BatchMode=yes $SshTarget $remoteCmd | Select-Object -First 1)
    if ($LASTEXITCODE -ne 0 -or -not $token) {
        throw "Não foi possível ler o token via SSH. Confirma a chave SSH e ~/overseer-runners/.env.overseer no servidor."
    }
    $token = $token.Trim()
}

$apiUrl = "http://127.0.0.1:$LocalPort"
$content = @(
    "# Gerado automaticamente por Initialize-OverseerEnv.ps1. Não versionar.",
    "OVERSEER_API_URL=$apiUrl",
    "OVERSEER_API_TOKEN=$token",
    "OVERSEER_HOST_ID=$HostId"
) -join "`n"

Set-Content -LiteralPath $envFile -Value $content -Encoding UTF8 -NoNewline

# ACL restrita ao utilizador atual.
& icacls $envFile /inheritance:r /grant:r "$($env:USERNAME):(R,W)" | Out-Null

Write-Host "Escrito $envFile"
Write-Host "  OVERSEER_API_URL=$apiUrl"
Write-Host "  OVERSEER_HOST_ID=$HostId"
Write-Host "  OVERSEER_API_TOKEN=(definido)"
