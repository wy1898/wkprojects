"""Top-level representation of one complete diagnostic task."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid

from .finding import Finding, Severity
from .snapshot import DiagnosticSnapshot


class DiagnosticStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass(slots=True)
class DiagnosticRun:
    """A single operator-triggered execution, from host capture to findings."""

    snapshot: DiagnosticSnapshot
    findings: list[Finding] = field(default_factory=list)
    host_info: dict[str, Any] = field(default_factory=dict)
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def hostname(self) -> str:
        return str(self.host_info.get("hostname", {}).get("stdout", "").strip() or self.snapshot.hostname)

    @property
    def system_info(self) -> dict[str, Any]:
        return self.snapshot.system

    @property
    def status(self) -> DiagnosticStatus:
        levels = {Severity.WARNING: DiagnosticStatus.WARNING, Severity.ERROR: DiagnosticStatus.ERROR, Severity.CRITICAL: DiagnosticStatus.CRITICAL}
        for severity in (Severity.CRITICAL, Severity.ERROR, Severity.WARNING):
            if any(item.severity == severity for item in self.findings):
                return levels[severity]
        return DiagnosticStatus.PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "timestamp": self.timestamp,
            "hostname": self.hostname,
            "status": self.status.value,
            "finding_count": len(self.findings),
            "host_info": self.host_info,
            "system_info": self.system_info,
            "snapshot": self.snapshot.to_dict(),
            "findings": [item.to_dict() for item in self.findings],
        }
