# coding=utf-8
"""NewNow 热榜聚合信息源"""

import json
import time
import random
from typing import List, Dict, Any, Tuple, Union, Optional
from src.sources.base import BaseSource
from src.models.news import News
from src.utils.http import HTTPClient
from src.utils.file import clean_title


class NewNowSource(BaseSource):
    """NewNow 热榜聚合信息源

    从 newsnow API 获取各平台热点新闻
    """

    API_BASE_URL = "https://newsnow.busiyi.world/api/s"

    @property
    def source_id(self) -> str:
        return "newsnow"

    @property
    def source_name(self) -> str:
        return "NewNow 热榜聚合"

    def fetch_news(
        self,
        request_interval: Optional[int] = None,
        **kwargs
    ) -> List[News]:
        """获取新闻列表

        Args:
            request_interval: 请求间隔（毫秒），默认从配置读取
            **kwargs: 其他参数

        Returns:
            List[News]: 新闻列表
        """
        source_config = self.get_source_config()
        platforms = source_config.get("platforms", self.config.get("PLATFORMS", []))

        if not platforms:
            print(f"警告: {self.source_name} 未配置平台列表")
            return []

        # 获取请求间隔
        if request_interval is None:
            request_interval = self.config.get("REQUEST_INTERVAL", 1000)

        # 爬取数据
        results, id_to_name, failed_ids = self._crawl_platforms(
            platforms,
            request_interval
        )

        # 转换为 News 对象
        news_list = self._convert_to_news(results, id_to_name)

        return news_list

    def _crawl_platforms(
        self,
        platforms: List[Dict[str, str]],
        request_interval: int
    ) -> Tuple[Dict, Dict, List]:
        """爬取多个平台数据

        Args:
            platforms: 平台列表 [{"id": "zhihu", "name": "知乎"}, ...]
            request_interval: 请求间隔（毫秒）

        Returns:
            Tuple[Dict, Dict, List]:
                - results: 爬取结果 {platform_id: {title: {ranks, url, mobileUrl}}}
                - id_to_name: ID到名称的映射
                - failed_ids: 失败的平台ID列表
        """
        # 初始化 HTTP 客户端
        proxy_url = None
        if self.config.get("USE_PROXY"):
            proxy_url = self.config.get("DEFAULT_PROXY")

        http_client = HTTPClient(proxy_url=proxy_url)

        results = {}
        id_to_name = {}
        failed_ids = []

        for i, platform in enumerate(platforms):
            platform_id = platform["id"]
            platform_name = platform["name"]
            id_to_name[platform_id] = platform_name

            # 获取平台数据
            response_text, success, error = self._fetch_platform_data(
                http_client,
                platform_id
            )

            if success and response_text:
                try:
                    data = json.loads(response_text)
                    results[platform_id] = self._parse_platform_data(data)
                except json.JSONDecodeError:
                    print(f"解析 {platform_id} 响应失败")
                    failed_ids.append(platform_id)
                except Exception as e:
                    print(f"处理 {platform_id} 数据出错: {e}")
                    failed_ids.append(platform_id)
            else:
                failed_ids.append(platform_id)

            # 请求间隔（最后一个不需要等待）
            if i < len(platforms) - 1:
                actual_interval = request_interval + random.randint(-10, 20)
                actual_interval = max(50, actual_interval)
                time.sleep(actual_interval / 1000)

        http_client.close()

        print(f"成功: {list(results.keys())}, 失败: {failed_ids}")
        return results, id_to_name, failed_ids

    def _fetch_platform_data(
        self,
        http_client: HTTPClient,
        platform_id: str
    ) -> Tuple[Optional[str], bool, Optional[str]]:
        """获取单个平台数据

        Args:
            http_client: HTTP 客户端
            platform_id: 平台ID

        Returns:
            Tuple[Optional[str], bool, Optional[str]]:
                - 响应文本
                - 是否成功
                - 错误信息
        """
        url = f"{self.API_BASE_URL}?id={platform_id}&latest"

        response_text, success, error = http_client.get(url, max_retries=2)

        if success and response_text:
            try:
                data_json = json.loads(response_text)
                status = data_json.get("status", "未知")

                if status not in ["success", "cache"]:
                    print(f"{platform_id} 响应状态异常: {status}")
                    return None, False, f"状态异常: {status}"

                status_info = "最新数据" if status == "success" else "缓存数据"
                print(f"获取 {platform_id} 成功（{status_info}）")
                return response_text, True, None

            except json.JSONDecodeError:
                print(f"{platform_id} JSON 解析失败")
                return None, False, "JSON 解析失败"

        return None, False, error

    def _parse_platform_data(self, data: Dict[str, Any]) -> Dict[str, Dict]:
        """解析平台数据

        Args:
            data: API 返回的JSON数据

        Returns:
            Dict: 解析后的数据 {title: {ranks, url, mobileUrl}}
        """
        parsed = {}
        items = data.get("items", [])

        for index, item in enumerate(items, 1):
            title = clean_title(item.get("title", ""))
            if not title:
                continue

            url = item.get("url", "")
            mobile_url = item.get("mobileUrl", "")

            if title in parsed:
                # 标题重复，添加排名
                parsed[title]["ranks"].append(index)
            else:
                parsed[title] = {
                    "ranks": [index],
                    "url": url,
                    "mobileUrl": mobile_url,
                }

        return parsed

    def _convert_to_news(
        self,
        results: Dict[str, Dict],
        id_to_name: Dict[str, str]
    ) -> List[News]:
        """将爬取结果转换为 News 对象列表

        Args:
            results: 爬取结果
            id_to_name: ID到名称的映射

        Returns:
            List[News]: 新闻列表
        """
        news_list = []

        for platform_id, titles in results.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            for title, info in titles.items():
                ranks = info["ranks"]
                # 使用最高排名（最小值）
                min_rank = min(ranks) if ranks else 999

                news = News(
                    title=title,
                    url=info["url"],
                    platform=platform_id,
                    platform_name=platform_name,
                    rank=min_rank,
                    source_id=self.source_id,
                    mobile_url=info.get("mobileUrl"),
                    extra={
                        "all_ranks": ranks  # 保存所有排名
                    }
                )
                news_list.append(news)

        return news_list

    def validate_config(self) -> bool:
        """验证配置

        Returns:
            bool: 配置是否有效
        """
        source_config = self.get_source_config()
        platforms = source_config.get("platforms", self.config.get("PLATFORMS", []))

        if not platforms:
            print(f"警告: {self.source_name} 未配置平台列表")
            return False

        return True
