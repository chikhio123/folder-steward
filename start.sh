#!/usr/bin/env bash
# Folder Steward - 启动脚本

set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

echo "📁 Folder Steward 启动中..."

cd "$FRONTEND_DIR"
npm run dev

echo "👋 已退出 Folder Steward"
