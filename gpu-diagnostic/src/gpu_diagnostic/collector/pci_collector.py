"""Collect PCIe enumeration output for NVIDIA adapters."""

from __future__ import annotations

from typing import Any

from .command_runner import CommandRunner


class PCICollector:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def collect(self) -> dict[str, Any]:
        result = self.runner.run(["lspci", "-nn"])
        nvidia_devices = [line for line in result.stdout.splitlines() if "NVIDIA" in line.upper()]
        return {"lspci": result.to_dict(), "nvidia_devices": nvidia_devices}
