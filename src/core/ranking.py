# coding=utf-8
"""新闻权重计算和排序模块"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from src.models.news import News, WordGroupStatistic
from src.core.filter import NewsFilter
from src.utils.time import format_date_folder
from src.utils.file import clean_title


class NewsRanking:
    """新闻权重计算和排序器

    负责：
    - 读取历史新闻数据
    - 筛选匹配的新闻
    - 计算权重并排序
    - 统计词组频次
    - 识别新增新闻
    """

    def __init__(
        self,
        news_filter: NewsFilter,
        rank_threshold: int = 10,
        rank_weight: float = 0.6,
        frequency_weight: float = 0.3,
        hotness_weight: float = 0.1
    ):
        """初始化排序器

        Args:
            news_filter: 新闻筛选器
            rank_threshold: 排名阈值（用于高排名判定）
            rank_weight: 排名权重系数
            frequency_weight: 频次权重系数
            hotness_weight: 热度权重系数
        """
        self.news_filter = news_filter
        self.rank_threshold = rank_threshold
        self.rank_weight = rank_weight
        self.frequency_weight = frequency_weight
        self.hotness_weight = hotness_weight

    def parse_file_titles(self, file_path: Path) -> Tuple[Dict, Dict]:
        """解析单个txt文件的标题数据

        Args:
            file_path: 文件路径

        Returns:
            Tuple[Dict, Dict]: (titles_by_id, id_to_name)
                - titles_by_id: {platform_id: {title: {ranks, url, mobileUrl}}}
                - id_to_name: {platform_id: platform_name}
        """
        titles_by_id = {}
        id_to_name = {}

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            sections = content.split("\n\n")

        for section in sections:
            if not section.strip() or "==== 以下ID请求失败 ====" in section:
                continue

            lines = section.strip().split("\n")
            if len(lines) < 2:
                continue

            # 解析header: "id | name" 或 "id"
            header_line = lines[0].strip()
            if " | " in header_line:
                parts = header_line.split(" | ", 1)
                source_id = parts[0].strip()
                name = parts[1].strip()
                id_to_name[source_id] = name
            else:
                source_id = header_line
                id_to_name[source_id] = source_id

            titles_by_id[source_id] = {}

            # 解析标题行
            for line in lines[1:]:
                if line.strip():
                    try:
                        title_part = line.strip()
                        rank = None

                        # 提取排名 "1. title"
                        if ". " in title_part and title_part.split(". ")[0].isdigit():
                            rank_str, title_part = title_part.split(". ", 1)
                            rank = int(rank_str)

                        # 提取 MOBILE URL
                        mobile_url = ""
                        if " [MOBILE:" in title_part:
                            title_part, mobile_part = title_part.rsplit(" [MOBILE:", 1)
                            if mobile_part.endswith("]"):
                                mobile_url = mobile_part[:-1]

                        # 提取 URL
                        url = ""
                        if " [URL:" in title_part:
                            title_part, url_part = title_part.rsplit(" [URL:", 1)
                            if url_part.endswith("]"):
                                url = url_part[:-1]

                        title = clean_title(title_part.strip())
                        ranks = [rank] if rank is not None else [1]

                        titles_by_id[source_id][title] = {
                            "ranks": ranks,
                            "url": url,
                            "mobileUrl": mobile_url,
                        }

                    except Exception as e:
                        print(f"解析标题行出错: {line}, 错误: {e}")

        return titles_by_id, id_to_name

    def read_all_today_titles(
        self,
        current_platform_ids: Optional[List[str]] = None
    ) -> Tuple[Dict, Dict, Dict]:
        """读取当天所有标题文件

        Args:
            current_platform_ids: 当前监控的平台ID列表（用于过滤）

        Returns:
            Tuple[Dict, Dict, Dict]: (all_results, id_to_name, title_info)
                - all_results: {platform_id: {title: {ranks, url, mobileUrl}}}
                - id_to_name: {platform_id: platform_name}
                - title_info: {platform_id: {title: {first_time, last_time, count, ranks, url, mobileUrl}}}
        """
        date_folder = format_date_folder()
        txt_dir = Path("output") / date_folder / "txt"

        if not txt_dir.exists():
            return {}, {}, {}

        all_results = {}
        final_id_to_name = {}
        title_info = {}

        files = sorted([f for f in txt_dir.iterdir() if f.suffix == ".txt"])

        for file_path in files:
            time_info = file_path.stem  # 文件名作为时间标识

            titles_by_id, file_id_to_name = self.parse_file_titles(file_path)

            # 如果指定了平台过滤
            if current_platform_ids is not None:
                filtered_titles_by_id = {}
                filtered_id_to_name = {}

                for source_id, title_data in titles_by_id.items():
                    if source_id in current_platform_ids:
                        filtered_titles_by_id[source_id] = title_data
                        if source_id in file_id_to_name:
                            filtered_id_to_name[source_id] = file_id_to_name[source_id]

                titles_by_id = filtered_titles_by_id
                file_id_to_name = filtered_id_to_name

            final_id_to_name.update(file_id_to_name)

            # 处理每个平台的数据
            for source_id, title_data in titles_by_id.items():
                self._process_source_data(
                    source_id, title_data, time_info, all_results, title_info
                )

        return all_results, final_id_to_name, title_info

    def _process_source_data(
        self,
        source_id: str,
        title_data: Dict,
        time_info: str,
        all_results: Dict,
        title_info: Dict
    ) -> None:
        """处理来源数据，合并重复标题

        Args:
            source_id: 平台ID
            title_data: {title: {ranks, url, mobileUrl}}
            time_info: 时间标识
            all_results: 汇总结果（会被修改）
            title_info: 标题信息（会被修改）
        """
        if source_id not in all_results:
            all_results[source_id] = title_data

            if source_id not in title_info:
                title_info[source_id] = {}

            for title, data in title_data.items():
                ranks = data.get("ranks", [])
                url = data.get("url", "")
                mobile_url = data.get("mobileUrl", "")

                title_info[source_id][title] = {
                    "first_time": time_info,
                    "last_time": time_info,
                    "count": 1,
                    "ranks": ranks,
                    "url": url,
                    "mobileUrl": mobile_url,
                }
        else:
            for title, data in title_data.items():
                ranks = data.get("ranks", [])
                url = data.get("url", "")
                mobile_url = data.get("mobileUrl", "")

                if title not in all_results[source_id]:
                    # 新标题
                    all_results[source_id][title] = data
                    title_info[source_id][title] = {
                        "first_time": time_info,
                        "last_time": time_info,
                        "count": 1,
                        "ranks": ranks,
                        "url": url,
                        "mobileUrl": mobile_url,
                    }
                else:
                    # 已存在的标题，合并排名
                    existing_ranks = all_results[source_id][title].get("ranks", [])
                    merged_ranks = existing_ranks + ranks
                    all_results[source_id][title]["ranks"] = merged_ranks

                    # 更新统计信息
                    title_info[source_id][title]["last_time"] = time_info
                    title_info[source_id][title]["ranks"] = merged_ranks
                    title_info[source_id][title]["count"] += 1
                    if not title_info[source_id][title].get("url"):
                        title_info[source_id][title]["url"] = url
                    if not title_info[source_id][title].get("mobileUrl"):
                        title_info[source_id][title]["mobileUrl"] = mobile_url

    def detect_latest_new_titles(
        self,
        current_platform_ids: Optional[List[str]] = None
    ) -> Dict:
        """检测当日最新批次的新增标题

        Args:
            current_platform_ids: 当前监控的平台ID列表（用于过滤）

        Returns:
            Dict: {platform_id: {title: {ranks, url, mobileUrl}}}
        """
        date_folder = format_date_folder()
        txt_dir = Path("output") / date_folder / "txt"

        if not txt_dir.exists():
            return {}

        files = sorted([f for f in txt_dir.iterdir() if f.suffix == ".txt"])
        if len(files) < 2:
            return {}

        # 解析最新文件
        latest_file = files[-1]
        latest_titles, _ = self.parse_file_titles(latest_file)

        # 如果指定了当前平台列表，过滤最新文件数据
        if current_platform_ids is not None:
            filtered_latest_titles = {}
            for source_id, title_data in latest_titles.items():
                if source_id in current_platform_ids:
                    filtered_latest_titles[source_id] = title_data
            latest_titles = filtered_latest_titles

        # 汇总历史标题（按平台过滤）
        historical_titles = {}
        for file_path in files[:-1]:
            historical_data, _ = self.parse_file_titles(file_path)

            # 过滤历史数据
            if current_platform_ids is not None:
                filtered_historical_data = {}
                for source_id, title_data in historical_data.items():
                    if source_id in current_platform_ids:
                        filtered_historical_data[source_id] = title_data
                historical_data = filtered_historical_data

            for source_id, titles_data in historical_data.items():
                if source_id not in historical_titles:
                    historical_titles[source_id] = set()
                for title in titles_data.keys():
                    historical_titles[source_id].add(title)

        # 找出新增标题
        new_titles = {}
        for source_id, latest_source_titles in latest_titles.items():
            historical_set = historical_titles.get(source_id, set())
            source_new_titles = {}

            for title, title_data in latest_source_titles.items():
                if title not in historical_set:
                    source_new_titles[title] = title_data

            if source_new_titles:
                new_titles[source_id] = source_new_titles

        return new_titles

    def is_first_crawl_today(self) -> bool:
        """判断是否是当天第一次爬取

        Returns:
            bool: 是否是第一次
        """
        date_folder = format_date_folder()
        txt_dir = Path("output") / date_folder / "txt"

        if not txt_dir.exists():
            return True

        files = list(txt_dir.glob("*.txt"))
        return len(files) <= 1

    def calculate_statistics(
        self,
        results: Dict,
        id_to_name: Dict,
        title_info: Optional[Dict] = None,
        new_titles: Optional[Dict] = None,
        mode: str = "daily"
    ) -> Tuple[List[WordGroupStatistic], int]:
        """统计词频并计算权重

        Args:
            results: 爬取结果 {platform_id: {title: {ranks, url, mobileUrl}}}
            id_to_name: ID到名称的映射
            title_info: 标题统计信息
            new_titles: 新增标题
            mode: 模式 (daily/current/incremental)

        Returns:
            Tuple[List[WordGroupStatistic], int]: (统计列表, 总标题数)
        """
        # 获取词组配置
        word_groups = self.news_filter.get_word_groups()
        filter_words = self.news_filter.get_filter_words()

        # 如果没有配置词组，创建一个包含所有新闻的虚拟词组
        if not word_groups:
            print("频率词配置为空，将显示所有新闻")
            word_groups = [{"required": [], "normal": [], "group_key": "全部新闻"}]
            filter_words = []

        is_first_today = self.is_first_crawl_today()

        # 确定处理的数据源和新增标记逻辑
        results_to_process, all_news_are_new = self._determine_processing_mode(
            results, title_info, new_titles, mode, is_first_today
        )

        # 初始化统计
        word_stats = {}
        for group in word_groups:
            group_key = group["group_key"]
            word_stats[group_key] = {"count": 0, "titles": {}}

        total_titles = 0
        processed_titles = {}
        matched_new_count = 0

        if title_info is None:
            title_info = {}
        if new_titles is None:
            new_titles = {}

        # 处理每个平台的每个标题
        for source_id, titles_data in results_to_process.items():
            total_titles += len(titles_data)

            if source_id not in processed_titles:
                processed_titles[source_id] = {}

            for title, title_data in titles_data.items():
                if title in processed_titles.get(source_id, {}):
                    continue

                # 使用筛选器检查是否匹配
                if not self.news_filter.matches(title):
                    continue

                # 如果是增量模式或 current 模式第一次，统计匹配的新增新闻数量
                if (mode == "incremental" and all_news_are_new) or (
                    mode == "current" and is_first_today
                ):
                    matched_new_count += 1

                # 处理标题数据
                self._process_title_for_stats(
                    title, title_data, source_id, word_groups, word_stats,
                    title_info, new_titles, id_to_name, mode, all_news_are_new,
                    processed_titles
                )

        # 打印汇总信息
        self._print_summary(
            mode, is_first_today, results, new_titles, matched_new_count,
            word_groups, results_to_process
        )

        # 生成统计结果
        stats = self._generate_statistics(word_stats, total_titles)

        return stats, total_titles

    def _determine_processing_mode(
        self,
        results: Dict,
        title_info: Optional[Dict],
        new_titles: Optional[Dict],
        mode: str,
        is_first_today: bool
    ) -> Tuple[Dict, bool]:
        """确定处理模式和数据源

        Returns:
            Tuple[Dict, bool]: (results_to_process, all_news_are_new)
        """
        if mode == "incremental":
            if is_first_today:
                # 增量模式 + 当天第一次：处理所有新闻，都标记为新增
                results_to_process = results
                all_news_are_new = True
            else:
                # 增量模式 + 当天非第一次：只处理新增的新闻
                results_to_process = new_titles if new_titles else {}
                all_news_are_new = True

        elif mode == "current":
            # current 模式：只处理当前时间批次的新闻
            if title_info:
                results_to_process = self._filter_current_batch(results, title_info)
            else:
                results_to_process = results
            all_news_are_new = False

        else:
            # 当日汇总模式：处理所有新闻
            results_to_process = results
            all_news_are_new = False
            total_input_news = sum(len(titles) for titles in results.values())
            filter_status = "全部显示" if len(self.news_filter.get_word_groups()) == 0 else "频率词过滤"
            print(f"当日汇总模式：处理 {total_input_news} 条新闻，模式：{filter_status}")

        return results_to_process, all_news_are_new

    def _filter_current_batch(self, results: Dict, title_info: Dict) -> Dict:
        """筛选当前批次的新闻

        Args:
            results: 所有结果
            title_info: 标题信息

        Returns:
            Dict: 当前批次的新闻
        """
        # 找到最新时间
        latest_time = None
        for source_titles in title_info.values():
            for title_data in source_titles.values():
                last_time = title_data.get("last_time", "")
                if last_time:
                    if latest_time is None or last_time > latest_time:
                        latest_time = last_time

        if not latest_time:
            return results

        # 只处理 last_time 等于最新时间的新闻
        results_to_process = {}
        for source_id, source_titles in results.items():
            if source_id in title_info:
                filtered_titles = {}
                for title, title_data in source_titles.items():
                    if title in title_info[source_id]:
                        info = title_info[source_id][title]
                        if info.get("last_time") == latest_time:
                            filtered_titles[title] = title_data
                if filtered_titles:
                    results_to_process[source_id] = filtered_titles

        print(
            f"当前榜单模式：最新时间 {latest_time}，筛选出 {sum(len(titles) for titles in results_to_process.values())} 条当前榜单新闻"
        )

        return results_to_process

    def _process_title_for_stats(
        self,
        title: str,
        title_data: Dict,
        source_id: str,
        word_groups: List[Dict],
        word_stats: Dict,
        title_info: Dict,
        new_titles: Dict,
        id_to_name: Dict,
        mode: str,
        all_news_are_new: bool,
        processed_titles: Dict
    ) -> None:
        """处理单个标题并更新统计

        Args:
            title: 标题
            title_data: 标题数据
            source_id: 平台ID
            word_groups: 词组配置
            word_stats: 词组统计（会被修改）
            title_info: 标题信息
            new_titles: 新增标题
            id_to_name: ID到名称映射
            mode: 模式
            all_news_are_new: 所有新闻是否都是新增
            processed_titles: 已处理标题（会被修改）
        """
        source_ranks = title_data.get("ranks", [])
        source_url = title_data.get("url", "")
        source_mobile_url = title_data.get("mobileUrl", "")

        # 找到匹配的词组
        title_lower = title.lower()
        for group in word_groups:
            required_words = group["required"]
            normal_words = group["normal"]
            group_key = group["group_key"]

            # 如果是"全部新闻"模式，所有标题都匹配
            if group_key == "全部新闻":
                matched = True
            else:
                # 检查必须词
                if required_words:
                    all_required_present = all(
                        req_word.lower() in title_lower for req_word in required_words
                    )
                    if not all_required_present:
                        continue

                # 检查普通词
                if normal_words:
                    any_normal_present = any(
                        normal_word.lower() in title_lower for normal_word in normal_words
                    )
                    if not any_normal_present:
                        continue

                matched = True

            if not matched:
                continue

            # 更新词组统计
            word_stats[group_key]["count"] += 1
            if source_id not in word_stats[group_key]["titles"]:
                word_stats[group_key]["titles"][source_id] = []

            # 获取完整的统计信息
            first_time = ""
            last_time = ""
            count_info = 1
            ranks = source_ranks if source_ranks else []
            url = source_url
            mobile_url = source_mobile_url

            # 对于 current 模式或 daily 模式，从历史统计信息中获取完整数据
            if title_info and source_id in title_info and title in title_info[source_id]:
                info = title_info[source_id][title]
                first_time = info.get("first_time", "")
                last_time = info.get("last_time", "")
                count_info = info.get("count", 1)
                if "ranks" in info and info["ranks"]:
                    ranks = info["ranks"]
                url = info.get("url", source_url)
                mobile_url = info.get("mobileUrl", source_mobile_url)

            if not ranks:
                ranks = [99]

            # 格式化时间显示
            if first_time and last_time and first_time != last_time:
                time_display = f"[{first_time} ~ {last_time}]"
            elif first_time:
                time_display = first_time
            else:
                time_display = ""

            source_name = id_to_name.get(source_id, source_id)

            # 判断是否为新增
            is_new = False
            if all_news_are_new:
                is_new = True
            elif new_titles and source_id in new_titles:
                new_titles_for_source = new_titles[source_id]
                is_new = title in new_titles_for_source

            # 添加到统计
            word_stats[group_key]["titles"][source_id].append({
                "title": title,
                "source_name": source_name,
                "first_time": first_time,
                "last_time": last_time,
                "time_display": time_display,
                "count": count_info,
                "ranks": ranks,
                "rank_threshold": self.rank_threshold,
                "url": url,
                "mobileUrl": mobile_url,
                "is_new": is_new,
            })

            # 标记已处理
            if source_id not in processed_titles:
                processed_titles[source_id] = {}
            processed_titles[source_id][title] = True

            break  # 只匹配第一个词组

    def _print_summary(
        self,
        mode: str,
        is_first_today: bool,
        results: Dict,
        new_titles: Optional[Dict],
        matched_new_count: int,
        word_groups: List[Dict],
        results_to_process: Dict
    ) -> None:
        """打印统计汇总信息

        Args:
            mode: 模式
            is_first_today: 是否第一次爬取
            results: 所有结果
            new_titles: 新增标题
            matched_new_count: 匹配的新增数量
            word_groups: 词组配置
            results_to_process: 处理的结果
        """
        is_show_all = len(word_groups) == 1 and word_groups[0]["group_key"] == "全部新闻"
        filter_status = "全部显示" if is_show_all else "频率词匹配"

        if mode == "incremental":
            if is_first_today:
                total_input_news = sum(len(titles) for titles in results.values())
                print(f"增量模式：当天第一次爬取，{total_input_news} 条新闻中有 {matched_new_count} 条{filter_status}")
            else:
                if new_titles:
                    total_new_count = sum(len(titles) for titles in new_titles.values())
                    print(f"增量模式：{total_new_count} 条新增新闻中，有 {matched_new_count} 条匹配频率词")
                    if matched_new_count == 0 and not is_show_all:
                        print("增量模式：没有新增新闻匹配频率词，将不会发送通知")
                else:
                    print("增量模式：未检测到新增新闻")

        elif mode == "current":
            total_input_news = sum(len(titles) for titles in results_to_process.values())
            if is_first_today:
                print(f"当前榜单模式：当天第一次爬取，{total_input_news} 条当前榜单新闻中有 {matched_new_count} 条{filter_status}")
            else:
                matched_count = sum(
                    len(word_stats["titles"].get(sid, []))
                    for word_stats in [{"titles": {}}]
                    for sid in results_to_process.keys()
                )
                print(f"当前榜单模式：{total_input_news} 条当前榜单新闻")

    def _generate_statistics(
        self,
        word_stats: Dict,
        total_titles: int
    ) -> List[WordGroupStatistic]:
        """生成统计结果

        Args:
            word_stats: 词组统计
            total_titles: 总标题数

        Returns:
            List[WordGroupStatistic]: 统计列表
        """
        stats = []

        for group_key, data in word_stats.items():
            all_titles = []
            for source_id, title_list in data["titles"].items():
                all_titles.extend(title_list)

            # 按权重排序
            sorted_titles = sorted(
                all_titles,
                key=lambda x: (
                    -self._calculate_weight(x),
                    min(x["ranks"]) if x["ranks"] else 999,
                    -x["count"],
                ),
            )

            # 转换为 News 对象
            news_list = []
            for item in sorted_titles:
                news = News(
                    title=item["title"],
                    url=item["url"],
                    platform="",  # 从 source_name 中无法反推 platform_id
                    platform_name=item["source_name"],
                    rank=min(item["ranks"]) if item["ranks"] else 99,
                    hotness=0,  # 暂时设为0
                    extra={
                        "first_time": item["first_time"],
                        "last_time": item["last_time"],
                        "time_display": item["time_display"],
                        "count": item["count"],
                        "all_ranks": item["ranks"],
                        "is_new": item["is_new"],
                        "mobileUrl": item["mobileUrl"],
                    }
                )
                news_list.append(news)

            percentage = round(data["count"] / total_titles * 100, 2) if total_titles > 0 else 0

            stat = WordGroupStatistic(
                word=group_key,
                count=data["count"],
                news_list=news_list,
                percentage=percentage
            )
            stats.append(stat)

        # 按数量排序
        stats.sort(key=lambda x: x.count, reverse=True)

        return stats

    def _calculate_weight(self, title_data: Dict) -> float:
        """计算新闻权重

        Args:
            title_data: 标题数据字典

        Returns:
            float: 权重值
        """
        ranks = title_data.get("ranks", [])
        if not ranks:
            return 0.0

        count = title_data.get("count", len(ranks))

        # 排名权重：Σ(11 - min(rank, 10)) / 出现次数
        rank_scores = []
        for rank in ranks:
            score = 11 - min(rank, 10)
            rank_scores.append(score)

        rank_weight_value = sum(rank_scores) / len(ranks) if ranks else 0

        # 频次权重：min(出现次数, 10) × 10
        frequency_weight_value = min(count, 10) * 10

        # 热度加成：高排名次数 / 总出现次数 × 100
        high_rank_count = sum(1 for rank in ranks if rank <= self.rank_threshold)
        hotness_ratio = high_rank_count / len(ranks) if ranks else 0
        hotness_weight_value = hotness_ratio * 100

        total_weight = (
            rank_weight_value * self.rank_weight
            + frequency_weight_value * self.frequency_weight
            + hotness_weight_value * self.hotness_weight
        )

        return total_weight
