# coding=utf-8
"""TrendRadar 主应用"""

from typing import List, Dict

from src.core.config import ConfigManager
from src.core.filter import NewsFilter
from src.core.ranking import NewsRanking
from src.core.reporter import NewsReporter
from src.sources.registry import get_registry
from src.notifiers.manager import NotificationManager
from src.models.news import News


class TrendRadarApp:
    """TrendRadar 主应用类

    整合所有功能模块，提供完整的工作流程
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化应用

        Args:
            config_path: 配置文件路径
        """
        print("=" * 60)
        print("TrendRadar - 热点新闻聚合与分析")
        print("=" * 60)

        # 加载配置
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager._config

        print(f"✓ 配置加载完成")

        # 初始化各模块
        self._initialize_modules()

        print("✓ 模块初始化完成\n")

    def _initialize_modules(self) -> None:
        """初始化各功能模块"""
        # 信息源注册器
        self.source_registry = get_registry()

        # 关键词筛选器
        frequency_file = self.config.get("FREQUENCY_WORDS_PATH", "config/frequency_words.txt")
        self.news_filter = NewsFilter(frequency_file)

        # 排序器
        rank_threshold = self.config.get("RANK_THRESHOLD", 10)
        weight_config = self.config.get("WEIGHT_CONFIG", {})
        self.news_ranking = NewsRanking(
            news_filter=self.news_filter,
            rank_threshold=rank_threshold,
            rank_weight=weight_config.get("RANK_WEIGHT", 0.6),
            frequency_weight=weight_config.get("FREQUENCY_WEIGHT", 0.3),
            hotness_weight=weight_config.get("HOTNESS_WEIGHT", 0.1)
        )

        # 报告生成器
        self.news_reporter = NewsReporter(rank_threshold=rank_threshold)

        # 通知管理器
        self.notification_manager = NotificationManager(self.config)

    def run(self, mode: str = "daily") -> bool:
        """运行完整流程

        Args:
            mode: 运行模式 (daily/current/incremental)

        Returns:
            bool: 是否运行成功
        """
        print(f"开始运行 - 模式: {mode}")
        print("-" * 60)

        try:
            # 1. 获取信息源
            sources = self._get_sources()
            if not sources:
                print("错误: 没有启用的信息源")
                return False

            # 2. 爬取新闻
            print("\n[1/6] 爬取新闻数据...")
            all_news, failed_ids = self._fetch_all_news(sources)
            if not all_news:
                print("警告: 未获取到任何新闻数据")
                return False

            print(f"✓ 成功爬取 {len(all_news)} 条新闻")

            # 3. 读取历史数据（用于统计）
            print("\n[2/6] 读取历史数据...")
            platform_ids = [source.source_id for source in sources]
            all_results, id_to_name, title_info = self.news_ranking.read_all_today_titles(
                current_platform_ids=platform_ids
            )

            # 如果历史数据为空（首次运行），使用刚爬取的数据
            if not all_results:
                print("⚠️  历史数据为空，使用当前爬取的数据")
                all_results, id_to_name, title_info = self._convert_news_to_results(
                    all_news, sources
                )

            print(f"✓ 读取历史数据完成（共 {sum(len(titles) for titles in all_results.values())} 条）")

            # 4. 检测新增新闻
            print("\n[3/6] 检测新增新闻...")
            new_titles = self.news_ranking.detect_latest_new_titles(
                current_platform_ids=platform_ids
            )
            new_count = sum(len(titles) for titles in new_titles.values())
            print(f"✓ 检测到 {new_count} 条新增新闻")

            # 5. 计算统计和排序
            print("\n[4/6] 计算权重并排序...")
            stats, total_titles = self.news_ranking.calculate_statistics(
                results=all_results,
                id_to_name=id_to_name,
                title_info=title_info,
                new_titles=new_titles,
                mode=mode
            )
            print(f"✓ 统计完成，匹配 {sum(s.count for s in stats)} 条新闻")

            # 6. 生成报告
            print("\n[5/6] 生成报告...")
            report_type = self._get_report_type(mode)
            is_daily_summary = True  # 总是生成当日汇总

            # 生成文本报告
            txt_path = self.news_reporter.generate_text_report(
                stats=stats,
                total_titles=total_titles,
                failed_ids=failed_ids,
                new_news_list=self._convert_new_titles_to_news(new_titles, id_to_name),
                mode=mode,
                is_daily_summary=is_daily_summary
            )
            print(f"✓ 文本报告: {txt_path}")

            # 生成 JSON 报告(汇总+增量)
            summary_path, incremental_path = self.news_reporter.generate_json_report(
                stats=stats,
                total_titles=total_titles,
                failed_ids=failed_ids,
                new_news_list=self._convert_new_titles_to_news(new_titles, id_to_name),
                mode=mode,
                is_daily_summary=is_daily_summary
            )
            print(f"✓ JSON 汇总: {summary_path}")
            print(f"✓ JSON 增量: {incremental_path}")

            # TODO: 生成HTML报告(可选)
            html_path = None

            # 7. 发送通知
            print("\n[6/6] 发送通知...")
            report_data = self.news_reporter.prepare_report_data(
                stats=stats,
                failed_ids=failed_ids,
                new_news_list=self._convert_new_titles_to_news(new_titles, id_to_name),
                mode=mode
            )

            self.notification_manager.send_notifications(
                report_data=report_data,
                report_type=report_type,
                update_info=None,  # TODO: 实现版本检查
                proxy_url=self.config.get("DEFAULT_PROXY") if self.config.get("USE_PROXY") else None,
                mode=mode,
                html_file_path=str(html_path) if html_path else None
            )

            print("\n" + "=" * 60)
            print("运行完成!")
            print("=" * 60)

            return True

        except Exception as e:
            print(f"\n错误: 运行过程中出现异常: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _get_sources(self) -> List:
        """获取启用的信息源

        Returns:
            List: 信息源列表
        """
        enabled_sources = self.source_registry.get_enabled_sources(self.config)

        print(f"已启用 {len(enabled_sources)} 个信息源:")
        for source in enabled_sources:
            print(f"  - {source.source_name} ({source.source_id})")

        return enabled_sources

    def _fetch_all_news(self, sources: List) -> tuple:
        """从所有信息源获取新闻

        Args:
            sources: 信息源列表

        Returns:
            tuple: (所有新闻列表, 失败的ID列表)
        """
        all_news = []
        failed_ids = []

        request_interval = self.config.get("REQUEST_INTERVAL", 1000)

        for source in sources:
            try:
                print(f"  正在爬取: {source.source_name}...")
                news_list = source.fetch_news(request_interval=request_interval)
                all_news.extend(news_list)
                print(f"  ✓ {source.source_name}: {len(news_list)} 条")
            except Exception as e:
                print(f"  ✗ {source.source_name}: 失败 - {e}")
                failed_ids.append(source.source_id)

        return all_news, failed_ids

    def _convert_news_to_results(
        self,
        all_news: List[News],
        sources: List
    ) -> tuple:
        """将News对象列表转换为results格式

        Args:
            all_news: 新闻列表
            sources: 信息源列表

        Returns:
            tuple: (results字典, id_to_name映射, title_info信息)
        """
        from src.utils.time import format_time_filename
        from src.utils.file import clean_title

        results = {}
        id_to_name = {}
        title_info = {}

        # 构建id_to_name映射
        for source in sources:
            id_to_name[source.source_id] = source.source_name

        # 转换新闻数据
        time_info = format_time_filename()
        for news in all_news:
            platform_id = news.platform

            if platform_id not in results:
                results[platform_id] = {}
                title_info[platform_id] = {}

            title = clean_title(news.title)

            if title in results[platform_id]:
                # 标题已存在,添加排名
                results[platform_id][title]["ranks"].append(news.rank)
            else:
                # 新标题
                results[platform_id][title] = {
                    "ranks": [news.rank],
                    "url": news.url,
                    "mobileUrl": news.mobile_url or ""
                }

                # 添加title_info
                title_info[platform_id][title] = {
                    "first_time": time_info,
                    "last_time": time_info,
                    "count": 1,
                    "ranks": [news.rank],
                    "url": news.url,
                    "mobileUrl": news.mobile_url or ""
                }

        return results, id_to_name, title_info

    def _convert_new_titles_to_news(
        self,
        new_titles: Dict,
        id_to_name: Dict
    ) -> List[News]:
        """将新增标题字典转换为News对象列表

        Args:
            new_titles: 新增标题字典
            id_to_name: ID到名称的映射

        Returns:
            List[News]: 新闻列表
        """
        news_list = []

        for source_id, titles_data in new_titles.items():
            source_name = id_to_name.get(source_id, source_id)

            for title, title_data in titles_data.items():
                ranks = title_data.get("ranks", [])
                url = title_data.get("url", "")
                mobile_url = title_data.get("mobileUrl", "")

                news = News(
                    title=title,
                    url=url,
                    platform=source_id,
                    platform_name=source_name,
                    rank=min(ranks) if ranks else 99,
                    mobile_url=mobile_url
                )
                news_list.append(news)

        return news_list

    def _get_report_type(self, mode: str) -> str:
        """获取报告类型名称

        Args:
            mode: 模式

        Returns:
            str: 报告类型
        """
        mode_map = {
            "daily": "当日汇总",
            "current": "当前榜单",
            "incremental": "增量监控"
        }
        return mode_map.get(mode, "当日汇总")

    def list_sources(self) -> None:
        """列出所有可用的信息源"""
        print("\n可用的信息源:")
        print("-" * 60)

        all_sources = self.source_registry.get_all_sources(self.config)
        enabled_ids = [s.source_id for s in self.source_registry.get_enabled_sources(self.config)]

        for source in all_sources:
            status = "✓ 已启用" if source.source_id in enabled_ids else "  未启用"
            print(f"{status} | {source.source_name:20} | {source.source_id}")

        print("-" * 60)

    def list_notifiers(self) -> None:
        """列出所有通知渠道"""
        print("\n通知渠道配置:")
        print("-" * 60)

        notifiers = self.notification_manager.list_notifiers()

        for notifier in notifiers:
            status = "✓ 已配置" if notifier["configured"] == "是" else "  未配置"
            print(f"{status} | {notifier['name']:15} | {notifier['key']}")

        print("-" * 60)

    def show_config_summary(self) -> None:
        """显示配置摘要"""
        print("\n配置摘要:")
        print("-" * 60)

        # 推送窗口
        push_window = self.config.get("PUSH_WINDOW", {})
        if push_window.get("ENABLED", False):
            time_range = push_window.get("TIME_RANGE", {})
            once_per_day = "是" if push_window.get("ONCE_PER_DAY", False) else "否"
            print(f"推送窗口: 启用")
            print(f"  时间范围: {time_range.get('START', '00:00')} - {time_range.get('END', '23:59')}")
            print(f"  每天一次: {once_per_day}")
        else:
            print(f"推送窗口: 未启用")

        # 权重配置
        weight = self.config.get("WEIGHT_CONFIG", {})
        print(f"\n权重配置:")
        print(f"  排名权重: {weight.get('RANK_WEIGHT', 0.6) * 100:.0f}%")
        print(f"  频次权重: {weight.get('FREQUENCY_WEIGHT', 0.3) * 100:.0f}%")
        print(f"  热度权重: {weight.get('HOTNESS_WEIGHT', 0.1) * 100:.0f}%")

        # 其他
        print(f"\n其他配置:")
        print(f"  排名阈值: {self.config.get('RANK_THRESHOLD', 10)}")
        print(f"  请求间隔: {self.config.get('REQUEST_INTERVAL', 1000)}ms")
        print(f"  使用代理: {'是' if self.config.get('USE_PROXY', False) else '否'}")

        print("-" * 60)
