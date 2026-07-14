<#
.SYNOPSIS
    Mostra o nome do catálogo YAML esperado para esta máquina.
#>
param(
    [string]$RepoRoot = "",
    [string]$RunnersDir = $env:OVERSEER_RUNNERS_DIR
)

. (Join-Path $PSScriptRoot "_common.ps1")
if (-not $RepoRoot) { $RepoRoot = $OverseerRepoRoot }
if (-not $RunnersDir) { throw "Define OVERSEER_RUNNERS_DIR ou passa -RunnersDir." }

$raw = $env:COMPUTERNAME
$normalized = ($raw -replace '[^A-Za-z0-9_-]+', '-').Trim('-')
$catalogName = "$normalized.yaml"
$catalogPath = Join-Path $RunnersDir $catalogName

Write-Host "Hostname: $raw"
Write-Host "Catálogo esperado: $catalogPath"
if (Test-Path -LiteralPath $catalogPath) {
    Write-Host "Estado: encontrado no diretório privado"
}
else {
    Write-Host "Estado: em falta - criar com new-host-catalog.ps1 ou manualmente"
}
