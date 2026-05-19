# Stop the FinAlly container (Windows PowerShell).
# Idempotent: exits 0 whether or not the container was running.
# The .\db volume is intentionally NOT removed - data persists across stops.

[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$Container = 'finally'

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'docker is not installed or not on PATH.'
    exit 1
}

& docker rm -f $Container *> $null
if ($LASTEXITCODE -eq 0) {
    Write-Host 'Stopped.'
} else {
    Write-Host 'Not running.'
}

exit 0
