"""Minimal configuration loader for the project's deliberately simple YAML file."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class DiagnosticConfig:
    temperature_threshold: int = 85
    expected_gpu_count: int | None = None
    expected_persistence_mode: str | None = None
    log_keywords: tuple[str, ...] = ("NVRM", "Xid", "PCI", "AER")


def load_config(path: Path | None = None) -> DiagnosticConfig:
    config_path = path or Path(__file__).parents[3] / "config.yaml"
    if not config_path.exists():
        return DiagnosticConfig()
    values: dict[str, object] = {}
    for line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        key, raw_value = stripped.split(":", 1)
        value = raw_value.strip()
        if value.startswith("[") and value.endswith("]"):
            values[key] = tuple(item.strip().strip('"').strip("'") for item in next(csv.reader([value[1:-1]], skipinitialspace=True)))
        elif value.lower() in {"null", "none", ""}:
            values[key] = None
        else:
            try:
                values[key] = int(value)
            except ValueError:
                values[key] = value.strip('"').strip("'")
    return DiagnosticConfig(
        temperature_threshold=int(values.get("temperature_threshold", 85)),
        expected_gpu_count=values.get("expected_gpu_count") if isinstance(values.get("expected_gpu_count"), int) else None,
        expected_persistence_mode=values.get("expected_persistence_mode") if isinstance(values.get("expected_persistence_mode"), str) else None,
        log_keywords=values.get("log_keywords") if isinstance(values.get("log_keywords"), tuple) else DiagnosticConfig().log_keywords,
    )
