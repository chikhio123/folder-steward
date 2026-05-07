@echo off
chcp 65001 > nul
title Folder Steward

echo ========================================
echo         Folder Steward - V3
echo ========================================
echo.
echo [1/2] 正在进行系统自检与环境清理...

for %%P in (8000 5173 5174 5175) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr :%%P ^| findstr LISTENING') do (
        echo   - 发现占用端口 %%P 的残留进程 [PID %%a]，正在清理...
        taskkill /F /PID %%a > nul 2>&1
    )
)
echo       环境清理完毕。
echo.
echo [2/2] 正在启动 Folder Steward 服务...
echo       请稍候，前端与后端即将唤醒...
echo.

cd /d "%~dp0frontend"
call npm run dev

echo.
echo ========================================
echo   Folder Steward 进程已结束。
echo ========================================
pause
