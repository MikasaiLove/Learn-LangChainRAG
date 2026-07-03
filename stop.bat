@echo off
cd /d "%~dp0"
echo Stopping RAG servers...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo   Backend (port 8000): stopped

for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING" 2^>nul') do (
    taskkill /PID %%a /F >nul 2>&1
)
echo   Frontend (port 5173): stopped

echo.
echo All services stopped.
pause
