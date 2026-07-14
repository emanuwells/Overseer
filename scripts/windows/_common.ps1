# Helpers partilhados por scripts/windows/*.ps1
# Uso: . (Join-Path $PSScriptRoot '_common.ps1')

$OverseerScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$OverseerRepoRoot = Split-Path -Parent (Split-Path -Parent $OverseerScriptDir)

function Import-OverseerEnvFile {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { return }
    foreach ($raw in Get-Content -LiteralPath $Path -Encoding UTF8) {
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith("#") -or ($line -notmatch "=")) { continue }
        $key, $value = $line.Split("=", 2)
        [Environment]::SetEnvironmentVariable($key.Trim(), $value.Trim(), "Process")
    }
}

function Write-OverseerEnvFile {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string[]]$Lines
    )
    $dir = Split-Path -Parent $Path
    if ($dir -and -not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    $content = ($Lines -join "`n") + "`n"
    $utf8 = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($Path, $content, $utf8)
}

function Get-OverseerPython {
    param(
        [string]$VenvPath = (Join-Path $env:LOCALAPPDATA "overseer-venv"),
        [string]$PythonPath = ""
    )
    if ($PythonPath) {
        if (-not (Test-Path -LiteralPath $PythonPath)) {
            throw "Python não encontrado: $PythonPath"
        }
        return $PythonPath
    }
    $venvPython = Join-Path $VenvPath "Scripts\python.exe"
    if (Test-Path -LiteralPath $venvPython) { return $venvPython }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if (-not $python) { throw "Python não encontrado no PATH nem em $venvPython." }
    return $python.Source
}
