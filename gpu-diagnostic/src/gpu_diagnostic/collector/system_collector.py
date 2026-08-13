"""Collect OS and kernel identity, without interpreting it."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .command_runner import CommandRunner


class SystemCollector:
    def __init__(self, runner: CommandRunner) -> None:
        self.runner = runner

    def collect(self) -> dict[str, Any]:
        uname = self.runner.run(["uname", "-a"])
        os_release = self._read_os_release()
        return {"uname": uname.to_dict(), "os_release": os_release}

    @staticmethod
    def _read_os_release() -> dict[str, str]:
        path = Path("/etc/os-release")
        if not path.exists():
            return {"error": "/etc/os-release is unavailable (this may not be Linux)."}
        values: dict[str, str] = {}
        for line in path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                values[key] = value.strip().strip('"')
        return values
