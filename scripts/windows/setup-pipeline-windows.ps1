<#
.SYNOPSIS
    Configura um pipeline Windows no Overseer: provisionar, Task Scheduler e validação.

.DESCRIPTION
    Fluxo recomendado para uma máquina nova ou para acrescentar um pipeline:
      1. Verificar túnel SSH (infra Overseer)
      2. provision-runners.ps1 -Register
      3. register-pipeline-task.ps1 (Task Scheduler, conta não admin)
      4. (opcional) teste manual do run.ps1
      5. inventário Task Scheduler + heartbeat

    Pré-requisito na 1.ª máquina: bootstrap-windows.ps1 (agente + túnel + heartbeat).

.EXAMPLE
    .\setup-pipeline-windows.ps1 -PipelineId windows_pipeline -SshTarget operator@server.example.com

.EXAMPLE
    .\setup-pipeline-windows.ps1 -PipelineId example_pipeline -TestRun
#>
param(
    [Parameter(Mandatory = $true)][string]$PipelineId,
    [string]$SshTarget = "",
    [int]$TunnelPort = 18090,
    [string]$VenvPath = (Join-Path $env:LOCALAPPDATA "overseer-venv"),
    [string]$CatalogJson = (Join-Path $env:USERPROFILE "overseer-runners\catalog.json"),
    [string]$TaskName = "",
    [string]$DailyAt = "",
    [string[]]$RemoveLegacyTaskNames = @(),
    [switch]$SkipProvision,
    [switch]$SkipTunnelCheck,
    [switch]$SkipHeartbeat,
    [switch]$TestRun
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")

function Test-OverseerTunnel {
    param([int]$Port)
    $listening = netstat -an | Select-String "127\.0\.0\.1:$Port.*LISTENING"
    return [bool]$listening
}

if (-not $SkipTunnelCheck) {
    if (-not (Test-OverseerTunnel -Port $TunnelPort)) {
        Write-Warning "Túnel SSH não detectado em 127.0.0.1:$TunnelPort."
        $tunnelTask = Get-ScheduledTask -TaskName "Overseer SSH Tunnel" -ErrorAction SilentlyContinue
        if ($tunnelTask) {
            Write-Host "A arrancar tarefa 'Overseer SSH Tunnel'..."
            Start-ScheduledTask -TaskName "Overseer SSH Tunnel"
            Start-Sleep -Seconds 3
        }
        if (-not (Test-OverseerTunnel -Port $TunnelPort)) {
            Write-Host "Arranca manualmente (outra janela):"
            Write-Host "  powershell -ExecutionPolicy Bypass -File `"$OverseerScriptDir\ssh-tunnel.ps1`" -SshTarget $SshTarget -LocalPort $TunnelPort"
            Write-Host "Ou corre primeiro: .\scripts\windows\bootstrap-windows.ps1 -RepoPath $OverseerRepoRoot -SshTarget $SshTarget"
            throw "Túnel em falta — o Overseer não recebe runs sem API em loopback."
        }
    }
    Write-Host "Túnel OK em 127.0.0.1:$TunnelPort"
}

if (-not $SkipProvision) {
    Write-Host "== Provisionar runners =="
    & (Join-Path $OverseerScriptDir "provision-runners.ps1") -Register -VenvPath $VenvPath -CatalogJsonOut $CatalogJson
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "== Registar tarefa no Task Scheduler =="
$taskArgs = @{
    PipelineId           = $PipelineId
    CatalogJson          = $CatalogJson
}
if ($TaskName) { $taskArgs["TaskName"] = $TaskName }
if ($DailyAt) { $taskArgs["DailyAt"] = $DailyAt }
if ($RemoveLegacyTaskNames.Count -gt 0) { $taskArgs["RemoveLegacyTaskNames"] = $RemoveLegacyTaskNames }
& (Join-Path $OverseerScriptDir "register-pipeline-task.ps1") @taskArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$catalog = Get-Content -LiteralPath $CatalogJson -Raw | ConvertFrom-Json
$entry = $catalog.pipelines | Where-Object { $_.id -eq $PipelineId } | Select-Object -First 1
$runPs = [string]$entry.run_ps
$taskLabel = if ($TaskName) { $TaskName } else { [string]$entry.task_name }

if ($TestRun -and $runPs) {
    Write-Host "== Teste manual do runner =="
    Import-OverseerEnvFile (Join-Path $env:USERPROFILE "overseer-runners\.env.overseer")
    $env:NO_PROXY = "127.0.0.1,localhost"
    $env:HTTP_PROXY = ""
    $env:HTTPS_PROXY = ""
    $env:ALL_PROXY = ""
    & $runPs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

if (-not $SkipHeartbeat) {
    Write-Host "== Inventário Task Scheduler + heartbeat =="
    & (Join-Path $OverseerScriptDir "collect-taskscheduler-info.ps1") -CatalogJson $CatalogJson
    & (Join-Path $OverseerScriptDir "heartbeat.ps1")
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host ""
Write-Host "Setup concluído para pipeline '$PipelineId'."
Write-Host "  Tarefa: $taskLabel"
Write-Host "  Runner: $runPs"
Write-Host "Validar no Overseer: pipeline_id=$PipelineId e host_id do .env.overseer"
