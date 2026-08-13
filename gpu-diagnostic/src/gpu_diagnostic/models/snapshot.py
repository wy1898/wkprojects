"""The normalized evidence captured during one diagnostic run."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import socket


@dataclass(slots=True)
class DiagnosticSnapshot:
    snapshot_id: str
    hostname: str = field(default_factory=socket.gethostname)
    collected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    system: dict[str, Any] = field(default_factory=dict)
    gpu: dict[str, Any] = field(default_factory=dict)
    pci: dict[str, Any] = field(default_factory=dict)
    driver: dict[str, Any] = field(default_factory=dict)
    runtime: dict[str, Any] = field(default_factory=dict)
    logs: dict[str, Any] = field(default_factory=dict)
    expected_gpu_count: int | None = None
    collector_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
