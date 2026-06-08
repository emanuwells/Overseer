<#
.SYNOPSIS
    Mostra o nome do catálogo YAML esperado para esta máquina.
#>
param(
    [string]$RepoRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
)

$raw = $env:COMPUTERNAME
$normalized = ($raw -replace '[^A-Za-z0-9_-]+', '-').Trim('-')
$catalogName = "$normalized.yaml"
$catalogPath = Join-Path $RepoRoot "deploy\runners\$catalogName"

Write-Host "Hostname: $raw"
Write-Host "Catálogo esperado: deploy/runners/$catalogName"
if (Test-Path -LiteralPath $catalogPath) {
    Write-Host "Estado: encontrado no repo"
}
else {
    Write-Host "Estado: em falta — criar com new-host-catalog.ps1 ou manualmente"
}
