"""Application service that owns the collect -> analyze -> report workflow."""

from __future__ import annotations

from pathlib import Path
import uuid

from gpu_diagnostic.analyzer.rule_engine import RuleEngine
from gpu_diagnostic.collector import DriverCollector, GPUCollector, HostCollector, LogCollector, PCICollector, RuntimeCollector, SystemCollector
from gpu_diagnostic.collector.command_runner import CommandRunner
from gpu_diagnostic.models.run import DiagnosticRun
from gpu_diagnostic.models.snapshot import DiagnosticSnapshot
from gpu_diagnostic.reporter.html_reporter import HTMLReporter
from gpu_diagnostic.reporter.json_reporter import JSONReporter
from gpu_diagnostic.utils.config import DiagnosticConfig, load_config


class DiagnosticService:
    def __init__(self, runner: CommandRunner | None = None, config: DiagnosticConfig | None = None) -> None:
        self.runner = runner or CommandRunner()
        self.config = config or load_config()

    def collect(self, expected_gpu_count: int | None = None) -> DiagnosticSnapshot:
        collectors = {
            "system": SystemCollector(self.runner),
            "gpu": GPUCollector(self.runner),
            "pci": PCICollector(self.runner),
            "driver": DriverCollector(self.runner),
            "runtime": RuntimeCollector(self.runner),
            "logs": LogCollector(self.runner, self.config.log_keywords),
        }
        data: dict[str, object] = {}
        errors: list[str] = []
        for name, collector in collectors.items():
            try:
                data[name] = collector.collect()
            except Exception as error:  # A diagnostic tool must preserve partial evidence.
                data[name] = {"error": str(error)}
                errors.append(f"{name}: {error}")
        return DiagnosticSnapshot(snapshot_id=str(uuid.uuid4()), collector_errors=errors, expected_gpu_count=expected_gpu_count, **data)  # type: ignore[arg-type]

    def diagnose(self, expected_gpu_count: int | None = None) -> DiagnosticRun:
        expected = expected_gpu_count if expected_gpu_count is not None else self.config.expected_gpu_count
        snapshot = self.collect(expected)
        host_info = HostCollector(self.runner).collect()
        findings = RuleEngine(config=self.config).analyze(snapshot)
        return DiagnosticRun(snapshot=snapshot, findings=findings, host_info=host_info)

    @staticmethod
    def save(run: DiagnosticRun, output_dir: Path) -> dict[str, Path]:
        return {
            "json": JSONReporter().write(run, output_dir),
            "html": HTMLReporter().write(run, output_dir),
        }
