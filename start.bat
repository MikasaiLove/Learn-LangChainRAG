@echo off
title RAG KB System - Startup
cd /d "%~dp0"

echo.
echo ================================================
echo   RAG Enterprise KB Q&A System - Starting...
echo ================================================
echo.

:: ============================================
:: 1. Environment Check
:: ============================================
echo [1/5] Checking environment...

:: Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Python not found. Please install Python 3.11+
    pause
    exit /b 1
)
python --version 2>&1
echo   Python: OK

:: Node.js
where node >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAIL] Node.js not found. Please install Node.js 18+
    pause
    exit /b 1
)
node --version 2>&1
echo   Node.js: OK

:: .env config file
if not exist "%~dp0backend\.env" (
    if exist "%~dp0.env" (
        echo   Copying .env from root to backend...
        copy "%~dp0.env" "%~dp0backend\.env" >nul
    ) else (
        echo [WARN] .env file not found, please create backend\.env
    )
) else (
    echo   .env: OK
)

:: Python dependencies
python -c "import fastapi" 2>nul
if %errorlevel% neq 0 (
    echo [WARN] Python deps missing, installing...
    cd /d "%~dp0backend"
    pip install -r requirements.txt -q
    if %errorlevel% neq 0 (
        echo [FAIL] pip install failed. Run manually: pip install -r requirements.txt
        pause
        exit /b 1
    )
    cd /d "%~dp0"
    echo   Done.
) else (
    echo   Python deps: OK
)

:: Node dependencies
if not exist "%~dp0frontend\node_modules" (
    echo [WARN] Node deps missing, installing...
    cd /d "%~dp0frontend"
    call npm install
    if %errorlevel% neq 0 (
        echo [FAIL] npm install failed. Run manually.
        pause
        exit /b 1
    )
    cd /d "%~dp0"
    echo   Done.
) else (
    echo   Node deps: OK
)

:: ============================================
:: 2. Free ports
:: ============================================
echo.
echo [2/5] Checking ports...

:: Port 8000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000 " ^| findstr "LISTENING" 2^>nul') do (
    echo   Port 8000 in use by PID %%a, releasing...
    taskkill /PID %%a /F >nul 2>&1
)
echo   Port 8000: OK

:: Port 5173
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5173 " ^| findstr "LISTENING" 2^>nul') do (
    echo   Port 5173 in use by PID %%a, releasing...
    taskkill /PID %%a /F >nul 2>&1
)
echo   Port 5173: OK

:: ============================================
:: 3. Init admin account
:: ============================================
echo.
echo [3/5] Init admin account...

cd /d "%~dp0backend"
python -m app.init_admin 2>nul
cd /d "%~dp0"
echo   Admin: admin / 123456

:: ============================================
:: 4. Start services
:: ============================================
echo.
echo [4/5] Starting backend (port 8000)...

start "RAG-Backend" cmd /k "title RAG-Backend-API-Port8000 && echo ============================================= && echo   BACKEND - FastAPI Server (port 8000) && echo   API Docs: http://localhost:8000/docs && echo ============================================= && cd /d %~dp0backend && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --no-use-colors"

echo   Waiting for backend (5s)...
timeout /t 5 /nobreak >nul

echo.
echo [5/5] Starting frontend (port 5173)...

start "RAG-Frontend" cmd /k "title RAG-Frontend-Vite-Port5173 && echo ============================================= && echo   FRONTEND - Vite Dev Server (port 5173) && echo   Page: http://localhost:5173 && echo ============================================= && cd /d %~dp0frontend && set FORCE_COLOR=0 && npm run dev"

echo   Waiting for frontend (3s)...
timeout /t 3 /nobreak >nul

:: ============================================
:: 5. Open browser
:: ============================================
echo.
echo ================================================
echo   Startup complete! Opening browser...
echo.
echo   Frontend : http://localhost:5173
echo   API Docs : http://localhost:8000/docs
echo   Admin    : admin / 123456
echo.
echo   Close all terminal windows to stop services.
echo ================================================
echo.

start http://localhost:5173

pause
