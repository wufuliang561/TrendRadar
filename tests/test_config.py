# coding=utf-8
"""测试配置管理"""

import os
import tempfile
from pathlib import Path
import pytest
import yaml
from src.core.config import ConfigManager


@pytest.fixture
def sample_config():
    """示例配置数据"""
    return {
        "app": {
            "version_check_url": "https://example.com/version",
            "show_version_update": True
        },
        "crawler": {
            "request_interval": 1000,
            "use_proxy": False,
            "default_proxy": "",
            "enable_crawler": True
        },
        "report": {
            "mode": "daily",
            "rank_threshold": 10
        },
        "notification": {
            "enable_notification": True,
            "message_batch_size": 4000,
            "dingtalk_batch_size": 20000,
            "feishu_batch_size": 29000,
            "batch_send_interval": 2,
            "feishu_message_separator": "---",
            "push_window": {
                "enabled": False,
                "time_range": {
                    "start": "08:00",
                    "end": "22:00"
                },
                "once_per_day": True,
                "push_record_retention_days": 7
            },
            "webhooks": {
                "feishu_url": "",
                "dingtalk_url": "",
                "wework_url": "",
                "telegram_bot_token": "",
                "telegram_chat_id": "",
                "email_from": "",
                "email_password": "",
                "email_to": "",
                "email_smtp_server": "",
                "email_smtp_port": "",
                "ntfy_server_url": "https://ntfy.sh",
                "ntfy_topic": "",
                "ntfy_token": ""
            }
        },
        "weight": {
            "rank_weight": 0.6,
            "frequency_weight": 0.3,
            "hotness_weight": 0.1
        },
        "platforms": [
            {"id": "zhihu", "name": "知乎"},
            {"id": "weibo", "name": "微博"}
        ]
    }


@pytest.fixture
def config_file(tmp_path, sample_config):
    """创建临时配置文件"""
    config_path = tmp_path / "config.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(sample_config, f, allow_unicode=True)
    return str(config_path)


class TestConfigManager:
    """测试 ConfigManager 类"""

    def test_load_config_success(self, config_file):
        """测试成功加载配置"""
        config_manager = ConfigManager(config_file)
        assert config_manager.config is not None
        assert config_manager["VERSION_CHECK_URL"] == "https://example.com/version"
        assert config_manager["REQUEST_INTERVAL"] == 1000
        assert config_manager["REPORT_MODE"] == "daily"

    def test_load_config_file_not_found(self):
        """测试配置文件不存在"""
        with pytest.raises(FileNotFoundError):
            ConfigManager("not_exists.yaml")

    def test_config_get_method(self, config_file):
        """测试 get 方法"""
        config_manager = ConfigManager(config_file)
        assert config_manager.get("REQUEST_INTERVAL") == 1000
        assert config_manager.get("NOT_EXISTS", "default") == "default"

    def test_config_contains(self, config_file):
        """测试 in 运算符"""
        config_manager = ConfigManager(config_file)
        assert "REQUEST_INTERVAL" in config_manager
        assert "NOT_EXISTS" not in config_manager

    def test_config_getitem(self, config_file):
        """测试 [] 运算符"""
        config_manager = ConfigManager(config_file)
        assert config_manager["REQUEST_INTERVAL"] == 1000

        with pytest.raises(KeyError):
            _ = config_manager["NOT_EXISTS"]

    def test_weight_config(self, config_file):
        """测试权重配置"""
        config_manager = ConfigManager(config_file)
        weight_config = config_manager["WEIGHT_CONFIG"]
        assert weight_config["RANK_WEIGHT"] == 0.6
        assert weight_config["FREQUENCY_WEIGHT"] == 0.3
        assert weight_config["HOTNESS_WEIGHT"] == 0.1

    def test_platforms_config(self, config_file):
        """测试平台配置"""
        config_manager = ConfigManager(config_file)
        platforms = config_manager["PLATFORMS"]
        assert len(platforms) == 2
        assert platforms[0]["id"] == "zhihu"
        assert platforms[1]["id"] == "weibo"

    def test_push_window_config(self, config_file):
        """测试推送窗口配置"""
        config_manager = ConfigManager(config_file)
        push_window = config_manager["PUSH_WINDOW"]
        assert push_window["ENABLED"] is False
        assert push_window["TIME_RANGE"]["START"] == "08:00"
        assert push_window["TIME_RANGE"]["END"] == "22:00"
        assert push_window["ONCE_PER_DAY"] is True

    def test_notification_config_from_env(self, config_file, monkeypatch):
        """测试从环境变量加载通知配置"""
        # 设置环境变量
        monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://feishu.webhook.url")
        monkeypatch.setenv("DINGTALK_WEBHOOK_URL", "https://dingtalk.webhook.url")
        monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot_token_123")
        monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat_id_456")

        config_manager = ConfigManager(config_file)

        assert config_manager["FEISHU_WEBHOOK_URL"] == "https://feishu.webhook.url"
        assert config_manager["DINGTALK_WEBHOOK_URL"] == "https://dingtalk.webhook.url"
        assert config_manager["TELEGRAM_BOT_TOKEN"] == "bot_token_123"
        assert config_manager["TELEGRAM_CHAT_ID"] == "chat_id_456"

    def test_has_notification_configured_false(self, config_file):
        """测试未配置通知渠道"""
        config_manager = ConfigManager(config_file)
        assert config_manager.has_notification_configured() is False

    def test_has_notification_configured_true(self, config_file, monkeypatch):
        """测试已配置通知渠道"""
        monkeypatch.setenv("FEISHU_WEBHOOK_URL", "https://feishu.webhook.url")

        config_manager = ConfigManager(config_file)
        assert config_manager.has_notification_configured() is True

    def test_config_path_from_env(self, tmp_path, sample_config, monkeypatch):
        """测试从环境变量读取配置路径"""
        config_path = tmp_path / "custom_config.yaml"
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(sample_config, f, allow_unicode=True)

        monkeypatch.setenv("CONFIG_PATH", str(config_path))

        config_manager = ConfigManager()
        assert config_manager.config_path == str(config_path)
