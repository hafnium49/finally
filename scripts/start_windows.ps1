# Start the FinAlly container (Windows PowerShell).
# Usage:
#   .\scripts\start_windows.ps1            # build only if image missing
#   .\scripts\start_windows.ps1 -Build     # force rebuild
#
# Idempotent: safe to run repeatedly. Any existing `finally` container is
# removed before a new one is started.

[CmdletBinding()]
param(
    [switch]$Build
)

$ErrorActionPreference = 'Stop'

$Image     = 'finally:latest'
$Container = 'finally'
$Port      = 8000

# Move to the project root (parent of scripts/).
$ScriptDir   = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir '..')
Set-Location $ProjectRoot

# Sanity check.
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Error 'docker is not installed or not on PATH.'
    exit 1
}

# Warn if .env is missing.
$EnvFileArgs = @()
if (Test-Path .env) {
    $EnvFileArgs = @('--env-file', '.env')
} else {
    Write-Warning '.env not found. Copy .env.example to .env and fill in keys.'
    Write-Warning 'Continuing without it; LLM chat will be unavailable.'
}

# Ensure the bind-mount target exists on the host.
if (-not (Test-Path db)) {
    New-Item -ItemType Directory -Path db | Out-Null
}

# Build the image if missing, or if -Build was requested.
$imageExists = $false
& docker image inspect $Image *> $null
if ($LASTEXITCODE -eq 0) { $imageExists = $true }

if ($Build -or -not $imageExists) {
    Write-Host "Building $Image..."
    docker build -t $Image .
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "Reusing existing image $Image (pass -Build to force rebuild)."
}

# Remove any prior container with the same name (idempotency).
& docker rm -f $Container *> $null

# Launch.
$dbMount = "$($ProjectRoot.Path)\db:/app/db"
$runArgs = @(
    'run', '-d',
    '--name', $Container,
    '-p', "${Port}:${Port}"
) + $EnvFileArgs + @(
    '-v', $dbMount,
    '--restart', 'unless-stopped',
    $Image
)

& docker @runArgs | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "FinAlly is starting at http://localhost:$Port - tail logs with: docker logs -f $Container"
