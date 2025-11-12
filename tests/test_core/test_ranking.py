# coding=utf-8
"""测试新闻权重计算和排序模块"""

import pytest
from pathlib import Path
from datetime import datetime
from src.core.ranking import NewsRanking
from src.core.filter import NewsFilter


@pytest.fixture
def temp_output_dir(tmp_path):
    """创建临时输出目录"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_txt_file(temp_output_dir):
    """创建示例txt文件"""
    from src.utils.time import format_date_folder

    date_folder = format_date_folder()
    date_dir = temp_output_dir / date_folder
    txt_dir = date_dir / "txt"
    txt_dir.mkdir(parents=True)

    # 创建第一个文件
    file1 = txt_dir / "120000.txt"
    content1 = """zhihu | 知乎
1. 测试新闻A [URL:https://example.com/a] [MOBILE:https://m.example.com/a]
2. 测试新闻B [URL:https://example.com/b]

weibo | 微博
1. 测试新闻C [URL:https://example.com/c]
2. 测试新闻A [URL:https://example.com/a]
"""
    file1.write_text(content1, encoding="utf-8")

    # 创建第二个文件
    file2 = txt_dir / "130000.txt"
    content2 = """zhihu | 知乎
1. 测试新闻A [URL:https://example.com/a]
3. 测试新闻D [URL:https://example.com/d]

weibo | 微博
2. 测试新闻C [URL:https://example.com/c]
"""
    file2.write_text(content2, encoding="utf-8")

    return txt_dir


@pytest.fixture
def frequency_words_file(tmp_path):
    """创建频率词文件"""
    words_file = tmp_path / "frequency_words.txt"
    content = """测试
新闻

+Python
编程
"""
    words_file.write_text(content, encoding="utf-8")
    return str(words_file)


@pytest.fixture
def news_filter(frequency_words_file):
    """创建新闻筛选器"""
    return NewsFilter(frequency_words_file)


@pytest.fixture
def news_ranking(news_filter):
    """创建新闻排序器"""
    return NewsRanking(
        news_filter=news_filter,
        rank_threshold=10,
        rank_weight=0.6,
        frequency_weight=0.3,
        hotness_weight=0.1
    )


class TestNewsRanking:
    """测试 NewsRanking 类"""

    def test_parse_file_titles(self, news_ranking, sample_txt_file):
        """测试解析txt文件"""
        file_path = list(sample_txt_file.glob("*.txt"))[0]
        titles_by_id, id_to_name = news_ranking.parse_file_titles(file_path)

        assert "zhihu" in titles_by_id
        assert "weibo" in titles_by_id
        assert id_to_name["zhihu"] == "知乎"
        assert id_to_name["weibo"] == "微博"

        # 检查知乎的标题
        assert "测试新闻A" in titles_by_id["zhihu"]
        assert "测试新闻B" in titles_by_id["zhihu"]

        # 检查排名
        assert titles_by_id["zhihu"]["测试新闻A"]["ranks"] == [1]
        assert titles_by_id["zhihu"]["测试新闻B"]["ranks"] == [2]

        # 检查URL
        assert titles_by_id["zhihu"]["测试新闻A"]["url"] == "https://example.com/a"
        assert titles_by_id["zhihu"]["测试新闻A"]["mobileUrl"] == "https://m.example.com/a"

    def test_read_all_today_titles(self, news_ranking, sample_txt_file, monkeypatch):
        """测试读取当天所有标题"""
        # 修改工作目录
        monkeypatch.chdir(sample_txt_file.parent.parent.parent)

        all_results, id_to_name, title_info = news_ranking.read_all_today_titles()

        assert "zhihu" in all_results
        assert "weibo" in all_results

        # 测试新闻A 在两个平台都出现
        assert "测试新闻A" in all_results["zhihu"]
        assert "测试新闻A" in all_results["weibo"]

        # 测试新闻A 在知乎出现2次（两个文件）
        assert title_info["zhihu"]["测试新闻A"]["count"] == 2
        assert title_info["zhihu"]["测试新闻A"]["first_time"] == "120000"
        assert title_info["zhihu"]["测试新闻A"]["last_time"] == "130000"

        # 测试新闻A 的排名应该合并 [1, 1]
        assert title_info["zhihu"]["测试新闻A"]["ranks"] == [1, 1]

        # 测试新闻D 只在第二个文件出现
        assert title_info["zhihu"]["测试新闻D"]["count"] == 1

    def test_read_all_today_titles_with_filter(self, news_ranking, sample_txt_file, monkeypatch):
        """测试带平台过滤的读取"""
        monkeypatch.chdir(sample_txt_file.parent.parent.parent)

        # 只读取知乎
        all_results, id_to_name, title_info = news_ranking.read_all_today_titles(
            current_platform_ids=["zhihu"]
        )

        assert "zhihu" in all_results
        assert "weibo" not in all_results

    def test_detect_latest_new_titles(self, news_ranking, sample_txt_file, monkeypatch):
        """测试检测新增标题"""
        monkeypatch.chdir(sample_txt_file.parent.parent.parent)

        new_titles = news_ranking.detect_latest_new_titles()

        # 新增的标题应该只有"测试新闻D"（只在第二个文件出现）
        assert "zhihu" in new_titles
        assert "测试新闻D" in new_titles["zhihu"]

        # 测试新闻A 不是新增（两个文件都有）
        if "测试新闻A" in new_titles.get("zhihu", {}):
            pytest.fail("测试新闻A 不应该是新增")

    def test_is_first_crawl_today(self, news_ranking, sample_txt_file, monkeypatch):
        """测试判断是否第一次爬取"""
        monkeypatch.chdir(sample_txt_file.parent.parent.parent)

        # 有2个文件，不是第一次
        assert news_ranking.is_first_crawl_today() is False

        # 删除一个文件
        files = list(sample_txt_file.glob("*.txt"))
        files[0].unlink()

        # 只有1个文件，是第一次
        assert news_ranking.is_first_crawl_today() is True

    def test_calculate_statistics_daily_mode(self, news_ranking, sample_txt_file, monkeypatch):
        """测试当日汇总模式统计"""
        monkeypatch.chdir(sample_txt_file.parent.parent.parent)

        all_results, id_to_name, title_info = news_ranking.read_all_today_titles()

        stats, total_titles = news_ranking.calculate_statistics(
            results=all_results,
            id_to_name=id_to_name,
            title_info=title_info,
            mode="daily"
        )

        # 应该有统计结果
        assert len(stats) > 0
        assert total_titles > 0

        # 检查统计对象
        for stat in stats:
            assert stat.word is not None
            assert stat.count >= 0
            assert isinstance(stat.news_list, list)

    def test_calculate_statistics_incremental_mode(self, news_ranking, sample_txt_file, monkeypatch):
        """测试增量模式统计"""
        monkeypatch.chdir(sample_txt_file.parent.parent.parent)

        all_results, id_to_name, title_info = news_ranking.read_all_today_titles()
        new_titles = news_ranking.detect_latest_new_titles()

        # 删除一个文件让 is_first_today 返回 False
        files = list(sample_txt_file.glob("*.txt"))
        if len(files) > 1:
            # 模拟非第一次爬取
            stats, total_titles = news_ranking.calculate_statistics(
                results=all_results,
                id_to_name=id_to_name,
                title_info=title_info,
                new_titles=new_titles,
                mode="incremental"
            )

            # 增量模式下应该只统计新增的
            assert total_titles >= 0

    def test_calculate_weight(self, news_ranking):
        """测试权重计算"""
        # 测试高排名、高频次
        title_data1 = {
            "ranks": [1, 2, 1],
            "count": 3,
        }
        weight1 = news_ranking._calculate_weight(title_data1)
        assert weight1 > 0

        # 测试低排名、低频次
        title_data2 = {
            "ranks": [50, 60],
            "count": 2,
        }
        weight2 = news_ranking._calculate_weight(title_data2)

        # 高排名应该权重更高
        assert weight1 > weight2

        # 测试空排名
        title_data3 = {
            "ranks": [],
            "count": 0,
        }
        weight3 = news_ranking._calculate_weight(title_data3)
        assert weight3 == 0.0

    def test_process_source_data(self, news_ranking):
        """测试处理来源数据"""
        all_results = {}
        title_info = {}

        title_data = {
            "测试新闻": {
                "ranks": [1],
                "url": "https://example.com",
                "mobileUrl": ""
            }
        }

        # 第一次处理
        news_ranking._process_source_data(
            "zhihu", title_data, "120000", all_results, title_info
        )

        assert "zhihu" in all_results
        assert "测试新闻" in all_results["zhihu"]
        assert title_info["zhihu"]["测试新闻"]["count"] == 1
        assert title_info["zhihu"]["测试新闻"]["first_time"] == "120000"

        # 第二次处理同一标题
        title_data2 = {
            "测试新闻": {
                "ranks": [2],
                "url": "https://example.com",
                "mobileUrl": ""
            }
        }

        news_ranking._process_source_data(
            "zhihu", title_data2, "130000", all_results, title_info
        )

        assert title_info["zhihu"]["测试新闻"]["count"] == 2
        assert title_info["zhihu"]["测试新闻"]["last_time"] == "130000"
        assert title_info["zhihu"]["测试新闻"]["ranks"] == [1, 2]

    def test_filter_current_batch(self, news_ranking):
        """测试筛选当前批次"""
        results = {
            "zhihu": {
                "新闻A": {"ranks": [1]},
                "新闻B": {"ranks": [2]},
            }
        }

        title_info = {
            "zhihu": {
                "新闻A": {"last_time": "130000"},
                "新闻B": {"last_time": "120000"},
            }
        }

        current_batch = news_ranking._filter_current_batch(results, title_info)

        # 只有新闻A 是最新批次
        assert "zhihu" in current_batch
        assert "新闻A" in current_batch["zhihu"]
        assert "新闻B" not in current_batch["zhihu"]
