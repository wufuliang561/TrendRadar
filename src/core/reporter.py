# coding=utf-8
"""新闻报告生成模块"""

import os
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime

from src.models.news import News, WordGroupStatistic
from src.utils.file import clean_title, html_escape
from src.utils.time import format_time_filename, format_date_folder


class NewsReporter:
    """新闻报告生成器

    负责：
    - 准备报告数据
    - 格式化标题
    - 生成各种格式的报告（HTML、文本等）
    """

    def __init__(self, rank_threshold: int = 10):
        """初始化报告生成器

        Args:
            rank_threshold: 排名阈值（用于高亮显示）
        """
        self.rank_threshold = rank_threshold

    def prepare_report_data(
        self,
        stats: List[WordGroupStatistic],
        failed_ids: Optional[List[str]] = None,
        new_news_list: Optional[List[News]] = None,
        mode: str = "daily"
    ) -> Dict:
        """准备报告数据

        Args:
            stats: 词组统计列表
            failed_ids: 失败的平台ID列表
            new_news_list: 新增新闻列表
            mode: 模式 (daily/current/incremental)

        Returns:
            Dict: 报告数据字典
        """
        # 在增量模式下隐藏新增新闻区域
        hide_new_section = mode == "incremental"

        # 处理新增新闻
        processed_new_titles = []
        if not hide_new_section and new_news_list:
            # 按平台分组
            new_by_platform = {}
            for news in new_news_list:
                platform_name = news.platform_name
                if platform_name not in new_by_platform:
                    new_by_platform[platform_name] = []
                new_by_platform[platform_name].append(news)

            for platform_name, news_list in new_by_platform.items():
                source_titles = []
                for news in news_list:
                    processed_title = {
                        "title": news.title,
                        "source_name": news.platform_name,
                        "time_display": "",
                        "count": 1,
                        "ranks": [news.rank],
                        "rank_threshold": self.rank_threshold,
                        "url": news.url,
                        "mobile_url": news.mobile_url or "",
                        "is_new": True,
                    }
                    source_titles.append(processed_title)

                if source_titles:
                    processed_new_titles.append({
                        "source_id": news.platform,
                        "source_name": platform_name,
                        "titles": source_titles,
                    })

        # 处理统计数据
        processed_stats = []
        for stat in stats:
            if stat.count <= 0:
                continue

            processed_titles = []
            for news in stat.news_list:
                # 从extra中获取信息
                extra = news.extra
                processed_title = {
                    "title": news.title,
                    "source_name": news.platform_name,
                    "time_display": extra.get("time_display", ""),
                    "count": extra.get("count", 1),
                    "ranks": extra.get("all_ranks", [news.rank]),
                    "rank_threshold": self.rank_threshold,
                    "url": news.url,
                    "mobile_url": extra.get("mobileUrl", ""),
                    "is_new": extra.get("is_new", False),
                }
                processed_titles.append(processed_title)

            processed_stats.append({
                "word": stat.word,
                "count": stat.count,
                "percentage": stat.percentage,
                "titles": processed_titles,
            })

        return {
            "stats": processed_stats,
            "new_titles": processed_new_titles,
            "failed_ids": failed_ids or [],
            "total_new_count": sum(
                len(source["titles"]) for source in processed_new_titles
            ),
        }

    def format_rank_display(
        self,
        ranks: List[int],
        rank_threshold: int,
        format_type: str
    ) -> str:
        """统一的排名格式化方法

        Args:
            ranks: 排名列表
            rank_threshold: 排名阈值
            format_type: 格式类型 (html/feishu/dingtalk/wework/telegram/ntfy)

        Returns:
            str: 格式化后的排名显示
        """
        if not ranks:
            return ""

        unique_ranks = sorted(set(ranks))
        min_rank = unique_ranks[0]
        max_rank = unique_ranks[-1]

        # 根据平台选择高亮格式
        if format_type == "html":
            highlight_start = "<font color='red'><strong>"
            highlight_end = "</strong></font>"
        elif format_type == "feishu":
            highlight_start = "<font color='red'>**"
            highlight_end = "**</font>"
        elif format_type in ["dingtalk", "wework"]:
            highlight_start = "**"
            highlight_end = "**"
        elif format_type == "telegram":
            highlight_start = "<b>"
            highlight_end = "</b>"
        else:
            highlight_start = "**"
            highlight_end = "**"

        # 判断是否高亮
        is_highlight = min_rank <= rank_threshold

        if min_rank == max_rank:
            rank_text = f"[{min_rank}]"
        else:
            rank_text = f"[{min_rank} - {max_rank}]"

        if is_highlight:
            return f"{highlight_start}{rank_text}{highlight_end}"
        else:
            return rank_text

    def format_title_for_platform(
        self,
        platform: str,
        title_data: Dict,
        show_source: bool = True
    ) -> str:
        """统一的标题格式化方法

        Args:
            platform: 平台类型 (feishu/dingtalk/wework/telegram/ntfy/html)
            title_data: 标题数据字典
            show_source: 是否显示来源平台

        Returns:
            str: 格式化后的标题
        """
        rank_display = self.format_rank_display(
            title_data["ranks"],
            title_data["rank_threshold"],
            platform
        )

        link_url = title_data["mobile_url"] or title_data["url"]
        cleaned_title = clean_title(title_data["title"])
        title_prefix = "🆕 " if title_data.get("is_new") else ""

        if platform == "feishu":
            return self._format_feishu(
                cleaned_title, link_url, title_prefix, title_data, rank_display, show_source
            )
        elif platform == "dingtalk":
            return self._format_dingtalk(
                cleaned_title, link_url, title_prefix, title_data, rank_display, show_source
            )
        elif platform == "wework":
            return self._format_wework(
                cleaned_title, link_url, title_prefix, title_data, rank_display, show_source
            )
        elif platform == "telegram":
            return self._format_telegram(
                cleaned_title, link_url, title_prefix, title_data, rank_display, show_source
            )
        elif platform == "ntfy":
            return self._format_ntfy(
                cleaned_title, link_url, title_prefix, title_data, rank_display, show_source
            )
        elif platform == "html":
            return self._format_html(
                cleaned_title, link_url, title_data, rank_display
            )
        else:
            return cleaned_title

    def _format_feishu(
        self,
        title: str,
        link_url: str,
        prefix: str,
        data: Dict,
        rank_display: str,
        show_source: bool
    ) -> str:
        """飞书格式"""
        if link_url:
            formatted_title = f"[{title}]({link_url})"
        else:
            formatted_title = title

        if show_source:
            result = f"<font color='grey'>[{data['source_name']}]</font> {prefix}{formatted_title}"
        else:
            result = f"{prefix}{formatted_title}"

        if rank_display:
            result += f" {rank_display}"
        if data["time_display"]:
            result += f" <font color='grey'>- {data['time_display']}</font>"
        if data["count"] > 1:
            result += f" <font color='green'>({data['count']}次)</font>"

        return result

    def _format_dingtalk(
        self,
        title: str,
        link_url: str,
        prefix: str,
        data: Dict,
        rank_display: str,
        show_source: bool
    ) -> str:
        """钉钉格式"""
        if link_url:
            formatted_title = f"[{title}]({link_url})"
        else:
            formatted_title = title

        if show_source:
            result = f"[{data['source_name']}] {prefix}{formatted_title}"
        else:
            result = f"{prefix}{formatted_title}"

        if rank_display:
            result += f" {rank_display}"
        if data["time_display"]:
            result += f" - {data['time_display']}"
        if data["count"] > 1:
            result += f" ({data['count']}次)"

        return result

    def _format_wework(
        self,
        title: str,
        link_url: str,
        prefix: str,
        data: Dict,
        rank_display: str,
        show_source: bool
    ) -> str:
        """企业微信格式"""
        return self._format_dingtalk(title, link_url, prefix, data, rank_display, show_source)

    def _format_telegram(
        self,
        title: str,
        link_url: str,
        prefix: str,
        data: Dict,
        rank_display: str,
        show_source: bool
    ) -> str:
        """Telegram格式"""
        if link_url:
            formatted_title = f'<a href="{link_url}">{html_escape(title)}</a>'
        else:
            formatted_title = title

        if show_source:
            result = f"[{data['source_name']}] {prefix}{formatted_title}"
        else:
            result = f"{prefix}{formatted_title}"

        if rank_display:
            result += f" {rank_display}"
        if data["time_display"]:
            result += f" <code>- {data['time_display']}</code>"
        if data["count"] > 1:
            result += f" <code>({data['count']}次)</code>"

        return result

    def _format_ntfy(
        self,
        title: str,
        link_url: str,
        prefix: str,
        data: Dict,
        rank_display: str,
        show_source: bool
    ) -> str:
        """ntfy格式"""
        if link_url:
            formatted_title = f"[{title}]({link_url})"
        else:
            formatted_title = title

        if show_source:
            result = f"[{data['source_name']}] {prefix}{formatted_title}"
        else:
            result = f"{prefix}{formatted_title}"

        if rank_display:
            result += f" {rank_display}"
        if data["time_display"]:
            result += f" `- {data['time_display']}`"
        if data["count"] > 1:
            result += f" `({data['count']}次)`"

        return result

    def _format_html(
        self,
        title: str,
        link_url: str,
        data: Dict,
        rank_display: str
    ) -> str:
        """HTML格式"""
        escaped_title = html_escape(title)
        escaped_source_name = html_escape(data["source_name"])

        if link_url:
            escaped_url = html_escape(link_url)
            formatted_title = f'[{escaped_source_name}] <a href="{escaped_url}" target="_blank" class="news-link">{escaped_title}</a>'
        else:
            formatted_title = f'[{escaped_source_name}] <span class="no-link">{escaped_title}</span>'

        if rank_display:
            formatted_title += f" {rank_display}"
        if data["time_display"]:
            escaped_time = html_escape(data["time_display"])
            formatted_title += f" <font color='grey'>- {escaped_time}</font>"
        if data["count"] > 1:
            formatted_title += f" <font color='green'>({data['count']}次)</font>"

        if data.get("is_new"):
            formatted_title = f"<div class='new-title'>🆕 {formatted_title}</div>"

        return formatted_title

    def get_output_path(self, output_type: str, filename: str) -> Path:
        """获取输出文件路径

        Args:
            output_type: 输出类型 (html/txt)
            filename: 文件名

        Returns:
            Path: 文件路径
        """
        date_folder = format_date_folder()
        output_dir = Path("output") / date_folder / output_type
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir / filename

    def generate_text_report(
        self,
        stats: List[WordGroupStatistic],
        total_titles: int,
        failed_ids: Optional[List[str]] = None,
        new_news_list: Optional[List[News]] = None,
        mode: str = "daily",
        is_daily_summary: bool = False
    ) -> Path:
        """生成文本报告

        Args:
            stats: 词组统计列表
            total_titles: 总标题数
            failed_ids: 失败的平台ID列表
            new_news_list: 新增新闻列表
            mode: 模式
            is_daily_summary: 是否为当日汇总

        Returns:
            Path: 生成的文件路径
        """
        if is_daily_summary:
            if mode == "current":
                filename = "当前榜单汇总.txt"
            elif mode == "incremental":
                filename = "当日增量.txt"
            else:
                filename = "当日汇总.txt"
        else:
            filename = f"{format_time_filename()}.txt"

        file_path = self.get_output_path("txt", filename)

        report_data = self.prepare_report_data(stats, failed_ids, new_news_list, mode)

        content_lines = []

        # 写入词组统计
        for stat in report_data["stats"]:
            content_lines.append(f"{stat['word']} (共{stat['count']}条)")
            content_lines.append("")

            for title_data in stat["titles"]:
                # 简单的文本格式
                line = f"[{title_data['source_name']}] {title_data['title']}"
                if title_data["ranks"]:
                    min_rank = min(title_data["ranks"])
                    max_rank = max(title_data["ranks"])
                    if min_rank == max_rank:
                        line += f" [{min_rank}]"
                    else:
                        line += f" [{min_rank} - {max_rank}]"
                if title_data["time_display"]:
                    line += f" - {title_data['time_display']}"
                if title_data["count"] > 1:
                    line += f" ({title_data['count']}次)"
                if title_data["url"]:
                    line += f" [URL:{title_data['url']}]"
                if title_data["mobile_url"]:
                    line += f" [MOBILE:{title_data['mobile_url']}]"

                content_lines.append(line)

            content_lines.append("")

        # 写入新增新闻
        if report_data["new_titles"]:
            content_lines.append("==== 最新批次新增 ====")
            content_lines.append("")

            for source_data in report_data["new_titles"]:
                content_lines.append(f"{source_data['source_name']} (新增{len(source_data['titles'])}条)")
                content_lines.append("")

                for title_data in source_data["titles"]:
                    line = f"{title_data['title']}"
                    if title_data["ranks"]:
                        line += f" [{title_data['ranks'][0]}]"
                    if title_data["url"]:
                        line += f" [URL:{title_data['url']}]"
                    if title_data["mobile_url"]:
                        line += f" [MOBILE:{title_data['mobile_url']}]"

                    content_lines.append(line)

                content_lines.append("")

        # 写入失败信息
        if report_data["failed_ids"]:
            content_lines.append("==== 以下ID请求失败 ====")
            content_lines.append(", ".join(report_data["failed_ids"]))

        # 写入文件
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))

        return file_path

    def generate_json_report(
        self,
        stats: List[WordGroupStatistic],
        total_titles: int,
        failed_ids: Optional[List[str]] = None,
        new_news_list: Optional[List[News]] = None,
        mode: str = "daily",
        is_daily_summary: bool = False
    ) -> Tuple[Path, Path]:
        """生成 JSON 报告(汇总+增量)

        Args:
            stats: 词组统计列表
            total_titles: 总标题数
            failed_ids: 失败的平台ID列表
            new_news_list: 新增新闻列表
            mode: 模式
            is_daily_summary: 是否为当日汇总

        Returns:
            Tuple[Path, Path]: (汇总文件路径, 增量文件路径)
        """
        # 准备报告数据
        report_data = self.prepare_report_data(stats, failed_ids, new_news_list, mode)

        # 当前批次时间戳
        now = datetime.now()
        batch_id = format_time_filename()  # 如: "15时35分"

        # 构建当前批次数据
        current_batch = self._build_batch_data(
            batch_id=batch_id,
            timestamp=now,
            report_data=report_data,
            total_titles=total_titles
        )

        # 保存汇总 JSON (追加模式)
        summary_path = self._save_summary_json(current_batch, mode)

        # 保存增量 JSON (覆写模式)
        incremental_path = self._save_incremental_json(
            batch_id=batch_id,
            timestamp=now,
            report_data=report_data,
            mode=mode
        )

        return summary_path, incremental_path

    def _build_batch_data(
        self,
        batch_id: str,
        timestamp: datetime,
        report_data: Dict,
        total_titles: int
    ) -> Dict[str, Any]:
        """构建单个批次的数据结构

        Args:
            batch_id: 批次ID(如 "15时35分")
            timestamp: 时间戳
            report_data: prepare_report_data() 返回的数据
            total_titles: 总新闻数

        Returns:
            Dict: 批次数据结构
        """
        # 转换词组统计数据
        stats_list = []
        for stat in report_data["stats"]:
            news_list = []
            for title_data in stat["titles"]:
                news_item = {
                    "title": title_data["title"],
                    "url": title_data["url"],
                    "mobile_url": title_data["mobile_url"],
                    "platform": title_data["source_name"],  # 平台显示名称
                    "rank": min(title_data["ranks"]) if title_data["ranks"] else 999,
                    "ranks": title_data["ranks"],  # 所有排名
                    "occurrence_count": title_data["count"],  # 出现次数
                    "time_display": title_data["time_display"],
                    "is_new": title_data.get("is_new", False),
                }
                news_list.append(news_item)

            stats_list.append({
                "word_group": stat["word"],
                "count": stat["count"],
                "percentage": round(stat["percentage"], 2),
                "news_list": news_list,
            })

        return {
            "batch_id": batch_id,
            "timestamp": timestamp.isoformat(),
            "total_news_count": total_titles,
            "stats": stats_list,
        }

    def _save_summary_json(
        self,
        current_batch: Dict[str, Any],
        mode: str
    ) -> Path:
        """保存汇总 JSON (追加模式)

        汇总文件包含当天所有批次的历史数据,每次执行时追加新批次。

        Args:
            current_batch: 当前批次数据
            mode: 运行模式

        Returns:
            Path: 汇总文件路径
        """
        # 获取汇总文件路径
        summary_path = self.get_output_path("json", "news_summary.json")

        # 读取现有汇总数据
        if summary_path.exists():
            try:
                with open(summary_path, "r", encoding="utf-8") as f:
                    summary_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                # 文件损坏或读取失败,重新初始化
                summary_data = self._init_summary_structure()
        else:
            # 首次创建
            summary_data = self._init_summary_structure()

        # 追加当前批次
        summary_data["batches"].append(current_batch)

        # 更新元数据
        summary_data["metadata"]["total_batches"] = len(summary_data["batches"])
        summary_data["metadata"]["last_update"] = current_batch["timestamp"]
        summary_data["metadata"]["total_news_count"] = sum(
            batch["total_news_count"] for batch in summary_data["batches"]
        )

        # 原子写入(先写临时文件,再重命名)
        self._atomic_write_json(summary_path, summary_data)

        return summary_path

    def _save_incremental_json(
        self,
        batch_id: str,
        timestamp: datetime,
        report_data: Dict,
        mode: str
    ) -> Path:
        """保存增量 JSON (覆写模式)

        增量文件仅包含当前批次的新增数据,每次执行时完全覆写。

        Args:
            batch_id: 批次ID
            timestamp: 时间戳
            report_data: prepare_report_data() 返回的数据
            mode: 运行模式

        Returns:
            Path: 增量文件路径
        """
        incremental_path = self.get_output_path("json", "news_incremental.json")

        # 构建增量数据(仅包含标记为新增的新闻)
        incremental_stats = []
        for stat in report_data["stats"]:
            # 只保留新增新闻
            new_news_list = [
                title_data for title_data in stat["titles"]
                if title_data.get("is_new", False)
            ]

            if new_news_list:
                news_items = []
                for title_data in new_news_list:
                    news_items.append({
                        "title": title_data["title"],
                        "url": title_data["url"],
                        "mobile_url": title_data["mobile_url"],
                        "platform": title_data["source_name"],
                        "rank": min(title_data["ranks"]) if title_data["ranks"] else 999,
                        "ranks": title_data["ranks"],
                        "occurrence_count": title_data["count"],
                        "time_display": title_data["time_display"],
                    })

                incremental_stats.append({
                    "word_group": stat["word"],
                    "count": len(news_items),
                    "percentage": round(
                        len(news_items) / report_data.get("total_new_count", 1) * 100, 2
                    ) if report_data.get("total_new_count") else 0,
                    "news_list": news_items,
                })

        # 构建完整增量数据结构
        incremental_data = {
            "metadata": {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "batch_id": batch_id,
                "timestamp": timestamp.isoformat(),
                "new_news_count": report_data.get("total_new_count", 0),
            },
            "stats": incremental_stats,
        }

        # 原子写入
        self._atomic_write_json(incremental_path, incremental_data)

        return incremental_path

    def _init_summary_structure(self) -> Dict[str, Any]:
        """初始化汇总数据结构

        Returns:
            Dict: 初始化的汇总数据
        """
        return {
            "metadata": {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "total_batches": 0,
                "total_news_count": 0,
                "last_update": None,
            },
            "batches": [],
        }

    def _atomic_write_json(self, file_path: Path, data: Dict[str, Any]) -> None:
        """原子写入 JSON 文件

        先写入临时文件,成功后再重命名,防止写入失败导致数据丢失。

        Args:
            file_path: 目标文件路径
            data: 要写入的数据
        """
        # 确保目录存在
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # 创建临时文件(在同一目录下,确保原子 rename)
        fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix=".tmp_",
            suffix=".json"
        )

        try:
            # 写入临时文件
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            # 原子重命名
            os.replace(temp_path, file_path)
        except Exception as e:
            # 清理临时文件
            try:
                os.unlink(temp_path)
            except:
                pass
            raise e
