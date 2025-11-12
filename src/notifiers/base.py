# coding=utf-8
"""通知发送基类"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class BaseNotifier(ABC):
    """通知发送器抽象基类

    所有通知渠道的基类，定义统一的接口
    """

    def __init__(self, config: Dict):
        """初始化通知器

        Args:
            config: 配置字典
        """
        self.config = config

    @property
    @abstractmethod
    def name(self) -> str:
        """通知渠道名称

        Returns:
            str: 渠道名称
        """
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """检查是否已配置

        Returns:
            bool: 是否已配置
        """
        pass

    @abstractmethod
    def send(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict] = None,
        proxy_url: Optional[str] = None,
        mode: str = "daily"
    ) -> bool:
        """发送通知

        Args:
            report_data: 报告数据
            report_type: 报告类型
            update_info: 更新信息
            proxy_url: 代理URL
            mode: 模式 (daily/current/incremental)

        Returns:
            bool: 是否发送成功
        """
        pass

    def _get_proxy(self, proxy_url: Optional[str] = None) -> Optional[Dict]:
        """获取代理配置

        Args:
            proxy_url: 代理URL

        Returns:
            Optional[Dict]: 代理字典
        """
        if proxy_url:
            return {"http": proxy_url, "https": proxy_url}
        return None
