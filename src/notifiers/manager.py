# coding=utf-8
"""通知管理器"""

from typing import Dict, List, Optional, Type

from src.notifiers.base import BaseNotifier
from src.notifiers.feishu import FeishuNotifier
from src.notifiers.dingtalk import DingTalkNotifier
from src.notifiers.wework import WeWorkNotifier
from src.notifiers.telegram import TelegramNotifier
from src.notifiers.email import EmailNotifier
from src.notifiers.ntfy import NtfyNotifier
from src.core.push_record import PushRecordManager
from src.utils.time import get_beijing_time


class NotificationManager:
    """通知管理器

    负责：
    - 管理所有通知渠道
    - 检查推送窗口和限制
    - 协调多渠道发送
    - 记录推送状态
    """

    def __init__(self, config: Dict):
        """初始化通知管理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.notifiers: Dict[str, BaseNotifier] = {}

        # 注册所有通知器
        self._register_notifiers()

    def _register_notifiers(self) -> None:
        """注册所有通知器"""
        notifier_classes: List[Type[BaseNotifier]] = [
            FeishuNotifier,
            DingTalkNotifier,
            WeWorkNotifier,
            TelegramNotifier,
            EmailNotifier,
            NtfyNotifier,
        ]

        for notifier_class in notifier_classes:
            notifier = notifier_class(self.config)
            # 使用类名作为key（去掉Notifier后缀）
            key = notifier_class.__name__.replace("Notifier", "").lower()
            self.notifiers[key] = notifier

    def send_notifications(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict] = None,
        proxy_url: Optional[str] = None,
        mode: str = "daily",
        html_file_path: Optional[str] = None
    ) -> Dict[str, bool]:
        """发送通知到所有配置的渠道

        Args:
            report_data: 报告数据
            report_type: 报告类型
            update_info: 更新信息
            proxy_url: 代理URL
            mode: 模式 (daily/current/incremental)
            html_file_path: HTML文件路径（用于邮件）

        Returns:
            Dict[str, bool]: 各渠道发送结果
        """
        results = {}

        # 检查推送窗口
        if not self._check_push_window():
            print("推送窗口控制：不在推送时间范围内或今天已推送，跳过推送")
            return results

        # 获取启用的通知器
        enabled_notifiers = self._get_enabled_notifiers()

        if not enabled_notifiers:
            print("未配置任何通知渠道，跳过通知发送")
            return results

        # 显示推送信息
        show_update_info = self.config.get("SHOW_VERSION_UPDATE", True)
        update_to_send = update_info if show_update_info else None

        # 逐个发送
        for name, notifier in enabled_notifiers.items():
            print(f"\n=== 发送到 {notifier.name} ===")

            try:
                # 邮件特殊处理
                if isinstance(notifier, EmailNotifier):
                    success = notifier.send(
                        report_data=report_data,
                        report_type=report_type,
                        update_info=update_to_send,
                        proxy_url=proxy_url,
                        mode=mode,
                        html_file_path=html_file_path
                    )
                else:
                    success = notifier.send(
                        report_data=report_data,
                        report_type=report_type,
                        update_info=update_to_send,
                        proxy_url=proxy_url,
                        mode=mode
                    )

                results[name] = success

            except Exception as e:
                print(f"{notifier.name} 发送异常: {e}")
                results[name] = False

        # 记录推送
        if any(results.values()):
            self._record_push(report_type)

        # 打印汇总
        self._print_summary(results)

        return results

    def _check_push_window(self) -> bool:
        """检查推送窗口限制

        Returns:
            bool: 是否允许推送
        """
        push_window = self.config.get("PUSH_WINDOW", {})

        if not push_window.get("ENABLED", False):
            return True

        push_manager = PushRecordManager(
            retention_days=push_window.get("RECORD_RETENTION_DAYS", 7)
        )

        # 检查时间范围
        time_range = push_window.get("TIME_RANGE", {})
        start_time = time_range.get("START", "00:00")
        end_time = time_range.get("END", "23:59")

        if not push_manager.is_in_time_range(start_time, end_time):
            now = get_beijing_time()
            print(
                f"推送窗口控制：当前时间 {now.strftime('%H:%M')} "
                f"不在推送时间窗口 {start_time}-{end_time} 内"
            )
            return False

        # 检查每日一次限制
        if push_window.get("ONCE_PER_DAY", False):
            if push_manager.has_pushed_today():
                print("推送窗口控制：今天已推送过")
                return False
            else:
                print("推送窗口控制：今天首次推送")

        return True

    def _get_enabled_notifiers(self) -> Dict[str, BaseNotifier]:
        """获取已配置的通知器

        Returns:
            Dict[str, BaseNotifier]: 已配置的通知器字典
        """
        enabled = {}

        for name, notifier in self.notifiers.items():
            if notifier.is_configured():
                enabled[name] = notifier

        return enabled

    def _record_push(self, report_type: str) -> None:
        """记录推送

        Args:
            report_type: 报告类型
        """
        push_window = self.config.get("PUSH_WINDOW", {})

        if push_window.get("ENABLED", False) and push_window.get("ONCE_PER_DAY", False):
            push_manager = PushRecordManager(
                retention_days=push_window.get("RECORD_RETENTION_DAYS", 7)
            )
            push_manager.record_push(report_type)

    def _print_summary(self, results: Dict[str, bool]) -> None:
        """打印发送汇总

        Args:
            results: 发送结果
        """
        print("\n" + "=" * 50)
        print("通知发送汇总")
        print("=" * 50)

        if not results:
            print("未发送任何通知")
            return

        success_count = sum(1 for success in results.values() if success)
        fail_count = len(results) - success_count

        for name, success in results.items():
            notifier = self.notifiers.get(name)
            status = "✅ 成功" if success else "❌ 失败"
            channel_name = notifier.name if notifier else name
            print(f"{channel_name}: {status}")

        print("-" * 50)
        print(f"总计: {len(results)} 个渠道 | 成功: {success_count} | 失败: {fail_count}")
        print("=" * 50)

    def list_notifiers(self) -> List[Dict[str, str]]:
        """列出所有通知器及其状态

        Returns:
            List[Dict[str, str]]: 通知器列表
        """
        notifier_list = []

        for name, notifier in self.notifiers.items():
            notifier_list.append({
                "name": notifier.name,
                "key": name,
                "configured": "是" if notifier.is_configured() else "否"
            })

        return notifier_list
