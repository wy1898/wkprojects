from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from gpu_diagnostic.analyzer.rule_engine import RuleEngine
from gpu_diagnostic.models.finding import Evidence, Finding, Severity
from gpu_diagnostic.models.run import DiagnosticRun, DiagnosticStatus
from gpu_diagnostic.models.snapshot import DiagnosticSnapshot
from gpu_diagnostic.reporter.html_reporter import HTMLReporter
from gpu_diagnostic.utils.config import DiagnosticConfig, load_config


class PhaseTwoTests(unittest.TestCase):
    def test_status_uses_highest_finding_severity_and_pass_without_findings(self) -> None:
        snapshot = DiagnosticSnapshot(snapshot_id="status")
        self.assertEqual(DiagnosticRun(snapshot=snapshot).status, DiagnosticStatus.PASS)
        warning = Finding("warm", Severity.WARNING, "Warm", "Sample threshold exceeded", [Evidence("nvidia-smi", "86")])
        critical = Finding("xid", Severity.CRITICAL, "Xid", "Communication event", [Evidence("dmesg", "Xid 79")])
        self.assertEqual(DiagnosticRun(snapshot=snapshot, findings=[warning, critical]).status, DiagnosticStatus.CRITICAL)

    def test_html_report_contains_evidence_and_escapes_raw_log_text(self) -> None:
        finding = Finding("xid", Severity.CRITICAL, "Xid", "Event", [Evidence("dmesg", "<NVRM: Xid 79>")], ["PCIe issue"], ["Inspect AER"])
        run = DiagnosticRun(snapshot=DiagnosticSnapshot(snapshot_id="html"), findings=[finding])
        with TemporaryDirectory() as directory:
            path = HTMLReporter().write(run, Path(directory))
            output = path.read_text(encoding="utf-8")
        self.assertIn("GPU Diagnostic Report", output)
        self.assertIn("dmesg", output)
        self.assertIn("&lt;NVRM: Xid 79&gt;", output)

    def test_config_loader_reads_threshold_and_log_keywords(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.yaml"
            path.write_text("temperature_threshold: 90\nexpected_gpu_count: 4\nexpected_persistence_mode: Enabled\nlog_keywords: [NVRM, Xid]\n", encoding="utf-8")
            config = load_config(path)
        self.assertEqual(config.temperature_threshold, 90)
        self.assertEqual(config.expected_gpu_count, 4)
        self.assertEqual(config.expected_persistence_mode, "Enabled")
        self.assertEqual(config.log_keywords, ("NVRM", "Xid"))

    def test_xid13_rule_matches_fixture(self) -> None:
        line = (Path(__file__).parent / "fixtures" / "xid13.log").read_text(encoding="utf-8")
        findings = RuleEngine().analyze(DiagnosticSnapshot(snapshot_id="xid13", logs={"relevant_lines": [line]}))
        self.assertIn("xid_13", [item.error_id for item in findings])

    def test_persistence_rule_uses_operator_configuration(self) -> None:
        config = DiagnosticConfig(expected_persistence_mode="Enabled")
        snapshot = DiagnosticSnapshot(snapshot_id="persistence", gpu={"gpus": [{"persistence_mode": "Disabled"}]})
        findings = RuleEngine(config=config).analyze(snapshot)
        self.assertIn("persistence_mode_unexpected", [item.error_id for item in findings])


if __name__ == "__main__":
    unittest.main()
