# coding=utf-8
"""时间处理工具函数"""

from datetime import datetime
from typing import Optional
import pytz


# 北京时区
BEIJING_TZ = pytz.timezone("Asia/Shanghai")


def get_beijing_time() -> datetime:
    """获取北京时区的当前时间

    Returns:
        datetime: 北京时间的 datetime 对象
    """
    return datetime.now(BEIJING_TZ)


def format_date_folder(dt: Optional[datetime] = None) -> str:
    """格式化日期为文件夹名称

    Args:
        dt: datetime 对象，如果为 None 则使用当前北京时间

    Returns:
        str: 格式化后的日期字符串，如 "2025年01月15日"
    """
    if dt is None:
        dt = get_beijing_time()
    return dt.strftime("%Y-%m-%d")


def format_time_filename(dt: Optional[datetime] = None) -> str:
    """格式化时间为文件名

    Args:
        dt: datetime 对象，如果为 None 则使用当前北京时间

    Returns:
        str: 格式化后的时间字符串，如 "14时30分"
    """
    if dt is None:
        dt = get_beijing_time()
    return dt.strftime("%H:%M")


def format_time_display(first_time: str, last_time: str) -> str:
    """格式化时间范围显示

    Args:
        first_time: 首次出现时间（格式：HH时MM分）
        last_time: 最后出现时间（格式：HH时MM分）

    Returns:
        str: 格式化后的时间范围字符串
            - 相同时间：返回单个时间，如 "14时30分"
            - 不同时间：返回范围，如 "10时30分 ~ 14时30分"
    """
    if first_time == last_time:
        return first_time
    return f"{first_time} ~ {last_time}"


def is_time_in_range(
    current_time: datetime,
    time_range: str
) -> bool:
    """检查当前时间是否在指定时间范围内

    Args:
        current_time: 当前时间
        time_range: 时间范围字符串，格式 "HH:MM-HH:MM"（如 "09:00-18:00"）

    Returns:
        bool: 是否在范围内
    """
    try:
        start_str, end_str = time_range.split("-")
        start_hour, start_minute = map(int, start_str.split(":"))
        end_hour, end_minute = map(int, end_str.split(":"))

        current_minutes = current_time.hour * 60 + current_time.minute
        start_minutes = start_hour * 60 + start_minute
        end_minutes = end_hour * 60 + end_minute

        # 处理跨天的情况（如 23:00-01:00）
        if end_minutes < start_minutes:
            return current_minutes >= start_minutes or current_minutes <= end_minutes
        else:
            return start_minutes <= current_minutes <= end_minutes

    except (ValueError, AttributeError):
        # 解析失败，默认返回 True（不限制）
        return True


def get_date_string(dt: Optional[datetime] = None, format: str = "%Y-%m-%d") -> str:
    """获取日期字符串

    Args:
        dt: datetime 对象，如果为 None 则使用当前北京时间
        format: 日期格式字符串（默认 "%Y-%m-%d"）

    Returns:
        str: 格式化后的日期字符串
    """
    if dt is None:
        dt = get_beijing_time()
    return dt.strftime(format)


def parse_time_from_filename(filename: str) -> Optional[str]:
    """从文件名中解析时间

    Args:
        filename: 文件名，如 "news_2025-01-15.txt" 或 "14时30分.txt"

    Returns:
        Optional[str]: 解析出的时间字符串，失败返回 None
    """
    try:
        # 提取时间部分（HH时MM分）
        if "时" in filename and "分" in filename:
            time_part = filename.split(".")[0]  # 去除扩展名
            return time_part
        return None
    except Exception:
        return None
