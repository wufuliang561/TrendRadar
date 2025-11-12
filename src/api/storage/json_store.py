# coding=utf-8
"""JSON 会话存储模块

提供基于 JSON 文件的会话持久化存储功能
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import threading


class JSONConversationStore:
    """JSON 会话存储类

    负责将对话会话数据持久化到 JSON 文件中

    特性:
    - 每个会话一个 JSON 文件
    - 支持会话历史长度限制
    - 线程安全的文件读写
    - 自动创建存储目录
    """

    def __init__(self, storage_path: str = "conversations"):
        """初始化 JSON 存储

        Args:
            storage_path: 存储目录路径
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self._file_locks: Dict[str, threading.Lock] = {}
        self._locks_lock = threading.Lock()

    def _get_file_lock(self, session_id: str) -> threading.Lock:
        """获取文件锁（线程安全）

        Args:
            session_id: 会话 ID

        Returns:
            threading.Lock: 文件锁
        """
        with self._locks_lock:
            if session_id not in self._file_locks:
                self._file_locks[session_id] = threading.Lock()
            return self._file_locks[session_id]

    def _get_session_path(self, session_id: str) -> Path:
        """获取会话文件路径

        Args:
            session_id: 会话 ID

        Returns:
            Path: 文件路径
        """
        return self.storage_path / f"{session_id}.json"

    def save_session(self, session_data: Dict[str, Any]) -> bool:
        """保存会话数据

        Args:
            session_data: 会话数据字典,必须包含 session_id

        Returns:
            bool: 是否成功
        """
        session_id = session_data.get("session_id")
        if not session_id:
            raise ValueError("session_data 必须包含 session_id")

        file_path = self._get_session_path(session_id)
        file_lock = self._get_file_lock(session_id)

        try:
            with file_lock:
                # 更新时间戳
                session_data["updated_at"] = datetime.now().isoformat()

                # 写入文件
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(session_data, f, ensure_ascii=False, indent=2)

                return True
        except Exception as e:
            print(f"保存会话失败: {e}")
            return False

    def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据

        Args:
            session_id: 会话 ID

        Returns:
            Optional[Dict]: 会话数据,不存在则返回 None
        """
        file_path = self._get_session_path(session_id)

        if not file_path.exists():
            return None

        file_lock = self._get_file_lock(session_id)

        try:
            with file_lock:
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"加载会话失败: {e}")
            return None

    def delete_session(self, session_id: str) -> bool:
        """删除会话数据

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否成功
        """
        file_path = self._get_session_path(session_id)

        if not file_path.exists():
            return False

        file_lock = self._get_file_lock(session_id)

        try:
            with file_lock:
                file_path.unlink()

            # 清理锁
            with self._locks_lock:
                self._file_locks.pop(session_id, None)

            return True
        except Exception as e:
            print(f"删除会话失败: {e}")
            return False

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在

        Args:
            session_id: 会话 ID

        Returns:
            bool: 是否存在
        """
        return self._get_session_path(session_id).exists()

    def list_sessions(self, limit: int = 100) -> List[str]:
        """列出所有会话 ID

        Args:
            limit: 最大返回数量

        Returns:
            List[str]: 会话 ID 列表（按修改时间倒序）
        """
        try:
            files = list(self.storage_path.glob("*.json"))
            # 按修改时间排序（最新的在前）
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            return [f.stem for f in files[:limit]]
        except Exception as e:
            print(f"列出会话失败: {e}")
            return []

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        max_history: int = 20
    ) -> bool:
        """向会话添加消息

        Args:
            session_id: 会话 ID
            role: 消息角色（system/user/assistant）
            content: 消息内容
            max_history: 最大历史消息数（超过自动截断）

        Returns:
            bool: 是否成功
        """
        session = self.load_session(session_id)

        if not session:
            return False

        # 添加新消息
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }

        session["messages"].append(message)

        # 截断历史消息（保留 system 消息）
        if len(session["messages"]) > max_history:
            # 保留第一条 system 消息 + 最新的 (max_history - 1) 条消息
            system_messages = [msg for msg in session["messages"] if msg["role"] == "system"]
            other_messages = [msg for msg in session["messages"] if msg["role"] != "system"]

            if system_messages:
                session["messages"] = system_messages[:1] + other_messages[-(max_history - 1):]
            else:
                session["messages"] = other_messages[-max_history:]

        return self.save_session(session)

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """获取会话的所有消息

        Args:
            session_id: 会话 ID

        Returns:
            List[Dict]: 消息列表
        """
        session = self.load_session(session_id)
        return session.get("messages", []) if session else []

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """清理超过指定天数的会话

        Args:
            days: 保留天数

        Returns:
            int: 删除的会话数量
        """
        import time

        count = 0
        current_time = time.time()
        threshold = days * 24 * 60 * 60  # 转换为秒

        try:
            for file_path in self.storage_path.glob("*.json"):
                # 检查文件修改时间
                if current_time - file_path.stat().st_mtime > threshold:
                    session_id = file_path.stem
                    if self.delete_session(session_id):
                        count += 1
        except Exception as e:
            print(f"清理会话失败: {e}")

        return count
