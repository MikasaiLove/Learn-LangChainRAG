@echo off
title RAG-KB Log Viewer
cd /d "%~dp0"

set LOG_FILE=backend\logs\app.log

if not exist "%LOG_FILE%" (
    echo [WARN] No log file found: %LOG_FILE%
    echo        Start the backend first to generate logs.
    pause
    exit /b
)

echo ================================================
echo   RAG KB - Application Logs
echo   File: %LOG_FILE%
echo ================================================
echo.

echo [1] Show last 50 lines (default)
echo [2] Show last 200 lines
echo [3] Show errors only
echo [4] Tail - follow log in real-time
echo [5] Open log file in Notepad
echo.

set /p CHOICE="Choose (1-5, Enter=1): "

if "%CHOICE%"=="" set CHOICE=1

if "%CHOICE%"=="1" (
    echo.
    echo === Last 50 lines ===
    type "%LOG_FILE%" | more +0
)
if "%CHOICE%"=="2" (
    echo.
    echo === Last 200 lines ===
    powershell -Command "Get-Content '%LOG_FILE%' -Tail 200"
)
if "%CHOICE%"=="3" (
    echo.
    echo === Errors only ===
    findstr /i "ERROR" "%LOG_FILE%"
)
if "%CHOICE%"=="4" (
    echo.
    echo === Following log (Ctrl+C to stop) ===
    powershell -Command "Get-Content '%LOG_FILE%' -Wait -Tail 20"
)
if "%CHOICE%"=="5" (
    start notepad "%LOG_FILE%"
)

pause
