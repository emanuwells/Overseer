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
    .\bootstrap-windows.ps1 -RepoPath "C:\Dev\Repos\your-organization\Overseer" -SshTarget operator@server.example.com
#>
param(
    [Parameter(Mandatory = $true)][string]$RepoPath,
    [Parameter(Mandatory = $true)][string]$SshTarget,
    [int]$LocalPort = 18090,
    [int]$HeartbeatMinutes = 5,
    [string]$VenvPath = (Join-Path $env:LOCALAPPDATA "overseer-venv"),
    [string]$PythonPath = "",
    [string]$IdentityFile = "",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")

Write-Host "== 1/4 Instalar agente =="
$installArgs = @{ RepoPath = $RepoPath; VenvPath = $VenvPath }
if ($PythonPath) { $installArgs["PythonPath"] = $PythonPath }
& (Join-Path $OverseerScriptDir "install-runner.ps1") @installArgs

Write-Host "== 2/4 Configurar .env.overseer =="
$initArgs = @{
    SshTarget = $SshTarget
    LocalPort = $LocalPort
}
if ($Force) { $initArgs["Force"] = $true }
if ($IdentityFile) { $initArgs["IdentityFile"] = $IdentityFile }
& (Join-Path $OverseerScriptDir "Initialize-OverseerEnv.ps1") @initArgs

Write-Host "== 3/4 Registar túnel SSH + heartbeat =="
$infraArgs = @{
    SshTarget = $SshTarget
    LocalPort = $LocalPort
    HeartbeatMinutes = $HeartbeatMinutes
    VenvPath = $VenvPath
}
if ($IdentityFile) { $infraArgs["IdentityFile"] = $IdentityFile }
& (Join-Path $OverseerScriptDir "register-infra-tasks.ps1") @infraArgs

Write-Host "== 4/4 Arrancar túnel SSH =="
Start-ScheduledTask -TaskName "Overseer SSH Tunnel"

Write-Host ""
Write-Host "Bootstrap concluído."
Write-Host "  .env.overseer: $(Join-Path $env:USERPROFILE 'overseer-runners\.env.overseer')"
Write-Host "Próximo passo (catálogo privado OVERSEER_RUNNERS_DIR/<hostname>.yaml):"
Write-Host "  .\scripts\windows\show-host-catalog.ps1"
Write-Host "  .\scripts\windows\new-host-catalog.ps1 -Template _example.yaml   # se ainda não existir no diretório privado"
Write-Host "  .\scripts\windows\setup-pipeline-windows.ps1 -PipelineId <pipeline_id> -SshTarget $SshTarget -TestRun"
Write-Host "  Guia: docs\windows-pipeline-onboarding.md"
