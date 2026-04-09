# Kill processes listening on the backend HTTP port (Uvicorn --reload tree).
# Usage: .\stop-backend.ps1   or   .\stop-backend.ps1 -Port 8990

param(
    [int]$Port = 0
)

$ErrorActionPreference = "SilentlyContinue"
$here = $PSScriptRoot
$defaultPort = 8990

if ($Port -le 0) {
    $envPath = Join-Path $here ".env"
    $Port = $defaultPort
    if (Test-Path $envPath) {
        Get-Content $envPath -Encoding UTF8 | ForEach-Object {
            if ($_ -match '^\s*PORT\s*=\s*(\d+)\s*$') {
                $Port = [int]$Matches[1]
            }
        }
    }
}

$listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
if (-not $listeners) {
    Write-Host "No listener on port $Port (already stopped?)."
    exit 0
}

$targetPids = $listeners | Select-Object -ExpandProperty OwningProcess -Unique
foreach ($targetPid in $targetPids) {
    $p = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
    $name = if ($p) { $p.ProcessName } else { "?" }
    Write-Host "Stopping process tree PID=$targetPid ($name) ..."
    & taskkill.exe /F /T /PID $targetPid | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Stopped PID=$targetPid"
    } else {
        Write-Warning "taskkill exit $LASTEXITCODE for PID=$targetPid (try Run as administrator)"
    }
}

Write-Host "Done."
