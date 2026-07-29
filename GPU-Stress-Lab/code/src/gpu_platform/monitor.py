"""GPU 实时监控模块。

本模块只负责读取 nvidia-smi 数据和监控循环，终端消息统一交给 output.py。
"""

from __future__ import annotations

import time
from typing import Any

from .output import print_error, print_info, print_monitor_status
from .utils import GpuQueryError, clear_screen, get_logger, read_gpu_metrics


def _read_gpu(device: int) -> dict[str, Any]:
    """复用共享采集器，并保留监控模块原有字段接口。"""
    snapshot = read_gpu_metrics(device)
    return {
        "GPU Name": snapshot["name"],
        "Driver Version": snapshot["driver_version"],
        "Memory Total": snapshot["memory_total_mib"],
        "Memory Used": snapshot["memory_used_mib"],
        "GPU Utilization": snapshot["utilization_percent"],
        "GPU Temperature": snapshot["temperature_c"],
        "GPU Power Draw": snapshot["power_draw_w"],
        "CUDA Version": snapshot["cuda_version"] or "Unavailable",
    }


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
        "CUDA Version": data["CUDA Version"],
        "Monitoring Running Time": f"{running}s",
        "Refresh Interval": f"{interval:g}s",
        "GPU Index": str(device),
    }


def _clear_screen() -> None:
    """清除当前终端内容，使刷新保持为单一监控界面。"""
    clear_screen()


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

    logger = get_logger()
    print_info(f"GPU 监控已启动（设备 {device}，刷新间隔 {interval:g}s）")
    started = time.monotonic()
    try:
        while True:
            data = _read_gpu(device)
            _clear_screen()
            print_monitor_status(_status(data, device, interval, started))
            logger.info(
                "monitor sample device=%s utilization=%s temperature=%s memory=%s",
                device,
                data["GPU Utilization"],
                data["GPU Temperature"],
                data["Memory Used"],
            )
            time.sleep(interval)
    except KeyboardInterrupt:
        print_info("Monitoring stopped.")
    except (FileNotFoundError, GpuQueryError) as exc:
        print_error(str(exc))
    except IndexError as exc:
        print_error(str(exc))
    except RuntimeError as exc:
        print_error(str(exc))
    except Exception as exc:
        print_error(f"监控运行失败：{exc}")
