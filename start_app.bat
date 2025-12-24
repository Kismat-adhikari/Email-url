@echo off
echo ================================================================================
echo EMAIL VALIDATOR - STARTING APPLICATION
echo ================================================================================
echo.

echo [1/2] Starting Backend Server (Python Flask)...
echo.
start "Email Validator Backend" cmd /k "python app_anon_history.py"
timeout /t 3 /nobreak >nul

echo [2/2] Starting Frontend Server (React)...
echo.
start "Email Validator Frontend" cmd /k "cd frontend && set PORT=3002 && npm start"

echo.
echo ================================================================================
echo APPLICATION STARTED!
echo ================================================================================
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:3002
echo.
echo Two terminal windows have been opened.
echo Keep them running while using the application.
echo.
echo Press Ctrl+C in each window to stop the servers.
echo.
echo This window can be closed safely.
echo ================================================================================
pause
