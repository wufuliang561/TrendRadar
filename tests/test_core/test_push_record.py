# coding=utf-8
"""测试推送记录管理模块"""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from src.core.push_record import PushRecordManager


@pytest.fixture
def temp_output_dir(tmp_path):
    """创建临时output目录"""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def record_manager(temp_output_dir, monkeypatch):
    """创建推送记录管理器"""
    monkeypatch.chdir(temp_output_dir.parent)
    return PushRecordManager(retention_days=7)


class TestPushRecordManager:
    """测试 PushRecordManager 类"""

    def test_initialization(self, record_manager):
        """测试初始化"""
        assert record_manager.record_dir.exists()
        assert record_manager.retention_days == 7

    def test_ensure_record_dir(self, record_manager):
        """测试确保记录目录存在"""
        # 删除目录
        record_manager.record_dir.rmdir()
        assert not record_manager.record_dir.exists()

        # 重新创建
        record_manager.ensure_record_dir()
        assert record_manager.record_dir.exists()

    def test_get_today_record_file(self, record_manager):
        """测试获取今天的记录文件路径"""
        from src.utils.time import get_beijing_time

        record_file = record_manager.get_today_record_file()

        # 检查文件名格式
        today = get_beijing_time().strftime("%Y%m%d")
        expected_name = f"push_record_{today}.json"
        assert record_file.name == expected_name
        assert record_file.parent == record_manager.record_dir

    def test_has_pushed_today_no_record(self, record_manager):
        """测试检查推送记录（无记录）"""
        assert record_manager.has_pushed_today() is False

    def test_has_pushed_today_with_record(self, record_manager):
        """测试检查推送记录（有记录）"""
        # 创建推送记录
        record_manager.record_push("daily")

        # 检查
        assert record_manager.has_pushed_today() is True

    def test_record_push(self, record_manager):
        """测试记录推送"""
        record_manager.record_push("daily")

        # 检查文件是否创建
        record_file = record_manager.get_today_record_file()
        assert record_file.exists()

        # 检查文件内容
        with open(record_file, "r", encoding="utf-8") as f:
            record = json.load(f)

        assert record["pushed"] is True
        assert record["report_type"] == "daily"
        assert "push_time" in record

    def test_get_push_record(self, record_manager):
        """测试获取推送记录"""
        # 无记录时
        assert record_manager.get_push_record() is None

        # 有记录时
        record_manager.record_push("current")
        record = record_manager.get_push_record()

        assert record is not None
        assert record["pushed"] is True
        assert record["report_type"] == "current"

    def test_cleanup_old_records(self, record_manager):
        """测试清理过期记录"""
        from src.utils.time import get_beijing_time

        # 创建一些过期的记录文件
        old_date1 = (get_beijing_time() - timedelta(days=10)).strftime("%Y%m%d")
        old_date2 = (get_beijing_time() - timedelta(days=5)).strftime("%Y%m%d")
        today = get_beijing_time().strftime("%Y%m%d")

        old_file1 = record_manager.record_dir / f"push_record_{old_date1}.json"
        old_file2 = record_manager.record_dir / f"push_record_{old_date2}.json"
        today_file = record_manager.record_dir / f"push_record_{today}.json"

        # 写入文件
        for file in [old_file1, old_file2, today_file]:
            with open(file, "w", encoding="utf-8") as f:
                json.dump({"pushed": True}, f)

        # 清理
        record_manager.cleanup_old_records()

        # 检查结果（保留天数为7）
        assert not old_file1.exists()  # 10天前，应该被清理
        assert old_file2.exists()      # 5天前，应该保留
        assert today_file.exists()     # 今天，应该保留

    def test_is_in_time_range(self, record_manager, monkeypatch):
        """测试时间范围检查"""
        from src.utils.time import get_beijing_time
        import pytz

        # 模拟当前时间为 10:30
        mock_time = datetime(2025, 11, 12, 10, 30, 0)
        mock_time = pytz.timezone("Asia/Shanghai").localize(mock_time)

        def mock_get_beijing_time():
            return mock_time

        monkeypatch.setattr("src.core.push_record.get_beijing_time", mock_get_beijing_time)

        # 在范围内
        assert record_manager.is_in_time_range("09:00", "12:00") is True
        assert record_manager.is_in_time_range("10:00", "11:00") is True
        assert record_manager.is_in_time_range("10:30", "10:30") is True

        # 不在范围内
        assert record_manager.is_in_time_range("08:00", "09:00") is False
        assert record_manager.is_in_time_range("12:00", "18:00") is False
        assert record_manager.is_in_time_range("10:31", "12:00") is False

    def test_normalize_time(self, record_manager):
        """测试时间标准化"""
        # 正常格式
        assert record_manager._normalize_time("9:0") == "09:00"
        assert record_manager._normalize_time("09:00") == "09:00"
        assert record_manager._normalize_time("23:59") == "23:59"

        # 错误格式（返回原字符串）
        assert record_manager._normalize_time("9") == "9"
        assert record_manager._normalize_time("25:00") == "25:00"
        assert record_manager._normalize_time("12:60") == "12:60"
        assert record_manager._normalize_time("abc") == "abc"

    def test_clear_today_record(self, record_manager):
        """测试清除今天的记录"""
        # 创建记录
        record_manager.record_push("daily")
        assert record_manager.has_pushed_today() is True

        # 清除记录
        record_manager.clear_today_record()
        assert record_manager.has_pushed_today() is False

    def test_get_record_count(self, record_manager):
        """测试获取记录数量"""
        from src.utils.time import get_beijing_time

        # 初始为0
        assert record_manager.get_record_count() == 0

        # 创建今天的记录
        record_manager.record_push("daily")
        assert record_manager.get_record_count() == 1

        # 创建昨天的记录
        yesterday = (get_beijing_time() - timedelta(days=1)).strftime("%Y%m%d")
        yesterday_file = record_manager.record_dir / f"push_record_{yesterday}.json"
        with open(yesterday_file, "w", encoding="utf-8") as f:
            json.dump({"pushed": True}, f)

        assert record_manager.get_record_count() == 2

    def test_invalid_record_file(self, record_manager):
        """测试处理损坏的记录文件"""
        record_file = record_manager.get_today_record_file()

        # 写入无效的JSON
        with open(record_file, "w", encoding="utf-8") as f:
            f.write("invalid json{")

        # 应该返回False而不是抛出异常
        assert record_manager.has_pushed_today() is False
        assert record_manager.get_push_record() is None

    def test_record_push_multiple_types(self, record_manager):
        """测试记录不同类型的推送"""
        # 第一次推送
        record_manager.record_push("daily")
        record = record_manager.get_push_record()
        assert record["report_type"] == "daily"

        # 第二次推送（会覆盖）
        record_manager.record_push("current")
        record = record_manager.get_push_record()
        assert record["report_type"] == "current"

    def test_cleanup_invalid_filename(self, record_manager):
        """测试清理时忽略无效文件名"""
        # 创建一个格式错误的文件
        invalid_file = record_manager.record_dir / "push_record_invalid.json"
        with open(invalid_file, "w", encoding="utf-8") as f:
            json.dump({"pushed": True}, f)

        # 清理不应该崩溃
        record_manager.cleanup_old_records()

        # 文件应该仍然存在（被跳过）
        assert invalid_file.exists()
