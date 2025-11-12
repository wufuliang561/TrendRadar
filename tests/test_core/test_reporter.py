# coding=utf-8
"""测试新闻报告生成模块"""

import pytest
from pathlib import Path
from src.core.reporter import NewsReporter
from src.models.news import News, WordGroupStatistic


@pytest.fixture
def reporter():
    """创建报告生成器"""
    return NewsReporter(rank_threshold=10)


@pytest.fixture
def sample_news_list():
    """创建示例新闻列表"""
    return [
        News(
            title="测试新闻A",
            url="https://example.com/a",
            platform="zhihu",
            platform_name="知乎",
            rank=1,
            extra={
                "time_display": "120000 ~ 130000",
                "count": 2,
                "all_ranks": [1, 2],
                "is_new": False,
                "mobileUrl": "https://m.example.com/a"
            }
        ),
        News(
            title="测试新闻B",
            url="https://example.com/b",
            platform="weibo",
            platform_name="微博",
            rank=5,
            extra={
                "time_display": "120000",
                "count": 1,
                "all_ranks": [5],
                "is_new": True,
                "mobileUrl": ""
            }
        ),
    ]


@pytest.fixture
def sample_stats(sample_news_list):
    """创建示例统计"""
    return [
        WordGroupStatistic(
            word="测试 新闻",
            count=2,
            news_list=sample_news_list,
            percentage=100.0
        )
    ]


