<#
.SYNOPSIS
    Recolhe inventário read-only do Task Scheduler para pipelines Overseer.

.DESCRIPTION
    Lê o catalog.json gerado por provision-runners.ps1 e observa as tarefas
    agendadas associadas a cada pipeline. Não cria, altera, arranca nem remove
    tarefas. A saída é um objeto JSON para anexar ao heartbeat do agente.

.EXAMPLE
    .\scripts\windows\collect-taskscheduler-info.ps1 -CatalogJson "$env:USERPROFILE\overseer-runners\catalog.json"
#>
param(
    [string]$CatalogJson = (Join-Path $env:USERPROFILE "overseer-runners\catalog.json"),
    [string]$HostId = ""
)

$ErrorActionPreference = "Stop"

function ConvertTo-IsoDate {
    param([object]$Value)
    if ($null -eq $Value) { return $null }
    try {
        $date = [datetime]$Value
        if ($date.Year -le 1901) { return $null }
        return $date.ToUniversalTime().ToString("o")
    }
    catch {
        return $null
    }
}

function ConvertTo-SafeTaskText {
    param([string]$Value)
    if (-not $Value) { return "" }
    $safe = $Value
    $safe = $safe -replace '(?i)(token|password|passwd|secret|apikey|api_key)(\s*[=:]\s*)("[^"]*"|''[^'']*''|\S+)', '$1$2***'
    $safe = $safe -replace '(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+', '$1***'
    $safe = $safe -replace '(?i)(\.env(?:\.overseer)?)(["''\s]|$)', '$1$2'
    if ($safe.Length -gt 1000) { return $safe.Substring(0, 1000) }
    return $safe
}

function Get-ActionSummary {
    param([object]$Action)
    $parts = @()
    if ($Action.Execute) { $parts += [string]$Action.Execute }
    if ($Action.Arguments) { $parts += [string]$Action.Arguments }
    if ($Action.WorkingDirectory) { $parts += "(cwd: $($Action.WorkingDirectory))" }
    return ConvertTo-SafeTaskText ([string]::Join(" ", $parts))
}

function Get-TriggerSummary {
    param([object]$Trigger)
    $parts = @()
    if ($Trigger.Enabled -ne $null) { $parts += "enabled=$($Trigger.Enabled)" }
    if ($Trigger.StartBoundary) { $parts += "start=$($Trigger.StartBoundary)" }
    if ($Trigger.EndBoundary) { $parts += "end=$($Trigger.EndBoundary)" }
    if ($Trigger.DaysOfWeek) { $parts += "days=$($Trigger.DaysOfWeek)" }
    if ($Trigger.Repetition -and $Trigger.Repetition.Interval) { $parts += "repeat=$($Trigger.Repetition.Interval)" }
    if (-not $parts) { return [string]$Trigger }
    return [string]::Join("; ", $parts)
}

function Test-TaskActionMatch {
    param(
        [object]$Task,
        [string]$Needle
    )
    if (-not $Needle) { return $false }
    foreach ($action in @($Task.Actions)) {
        if ($action.Execute -and $action.Execute -like "*$Needle*") { return $true }
        if ($action.Arguments -and $action.Arguments -like "*$Needle*") { return $true }
        if ($action.WorkingDirectory -and $action.WorkingDirectory -like "*$Needle*") { return $true }
    }
    return $false
}

function Find-ScheduledTaskForPipeline {
    param(
        [object]$Item,
        [object[]]$AllTasks
    )

    $taskName = [string]$Item.task_name
    if ($taskName) {
        $byName = @(Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue)
        if ($byName) {
            return @{ Tasks = $byName; Reason = "task_name" }
        }
    }

    $runPs = [string]$Item.run_ps
    if ($runPs) {
        $byRunPs = @($AllTasks | Where-Object { Test-TaskActionMatch -Task $_ -Needle $runPs })
        if ($byRunPs) {
            return @{ Tasks = $byRunPs; Reason = "run_ps" }
        }
    }

    $taskMatch = [string]$Item.task_match
    if ($taskMatch) {
        $byMatch = @($AllTasks | Where-Object { Test-TaskActionMatch -Task $_ -Needle $taskMatch })
        if ($byMatch) {
            return @{ Tasks = $byMatch; Reason = "task_match" }
        }
    }

    return @{ Tasks = @(); Reason = "not_found" }
}

function ConvertTo-PipelineTaskInfo {
    param(
        [object]$Item,
        [object]$Task,
        [string]$MatchReason
    )

    $info = $null
    try {
        $info = Get-ScheduledTaskInfo -TaskName $Task.TaskName -TaskPath $Task.TaskPath -ErrorAction Stop
    }
    catch {
        $info = $null
    }

    $missedRuns = $null
    if ($info -and ($info.PSObject.Properties.Name -contains "NumberOfMissedRuns")) {
        $missedRuns = $info.NumberOfMissedRuns
    }

    return [ordered]@{
        pipeline_id = [string]$Item.id
        expected_task_name = [string]$Item.task_name
        task_found = $true
        match_reason = $MatchReason
        task_name = [string]$Task.TaskName
        task_path = [string]$Task.TaskPath
        state = [string]$Task.State
        last_run_time = if ($info) { ConvertTo-IsoDate $info.LastRunTime } else { $null }
        next_run_time = if ($info) { ConvertTo-IsoDate $info.NextRunTime } else { $null }
        last_task_result = if ($info) { $info.LastTaskResult } else { $null }
        missed_runs = $missedRuns
        actions = @($Task.Actions | ForEach-Object { Get-ActionSummary $_ })
        triggers = @($Task.Triggers | ForEach-Object { Get-TriggerSummary $_ })
    }
}

if (-not (Test-Path -LiteralPath $CatalogJson)) {
    throw "Catálogo JSON não encontrado: $CatalogJson"
}

$catalog = Get-Content -LiteralPath $CatalogJson -Raw | ConvertFrom-Json
$hostValue = $HostId
if (-not $hostValue) { $hostValue = [string]$catalog.host_id }
if (-not $hostValue) { $hostValue = $env:COMPUTERNAME }

$allTasks = @(Get-ScheduledTask)
$pipelines = @()

foreach ($item in @($catalog.pipelines)) {
    $match = Find-ScheduledTaskForPipeline -Item $item -AllTasks $allTasks
    $tasks = @($match.Tasks)

    if (-not $tasks) {
        $pipelines += [ordered]@{
            pipeline_id = [string]$item.id
            expected_task_name = [string]$item.task_name
            task_found = $false
            match_reason = "not_found"
            task_name = $null
            task_path = $null
            state = $null
            last_run_time = $null
            next_run_time = $null
            last_task_result = $null
            missed_runs = $null
            actions = @()
            triggers = @()
        }
        continue
    }

    foreach ($task in $tasks) {
        $pipelines += ConvertTo-PipelineTaskInfo -Item $item -Task $task -MatchReason $match.Reason
    }
}

[ordered]@{
    task_scheduler = [ordered]@{
        ok = $true
        collected_at = (Get-Date).ToUniversalTime().ToString("o")
        host_id = $hostValue
        pipelines = $pipelines
    }
} | ConvertTo-Json -Depth 8
