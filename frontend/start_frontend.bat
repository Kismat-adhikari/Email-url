@echo off
echo ============================================================
echo Starting React Frontend...
echo ============================================================
echo.
echo Installing dependencies...
call npm install
echo.
echo Setting frontend port to 3002
set PORT=3002
echo Starting development server on http://localhost:3002
echo.
call npm start
