"""V2 共用工具：GPU 数据采集、日志和终端辅助函数。"""

from __future__ import annotations

import csv
import logging
import os
import re
import shutil
import subprocess
import time
from functools import lru_cache
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from . import gpu


GPU_QUERY = (
    "index,name,driver_version,memory.total,memory.used,"
    "utilization.gpu,temperature.gpu,power.draw"
)


class GpuQueryError(RuntimeError):
    """表示 nvidia-smi 不可用、设备无效或返回数据损坏。"""


def _to_float(value: str) -> float | None:
    """将 nvidia-smi 的数值字段转换为浮点数。"""
    try:
        return float(value.strip().replace("%", "").replace("W", ""))
    except (AttributeError, ValueError):
        return None


def _query_error(device: int, detail: str) -> GpuQueryError:
    """根据 nvidia-smi 错误文本生成统一异常。"""
    lowered = detail.lower()
    if "not found" in lowered:
        return GpuQueryError("nvidia-smi 未找到，请确认 NVIDIA 驱动已安装")
    if re.search(r"invalid|not exist|no.*gpu|no devices", lowered):
        return GpuQueryError(f"GPU 编号 {device} 不存在：{detail}")
    return GpuQueryError(f"读取 GPU 信息失败：{detail}")


def read_gpu_metrics(device: int = 0) -> dict[str, Any]:
    """读取一份适合 CLI、Web 和告警模块复用的 GPU 快照。"""
    output, error = gpu._run_nvidia_smi(
        f"--id={device}",
        f"--query-gpu={GPU_QUERY}",
        "--format=csv,noheader,nounits",
    )
    if output is None:
        raise _query_error(device, error or "nvidia-smi 未返回数据")

    rows = list(csv.reader(output.splitlines(), skipinitialspace=True))
    if not rows or len(rows[0]) != 8:
        raise GpuQueryError("nvidia-smi 返回的 CSV 数据格式无效")

    values = [value.strip() for value in rows[0]]
    return {
        "index": int(values[0]) if values[0].isdigit() else device,
        "name": values[1],
        "driver_version": values[2],
        "memory_total_mib": _to_float(values[3]),
        "memory_used_mib": _to_float(values[4]),
        "utilization_percent": _to_float(values[5]),
        "temperature_c": _to_float(values[6]),
        "power_draw_w": _to_float(values[7]),
        "cuda_version": read_cuda_version(),
        "timestamp": time.time(),
    }


@lru_cache(maxsize=1)
def read_cuda_version() -> str | None:
    """读取驱动报告的 CUDA 版本，失败时返回 None。"""
    executable = shutil.which("nvidia-smi")
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = re.search(r"CUDA Version\s*:\s*([\w.]+)", result.stdout)
    return match.group(1) if match else None


def clear_screen() -> None:
    """清除终端当前内容，供 CLI 实时界面复用。"""
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="")


@lru_cache(maxsize=4)
def get_logger(name: str = "gpu-platform") -> logging.Logger:
    """创建带滚动文件的项目日志器。"""
    log_dir = Path(os.environ.get("GPU_PLATFORM_LOG_DIR", "logs"))
    if not log_dir.is_absolute():
        log_dir = Path(__file__).resolve().parents[2] / log_dir
    log_dir.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        handler = RotatingFileHandler(
            log_dir / "gpu-platform.log",
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(handler)
    return logger
