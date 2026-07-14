param(
    [string]$EnvFile = "secrets/.env",
    [string]$OutFile = "frontend/public/overseer-config.js"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$envPath = Join-Path $root $EnvFile
$outPath = Join-Path $root $OutFile

$token = ""
if (Test-Path $envPath) {
    $line = Get-Content $envPath | Where-Object { $_ -match '^\s*OVERSEER_API_TOKEN\s*=' } | Select-Object -First 1
    if ($line) {
        $token = ($line -split '=', 2)[1].Trim().Trim('"').Trim("'")
    }
}

$escaped = $token.Replace('\', '\\').Replace('"', '\"')
$content = @"
// Gerado por scripts/generate-frontend-config.ps1 — não versionar.
window.OVERSEER_CONFIG = window.OVERSEER_CONFIG || {
  apiToken: "$escaped",
};
"@

New-Item -ItemType Directory -Force -Path (Split-Path $outPath) | Out-Null
Set-Content -Path $outPath -Value $content -Encoding UTF8
Write-Host "Config frontend: $outPath"
