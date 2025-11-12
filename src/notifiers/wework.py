# coding=utf-8
"""企业微信通知器"""

import time
import requests
from typing import Dict, Optional

from src.notifiers.base import BaseNotifier
from src.notifiers.batch_sender import BatchSender
from src.core.reporter import NewsReporter


class WeWorkNotifier(BaseNotifier):
    """企业微信通知发送器"""

    @property
    def name(self) -> str:
        return "企业微信"

    def is_configured(self) -> bool:
        webhook_url = self.config.get("WEWORK_WEBHOOK_URL", "")
        return bool(webhook_url and webhook_url.strip())

    def send(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict] = None,
        proxy_url: Optional[str] = None,
        mode: str = "daily"
    ) -> bool:
        webhook_url = self.config.get("WEWORK_WEBHOOK_URL", "")
        if not webhook_url:
            print("企业微信 webhook URL 未配置，跳过发送")
            return False

        headers = {"Content-Type": "application/json"}
        proxies = self._get_proxy(proxy_url)

        reporter = NewsReporter(rank_threshold=self.config.get("RANK_THRESHOLD", 10))
        batch_sender = BatchSender(reporter)

        # 企业微信限制较小，使用4KB
        max_bytes = self.config.get("WEWORK_BATCH_SIZE", 4000)
        batches = batch_sender.split_content_into_batches(
            report_data, "wework", update_info, max_bytes, mode
        )

        print(f"企业微信消息分为 {len(batches)} 批次发送 [{report_type}]")

        all_success = True
        for i, batch_content in enumerate(batches, 1):
            batch_size = len(batch_content.encode("utf-8"))
            print(f"发送企业微信第 {i}/{len(batches)} 批次，大小：{batch_size} 字节 [{report_type}]")

            if len(batches) > 1:
                batch_header = f"**[第 {i}/{len(batches)} 批次]**\n\n"
                if "📊 **热点词汇统计**" in batch_content:
                    batch_content = batch_content.replace(
                        "📊 **热点词汇统计**\n\n", f"📊 **热点词汇统计** {batch_header}"
                    )
                else:
                    batch_content = batch_header + batch_content

            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": batch_content,
                },
            }

            try:
                response = requests.post(
                    webhook_url, headers=headers, json=payload, proxies=proxies, timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("errcode") == 0:
                        print(f"企业微信第 {i}/{len(batches)} 批次发送成功 [{report_type}]")
                        if i < len(batches):
                            time.sleep(self.config.get("BATCH_SEND_INTERVAL", 1))
                    else:
                        error_msg = result.get("errmsg", "未知错误")
                        print(f"企业微信第 {i}/{len(batches)} 批次发送失败: {error_msg} [{report_type}]")
                        all_success = False
                else:
                    print(f"企业微信第 {i}/{len(batches)} 批次发送失败: HTTP {response.status_code} [{report_type}]")
                    all_success = False

            except Exception as e:
                print(f"企业微信第 {i}/{len(batches)} 批次发送出错: {e} [{report_type}]")
                all_success = False

        return all_success
