<#
.SYNOPSIS
    Wrapper Windows para scripts\provision_runners.py.

.DESCRIPTION
    Gera manifests e run.ps1 por pipeline. O catálogo resolve automaticamente para
    OVERSEER_RUNNERS_DIR/<hostname>.yaml (lê OVERSEER_HOST_ID ou hostname).

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
. (Join-Path $PSScriptRoot "_common.ps1")

$python = Get-OverseerPython -VenvPath $VenvPath
$provision = Join-Path $OverseerRepoRoot "scripts\provision_runners.py"

$pyArgs = @(
    $provision,
    "--platform", "windows",
    "--host-id", $HostId,
    "--venv", $VenvPath,
    "--repo-root", $OverseerRepoRoot,
    "--catalog-json-out", $CatalogJsonOut
)
if ($Catalog) { $pyArgs += @("--catalog", $Catalog) }
if ($Register) { $pyArgs += "--register" }

& $python @pyArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Catálogo gerado: $CatalogJsonOut"
Write-Host "Registar Task Scheduler: .\scripts\windows\register-pipeline-task.ps1 -PipelineId <id>"
Write-Host "Setup completo: .\scripts\windows\setup-pipeline-windows.ps1 -PipelineId <id> -TestRun"
Write-Host "Guia: docs\windows-pipeline-onboarding.md"
