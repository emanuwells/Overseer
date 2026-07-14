<#
.SYNOPSIS
    Regista ou actualiza uma tarefa de pipeline no Task Scheduler (conta não admin).

.DESCRIPTION
    Lê o catálogo JSON gerado por provision-runners.ps1 e cria a tarefa com
    -RunLevel Limited (sem privilégios de administrador). Por defeito usa
    task_name, schedule e run_ps do catálogo.

    Crons diários simples suportados: "M H * * *" (ex.: "45 7 * * *" -> 07:45).

.EXAMPLE
    .\register-pipeline-task.ps1 -PipelineId windows_pipeline

.EXAMPLE
    .\register-pipeline-task.ps1 -PipelineId example_pipeline -DailyAt "07:30"
#>
param(
    [Parameter(Mandatory = $true)][string]$PipelineId,
    [string]$CatalogJson = (Join-Path $env:USERPROFILE "overseer-runners\catalog.json"),
    [string]$TaskName = "",
    [string]$DailyAt = "",
    [string[]]$RemoveLegacyTaskNames = @(),
    [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_common.ps1")

function Convert-DailyCronToTime {
    param([string]$Cron)
    $raw = ($Cron -replace '\s+', ' ').Trim()
    if (-not $raw -or $raw -eq 'manual') { return $null }
    $parts = $raw -split ' '
    if ($parts.Count -ne 5) { return $null }
    $minute, $hour, $dom, $month, $dow = $parts
    if ($minute -match '^\d+$' -and $hour -match '^\d+$' -and $dom -eq '*' -and $month -eq '*' -and $dow -eq '*') {
        return '{0:D2}:{1:D2}' -f [int]$hour, [int]$minute
    }
    return $null
}

if (-not (Test-Path -LiteralPath $CatalogJson)) {
    throw "Catálogo JSON não encontrado: $CatalogJson. Corre provision-runners.ps1 -Register primeiro."
}

$catalog = Get-Content -LiteralPath $CatalogJson -Raw | ConvertFrom-Json
$pipeline = $catalog.pipelines | Where-Object { $_.id -eq $PipelineId } | Select-Object -First 1
if (-not $pipeline) {
    $ids = @($catalog.pipelines | ForEach-Object { $_.id })
    throw "Pipeline '$PipelineId' não está no catálogo. Disponíveis: $([string]::Join(', ', $ids))"
}

$runPs = [string]$pipeline.run_ps
if (-not $runPs -or -not (Test-Path -LiteralPath $runPs)) {
    throw "run.ps1 em falta para '$PipelineId': $runPs"
}

$resolvedTaskName = $TaskName
if (-not $resolvedTaskName) {
    $resolvedTaskName = [string]$pipeline.task_name
}
if (-not $resolvedTaskName) {
    $resolvedTaskName = "Overseer - $PipelineId"
}

$resolvedDailyAt = $DailyAt
if (-not $resolvedDailyAt) {
    $resolvedDailyAt = Convert-DailyCronToTime -Cron ([string]$pipeline.schedule)
}
if (-not $resolvedDailyAt) {
    throw "Schedule diário não suportado para Task Scheduler: '$($pipeline.schedule)'. Usa -DailyAt HH:mm."
}

$runDir = Split-Path -Parent $runPs
$pwsh = (Get-Command powershell.exe).Source
$action = New-ScheduledTaskAction -Execute $pwsh `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$runPs`""
$trigger = New-ScheduledTaskTrigger -Daily -At $resolvedDailyAt
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable

foreach ($legacy in $RemoveLegacyTaskNames) {
    if (-not $legacy) { continue }
    if ($WhatIfOnly) {
        Write-Host "[dry-run] Remover tarefa legada: $legacy"
        continue
    }
    Unregister-ScheduledTask -TaskName $legacy -Confirm:$false -ErrorAction SilentlyContinue
    if ($?) { Write-Host "Removida tarefa legada: $legacy" }
}

if ($WhatIfOnly) {
    Write-Host "[dry-run] Criar/atualizar '$resolvedTaskName' diariamente às $resolvedDailyAt"
    Write-Host "  Programa: $pwsh"
    Write-Host "  Argumentos: -NoProfile -ExecutionPolicy Bypass -File `"$runPs`""
    Write-Host "  Iniciar em: $runDir"
    exit 0
}

Register-ScheduledTask `
    -TaskName $resolvedTaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -User $env:USERNAME `
    -RunLevel Limited `
    -Description "Pipeline Overseer ($PipelineId) — wrapper run.ps1" `
    -Force | Out-Null

Write-Host "Tarefa registada: $resolvedTaskName (diária às $resolvedDailyAt)"
Write-Host "  run.ps1: $runPs"
Write-Host "Teste imediato: Start-ScheduledTask -TaskName '$resolvedTaskName'"
