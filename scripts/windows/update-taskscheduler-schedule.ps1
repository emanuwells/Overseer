<#
.SYNOPSIS
    Actualiza triggers do Task Scheduler a partir do schedule (cron) no catalog.json.

.DESCRIPTION
    Correr após provision-runners.ps1 -Register quando o schedule mudou no Overseer.
    Procura tarefas por task_name (Overseer - <id>) ou task_match e substitui os triggers.

.EXAMPLE
    .\update-taskscheduler-schedule.ps1 -CatalogJson "$env:USERPROFILE\overseer-runners\catalog.json"
#>
param(
    [Parameter(Mandatory = $true)][string]$CatalogJson,
    [string]$BackupDir = (Join-Path $env:USERPROFILE "overseer-runners\task-backups"),
    [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"

function Convert-CronToTriggers {
    param([string]$Cron)
    $raw = ($Cron -replace '\s+', ' ').Trim()
    if (-not $raw -or $raw -eq 'manual') { return @() }
    $parts = $raw -split ' '
    if ($parts.Count -ne 5) { throw "Cron inválido (5 campos): $Cron" }

    $minute, $hour, $dayOfMonth, $month, $dayOfWeek = $parts
    $triggers = @()

    if ($minute -match '^\*/(\d+)$' -and $hour -eq '*' -and $dayOfMonth -eq '*' -and $month -eq '*' -and $dayOfWeek -eq '*') {
        $every = [int]$Matches[1]
        $at = (Get-Date).Date
        $triggers += New-ScheduledTaskTrigger -Once -At $at `
            -RepetitionInterval (New-TimeSpan -Minutes $every) `
            -RepetitionDuration (New-TimeSpan -Days 1)
        return $triggers
    }

    if ($minute -match '^(\d+),(\d+)$' -and $hour -eq '*' -and $dayOfMonth -eq '*' -and $month -eq '*' -and $dayOfWeek -eq '*') {
        $every = [int]$minute.Split(',')[1] - [int]$minute.Split(',')[0]
        if ($every -le 0) { $every = 30 }
        $at = (Get-Date).Date.AddMinutes([int]$minute.Split(',')[0])
        $triggers += New-ScheduledTaskTrigger -Once -At $at `
            -RepetitionInterval (New-TimeSpan -Minutes $every) `
            -RepetitionDuration (New-TimeSpan -Days 1)
        return $triggers
    }

    if ($minute -match '^\d+$' -and $hour -match '^\d+$' -and $dayOfMonth -eq '*' -and $month -eq '*' -and $dayOfWeek -eq '*') {
        $at = '{0:D2}:{1:D2}' -f [int]$hour, [int]$minute
        $triggers += New-ScheduledTaskTrigger -Daily -At $at
        return $triggers
    }

    if ($minute -match '^\d+$' -and $hour -match '^\d+$' -and $dayOfMonth -eq '*' -and $month -eq '*' -and $dayOfWeek -match '^\d+$') {
        $at = '{0:D2}:{1:D2}' -f [int]$hour, [int]$minute
        $dowMap = @{ '0' = 'Sunday'; '1' = 'Monday'; '2' = 'Tuesday'; '3' = 'Wednesday'; '4' = 'Thursday'; '5' = 'Friday'; '6' = 'Saturday'; '7' = 'Sunday' }
        $dow = $dowMap[[string][int]$dayOfWeek]
        $triggers += New-ScheduledTaskTrigger -Weekly -DaysOfWeek $dow -At $at
        return $triggers
    }

    throw "Cron não suportado para Task Scheduler: $Cron"
}

function Find-ScheduledTaskForPipeline {
    param($Item)
    $taskName = $Item.task_name
    if ($taskName) {
        $byName = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        if ($byName) { return @($byName) }
    }
    $match = $Item.task_match
    if (-not $match) { return @() }
    return @(Get-ScheduledTask | Where-Object {
        $_.Actions | Where-Object {
            ($_.Execute -and $_.Execute -like "*$match*") -or
            ($_.Arguments -and $_.Arguments -like "*$match*")
        }
    })
}

if (-not (Test-Path -LiteralPath $CatalogJson)) { throw "Catálogo JSON não encontrado: $CatalogJson" }
if (-not (Test-Path -LiteralPath $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null }

$catalog = Get-Content -LiteralPath $CatalogJson -Raw | ConvertFrom-Json
$stamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$updated = @()
$skipped = @()
$errors = @()

foreach ($item in $catalog.pipelines) {
    $schedule = [string]$item.schedule
    if (-not $schedule -or $schedule -eq 'manual') {
        $skipped += $item.id
        continue
    }

    try {
        $newTriggers = Convert-CronToTriggers -Cron $schedule
    }
    catch {
        $errors += "$($item.id): $($_.Exception.Message)"
        continue
    }

    $tasks = Find-ScheduledTaskForPipeline -Item $item
    if (-not $tasks) {
        $errors += "$($item.id): tarefa não encontrada no Task Scheduler"
        continue
    }

    foreach ($task in $tasks) {
        $safeName = ($task.TaskName -replace '[\\/:*?"<>|]', '_')
        $backup = Join-Path $BackupDir "$safeName-schedule-$stamp.xml"
        Export-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath | Set-Content -LiteralPath $backup -Encoding UTF8

        if ($WhatIfOnly) {
            Write-Host "[dry-run] $($task.TaskName) schedule=$schedule (backup: $backup)"
        }
        else {
            Set-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath -Trigger $newTriggers | Out-Null
            Write-Host "Agenda actualizada: $($task.TaskName) -> $schedule (backup: $backup)"
        }
        $updated += $item.id
    }
}

Write-Host ""
Write-Host "Triggers actualizados: $((($updated | Select-Object -Unique)).Count)"
if ($skipped) {
    Write-Host "Ignorados (manual): $([string]::Join(', ', ($skipped | Select-Object -Unique)))"
}
if ($errors) {
    Write-Warning ($errors -join '; ')
    exit 1
}
