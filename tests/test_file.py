# coding=utf-8
"""测试文件工具函数"""

import os
import tempfile
from pathlib import Path
import pytest
from src.utils.file import (
    ensure_directory_exists,
    get_output_path,
    clean_title,
    html_escape,
    read_file,
    write_file,
    append_file
)


class TestFileUtils:
    """测试文件工具函数"""

    def test_ensure_directory_exists(self, tmp_path):
        """测试确保目录存在"""
        test_dir = tmp_path / "test" / "nested" / "dir"
        ensure_directory_exists(str(test_dir))
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_directory_exists_already_exists(self, tmp_path):
        """测试目录已存在的情况"""
        test_dir = tmp_path / "existing"
        test_dir.mkdir()
        # 不应抛出异常
        ensure_directory_exists(str(test_dir))
        assert test_dir.exists()

    def test_get_output_path(self, tmp_path):
        """测试获取输出路径"""
        base_dir = str(tmp_path)
        date_folder = "2025年01月15日"
        filename = "14时30分.txt"

        path = get_output_path(base_dir, date_folder, filename)
        assert date_folder in path
        assert filename in path
        # 目录应自动创建
        assert Path(path).parent.exists()

    def test_clean_title_with_newlines(self):
        """测试清理带换行符的标题"""
        title = "这是一个\n多行\r\n标题"
        cleaned = clean_title(title)
        assert "\n" not in cleaned
        assert "\r" not in cleaned
        assert cleaned == "这是一个 多行 标题"

    def test_clean_title_with_multiple_spaces(self):
        """测试清理多余空格"""
        title = "这是   一个   标题"
        cleaned = clean_title(title)
        assert cleaned == "这是 一个 标题"

    def test_clean_title_with_leading_trailing_spaces(self):
        """测试清理首尾空格"""
        title = "  标题  "
        cleaned = clean_title(title)
        assert cleaned == "标题"

    def test_html_escape(self):
        """测试 HTML 转义"""
        text = '<script>alert("XSS")</script>'
        escaped = html_escape(text)
        assert "&lt;" in escaped
        assert "&gt;" in escaped
        assert "&quot;" in escaped
        assert "<script>" not in escaped

    def test_html_escape_with_special_chars(self):
        """测试特殊字符转义"""
        text = "A & B < C > D \"E\" 'F' /G"
        escaped = html_escape(text)
        assert "&amp;" in escaped
        assert "&lt;" in escaped
        assert "&gt;" in escaped
        assert "&quot;" in escaped
        assert "&#x27;" in escaped
        assert "&#x2F;" in escaped

    def test_html_escape_empty_string(self):
        """测试空字符串"""
        assert html_escape("") == ""
        assert html_escape(None) == ""

    def test_write_and_read_file(self, tmp_path):
        """测试写入和读取文件"""
        file_path = tmp_path / "test.txt"
        content = "测试内容\n第二行"

        # 写入
        assert write_file(str(file_path), content) is True
        assert file_path.exists()

        # 读取
        read_content = read_file(str(file_path))
        assert read_content == content

    def test_write_file_creates_directory(self, tmp_path):
        """测试写入文件时自动创建目录"""
        file_path = tmp_path / "nested" / "dir" / "test.txt"
        assert write_file(str(file_path), "content") is True
        assert file_path.exists()

    def test_append_file(self, tmp_path):
        """测试追加文件内容"""
        file_path = tmp_path / "test.txt"

        # 写入初始内容
        write_file(str(file_path), "第一行\n")

        # 追加内容
        assert append_file(str(file_path), "第二行\n") is True

        # 读取验证
        content = read_file(str(file_path))
        assert content == "第一行\n第二行\n"

    def test_read_file_not_exists(self, tmp_path):
        """测试读取不存在的文件"""
        file_path = tmp_path / "not_exists.txt"
        content = read_file(str(file_path))
        assert content is None