class TestNewsReporter:
    """测试 NewsReporter 类"""

    def test_initialization(self, reporter):
        """测试初始化"""
        assert reporter.rank_threshold == 10

    def test_prepare_report_data(self, reporter, sample_stats):
        """测试准备报告数据"""
        report_data = reporter.prepare_report_data(
            stats=sample_stats,
            failed_ids=["failed1"],
            new_news_list=None,
            mode="daily"
        )

        assert "stats" in report_data
        assert "new_titles" in report_data
        assert "failed_ids" in report_data
        assert "total_new_count" in report_data

        # 检查stats
        assert len(report_data["stats"]) == 1
        assert report_data["stats"][0]["word"] == "测试 新闻"
        assert report_data["stats"][0]["count"] == 2
        assert len(report_data["stats"][0]["titles"]) == 2

        # 检查failed_ids
        assert report_data["failed_ids"] == ["failed1"]

    def test_prepare_report_data_with_new_news(self, reporter, sample_stats):
        """测试准备报告数据（带新增新闻）"""
        new_news = News(
            title="新增新闻C",
            url="https://example.com/c",
            platform="douyin",
            platform_name="抖音",
            rank=3,
            mobile_url="https://m.example.com/c"
        )

        report_data = reporter.prepare_report_data(
            stats=sample_stats,
            new_news_list=[new_news],
            mode="daily"
        )

        # 检查新增新闻
        assert len(report_data["new_titles"]) == 1
        assert report_data["new_titles"][0]["source_name"] == "抖音"
        assert len(report_data["new_titles"][0]["titles"]) == 1
        assert report_data["total_new_count"] == 1

    def test_prepare_report_data_incremental_mode(self, reporter, sample_stats):
        """测试增量模式（隐藏新增区域）"""
        new_news = News(
            title="新增新闻C",
            url="https://example.com/c",
            platform="douyin",
            platform_name="抖音",
            rank=3
        )

        report_data = reporter.prepare_report_data(
            stats=sample_stats,
            new_news_list=[new_news],
            mode="incremental"
        )

        # 增量模式下新增区域应该被隐藏
        assert len(report_data["new_titles"]) == 0
        assert report_data["total_new_count"] == 0

    def test_format_rank_display(self, reporter):
        """测试排名格式化"""
        # 单个排名，高亮
        result = reporter.format_rank_display([5], 10, "html")
        assert "[5]" in result
        assert "red" in result  # 应该有高亮

        # 范围排名，高亮
        result = reporter.format_rank_display([3, 5, 7], 10, "feishu")
        assert "[3 - 7]" in result
        assert "red" in result

        # 范围排名，不高亮（超过阈值）
        result = reporter.format_rank_display([15, 20], 10, "dingtalk")
        assert "[15 - 20]" in result
        # 不高亮时不应该有格式符号
        assert result == "[15 - 20]"

        # 空排名
        result = reporter.format_rank_display([], 10, "html")
        assert result == ""

    def test_format_title_for_feishu(self, reporter):
        """测试飞书格式化"""
        title_data = {
            "title": "测试新闻",
            "source_name": "知乎",
            "ranks": [5],
            "rank_threshold": 10,
            "url": "https://example.com",
            "mobile_url": "",
            "time_display": "120000",
            "count": 2,
            "is_new": True,
        }

        result = reporter.format_title_for_platform("feishu", title_data, show_source=True)

        assert "测试新闻" in result
        assert "知乎" in result
        assert "🆕" in result
        assert "https://example.com" in result
        assert "120000" in result
        assert "2次" in result

    def test_format_title_for_telegram(self, reporter):
        """测试Telegram格式化"""
        title_data = {
            "title": "测试新闻<script>",  # 带特殊字符
            "source_name": "微博",
            "ranks": [1, 2],
            "rank_threshold": 10,
            "url": "https://example.com",
            "mobile_url": "",
            "time_display": "",
            "count": 1,
            "is_new": False,
        }

        result = reporter.format_title_for_platform("telegram", title_data, show_source=True)

        # 应该转义HTML
        assert "&lt;script&gt;" in result
        assert "<a href=" in result
        assert "微博" in result

    def test_format_title_for_html(self, reporter):
        """测试HTML格式化"""
        title_data = {
            "title": "测试新闻",
            "source_name": "知乎",
            "ranks": [5],
            "rank_threshold": 10,
            "url": "https://example.com",
            "mobile_url": "https://m.example.com",
            "time_display": "120000",
            "count": 3,
            "is_new": True,
        }

        result = reporter.format_title_for_platform("html", title_data)

        assert "测试新闻" in result
        assert "知乎" in result
        assert "new-title" in result  # 新增样式
        assert "news-link" in result
        assert "3次" in result

    def test_format_title_without_source(self, reporter):
        """测试不显示来源的格式化"""
        title_data = {
            "title": "测试新闻",
            "source_name": "知乎",
            "ranks": [5],
            "rank_threshold": 10,
            "url": "https://example.com",
            "mobile_url": "",
            "time_display": "",
            "count": 1,
            "is_new": False,
        }

        result = reporter.format_title_for_platform("feishu", title_data, show_source=False)

        # 不应该包含来源
        assert "知乎" not in result
        assert "测试新闻" in result

    def test_get_output_path(self, reporter, tmp_path, monkeypatch):
        """测试获取输出路径"""
        # 修改工作目录
        monkeypatch.chdir(tmp_path)

        path = reporter.get_output_path("html", "test.html")

        # 检查路径结构
        assert path.parent.name == "html"
        assert path.name == "test.html"
        assert path.parent.exists()  # 目录应该被创建

    def test_generate_text_report(self, reporter, sample_stats, tmp_path, monkeypatch):
        """测试生成文本报告"""
        monkeypatch.chdir(tmp_path)

        file_path = reporter.generate_text_report(
            stats=sample_stats,
            total_titles=2,
            failed_ids=["failed1", "failed2"],
            new_news_list=None,
            mode="daily",
            is_daily_summary=True
        )

        # 检查文件是否生成
        assert file_path.exists()
        assert file_path.name == "当日汇总.txt"

        # 检查文件内容
        content = file_path.read_text(encoding="utf-8")
        assert "测试 新闻" in content
        assert "知乎" in content
        assert "测试新闻A" in content
        assert "failed1" in content
        assert "failed2" in content

    def test_generate_text_report_with_new_news(self, reporter, sample_stats, tmp_path, monkeypatch):
        """测试生成文本报告（带新增新闻）"""
        monkeypatch.chdir(tmp_path)

        new_news = News(
            title="新增新闻C",
            url="https://example.com/c",
            platform="douyin",
            platform_name="抖音",
            rank=3,
            mobile_url="https://m.example.com/c"
        )

        file_path = reporter.generate_text_report(
            stats=sample_stats,
            total_titles=3,
            new_news_list=[new_news],
            mode="daily",
            is_daily_summary=False
        )

        # 检查文件内容
        content = file_path.read_text(encoding="utf-8")
        assert "最新批次新增" in content
        assert "抖音" in content
        assert "新增新闻C" in content

    def test_generate_text_report_current_mode(self, reporter, sample_stats, tmp_path, monkeypatch):
        """测试生成当前榜单文本报告"""
        monkeypatch.chdir(tmp_path)

        file_path = reporter.generate_text_report(
            stats=sample_stats,
            total_titles=2,
            mode="current",
            is_daily_summary=True
        )

        assert file_path.name == "当前榜单汇总.txt"

    def test_generate_text_report_incremental_mode(self, reporter, sample_stats, tmp_path, monkeypatch):
        """测试生成增量模式文本报告"""
        monkeypatch.chdir(tmp_path)

        file_path = reporter.generate_text_report(
            stats=sample_stats,
            total_titles=2,
            mode="incremental",
            is_daily_summary=True
        )

        assert file_path.name == "当日增量.txt"

    def test_format_platforms(self, reporter):
        """测试所有平台格式化"""
        title_data = {
            "title": "测试新闻",
            "source_name": "知乎",
            "ranks": [5],
            "rank_threshold": 10,
            "url": "https://example.com",
            "mobile_url": "",
            "time_display": "120000",
            "count": 1,
            "is_new": False,
        }

        platforms = ["feishu", "dingtalk", "wework", "telegram", "ntfy", "html"]

        for platform in platforms:
            result = reporter.format_title_for_platform(platform, title_data)
            assert result  # 不应该为空
            assert "测试新闻" in result or "&#x6D4B;" in result  # 可能被转义
