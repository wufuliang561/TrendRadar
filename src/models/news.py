# coding=utf-8
"""新闻数据模型"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any


@dataclass
class News:
    """标准化新闻数据模型

    该类用于统一不同信息源获取的新闻数据格式，便于后续处理
    """

    title: str                          # 新闻标题
    url: str                            # 新闻链接
    platform: str                       # 平台 ID（如 zhihu, weibo）
    platform_name: str                  # 平台显示名称（如 知乎, 微博）
    rank: int                           # 当前排名
    hotness: int = 0                    # 热度值
    timestamp: Optional[datetime] = None  # 时间戳
    source_id: str = "unknown"          # 信息源 ID（如 newsnow, rss）
    mobile_url: Optional[str] = None    # 移动端链接
    extra: Dict[str, Any] = field(default_factory=dict)  # 扩展字段

    def __post_init__(self):
        """初始化后处理"""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def calculate_weight(
        self,
        ranks: List[int],
        count: int,
        rank_weight: float = 0.6,
        frequency_weight: float = 0.3,
        hotness_weight: float = 0.1
    ) -> float:
        """计算新闻权重

        权重计算公式:
        - 排名权重 = Σ(11 - min(rank, 10)) / 出现次数
        - 频次权重 = min(出现次数, 10) × 10
        - 热度权重 = (高排名次数 / 总次数) × 100
        - 总权重 = 排名权重 × 60% + 频次权重 × 30% + 热度权重 × 10%

        Args:
            ranks: 该新闻在不同时间的排名列表
            count: 出现次数
            rank_weight: 排名权重系数（默认 0.6）
            frequency_weight: 频次权重系数（默认 0.3）
            hotness_weight: 热度权重系数（默认 0.1）

        Returns:
            float: 计算得出的总权重分数
        """
        if not ranks or count == 0:
            return 0.0

        # 1. 排名权重：排名越高（数字越小）权重越大
        rank_score = sum(11 - min(rank, 10) for rank in ranks) / len(ranks)

        # 2. 频次权重：出现次数越多权重越大（最高10次）
        freq_score = min(count, 10) * 10

        # 3. 热度权重：高排名（前10）次数占比
        high_rank_count = sum(1 for rank in ranks if rank <= 10)
        hot_score = (high_rank_count / len(ranks)) * 100 if ranks else 0

        # 4. 加权总分
        total = (
            rank_score * rank_weight +
            freq_score * frequency_weight +
            hot_score * hotness_weight
        )

        return round(total, 2)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            Dict: 新闻对象的字典表示
        """
        return {
            "title": self.title,
            "url": self.url,
            "platform": self.platform,
            "platform_name": self.platform_name,
            "rank": self.rank,
            "hotness": self.hotness,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source_id": self.source_id,
            "mobile_url": self.mobile_url,
            "extra": self.extra
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "News":
        """从字典创建新闻对象

        Args:
            data: 包含新闻数据的字典

        Returns:
            News: 新闻对象实例
        """
        timestamp = data.get("timestamp")
        if timestamp and isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)

        return cls(
            title=data["title"],
            url=data["url"],
            platform=data["platform"],
            platform_name=data["platform_name"],
            rank=data["rank"],
            hotness=data.get("hotness", 0),
            timestamp=timestamp,
            source_id=data.get("source_id", "unknown"),
            mobile_url=data.get("mobile_url"),
            extra=data.get("extra", {})
        )


@dataclass
class NewsStatistic:
    """新闻统计信息

    用于存储新闻在多个时间批次中的统计数据
    """

    title: str                          # 新闻标题
    source_name: str                    # 来源平台名称
    url: str                            # 新闻链接
    mobile_url: Optional[str] = None    # 移动端链接
    ranks: List[int] = field(default_factory=list)  # 所有排名记录
    count: int = 0                      # 出现次数
    first_time: str = ""                # 首次出现时间
    last_time: str = ""                 # 最后出现时间
    time_display: str = ""              # 时间范围显示
    rank_threshold: int = 10            # 排名阈值
    is_new: bool = False                # 是否为新增
    weight: float = 0.0                 # 权重分数

    def calculate_weight(
        self,
        rank_weight: float = 0.6,
        frequency_weight: float = 0.3,
        hotness_weight: float = 0.1
    ) -> float:
        """计算统计权重（复用 News 的计算逻辑）"""
        if not self.ranks or self.count == 0:
            return 0.0

        # 排名权重
        rank_score = sum(11 - min(rank, 10) for rank in self.ranks) / len(self.ranks)

        # 频次权重
        freq_score = min(self.count, 10) * 10

        # 热度权重
        high_rank_count = sum(1 for rank in self.ranks if rank <= 10)
        hot_score = (high_rank_count / len(self.ranks)) * 100 if self.ranks else 0

        # 加权总分
        total = (
            rank_score * rank_weight +
            freq_score * frequency_weight +
            hot_score * hotness_weight
        )

        self.weight = round(total, 2)
        return self.weight


@dataclass
class WordGroupStatistic:
    """词组统计信息

    用于存储某个关键词组匹配的新闻统计
    """

    word: str                           # 词组关键字
    count: int                          # 匹配的新闻数量
    news_list: List[News]               # 新闻列表
    percentage: float = 0.0             # 占总新闻的百分比
