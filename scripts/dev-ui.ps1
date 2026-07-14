param(
    [switch]$Pull,
    [string]$Port = "8090",
    [switch]$OpenBrowser
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location (Join-Path $root "..")

$null = & (Join-Path $root "ensure-env.ps1")
& (Join-Path $root "generate-frontend-config.ps1") -EnvFile "secrets/.env"

$compose = "docker compose --project-directory . --env-file secrets/.env -f docker/docker-compose.yml"
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
            Write-Host "Config em secrets/.env; token injectado no contentor ao arrancar."
            Write-Host "Producao nginx: http://<host>/Overseer/ (scripts/deploy-nginx-frontend.sh)"
            Write-Host "Hot-reload frontend: scripts/dev-frontend.ps1"
            if ($OpenBrowser) { Start-Process $ui }
            exit 0
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

Write-Host "Overseer arrancou, mas o health check nao respondeu em 180s: $health"
exit 1
