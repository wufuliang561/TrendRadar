# coding=utf-8
"""邮件通知器"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Dict, Optional

from src.notifiers.base import BaseNotifier


class EmailNotifier(BaseNotifier):
    """邮件通知发送器"""

    @property
    def name(self) -> str:
        return "邮件"

    def is_configured(self) -> bool:
        email_from = self.config.get("EMAIL_FROM", "")
        email_password = self.config.get("EMAIL_PASSWORD", "")
        email_to = self.config.get("EMAIL_TO", "")
        return bool(
            email_from and email_from.strip()
            and email_password and email_password.strip()
            and email_to and email_to.strip()
        )

    def send(
        self,
        report_data: Dict,
        report_type: str,
        update_info: Optional[Dict] = None,
        proxy_url: Optional[str] = None,
        mode: str = "daily",
        html_file_path: Optional[str] = None
    ) -> bool:
        """发送邮件通知

        Args:
            report_data: 报告数据（未使用，邮件发送HTML文件）
            report_type: 报告类型
            update_info: 更新信息（未使用）
            proxy_url: 代理URL（邮件不支持）
            mode: 模式（未使用）
            html_file_path: HTML文件路径

        Returns:
            bool: 是否发送成功
        """
        email_from = self.config.get("EMAIL_FROM", "")
        email_password = self.config.get("EMAIL_PASSWORD", "")
        email_to = self.config.get("EMAIL_TO", "")
        smtp_server = self.config.get("EMAIL_SMTP_SERVER", "")
        smtp_port = self.config.get("EMAIL_SMTP_PORT", 465)

        if not email_from or not email_password or not email_to:
            print("邮件配置不完整，跳过发送")
            return False

        # 自动检测SMTP服务器
        if not smtp_server:
            smtp_server = self._get_smtp_server(email_from)
            if not smtp_server:
                print("无法自动检测SMTP服务器，跳过发送")
                return False

        # 读取HTML内容
        if html_file_path and Path(html_file_path).exists():
            with open(html_file_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        else:
            print(f"HTML文件不存在: {html_file_path}，跳过邮件发送")
            return False

        # 构建邮件
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"TrendRadar - {report_type}"
        msg["From"] = email_from
        msg["To"] = email_to

        # 添加HTML内容
        html_part = MIMEText(html_content, "html", "utf-8")
        msg.attach(html_part)

        # 发送邮件
        try:
            print(f"正在连接SMTP服务器: {smtp_server}:{smtp_port}")

            # 根据端口选择连接方式
            if smtp_port == 465:
                # SSL连接
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=30)
            else:
                # TLS连接
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)
                server.starttls()

            # 登录
            print("正在登录邮箱...")
            server.login(email_from, email_password)

            # 发送
            print(f"正在发送邮件到: {email_to}")
            server.sendmail(email_from, email_to.split(","), msg.as_string())

            server.quit()
            print(f"邮件发送成功 [{report_type}]")
            return True

        except smtplib.SMTPAuthenticationError:
            print("邮件发送失败: 认证失败，请检查邮箱和密码")
            return False
        except smtplib.SMTPException as e:
            print(f"邮件发送失败: SMTP错误 - {e}")
            return False
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False

    def _get_smtp_server(self, email: str) -> Optional[str]:
        """根据邮箱地址自动检测SMTP服务器

        Args:
            email: 邮箱地址

        Returns:
            Optional[str]: SMTP服务器地址
        """
        domain = email.split("@")[-1].lower()

        smtp_map = {
            "gmail.com": "smtp.gmail.com",
            "qq.com": "smtp.qq.com",
            "163.com": "smtp.163.com",
            "126.com": "smtp.126.com",
            "sina.com": "smtp.sina.com",
            "outlook.com": "smtp.office365.com",
            "hotmail.com": "smtp.office365.com",
            "live.com": "smtp.office365.com",
            "yahoo.com": "smtp.mail.yahoo.com",
        }

        smtp_server = smtp_map.get(domain)
        if smtp_server:
            print(f"自动检测SMTP服务器: {smtp_server} (基于 {domain})")
        else:
            print(f"警告: 无法为 {domain} 自动检测SMTP服务器")

        return smtp_server
