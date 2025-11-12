# coding=utf-8
"""关键词筛选模块"""

import os
from pathlib import Path
from typing import List, Dict, Tuple, Optional


class NewsFilter:
    """新闻筛选器

    基于关键词配置文件筛选新闻标题
    支持三种语法：
    - 普通词：标题包含任一即匹配
    - 必须词（+前缀）：必须同时包含才匹配
    - 过滤词（!前缀）：包含则排除
    """

    def __init__(self, frequency_file: Optional[str] = None):
        """初始化筛选器

        Args:
            frequency_file: 关键词配置文件路径
        """
        if frequency_file is None:
            frequency_file = os.environ.get(
                "FREQUENCY_WORDS_PATH", "config/frequency_words.txt"
            )

        self.frequency_file = frequency_file
        self.word_groups: List[Dict] = []
        self.filter_words: List[str] = []

        self._load_frequency_words()

    def _load_frequency_words(self) -> None:
        """加载频率词配置"""
        frequency_path = Path(self.frequency_file)
        if not frequency_path.exists():
            raise FileNotFoundError(f"频率词文件 {self.frequency_file} 不存在")

        with open(frequency_path, "r", encoding="utf-8") as f:
            content = f.read()

        # 以空行分隔词组
        word_groups = [group.strip() for group in content.split("\n\n") if group.strip()]

        processed_groups = []
        filter_words = []

        for group in word_groups:
            words = [word.strip() for word in group.split("\n") if word.strip()]

            group_required_words = []
            group_normal_words = []
            group_filter_words = []

            for word in words:
                if word.startswith("!"):
                    # 过滤词（全局生效）
                    filter_words.append(word[1:])
                    group_filter_words.append(word[1:])
                elif word.startswith("+"):
                    # 必须词
                    group_required_words.append(word[1:])
                else:
                    # 普通词
                    group_normal_words.append(word)

            # 至少有必须词或普通词才添加词组
            if group_required_words or group_normal_words:
                if group_normal_words:
                    group_key = " ".join(group_normal_words)
                else:
                    group_key = " ".join(group_required_words)

                processed_groups.append(
                    {
                        "required": group_required_words,
                        "normal": group_normal_words,
                        "group_key": group_key,
                    }
                )

        self.word_groups = processed_groups
        self.filter_words = filter_words

        print(f"已加载 {len(self.word_groups)} 个词组，{len(self.filter_words)} 个过滤词")

    def matches(self, title: str) -> bool:
        """检查标题是否匹配筛选规则

        Args:
            title: 新闻标题

        Returns:
            bool: 是否匹配
        """
        # 如果没有配置词组，则匹配所有标题（支持显示全部新闻）
        if not self.word_groups:
            return True

        title_lower = title.lower()

        # 过滤词检查（任一匹配则排除）
        if any(filter_word.lower() in title_lower for filter_word in self.filter_words):
            return False

        # 词组匹配检查
        for group in self.word_groups:
            required_words = group["required"]
            normal_words = group["normal"]

            # 必须词检查（所有必须词都要包含）
            if required_words:
                all_required_present = all(
                    req_word.lower() in title_lower for req_word in required_words
                )
                if not all_required_present:
                    continue

            # 普通词检查（任一包含即可）
            if normal_words:
                any_normal_present = any(
                    normal_word.lower() in title_lower for normal_word in normal_words
                )
                if not any_normal_present:
                    continue

            # 该词组匹配成功
            return True

        return False

    def filter_news_list(self, news_list: List) -> List:
        """筛选新闻列表

        Args:
            news_list: 新闻对象列表

        Returns:
            List: 筛选后的新闻列表
        """
        return [news for news in news_list if self.matches(news.title)]

    def get_word_groups(self) -> List[Dict]:
        """获取词组配置

        Returns:
            List[Dict]: 词组列表
        """
        return self.word_groups

    def get_filter_words(self) -> List[str]:
        """获取过滤词列表

        Returns:
            List[str]: 过滤词列表
        """
        return self.filter_words

    def reload(self) -> None:
        """重新加载配置文件"""
        self._load_frequency_words()
