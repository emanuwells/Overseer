<#
.SYNOPSIS
    Regista as tarefas de infraestrutura do Overseer no Task Scheduler.

.DESCRIPTION
    Cria/atualiza duas tarefas que devem estar sempre ativas:
      - "Overseer SSH Tunnel": mantém o túnel para a API central (At logon,
        reinicia se morrer).
      - "Overseer Heartbeat": envia heartbeat a cada N minutos, para o painel
        Ambiente saber que a máquina e o túnel estão vivos.

.EXAMPLE
    .\register-infra-tasks.ps1 -SshTarget eferreira@195.23.9.32
#>
param(
    [Parameter(Mandatory = $true)][string]$SshTarget,
    [int]$LocalPort = 18090,
    [int]$HeartbeatMinutes = 5,
    [string]$VenvPath = (Join-Path $env:LOCALAPPDATA "overseer-venv")
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TunnelScript = Join-Path $ScriptDir "ssh-tunnel.ps1"
$HeartbeatScript = Join-Path $ScriptDir "heartbeat.ps1"
$Agent = Join-Path $VenvPath "Scripts\overseer-agent.exe"

if (-not (Test-Path -LiteralPath $TunnelScript)) { throw "Não encontrei $TunnelScript" }
if (-not (Test-Path -LiteralPath $HeartbeatScript)) { throw "Não encontrei $HeartbeatScript" }
if (-not (Test-Path -LiteralPath $Agent)) { throw "overseer-agent não encontrado em $Agent. Corre install-runner.ps1 primeiro." }

$pwsh = (Get-Command powershell.exe).Source

# --- Tarefa 1: túnel SSH (At logon, reinicia se cair) ---
$tunnelArgs = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$TunnelScript`" -SshTarget $SshTarget -LocalPort $LocalPort"
$tunnelAction = New-ScheduledTaskAction -Execute $pwsh -Argument $tunnelArgs
$tunnelTrigger = New-ScheduledTaskTrigger -AtLogOn
$tunnelSettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0)

Register-ScheduledTask -TaskName "Overseer SSH Tunnel" `
    -Action $tunnelAction -Trigger $tunnelTrigger -Settings $tunnelSettings `
    -Description "Túnel SSH em loopback para a API central do Overseer." -Force | Out-Null
Write-Host "Tarefa 'Overseer SSH Tunnel' registada."

# --- Tarefa 2: heartbeat periódico (carrega .env.overseer via heartbeat.ps1) ---
$hbArgs = "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$HeartbeatScript`""
$hbAction = New-ScheduledTaskAction -Execute $pwsh -Argument $hbArgs
$hbTrigger = New-ScheduledTaskTrigger -Once -At (Get-Date) `
    -RepetitionInterval (New-TimeSpan -Minutes $HeartbeatMinutes)
$hbSettings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

Register-ScheduledTask -TaskName "Overseer Heartbeat" `
    -Action $hbAction -Trigger $hbTrigger -Settings $hbSettings `
    -Description "Heartbeat periódico do agente Overseer." -Force | Out-Null
Write-Host "Tarefa 'Overseer Heartbeat' registada (cada $HeartbeatMinutes min)."

Write-Host "Para arrancar já o túnel sem reiniciar a sessão: Start-ScheduledTask -TaskName 'Overseer SSH Tunnel'"
