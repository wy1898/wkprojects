from dataclasses import dataclass
import subprocess

@dataclass
class CommandResult:
    command: list[str]
    stdout: str = ""
    stderr: str = ""
    return_code: int | None = None
    status: str = "AVAILABLE"
    error: str | None = None

class CommandRunner:
    def __init__(self, timeout: float = 10): self.timeout = timeout
    def run(self, command: list[str], timeout: float | None = None) -> CommandResult:
        try:
            p = subprocess.run(command, capture_output=True, text=True, timeout=timeout or self.timeout, check=False)
            return CommandResult(command, p.stdout.strip(), p.stderr.strip(), p.returncode, "AVAILABLE" if p.returncode == 0 else "ERROR")
        except FileNotFoundError as e: return CommandResult(command, status="UNAVAILABLE", error=str(e))
        except PermissionError as e: return CommandResult(command, status="ERROR", error=str(e))
        except subprocess.TimeoutExpired as e: return CommandResult(command, status="ERROR", error=f"timeout after {timeout or self.timeout}s")
