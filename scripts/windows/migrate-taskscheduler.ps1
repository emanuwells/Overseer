<#
.SYNOPSIS
    Aponta tarefas existentes do Task Scheduler para os wrappers run.ps1.

.DESCRIPTION
    Equivalente Windows de scripts\update-crontab-overseer.py. Lê o JSON gerado
    pelo provisionamento, faz backup XML das tarefas afetadas e substitui a ação
    de cada tarefa cujo comando contém "task_match" por:
        powershell.exe -File <run.ps1>
    mantendo os triggers (agendamento) originais. Assim a observabilidade fica
    ativa sem reescrever o agendamento.

.EXAMPLE
    .\migrate-taskscheduler.ps1 -CatalogJson "$env:USERPROFILE\overseer-runners\catalog.json"
#>
param(
    [Parameter(Mandatory = $true)][string]$CatalogJson,
    [string]$BackupDir = (Join-Path $env:USERPROFILE "overseer-runners\task-backups"),
    [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $CatalogJson)) { throw "Catálogo JSON não encontrado: $CatalogJson" }
if (-not (Test-Path -LiteralPath $BackupDir)) { New-Item -ItemType Directory -Path $BackupDir -Force | Out-Null }

$catalog = Get-Content -LiteralPath $CatalogJson -Raw | ConvertFrom-Json
$pwsh = (Get-Command powershell.exe).Source
$stamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$replaced = @()
$missing = @()

foreach ($item in $catalog.pipelines) {
    $match = $item.task_match
    $runPs = $item.run_ps
    if (-not $match -or -not $runPs) {
        $missing += $item.id
        continue
    }

    $candidates = Get-ScheduledTask | Where-Object {
        $_.Actions | Where-Object {
            ($_.Execute -and $_.Execute -like "*$match*") -or
            ($_.Arguments -and $_.Arguments -like "*$match*")
        }
    }

    if (-not $candidates) {
        $missing += $item.id
        continue
    }

    foreach ($task in $candidates) {
        $safeName = ($task.TaskName -replace '[\\/:*?"<>|]', '_')
        $backup = Join-Path $BackupDir "$safeName-$stamp.xml"
        Export-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath | Set-Content -LiteralPath $backup -Encoding UTF8

        $newArgs = "-NoProfile -ExecutionPolicy Bypass -File `"$runPs`""
        $newAction = New-ScheduledTaskAction -Execute $pwsh -Argument $newArgs

        if ($WhatIfOnly) {
            Write-Host "[dry-run] $($task.TaskName) -> $pwsh $newArgs (backup: $backup)"
        }
        else {
            Set-ScheduledTask -TaskName $task.TaskName -TaskPath $task.TaskPath -Action $newAction | Out-Null
            Write-Host "Migrada: $($task.TaskName) (backup: $backup)"
        }
        $replaced += $item.id
    }
}

Write-Host ""
$replacedUnique = @($replaced | Select-Object -Unique)
$missingUnique = @($missing | Select-Object -Unique)
$replacedLabel = if ($replacedUnique.Count -gt 0) { [string]::Join(', ', $replacedUnique) } else { '(nenhuma)' }
Write-Host "Substituídas $($replacedUnique.Count) tarefas: $replacedLabel"
if ($missingUnique.Count -gt 0) {
    Write-Warning "Sem correspondência no Task Scheduler: $([string]::Join(', ', $missingUnique))"
}
