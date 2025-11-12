# coding=utf-8
"""会话管理服务

整合上下文构建、大模型调用和会话存储
"""

import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Iterator

from src.api.storage.json_store import JSONConversationStore
from src.api.services.context_builder import ContextBuilder
from src.api.services.llm_service import LLMService


class ChatService:
    """会话管理服务

    负责:
    - 创建和管理会话
    - 处理用户消息
    - 调用大模型生成回复
    - 维护对话历史
    """

    def __init__(
        self,
        llm_service: LLMService,
        context_builder: ContextBuilder,
        store: JSONConversationStore,
        max_history_length: int = 20
    ):
        """初始化会话服务

        Args:
            llm_service: 大模型服务
            context_builder: 上下文构建器
            store: 会话存储
            max_history_length: 最大历史消息数
        """
        self.llm_service = llm_service
        self.context_builder = context_builder
        self.store = store
        self.max_history_length = max_history_length

    def create_session(
        self,
        inject_context: bool = True,
        platforms: Optional[List[str]] = None,
        news_limit: int = 50
    ) -> Tuple[str, bool, Optional[str], Optional[int]]:
        """创建新会话

        Args:
            inject_context: 是否注入新闻上下文
            platforms: 平台筛选列表
            news_limit: 新闻数量限制

        Returns:
            Tuple: (会话ID, 是否成功, 错误信息, 新闻数量)
        """
        session_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        # 初始化会话数据
        session_data = {
            "session_id": session_id,
            "created_at": created_at,
            "updated_at": created_at,
            "context_injected": inject_context,
            "metadata": {},
            "messages": []
        }

        # 注入新闻上下文
        news_count = None
        if inject_context:
            context_data = self.context_builder.get_latest_news_context(
                platforms=platforms,
                limit=news_limit
            )

            if context_data.get("error"):
                return session_id, False, context_data["error"], None

            # 构建 system prompt
            system_prompt = self.context_builder.build_system_prompt(context_data)
            context_message = self.context_builder.build_context_message(context_data)

            # 添加 system 消息
            session_data["messages"].append({
                "role": "system",
                "content": system_prompt,
                "timestamp": created_at
            })

            # 添加上下文数据作为第一条 user 消息(隐藏的)
            session_data["messages"].append({
                "role": "user",
                "content": f"以下是今天的新闻数据:\n{context_message}",
                "timestamp": created_at,
                "hidden": True  # 标记为隐藏,不在历史中显示给用户
            })

            # 添加 assistant 确认消息
            session_data["messages"].append({
                "role": "assistant",
                "content": f"我已收到 {context_data['news_count']} 条新闻数据,准备好为您分析了。请问有什么需要了解的吗?",
                "timestamp": created_at
            })

            # 保存元数据
            session_data["metadata"] = {
                "news_date": context_data.get("date"),
                "news_count": context_data.get("news_count"),
                "platforms": context_data.get("platforms", [])
            }

            news_count = context_data.get("news_count")

        # 保存会话
        success = self.store.save_session(session_data)

        if not success:
            return session_id, False, "保存会话失败", None

        return session_id, True, None, news_count

    def send_message(
        self,
        session_id: str,
        user_message: str,
        inject_context: bool = False,
        platforms: Optional[List[str]] = None
    ) -> Tuple[Optional[str], bool, Optional[str], Optional[Dict[str, int]]]:
        """发送消息并获取回复

        Args:
            session_id: 会话 ID
            user_message: 用户消息
            inject_context: 是否重新注入上下文
            platforms: 平台筛选

        Returns:
            Tuple: (AI回复, 是否成功, 错误信息, Token使用情况)
        """
        # 加载会话
        session = self.store.load_session(session_id)
        if not session:
            return None, False, "会话不存在", None

        # 重新注入上下文（可选）
        if inject_context:
            context_data = self.context_builder.get_latest_news_context(
                platforms=platforms,
                limit=50
            )

            if not context_data.get("error"):
                context_message = self.context_builder.build_context_message(context_data)
                user_message = f"{user_message}\n\n最新数据:\n{context_message}"

        # 添加用户消息
        session["messages"].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })

        # 准备发送给大模型的消息（排除隐藏消息）
        llm_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in session["messages"]
            if not msg.get("hidden", False)
        ]

        # 调用大模型
        reply, success, error, token_usage = self.llm_service.chat_completion(llm_messages)

        if not success:
            return None, False, error, None

        # 添加 assistant 回复
        session["messages"].append({
            "role": "assistant",
            "content": reply,
            "timestamp": datetime.now().isoformat()
        })

        # 保存会话（带历史截断）
        self.store.add_message(
            session_id,
            "assistant",
            reply,
            max_history=self.max_history_length
        )

        return reply, True, None, token_usage

    def send_message_stream(
        self,
        session_id: str,
        user_message: str,
        inject_context: bool = False,
        platforms: Optional[List[str]] = None
    ) -> Iterator[Dict[str, Any]]:
        """发送消息并获取流式回复

        Args:
            session_id: 会话 ID
            user_message: 用户消息
            inject_context: 是否重新注入上下文
            platforms: 平台筛选

        Yields:
            Dict: 流式数据块
                - type: "content" | "error" | "done"
                - content: 文本内容
                - error: 错误信息
                - full_reply: 完整回复（仅 type="done"）
        """
        # 加载会话
        session = self.store.load_session(session_id)
        if not session:
            yield {
                "type": "error",
                "error": "会话不存在"
            }
            return

        # 重新注入上下文（可选）
        if inject_context:
            context_data = self.context_builder.get_latest_news_context(
                platforms=platforms,
                limit=50
            )

            if not context_data.get("error"):
                context_message = self.context_builder.build_context_message(context_data)
                user_message = f"{user_message}\n\n最新数据:\n{context_message}"

        # 添加用户消息
        session["messages"].append({
            "role": "user",
            "content": user_message,
            "timestamp": datetime.now().isoformat()
        })

        # 准备发送给大模型的消息（排除隐藏消息）
        llm_messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in session["messages"]
            if not msg.get("hidden", False)
        ]

        # 调用大模型流式 API
        full_reply = ""
        has_error = False

        for chunk in self.llm_service.chat_completion_stream(llm_messages):
            if chunk["type"] == "content":
                full_reply += chunk["content"]
                yield chunk
            elif chunk["type"] == "error":
                has_error = True
                yield chunk
                return
            elif chunk["type"] == "done":
                full_reply = chunk.get("full_content", full_reply)
                break

        if not has_error and full_reply:
            # 添加 assistant 回复到会话
            session["messages"].append({
                "role": "assistant",
                "content": full_reply,
                "timestamp": datetime.now().isoformat()
            })

            # 保存会话
            self.store.save_session(session)

            # 返回完成信号
            yield {
                "type": "done",
                "full_reply": full_reply
            }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息

        Args:
            session_id: 会话 ID

        Returns:
            Optional[Dict]: 会话数据
        """
        return self.store.load_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """删除会话

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功
        """
        return self.store.delete_session(session_id)

    def list_sessions(self, limit: int = 100) -> List[str]:
        """列出所有会话

        Args:
            limit: 最大返回数量

        Returns:
            List[str]: 会话 ID 列表
        """
        return self.store.list_sessions(limit=limit)

    def get_session_messages(
        self,
        session_id: str,
        include_hidden: bool = False
    ) -> List[Dict[str, Any]]:
        """获取会话消息列表

        Args:
            session_id: 会话 ID
            include_hidden: 是否包含隐藏消息

        Returns:
            List[Dict]: 消息列表
        """
        session = self.store.load_session(session_id)
        if not session:
            return []

        messages = session.get("messages", [])

        if not include_hidden:
            messages = [msg for msg in messages if not msg.get("hidden", False)]

        return messages
