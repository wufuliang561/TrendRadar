# coding=utf-8
"""飞书通知器"""

import time
import requests
from typing import Dict, Optional

from src.notifiers.base import BaseNotifier
from src.notifiers.batch_sender import BatchSender
from src.core.reporter import NewsReporter
from src.utils.time import get_beijing_time


class FeishuNotifier(BaseNotifier):
    """飞书通知发送器"""

    @property
    def name(self) -> str:
        return "飞书"

    def is_configured(self) -> bool:
        """检查是否已配置

        Returns:
            bool: 是否已配置
        """
        webhook_url = self.config.get("FEISHU_WEBHOOK_URL", "")
        return bool(webhook_url and webhook_url.strip())

    def send(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict] = None,
        proxy_url: Optional[str] = None,
        mode: str = "daily"
    ) -> bool:
        """发送到飞书

        Args:
            report_data: 报告数据
            report_type: 报告类型
            update_info: 更新信息
            proxy_url: 代理URL
            mode: 模式

        Returns:
            bool: 是否发送成功
        """
        webhook_url = self.config.get("FEISHU_WEBHOOK_URL", "")
        if not webhook_url:
            print("飞书 webhook URL 未配置，跳过发送")
            return False

        # 准备请求
        headers = {"Content-Type": "application/json"}
        proxies = self._get_proxy(proxy_url)

        # 创建分批发送器
        reporter = NewsReporter(rank_threshold=self.config.get("RANK_THRESHOLD", 10))
        batch_sender = BatchSender(reporter)

        # 获取分批内容
        max_bytes = self.config.get("FEISHU_BATCH_SIZE", 29000)
        batches = batch_sender.split_content_into_batches(
            report_data, "feishu", update_info, max_bytes, mode
        )

        print(f"飞书消息分为 {len(batches)} 批次发送 [{report_type}]")

        # 逐批发送
        all_success = True
        for i, batch_content in enumerate(batches, 1):
            batch_size = len(batch_content.encode("utf-8"))
            print(f"发送飞书第 {i}/{len(batches)} 批次，大小：{batch_size} 字节 [{report_type}]")

            # 添加批次标识
            if len(batches) > 1:
                batch_header = f"**[第 {i}/{len(batches)} 批次]**\n\n"
                if "📊 **热点词汇统计**" in batch_content:
                    batch_content = batch_content.replace(
                        "📊 **热点词汇统计**\n\n", f"📊 **热点词汇统计** {batch_header}"
                    )
                else:
                    batch_content = batch_header + batch_content

            # 构建payload
            total_titles = sum(
                len(stat["titles"]) for stat in report_data["stats"] if stat["count"] > 0
            )
            now = get_beijing_time()

            payload = {
                "msg_type": "text",
                "content": {
                    "total_titles": total_titles,
                    "timestamp": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "report_type": report_type,
                    "text": batch_content,
                },
            }

            # 发送请求
            try:
                response = requests.post(
                    webhook_url, headers=headers, json=payload, proxies=proxies, timeout=30
                )

                if response.status_code == 200:
                    result = response.json()
                    # 检查飞书的响应状态
                    if result.get("StatusCode") == 0 or result.get("code") == 0:
                        print(f"飞书第 {i}/{len(batches)} 批次发送成功 [{report_type}]")
                        # 批次间间隔
                        if i < len(batches):
                            time.sleep(self.config.get("BATCH_SEND_INTERVAL", 1))
                    else:
                        error_msg = result.get("msg") or result.get("StatusMessage", "未知错误")
                        print(f"飞书第 {i}/{len(batches)} 批次发送失败: {error_msg} [{report_type}]")
                        all_success = False
                else:
                    print(
                        f"飞书第 {i}/{len(batches)} 批次发送失败: HTTP {response.status_code} [{report_type}]"
                    )
                    all_success = False

            except requests.exceptions.Timeout:
                print(f"飞书第 {i}/{len(batches)} 批次发送超时 [{report_type}]")
                all_success = False
            except requests.exceptions.RequestException as e:
                print(f"飞书第 {i}/{len(batches)} 批次发送异常: {e} [{report_type}]")
                all_success = False
            except Exception as e:
                print(f"飞书第 {i}/{len(batches)} 批次发送出错: {e} [{report_type}]")
                all_success = False

        return all_success
