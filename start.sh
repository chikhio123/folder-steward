#!/usr/bin/env bash
# Folder Steward - 启动脚本
# 同时启动后端 (FastAPI) 和前端 (Vite)

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "📁 Folder Steward 启动中..."

# 后端启动
echo "🔧 启动后端 (FastAPI)..."
cd "$BACKEND_DIR"
PYTHONPATH=. py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# 等后端起来
sleep 2

# 前端和 Electron 启动
echo "🎨 启动前端 & Electron..."
cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "✅ 启动完成！"
echo "   后端: http://localhost:8000"
echo "   前端桌面: Electron Window"
echo "   API 文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止所有服务"

# 捕获退出信号，清理子进程
cleanup() {
    echo ""
    echo "🛑 正在停止服务..."
    kill "$BACKEND_PID" 2>/dev/null
    kill "$FRONTEND_PID" 2>/dev/null
    wait
    echo "👋 已停止"
}
trap cleanup EXIT INT TERM

# 保持前台运行
wait
