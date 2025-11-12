# coding=utf-8
"""Telegram通知器"""

import time
import requests
from typing import Dict, Optional

from src.notifiers.base import BaseNotifier
from src.notifiers.batch_sender import BatchSender
from src.core.reporter import NewsReporter


class TelegramNotifier(BaseNotifier):
    """Telegram通知发送器"""

    @property
    def name(self) -> str:
        return "Telegram"

    def is_configured(self) -> bool:
        bot_token = self.config.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = self.config.get("TELEGRAM_CHAT_ID", "")
        return bool(bot_token and bot_token.strip() and chat_id and chat_id.strip())

    def send(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict] = None,
        proxy_url: Optional[str] = None,
        mode: str = "daily"
    ) -> bool:
        bot_token = self.config.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = self.config.get("TELEGRAM_CHAT_ID", "")

        if not bot_token or not chat_id:
            print("Telegram Bot Token 或 Chat ID 未配置，跳过发送")
            return False

        # 构建API URL
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

        headers = {"Content-Type": "application/json"}
        proxies = self._get_proxy(proxy_url)

        reporter = NewsReporter(rank_threshold=self.config.get("RANK_THRESHOLD", 10))
        batch_sender = BatchSender(reporter)

        # Telegram限制为4096字符，但我们用字节数更安全
        max_bytes = self.config.get("TELEGRAM_BATCH_SIZE", 4000)
        batches = batch_sender.split_content_into_batches(
            report_data, "telegram", update_info, max_bytes, mode
        )

        print(f"Telegram消息分为 {len(batches)} 批次发送 [{report_type}]")

        all_success = True
        for i, batch_content in enumerate(batches, 1):
            batch_size = len(batch_content.encode("utf-8"))
            print(f"发送Telegram第 {i}/{len(batches)} 批次，大小：{batch_size} 字节 [{report_type}]")

            if len(batches) > 1:
                batch_header = f"<b>[第 {i}/{len(batches)} 批次]</b>\n\n"
                if "📊 <b>热点词汇统计</b>" in batch_content:
                    batch_content = batch_content.replace(
                        "📊 <b>热点词汇统计</b>\n\n", f"📊 <b>热点词汇统计</b> {batch_header}"
                    )
                else:
                    batch_content = batch_header + batch_content

            payload = {
                "chat_id": chat_id,
                "text": batch_content,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            }

            try:
                response = requests.post(
                    api_url, headers=headers, json=payload, proxies=proxies, timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get("ok"):
                        print(f"Telegram第 {i}/{len(batches)} 批次发送成功 [{report_type}]")
                        if i < len(batches):
                            time.sleep(self.config.get("BATCH_SEND_INTERVAL", 1))
                    else:
                        error_desc = result.get("description", "未知错误")
                        print(f"Telegram第 {i}/{len(batches)} 批次发送失败: {error_desc} [{report_type}]")
                        all_success = False
                else:
                    print(f"Telegram第 {i}/{len(batches)} 批次发送失败: HTTP {response.status_code} [{report_type}]")
                    all_success = False

            except Exception as e:
                print(f"Telegram第 {i}/{len(batches)} 批次发送出错: {e} [{report_type}]")
                all_success = False

        return all_success
