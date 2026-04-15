$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $projectRoot "backend"
$stdoutLog = Join-Path $projectRoot "run-logs\backend.service.out.log"
$stderrLog = Join-Path $projectRoot "run-logs\backend.service.err.log"
$pythonExe = Join-Path $backendDir ".venv\Scripts\python.exe"

New-Item -ItemType Directory -Force (Split-Path -Parent $stdoutLog) | Out-Null

if (Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue) {
  exit 0
}

Start-Process -FilePath $pythonExe `
  -ArgumentList "-m", "app.main" `
  -WorkingDirectory $backendDir `
  -RedirectStandardOutput $stdoutLog `
  -RedirectStandardError $stderrLog `
  -WindowStyle Hidden | Out-Null
