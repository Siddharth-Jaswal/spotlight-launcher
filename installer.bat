@echo off
setlocal EnableExtensions EnableDelayedExpansion

cd /d "%~dp0"
set "REPO_DIR=%CD%"
set "VENV_DIR=%REPO_DIR%\.venv"
set "APP_BAT=%REPO_DIR%\app.bat"
set "USER_BIN=%USERPROFILE%\spotlight-launcher-bin"
set "SHIM_BAT=%USER_BIN%\spotlight-sid.bat"
set "PYTHON_CMD="

call :find_python
if not defined PYTHON_CMD (
    echo Python 3.10+ was not found. Trying to install Python with winget...
    call :install_python
    call :find_python
)

if not defined PYTHON_CMD (
    echo Could not find or install Python 3.10+.
    echo Install Python manually, then run installer.bat again.
    exit /b 1
)

echo Using Python: %PYTHON_CMD%

if not exist "%VENV_DIR%\Scripts\python.exe" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo Failed to create virtual environment.
        exit /b 1
    )
)

echo Ensuring pip is available in the virtual environment...
"%VENV_DIR%\Scripts\python.exe" -m ensurepip --upgrade >nul 2>nul

echo Installing or updating Spotlight Launcher in %VENV_DIR%...
"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Failed to upgrade pip inside the virtual environment.
    exit /b 1
)

"%VENV_DIR%\Scripts\python.exe" -m pip install --upgrade .
if errorlevel 1 (
    echo Failed to install Spotlight Launcher in the virtual environment.
    exit /b 1
)

echo Creating app launcher at %APP_BAT%...
(
    echo @echo off
    echo setlocal
    echo cd /d "%REPO_DIR%"
    echo if exist "%VENV_DIR%\Scripts\pythonw.exe" ^(
    echo     start "" "%VENV_DIR%\Scripts\pythonw.exe" -m main
    echo ^) else ^(
    echo     start "" "%VENV_DIR%\Scripts\python.exe" -m main
    echo ^)
    echo endlocal
) > "%APP_BAT%"
if errorlevel 1 (
    echo Failed to create app.bat.
    exit /b 1
)

if not exist "%USER_BIN%" mkdir "%USER_BIN%"

echo Creating command shim at %SHIM_BAT%...
(
    echo @echo off
    echo call "%APP_BAT%" %%*
) > "%SHIM_BAT%"
if errorlevel 1 (
    echo Failed to create spotlight-sid.bat.
    exit /b 1
)

echo Ensuring %USER_BIN% is in your user PATH...
set "SPOTLIGHT_USER_BIN=%USER_BIN%"
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$bin = [Environment]::GetEnvironmentVariable('SPOTLIGHT_USER_BIN', 'Process');" ^
    "$current = [Environment]::GetEnvironmentVariable('Path', 'User');" ^
    "$parts = @();" ^
    "if ($current) { $parts = $current -split ';' | Where-Object { $_ -and $_.Trim() }; }" ^
    "$normalizedBin = [System.IO.Path]::GetFullPath($bin).TrimEnd('\');" ^
    "$filtered = foreach ($part in $parts) {" ^
    "  try { $normalizedPart = [System.IO.Path]::GetFullPath($part).TrimEnd('\'); } catch { $normalizedPart = $part.TrimEnd('\'); }" ^
    "  if ($normalizedPart -ine $normalizedBin) { $part }" ^
    "};" ^
    "$newPath = @($bin) + $filtered;" ^
    "[Environment]::SetEnvironmentVariable('Path', ($newPath -join ';'), 'User')"
if errorlevel 1 (
    echo Failed to update your user PATH.
    exit /b 1
)

echo.
echo Installation complete.
echo Repo launcher: %APP_BAT%
echo Command shim: %SHIM_BAT%
echo.
echo Open a new terminal and run: spotlight-sid
echo Or run directly: "%APP_BAT%"

endlocal & exit /b 0

:find_python
set "PYTHON_CMD="
for /f "delims=" %%I in ('where py 2^>nul') do (
    py -3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD=py -3"
        goto :eof
    )
)
for /f "delims=" %%I in ('where python 2^>nul') do (
    "%%I" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD="%%I""
        goto :eof
    )
)
goto :eof

:install_python
where winget >nul 2>nul
if errorlevel 1 goto :eof
winget install --id Python.Python.3.12 --exact --silent --accept-package-agreements --accept-source-agreements
goto :eof
