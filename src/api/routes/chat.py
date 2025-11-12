# coding=utf-8
"""对话 API 路由"""

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from typing import Dict, Any
import json

from src.api.models.schemas import (
    APIResponse,
    CreateSessionRequest,
    CreateSessionResponse,
    SendMessageRequest,
    SendMessageResponse,
    GetSessionResponse,
    ChatMessage
)
from src.api.services.chat_service import ChatService


router = APIRouter(prefix="/chat", tags=["对话管理"])

# 全局 chat_service 实例（将在 server.py 中注入）
_chat_service: ChatService = None


def get_chat_service() -> ChatService:
    """获取 ChatService 实例（依赖注入）"""
    if _chat_service is None:
        raise HTTPException(status_code=500, detail="ChatService 未初始化")
    return _chat_service


def set_chat_service(service: ChatService):
    """设置 ChatService 实例"""
    global _chat_service
    _chat_service = service


@router.post("/sessions", response_model=APIResponse, summary="创建新会话")
async def create_session(
    request: CreateSessionRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    创建新的对话会话

    - **inject_context**: 是否注入最新新闻数据到会话上下文
    - **platforms**: 平台筛选列表（可选）,如 ["zhihu", "weibo"]
    - **news_limit**: 注入的新闻数量限制（默认 50）

    返回会话 ID 和创建信息
    """
    session_id, success, error, news_count = chat_service.create_session(
        inject_context=request.inject_context,
        platforms=request.platforms,
        news_limit=request.news_limit or 50
    )

    if not success:
        return APIResponse(
            success=False,
            error=error or "创建会话失败"
        )

    response_data = CreateSessionResponse(
        session_id=session_id,
        created_at=chat_service.get_session(session_id)["created_at"],
        context_injected=request.inject_context,
        news_count=news_count
    )

    return APIResponse(
        success=True,
        data=response_data.dict(),
        message="会话创建成功"
    )


@router.get("/sessions/{session_id}", response_model=APIResponse, summary="获取会话信息")
async def get_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    获取指定会话的详细信息

    包含会话元数据和完整的消息历史
    """
    session = chat_service.get_session(session_id)

    if not session:
        return APIResponse(
            success=False,
            error="会话不存在"
        )

    # 过滤隐藏消息
    messages = chat_service.get_session_messages(session_id, include_hidden=False)

    response_data = GetSessionResponse(
        session_id=session["session_id"],
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        context_injected=session.get("context_injected", False),
        message_count=len(messages),
        messages=[ChatMessage(**msg) for msg in messages],
        metadata=session.get("metadata")
    )

    return APIResponse(
        success=True,
        data=response_data.dict()
    )


@router.post("/sessions/{session_id}/messages", response_model=APIResponse, summary="发送消息")
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    向指定会话发送消息并获取 AI 回复

    - **message**: 用户消息内容
    - **inject_context**: 是否重新注入最新新闻数据（可选,用于更新上下文）
    - **platforms**: 平台筛选列表（可选）

    返回 AI 的回复和 Token 使用情况
    """
    reply, success, error, token_usage = chat_service.send_message(
        session_id=session_id,
        user_message=request.message,
        inject_context=request.inject_context,
        platforms=request.platforms
    )

    if not success:
        return APIResponse(
            success=False,
            error=error or "发送消息失败"
        )

    from datetime import datetime
    response_data = SendMessageResponse(
        reply=reply,
        session_id=session_id,
        timestamp=datetime.now().isoformat(),
        token_usage=token_usage
    )

    return APIResponse(
        success=True,
        data=response_data.dict(),
        message="消息发送成功"
    )


@router.post("/sessions/{session_id}/messages/stream", summary="发送消息（流式输出）")
async def send_message_stream(
    session_id: str,
    request: SendMessageRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    向指定会话发送消息并获取流式 AI 回复（SSE）

    - **message**: 用户消息内容
    - **inject_context**: 是否重新注入最新新闻数据（可选）
    - **platforms**: 平台筛选列表（可选）

    返回 Server-Sent Events (SSE) 流式数据

    **事件类型**:
    - `data`: 文本内容（逐字输出）
    - `error`: 错误信息
    - `done`: 完成信号（包含完整回复）

    **使用示例**:
    ```javascript
    const eventSource = new EventSource('/api/v1/chat/sessions/xxx/messages/stream');
    eventSource.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'content') {
            console.log(data.content); // 逐字显示
        } else if (data.type === 'done') {
            console.log('完成:', data.full_reply);
            eventSource.close();
        }
    };
    ```
    """
    def event_generator():
        """SSE 事件生成器"""
        try:
            for chunk in chat_service.send_message_stream(
                session_id=session_id,
                user_message=request.message,
                inject_context=request.inject_context,
                platforms=request.platforms
            ):
                # 将数据编码为 SSE 格式
                yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_data = {"type": "error", "error": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # 禁用 Nginx 缓冲
        }
    )


@router.delete("/sessions/{session_id}", response_model=APIResponse, summary="删除会话")
async def delete_session(
    session_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    删除指定的会话

    会话文件将被永久删除
    """
    success = chat_service.delete_session(session_id)

    if not success:
        return APIResponse(
            success=False,
            error="删除失败,会话不存在或已被删除"
        )

    return APIResponse(
        success=True,
        message="会话删除成功"
    )


@router.get("/sessions", response_model=APIResponse, summary="列出所有会话")
async def list_sessions(
    limit: int = 100,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    列出所有会话 ID（按修改时间倒序）

    - **limit**: 最大返回数量（默认 100）
    """
    session_ids = chat_service.list_sessions(limit=limit)

    return APIResponse(
        success=True,
        data={
            "sessions": session_ids,
            "total": len(session_ids)
        }
    )
