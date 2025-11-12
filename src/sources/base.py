# coding=utf-8
"""信息源抽象基类"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.models.news import News


class BaseSource(ABC):
    """信息源抽象基类

    所有信息源实现都应继承此类并实现抽象方法
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化信息源

        Args:
            config: 配置字典
        """
        self.config = config
        self._enabled = self._check_enabled()

    @property
    @abstractmethod
    def source_id(self) -> str:
        """信息源唯一标识

        Returns:
            str: 信息源 ID（如 'newsnow', 'rss'）
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """信息源显示名称

        Returns:
            str: 显示名称（如 'NewNow 热榜聚合', 'RSS 订阅'）
        """
        pass

    @abstractmethod
    def fetch_news(self, **kwargs) -> List[News]:
        """获取新闻列表

        Args:
            **kwargs: 可选参数，由子类定义

        Returns:
            List[News]: 标准化的 News 对象列表
        """
        pass

    def _check_enabled(self) -> bool:
        """检查该信息源是否启用

        Returns:
            bool: 是否启用
        """
        sources_config = self.config.get("SOURCES", {})
        enabled_sources = sources_config.get("enabled", [])
        return self.source_id in enabled_sources

    @property
    def is_enabled(self) -> bool:
        """检查信息源是否启用

        Returns:
            bool: 是否启用
        """
        return self._enabled

    def get_source_config(self) -> Dict[str, Any]:
        """获取该信息源的配置

        Returns:
            Dict: 信息源特定的配置
        """
        sources_config = self.config.get("SOURCES", {})
        return sources_config.get(self.source_id, {})

    def validate_config(self) -> bool:
        """验证配置是否完整

        子类可以重写此方法以添加特定的配置验证逻辑

        Returns:
            bool: 配置是否有效
        """
        return True

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.source_name} ({self.source_id})"

    def __repr__(self) -> str:
        """开发者表示"""
        return f"<{self.__class__.__name__} source_id='{self.source_id}' enabled={self.is_enabled}>"
