"""Capture host identity evidence needed to interpret one diagnostic run."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .command_runner import CommandRunner


class HostCollector:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def collect(self) -> dict[str, Any]:
        return {
            "hostname": self.runner.run(["hostname"]).to_dict(),
            "kernel_version": self.runner.run(["uname", "-r"]).to_dict(),
            "architecture": self.runner.run(["uname", "-m"]).to_dict(),
            "os_release": self._os_release(),
        }

    @staticmethod
    def _os_release() -> dict[str, str]:
        path = Path("/etc/os-release")
        if not path.exists():
            return {"error": "/etc/os-release is unavailable"}
        values: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                values[key] = value.strip().strip('"')
        return values
