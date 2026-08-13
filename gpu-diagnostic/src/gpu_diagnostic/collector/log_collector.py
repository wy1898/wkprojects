"""Collect focused kernel-log evidence relevant to NVIDIA/PCIe failures."""

from __future__ import annotations

from typing import Any

from .command_runner import CommandRunner


class LogCollector:
    def __init__(self, runner: CommandRunner, keywords: tuple[str, ...] = ("NVRM", "XID", "PCI", "AER")) -> None:
        self.runner = runner
        self.keywords = tuple(item.upper() for item in keywords)

    def collect(self) -> dict[str, Any]:
        result = self.runner.run(["dmesg", "-T"])
        lines = [line for line in result.stdout.splitlines() if any(word in line.upper() for word in self.keywords)]
        return {"dmesg": result.to_dict(), "relevant_lines": lines}
