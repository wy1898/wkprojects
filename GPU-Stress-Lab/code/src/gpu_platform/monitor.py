"""GPU 实时监控模块。

本模块只负责读取 nvidia-smi 数据和监控循环，终端消息统一交给 output.py。
"""

from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import time
from typing import Any

from .output import print_error, print_info, print_monitor_status


_QUERY = (
    "name,driver_version,memory.total,memory.used,utilization.gpu,"
    "temperature.gpu,power.draw"
)


def _read_gpu(device: int) -> dict[str, str]:
    """通过 nvidia-smi 的 query-gpu CSV 接口读取指定 GPU。"""
    executable = shutil.which("nvidia-smi")
    if not executable:
        raise FileNotFoundError("nvidia-smi 未找到，请确认 NVIDIA 驱动已安装")

    command = [
        executable,
        f"--id={device}",
        f"--query-gpu={_QUERY}",
        "--format=csv,noheader,nounits",
    ]
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=10
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError(f"读取 GPU 信息失败：{exc}") from exc

    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        if re.search(r"invalid|not found|does not exist|no.*gpu", detail, re.I):
            raise IndexError(f"GPU 编号 {device} 不存在：{detail}")
        raise RuntimeError(f"读取 GPU 信息失败：{detail or result.returncode}")

    rows = list(csv.reader(result.stdout.splitlines(), skipinitialspace=True))
    if not rows or len(rows[0]) != 7:
        raise RuntimeError("读取 GPU 信息失败：nvidia-smi 返回数据格式无效")
    names = ("GPU Name", "Driver Version", "Memory Total", "Memory Used",
             "GPU Utilization", "GPU Temperature", "GPU Power Draw")
    return dict(zip(names, (value.strip() for value in rows[0])))


def _cuda_version() -> str:
    """读取 nvidia-smi 版本信息中的 CUDA Version。"""
    executable = shutil.which("nvidia-smi")
    if not executable:
        return "Unavailable"
    try:
        result = subprocess.run(
            [executable, "--version"],
            capture_output=True,
            text=True,
            check=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return "Unavailable"
    match = re.search(r"CUDA Version\s*:\s*([\w.]+)", result.stdout)
    return match.group(1) if match else "Unavailable"


def _status(data: dict[str, str], device: int, interval: float, started: float) -> dict[str, Any]:
    """整理一次采集结果，并补充监控自身的运行信息。"""
    running = int(time.monotonic() - started)
    return {
        "GPU Name": data["GPU Name"],
        "GPU Utilization (%)": f"{data['GPU Utilization']}%",
        "GPU Memory (Used / Total)": f"{data['Memory Used']} / {data['Memory Total']} MiB",
        "GPU Temperature (°C)": f"{data['GPU Temperature']} °C",
        "GPU Power Draw (W)": f"{data['GPU Power Draw']} W",
        "Driver Version": data["Driver Version"],
        "CUDA Version": _cuda_version(),
        "Monitoring Running Time": f"{running}s",
        "Refresh Interval": f"{interval:g}s",
        "GPU Index": str(device),
    }


def _clear_screen() -> None:
    """清除当前终端内容，使刷新保持为单一监控界面。"""
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="")


def run_monitor(interval: float = 1, device: int = 0) -> None:
    """启动 GPU 监控循环，支持 Ctrl+C 安全退出。"""
    try:
        if interval <= 0:
            raise ValueError("刷新间隔必须大于 0")
        if device < 0:
            raise ValueError("GPU 编号不能为负数")
    except (TypeError, ValueError) as exc:
        print_error(f"监控参数错误：{exc}")
        return

    print_info(f"GPU 监控已启动（设备 {device}，刷新间隔 {interval:g}s）")
    started = time.monotonic()
    try:
        while True:
            data = _read_gpu(device)
            _clear_screen()
            print_monitor_status(_status(data, device, interval, started))
            time.sleep(interval)
    except KeyboardInterrupt:
        print_info("Monitoring stopped.")
    except FileNotFoundError as exc:
        print_error(str(exc))
    except IndexError as exc:
        print_error(str(exc))
    except RuntimeError as exc:
        print_error(str(exc))
    except Exception as exc:
        print_error(f"监控运行失败：{exc}")
