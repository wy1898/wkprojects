"""轻量级压力测试历史记录存储。"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from .utils import get_logger


MAX_HISTORY = 10
_FILE_LOCK = threading.Lock()


def history_path() -> Path:
    """返回历史 JSON 文件路径，支持环境变量覆盖。"""
    configured_value = os.environ.get("GPU_PLATFORM_HISTORY_FILE", "").strip()
    if configured_value:
        configured = Path(configured_value)
        return configured if configured.is_absolute() else Path.cwd() / configured
    return Path(__file__).resolve().parents[2] / "logs" / "stress_history.json"


def format_clock(value: float | int | str | None) -> str:
    """将时间统一格式化为本地 24 小时制 HH:mm:ss。"""
    try:
        if isinstance(value, str):
            return datetime.fromisoformat(value).strftime("%H:%M:%S")
        return datetime.fromtimestamp(float(value)).strftime("%H:%M:%S")
    except (TypeError, ValueError, OSError):
        return "--:--:--"


def _read() -> list[dict[str, Any]]:
    """读取历史文件，损坏或不存在时返回空列表。"""
    path = history_path()
    if not path.exists() or path.is_dir():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data[-MAX_HISTORY:] if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError) as exc:
        get_logger("gpu-platform.history").warning("无法读取历史文件：%s", exc)
        return []


def load_history() -> list[dict[str, Any]]:
    """读取最近十次压力测试记录。"""
    with _FILE_LOCK:
        return _read()


def append_history(summary: dict[str, Any]) -> dict[str, Any] | None:
    """从压力测试摘要生成记录并原子写入 JSON 文件。"""
    if not summary or "duration_seconds" not in summary:
        return None
    record = {
        "test_time": datetime.now().isoformat(timespec="seconds"),
        "duration_seconds": float(summary.get("duration_seconds", 0)),
        "average_utilization": float(summary.get("average_utilization", 0)),
        "peak_temperature": float(summary.get("peak_temperature", 0)),
        "peak_memory": float(summary.get("peak_memory", 0)),
        "status": "WARNING" if summary.get("status") == "WARNING" else "PASS",
    }
    with _FILE_LOCK:
        path = history_path()
        records = (_read() + [record])[-MAX_HISTORY:]
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            temp_path = path.with_suffix(path.suffix + ".tmp")
            temp_path.write_text(
                json.dumps(records, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            temp_path.replace(path)
        except OSError as exc:
            get_logger("gpu-platform.history").exception("无法写入历史文件：%s", exc)
            return None
    return record
