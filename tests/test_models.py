# coding=utf-8
"""测试数据模型"""

from datetime import datetime
import pytest
from src.models.news import News, NewsStatistic


class TestNews:
    """测试 News 类"""

    def test_news_creation(self):
        """测试新闻对象创建"""
        news = News(
            title="测试新闻标题",
            url="https://example.com/news/1",
            platform="zhihu",
            platform_name="知乎",
            rank=1,
            hotness=1000,
            source_id="newsnow"
        )

        assert news.title == "测试新闻标题"
        assert news.url == "https://example.com/news/1"
        assert news.platform == "zhihu"
        assert news.platform_name == "知乎"
        assert news.rank == 1
        assert news.hotness == 1000
        assert news.source_id == "newsnow"
        assert news.timestamp is not None

    def test_news_with_timestamp(self):
        """测试带时间戳的新闻对象"""
        now = datetime.now()
        news = News(
            title="测试新闻",
            url="https://example.com",
            platform="weibo",
            platform_name="微博",
            rank=2,
            timestamp=now
        )

        assert news.timestamp == now

    def test_calculate_weight(self):
        """测试权重计算"""
        news = News(
            title="测试新闻",
            url="https://example.com",
            platform="zhihu",
            platform_name="知乎",
            rank=1
        )

        # 测试单次出现在第1名
        weight = news.calculate_weight(ranks=[1], count=1)
        assert weight > 0

        # 测试多次出现
        weight = news.calculate_weight(ranks=[1, 2, 3], count=3)
        assert weight > 0

        # 测试高排名次数多的情况
        weight_high = news.calculate_weight(ranks=[1, 2, 3], count=3)
        weight_low = news.calculate_weight(ranks=[8, 9, 10], count=3)
        assert weight_high > weight_low

    def test_calculate_weight_with_custom_weights(self):
        """测试自定义权重系数"""
        news = News(
            title="测试新闻",
            url="https://example.com",
            platform="zhihu",
            platform_name="知乎",
            rank=1
        )

        # 使用自定义权重
        weight = news.calculate_weight(
            ranks=[1, 2, 3],
            count=3,
            rank_weight=0.5,
            frequency_weight=0.3,
            hotness_weight=0.2
        )
        assert weight > 0

    def test_to_dict(self):
        """测试转换为字典"""
        news = News(
            title="测试新闻",
            url="https://example.com",
            platform="zhihu",
            platform_name="知乎",
            rank=1,
            hotness=1000
        )

        data = news.to_dict()
        assert data["title"] == "测试新闻"
        assert data["url"] == "https://example.com"
        assert data["platform"] == "zhihu"
        assert data["rank"] == 1
        assert "timestamp" in data

    def test_from_dict(self):
        """测试从字典创建对象"""
        data = {
            "title": "测试新闻",
            "url": "https://example.com",
            "platform": "zhihu",
            "platform_name": "知乎",
            "rank": 1,
            "hotness": 1000
        }

        news = News.from_dict(data)
        assert news.title == "测试新闻"
        assert news.url == "https://example.com"
        assert news.platform == "zhihu"
        assert news.rank == 1


class TestNewsStatistic:
    """测试 NewsStatistic 类"""

    def test_news_statistic_creation(self):
        """测试统计对象创建"""
        stat = NewsStatistic(
            title="测试新闻",
            source_name="知乎",
            url="https://example.com",
            ranks=[1, 2, 3],
            count=3,
            first_time="10时30分",
            last_time="14时30分"
        )

        assert stat.title == "测试新闻"
        assert stat.source_name == "知乎"
        assert stat.ranks == [1, 2, 3]
        assert stat.count == 3
        assert stat.first_time == "10时30分"
        assert stat.last_time == "14时30分"

    def test_calculate_weight(self):
        """测试统计权重计算"""
        stat = NewsStatistic(
            title="测试新闻",
            source_name="知乎",
            url="https://example.com",
            ranks=[1, 2, 3],
            count=3
        )

        weight = stat.calculate_weight()
        assert weight > 0
        assert stat.weight == weight

    def test_is_new_flag(self):
        """测试新增标记"""
        stat = NewsStatistic(
            title="测试新闻",
            source_name="知乎",
            url="https://example.com",
            is_new=True
        )

        assert stat.is_new is True
