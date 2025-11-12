# coding=utf-8
"""文件操作工具函数"""

import re
from pathlib import Path
from typing import Optional


def ensure_directory_exists(directory: str) -> None:
    """确保目录存在，如果不存在则创建

    Args:
        directory: 目录路径
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_output_path(
    base_dir: str,
    date_folder: str,
    filename: str
) -> str:
    """获取输出文件的完整路径

    Args:
        base_dir: 基础目录（如 "output"）
        date_folder: 日期文件夹名称（如 "2025年01月15日"）
        filename: 文件名（如 "14时30分.txt"）

    Returns:
        str: 完整文件路径
    """
    full_dir = Path(base_dir) / date_folder
    ensure_directory_exists(str(full_dir))
    return str(full_dir / filename)


def clean_title(title: str) -> str:
    """清理标题中的换行符和多余空格

    Args:
        title: 原始标题字符串

    Returns:
        str: 清理后的标题
    """
    # 移除所有换行符和回车符
    cleaned = re.sub(r"[\n\r]+", " ", title)
    # 移除多余空格
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def html_escape(text: str) -> str:
    """HTML 转义函数

    Args:
        text: 原始文本

    Returns:
        str: 转义后的文本
    """
    if not text:
        return ""

    replacements = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
        "/": "&#x2F;",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return text


def get_file_list(directory: str, pattern: str = "*") -> list:
    """获取目录下的文件列表

    Args:
        directory: 目录路径
        pattern: 文件匹配模式（默认 "*" 匹配所有文件）

    Returns:
        list: 文件路径列表（按修改时间排序）
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        return []

    files = list(dir_path.glob(pattern))
    # 按修改时间排序
    files.sort(key=lambda f: f.stat().st_mtime)
    return [str(f) for f in files]


def read_file(file_path: str, encoding: str = "utf-8") -> Optional[str]:
    """读取文件内容

    Args:
        file_path: 文件路径
        encoding: 文件编码（默认 UTF-8）

    Returns:
        Optional[str]: 文件内容，读取失败返回 None
    """
    try:
        with open(file_path, "r", encoding=encoding) as f:
            return f.read()
    except Exception as e:
        print(f"读取文件失败 {file_path}: {e}")
        return None


def write_file(file_path: str, content: str, encoding: str = "utf-8") -> bool:
    """写入文件内容

    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码（默认 UTF-8）

    Returns:
        bool: 是否写入成功
    """
    try:
        # 确保目录存在
        ensure_directory_exists(str(Path(file_path).parent))

        with open(file_path, "w", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"写入文件失败 {file_path}: {e}")
        return False


def append_file(file_path: str, content: str, encoding: str = "utf-8") -> bool:
    """追加内容到文件

    Args:
        file_path: 文件路径
        content: 要追加的内容
        encoding: 文件编码（默认 UTF-8）

    Returns:
        bool: 是否追加成功
    """
    try:
        # 确保目录存在
        ensure_directory_exists(str(Path(file_path).parent))

        with open(file_path, "a", encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"追加文件失败 {file_path}: {e}")
        return False
