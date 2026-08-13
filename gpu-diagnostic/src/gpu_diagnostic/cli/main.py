"""CLI entry point for evidence collection and rule-based diagnosis."""

from __future__ import annotations

import argparse
from pathlib import Path

from gpu_diagnostic.models.run import DiagnosticRun
from gpu_diagnostic.services.diagnostic_service import DiagnosticService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gpu-diag", description="Linux NVIDIA GPU diagnostic helper")
    parser.add_argument("command", choices=("collect", "diagnose"))
    parser.add_argument("--output-dir", type=Path, default=Path("reports"), help="Directory for JSON reports")
    parser.add_argument("--expected-gpus", type=int, help="Expected GPU count for multi-GPU inventory checks")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    service = DiagnosticService()
    if args.command == "collect":
        report = DiagnosticRun(snapshot=service.collect(args.expected_gpus))
        print("Collection Status: COMPLETE")
        print("Findings: not analyzed (use 'gpu-diag diagnose')")
    else:
        report = service.diagnose(args.expected_gpus)
        print("Diagnostic Summary:")
        print(f"Status: {report.status.value}")
        print(f"Findings: {len(report.findings)}")
        print("Findings:")
        if report.findings:
            for index, finding in enumerate(report.findings, start=1):
                print(f"{index}. [{finding.severity.value}] {finding.title}")
        else:
            print("No rule matches found. Review collected evidence before concluding the host is healthy.")
    report_paths = service.save(report, args.output_dir)
    print(f"JSON Report: {report_paths['json']}")
    print(f"HTML Report: {report_paths['html']}")


if __name__ == "__main__":
    main()
