"""Evidence-first, dependency-free rule engine for diagnostic snapshots."""

from __future__ import annotations

import csv
from pathlib import Path
import re
from typing import Any

from gpu_diagnostic.models.finding import Evidence, Finding, Severity
from gpu_diagnostic.models.snapshot import DiagnosticSnapshot
from gpu_diagnostic.utils.config import DiagnosticConfig


class RuleEngine:
    """Match structured YAML rules using log text and independent collector signals."""

    def __init__(self, rules_path: Path | None = None, config: DiagnosticConfig | None = None) -> None:
        self.rules_path = rules_path or Path(__file__).parents[1] / "knowledge" / "rules.yaml"
        self.config = config or DiagnosticConfig()
        self.rules = self._load_rules()

    def _load_rules(self) -> dict[str, dict[str, Any]]:
        """Read the intentionally small YAML subset used by this repository.

        It supports nested maps and inline lists required by rules.yaml, avoiding a
        third-party parser on minimally provisioned support hosts.
        """
        rules: dict[str, dict[str, Any]] = {}
        current_rule: dict[str, Any] | None = None
        current_section: dict[str, Any] | None = None
        for raw_line in self.rules_path.read_text(encoding="utf-8").splitlines():
            stripped = raw_line.strip()
            if not stripped or stripped.startswith("#") or stripped == "rules:":
                continue
            indent = len(raw_line) - len(raw_line.lstrip())
            key, separator, raw_value = stripped.partition(":")
            if not separator:
                continue
            value = raw_value.strip()
            if indent == 2:
                current_rule = {}
                rules[key] = current_rule
                current_section = None
            elif indent == 4 and current_rule is not None:
                if value:
                    current_rule[key] = self._parse_value(value)
                    current_section = None
                else:
                    current_section = {}
                    current_rule[key] = current_section
            elif indent == 6 and current_section is not None:
                current_section[key] = self._parse_value(value)
        return rules

    @staticmethod
    def _parse_value(value: str) -> str | list[str]:
        if value.startswith("[") and value.endswith("]"):
            body = value[1:-1].strip()
            return [] if not body else [item.strip().strip('"').strip("'").replace("\\\\", "\\") for item in next(csv.reader([body], skipinitialspace=True))]
        return value.strip().strip('"').strip("'").replace("\\\\", "\\")

    def analyze(self, snapshot: DiagnosticSnapshot) -> list[Finding]:
        signals = self._signals(snapshot)
        findings: list[Finding] = []
        for rule_key, rule in self.rules.items():
            conditions = rule.get("match_conditions", {})
            if not self._matches(snapshot, conditions, signals):
                continue
            findings.append(Finding(
                error_id=str(rule.get("id", rule_key)),
                severity=Severity(str(rule["severity"])),
                title=str(rule["name"]),
                description=str(rule["description"]),
                evidence=self._evidence(snapshot, conditions, signals),
                possible_causes=list(rule.get("possible_causes", [])),
                recommendations=list(rule.get("recommendations", [])),
            ))
        return findings

    def _matches(self, snapshot: DiagnosticSnapshot, conditions: dict[str, Any], signals: dict[str, bool]) -> bool:
        corpus = self._corpus(snapshot)
        keywords = [str(item).lower() for item in conditions.get("keywords", [])]
        regexes = [str(item) for item in conditions.get("regex", [])]
        required = [str(item) for item in conditions.get("all_signals", [])]
        text_conditions_present = bool(keywords or regexes)
        text_match = (
            any(item in corpus for item in keywords)
            or any(re.search(item, corpus, re.IGNORECASE) for item in regexes)
        ) if text_conditions_present else True
        all_signals = all(signals.get(item, False) for item in required)
        return text_match and all_signals and bool(keywords or regexes or required)

    @staticmethod
    def _corpus(snapshot: DiagnosticSnapshot) -> str:
        return str(snapshot.to_dict()).lower()

    def _signals(self, snapshot: DiagnosticSnapshot) -> dict[str, bool]:
        gpu = snapshot.gpu
        pci = snapshot.pci
        driver = snapshot.driver
        runtime = snapshot.runtime
        smi = gpu.get("nvidia_smi", {})
        gpus = gpu.get("gpus", [])
        pci_devices = pci.get("nvidia_devices", [])
        modules = driver.get("nvidia_modules", [])
        pytorch_text = " ".join(str(runtime.get("pytorch", {}).get(key, "")) for key in ("stdout", "stderr")).lower()
        return {
            "no_pci_nvidia": pci.get("lspci", {}).get("succeeded") is True and not pci_devices,
            "pci_nvidia_detected": bool(pci_devices),
            "nvidia_smi_failed": smi.get("succeeded") is False,
            "driver_module_missing": driver.get("lsmod", {}).get("succeeded") is True and not modules,
            "nvcc_failed": runtime.get("nvcc", {}).get("succeeded") is False,
            "pytorch_cuda_unavailable": "cuda_available=false" in pytorch_text or "torch.cuda.is_available() = false" in pytorch_text,
            "high_temperature": any(_as_int(item.get("temperature_c")) >= self.config.temperature_threshold for item in gpus),
            "ecc_uncorrectable": any(_as_int(item.get("ecc_uncorrected")) > 0 for item in gpus),
            "gpu_count_below_expected": snapshot.expected_gpu_count is not None and len(gpus) < snapshot.expected_gpu_count,
            "persistence_mode_unexpected": self.config.expected_persistence_mode is not None and any(item.get("persistence_mode") != self.config.expected_persistence_mode for item in gpus),
        }

    def _evidence(self, snapshot: DiagnosticSnapshot, conditions: dict[str, Any], signals: dict[str, bool]) -> list[Evidence]:
        keywords = [str(item).lower() for item in conditions.get("keywords", [])]
        regexes = [str(item) for item in conditions.get("regex", [])]
        evidence: list[Evidence] = []
        for line in snapshot.logs.get("relevant_lines", []):
            if any(key in line.lower() for key in keywords) or any(re.search(pattern, line, re.IGNORECASE) for pattern in regexes):
                evidence.append(Evidence(source="dmesg", matched=line, detail="Matched diagnostic log condition."))
        signal_details = self._signal_evidence(snapshot)
        for signal in conditions.get("all_signals", []):
            if signals.get(signal):
                evidence.append(signal_details.get(signal, Evidence(source="snapshot", matched=str(signal))))
        return evidence or [Evidence(source="snapshot", matched="Rule condition matched", detail="See collected snapshot for details.")]

    def _signal_evidence(self, snapshot: DiagnosticSnapshot) -> dict[str, Evidence]:
        return {
            "no_pci_nvidia": Evidence("lspci", "No NVIDIA device lines found", "PCI enumeration completed successfully."),
            "pci_nvidia_detected": Evidence("lspci", "NVIDIA PCI device detected", "The adapter is visible on the PCI bus."),
            "nvidia_smi_failed": Evidence("nvidia-smi", str(snapshot.gpu.get("nvidia_smi", {}).get("stderr") or snapshot.gpu.get("nvidia_smi", {}).get("error_message")), "NVIDIA management command did not complete."),
            "driver_module_missing": Evidence("lsmod", "No loaded module beginning with 'nvidia'", "lsmod completed successfully."),
            "nvcc_failed": Evidence("nvcc", str(snapshot.runtime.get("nvcc", {}).get("stderr") or snapshot.runtime.get("nvcc", {}).get("error_message")), "CUDA compiler check did not complete."),
            "pytorch_cuda_unavailable": Evidence("PyTorch", str(snapshot.runtime.get("pytorch", {}).get("stdout")), "PyTorch reported CUDA unavailable."),
            "high_temperature": Evidence("nvidia-smi", f"GPU temperature >= {self.config.temperature_threshold}C", "Threshold is sampled, not a continuous thermal history."),
            "ecc_uncorrectable": Evidence("nvidia-smi", "Non-zero volatile uncorrectable ECC count", "Counter requires historical follow-up."),
            "gpu_count_below_expected": Evidence("nvidia-smi", f"Detected {len(snapshot.gpu.get('gpus', []))}; expected {snapshot.expected_gpu_count}", "Expected count was provided by the operator."),
            "persistence_mode_unexpected": Evidence("nvidia-smi", f"Persistence mode differs from expected {self.config.expected_persistence_mode}", "Expected mode is configured by the operator."),
        }


def _as_int(value: object) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
