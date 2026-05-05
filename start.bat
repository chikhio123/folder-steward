@echo off
chcp 65001 > nul
title Folder Steward

echo ========================================
echo   Folder Steward
echo ========================================
echo.

echo Starting Folder Steward...
cd /d "%~dp0frontend"
npm run dev

echo.
echo ========================================
echo  Folder Steward exited.
echo ========================================
pause
