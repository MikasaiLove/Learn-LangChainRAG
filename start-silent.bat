@echo off
title RAG KB - Silent Start
cd /d "%~dp0"

echo ================================================
echo   RAG System - Silent Background Start
echo ================================================
echo.

:: Kill any existing processes on ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING" 2^>nul') do taskkill /PID %%a /F >nul 2>&1

:: Init admin
cd /d "%~dp0backend"
python -m app.init_admin 2>nul
cd /d "%~dp0"
echo   Admin: admin / 123456

:: Start backend (hidden window via VBS)
set VBS_BACKEND="%TEMP%\start_backend.vbs"
echo Set WshShell = CreateObject("WScript.Shell") > %VBS_BACKEND%
echo WshShell.Run "cmd /c cd /d %~dp0backend ^&^& uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-use-colors --no-access-log", 0, False >> %VBS_BACKEND%
cscript //nologo %VBS_BACKEND%
del %VBS_BACKEND%
echo   Backend started (port 8000)

:: Wait
timeout /t 3 /nobreak >nul

:: Start frontend (hidden window via VBS)
set VBS_FRONTEND="%TEMP%\start_frontend.vbs"
echo Set WshShell = CreateObject("WScript.Shell") > %VBS_FRONTEND%
echo WshShell.Run "cmd /c cd /d %~dp0frontend ^&^& set FORCE_COLOR=0 ^&^& npm run dev", 0, False >> %VBS_FRONTEND%
cscript //nologo %VBS_FRONTEND%
del %VBS_FRONTEND%
echo   Frontend started (port 5173)

:: Wait and open browser
timeout /t 3 /nobreak >nul
start http://localhost:5173

echo.
echo ================================================
echo   Servers running in background!
echo   http://localhost:5173
echo.
echo   Run stop.bat to shut them down.
echo ================================================
echo.
pause
