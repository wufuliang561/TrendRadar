# coding=utf-8
"""测试时间工具函数"""

from datetime import datetime
import pytest
from src.utils.time import (
    get_beijing_time,
    format_date_folder,
    format_time_filename,
    format_time_display,
    is_time_in_range,
    get_date_string,
    BEIJING_TZ
)


class TestTimeUtils:
    """测试时间工具函数"""

    def test_get_beijing_time(self):
        """测试获取北京时间"""
        beijing_time = get_beijing_time()
        assert beijing_time is not None
        assert beijing_time.tzinfo is not None
        # 检查时区名称是否正确
        assert str(beijing_time.tzinfo) in ["CST", "Asia/Shanghai"]

    def test_format_date_folder(self):
        """测试格式化日期文件夹名"""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        formatted = format_date_folder(dt)
        assert formatted == "2025年01月15日"

    def test_format_date_folder_with_no_param(self):
        """测试无参数时使用当前时间"""
        formatted = format_date_folder()
        assert "年" in formatted
        assert "月" in formatted
        assert "日" in formatted

    def test_format_time_filename(self):
        """测试格式化时间文件名"""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        formatted = format_time_filename(dt)
        assert formatted == "14时30分"

    def test_format_time_filename_with_no_param(self):
        """测试无参数时使用当前时间"""
        formatted = format_time_filename()
        assert "时" in formatted
        assert "分" in formatted

    def test_format_time_display_same_time(self):
        """测试相同时间的显示"""
        result = format_time_display("14时30分", "14时30分")
        assert result == "14时30分"

    def test_format_time_display_different_time(self):
        """测试不同时间的显示"""
        result = format_time_display("10时30分", "14时30分")
        assert result == "10时30分 ~ 14时30分"

    def test_is_time_in_range_normal(self):
        """测试时间范围检查（正常情况）"""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        assert is_time_in_range(dt, "09:00-18:00") is True
        assert is_time_in_range(dt, "15:00-18:00") is False

    def test_is_time_in_range_boundary(self):
        """测试时间范围边界"""
        dt = datetime(2025, 1, 15, 9, 0, 0)
        assert is_time_in_range(dt, "09:00-18:00") is True

        dt = datetime(2025, 1, 15, 18, 0, 0)
        assert is_time_in_range(dt, "09:00-18:00") is True

    def test_is_time_in_range_cross_day(self):
        """测试跨天时间范围"""
        dt_night = datetime(2025, 1, 15, 23, 30, 0)
        dt_morning = datetime(2025, 1, 16, 0, 30, 0)

        assert is_time_in_range(dt_night, "23:00-01:00") is True
        assert is_time_in_range(dt_morning, "23:00-01:00") is True

    def test_is_time_in_range_invalid_format(self):
        """测试无效格式时的处理"""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        # 无效格式应返回 True（不限制）
        assert is_time_in_range(dt, "invalid") is True

    def test_get_date_string_default_format(self):
        """测试获取日期字符串（默认格式）"""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        result = get_date_string(dt)
        assert result == "2025-01-15"

    def test_get_date_string_custom_format(self):
        """测试获取日期字符串（自定义格式）"""
        dt = datetime(2025, 1, 15, 14, 30, 0)
        result = get_date_string(dt, "%Y/%m/%d")
        assert result == "2025/01/15"
