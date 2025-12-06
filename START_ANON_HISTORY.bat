@echo off
echo ========================================
echo Starting Email Validator with Anonymous History
echo ========================================
echo.

echo Step 1: Starting Backend (app_anon_history.py)...
echo.
start cmd /k "python app_anon_history.py"

timeout /t 3 /nobreak >nul

echo Step 2: Starting Frontend (React)...
echo.
start cmd /k "cd frontend && npm start"

echo.
echo ========================================
echo Both servers are starting!
echo ========================================
echo.
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Features:
echo - Anonymous User ID System
echo - Private History (No Login Required)
echo - User-Specific Analytics
echo - Cross-User Isolation
echo.
echo Press any key to close this window...
pause >nul
