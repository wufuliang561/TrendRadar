# coding=utf-8
"""信息源注册器"""

from typing import List, Dict, Type, Optional
from src.sources.base import BaseSource


class SourceRegistry:
    """信息源注册器

    管理所有可用的信息源
    """

    def __init__(self):
        """初始化注册器"""
        self._sources: Dict[str, Type[BaseSource]] = {}

    def register(self, source_class: Type[BaseSource]) -> None:
        """注册信息源

        Args:
            source_class: 信息源类
        """
        # 创建临时实例以获取 source_id
        temp_instance = source_class({})
        source_id = temp_instance.source_id

        if source_id in self._sources:
            print(f"警告: 信息源 {source_id} 已存在，将被覆盖")

        self._sources[source_id] = source_class
        print(f"注册信息源: {source_id} ({temp_instance.source_name})")

    def get_source(self, source_id: str, config: Dict) -> Optional[BaseSource]:
        """获取信息源实例

        Args:
            source_id: 信息源ID
            config: 配置字典

        Returns:
            Optional[BaseSource]: 信息源实例，不存在返回 None
        """
        source_class = self._sources.get(source_id)
        if not source_class:
            return None

        return source_class(config)

    def get_enabled_sources(self, config: Dict) -> List[BaseSource]:
        """获取所有启用的信息源实例

        Args:
            config: 配置字典

        Returns:
            List[BaseSource]: 启用的信息源列表
        """
        enabled = []
        sources_config = config.get("SOURCES", {})
        enabled_ids = sources_config.get("enabled", [])

        for source_id in enabled_ids:
            source = self.get_source(source_id, config)
            if source and source.is_enabled:
                enabled.append(source)

        return enabled

    def get_all_sources(self, config: Dict) -> List[BaseSource]:
        """获取所有信息源实例（无论是否启用）

        Args:
            config: 配置字典

        Returns:
            List[BaseSource]: 所有信息源列表
        """
        return [
            source_class(config)
            for source_class in self._sources.values()
        ]

    def list_source_ids(self) -> List[str]:
        """列出所有已注册的信息源ID

        Returns:
            List[str]: 信息源ID列表
        """
        return list(self._sources.keys())

    def __contains__(self, source_id: str) -> bool:
        """检查信息源是否已注册

        Args:
            source_id: 信息源ID

        Returns:
            bool: 是否已注册
        """
        return source_id in self._sources

    def __len__(self) -> int:
        """获取已注册信息源数量

        Returns:
            int: 信息源数量
        """
        return len(self._sources)


# 全局注册器实例
_global_registry = SourceRegistry()


def register_source(source_class: Type[BaseSource]) -> None:
    """注册信息源到全局注册器

    Args:
        source_class: 信息源类
    """
    _global_registry.register(source_class)


def get_registry() -> SourceRegistry:
    """获取全局注册器

    Returns:
        SourceRegistry: 全局注册器实例
    """
    return _global_registry


# 自动注册内置信息源
def auto_register_builtin_sources():
    """自动注册内置信息源"""
    try:
        from src.sources.newsnow import NewNowSource
        register_source(NewNowSource)
    except ImportError:
        print("警告: 无法导入 NewNowSource")

    try:
        from src.sources.rss import RSSSource
        register_source(RSSSource)
    except ImportError:
        print("警告: 无法导入 RSSSource")


# 初始化时自动注册
auto_register_builtin_sources()
