from ..services.runner import CommandRunner

class RaidCollector:
    """Capability-first RAID collector with normalized output and graceful gaps."""
    TOOLS = (("mdadm", ["mdadm", "--detail", "--scan"]), ("storcli", ["storcli", "show"]), ("perccli", ["perccli", "show"]))
    def __init__(self, runner=None): self.runner = runner or CommandRunner()
    def collect(self):
        attempts = []
        for tool, command in self.TOOLS:
            result = self.runner.run(command)
            attempts.append({"tool": tool, "status": result.status, "stdout": result.stdout, "stderr": result.stderr, "error": result.error})
            if result.status == "AVAILABLE":
                return {"status": "AVAILABLE", "tool": tool, "controller": tool, "level": _find_level(result.stdout), "state": _find_state(result.stdout), "attempts": attempts}
        return {"status": "UNAVAILABLE", "message": "No supported RAID capability was available", "attempts": attempts}

def _find_level(text):
    upper = text.upper()
    for level in ("RAID10", "RAID6", "RAID5", "RAID1", "RAID0"):
        if level in upper: return level
    return None
def _find_state(text):
    upper = text.upper()
    if "DEGRADED" in upper or "FAILED" in upper: return "Degraded"
    if "OPTIMAL" in upper or "CLEAN" in upper: return "Optimal"
    return None
