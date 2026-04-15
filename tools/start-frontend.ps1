$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendDir = Join-Path $projectRoot "frontend"
$logFile = Join-Path $projectRoot "run-logs\frontend.service.log"
$env:NEXT_TELEMETRY_DISABLED = "1"

New-Item -ItemType Directory -Force (Split-Path -Parent $logFile) | Out-Null
Set-Location $frontendDir

& "C:\Users\Lenovo\AppData\Local\Microsoft\WinGet\Packages\OpenJS.NodeJS.LTS_Microsoft.Winget.Source_8wekyb3d8bbwe\node-v24.14.0-win-x64\node.exe" ".\node_modules\next\dist\bin\next" start --port 3000 *>> $logFile
