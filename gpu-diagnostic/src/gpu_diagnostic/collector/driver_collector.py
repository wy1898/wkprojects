"""Collect loaded NVIDIA module evidence used for driver diagnosis."""

from __future__ import annotations

from typing import Any

from .command_runner import CommandRunner


class DriverCollector:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def collect(self) -> dict[str, Any]:
        result = self.runner.run(["lsmod"])
        modules = [line for line in result.stdout.splitlines() if line.lower().startswith("nvidia")]
        return {"lsmod": result.to_dict(), "nvidia_modules": modules}
