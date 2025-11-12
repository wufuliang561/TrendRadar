# coding=utf-8
"""推送记录管理模块"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

from src.utils.time import get_beijing_time


class PushRecordManager:
    """推送记录管理器

    负责：
    - 管理推送记录文件
    - 检查是否已推送
    - 清理过期记录
    - 时间窗口检查
    """

    def __init__(self, retention_days: int = 7):
        """初始化推送记录管理器

        Args:
            retention_days: 记录保留天数
        """
        self.record_dir = Path("output") / ".push_records"
        self.retention_days = retention_days
        self.ensure_record_dir()
        self.cleanup_old_records()

    def ensure_record_dir(self) -> None:
        """确保记录目录存在"""
        self.record_dir.mkdir(parents=True, exist_ok=True)

    def get_today_record_file(self) -> Path:
        """获取今天的记录文件路径

        Returns:
            Path: 记录文件路径
        """
        today = get_beijing_time().strftime("%Y%m%d")
        return self.record_dir / f"push_record_{today}.json"

    def cleanup_old_records(self) -> None:
        """清理过期的推送记录"""
        current_time = get_beijing_time()

        for record_file in self.record_dir.glob("push_record_*.json"):
            try:
                # 从文件名提取日期
                date_str = record_file.stem.replace("push_record_", "")
                file_date = datetime.strptime(date_str, "%Y%m%d")

                # 计算天数差
                days_diff = (current_time.date() - file_date.date()).days

                if days_diff > self.retention_days:
                    record_file.unlink()
                    print(f"清理过期推送记录: {record_file.name} (已保留{days_diff}天)")
            except ValueError:
                # 文件名格式不正确，跳过
                print(f"警告: 推送记录文件名格式错误: {record_file.name}")
            except Exception as e:
                print(f"清理记录文件失败 {record_file}: {e}")

    def has_pushed_today(self) -> bool:
        """检查今天是否已经推送过

        Returns:
            bool: 是否已推送
        """
        record_file = self.get_today_record_file()

        if not record_file.exists():
            return False

        try:
            with open(record_file, "r", encoding="utf-8") as f:
                record = json.load(f)
            return record.get("pushed", False)
        except Exception as e:
            print(f"读取推送记录失败: {e}")
            return False

    def record_push(self, report_type: str) -> None:
        """记录推送

        Args:
            report_type: 报告类型 (daily/current/incremental)
        """
        record_file = self.get_today_record_file()
        now = get_beijing_time()

        record = {
            "pushed": True,
            "push_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "report_type": report_type,
        }

        try:
            with open(record_file, "w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False, indent=2)
            print(f"推送记录已保存: {report_type} at {now.strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"保存推送记录失败: {e}")

    def get_push_record(self) -> Optional[dict]:
        """获取今天的推送记录

        Returns:
            Optional[dict]: 推送记录，不存在返回 None
        """
        record_file = self.get_today_record_file()

        if not record_file.exists():
            return None

        try:
            with open(record_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"读取推送记录失败: {e}")
            return None

    def is_in_time_range(self, start_time: str, end_time: str) -> bool:
        """检查当前时间是否在指定时间范围内

        Args:
            start_time: 开始时间 (HH:MM 格式)
            end_time: 结束时间 (HH:MM 格式)

        Returns:
            bool: 是否在范围内
        """
        now = get_beijing_time()
        current_time = now.strftime("%H:%M")

        # 标准化时间格式
        normalized_start = self._normalize_time(start_time)
        normalized_end = self._normalize_time(end_time)
        normalized_current = self._normalize_time(current_time)

        result = normalized_start <= normalized_current <= normalized_end

        if not result:
            print(
                f"当前时间 {normalized_current} 不在推送窗口 "
                f"[{normalized_start} - {normalized_end}] 内，跳过推送"
            )

        return result

    def _normalize_time(self, time_str: str) -> str:
        """将时间字符串标准化为 HH:MM 格式

        Args:
            time_str: 时间字符串

        Returns:
            str: 标准化后的时间字符串

        Raises:
            ValueError: 时间格式错误
        """
        try:
            parts = time_str.strip().split(":")
            if len(parts) != 2:
                raise ValueError(f"时间格式错误: {time_str}，应为 HH:MM 格式")

            hour = int(parts[0])
            minute = int(parts[1])

            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError(
                    f"时间范围错误: {time_str}，小时应在 0-23，分钟应在 0-59"
                )

            return f"{hour:02d}:{minute:02d}"
        except ValueError as e:
            print(f"时间格式化错误 '{time_str}': {e}")
            # 返回原字符串，让比较失败
            return time_str

    def clear_today_record(self) -> None:
        """清除今天的推送记录（用于测试）"""
        record_file = self.get_today_record_file()
        if record_file.exists():
            record_file.unlink()
            print(f"已清除今天的推送记录")

    def get_record_count(self) -> int:
        """获取记录文件数量

        Returns:
            int: 记录文件数量
        """
        return len(list(self.record_dir.glob("push_record_*.json")))
