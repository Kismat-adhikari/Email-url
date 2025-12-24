@echo off
REM CSS Fix Script - Windows
REM This script will clean up the node cache and restart the frontend

echo.
echo ===================================
echo CSS FIX - Frontend Rebuild Script
echo ===================================
echo.

REM Navigate to frontend directory
cd frontend
echo [1/5] Navigating to frontend directory... Done!
echo.

REM Kill any running npm processes
echo [2/5] Stopping any running npm processes...
taskkill /F /IM node.exe 2>nul
if errorlevel 1 (
    echo        No running processes found.
) else (
    echo        Node processes stopped.
)
echo.

REM Clear npm cache
echo [3/5] Clearing npm cache...
call npm cache clean --force
echo        npm cache cleared!
echo.

REM Remove node_modules and package-lock.json
echo [4/5] Removing old dependencies...
if exist node_modules (
    rmdir /s /q node_modules
    echo        node_modules removed
)
if exist package-lock.json (
    del package-lock.json
    echo        package-lock.json removed
)
echo.

REM Reinstall dependencies
echo [5/5] Installing fresh dependencies...
call npm install
echo        npm dependencies reinstalled!
echo.

REM Start the dev server
echo ===================================
echo Starting development server...
echo ===================================
echo.
call npm start

