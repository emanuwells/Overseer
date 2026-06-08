# Instala overseer-agent no Windows.
# Para o fluxo completo (venv dedicado, verificação de Python, túnel SSH e
# tarefas agendadas) usar antes: scripts\windows\install-runner.ps1
$Root = Split-Path -Parent $PSScriptRoot
$Installer = Join-Path $Root "scripts\windows\install-runner.ps1"
if (Test-Path -LiteralPath $Installer) {
    Write-Host "Use o instalador completo:"
    Write-Host "  $Installer -RepoPath `"$Root`""
}
Set-Location $Root
python -m pip install -e .
Write-Host "Run (com tunel SSH ativo): python -m overseer_agent heartbeat"
