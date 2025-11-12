# coding=utf-8
"""上下文构建服务

负责构建大模型对话所需的上下文数据
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.utils.time import get_beijing_time, format_date_folder


class ContextBuilder:
    """上下文构建器

    负责:
    - 从 output/ 目录读取最新新闻数据
    - 精简字段以节省 Token
    - 构建 System Prompt
    - 统计 Token 使用量
    """

    def __init__(self, output_dir: str = "output"):
        """初始化上下文构建器

        Args:
            output_dir: 输出目录路径
        """
        self.output_dir = Path(output_dir)

    def get_latest_news_context(
        self,
        platforms: Optional[List[str]] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """获取最新新闻上下文

        Args:
            platforms: 平台筛选列表（如 ["zhihu", "weibo"]）
            limit: 最大新闻数量

        Returns:
            Dict: 包含 date, news_count, news_data 的字典
        """
        # 获取今天的日期目录
        today = get_beijing_time()
        date_str = format_date_folder(today)
        date_dir = self.output_dir / date_str

        if not date_dir.exists():
            return {
                "date": date_str,
                "news_count": 0,
                "news_data": [],
                "error": f"未找到 {date_str} 的新闻数据"
            }

        # 查找 JSON 数据文件
        json_dir = date_dir / "json"
        summary_file = json_dir / "news_summary.json"

        if not summary_file.exists():
            return {
                "date": date_str,
                "news_count": 0,
                "news_data": [],
                "error": "新闻数据文件不存在"
            }

        try:
            # 读取汇总文件
            with open(summary_file, "r", encoding="utf-8") as f:
                summary_data = json.load(f)

            # 提取最新批次的新闻数据
            news_items = self._extract_news_from_summary(
                summary_data,
                platforms=platforms,
                limit=limit
            )

            return {
                "date": date_str,
                "news_count": len(news_items),
                "news_data": news_items,
                "platforms": list(set(item["platform"] for item in news_items))
            }

        except Exception as e:
            return {
                "date": date_str,
                "news_count": 0,
                "news_data": [],
                "error": f"读取数据失败: {str(e)}"
            }

    def _extract_news_from_summary(
        self,
        summary_data: Dict[str, Any],
        platforms: Optional[List[str]] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """从汇总数据中提取新闻（精简格式）

        Args:
            summary_data: 汇总数据
            platforms: 平台筛选
            limit: 数量限制

        Returns:
            List[Dict]: 精简的新闻列表
        """
        news_list = []

        # 从最新批次中提取
        batches = summary_data.get("batches", [])
        if not batches:
            return news_list

        # 获取最新批次
        latest_batch = batches[-1]
        stats = latest_batch.get("stats", [])

        # 遍历词组统计
        for stat in stats:
            titles = stat.get("titles", [])

            for title_data in titles:
                # 平台筛选
                source_id = title_data.get("source_id", "")
                if platforms and source_id not in platforms:
                    continue

                # 构建精简的新闻项（仅保留核心字段）
                news_item = {
                    "title": title_data.get("title", ""),
                    "platform": title_data.get("source_name", ""),
                    "rank": min(title_data.get("ranks", [99])[-1] if title_data.get("ranks") else 99, 99),
                    "count": title_data.get("count", 1),
                    "weight": round(title_data.get("weight", 0.0), 2)
                }

                news_list.append(news_item)

                # 达到数量限制
                if len(news_list) >= limit:
                    break

            if len(news_list) >= limit:
                break

        # 按权重排序
        news_list.sort(key=lambda x: x["weight"], reverse=True)

        return news_list[:limit]

    def build_system_prompt(self, context_data: Dict[str, Any]) -> str:
        """构建 System Prompt

        Args:
            context_data: 上下文数据

        Returns:
            str: System Prompt
        """
        date = context_data.get("date", "")
        news_count = context_data.get("news_count", 0)
        platforms = context_data.get("platforms", [])

        prompt = f"""你是一个专业的新闻分析助手,擅长从热点新闻数据中提取洞察和分析趋势。

【当前数据范围】
- 日期: {date}
- 新闻数量: {news_count} 条
- 覆盖平台: {', '.join(platforms)}

【数据字段说明】
- title: 新闻标题
- platform: 来源平台
- rank: 在平台的排名(越小越热门,1 为最热)
- count: 在不同批次中出现的次数(持续热度指标)
- weight: 综合权重分数(0-100,考虑排名+频次+热度,越高越重要)

【分析原则】
1. 客观准确,基于数据事实进行分析
2. 结构清晰,突出重点和趋势
3. 识别新闻间的关联性和热点话题
4. 避免主观臆断和不实猜测
5. 如涉及敏感话题,保持中立客观

【输出要求】
- 使用中文回答
- 分条列举,逻辑清晰
- 适当使用数据支撑观点
- 避免冗长的描述,言简意赅"""

        return prompt

    def build_context_message(self, context_data: Dict[str, Any]) -> str:
        """构建上下文消息（发送给大模型的数据）

        Args:
            context_data: 上下文数据

        Returns:
            str: JSON 格式的上下文数据
        """
        # 构建精简的数据结构
        simplified_data = {
            "date": context_data.get("date"),
            "total_count": context_data.get("news_count"),
            "news": context_data.get("news_data", [])
        }

        return json.dumps(simplified_data, ensure_ascii=False, indent=2)

    def estimate_tokens(self, text: str) -> int:
        """估算文本的 Token 数量（粗略估计）

        Args:
            text: 文本内容

        Returns:
            int: 估算的 Token 数量
        """
        # 中文约 1.5 字符 = 1 token
        # 英文约 4 字符 = 1 token
        # 这里使用简单估算：中文占比60%,英文占比40%
        chinese_chars = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        other_chars = len(text) - chinese_chars

        estimated_tokens = int(chinese_chars / 1.5 + other_chars / 4)
        return estimated_tokens

    def get_context_stats(self, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取上下文统计信息

        Args:
            context_data: 上下文数据

        Returns:
            Dict: 统计信息
        """
        context_message = self.build_context_message(context_data)
        system_prompt = self.build_system_prompt(context_data)

        return {
            "news_count": context_data.get("news_count", 0),
            "platforms": context_data.get("platforms", []),
            "estimated_context_tokens": self.estimate_tokens(context_message),
            "estimated_system_tokens": self.estimate_tokens(system_prompt),
            "estimated_total_tokens": self.estimate_tokens(context_message + system_prompt),
            "data_size_bytes": len(context_message.encode('utf-8'))
        }
