"""Final artifact combining a snapshot with diagnostic findings."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid

from .finding import Finding, Severity
from .snapshot import DiagnosticSnapshot


@dataclass(slots=True)
class DiagnosticReport:
    snapshot: DiagnosticSnapshot
    findings: list[Finding] = field(default_factory=list)
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def status(self) -> Severity:
        if not self.findings:
            return Severity.INFO
        return max(self.findings, key=lambda finding: list(Severity).index(finding.severity)).severity

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "status": self.status.value,
            "snapshot": self.snapshot.to_dict(),
            "findings": [finding.to_dict() for finding in self.findings],
        }
