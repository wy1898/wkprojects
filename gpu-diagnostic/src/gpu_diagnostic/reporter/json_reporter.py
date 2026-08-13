"""JSON report output; stable enough for later database/Web integration."""

from __future__ import annotations

import json
from pathlib import Path

from typing import Protocol


class ReportArtifact(Protocol):
    run_id: str

    def to_dict(self) -> dict[str, object]: ...


class JSONReporter:
    def write(self, report: ReportArtifact, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        artifact_id = getattr(report, "run_id", getattr(report, "report_id", "unknown"))
        output_path = output_dir / f"diagnostic_{artifact_id}.json"
        output_path.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
        return output_path
