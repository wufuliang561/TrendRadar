# coding=utf-8
"""TrendRadar FastAPI 服务器

提供热点新闻 AI 分析的 RESTful API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import ConfigManager
from src.api.storage.json_store import JSONConversationStore
from src.api.services.context_builder import ContextBuilder
from src.api.services.llm_service import create_llm_service_from_config
from src.api.services.chat_service import ChatService
from src.api.routes import chat, system, dashboard


# 全局实例
config_manager: ConfigManager = None
chat_service: ChatService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global config_manager, chat_service

    # 启动时初始化
    print("=" * 60)
    print("TrendRadar API 服务器启动中...")
    print("=" * 60)

    try:
        # 1. 加载配置
        config_manager = ConfigManager()
        print("✓ 配置加载成功")

        # 2. 初始化服务
        llm_config = config_manager.get("LLM_CONFIG", {})
        chat_config = config_manager.get("CHAT_CONFIG", {})

        # 检查 LLM 配置
        if not llm_config.get("API_KEY"):
            print("⚠ 警告: 未配置 LLM API Key,请设置环境变量 LLM_API_KEY")
        else:
            print(f"✓ LLM 配置完成: {llm_config.get('PROVIDER')} / {llm_config.get('MODEL')}")

        # 创建服务实例
        llm_service = create_llm_service_from_config(config_manager.config)
        context_builder = ContextBuilder()
        store = JSONConversationStore(chat_config.get("STORAGE_PATH", "conversations"))

        print(f"✓ 会话存储路径: {chat_config.get('STORAGE_PATH', 'conversations')}")

        # 创建 ChatService
        chat_service = ChatService(
            llm_service=llm_service,
            context_builder=context_builder,
            store=store,
            max_history_length=chat_config.get("MAX_HISTORY_LENGTH", 20)
        )

        # 设置依赖注入
        chat.set_chat_service(chat_service)
        system.set_dependencies(config_manager, context_builder, store, llm_service)

        print("✓ 所有服务初始化完成")
        print("=" * 60)
        print(f"📚 API 文档地址: http://localhost:8000/docs")
        print(f"🔍 ReDoc 文档: http://localhost:8000/redoc")
        print("=" * 60)

    except Exception as e:
        print(f"✗ 初始化失败: {e}")
        import traceback
        traceback.print_exc()
        raise

    yield

    # 关闭时清理
    print("\nTrendRadar API 服务器关闭")


# 创建 FastAPI 应用
app = FastAPI(
    title="TrendRadar API",
    description="热点新闻 AI 分析 API - 支持大模型对话分析",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置（允许跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(system.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "TrendRadar API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    print("""
╔════════════════════════════════════════════════════════════╗
║                  TrendRadar API Server                     ║
║                热点新闻 AI 分析服务                         ║
╚════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
