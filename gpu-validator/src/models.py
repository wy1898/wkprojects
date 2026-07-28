"""Data models shared by the GPU validation modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class GPUInfo:
    """Describe information reported by an NVIDIA GPU."""

    gpu_name: str
    memory_total: float
    driver_version: str
    cuda_version: str
    temperature: float
    power_usage: float


@dataclass
class CheckResult:
    """Represent the outcome of one environment check.

    ``detail`` is optional so short checks need only provide a message while
    checks such as GPU detection can attach structured measurements.
    """

    check_name: str
    status: str
    message: str
    detail: dict[str, Any] | None = None


@dataclass
class ValidationReport:
    """Represent all checks and the aggregate final result."""

    checks: list[CheckResult]
    final_result: CheckResult
