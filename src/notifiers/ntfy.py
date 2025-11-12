# coding=utf-8
"""ntfy通知器"""

import time
import requests
from typing import Dict, Optional

from src.notifiers.base import BaseNotifier
from src.notifiers.batch_sender import BatchSender
from src.core.reporter import NewsReporter


class NtfyNotifier(BaseNotifier):
    """ntfy通知发送器"""

    @property
    def name(self) -> str:
        return "ntfy"

    def is_configured(self) -> bool:
        server_url = self.config.get("NTFY_SERVER_URL", "")
        topic = self.config.get("NTFY_TOPIC", "")
        return bool(server_url and server_url.strip() and topic and topic.strip())

    def send(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict] = None,
        proxy_url: Optional[str] = None,
        mode: str = "daily"
    ) -> bool:
        server_url = self.config.get("NTFY_SERVER_URL", "https://ntfy.sh")
        topic = self.config.get("NTFY_TOPIC", "")
        token = self.config.get("NTFY_TOKEN", "")

        if not topic:
            print("ntfy topic 未配置，跳过发送")
            return False

        # 构建发送URL
        url = f"{server_url.rstrip('/')}/{topic}"

        headers = {"Content-Type": "text/markdown"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        proxies = self._get_proxy(proxy_url)

        reporter = NewsReporter(rank_threshold=self.config.get("RANK_THRESHOLD", 10))
        batch_sender = BatchSender(reporter)

        # ntfy没有明确的大小限制，但我们保守一点
        max_bytes = self.config.get("NTFY_BATCH_SIZE", 4000)
        batches = batch_sender.split_content_into_batches(
            report_data, "ntfy", update_info, max_bytes, mode
        )

        print(f"ntfy消息分为 {len(batches)} 批次发送 [{report_type}]")

        all_success = True
        for i, batch_content in enumerate(batches, 1):
            batch_size = len(batch_content.encode("utf-8"))
            print(f"发送ntfy第 {i}/{len(batches)} 批次，大小：{batch_size} 字节 [{report_type}]")

            # 添加批次标识和标题
            if len(batches) > 1:
                title = f"{report_type} [{i}/{len(batches)}]"
            else:
                title = report_type

            # ntfy使用特殊的header来设置标题和优先级
            batch_headers = headers.copy()
            batch_headers["Title"] = title
            batch_headers["Priority"] = "default"
            batch_headers["Tags"] = "newspaper"

            try:
                response = requests.post(
                    url,
                    headers=batch_headers,
                    data=batch_content.encode("utf-8"),
                    proxies=proxies,
                    timeout=30
                )

                if response.status_code == 200:
                    print(f"ntfy第 {i}/{len(batches)} 批次发送成功 [{report_type}]")
                    if i < len(batches):
                        time.sleep(self.config.get("BATCH_SEND_INTERVAL", 1))
                else:
                    print(f"ntfy第 {i}/{len(batches)} 批次发送失败: HTTP {response.status_code} [{report_type}]")
                    print(f"响应内容: {response.text}")
                    all_success = False

            except Exception as e:
                print(f"ntfy第 {i}/{len(batches)} 批次发送出错: {e} [{report_type}]")
                all_success = False

        return all_success
