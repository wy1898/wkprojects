"""统一的终端输出模块。

业务模块只需要传入消息或结构化数据，颜色、标题和表格样式都在这里维护。
Rich 是可选依赖；导入失败时自动使用普通文本输出，保证核心功能仍可运行。
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:  # Rich 未安装时保留纯文本降级路径
    Console = None  # type: ignore[assignment,misc]
    Table = None  # type: ignore[assignment,misc]


# 颜色和 Console 实例集中定义，业务代码不应自行处理终端样式。
_console = Console() if Console else None
_COLORS = {"success": "green", "warning": "yellow", "error": "red", "info": "cyan"}


def _message(message: Any, level: str = "info") -> None:
    """输出带统一颜色的消息，或在 Rich 不可用时输出普通文本。"""
    text = str(message)
    if _console:
        _console.print(text, style=_COLORS.get(level, "white"))
    else:
        print(text)


def _rows(data: Any) -> list[tuple[str, str]]:
    """把常见的字典、字典列表和键值序列转换为表格行。"""
    if isinstance(data, Mapping):
        return [(str(key), str(value)) for key, value in data.items()]
    if isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
        rows: list[tuple[str, str]] = []
        for index, item in enumerate(data, 1):
            if isinstance(item, Mapping):
                rows.extend((str(key), str(value)) for key, value in item.items())
            elif isinstance(item, Sequence) and len(item) >= 2:
                rows.append((str(item[0]), str(item[1])))
            else:
                rows.append((str(index), str(item)))
        return rows
    return [("value", str(data))]


def _table(title: str, data: Any) -> None:
    """渲染两列表格；无 Rich 时使用对齐的普通文本。"""
    rows = _rows(data)
    if _console and Table:
        table = Table(title=title, header_style="bold magenta", border_style="blue")
        table.add_column("项目", style="cyan")
        table.add_column("值", style="white")
        for key, value in rows:
            table.add_row(key, value)
        _console.print(table)
        return
    print(title)
    for key, value in rows:
        print(f"{key}: {value}")


def print_header(title: str) -> None:
    """打印统一样式的章节标题。"""
    if _console:
        _console.rule(f"[bold blue]{title}[/bold blue]")
    else:
        print(f"=== {title} ===")


def print_success(message: str) -> None:
    """打印成功消息。"""
    _message(message, "success")


def print_warning(message: str) -> None:
    """打印警告消息。"""
    _message(message, "warning")


def print_error(message: str) -> None:
    """打印错误消息。"""
    _message(message, "error")


def print_info(message: str) -> None:
    """打印普通信息消息。"""
    _message(message, "info")


def print_gpu_table(gpu_info: Any) -> None:
    """打印 GPU 信息表格。"""
    _table("GPU 信息", gpu_info)


def print_env_table(environment_info: Any) -> None:
    """打印运行环境信息表格。"""
    _table("运行环境", environment_info)


def print_monitor_status(status: Any) -> None:
    """打印监控状态。"""
    _table("GPU 监控状态", status)


def print_stress_summary(summary: Any) -> None:
    """打印压力测试摘要。"""
    print_header("GPU 压力测试摘要")
    if isinstance(summary, (Mapping, Sequence)) and not isinstance(summary, (str, bytes)):
        _table("测试结果", summary)
    else:
        print_info(summary)
