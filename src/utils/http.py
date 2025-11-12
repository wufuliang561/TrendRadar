# coding=utf-8
"""HTTP 请求工具"""

import time
import random
from typing import Optional, Dict, Any, Tuple
import requests


class HTTPClient:
    """HTTP 客户端

    提供带重试机制的 HTTP 请求功能
    """

    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache",
    }

    def __init__(self, proxy_url: Optional[str] = None, timeout: int = 10):
        """初始化 HTTP 客户端

        Args:
            proxy_url: 代理URL（如 "http://127.0.0.1:7890"）
            timeout: 请求超时时间（秒）
        """
        self.proxy_url = proxy_url
        self.timeout = timeout
        self.session = requests.Session()

    def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
        min_retry_wait: int = 3,
        max_retry_wait: int = 5,
    ) -> Tuple[Optional[str], bool, Optional[str]]:
        """发送 GET 请求（带重试机制）

        Args:
            url: 请求URL
            headers: 请求头（会与默认请求头合并）
            params: URL 参数
            max_retries: 最大重试次数
            min_retry_wait: 最小重试等待时间（秒）
            max_retry_wait: 最大重试等待时间（秒）

        Returns:
            Tuple[Optional[str], bool, Optional[str]]:
                - 响应文本（失败返回 None）
                - 是否成功
                - 错误信息（成功返回 None）
        """
        # 合并请求头
        merged_headers = self.DEFAULT_HEADERS.copy()
        if headers:
            merged_headers.update(headers)

        # 配置代理
        proxies = None
        if self.proxy_url:
            proxies = {"http": self.proxy_url, "https": self.proxy_url}

        retries = 0
        while retries <= max_retries:
            try:
                response = self.session.get(
                    url,
                    headers=merged_headers,
                    params=params,
                    proxies=proxies,
                    timeout=self.timeout
                )
                response.raise_for_status()

                return response.text, True, None

            except requests.exceptions.Timeout as e:
                error_msg = f"请求超时: {e}"
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP 错误: {e}"
            except requests.exceptions.RequestException as e:
                error_msg = f"请求异常: {e}"
            except Exception as e:
                error_msg = f"未知错误: {e}"

            retries += 1
            if retries <= max_retries:
                # 计算等待时间（随机退避）
                base_wait = random.uniform(min_retry_wait, max_retry_wait)
                additional_wait = (retries - 1) * random.uniform(1, 2)
                wait_time = base_wait + additional_wait

                print(f"请求失败: {error_msg}. {wait_time:.2f}秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"请求最终失败: {error_msg}")
                return None, False, error_msg

        return None, False, "超过最大重试次数"

    def post(
        self,
        url: str,
        data: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        max_retries: int = 2,
        min_retry_wait: int = 3,
        max_retry_wait: int = 5,
    ) -> Tuple[Optional[str], bool, Optional[str]]:
        """发送 POST 请求（带重试机制）

        Args:
            url: 请求URL
            data: 表单数据
            json: JSON 数据
            headers: 请求头
            max_retries: 最大重试次数
            min_retry_wait: 最小重试等待时间（秒）
            max_retry_wait: 最大重试等待时间（秒）

        Returns:
            Tuple[Optional[str], bool, Optional[str]]:
                - 响应文本（失败返回 None）
                - 是否成功
                - 错误信息（成功返回 None）
        """
        # 合并请求头
        merged_headers = self.DEFAULT_HEADERS.copy()
        if headers:
            merged_headers.update(headers)

        # 配置代理
        proxies = None
        if self.proxy_url:
            proxies = {"http": self.proxy_url, "https": self.proxy_url}

        retries = 0
        while retries <= max_retries:
            try:
                response = self.session.post(
                    url,
                    data=data,
                    json=json,
                    headers=merged_headers,
                    proxies=proxies,
                    timeout=self.timeout
                )
                response.raise_for_status()

                return response.text, True, None

            except requests.exceptions.Timeout as e:
                error_msg = f"请求超时: {e}"
            except requests.exceptions.HTTPError as e:
                error_msg = f"HTTP 错误: {e}"
            except requests.exceptions.RequestException as e:
                error_msg = f"请求异常: {e}"
            except Exception as e:
                error_msg = f"未知错误: {e}"

            retries += 1
            if retries <= max_retries:
                # 计算等待时间（随机退避）
                base_wait = random.uniform(min_retry_wait, max_retry_wait)
                additional_wait = (retries - 1) * random.uniform(1, 2)
                wait_time = base_wait + additional_wait

                print(f"请求失败: {error_msg}. {wait_time:.2f}秒后重试...")
                time.sleep(wait_time)
            else:
                print(f"请求最终失败: {error_msg}")
                return None, False, error_msg

        return None, False, "超过最大重试次数"

    def close(self):
        """关闭会话"""
        self.session.close()

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.close()
