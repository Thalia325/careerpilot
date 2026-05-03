@echo off
setlocal EnableExtensions

REM UTF-8 console to avoid garbled output in batch windows.
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
set NEXT_TELEMETRY_DISABLED=1
set NEXT_DISABLE_UNICODE=1
set NO_COLOR=1
set FORCE_COLOR=0
set NPM_CONFIG_FUND=false
set NPM_CONFIG_AUDIT=false

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "BACKEND_DIR=%ROOT%backend"
set "FRONTEND_DIR=%ROOT%frontend"
set "VENV_DIR=%BACKEND_DIR%\.venv"
set "BACKEND_PY=%VENV_DIR%\Scripts\python.exe"
set "BACKEND_PORT=8000"
set "FRONTEND_PORT=3000"
set "ENV_DATABASE_URL="
set "BACKEND_DB_URL=sqlite:///./careerpilot.db"

if exist ".env" (
  for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
    if /I "%%~A"=="API_PORT" set "BACKEND_PORT=%%~B"
    if /I "%%~A"=="FRONTEND_PORT" set "FRONTEND_PORT=%%~B"
    if /I "%%~A"=="DATABASE_URL" set "ENV_DATABASE_URL=%%~B"
  )
)

if defined ENV_DATABASE_URL set "BACKEND_DB_URL=%ENV_DATABASE_URL%"

if not exist "%BACKEND_DIR%\requirements.txt" (
  echo [error] Missing backend requirements: %BACKEND_DIR%\requirements.txt
  goto :fail
)

if not exist "%FRONTEND_DIR%\package.json" (
  echo [error] Missing frontend package.json: %FRONTEND_DIR%\package.json
  goto :fail
)

where python >nul 2>&1
if errorlevel 1 (
  echo [error] Python is not available in PATH.
  goto :fail
)

where npm >nul 2>&1
if errorlevel 1 (
  echo [error] npm is not available in PATH.
  goto :fail
)

if not exist ".env" if exist ".env.example" (
  copy ".env.example" ".env" >nul
)

if not exist "%BACKEND_PY%" (
  echo [backend] Creating virtual environment...
  python -m venv "%VENV_DIR%"
  if errorlevel 1 goto :fail
)

echo [backend] Installing/updating Python dependencies...
"%BACKEND_PY%" -m pip install -r "%BACKEND_DIR%\requirements.txt"
if errorlevel 1 goto :fail

echo [frontend] Installing/updating Node dependencies...
call npm install --prefix "%FRONTEND_DIR%"
if errorlevel 1 goto :fail

echo Launching backend and frontend in background...
call :kill_port_owner %BACKEND_PORT%
call :kill_port_owner %FRONTEND_PORT%

call :is_port_open %BACKEND_PORT%
if errorlevel 1 (
  set "DATABASE_URL=%BACKEND_DB_URL%"
  start "CareerPilot Backend" /MIN /D "%BACKEND_DIR%" "%BACKEND_PY%" -m app.main
) else (
  echo [backend] Port %BACKEND_PORT% is still in use after cleanup, skip backend start.
)

call :is_port_open %FRONTEND_PORT%
if errorlevel 1 (
  start "CareerPilot Frontend" /MIN /D "%FRONTEND_DIR%" cmd /c "chcp 65001>nul && set NEXT_TELEMETRY_DISABLED=1 && set NEXT_DISABLE_UNICODE=1 && set NO_COLOR=1 && set FORCE_COLOR=0 && set NEXT_PUBLIC_API_BASE_URL=http://localhost:%BACKEND_PORT%/api/v1 && call npx next dev --port %FRONTEND_PORT%"
) else (
  echo [frontend] Port %FRONTEND_PORT% is still in use after cleanup, skip frontend start.
)

call :wait_for_port %BACKEND_PORT% Backend
call :wait_for_port %FRONTEND_PORT% Frontend

echo Opening browser at http://localhost:%FRONTEND_PORT% ...
start "" "http://localhost:%FRONTEND_PORT%"

echo All done.
exit /b 0

:fail
echo Start failed. Please check the errors above.
pause
exit /b 1

:kill_port_owner
set "PORT=%~1"
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:"^ *TCP .*:%PORT% .*LISTENING"') do (
  taskkill /PID %%P /F >nul 2>&1
)
timeout /t 1 >nul
exit /b 0

:wait_for_port
set "PORT=%~1"
set "NAME=%~2"
echo Waiting for %NAME% on port %PORT% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$port=%PORT%;$deadline=(Get-Date).AddSeconds(120);while((Get-Date)-lt $deadline){try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',$port);$c.Close();exit 0}catch{Start-Sleep -Milliseconds 500}};exit 1"
if errorlevel 1 (
  echo [warn] %NAME% did not become ready within 120 seconds.
)
exit /b 0

:is_port_open
set "PORT=%~1"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$port=%PORT%;try{$c=New-Object Net.Sockets.TcpClient('127.0.0.1',$port);$c.Close();exit 0}catch{exit 1}"
exit /b %ERRORLEVEL%
