# coding=utf-8
"""消息分批发送工具"""

from typing import Dict, List, Optional
from src.core.reporter import NewsReporter
from src.utils.time import get_beijing_time


class BatchSender:
    """消息分批发送器

    负责将长消息分批，避免超过平台限制
    """

    def __init__(self, reporter: NewsReporter):
        """初始化分批发送器

        Args:
            reporter: 报告生成器
        """
        self.reporter = reporter

    def split_content_into_batches(
        self,
        report_data: Dict,
        platform: str,
        update_info: Optional[Dict] = None,
        max_bytes: int = 20000,
        mode: str = "daily"
    ) -> List[str]:
        """将内容分割为多个批次

        Args:
            report_data: 报告数据
            platform: 平台类型
            update_info: 更新信息
            max_bytes: 每批次最大字节数
            mode: 模式

        Returns:
            List[str]: 批次内容列表
        """
        batches = []
        current_batch = ""

        # 构建基础页脚
        base_footer = self._build_footer(update_info, platform, mode)
        footer_size = len(base_footer.encode("utf-8"))

        # 留出安全余量
        safe_max_bytes = max_bytes - footer_size - 500

        # 添加标题
        header = self._build_header(report_data, platform)
        current_batch += header

        # 处理词组统计
        for stat in report_data["stats"]:
            if stat["count"] <= 0:
                continue

            stat_content = self._build_stat_section(stat, platform)
            stat_size = len(stat_content.encode("utf-8"))
            current_size = len(current_batch.encode("utf-8"))

            # 检查是否需要新批次
            if current_size + stat_size > safe_max_bytes and current_batch.strip():
                batches.append(current_batch + base_footer)
                current_batch = header

            current_batch += stat_content

        # 处理新增新闻
        if report_data.get("new_titles"):
            new_section = self._build_new_titles_section(report_data["new_titles"], platform)
            new_size = len(new_section.encode("utf-8"))
            current_size = len(current_batch.encode("utf-8"))

            if current_size + new_size > safe_max_bytes and current_batch.strip():
                batches.append(current_batch + base_footer)
                current_batch = header

            current_batch += new_section

        # 添加失败信息
        if report_data.get("failed_ids"):
            failed_section = self._build_failed_section(report_data["failed_ids"], platform)
            current_batch += failed_section

        # 添加最后一批
        current_batch_has_content = current_batch.strip() != header.strip()
        if current_batch_has_content:
            batches.append(current_batch + base_footer)

        return batches

    def _build_header(self, report_data: Dict, platform: str) -> str:
        """构建消息头部

        Args:
            report_data: 报告数据
            platform: 平台类型

        Returns:
            str: 头部内容
        """
        total_news = sum(stat["count"] for stat in report_data["stats"])

        if platform == "feishu":
            return f"📊 **热点词汇统计**\n\n共 {total_news} 条匹配新闻\n\n"
        elif platform in ["dingtalk", "wework"]:
            return f"📊 **热点词汇统计**\n\n共 {total_news} 条匹配新闻\n\n"
        elif platform == "telegram":
            return f"📊 <b>热点词汇统计</b>\n\n共 {total_news} 条匹配新闻\n\n"
        else:
            return f"📊 热点词汇统计\n\n共 {total_news} 条匹配新闻\n\n"

    def _build_stat_section(self, stat: Dict, platform: str) -> str:
        """构建词组统计部分

        Args:
            stat: 统计数据
            platform: 平台类型

        Returns:
            str: 统计部分内容
        """
        content = ""

        # 词组标题
        if platform == "feishu":
            content += f"**{stat['word']}** (共{stat['count']}条，占比{stat['percentage']}%)\n\n"
        elif platform in ["dingtalk", "wework"]:
            content += f"**{stat['word']}** (共{stat['count']}条，占比{stat['percentage']}%)\n\n"
        elif platform == "telegram":
            content += f"<b>{stat['word']}</b> (共{stat['count']}条，占比{stat['percentage']}%)\n\n"
        else:
            content += f"{stat['word']} (共{stat['count']}条，占比{stat['percentage']}%)\n\n"

        # 新闻列表
        for title_data in stat["titles"]:
            formatted_title = self.reporter.format_title_for_platform(
                platform, title_data, show_source=True
            )
            content += f"{formatted_title}\n"

        content += "\n"
        return content

    def _build_new_titles_section(self, new_titles: List[Dict], platform: str) -> str:
        """构建新增新闻部分

        Args:
            new_titles: 新增新闻列表
            platform: 平台类型

        Returns:
            str: 新增部分内容
        """
        content = ""

        if platform == "feishu":
            content += "**🆕 最新批次新增**\n\n"
        elif platform in ["dingtalk", "wework"]:
            content += "**🆕 最新批次新增**\n\n"
        elif platform == "telegram":
            content += "<b>🆕 最新批次新增</b>\n\n"
        else:
            content += "🆕 最新批次新增\n\n"

        for source_data in new_titles:
            source_name = source_data["source_name"]
            titles_count = len(source_data["titles"])

            if platform == "feishu":
                content += f"**{source_name}** (新增{titles_count}条)\n\n"
            elif platform in ["dingtalk", "wework"]:
                content += f"**{source_name}** (新增{titles_count}条)\n\n"
            elif platform == "telegram":
                content += f"<b>{source_name}</b> (新增{titles_count}条)\n\n"
            else:
                content += f"{source_name} (新增{titles_count}条)\n\n"

            for title_data in source_data["titles"]:
                formatted_title = self.reporter.format_title_for_platform(
                    platform, title_data, show_source=False
                )
                content += f"{formatted_title}\n"

            content += "\n"

        return content

    def _build_failed_section(self, failed_ids: List[str], platform: str) -> str:
        """构建失败信息部分

        Args:
            failed_ids: 失败的ID列表
            platform: 平台类型

        Returns:
            str: 失败部分内容
        """
        if not failed_ids:
            return ""

        content = "\n"

        if platform == "feishu":
            content += f"<font color='grey'>⚠️ 以下平台请求失败: {', '.join(failed_ids)}</font>\n"
        elif platform in ["dingtalk", "wework"]:
            content += f"⚠️ 以下平台请求失败: {', '.join(failed_ids)}\n"
        elif platform == "telegram":
            content += f"⚠️ 以下平台请求失败: {', '.join(failed_ids)}\n"
        else:
            content += f"⚠️ 以下平台请求失败: {', '.join(failed_ids)}\n"

        return content

    def _build_footer(self, update_info: Optional[Dict], platform: str, mode: str) -> str:
        """构建消息页脚

        Args:
            update_info: 更新信息
            platform: 平台类型
            mode: 模式

        Returns:
            str: 页脚内容
        """
        footer = "\n"

        # 添加更新信息
        if update_info:
            if platform == "feishu":
                footer += f"<font color='orange'>ℹ️ 发现新版本 v{update_info['latest_version']}，请前往 GitHub 更新</font>\n"
            elif platform in ["dingtalk", "wework"]:
                footer += f"ℹ️ 发现新版本 v{update_info['latest_version']}，请前往 GitHub 更新\n"
            elif platform == "telegram":
                footer += f"ℹ️ 发现新版本 v{update_info['latest_version']}，请前往 GitHub 更新\n"
            else:
                footer += f"ℹ️ 发现新版本 v{update_info['latest_version']}，请前往 GitHub 更新\n"

        # 添加时间戳
        now = get_beijing_time()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        if platform == "feishu":
            footer += f"<font color='grey'>📅 {timestamp}</font>"
        elif platform in ["dingtalk", "wework"]:
            footer += f"📅 {timestamp}"
        elif platform == "telegram":
            footer += f"<code>📅 {timestamp}</code>"
        else:
            footer += f"📅 {timestamp}"

        return footer
