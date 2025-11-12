# coding=utf-8
"""配置管理模块"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml


class ConfigManager:
    """配置管理类

    负责加载和管理应用配置，支持环境变量覆盖
    """

    def __init__(self, config_path: str = "config/config.yaml"):
        """初始化配置管理器

        Args:
            config_path: 配置文件路径（可通过环境变量 CONFIG_PATH 覆盖）
        """
        self.config_path = os.environ.get("CONFIG_PATH", config_path)
        self._config: Optional[Dict[str, Any]] = None
        self._load_config()

    def _load_config(self) -> None:
        """加载配置文件"""
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"配置文件 {self.config_path} 不存在")

        with open(self.config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        print(f"配置文件加载成功: {self.config_path}")

        # 构建配置字典
        self._config = self._build_config(config_data)

        # 输出配置来源信息
        self._print_notification_sources()

    def _build_config(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """构建配置字典

        Args:
            config_data: 从 YAML 读取的原始配置数据

        Returns:
            Dict: 处理后的配置字典
        """
        config = {
            # 应用配置
            "VERSION_CHECK_URL": config_data["app"]["version_check_url"],
            "SHOW_VERSION_UPDATE": config_data["app"]["show_version_update"],

            # 爬虫配置
            "REQUEST_INTERVAL": config_data["crawler"]["request_interval"],
            "USE_PROXY": config_data["crawler"]["use_proxy"],
            "DEFAULT_PROXY": config_data["crawler"]["default_proxy"],
            "ENABLE_CRAWLER": config_data["crawler"]["enable_crawler"],

            # 报告配置
            "REPORT_MODE": config_data["report"]["mode"],
            "RANK_THRESHOLD": config_data["report"]["rank_threshold"],

            # 通知配置
            "ENABLE_NOTIFICATION": config_data["notification"]["enable_notification"],
            "MESSAGE_BATCH_SIZE": config_data["notification"]["message_batch_size"],
            "DINGTALK_BATCH_SIZE": config_data["notification"].get("dingtalk_batch_size", 20000),
            "FEISHU_BATCH_SIZE": config_data["notification"].get("feishu_batch_size", 29000),
            "BATCH_SEND_INTERVAL": config_data["notification"]["batch_send_interval"],
            "FEISHU_MESSAGE_SEPARATOR": config_data["notification"]["feishu_message_separator"],

            # 推送窗口配置
            "PUSH_WINDOW": {
                "ENABLED": config_data["notification"].get("push_window", {}).get("enabled", False),
                "TIME_RANGE": {
                    "START": config_data["notification"].get("push_window", {}).get("time_range", {}).get("start", "08:00"),
                    "END": config_data["notification"].get("push_window", {}).get("time_range", {}).get("end", "22:00"),
                },
                "ONCE_PER_DAY": config_data["notification"].get("push_window", {}).get("once_per_day", True),
                "RECORD_RETENTION_DAYS": config_data["notification"].get("push_window", {}).get("push_record_retention_days", 7),
            },

            # 权重配置
            "WEIGHT_CONFIG": {
                "RANK_WEIGHT": config_data["weight"]["rank_weight"],
                "FREQUENCY_WEIGHT": config_data["weight"]["frequency_weight"],
                "HOTNESS_WEIGHT": config_data["weight"]["hotness_weight"],
            },

            # 平台配置
            "PLATFORMS": config_data["platforms"],

            # 信息源配置（新增）
            "SOURCES": config_data.get("sources", {
                "enabled": ["newsnow"],
                "newsnow": {
                    "api_url": "https://newsnow.busiyi.world/api/s",
                    "platforms": config_data["platforms"]
                }
            }),

            # 大模型配置（新增）
            "LLM_CONFIG": {
                "PROVIDER": config_data.get("llm", {}).get("provider", "openai"),
                "BASE_URL": os.environ.get("LLM_BASE_URL", config_data.get("llm", {}).get("base_url", "https://api.openai.com/v1")),
                "API_KEY": os.environ.get("LLM_API_KEY", config_data.get("llm", {}).get("api_key", "")),
                "MODEL": os.environ.get("LLM_MODEL", config_data.get("llm", {}).get("model", "gpt-4")),
                "MAX_TOKENS": int(os.environ.get("LLM_MAX_TOKENS", config_data.get("llm", {}).get("max_tokens", 2000))),
                "TEMPERATURE": float(os.environ.get("LLM_TEMPERATURE", config_data.get("llm", {}).get("temperature", 0.7))),
                "TIMEOUT": int(os.environ.get("LLM_TIMEOUT", config_data.get("llm", {}).get("timeout", 60))),
            },

            # 对话配置（新增）
            "CHAT_CONFIG": {
                "STORAGE_PATH": config_data.get("chat", {}).get("storage_path", "conversations"),
                "MAX_HISTORY_LENGTH": config_data.get("chat", {}).get("max_history_length", 20),
                "CONTEXT_NEWS_LIMIT": config_data.get("chat", {}).get("context_news_limit", 50),
                "ENABLE_STREAMING": config_data.get("chat", {}).get("enable_streaming", False),
            }
        }

        # 通知渠道配置（环境变量优先）
        self._load_notification_config(config, config_data.get("notification", {}))

        return config

    def _load_notification_config(self, config: Dict[str, Any], notification: Dict[str, Any]) -> None:
        """加载通知渠道配置

        Args:
            config: 配置字典
            notification: 通知配置数据
        """
        webhooks = notification.get("webhooks", {})

        # 飞书
        config["FEISHU_WEBHOOK_URL"] = (
            os.environ.get("FEISHU_WEBHOOK_URL", "").strip() or
            webhooks.get("feishu_url", "")
        )

        # 钉钉
        config["DINGTALK_WEBHOOK_URL"] = (
            os.environ.get("DINGTALK_WEBHOOK_URL", "").strip() or
            webhooks.get("dingtalk_url", "")
        )

        # 企业微信
        config["WEWORK_WEBHOOK_URL"] = (
            os.environ.get("WEWORK_WEBHOOK_URL", "").strip() or
            webhooks.get("wework_url", "")
        )

        # Telegram
        config["TELEGRAM_BOT_TOKEN"] = (
            os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or
            webhooks.get("telegram_bot_token", "")
        )
        config["TELEGRAM_CHAT_ID"] = (
            os.environ.get("TELEGRAM_CHAT_ID", "").strip() or
            webhooks.get("telegram_chat_id", "")
        )

        # 邮件
        config["EMAIL_FROM"] = (
            os.environ.get("EMAIL_FROM", "").strip() or
            webhooks.get("email_from", "")
        )
        config["EMAIL_PASSWORD"] = (
            os.environ.get("EMAIL_PASSWORD", "").strip() or
            webhooks.get("email_password", "")
        )
        config["EMAIL_TO"] = (
            os.environ.get("EMAIL_TO", "").strip() or
            webhooks.get("email_to", "")
        )
        config["EMAIL_SMTP_SERVER"] = (
            os.environ.get("EMAIL_SMTP_SERVER", "").strip() or
            webhooks.get("email_smtp_server", "")
        )
        config["EMAIL_SMTP_PORT"] = (
            os.environ.get("EMAIL_SMTP_PORT", "").strip() or
            webhooks.get("email_smtp_port", "")
        )

        # ntfy
        config["NTFY_SERVER_URL"] = (
            os.environ.get("NTFY_SERVER_URL", "https://ntfy.sh").strip() or
            webhooks.get("ntfy_server_url", "https://ntfy.sh")
        )
        config["NTFY_TOPIC"] = (
            os.environ.get("NTFY_TOPIC", "").strip() or
            webhooks.get("ntfy_topic", "")
        )
        config["NTFY_TOKEN"] = (
            os.environ.get("NTFY_TOKEN", "").strip() or
            webhooks.get("ntfy_token", "")
        )

    def _print_notification_sources(self) -> None:
        """输出通知渠道配置来源信息"""
        notification_sources = []

        if self._config["FEISHU_WEBHOOK_URL"]:
            source = "环境变量" if os.environ.get("FEISHU_WEBHOOK_URL") else "配置文件"
            notification_sources.append(f"飞书({source})")

        if self._config["DINGTALK_WEBHOOK_URL"]:
            source = "环境变量" if os.environ.get("DINGTALK_WEBHOOK_URL") else "配置文件"
            notification_sources.append(f"钉钉({source})")

        if self._config["WEWORK_WEBHOOK_URL"]:
            source = "环境变量" if os.environ.get("WEWORK_WEBHOOK_URL") else "配置文件"
            notification_sources.append(f"企业微信({source})")

        if self._config["TELEGRAM_BOT_TOKEN"] and self._config["TELEGRAM_CHAT_ID"]:
            token_source = "环境变量" if os.environ.get("TELEGRAM_BOT_TOKEN") else "配置文件"
            chat_source = "环境变量" if os.environ.get("TELEGRAM_CHAT_ID") else "配置文件"
            notification_sources.append(f"Telegram({token_source}/{chat_source})")

        if (self._config["EMAIL_FROM"] and
            self._config["EMAIL_PASSWORD"] and
            self._config["EMAIL_TO"]):
            from_source = "环境变量" if os.environ.get("EMAIL_FROM") else "配置文件"
            notification_sources.append(f"邮件({from_source})")

        if self._config["NTFY_SERVER_URL"] and self._config["NTFY_TOPIC"]:
            server_source = "环境变量" if os.environ.get("NTFY_SERVER_URL") else "配置文件"
            notification_sources.append(f"ntfy({server_source})")

        if notification_sources:
            print(f"通知渠道配置来源: {', '.join(notification_sources)}")
        else:
            print("未配置任何通知渠道")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项

        Args:
            key: 配置键名
            default: 默认值

        Returns:
            Any: 配置值
        """
        return self._config.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """通过 [] 运算符获取配置项

        Args:
            key: 配置键名

        Returns:
            Any: 配置值
        """
        return self._config[key]

    def __contains__(self, key: str) -> bool:
        """检查配置项是否存在

        Args:
            key: 配置键名

        Returns:
            bool: 是否存在
        """
        return key in self._config

    @property
    def config(self) -> Dict[str, Any]:
        """获取完整配置字典

        Returns:
            Dict: 配置字典
        """
        return self._config

    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()

    def has_notification_configured(self) -> bool:
        """检查是否配置了任何通知渠道

        Returns:
            bool: 是否配置了通知渠道
        """
        return any([
            self._config.get("FEISHU_WEBHOOK_URL"),
            self._config.get("DINGTALK_WEBHOOK_URL"),
            self._config.get("WEWORK_WEBHOOK_URL"),
            (self._config.get("TELEGRAM_BOT_TOKEN") and self._config.get("TELEGRAM_CHAT_ID")),
            (self._config.get("EMAIL_FROM") and self._config.get("EMAIL_PASSWORD") and self._config.get("EMAIL_TO")),
            (self._config.get("NTFY_SERVER_URL") and self._config.get("NTFY_TOPIC")),
        ])
