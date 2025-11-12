# coding=utf-8
"""仪表盘 API 路由

提供对 output 目录下 JSON 数据的访问接口
"""

from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from typing import Optional

from src.api.models.schemas import APIResponse


router = APIRouter(tags=["仪表盘"])


def get_json_file_path(date: str, filename: str) -> Path:
    """获取 JSON 文件路径

    Args:
        date: 日期 (YYYY-MM-DD)
        filename: 文件名 (news_summary.json 或 news_incremental.json)

    Returns:
        Path: JSON 文件路径
    """
    project_root = Path(__file__).parent.parent.parent.parent
    json_path = project_root / "output" / date / "json" / filename
    return json_path


def read_json_file(file_path: Path) -> dict:
    """读取 JSON 文件

    Args:
        file_path: 文件路径

    Returns:
        dict: JSON 数据

    Raises:
        HTTPException: 文件不存在或读取失败
    """
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"数据文件不存在: {file_path.name}"
        )

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"JSON 解析失败: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"文件读取失败: {str(e)}"
        )


@router.get("/dashboard/summary", response_model=APIResponse, summary="获取汇总数据")
async def get_dashboard_summary(date: str):
    """
    获取指定日期的汇总数据

    - **date**: 日期 (格式: YYYY-MM-DD, 如: 2025-11-12)

    返回 news_summary.json 的完整内容，包含当天所有批次的历史数据。

    数据结构:
    - metadata: 元数据 (日期、总批次数、总新闻数、最后更新时间)
    - batches: 批次列表，每个批次包含:
        - batch_id: 批次ID (如 "16时32分")
        - timestamp: 时间戳
        - total_news_count: 该批次新闻总数
        - stats: 关键词统计列表
    """
    file_path = get_json_file_path(date, "news_summary.json")
    data = read_json_file(file_path)

    return APIResponse(
        success=True,
        data=data,
        message=f"成功获取 {date} 的汇总数据"
    )


@router.get("/dashboard/incremental", response_model=APIResponse, summary="获取增量数据")
async def get_dashboard_incremental(date: str):
    """
    获取指定日期的增量数据

    - **date**: 日期 (格式: YYYY-MM-DD, 如: 2025-11-12)

    返回 news_incremental.json 的完整内容，包含最新批次的增量新闻。

    数据结构:
    - metadata: 元数据 (日期、批次ID、时间戳、新增新闻数)
    - stats: 关键词统计列表 (仅包含新增的新闻)
    """
    file_path = get_json_file_path(date, "news_incremental.json")
    data = read_json_file(file_path)

    return APIResponse(
        success=True,
        data=data,
        message=f"成功获取 {date} 的增量数据"
    )


@router.get("/dashboard/available-dates", response_model=APIResponse, summary="获取可用日期列表")
async def get_available_dates(limit: Optional[int] = 30):
    """
    获取 output 目录下所有可用的数据日期

    - **limit**: 返回的日期数量限制 (默认 30)

    返回按日期倒序排列的日期列表，方便前端选择。
    """
    project_root = Path(__file__).parent.parent.parent.parent
    output_dir = project_root / "output"

    if not output_dir.exists():
        return APIResponse(
            success=True,
            data=[],
            message="output 目录不存在"
        )

    # 获取所有日期目录 (格式: YYYY-MM-DD)
    date_dirs = []
    for item in output_dir.iterdir():
        if item.is_dir() and len(item.name) == 10:  # YYYY-MM-DD 长度为 10
            # 检查是否包含 json 子目录
            json_dir = item / "json"
            if json_dir.exists() and json_dir.is_dir():
                date_dirs.append(item.name)

    # 倒序排列 (最新日期在前)
    date_dirs.sort(reverse=True)

    # 限制数量
    if limit:
        date_dirs = date_dirs[:limit]

    return APIResponse(
        success=True,
        data={
            "dates": date_dirs,
            "total": len(date_dirs)
        },
        message=f"找到 {len(date_dirs)} 个可用日期"
    )
