# coding=utf-8
"""TrendRadar 主入口

重构后的入口文件，提供简洁的命令行接口
"""

import sys
import argparse
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.app import TrendRadarApp


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="TrendRadar - 热点新闻聚合与智能分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
运行模式说明:
  daily        当日汇总模式 - 汇总当天所有匹配的新闻（默认）
  current      当前榜单模式 - 只推送当前批次的新闻
  incremental  增量监控模式 - 只推送新增的新闻

示例:
  python main_new.py                    # 使用默认配置运行（daily模式）
  python main_new.py --mode current     # 当前榜单模式
  python main_new.py --mode incremental # 增量监控模式
  python main_new.py --list-sources     # 列出所有信息源
  python main_new.py --list-notifiers   # 列出所有通知渠道
  python main_new.py --config custom.yaml  # 使用自定义配置文件
        """
    )

    parser.add_argument(
        "--mode",
        choices=["daily", "current", "incremental"],
        default="daily",
        help="运行模式（默认: daily）"
    )

    parser.add_argument(
        "--config",
        default="config/config.yaml",
        help="配置文件路径（默认: config/config.yaml）"
    )

    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="列出所有可用的信息源"
    )

    parser.add_argument(
        "--list-notifiers",
        action="store_true",
        help="列出所有通知渠道配置状态"
    )

    parser.add_argument(
        "--show-config",
        action="store_true",
        help="显示配置摘要"
    )

    args = parser.parse_args()

    try:
        # 创建应用实例
        app = TrendRadarApp(config_path=args.config)

        # 处理列表命令
        if args.list_sources:
            app.list_sources()
            return 0

        if args.list_notifiers:
            app.list_notifiers()
            return 0

        if args.show_config:
            app.show_config_summary()
            return 0

        # 运行主流程
        success = app.run(mode=args.mode)

        return 0 if success else 1

    except FileNotFoundError as e:
        print(f"错误: 找不到文件 - {e}")
        return 1
    except KeyboardInterrupt:
        print("\n\n用户中断运行")
        return 130
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
