# coding=utf-8
"""系统和新闻 API 路由"""

from fastapi import APIRouter, Depends
from typing import Optional, List

from src.api.models.schemas import APIResponse, SystemStatus, ConfigInfo, NewsListResponse, NewsItem
from src.core.config import ConfigManager
from src.api.services.context_builder import ContextBuilder
from src.api.storage.json_store import JSONConversationStore
from src.api.services.llm_service import LLMService
import time


router = APIRouter(tags=["系统和数据"])

# 全局实例（将在 server.py 中注入）
_config_manager: ConfigManager = None
_context_builder: ContextBuilder = None
_store: JSONConversationStore = None
_llm_service: LLMService = None
_server_start_time = time.time()


def get_config_manager() -> ConfigManager:
    """获取 ConfigManager 实例"""
    return _config_manager


def get_context_builder() -> ContextBuilder:
    """获取 ContextBuilder 实例"""
    return _context_builder


def set_dependencies(config: ConfigManager, context: ContextBuilder, store: JSONConversationStore, llm: LLMService):
    """设置依赖实例"""
    global _config_manager, _context_builder, _store, _llm_service
    _config_manager = config
    _context_builder = context
    _store = store
    _llm_service = llm


@router.get("/system/status", response_model=APIResponse, summary="获取系统状态")
async def get_system_status(
    config: ConfigManager = Depends(get_config_manager)
):
    """
    获取系统运行状态

    包含服务状态、配置信息、活跃会话数等
    """
    # 计算运行时间
    uptime_seconds = int(time.time() - _server_start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    uptime = f"{hours}小时{minutes}分钟"

    # 统计活跃会话数
    active_sessions = len(_store.list_sessions()) if _store else 0

    # 检查 LLM 是否配置
    llm_config = config.get("LLM_CONFIG", {})
    llm_configured = bool(llm_config.get("API_KEY"))

    status = SystemStatus(
        service="TrendRadar API",
        version="1.0.0",
        status="running",
        uptime=uptime,
        llm_configured=llm_configured,
        storage_path=config.get("CHAT_CONFIG", {}).get("STORAGE_PATH", "conversations"),
        active_sessions=active_sessions
    )

    return APIResponse(
        success=True,
        data=status.dict()
    )


@router.get("/system/config", response_model=APIResponse, summary="获取配置信息")
async def get_config_info(
    config: ConfigManager = Depends(get_config_manager)
):
    """
    获取系统配置信息

    不包含敏感信息（如 API Key）
    """
    llm_config = config.get("LLM_CONFIG", {})
    chat_config = config.get("CHAT_CONFIG", {})
    platforms = config.get("PLATFORMS", [])

    config_info = ConfigInfo(
        llm_provider=llm_config.get("PROVIDER", "openai"),
        llm_model=llm_config.get("MODEL", "gpt-4"),
        llm_base_url=llm_config.get("BASE_URL", "https://api.openai.com/v1"),
        max_history_length=chat_config.get("MAX_HISTORY_LENGTH", 20),
        context_news_limit=chat_config.get("CONTEXT_NEWS_LIMIT", 50),
        platforms=platforms
    )

    return APIResponse(
        success=True,
        data=config_info.dict()
    )


@router.get("/news/latest", response_model=APIResponse, summary="获取最新新闻")
async def get_latest_news(
    platforms: Optional[str] = None,
    limit: int = 50,
    context_builder: ContextBuilder = Depends(get_context_builder)
):
    """
    获取最新的新闻数据

    - **platforms**: 平台筛选,多个平台用逗号分隔（如 "zhihu,weibo"）
    - **limit**: 返回的新闻数量限制（默认 50）

    返回精简的新闻列表（title, platform, rank, count, weight）
    """
    # 解析平台参数
    platform_list = None
    if platforms:
        platform_list = [p.strip() for p in platforms.split(",") if p.strip()]

    # 获取新闻数据
    context_data = context_builder.get_latest_news_context(
        platforms=platform_list,
        limit=limit
    )

    if context_data.get("error"):
        return APIResponse(
            success=False,
            error=context_data["error"]
        )

    # 转换为 NewsItem 模型
    news_items = [NewsItem(**item) for item in context_data.get("news_data", [])]

    response_data = NewsListResponse(
        total=len(news_items),
        news=news_items,
        date=context_data.get("date")
    )

    return APIResponse(
        success=True,
        data=response_data.dict()
    )


@router.get("/", summary="API 根路径")
async def root():
    """
    API 根路径

    返回欢迎信息和文档链接
    """
    return {
        "service": "TrendRadar API",
        "version": "1.0.0",
        "docs": "/docs",
        "description": "热点新闻 AI 分析 API"
    }
