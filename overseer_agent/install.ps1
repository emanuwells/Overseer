# Install overseer-agent on Windows (editable from repo root)
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
python -m pip install -r requirements.txt
Write-Host "Run: python -m overseer_agent heartbeat"
