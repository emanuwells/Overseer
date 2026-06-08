<#
.SYNOPSIS
    Wrapper Windows para scripts\provision_runners.py.

.DESCRIPTION
    Gera manifests e run.ps1 por pipeline. O catálogo resolve automaticamente para
    deploy/runners/<hostname>.yaml (lê OVERSEER_HOST_ID ou hostname).

.EXAMPLE
    .\provision-runners.ps1 -Register
#>
param(
    [string]$Catalog = "",
    [string]$HostId = "auto",
    [string]$VenvPath = (Join-Path $env:LOCALAPPDATA "overseer-venv"),
    [string]$CatalogJsonOut = (Join-Path $env:USERPROFILE "overseer-runners\catalog.json"),
    [switch]$Register
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$venvPython = Join-Path $VenvPath "Scripts\python.exe"
$python = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { "python" }

$provision = Join-Path $RepoRoot "scripts\provision_runners.py"

$pyArgs = @(
    $provision,
    "--platform", "windows",
    "--host-id", $HostId,
    "--venv", $VenvPath,
    "--repo-root", $RepoRoot,
    "--catalog-json-out", $CatalogJsonOut
)
if ($Catalog) { $pyArgs += @("--catalog", $Catalog) }
if ($Register) { $pyArgs += "--register" }

& $python @pyArgs
Write-Host "Catálogo gerado: $CatalogJsonOut"
Write-Host "Migrar o Task Scheduler (1.ª vez): .\scripts\windows\migrate-taskscheduler.ps1 -CatalogJson `"$CatalogJsonOut`""
