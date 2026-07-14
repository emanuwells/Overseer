<#
.SYNOPSIS
    Cria <OVERSEER_RUNNERS_DIR>/<hostname>.yaml a partir do exemplo público.

.DESCRIPTION
    Usar na primeira vez numa máquina Windows quando o catálogo ainda não
    existe no diretório privado de configuração.

.EXAMPLE
    .\new-host-catalog.ps1 -Template _example.yaml
#>
param(
    [string]$Template = "_example.yaml",
    [string]$RepoRoot = "",
    [string]$RunnersDir = $env:OVERSEER_RUNNERS_DIR,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")
if (-not $RepoRoot) { $RepoRoot = $OverseerRepoRoot }
if (-not $RunnersDir) { throw "Define OVERSEER_RUNNERS_DIR ou passa -RunnersDir." }

$raw = $env:COMPUTERNAME
$normalized = ($raw -replace '[^A-Za-z0-9_-]+', '-').Trim('-')
$src = Join-Path $RepoRoot "deploy\runners\$Template"
$dest = Join-Path $RunnersDir "$normalized.yaml"

if (-not (Test-Path -LiteralPath $src)) {
    throw "Template não encontrado: $src"
}
if ((Test-Path -LiteralPath $dest) -and -not $Force) {
    Write-Host "Já existe $dest (usa -Force para sobrescrever)."
    exit 0
}

New-Item -ItemType Directory -Path $RunnersDir -Force | Out-Null
Copy-Item -LiteralPath $src -Destination $dest -Force
Write-Host "Criado: $dest"
Write-Host "Próximo passo: ajustar o catálogo privado e executar provision-runners.ps1 -Register"
