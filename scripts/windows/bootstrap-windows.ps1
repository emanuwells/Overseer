<#
.SYNOPSIS
    Onboarding completo de uma máquina Windows no Overseer, num só comando.

.DESCRIPTION
    Executa por ordem:
      1. install-runner.ps1        (venv + pip install -e)
      2. Initialize-OverseerEnv.ps1 (.env.overseer automático: URL, host_id, token via SSH)
      3. register-infra-tasks.ps1  (túnel SSH + heartbeat no Task Scheduler)
      4. arranca já a tarefa do túnel SSH

    Pré-requisito: SSH por chave (sem password) para o servidor de prod, e
    ~/overseer-runners/.env.overseer já existente no servidor (contém o token).

.EXAMPLE
    .\bootstrap-windows.ps1 -RepoPath "C:\Dev\Repos\emanuwells\Overseer" -SshTarget eferreira@195.23.9.32
#>
param(
    [Parameter(Mandatory = $true)][string]$RepoPath,
    [Parameter(Mandatory = $true)][string]$SshTarget,
    [int]$LocalPort = 18090,
    [int]$HeartbeatMinutes = 5,
    [string]$VenvPath = (Join-Path $env:LOCALAPPDATA "overseer-venv"),
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "== 1/4 Instalar agente =="
& (Join-Path $ScriptDir "install-runner.ps1") -RepoPath $RepoPath -VenvPath $VenvPath

Write-Host "== 2/4 Configurar .env.overseer =="
$initArgs = @{
    SshTarget = $SshTarget
    LocalPort = $LocalPort
}
if ($Force) { $initArgs["Force"] = $true }
& (Join-Path $ScriptDir "Initialize-OverseerEnv.ps1") @initArgs

Write-Host "== 3/4 Registar túnel SSH + heartbeat =="
& (Join-Path $ScriptDir "register-infra-tasks.ps1") `
    -SshTarget $SshTarget -LocalPort $LocalPort -HeartbeatMinutes $HeartbeatMinutes -VenvPath $VenvPath

Write-Host "== 4/4 Arrancar túnel SSH =="
Start-ScheduledTask -TaskName "Overseer SSH Tunnel"

Write-Host ""
Write-Host "Bootstrap concluído."
Write-Host "  .env.overseer: $(Join-Path $env:USERPROFILE 'overseer-runners\.env.overseer')"
Write-Host "Próximo passo (catálogo deploy/runners/<hostname>.yaml):"
Write-Host "  .\scripts\windows\show-host-catalog.ps1"
Write-Host "  .\scripts\windows\new-host-catalog.ps1 -Template _medidata.yaml   # se ainda não existir no repo"
Write-Host "  .\scripts\windows\provision-runners.ps1 -Register"
Write-Host "  .\scripts\windows\migrate-taskscheduler.ps1 -CatalogJson `"$env:USERPROFILE\overseer-runners\catalog.json`""
