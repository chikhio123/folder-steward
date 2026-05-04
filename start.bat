@echo off
chcp 65001 > nul
title Folder Steward

echo ========================================
echo   Folder Steward
echo ========================================
echo.

if not exist "%~dp0data" mkdir "%~dp0data"

echo [1/2] Starting backend...
cd /d "%~dp0backend"
start "FolderSteward-Backend" cmd /c "py -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
timeout /t 3 /nobreak > nul

echo [2/2] Starting frontend...
cd /d "%~dp0frontend"
start "FolderSteward-Frontend" cmd /c "npx vite --host 0.0.0.0 --port 5174"

echo.
echo ========================================
echo  Backend:  http://localhost:8000
echo  Frontend: http://localhost:5174
echo  Docs:     http://localhost:8000/docs
echo ========================================
echo.
echo Close the two windows to stop services.
pause
