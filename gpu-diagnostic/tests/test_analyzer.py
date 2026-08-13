from __future__ import annotations

from pathlib import Path
import unittest

from gpu_diagnostic.analyzer.rule_engine import RuleEngine
from gpu_diagnostic.models.snapshot import DiagnosticSnapshot


FIXTURES = Path(__file__).parent / "fixtures"


class AnalyzerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = RuleEngine()

    def test_xid79_fixture_creates_critical_evidence_backed_finding(self) -> None:
        lines = (FIXTURES / "xid79.log").read_text(encoding="utf-8").splitlines()
        snapshot = DiagnosticSnapshot(snapshot_id="xid79", logs={"relevant_lines": lines})
        finding = next(item for item in self.engine.analyze(snapshot) if item.error_id == "xid_79")
        self.assertEqual(finding.severity.value, "CRITICAL")
        self.assertEqual(finding.evidence[0].source, "dmesg")
        self.assertIn("Xid", finding.evidence[0].matched)

    def test_pcie_visible_and_smi_failure_is_driver_communication_issue(self) -> None:
        snapshot = DiagnosticSnapshot(
            snapshot_id="driver-comms",
            pci={"lspci": {"succeeded": True}, "nvidia_devices": ["65:00.0 VGA compatible controller: NVIDIA"]},
            gpu={"nvidia_smi": {"succeeded": False, "stderr": "Unable to determine the device handle"}},
        )
        finding = next(item for item in self.engine.analyze(snapshot) if item.error_id == "driver_communication_failure")
        self.assertEqual(finding.severity.value, "ERROR")
        self.assertEqual({item.source for item in finding.evidence}, {"lspci", "nvidia-smi"})

    def test_expected_gpu_count_generates_inventory_finding(self) -> None:
        snapshot = DiagnosticSnapshot(
            snapshot_id="inventory",
            expected_gpu_count=4,
            gpu={"gpus": [{"name": "NVIDIA A100"}, {"name": "NVIDIA A100"}]},
        )
        findings = self.engine.analyze(snapshot)
        self.assertIn("gpu_count_below_expected", [item.error_id for item in findings])

    def test_xid31_and_pcie_fixtures_match_log_rules(self) -> None:
        xid31 = (FIXTURES / "xid31.log").read_text(encoding="utf-8").splitlines()
        pcie = (FIXTURES / "pcie_error.log").read_text(encoding="utf-8").splitlines()
        xid_findings = self.engine.analyze(DiagnosticSnapshot(snapshot_id="xid31", logs={"relevant_lines": xid31}))
        pcie_findings = self.engine.analyze(DiagnosticSnapshot(snapshot_id="pcie", logs={"relevant_lines": pcie}))
        self.assertIn("xid_31", [item.error_id for item in xid_findings])
        self.assertIn("pcie_aer_error", [item.error_id for item in pcie_findings])

    def test_runtime_and_inventory_evidence_rules(self) -> None:
        cuda_error = (FIXTURES / "cuda_error.log").read_text(encoding="utf-8")
        snapshot = DiagnosticSnapshot(
            snapshot_id="runtime",
            pci={"lspci": {"succeeded": True}, "nvidia_devices": []},
            driver={"lsmod": {"succeeded": True}, "nvidia_modules": []},
            runtime={
                "nvcc": {"succeeded": False, "stderr": "nvcc: command not found"},
                "pytorch": {"succeeded": True, "stdout": cuda_error},
            },
        )
        findings = self.engine.analyze(snapshot)
        ids = [item.error_id for item in findings]
        self.assertIn("gpu_not_detected", ids)
        self.assertIn("driver_module_missing", ids)
        self.assertIn("nvcc_unavailable", ids)
        self.assertIn("pytorch_cuda_unavailable", ids)


if __name__ == "__main__":
    unittest.main()
