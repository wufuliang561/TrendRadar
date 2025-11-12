#!/bin/bash
# TrendRadar 一键启动脚本
# 功能: 环境安装 → 生成新闻数据 → 启动 API 服务器

set -e  # 遇到错误立即退出

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           TrendRadar 一键启动脚本                          ║"
echo "║  功能: 环境安装 → 生成新闻 → 启动 API                      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# ==================== 颜色定义 ====================
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# ==================== 函数定义 ====================

# 打印成功信息
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# 打印警告信息
warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# 打印错误信息
error() {
    echo -e "${RED}✗ $1${NC}"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ==================== 1. 检查 Python 环境 ====================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. 检查 Python 环境"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    success "Python 已安装: $PYTHON_VERSION"
else
    error "未找到 Python 3"
    echo "请先安装 Python 3.10 或更高版本"
    echo "macOS: brew install python3"
    echo "Ubuntu: sudo apt-get install python3"
    exit 1
fi

# 检查 Python 版本
PYTHON_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    error "Python 版本过低 ($PYTHON_MAJOR.$PYTHON_MINOR)"
    echo "需要 Python 3.10 或更高版本"
    exit 1
fi

success "Python 版本符合要求 ($PYTHON_MAJOR.$PYTHON_MINOR)"
echo ""

# ==================== 2. 安装依赖 ====================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. 安装/检查依赖"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查关键依赖是否已安装
if python3 -c "import fastapi" 2>/dev/null && \
   python3 -c "import uvicorn" 2>/dev/null && \
   python3 -c "import openai" 2>/dev/null; then
    success "关键依赖已安装"
else
    echo "正在安装依赖..."
    if pip3 install -q -r requirements.txt; then
        success "依赖安装完成"
    else
        error "依赖安装失败"
        echo "尝试手动安装: pip3 install -r requirements.txt"
        exit 1
    fi
fi
echo ""

# ==================== 3. 检查 API Key 配置 ====================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. 检查 LLM API Key 配置"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -z "$LLM_API_KEY" ]; then
    warning "未设置 LLM_API_KEY 环境变量"
    echo ""
    echo "请选择配置方式:"
    echo "  1) 从 .env 文件加载"
    echo "  2) 从 setup-deepseek.sh 加载"
    echo "  3) 手动输入 API Key"
    echo "  4) 跳过（稍后配置）"
    echo ""
    read -p "请选择 [1-4]: " choice

    case $choice in
        1)
            if [ -f ".env" ]; then
                export $(cat .env | grep -v '^#' | xargs)
                success "已从 .env 加载配置"
            else
                error ".env 文件不存在"
                echo "创建示例: cp .env.example .env"
                exit 1
            fi
            ;;
        2)
            if [ -f "setup-deepseek.sh" ]; then
                source setup-deepseek.sh
                success "已从 setup-deepseek.sh 加载配置"
            else
                error "setup-deepseek.sh 文件不存在"
                echo "创建示例: cp setup-deepseek-demo.sh setup-deepseek.sh"
                exit 1
            fi
            ;;
        3)
            read -p "请输入 API Key: " api_key
            export LLM_API_KEY="$api_key"
            read -p "Base URL [https://api.deepseek.com/v1]: " base_url
            base_url=${base_url:-https://api.deepseek.com/v1}
            export LLM_BASE_URL="$base_url"
            read -p "Model [deepseek-chat]: " model
            model=${model:-deepseek-chat}
            export LLM_MODEL="$model"
            success "API Key 已设置"
            ;;
        4)
            warning "跳过 API Key 配置"
            warning "API 服务器将启动,但对话功能不可用"
            ;;
        *)
            error "无效选择"
            exit 1
            ;;
    esac
else
    success "LLM_API_KEY 已配置: ${LLM_API_KEY:0:20}..."
fi

if [ -n "$LLM_BASE_URL" ]; then
    echo "  Base URL: $LLM_BASE_URL"
fi
if [ -n "$LLM_MODEL" ]; then
    echo "  Model: $LLM_MODEL"
fi
echo ""

# ==================== 4. 生成新闻数据 ====================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. 生成新闻数据"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查今天是否已有数据
TODAY=$(date +"%Y年%m月%d日")
if [ -d "output/$TODAY/json" ] && [ -f "output/$TODAY/json/news_summary.json" ]; then
    warning "今天的新闻数据已存在"
    read -p "是否重新生成? [y/N]: " regenerate
    if [[ $regenerate =~ ^[Yy]$ ]]; then
        echo "正在生成新闻数据..."
        if python3 main.py; then
            success "新闻数据生成完成"
        else
            error "新闻数据生成失败"
            warning "API 将启动,但无法注入新闻上下文"
        fi
    else
        success "使用现有新闻数据"
    fi
else
    echo "正在生成新闻数据..."
    echo "提示: 这可能需要 1-2 分钟,请耐心等待..."
    if python3 main.py; then
        success "新闻数据生成完成"
    else
        error "新闻数据生成失败"
        warning "API 将启动,但无法注入新闻上下文"
    fi
fi
echo ""

# ==================== 5. 启动 API 服务器 ====================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. 启动 API 服务器"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 检查端口是否被占用
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1; then
    warning "端口 8000 已被占用"
    read -p "是否杀死占用进程并重启? [y/N]: " kill_process
    if [[ $kill_process =~ ^[Yy]$ ]]; then
        PID=$(lsof -ti:8000)
        kill -9 $PID 2>/dev/null
        success "已停止旧进程 (PID: $PID)"
        sleep 2
    else
        error "无法启动服务器,端口被占用"
        echo "查看占用进程: lsof -i:8000"
        exit 1
    fi
fi

echo "正在启动 API 服务器..."
echo ""

# 启动服务器
python3 -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# 等待服务器启动
echo "等待服务器启动..."
for i in {1..20}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

# 验证服务器状态
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    success "API 服务器启动成功! (PID: $SERVER_PID)"
else
    error "API 服务器启动失败"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  启动成功! 🎉                              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "服务信息:"
echo "  • API 文档: http://localhost:8000/docs"
echo "  • 健康检查: http://localhost:8000/health"
echo "  • 系统状态: http://localhost:8000/api/v1/system/status"
echo ""
echo "测试命令:"
echo "  • 查看系统状态: curl http://localhost:8000/api/v1/system/status"
echo "  • 运行测试脚本: python3 test_api.py"
echo "  • 流式对话示例: python3 example_stream_chat.py"
echo ""
echo "停止服务:"
echo "  • 按 Ctrl+C"
echo "  • 或执行: kill $SERVER_PID"
echo ""
echo "查看文档:"
echo "  • API 使用指南: docs/API_USAGE.md"
echo "  • API Key 配置: docs/API_KEY_SETUP.md"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "服务器正在运行中,按 Ctrl+C 停止..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# 等待用户按 Ctrl+C
wait $SERVER_PID
