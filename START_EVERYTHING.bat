@echo off
echo ========================================
echo Starting Email Validator Dashboard
echo ========================================
echo.

echo Step 1: Starting Backend (app_dashboard.py)...
echo.
start cmd /k "python app_dashboard.py"

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
echo Press any key to close this window...
pause >nul
