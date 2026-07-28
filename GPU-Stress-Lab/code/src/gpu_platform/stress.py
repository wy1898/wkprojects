"""基于 PyTorch CUDA 的 GPU 矩阵乘法压力测试模块。"""

from __future__ import annotations

import csv
import os
import sys
import time
from typing import Any

from . import gpu
from .output import (
    print_error,
    print_info,
    print_monitor_status,
    print_stress_summary,
    print_success,
    print_warning,
)


# 查询字段固定使用 CSV，避免依赖 nvidia-smi 默认表格的显示格式。
_QUERY = (
    "name,driver_version,memory.total,memory.used,utilization.gpu,"
    "temperature.gpu,power.draw"
)
_FIELDS = (
    "GPU Name",
    "Driver Version",
    "Memory Total",
    "Memory Used",
    "GPU Utilization",
    "GPU Temperature",
    "GPU Power Draw",
)


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


def _read_gpu(device: int) -> dict[str, str]:
    """调用 gpu.py 的 nvidia-smi 辅助函数读取一行 GPU CSV 数据。"""
    output, error = gpu._run_nvidia_smi(
        f"--id={device}",
        f"--query-gpu={_QUERY}",
        "--format=csv,noheader,nounits",
    )
    if output is None:
        detail = error or "nvidia-smi 未返回数据"
        if "not found" in detail.lower():
            raise FileNotFoundError(detail)
        if any(word in detail.lower() for word in ("invalid", "not exist", "no gpu")):
            raise IndexError(f"GPU 编号 {device} 不存在：{detail}")
        raise RuntimeError(f"读取 GPU 信息失败：{detail}")

    rows = list(csv.reader(output.splitlines(), skipinitialspace=True))
    if not rows or len(rows[0]) != len(_FIELDS):
        raise RuntimeError("读取 GPU 信息失败：nvidia-smi CSV 数据格式无效")
    return dict(zip(_FIELDS, (value.strip() for value in rows[0])))


def _number(value: str) -> float:
    """提取 nvidia-smi 数值字段，无法读取时返回零。"""
    try:
        return float(value.replace("%", "").replace("W", "").strip())
    except (TypeError, ValueError):
        return 0.0


def _clear_screen() -> None:
    """清理终端画面，避免压力测试状态无限滚屏。"""
    if os.name == "nt":
        os.system("cls")
    else:
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()


def _show_status(data: dict[str, str], device: int, elapsed: float, interval: float) -> None:
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
    data: dict[str, str],
    device: int,
    size: int,
    elapsed: float,
    iterations: int,
    normal: bool,
    peak_memory: float,
    peak_utilization: float,
    peak_temperature: float,
) -> dict[str, Any]:
    """整理测试统计结果，供 output.py 统一渲染。"""
    seconds = max(elapsed, 1e-9)
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
    }


def _update_peaks(data: dict[str, str], peaks: dict[str, float]) -> None:
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
) -> None:
    """在指定 GPU 上持续执行 CUDA 矩阵乘法压力测试。"""
    torch = None
    left = right = result = None
    initial_info: dict[str, str] = {}
    started = time.monotonic()
    iterations = 0
    normal = False
    peaks = {"memory": 0.0, "utilization": 0.0, "temperature": 0.0}

    try:
        _validate_arguments(device, duration, size, interval)
        initial_info = _read_gpu(device)
        torch = _load_torch()
        torch.cuda.set_device(device)
        cuda_device = f"cuda:{device}"
        print_info(f"正在申请 {size} x {size} CUDA 矩阵（GPU {device}）")
        left = torch.randn((size, size), device=cuda_device)
        right = torch.randn((size, size), device=cuda_device)
        result = torch.matmul(left, right)
        torch.cuda.synchronize()
        del result
        result = None
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
                _show_status(sample, device, now - started, interval)
                next_refresh += interval
            if now - started >= duration:
                normal = True
                break

        final_info = _read_gpu(device)
        _update_peaks(final_info, peaks)
        print_success("Stress test completed.")
    except KeyboardInterrupt:
        print_warning("Stress test interrupted by user.")
    except FileNotFoundError as exc:
        print_error(str(exc))
    except IndexError as exc:
        print_error(str(exc))
    except (MemoryError, RuntimeError) as exc:
        message = str(exc)
        if "out of memory" in message.lower() or "cuda" in message.lower():
            print_error(f"CUDA 压力测试失败：{message}")
        else:
            print_error(message)
    except ValueError as exc:
        print_error(f"压力测试参数错误：{exc}")
    except Exception as exc:
        print_error(f"压力测试运行失败：{exc}")
    finally:
        elapsed = time.monotonic() - started
        if torch is not None:
            try:
                del result, left, right
                torch.cuda.empty_cache()
            except (NameError, RuntimeError):
                pass
        if initial_info:
            print_stress_summary(_summary(
                initial_info, device, size, elapsed, iterations, normal,
                peaks["memory"], peaks["utilization"], peaks["temperature"],
            ))
