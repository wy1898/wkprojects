"""Terminal and JSON report output for validation results."""

from __future__ import annotations

import json
from pathlib import Path

from .models import CheckResult, ValidationReport


class ReportWriter:
    """Render validation reports to the terminal and a JSON file."""

    def print_terminal(self, report: ValidationReport) -> None:
        """Print all checks and the final result to standard output."""
        print("GPU Environment Validation Report")
        print("=" * 36)
        for check in report.checks:
            print(f"{check.check_name}: {check.status} - {check.message}")
        print(f"final_result: {report.final_result.status} - "
              f"{report.final_result.message}")
        print("=" * 36)

    def write_json(self, report: ValidationReport, destination: Path) -> None:
        """Serialize checks and the final result to a JSON file.

        Args:
            report: Aggregate validation report.
            destination: Path of the JSON output file.
        """
        checks = [self._serialize_check(check) for check in report.checks]
        payload = {
            "checks": checks,
            "final_result": self._serialize_check(report.final_result),
        }
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @staticmethod
    def _serialize_check(check: CheckResult) -> dict[str, object]:
        """Serialize a check without duplicating its message in ``detail``."""
        item: dict[str, object] = {
            "check_name": check.check_name,
            "status": check.status,
            "message": check.message,
        }
        if check.detail:
            item["detail"] = check.detail
        return item
