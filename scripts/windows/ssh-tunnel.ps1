<#
.SYNOPSIS
    Mantém um túnel SSH em loopback para a API central do Overseer.

.DESCRIPTION
    Encaminha a porta local (default 18090) para 127.0.0.1:8090 no servidor de
    prod, onde a API só escuta em loopback. Reconecta automaticamente se a
    ligação cair. Pensado para correr como tarefa "At logon" no Task Scheduler.

    A autenticação deve ser por chave SSH sem password (ex.: ed25519) na conta
    que corre a tarefa. Nunca guardar passwords nem o token da API neste script.

.EXAMPLE
    .\ssh-tunnel.ps1 -SshTarget operator@server.example.com
#>
param(
    [Parameter(Mandatory = $true)][string]$SshTarget,
    [int]$LocalPort = 18090,
    [string]$RemoteHost = "127.0.0.1",
    [int]$RemotePort = 8090,
    [int]$RetrySeconds = 10,
    [string]$IdentityFile = "",
    [string]$LogFile = (Join-Path $env:USERPROFILE "overseer-runners\ssh-tunnel.log")
)

$ErrorActionPreference = "Continue"

$logDir = Split-Path -Parent $LogFile
if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

function Write-Log {
    param([string]$Message)
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$stamp $Message" | Tee-Object -FilePath $LogFile -Append
}

$forward = "{0}:{1}:{2}" -f $LocalPort, $RemoteHost, $RemotePort
Write-Log "Túnel SSH a iniciar: $forward via $SshTarget"

while ($true) {
    try {
        $sshArgs = @(
            "-N",
            "-o", "ServerAliveInterval=30",
            "-o", "ServerAliveCountMax=3",
            "-o", "ExitOnForwardFailure=yes",
            "-o", "StrictHostKeyChecking=accept-new",
            "-L", $forward
        )
        if ($IdentityFile) { $sshArgs = @("-i", $IdentityFile) + $sshArgs }
        $sshArgs += $SshTarget
        & ssh @sshArgs
        Write-Log "Túnel terminou (exit=$LASTEXITCODE). A reconectar em ${RetrySeconds}s."
    }
    catch {
        Write-Log "Erro no túnel: $($_.Exception.Message). A reconectar em ${RetrySeconds}s."
    }
    Start-Sleep -Seconds $RetrySeconds
}
