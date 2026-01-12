@echo off
REM Bank Analyzer - Easy Run Script for Windows
REM This script automatically sets up Python virtual environment and runs the analyzer

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
set "VENV_DIR=%SCRIPT_DIR%.venv"
set "PYTHON_CMD="

echo.
echo ==========================================
echo    Bank Analyzer - Easy Setup ^& Run
echo ==========================================
echo.

REM Find Python 3.9+
for %%P in (python3 python py) do (
    where %%P >nul 2>nul
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%V in ('%%P -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2^>nul') do (
            set "version=%%V"
        )
        for /f "tokens=1,2 delims=." %%A in ("!version!") do (
            set "major=%%A"
            set "minor=%%B"
        )
        if !major! geq 3 if !minor! geq 9 (
            set "PYTHON_CMD=%%P"
            echo [INFO] Found Python !version! ^(%%P^)
            goto :found_python
        )
    )
)

echo [ERROR] Python 3.9 or higher is required but not found!
echo [ERROR] Please install Python from https://www.python.org/downloads/
exit /b 1

:found_python

REM Setup virtual environment if needed
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    %PYTHON_CMD% -m venv "%VENV_DIR%"
)

REM Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

REM Check if package is installed
pip show bank-analyzer >nul 2>nul
if !errorlevel! neq 0 (
    echo [INFO] Installing dependencies...
    pip install --quiet --upgrade pip
    if exist "%SCRIPT_DIR%requirements.txt" (
        pip install --quiet -r "%SCRIPT_DIR%requirements.txt"
    )
    echo [INFO] Installing bank-analyzer...
    pip install --quiet -e "%SCRIPT_DIR%."
)

REM Copy example config if needed
if not exist "%SCRIPT_DIR%config\rules.yaml" (
    if exist "%SCRIPT_DIR%config\rules.example.yaml" (
        echo [INFO] Copying example rules configuration...
        copy "%SCRIPT_DIR%config\rules.example.yaml" "%SCRIPT_DIR%config\rules.yaml" >nul
    )
)

if not exist "%SCRIPT_DIR%config\categories.yaml" (
    if exist "%SCRIPT_DIR%config\categories.example.yaml" (
        echo [INFO] Copying example categories configuration...
        copy "%SCRIPT_DIR%config\categories.example.yaml" "%SCRIPT_DIR%config\categories.yaml" >nul
    )
)

REM Create data directories if needed
if not exist "%SCRIPT_DIR%data\input" mkdir "%SCRIPT_DIR%data\input"
if not exist "%SCRIPT_DIR%data\output" mkdir "%SCRIPT_DIR%data\output"
if not exist "%SCRIPT_DIR%data\processed" mkdir "%SCRIPT_DIR%data\processed"

echo.
echo [INFO] Setup complete!
echo.

REM Run CLI with arguments or show help
if "%~1"=="" (
    echo Usage:
    echo   run.bat analyze data\input\*.csv     - Analyze CSV files
    echo   run.bat parse file.csv               - Parse single file
    echo   run.bat detect file.csv              - Detect bank format
    echo   run.bat version                      - Show version
    echo   run.bat --help                       - Show all commands
    echo.
    echo Example:
    echo   run.bat analyze data\input\pko_*.csv -o output.xlsx
    echo.
    bank-analyzer --help
) else (
    echo [INFO] Running: bank-analyzer %*
    echo.
    bank-analyzer %*
)

endlocal
