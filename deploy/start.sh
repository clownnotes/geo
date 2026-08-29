#!/bin/bash
# GEO Web 生产后台启动脚本 (支持腾讯云 Linux 与 Mac Mini)

PORT=${1:-8088}
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"

cd "$PROJECT_ROOT" || exit 1

# 检查是否已有进程运行在指定端口
PID=$(lsof -ti :"$PORT")
if [ -n "$PID" ]; then
    echo "⚠️ 发现端口 $PORT 已被进程 PID $PID 占用，正在停止旧进程..."
    kill -9 "$PID"
    sleep 1
fi

echo "🚀 正在启动 GEO 商业交付 Web 管理端 (端口: $PORT)..."
nohup python3 -m tools.geo web --port "$PORT" > "$PROJECT_ROOT/server.log" 2>&1 &

NEW_PID=$!
echo "✅ 服务已成功在后台启动！(PID: $NEW_PID)"
echo "📍 本地监听地址: http://127.0.0.1:$PORT"
echo "📄 运行日志文件: $PROJECT_ROOT/server.log"
echo "💡 可通过 'tail -f server.log' 查看实时日志。"
