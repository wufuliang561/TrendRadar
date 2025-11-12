# coding=utf-8
"""RSS 订阅源"""

import feedparser
from datetime import datetime
from typing import List, Dict, Any
from src.sources.base import BaseSource
from src.models.news import News
from src.utils.file import clean_title


class RSSSource(BaseSource):
    """RSS 订阅源

    支持标准的 RSS/Atom feed
    """

    @property
    def source_id(self) -> str:
        return "rss"

    @property
    def source_name(self) -> str:
        return "RSS 订阅"

    def fetch_news(self, **kwargs) -> List[News]:
        """获取新闻列表

        Returns:
            List[News]: 新闻列表
        """
        source_config = self.get_source_config()
        feeds = source_config.get("feeds", [])

        if not feeds:
            print(f"警告: {self.source_name} 未配置 feed 列表")
            return []

        news_list = []

        for feed_config in feeds:
            feed_url = feed_config.get("url")
            feed_name = feed_config.get("name", feed_url)

            if not feed_url:
                continue

            try:
                feed_news = self._fetch_feed(feed_url, feed_name)
                news_list.extend(feed_news)
            except Exception as e:
                print(f"获取 RSS feed {feed_name} 失败: {e}")
                continue

        return news_list

    def _fetch_feed(self, feed_url: str, feed_name: str) -> List[News]:
        """获取单个 feed 的新闻

        Args:
            feed_url: Feed URL
            feed_name: Feed 名称

        Returns:
            List[News]: 新闻列表
        """
        try:
            feed = feedparser.parse(feed_url)

            if feed.bozo:
                print(f"警告: RSS feed {feed_name} 解析可能有问题")

            news_list = []
            for index, entry in enumerate(feed.entries, 1):
                title = clean_title(entry.get("title", ""))
                link = entry.get("link", "")

                if not title or not link:
                    continue

                # 解析发布时间
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                timestamp = None
                if published:
                    try:
                        timestamp = datetime(*published[:6])
                    except Exception:
                        pass

                # 提取摘要
                summary = entry.get("summary", "")

                news = News(
                    title=title,
                    url=link,
                    platform="rss",
                    platform_name=feed_name,
                    rank=index,
                    source_id=self.source_id,
                    timestamp=timestamp,
                    extra={
                        "summary": summary,
                        "feed_url": feed_url
                    }
                )
                news_list.append(news)

            print(f"获取 RSS feed {feed_name} 成功，共 {len(news_list)} 条")
            return news_list

        except Exception as e:
            print(f"解析 RSS feed {feed_name} 失败: {e}")
            return []

    def validate_config(self) -> bool:
        """验证配置

        Returns:
            bool: 配置是否有效
        """
        source_config = self.get_source_config()
        feeds = source_config.get("feeds", [])

        if not feeds:
            print(f"警告: {self.source_name} 未配置 feed 列表")
            return False

        for feed in feeds:
            if "url" not in feed:
                print(f"警告: RSS feed 配置缺少 url 字段")
                return False

        return True
