#!/bin/bash
# TrendRadar 快速启动脚本（简化版）
# 用法: ./quick-start.sh

set -e

echo "🚀 TrendRadar 快速启动..."
echo ""

# 1. 安装依赖（如果需要）
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 安装依赖..."
    pip3 install -q -r requirements.txt
    echo "✓ 依赖安装完成"
fi

# 2. 检查 API Key
if [ -z "$LLM_API_KEY" ]; then
    echo "⚠️  未设置 LLM_API_KEY"
    echo ""
    echo "请先配置 API Key:"
    echo "  1. 复制配置文件: cp setup-deepseek-demo.sh setup-deepseek.sh"
    echo "  2. 编辑文件,填入真实 API Key"
    echo "  3. 加载配置: source setup-deepseek.sh"
    echo "  4. 重新运行: ./quick-start.sh"
    echo ""
    echo "或使用完整启动脚本: ./start-all.sh"
    exit 1
fi

echo "✓ API Key 已配置: ${LLM_API_KEY:0:20}..."

# 3. 生成新闻数据（如果今天还没有）
TODAY=$(date +"%Y年%m月%d日")
if [ ! -f "output/$TODAY/json/news_summary.json" ]; then
    echo ""
    echo "📰 生成新闻数据..."
    python3 main.py
    echo "✓ 新闻数据生成完成"
fi

# 4. 杀死旧进程（如果存在）
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    PID=$(lsof -ti:8000)
    kill -9 $PID 2>/dev/null
    echo "✓ 已停止旧进程 (PID: $PID)"
    sleep 1
fi

# 5. 启动服务器
echo ""
echo "🚀 启动 API 服务器..."
python3 -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# 等待启动
sleep 3

if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo ""
    echo "✅ 启动成功!"
    echo ""
    echo "📚 API 文档: http://localhost:8000/docs"
    echo "🧪 测试脚本: python3 example_stream_chat.py"
    echo "🛑 停止服务: kill $SERVER_PID"
    echo ""
    echo "按 Ctrl+C 停止服务器"
    wait $SERVER_PID
else
    echo "❌ 启动失败"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi
