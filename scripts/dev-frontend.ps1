param(
    [ValidateSet("local", "prod")]
    [string]$Mode = "local",
    [string]$SshTarget = "",
    [int]$ApiPort = 8090,
    [int]$DevPort = 5173,
    [string]$WorkDir = ""
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = (Resolve-Path (Join-Path $root "..")).Path
$frontendSrc = Join-Path $repoRoot "frontend"

if (-not $WorkDir) {
    $WorkDir = Join-Path $env:LOCALAPPDATA "Temp\overseer-frontend-dev"
}

function Sync-FrontendWorkdir {
    New-Item -ItemType Directory -Force -Path $WorkDir | Out-Null
    $exclude = @("node_modules", "dist", "dist-nginx")
    Get-ChildItem $frontendSrc -Force | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
        $dest = Join-Path $WorkDir $_.Name
        if ($_.PSIsContainer) {
            if (Test-Path $dest) { Remove-Item -Recurse -Force $dest }
            Copy-Item $_.FullName $dest -Recurse -Force
        } else {
            Copy-Item $_.FullName $dest -Force
        }
    }
}

function Stop-Tunnel {
    Get-Job -Name "overseer-ssh-tunnel" -ErrorAction SilentlyContinue | Stop-Job -PassThru | Remove-Job -Force
}

if ($Mode -eq "prod") {
    if (-not $SshTarget) {
        $SshTarget = $env:OVERSEER_SSH_TARGET
    }
    if (-not $SshTarget) {
        throw "Modo prod requer -SshTarget ou variavel OVERSEER_SSH_TARGET (ex. user@baze2.cm-maia.pt)"
    }
    Stop-Tunnel
    Write-Host "Tunel SSH: localhost:$ApiPort -> ${SshTarget}:127.0.0.1:8090"
    Start-Job -Name "overseer-ssh-tunnel" -ScriptBlock {
        param($target, $port)
        ssh -N -L "${port}:127.0.0.1:8090" $target
    } -ArgumentList $SshTarget, $ApiPort | Out-Null
    Start-Sleep -Seconds 2
}

if ($Mode -eq "local") {
    try {
        Invoke-RestMethod -Uri "http://127.0.0.1:$ApiPort/v1/health" -TimeoutSec 3 | Out-Null
    } catch {
        Write-Host "API local indisponivel. A arrancar Docker..."
        & (Join-Path $root "dev-ui.ps1")
    }
}

& (Join-Path $root "generate-frontend-config.ps1") -EnvFile "secrets/.env"

Sync-FrontendWorkdir
Set-Location $WorkDir

if (-not (Test-Path "node_modules")) {
    npm ci
}

$env:VITE_API_PROXY_TARGET = "http://127.0.0.1:$ApiPort"
$env:VITE_DEV_PORT = "$DevPort"
$uiUrl = "http://127.0.0.1:$DevPort/ui/operations"

Write-Host ""
Write-Host "Vite dev (proxy /v1 -> http://127.0.0.1:$ApiPort)"
Write-Host "  UI: $uiUrl"
Write-Host "  Modo: $Mode"
Write-Host ""
Write-Host "Ctrl+C para parar. Tunel SSH (modo prod) sera terminado ao sair."

try {
    npm run dev -- --host 127.0.0.1 --port $DevPort
} finally {
    if ($Mode -eq "prod") { Stop-Tunnel }
}
