$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envFile = if ($env:OVERSEER_ENV_FILE) { $env:OVERSEER_ENV_FILE } else { Join-Path $root "secrets\.env" }
$template = Join-Path $root "docs\resources\templates\.env.example"
$legacy = Join-Path $root ".env"

if ((Test-Path $legacy) -and -not (Test-Path $envFile)) {
    New-Item -ItemType Directory -Force -Path (Split-Path $envFile) | Out-Null
    Move-Item $legacy $envFile
    Write-Host "Movido .env da raiz para secrets/.env"
}

if (-not (Test-Path $envFile)) {
    if (-not (Test-Path $template)) {
        throw "Falta $template"
    }
    New-Item -ItemType Directory -Force -Path (Split-Path $envFile) | Out-Null
    Copy-Item $template $envFile
    Write-Host "Criado secrets/.env a partir do exemplo. Ajusta OVERSEER_API_TOKEN se necessario."
}

$env:OVERSEER_ENV_FILE = $envFile
return $envFile
