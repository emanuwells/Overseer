<#
.SYNOPSIS
    Cria deploy/runners/<hostname>.yaml a partir de um template _*.yaml.

.DESCRIPTION
    Usar na primeira vez numa máquina Windows quando o catálogo ainda não
    existe no repo com o hostname correcto. Depois fazer commit + push do ficheiro.

.EXAMPLE
    .\new-host-catalog.ps1 -Template _medidata.yaml
#>
param(
    [string]$Template = "_medidata.yaml",
    [string]$RepoRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$raw = $env:COMPUTERNAME
$normalized = ($raw -replace '[^A-Za-z0-9_-]+', '-').Trim('-')
$src = Join-Path $RepoRoot "deploy\runners\$Template"
$dest = Join-Path $RepoRoot "deploy\runners\$normalized.yaml"

if (-not (Test-Path -LiteralPath $src)) {
    throw "Template não encontrado: $src"
}
if ((Test-Path -LiteralPath $dest) -and -not $Force) {
    Write-Host "Já existe $dest (usa -Force para sobrescrever)."
    exit 0
}

Copy-Item -LiteralPath $src -Destination $dest -Force
Write-Host "Criado: deploy/runners/$normalized.yaml"
Write-Host "Próximo passo: commit + push, depois provision-runners.ps1 -Register"
