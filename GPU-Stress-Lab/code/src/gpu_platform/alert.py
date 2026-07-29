"""GPU 监控异常检测规则。"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


TEMPERATURE_WARNING_C = 85.0
DEFAULT_EXPECTED_UTILIZATION = 70.0


def detect_alerts(
    snapshot: dict[str, Any],
    history: Sequence[dict[str, Any]] = (),
    stress_active: bool = False,
    expected_utilization: float = DEFAULT_EXPECTED_UTILIZATION,
) -> list[dict[str, str]]:
    """根据当前快照和历史数据返回结构化 WARNING 列表。"""
    alerts: list[dict[str, str]] = []
    temperature = snapshot.get("temperature_c")
    if isinstance(temperature, (int, float)) and temperature > TEMPERATURE_WARNING_C:
        alerts.append({
            "level": "WARNING",
            "metric": "temperature",
            "message": f"GPU 温度过高：{temperature:.1f}°C（阈值 {TEMPERATURE_WARNING_C:.0f}°C）",
        })

    memory = snapshot.get("memory_used_mib")
    if not isinstance(memory, (int, float)) or memory <= 0:
        alerts.append({
            "level": "WARNING",
            "metric": "memory",
            "message": "GPU 显存不可用或读取异常",
        })
    elif history:
        previous = history[-1].get("memory_used_mib")
        if isinstance(previous, (int, float)) and previous > 0 and memory < previous * 0.5:
            alerts.append({
                "level": "WARNING",
                "metric": "memory",
                "message": "GPU 显存占用异常下降",
            })

    if stress_active and len(history) >= 2:
        recent = [item.get("utilization_percent") for item in (*history[-2:], snapshot)]
        if all(isinstance(value, (int, float)) and value < expected_utilization for value in recent):
            alerts.append({
                "level": "WARNING",
                "metric": "utilization",
                "message": f"压测期间 GPU 利用率持续低于预期 {expected_utilization:.0f}%",
            })
    return alerts
