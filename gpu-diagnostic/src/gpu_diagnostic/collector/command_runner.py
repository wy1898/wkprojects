"""Safe, structured execution wrapper for Linux diagnostic commands."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import subprocess
from typing import Sequence


@dataclass(slots=True)
class CommandResult:
    command: list[str]
    stdout: str = ""
    stderr: str = ""
    return_code: int | None = None
    timed_out: bool = False
    error_type: str | None = None
    error_message: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.return_code == 0 and self.error_type is None and not self.timed_out

    def to_dict(self) -> dict[str, object]:
        return asdict(self) | {"succeeded": self.succeeded}


class CommandRunner:
    def __init__(self, default_timeout: int = 15) -> None:
        self.default_timeout = default_timeout

    def run(self, command: Sequence[str], timeout: int | None = None) -> CommandResult:
        command_list = list(command)
        try:
            completed = subprocess.run(
                command_list,
                capture_output=True,
                text=True,
                timeout=timeout or self.default_timeout,
                check=False,
            )
            return CommandResult(
                command=command_list,
                stdout=completed.stdout,
                stderr=completed.stderr,
                return_code=completed.returncode,
            )
        except FileNotFoundError as error:
            return CommandResult(command_list, error_type="command_not_found", error_message=str(error))
        except PermissionError as error:
            return CommandResult(command_list, error_type="permission_denied", error_message=str(error))
        except subprocess.TimeoutExpired as error:
            return CommandResult(
                command_list,
                stdout=error.stdout or "",
                stderr=error.stderr or "",
                timed_out=True,
                error_type="timeout",
                error_message=f"Command exceeded {timeout or self.default_timeout}s timeout",
            )
