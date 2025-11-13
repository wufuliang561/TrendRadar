# coding=utf-8
"""上下文构建器测试"""

import pytest
from src.api.services.context_builder import ContextBuilder


class TestContextBuilder:
    """测试上下文构建器"""

    @pytest.fixture
    def builder(self):
        """创建上下文构建器实例"""
        return ContextBuilder()

    @pytest.fixture
    def sample_context_data(self):
        """示例上下文数据"""
        return {
            "date": "2025-01-13",
            "news_count": 3,
            "platforms": ["知乎", "微博"],
            "news_data": [
                {
                    "title": "测试新闻1",
                    "platform": "知乎",
                    "rank": 1,
                    "count": 5,
                    "weight": 95.5
                },
                {
                    "title": "测试新闻2",
                    "platform": "微博",
                    "rank": 2,
                    "count": 3,
                    "weight": 85.3
                },
                {
                    "title": "测试新闻3",
                    "platform": "知乎",
                    "rank": 5,
                    "count": 2,
                    "weight": 70.1
                }
            ]
        }

    def test_build_system_prompt_without_data(self, builder, sample_context_data):
        """测试构建 system prompt（不包含新闻数据）"""
        prompt = builder.build_system_prompt(sample_context_data, include_news_data=False)

        # 应该包含角色说明
        assert "专业的新闻分析助手" in prompt
        assert "数据字段说明" in prompt
        assert "分析原则" in prompt

        # 应该包含数据范围信息
        assert "2025-01-13" in prompt
        assert "3 条" in prompt
        assert "知乎" in prompt
        assert "微博" in prompt

        # 不应该包含具体新闻数据
        assert "测试新闻1" not in prompt
        assert "测试新闻2" not in prompt

    def test_build_system_prompt_with_data(self, builder, sample_context_data):
        """测试构建 system prompt（包含新闻数据）"""
        prompt = builder.build_system_prompt(sample_context_data, include_news_data=True)

        # 应该包含角色说明
        assert "专业的新闻分析助手" in prompt

        # 应该包含新闻数据标记
        assert "【新闻数据】" in prompt

        # 应该包含具体新闻标题
        assert "测试新闻1" in prompt
        assert "测试新闻2" in prompt
        assert "测试新闻3" in prompt

    def test_build_context_message(self, builder, sample_context_data):
        """测试构建上下文消息"""
        message = builder.build_context_message(sample_context_data)

        # 应该是 JSON 格式
        assert "\"date\"" in message
        assert "\"total_count\"" in message
        assert "\"news\"" in message

        # 应该包含新闻标题
        assert "测试新闻1" in message
        assert "测试新闻2" in message
        assert "测试新闻3" in message

    def test_get_context_stats(self, builder, sample_context_data):
        """测试获取上下文统计信息"""
        stats = builder.get_context_stats(sample_context_data)

        # 验证返回的字段
        assert "news_count" in stats
        assert "platforms" in stats
        assert "estimated_context_tokens" in stats
        assert "estimated_system_tokens" in stats
        assert "estimated_system_with_data_tokens" in stats
        assert "estimated_total_tokens" in stats
        assert "data_size_bytes" in stats

        # 验证基本数值
        assert stats["news_count"] == 3
        assert stats["platforms"] == ["知乎", "微博"]
        assert stats["estimated_system_tokens"] > 0
        assert stats["estimated_system_with_data_tokens"] > stats["estimated_system_tokens"]

    def test_estimate_tokens(self, builder):
        """测试 token 估算"""
        # 纯中文
        chinese_text = "这是一段中文文本"
        tokens = builder.estimate_tokens(chinese_text)
        assert tokens > 0

        # 纯英文
        english_text = "This is an English text"
        tokens = builder.estimate_tokens(english_text)
        assert tokens > 0

        # 混合文本
        mixed_text = "这是 mixed 文本 with English"
        tokens = builder.estimate_tokens(mixed_text)
        assert tokens > 0
