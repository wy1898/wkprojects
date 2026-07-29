"""GPU 平台命令行入口。"""

import argparse

from .gpu import run_env, run_info
from .monitor import run_monitor
from .stress import run_stress


def build_parser() -> argparse.ArgumentParser:
    """创建统一的命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="gpu-platform",
        description="GPU 计算环境部署与压力测试平台",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    # 信息和环境命令不需要额外参数。
    subparsers.add_parser("info", help="查看 GPU 信息")
    subparsers.add_parser("env", help="检查 GPU 计算环境")

    # 实时监控参数直接映射到 monitor.run_monitor。 
    monitor_parser = subparsers.add_parser("monitor", help="实时监控 GPU 状态")
    monitor_parser.add_argument(
        "--device", type=int, default=0, help="GPU 编号（默认：0）"
    )
    monitor_parser.add_argument(
        "--interval", type=float, default=1, help="刷新间隔，单位秒（默认：1）"
    )

    # 压力测试参数直接映射到 stress.run_stress。
    stress_parser = subparsers.add_parser("stress", help="执行 GPU 压力测试")
    stress_parser.add_argument(
        "--device", type=int, default=0, help="GPU 编号（默认：0）"
    )
    stress_parser.add_argument(
        "--duration", type=float, default=60, help="测试时长，单位秒（默认：60）"
    )
    stress_parser.add_argument(
        "--size", type=int, default=2048, help="矩阵规模（默认：2048）"
    )
    stress_parser.add_argument(
        "--interval", type=float, default=1, help="状态刷新间隔，单位秒（默认：1）"
    )

    # Web Dashboard 使用惰性导入，Flask 缺失时不影响原有 CLI 命令。
    web_parser = subparsers.add_parser("web", help="启动 Web Dashboard")
    web_parser.add_argument("--host", default="127.0.0.1", help="监听地址（默认：127.0.0.1）")
    web_parser.add_argument("--port", type=int, default=5000, help="监听端口（默认：5000）")
    web_parser.add_argument("--device", type=int, default=0, help="GPU 编号（默认：0）")

    return parser


def main() -> None:
    """解析命令行参数并调用对应业务模块。"""
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "info":
        run_info()
    elif args.command == "env":
        run_env()
    elif args.command == "monitor":
        run_monitor(interval=args.interval, device=args.device)
    elif args.command == "stress":
        run_stress(
            device=args.device,
            duration=args.duration,
            size=args.size,
            interval=args.interval,
        )
    elif args.command == "web":
        try:
            from .web import run_web
        except ImportError as exc:
            from .output import print_error

            print_error(f"Web Dashboard 依赖未安装，请先安装 Flask：{exc}")
            return

        run_web(host=args.host, port=args.port, device=args.device)
    else:
        # 没有子命令时显示帮助，方便首次使用。
        parser.print_help()
