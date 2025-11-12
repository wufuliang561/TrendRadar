# coding=utf-8
"""测试信息源注册器"""

import pytest
from src.sources.registry import SourceRegistry, get_registry, register_source
from src.sources.base import BaseSource
from src.models.news import News
from typing import List


class MockSource(BaseSource):
    """模拟信息源（用于测试）"""

    @property
    def source_id(self) -> str:
        return "mock"

    @property
    def source_name(self) -> str:
        return "模拟信息源"

    def fetch_news(self, **kwargs) -> List[News]:
        return [
            News(
                title="测试新闻1",
                url="https://example.com/1",
                platform="mock_platform",
                platform_name="模拟平台",
                rank=1,
                source_id=self.source_id
            )
        ]


class TestSourceRegistry:
    """测试 SourceRegistry 类"""

    def test_registry_creation(self):
        """测试创建注册器"""
        registry = SourceRegistry()
        assert len(registry) == 0

    def test_register_source(self):
        """测试注册信息源"""
        registry = SourceRegistry()
        registry.register(MockSource)

        assert "mock" in registry
        assert len(registry) == 1

    def test_get_source(self):
        """测试获取信息源实例"""
        registry = SourceRegistry()
        registry.register(MockSource)

        config = {
            "SOURCES": {
                "enabled": ["mock"],
                "mock": {}
            }
        }

        source = registry.get_source("mock", config)
        assert source is not None
        assert source.source_id == "mock"
        assert source.source_name == "模拟信息源"

    def test_get_nonexistent_source(self):
        """测试获取不存在的信息源"""
        registry = SourceRegistry()
        config = {"SOURCES": {}}

        source = registry.get_source("nonexistent", config)
        assert source is None

    def test_get_enabled_sources(self):
        """测试获取启用的信息源"""
        registry = SourceRegistry()
        registry.register(MockSource)

        config = {
            "SOURCES": {
                "enabled": ["mock"],
                "mock": {}
            }
        }

        enabled_sources = registry.get_enabled_sources(config)
        assert len(enabled_sources) == 1
        assert enabled_sources[0].source_id == "mock"

    def test_get_enabled_sources_none_enabled(self):
        """测试没有启用的信息源"""
        registry = SourceRegistry()
        registry.register(MockSource)

        config = {
            "SOURCES": {
                "enabled": [],
                "mock": {}
            }
        }

        enabled_sources = registry.get_enabled_sources(config)
        assert len(enabled_sources) == 0

    def test_get_all_sources(self):
        """测试获取所有信息源"""
        registry = SourceRegistry()
        registry.register(MockSource)

        config = {"SOURCES": {}}
        all_sources = registry.get_all_sources(config)

        assert len(all_sources) == 1
        assert all_sources[0].source_id == "mock"

    def test_list_source_ids(self):
        """测试列出所有信息源ID"""
        registry = SourceRegistry()
        registry.register(MockSource)

        ids = registry.list_source_ids()
        assert "mock" in ids

    def test_global_registry(self):
        """测试全局注册器"""
        registry = get_registry()
        assert registry is not None

        # 全局注册器应该已经注册了内置信息源
        ids = registry.list_source_ids()
        assert "newsnow" in ids or "rss" in ids
