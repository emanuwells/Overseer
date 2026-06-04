param(
    [switch]$Pull,
    [string]$Port = "8090"
)

$ErrorActionPreference = "Stop"

if ($Pull) {
    docker compose pull
}

docker compose up --build -d

$health = "http://127.0.0.1:$Port/v1/health"
$ui = "http://127.0.0.1:$Port/ui/"
$deadline = (Get-Date).AddSeconds(120)

while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-RestMethod -Uri $health -Headers @{ Accept = "application/json" } -TimeoutSec 5
        if ($response.ok) {
            Write-Host "Overseer pronto: $ui"
            Write-Host "API: http://127.0.0.1:$Port/docs"
            exit 0
        }
    } catch {
        Start-Sleep -Seconds 2
    }
}

Write-Host "Overseer arrancou, mas o health check nao respondeu em 120s: $health"
exit 1
