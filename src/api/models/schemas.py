# coding=utf-8
"""API 数据模型定义

使用 Pydantic 进行数据验证和序列化
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ==================== 通用响应模型 ====================

class APIResponse(BaseModel):
    """API 标准响应模型"""
    success: bool = Field(..., description="请求是否成功")
    data: Optional[Any] = Field(None, description="响应数据")
    message: Optional[str] = Field(None, description="提示消息")
    error: Optional[str] = Field(None, description="错误信息")


# ==================== 新闻相关模型 ====================

class NewsItem(BaseModel):
    """新闻项模型（精简版）"""
    title: str = Field(..., description="新闻标题")
    platform: str = Field(..., description="平台名称")
    rank: int = Field(..., description="排名")
    count: int = Field(default=1, description="出现次数")
    weight: float = Field(default=0.0, description="权重分数")
    url: Optional[str] = Field(None, description="新闻链接")


class NewsListResponse(BaseModel):
    """新闻列表响应"""
    total: int = Field(..., description="新闻总数")
    news: List[NewsItem] = Field(..., description="新闻列表")
    date: Optional[str] = Field(None, description="数据日期")


# ==================== 会话相关模型 ====================

class ChatMessage(BaseModel):
    """聊天消息模型"""
    role: str = Field(..., description="消息角色：system/user/assistant")
    content: str = Field(..., description="消息内容")
    timestamp: Optional[str] = Field(None, description="时间戳")


class CreateSessionRequest(BaseModel):
    """创建会话请求"""
    inject_context: bool = Field(default=True, description="是否注入新闻上下文")
    platforms: Optional[List[str]] = Field(None, description="平台筛选列表")
    news_limit: Optional[int] = Field(50, description="新闻数量限制")


class CreateSessionResponse(BaseModel):
    """创建会话响应"""
    session_id: str = Field(..., description="会话 ID")
    created_at: str = Field(..., description="创建时间")
    context_injected: bool = Field(..., description="是否已注入上下文")
    news_count: Optional[int] = Field(None, description="注入的新闻数量")


class SendMessageRequest(BaseModel):
    """发送消息请求"""
    message: str = Field(..., min_length=1, max_length=2000, description="用户消息")
    inject_context: bool = Field(default=False, description="是否重新注入上下文")
    platforms: Optional[List[str]] = Field(None, description="平台筛选列表")


class SendMessageResponse(BaseModel):
    """发送消息响应"""
    reply: str = Field(..., description="AI 回复")
    session_id: str = Field(..., description="会话 ID")
    timestamp: str = Field(..., description="时间戳")
    token_usage: Optional[Dict[str, int]] = Field(None, description="Token 使用情况")


class GetSessionResponse(BaseModel):
    """获取会话响应"""
    session_id: str = Field(..., description="会话 ID")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")
    context_injected: bool = Field(..., description="是否已注入上下文")
    message_count: int = Field(..., description="消息数量")
    messages: List[ChatMessage] = Field(..., description="消息列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="会话元数据")


# ==================== 系统相关模型 ====================

class SystemStatus(BaseModel):
    """系统状态模型"""
    service: str = Field(default="TrendRadar API", description="服务名称")
    version: str = Field(default="1.0.0", description="版本号")
    status: str = Field(default="running", description="运行状态")
    uptime: Optional[str] = Field(None, description="运行时间")
    llm_configured: bool = Field(..., description="大模型是否配置")
    storage_path: str = Field(..., description="存储路径")
    active_sessions: int = Field(..., description="活跃会话数")


class ConfigInfo(BaseModel):
    """配置信息模型"""
    llm_provider: str = Field(..., description="大模型服务商")
    llm_model: str = Field(..., description="模型名称")
    llm_base_url: str = Field(..., description="API 基础 URL")
    max_history_length: int = Field(..., description="最大历史长度")
    context_news_limit: int = Field(..., description="上下文新闻限制")
    platforms: List[Dict[str, str]] = Field(..., description="监控平台列表")
