"""基于 PyTorch CUDA 的 GPU 矩阵乘法压力测试模块。"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from .output import (
    print_error,
    print_info,
    print_monitor_status,
    print_stress_summary,
    print_success,
    print_warning,
)
from .utils import GpuQueryError, clear_screen, get_logger, read_gpu_metrics


def _validate_arguments(device: int, duration: float, size: int, interval: float) -> None:
    """检查压力测试参数，尽早给出明确错误。"""
    if device < 0:
        raise ValueError("GPU 编号不能为负数")
    if duration <= 0:
        raise ValueError("测试时长必须大于 0 秒")
    if size <= 0:
        raise ValueError("矩阵规模必须大于 0")
    if interval <= 0:
        raise ValueError("状态刷新间隔必须大于 0 秒")


def _read_gpu(device: int) -> dict[str, Any]:
    """复用 utils 的采集结果，并保留压力测试内部的旧字段名。"""
    snapshot = read_gpu_metrics(device)
    return {
        "GPU Name": snapshot["name"],
        "Driver Version": snapshot["driver_version"],
        "Memory Total": snapshot["memory_total_mib"],
        "Memory Used": snapshot["memory_used_mib"],
        "GPU Utilization": snapshot["utilization_percent"],
        "GPU Temperature": snapshot["temperature_c"],
        "GPU Power Draw": snapshot["power_draw_w"],
        "_snapshot": snapshot,
    }


def _number(value: Any) -> float:
    """提取 nvidia-smi 数值字段，无法读取时返回零。"""
    try:
        return float(str(value).replace("%", "").replace("W", "").strip())
    except (TypeError, ValueError):
        return 0.0


def _clear_screen() -> None:
    """清理终端画面，避免压力测试状态无限滚屏。"""
    clear_screen()


def _show_status(data: dict[str, Any], device: int, elapsed: float, interval: float) -> None:
    """将一次 GPU 采样转换为统一的实时状态输出。"""
    _clear_screen()
    print_monitor_status({
        "GPU Name": data["GPU Name"],
        "GPU Utilization": f"{data['GPU Utilization']}%",
        "GPU Memory": f"{data['Memory Used']} / {data['Memory Total']} MiB",
        "GPU Temperature": f"{data['GPU Temperature']} °C",
        "GPU Power Draw": f"{data['GPU Power Draw']} W",
        "GPU Index": str(device),
        "Monitoring Running Time": f"{elapsed:.1f}s",
        "Refresh Interval": f"{interval:g}s",
    })


def _summary(
    data: dict[str, Any],
    device: int,
    size: int,
    elapsed: float,
    iterations: int,
    normal: bool,
    peak_memory: float,
    peak_utilization: float,
    peak_temperature: float,
    average_utilization: float,
) -> dict[str, Any]:
    """整理测试统计结果，供 output.py 统一渲染。"""
    seconds = max(elapsed, 1e-9)
    status = "WARNING" if (
        peak_temperature > 85 or average_utilization < 70 or peak_memory <= 0
    ) else "PASS"
    return {
        "GPU Name": data.get("GPU Name", "Unknown"),
        "GPU Index": device,
        "运行时间": f"{elapsed:.2f}s",
        "矩阵规模": f"{size} x {size}",
        "总迭代次数": iterations,
        "平均每秒迭代次数": f"{iterations / seconds:.2f}",
        "峰值显存": f"{peak_memory:.0f} MiB",
        "峰值 GPU 利用率": f"{peak_utilization:.0f}%",
        "峰值温度": f"{peak_temperature:.0f} °C",
        "是否正常结束": "是" if normal else "否",
        "completed_at": time.time(),
        "duration_seconds": round(elapsed, 2),
        "average_utilization": round(average_utilization, 1),
        "peak_temperature": round(peak_temperature, 1),
        "peak_memory": round(peak_memory, 1),
        "status": status,
    }


def _update_peaks(data: dict[str, Any], peaks: dict[str, float]) -> None:
    """用最新 nvidia-smi 采样更新峰值统计。"""
    peaks["memory"] = max(peaks["memory"], _number(data["Memory Used"]))
    peaks["utilization"] = max(peaks["utilization"], _number(data["GPU Utilization"]))
    peaks["temperature"] = max(peaks["temperature"], _number(data["GPU Temperature"]))


def _load_torch() -> Any:
    """延迟导入 PyTorch，避免未安装时影响其它 CLI 命令。"""
    try:
        import torch
    except ImportError as exc:
        raise RuntimeError("PyTorch 未安装，无法执行 CUDA 压力测试") from exc
    except Exception as exc:
        raise RuntimeError(f"PyTorch 加载失败：{exc}") from exc
    try:
        cuda_available = torch.cuda.is_available()
    except Exception as exc:
        raise RuntimeError(f"CUDA 状态检查失败：{exc}") from exc
    if not cuda_available:
        raise RuntimeError("CUDA 不可用，无法执行 GPU 压力测试")
    return torch


def run_stress(
    device: int = 0,
    duration: float = 60,
    size: int = 2048,
    interval: float = 1,
    stop_event: threading.Event | None = None,
    status_callback: Callable[[dict[str, Any]], None] | None = None,
    console_output: bool = True,
) -> dict[str, Any]:
    """在指定 GPU 上持续执行 CUDA 矩阵乘法压力测试。"""
    logger = get_logger()
    torch = None
    left = right = result = None
    initial_info: dict[str, Any] = {}
    started = time.monotonic()
    iterations = 0
    normal = False
    peaks = {"memory": 0.0, "utilization": 0.0, "temperature": 0.0}
    utilization_total = 0.0
    utilization_samples = 0

    try:
        _validate_arguments(device, duration, size, interval)
        initial_info = _read_gpu(device)
        torch = _load_torch()
        torch.cuda.set_device(device)
        cuda_device = f"cuda:{device}"
        if console_output:
            print_info(f"正在申请 {size} x {size} CUDA 矩阵（GPU {device}）")
        left = torch.randn((size, size), device=cuda_device)
        right = torch.randn((size, size), device=cuda_device)
        result = torch.matmul(left, right)
        torch.cuda.synchronize()
        del result
        result = None
        if console_output:
            print_info("CUDA warm-up completed.")

        started = time.monotonic()
        next_refresh = started
        while True:
            result = torch.matmul(left, right)
            torch.cuda.synchronize()
            iterations += 1
            now = time.monotonic()
            if now >= next_refresh:
                sample = _read_gpu(device)
                _update_peaks(sample, peaks)
                utilization = _number(sample["GPU Utilization"])
                utilization_total += utilization
                utilization_samples += 1
                if status_callback:
                    status_callback({
                        **sample["_snapshot"],
                        "stress_elapsed": now - started,
                        "stress_iterations": iterations,
                    })
                elif console_output:
                    _show_status(sample, device, now - started, interval)
                logger.info(
                    "stress sample device=%s utilization=%s temperature=%s memory=%s",
                    device,
                    sample["GPU Utilization"],
                    sample["GPU Temperature"],
                    sample["Memory Used"],
                )
                next_refresh += interval
            if stop_event and stop_event.is_set():
                break
            if now - started >= duration:
                normal = True
                break

        final_info = _read_gpu(device)
        _update_peaks(final_info, peaks)
        final_utilization = _number(final_info["GPU Utilization"])
        utilization_total += final_utilization
        utilization_samples += 1
        if console_output:
            print_success("Stress test completed.")
        logger.info("stress finished device=%s iterations=%s normal=%s", device, iterations, normal)
    except KeyboardInterrupt:
        if console_output:
            print_warning("Stress test interrupted by user.")
        logger.info("stress interrupted by user")
        if not console_output:
            raise
    except (FileNotFoundError, IndexError, GpuQueryError, MemoryError, RuntimeError, ValueError) as exc:
        message = str(exc)
        logger.exception("stress failed: %s", message)
        if console_output:
            print_error(f"CUDA 压力测试失败：{message}")
        else:
            raise
    except Exception as exc:
        logger.exception("stress failed unexpectedly: %s", exc)
        if console_output:
            print_error(f"压力测试运行失败：{exc}")
        else:
            raise
    finally:
        elapsed = time.monotonic() - started
        if torch is not None:
            try:
                del result, left, right
                torch.cuda.empty_cache()
            except (NameError, RuntimeError):
                pass
        summary = _summary(
                initial_info, device, size, elapsed, iterations, normal,
                peaks["memory"], peaks["utilization"], peaks["temperature"],
                utilization_total / utilization_samples if utilization_samples else 0,
            ) if initial_info else {}
        if initial_info and console_output:
            print_stress_summary(summary)
    return summary
