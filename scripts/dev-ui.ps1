param(
    [switch]$Pull,
    [string]$Port = "8090",
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root "..")

$envExample = "docs/resources/templates/.env.example"
if (-not (Test-Path ".env")) {
    if (-not (Test-Path $envExample)) {
        throw "Falta .env e $envExample"
    }
    Copy-Item $envExample ".env"
    Write-Host "Criado .env a partir do exemplo. Ajusta OVERSEER_API_TOKEN se necessario."
}

& (Join-Path $root "generate-frontend-config.ps1")

$compose = "docker compose --project-directory . -f docker/docker-compose.yml"
if ($Pull) { Invoke-Expression "$compose pull" }
Invoke-Expression "$compose up --build -d"

$health = "http://127.0.0.1:$Port/v1/health"
$ui = "http://127.0.0.1:$Port/ui/operations"
$deadline = (Get-Date).AddSeconds(180)

while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-RestMethod -Uri $health -Headers @{ Accept = "application/json" } -TimeoutSec 5
        if ($response.ok) {
            Write-Host ""
            Write-Host "Overseer pronto com UI e API local:"
            Write-Host "  UI:  $ui"
            Write-Host "  API: http://127.0.0.1:$Port/v1/health"
            Write-Host ""
            Write-Host "O token em .env e injectado no contentor ao arrancar."
            Write-Host "Para hot-reload do frontend: scripts/dev-frontend.ps1"
            if ($OpenBrowser) { Start-Process $ui }
            exit 0
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

Write-Host "Overseer arrancou, mas o health check nao respondeu em 180s: $health"
exit 1
