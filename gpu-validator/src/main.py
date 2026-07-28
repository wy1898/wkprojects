"""Command-line entry point for GPU environment validation."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Sequence

if __package__:
    from .report import ReportWriter
    from .validator import ValidationRunner
else:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from src.report import ReportWriter
    from src.validator import ValidationRunner


def main(argv: Sequence[str] | None = None) -> int:
    """Run validation, print the report, and save the JSON report.

    Args:
        argv: Reserved for future command-line options.

    Returns:
        Zero when the validation workflow completed.
    """
    del argv
    try:
        report = ValidationRunner().run()
        writer = ReportWriter()
        writer.print_terminal(report)
        writer.write_json(report, Path("reports/gpu_validation_report.json"))
    except Exception as exc:
        print(f"Validation tool error: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
